import { useState, useCallback } from 'react';
import { api } from '../utils/api';
import { useAuth } from './useAuth';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/stripe-js/pure';

interface PaymentData {
  amount: number;
  currency?: string;
  payment_method: 'credit_card' | 'crypto';
  crypto_provider?: 'coinbase' | 'bitpay';
  order_id?: string;
  customer_id?: string;
  description?: string;
  customer_email?: string;
  redirect_url?: string;
}

interface TransactionFilters {
  payment_method?: 'credit_card' | 'crypto';
  provider?: 'stripe' | 'coinbase' | 'bitpay';
  status?: 'pending' | 'completed' | 'failed';
  start_date?: string;
  end_date?: string;
}

interface Transaction {
  timestamp: string;
  payment_method: string;
  provider: string;
  amount: string;
  currency: string;
  status: string;
  transaction_id: string;
  updated_at?: string;
}

interface TransactionStats {
  total_transactions: number;
  total_amount: Record<string, number>;
  by_payment_method: {
    credit_card: number;
    crypto: number;
  };
  by_status: {
    completed: number;
    pending: number;
    failed: number;
  };
}

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

export const usePayment = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [stats, setStats] = useState<TransactionStats | null>(null);

  // Create payment
  const createPayment = useCallback(async (paymentData: PaymentData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/payments/create', paymentData);
      
      if (paymentData.payment_method === 'credit_card') {
        // Return Stripe payment intent for credit card payments
        return {
          success: true,
          type: 'credit_card',
          data: response.data
        };
      } else {
        // Return crypto payment details
        return {
          success: true,
          type: 'crypto',
          data: response.data
        };
      }

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Process credit card payment
  const processCreditCardPayment = useCallback(async (
    paymentMethodId: string,
    paymentIntentId: string
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/payments/process-card', {
        payment_method_id: paymentMethodId,
        payment_intent_id: paymentIntentId
      });

      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get crypto payment status
  const getCryptoPaymentStatus = useCallback(async (
    provider: 'coinbase' | 'bitpay',
    transactionId: string
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/api/payments/${provider}/status/${transactionId}`);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get transaction history
  const getTransactionHistory = useCallback(async (filters?: TransactionFilters) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/payments/transactions', {
        params: filters
      });
      
      setTransactions(response.data);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get transaction statistics
  const getTransactionStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/payments/stats');
      setStats(response.data);
      return response.data;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get real-time crypto exchange rates
  const getCryptoExchangeRate = useCallback(async (
    cryptoCurrency: string,
    fiatCurrency: string = 'USD'
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/payments/crypto/exchange-rate', {
        params: {
          crypto: cryptoCurrency,
          fiat: fiatCurrency
        }
      });
      
      return response.data.rate;

    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Helper function to handle credit card payment flow
  const handleCreditCardPayment = useCallback(async (
    amount: number,
    currency: string = 'USD'
  ) => {
    try {
      // Create payment intent
      const { data: paymentIntent } = await createPayment({
        amount,
        currency,
        payment_method: 'credit_card'
      });

      // Initialize Stripe elements
      const stripe = await stripePromise;
      if (!stripe) throw new Error('Stripe failed to initialize');

      // Confirm card payment
      const result = await stripe.confirmCardPayment(paymentIntent.client_secret, {
        payment_method: {
          card: elements.getElement(CardElement)!,
          billing_details: {
            email: user?.email
          }
        }
      });

      if (result.error) {
        throw new Error(result.error.message);
      }

      return result.paymentIntent;

    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [createPayment, user]);

  // Helper function to handle crypto payment flow
  const handleCryptoPayment = useCallback(async (
    amount: number,
    currency: string = 'USD',
    provider: 'coinbase' | 'bitpay' = 'coinbase'
  ) => {
    try {
      // Create crypto payment
      const { data: cryptoPayment } = await createPayment({
        amount,
        currency,
        payment_method: 'crypto',
        crypto_provider: provider
      });

      // Start polling for payment status
      const pollStatus = async () => {
        const status = await getCryptoPaymentStatus(provider, cryptoPayment.charge_id);
        if (status.status === 'completed') {
          return status;
        } else if (status.status === 'failed') {
          throw new Error('Crypto payment failed');
        } else {
          await new Promise(resolve => setTimeout(resolve, 5000));
          return pollStatus();
        }
      };

      return {
        paymentDetails: cryptoPayment,
        statusPromise: pollStatus()
      };

    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [createPayment, getCryptoPaymentStatus]);

  return {
    loading,
    error,
    transactions,
    stats,
    createPayment,
    processCreditCardPayment,
    getCryptoPaymentStatus,
    getTransactionHistory,
    getTransactionStats,
    getCryptoExchangeRate,
    handleCreditCardPayment,
    handleCryptoPayment,
    Elements,
    CardElement,
    useStripe,
    useElements,
    stripePromise
  };
};
