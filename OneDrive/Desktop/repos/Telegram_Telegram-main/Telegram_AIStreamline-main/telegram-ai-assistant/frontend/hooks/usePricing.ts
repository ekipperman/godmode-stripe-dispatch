import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';
import { usePayment } from './usePayment';

interface PlanFeatures {
  ai_chatbot: {
    enabled: boolean;
    monthly_tokens: number | 'unlimited';
    model: string;
    custom_training?: boolean;
  };
  crm_integration: {
    enabled: boolean;
    platforms: string[] | 'all';
    monthly_syncs: number | 'unlimited';
    custom_integrations?: boolean;
  };
  social_media: {
    enabled: boolean;
    platforms: string[] | 'all';
    monthly_posts: number | 'unlimited';
    custom_automation?: boolean;
  };
  analytics: {
    enabled: boolean;
    retention_days: number;
    export_formats: string[] | 'all';
    custom_reports?: boolean;
  };
  voice_commands?: {
    enabled: boolean;
    languages: string[] | 'all';
  };
}

interface PlanLimits {
  contacts: number | 'unlimited';
  monthly_messages: number | 'unlimited';
  storage_gb: number | 'unlimited' | 'custom';
  concurrent_users: number | 'unlimited';
}

interface SubscriptionPlan {
  name: string;
  price: {
    monthly: number;
    yearly: number;
  } | 'custom';
  features: PlanFeatures;
  limits: PlanLimits;
}

interface UsageData {
  ai_tokens: {
    [model: string]: number;
  };
  storage: number;
  api_calls: number;
}

interface UsageReport {
  usage: {
    ai_tokens: number;
    storage: number;
    api_calls: number;
  };
  costs: {
    [resource: string]: {
      usage: number;
      rate: number;
      cost: number;
    };
  };
  period: {
    start: string | null;
    end: string | null;
  };
}

export const usePricing = () => {
  const { user } = useAuth();
  const { createPayment } = usePayment();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<SubscriptionPlan | null>(null);
  const [usageReport, setUsageReport] = useState<UsageReport | null>(null);

  // Get subscription plans
  const getSubscriptionPlans = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/pricing/plans');
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Calculate subscription price
  const calculatePrice = useCallback(async (
    planId: string,
    billingCycle: 'monthly' | 'yearly' = 'monthly'
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/pricing/calculate', {
        plan_id: planId,
        billing_cycle: billingCycle
      });
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Calculate usage cost
  const calculateUsageCost = useCallback(async (usageData: UsageData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/pricing/usage-cost', usageData);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Subscribe to plan
  const subscribeToPlan = useCallback(async (
    planId: string,
    billingCycle: 'monthly' | 'yearly',
    paymentMethod: 'credit_card' | 'crypto',
    cryptoProvider?: 'coinbase' | 'bitpay'
  ) => {
    try {
      setLoading(true);
      setError(null);

      // Calculate price
      const priceResult = await calculatePrice(planId, billingCycle);
      
      // Create payment
      const paymentResult = await createPayment({
        amount: priceResult.final_price,
        currency: 'USD',
        payment_method: paymentMethod,
        crypto_provider: cryptoProvider,
        description: `Subscription to ${priceResult.plan_name} (${billingCycle})`
      });

      // Process payment and create subscription
      const response = await api.post('/api/subscriptions/create', {
        plan_id: planId,
        billing_cycle: billingCycle,
        payment_id: paymentResult.data.payment_id
      });

      setCurrentPlan(response.data.plan);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [calculatePrice, createPayment]);

  // Get usage report
  const getUsageReport = useCallback(async (
    startDate?: string,
    endDate?: string
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/pricing/usage-report', {
        params: { start_date: startDate, end_date: endDate }
      });
      
      setUsageReport(response.data);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Check usage limits
  const checkUsageLimits = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/pricing/check-limits');
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Apply promotional offer
  const applyPromotion = useCallback(async (
    offerType: 'new_user_discount' | 'referral',
    planId?: string
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/pricing/apply-promotion', {
        offer_type: offerType,
        plan_id: planId
      });
      
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Cancel subscription
  const cancelSubscription = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/subscriptions/cancel');
      setCurrentPlan(null);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Change subscription plan
  const changePlan = useCallback(async (
    newPlanId: string,
    billingCycle?: 'monthly' | 'yearly'
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/subscriptions/change-plan', {
        plan_id: newPlanId,
        billing_cycle: billingCycle
      });
      
      setCurrentPlan(response.data.plan);
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
    currentPlan,
    usageReport,
    getSubscriptionPlans,
    calculatePrice,
    calculateUsageCost,
    subscribeToPlan,
    getUsageReport,
    checkUsageLimits,
    applyPromotion,
    cancelSubscription,
    changePlan
  };
};
