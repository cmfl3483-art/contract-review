# Utility Functions

This directory contains various utility functions for the frontend application, including HTTP client utilities, time formatting, contract filtering, general formatting, and avatar generation.

## Files

### `axios.ts`

Configured Axios instance with:

- **Base URL**: Automatically set from environment variable `VITE_API_BASE_URL`
- **Timeout**: 30 seconds
- **Request Interceptor**: Automatically adds JWT token from localStorage to Authorization header
- **Response Interceptor**: Handles errors uniformly with user-friendly messages

### `request.ts`

Typed wrapper functions for common HTTP methods:

- `get<T>(url, config)` - GET request
- `post<T>(url, data, config)` - POST request
- `put<T>(url, data, config)` - PUT request
- `patch<T>(url, data, config)` - PATCH request
- `del<T>(url, config)` - DELETE request
- `upload<T>(url, formData, onProgress)` - File upload with progress tracking
- `download(url, filename)` - File download

All functions return the `data` property from the API response for convenience.

## Usage Examples

### Basic GET Request

```typescript
import { get } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/api';

const contracts = await get(API_ENDPOINTS.CONTRACTS.LIST);
```

### POST Request with Data

```typescript
import { post } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/api';

const newContract = await post(API_ENDPOINTS.CONTRACTS.CREATE, {
  name: 'New Contract',
  description: 'Contract description',
  reviewers: ['user1', 'user2'],
  ccUsers: ['user3'],
});
```

### File Upload with Progress

```typescript
import { upload } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/api';

const formData = new FormData();
formData.append('file', file);

const result = await upload(
  API_ENDPOINTS.CONTRACTS.ATTACHMENTS(contractId),
  formData,
  (progressEvent) => {
    const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
    console.log(`Upload progress: ${percent}%`);
  }
);
```

### File Download

```typescript
import { download } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/api';

await download(API_ENDPOINTS.ATTACHMENTS.DOWNLOAD(attachmentId), 'contract.pdf');
```

## Error Handling

The Axios interceptor automatically handles common HTTP errors:

- **401 Unauthorized**: Clears token and redirects to DingTalk login
- **403 Forbidden**: Shows "权限不足" message
- **404 Not Found**: Shows "资源不存在" message
- **413 Payload Too Large**: Shows "文件过大" message
- **500 Internal Server Error**: Shows "服务器错误,请稍后重试" message
- **502 Bad Gateway**: Shows "服务暂时不可用,请稍后重试" message
- **503 Service Unavailable**: Shows "系统正在维护,请稍后重试" message
- **Network Error**: Shows "网络连接失败,请检查网络" message

All error messages are displayed using Ant Design's `message` component.

## Authentication

The request interceptor automatically adds the JWT token from localStorage:

```typescript
Authorization: Bearer<token>;
```

When a 401 error occurs, the token is automatically cleared and the user is redirected to the DingTalk login page.

## Type Safety

All request functions are fully typed using TypeScript generics:

```typescript
interface Contract {
  id: string;
  name: string;
  status: string;
}

// Type-safe request
const contracts = await get<Contract[]>(API_ENDPOINTS.CONTRACTS.LIST);
// contracts is typed as Contract[]
```

## API Response Format

All API responses follow this standard format:

```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
  field?: string;
  requestId?: string;
}
```

The request utilities automatically extract the `data` property, so you don't need to access `response.data.data`.


---

## Time Formatting (`time.ts`)

Utilities for formatting dates and times in a user-friendly way.

### Functions

#### `formatRelativeTime(date)`

Format a date as relative time or absolute date.

**Rules:**
- Within 1 minute: "刚刚"
- Within 1 hour: "X分钟前"
- Between 1 hour and 30 days: Relative time (e.g., "2小时前", "3天前")
- More than 30 days: Specific date (e.g., "2024-01-01")

```typescript
import { formatRelativeTime } from '@/utils';

formatRelativeTime(new Date()); // "刚刚"
formatRelativeTime(Date.now() - 5 * 60 * 1000); // "5分钟前"
formatRelativeTime(Date.now() - 2 * 60 * 60 * 1000); // "2小时前"
formatRelativeTime(new Date('2024-01-01')); // "2024-01-01"
```

#### `formatDateTime(date, format?)`

Format a date as absolute date and time.

```typescript
formatDateTime(new Date()); // "2025-03-15 14:30:00"
formatDateTime(new Date(), 'YYYY-MM-DD'); // "2025-03-15"
```

#### Other Functions

- `formatDate(date)` - Format as date only
- `formatTime(date)` - Format as time only
- `isToday(date)` - Check if date is today
- `isWithinDays(date, days)` - Check if date is within N days

---

## Contract Filtering (`filter.ts`)

Utilities for filtering and searching contracts.

### Functions

#### `filterContracts(contracts, filter, searchKeyword?, currentUserId?)`

Filter contracts based on filter type and search keyword.

**Filter Types:**
- `'all'` - All contracts
- `'进行中'` - Contracts with status 'progress'
- `'已完成'` - Contracts with status 'completed'
- `'待我处理'` - Contracts with pending reviews for current user
- `'抄送我'` - Contracts where current user is CC'd

```typescript
import { filterContracts } from '@/utils';

// Filter by status
const inProgress = filterContracts(contracts, '进行中', '');

// Search by keyword
const searched = filterContracts(contracts, 'all', '张三');

// Filter pending reviews
const pending = filterContracts(contracts, '待我处理', '', 'user123');
```

#### Other Functions

- `getFilterCount(contracts, filter, currentUserId?)` - Get count of matching contracts
- `matchesSearch(contract, keyword)` - Check if contract matches search
- `sortContracts(contracts, field, order?)` - Sort contracts by field

---

## General Formatting (`format.ts`)

Utilities for formatting various data types.

### Functions

#### `formatFileSize(bytes, decimals?)`

Format file size in bytes to human-readable format.

```typescript
import { formatFileSize } from '@/utils';

formatFileSize(1024); // "1.00 KB"
formatFileSize(1048576); // "1.00 MB"
formatFileSize(1073741824); // "1.00 GB"
formatFileSize(1234567, 1); // "1.2 MB"
```

#### `formatNumber(num, separator?)`

Format a number with thousand separators.

```typescript
formatNumber(1234567); // "1,234,567"
formatNumber(1234567.89); // "1,234,567.89"
```

#### `formatPercentage(value, decimals?, isDecimal?)`

Format a percentage value.

```typescript
formatPercentage(0.5); // "50%"
formatPercentage(0.666, 2); // "66.60%"
formatPercentage(75, 0, false); // "75%"
```

#### Other Functions

- `truncateString(str, maxLength, ellipsis?)` - Truncate string with ellipsis
- `formatPhoneNumber(phone)` - Format phone number
- `capitalize(str)` - Capitalize first letter
- `toTitleCase(str)` - Convert to title case
- `getFileExtension(filename)` - Get file extension
- `getFileNameWithoutExtension(filename)` - Get filename without extension

---

## Avatar Utilities (`avatar.ts`)

Utilities for generating avatar colors and initials.

### Functions

#### `getAvatarColor(name)`

Generate a consistent color for a user based on their name. The same name will always produce the same color.

```typescript
import { getAvatarColor } from '@/utils';

getAvatarColor('张三'); // "#1890ff"
getAvatarColor('李四'); // "#52c41a"
getAvatarColor('张三'); // "#1890ff" (same as first call)
```

#### `getInitials(name)`

Get initials from a name.

**Rules:**
- Chinese names: Use the last character (usually the given name)
- English names: Use the first letter of first and last name
- Single word: Use the first character

```typescript
getInitials('张三'); // "三"
getInitials('李明华'); // "华"
getInitials('John Doe'); // "JD"
getInitials('Alice'); // "A"
```

#### `getAvatarStyle(name, size?)`

Generate avatar style object for use in React components.

```typescript
const style = getAvatarStyle('张三', 40);
// {
//   backgroundColor: '#1890ff',
//   color: '#fff',
//   width: 40,
//   height: 40,
//   fontSize: 16
// }

<div style={style}>{getInitials('张三')}</div>
```

#### `generateAvatarDataUrl(name, size?)`

Generate a data URL for an avatar image with initials. Can be used as an img src.

```typescript
const avatarUrl = generateAvatarDataUrl('张三', 40);
<img src={avatarUrl} alt="Avatar" />
```

#### Other Functions

- `getContrastColor(hexColor)` - Get contrasting text color (black or white) for a background color

---

## Usage Examples

### Complete Example: Contract Card Component

```typescript
import {
  formatRelativeTime,
  getAvatarColor,
  getInitials,
  formatFileSize,
} from '@/utils';

function ContractCard({ contract }) {
  return (
    <div className="contract-card">
      <div className="header">
        <div
          className="avatar"
          style={{
            backgroundColor: getAvatarColor(contract.initiator.name),
            color: '#fff',
          }}
        >
          {getInitials(contract.initiator.name)}
        </div>
        <div className="info">
          <h3>{contract.name}</h3>
          <p>{contract.initiator.name}</p>
        </div>
      </div>
      <div className="meta">
        <span>{formatRelativeTime(contract.createdAt)}</span>
        {contract.attachments && (
          <span>{formatFileSize(contract.attachments[0].size)}</span>
        )}
      </div>
    </div>
  );
}
```

### Complete Example: Contract List with Filtering

```typescript
import { useState } from 'react';
import { filterContracts, getFilterCount } from '@/utils';

function ContractList({ contracts, currentUserId }) {
  const [filter, setFilter] = useState('all');
  const [searchKeyword, setSearchKeyword] = useState('');

  const filteredContracts = filterContracts(
    contracts,
    filter,
    searchKeyword,
    currentUserId
  );

  const pendingCount = getFilterCount(contracts, '待我处理', currentUserId);

  return (
    <div>
      <div className="filters">
        <button onClick={() => setFilter('all')}>全部</button>
        <button onClick={() => setFilter('进行中')}>进行中</button>
        <button onClick={() => setFilter('已完成')}>已完成</button>
        <button onClick={() => setFilter('待我处理')}>
          待我处理 {pendingCount > 0 && <span>({pendingCount})</span>}
        </button>
        <button onClick={() => setFilter('抄送我')}>抄送我</button>
      </div>
      <input
        type="text"
        placeholder="搜索合同名称或发起人"
        value={searchKeyword}
        onChange={(e) => setSearchKeyword(e.target.value)}
      />
      <div className="list">
        {filteredContracts.map((contract) => (
          <ContractCard key={contract.id} contract={contract} />
        ))}
      </div>
    </div>
  );
}
```
