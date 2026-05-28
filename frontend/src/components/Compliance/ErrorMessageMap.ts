/**
 * 合规检查错误文案映射
 * Compliance check error message mapping
 *
 * 对应 Requirement 5.8
 */

export const COMPLIANCE_ERROR_MESSAGES: Record<string, string> = {
  file_extraction_failed: '合同文件解析失败，请确认文件未损坏且非加密文件',
  empty_extracted_text: '合同文件未抽取到可读文本（纯图片 PDF 暂不支持）',
  ai_timeout: 'AI 检查超时，请稍后重试',
  ai_invalid_response: 'AI 返回结果无法解析，请稍后重试',
};

/**
 * 获取合规检查错误的中文文案
 *
 * - 已知 key → 映射表中的文案
 * - 未知 key → `AI 检查失败:{errorMessage}`
 * - 空值/null/undefined → `AI 检查失败`
 *
 * Property 15: 对任意输入都返回非空中文字符串
 */
export function getComplianceErrorText(
  errorMessage: string | null | undefined
): string {
  if (!errorMessage) return 'AI 检查失败';
  return COMPLIANCE_ERROR_MESSAGES[errorMessage] ?? `AI 检查失败：${errorMessage}`;
}
