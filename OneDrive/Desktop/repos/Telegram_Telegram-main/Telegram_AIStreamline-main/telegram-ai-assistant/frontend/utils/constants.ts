// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  TIMEOUT: 30000, // 30 seconds
}

// Authentication
export const AUTH_CONFIG = {
  TOKEN_KEY: 'telegram_assistant_token',
  REFRESH_TOKEN_KEY: 'telegram_assistant_refresh_token',
}

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
}

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM DD, YYYY',
  DISPLAY_WITH_TIME: 'MMM DD, YYYY HH:mm',
  API: 'YYYY-MM-DD',
  API_WITH_TIME: 'YYYY-MM-DDTHH:mm:ss',
}

// Plugin Types
export const PLUGIN_TYPES = {
  AI_CHATBOT: 'ai_chatbot',
  VOICE_COMMAND: 'voice_command',
  CRM: 'crm',
  SOCIAL_MEDIA: 'social_media',
  MESSAGING: 'messaging',
  ANALYTICS: 'analytics',
} as const

// Plugin Status
export const PLUGIN_STATUS = {
  ACTIVE: 'ACTIVE',
  INACTIVE: 'INACTIVE'
} as const

// Message Types
export const MESSAGE_TYPES = {
  TEXT: 'text',
  VOICE: 'voice',
  COMMAND: 'command',
} as const

// Message Status
export const MESSAGE_STATUS = {
  PENDING: 'PENDING',
  PROCESSED: 'PROCESSED',
  FAILED: 'FAILED',
} as const

// Social Media Platforms
export const SOCIAL_PLATFORMS = {
  LINKEDIN: 'LINKEDIN',
  TWITTER: 'TWITTER',
  FACEBOOK: 'FACEBOOK',
} as const

// Post Status
export const POST_STATUS = {
  DRAFT: 'DRAFT',
  SCHEDULED: 'SCHEDULED',
  PUBLISHED: 'PUBLISHED',
  FAILED: 'FAILED',
} as const

// Campaign Status
export const CAMPAIGN_STATUS = {
  DRAFT: 'DRAFT',
  SCHEDULED: 'SCHEDULED',
  SENDING: 'SENDING',
  COMPLETED: 'COMPLETED',
} as const

// Analytics Time Ranges
export const TIME_RANGES = {
  TODAY: 'TODAY',
  YESTERDAY: 'YESTERDAY',
  LAST_7_DAYS: 'LAST_7_DAYS',
  LAST_30_DAYS: 'LAST_30_DAYS',
  THIS_MONTH: 'THIS_MONTH',
  LAST_MONTH: 'LAST_MONTH',
  CUSTOM: 'CUSTOM',
} as const

export type TimeRange = typeof TIME_RANGES[keyof typeof TIME_RANGES]

// Chart Colors
export const CHART_COLORS = {
  PRIMARY: '#0ea5e9',
  SECONDARY: '#64748b',
  SUCCESS: '#22c55e',
  DANGER: '#ef4444',
  WARNING: '#f59e0b',
  INFO: '#3b82f6',
  BACKGROUND: '#f8fafc',
  TEXT: '#1e293b',
}

// Toast Configuration
export const TOAST_CONFIG = {
  DURATION: 5000,
  POSITION: 'top-right',
  STYLE: {
    background: '#363636',
    color: '#fff',
  },
}

// Route Paths
export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  CHAT: '/chat',
  CRM: '/crm',
  SOCIAL: '/social',
  MESSAGING: '/messaging',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
} as const

// Navigation Items
export const NAV_ITEMS = [
  { name: 'Dashboard', path: ROUTES.DASHBOARD, icon: 'HomeIcon' },
  { name: 'Chat History', path: ROUTES.CHAT, icon: 'ChatBubbleLeftRightIcon' },
  { name: 'CRM', path: ROUTES.CRM, icon: 'UserGroupIcon' },
  { name: 'Social Media', path: ROUTES.SOCIAL, icon: 'MegaphoneIcon' },
  { name: 'Messaging', path: ROUTES.MESSAGING, icon: 'EnvelopeIcon' },
  { name: 'Analytics', path: ROUTES.ANALYTICS, icon: 'ChartBarIcon' },
  { name: 'Settings', path: ROUTES.SETTINGS, icon: 'CogIcon' },
]

// Form Validation Rules
export const VALIDATION_RULES = {
  EMAIL: {
    pattern: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
    message: 'Invalid email address',
  },
  PASSWORD: {
    minLength: 8,
    message: 'Password must be at least 8 characters',
  },
  PHONE: {
    pattern: /^\+?[1-9]\d{1,14}$/,
    message: 'Invalid phone number',
  },
}

// Error Messages
export const ERROR_MESSAGES = {
  GENERIC: 'An error occurred. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION: 'Please check your input and try again.',
  SERVER: 'Server error. Please try again later.',
}

// Success Messages
export const SUCCESS_MESSAGES = {
  SAVED: 'Changes saved successfully.',
  CREATED: 'Created successfully.',
  UPDATED: 'Updated successfully.',
  DELETED: 'Deleted successfully.',
  SENT: 'Sent successfully.',
}

// Local Storage Keys
export const STORAGE_KEYS = {
  THEME: 'telegram_assistant_theme',
  LANGUAGE: 'telegram_assistant_language',
  USER_PREFERENCES: 'telegram_assistant_preferences',
}
