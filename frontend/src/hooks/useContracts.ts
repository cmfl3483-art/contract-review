import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { queryKeys } from '../config/queryClient';
import type {
  ApiResponse,
  ContractListResponse,
  ContractDetailResponse,
  ContractFormData,
  FilterType,
} from '../types';

// 后端 snake_case 合同原始结构 → 前端 camelCase 适配层
// 后端返回字段名参考 backend/app/services/contract_service.py 与 routes/contracts.py
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapContractFromApi(c: any) {
  if (!c) return c;
  return {
    id: c.id,
    name: c.name,
    contractNumber: c.contract_number ?? c.contractNumber,
    description: c.description,
    status: c.status,
    initiatorId: c.initiator?.id ?? c.initiator_id,
    initiator: c.initiator,
    ccUsers: c.cc_users ?? c.ccUsers ?? [],
    hasPendingReview: c.has_pending_review ?? c.hasPendingReview,
    createdAt: c.created_at ?? c.createdAt,
    updatedAt: c.updated_at ?? c.updatedAt,
    reviewCount: c.review_count,
    approvedCount: c.approved_count,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapAttachmentVersion(v: any) {
  return {
    id: v.id,
    contractId: v.contract_id ?? v.contractId,
    fileName: v.file_name ?? v.fileName,
    version: v.version,
    fileSize: v.file_size ?? v.fileSize,
    mimeType: v.mime_type ?? v.mimeType,
    storageKey: v.storage_key ?? v.storageKey,
    uploaderId: v.uploader?.id ?? v.uploader_id ?? v.uploaderId,
    uploader: v.uploader,
    createdAt: v.created_at ?? v.createdAt,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapAttachmentGroup(g: any) {
  return {
    fileName: g.file_name ?? g.fileName,
    versionCount: g.version_count ?? g.versionCount,
    versions: (g.versions ?? []).map(mapAttachmentVersion),
  };
}

/**
 * 获取合同列表
 *
 * @param filter - 筛选条件
 * @param search - 搜索关键词
 * @param page - 页码
 * @param limit - 每页数量
 */
export function useContractList(
  filter: FilterType = 'all',
  search: string = '',
  page: number = 1,
  limit: number = 50
) {
  return useQuery({
    queryKey: queryKeys.contracts.list(filter, search),
    queryFn: async () => {
      const response = await axios.get<ApiResponse<ContractListResponse>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.LIST}`,
        {
          params: { filter, search, page, limit },
        }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取合同列表失败');
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const raw = response.data.data as any;
      return {
        contracts: (raw?.contracts ?? []).map(mapContractFromApi),
        total: raw?.total ?? 0,
        pendingCount: raw?.pendingCount ?? raw?.pending_count ?? 0,
      } as ContractListResponse;
    },
    // 合同列表数据在5分钟内被认为是新鲜的
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取合同详情
 *
 * @param contractId - 合同ID
 */
export function useContractDetail(contractId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.contracts.detail(contractId || ''),
    queryFn: async () => {
      if (!contractId) {
        throw new Error('合同ID不能为空');
      }

      const response = await axios.get<ApiResponse<ContractDetailResponse>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.DETAIL(contractId)}`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取合同详情失败');
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const raw = response.data.data as any;
      return {
        contract: mapContractFromApi(raw?.contract),
        attachments: (raw?.attachments ?? []).map(mapAttachmentGroup),
        reviewers: raw?.reviewers ?? [],
      } as ContractDetailResponse;
    },
    // 只有当contractId存在时才执行查询
    enabled: !!contractId,
    // 合同详情数据在10分钟内被认为是新鲜的
    staleTime: 10 * 60 * 1000,
  });
}

/**
 * 创建合同
 */
export function useCreateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ContractFormData) => {
      const response = await axios.post<ApiResponse<{ contractId: string }>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.CREATE}`,
        data
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '创建合同失败');
      }

      return response.data.data!;
    },
    onSuccess: () => {
      // 创建成功后,使合同列表缓存失效
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
      // 使待办数量缓存失效
      queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });
    },
  });
}

/**
 * 获取待办数量
 */
export function usePendingCount() {
  return useQuery({
    queryKey: queryKeys.pending.count(),
    queryFn: async () => {
      // 通过获取"待我处理"筛选的合同列表来计算待办数量
      const response = await axios.get<ApiResponse<ContractListResponse>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.LIST}`,
        {
          params: { filter: '待我处理', page: 1, limit: 1 },
        }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取待办数量失败');
      }

      return response.data.data!.pendingCount;
    },
    // 待办数量数据在1分钟内被认为是新鲜的
    staleTime: 1 * 60 * 1000,
    // 每30秒自动重新获取
    refetchInterval: 30 * 1000,
  });
}
