import apiClient from './client';
import type { Generation, GenerationCreateRequest } from '@/types';

export const generationApi = {
  create: async (request: GenerationCreateRequest): Promise<Generation> => {
    const { data } = await apiClient.post('/api/v1/generation', request);
    return data;
  },

  getById: async (id: string): Promise<Generation> => {
    const { data } = await apiClient.get(`/api/v1/generation/${id}`);
    return data;
  },

  getStatus: async (id: string): Promise<{
    id: string;
    status: string;
    result_url: string | null;
    result_file_url: string | null;
    error_message: string | null;
  }> => {
    const { data } = await apiClient.get(`/api/v1/generation/${id}/status`);
    return data;
  },

  getAll: async (
    offset = 0,
    limit = 50,
    generationType?: string
  ): Promise<{ items: Generation[]; total: number }> => {
    const { data } = await apiClient.get('/api/v1/generation', {
      params: {
        offset,
        limit,
        ...(generationType && { generation_type: generationType }),
      },
    });
    return data;
  },
};
