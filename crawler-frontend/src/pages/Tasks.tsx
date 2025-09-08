import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/api/tasks';
import type { TaskHistoryQuery } from '@/api/tasks';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Play,
  Pause,
  X,
  RefreshCw,
  Globe,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  RotateCcw,
  Trash2,
  TrendingUp,
  Activity,
} from 'lucide-react';

export function Tasks() {
  const queryClient = useQueryClient();
  const [crawlUrl, setCrawlUrl] = useState('');
  const [batchUrls, setBatchUrls] = useState('');
  
  // 历史任务查询参数
  const [historyQuery, setHistoryQuery] = useState<TaskHistoryQuery>({
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    order: 'desc',
  });

  const { data: activeTasks, refetch: refetchActive } = useQuery({
    queryKey: ['activeTasks'],
    queryFn: tasksApi.getActiveTasks,
    refetchInterval: 3000,
  });

  const { data: scheduledTasks, refetch: refetchScheduled } = useQuery({
    queryKey: ['scheduledTasks'],
    queryFn: tasksApi.getScheduledTasks,
    refetchInterval: 5000,
  });

  const { data: taskHistory, isLoading: isHistoryLoading } = useQuery({
    queryKey: ['taskHistory', historyQuery],
    queryFn: () => tasksApi.getTaskHistory(historyQuery),
  });

  const { data: taskStats } = useQuery({
    queryKey: ['taskStats'],
    queryFn: tasksApi.getTaskStats,
    refetchInterval: 30000,
  });

  const crawlMutation = useMutation({
    mutationFn: tasksApi.createCrawlTask,
    onSuccess: () => {
      setCrawlUrl('');
      refetchActive();
      queryClient.invalidateQueries({ queryKey: ['taskHistory'] });
    },
  });

  const batchCrawlMutation = useMutation({
    mutationFn: tasksApi.createBatchCrawlTask,
    onSuccess: () => {
      setBatchUrls('');
      refetchActive();
      queryClient.invalidateQueries({ queryKey: ['taskHistory'] });
    },
  });

  const cancelTaskMutation = useMutation({
    mutationFn: tasksApi.cancelTask,
    onSuccess: () => {
      refetchActive();
      queryClient.invalidateQueries({ queryKey: ['taskHistory'] });
    },
  });

  const deleteHistoryMutation = useMutation({
    mutationFn: tasksApi.deleteTaskHistory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['taskHistory'] });
    },
  });

  const handleCrawl = () => {
    if (crawlUrl) {
      crawlMutation.mutate({ url: crawlUrl });
    }
  };

  const handleBatchCrawl = () => {
    if (batchUrls) {
      const urls = batchUrls.split('\n').filter((url) => url.trim());
      if (urls.length > 0) {
        batchCrawlMutation.mutate({ urls });
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failure':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'retry':
        return <RotateCcw className="h-4 w-4 text-orange-500" />;
      case 'revoked':
        return <X className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      pending: 'secondary',
      running: 'default',
      success: 'outline',
      failure: 'destructive',
      retry: 'secondary',
      revoked: 'secondary',
    };
    
    return (
      <Badge variant={variants[status] || 'default'}>
        {status}
      </Badge>
    );
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const totalPages = taskHistory ? Math.ceil(taskHistory.total / taskHistory.page_size) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">任务管理</h2>
        <p className="text-muted-foreground">创建和管理爬取任务</p>
      </div>

      {/* 统计卡片 */}
      {taskStats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">总任务数</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{taskStats.total_tasks}</div>
              <p className="text-xs text-muted-foreground">
                24小时内: {taskStats.recent_tasks_24h}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">成功率</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{taskStats.success_rate}%</div>
              <p className="text-xs text-muted-foreground">
                成功: {taskStats.status_counts.success || 0}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">失败任务</CardTitle>
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{taskStats.status_counts.failure || 0}</div>
              <p className="text-xs text-muted-foreground">
                重试中: {taskStats.status_counts.retry || 0}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">平均耗时</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatDuration(taskStats.avg_duration_seconds)}
              </div>
              <p className="text-xs text-muted-foreground">
                执行中: {taskStats.status_counts.running || 0}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 创建任务 */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>单个URL爬取</CardTitle>
            <CardDescription>输入单个URL进行爬取</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="https://example.com"
                  value={crawlUrl}
                  onChange={(e) => setCrawlUrl(e.target.value)}
                />
                <Button
                  onClick={handleCrawl}
                  disabled={!crawlUrl || crawlMutation.isPending}
                >
                  {crawlMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="mr-2 h-4 w-4" />
                  )}
                  爬取
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>批量URL爬取</CardTitle>
            <CardDescription>每行输入一个URL</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <textarea
                className="w-full h-24 px-3 py-2 text-sm rounded-md border border-input bg-background"
                placeholder="https://example1.com&#10;https://example2.com&#10;https://example3.com"
                value={batchUrls}
                onChange={(e) => setBatchUrls(e.target.value)}
              />
              <Button
                onClick={handleBatchCrawl}
                disabled={!batchUrls || batchCrawlMutation.isPending}
                className="w-full"
              >
                {batchCrawlMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                批量爬取
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 任务列表标签页 */}
      <Tabs defaultValue="active" className="space-y-4">
        <TabsList>
          <TabsTrigger value="active">活动任务</TabsTrigger>
          <TabsTrigger value="scheduled">定时任务</TabsTrigger>
          <TabsTrigger value="history">历史记录</TabsTrigger>
        </TabsList>

        {/* 活动任务 */}
        <TabsContent value="active">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>活动任务</CardTitle>
                  <CardDescription>正在执行的爬取任务</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={() => refetchActive()}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {activeTasks && activeTasks.length > 0 ? (
                  activeTasks.map((task: any) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        {getStatusIcon('running')}
                        <div>
                          <p className="font-medium text-sm">{task.name}</p>
                          <p className="text-xs text-muted-foreground">
                            Worker: {task.worker}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {task.args && task.args[0] && (
                          <span className="text-xs text-muted-foreground flex items-center">
                            <Globe className="h-3 w-3 mr-1" />
                            {new URL(task.args[0]).hostname}
                          </span>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => cancelTaskMutation.mutate(task.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-muted-foreground py-4">
                    没有活动的任务
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 定时任务 */}
        <TabsContent value="scheduled">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>定时任务</CardTitle>
                  <CardDescription>计划执行的任务</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={() => refetchScheduled()}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {scheduledTasks && scheduledTasks.length > 0 ? (
                  scheduledTasks.map((task: any) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        {getStatusIcon('pending')}
                        <div>
                          <p className="font-medium text-sm">{task.name}</p>
                          <p className="text-xs text-muted-foreground">
                            Worker: {task.worker}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {task.eta && (
                          <span className="text-xs text-muted-foreground">
                            计划时间: {new Date(task.eta).toLocaleString()}
                          </span>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => cancelTaskMutation.mutate(task.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-muted-foreground py-4">
                    没有定时任务
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 历史记录 */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>任务历史</CardTitle>
                    <CardDescription>所有执行过的任务记录</CardDescription>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => queryClient.invalidateQueries({ queryKey: ['taskHistory'] })}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
                
                {/* 筛选器 */}
                <div className="flex gap-2">
                  <Select
                    value={historyQuery.status || 'all'}
                    onValueChange={(value) => 
                      setHistoryQuery(prev => ({
                        ...prev,
                        status: value === 'all' ? undefined : value,
                        page: 1,
                      }))
                    }
                  >
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="状态筛选" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      <SelectItem value="success">成功</SelectItem>
                      <SelectItem value="failure">失败</SelectItem>
                      <SelectItem value="running">执行中</SelectItem>
                      <SelectItem value="pending">等待中</SelectItem>
                      <SelectItem value="retry">重试中</SelectItem>
                      <SelectItem value="revoked">已取消</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Select
                    value={historyQuery.task_type || 'all'}
                    onValueChange={(value) => 
                      setHistoryQuery(prev => ({
                        ...prev,
                        task_type: value === 'all' ? undefined : value,
                        page: 1,
                      }))
                    }
                  >
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="任务类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部类型</SelectItem>
                      <SelectItem value="crawl_url">单个爬取</SelectItem>
                      <SelectItem value="crawl_batch">批量爬取</SelectItem>
                      <SelectItem value="scheduled_crawl">定时爬取</SelectItem>
                      <SelectItem value="reprocess">重新处理</SelectItem>
                      <SelectItem value="cleanup">清理任务</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Select
                    value={historyQuery.sort_by || 'created_at'}
                    onValueChange={(value: any) => 
                      setHistoryQuery(prev => ({
                        ...prev,
                        sort_by: value,
                      }))
                    }
                  >
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="排序方式" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="created_at">创建时间</SelectItem>
                      <SelectItem value="completed_at">完成时间</SelectItem>
                      <SelectItem value="status">状态</SelectItem>
                      <SelectItem value="task_type">任务类型</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isHistoryLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : taskHistory && taskHistory.tasks.length > 0 ? (
                <div className="space-y-4">
                  <div className="rounded-md border">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b bg-muted/50">
                          <th className="p-2 text-left text-sm">状态</th>
                          <th className="p-2 text-left text-sm">任务类型</th>
                          <th className="p-2 text-left text-sm">URL</th>
                          <th className="p-2 text-left text-sm">创建时间</th>
                          <th className="p-2 text-left text-sm">耗时</th>
                          <th className="p-2 text-left text-sm">操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {taskHistory.tasks.map((task) => (
                          <tr key={task.id} className="border-b">
                            <td className="p-2">
                              <div className="flex items-center gap-2">
                                {getStatusIcon(task.status)}
                                {getStatusBadge(task.status)}
                              </div>
                            </td>
                            <td className="p-2 text-sm">{task.task_type}</td>
                            <td className="p-2 text-sm">
                              {task.url ? (
                                <span className="text-xs">
                                  {new URL(task.url).hostname}
                                </span>
                              ) : task.urls ? (
                                <span className="text-xs">
                                  {task.urls.length} URLs
                                </span>
                              ) : (
                                '-'
                              )}
                            </td>
                            <td className="p-2 text-sm">
                              {new Date(task.created_at).toLocaleString()}
                            </td>
                            <td className="p-2 text-sm">
                              {formatDuration(task.duration_seconds)}
                            </td>
                            <td className="p-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => deleteHistoryMutation.mutate(task.task_id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* 分页 */}
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      共 {taskHistory.total} 条记录
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={historyQuery.page === 1}
                        onClick={() => 
                          setHistoryQuery(prev => ({
                            ...prev,
                            page: Math.max(1, (prev.page || 1) - 1),
                          }))
                        }
                      >
                        上一页
                      </Button>
                      <span className="flex items-center px-3 text-sm">
                        {historyQuery.page} / {totalPages}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={historyQuery.page === totalPages}
                        onClick={() => 
                          setHistoryQuery(prev => ({
                            ...prev,
                            page: Math.min(totalPages, (prev.page || 1) + 1),
                          }))
                        }
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  暂无历史记录
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}