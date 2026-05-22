# ReplyList Component

## Overview

The `ReplyList` component displays a list of replies to a review or comment with support for nested replies, liking, and automatic collapsing when there are more than 2 replies.

## Features

- **Reply Display**: Shows reply author avatar, name, content, and timestamp
- **Nested Replies**: Supports replies to replies (nested structure)
- **Like Functionality**: Users can like replies with visual feedback
- **Auto-Collapse**: Automatically collapses when more than 2 replies exist
- **Expand/Collapse**: Shows "共N条回复" button to expand all replies
- **Relative Time**: Displays relative time for recent replies (e.g., "5分钟前")
- **Avatar Generation**: Generates colored avatars based on user names

## Props

```typescript
interface ReplyListProps {
  replies: Comment[];           // Array of reply comments
  onLike?: (commentId: string) => void;  // Callback when user likes a reply
  currentUserId?: string;        // Current user ID to show liked state
}
```

## Usage

```tsx
import { ReplyList } from '@/components/Timeline';

function ReviewCard() {
  const replies = [
    {
      id: '1',
      content: '这是一条回复',
      author: { name: '张三', avatar: '...' },
      likes: 2,
      likedBy: ['user-1', 'user-2'],
      createdAt: '2025-03-15T10:00:00Z',
      // ... other fields
    },
    // ... more replies
  ];

  const handleLike = (commentId: string) => {
    // Handle like action
    console.log('Liked comment:', commentId);
  };

  return (
    <div>
      <ReplyList 
        replies={replies}
        onLike={handleLike}
        currentUserId="current-user-id"
      />
    </div>
  );
}
```

## Behavior

### Collapse Logic

- **≤ 2 replies**: All replies are shown, no expand/collapse button
- **> 2 replies**: Shows first 2 replies by default with "共N条回复" button
- **Expanded**: Shows all replies with "收起" button

### Like Interaction

- Click the like button to like/unlike a reply
- Liked state is shown with a filled heart icon and blue color
- Like count is displayed next to the icon

### Time Display

- Uses `formatRelativeTime` utility for user-friendly time display
- Shows "刚刚", "5分钟前", "2小时前", etc.
- Shows specific date for times > 30 days ago

## Styling

The component uses CSS classes for styling:

- `.reply-list` - Container for all replies
- `.reply-items` - Container for reply items
- `.reply-item` - Individual reply item
- `.reply-content` - Reply content area
- `.reply-header` - Author and time header
- `.reply-text` - Reply text content
- `.reply-actions` - Action buttons (like)
- `.reply-like-button` - Like button
- `.reply-toggle-button` - Expand/collapse button

## Requirements

Implements the following requirements:

- **5.4**: Support for replying to reviews
- **5.5**: Display reply author avatar, content, and time
- **5.6**: Support for liking replies
- **5.7**: Collapse when more than 2 replies
- **5.8**: Show "共N条回复" button to expand
- **5.9**: Show all replies when expanded, change button to "收起"

## Dependencies

- `antd` - Avatar and Tooltip components
- `@ant-design/icons` - Like icons
- `../../utils/time` - Time formatting utilities
- `../../utils/avatar` - Avatar color and initials generation
- `../../types` - TypeScript type definitions

## Accessibility

- Avatar tooltips show user names on hover
- Buttons have appropriate hover states
- Text content is readable with proper contrast
- Responsive design for mobile devices

## Testing

The component includes comprehensive unit tests covering:

- Reply list rendering
- Author name and time display
- Like count display
- Expand/collapse functionality
- Like interaction
- Empty state handling
- User liked state display

Run tests with:
```bash
npm test -- ReplyList.test.tsx
```

## Related Components

- `ReviewCard` - Parent component that uses ReplyList
- `CommentInput` - Component for adding new replies
- `Timeline` - Main timeline component that orchestrates all components
