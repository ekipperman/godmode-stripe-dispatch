import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { apiHelpers } from '../utils/api'
import { SocialPost } from '../types'
import { SOCIAL_PLATFORMS, POST_STATUS } from '../utils/constants'
import toast from 'react-hot-toast'

interface UseSocialMediaProps {
  pageSize?: number
  initialPage?: number
}

interface SocialMediaResponse {
  posts: SocialPost[]
  total: number
  page: number
  totalPages: number
}

interface CreatePostData {
  content: string
  platforms: (keyof typeof SOCIAL_PLATFORMS)[]
  scheduledFor?: string
  media?: string[]
}

export function useSocialMedia({ pageSize = 10, initialPage = 1 }: UseSocialMediaProps = {}) {
  const queryClient = useQueryClient()
  const [currentPage, setCurrentPage] = useState(initialPage)

  // Fetch social media posts
  const {
    data: postsData,
    isLoading,
    error,
    refetch,
  } = useQuery<SocialMediaResponse>(
    ['social-posts', currentPage],
    async () => {
      const response = await apiHelpers.getPosts(currentPage)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    }
  )

  // Create post mutation
  const createPostMutation = useMutation(
    async (postData: CreatePostData) => {
      const response = await apiHelpers.createPost(postData)
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: (newPost) => {
        queryClient.setQueryData<SocialMediaResponse>(['social-posts', currentPage], (old) => {
          if (!old) return { posts: [newPost], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            posts: [newPost, ...old.posts],
            total: old.total + 1,
          }
        })
        toast.success('Post created successfully')
      },
      onError: (error: Error) => {
        toast.error(error.message || 'Failed to create post')
      },
    }
  )

  // Schedule post mutation
  const schedulePostMutation = useMutation(
    async ({ postId, scheduledFor }: { postId: string; scheduledFor: string }) => {
      const response = await apiHelpers.schedulePost(postId, { scheduledFor })
      if (response.status === 'error') {
        throw new Error(response.error)
      }
      return response.data
    },
    {
      onSuccess: (updatedPost) => {
        queryClient.setQueryData<SocialMediaResponse>(['social-posts', currentPage], (old) => {
          if (!old) return { posts: [updatedPost], total: 1, page: 1, totalPages: 1 }
          return {
            ...old,
            posts: old.posts.map((post) =>
              post.id === updatedPost.id ? updatedPost : post
            ),
          }
        })
        toast.success('Post scheduled successfully')
      },
      onError: (error: Error) => {
        toast.error(error.message || 'Failed to schedule post')
      },
    }
  )

  const createPost = async (postData: CreatePostData) => {
    try {
      await createPostMutation.mutateAsync(postData)
    } catch (error) {
      console.error('Error creating post:', error)
    }
  }

  const schedulePost = async (postId: string, scheduledFor: string) => {
    try {
      await schedulePostMutation.mutateAsync({ postId, scheduledFor })
    } catch (error) {
      console.error('Error scheduling post:', error)
    }
  }

  const goToPage = (page: number) => {
    if (page >= 1 && page <= (postsData?.totalPages || 1)) {
      setCurrentPage(page)
    }
  }

  const getPostsByPlatform = (platform: keyof typeof SOCIAL_PLATFORMS): SocialPost[] => {
    return (
      postsData?.posts.filter((post) => post.platforms.includes(platform)) || []
    )
  }

  const getPostsByStatus = (status: keyof typeof POST_STATUS): SocialPost[] => {
    return postsData?.posts.filter((post) => post.status === status) || []
  }

  const getScheduledPosts = (): SocialPost[] => {
    return getPostsByStatus('scheduled')
  }

  const getFailedPosts = (): SocialPost[] => {
    return getPostsByStatus('failed')
  }

  const getDraftPosts = (): SocialPost[] => {
    return getPostsByStatus('draft')
  }

  const getPublishedPosts = (): SocialPost[] => {
    return getPostsByStatus('published')
  }

  const getPostAnalytics = (postId: number) => {
    const post = postsData?.posts.find((p) => p.id === postId)
    return post?.analytics || { impressions: 0, engagements: 0, clicks: 0 }
  }

  const getTotalEngagement = () => {
    return (
      postsData?.posts.reduce(
        (total, post) => total + (post.analytics?.engagements || 0),
        0
      ) || 0
    )
  }

  const getTotalImpressions = () => {
    return (
      postsData?.posts.reduce(
        (total, post) => total + (post.analytics?.impressions || 0),
        0
      ) || 0
    )
  }

  const getTotalClicks = () => {
    return (
      postsData?.posts.reduce(
        (total, post) => total + (post.analytics?.clicks || 0),
        0
      ) || 0
    )
  }

  return {
    posts: postsData?.posts || [],
    total: postsData?.total || 0,
    currentPage,
    totalPages: postsData?.totalPages || 1,
    isLoading,
    error,
    createPost,
    schedulePost,
    goToPage,
    getPostsByPlatform,
    getPostsByStatus,
    getScheduledPosts,
    getFailedPosts,
    getDraftPosts,
    getPublishedPosts,
    getPostAnalytics,
    getTotalEngagement,
    getTotalImpressions,
    getTotalClicks,
    createPostMutation,
    schedulePostMutation,
    refetch,
  }
}
