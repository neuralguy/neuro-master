import apiClient from './client';
import type { Payment, PaymentPackages } from '@/types';

export const paymentsApi = {
  getPackages: async (): Promise<PaymentPackages> => {
    const { data } = await apiClient.get('/api/v1/payments/packages');
    return data;
  },

  create: async (amount: number): Promise<{
    payment_id: string;
    amount: number;
    tokens: number;
    confirmation_url: string;
  }> => {
    const { data } = await apiClient.post('/api/v1/payments', { amount });
    return data;
  },

  check: async (paymentId: string): Promise<{
    payment_id: string;
    status: string;
    success: boolean;
    new_balance: number | null;
    message: string;
  }> => {
    const { data } = await apiClient.post(`/api/v1/payments/${paymentId}/check`);
    return data;
  },

  getAll: async (offset = 0, limit = 50): Promise<{
    items: Payment[];
    total: number;
  }> => {
    const { data } = await apiClient.get('/api/v1/payments', {
      params: { offset, limit },
    });
    return data;
  },

  getById: async (id: string): Promise<Payment> => {
    const { data } = await apiClient.get(`/api/v1/payments/${id}`);
    return data;
  },
};
