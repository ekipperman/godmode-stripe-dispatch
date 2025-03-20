import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { apiHelpers } from '../utils/api'
import { Message } from '../types'
import toast from 'react-hot-toast'
import { ERROR_MESSAGES, SUCCESS_MESSAGES, MESSAGE_STATUS } from '../utils/constants'

interface UseMessagesProps {
  pageSize?: number
  initialPage?: number
}

interface MessagesResponse {
  messages: Message[]
  total: number
  page: number
  totalPages: number
}

export function useMessages({ pageSize = 10, initialPage = 1 }: UseMessagesProps = {}) {
  const queryClient = useQueryClient()
  const [currentPage, setCurrentPage] = useState(initialPage)

  // Fetch messages
  const {
    data: messagesData,
    isLoading,
    error,
    refetch,
  } = useQuery<MessagesResponse>(
    ['messages', currentPage],
    async () => {
      const response = await apiHelpers.getMessages(currentPage)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    }
  )

  // Send message mutation
  const sendMessageMutation = useMutation(
    async (content: string) => {
      // TODO: Implement actual message sending
      return {
        id: Date.now(),
        user_id: 1,
        content,
        type: 'text',
        created_at: new Date().toISOString(),
        status: MESSAGE_STATUS.PENDING,
      }
    },
    {
      onSuccess: (newMessage) => {
        queryClient.setQueryData<MessagesResponse>(['messages', currentPage], (old) => {
          if (!old) return { messages: [newMessage], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            messages: [newMessage, ...old.messages],
            total: old.total + 1,
          }
        })
        toast.success(SUCCESS_MESSAGES.SENT)
      },
      onError: (error: Error) => {
        toast.error(error.message || ERROR_MESSAGES.GENERIC)
      },
    }
  )

  // Send voice message mutation
  const sendVoiceMessageMutation = useMutation(
    async (audioBlob: Blob) => {
      // TODO: Implement voice message sending
      return {
        id: Date.now(),
        user_id: 1,
        content: 'Voice message',
        type: 'voice',
        created_at: new Date().toISOString(),
        status: MESSAGE_STATUS.PENDING,
      }
    },
    {
      onSuccess: (newMessage) => {
        queryClient.setQueryData<MessagesResponse>(['messages', currentPage], (old) => {
          if (!old) return { messages: [newMessage], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            messages: [newMessage, ...old.messages],
            total: old.total + 1,
          }
        })
        toast.success(SUCCESS_MESSAGES.SENT)
      },
      onError: (error: Error) => {
        toast.error(error.message || ERROR_MESSAGES.GENERIC)
      },
    }
  )

  const sendMessage = async (content: string) => {
    try {
      await sendMessageMutation.mutateAsync(content)
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }

  const sendVoiceMessage = async (audioBlob: Blob) => {
    try {
      await sendVoiceMessageMutation.mutateAsync(audioBlob)
    } catch (error) {
      console.error('Error sending voice message:', error)
    }
  }

  const goToPage = (page: number) => {
    if (page >= 1 && page <= (messagesData?.totalPages || 1)) {
      setCurrentPage(page)
    }
  }

  const nextPage = () => {
    if (currentPage < (messagesData?.totalPages || 1)) {
      setCurrentPage((prev) => prev + 1)
    }
  }

  const previousPage = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1)
    }
  }

  const getMessageById = (messageId: number): Message | undefined => {
    return messagesData?.messages.find((msg) => msg.id === messageId)
  }

  const getPendingMessages = (): Message[] => {
    return messagesData?.messages.filter((msg) => msg.status === MESSAGE_STATUS.PENDING) || []
  }

  const getFailedMessages = (): Message[] => {
    return messagesData?.messages.filter((msg) => msg.status === MESSAGE_STATUS.FAILED) || []
  }

  return {
    messages: messagesData?.messages || [],
    total: messagesData?.total || 0,
    currentPage,
    totalPages: messagesData?.totalPages || 1,
    isLoading,
    error,
    sendMessage,
    sendVoiceMessage,
    goToPage,
    nextPage,
    previousPage,
    refetch,
    getMessageById,
    getPendingMessages,
    getFailedMessages,
    sendMessageMutation,
    sendVoiceMessageMutation,
  }
}
