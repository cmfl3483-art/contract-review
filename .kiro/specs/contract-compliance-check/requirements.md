# Requirements Document

## Introduction

本文档描述合同预审看板系统的「合同合规检查」功能需求。该功能面向销售用户:在销售即将通过「发起合同预审」表单填写合同编号(`contract_number`)、合同名称(`name`)、合同描述(`description`)三个字段之前,先把合同文件(PDF / Word)以及自己已经手填的字段初稿提交给后端,由后端从合同文件抽取纯文本后交给 AI,基于管理员维护的合同规范集合(覆盖三个表单字段以及合同文件正文本身的规则)进行合规检查,产出逐条不符合项,以及可供销售复制到预审表单的「合同名称建议」与「合同描述建议」。

本功能采用分阶段实施策略,本 Spec 仅覆盖**第一阶段:合规检查 + 字段建议草稿**。第一阶段定位是「检查 + 草稿」,销售仍需手动把建议复制回预审表单后再点击「发起预审」按钮;不包含「自动发起合同预审」「AI 生成合同编号」相关流程,后续阶段在 Out of Scope 与 Future Considerations 中说明。

现有系统技术栈:后端 FastAPI + SQLAlchemy 2.0 (async/asyncpg) + PostgreSQL 15 + Redis 7 + MinIO + Socket.IO,前端 React 19 + TypeScript + Vite + Ant Design 6 + Zustand 5 + TanStack Query 5,AI 集成走 OpenAI SDK + DeepSeek API(`backend/app/services/ai_service.py`),认证采用钉钉 OAuth2 + JWT。本功能在已交付的 `contract-pre-review`、`contract-enhancements`、`contract-revision-and-ai-improvements` 三个 Spec 之上扩展,并复用现有附件能力(`backend/app/services/file_service.py`、`backend/app/routes/files.py`、MinIO 存储、`MAX_ATTACHMENT_SIZE_BYTES = 50MB`)。预审表单字段约束严格对齐 `backend/app/routes/contracts.py` 的 `CreateContractRequest`:`name` 长度 1~200 字符、`contract_number` 长度 1~100 字符、`description` 长度 0~2000 字符。

## Glossary

- **System**:合同预审看板系统整体
- **Contract**:合同记录,对应 `contracts` 表
- **Pre_Review_Form**:销售在合同预审看板上「发起合同预审」时填写的表单,包含三个字段:合同编号(`contract_number`)、合同名称(`name`)、合同描述(`description`),分别对应 `Contract.contract_number`(String(100))、`Contract.name`(1~200 字符)、`Contract.description`(0~2000 字符)
- **Compliance_Rule_Set**:合同规范集合,由管理员维护的一组合规要求,既包含针对 Pre_Review_Form 三个字段的规则,也包含针对合同文件正文本身的规则,对应新增的 `compliance_rule_sets` 表
- **Compliance_Rule**:单条合规规则,归属于某一 Compliance_Rule_Set,作用对象由 `rule_type` 标识,对应新增的 `compliance_rules` 表
- **Rule_Type**:规则作用对象枚举,取值为 `number`(对 `contract_number` 表单字段进行格式与内容校验)、`name`(对 `name` 表单字段进行校验)、`description`(对 `description` 表单字段进行校验)、`file`(对合同文件正文本身进行校验,例如必须包含的条款、违禁字眼、签字盖章页等)
- **Rule_Severity**:规则严重程度枚举,取值为 `must`(必须)或 `should`(建议)
- **Active_Rule_Set**:当前生效的 Compliance_Rule_Set;同一时刻系统仅允许一个 Compliance_Rule_Set 处于 `is_active = true` 状态
- **Contract_File**:销售在合规检查请求中上传的合同文件,MIME 类型必须为 `application/pdf`、`application/msword`、`application/vnd.openxmlformats-officedocument.wordprocessingml.document` 三者之一(分别对应 PDF、`.doc`、`.docx`),文件大小 ≤ 50 MB(沿用 `MAX_ATTACHMENT_SIZE_BYTES`)
- **Extracted_Contract_Text**:后端从 Contract_File 抽取出的纯文本,长度 0 至 100000 字符;如抽取出的原始文本超过 100000 字符,SHALL 截断到前 100000 字符并设置 `text_truncated = true`,作为 AI 判断「字段初稿是否与合同正文一致」「合同文件正文是否符合规范」的事实依据
- **Field_Draft**:销售在合规检查请求中手填的预审表单字段初稿,共三个,均为可选,分别为:`number_draft`(对应预审表单的 `contract_number` 字段,0~100 字符)、`name_draft`(对应预审表单的 `name` 字段,0~200 字符)、`description_draft`(对应预审表单的 `description` 字段,0~2000 字符);可单独缺省任意字段
- **Compliance_Check_Request**:销售提交的合规检查请求,包含 Contract_File、零或多个 Field_Draft、可选的 `rule_set_id`,以 multipart/form-data 形式提交
- **Compliance_Check_Result**:AI 完成合规检查后产出的结果记录,对应新增的 `compliance_check_results` 表
- **Violation_Item**:单条不符合项,描述某个 Field_Draft 或 Extracted_Contract_Text 违反某条 Compliance_Rule 的具体内容,包含 `rule_id`、`location`(取值为 `number` / `name` / `description` / `file`,指明违反规则的对象;`location` 取值必须与对应 Compliance_Rule 的 `rule_type` 一致)、`excerpt`(违反规则的原文片段;当 `location` 为 `number` / `name` / `description` 时来自对应字段初稿,当 `location = 'file'` 时来自 Extracted_Contract_Text 的相关片段,允许为空字符串以指代「整个文件缺失某条款」)、`description`(违反描述)、`suggestion`(修改建议)、`severity`
- **Suggested_Field_Value**:AI 基于 Extracted_Contract_Text 与 Compliance_Rule_Set 为 Pre_Review_Form 字段生成的建议取值,本 Spec 仅产出两个:`suggested_name`(供销售复制到预审表单的合同名称字段,长度 1~200 字符)和 `suggested_description`(供销售复制到预审表单的合同描述字段,长度 0~2000 字符);**不产出 `suggested_number`**,合同编号由后端发号器在销售点击「发起预审」时按现有规则生成
- **Compliance_Score**:本次合规检查的整体合规评分,取值为 0 至 100 的整数,数值越大代表合同与 Compliance_Rule_Set 越吻合。该字段持久化在 Compliance_Check_Result 上,由后端在 AI 检查完成后基于 `violations` 计算或采纳 AI 返回值的范围内裁剪得到;计算细则见 Requirement 4 第 13 条
- **Compliance_Service**:后端合同合规检查服务,负责管理 Compliance_Rule_Set / Compliance_Rule 的 CRUD,以及调用 AI 执行合规检查
- **Text_Extractor**:后端从 Contract_File 抽取纯文本的组件;PDF 文件采用 `pdfplumber` 等成熟的 PDF 文本抽取库逐页抽取,`.docx` 文件采用 `python-docx` 抽取段落文本,`.doc` 文件按本 Spec 同样要求支持文本抽取(具体技术选型见 design 阶段);抽取失败时 SHALL 抛出可识别的错误以触发 Requirement 3 的失败处理路径
- **AI_Service**:后端 AI 服务模块,对应 `backend/app/services/ai_service.py`,本 Spec 在其上新增合规检查方法
- **Compliance_Console**:管理员维护合同规范的前端页面
- **Compliance_Check_Panel**:销售提交合规检查请求并查看检查结果的前端页面或面板
- **Current_User**:当前已登录的用户
- **Admin_User**:被授权维护 Compliance_Rule_Set 的管理员用户,定义见 Requirement 1 的「管理员授权范围」
- **Sales_User**:`User.role == '销售'` 的用户

---

## Requirements

### Requirement 1: 管理员维护合同规范集合

**User Story:** 作为管理员,我希望维护一份合同规范集合(包含针对预审表单字段 `number` / `name` / `description` 以及合同文件正文 `file` 的规则),以便后续 AI 据此对销售提交的字段初稿与合同文件正文做合规检查。

#### Acceptance Criteria

1. THE Compliance_Service SHALL 提供创建 Compliance_Rule_Set 的接口 `POST /api/compliance/rule-sets`,请求体包含 `name`(1 至 100 字符,去除首尾空白后非空)、`description`(0 至 1000 字符)、`is_active`(布尔,默认 false)。
2. WHEN Admin_User 创建 Compliance_Rule_Set 且 `is_active` 为 true,THE Compliance_Service SHALL 在同一数据库事务中将其他所有 Compliance_Rule_Set 的 `is_active` 字段更新为 false,确保系统中至多存在一个 Active_Rule_Set。
3. THE Compliance_Service SHALL 提供查询 Compliance_Rule_Set 列表的接口 `GET /api/compliance/rule-sets`,返回结果按 `created_at` 倒序排列,每条记录包含 `id`、`name`、`description`、`is_active`、`created_at`、`updated_at`、`rule_count`(关联的 Compliance_Rule 数量)。
4. THE Compliance_Service SHALL 提供更新 Compliance_Rule_Set 的接口 `PUT /api/compliance/rule-sets/{rule_set_id}`,支持修改 `name`、`description`、`is_active` 字段,字段长度约束与创建接口一致。
5. WHEN Admin_User 通过更新接口将某 Compliance_Rule_Set 的 `is_active` 字段由 false 设置为 true,THE Compliance_Service SHALL 在同一数据库事务中将其他所有 Compliance_Rule_Set 的 `is_active` 字段更新为 false。
6. THE Compliance_Service SHALL 提供删除 Compliance_Rule_Set 的接口 `DELETE /api/compliance/rule-sets/{rule_set_id}`;删除时 SHALL 级联删除该 Compliance_Rule_Set 关联的全部 Compliance_Rule 记录。
7. IF Admin_User 尝试删除 `is_active` 为 true 的 Compliance_Rule_Set,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 409 错误,响应体说明需先停用该规范集合再删除,且不修改任何 Compliance_Rule_Set 或 Compliance_Rule 数据。
8. IF Current_User 不属于「管理员授权范围」(即 `User.role` 不属于集合 `{'法务', '运营'}`),且尝试调用 Requirement 1 第 1、4、6 条所述的写接口(POST、PUT、DELETE),THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 403 错误,响应体包含权限不足说明,且不修改任何 Compliance_Rule_Set 或 Compliance_Rule 数据。
9. IF 请求中 JWT Token 缺失、格式无效或已过期,THEN THE Compliance_Service SHALL 返回 HTTP 401 错误,响应体包含认证失败说明。
10. IF 请求中的 `rule_set_id` 在 `compliance_rule_sets` 表中不存在,THEN THE Compliance_Service SHALL 对 PUT 与 DELETE 请求返回 HTTP 404 错误,响应体说明规范集合不存在,且不修改任何数据。
11. IF Admin_User 提交的 `name` 在去除首尾空白后长度为 0 或超过 100 字符,或 `description` 长度超过 1000 字符,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 422 错误,响应体说明触发限制的字段及其约束。

---

### Requirement 2: 管理员维护合同规范的具体规则

**User Story:** 作为管理员,我希望在合同规范集合下维护多条具体的合规规则,每条规则作用于预审表单的某一个字段(`number` / `name` / `description`)或合同文件正文本身(`file`),并标注严重程度,以便 AI 据此对销售提交的字段初稿与合同文件正文进行精细化合规检查。

#### Acceptance Criteria

1. THE Compliance_Service SHALL 提供新增 Compliance_Rule 的接口 `POST /api/compliance/rule-sets/{rule_set_id}/rules`,请求体包含 `rule_type`(取值为 `number`、`name`、`description`、`file` 四选一,分别对应预审表单的 `contract_number`、`name`、`description` 字段以及合同文件正文)、`title`(规则名称,1 至 100 字符,去除首尾空白后非空)、`requirement`(规则正文描述,1 至 2000 字符,去除首尾空白后非空)、`severity`(取值为 `must` 或 `should`,默认 `must`)、`order`(整数,用于排序,默认 0)。
2. THE Compliance_Service SHALL 提供查询 Compliance_Rule 列表的接口 `GET /api/compliance/rule-sets/{rule_set_id}/rules`,返回结果按 `rule_type` 升序(`number` < `name` < `description` < `file`)、`order` 升序、`created_at` 升序排列,每条记录包含 `id`、`rule_type`、`title`、`requirement`、`severity`、`order`、`created_at`、`updated_at`。
3. THE Compliance_Service SHALL 提供更新 Compliance_Rule 的接口 `PUT /api/compliance/rules/{rule_id}`,支持修改 `rule_type`、`title`、`requirement`、`severity`、`order` 字段,字段约束与新增接口一致。
4. THE Compliance_Service SHALL 提供删除 Compliance_Rule 的接口 `DELETE /api/compliance/rules/{rule_id}`。
5. WHEN Admin_User 通过新增、更新或删除接口对某 Compliance_Rule 进行写操作,THE Compliance_Service SHALL 同步更新所属 Compliance_Rule_Set 的 `updated_at` 字段。
6. IF Admin_User 提交的 `rule_type` 取值不属于集合 `{'number', 'name', 'description', 'file'}`,或 `severity` 取值不属于集合 `{'must', 'should'}`,或 `title` 在去除首尾空白后长度为 0 或超过 100 字符,或 `requirement` 在去除首尾空白后长度为 0 或超过 2000 字符,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 422 错误,响应体说明触发限制的字段及其约束,且不写入任何数据。
7. IF Current_User 不属于「管理员授权范围」(同 Requirement 1 第 8 条),且尝试调用 Requirement 2 第 1、3、4 条所述的写接口(POST、PUT、DELETE),THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 403 错误,响应体包含权限不足说明,且不修改任何 Compliance_Rule 数据。
8. IF 请求中的 `rule_set_id` 或 `rule_id` 在数据库中不存在,THEN THE Compliance_Service SHALL 返回 HTTP 404 错误,响应体说明对应资源不存在,且不修改任何数据。
9. IF 单个 Compliance_Rule_Set 下的 Compliance_Rule 总数已达到 200 条且 Admin_User 尝试新增第 201 条,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 409 错误,响应体说明单个规范集合下最多可包含 200 条规则。

---

### Requirement 3: 销售提交合同合规检查请求

**User Story:** 作为销售,我希望在正式发起预审之前,把合同文件(PDF / Word)以及我已经手填的预审表单字段初稿一起提交给系统,由后端从合同文件抽取文本后交给 AI 检查,以便发现并修正不符合规范的字段填写或合同文件正文,并拿到 AI 给出的合同名称与合同描述建议草案。

#### Acceptance Criteria

1. THE Compliance_Service SHALL 提供发起合规检查的接口 `POST /api/compliance/checks`,以 `multipart/form-data` 形式接收以下字段:
   - `file`(必填,UploadFile,Contract_File,MIME 类型必须为 `application/pdf`、`application/msword`、`application/vnd.openxmlformats-officedocument.wordprocessingml.document` 之一,文件大小 ≤ 50 MB)
   - `number_draft`(可选 form 字段,0 至 100 字符,允许为 null 或空字符串,对应 Pre_Review_Form 的 `contract_number` 字段初稿)
   - `name_draft`(可选 form 字段,0 至 200 字符,允许为 null 或空字符串,对应 Pre_Review_Form 的 `name` 字段初稿)
   - `description_draft`(可选 form 字段,0 至 2000 字符,允许为 null 或空字符串,对应 Pre_Review_Form 的 `description` 字段初稿)
   - `rule_set_id`(可选 form 字段,UUID 字符串,用于指定使用哪个规范集合,未提供时默认使用 Active_Rule_Set)
2. WHEN Sales_User 提交合规检查请求且参数校验通过,THE Compliance_Service SHALL 依次执行以下步骤:(a) 将 Contract_File 上传至 MinIO 并获得 `file_storage_key`;(b) 通过 Text_Extractor 从 Contract_File 抽取 Extracted_Contract_Text,若原始文本长度超过 100000 字符则截断到前 100000 字符并将 `text_truncated` 标记为 true,否则 `text_truncated` 为 false;(c) 创建一条 Compliance_Check_Result 记录,状态字段 `status` 初始为 `pending`;(d) 立即调用 AI_Service 执行合规检查。
3. WHEN AI_Service 完成合规检查并写回结果,THE Compliance_Service SHALL 在同一数据库事务中将对应 Compliance_Check_Result 的 `status` 字段更新为 `completed`,并持久化 `violations`(Violation_Item 数组)、`suggested_name`、`suggested_description`、`compliance_score`(0 至 100 的整数,详见 Requirement 4 第 13 条)、`completed_at` 字段。
4. WHEN Sales_User 未提供任何 Field_Draft(即 `number_draft`、`name_draft`、`description_draft` 三个字段全部为 null 或空字符串),THE Compliance_Service SHALL 仍然受理该请求,并允许 AI 仅基于 Extracted_Contract_Text 与 Compliance_Rule_Set(其中 `rule_type = 'file'` 的规则始终参与检查)产出 `suggested_name` 与 `suggested_description`,但 `violations` 数组中不应包含 `location` 为 `number` / `name` / `description` 中初稿为空那一类规则的违规项(具体行为见 Requirement 4 第 6 条至第 9 条)。
5. IF Sales_User 未提供 `rule_set_id` 且系统中不存在 Active_Rule_Set,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 409 错误,响应体说明系统当前未配置生效的合同规范集合,且不上传文件至 MinIO、不创建 Compliance_Check_Result 记录、不调用 AI_Service。
6. IF Sales_User 提供的 `rule_set_id` 在 `compliance_rule_sets` 表中不存在,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 404 错误,响应体说明规范集合不存在,且不上传文件至 MinIO、不创建 Compliance_Check_Result 记录、不调用 AI_Service。
7. IF Sales_User 提交的 `file` 缺失,或 MIME 类型不属于集合 `{'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}`,或文件大小超过 50 MB,或 `number_draft` 长度超过 100 字符,或 `name_draft` 长度超过 200 字符,或 `description_draft` 长度超过 2000 字符,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 422 错误,响应体说明触发限制的字段及其约束,且不上传文件至 MinIO、不创建 Compliance_Check_Result 记录、不调用 AI_Service。
8. IF Current_User 的 `role` 不在集合 `{'销售', '法务', '运营'}` 中,THEN THE Compliance_Service SHALL 拒绝该请求并返回 HTTP 403 错误,响应体包含权限不足说明,且不上传文件至 MinIO、不创建 Compliance_Check_Result 记录、不调用 AI_Service。
9. IF 请求中 JWT Token 缺失、格式无效或已过期,THEN THE Compliance_Service SHALL 返回 HTTP 401 错误,响应体包含认证失败说明。
10. WHEN Compliance_Service 创建 Compliance_Check_Result 记录,THE Compliance_Service SHALL 将 `requested_by`(Current_User 的用户 ID)、`rule_set_id`(实际使用的规范集合 ID)、`file_storage_key`(MinIO 中的存储 key)、`file_name`(原始文件名)、`file_size`(字节数)、`file_mime_type`、`extracted_text`(Extracted_Contract_Text,0 至 100000 字符)、`text_truncated`(布尔)、`number_draft`、`name_draft`、`description_draft`、`requested_at`(UTC 时间戳)持久化至 `compliance_check_results` 表;为空或未提供的 Field_Draft 字段统一持久化为 NULL。
11. WHEN Compliance_Service 完成请求体响应,THE Compliance_Service SHALL 在响应体中返回字段:`id`、`status`、`violations`(数组,详见 Requirement 4)、`suggested_name`、`suggested_description`、`compliance_score`(0 至 100 的整数,`status` 不为 `completed` 时为 null)、`requested_at`、`completed_at`、`text_truncated`(供前端在为 true 时展示「文件过长已截断,可能影响检查准确性」提示);响应体中 SHALL NOT 包含 `suggested_number` 字段(合同编号由后端发号器在销售点击「发起预审」时按现有规则生成,不在本接口产出)。
12. WHILE Sales_User 在 60 秒内对同一账户连续发起合规检查请求超过 10 次,THE Compliance_Service SHALL 对超过限额的请求返回 HTTP 429 错误,响应体说明请求频率超出限制,且不上传文件至 MinIO、不创建 Compliance_Check_Result 记录、不调用 AI_Service。
13. IF Text_Extractor 在抽取过程中抛出异常(例如文件损坏、加密 PDF、不支持的内嵌格式等),THEN THE Compliance_Service SHALL 在对应 Compliance_Check_Result 中将 `status` 字段更新为 `failed`、写入失败原因 `error_message = 'file_extraction_failed'`,并向调用方返回 HTTP 422 错误,响应体包含失败原因,且不再调用 AI_Service。
14. IF Text_Extractor 抽取出的纯文本在去除首尾空白后长度为 0(例如纯图片 PDF 等无可读文字情形),THEN THE Compliance_Service SHALL 在对应 Compliance_Check_Result 中将 `status` 字段更新为 `failed`、写入失败原因 `error_message = 'empty_extracted_text'`,并向调用方返回 HTTP 422 错误,响应体包含失败原因,且不再调用 AI_Service。
15. IF AI_Service 在 60 秒内未返回结果,THEN THE Compliance_Service SHALL 将对应 Compliance_Check_Result 的 `status` 字段更新为 `failed`、写入失败原因 `error_message = 'ai_timeout'`,并向调用方返回 HTTP 504 错误,响应体包含失败原因。
16. IF AI_Service 返回错误(含网络异常、模型 API 错误响应),THEN THE Compliance_Service SHALL 将对应 Compliance_Check_Result 的 `status` 字段更新为 `failed`、写入失败原因 `error_message`,并向调用方返回 HTTP 502 错误,响应体包含失败原因。

---

### Requirement 4: AI 执行合同合规检查并产出不符合项与字段建议

**User Story:** 作为销售,我希望 AI 基于管理员维护的合同规范、后端从合同文件抽取的纯文本与我提供的字段初稿,逐条比对并列出全部不符合项(包括对合同文件正文本身的合规审查),同时给出符合规范的合同名称与合同描述建议,以便我有针对性地修改合同文件或字段后再发起预审。

#### Acceptance Criteria

1. WHEN AI_Service 接收到 Compliance_Check_Request 与对应 Compliance_Rule_Set,THE AI_Service SHALL 通过 system prompt 显式向大语言模型传入:所有 Compliance_Rule 的 `id`、`rule_type`、`title`、`requirement`、`severity`,以及 `extracted_contract_text`(Extracted_Contract_Text)、`text_truncated`(布尔)、`number_draft`、`name_draft`、`description_draft`(为空的 Field_Draft 显式以 null 占位,使模型能够辨识缺省)。
2. WHEN AI_Service 调用大语言模型,THE AI_Service SHALL 通过 system prompt 要求模型以 JSON 结构返回结果,结构包含:
   - `violations`(数组,每项含 `rule_id`、`location`(取值为 `number` / `name` / `description` / `file`,必须与对应 Compliance_Rule 的 `rule_type` 一致)、`excerpt`(违反规则的原文片段,0 至 500 字符;当 `location` 为 `number` / `name` / `description` 时来自对应字段初稿,当 `location = 'file'` 时来自 Extracted_Contract_Text 的相关片段,允许为空字符串以指代「整个文件缺失某条款」)、`description`(违反描述,1 至 500 字符)、`suggestion`(修改建议,1 至 500 字符)、`severity`(取值为 `must` 或 `should`,需与对应 Compliance_Rule 的 `severity` 一致))
   - `suggested_name`(1 至 200 字符,符合 `Contract.name` 字段长度约束)
   - `suggested_description`(0 至 2000 字符,符合 `Contract.description` 字段长度约束;允许为空字符串)
   - 不包含 `suggested_number` 字段
3. WHEN AI_Service 收到模型返回的 JSON,THE AI_Service SHALL 校验 `violations` 数组中每条记录的 `rule_id` 是否存在于本次请求所传入的 Compliance_Rule_Set 的规则 ID 集合中,且 `location` 取值与该规则的 `rule_type` 一一一致;IF 某条记录的 `rule_id` 不在该集合中,或 `location` 与对应规则的 `rule_type` 不一致,THEN THE AI_Service SHALL 丢弃该条 Violation_Item,且不影响其余有效 Violation_Item 的持久化。
4. WHEN AI_Service 收到模型返回的 JSON,THE AI_Service SHALL 校验 `suggested_name` 长度为 1 至 200 字符、`suggested_description` 长度为 0 至 2000 字符;IF 任一字段超出长度上限,THEN THE AI_Service SHALL 对该字段执行截断(`suggested_name` 保留前 200 字符,`suggested_description` 保留前 2000 字符)后再持久化;IF `suggested_name` 长度为 0,THEN THE AI_Service SHALL 回退使用 `name_draft`(若非空)否则取 Extracted_Contract_Text 前 200 字符的去换行结果作为 `suggested_name`,以确保 `suggested_name` 满足 1 至 200 字符的强约束。
5. WHEN AI_Service 完成单次合规检查,THE AI_Service SHALL 持久化包含 0 至 N 条 Violation_Item 的 `violations`、`suggested_name`、`suggested_description`、`compliance_score` 至对应 Compliance_Check_Result 记录,并 SHALL NOT 写入 `suggested_number` 字段。
6. WHEN AI_Service 处理 `rule_type = 'number'` 的 Compliance_Rule,THE AI_Service SHALL 仅基于 `number_draft` 进行合规判断;IF `number_draft` 为 null 或空字符串,THEN THE AI_Service SHALL 跳过该类规则的违规项产出,即在 `violations` 中不输出 `location = 'number'` 的条目。
7. WHEN AI_Service 处理 `rule_type = 'name'` 的 Compliance_Rule 且 `name_draft` 非空,THE AI_Service SHALL 综合 `name_draft` 与 Extracted_Contract_Text 进行合规判断,违规项 `location` 取 `name`;WHEN AI_Service 处理 `rule_type = 'name'` 的 Compliance_Rule 且 `name_draft` 为 null 或空字符串,THE AI_Service SHALL 仅基于 Extracted_Contract_Text 产出 `suggested_name`,且 SHALL NOT 在 `violations` 中输出 `location = 'name'` 的条目。
8. WHEN AI_Service 处理 `rule_type = 'description'` 的 Compliance_Rule 且 `description_draft` 非空,THE AI_Service SHALL 综合 `description_draft` 与 Extracted_Contract_Text 进行合规判断,违规项 `location` 取 `description`;WHEN AI_Service 处理 `rule_type = 'description'` 的 Compliance_Rule 且 `description_draft` 为 null 或空字符串,THE AI_Service SHALL 仅基于 Extracted_Contract_Text 产出 `suggested_description`,且 SHALL NOT 在 `violations` 中输出 `location = 'description'` 的条目。
9. WHEN AI_Service 处理 `rule_type = 'file'` 的 Compliance_Rule,THE AI_Service SHALL 始终基于 Extracted_Contract_Text 进行合规判断,违规项 `location` 取 `file`,`excerpt` 来自 Extracted_Contract_Text 的相关片段(0 至 500 字符,允许为空字符串以指代「整个文件缺失某条款」),且 `rule_type = 'file'` 类规则的违规判断与三个 Field_Draft 是否为空无关。
10. IF Compliance_Rule_Set 中不存在任何 Compliance_Rule,THEN THE AI_Service SHALL 跳过模型调用,直接持久化空的 `violations` 数组,将 `suggested_name` 置为 `name_draft`(非空时)或 Extracted_Contract_Text 前 200 字符的去换行结果(空时),将 `suggested_description` 置为 `description_draft`(非空时)或空字符串(空时),并将 Compliance_Check_Result 的 `status` 字段更新为 `completed`。
11. IF 模型返回的内容无法解析为符合本 Requirement 第 2 条所述结构的 JSON,THEN THE AI_Service SHALL 重试一次;IF 第二次仍失败,THEN THE AI_Service SHALL 将对应 Compliance_Check_Result 的 `status` 字段更新为 `failed`、写入失败原因 `error_message = 'ai_invalid_response'`。
12. WHEN AI_Service 调用大语言模型,THE AI_Service SHALL 设置单次模型调用的最大等待时间为 60 秒;IF 超时,THEN THE AI_Service SHALL 抛出超时异常以触发 Requirement 3 第 15 条的处理逻辑。
13. WHEN AI_Service 完成 `violations` 的产出,THE AI_Service SHALL 计算 `compliance_score` 并持久化到对应 Compliance_Check_Result 记录;`compliance_score` 计算规则为:初始值 100,每条 `severity = 'must'` 的 Violation_Item 扣 10 分、每条 `severity = 'should'` 的 Violation_Item 扣 2 分,最终结果 SHALL 被裁剪到 `[0, 100]` 闭区间内;`violations` 为空数组时 `compliance_score` 等于 100;`status` 为 `failed` 时 `compliance_score` 字段持久化为 NULL。

---

### Requirement 5: 销售查看合规检查结果与历史

**User Story:** 作为销售,我希望查看 AI 给出的不符合项清单(含合同文件正文的违规项)与建议的合同名称、合同描述草案,并能够回看自己历史提交的合规检查记录,以便有据可查地完善预审表单字段与合同文件本身。

#### Acceptance Criteria

1. THE Compliance_Service SHALL 提供查询单条合规检查结果的接口 `GET /api/compliance/checks/{check_id}`,返回字段包含 `id`、`status`、`requested_by`(仅返回 `id`、`name`、`avatar`)、`rule_set_id`、`rule_set_name`、`file_name`、`file_size`、`file_mime_type`、`extracted_text`(Extracted_Contract_Text,0 至 100000 字符,用于辅助查看 violations 的上下文)、`text_truncated`、`number_draft`、`name_draft`、`description_draft`、`violations`(每项含 `rule_id`、`rule_title`、`rule_type`、`location`、`excerpt`、`description`、`suggestion`、`severity`)、`suggested_name`、`suggested_description`、`compliance_score`(0 至 100 的整数,`status` 不为 `completed` 时为 null)、`requested_at`、`completed_at`、`error_message`;响应体 SHALL NOT 包含 `suggested_number` 字段,SHALL NOT 包含 `contract_text` 字段(已被 `extracted_text` 取代)。
2. THE Compliance_Service SHALL 提供查询当前用户合规检查历史列表的接口 `GET /api/compliance/checks`,支持 `page`(默认 1)、`page_size`(默认 20,上限 100)、`status`(可选,取值为 `pending`、`completed`、`failed`)查询参数;返回结果按 `requested_at` 倒序排列,每条记录包含 `id`、`status`、`name_draft`、`rule_set_name`、`file_name`、`text_truncated`、`violation_count`(已完成的检查为 `violations` 数组长度,否则为 null)、`compliance_score`(0 至 100 的整数,`status` 不为 `completed` 时为 null)、`requested_at`、`completed_at`;列表接口响应体 SHALL NOT 包含 `contract_text` 字段。
3. WHEN Compliance_Check_Panel 加载合规检查结果,THE Compliance_Check_Panel SHALL 按 `severity` 优先(`must` 优先于 `should`)、`location` 次之(`number` 优先于 `name` 优先于 `description` 优先于 `file`)的顺序展示 `violations` 列表;每条 Violation_Item 渲染规则名称、严重程度标签(`must` 显示为红色「必须」、`should` 显示为黄色「建议」)、违反位置(以中文映射展示:`number` → 「合同编号」、`name` → 「合同名称」、`description` → 「合同描述」、`file` → 「合同文件」)、原文片段、违反描述、修改建议。
4. WHEN Compliance_Check_Panel 加载合规检查结果且 `status` 为 `completed`,THE Compliance_Check_Panel SHALL 在违规清单上方分两个独立区块展示 `suggested_name` 与 `suggested_description`,每个区块各自提供「复制到剪贴板」按钮,且 SHALL NOT 展示任何关于合同编号建议的区块或按钮;同时 SHALL 在页面顶部显著位置展示 `compliance_score`,以「合规评分:XX/100」的形式呈现,并在评分旁以颜色标签提示风险等级:`compliance_score >= 90` 显示绿色「优秀」、`compliance_score 70-89` 显示蓝色「良好」、`compliance_score 50-69` 显示黄色「待改进」、`compliance_score < 50` 显示红色「不合规」。
5. WHEN Compliance_Check_Panel 加载合规检查结果且 `text_truncated` 为 true,THE Compliance_Check_Panel SHALL 在页面上方展示「文件过长已截断,可能影响检查准确性」的提示。
6. WHEN Compliance_Check_Panel 加载合规检查结果且 `status` 为 `pending`,THE Compliance_Check_Panel SHALL 显示「AI 检查中」加载态,并每 2 秒轮询一次 `GET /api/compliance/checks/{check_id}` 直至 `status` 不为 `pending` 或累计轮询时长达到 90 秒。
7. WHEN Compliance_Check_Panel 加载合规检查结果且 `status` 为 `completed` 且 `violations` 为空数组,THE Compliance_Check_Panel SHALL 显示「未发现不符合项」提示,并仍展示 `suggested_name` 与 `suggested_description` 区块。
8. WHEN Compliance_Check_Panel 加载合规检查结果且 `status` 为 `failed`,THE Compliance_Check_Panel SHALL 展示 `error_message` 对应的错误提示文本(`file_extraction_failed` 显示为「合同文件解析失败,请确认文件未损坏且非加密文件」、`empty_extracted_text` 显示为「合同文件未抽取到可读文本(纯图片 PDF 暂不支持)」、`ai_timeout` 显示为「AI 检查超时,请稍后重试」、`ai_invalid_response` 显示为「AI 返回结果无法解析,请稍后重试」、其他取值显示为「AI 检查失败:{error_message}」),并提供「重新检查」按钮。
9. WHEN Sales_User 点击「重新检查」按钮,THE Compliance_Service SHALL 复用对应 Compliance_Check_Result 记录中已存的 `file_storage_key` 重新从 MinIO 拉取 Contract_File、重新执行 Text_Extractor 抽取文本、重新调用 AI_Service,并基于原 `number_draft` / `name_draft` / `description_draft` / `rule_set_id` 完成检查;IF 对应 `file_storage_key` 在 MinIO 中已过期或丢失,THEN THE Compliance_Service SHALL 返回 HTTP 410 错误,响应体说明合同文件已不可访问,需销售重新上传发起新的合规检查。
10. IF Current_User 不是该 Compliance_Check_Result 的 `requested_by`,且 `User.role` 不属于集合 `{'法务', '运营'}`,THEN THE Compliance_Service SHALL 拒绝 `GET /api/compliance/checks/{check_id}` 请求并返回 HTTP 403 错误,响应体包含权限不足说明。
11. IF 请求中的 `check_id` 在 `compliance_check_results` 表中不存在,THEN THE Compliance_Service SHALL 对查询接口返回 HTTP 404 错误,响应体说明检查记录不存在。
12. WHEN Current_User 调用 `GET /api/compliance/checks` 且 `User.role` 属于集合 `{'销售'}`,THE Compliance_Service SHALL 仅返回 `requested_by = Current_User.id` 的记录;WHEN Current_User 调用同一接口且 `User.role` 属于集合 `{'法务', '运营'}`,THE Compliance_Service SHALL 返回全部记录。

---

### Requirement 6: 独立访问与系统解耦

**User Story:** 作为系统使用者(销售 / 法务 / 运营),我希望「合同合规检查」功能拥有独立的前端路由、独立可分享的链接、独立的后端 API 前缀与独立的数据/存储空间,与现有「合同预审看板」功能保持解耦,以便销售直接通过链接访问检查结果而无需穿透合同列表/详情页,同时保证既有合同预审、评审、评论、通知功能不被本功能的新增内容破坏。

#### Acceptance Criteria

1. THE Compliance_Check_Panel SHALL 通过以下独立的前端路由路径对外提供访问:`/compliance`(我的合规检查列表页)、`/compliance/check/new`(新建合规检查页)、`/compliance/check/{check_id}`(合规检查结果页)、`/compliance/admin/rule-sets`(规则集合列表管理页)、`/compliance/admin/rule-sets/{rule_set_id}`(规则集合详情管理页);以上路径在前端路由表中独立注册,且 SHALL NOT 嵌入合同详情页或合同列表页的子路由之下。
2. WHEN Current_User 持有有效 JWT 直接访问 `/compliance/check/{check_id}`,THE Compliance_Check_Panel SHALL 直接调用 `GET /api/compliance/checks/{check_id}` 渲染该结果页,且 SHALL NOT 要求前置访问任何合同列表或合同详情页;IF Current_User 未登录(JWT 缺失或已过期),THEN THE Compliance_Check_Panel SHALL 跳转至现有钉钉登录流程,登录完成后回跳至原始 URL(沿用现有路由的登录回跳约定)。
3. THE 现有应用顶部导航或侧边栏 SHALL 新增一个一级入口,文案为「合规审查」,链接指向 `/compliance`;该入口对所有已登录用户可见。
4. WHEN Current_User 在「合规审查」入口下访问 `/compliance` 且 `User.role ∈ {'销售'}`,THE Compliance_Check_Panel SHALL 渲染「我的合规检查」列表(对应 `GET /api/compliance/checks` 的当前用户视图)与「新建合规检查」按钮;WHEN Current_User 访问 `/compliance` 且 `User.role ∈ {'法务', '运营'}`,THE Compliance_Check_Panel SHALL 在前述渲染基础上额外渲染「规则管理」入口(链接指向 `/compliance/admin/rule-sets`)与「全部合规检查」视图。
5. THE Compliance_Service 后端 SHALL 将本功能的 API 路径统一以 `/api/compliance/` 为前缀,且 SHALL NOT 在 `/api/contracts`、`/api/files`、`/api/reviews` 等已有路由模块中新增涉及 Compliance_Rule_Set / Compliance_Rule / Compliance_Check_Result 资源的端点。
6. THE Compliance_Service 后端 SHALL 将本功能的 SQLAlchemy 模型(`ComplianceRuleSet`、`ComplianceRule`、`ComplianceCheckResult`)放置于独立模块(建议路径 `backend/app/models/compliance.py`),且 SHALL NOT 在 `Contract`、`Attachment`、`Review`、`Comment`、`AISummary`、`Notification` 等现有 ORM 模型上新增列、外键或关系字段。
7. THE `compliance_check_results` 表 SHALL NOT 包含指向 `contracts` 表的外键(本阶段合规检查与已发起的合同记录不绑定);未来阶段如需绑定,通过新增可空外键列扩展(详见 Future Considerations)。
8. WHEN Compliance_Service 上传 Contract_File 至 MinIO,THE Compliance_Service SHALL 将文件存储到与现有附件 bucket 路径隔离的独立路径前缀(建议 `compliance/{user_id}/{check_id}/{filename}`),且 SHALL NOT 复用 `/api/contracts/{contract_id}/attachments` 上传接口或 `Attachment` 模型/`attachments` 表来落库本功能上传的文件。
9. IF 现有合同列表页与合同详情页的代码未因本功能改动,THEN 已交付的合同预审、评审、评论、通知功能 SHALL 保持现有行为不变(本验收项以解耦约束方式表达:本功能新增内容不应破坏既有功能的对外行为)。

---

## Out of Scope(本阶段明确不做)

- 销售在合规检查结果上原地编辑后再次确认提交(含将 AI 修改稿一键应用到合同草稿)。
- **合规检查通过后自动调用 `POST /api/contracts` 发起合同预审、自动选定评审人/抄送人**:第一阶段的定位是「检查 + 草稿」,销售仍需手动把 `suggested_name` / `suggested_description` 复制到预审表单后再点击「发起预审」按钮。
- **AI 生成 `suggested_number`(合同编号建议)**:合同编号由后端发号器在销售点击「发起预审」(`POST /api/contracts`)时按现有规则生成,本 Spec 接口与响应体均不产出 `suggested_number` 字段;AI 仅可对销售手填的 `number_draft` 进行格式与内容合规校验(产出 `location = 'number'` 的违规项)。
- 合规规则版本化(同一规则的多版本历史回溯)、规则导入/导出(如 Excel/JSON 批量导入)。
- **OCR(纯图片 PDF 不支持)**:Text_Extractor 仅做文本层抽取,纯图片 PDF / 扫描件直接返回 `error_message = 'empty_extracted_text'`(HTTP 422)。
- **加密 PDF / 受保护 docx**:对带密码或权限保护的文档,Text_Extractor 直接返回 `error_message = 'file_extraction_failed'`(HTTP 422)。
- **`.doc` / `.docx` 之外的 Office 格式**:不支持 `.rtf`、`.odt`、`.pages`、`.wps` 等格式,统一在 MIME 类型校验阶段返回 HTTP 422。
- 多语言合规规则(中英文混合规则的语义区分)。
- 实时流式输出 AI 检查结果(采用同步请求 + 轮询 / 短期等待模式即可)。
- 本阶段不在合同详情页内嵌「一键合规检查」入口,合规检查完全在 `/compliance` 子站完成,只在主导航上新增一个一级入口「合规审查」。

## Future Considerations(保留接口,避免堵死后续阶段)

- **第二阶段「确认修改并自动发起预审」**:本 Spec 在 `compliance_check_results` 表中保留 `suggested_name`、`suggested_description`、`file_storage_key` 字段并在 API 中返回;未来可在表上预留 `auto_initiated_attachment_id`(自动发起预审时复用本次合规检查的 MinIO 文件转为合同附件,避免销售再次上传)、`confirmed_at`(销售确认时间)、`auto_initiated_contract_id`(自动发起的合同 ID)等扩展字段,以及一个 `POST /api/compliance/checks/{check_id}/confirm-and-initiate` 端点而无需破坏现有结构。该端点在二阶段会在内部调用 `POST /api/contracts`,由后端发号器为合同分配 `contract_number`,与第一阶段「AI 不生成合同编号」的边界保持一致。
- 后续可在 `compliance_rule_sets` 表上扩展 `version`、`parent_id` 字段以支持版本化与回滚。
- 后续可在 Text_Extractor 上叠加 OCR 管线(如腾讯云 OCR 或本地 PaddleOCR),以支持纯图片 PDF / 扫描件的合规检查。
