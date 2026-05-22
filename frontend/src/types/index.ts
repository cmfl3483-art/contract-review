// User types
export interface User {
  id: string;
  dingtalkUserId: string;
  dingtalkUnionId?: string;
  name: string;
  role: string;
  email?: string;
  mobile?: string;
  avatar?: string;
  department?: string;
  createdAt: string;
  updatedAt: string;
}

// Contract types
export type ContractStatus = 'progress' | 'completed';
export type FilterType = 'all' | '进行中' | '已完成' | '待我处理' | '抄送我' | '我发起的';

export interface Contract {
  id: string;
  name: string;
  description?: string;
  status: ContractStatus;
  initiatorId: string;
  initiator?: User;
  ccUsers: string[];
  hasPendingReview?: boolean; // Whether current user has pending reviews
  createdAt: string;
  updatedAt: string;
}

// Review types
export type ReviewStatus = 'pending' | 'reviewing' | 'approved';

export interface Review {
  id: string;
  contractId: string;
  reviewerId: string;
  reviewer?: User;
  role: string;
  step: string;
  opinion?: string;
  status: ReviewStatus;
  likes: number;
  likedBy: string[];
  replies?: Comment[];
  createdAt: string;
  updatedAt: string;
}

export interface ReviewerStatus {
  id: string;
  userId?: string;
  name: string;
  role: string;
  status: ReviewStatus;
  avatar?: string;
}

// Comment types
export interface Comment {
  id: string;
  contractId: string;
  reviewId?: string;
  parentCommentId?: string;
  authorId: string;
  author?: User;
  content: string;
  likes: number;
  likedBy: string[];
  replies?: Comment[];
  createdAt: string;
  updatedAt: string;
}

// Attachment types
export interface Attachment {
  id: string;
  contractId: string;
  fileName: string;
  version: string;
  fileSize: number;
  mimeType: string;
  storageKey: string;
  uploaderId: string;
  uploader?: User;
  createdAt: string;
}

export interface AttachmentGroup {
  fileName: string;
  versions: Attachment[];
  versionCount: number;
}

// AI types
export interface KeyIssue {
  issue: string;
  solution?: string;
}

export type ApprovalStatus = 'completed' | 'in_progress';

export interface AISummary {
  id: string;
  contractId: string;
  approvalStatus: ApprovalStatus;
  completedCount: number;
  totalCount: number;
  reviewCount: number;
  keyIssues: KeyIssue[];
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
  field?: string;
  requestId?: string;
}

export interface ContractListResponse {
  contracts: Contract[];
  total: number;
  pendingCount: number;
}

export interface ContractDetailResponse {
  contract: Contract;
  attachments: AttachmentGroup[];
  reviewers: ReviewerStatus[];
}

export interface ReviewsResponse {
  reviews: Review[];
  aiSummary: AISummary | null;
  topLevelComments: Comment[];
}

// Form types
export interface ContractFormData {
  name: string;
  description?: string;
  reviewers: string[];
  ccUsers: string[];
  files?: File[];
}

// Socket.IO types
export type {
  ContractUpdatedData,
  ReviewAddedData,
  CommentAddedData,
  ReplyAddedData,
  LikeUpdatedData,
  PendingChangedData,
  SocketEventCallback,
  UnsubscribeFunction,
} from './socket';
