import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from '../utils/axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { queryKeys } from '../config/queryClient';
import type { ApiResponse, ReviewsResponse, Review, Comment } from '../types';

// 后端 snake_case 评论/评审 → 前端 camelCase 适配层
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapCommentFromApi(c: any): Comment {
  return {
    id: c.id,
    contractId: c.contract_id ?? c.contractId,
    reviewId: c.review_id ?? c.reviewId,
    parentCommentId: c.parent_comment_id ?? c.parentCommentId,
    authorId: c.author?.id ?? c.author_id ?? c.authorId,
    author: c.author,
    content: c.content,
    likes: c.likes ?? 0,
    likedBy: c.liked_by ?? c.likedBy ?? [],
    replies: Array.isArray(c.replies) ? c.replies.map(mapCommentFromApi) : undefined,
    createdAt: c.created_at ?? c.createdAt,
    updatedAt: c.updated_at ?? c.updatedAt ?? c.created_at ?? c.createdAt,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapReviewFromApi(r: any): Review {
  // 路由层已把 comments 重命名为 replies, 同时兼容两者
  const replies = (r.replies ?? r.comments ?? []).map(mapCommentFromApi);
  return {
    id: r.id,
    contractId: r.contract_id ?? r.contractId,
    reviewerId: r.reviewer?.id ?? r.reviewer_id ?? r.reviewerId,
    reviewer: r.reviewer,
    role: r.role,
    step: r.step,
    opinion: r.opinion,
    status: r.status,
    likes: r.likes ?? 0,
    likedBy: r.liked_by ?? r.likedBy ?? [],
    replies,
    createdAt: r.created_at ?? r.createdAt,
    updatedAt: r.updated_at ?? r.updatedAt ?? r.created_at ?? r.createdAt,
  };
}

/**
 * 获取合同的评审记录
 *
 * @param contractId - 合同ID
 */
export function useReviews(contractId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.reviews.list(contractId || ''),
    queryFn: async () => {
      if (!contractId) {
        throw new Error('合同ID不能为空');
      }

      const response = await axios.get<ApiResponse<ReviewsResponse>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.REVIEWS(contractId)}`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '获取评审记录失败');
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const raw = response.data.data as any;
      const result: ReviewsResponse = {
        reviews: (raw?.reviews ?? []).map(mapReviewFromApi),
        aiSummary: raw?.aiSummary ?? raw?.ai_summary ?? null,
        topLevelComments: (raw?.topLevelComments ?? raw?.top_level_comments ?? []).map(
          mapCommentFromApi
        ),
      };
      return result;
    },
    // 只有当contractId存在时才执行查询
    enabled: !!contractId,
    // 评审记录数据在5分钟内被认为是新鲜的
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 同意评审
 */
export function useApproveReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      reviewId,
      opinion,
    }: {
      contractId: string;
      reviewId: string;
      opinion: string;
    }) => {
      const response = await axios.post<ApiResponse<{ review: Review }>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.APPROVE(contractId, reviewId)}`,
        { opinion }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '同意评审失败');
      }

      return response.data.data!;
    },
    onSuccess: (_, variables) => {
      // 同意成功后,使相关缓存失效
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviews.list(variables.contractId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contracts.detail(variables.contractId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.contracts.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.pending.count() });
    },
  });
}

/**
 * 添加评论
 */
export function useAddComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      reviewId,
      parentCommentId,
      content,
      mentionedUserIds,
    }: {
      contractId: string;
      reviewId?: string;
      parentCommentId?: string;
      content: string;
      mentionedUserIds?: string[];
    }) => {
      const response = await axios.post<ApiResponse<{ comment: Comment }>>(
        `${API_BASE_URL}${API_ENDPOINTS.CONTRACTS.COMMENTS(contractId)}`,
        { 
          review_id: reviewId,  // 使用蛇形命名
          parent_comment_id: parentCommentId,  // 使用蛇形命名
          content,
          mentioned_user_ids: mentionedUserIds ?? [],  // 新增 @ 提及用户 ID 列表
        }
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '添加评论失败');
      }

      return response.data.data!;
    },
    onSuccess: (_, variables) => {
      // 添加评论成功后,使评审记录缓存失效
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviews.list(variables.contractId),
      });
    },
  });
}

/**
 * 点赞评审
 */
export function useLikeReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ reviewId }: { reviewId: string; contractId: string }) => {
      const response = await axios.post<ApiResponse<{ likes: number }>>(
        `${API_BASE_URL}${API_ENDPOINTS.REVIEWS.LIKE(reviewId)}`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '点赞失败');
      }

      return response.data.data!;
    },
    onSuccess: (_, variables) => {
      // 点赞成功后,使评审记录缓存失效
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviews.list(variables.contractId),
      });
    },
  });
}

/**
 * 点赞评论
 */
export function useLikeComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ commentId }: { commentId: string; contractId: string }) => {
      const response = await axios.post<ApiResponse<{ likes: number }>>(
        `${API_BASE_URL}${API_ENDPOINTS.COMMENTS.LIKE(commentId)}`
      );

      if (!response.data.success) {
        throw new Error(response.data.error || '点赞失败');
      }

      return response.data.data!;
    },
    onSuccess: (_, variables) => {
      // 点赞成功后,使评审记录缓存失效
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviews.list(variables.contractId),
      });
    },
  });
}
