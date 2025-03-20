import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';

interface VisitorData {
  anonymous_id?: string;
  ip_address?: string;
  user_agent?: string;
  referrer?: string;
  page_url?: string;
  custom_data?: Record<string, any>;
}

interface SegmentData {
  name: string;
  description?: string;
  rules: {
    field: string;
    operator: string;
    value: any;
  }[];
  update_frequency?: 'realtime' | 'hourly' | 'daily';
}

interface EventData {
  visitor_id: string;
  event_name: string;
  properties?: Record<string, any>;
  timestamp?: string;
}

interface MatchData {
  visitor_id: string;
  identifiers: {
    email?: string;
    phone?: string;
    custom_id?: string;
    [key: string]: any;
  };
  confidence_threshold?: number;
}

interface TrackingHistory {
  timestamp: string;
  action_type: string;
  identifier: string;
  result: any;
}

export const useAudienceLab = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trackingHistory, setTrackingHistory] = useState<TrackingHistory[]>([]);

  // Initialize SuperPixel
  const initializeSuperpixel = useCallback(async () => {
    try {
      const script = document.createElement('script');
      script.src = 'https://cdn.audiencelab.io/superpixel.js';
      script.async = true;
      document.head.appendChild(script);

      return new Promise((resolve) => {
        script.onload = resolve;
      });
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, []);

  // Identify visitor
  const identifyVisitor = useCallback(async (visitorData: VisitorData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/audiencelab/identify', visitorData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create segment
  const createSegment = useCallback(async (segmentData: SegmentData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/audiencelab/segments', segmentData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Track event
  const trackEvent = useCallback(async (eventData: EventData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/audiencelab/events', eventData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Match profiles
  const matchProfiles = useCallback(async (matchData: MatchData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/audiencelab/match', matchData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get segment members
  const getSegmentMembers = useCallback(async (segmentId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/audiencelab/segments/${segmentId}/members`);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get visitor profile
  const getVisitorProfile = useCallback(async (visitorId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/audiencelab/visitors/${visitorId}/profile`);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get tracking history
  const getTrackingHistory = useCallback(async (limit?: number) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/audiencelab/history', {
        params: { limit }
      });
      setTrackingHistory(response.data);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get SuperPixel status
  const getSuperpixelStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/audiencelab/superpixel/status');
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Helper function to identify and track visitor
  const identifyAndTrackVisitor = useCallback(async (
    visitorData: VisitorData,
    eventName: string,
    eventProperties?: Record<string, any>
  ) => {
    try {
      // First identify the visitor
      const identifyResult = await identifyVisitor(visitorData);
      
      if (identifyResult.success) {
        // Then track the event
        await trackEvent({
          visitor_id: identifyResult.visitor_id,
          event_name: eventName,
          properties: eventProperties
        });
        
        return identifyResult;
      }
      
      throw new Error('Failed to identify visitor');

    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [identifyVisitor, trackEvent]);

  // Create dynamic segment based on behavior
  const createBehavioralSegment = useCallback(async (
    name: string,
    eventName: string,
    threshold: number
  ) => {
    try {
      return await createSegment({
        name,
        rules: [{
          field: `events.${eventName}.count`,
          operator: 'greater_than',
          value: threshold
        }],
        update_frequency: 'realtime'
      });

    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [createSegment]);

  return {
    loading,
    error,
    trackingHistory,
    initializeSuperpixel,
    identifyVisitor,
    createSegment,
    trackEvent,
    matchProfiles,
    getSegmentMembers,
    getVisitorProfile,
    getTrackingHistory,
    getSuperpixelStatus,
    identifyAndTrackVisitor,
    createBehavioralSegment
  };
};
