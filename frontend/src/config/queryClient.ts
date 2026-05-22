import { QueryClient } from '@tanstack/react-query';

/**
 * React Query 配置
 *
 * 缓存策略:
 * - staleTime: 数据被认为是新鲜的时间,在此期间不会重新获取
 * - gcTime: 未使用的数据在缓存中保留的时间
 * - refetchOnWindowFocus: 窗口重新获得焦点时是否重新获取数据
 * - refetchOnReconnect: 网络重新连接时是否重新获取数据
 * - retry: 失败后的重试次数
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 数据在5分钟内被认为是新鲜的
      staleTime: 5 * 60 * 1000,
      // 未使用的数据在10分钟后被垃圾回收
      gcTime: 10 * 60 * 1000,
      // 窗口重新获得焦点时重新获取数据
      refetchOnWindowFocus: true,
      // 网络重新连接时重新获取数据
      refetchOnReconnect: true,
      // 失败后重试1次
      retry: 1,
      // 重试延迟
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      // 失败后重试1次
      retry: 1,
    },
  },
});

/**
 * Query Keys 常量
 * 用于标识不同的查询,便于缓存管理和失效
 */
export const queryKeys = {
  // 合同相关
  contracts: {
    all: ['contracts'] as const,
    lists: () => [...queryKeys.contracts.all, 'list'] as const,
    list: (filter: string, search: string) =>
      [...queryKeys.contracts.lists(), { filter, search }] as const,
    details: () => [...queryKeys.contracts.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.contracts.details(), id] as const,
  },
  // 评审相关
  reviews: {
    all: ['reviews'] as const,
    lists: () => [...queryKeys.reviews.all, 'list'] as const,
    list: (contractId: string) => [...queryKeys.reviews.lists(), contractId] as const,
  },
  // 待办数量
  pending: {
    all: ['pending'] as const,
    count: () => [...queryKeys.pending.all, 'count'] as const,
  },
  // 用户相关
  user: {
    all: ['user'] as const,
    current: () => [...queryKeys.user.all, 'current'] as const,
  },
  // AI相关
  ai: {
    all: ['ai'] as const,
    summary: (contractId: string) => [...queryKeys.ai.all, 'summary', contractId] as const,
  },
};
