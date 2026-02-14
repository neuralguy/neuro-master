import apiClient from './client';
import type { User, BalanceHistoryItem, ReferralInfo } from '@/types';

export const userApi = {
  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get('/api/v1/user/me');
    return data;
  },

  getBalance: async (): Promise<{ balance: number }> => {
    const { data } = await apiClient.get('/api/v1/user/balance');
    return data;
  },

  getHistory: async (offset = 0, limit = 50): Promise<{
    items: BalanceHistoryItem[];
    total: number;
  }> => {
    const { data } = await apiClient.get('/api/v1/user/history', {
      params: { offset, limit },
    });
    return data;
  },

  getReferralInfo: async (): Promise<ReferralInfo> => {
    const { data } = await apiClient.get('/api/v1/user/referral');
    return data;
  },
};
