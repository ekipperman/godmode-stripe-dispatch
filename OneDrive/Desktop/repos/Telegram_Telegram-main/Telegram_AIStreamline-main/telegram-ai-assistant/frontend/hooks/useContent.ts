import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';
import { useAnalytics } from './useAnalytics';

interface WebsiteContent {
  title: string;
  description: string;
  cta?: string;
  generated_at: string;
}

interface VideoContent {
  outline: any;
  script: any;
  duration_estimate: number;
}

interface PodcastContent {
  outline: any;
  talking_points: any;
  script: any;
  duration_estimate: number;
}

interface BlogContent {
  title: string;
  meta_description: string;
  tags: string[];
  sections: Array<{
    title: string;
    content: string;
    keywords: string[];
  }>;
  estimated_read_time: number;
}

interface SocialContent {
  posts: any[];
  hashtags: string[];
  generated_at: string;
}

interface EmailContent {
  subject_lines: string[];
  body: {
    preview: string;
    content: string;
  };
  ctas: string[];
  preview_text: string;
  generated_at: string;
}

export const useContent = () => {
  const { user } = useAuth();
  const { trackEvent } = useAnalytics();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState<Record<string, any>>({});

  // Generate website content
  const generateWebsiteContent = useCallback(async (websiteData: {
    business_name: string;
    value_proposition: string;
    product_type: string;
    mission: string;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/content/website/generate', websiteData);
      
      if (response.data.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [response.data.content_id]: response.data.content
        }));
        
        await trackEvent('website_content_generated', {
          content_id: response.data.content_id
        });
      }
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [trackEvent]);

  // Generate video content
  const generateVideoContent = useCallback(async (videoData: {
    title: string;
    main_points: string[];
    style: string;
    duration: number;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/content/video/generate', videoData);
      
      if (response.data.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [response.data.content_id]: response.data.content
        }));
        
        await trackEvent('video_content_generated', {
          content_id: response.data.content_id
        });
      }
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [trackEvent]);

  // Generate podcast content
  const generatePodcastContent = useCallback(async (podcastData: {
    title: string;
    topics: string[];
    format: string;
    duration: number;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/content/podcast/generate', podcastData);
      
      if (response.data.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [response.data.content_id]: response.data.content
        }));
        
        await trackEvent('podcast_content_generated', {
          content_id: response.data.content_id
        });
      }
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [trackEvent]);

  // Generate blog post
  const generateBlogPost = useCallback(async (blogData: {
    title: string;
    topic: string;
    audience: string;
    keywords: string[];
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/content/blog/generate', blogData);
      
      if (response.data.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [response.data.content_id]: response.data.content
        }));
        
        await trackEvent('blog_content_generated', {
          content_id: response.data.content_id
        });
      }
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [trackEvent]);

  // Generate social media content
  const generateSocialContent = useCallback(async (socialData: {
    topic: string;
    audience: string;
    platforms: string[];
    tone: string;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/content/social/generate', socialData);
      
      if (response.data.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [response.data.content_id]: response.data.content
        }));
        
        await trackEvent('social_content_generated', {
          content_id: response.data.content_id
        });
      }
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [trackEvent]);

  // Generate email campaign
  const generateEmailCampaign = useCallback(async (campaignData: {
    campaign_type: string;
    audience: string;
    objective: string;
    tone: string;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/content/email/generate', campaignData);
      
      if (response.data.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [response.data.content_id]: response.data.content
        }));
        
        await trackEvent('email_content_generated', {
          content_id: response.data.content_id
        });
      }
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [trackEvent]);

  // Get generated content
  const getContent = useCallback((contentId: string) => {
    return generatedContent[contentId] || null;
  }, [generatedContent]);

  // Update generated content
  const updateContent = useCallback(async (contentId: string, updates: any) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.put(`/api/content/${contentId}/update`, updates);
      
      if (response.data.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [contentId]: {
            ...prev[contentId],
            ...updates
          }
        }));
        
        await trackEvent('content_updated', {
          content_id: contentId
        });
      }
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [trackEvent]);

  return {
    loading,
    error,
    generatedContent,
    generateWebsiteContent,
    generateVideoContent,
    generatePodcastContent,
    generateBlogPost,
    generateSocialContent,
    generateEmailCampaign,
    getContent,
    updateContent
  };
};
