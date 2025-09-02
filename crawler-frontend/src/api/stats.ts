import axios from './client';

export interface DailyStats {
  date: string;
  articlesCount: number;
  tasksCount: number;
  successRate: number;
  avgProcessingTime: number; // 秒
}

export interface CategoryStats {
  category: string;
  count: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
  change: number; // 百分比变化
}

export interface SourceStats {
  sourceId: number;
  sourceName: string;
  totalArticles: number;
  todayArticles: number;
  successRate: number;
  avgResponseTime: number; // 毫秒
  lastSuccess?: string;
  lastError?: string;
}

export interface TagStats {
  tag: string;
  count: number;
  articles: number;
  trending: boolean;
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
}

export interface StatsOverview {
  totalArticles: number;
  totalTasks: number;
  totalSources: number;
  activeWorkers: number;
  todayArticles: number;
  todayTasks: number;
  weekGrowth: number; // 百分比
  monthGrowth: number; // 百分比
}

export const statsApi = {
  // 获取统计概览
  getOverview: async (): Promise<StatsOverview> => {
    const response = await axios.get('/api/stats/overview');
    return response.data;
  },

  // 获取每日统计
  getDailyStats: async (days: number = 30): Promise<DailyStats[]> => {
    const response = await axios.get('/api/stats/daily', {
      params: { days },
    });
    return response.data;
  },

  // 获取分类统计
  getCategoryStats: async (): Promise<CategoryStats[]> => {
    const response = await axios.get('/api/stats/categories');
    return response.data;
  },

  // 获取爬取源统计
  getSourceStats: async (): Promise<SourceStats[]> => {
    const response = await axios.get('/api/stats/sources');
    return response.data;
  },

  // 获取标签统计
  getTagStats: async (limit: number = 20): Promise<TagStats[]> => {
    const response = await axios.get('/api/stats/tags', {
      params: { limit },
    });
    return response.data;
  },

  // 获取时间序列数据
  getTimeSeries: async (
    metric: 'articles' | 'tasks' | 'errors' | 'response_time',
    interval: 'hour' | 'day' | 'week' | 'month',
    period: number = 7
  ): Promise<TimeSeriesData[]> => {
    const response = await axios.get('/api/stats/timeseries', {
      params: { metric, interval, period },
    });
    return response.data;
  },

  // 导出统计报告
  exportReport: async (
    format: 'csv' | 'excel' | 'pdf',
    startDate?: string,
    endDate?: string
  ): Promise<Blob> => {
    const response = await axios.get('/api/stats/export', {
      params: { format, start_date: startDate, end_date: endDate },
      responseType: 'blob',
    });
    return response.data;
  },
};