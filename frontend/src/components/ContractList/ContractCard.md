# ContractCard Component

## Overview

The `ContractCard` component displays a single contract in the contract list. It shows the contract's basic information including name, status, initiator, and creation date. The component supports selection states and optional quick approval functionality.

## Features

- **Contract Information Display**: Shows contract name, status tag, initiator avatar/name, and creation date
- **Status Visualization**: Different colored tags for "进行中" (In Progress) and "已完成" (Completed) statuses
- **Interactive States**: Hover effects and selected state with visual feedback
- **Quick Approval**: Optional "同意" (Approve) button when user has pending reviews
- **Relative Time Display**: Shows creation time in a user-friendly format (e.g., "5分钟前", "2天前")
- **Avatar Generation**: Automatically generates colored avatars based on initiator name

## Props

```typescript
interface ContractCardProps {
  contract: Contract;           // Contract data to display
  selected?: boolean;           // Whether this card is currently selected
  onSelect: (contractId: string) => void;  // Callback when card is clicked
  onApprove?: (contractId: string) => void; // Optional callback for approve button
}
```

## Usage

### Basic Usage

```tsx
import { ContractCard } from './components/ContractList';

function MyComponent() {
  const contract = {
    id: '1',
    name: '采购合同',
    status: 'progress',
    initiatorId: 'user1',
    initiator: {
      id: 'user1',
      name: '张三',
      role: '销售',
      // ... other user fields
    },
    ccUsers: [],
    hasPendingReview: false,
    createdAt: '2025-03-15T10:30:00Z',
    updatedAt: '2025-03-15T10:30:00Z',
  };

  const handleSelect = (contractId: string) => {
    console.log('Selected contract:', contractId);
  };

  return (
    <ContractCard
      contract={contract}
      onSelect={handleSelect}
    />
  );
}
```

### With Selection State

```tsx
<ContractCard
  contract={contract}
  selected={selectedContractId === contract.id}
  onSelect={handleSelect}
/>
```

### With Quick Approval

```tsx
const contractWithPending = {
  ...contract,
  hasPendingReview: true, // User has pending reviews for this contract
};

const handleApprove = (contractId: string) => {
  console.log('Approve contract:', contractId);
  // Show approval dialog or directly approve
};

<ContractCard
  contract={contractWithPending}
  onSelect={handleSelect}
  onApprove={handleApprove}
/>
```

## Visual States

### Default State
- White background
- Transparent left border
- Standard text colors

### Hover State
- Light gray background (#f5f5f5)
- Smooth transition animation

### Selected State
- Light blue background (#e6f7ff)
- Blue left border (3px, #1890ff)
- Maintains selected appearance on hover

## Status Tags

The component displays different status tags based on the contract status:

- **进行中** (In Progress): Blue processing tag
- **已完成** (Completed): Green success tag

## Time Display

The component uses the `formatRelativeTime` utility to display creation time:

- Within 1 minute: "刚刚"
- Within 1 hour: "X分钟前"
- Within 30 days: "X小时前", "X天前"
- Over 30 days: "YYYY-MM-DD"

## Avatar Generation

The component generates colored avatars for initiators:

1. If initiator has an avatar URL, displays the image
2. Otherwise, generates a colored circle with the first character of the name
3. Avatar color is determined by the initiator's name (consistent for same name)
4. Tooltip shows full initiator name on hover

## Approve Button

The approve button is only displayed when:
- `contract.hasPendingReview` is `true`
- `onApprove` callback is provided

Button behavior:
- Clicking the button triggers `onApprove` callback
- Click event is stopped from propagating to prevent card selection
- Button has hover and active states with color transitions

## Styling

The component uses CSS classes for styling:

- `.contract-card`: Main container
- `.contract-card-selected`: Selected state modifier
- `.contract-card-header`: Header section with title and status
- `.contract-card-title`: Contract name (supports multi-line with ellipsis)
- `.contract-card-meta`: Metadata section with initiator and date
- `.contract-card-actions`: Actions section (approve button)
- `.contract-card-approve-btn`: Approve button

## Accessibility

- Uses semantic HTML structure
- Provides tooltips for truncated text
- Keyboard accessible (clickable elements)
- Clear visual feedback for interactive states
- `data-testid` attribute for testing

## Requirements Coverage

This component implements the following requirements from the design document:

- **需求 1.4**: Display contract name, initiator, date, and status tag for each contract card
- **需求 1.8**: Set selected contract and highlight when user clicks contract card
- **需求 9.1**: Display "同意" button when contract has pending reviews for current user
- **需求 10.1**: Change card background color on hover for visual feedback
- **需求 10.2**: Add left blue border and highlight background for selected contract card
- **需求 10.4**: Display user name tooltip on avatar hover

## Dependencies

- `antd`: Tag, Tooltip, Avatar components
- `@ant-design/icons`: UserOutlined icon
- `../../types`: Contract type definition
- `../../utils/time`: formatRelativeTime utility

## Related Components

- `ContractList`: Parent component that renders multiple ContractCard components
- `FilterBar`: Filters contracts displayed in the list
- `SearchBox`: Searches contracts by name or initiator
- `QuickApprovalButton`: Alternative approval UI (not used in this component)

## Future Enhancements

Potential improvements for future iterations:

1. **Drag and Drop**: Support dragging cards for reordering or categorization
2. **Context Menu**: Right-click menu for additional actions
3. **Badges**: Show notification badges for unread comments or updates
4. **Preview**: Quick preview on hover showing more details
5. **Animations**: Smooth animations when cards are added/removed
6. **Accessibility**: Enhanced keyboard navigation and screen reader support
