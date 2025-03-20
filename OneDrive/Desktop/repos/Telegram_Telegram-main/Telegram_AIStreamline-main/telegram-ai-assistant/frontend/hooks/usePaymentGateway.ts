import { useState, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { PayPalButtons, PayPalScriptProvider } from '@paypal/react-paypal-js';
import { useAuth } from './useAuth';
import { api } from '../utils/api';

interface PaymentConfig {
  stripePublicKey: string;
  paypalClientId: string;
}

interface PaymentData {
  amount: number;
  currency: string;
  customerId?: string;
  orderId?: string;
  description?: string;
  metadata?: Record<string, any>;
}

interface PaymentResult {
  success: boolean;
  paymentId?: string;
  error?: string;
  status?: string;
}

interface PaymentHistory {
  gateway: string;
  amount: number;
  currency: string;
  status: string;
  paymentId: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

interface PaymentAnalytics {
  totalPayments: number;
  totalAmount: number;
  byGateway: {
    stripe: {
      count: number;
      amount: number;
    };
    paypal: {
      count: number;
      amount: number;
    };
  };
  recentPayments: PaymentHistory[];
}

export const usePaymentGateway = (config: PaymentConfig) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentHistory, setPaymentHistory] = useState<PaymentHistory[]>([]);
  const [analytics, setAnalytics] = useState<PaymentAnalytics | null>(null);

  // Initialize Stripe
  const stripePromise = loadStripe(config.stripePublicKey);

  // Initialize PayPal
  const paypalOptions = {
    'client-id': config.paypalClientId,
    currency: 'USD',
  };

  const processStripePayment = useCallback(async (paymentData: PaymentData): Promise<PaymentResult> => {
    try {
      setLoading(true);
      setError(null);

      const stripe = await stripePromise;
      if (!stripe) {
        throw new Error('Failed to load Stripe');
      }

      // Create payment intent
      const response = await api.post('/api/payments/stripe/create-intent', {
        amount: paymentData.amount,
        currency: paymentData.currency,
        customer_id: paymentData.customerId,
        order_id: paymentData.orderId,
        metadata: paymentData.metadata
      });

      const { clientSecret } = response.data;

      // Confirm payment
      const result = await stripe.confirmCardPayment(clientSecret);

      if (result.error) {
        throw new Error(result.error.message);
      }

      return {
        success: true,
        paymentId: result.paymentIntent?.id,
        status: result.paymentIntent?.status
      };

    } catch (err: any) {
      setError(err.message);
      return {
        success: false,
        error: err.message
      };
    } finally {
      setLoading(false);
    }
  }, [stripePromise]);

  const processPayPalPayment = useCallback(async (paymentData: PaymentData): Promise<PaymentResult> => {
    try {
      setLoading(true);
      setError(null);

      // Create PayPal order
      const response = await api.post('/api/payments/paypal/create-order', {
        amount: paymentData.amount,
        currency: paymentData.currency,
        customer_id: paymentData.customerId,
        order_id: paymentData.orderId,
        description: paymentData.description,
        metadata: paymentData.metadata
      });

      const { orderId } = response.data;

      return {
        success: true,
        paymentId: orderId
      };

    } catch (err: any) {
      setError(err.message);
      return {
        success: false,
        error: err.message
      };
    } finally {
      setLoading(false);
    }
  }, []);

  const getPaymentHistory = useCallback(async (
    customerId?: string,
    gateway?: string,
    limit?: number
  ): Promise<PaymentHistory[]> => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/payments/history', {
        params: { customer_id: customerId, gateway, limit }
      });

      const history = response.data;
      setPaymentHistory(history);
      return history;

    } catch (err: any) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const getPaymentAnalytics = useCallback(async (): Promise<PaymentAnalytics | null> => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/api/payments/analytics');
      const analyticsData = response.data;
      setAnalytics(analyticsData);
      return analyticsData;

    } catch (err: any) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const refundPayment = useCallback(async (
    paymentId: string,
    gateway: string,
    amount?: number
  ): Promise<PaymentResult> => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/payments/refund', {
        payment_id: paymentId,
        gateway,
        amount
      });

      return {
        success: true,
        ...response.data
      };

    } catch (err: any) {
      setError(err.message);
      return {
        success: false,
        error: err.message
      };
    } finally {
      setLoading(false);
    }
  }, []);

  const PayPalButtonWrapper = useCallback(({ amount, onSuccess, onError }: {
    amount: number;
    onSuccess: (details: any) => void;
    onError: (err: any) => void;
  }) => (
    <PayPalScriptProvider options={paypalOptions}>
      <PayPalButtons
        createOrder={(data, actions) => {
          return actions.order.create({
            purchase_units: [{
              amount: {
                value: amount.toString()
              }
            }]
          });
        }}
        onApprove={async (data, actions) => {
          if (actions.order) {
            const details = await actions.order.capture();
            onSuccess(details);
          }
        }}
        onError={onError}
      />
    </PayPalScriptProvider>
  ), [paypalOptions]);

  return {
    loading,
    error,
    paymentHistory,
    analytics,
    processStripePayment,
    processPayPalPayment,
    getPaymentHistory,
    getPaymentAnalytics,
    refundPayment,
    PayPalButtonWrapper
  };
};
