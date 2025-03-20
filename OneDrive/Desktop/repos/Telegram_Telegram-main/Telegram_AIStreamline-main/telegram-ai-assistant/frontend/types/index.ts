import type { ComponentType } from 'react'

type IconType = ComponentType<{ className?: string }>

export interface AnalyticsMetric {
  value: number
  change: number
  trend: 'up' | 'down' | 'stable'
}

export interface AnalyticsData {
  messages: AnalyticsMetric
  users: AnalyticsMetric
  engagement: AnalyticsMetric
  automation: AnalyticsMetric
  timeRange: {
    start: string
    end: string
  }
}

export interface StatsData {
  value: number
  change: string
  changeType: 'increase' | 'decrease'
}

export interface DashboardStats {
  messages: StatsData
  users: StatsData
  posts: StatsData
  emails: StatsData
}

export interface PluginData {
  title: string
  description: string
  status: 'active' | 'inactive'
  icon: IconType
}

export interface DashboardData {
  stats: DashboardStats
  plugins: PluginData[]
}

// Component Props Types
export interface StatsCardProps {
  title: string
  value: string | number
  icon: IconType
  change?: string
  changeType?: 'increase' | 'decrease'
}

export interface PluginCardProps {
  title: string
  description: string
  status: 'active' | 'inactive'
  icon: IconType
}

// API Response Types
export interface APIResponse<T> {
  data: T
  error?: string
  status: 'success' | 'error'
}

// Plugin Settings
export interface PluginSettings {
  enabled: boolean
  config: Record<string, any>
}

export interface BotConfig {
  telegram_token: string
  webhook_url: string
  plugins: Record<string, PluginSettings>
}

// Analytics Types
export interface AnalyticsMetric {
  value: number
  change: number
  trend: 'up' | 'down' | 'stable'
}

export interface AnalyticsData {
  messages: AnalyticsMetric
  users: AnalyticsMetric
  engagement: AnalyticsMetric
  automation: AnalyticsMetric
  timeRange: {
    start: string
    end: string
  }
}

// User Types
export interface User {
  id: number
  name: string
  email: string
  role: 'admin' | 'user'
  created_at: string
  last_active: string
}

// Message Types
export interface Message {
  id: number
  user_id: number
  content: string
  type: 'text' | 'voice' | 'command'
  created_at: string
  response?: string
  status: 'pending' | 'processed' | 'failed'
}

// CRM Types
export interface Contact {
  id: number
  name: string
  email: string
  phone?: string
  company?: string
  source: string
  created_at: string
  last_interaction: string
}

// Social Media Types
export interface SocialPost {
  id: number
  content: string
  platforms: ('linkedin' | 'twitter' | 'facebook')[]
  scheduled_for?: string
  status: 'draft' | 'scheduled' | 'published' | 'failed'
  created_at: string
  analytics?: {
    impressions: number
    engagements: number
    clicks: number
  }
}

// Email Campaign Types
export interface EmailCampaign {
  id: number
  name: string
  subject: string
  content: string
  recipients: number
  sent: number
  opened: number
  clicked: number
  status: 'draft' | 'scheduled' | 'sending' | 'completed'
  scheduled_for?: string
  created_at: string
}

// Automation Types
export interface AutomationRule {
  id: number
  name: string
  trigger: {
    type: 'message' | 'event' | 'schedule'
    conditions: Record<string, any>
  }
  actions: {
    type: string
    params: Record<string, any>
  }[]
  status: 'active' | 'inactive'
  created_at: string
  last_triggered?: string
}
