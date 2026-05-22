import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import QuickApprovalButton from './QuickApprovalButton';
import type { Review } from '../../types';

// Mock antd message
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

describe('QuickApprovalButton', () => {
  const mockContractId = 'contract-123';
  const mockContractName = '测试合同';
  const mockOnApprovalSuccess = vi.fn();

  const createMockReview = (id: string, role: string, step?: string): Review => ({
    id,
    contractId: mockContractId,
    reviewerId: 'user-1',
    role,
    step: step || '',
    status: 'pending',
    likes: 0,
    likedBy: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should not render when there are no pending reviews', () => {
      const { container } = render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={[]}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('should render button when there are pending reviews', () => {
      const pendingReviews = [createMockReview('review-1', '法务')];

      render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={pendingReviews}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      expect(screen.getByText('同意')).toBeInTheDocument();
    });
  });

  describe('Single Pending Review', () => {
    it('should show confirmation dialog directly when clicking button with single pending review', async () => {
      const pendingReviews = [createMockReview('review-1', '法务', '法务初审')];

      render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={pendingReviews}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      // Click the button
      fireEvent.click(screen.getByText('同意'));

      // Should show confirmation modal
      await waitFor(() => {
        expect(screen.getByText('确认同意')).toBeInTheDocument();
      });

      // Should display contract name
      expect(screen.getByText(mockContractName)).toBeInTheDocument();

      // Should display review info
      expect(screen.getByText('法务 - 法务初审')).toBeInTheDocument();

      // Should pre-fill opinion
      const textarea = screen.getByPlaceholderText('请输入审批意见');
      expect(textarea).toHaveValue('同意并通过');
    });
  });

  describe('Multiple Pending Reviews', () => {
    it('should show selection list when clicking button with multiple pending reviews', async () => {
      const pendingReviews = [
        createMockReview('review-1', '法务', '法务初审'),
        createMockReview('review-2', '财务', '财务审核'),
      ];

      render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={pendingReviews}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      // Click the button
      fireEvent.click(screen.getByText('同意'));

      // Should show selection modal
      await waitFor(() => {
        expect(screen.getByText('选择待处理项')).toBeInTheDocument();
      });

      // Should display all pending reviews
      expect(screen.getByText('法务')).toBeInTheDocument();
      expect(screen.getByText('财务')).toBeInTheDocument();
    });

    it('should show confirmation dialog after selecting a review from list', async () => {
      const pendingReviews = [
        createMockReview('review-1', '法务', '法务初审'),
        createMockReview('review-2', '财务', '财务审核'),
      ];

      render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={pendingReviews}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      // Click the button to show selection modal
      fireEvent.click(screen.getByText('同意'));

      await waitFor(() => {
        expect(screen.getByText('选择待处理项')).toBeInTheDocument();
      });

      // Click on first review item
      const reviewItems = screen.getAllByRole('listitem');
      fireEvent.click(reviewItems[0]);

      // Should close selection modal and show confirmation modal
      await waitFor(() => {
        expect(screen.getByText('确认同意')).toBeInTheDocument();
      });

      // Should display selected review info
      expect(screen.getByText('法务 - 法务初审')).toBeInTheDocument();
    });
  });

  describe('Approval Confirmation', () => {
    it('should allow editing opinion text', async () => {
      const pendingReviews = [createMockReview('review-1', '法务')];

      render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={pendingReviews}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      // Open confirmation dialog
      fireEvent.click(screen.getByText('同意'));

      await waitFor(() => {
        expect(screen.getByText('确认同意')).toBeInTheDocument();
      });

      // Edit opinion
      const textarea = screen.getByPlaceholderText('请输入审批意见');
      fireEvent.change(textarea, { target: { value: '审核通过,无问题' } });

      expect(textarea).toHaveValue('审核通过,无问题');
    });

    it('should handle cancel button click', async () => {
      const pendingReviews = [createMockReview('review-1', '法务')];

      render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={pendingReviews}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      // Open confirmation dialog
      fireEvent.click(screen.getByText('同意'));

      await waitFor(() => {
        expect(screen.getByText('确认同意')).toBeInTheDocument();
      });

      // Click cancel
      fireEvent.click(screen.getByText('取消'));

      // Modal should be closed
      await waitFor(() => {
        expect(screen.queryByText('确认同意')).not.toBeInTheDocument();
      });
    });
  });

  describe('Approval Submission', () => {
    it('should handle successful approval', async () => {
      const pendingReviews = [createMockReview('review-1', '法务')];

      render(
        <QuickApprovalButton
          contractId={mockContractId}
          contractName={mockContractName}
          pendingReviews={pendingReviews}
          onApprovalSuccess={mockOnApprovalSuccess}
        />
      );

      // Open confirmation dialog
      fireEvent.click(screen.getByText('同意'));

      await waitFor(() => {
        expect(screen.getByText('确认同意')).toBeInTheDocument();
      });

      // Click confirm
      fireEvent.click(screen.getByText('确定'));

      // Should call success callback
      await waitFor(() => {
        expect(mockOnApprovalSuccess).toHaveBeenCalled();
      });

      // Modal should be closed
      await waitFor(() => {
        expect(screen.queryByText('确认同意')).not.toBeInTheDocument();
      });
    });
  });
});
