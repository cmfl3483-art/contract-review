/**
 * 合规检查相关 TanStack Query hooks
 * Compliance check related TanStack Query hooks
 *
 * 所有请求使用 frontend/src/utils/axios 实例（steering 约定 #1）
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '../utils/axios';
import type {
  RuleSet,
  RuleSetDetail,
  Rule,
  ComplianceCheckResult,
  ComplianceCheckListResponse,
  CreateRuleSetDto,
  UpdateRuleSetDto,
  CreateRuleDto,
  UpdateRuleDto,
  ListChecksParams,
  ImportPreviewResponse,
  ImportConfirmResponse,
} from '../types/compliance';

// ─────────────────────────────────────────────
// Query Keys
// ─────────────────────────────────────────────

export const complianceKeys = {
  all: ['compliance'] as const,
  ruleSets: () => [...complianceKeys.all, 'rule-sets'] as const,
  ruleSet: (id: string) => [...complianceKeys.ruleSets(), id] as const,
  rules: (ruleSetId: string) =>
    [...complianceKeys.all, 'rules', ruleSetId] as const,
  checks: (params?: ListChecksParams) =>
    [...complianceKeys.all, 'checks', params] as const,
  check: (id: string) => [...complianceKeys.all, 'check', id] as const,
};

// ─────────────────────────────────────────────
// API helpers
// ─────────────────────────────────────────────

async function unwrap<T>(promise: Promise<{ data: { success: boolean; data: T } }>): Promise<T> {
  const res = await promise;
  return res.data.data;
}

// ─────────────────────────────────────────────
// Rule Set hooks
// ─────────────────────────────────────────────

/** 获取规则集合列表 */
export function useRuleSets() {
  return useQuery({
    queryKey: complianceKeys.ruleSets(),
    queryFn: () =>
      unwrap<{ rule_sets: RuleSet[] }>(
        axiosInstance.get('/api/compliance/rule-sets')
      ).then((d) => d.rule_sets),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });
}

/** 获取单个规则集合详情（含规则列表） */
export function useRuleSet(ruleSetId: string) {
  return useQuery({
    queryKey: complianceKeys.ruleSet(ruleSetId),
    queryFn: () =>
      unwrap<{ rule_set: RuleSetDetail }>(
        axiosInstance.get(`/api/compliance/rule-sets/${ruleSetId}`)
      ).then((d) => d.rule_set),
    enabled: !!ruleSetId,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });
}

/** 创建规则集合 */
export function useCreateRuleSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (dto: CreateRuleSetDto) =>
      unwrap<RuleSet>(axiosInstance.post('/api/compliance/rule-sets', dto)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complianceKeys.ruleSets() });
    },
  });
}

/** 更新规则集合 */
export function useUpdateRuleSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...dto }: UpdateRuleSetDto & { id: string }) =>
      unwrap<RuleSet>(
        axiosInstance.put(`/api/compliance/rule-sets/${id}`, dto)
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: complianceKeys.ruleSets() });
      queryClient.invalidateQueries({
        queryKey: complianceKeys.ruleSet(variables.id),
      });
    },
  });
}

/** 删除规则集合 */
export function useDeleteRuleSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      axiosInstance.delete(`/api/compliance/rule-sets/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complianceKeys.ruleSets() });
    },
  });
}

// ─────────────────────────────────────────────
// Rule hooks
// ─────────────────────────────────────────────

/** 获取规则列表 */
export function useRules(ruleSetId: string) {
  return useQuery({
    queryKey: complianceKeys.rules(ruleSetId),
    queryFn: () =>
      unwrap<{ rules: Rule[] }>(
        axiosInstance.get(`/api/compliance/rule-sets/${ruleSetId}/rules`)
      ).then((d) => d.rules),
    enabled: !!ruleSetId,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });
}

/** 创建规则 */
export function useCreateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ rule_set_id, ...dto }: CreateRuleDto) =>
      unwrap<Rule>(
        axiosInstance.post(
          `/api/compliance/rule-sets/${rule_set_id}/rules`,
          dto
        )
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: complianceKeys.rules(variables.rule_set_id),
      });
      queryClient.invalidateQueries({ queryKey: complianceKeys.ruleSets() });
    },
  });
}

/** 更新规则 */
export function useUpdateRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ rule_id, ...dto }: UpdateRuleDto) =>
      unwrap<Rule>(
        axiosInstance.put(`/api/compliance/rules/${rule_id}`, dto)
      ),
    onSuccess: () => {
      // 规则更新后使所有规则集合的规则缓存失效
      queryClient.invalidateQueries({
        queryKey: [...complianceKeys.all, 'rules'],
      });
      queryClient.invalidateQueries({ queryKey: complianceKeys.ruleSets() });
    },
  });
}

/** 删除规则 */
export function useDeleteRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ rule_id, rule_set_id }: { rule_id: string; rule_set_id: string }) =>
      axiosInstance.delete(`/api/compliance/rules/${rule_id}`).then(() => rule_set_id),
    onSuccess: (rule_set_id) => {
      queryClient.invalidateQueries({
        queryKey: complianceKeys.rules(rule_set_id),
      });
      queryClient.invalidateQueries({ queryKey: complianceKeys.ruleSets() });
    },
  });
}

// ─────────────────────────────────────────────
// Check hooks
// ─────────────────────────────────────────────

/** 获取合规检查历史列表 */
export function useComplianceChecks(params: ListChecksParams = {}) {
  return useQuery({
    queryKey: complianceKeys.checks(params),
    queryFn: () =>
      unwrap<ComplianceCheckListResponse>(
        axiosInstance.get('/api/compliance/checks', { params })
      ),
    staleTime: 30 * 1000, // 30s，检查列表变化较频繁
    gcTime: 5 * 60 * 1000,
  });
}

/** 获取单条合规检查结果 */
export function useComplianceCheck(checkId: string) {
  return useQuery({
    queryKey: complianceKeys.check(checkId),
    queryFn: () =>
      unwrap<ComplianceCheckResult>(
        axiosInstance.get(`/api/compliance/checks/${checkId}`)
      ),
    enabled: !!checkId,
    staleTime: 0, // 检查结果不缓存，每次都重新获取
    gcTime: 5 * 60 * 1000,
  });
}

/** 发起合规检查（multipart/form-data） */
export function useCreateComplianceCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) =>
      unwrap<ComplianceCheckResult>(
        axiosInstance.post('/api/compliance/checks', formData)
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: complianceKeys.checks(),
      });
    },
  });
}

/** 重新检查 */
export function useRecheckCompliance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (checkId: string) =>
      unwrap<ComplianceCheckResult>(
        axiosInstance.post(`/api/compliance/checks/${checkId}/recheck`)
      ),
    onSuccess: (_data, checkId) => {
      queryClient.invalidateQueries({
        queryKey: complianceKeys.check(checkId),
      });
      queryClient.invalidateQueries({
        queryKey: complianceKeys.checks(),
      });
    },
  });
}

// ─────────────────────────────────────────────
// 轮询 hook (R5.6)
// ─────────────────────────────────────────────

/**
 * 合规检查结果轮询 hook
 *
 * - status === 'pending' 时每 2 秒轮询一次
 * - status !== 'pending' 时停止轮询（refetchInterval 返回 false）
 * - enabled=false 时停止轮询（Detail 页面在累计 90s 后置 false）
 *
 * Property 16: 轮询自动停止 / Validates: Requirements 5.6
 */
export function useComplianceCheckPolling(checkId: string, enabled: boolean) {
  return useQuery({
    queryKey: complianceKeys.check(checkId),
    queryFn: () =>
      unwrap<ComplianceCheckResult>(
        axiosInstance.get(`/api/compliance/checks/${checkId}`)
      ),
    enabled: enabled && !!checkId,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === 'pending' ? 2000 : false;
    },
    refetchIntervalInBackground: false,
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
  });
}

// ─────────────────────────────────────────────
// Excel 批量导入 hooks（追加到文件末尾）
// ─────────────────────────────────────────────

/**
 * 下载 Excel 模板（blob 下载，遵循 steering 约定 #9）
 * 不使用 useMutation，直接返回触发函数，由组件调用
 */
export function useDownloadRulesTemplate() {
  return async (ruleSetId: string): Promise<void> => {
    const response = await axiosInstance.get(
      `/api/compliance/rule-sets/${ruleSetId}/rules/template`,
      { responseType: 'blob' }
    );
    const url = URL.createObjectURL(new Blob([response.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'compliance_rules_template.xlsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
}

/**
 * 上传 Excel 并获取解析预览
 */
export function useImportRulesPreview() {
  return useMutation({
    mutationFn: ({
      ruleSetId,
      file,
    }: {
      ruleSetId: string;
      file: File;
    }): Promise<ImportPreviewResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      return unwrap<ImportPreviewResponse>(
        axiosInstance.post(
          `/api/compliance/rule-sets/${ruleSetId}/rules/import/preview`,
          formData
        )
      );
    },
  });
}

/**
 * 确认导入并批量写入规则
 */
export function useImportRulesConfirm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      ruleSetId,
      previewSessionToken,
    }: {
      ruleSetId: string;
      previewSessionToken: string;
    }): Promise<ImportConfirmResponse> =>
      unwrap<ImportConfirmResponse>(
        axiosInstance.post(
          `/api/compliance/rule-sets/${ruleSetId}/rules/import/confirm`,
          { preview_session_token: previewSessionToken }
        )
      ),
    onSuccess: (_data, variables) => {
      // 刷新规则列表（使 TanStack Query 对应 queryKey 失效）
      queryClient.invalidateQueries({
        queryKey: complianceKeys.rules(variables.ruleSetId),
      });
      queryClient.invalidateQueries({
        queryKey: complianceKeys.ruleSets(),
      });
    },
  });
}
