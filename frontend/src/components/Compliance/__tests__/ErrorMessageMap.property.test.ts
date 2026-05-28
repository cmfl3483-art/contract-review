/**
 * Property 15: 错误文案 fallback 完备
 * Validates: Requirements 5.8
 *
 * 对任意字符串输入，getComplianceErrorText 必须返回非空中文字符串。
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { getComplianceErrorText } from '../ErrorMessageMap';

describe('Property 15: 错误文案 fallback 完备', () => {
  it('任意字符串输入都返回非空中文字符串', () => {
    fc.assert(
      fc.property(fc.string(), (errorMessage) => {
        const result = getComplianceErrorText(errorMessage);
        expect(result).toBeTruthy();
        expect(typeof result).toBe('string');
        expect(result.length).toBeGreaterThan(0);
      })
    );
  });

  it('null 输入返回 AI 检查失败', () => {
    expect(getComplianceErrorText(null)).toBe('AI 检查失败');
  });

  it('undefined 输入返回 AI 检查失败', () => {
    expect(getComplianceErrorText(undefined)).toBe('AI 检查失败');
  });

  it('空字符串输入返回 AI 检查失败', () => {
    expect(getComplianceErrorText('')).toBe('AI 检查失败');
  });

  it('已知 key 返回对应中文文案', () => {
    expect(getComplianceErrorText('file_extraction_failed')).toContain('解析失败');
    expect(getComplianceErrorText('empty_extracted_text')).toContain('未抽取到');
    expect(getComplianceErrorText('ai_timeout')).toContain('超时');
    expect(getComplianceErrorText('ai_invalid_response')).toContain('无法解析');
  });

  it('未知 key 返回 AI 检查失败:{key}', () => {
    const unknownKey = 'some_unknown_error_code';
    const result = getComplianceErrorText(unknownKey);
    expect(result).toContain('AI 检查失败');
    expect(result).toContain(unknownKey);
  });
});
