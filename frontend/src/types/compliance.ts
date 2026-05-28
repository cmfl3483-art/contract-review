/**
 * 合规检查相关类型定义
 * Compliance check related TypeScript types
 */

// ─────────────────────────────────────────────
// 枚举字面量联合类型
// ─────────────────────────────────────────────

export type RuleType = 'number' | 'name' | 'description' | 'file';

export type RuleSeverity = 'must' | 'should';

export type ComplianceCheckStatus = 'pending' | 'completed' | 'failed';

// ─────────────────────────────────────────────
// 规则集合 (Rule Set)
// ─────────────────────────────────────────────

export interface RuleSet {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  rule_count: number;
  created_at: string;
  updated_at: string;
}

export interface RuleSetDetail extends RuleSet {
  rules: Rule[];
}

export interface CreateRuleSetDto {
  name: string;
  description?: string;
  is_active?: boolean;
}

export interface UpdateRuleSetDto {
  name?: string;
  description?: string;
  is_active?: boolean;
}

// ─────────────────────────────────────────────
// 规则 (Rule)
// ─────────────────────────────────────────────

export interface Rule {
  id: string;
  rule_set_id: string;
  rule_type: RuleType;
  title: string;
  requirement: string;
  severity: RuleSeverity;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface CreateRuleDto {
  rule_set_id: string;
  rule_type: RuleType;
  title: string;
  requirement: string;
  severity?: RuleSeverity;
  order?: number;
}

export interface UpdateRuleDto {
  rule_id: string;
  rule_type?: RuleType;
  title?: string;
  requirement?: string;
  severity?: RuleSeverity;
  order?: number;
}

// ─────────────────────────────────────────────
// 违规项 (Violation)
// ─────────────────────────────────────────────

export interface Violation {
  rule_id: string;
  rule_title: string;
  rule_type: RuleType;
  location: RuleType;
  excerpt: string;
  description: string;
  suggestion: string;
  severity: RuleSeverity;
}

// ─────────────────────────────────────────────
// 合规检查结果 (Check Result)
// ─────────────────────────────────────────────

export interface UserBrief {
  id: string;
  name: string;
  avatar: string | null;
}

export interface ComplianceCheckResult {
  id: string;
  status: ComplianceCheckStatus;
  requested_by: UserBrief;
  rule_set_id: string | null;
  rule_set_name: string | null;
  file_name: string;
  file_size: number;
  file_mime_type: string;
  extracted_text: string;
  text_truncated: boolean;
  number_draft: string | null;
  name_draft: string | null;
  description_draft: string | null;
  violations: Violation[];
  suggested_name: string | null;
  suggested_description: string | null;
  compliance_score: number | null; // 0..100, status !== 'completed' 时为 null
  requested_at: string;
  completed_at: string | null;
  error_message: string | null;
  // 注意: 不包含 suggested_number / contract_text 字段
}

export interface ComplianceCheckSummary {
  id: string;
  status: ComplianceCheckStatus;
  name_draft: string | null;
  rule_set_name: string | null;
  file_name: string;
  text_truncated: boolean;
  violation_count: number | null; // 仅 completed 才有
  compliance_score: number | null; // 0..100, status !== 'completed' 时为 null
  requested_at: string;
  completed_at: string | null;
}

export interface ComplianceCheckListResponse {
  items: ComplianceCheckSummary[];
  total: number;
  page: number;
  page_size: number;
}

// ─────────────────────────────────────────────
// 查询参数
// ─────────────────────────────────────────────

export interface ListChecksParams {
  page?: number;
  page_size?: number;
  status?: ComplianceCheckStatus;
}

// ─────────────────────────────────────────────
// Excel 批量导入相关类型
// ─────────────────────────────────────────────

/** 预览接口返回的单条规则（含 Excel 行号） */
export interface ImportPreviewRule {
  row_number: number;
  rule_type: RuleType;
  title: string;
  requirement: string;
  severity: RuleSeverity;
  order: number;
}

/** 预览接口响应 */
export interface ImportPreviewResponse {
  preview_session_token: string;
  rules: ImportPreviewRule[];
  total_count: number;
}

/** 确认导入接口响应 */
export interface ImportConfirmResponse {
  imported_count: number;
  rule_set_id: string;
}

/** 行级校验错误 */
export interface ImportRowError {
  row_number: number;
  field: string;
  message: string;
}

/** 422 校验失败响应体 detail */
export interface ImportValidationError {
  code: string;
  message: string;
  errors?: ImportRowError[];
  current_count?: number;
  import_count?: number;
  limit?: number;
}
