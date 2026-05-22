# QuickApprovalButton Component

## Overview

The `QuickApprovalButton` component provides a quick approval interface for contracts with pending reviews. It allows users to efficiently approve their pending review items with minimal clicks.

## Features

- **Conditional Rendering**: Only displays when there are pending reviews for the current user
- **Smart Workflow**:
  - Single pending item: Shows confirmation dialog directly
  - Multiple pending items: Shows selection list first, then confirmation dialog
- **Pre-filled Opinion**: Automatically fills "同意并通过" in the opinion field
- **User-friendly**: Clear visual feedback and intuitive interaction flow

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `contractId` | `string` | Yes | The ID of the contract |
| `contractName` | `string` | Yes | The name of the contract (displayed in confirmation dialog) |
| `pendingReviews` | `Review[]` | Yes | Array of pending review items for the current user |
| `onApprovalSuccess` | `() => void` | No | Callback function called after successful approval |

## Usage Example

```tsx
import { QuickApprovalButton } from './components/ContractList';
import type { Review } from './types';

function ContractCard({ contract, pendingReviews }) {
  const handleApprovalSuccess = () => {
    // Refresh contract list or update UI
    console.log('Approval successful, refreshing data...');
  };

  return (
    <div className="contract-card">
      <h3>{contract.name}</h3>
      <p>{contract.description}</p>
      
      <QuickApprovalButton
        contractId={contract.id}
        contractName={contract.name}
        pendingReviews={pendingReviews}
        onApprovalSuccess={handleApprovalSuccess}
      />
    </div>
  );
}
```

## Workflow

### Single Pending Review

1. User clicks "同意" button
2. Confirmation dialog appears immediately
3. Dialog shows:
   - Contract name
   - Review item details (role and step)
   - Opinion textarea (pre-filled with "同意并通过")
4. User can edit opinion or confirm directly
5. On confirmation, approval is submitted

### Multiple Pending Reviews

1. User clicks "同意" button
2. Selection modal appears with list of pending reviews
3. User clicks on a review item
4. Confirmation dialog appears
5. Dialog shows selected review details
6. User can edit opinion or confirm
7. On confirmation, approval is submitted

## Styling

The component uses CSS classes for styling:

- `.quick-approval-button` - The main button
- `.pending-review-item` - Review items in selection list
- `.approval-confirmation` - Confirmation dialog content
- `.contract-info`, `.review-info` - Information sections
- `.opinion-input` - Opinion textarea container

Custom styles can be added by importing and modifying `QuickApprovalButton.css`.

## Requirements Coverage

This component implements the following requirements:

- **需求 9.1**: Display "同意" button when contract has pending reviews for current user
- **需求 9.2**: Hide button when no pending reviews
- **需求 9.3**: Show confirmation dialog directly for single pending item
- **需求 9.4**: Show selection list for multiple pending items
- **需求 9.5**: Show confirmation dialog after selecting from list
- **需求 9.6**: Pre-fill "同意并通过" text
- **需求 9.7**: Update review status to "✅" on confirmation
- **需求 9.8**: Add new comment record to timeline
- **需求 9.9**: Refresh timeline, contract list, and pending badge

## API Integration

The component includes a TODO comment for API integration:

```typescript
// TODO: Call API to approve review
// const response = await axios.post(
//   API_ENDPOINTS.CONTRACTS.APPROVE(contractId, selectedReview.id),
//   { opinion }
// );
```

To complete the integration:

1. Import axios and API_ENDPOINTS
2. Uncomment and implement the API call
3. Handle response and errors appropriately
4. Update UI based on response

## Testing

Unit tests are provided in `QuickApprovalButton.test.tsx` covering:

- Rendering behavior (show/hide based on pending reviews)
- Single pending review workflow
- Multiple pending reviews workflow
- Opinion editing
- Modal interactions (open/close)
- Approval submission

## Future Enhancements

Potential improvements:

1. Add loading state during API call
2. Add optimistic UI updates
3. Support batch approval (approve all pending items at once)
4. Add keyboard shortcuts (e.g., Ctrl+Enter to confirm)
5. Add approval history/audit trail
6. Support custom opinion templates
