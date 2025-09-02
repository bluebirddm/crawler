import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { tasksApi } from '@/api/tasks';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
} from 'lucide-react';

export function Tasks() {
  const [crawlUrl, setCrawlUrl] = useState('');
  const [batchUrls, setBatchUrls] = useState('');

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

  const crawlMutation = useMutation({
    mutationFn: tasksApi.createCrawlTask,
    onSuccess: () => {
      setCrawlUrl('');
      refetchActive();
    },
  });

  const batchCrawlMutation = useMutation({
    mutationFn: tasksApi.createBatchCrawlTask,
    onSuccess: () => {
      setBatchUrls('');
      refetchActive();
    },
  });

  const cancelTaskMutation = useMutation({
    mutationFn: tasksApi.cancelTask,
    onSuccess: () => {
      refetchActive();
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
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">任务管理</h2>
        <p className="text-muted-foreground">创建和管理爬取任务</p>
      </div>

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

      {/* 活动任务 */}
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

      {/* 定时任务 */}
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
    </div>
  );
}