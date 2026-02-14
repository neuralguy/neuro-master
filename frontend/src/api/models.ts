import apiClient from './client';
import type { AIModel, AIModelsGrouped } from '@/types';

export const modelsApi = {
  getAll: async (generationType?: string): Promise<AIModel[]> => {
    const { data } = await apiClient.get('/api/v1/models', {
      params: generationType ? { generation_type: generationType } : {},
    });
    return data;
  },

  getGrouped: async (): Promise<AIModelsGrouped> => {
    const { data } = await apiClient.get('/api/v1/models/grouped');
    return data;
  },

  getByCode: async (code: string): Promise<AIModel> => {
    const { data } = await apiClient.get(`/api/v1/models/${code}`);
    return data;
  },
};
