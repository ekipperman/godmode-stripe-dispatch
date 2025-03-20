import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';
import { useAnalytics } from './useAnalytics';

interface TargetAudience {
  segment: string;
  score: number;
  channels: string[];
  content_topics: string[];
}

interface CampaignMetrics {
  impressions: number;
  clicks: number;
  conversions: number;
  cost: number;
}

interface ChannelMetrics extends CampaignMetrics {
  sent?: number;
  opened?: number;
  clicked?: number;
  converted?: number;
}

interface CampaignPerformance {
  campaign_id: string;
  status: string;
  duration: {
    start: string;
    end: string;
  };
  overall_metrics: CampaignMetrics;
  channel_metrics: {
    [channel: string]: ChannelMetrics;
  };
  derived_metrics: {
    cpc: number;
    cpa: number;
    conversion_rate: number;
  };
}

interface CampaignOptimization {
  type: string;
  action: string;
  reason: string;
  suggestions: string[];
}

export const useMarketing = () => {
  const { user } = useAuth();
  const { trackEvent } = useAnalytics();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [targetAudiences, setTargetAudiences] = useState<TargetAudience[]>([]);
  const [activeCampaigns, setActiveCampaigns] = useState<string[]>([]);

  // Identify target audience
  const identifyTargetAudience = useCallback(async (userData: any) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/marketing/identify-audience', userData);
      setTargetAudiences(response.data.segments);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create marketing campaign
  const createCampaign = useCallback(async (campaignData: {
    channels: string[];
    campaign_types?: string[];
    targeting?: any;
    keywords?: string[];
    email_sequence?: any[];
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/marketing/campaigns/create', campaignData);
      
      if (response.data.success) {
        setActiveCampaigns(prev => [...prev, response.data.campaign_id]);
        
        // Track campaign creation
        await trackEvent('campaign_created', {
          campaign_id: response.data.campaign_id,
          channels: campaignData.channels
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

  // Track campaign metrics
  const trackCampaignMetrics = useCallback(async (
    campaignId: string,
    channel: string,
    metrics: ChannelMetrics
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/marketing/campaigns/track', {
        campaign_id: campaignId,
        channel,
        metrics
      });
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get campaign performance
  const getCampaignPerformance = useCallback(async (campaignId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/marketing/campaigns/${campaignId}/performance`);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Optimize campaign
  const optimizeCampaign = useCallback(async (campaignId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post(`/api/marketing/campaigns/${campaignId}/optimize`);
      
      if (response.data.success) {
        // Track optimization event
        await trackEvent('campaign_optimized', {
          campaign_id: campaignId,
          optimizations: response.data.optimizations
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

  // Get recommended content topics
  const getContentRecommendations = useCallback(async (segment: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/marketing/content/recommendations', {
        params: { segment }
      });
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create email sequence
  const createEmailSequence = useCallback(async (sequenceData: {
    name: string;
    trigger: string;
    emails: Array<{
      subject: string;
      content: string;
      delay_days: number;
    }>;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/marketing/email/sequences/create', sequenceData);
      
      if (response.data.success) {
        // Track sequence creation
        await trackEvent('email_sequence_created', {
          sequence_id: response.data.sequence_id,
          name: sequenceData.name
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

  // Get campaign analytics
  const getCampaignAnalytics = useCallback(async (
    campaignId: string,
    dateRange?: { start: string; end: string }
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/marketing/campaigns/${campaignId}/analytics`, {
        params: dateRange
      });
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    targetAudiences,
    activeCampaigns,
    identifyTargetAudience,
    createCampaign,
    trackCampaignMetrics,
    getCampaignPerformance,
    optimizeCampaign,
    getContentRecommendations,
    createEmailSequence,
    getCampaignAnalytics
  };
};
