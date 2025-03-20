import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { apiHelpers } from '../utils/api'
import { EmailCampaign } from '../types'
import toast from 'react-hot-toast'
import { ERROR_MESSAGES, SUCCESS_MESSAGES, CAMPAIGN_STATUS } from '../utils/constants'

interface UseMessagingProps {
  pageSize?: number
  initialPage?: number
}

interface MessagingResponse {
  campaigns: EmailCampaign[]
  total: number
  page: number
  totalPages: number
}

interface CreateCampaignData {
  name: string
  subject: string
  content: string
  recipients: string[]
  scheduledFor?: string
}

export function useMessaging({ pageSize = 10, initialPage = 1 }: UseMessagingProps = {}) {
  const queryClient = useQueryClient()
  const [currentPage, setCurrentPage] = useState(initialPage)

  // Fetch campaigns
  const {
    data: campaignsData,
    isLoading,
    error,
    refetch,
  } = useQuery<MessagingResponse>(
    ['campaigns', currentPage],
    async () => {
      const response = await apiHelpers.getCampaigns(currentPage)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    }
  )

  // Create campaign mutation
  const createCampaignMutation = useMutation<EmailCampaign, Error, CreateCampaignData>(
    async (campaignData) => {
      const response = await apiHelpers.createCampaign(campaignData)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: (newCampaign) => {
        queryClient.setQueryData<MessagingResponse>(['campaigns', currentPage], (old) => {
          if (!old) return { campaigns: [newCampaign], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            campaigns: [newCampaign, ...old.campaigns],
            total: old.total + 1,
          }
        })
        toast.success(SUCCESS_MESSAGES.CREATED)
      },
      onError: (error: Error) => {
        toast.error(error.message || ERROR_MESSAGES.GENERIC)
      },
    }
  )

  // Send campaign mutation
  const sendCampaignMutation = useMutation<EmailCampaign, Error, string>(
    async (campaignId) => {
      const response = await apiHelpers.sendCampaign(campaignId)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: (updatedCampaign) => {
        queryClient.setQueryData<MessagingResponse>(['campaigns', currentPage], (old) => {
          if (!old) return { campaigns: [updatedCampaign], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            campaigns: old.campaigns.map((campaign) =>
              campaign.id === updatedCampaign.id ? updatedCampaign : campaign
            ),
          }
        })
        toast.success(SUCCESS_MESSAGES.SENT)
      },
      onError: (error: Error) => {
        toast.error(error.message || ERROR_MESSAGES.GENERIC)
      },
    }
  )

  const createCampaign = async (campaignData: CreateCampaignData) => {
    try {
      await createCampaignMutation.mutateAsync(campaignData)
    } catch (error) {
      console.error('Error creating campaign:', error)
    }
  }

  const sendCampaign = async (campaignId: string) => {
    try {
      await sendCampaignMutation.mutateAsync(campaignId)
    } catch (error) {
      console.error('Error sending campaign:', error)
    }
  }

  const goToPage = (page: number) => {
    if (page >= 1 && page <= (campaignsData?.totalPages || 1)) {
      setCurrentPage(page)
    }
  }

  const getCampaignById = (campaignId: number): EmailCampaign | undefined => {
    return campaignsData?.campaigns.find((campaign) => campaign.id === campaignId)
  }

  const getCampaignsByStatus = (status: keyof typeof CAMPAIGN_STATUS): EmailCampaign[] => {
    return campaignsData?.campaigns.filter((campaign) => campaign.status === status) || []
  }

  const getDraftCampaigns = (): EmailCampaign[] => {
    return getCampaignsByStatus('DRAFT')
  }

  const getScheduledCampaigns = (): EmailCampaign[] => {
    return getCampaignsByStatus('SCHEDULED')
  }

  const getSendingCampaigns = (): EmailCampaign[] => {
    return getCampaignsByStatus('SENDING')
  }

  const getCompletedCampaigns = (): EmailCampaign[] => {
    return getCampaignsByStatus('COMPLETED')
  }

  const getCampaignStats = () => {
    if (!campaignsData?.campaigns) {
      return {
        total: 0,
        sent: 0,
        opened: 0,
        clicked: 0,
        averageOpenRate: 0,
        averageClickRate: 0,
      }
    }

    const stats = campaignsData.campaigns.reduce(
      (acc, campaign) => {
        acc.sent += campaign.sent
        acc.opened += campaign.opened
        acc.clicked += campaign.clicked
        return acc
      },
      { sent: 0, opened: 0, clicked: 0 }
    )

    const totalCampaigns = campaignsData.campaigns.length
    const averageOpenRate = stats.sent > 0 ? (stats.opened / stats.sent) * 100 : 0
    const averageClickRate = stats.opened > 0 ? (stats.clicked / stats.opened) * 100 : 0

    return {
      total: totalCampaigns,
      ...stats,
      averageOpenRate: Math.round(averageOpenRate * 10) / 10,
      averageClickRate: Math.round(averageClickRate * 10) / 10,
    }
  }

  return {
    campaigns: campaignsData?.campaigns || [],
    total: campaignsData?.total || 0,
    currentPage,
    totalPages: campaignsData?.totalPages || 1,
    isLoading,
    error,
    createCampaign,
    sendCampaign,
    goToPage,
    getCampaignById,
    getCampaignsByStatus,
    getDraftCampaigns,
    getScheduledCampaigns,
    getSendingCampaigns,
    getCompletedCampaigns,
    getCampaignStats,
    createCampaignMutation,
    sendCampaignMutation,
    refetch,
  }
}
