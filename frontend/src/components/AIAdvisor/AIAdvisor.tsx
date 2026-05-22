import { useState, useEffect, useRef } from 'react';
import { message as antdMessage } from 'antd';
import ChatInput from './ChatInput';
import Message from './Message';
import { useAIAdvisor } from '../../hooks/useAI';
import { useSelectedContractStore } from '../../stores/useSelectedContractStore';
import { useContractDetail } from '../../hooks/useContracts';
import { useUserStore } from '../../stores/useUserStore';
import type { Message as MessageType } from '../../types';
import './AIAdvisor.css';

const AIAdvisor: React.FC = () => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get selected contract ID from store
  const { selectedContractId } = useSelectedContractStore();

  // Get contract details
  const { data: contractDetail } = useContractDetail(selectedContractId || undefined);

  // Get current user
  const { currentUser } = useUserStore();

  // AI advisor mutation
  const aiAdvisor = useAIAdvisor();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Clear messages when contract changes
  useEffect(() => {
    setMessages([]);
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

    try {
      // Call AI advisor API
      const answer = await aiAdvisor.mutateAsync({
        contractId: selectedContractId,
        question,
      });

      // Add assistant message
      const assistantMessage: MessageType = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: answer,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      // Handle error
      const errorMessage: MessageType = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content:
          error instanceof Error
            ? error.message
            : 'AI顾问服务暂时不可用，请稍后重试',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
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
          当前合同: {contractDetail?.contract.name || '未选择'}
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
