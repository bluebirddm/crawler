import { apiClient } from './client';
import type { SystemInfo, Worker } from '../types';

export const adminApi = {
  getSystemInfo: async () => {
    const response = await apiClient.get<SystemInfo>('/api/admin/system/info');
    return response.data;
  },

  getWorkersStatus: async () => {
    const response = await apiClient.get<{ workers: Worker[] }>('/api/admin/workers/status');
    return response.data.workers;
  },

  cleanupDatabase: async (days = 90) => {
    const response = await apiClient.post('/api/admin/database/cleanup', null, {
      params: { days },
    });
    return response.data;
  },

  resetDatabase: async (confirm = false) => {
    const response = await apiClient.post('/api/admin/database/reset', null, {
      params: { confirm },
    });
    return response.data;
  },

  restartWorkers: async () => {
    const response = await apiClient.post('/api/admin/workers/restart');
    return response.data;
  },

  getConfig: async () => {
    const response = await apiClient.get('/api/admin/config');
    return response.data;
  },
};