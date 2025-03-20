import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';
import { useAnalytics } from './useAnalytics';

interface BotConfig {
  token: string;
  group_id: string;
  channel_id: string;
}

interface BroadcastMessage {
  type: 'text' | 'image' | 'video';
  content: string;
  buttons?: Array<{
    text: string;
    url?: string;
    callback_data?: string;
  }>;
  schedule?: Date;
}

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  action?: string;
}

interface SupportTicket {
  id: string;
  user_id: number;
  issue_type: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved';
  created_at: string;
}

export const useTelegramBot = () => {
  const { user } = useAuth();
  const { trackEvent } = useAnalytics();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeChats, setActiveChats] = useState<number[]>([]);
  const [supportTickets, setSupportTickets] = useState<SupportTicket[]>([]);

  // Initialize bot
  const initializeBot = useCallback(async (config: BotConfig) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/telegram/bot/initialize', config);
      
      if (response.data.success) {
        await trackEvent('bot_initialized', {
          bot_id: response.data.bot_id
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

  // Send broadcast message
  const sendBroadcast = useCallback(async (message: BroadcastMessage) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/telegram/bot/broadcast', message);
      
      if (response.data.success) {
        await trackEvent('broadcast_sent', {
          message_id: response.data.message_id,
          type: message.type
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

  // Start onboarding
  const startOnboarding = useCallback(async (userId: number) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/telegram/bot/onboarding/start', {
        user_id: userId
      });
      
      if (response.data.success) {
        await trackEvent('onboarding_started', {
          user_id: userId
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

  // Track onboarding progress
  const trackOnboardingProgress = useCallback(async (
    userId: number,
    stepId: string,
    status: 'completed' | 'skipped'
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/telegram/bot/onboarding/track', {
        user_id: userId,
        step_id: stepId,
        status
      });
      
      if (response.data.success) {
        await trackEvent('onboarding_step_completed', {
          user_id: userId,
          step_id: stepId,
          status
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

  // Create support ticket
  const createSupportTicket = useCallback(async (
    userId: number,
    issueType: string,
    description: string
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/telegram/bot/support/create', {
        user_id: userId,
        issue_type: issueType,
        description
      });
      
      if (response.data.success) {
        setSupportTickets(prev => [...prev, response.data.ticket]);
        
        await trackEvent('support_ticket_created', {
          ticket_id: response.data.ticket.id,
          user_id: userId
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

  // Update support ticket
  const updateSupportTicket = useCallback(async (
    ticketId: string,
    status: 'in_progress' | 'resolved'
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.put(`/api/telegram/bot/support/${ticketId}`, {
        status
      });
      
      if (response.data.success) {
        setSupportTickets(prev =>
          prev.map(ticket =>
            ticket.id === ticketId
              ? { ...ticket, status }
              : ticket
          )
        );
        
        await trackEvent('support_ticket_updated', {
          ticket_id: ticketId,
          status
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

  // Get bot analytics
  const getBotAnalytics = useCallback(async (
    startDate?: string,
    endDate?: string
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/telegram/bot/analytics', {
        params: { start_date: startDate, end_date: endDate }
      });
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get active chats
  const getActiveChats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/telegram/bot/chats/active');
      setActiveChats(response.data.chats);
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get support tickets
  const getSupportTickets = useCallback(async (status?: 'open' | 'in_progress' | 'resolved') => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/telegram/bot/support/tickets', {
        params: { status }
      });
      setSupportTickets(response.data.tickets);
      
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
    activeChats,
    supportTickets,
    initializeBot,
    sendBroadcast,
    startOnboarding,
    trackOnboardingProgress,
    createSupportTicket,
    updateSupportTicket,
    getBotAnalytics,
    getActiveChats,
    getSupportTickets
  };
};
