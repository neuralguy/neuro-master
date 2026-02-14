import apiClient from './client';
import type { GalleryItem } from '@/types';

export const galleryApi = {
  getAll: async (
    offset = 0,
    limit = 50,
    fileType?: string,
    favoritesOnly = false
  ): Promise<{ items: GalleryItem[]; total: number }> => {
    const { data } = await apiClient.get('/api/v1/gallery', {
      params: {
        offset,
        limit,
        ...(fileType && { file_type: fileType }),
        ...(favoritesOnly && { favorites_only: true }),
      },
    });
    return data;
  },

  getById: async (id: string): Promise<GalleryItem> => {
    const { data } = await apiClient.get(`/api/v1/gallery/${id}`);
    return data;
  },

  toggleFavorite: async (id: string): Promise<{ id: string; is_favorite: boolean }> => {
    const { data } = await apiClient.post(`/api/v1/gallery/${id}/favorite`);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/gallery/${id}`);
  },
};
