import { apiClient } from './client';
import type { Article, CategoryStats, DailyStats, ArticleCreateRequest, ArticleUpdateRequest } from '../types/index';

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

  searchArticles: async (params?: {
    q?: string;
    category?: string;
    level?: number;
    skip?: number;
    limit?: number;
  }) => {
    const response = await apiClient.get<Article[]>('/api/articles/search/', {
      params,
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

  // 热门文章相关API
  getHotArticles: async (params?: {
    limit?: number;
    category?: string;
    time_range?: '1d' | '7d' | '30d' | 'all';
  }) => {
    const response = await apiClient.get<Article[]>('/api/articles/hot/', { params });
    return response.data;
  },

  getTrendingArticles: async (params?: {
    limit?: number;
    hours?: number;
  }) => {
    const response = await apiClient.get<Article[]>('/api/articles/trending/', { params });
    return response.data;
  },

  incrementView: async (id: number) => {
    const response = await apiClient.post(`/api/articles/${id}/view`);
    return response.data;
  },

  toggleLike: async (id: number, isLike: boolean) => {
    const response = await apiClient.post(`/api/articles/${id}/like`, null, {
      params: { is_like: isLike }
    });
    return response.data;
  },

  recordShare: async (id: number) => {
    const response = await apiClient.post(`/api/articles/${id}/share`);
    return response.data;
  },

  updateHotScores: async (daysBack = 7) => {
    const response = await apiClient.post('/api/articles/update-hot-scores', null, {
      params: { days_back: daysBack }
    });
    return response.data;
  },

  createArticle: async (article: ArticleCreateRequest) => {
    const response = await apiClient.post<Article>('/api/articles/', article);
    return response.data;
  },

  updateArticle: async (id: number, article: ArticleUpdateRequest) => {
    const response = await apiClient.put<Article>(`/api/articles/${id}`, article);
    return response.data;
  },

  deleteArticlesBatch: async (articleIds: number[]) => {
    const response = await apiClient.delete('/api/articles/batch/delete', {
      data: { article_ids: articleIds }
    });
    return response.data;
  },
};