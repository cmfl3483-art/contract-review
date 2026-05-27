import { useQuery } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL } from '../config/api';
import type { ApiResponse, MentionableUser } from '../types';

/**
 * 获取某合同的 @ 提及候选人列表。
 * 候选范围：合同发起人 + 评审人 + 抄送人（去重）。
 *
 * @param contractId - 合同 ID
 * @param search - 搜索关键词（可选；空字符串或未提供时返回完整并集）
 */
export function useMentionableUsers(contractId: string, search?: string) {
  const trimmedSearch = (search ?? '').trim();

  return useQuery({
    queryKey: ['mentionable-users', contractId, trimmedSearch],
    queryFn: async () => {
      const response = await axios.get<ApiResponse<{ users: MentionableUser[] }>>(
        `${API_BASE_URL}/api/contracts/${contractId}/mentionable-users`,
        {
          params: trimmedSearch ? { search: trimmedSearch } : {},
          timeout: 5000,
        }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取候选人列表失败');
      }

      return response.data.data?.users ?? [];
    },
    enabled: !!contractId,
    retry: false,
    staleTime: 30 * 1000,
  });
}
