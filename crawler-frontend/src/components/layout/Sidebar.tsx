import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  FileText,
  ListTodo,
  Settings,
  Database,
  Activity,
  BarChart,
  Flame,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: '仪表板', href: '/', icon: Home },
  { name: '文章管理', href: '/articles', icon: FileText },
  { name: '热门文章', href: '/hot', icon: Flame },
  { name: '任务管理', href: '/tasks', icon: ListTodo },
  { name: '爬取源', href: '/sources', icon: Database },
  { name: '系统监控', href: '/monitor', icon: Activity },
  { name: '数据统计', href: '/stats', icon: BarChart },
  { name: '系统设置', href: '/admin', icon: Settings },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900">
      <div className="flex h-16 items-center px-6">
        <h1 className="text-xl font-bold text-white">爬虫管理系统</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )}
            >
              <Icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}