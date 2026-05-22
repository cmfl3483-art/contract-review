import { useQuery } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { queryKeys } from '../config/queryClient';
import type { ApiResponse, User } from '../types';

/**
 * 获取当前用户信息
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.user.current(),
    queryFn: async () => {
      const response = await axios.get<ApiResponse<{ user: User }>>(
        `${API_BASE_URL}${API_ENDPOINTS.AUTH.ME}`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取用户信息失败');
      }

      return response.data.data!.user;
    },
    // 用户信息在整个会话期间被认为是新鲜的
    staleTime: Infinity,
    // 失败时重试3次
    retry: 3,
  });
}

/**
 * 获取钉钉登录URL
 */
export async function getDingTalkLoginUrl(): Promise<string> {
  const response = await axios.get<ApiResponse<{ authUrl: string }>>(
    `${API_BASE_URL}${API_ENDPOINTS.AUTH.LOGIN}`
  );

  if (!response.data.success) {
    throw new Error(response.data.error || '获取登录URL失败');
  }

  return response.data.data!.authUrl;
}
