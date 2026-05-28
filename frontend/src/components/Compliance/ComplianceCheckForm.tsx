import React, { useRef, useState } from 'react';
import { Form, Input, Button, message, Upload } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd';
import { useCreateComplianceCheck } from '../../hooks/useCompliance';
import RuleSetSelector from './RuleSetSelector';

const { TextArea } = Input;

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_ACCEPT = '.pdf,.doc,.docx';

interface ComplianceCheckFormProps {
  onSuccess?: (checkId: string) => void;
}

const ComplianceCheckForm: React.FC<ComplianceCheckFormProps> = ({ onSuccess }) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const createCheck = useCreateComplianceCheck();

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (fileList.length === 0) {
        message.error('请上传合同文件');
        return;
      }

      const file = fileList[0].originFileObj;
      if (!file) {
        message.error('文件无效，请重新选择');
        return;
      }

      const formData = new FormData();
      formData.append('file', file, file.name);
      if (values.number_draft) formData.append('number_draft', values.number_draft);
      if (values.name_draft) formData.append('name_draft', values.name_draft);
      if (values.description_draft) formData.append('description_draft', values.description_draft);
      if (values.rule_set_id) formData.append('rule_set_id', values.rule_set_id);

      const result = await createCheck.mutateAsync(formData);
      message.success('合规检查已提交');
      form.resetFields();
      setFileList([]);
      onSuccess?.(result.id);
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) return;
      const msg = error instanceof Error ? error.message : '提交失败，请稍后重试';
      message.error(msg);
    }
  };

  return (
    <Form form={form} layout="vertical" autoComplete="off">
      {/* 合同文件上传 */}
      <Form.Item label="合同文件" required>
        <Upload
          accept={ALLOWED_ACCEPT}
          maxCount={1}
          fileList={fileList}
          beforeUpload={(file) => {
            const ext = file.name.split('.').pop()?.toLowerCase();
            const allowed = ['pdf', 'doc', 'docx'];
            if (!allowed.includes(ext ?? '')) {
              message.error('仅支持 PDF、DOC、DOCX 格式');
              return Upload.LIST_IGNORE;
            }
            if (file.size > MAX_FILE_SIZE) {
              message.error('文件大小不能超过 50MB');
              return Upload.LIST_IGNORE;
            }
            return false; // 阻止自动上传，手动提交时处理
          }}
          onChange={({ fileList: newList }) => setFileList(newList)}
        >
          <Button icon={<UploadOutlined />}>选择文件</Button>
          <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
            支持 PDF、DOC、DOCX，不超过 50MB
          </span>
        </Upload>
      </Form.Item>

      {/* 规则集合选择 */}
      <Form.Item
        label="规则集合"
        name="rule_set_id"
        rules={[{ required: true, message: '请选择规则集合' }]}
      >
        <RuleSetSelector />
      </Form.Item>

      {/* 合同编号初稿 */}
      <Form.Item
        label="合同编号初稿"
        name="number_draft"
        rules={[{ max: 100, message: '合同编号不能超过 100 个字符' }]}
      >
        <Input
          placeholder="请输入合同编号初稿（可选）"
          maxLength={100}
          showCount
        />
      </Form.Item>

      {/* 合同名称初稿 */}
      <Form.Item
        label="合同名称初稿"
        name="name_draft"
        rules={[{ max: 200, message: '合同名称不能超过 200 个字符' }]}
      >
        <TextArea
          placeholder="请输入合同名称初稿（可选）"
          maxLength={200}
          showCount
          rows={2}
        />
      </Form.Item>

      {/* 合同描述初稿 */}
      <Form.Item
        label="合同描述初稿"
        name="description_draft"
        rules={[{ max: 2000, message: '合同描述不能超过 2000 个字符' }]}
      >
        <TextArea
          placeholder="请输入合同描述初稿（可选）"
          maxLength={2000}
          showCount
          rows={5}
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          onClick={handleSubmit}
          loading={createCheck.isPending}
        >
          提交合规检查
        </Button>
      </Form.Item>
    </Form>
  );
};

export default ComplianceCheckForm;
