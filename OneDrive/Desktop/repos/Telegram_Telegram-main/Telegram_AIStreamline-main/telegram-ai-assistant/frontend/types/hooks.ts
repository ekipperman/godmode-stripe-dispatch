import { RefObject } from 'react'

// Auth Types
export interface User {
  id: string
  name: string
  email: string
  role: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Plugin Types
export interface PluginData {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  type: string
}

// Analytics Types
export interface AnalyticsMetric {
  name: string
  value: number
  change: number
  trend: 'up' | 'down' | 'neutral'
}

export interface AnalyticsData {
  metrics: AnalyticsMetric[]
  timeRange: string
}

// Message Types
export interface Message {
  id: string
  content: string
  sender: string
  timestamp: string
  status: 'sent' | 'delivered' | 'read'
}

// CRM Types
export interface Contact {
  id: string
  name: string
  email: string
  phone: string
  lastContact: string
}

// Social Media Types
export interface SocialPost {
  id: string
  content: string
  platform: string
  status: 'draft' | 'scheduled' | 'published'
  scheduledTime?: string
}

// Form Types
export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  validate?: (value: any) => boolean | string
}

export interface ValidationErrors {
  [key: string]: string
}

// Window Size Types
export interface WindowSize {
  width: number
  height: number
}

export interface Breakpoints {
  sm: number
  md: number
  lg: number
  xl: number
}

// Storage Types
export type SetValue<T> = (value: T | ((prevValue: T) => T)) => void
export type RemoveValue = () => void

// Focus Types
export interface UseFocusOptions {
  autoFocus?: boolean
  selectOnFocus?: boolean
  onFocus?: () => void
  onBlur?: () => void
}

export interface UseFocusTrapOptions {
  enabled?: boolean
  onEscape?: () => void
}
