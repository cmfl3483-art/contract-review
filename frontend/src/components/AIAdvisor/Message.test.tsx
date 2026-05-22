import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Message from './Message';
import type { Message as MessageType } from '../../types';

describe('Message', () => {
  const mockUserMessage: MessageType = {
    id: '1',
    role: 'user',
    content: '法务意见是什么？',
    timestamp: new Date().toISOString(),
  };

  const mockAssistantMessage: MessageType = {
    id: '2',
    role: 'assistant',
    content: '根据评审记录，法务部门提出了以下意见：\n1. 合同条款需要明确违约责任\n2. 建议增加保密条款',
    timestamp: new Date().toISOString(),
  };

  it('应该渲染用户消息', () => {
    render(<Message message={mockUserMessage} currentUserName="张三" />);

    const messageElement = screen.getByTestId('message');
    expect(messageElement).toBeInTheDocument();
    expect(messageElement).toHaveAttribute('data-role', 'user');
    expect(screen.getByText('法务意见是什么？')).toBeInTheDocument();
  });

  it('应该渲染 AI 消息', () => {
    render(<Message message={mockAssistantMessage} />);

    const messageElement = screen.getByTestId('message');
    expect(messageElement).toBeInTheDocument();
    expect(messageElement).toHaveAttribute('data-role', 'assistant');
    expect(screen.getByText(/根据评审记录/)).toBeInTheDocument();
  });

  it('应该为用户消息应用正确的样式类', () => {
    render(<Message message={mockUserMessage} />);

    const messageElement = screen.getByTestId('message');
    expect(messageElement).toHaveClass('message-user');
  });

  it('应该为 AI 消息应用正确的样式类', () => {
    render(<Message message={mockAssistantMessage} />);

    const messageElement = screen.getByTestId('message');
    expect(messageElement).toHaveClass('message-assistant');
  });

  it('应该显示时间戳', () => {
    const recentMessage: MessageType = {
      id: '3',
      role: 'user',
      content: '测试消息',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5分钟前
    };

    render(<Message message={recentMessage} />);

    // 时间戳应该显示为相对时间
    expect(screen.getByText(/分钟前|刚刚/)).toBeInTheDocument();
  });

  it('应该正确处理多行内容', () => {
    const multilineMessage: MessageType = {
      id: '4',
      role: 'assistant',
      content: '第一行\n第二行\n第三行',
      timestamp: new Date().toISOString(),
    };

    render(<Message message={multilineMessage} />);

    const textElement = screen.getByText(/第一行/);
    expect(textElement).toBeInTheDocument();
    // CSS white-space: pre-wrap 会保留换行符
  });

  it('应该显示用户头像', () => {
    render(<Message message={mockUserMessage} currentUserName="张三" />);

    // 检查头像是否存在
    const avatars = document.querySelectorAll('.ant-avatar');
    expect(avatars.length).toBeGreaterThan(0);
  });

  it('应该显示 AI 头像', () => {
    render(<Message message={mockAssistantMessage} />);

    // 检查头像是否存在
    const avatars = document.querySelectorAll('.ant-avatar');
    expect(avatars.length).toBeGreaterThan(0);
  });

  it('应该处理空内容', () => {
    const emptyMessage: MessageType = {
      id: '5',
      role: 'user',
      content: '',
      timestamp: new Date().toISOString(),
    };

    render(<Message message={emptyMessage} />);

    const messageElement = screen.getByTestId('message');
    expect(messageElement).toBeInTheDocument();
  });

  it('应该处理长文本内容', () => {
    const longMessage: MessageType = {
      id: '6',
      role: 'assistant',
      content: '这是一段很长的文本内容'.repeat(50),
      timestamp: new Date().toISOString(),
    };

    render(<Message message={longMessage} />);

    const messageElement = screen.getByTestId('message');
    expect(messageElement).toBeInTheDocument();
    // 长文本应该被正确包裹，不会溢出
  });
});
