/**
 * API Response Types
 *
 * Standard response format for all API endpoints
 */

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
  field?: string;
  requestId?: string;
}

/**
 * API Error response
 */
export interface ApiError {
  success: false;
  error: string;
  code?: string;
  field?: string;
  requestId?: string;
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}
