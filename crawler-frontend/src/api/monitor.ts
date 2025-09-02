import axios from './client';

export interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  network: {
    bytesIn: number;
    bytesOut: number;
  };
}

export interface WorkerStatus {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'busy';
  activeTasks: number;
  completedTasks: number;
  failedTasks: number;
  uptime: number; // 秒
  lastHeartbeat: string;
}

export interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error';
  message?: string;
  uptime?: number;
}

export interface SystemLog {
  id: number;
  level: 'info' | 'warning' | 'error';
  message: string;
  source: string;
  timestamp: string;
  details?: any;
}

export const monitorApi = {
  // 获取系统指标
  getSystemMetrics: async (): Promise<SystemMetrics> => {
    const response = await axios.get('/api/monitor/metrics');
    return response.data;
  },

  // 获取所有Worker状态
  getWorkers: async (): Promise<WorkerStatus[]> => {
    const response = await axios.get('/api/monitor/workers');
    return response.data;
  },

  // 获取服务状态
  getServices: async (): Promise<ServiceStatus[]> => {
    const response = await axios.get('/api/monitor/services');
    return response.data;
  },

  // 获取系统日志
  getLogs: async (params?: {
    level?: string;
    source?: string;
    limit?: number;
    offset?: number;
  }): Promise<SystemLog[]> => {
    const response = await axios.get('/api/monitor/logs', { params });
    return response.data;
  },

  // 重启Worker
  restartWorker: async (workerId: string): Promise<void> => {
    await axios.post(`/api/monitor/workers/${workerId}/restart`);
  },

  // 重启服务
  restartService: async (serviceName: string): Promise<void> => {
    await axios.post(`/api/monitor/services/${serviceName}/restart`);
  },

  // 清理日志
  clearLogs: async (olderThanDays?: number): Promise<{ deleted: number }> => {
    const response = await axios.delete('/api/monitor/logs', {
      params: { older_than_days: olderThanDays },
    });
    return response.data;
  },
};