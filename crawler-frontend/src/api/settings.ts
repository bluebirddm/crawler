import axios from './client';

export interface SystemConfig {
  crawling: {
    defaultInterval: number; // 分钟
    maxConcurrent: number;
    timeout: number; // 秒
    retryTimes: number;
    userAgent: string;
  };
  processing: {
    enableNLP: boolean;
    enableClassification: boolean;
    enableTagging: boolean;
    nlpModel: string;
    minConfidence: number; // 0-1
  };
  storage: {
    maxArticleAge: number; // 天
    autoCleanup: boolean;
    cleanupInterval: number; // 小时
    backupEnabled: boolean;
    backupPath: string;
  };
  notification: {
    enabled: boolean;
    email?: string;
    webhook?: string;
    events: string[]; // 通知事件类型
  };
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  createdAt: string;
  lastLogin?: string;
  isActive: boolean;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role: 'admin' | 'editor' | 'viewer';
}

export interface DatabaseInfo {
  size: number; // MB
  tables: {
    name: string;
    rowCount: number;
    size: number; // MB
  }[];
  lastBackup?: string;
  version: string;
}

export const settingsApi = {
  // 系统配置
  getConfig: async (): Promise<SystemConfig> => {
    const response = await axios.get('/api/settings/config');
    return response.data;
  },

  updateConfig: async (config: Partial<SystemConfig>): Promise<SystemConfig> => {
    const response = await axios.put('/api/settings/config', config);
    return response.data;
  },

  resetConfig: async (): Promise<SystemConfig> => {
    const response = await axios.post('/api/settings/config/reset');
    return response.data;
  },

  // 用户管理
  getUsers: async (): Promise<User[]> => {
    const response = await axios.get('/api/settings/users');
    return response.data;
  },

  createUser: async (data: CreateUserRequest): Promise<User> => {
    const response = await axios.post('/api/settings/users', data);
    return response.data;
  },

  updateUser: async (id: number, data: Partial<User>): Promise<User> => {
    const response = await axios.put(`/api/settings/users/${id}`, data);
    return response.data;
  },

  deleteUser: async (id: number): Promise<void> => {
    await axios.delete(`/api/settings/users/${id}`);
  },

  // 数据库管理
  getDatabaseInfo: async (): Promise<DatabaseInfo> => {
    const response = await axios.get('/api/settings/database');
    return response.data;
  },

  backupDatabase: async (): Promise<{ path: string; size: number }> => {
    const response = await axios.post('/api/settings/database/backup');
    return response.data;
  },

  restoreDatabase: async (backupPath: string): Promise<void> => {
    await axios.post('/api/settings/database/restore', { path: backupPath });
  },

  cleanupDatabase: async (olderThanDays: number): Promise<{ deleted: number }> => {
    const response = await axios.post('/api/settings/database/cleanup', {
      older_than_days: olderThanDays,
    });
    return response.data;
  },

  // 系统操作
  clearCache: async (): Promise<void> => {
    await axios.post('/api/settings/cache/clear');
  },

  exportLogs: async (): Promise<Blob> => {
    const response = await axios.get('/api/settings/logs/export', {
      responseType: 'blob',
    });
    return response.data;
  },
};