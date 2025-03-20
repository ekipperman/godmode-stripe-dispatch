// Authentication
export { useAuth } from './useAuth'

// State Management
export { useAppState } from './useAppState'

// Plugin Management
export { usePlugins } from './usePlugins'

// Analytics
export { useAnalytics } from './useAnalytics'

// Messaging
export { useMessages } from './useMessages'
export { useMessaging } from './useMessaging'

// Social Media
export { useSocialMedia } from './useSocialMedia'

// CRM
export { useCRM } from './useCRM'

// Forms and Validation
export { useForm } from './useForm'

// UI and Interactions
export { useHotkeys } from './useHotkeys'
export { useInfiniteScroll } from './useInfiniteScroll'
export { useWindowSize } from './useWindowSize'
export { useClipboard } from './useClipboard'
export { useFocus } from './useFocus'

// Storage
export { useLocalStorage } from './useLocalStorage'

// Types
export type {
  // Auth Types
  User,
  AuthState,

  // Plugin Types
  PluginData,

  // Analytics Types
  AnalyticsData,
  AnalyticsMetric,

  // Message Types
  Message,

  // CRM Types
  Contact,

  // Social Media Types
  SocialPost,

  // Form Types
  ValidationRule,
  ValidationErrors,

  // Window Size Types
  WindowSize,
  Breakpoints,

  // Storage Types
  SetValue,
  RemoveValue,

  // Focus Types
  UseFocusOptions,
  UseFocusTrapOptions,
} from '../types/hooks'
