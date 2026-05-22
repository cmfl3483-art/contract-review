# ReviewCard Component

## Overview

The `ReviewCard` component displays a single review opinion in the timeline. It shows the reviewer's information, opinion content, timestamp, and allows users to like the review.

## Features

- **Reviewer Information**: Displays reviewer avatar, name, and role
- **Review Content**: Shows the review opinion with support for multi-line text
- **Status Display**: Shows review status (✅ for approved, "评审中" for reviewing, "待处理" for pending)
- **Timestamp**: Displays relative time (e.g., "2小时前") or absolute date
- **Like Functionality**: Users can like/unlike reviews with visual feedback
- **Default Text**: Shows "参与了讨论" when no opinion is provided but has replies
- **Responsive Design**: Adapts to different screen sizes

## Props

```typescript
interface ReviewCardProps {
  review: Review;           // Review data object
  currentUserId?: string;   // Current user ID for like status
  onLike?: (reviewId: string) => void;  // Callback when like button is clicked
}
```

### Review Type

```typescript
interface Review {
  id: string;
  contractId: string;
  reviewerId: string;
  reviewer?: User;
  role: string;
  step: string;
  opinion?: string;
  status: 'pending' | 'reviewing' | 'approved';
  likes: number;
  likedBy: string[];
  createdAt: string;
  updatedAt: string;
}
```

## Usage

### Basic Usage

```tsx
import { ReviewCard } from '@/components/Timeline';

function Timeline() {
  const review = {
    id: 'review-1',
    contractId: 'contract-1',
    reviewerId: 'user-1',
    reviewer: {
      id: 'user-1',
      name: '张三',
      role: '法务',
      avatar: 'https://example.com/avatar.jpg'
    },
    role: '法务',
    step: '法务初审',
    opinion: '合同条款清晰，建议在第三条增加违约责任说明。',
    status: 'approved',
    likes: 5,
    likedBy: ['user-2', 'user-3'],
    createdAt: '2025-03-15T10:00:00Z',
    updatedAt: '2025-03-15T10:00:00Z'
  };

  return <ReviewCard review={review} />;
}
```

### With Like Functionality

```tsx
import { ReviewCard } from '@/components/Timeline';

function Timeline() {
  const currentUserId = 'user-123';

  const handleLike = (reviewId: string) => {
    // Call API to like/unlike the review
    console.log('Like review:', reviewId);
  };

  return (
    <ReviewCard
      review={review}
      currentUserId={currentUserId}
      onLike={handleLike}
    />
  );
}
```

### Review Without Opinion

When a review has no opinion but has replies, it displays "参与了讨论":

```tsx
const reviewWithoutOpinion = {
  ...review,
  opinion: undefined  // or empty string
};

<ReviewCard review={reviewWithoutOpinion} />
// Displays: "参与了讨论"
```

## Status Display

The component shows different status indicators:

- **✅** - Review is approved (`status: 'approved'`)
- **评审中** - Review is in progress (`status: 'reviewing'`)
- **待处理** - Review is pending (`status: 'pending'`)

## Like Functionality

- **Liked State**: When `currentUserId` is in `review.likedBy`, the like button shows a filled icon and blue color
- **Unliked State**: When `currentUserId` is not in `review.likedBy`, the like button shows an outline icon and gray color
- **Like Count**: Shows the number of likes, or "点赞" text when count is 0
- **Click Handler**: Calls `onLike(reviewId)` when the like button is clicked

## Time Display

The component uses `formatRelativeTime` utility to display timestamps:

- **Within 1 minute**: "刚刚"
- **Within 1 hour**: "5分钟前"
- **Within 30 days**: "2小时前", "3天前"
- **More than 30 days**: "2025-01-01"

## Avatar Colors

The component generates consistent avatar colors based on the reviewer's name using a hash function. This ensures the same reviewer always has the same color.

## Styling

The component uses CSS classes with the `review-card-` prefix:

- `.review-card` - Main container
- `.review-card-header` - Header with user info and status
- `.review-card-user` - User avatar and info section
- `.review-card-content` - Opinion content area
- `.review-card-footer` - Footer with like button
- `.review-card-like-btn` - Like button
- `.review-card-like-btn-active` - Active state for liked reviews

## Accessibility

- Avatar has tooltip showing reviewer name
- Like button has proper click handling
- Semantic HTML structure
- Keyboard accessible (button elements)

## Responsive Design

The component adapts to mobile screens:

- Reduced padding on small screens
- Stacked layout for user info
- Adjusted font sizes

## Requirements Coverage

This component implements the following requirements:

- **需求 4.5**: Display reviewer avatar, opinion content, and time
- **需求 4.6**: Support liking reviews
- **需求 4.7**: Display like count
- **需求 4.8**: Display relative time within 1 hour
- **需求 4.9**: Display specific date after 30 days
- **需求 4.4**: Show "参与了讨论" when no opinion but has replies

## Testing

The component includes comprehensive unit tests covering:

- Rendering review information
- Status display (approved, reviewing, pending)
- Like functionality and visual feedback
- Time formatting
- Avatar display
- Default text for empty opinions
- Edge cases (missing reviewer, long text, multi-line text)

Run tests with:

```bash
npm test -- ReviewCard.test.tsx
```

## Notes

- The component expects the `Review` type to include a `reviewer` object with user information
- If `reviewer` is undefined, it displays "未知用户" as fallback
- The opinion text supports multi-line content with `white-space: pre-wrap`
- The component is designed to be used within a Timeline component
