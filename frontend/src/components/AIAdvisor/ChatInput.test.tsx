import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChatInput from './ChatInput';

describe('ChatInput', () => {
  it('应该渲染输入框和发送按钮', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    expect(screen.getByPlaceholderText('输入您的问题...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /发送/i })).toBeInTheDocument();
  });

  it('应该使用自定义占位符文本', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} placeholder="自定义占位符" />);

    expect(screen.getByPlaceholderText('自定义占位符')).toBeInTheDocument();
  });

  it('应该在输入时更新输入框的值', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '测试消息' } });

    expect(input.value).toBe('测试消息');
  });

  it('点击发送按钮应该调用 onSend 并清空输入框', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /发送/i });

    fireEvent.change(input, { target: { value: '测试消息' } });
    fireEvent.click(sendButton);

    expect(onSend).toHaveBeenCalledWith('测试消息');
    expect(onSend).toHaveBeenCalledTimes(1);
    expect(input.value).toBe('');
  });

  it('按回车键应该调用 onSend 并清空输入框', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;

    fireEvent.change(input, { target: { value: '测试消息' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });

    expect(onSend).toHaveBeenCalledWith('测试消息');
    expect(onSend).toHaveBeenCalledTimes(1);
    expect(input.value).toBe('');
  });

  it('按 Shift+Enter 不应该发送消息', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;

    fireEvent.change(input, { target: { value: '测试消息' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13, shiftKey: true });

    expect(onSend).not.toHaveBeenCalled();
    expect(input.value).toBe('测试消息');
  });

  it('不应该发送空消息或只有空格的消息', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /发送/i });

    // 测试空消息
    fireEvent.click(sendButton);
    expect(onSend).not.toHaveBeenCalled();

    // 测试只有空格的消息
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.click(sendButton);
    expect(onSend).not.toHaveBeenCalled();
  });

  it('当 loading 为 true 时应该禁用输入框和按钮', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} loading={true} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /发送/i });

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('当 loading 为 true 时不应该发送消息', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} loading={true} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;

    fireEvent.change(input, { target: { value: '测试消息' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });

    expect(onSend).not.toHaveBeenCalled();
  });

  it('当输入框为空时发送按钮应该被禁用', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const sendButton = screen.getByRole('button', { name: /发送/i });

    expect(sendButton).toBeDisabled();
  });

  it('当输入框有内容时发送按钮应该被启用', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /发送/i });

    fireEvent.change(input, { target: { value: '测试消息' } });

    expect(sendButton).not.toBeDisabled();
  });

  it('应该修剪消息前后的空格', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入您的问题...') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /发送/i });

    fireEvent.change(input, { target: { value: '  测试消息  ' } });
    fireEvent.click(sendButton);

    expect(onSend).toHaveBeenCalledWith('测试消息');
  });
});
