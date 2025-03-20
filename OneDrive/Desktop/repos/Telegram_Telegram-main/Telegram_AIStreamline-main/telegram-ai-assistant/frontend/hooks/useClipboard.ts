import { useState, useCallback } from 'react'

interface UseClipboardOptions {
  timeout?: number
  onSuccess?: () => void
  onError?: (error: Error) => void
}

interface UseClipboardReturn {
  copied: boolean
  copy: (text: string) => Promise<void>
  copyFromElement: (element: HTMLElement) => Promise<void>
  clear: () => void
}

export function useClipboard({
  timeout = 2000,
  onSuccess,
  onError,
}: UseClipboardOptions = {}): UseClipboardReturn {
  const [copied, setCopied] = useState(false)

  // Clear the copied state after timeout
  const clear = useCallback(() => {
    setCopied(false)
  }, [])

  // Copy text to clipboard
  const copy = useCallback(
    async (text: string) => {
      try {
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(text)
        } else {
          // Fallback for older browsers
          const textArea = document.createElement('textarea')
          textArea.value = text
          textArea.style.position = 'fixed'
          textArea.style.left = '-999999px'
          textArea.style.top = '-999999px'
          document.body.appendChild(textArea)
          textArea.focus()
          textArea.select()
          document.execCommand('copy')
          textArea.remove()
        }

        setCopied(true)
        onSuccess?.()

        if (timeout) {
          setTimeout(clear, timeout)
        }
      } catch (error) {
        const err = error instanceof Error ? error : new Error('Failed to copy text')
        onError?.(err)
        console.error('Copy failed:', err)
      }
    },
    [timeout, clear, onSuccess, onError]
  )

  // Copy text from an HTML element
  const copyFromElement = useCallback(
    async (element: HTMLElement) => {
      try {
        const text = element.innerText || element.textContent || ''
        await copy(text)
      } catch (error) {
        const err = error instanceof Error ? error : new Error('Failed to copy from element')
        onError?.(err)
        console.error('Copy from element failed:', err)
      }
    },
    [copy, onError]
  )

  return {
    copied,
    copy,
    copyFromElement,
    clear,
  }
}

// Example usage:
/*
const { copied, copy, copyFromElement, clear } = useClipboard({
  timeout: 2000,
  onSuccess: () => {
    toast.success('Copied to clipboard!')
  },
  onError: (error) => {
    toast.error(`Failed to copy: ${error.message}`)
  },
})

// Copy text
<button onClick={() => copy('Text to copy')}>
  {copied ? 'Copied!' : 'Copy'}
</button>

// Copy from element
<div ref={elementRef}>Text to copy</div>
<button onClick={() => copyFromElement(elementRef.current)}>
  {copied ? 'Copied!' : 'Copy'}
</button>
*/

// Utility function to check if clipboard API is available
export function isClipboardAvailable(): boolean {
  return Boolean(
    typeof navigator !== 'undefined' &&
    navigator.clipboard &&
    typeof navigator.clipboard.writeText === 'function'
  )
}

// Utility function to read from clipboard
export async function readFromClipboard(): Promise<string> {
  try {
    if (navigator.clipboard && typeof navigator.clipboard.readText === 'function') {
      return await navigator.clipboard.readText()
    }
    throw new Error('Clipboard reading not supported')
  } catch (error) {
    throw error instanceof Error ? error : new Error('Failed to read from clipboard')
  }
}

// Utility function to copy multiple items to clipboard
export async function copyMultiple(items: string[]): Promise<void> {
  try {
    const text = items.join('\n')
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      textArea.remove()
    }
  } catch (error) {
    throw error instanceof Error ? error : new Error('Failed to copy multiple items')
  }
}

// Utility function to copy rich text (HTML) to clipboard
export async function copyRichText(html: string): Promise<void> {
  try {
    const blob = new Blob([html], { type: 'text/html' })
    const data = [new ClipboardItem({ 'text/html': blob })]
    
    if (navigator.clipboard && typeof navigator.clipboard.write === 'function') {
      await navigator.clipboard.write(data)
    } else {
      throw new Error('Rich text clipboard operations not supported')
    }
  } catch (error) {
    throw error instanceof Error ? error : new Error('Failed to copy rich text')
  }
}
