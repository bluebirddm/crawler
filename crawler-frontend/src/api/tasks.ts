import { apiClient } from './client';
import type { Task, CrawlRequest, BatchCrawlRequest } from '../types';

export const tasksApi = {
  createCrawlTask: async (request: CrawlRequest) => {
    const response = await apiClient.post<Task>('/api/tasks/crawl', request);
    return response.data;
  },

  createBatchCrawlTask: async (request: BatchCrawlRequest) => {
    const response = await apiClient.post<Task>('/api/tasks/crawl/batch', request);
    return response.data;
  },

  getTaskStatus: async (taskId: string) => {
    const response = await apiClient.get<{
      task_id: string;
      status: string;
      ready: boolean;
      successful?: boolean;
      result?: any;
    }>(`/api/tasks/status/${taskId}`);
    return response.data;
  },

  getActiveTasks: async () => {
    const response = await apiClient.get<{ active_tasks: any[] }>('/api/tasks/active');
    return response.data.active_tasks;
  },

  getScheduledTasks: async () => {
    const response = await apiClient.get<{ scheduled_tasks: any[] }>('/api/tasks/scheduled');
    return response.data.scheduled_tasks;
  },

  cancelTask: async (taskId: string) => {
    const response = await apiClient.delete(`/api/tasks/cancel/${taskId}`);
    return response.data;
  },

  reprocessArticles: async (articleIds?: number[]) => {
    const response = await apiClient.post<Task>('/api/tasks/reprocess', { article_ids: articleIds });
    return response.data;
  },
};