import apiClient from './client';
import type { AdminStats, AdminUser, AIModel, Payment, LogEntry } from '@/types';

export const adminApi = {
  // Stats
  getStats: async (): Promise<AdminStats> => {
    const { data } = await apiClient.get('/api/v1/admin/stats');
    return data;
  },

  // Users
  getUsers: async (
    offset = 0,
    limit = 50,
    search?: string,
    isBanned?: boolean
  ): Promise<{ items: AdminUser[]; total: number }> => {
    const { data } = await apiClient.get('/api/v1/admin/users', {
      params: {
        offset,
        limit,
        ...(search && { search }),
        ...(isBanned !== undefined && { is_banned: isBanned }),
      },
    });
    return data;
  },

  getUser: async (userId: number): Promise<AdminUser> => {
    const { data } = await apiClient.get(`/api/v1/admin/users/${userId}`);
    return data;
  },

  updateUser: async (
    userId: number,
    updates: { is_banned?: boolean; balance?: number }
  ): Promise<AdminUser> => {
    const { data } = await apiClient.patch(`/api/v1/admin/users/${userId}`, updates);
    return data;
  },

  // Payments
  getPayments: async (offset = 0, limit = 50): Promise<{
    items: Payment[];
    total: number;
  }> => {
    const { data } = await apiClient.get('/api/v1/admin/payments', {
      params: { offset, limit },
    });
    return data;
  },

  // Models
  getModels: async (): Promise<AIModel[]> => {
    const { data } = await apiClient.get('/api/v1/admin/models');
    return data;
  },

  createModel: async (model: Partial<AIModel>): Promise<AIModel> => {
    const { data } = await apiClient.post('/api/v1/admin/models', model);
    return data;
  },

  updateModel: async (modelId: number, updates: Partial<AIModel>): Promise<AIModel> => {
    const { data } = await apiClient.patch(`/api/v1/admin/models/${modelId}`, updates);
    return data;
  },

  toggleModel: async (modelId: number): Promise<{ message: string }> => {
    const { data } = await apiClient.post(`/api/v1/admin/models/${modelId}/toggle`);
    return data;
  },

  deleteModel: async (modelId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/admin/models/${modelId}`);
  },
};
