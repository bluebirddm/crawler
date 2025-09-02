export interface Article {
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

export interface Task {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  message: string;
  timestamp: string;
  result?: any;
}

export interface CrawlRequest {
  url: string;
  spider_name?: string;
}

export interface BatchCrawlRequest {
  urls: string[];
  spider_name?: string;
}

export interface SystemInfo {
  database_status: string;
  celery_status: string;
  total_articles: number;
  last_crawl_time?: string;
  system_time: string;
}

export interface CategoryStats {
  category: string;
  count: number;
}

export interface DailyStats {
  date: string;
  count: number;
}

export interface Worker {
  name: string;
  status: string;
  active_tasks: number;
  reserved_tasks: number;
}