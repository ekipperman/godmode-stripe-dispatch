import { useState, useEffect, useCallback } from 'react'

type SetValue<T> = T | ((prevValue: T) => T)
type RemoveValue = () => void

interface UseLocalStorageReturn<T> {
  value: T
  setValue: (value: SetValue<T>) => void
  remove: RemoveValue
}

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: {
    serialize?: (value: T) => string
    deserialize?: (value: string) => T
    onError?: (error: Error) => void
  } = {}
): UseLocalStorageReturn<T> {
  const {
    serialize = JSON.stringify,
    deserialize = JSON.parse,
    onError = console.error,
  } = options

  // Get initial value from localStorage or use initialValue
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue
    }

    try {
      const item = window.localStorage.getItem(key)
      return item ? deserialize(item) : initialValue
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Failed to get stored value'))
      return initialValue
    }
  })

  // Return a wrapped version of useState's setter function that persists the new value to localStorage
  const setValue = useCallback(
    (value: SetValue<T>) => {
      try {
        // Allow value to be a function so we have same API as useState
        const valueToStore = value instanceof Function ? value(storedValue) : value
        setStoredValue(valueToStore)

        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, serialize(valueToStore))
        }
      } catch (error) {
        onError(error instanceof Error ? error : new Error('Failed to set stored value'))
      }
    },
    [key, serialize, storedValue, onError]
  )

  // Remove value from localStorage
  const remove = useCallback(() => {
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key)
        setStoredValue(initialValue)
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Failed to remove stored value'))
    }
  }, [key, initialValue, onError])

  // Sync with other windows/tabs
  useEffect(() => {
    function handleStorageChange(e: StorageEvent) {
      if (e.key === key) {
        try {
          const newValue = e.newValue ? deserialize(e.newValue) : initialValue
          setStoredValue(newValue)
        } catch (error) {
          onError(error instanceof Error ? error : new Error('Failed to sync stored value'))
        }
      }
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('storage', handleStorageChange)
      return () => window.removeEventListener('storage', handleStorageChange)
    }
  }, [key, deserialize, initialValue, onError])

  return { value: storedValue, setValue, remove }
}

// Example usage with type safety:
/*
interface UserPreferences {
  theme: 'light' | 'dark'
  fontSize: number
  notifications: boolean
}

const { value: preferences, setValue: setPreferences } = useLocalStorage<UserPreferences>(
  'user_preferences',
  {
    theme: 'light',
    fontSize: 16,
    notifications: true,
  }
)

// Usage with custom serialization
const { value: complexData, setValue: setComplexData } = useLocalStorage(
  'complex_data',
  initialComplexData,
  {
    serialize: (value) => btoa(JSON.stringify(value)),
    deserialize: (value) => JSON.parse(atob(value)),
    onError: (error) => {
      console.error('Storage error:', error)
      // Handle error (e.g., show notification)
    },
  }
)
*/

// Utility function to check if localStorage is available
export function isLocalStorageAvailable(): boolean {
  try {
    const testKey = '__storage_test__'
    localStorage.setItem(testKey, testKey)
    localStorage.removeItem(testKey)
    return true
  } catch (e) {
    return false
  }
}

// Utility function to get total localStorage usage
export function getLocalStorageUsage(): {
  used: number
  total: number
  percentage: number
} {
  try {
    let total = 0
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key) {
        total += localStorage.getItem(key)?.length || 0
      }
    }

    // Most browsers have a limit of 5-10MB
    const limit = 5 * 1024 * 1024 // 5MB in bytes
    return {
      used: total,
      total: limit,
      percentage: (total / limit) * 100,
    }
  } catch (e) {
    return {
      used: 0,
      total: 0,
      percentage: 0,
    }
  }
}

// Utility function to clear all items in localStorage
export function clearLocalStorage(): void {
  try {
    localStorage.clear()
  } catch (e) {
    console.error('Failed to clear localStorage:', e)
  }
}

// Utility function to get all keys in localStorage
export function getLocalStorageKeys(): string[] {
  try {
    return Object.keys(localStorage)
  } catch (e) {
    console.error('Failed to get localStorage keys:', e)
    return []
  }
}

// Utility function to get multiple items from localStorage
export function getMultipleItems(keys: string[]): Record<string, any> {
  try {
    return keys.reduce((acc, key) => {
      const value = localStorage.getItem(key)
      if (value) {
        try {
          acc[key] = JSON.parse(value)
        } catch {
          acc[key] = value
        }
      }
      return acc
    }, {} as Record<string, any>)
  } catch (e) {
    console.error('Failed to get multiple items:', e)
    return {}
  }
}
