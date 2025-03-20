import { useEffect, useCallback, useRef } from 'react'

type KeyCombo = string // e.g., 'ctrl+s', 'shift+a', 'meta+k'
type HotkeyCallback = (e: KeyboardEvent) => void
type HotkeyMap = Record<KeyCombo, HotkeyCallback>

interface HotkeyOptions {
  enabled?: boolean
  preventDefault?: boolean
  targetKey?: string
  keydown?: boolean
  keyup?: boolean
}

const defaultOptions: HotkeyOptions = {
  enabled: true,
  preventDefault: true,
  keydown: true,
  keyup: false,
}

function parseKeyCombo(combo: string): {
  ctrl: boolean
  shift: boolean
  alt: boolean
  meta: boolean
  key: string
} {
  const parts = combo.toLowerCase().split('+')
  return {
    ctrl: parts.includes('ctrl'),
    shift: parts.includes('shift'),
    alt: parts.includes('alt'),
    meta: parts.includes('meta'),
    key: parts[parts.length - 1],
  }
}

export function useHotkeys(
  hotkeys: HotkeyMap,
  options: HotkeyOptions = defaultOptions
) {
  const { enabled = true, preventDefault = true, keydown = true, keyup = false } = options

  // Use a ref to store hotkeys to prevent unnecessary effect triggers
  const hotkeysRef = useRef(hotkeys)
  hotkeysRef.current = hotkeys

  const handleKeyEvent = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return

      const eventKey = event.key.toLowerCase()
      const eventMeta = {
        ctrl: event.ctrlKey,
        shift: event.shiftKey,
        alt: event.altKey,
        meta: event.metaKey,
      }

      // Check each hotkey combination
      Object.entries(hotkeysRef.current).forEach(([combo, callback]) => {
        const { ctrl, shift, alt, meta, key } = parseKeyCombo(combo)

        // Check if the key combination matches
        if (
          key === eventKey &&
          ctrl === eventMeta.ctrl &&
          shift === eventMeta.shift &&
          alt === eventMeta.alt &&
          meta === eventMeta.meta
        ) {
          if (preventDefault) {
            event.preventDefault()
          }
          callback(event)
        }
      })
    },
    [enabled, preventDefault]
  )

  useEffect(() => {
    if (!enabled) return

    if (keydown) {
      document.addEventListener('keydown', handleKeyEvent)
    }
    if (keyup) {
      document.addEventListener('keyup', handleKeyEvent)
    }

    return () => {
      if (keydown) {
        document.removeEventListener('keydown', handleKeyEvent)
      }
      if (keyup) {
        document.removeEventListener('keyup', handleKeyEvent)
      }
    }
  }, [enabled, keydown, keyup, handleKeyEvent])

  // Return methods to programmatically trigger hotkeys
  const trigger = useCallback(
    (combo: KeyCombo) => {
      const callback = hotkeysRef.current[combo]
      if (callback) {
        callback(new KeyboardEvent('keydown'))
      }
    },
    []
  )

  return {
    trigger,
  }
}

// Example usage:
/*
const hotkeys = {
  'ctrl+s': (e) => {
    console.log('Save triggered')
    // Save functionality
  },
  'ctrl+shift+a': (e) => {
    console.log('Select all triggered')
    // Select all functionality
  },
  'meta+k': (e) => {
    console.log('Command palette triggered')
    // Open command palette
  },
}

const { trigger } = useHotkeys(hotkeys, {
  enabled: true,
  preventDefault: true,
})

// Programmatically trigger a hotkey
trigger('ctrl+s')
*/

// Utility function to create a hotkey map
export function createHotkeyMap(
  mappings: Record<string, HotkeyCallback>
): HotkeyMap {
  return Object.entries(mappings).reduce((acc, [combo, callback]) => {
    acc[combo.toLowerCase()] = callback
    return acc
  }, {} as HotkeyMap)
}

// Common hotkey combinations
export const commonHotkeys = {
  SAVE: 'ctrl+s',
  UNDO: 'ctrl+z',
  REDO: 'ctrl+shift+z',
  CUT: 'ctrl+x',
  COPY: 'ctrl+c',
  PASTE: 'ctrl+v',
  SELECT_ALL: 'ctrl+a',
  FIND: 'ctrl+f',
  NEW: 'ctrl+n',
  CLOSE: 'ctrl+w',
  REFRESH: 'ctrl+r',
  COMMAND_PALETTE: 'ctrl+shift+p',
} as const

// Platform-specific hotkey combinations
export const macHotkeys = {
  SAVE: 'meta+s',
  UNDO: 'meta+z',
  REDO: 'meta+shift+z',
  CUT: 'meta+x',
  COPY: 'meta+c',
  PASTE: 'meta+v',
  SELECT_ALL: 'meta+a',
  FIND: 'meta+f',
  NEW: 'meta+n',
  CLOSE: 'meta+w',
  REFRESH: 'meta+r',
  COMMAND_PALETTE: 'meta+shift+p',
} as const

// Detect platform and use appropriate hotkeys
export const platformHotkeys = 
  typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)
    ? macHotkeys
    : commonHotkeys
