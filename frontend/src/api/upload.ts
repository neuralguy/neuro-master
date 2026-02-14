import apiClient from './client';

export interface UploadResponse {
  url: string;
  filename: string;
}

export const uploadApi = {
  uploadBase64: async (data: string): Promise<UploadResponse> => {
    const response = await apiClient.post('/api/v1/upload/base64', { data });
    return response.data;
  },

  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/api/v1/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

