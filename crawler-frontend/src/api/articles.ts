import { apiClient } from './client';
import { Article, CategoryStats, DailyStats } from '../types';

export const articlesApi = {
  getArticles: async (params?: {
    skip?: number;
    limit?: number;
    category?: string;
    level?: number;
    days?: number;
  }) => {
    const response = await apiClient.get<Article[]>('/api/articles', { params });
    return response.data;
  },

  getArticle: async (id: number) => {
    const response = await apiClient.get<Article>(`/api/articles/${id}`);
    return response.data;
  },

  searchArticles: async (query: string, skip = 0, limit = 10) => {
    const response = await apiClient.get<Article[]>('/api/articles/search', {
      params: { q: query, skip, limit },
    });
    return response.data;
  },

  getCategoryStats: async () => {
    const response = await apiClient.get<{ categories: CategoryStats[] }>(
      '/api/articles/stats/categories'
    );
    return response.data.categories;
  },

  getDailyStats: async (days = 7) => {
    const response = await apiClient.get<{ daily_stats: DailyStats[] }>(
      '/api/articles/stats/daily',
      { params: { days } }
    );
    return response.data.daily_stats;
  },

  deleteArticle: async (id: number) => {
    const response = await apiClient.delete(`/api/articles/${id}`);
    return response.data;
  },
};