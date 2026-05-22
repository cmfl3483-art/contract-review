# AISummaryCard Component

## Overview

The `AISummaryCard` component displays an AI-generated summary of contract approval progress and key issues. It provides a quick overview of the approval status, completion statistics, and highlights important issues that need attention.

## Features

- **Approval Status**: Shows whether the approval is completed or in progress with appropriate icons
- **Progress Statistics**: Displays completed count vs total count and total review count
- **Key Issues**: Lists up to 3 key issues extracted from reviews
- **Solutions**: Shows solutions for issues when available
- **Visual Design**: Uses a gradient background with clear visual hierarchy

## Props

```typescript
interface AISummaryCardProps {
  summary: AISummary;
}
```

### AISummary Type

```typescript
interface AISummary {
  id: string;
  contractId: string;
  approvalStatus: 'completed' | 'in_progress';
  completedCount: number;
  totalCount: number;
  reviewCount: number;
  keyIssues: KeyIssue[];
  createdAt: string;
  updatedAt: string;
}

interface KeyIssue {
  issue: string;
  solution?: string;
}
```

## Usage

```tsx
import { AISummaryCard } from '@/components/Timeline';

function Timeline() {
  const summary = {
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
    ],
    createdAt: '2025-01-15T10:00:00Z',
    updatedAt: '2025-01-15T10:00:00Z',
  };

  return <AISummaryCard summary={summary} />;
}
```

## Visual States

### Approval Status

- **In Progress**: Shows a clock icon with yellow color and "审批进行中" text
- **Completed**: Shows a check icon with green color and "已全部通过" text

### Key Issues

- Issues are numbered (1, 2, 3) with blue circular badges
- Solutions are displayed in a green-bordered box below the issue
- Maximum of 3 issues are shown

## Styling

The component uses a gradient background (`#e6f7ff` to `#f0f5ff`) with a blue border to make it stand out in the timeline. All internal sections use white backgrounds with subtle borders for clear separation.

## Accessibility

- Uses semantic HTML structure
- Includes appropriate ARIA labels through Ant Design icons
- Maintains good color contrast ratios
- Responsive design for mobile devices

## Requirements Mapping

This component implements the following requirements from the design document:

- **需求 6.1**: Display AI summary at the top of timeline when reviews exist
- **需求 6.2**: Show approval progress status (completed/in progress)
- **需求 6.3**: Display completed count and total count
- **需求 6.4**: Display total review count
- **需求 6.5**: Extract and display up to 3 key issues
- **需求 6.6**: Show solutions for issues when replies exist
- **需求 6.7**: Mark status as "completed" when all reviewers approved
- **需求 6.8**: Mark status as "in progress" when pending reviewers exist
