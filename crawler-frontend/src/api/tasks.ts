import { apiClient } from './client';
import type { Task, CrawlRequest, BatchCrawlRequest } from '../types';

interface TaskHistoryQuery {
  page?: number;
  page_size?: number;
  status?: string;
  task_type?: string;
  start_date?: string;
  end_date?: string;
  sort_by?: 'created_at' | 'completed_at' | 'status' | 'task_type';
  order?: 'asc' | 'desc';
}

interface TaskHistoryResponse {
  total: number;
  page: number;
  page_size: number;
  tasks: TaskHistoryItem[];
}

interface TaskHistoryItem {
  id: number;
  task_id: string;
  task_name: string;
  task_type: string;
  url?: string;
  urls?: string[];
  status: string;
  result?: any;
  error_message?: string;
  retry_count: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  worker_name?: string;
}

interface TaskStats {
  total_tasks: number;
  status_counts: Record<string, number>;
  recent_tasks_24h: number;
  success_rate: number;
  avg_duration_seconds?: number;
}

export type {
  TaskHistoryQuery,
  TaskHistoryResponse,
  TaskHistoryItem,
  TaskStats
};

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

  // 历史任务相关 API
  getTaskHistory: async (query: TaskHistoryQuery = {}) => {
    const params = new URLSearchParams();
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
    
    const response = await apiClient.get<TaskHistoryResponse>(
      `/api/tasks/history?${params.toString()}`
    );
    return response.data;
  },

  getTaskHistoryDetail: async (taskId: string) => {
    const response = await apiClient.get<TaskHistoryItem>(
      `/api/tasks/history/${taskId}`
    );
    return response.data;
  },

  deleteTaskHistory: async (taskId: string) => {
    const response = await apiClient.delete(`/api/tasks/history/${taskId}`);
    return response.data;
  },

  getTaskStats: async () => {
    const response = await apiClient.get<TaskStats>('/api/tasks/history/stats/summary');
    return response.data;
  },

  cleanupOldHistory: async (days: number = 30) => {
    const response = await apiClient.delete(
      `/api/tasks/history/cleanup/old?days=${days}`
    );
    return response.data;
  },

  deleteBatchTaskHistory: async (taskIds: string[]) => {
    const response = await apiClient.delete('/api/tasks/history/batch', {
      data: { task_ids: taskIds }
    });
    return response.data;
  },
};