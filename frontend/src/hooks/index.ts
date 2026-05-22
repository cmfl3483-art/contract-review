/**
 * React Query Hooks
 *
 * 这个文件导出所有的 React Query hooks,用于数据获取和缓存管理
 */

// 合同相关 hooks
export {
  useContractList,
  useContractDetail,
  useCreateContract,
  usePendingCount,
} from './useContracts';

// 评审相关 hooks
export {
  useReviews,
  useApproveReview,
  useAddComment,
  useLikeReview,
  useLikeComment,
} from './useReviews';

// 附件相关 hooks
export { useUploadAttachment, getAttachmentDownloadUrl } from './useAttachments';

// AI相关 hooks
export { useAISummary, useAIAdvisor } from './useAI';

// 用户认证相关 hooks
export { useCurrentUser, getDingTalkLoginUrl } from './useAuth';

// Socket.IO 相关 hooks
export {
  useSocket,
  useContractRoom,
  useSocketEvents,
  useSocketIntegration,
  useSocketEvent,
} from './useSocket';

// 性能优化相关 hooks
export { useThrottle } from './useThrottle';
export { useImageLazyLoad } from './useImageLazyLoad';
