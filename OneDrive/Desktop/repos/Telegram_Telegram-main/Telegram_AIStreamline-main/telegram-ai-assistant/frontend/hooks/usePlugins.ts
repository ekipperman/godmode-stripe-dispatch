import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { apiHelpers } from '../utils/api'
import { PluginData } from '../types'
import toast from 'react-hot-toast'
import { ERROR_MESSAGES, SUCCESS_MESSAGES } from '../utils/constants'

export function usePlugins() {
  const queryClient = useQueryClient()
  const [activePlugins, setActivePlugins] = useState<string[]>([])

  // Fetch plugins
  const { data: plugins, isLoading, error } = useQuery<PluginData[]>(
    'plugins',
    async () => {
      const response = await apiHelpers.getPlugins()
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: (data) => {
        const active = data
          .filter((plugin) => plugin.status === 'active')
          .map((plugin) => plugin.title)
        setActivePlugins(active)
      },
    }
  )

  // Toggle plugin mutation
  const togglePluginMutation = useMutation(
    async (pluginId: string) => {
      const response = await apiHelpers.togglePlugin(pluginId)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('plugins')
        toast.success(SUCCESS_MESSAGES.UPDATED)
      },
      onError: (error: Error) => {
        toast.error(error.message || ERROR_MESSAGES.GENERIC)
      },
    }
  )

  // Update plugin configuration mutation
  const updatePluginConfigMutation = useMutation(
    async ({ pluginId, config }: { pluginId: string; config: any }) => {
      const response = await apiHelpers.updatePluginConfig(pluginId, config)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('plugins')
        toast.success(SUCCESS_MESSAGES.SAVED)
      },
      onError: (error: Error) => {
        toast.error(error.message || ERROR_MESSAGES.GENERIC)
      },
    }
  )

  const togglePlugin = async (pluginId: string) => {
    try {
      await togglePluginMutation.mutateAsync(pluginId)
    } catch (error) {
      console.error('Error toggling plugin:', error)
    }
  }

  const updatePluginConfig = async (pluginId: string, config: any) => {
    try {
      await updatePluginConfigMutation.mutateAsync({ pluginId, config })
    } catch (error) {
      console.error('Error updating plugin config:', error)
    }
  }

  const isPluginActive = (pluginId: string) => {
    return activePlugins.includes(pluginId)
  }

  const getPluginByTitle = (title: string) => {
    return plugins?.find((plugin) => plugin.title === title)
  }

  const getActivePlugins = () => {
    return plugins?.filter((plugin) => plugin.status === 'active') || []
  }

  const getInactivePlugins = () => {
    return plugins?.filter((plugin) => plugin.status === 'inactive') || []
  }

  return {
    plugins,
    isLoading,
    error,
    activePlugins,
    togglePlugin,
    updatePluginConfig,
    isPluginActive,
    getPluginByTitle,
    getActivePlugins,
    getInactivePlugins,
    togglePluginMutation,
    updatePluginConfigMutation,
  }
}
