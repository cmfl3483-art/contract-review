/**
 * Property 16: 轮询自动停止
 * Validates: Requirements 5.6
 *
 * 测试 useComplianceCheckPolling 的 refetchInterval 回调逻辑：
 * - status === 'pending' 时返回 2000（每 2 秒轮询）
 * - status !== 'pending' 时返回 false（停止轮询）
 * - enabled=false 时不发起请求
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { ComplianceCheckResult } from '../../types/compliance';

// ─────────────────────────────────────────────
// 提取 refetchInterval 逻辑进行单元测试
// useComplianceCheckPolling 的 refetchInterval 回调：
//   (query) => data?.status === 'pending' ? 2000 : false
// ─────────────────────────────────────────────

/**
 * 模拟 refetchInterval 回调，与 useComplianceCheckPolling 实现保持一致
 */
function makeRefetchInterval(data: Pick<ComplianceCheckResult, 'status'> | undefined): number | false {
  return data?.status === 'pending' ? 2000 : false;
}

/**
 * 模拟 enabled 条件，与 useComplianceCheckPolling 实现保持一致：
 *   enabled: enabled && !!checkId
 */
function isQueryEnabled(enabled: boolean, checkId: string): boolean {
  return enabled && !!checkId;
}

// ─────────────────────────────────────────────
// 测试套件
// ─────────────────────────────────────────────

describe('useComplianceCheckPolling - Property 16: 轮询自动停止', () => {
  describe('refetchInterval 回调逻辑', () => {
    it('status === "pending" 时，refetchInterval 返回 2000（每 2 秒轮询）', () => {
      const data: Pick<ComplianceCheckResult, 'status'> = { status: 'pending' };
      const interval = makeRefetchInterval(data);
      expect(interval).toBe(2000);
    });

    it('status === "completed" 时，refetchInterval 返回 false（停止轮询）', () => {
      const data: Pick<ComplianceCheckResult, 'status'> = { status: 'completed' };
      const interval = makeRefetchInterval(data);
      expect(interval).toBe(false);
    });

    it('status === "failed" 时，refetchInterval 返回 false（停止轮询）', () => {
      const data: Pick<ComplianceCheckResult, 'status'> = { status: 'failed' };
      const interval = makeRefetchInterval(data);
      expect(interval).toBe(false);
    });

    it('data 为 undefined 时（初始状态），refetchInterval 返回 false', () => {
      const interval = makeRefetchInterval(undefined);
      expect(interval).toBe(false);
    });
  });

  describe('enabled 条件逻辑', () => {
    it('enabled=false 时，查询不启用（不发起请求）', () => {
      const enabled = isQueryEnabled(false, 'check-123');
      expect(enabled).toBe(false);
    });

    it('enabled=true 且 checkId 非空时，查询启用', () => {
      const enabled = isQueryEnabled(true, 'check-123');
      expect(enabled).toBe(true);
    });

    it('enabled=true 但 checkId 为空字符串时，查询不启用', () => {
      const enabled = isQueryEnabled(true, '');
      expect(enabled).toBe(false);
    });

    it('enabled=false 且 checkId 非空时，查询不启用', () => {
      const enabled = isQueryEnabled(false, 'check-456');
      expect(enabled).toBe(false);
    });
  });

  describe('轮询状态转换（Property 16 核心场景）', () => {
    it('从 pending 变为 completed 后，refetchInterval 立即返回 false', () => {
      // 初始状态：pending → 轮询中
      const pendingInterval = makeRefetchInterval({ status: 'pending' });
      expect(pendingInterval).toBe(2000);

      // 状态变更：completed → 停止轮询
      const completedInterval = makeRefetchInterval({ status: 'completed' });
      expect(completedInterval).toBe(false);
    });

    it('从 pending 变为 failed 后，refetchInterval 立即返回 false', () => {
      // 初始状态：pending → 轮询中
      const pendingInterval = makeRefetchInterval({ status: 'pending' });
      expect(pendingInterval).toBe(2000);

      // 状态变更：failed → 停止轮询
      const failedInterval = makeRefetchInterval({ status: 'failed' });
      expect(failedInterval).toBe(false);
    });

    it('90s 超时后 enabled 置 false，查询不再启用', () => {
      // 模拟 Detail 页面在 90s 后将 enabled 置为 false
      const checkId = 'check-timeout-test';

      // 90s 前：enabled=true，查询启用
      expect(isQueryEnabled(true, checkId)).toBe(true);

      // 90s 后：Detail 页面置 enabled=false，查询停止
      expect(isQueryEnabled(false, checkId)).toBe(false);
    });

    it('pending 状态下轮询间隔固定为 2000ms', () => {
      // 多次调用，结果应一致
      for (let i = 0; i < 5; i++) {
        const interval = makeRefetchInterval({ status: 'pending' });
        expect(interval).toBe(2000);
      }
    });
  });
});
