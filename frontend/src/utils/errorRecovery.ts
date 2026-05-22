/**
 * Error Recovery Utilities
 * 
 * Provides utilities for error recovery and resilience
 */

/**
 * Retry a function with exponential backoff
 * 
 * @param fn - Function to retry
 * @param maxRetries - Maximum number of retries
 * @param baseDelay - Base delay in milliseconds
 * @returns Promise with the result
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // Don't retry on last attempt
      if (attempt === maxRetries) {
        break;
      }

      // Calculate delay with exponential backoff
      const delay = baseDelay * Math.pow(2, attempt);
      
      console.log(`[Retry] Attempt ${attempt + 1}/${maxRetries} failed, retrying in ${delay}ms...`);
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
}

/**
 * Execute a function with timeout
 * 
 * @param fn - Function to execute
 * @param timeoutMs - Timeout in milliseconds
 * @returns Promise with the result or timeout error
 */
export async function withTimeout<T>(
  fn: () => Promise<T>,
  timeoutMs: number
): Promise<T> {
  return Promise.race([
    fn(),
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`Operation timed out after ${timeoutMs}ms`)), timeoutMs)
    ),
  ]);
}

/**
 * Circuit breaker pattern implementation
 * Prevents cascading failures by stopping requests after repeated failures
 */
export class CircuitBreaker {
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private readonly failureThreshold: number = 5,
    private readonly resetTimeout: number = 60000 // 1 minute
  ) {}

  /**
   * Execute a function with circuit breaker protection
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // Check if circuit is open
    if (this.state === 'open') {
      const timeSinceLastFailure = Date.now() - this.lastFailureTime;
      
      if (timeSinceLastFailure < this.resetTimeout) {
        throw new Error('Circuit breaker is open - service unavailable');
      }
      
      // Try to close the circuit (half-open state)
      this.state = 'half-open';
    }

    try {
      const result = await fn();
      
      // Success - reset circuit breaker
      this.onSuccess();
      
      return result;
    } catch (error) {
      // Failure - record and potentially open circuit
      this.onFailure();
      
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.state = 'closed';
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.failureThreshold) {
      this.state = 'open';
      console.warn('[CircuitBreaker] Circuit opened due to repeated failures');
    }
  }

  /**
   * Get current circuit breaker state
   */
  getState(): 'closed' | 'open' | 'half-open' {
    return this.state;
  }

  /**
   * Manually reset the circuit breaker
   */
  reset(): void {
    this.failureCount = 0;
    this.state = 'closed';
  }
}

/**
 * Debounce error notifications to prevent spam
 */
export class ErrorNotificationDebouncer {
  private lastNotificationTime: Map<string, number> = new Map();
  private readonly debounceTime: number = 5000; // 5 seconds

  /**
   * Check if an error notification should be shown
   * 
   * @param errorKey - Unique key for the error type
   * @returns true if notification should be shown
   */
  shouldNotify(errorKey: string): boolean {
    const now = Date.now();
    const lastTime = this.lastNotificationTime.get(errorKey);

    if (!lastTime || now - lastTime > this.debounceTime) {
      this.lastNotificationTime.set(errorKey, now);
      return true;
    }

    return false;
  }

  /**
   * Clear debounce state for a specific error
   */
  clear(errorKey: string): void {
    this.lastNotificationTime.delete(errorKey);
  }

  /**
   * Clear all debounce state
   */
  clearAll(): void {
    this.lastNotificationTime.clear();
  }
}

/**
 * Global error notification debouncer instance
 */
export const errorDebouncer = new ErrorNotificationDebouncer();

/**
 * Safe JSON parse with fallback
 * 
 * @param json - JSON string to parse
 * @param fallback - Fallback value if parsing fails
 * @returns Parsed object or fallback
 */
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json) as T;
  } catch (error) {
    console.warn('[SafeJsonParse] Failed to parse JSON:', error);
    return fallback;
  }
}

/**
 * Safe localStorage operations with error handling
 */
export const safeLocalStorage = {
  getItem(key: string, fallback: string | null = null): string | null {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.warn(`[SafeLocalStorage] Failed to get item "${key}":`, error);
      return fallback;
    }
  },

  setItem(key: string, value: string): boolean {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      console.warn(`[SafeLocalStorage] Failed to set item "${key}":`, error);
      return false;
    }
  },

  removeItem(key: string): boolean {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.warn(`[SafeLocalStorage] Failed to remove item "${key}":`, error);
      return false;
    }
  },

  clear(): boolean {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.warn('[SafeLocalStorage] Failed to clear storage:', error);
      return false;
    }
  },
};

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

/**
 * Classify error severity based on error type
 */
export function classifyErrorSeverity(error: Error): ErrorSeverity {
  const message = error.message.toLowerCase();

  // Critical errors
  if (
    message.includes('network') ||
    message.includes('timeout') ||
    message.includes('connection')
  ) {
    return ErrorSeverity.CRITICAL;
  }

  // High severity errors
  if (
    message.includes('unauthorized') ||
    message.includes('forbidden') ||
    message.includes('authentication')
  ) {
    return ErrorSeverity.HIGH;
  }

  // Medium severity errors
  if (
    message.includes('validation') ||
    message.includes('invalid') ||
    message.includes('not found')
  ) {
    return ErrorSeverity.MEDIUM;
  }

  // Default to low severity
  return ErrorSeverity.LOW;
}

/**
 * Format error for user display
 */
export function formatErrorMessage(error: Error | unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message);
  }

  return '发生了未知错误';
}
