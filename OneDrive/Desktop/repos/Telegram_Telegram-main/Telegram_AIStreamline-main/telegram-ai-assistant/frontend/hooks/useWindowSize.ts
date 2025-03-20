import { useState, useEffect, useCallback } from 'react'

interface WindowSize {
  width: number
  height: number
}

interface Breakpoints {
  sm: number
  md: number
  lg: number
  xl: number
  '2xl': number
}

const defaultBreakpoints: Breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
}

interface UseWindowSizeOptions {
  breakpoints?: Breakpoints
  debounceDelay?: number
}

interface UseWindowSizeReturn extends WindowSize {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  breakpoint: keyof Breakpoints | null
  isBreakpoint: (breakpoint: keyof Breakpoints) => boolean
  isGreaterThan: (breakpoint: keyof Breakpoints) => boolean
  isLessThan: (breakpoint: keyof Breakpoints) => boolean
}

function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func(...args)
    }, wait)
  }
}

export function useWindowSize({
  breakpoints = defaultBreakpoints,
  debounceDelay = 250,
}: UseWindowSizeOptions = {}): UseWindowSizeReturn {
  const [windowSize, setWindowSize] = useState<WindowSize>({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  })

  const handleResize = useCallback(
    debounce(() => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    }, debounceDelay),
    [debounceDelay]
  )

  useEffect(() => {
    if (typeof window === 'undefined') return

    window.addEventListener('resize', handleResize)
    
    // Initial size
    handleResize()

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [handleResize])

  // Get current breakpoint
  const getCurrentBreakpoint = (): keyof Breakpoints | null => {
    if (typeof window === 'undefined') return null

    const sortedBreakpoints = Object.entries(breakpoints)
      .sort(([, a], [, b]) => b - a)

    for (const [name, minWidth] of sortedBreakpoints) {
      if (windowSize.width >= minWidth) {
        return name as keyof Breakpoints
      }
    }

    return null
  }

  const breakpoint = getCurrentBreakpoint()

  // Helper functions for responsive design
  const isBreakpoint = useCallback(
    (bp: keyof Breakpoints): boolean => {
      return breakpoint === bp
    },
    [breakpoint]
  )

  const isGreaterThan = useCallback(
    (bp: keyof Breakpoints): boolean => {
      return windowSize.width >= breakpoints[bp]
    },
    [windowSize.width, breakpoints]
  )

  const isLessThan = useCallback(
    (bp: keyof Breakpoints): boolean => {
      return windowSize.width < breakpoints[bp]
    },
    [windowSize.width, breakpoints]
  )

  // Common device type checks
  const isMobile = windowSize.width < breakpoints.md
  const isTablet = windowSize.width >= breakpoints.md && windowSize.width < breakpoints.lg
  const isDesktop = windowSize.width >= breakpoints.lg

  return {
    width: windowSize.width,
    height: windowSize.height,
    isMobile,
    isTablet,
    isDesktop,
    breakpoint,
    isBreakpoint,
    isGreaterThan,
    isLessThan,
  }
}

// Example usage:
/*
const {
  width,
  height,
  isMobile,
  isTablet,
  isDesktop,
  breakpoint,
  isBreakpoint,
  isGreaterThan,
  isLessThan,
} = useWindowSize({
  breakpoints: {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536,
  },
  debounceDelay: 250,
})

// Responsive rendering
if (isMobile) {
  return <MobileLayout />
}

if (isTablet) {
  return <TabletLayout />
}

return <DesktopLayout />

// Breakpoint checks
if (isBreakpoint('lg')) {
  // Large screen specific logic
}

// Comparative checks
if (isGreaterThan('md')) {
  // Larger than medium screens
}

if (isLessThan('xl')) {
  // Smaller than extra large screens
}
*/

// Utility function to get device type
export function getDeviceType(width: number): 'mobile' | 'tablet' | 'desktop' {
  if (width < defaultBreakpoints.md) {
    return 'mobile'
  }
  if (width < defaultBreakpoints.lg) {
    return 'tablet'
  }
  return 'desktop'
}

// Utility function to check if the device is touch-enabled
export function isTouchDevice(): boolean {
  if (typeof window === 'undefined') return false
  
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    // @ts-ignore
    navigator.msMaxTouchPoints > 0
  )
}
