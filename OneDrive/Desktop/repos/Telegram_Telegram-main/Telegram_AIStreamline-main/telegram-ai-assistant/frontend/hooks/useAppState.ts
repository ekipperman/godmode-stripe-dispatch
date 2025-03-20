import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react'
import { BotConfig } from '../types'

// State interface
interface AppState {
  isInitialized: boolean
  isLoading: boolean
  error: string | null
  config: BotConfig | null
  darkMode: boolean
}

// Action types
type AppAction =
  | { type: 'INITIALIZE' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CONFIG'; payload: BotConfig }
  | { type: 'TOGGLE_DARK_MODE' }

// Initial state
const initialState: AppState = {
  isInitialized: false,
  isLoading: false,
  error: null,
  config: null,
  darkMode: false
}

// Context
interface AppContextType {
  state: AppState
  initialize: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setConfig: (config: BotConfig) => void
  toggleDarkMode: () => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'INITIALIZE':
      return {
        ...state,
        isInitialized: true
      }
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      }
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload
      }
    case 'SET_CONFIG':
      return {
        ...state,
        config: action.payload
      }
    case 'TOGGLE_DARK_MODE':
      return {
        ...state,
        darkMode: !state.darkMode
      }
    default:
      return state
  }
}

// Provider component
interface AppProviderProps {
  children: ReactNode
}

export function AppProvider({ children }: AppProviderProps): JSX.Element {
  const [state, dispatch] = useReducer(appReducer, initialState)

  const initialize = useCallback(() => {
    dispatch({ type: 'INITIALIZE' })
  }, [])

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading })
  }, [])

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error })
  }, [])

  const setConfig = useCallback((config: BotConfig) => {
    dispatch({ type: 'SET_CONFIG', payload: config })
  }, [])

  const toggleDarkMode = useCallback(() => {
    dispatch({ type: 'TOGGLE_DARK_MODE' })
  }, [])

  const value = {
    state,
    initialize,
    setLoading,
    setError,
    setConfig,
    toggleDarkMode
  }

  return React.createElement(AppContext.Provider, { value }, children)
}

// Hook
export function useAppState(): AppContextType {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppProvider')
  }
  return context
}
