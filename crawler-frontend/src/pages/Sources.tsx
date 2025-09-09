import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit2, Trash2, Play, TestTube, RefreshCw, Globe, Clock, Hash, Search, Filter, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { sourcesApi, type CrawlerSource, type CreateSourceRequest } from '@/api/sources';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';

export function Sources() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<CrawlerSource | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // 获取爬取源列表
  const { data: sources = [], isLoading, refetch } = useQuery({
    queryKey: ['sources'],
    queryFn: sourcesApi.getSources,
    refetchInterval: 30000, // 每30秒自动刷新
  });

  // 获取所有分类
  const categories = useMemo(() => {
    const cats = new Set(sources.map(s => s.category));
    return Array.from(cats);
  }, [sources]);

  // 过滤源列表
  const filteredSources = useMemo(() => {
    return sources.filter((source) => {
      const matchesSearch = source.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           source.url.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = categoryFilter === 'all' || source.category === categoryFilter;
      const matchesStatus = statusFilter === 'all' ||
                           (statusFilter === 'enabled' && source.enabled) ||
                           (statusFilter === 'disabled' && !source.enabled);
      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [sources, searchTerm, categoryFilter, statusFilter]);

  // 创建爬取源
  const createMutation = useMutation({
    mutationFn: sourcesApi.createSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      setIsAddDialogOpen(false);
      toast({
        title: '创建成功',
        description: '爬取源已成功创建',
      });
    },
    onError: () => {
      toast({
        title: '创建失败',
        description: '无法创建爬取源',
        variant: 'destructive',
      });
    },
  });

  // 更新爬取源
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateSourceRequest> }) =>
      sourcesApi.updateSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      setEditingSource(null);
      toast({
        title: '更新成功',
        description: '爬取源已成功更新',
      });
    },
  });

  // 删除爬取源
  const deleteMutation = useMutation({
    mutationFn: sourcesApi.deleteSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      toast({
        title: '删除成功',
        description: '爬取源已成功删除',
      });
    },
  });

  // 测试爬取源
  const testMutation = useMutation({
    mutationFn: sourcesApi.testSource,
    onSuccess: (data) => {
      toast({
        title: data.success ? '测试成功' : '测试失败',
        description: data.message,
        variant: data.success ? 'default' : 'destructive',
      });
    },
  });

  // 触发爬取
  const triggerMutation = useMutation({
    mutationFn: sourcesApi.triggerCrawl,
    onSuccess: (data) => {
      toast({
        title: '爬取已启动',
        description: `任务ID: ${data.taskId}`,
      });
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data: CreateSourceRequest = {
      name: formData.get('name') as string,
      url: formData.get('url') as string,
      interval: parseInt(formData.get('interval') as string),
      selector: formData.get('selector') as string,
      category: formData.get('category') as string,
      enabled: formData.get('enabled') === 'on',
    };

    if (editingSource) {
      updateMutation.mutate({ id: editingSource.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '从未';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">爬取源管理</h1>
          <p className="text-muted-foreground">配置和管理网站爬取源</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => refetch()}
            title="刷新列表"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                添加爬取源
              </Button>
            </DialogTrigger>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>{editingSource ? '编辑' : '添加'}爬取源</DialogTitle>
              <DialogDescription>
                配置网站URL、爬取间隔和内容选择器
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">名称</Label>
                <Input
                  id="name"
                  name="name"
                  defaultValue={editingSource?.name}
                  placeholder="例如：科技新闻网"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="url">网站URL</Label>
                <Input
                  id="url"
                  name="url"
                  type="url"
                  defaultValue={editingSource?.url}
                  placeholder="https://example.com"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="interval">爬取间隔（分钟）</Label>
                <Input
                  id="interval"
                  name="interval"
                  type="number"
                  defaultValue={editingSource?.interval || 60}
                  min="5"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="selector">CSS选择器</Label>
                <Input
                  id="selector"
                  name="selector"
                  defaultValue={editingSource?.selector || 'article'}
                  placeholder="例如：.article-content"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="category">分类</Label>
                <Input
                  id="category"
                  name="category"
                  defaultValue={editingSource?.category}
                  placeholder="例如：科技"
                  required
                />
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="enabled"
                  name="enabled"
                  defaultChecked={editingSource?.enabled ?? true}
                />
                <Label htmlFor="enabled">启用自动爬取</Label>
              </div>
              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsAddDialogOpen(false);
                    setEditingSource(null);
                  }}
                >
                  取消
                </Button>
                <Button type="submit">
                  {editingSource ? '更新' : '创建'}
                </Button>
              </div>
            </form>
          </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* 搜索和筛选栏 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索爬取源名称或URL..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="选择分类" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有分类</SelectItem>
            {categories.map(cat => (
              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="选择状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有状态</SelectItem>
            <SelectItem value="enabled">已启用</SelectItem>
            <SelectItem value="disabled">已禁用</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 统计信息 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">总爬取源</p>
                <p className="text-2xl font-bold">{sources.length}</p>
              </div>
              <Globe className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已启用</p>
                <p className="text-2xl font-bold">{sources.filter(s => s.enabled).length}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已禁用</p>
                <p className="text-2xl font-bold">{sources.filter(s => !s.enabled).length}</p>
              </div>
              <XCircle className="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">文章总数</p>
                <p className="text-2xl font-bold">{sources.reduce((sum, s) => sum + s.articleCount, 0)}</p>
              </div>
              <Hash className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 爬取源列表 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredSources.map((source) => (
          <Card key={source.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{source.name}</CardTitle>
                  <CardDescription className="text-xs mt-1">
                    {source.url}
                  </CardDescription>
                </div>
                <div className="flex space-x-1">
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => testMutation.mutate(source.id)}
                    disabled={testMutation.isPending}
                    title="测试连接"
                  >
                    <TestTube className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => triggerMutation.mutate(source.id)}
                    disabled={triggerMutation.isPending || !source.enabled}
                    title="立即爬取"
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => {
                      setEditingSource(source);
                      setIsAddDialogOpen(true);
                    }}
                    title="编辑"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => {
                      if (confirm('确定要删除这个爬取源吗？')) {
                        deleteMutation.mutate(source.id);
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    title="删除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="flex items-center text-muted-foreground">
                    <Clock className="mr-1 h-3 w-3" />
                    间隔
                  </span>
                  <span>{source.interval} 分钟</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center text-muted-foreground">
                    <Globe className="mr-1 h-3 w-3" />
                    分类
                  </span>
                  <Badge variant="secondary">{source.category}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center text-muted-foreground">
                    <Hash className="mr-1 h-3 w-3" />
                    文章数
                  </span>
                  <span>{source.articleCount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">状态</span>
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      source.enabled
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {source.enabled ? '已启用' : '已禁用'}
                  </span>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">
                    上次爬取：{formatDate(source.lastCrawled)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 空状态 */}
      {filteredSources.length === 0 && searchTerm === '' && categoryFilter === 'all' && statusFilter === 'all' && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Globe className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-900">还没有爬取源</p>
            <p className="text-sm text-gray-500 mt-1">点击上方按钮添加第一个爬取源</p>
          </CardContent>
        </Card>
      )}

      {/* 搜索无结果 */}
      {filteredSources.length === 0 && (searchTerm !== '' || categoryFilter !== 'all' || statusFilter !== 'all') && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-900">没有找到匹配的爬取源</p>
            <p className="text-sm text-gray-500 mt-1">请尝试调整搜索条件</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => {
                setSearchTerm('');
                setCategoryFilter('all');
                setStatusFilter('all');
              }}
            >
              清除筛选
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}