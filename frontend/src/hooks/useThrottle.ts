import { useRef, useCallback } from 'react';

/**
 * useThrottle Hook
 * 
 * Creates a throttled version of a callback function that only executes
 * at most once per specified delay period.
 * 
 * @param callback - The function to throttle
 * @param delay - The throttle delay in milliseconds
 * @returns Throttled version of the callback
 * 
 * Usage:
 * ```tsx
 * const handleScroll = useThrottle(() => {
 *   console.log('Scrolling...');
 * }, 200);
 * 
 * <div onScroll={handleScroll}>...</div>
 * ```
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const lastRun = useRef(Date.now());
  const timeoutRef = useRef<number | null>(null);

  return useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRun.current;

      if (timeSinceLastRun >= delay) {
        callback(...args);
        lastRun.current = now;
      } else {
        // Schedule the callback to run after the remaining delay
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = window.setTimeout(() => {
          callback(...args);
          lastRun.current = Date.now();
        }, delay - timeSinceLastRun);
      }
    },
    [callback, delay]
  );
}
