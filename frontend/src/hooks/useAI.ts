import { useQuery, useMutation } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { queryKeys } from '../config/queryClient';
import type { ApiResponse, AISummary } from '../types';

/**
 * 获取AI智能总结
 *
 * @param contractId - 合同ID
 */
export function useAISummary(contractId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.ai.summary(contractId || ''),
    queryFn: async () => {
      if (!contractId) {
        throw new Error('合同ID不能为空');
      }

      const response = await axios.post<ApiResponse<{ summary: AISummary }>>(
        `${API_BASE_URL}${API_ENDPOINTS.AI.SUMMARY(contractId)}`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取AI总结失败');
      }

      return response.data.data!.summary;
    },
    // 只有当contractId存在时才执行查询
    enabled: !!contractId,
    // AI总结数据在30分钟内被认为是新鲜的
    staleTime: 30 * 60 * 1000,
    // 失败时不重试(AI服务可能不可用)
    retry: false,
  });
}

/**
 * AI顾问问答
 */
export function useAIAdvisor() {
  return useMutation({
    mutationFn: async ({ contractId, question }: { contractId: string; question: string }) => {
      const response = await axios.post<ApiResponse<{ answer: string }>>(
        `${API_BASE_URL}${API_ENDPOINTS.AI.ADVISOR}`,
        { contract_id: contractId, question }  // 使用 contract_id 而不是 contractId
      );

      if (!response.data.success) {
        throw new Error(response.data.error || 'AI顾问服务失败');
      }

      return response.data.data!.answer;
    },
    // 失败时不重试(AI服务可能不可用)
    retry: false,
  });
}
