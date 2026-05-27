import { useState, useEffect, useRef, useMemo } from 'react';
import { message as antdMessage } from 'antd';
import ChatInput from './ChatInput';
import Message from './Message';
import { useAIAdvisor } from '../../hooks/useAI';
import { useReviews } from '../../hooks/useReviews';
import { useSelectedContractStore } from '../../stores/useSelectedContractStore';
import { useContractDetail } from '../../hooks/useContracts';
import { useUserStore } from '../../stores/useUserStore';
import type { Message as MessageType, Comment } from '../../types';
import './AIAdvisor.css';

/**
 * 递归遍历评论树，把每个 comment.id → 作者姓名 写入 map。
 * 兼容多级 replies（虽然当前后端通常只下发一层）。
 */
function collectComments(
  comments: Comment[] | undefined,
  map: Map<string, { authorName: string }>
): void {
  if (!comments) return;
  for (const c of comments) {
    map.set(c.id, { authorName: c.author?.name ?? '未知' });
    if (c.replies && c.replies.length > 0) {
      collectComments(c.replies, map);
    }
  }
}

const AIAdvisor: React.FC = () => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  /** 当前正在流式接收的 AI 消息 ID；null 表示无流式中 */
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get selected contract ID from store
  const { selectedContractId } = useSelectedContractStore();

  // Get contract details
  const { data: contractDetail } = useContractDetail(
    selectedContractId || undefined
  );

  // Get reviews + comments for [ref:...] resolution
  const { data: reviewsData } = useReviews(selectedContractId || undefined);

  // Get current user
  const { currentUser } = useUserStore();

  // AI advisor mutation
  const aiAdvisor = useAIAdvisor();

  // 构建 review.id / comment.id → { authorName } 映射，供 Message → MessageContent 解析 [ref:...]
  const { reviewMap, commentMap } = useMemo(() => {
    const reviewMap = new Map<string, { authorName: string }>();
    const commentMap = new Map<string, { authorName: string }>();

    for (const r of reviewsData?.reviews ?? []) {
      reviewMap.set(r.id, { authorName: r.reviewer?.name ?? '未知' });
      // 评审下挂的评论（含可能的多级 replies）
      collectComments(r.replies, commentMap);
    }
    // 合同维度的独立顶层评论
    collectComments(reviewsData?.topLevelComments, commentMap);

    return { reviewMap, commentMap };
  }, [reviewsData]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Clear messages when contract changes
  useEffect(() => {
    setMessages([]);
    setStreamingMessageId(null);
  }, [selectedContractId]);

  const handleSendMessage = async (question: string) => {
    if (!selectedContractId) {
      antdMessage.warning('请先选择一个合同');
      return;
    }

    // Add user message
    const userMessage: MessageType = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // 提前为 AI 回复创建占位消息并标记为「流式中」，
    // 这样在请求过程中 CollapsibleMessage 不做测量、不显示折叠按钮，避免抖动；
    // 请求结束后清空 streamingMessageId 触发重新测量。
    const assistantId = `assistant-${Date.now()}`;
    const assistantPlaceholder: MessageType = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantPlaceholder]);
    setStreamingMessageId(assistantId);

    try {
      // Call AI advisor API
      const answer = await aiAdvisor.mutateAsync({
        contractId: selectedContractId,
        question,
      });

      // 用真实回答替换占位消息
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: answer } : m
        )
      );
    } catch (error) {
      // 错误时把占位消息内容替换为错误文案
      const errorContent =
        error instanceof Error
          ? error.message
          : 'AI顾问服务暂时不可用，请稍后重试';
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: errorContent } : m
        )
      );
    } finally {
      // 流式结束 → 触发 CollapsibleMessage 重新测量
      setStreamingMessageId(null);
    }
  };

  // 点击"需要"后，直接总结评审进度
  const handleQuickSummary = () => {
    handleSendMessage('总结');
  };

  return (
    <div className="ai-advisor">
      <div className="ai-advisor-header">
        <h3>AI 合同预审助理</h3>
        <p className="current-contract">
          当前合同: {contractDetail?.contract.contractNumber ? contractDetail.contract.contractNumber + ' ' : ''}{contractDetail?.contract.name || '未选择'}
        </p>
      </div>

      <div className="ai-advisor-messages">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <p>
              需要我帮你总结评审进度吗？
              <button
                type="button"
                className="welcome-quick-action"
                onClick={handleQuickSummary}
                disabled={!selectedContractId || aiAdvisor.isPending}
              >
                需要
              </button>
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <Message
                key={msg.id}
                message={msg}
                currentUserName={currentUser?.name}
                contractId={selectedContractId || undefined}
                reviewMap={reviewMap}
                commentMap={commentMap}
                isStreaming={streamingMessageId === msg.id}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="ai-advisor-input">
        <ChatInput
          onSend={handleSendMessage}
          loading={aiAdvisor.isPending}
          placeholder={
            selectedContractId ? '输入您的问题...' : '请先选择一个合同'
          }
        />
      </div>
    </div>
  );
};

export default AIAdvisor;
