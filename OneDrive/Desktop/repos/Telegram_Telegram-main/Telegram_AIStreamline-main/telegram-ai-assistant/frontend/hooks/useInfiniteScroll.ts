import { useState, useEffect, useCallback, useRef, RefObject } from 'react'

interface UseInfiniteScrollOptions {
  threshold?: number
  rootMargin?: string
  enabled?: boolean
  onLoadMore: () => Promise<void>
  hasMore: boolean
}

interface UseInfiniteScrollReturn {
  observerRef: (node: Element | null) => void
  isLoading: boolean
  error: Error | null
}

export function useInfiniteScroll({
  threshold = 1.0,
  rootMargin = '50px',
  enabled = true,
  onLoadMore,
  hasMore,
}: UseInfiniteScrollOptions): UseInfiniteScrollReturn {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const observer = useRef<IntersectionObserver | null>(null)
  const lastElementRef = useRef<Element | null>(null)

  const handleObserver = useCallback(
    async (entries: IntersectionObserverEntry[]) => {
      const target = entries[0]

      if (target.isIntersecting && hasMore && !isLoading && enabled) {
        setIsLoading(true)
        setError(null)

        try {
          await onLoadMore()
        } catch (err) {
          setError(err instanceof Error ? err : new Error('Failed to load more items'))
        } finally {
          setIsLoading(false)
        }
      }
    },
    [hasMore, isLoading, enabled, onLoadMore]
  )

  const observerRef = useCallback(
    (node: Element | null) => {
      if (isLoading) return

      if (observer.current) {
        observer.current.disconnect()
      }

      observer.current = new IntersectionObserver(handleObserver, {
        root: null,
        rootMargin,
        threshold,
      })

      lastElementRef.current = node

      if (node) {
        observer.current.observe(node)
      }
    },
    [handleObserver, isLoading, rootMargin, threshold]
  )

  // Cleanup observer on unmount
  useEffect(() => {
    return () => {
      if (observer.current) {
        observer.current.disconnect()
      }
    }
  }, [])

  return {
    observerRef,
    isLoading,
    error,
  }
}

// Hook for handling pagination
interface UsePaginationOptions {
  initialPage?: number
  initialPageSize?: number
  total?: number
}

interface UsePaginationReturn {
  page: number
  pageSize: number
  setPage: (page: number) => void
  setPageSize: (size: number) => void
  totalPages: number
  hasNextPage: boolean
  hasPreviousPage: boolean
  nextPage: () => void
  previousPage: () => void
  firstPage: () => void
  lastPage: () => void
  pageRange: number[]
}

export function usePagination({
  initialPage = 1,
  initialPageSize = 10,
  total = 0,
}: UsePaginationOptions = {}): UsePaginationReturn {
  const [page, setPage] = useState(initialPage)
  const [pageSize, setPageSize] = useState(initialPageSize)

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const hasNextPage = page < totalPages
  const hasPreviousPage = page > 1

  const nextPage = useCallback(() => {
    if (hasNextPage) {
      setPage((p) => p + 1)
    }
  }, [hasNextPage])

  const previousPage = useCallback(() => {
    if (hasPreviousPage) {
      setPage((p) => p - 1)
    }
  }, [hasPreviousPage])

  const firstPage = useCallback(() => {
    setPage(1)
  }, [])

  const lastPage = useCallback(() => {
    setPage(totalPages)
  }, [totalPages])

  // Generate page range (e.g., [1, 2, 3, 4, 5] for current page)
  const pageRange = useCallback(() => {
    const delta = 2 // Number of pages to show before and after current page
    const range: number[] = []
    const rangeWithDots: number[] = []

    for (
      let i = Math.max(2, page - delta);
      i <= Math.min(totalPages - 1, page + delta);
      i++
    ) {
      range.push(i)
    }

    if (page - delta > 2) {
      range.unshift(-1) // Add dots
    }
    if (page + delta < totalPages - 1) {
      range.push(-1) // Add dots
    }

    range.unshift(1) // Always add first page
    if (totalPages !== 1) {
      range.push(totalPages) // Always add last page
    }

    return range
  }, [page, totalPages])()

  return {
    page,
    pageSize,
    setPage,
    setPageSize,
    totalPages,
    hasNextPage,
    hasPreviousPage,
    nextPage,
    previousPage,
    firstPage,
    lastPage,
    pageRange,
  }
}

// Example usage:
/*
// Infinite Scroll
const { observerRef, isLoading, error } = useInfiniteScroll({
  onLoadMore: async () => {
    // Load more data
    await loadMoreItems()
  },
  hasMore: true, // Set this based on your data
})

// Use the ref on your last element
<div ref={observerRef}>Last Item</div>

// Pagination
const {
  page,
  pageSize,
  setPage,
  setPageSize,
  totalPages,
  hasNextPage,
  hasPreviousPage,
  nextPage,
  previousPage,
  firstPage,
  lastPage,
  pageRange,
} = usePagination({
  initialPage: 1,
  initialPageSize: 10,
  total: 100,
})
*/
