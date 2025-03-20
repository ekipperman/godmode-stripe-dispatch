import { useState, useCallback } from 'react';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { useAuth } from './useAuth';

// Types
interface User {
  id: string;
  email: string;
  full_name?: string;
  telegram_id?: string;
  role: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface CRMData {
  id: string;
  user_id: string;
  type: string;
  data: Record<string, any>;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Transaction {
  id: string;
  user_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface Campaign {
  id: string;
  user_id: string;
  name: string;
  type: string;
  content: Record<string, any>;
  schedule?: string;
  status: string;
  metrics: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export const useDatabase = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize Supabase client
  const supabase: SupabaseClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_KEY!
  );

  // User operations
  const updateUser = useCallback(async (userData: Partial<User>) => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('users')
        .update(userData)
        .eq('id', user?.id)
        .single();

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  // CRM operations
  const createCRMEntry = useCallback(async (crmData: Omit<CRMData, 'id' | 'user_id' | 'created_at' | 'updated_at'>) => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('crm_data')
        .insert({
          ...crmData,
          user_id: user?.id
        })
        .single();

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  const getCRMData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('crm_data')
        .select('*')
        .eq('user_id', user?.id);

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Transaction operations
  const createTransaction = useCallback(async (transactionData: Omit<Transaction, 'id' | 'user_id' | 'created_at' | 'updated_at'>) => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('transactions')
        .insert({
          ...transactionData,
          user_id: user?.id
        })
        .single();

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  const getTransactions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('transactions')
        .select('*')
        .eq('user_id', user?.id);

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Campaign operations
  const createCampaign = useCallback(async (campaignData: Omit<Campaign, 'id' | 'user_id' | 'created_at' | 'updated_at'>) => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('campaigns')
        .insert({
          ...campaignData,
          user_id: user?.id
        })
        .single();

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  const getCampaigns = useCallback(async (status?: string) => {
    try {
      setLoading(true);
      setError(null);

      let query = supabase
        .from('campaigns')
        .select('*')
        .eq('user_id', user?.id);

      if (status) {
        query = query.eq('status', status);
      }

      const { data, error } = await query;

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  const updateCampaign = useCallback(async (campaignId: string, campaignData: Partial<Campaign>) => {
    try {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('campaigns')
        .update(campaignData)
        .eq('id', campaignId)
        .eq('user_id', user?.id)
        .single();

      if (error) throw error;
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Analytics operations
  const getAnalytics = useCallback(async (startDate: string, endDate: string) => {
    try {
      setLoading(true);
      setError(null);

      const [transactions, campaigns, crmData] = await Promise.all([
        supabase
          .from('transactions')
          .select('*')
          .eq('user_id', user?.id)
          .gte('created_at', startDate)
          .lte('created_at', endDate),
        supabase
          .from('campaigns')
          .select('*')
          .eq('user_id', user?.id)
          .gte('created_at', startDate)
          .lte('created_at', endDate),
        supabase
          .from('crm_data')
          .select('*')
          .eq('user_id', user?.id)
          .gte('created_at', startDate)
          .lte('created_at', endDate)
      ]);

      if (transactions.error) throw transactions.error;
      if (campaigns.error) throw campaigns.error;
      if (crmData.error) throw crmData.error;

      return {
        transactions: transactions.data,
        campaigns: campaigns.data,
        crmData: crmData.data
      };
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  return {
    loading,
    error,
    updateUser,
    createCRMEntry,
    getCRMData,
    createTransaction,
    getTransactions,
    createCampaign,
    getCampaigns,
    updateCampaign,
    getAnalytics
  };
};
