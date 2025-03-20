import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';

interface ContactData {
  email: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  tags?: string[];
  custom_fields?: Record<string, any>;
}

interface AutomationData {
  name: string;
  description?: string;
  trigger: {
    type: string;
    conditions: any[];
  };
  actions: {
    type: string;
    settings: any;
  }[];
  conditions?: any[];
}

interface EventData {
  name: string;
  contact_id: string;
  properties?: Record<string, any>;
  timestamp?: string;
}

interface SegmentData {
  name: string;
  description?: string;
  rules: {
    field: string;
    operator: string;
    value: any;
  }[];
}

interface WebhookData {
  url: string;
  events: string[];
  secret?: string;
}

interface SyncHistory {
  timestamp: string;
  entity_type: string;
  identifier: string;
  result: any;
}

export const useBoostIntegration = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncHistory, setSyncHistory] = useState<SyncHistory[]>([]);

  // Sync contact with Boost.space
  const syncContact = useCallback(async (contactData: ContactData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/boost/contacts', contactData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create automation in Boost.space
  const createAutomation = useCallback(async (automationData: AutomationData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/boost/automations', automationData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Enrich contact data using Boost.space
  const enrichContact = useCallback(async (email: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/boost/enrich', { email });
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Track event in Boost.space
  const trackEvent = useCallback(async (eventData: EventData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/boost/events', eventData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create segment in Boost.space
  const createSegment = useCallback(async (segmentData: SegmentData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/boost/segments', segmentData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Register webhook in Boost.space
  const registerWebhook = useCallback(async (webhookData: WebhookData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/boost/webhooks', webhookData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get sync history
  const getSyncHistory = useCallback(async (limit?: number) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/boost/history', {
        params: { limit }
      });
      setSyncHistory(response.data);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get workspace status
  const getWorkspaceStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/boost/status');
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Example usage of Boost.space features
  const enrichAndSyncContact = useCallback(async (contactData: ContactData) => {
    try {
      // First enrich the contact data
      const enrichedData = await enrichContact(contactData.email);
      
      // Merge enriched data with original data
      const mergedData = {
        ...contactData,
        ...enrichedData.enriched_data
      };
      
      // Sync the enriched contact
      const syncResult = await syncContact(mergedData);
      
      // Track sync event
      await trackEvent({
        name: 'contact_synced',
        contact_id: syncResult.contact_id,
        properties: {
          enriched: true,
          source: 'telegram_assistant'
        }
      });
      
      return syncResult;

    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [enrichContact, syncContact, trackEvent]);

  // Create automated segment
  const createAutomatedSegment = useCallback(async (
    segmentName: string,
    conditions: any[]
  ) => {
    try {
      // Create the segment
      const segment = await createSegment({
        name: segmentName,
        rules: conditions
      });
      
      // Create automation for the segment
      await createAutomation({
        name: `${segmentName} Automation`,
        trigger: {
          type: 'segment_membership',
          conditions: [{
            segment_id: segment.segment_id
          }]
        },
        actions: [{
          type: 'tag_contact',
          settings: {
            tags: [segmentName.toLowerCase()]
          }
        }]
      });
      
      return segment;

    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [createSegment, createAutomation]);

  return {
    loading,
    error,
    syncHistory,
    syncContact,
    createAutomation,
    enrichContact,
    trackEvent,
    createSegment,
    registerWebhook,
    getSyncHistory,
    getWorkspaceStatus,
    enrichAndSyncContact,
    createAutomatedSegment
  };
};
