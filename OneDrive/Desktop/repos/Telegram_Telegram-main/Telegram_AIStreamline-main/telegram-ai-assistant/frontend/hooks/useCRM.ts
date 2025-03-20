import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { apiHelpers } from '../utils/api'
import { Contact } from '../types'
import toast from 'react-hot-toast'
import { ERROR_MESSAGES, SUCCESS_MESSAGES } from '../utils/constants'

interface UseCRMProps {
  pageSize?: number
  initialPage?: number
}

interface CRMResponse {
  contacts: Contact[]
  total: number
  page: number
  totalPages: number
}

interface CreateContactData {
  name: string
  email: string
  phone?: string
  company?: string
  source: string
}

export function useCRM({ pageSize = 10, initialPage = 1 }: UseCRMProps = {}) {
  const queryClient = useQueryClient()
  const [currentPage, setCurrentPage] = useState(initialPage)

  // Fetch contacts
  const {
    data: contactsData,
    isLoading,
    error,
    refetch,
  } = useQuery<CRMResponse>(
    ['contacts', currentPage],
    async () => {
      const response = await apiHelpers.getContacts(currentPage)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    }
  )

  // Create contact mutation
  const createContactMutation = useMutation<Contact, Error, CreateContactData>(
    async (contactData) => {
      const response = await apiHelpers.createContact(contactData)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: (newContact) => {
        queryClient.setQueryData<CRMResponse>(['contacts', currentPage], (old) => {
          if (!old) return { contacts: [newContact], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            contacts: [newContact, ...old.contacts],
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

  // Update contact mutation
  const updateContactMutation = useMutation<Contact, Error, { id: number; data: Partial<Contact> }>(
    async ({ id, data }) => {
      const response = await apiHelpers.updateContact(id.toString(), data)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: (updatedContact) => {
        queryClient.setQueryData<CRMResponse>(['contacts', currentPage], (old) => {
          if (!old) return { contacts: [updatedContact], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            contacts: old.contacts.map((contact) =>
              contact.id === updatedContact.id ? updatedContact : contact
            ),
          }
        })
        toast.success(SUCCESS_MESSAGES.UPDATED)
      },
      onError: (error: Error) => {
        toast.error(error.message || ERROR_MESSAGES.GENERIC)
      },
    }
  )

  const createContact = async (contactData: CreateContactData) => {
    try {
      await createContactMutation.mutateAsync(contactData)
    } catch (error) {
      console.error('Error creating contact:', error)
    }
  }

  const updateContact = async (id: number, data: Partial<Contact>) => {
    try {
      await updateContactMutation.mutateAsync({ id, data })
    } catch (error) {
      console.error('Error updating contact:', error)
    }
  }

  const goToPage = (page: number) => {
    if (page >= 1 && page <= (contactsData?.totalPages || 1)) {
      setCurrentPage(page)
    }
  }

  const getContactById = (contactId: number): Contact | undefined => {
    return contactsData?.contacts.find((contact) => contact.id === contactId)
  }

  const getContactsBySource = (source: string): Contact[] => {
    return contactsData?.contacts.filter((contact) => contact.source === source) || []
  }

  const getContactsByCompany = (company: string): Contact[] => {
    return contactsData?.contacts.filter((contact) => contact.company === company) || []
  }

  const getRecentContacts = (days: number = 7): Contact[] => {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - days)

    return (
      contactsData?.contacts.filter((contact) => {
        const contactDate = new Date(contact.created_at)
        return contactDate >= cutoffDate
      }) || []
    )
  }

  const getContactStats = () => {
    if (!contactsData?.contacts) return { total: 0, bySource: {}, byCompany: {} }

    const stats = contactsData.contacts.reduce(
      (acc, contact) => {
        // Count by source
        acc.bySource[contact.source] = (acc.bySource[contact.source] || 0) + 1

        // Count by company
        if (contact.company) {
          acc.byCompany[contact.company] = (acc.byCompany[contact.company] || 0) + 1
        }

        return acc
      },
      { total: contactsData.total, bySource: {}, byCompany: {} } as {
        total: number
        bySource: Record<string, number>
        byCompany: Record<string, number>
      }
    )

    return stats
  }

  return {
    contacts: contactsData?.contacts || [],
    total: contactsData?.total || 0,
    currentPage,
    totalPages: contactsData?.totalPages || 1,
    isLoading,
    error,
    createContact,
    updateContact,
    goToPage,
    getContactById,
    getContactsBySource,
    getContactsByCompany,
    getRecentContacts,
    getContactStats,
    createContactMutation,
    updateContactMutation,
    refetch,
  }
}
