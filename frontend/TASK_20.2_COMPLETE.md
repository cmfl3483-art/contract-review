# Task 20.2 Complete: 创建工具函数

## Summary

Successfully created utility functions for the frontend application according to the design specifications.

## Files Created

### 1. `src/utils/time.ts`
Time formatting utilities for user-friendly date/time display.

**Functions:**
- `formatRelativeTime(date)` - Format dates as relative time (e.g., "刚刚", "5分钟前") or absolute dates
- `formatDateTime(date, format?)` - Format as absolute date and time
- `formatDate(date)` - Format as date only
- `formatTime(date)` - Format as time only
- `isToday(date)` - Check if date is today
- `isWithinDays(date, days)` - Check if date is within N days

**Key Features:**
- Within 1 minute: "刚刚"
- Within 1 hour: "X分钟前"
- Between 1 hour and 30 days: Relative time (e.g., "2小时前", "3天前")
- More than 30 days: Specific date (e.g., "2024-01-01")
- Uses dayjs with Chinese locale

### 2. `src/utils/filter.ts`
Contract filtering and searching utilities.

**Functions:**
- `filterContracts(contracts, filter, searchKeyword?, currentUserId?)` - Filter contracts by type and search
- `getFilterCount(contracts, filter, currentUserId?)` - Get count of matching contracts
- `matchesSearch(contract, keyword)` - Check if contract matches search
- `sortContracts(contracts, field, order?)` - Sort contracts by field

**Filter Types:**
- `'all'` - All contracts
- `'进行中'` - Contracts with status 'progress'
- `'已完成'` - Contracts with status 'completed'
- `'待我处理'` - Contracts with pending reviews for current user
- `'抄送我'` - Contracts where current user is CC'd

**Search Features:**
- Searches in contract name
- Searches in initiator name
- Case-insensitive matching

### 3. `src/utils/format.ts`
General formatting utilities for various data types.

**Functions:**
- `formatFileSize(bytes, decimals?)` - Format file size (e.g., "1.00 MB")
- `formatNumber(num, separator?)` - Format numbers with thousand separators
- `formatPercentage(value, decimals?, isDecimal?)` - Format percentage values
- `truncateString(str, maxLength, ellipsis?)` - Truncate strings with ellipsis
- `formatPhoneNumber(phone)` - Format phone numbers
- `capitalize(str)` - Capitalize first letter
- `toTitleCase(str)` - Convert to title case
- `getFileExtension(filename)` - Get file extension
- `getFileNameWithoutExtension(filename)` - Get filename without extension

### 4. `src/utils/avatar.ts`
Avatar generation utilities for user display.

**Functions:**
- `getAvatarColor(name)` - Generate consistent color based on name
- `getInitials(name)` - Get initials from name (Chinese/English support)
- `getAvatarStyle(name, size?)` - Generate avatar style object
- `generateAvatarDataUrl(name, size?)` - Generate SVG avatar data URL
- `getContrastColor(hexColor)` - Get contrasting text color

**Key Features:**
- 12 predefined accessible colors
- Consistent color mapping (same name = same color)
- Chinese name support (uses last character)
- English name support (uses first letters)
- SVG avatar generation

## Updates Made

### 1. `src/utils/index.ts`
Updated to export all new utility functions:
```typescript
export * from './time';
export * from './filter';
export * from './format';
export * from './avatar';
```

### 2. `src/utils/README.md`
Comprehensive documentation added with:
- Function descriptions
- Usage examples
- Complete examples for contract components
- Integration examples

### 3. `src/types/index.ts`
Added `hasPendingReview` property to Contract interface:
```typescript
export interface Contract {
  // ... existing properties
  hasPendingReview?: boolean; // Whether current user has pending reviews
}
```

## Verification

✅ All utility functions created according to design specifications
✅ TypeScript compilation successful (no errors in utils directory)
✅ Comprehensive JSDoc documentation added
✅ Usage examples provided in README
✅ Type-safe implementations with proper TypeScript types
✅ Follows project coding standards and conventions

## Usage Examples

### Time Formatting
```typescript
import { formatRelativeTime } from '@/utils';

formatRelativeTime(new Date()); // "刚刚"
formatRelativeTime(Date.now() - 5 * 60 * 1000); // "5分钟前"
formatRelativeTime(new Date('2024-01-01')); // "2024-01-01"
```

### Contract Filtering
```typescript
import { filterContracts } from '@/utils';

const filtered = filterContracts(contracts, '进行中', '');
const searched = filterContracts(contracts, 'all', '张三');
const pending = filterContracts(contracts, '待我处理', '', 'user123');
```

### File Size Formatting
```typescript
import { formatFileSize } from '@/utils';

formatFileSize(1048576); // "1.00 MB"
formatFileSize(1234567, 1); // "1.2 MB"
```

### Avatar Generation
```typescript
import { getAvatarColor, getInitials } from '@/utils';

const color = getAvatarColor('张三'); // "#1890ff"
const initials = getInitials('张三'); // "三"
```

## Requirements Covered

This task implements utility functions specified in the design document (Section: Components and Interfaces, Task 20.2):

- ✅ **formatRelativeTime** - Relative time formatting (需求 4.8, 4.9)
- ✅ **filterContracts** - Contract filtering logic (需求 1.2, 1.3, 1.5, 1.6)
- ✅ **formatFileSize** - File size formatting (需求 3.1-3.8)
- ✅ **Avatar generation** - User avatar colors and initials (需求 2.1-2.5, 4.5)

## Next Steps

These utility functions are now ready to be used in:
- Task 22: Contract List Components (ContractCard, FilterBar, SearchBox)
- Task 24: Contract Detail Components (AttachmentList, AttachmentVersion)
- Task 26: Timeline Components (ReviewCard, ReplyList)
- Task 28: AI Advisor Components (Message display)

## Notes

- All functions are fully typed with TypeScript
- Comprehensive JSDoc documentation provided
- Usage examples included in README
- Functions follow functional programming principles (pure functions, no side effects)
- Proper error handling and edge case coverage
- Chinese locale support for time formatting
- Accessible color palette for avatars
