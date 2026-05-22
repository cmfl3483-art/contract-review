/**
 * Socket.IO 事件数据类型定义
 * Socket.IO Event Data Types
 */

/**
 * 合同更新事件数据
 */
export interface ContractUpdatedData {
  contract_id: string;
  [key: string]: unknown;
}

/**
 * 评审添加事件数据
 */
export interface ReviewAddedData {
  contract_id: string;
  review_id: string;
  [key: string]: unknown;
}

/**
 * 评论添加事件数据
 */
export interface CommentAddedData {
  contract_id: string;
  comment_id: string;
  [key: string]: unknown;
}

/**
 * 回复添加事件数据
 */
export interface ReplyAddedData {
  contract_id: string;
  reply_id: string;
  [key: string]: unknown;
}

/**
 * 点赞更新事件数据
 */
export interface LikeUpdatedData {
  contract_id: string;
  target_id: string;
  likes: number;
  [key: string]: unknown;
}

/**
 * 待办数量变化事件数据
 */
export interface PendingChangedData {
  pending_count: number;
  [key: string]: unknown;
}

/**
 * Socket.IO 事件回调函数类型
 */
export type SocketEventCallback<T = unknown> = (data: T) => void;

/**
 * Socket.IO 事件取消订阅函数类型
 */
export type UnsubscribeFunction = () => void;
