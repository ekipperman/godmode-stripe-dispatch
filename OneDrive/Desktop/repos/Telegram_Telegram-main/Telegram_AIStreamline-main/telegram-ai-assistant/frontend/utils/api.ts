import axios from 'axios'
import { APIResponse, AnalyticsData } from '../types'

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// API endpoints
export const endpoints = {
  // Bot management
  getBotStatus: () => '/bot/status',
  updateBotConfig: () => '/bot/config',
  
  // Plugin management
  getPlugins: () => '/plugins',
  togglePlugin: (pluginId: string) => `/plugins/${pluginId}/toggle`,
  updatePluginConfig: (pluginId: string) => `/plugins/${pluginId}/config`,
  
  // Analytics
  getDashboardStats: () => '/analytics/dashboard',
  getAnalytics: (timeRange: string) => `/analytics?timeRange=${timeRange}`,
  
  // Messages
  getMessages: (page: number) => `/messages?page=${page}`,
  getMessage: (id: string) => `/messages/${id}`,
  
  // CRM
  getContacts: (page: number) => `/crm/contacts?page=${page}`,
  createContact: () => '/crm/contacts',
  updateContact: (id: string) => `/crm/contacts/${id}`,
  
  // Social Media
  getPosts: (page: number) => `/social/posts?page=${page}`,
  createPost: () => '/social/posts',
  schedulePost: (id: string) => `/social/posts/${id}/schedule`,
  
  // Email Campaigns
  getCampaigns: (page: number) => `/email/campaigns?page=${page}`,
  createCampaign: () => '/email/campaigns',
  sendCampaign: (id: string) => `/email/campaigns/${id}/send`,
  
  // Automation
  getRules: (page: number) => `/automation/rules?page=${page}`,
  createRule: () => '/automation/rules',
  toggleRule: (id: string) => `/automation/rules/${id}/toggle`,
}

// API error handler
export const handleApiError = (error: any): string => {
  if (error.response) {
    // Server responded with error
    const data = error.response.data
    return data.error || 'An error occurred while processing your request'
  } else if (error.request) {
    // Request made but no response
    return 'Unable to connect to the server'
  } else {
    // Error setting up request
    return 'An error occurred while setting up the request'
  }
}

// Generic API request handler
export async function apiRequest<T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  endpoint: string,
  data?: any
): Promise<APIResponse<T>> {
  try {
    const response = await api.request({
      method,
      url: endpoint,
      data,
    })
    
    return {
      data: response.data,
      status: 'success',
    }
  } catch (error) {
    return {
      data: null as any,
      error: handleApiError(error),
      status: 'error',
    }
  }
}

// API helper functions
export const apiHelpers = {
  // Dashboard
  getDashboardData: async () => {
    return apiRequest('GET', endpoints.getDashboardStats())
  },
  
  // Plugin Management
  getPlugins: async () => {
    return apiRequest('GET', endpoints.getPlugins())
  },
  
  togglePlugin: async (pluginId: string) => {
    return apiRequest('POST', endpoints.togglePlugin(pluginId))
  },
  
  updatePluginConfig: async (pluginId: string, config: any) => {
    return apiRequest('PUT', endpoints.updatePluginConfig(pluginId), config)
  },
  
  // Analytics
  getAnalytics: async (timeRange: string) => {
    return apiRequest<AnalyticsData>('GET', endpoints.getAnalytics(timeRange))
  },
  
  // Messages
  getMessages: async (page: number = 1) => {
    return apiRequest('GET', endpoints.getMessages(page))
  },
  
  // CRM
  getContacts: async (page: number = 1) => {
    return apiRequest('GET', endpoints.getContacts(page))
  },
  
  createContact: async (contactData: any) => {
    return apiRequest('POST', endpoints.createContact(), contactData)
  },
  
  // Social Media
  getPosts: async (page: number = 1) => {
    return apiRequest('GET', endpoints.getPosts(page))
  },
  
  createPost: async (postData: any) => {
    return apiRequest('POST', endpoints.createPost(), postData)
  },
  
  schedulePost: async (postId: string, scheduleData: any) => {
    return apiRequest('POST', endpoints.schedulePost(postId), scheduleData)
  },
  
  // Email Campaigns
  getCampaigns: async (page: number = 1) => {
    return apiRequest('GET', endpoints.getCampaigns(page))
  },
  
  createCampaign: async (campaignData: any) => {
    return apiRequest('POST', endpoints.createCampaign(), campaignData)
  },
  
  // Automation
  getRules: async (page: number = 1) => {
    return apiRequest('GET', endpoints.getRules(page))
  },
  
  createRule: async (ruleData: any) => {
    return apiRequest('POST', endpoints.createRule(), ruleData)
  },
  
  toggleRule: async (ruleId: string) => {
    return apiRequest('POST', endpoints.toggleRule(ruleId))
  },
}

export default api
