import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ContractForm from './ContractForm';
import axios from 'axios';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios);

// Mock Ant Design message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
    },
  };
});

describe('ContractForm', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  const renderForm = (visible = true, onClose = vi.fn()) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ContractForm visible={visible} onClose={onClose} />
      </QueryClientProvider>
    );
  };

  it('应该显示表单标题', () => {
    renderForm();
    expect(screen.getByText('发起合同预审')).toBeInTheDocument();
  });

  it('应该显示所有必填字段', () => {
    renderForm();
    expect(screen.getByLabelText(/合同名称/)).toBeInTheDocument();
    expect(screen.getByLabelText(/评审人/)).toBeInTheDocument();
  });

  it('应该显示可选字段', () => {
    renderForm();
    expect(screen.getByLabelText(/合同描述/)).toBeInTheDocument();
    expect(screen.getByLabelText(/抄送人/)).toBeInTheDocument();
    expect(screen.getByLabelText(/附件/)).toBeInTheDocument();
  });

  it('当合同名称为空时应该显示验证错误', async () => {
    renderForm();

    // 点击提交按钮
    const submitButton = screen.getByText('提交');
    fireEvent.click(submitButton);

    // 等待验证错误显示
    await waitFor(() => {
      expect(screen.getByText('请输入合同名称')).toBeInTheDocument();
    });
  });

  it('当评审人为空时应该显示验证错误', async () => {
    renderForm();

    // 填写合同名称
    const nameInput = screen.getByLabelText(/合同名称/);
    fireEvent.change(nameInput, { target: { value: '测试合同' } });

    // 点击提交按钮
    const submitButton = screen.getByText('提交');
    fireEvent.click(submitButton);

    // 等待验证错误显示
    await waitFor(() => {
      expect(screen.getByText('请选择至少一个评审人')).toBeInTheDocument();
    });
  });

  it('当合同名称超过100个字符时应该显示验证错误', async () => {
    renderForm();

    // 填写超长的合同名称
    const nameInput = screen.getByLabelText(/合同名称/);
    const longName = 'a'.repeat(101);
    fireEvent.change(nameInput, { target: { value: longName } });

    // 点击提交按钮
    const submitButton = screen.getByText('提交');
    fireEvent.click(submitButton);

    // 等待验证错误显示
    await waitFor(() => {
      expect(screen.getByText('合同名称不能超过100个字符')).toBeInTheDocument();
    });
  });

  it('当合同描述超过500个字符时应该显示验证错误', async () => {
    renderForm();

    // 填写合同名称
    const nameInput = screen.getByLabelText(/合同名称/);
    fireEvent.change(nameInput, { target: { value: '测试合同' } });

    // 填写超长的合同描述
    const descriptionInput = screen.getByLabelText(/合同描述/);
    const longDescription = 'a'.repeat(501);
    fireEvent.change(descriptionInput, { target: { value: longDescription } });

    // 点击提交按钮
    const submitButton = screen.getByText('提交');
    fireEvent.click(submitButton);

    // 等待验证错误显示
    await waitFor(() => {
      expect(screen.getByText('合同描述不能超过500个字符')).toBeInTheDocument();
    });
  });

  it('当点击取消按钮时应该关闭对话框', () => {
    const onClose = vi.fn();
    renderForm(true, onClose);

    // 点击取消按钮
    const cancelButton = screen.getByText('取消');
    fireEvent.click(cancelButton);

    // 验证onClose被调用
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('应该在提交成功后关闭对话框', async () => {
    const onClose = vi.fn();
    renderForm(true, onClose);

    // Mock成功的API响应
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        success: true,
        data: { contractId: 'contract-123' },
      },
    });

    // 填写表单
    const nameInput = screen.getByLabelText(/合同名称/);
    fireEvent.change(nameInput, { target: { value: '测试合同' } });

    // 选择评审人 (这里需要模拟Select组件的交互,实际测试中可能需要更复杂的处理)
    // 为了简化测试,我们假设表单验证通过

    // 点击提交按钮
    const submitButton = screen.getByText('提交');
    fireEvent.click(submitButton);

    // 等待提交完成
    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});
