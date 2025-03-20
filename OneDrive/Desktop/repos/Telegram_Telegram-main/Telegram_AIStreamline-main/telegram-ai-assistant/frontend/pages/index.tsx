import React from 'react'
import { useQuery } from 'react-query'
import {
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  MegaphoneIcon,
  EnvelopeIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

// Stats card component
interface StatsCardProps {
  title: string
  value: string | number
  icon: React.ComponentType<any>
  change?: string
  changeType?: 'increase' | 'decrease'
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, change, changeType }) => (
  <div className="stats-card">
    <div className="flex items-center">
      <div className="flex-shrink-0">
        <Icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
      </div>
      <div className="ml-5 w-0 flex-1">
        <dl>
          <dt className="stats-label">{title}</dt>
          <dd className="stats-value">{value}</dd>
          {change && (
            <dd className={`text-sm ${changeType === 'increase' ? 'text-green-600' : 'text-red-600'}`}>
              {changeType === 'increase' ? '↑' : '↓'} {change}
            </dd>
          )}
        </dl>
      </div>
    </div>
  </div>
)

// Plugin card component
interface PluginCardProps {
  title: string
  description: string
  status: 'active' | 'inactive'
  icon: React.ComponentType<any>
}

const PluginCard: React.FC<PluginCardProps> = ({ title, description, status, icon: Icon }) => (
  <div className={`plugin-card ${status === 'active' ? 'plugin-card-active' : ''}`}>
    <div className="flex items-center">
      <div className="flex-shrink-0">
        <Icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
      </div>
      <div className="ml-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      </div>
    </div>
    <div className="mt-4">
      <span
        className={`badge ${
          status === 'active' ? 'badge-success' : 'badge-error'
        }`}
      >
        {status === 'active' ? 'Active' : 'Inactive'}
      </span>
    </div>
  </div>
)

export default function Dashboard() {
  // Fetch dashboard data
  const { data: dashboardData, isLoading } = useQuery('dashboard', async () => {
    // TODO: Replace with actual API call
    return {
      stats: {
        messages: { value: 1234, change: '12%', changeType: 'increase' as const },
        users: { value: 567, change: '8%', changeType: 'increase' as const },
        posts: { value: 89, change: '3%', changeType: 'decrease' as const },
        emails: { value: 456, change: '15%', changeType: 'increase' as const },
      },
      plugins: [
        {
          title: 'AI Chatbot',
          description: 'Intelligent responses powered by GPT',
          status: 'active' as const,
          icon: ChatBubbleLeftRightIcon,
        },
        {
          title: 'CRM Integration',
          description: 'Sync with HubSpot, Shopify & Stripe',
          status: 'active' as const,
          icon: UserGroupIcon,
        },
        {
          title: 'Social Media',
          description: 'Auto-post to LinkedIn, Twitter & Facebook',
          status: 'active' as const,
          icon: MegaphoneIcon,
        },
        {
          title: 'Email & SMS',
          description: 'Automated outreach campaigns',
          status: 'inactive' as const,
          icon: EnvelopeIcon,
        },
        {
          title: 'Analytics',
          description: 'Business insights and reporting',
          status: 'active' as const,
          icon: ChartBarIcon,
        },
      ],
    }
  })

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-gray-200 rounded mb-8"></div>
        <div className="grid gap-6 mb-8 md:grid-cols-2 xl:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded"></div>
          ))}
        </div>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-8">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid gap-6 mb-8 md:grid-cols-2 xl:grid-cols-4">
        <StatsCard
          title="Total Messages"
          value={dashboardData?.stats.messages.value || 0}
          icon={ChatBubbleLeftRightIcon}
          change={dashboardData?.stats.messages.change}
          changeType={dashboardData?.stats.messages.changeType}
        />
        <StatsCard
          title="Active Users"
          value={dashboardData?.stats.users.value || 0}
          icon={UserGroupIcon}
          change={dashboardData?.stats.users.change}
          changeType={dashboardData?.stats.users.changeType}
        />
        <StatsCard
          title="Social Posts"
          value={dashboardData?.stats.posts.value || 0}
          icon={MegaphoneIcon}
          change={dashboardData?.stats.posts.change}
          changeType={dashboardData?.stats.posts.changeType}
        />
        <StatsCard
          title="Emails Sent"
          value={dashboardData?.stats.emails.value || 0}
          icon={EnvelopeIcon}
          change={dashboardData?.stats.emails.change}
          changeType={dashboardData?.stats.emails.changeType}
        />
      </div>

      {/* Plugins Grid */}
      <h2 className="text-lg font-medium text-gray-900 mb-4">Active Plugins</h2>
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {dashboardData?.plugins.map((plugin, index) => (
          <PluginCard key={index} {...plugin} />
        ))}
      </div>
    </div>
  )
}
