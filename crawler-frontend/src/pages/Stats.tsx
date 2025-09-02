import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Download,
  Calendar,
  BarChart3,
  PieChartIcon,
  Activity,
  FileText,
  Clock,
  Zap,
  Hash,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { statsApi } from '@/api/stats';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export function Stats() {
  const [timeRange, setTimeRange] = useState('7');
  const [exportFormat, setExportFormat] = useState<'csv' | 'excel' | 'pdf'>('excel');

  // 获取统计概览
  const { data: overview } = useQuery({
    queryKey: ['stats-overview'],
    queryFn: statsApi.getOverview,
  });

  // 获取每日统计
  const { data: dailyStats = [] } = useQuery({
    queryKey: ['daily-stats', timeRange],
    queryFn: () => statsApi.getDailyStats(parseInt(timeRange)),
  });

  // 获取分类统计
  const { data: categoryStats = [] } = useQuery({
    queryKey: ['category-stats'],
    queryFn: statsApi.getCategoryStats,
  });

  // 获取爬取源统计
  const { data: sourceStats = [] } = useQuery({
    queryKey: ['source-stats'],
    queryFn: statsApi.getSourceStats,
  });

  // 获取标签统计
  const { data: tagStats = [] } = useQuery({
    queryKey: ['tag-stats'],
    queryFn: () => statsApi.getTagStats(20),
  });

  // 获取时间序列数据
  const { data: timeSeriesData = [] } = useQuery({
    queryKey: ['time-series', timeRange],
    queryFn: () => statsApi.getTimeSeries('articles', 'day', parseInt(timeRange)),
  });

  const handleExport = async () => {
    try {
      const blob = await statsApi.exportReport(exportFormat);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `统计报告_${new Date().toISOString().split('T')[0]}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出失败:', error);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      case 'stable':
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">数据统计</h1>
          <p className="text-muted-foreground">分析系统数据和趋势</p>
        </div>
        <div className="flex space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">最近7天</SelectItem>
              <SelectItem value="14">最近14天</SelectItem>
              <SelectItem value="30">最近30天</SelectItem>
              <SelectItem value="90">最近90天</SelectItem>
            </SelectContent>
          </Select>
          <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as any)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="csv">CSV</SelectItem>
              <SelectItem value="excel">Excel</SelectItem>
              <SelectItem value="pdf">PDF</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            导出报告
          </Button>
        </div>
      </div>

      {/* 统计概览卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">文章总数</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(overview?.totalArticles || 0)}</div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-xs text-green-500">+{overview?.weekGrowth || 0}%</span>
              <span className="text-xs text-muted-foreground ml-2">本周</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日文章</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.todayArticles || 0}</div>
            <p className="text-xs text-muted-foreground mt-2">
              今日任务: {overview?.todayTasks || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">爬取源</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.totalSources || 0}</div>
            <p className="text-xs text-muted-foreground mt-2">
              活动Workers: {overview?.activeWorkers || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">月增长</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">+{overview?.monthGrowth || 0}%</div>
            <p className="text-xs text-muted-foreground mt-2">
              相比上月
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
          <TabsTrigger value="categories">分类统计</TabsTrigger>
          <TabsTrigger value="sources">爬取源分析</TabsTrigger>
          <TabsTrigger value="tags">标签云</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>文章增长趋势</CardTitle>
              <CardDescription>每日文章数量和任务执行情况</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={dailyStats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="articlesCount"
                    stackId="1"
                    stroke="#8884d8"
                    fill="#8884d8"
                    name="文章数"
                  />
                  <Area
                    type="monotone"
                    dataKey="tasksCount"
                    stackId="1"
                    stroke="#82ca9d"
                    fill="#82ca9d"
                    name="任务数"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>成功率趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={dailyStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="successRate"
                      stroke="#00C49F"
                      name="成功率(%)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>平均处理时间</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={dailyStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="avgProcessingTime"
                      stroke="#FF8042"
                      name="处理时间(秒)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="categories" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>分类分布</CardTitle>
                <CardDescription>各分类文章占比</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryStats}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {categoryStats.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>分类排行</CardTitle>
                <CardDescription>文章数量排名</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {categoryStats.slice(0, 6).map((category, index) => (
                    <div key={category.category} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium w-6">{index + 1}</span>
                        <span className="text-sm">{category.category}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">{category.count}</span>
                        {getTrendIcon(category.trend)}
                        <Badge variant={category.change > 0 ? 'default' : 'secondary'}>
                          {category.change > 0 ? '+' : ''}{category.change}%
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>爬取源性能</CardTitle>
              <CardDescription>各爬取源的文章数量和性能指标</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={sourceStats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="sourceName" />
                  <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                  <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="totalArticles" fill="#8884d8" name="总文章数" />
                  <Bar yAxisId="left" dataKey="todayArticles" fill="#82ca9d" name="今日文章" />
                  <Bar yAxisId="right" dataKey="successRate" fill="#ffc658" name="成功率(%)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>爬取源详情</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {sourceStats.map((source) => (
                  <div key={source.sourceId} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{source.sourceName}</p>
                        <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">总文章:</span>
                            <span className="ml-2 font-medium">{source.totalArticles}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">今日:</span>
                            <span className="ml-2 font-medium">{source.todayArticles}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">成功率:</span>
                            <span className="ml-2 font-medium">{source.successRate}%</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">响应时间:</span>
                            <span className="ml-2 font-medium">{source.avgResponseTime}ms</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    {source.lastError && (
                      <p className="text-xs text-red-500 mt-2">
                        最后错误: {new Date(source.lastError).toLocaleString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tags" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>热门标签</CardTitle>
              <CardDescription>使用频率最高的标签</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {tagStats.map((tag) => {
                  const size = Math.min(Math.max(tag.count / 10, 0.8), 2);
                  return (
                    <Badge
                      key={tag.tag}
                      variant={tag.trending ? 'default' : 'secondary'}
                      style={{ fontSize: `${size}rem`, padding: `${size * 0.3}rem ${size * 0.5}rem` }}
                    >
                      {tag.tag}
                      <span className="ml-1 text-xs">({tag.articles})</span>
                    </Badge>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>标签趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={tagStats.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="tag" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="articles" fill="#8884d8" name="文章数" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}