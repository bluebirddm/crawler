import axios from './client';

export interface CrawlerSource {
  id: number;
  name: string;
  url: string;
  enabled: boolean;
  interval: number; // 分钟
  selector: string; // CSS选择器
  category: string;
  lastCrawled?: string;
  articleCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSourceRequest {
  name: string;
  url: string;
  interval: number;
  selector: string;
  category: string;
  enabled?: boolean;
}

export const sourcesApi = {
  // 获取所有爬取源
  getSources: async (): Promise<CrawlerSource[]> => {
    const response = await axios.get('/api/sources');
    return response.data;
  },

  // 创建新的爬取源
  createSource: async (data: CreateSourceRequest): Promise<CrawlerSource> => {
    const response = await axios.post('/api/sources', data);
    return response.data;
  },

  // 更新爬取源
  updateSource: async (id: number, data: Partial<CreateSourceRequest>): Promise<CrawlerSource> => {
    const response = await axios.put(`/api/sources/${id}`, data);
    return response.data;
  },

  // 删除爬取源
  deleteSource: async (id: number): Promise<void> => {
    await axios.delete(`/api/sources/${id}`);
  },

  // 测试爬取源
  testSource: async (id: number): Promise<{ success: boolean; message: string; data?: any }> => {
    const response = await axios.post(`/api/sources/${id}/test`);
    return response.data;
  },

  // 立即执行爬取
  triggerCrawl: async (id: number): Promise<{ taskId: string }> => {
    const response = await axios.post(`/api/sources/${id}/crawl`);
    return response.data;
  },
};