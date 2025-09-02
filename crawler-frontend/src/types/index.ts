interface Article {
  id: number;
  url: string;
  title: string;
  content: string;
  author?: string;
  publish_date?: string;
  source?: string;
  source_domain?: string;
  category?: string;
  tags?: string[];
  level: number;
  sentiment?: number;
  keywords?: string[];
  summary?: string;
  crawl_time: string;
  update_time: string;
}

export type { Article };

interface Task {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  message: string;
  timestamp: string;
  result?: any;
}

interface CrawlRequest {
  url: string;
  spider_name?: string;
}

interface BatchCrawlRequest {
  urls: string[];
  spider_name?: string;
}

interface SystemInfo {
  database_status: string;
  celery_status: string;
  total_articles: number;
  last_crawl_time?: string;
  system_time: string;
}

interface CategoryStats {
  category: string;
  count: number;
}

interface DailyStats {
  date: string;
  count: number;
}

export type Worker = {
  name: string;
  status: string;
  active_tasks: number;
  reserved_tasks: number;
};

export type User = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
};

export type SystemConfig = {
  crawl_interval: number;
  max_depth: number;
  max_workers: number;
  timeout: number;
  user_agent: string;
  proxy_enabled: boolean;
  proxy_url?: string;
};

export type CreateUserRequest = {
  username: string;
  email: string;
  password: string;
  is_admin?: boolean;
};

export type Source = {
  id: number;
  name: string;
  url: string;
  enabled: boolean;
  frequency: string;
  last_crawl?: string;
  created_at: string;
  updated_at: string;
};

export type CreateSourceRequest = {
  name: string;
  url: string;
  enabled?: boolean;
  frequency?: string;
};

export type MonitorStats = {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  redis_status: string;
  postgres_status: string;
  celery_workers: number;
  pending_tasks: number;
  active_tasks: number;
};

export type {
  Task,
  CrawlRequest,
  BatchCrawlRequest,
  SystemInfo,
  CategoryStats,
  DailyStats
};