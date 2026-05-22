import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import AISummaryCard from './AISummaryCard';
import type { AISummary } from '../../types';

describe('AISummaryCard', () => {
  const mockSummaryInProgress: AISummary = {
    id: 'summary-1',
    contractId: 'contract-1',
    approvalStatus: 'in_progress',
    completedCount: 3,
    totalCount: 5,
    reviewCount: 8,
    keyIssues: [
      {
        issue: '合同中缺少违约责任条款，建议补充明确的违约责任和赔偿标准',
        solution: '已在第5条补充违约责任条款',
      },
      {
        issue: '付款方式需要明确具体的付款时间节点',
      },
      {
        issue: '知识产权归属问题需要进一步明确',
        solution: '双方已达成一致，知识产权归甲方所有',
      },
    ],
    createdAt: '2025-01-15T10:00:00Z',
    updatedAt: '2025-01-15T10:00:00Z',
  };

  const mockSummaryCompleted: AISummary = {
    id: 'summary-2',
    contractId: 'contract-2',
    approvalStatus: 'completed',
    completedCount: 5,
    totalCount: 5,
    reviewCount: 12,
    keyIssues: [],
    createdAt: '2025-01-15T10:00:00Z',
    updatedAt: '2025-01-15T10:00:00Z',
  };

  it('应该渲染 AI 智能总结标题', () => {
    render(<AISummaryCard summary={mockSummaryInProgress} />);

    expect(screen.getByText('AI 智能总结')).toBeInTheDocument();
  });

  it('应该有正确的测试 ID', () => {
    const { container } = render(<AISummaryCard summary={mockSummaryInProgress} />);

    const cardElement = container.querySelector('[data-testid="ai-summary-card"]');
    expect(cardElement).toBeInTheDocument();
  });

  describe('审批状态', () => {
    it('当审批进行中时应该显示正确的状态', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(screen.getByText('审批状态：')).toBeInTheDocument();
      expect(screen.getByText('审批进行中')).toBeInTheDocument();
    });

    it('当审批完成时应该显示正确的状态', () => {
      render(<AISummaryCard summary={mockSummaryCompleted} />);

      expect(screen.getByText('审批状态：')).toBeInTheDocument();
      expect(screen.getByText('已全部通过')).toBeInTheDocument();
    });

    it('审批进行中时应该显示时钟图标', () => {
      const { container } = render(<AISummaryCard summary={mockSummaryInProgress} />);

      const clockIcon = container.querySelector('.anticon-clock-circle');
      expect(clockIcon).toBeInTheDocument();
    });

    it('审批完成时应该显示勾选图标', () => {
      const { container } = render(<AISummaryCard summary={mockSummaryCompleted} />);

      const checkIcon = container.querySelector('.anticon-check-circle');
      expect(checkIcon).toBeInTheDocument();
    });
  });

  describe('统计信息', () => {
    it('应该显示已完成人数和总人数', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(screen.getByText('已完成：')).toBeInTheDocument();
      expect(screen.getByText('3/5 人')).toBeInTheDocument();
    });

    it('应该显示评审意见总数', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(screen.getByText('评审意见：')).toBeInTheDocument();
      expect(screen.getByText('8 条')).toBeInTheDocument();
    });

    it('当所有人都完成时应该显示正确的统计', () => {
      render(<AISummaryCard summary={mockSummaryCompleted} />);

      expect(screen.getByText('5/5 人')).toBeInTheDocument();
      expect(screen.getByText('12 条')).toBeInTheDocument();
    });
  });

  describe('关键问题', () => {
    it('当有关键问题时应该显示关键问题标题', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(screen.getByText('关键问题')).toBeInTheDocument();
    });

    it('当没有关键问题时不应该显示关键问题区域', () => {
      render(<AISummaryCard summary={mockSummaryCompleted} />);

      expect(screen.queryByText('关键问题')).not.toBeInTheDocument();
    });

    it('应该显示最多3个关键问题', () => {
      const summaryWithManyIssues: AISummary = {
        ...mockSummaryInProgress,
        keyIssues: [
          { issue: '问题1' },
          { issue: '问题2' },
          { issue: '问题3' },
          { issue: '问题4' },
          { issue: '问题5' },
        ],
      };

      render(<AISummaryCard summary={summaryWithManyIssues} />);

      expect(screen.getByText('问题1')).toBeInTheDocument();
      expect(screen.getByText('问题2')).toBeInTheDocument();
      expect(screen.getByText('问题3')).toBeInTheDocument();
      expect(screen.queryByText('问题4')).not.toBeInTheDocument();
      expect(screen.queryByText('问题5')).not.toBeInTheDocument();
    });

    it('应该显示问题序号', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('应该显示问题内容', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(
        screen.getByText('合同中缺少违约责任条款，建议补充明确的违约责任和赔偿标准')
      ).toBeInTheDocument();
      expect(screen.getByText('付款方式需要明确具体的付款时间节点')).toBeInTheDocument();
    });

    it('当问题有解决方案时应该显示解决方案', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(screen.getByText('解决方案：')).toBeInTheDocument();
      expect(screen.getByText('已在第5条补充违约责任条款')).toBeInTheDocument();
    });

    it('当问题没有解决方案时不应该显示解决方案区域', () => {
      const summaryWithoutSolution: AISummary = {
        ...mockSummaryInProgress,
        keyIssues: [{ issue: '这是一个没有解决方案的问题' }],
      };

      render(<AISummaryCard summary={summaryWithoutSolution} />);

      expect(screen.queryByText('解决方案：')).not.toBeInTheDocument();
    });

    it('应该为每个问题显示正确的序号', () => {
      render(<AISummaryCard summary={mockSummaryInProgress} />);

      const issueNumbers = screen.getAllByText(/^[1-3]$/);
      expect(issueNumbers).toHaveLength(3);
    });
  });

  describe('样式和布局', () => {
    it('应该应用正确的 CSS 类', () => {
      const { container } = render(<AISummaryCard summary={mockSummaryInProgress} />);

      expect(container.querySelector('.ai-summary-card')).toBeInTheDocument();
      expect(container.querySelector('.ai-summary-header')).toBeInTheDocument();
      expect(container.querySelector('.ai-summary-content')).toBeInTheDocument();
      expect(container.querySelector('.ai-summary-status')).toBeInTheDocument();
      expect(container.querySelector('.ai-summary-stats')).toBeInTheDocument();
    });

    it('审批进行中时状态值应该有 in-progress 类', () => {
      const { container } = render(<AISummaryCard summary={mockSummaryInProgress} />);

      const statusValue = container.querySelector('.ai-summary-status-value.in-progress');
      expect(statusValue).toBeInTheDocument();
    });

    it('审批完成时状态值应该有 completed 类', () => {
      const { container } = render(<AISummaryCard summary={mockSummaryCompleted} />);

      const statusValue = container.querySelector('.ai-summary-status-value.completed');
      expect(statusValue).toBeInTheDocument();
    });
  });

  describe('边界情况', () => {
    it('当 keyIssues 为空数组时不应该显示关键问题区域', () => {
      render(<AISummaryCard summary={mockSummaryCompleted} />);

      expect(screen.queryByText('关键问题')).not.toBeInTheDocument();
    });

    it('当 completedCount 为 0 时应该正确显示', () => {
      const summaryWithZeroCompleted: AISummary = {
        ...mockSummaryInProgress,
        completedCount: 0,
      };

      render(<AISummaryCard summary={summaryWithZeroCompleted} />);

      expect(screen.getByText('0/5 人')).toBeInTheDocument();
    });

    it('当 reviewCount 为 0 时应该正确显示', () => {
      const summaryWithZeroReviews: AISummary = {
        ...mockSummaryInProgress,
        reviewCount: 0,
      };

      render(<AISummaryCard summary={summaryWithZeroReviews} />);

      expect(screen.getByText('0 条')).toBeInTheDocument();
    });

    it('当只有一个关键问题时应该正确显示', () => {
      const summaryWithOneIssue: AISummary = {
        ...mockSummaryInProgress,
        keyIssues: [{ issue: '唯一的问题' }],
      };

      render(<AISummaryCard summary={summaryWithOneIssue} />);

      expect(screen.getByText('唯一的问题')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });
});
