import { useEffect, useRef, useState } from 'react';

/**
 * useImageLazyLoad Hook
 * 
 * Implements lazy loading for images using Intersection Observer API.
 * Images are only loaded when they enter the viewport.
 * 
 * @param options - IntersectionObserver options
 * @returns Object with ref to attach to image element and loaded state
 * 
 * Usage:
 * ```tsx
 * const { ref, loaded } = useImageLazyLoad();
 * 
 * <img 
 *   ref={ref}
 *   src={loaded ? actualImageUrl : placeholderUrl}
 *   alt="Description"
 * />
 * ```
 */
export function useImageLazyLoad(options?: IntersectionObserverInit) {
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!imgRef.current) return;

    // Check if IntersectionObserver is supported
    if (!('IntersectionObserver' in window)) {
      // Fallback: load image immediately if IntersectionObserver is not supported
      setLoaded(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setLoaded(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.01,
        ...options,
      }
    );

    observer.observe(imgRef.current);

    return () => {
      observer.disconnect();
    };
  }, [options]);

  return { ref: imgRef, loaded };
}
