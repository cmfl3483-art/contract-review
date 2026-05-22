/**
 * Contract Filtering Utilities
 *
 * Utilities for filtering and searching contracts
 */

import type { Contract, FilterType } from '@/types';

/**
 * Filter contracts based on filter type and search keyword
 *
 * @param contracts - Array of contracts to filter
 * @param filter - Filter type
 * @param searchKeyword - Search keyword (searches in contract name and initiator name)
 * @param currentUserId - Current user ID (required for "待我处理" and "抄送我" filters)
 * @returns Filtered contracts
 *
 * @example
 * const filtered = filterContracts(contracts, '进行中', '');
 * const searched = filterContracts(contracts, 'all', '张三');
 * const pending = filterContracts(contracts, '待我处理', '', 'user123');
 */
export function filterContracts(
  contracts: Contract[],
  filter: FilterType,
  searchKeyword: string = '',
  currentUserId?: string
): Contract[] {
  let filtered = contracts;

  // Apply filter
  switch (filter) {
    case '进行中':
      filtered = contracts.filter((c) => c.status === 'progress');
      break;
    case '已完成':
      filtered = contracts.filter((c) => c.status === 'completed');
      break;
    case '待我处理':
      if (!currentUserId) {
        console.warn('filterContracts: currentUserId is required for "待我处理" filter');
        filtered = [];
      } else {
        filtered = contracts.filter((c) => c.hasPendingReview === true);
      }
      break;
    case '抄送我':
      if (!currentUserId) {
        console.warn('filterContracts: currentUserId is required for "抄送我" filter');
        filtered = [];
      } else {
        filtered = contracts.filter((c) => c.ccUsers?.includes(currentUserId));
      }
      break;
    case '我发起的':
      if (!currentUserId) {
        console.warn('filterContracts: currentUserId is required for "我发起的" filter');
        filtered = [];
      } else {
        filtered = contracts.filter((c) => c.initiatorId === currentUserId);
      }
      break;
    case 'all':
    default:
      filtered = contracts;
      break;
  }

  // Apply search keyword
  if (searchKeyword.trim()) {
    const keyword = searchKeyword.trim().toLowerCase();
    filtered = filtered.filter((c) => {
      const nameMatch = c.name.toLowerCase().includes(keyword);

      // Check initiator match
      let initiatorMatch = false;
      if (c.initiator && 'name' in c.initiator) {
        initiatorMatch = c.initiator.name.toLowerCase().includes(keyword);
      }

      return nameMatch || initiatorMatch;
    });
  }

  return filtered;
}

/**
 * Get the count of contracts matching a filter
 *
 * @param contracts - Array of contracts
 * @param filter - Filter type
 * @param currentUserId - Current user ID
 * @returns Count of matching contracts
 */
export function getFilterCount(
  contracts: Contract[],
  filter: FilterType,
  currentUserId?: string
): number {
  return filterContracts(contracts, filter, '', currentUserId).length;
}

/**
 * Check if a contract matches the search keyword
 *
 * @param contract - Contract to check
 * @param keyword - Search keyword
 * @returns True if the contract matches
 */
export function matchesSearch(contract: Contract, keyword: string): boolean {
  if (!keyword.trim()) return true;

  const lowerKeyword = keyword.trim().toLowerCase();
  const nameMatch = contract.name.toLowerCase().includes(lowerKeyword);

  // Check initiator match
  let initiatorMatch = false;
  if (contract.initiator && 'name' in contract.initiator) {
    initiatorMatch = contract.initiator.name.toLowerCase().includes(lowerKeyword);
  }

  return nameMatch || initiatorMatch;
}

/**
 * Sort contracts by a specific field
 *
 * @param contracts - Array of contracts to sort
 * @param field - Field to sort by
 * @param order - Sort order ('asc' or 'desc')
 * @returns Sorted contracts
 */
export function sortContracts(
  contracts: Contract[],
  field: keyof Contract,
  order: 'asc' | 'desc' = 'desc'
): Contract[] {
  return [...contracts].sort((a, b) => {
    const aValue = a[field];
    const bValue = b[field];

    if (aValue === undefined || aValue === null) return 1;
    if (bValue === undefined || bValue === null) return -1;

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return order === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
    }

    if (aValue < bValue) return order === 'asc' ? -1 : 1;
    if (aValue > bValue) return order === 'asc' ? 1 : -1;
    return 0;
  });
}
