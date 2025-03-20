import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';
import { useAnalytics } from './useAnalytics';

interface PLGFunnelConfig {
  trial_duration: number;
  trial_features: string[];
  freemium_features: string[];
  freemium_limits: Record<string, number>;
}

interface PLGMetrics {
  trial_signups: number;
  trial_conversions: number;
  freemium_users: number;
  paid_conversions: number;
}

interface InfluencerConfig {
  campaign_topic: string;
  target_audience: string;
  platforms: string[];
  base_commission: number;
  bonus_tiers: Array<{
    threshold: number;
    rate: number;
  }>;
  payout_schedule: string;
}

interface InfluencerMetrics {
  reach: number;
  clicks: number;
  conversions: number;
  revenue: number;
}

interface CROExperiment {
  type: 'landing_page' | 'email';
  target_metrics: string[];
  user_segment?: string;
  duration: number;
  variants: Record<string, any>;
}

interface CROMetrics {
  impressions: number;
  conversions: number;
  revenue: number;
}

export const useGrowth = () => {
  const { user } = useAuth();
  const { trackEvent } = useAnalytics();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFunnels, setActiveFunnels] = useState<string[]>([]);
  const [activePrograms, setActivePrograms] = useState<string[]>([]);
  const [activeExperiments, setActiveExperiments] = useState<string[]>([]);

  // Set up PLG funnel
  const setupPLGFunnel = useCallback(async (funnelData: {
    business_name: string;
    value_proposition: string;
    trial_duration: number;
    trial_features: string[];
    freemium_features: string[];
    freemium_limits: Record<string, number>;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/growth/plg/setup', funnelData);
      
      if (response.data.success) {
        setActiveFunnels(prev => [...prev, response.data.funnel_id]);
        
        await trackEvent('plg_funnel_created', {
          funnel_id: response.data.funnel_id
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

  // Set up influencer program
  const setupInfluencerProgram = useCallback(async (programData: InfluencerConfig) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/growth/influencer/setup', programData);
      
      if (response.data.success) {
        setActivePrograms(prev => [...prev, response.data.program_id]);
        
        await trackEvent('influencer_program_created', {
          program_id: response.data.program_id
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

  // Set up CRO experiment
  const setupCROExperiment = useCallback(async (experimentData: CROExperiment) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/growth/cro/setup', experimentData);
      
      if (response.data.success) {
        setActiveExperiments(prev => [...prev, response.data.experiment_id]);
        
        await trackEvent('cro_experiment_created', {
          experiment_id: response.data.experiment_id
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

  // Track PLG metrics
  const trackPLGMetrics = useCallback(async (
    funnelId: string,
    eventType: 'trial_signup' | 'trial_conversion' | 'freemium_signup' | 'paid_conversion'
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/growth/plg/track', {
        funnel_id: funnelId,
        type: eventType
      });
      
      if (response.data.success) {
        await trackEvent('plg_event_tracked', {
          funnel_id: funnelId,
          event_type: eventType
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

  // Track influencer metrics
  const trackInfluencerMetrics = useCallback(async (
    programId: string,
    influencerId: string,
    metrics: InfluencerMetrics
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/growth/influencer/track', {
        program_id: programId,
        influencer_id: influencerId,
        metrics
      });
      
      if (response.data.success) {
        await trackEvent('influencer_metrics_tracked', {
          program_id: programId,
          influencer_id: influencerId
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

  // Track CRO metrics
  const trackCROMetrics = useCallback(async (
    experimentId: string,
    variantId: string,
    eventType: 'impression' | 'conversion',
    revenue?: number
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/growth/cro/track', {
        experiment_id: experimentId,
        variant_id: variantId,
        type: eventType,
        revenue
      });
      
      if (response.data.success) {
        await trackEvent('cro_event_tracked', {
          experiment_id: experimentId,
          variant_id: variantId,
          event_type: eventType
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

  // Get PLG funnel performance
  const getPLGPerformance = useCallback(async (funnelId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/growth/plg/${funnelId}/performance`);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get influencer program performance
  const getInfluencerPerformance = useCallback(async (programId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/growth/influencer/${programId}/performance`);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get CRO experiment results
  const getCROResults = useCallback(async (experimentId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/growth/cro/${experimentId}/results`);
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
    activeFunnels,
    activePrograms,
    activeExperiments,
    setupPLGFunnel,
    setupInfluencerProgram,
    setupCROExperiment,
    trackPLGMetrics,
    trackInfluencerMetrics,
    trackCROMetrics,
    getPLGPerformance,
    getInfluencerPerformance,
    getCROResults
  };
};
