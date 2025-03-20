import { useRef, useEffect, useCallback, RefObject } from 'react'

interface UseFocusOptions {
  autoFocus?: boolean
  selectOnFocus?: boolean
  onFocus?: () => void
  onBlur?: () => void
}

interface UseFocusReturn<T extends HTMLElement> {
  ref: RefObject<T>
  isFocused: boolean
  focus: () => void
  blur: () => void
  select: () => void
}

export function useFocus<T extends HTMLElement>({
  autoFocus = false,
  selectOnFocus = false,
  onFocus,
  onBlur,
}: UseFocusOptions = {}): UseFocusReturn<T> {
  const ref = useRef<T>(null)
  const [isFocused, setIsFocused] = useState(false)

  // Focus the element
  const focus = useCallback(() => {
    if (ref.current) {
      ref.current.focus()
      if (selectOnFocus && 'select' in ref.current) {
        ;(ref.current as HTMLInputElement | HTMLTextAreaElement).select()
      }
    }
  }, [selectOnFocus])

  // Blur the element
  const blur = useCallback(() => {
    if (ref.current) {
      ref.current.blur()
    }
  }, [])

  // Select the element's content
  const select = useCallback(() => {
    if (ref.current && 'select' in ref.current) {
      ;(ref.current as HTMLInputElement | HTMLTextAreaElement).select()
    }
  }, [])

  // Handle focus events
  const handleFocus = useCallback(() => {
    setIsFocused(true)
    onFocus?.()
  }, [onFocus])

  // Handle blur events
  const handleBlur = useCallback(() => {
    setIsFocused(false)
    onBlur?.()
  }, [onBlur])

  // Set up focus and blur event listeners
  useEffect(() => {
    const element = ref.current
    if (!element) return

    element.addEventListener('focus', handleFocus)
    element.addEventListener('blur', handleBlur)

    if (autoFocus) {
      focus()
    }

    return () => {
      element.removeEventListener('focus', handleFocus)
      element.removeEventListener('blur', handleBlur)
    }
  }, [autoFocus, focus, handleFocus, handleBlur])

  return {
    ref,
    isFocused,
    focus,
    blur,
    select,
  }
}

// Focus trap hook for modals and dialogs
interface UseFocusTrapOptions {
  enabled?: boolean
  onEscape?: () => void
}

export function useFocusTrap<T extends HTMLElement>({
  enabled = true,
  onEscape,
}: UseFocusTrapOptions = {}) {
  const ref = useRef<T>(null)

  useEffect(() => {
    if (!enabled) return

    const element = ref.current
    if (!element) return

    // Get all focusable elements
    const getFocusableElements = () => {
      return element.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onEscape?.()
        return
      }

      if (e.key !== 'Tab') return

      const focusableElements = getFocusableElements()
      const firstFocusableElement = focusableElements[0]
      const lastFocusableElement = focusableElements[focusableElements.length - 1]

      if (e.shiftKey) {
        // If shift key pressed for shift + tab combination
        if (document.activeElement === firstFocusableElement) {
          lastFocusableElement?.focus()
          e.preventDefault()
        }
      } else {
        // If tab key pressed
        if (document.activeElement === lastFocusableElement) {
          firstFocusableElement?.focus()
          e.preventDefault()
        }
      }
    }

    // Focus first element when trap is enabled
    const firstFocusableElement = getFocusableElements()[0]
    firstFocusableElement?.focus()

    element.addEventListener('keydown', handleKeyDown)
    return () => {
      element.removeEventListener('keydown', handleKeyDown)
    }
  }, [enabled, onEscape])

  return ref
}

// Example usage:
/*
// Basic focus management
const { ref, isFocused, focus, blur, select } = useFocus<HTMLInputElement>({
  autoFocus: true,
  selectOnFocus: true,
  onFocus: () => console.log('Input focused'),
  onBlur: () => console.log('Input blurred'),
})

<input
  ref={ref}
  type="text"
  className={isFocused ? 'focused' : ''}
/>

// Focus trap for modals
const modalRef = useFocusTrap<HTMLDivElement>({
  enabled: isOpen,
  onEscape: closeModal,
})

<div ref={modalRef} role="dialog">
  <button>First focusable</button>
  <input type="text" />
  <button>Last focusable</button>
</div>
*/

// Utility function to check if an element is focusable
export function isFocusable(element: HTMLElement): boolean {
  if (!element) return false

  return (
    element.tabIndex >= 0 ||
    element.tagName === 'BUTTON' ||
    element.tagName === 'INPUT' ||
    element.tagName === 'SELECT' ||
    element.tagName === 'TEXTAREA' ||
    element.hasAttribute('href')
  )
}

// Utility function to get the next focusable element
export function getNextFocusableElement(
  container: HTMLElement,
  currentElement: HTMLElement
): HTMLElement | null {
  const focusableElements = Array.from(
    container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
  )

  const currentIndex = focusableElements.indexOf(currentElement)
  if (currentIndex === -1) return null

  const nextIndex = (currentIndex + 1) % focusableElements.length
  return focusableElements[nextIndex]
}

// Utility function to restore focus to an element
export function restoreFocus(element: HTMLElement | null): void {
  if (element && typeof element.focus === 'function') {
    try {
      element.focus()
    } catch (e) {
      console.warn('Failed to restore focus:', e)
    }
  }
}
