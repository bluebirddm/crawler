import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { adminApi, articlesApi } from '@/api';
import { Activity, Database, FileText, TrendingUp } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export function Dashboard() {
  const { data: systemInfo } = useQuery({
    queryKey: ['systemInfo'],
    queryFn: adminApi.getSystemInfo,
    refetchInterval: 5000,
  });

  const { data: dailyStats } = useQuery({
    queryKey: ['dailyStats'],
    queryFn: () => articlesApi.getDailyStats(7),
  });

  const { data: categoryStats } = useQuery({
    queryKey: ['categoryStats'],
    queryFn: articlesApi.getCategoryStats,
  });

  const { data: workers } = useQuery({
    queryKey: ['workers'],
    queryFn: adminApi.getWorkersStatus,
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">仪表板</h2>
        <p className="text-muted-foreground">系统运行状态概览</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">文章总数</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo?.total_articles || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              累计爬取文章数量
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">数据库状态</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo?.database_status || '未知'}
            </div>
            <p className="text-xs text-muted-foreground">
              PostgreSQL连接状态
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Celery状态</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo?.celery_status || '未知'}
            </div>
            <p className="text-xs text-muted-foreground">
              任务队列运行状态
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活动Workers</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workers?.length || 0}</div>
            <p className="text-xs text-muted-foreground">
              正在运行的工作进程
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 图表 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* 每日爬取趋势 */}
        <Card>
          <CardHeader>
            <CardTitle>爬取趋势</CardTitle>
            <CardDescription>最近7天文章爬取数量</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyStats || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#8884d8"
                  name="文章数"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 分类统计 */}
        <Card>
          <CardHeader>
            <CardTitle>分类分布</CardTitle>
            <CardDescription>文章分类统计</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryStats || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, percent }) =>
                    `${category} ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {categoryStats?.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Workers状态 */}
      <Card>
        <CardHeader>
          <CardTitle>Workers状态</CardTitle>
          <CardDescription>Celery工作进程详情</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workers?.map((worker) => (
              <div
                key={worker.name}
                className="flex items-center justify-between rounded-lg border p-4"
              >
                <div>
                  <p className="font-medium">{worker.name}</p>
                  <p className="text-sm text-muted-foreground">
                    状态: {worker.status}
                  </p>
                </div>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">活动任务: </span>
                    <span className="font-medium">{worker.active_tasks}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">保留任务: </span>
                    <span className="font-medium">{worker.reserved_tasks}</span>
                  </div>
                </div>
              </div>
            ))}
            {(!workers || workers.length === 0) && (
              <p className="text-center text-muted-foreground">
                没有活动的Worker
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}