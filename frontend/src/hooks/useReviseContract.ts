import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL } from '../config/api';
import { queryKeys } from '../config/queryClient';
import type { ApiResponse, Contract } from '../types';

interface ReviseContractInput {
  name?: string;
  contract_number?: string;
  description?: string;
}

/**
 * 修改合同的标题或描述（仅发起人可用）。
 * 成功后会触发后端的重审流程：所有评审人 review.status 重置为 pending。
 *
 * @param contractId - 合同 ID
 */
export function useReviseContract(contractId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ReviseContractInput) => {
      const response = await axios.patch<ApiResponse<{ contract: Contract }>>(
        `${API_BASE_URL}/api/contracts/${contractId}`,
        data
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '修改合同失败');
      }

      return response.data.data!.contract;
    },
    onSuccess: () => {
      // 重审后多个数据源失效
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.detail(contractId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.reviews.list(contractId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });
    },
  });
}
