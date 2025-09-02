import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Activity,
  Cpu,
  HardDrive,
  Wifi,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
  Power,
  Trash2,
  Info,
  AlertTriangle,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import {
  monitorApi,
  type SystemMetrics,
  type WorkerStatus,
  type ServiceStatus,
  type SystemLog,
} from '@/api/monitor';

export function Monitor() {
  const { toast } = useToast();
  const [selectedLogLevel, setSelectedLogLevel] = useState<string>('all');

  // 获取系统指标
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: monitorApi.getSystemMetrics,
    refetchInterval: 5000, // 每5秒刷新
  });

  // 获取Worker状态
  const { data: workers = [], isLoading: workersLoading } = useQuery({
    queryKey: ['workers'],
    queryFn: monitorApi.getWorkers,
    refetchInterval: 10000, // 每10秒刷新
  });

  // 获取服务状态
  const { data: services = [], isLoading: servicesLoading } = useQuery({
    queryKey: ['services'],
    queryFn: monitorApi.getServices,
    refetchInterval: 10000,
  });

  // 获取系统日志
  const { data: logs = [], isLoading: logsLoading, refetch: refetchLogs } = useQuery({
    queryKey: ['system-logs', selectedLogLevel],
    queryFn: () =>
      monitorApi.getLogs({
        level: selectedLogLevel === 'all' ? undefined : selectedLogLevel,
        limit: 100,
      }),
  });

  // 重启Worker
  const restartWorkerMutation = useMutation({
    mutationFn: monitorApi.restartWorker,
    onSuccess: () => {
      toast({
        title: '重启成功',
        description: 'Worker已成功重启',
      });
    },
  });

  // 重启服务
  const restartServiceMutation = useMutation({
    mutationFn: monitorApi.restartService,
    onSuccess: () => {
      toast({
        title: '重启成功',
        description: '服务已成功重启',
      });
    },
  });

  // 清理日志
  const clearLogsMutation = useMutation({
    mutationFn: () => monitorApi.clearLogs(7),
    onSuccess: (data) => {
      toast({
        title: '清理成功',
        description: `已删除 ${data.deleted} 条日志`,
      });
      refetchLogs();
    },
  });

  const formatBytes = (bytes: number) => {
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(2)} GB`;
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}天 ${hours}小时`;
    if (hours > 0) return `${hours}小时 ${minutes}分钟`;
    return `${minutes}分钟`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'stopped':
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'busy':
        return <Activity className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">系统监控</h1>
        <p className="text-muted-foreground">实时监控系统状态和性能</p>
      </div>

      {/* 系统指标卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU使用率</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.cpu.usage.toFixed(1)}%
            </div>
            <Progress value={metrics?.cpu.usage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {metrics?.cpu.cores} 核心
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">内存使用</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.memory.percentage.toFixed(1)}%
            </div>
            <Progress value={metrics?.memory.percentage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {metrics && `${formatBytes(metrics.memory.used)} / ${formatBytes(metrics.memory.total)}`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">磁盘使用</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.disk.percentage.toFixed(1)}%
            </div>
            <Progress value={metrics?.disk.percentage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {metrics && `${formatBytes(metrics.disk.used)} / ${formatBytes(metrics.disk.total)}`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">网络流量</CardTitle>
            <Wifi className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics && formatBytes(metrics.network.bytesIn + metrics.network.bytesOut)}
            </div>
            <div className="mt-2 space-y-1">
              <p className="text-xs text-muted-foreground">
                ↓ {metrics && formatBytes(metrics.network.bytesIn)}
              </p>
              <p className="text-xs text-muted-foreground">
                ↑ {metrics && formatBytes(metrics.network.bytesOut)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="workers" className="space-y-4">
        <TabsList>
          <TabsTrigger value="workers">Workers</TabsTrigger>
          <TabsTrigger value="services">服务</TabsTrigger>
          <TabsTrigger value="logs">系统日志</TabsTrigger>
        </TabsList>

        <TabsContent value="workers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Worker状态</CardTitle>
              <CardDescription>监控和管理Celery Workers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {workers.map((worker) => (
                  <div
                    key={worker.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      {getStatusIcon(worker.status)}
                      <div>
                        <p className="font-medium">{worker.name}</p>
                        <p className="text-sm text-muted-foreground">
                          ID: {worker.id}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-sm text-right">
                        <p>活动任务: {worker.activeTasks}</p>
                        <p className="text-muted-foreground">
                          完成: {worker.completedTasks} | 失败: {worker.failedTasks}
                        </p>
                      </div>
                      <div className="text-sm text-right">
                        <p>运行时间: {formatUptime(worker.uptime)}</p>
                        <p className="text-muted-foreground">
                          最后心跳: {new Date(worker.lastHeartbeat).toLocaleTimeString()}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => restartWorkerMutation.mutate(worker.id)}
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                {workers.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">
                    没有活动的Workers
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>服务状态</CardTitle>
              <CardDescription>系统服务运行状态</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {services.map((service) => (
                  <div
                    key={service.name}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      {getStatusIcon(service.status)}
                      <div>
                        <p className="font-medium">{service.name}</p>
                        {service.message && (
                          <p className="text-sm text-muted-foreground">
                            {service.message}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      {service.uptime && (
                        <p className="text-sm text-muted-foreground">
                          运行时间: {formatUptime(service.uptime)}
                        </p>
                      )}
                      <Badge
                        variant={
                          service.status === 'running'
                            ? 'default'
                            : service.status === 'error'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {service.status === 'running'
                          ? '运行中'
                          : service.status === 'stopped'
                          ? '已停止'
                          : '错误'}
                      </Badge>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => restartServiceMutation.mutate(service.name)}
                      >
                        <Power className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>系统日志</CardTitle>
                  <CardDescription>查看系统运行日志</CardDescription>
                </div>
                <div className="flex space-x-2">
                  <select
                    className="px-3 py-1 border rounded-md"
                    value={selectedLogLevel}
                    onChange={(e) => setSelectedLogLevel(e.target.value)}
                  >
                    <option value="all">所有级别</option>
                    <option value="info">信息</option>
                    <option value="warning">警告</option>
                    <option value="error">错误</option>
                  </select>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => clearLogsMutation.mutate()}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    清理旧日志
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50"
                  >
                    {getLogIcon(log.level)}
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <p className="text-sm font-medium">{log.message}</p>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        来源: {log.source}
                      </p>
                      {log.details && (
                        <pre className="text-xs mt-2 p-2 bg-gray-100 rounded">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                ))}
                {logs.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">
                    没有日志记录
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}