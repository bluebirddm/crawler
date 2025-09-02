import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings,
  User,
  Database,
  Bell,
  Shield,
  Save,
  RefreshCw,
  Download,
  Upload,
  Trash2,
  Plus,
  Edit2,
  Key,
  Mail,
  HardDrive,
  Cpu,
  Globe,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { settingsApi, type SystemConfig, type User as UserType, type CreateUserRequest } from '@/api/settings';

export function Admin() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isAddUserDialogOpen, setIsAddUserDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserType | null>(null);

  // 获取系统配置
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['system-config'],
    queryFn: settingsApi.getConfig,
  });

  // 获取用户列表
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: settingsApi.getUsers,
  });

  // 获取数据库信息
  const { data: dbInfo, isLoading: dbLoading } = useQuery({
    queryKey: ['database-info'],
    queryFn: settingsApi.getDatabaseInfo,
  });

  // 更新配置
  const updateConfigMutation = useMutation({
    mutationFn: settingsApi.updateConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-config'] });
      toast({
        title: '保存成功',
        description: '系统配置已更新',
      });
    },
  });

  // 重置配置
  const resetConfigMutation = useMutation({
    mutationFn: settingsApi.resetConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-config'] });
      toast({
        title: '重置成功',
        description: '系统配置已恢复默认值',
      });
    },
  });

  // 创建用户
  const createUserMutation = useMutation({
    mutationFn: settingsApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setIsAddUserDialogOpen(false);
      toast({
        title: '创建成功',
        description: '用户已成功创建',
      });
    },
  });

  // 更新用户
  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<UserType> }) =>
      settingsApi.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setEditingUser(null);
      toast({
        title: '更新成功',
        description: '用户信息已更新',
      });
    },
  });

  // 删除用户
  const deleteUserMutation = useMutation({
    mutationFn: settingsApi.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast({
        title: '删除成功',
        description: '用户已删除',
      });
    },
  });

  // 备份数据库
  const backupMutation = useMutation({
    mutationFn: settingsApi.backupDatabase,
    onSuccess: (data) => {
      toast({
        title: '备份成功',
        description: `备份文件: ${data.path}`,
      });
      queryClient.invalidateQueries({ queryKey: ['database-info'] });
    },
  });

  // 清理数据库
  const cleanupMutation = useMutation({
    mutationFn: (days: number) => settingsApi.cleanupDatabase(days),
    onSuccess: (data) => {
      toast({
        title: '清理成功',
        description: `已删除 ${data.deleted} 条旧数据`,
      });
      queryClient.invalidateQueries({ queryKey: ['database-info'] });
    },
  });

  // 清理缓存
  const clearCacheMutation = useMutation({
    mutationFn: settingsApi.clearCache,
    onSuccess: () => {
      toast({
        title: '清理成功',
        description: '缓存已清理',
      });
    },
  });

  const handleConfigSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const updatedConfig: Partial<SystemConfig> = {
      crawling: {
        defaultInterval: parseInt(formData.get('defaultInterval') as string),
        maxConcurrent: parseInt(formData.get('maxConcurrent') as string),
        timeout: parseInt(formData.get('timeout') as string),
        retryTimes: parseInt(formData.get('retryTimes') as string),
        userAgent: formData.get('userAgent') as string,
      },
      processing: {
        enableNLP: formData.get('enableNLP') === 'on',
        enableClassification: formData.get('enableClassification') === 'on',
        enableTagging: formData.get('enableTagging') === 'on',
        nlpModel: formData.get('nlpModel') as string,
        minConfidence: parseFloat(formData.get('minConfidence') as string),
      },
      storage: {
        maxArticleAge: parseInt(formData.get('maxArticleAge') as string),
        autoCleanup: formData.get('autoCleanup') === 'on',
        cleanupInterval: parseInt(formData.get('cleanupInterval') as string),
        backupEnabled: formData.get('backupEnabled') === 'on',
        backupPath: formData.get('backupPath') as string,
      },
      notification: {
        enabled: formData.get('notificationEnabled') === 'on',
        email: formData.get('email') as string,
        webhook: formData.get('webhook') as string,
        events: [], // 简化处理
      },
    };

    updateConfigMutation.mutate(updatedConfig);
  };

  const handleUserSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    if (editingUser) {
      const data: Partial<UserType> = {
        username: formData.get('username') as string,
        email: formData.get('email') as string,
        role: formData.get('role') as any,
        isActive: formData.get('isActive') === 'on',
      };
      updateUserMutation.mutate({ id: editingUser.id, data });
    } else {
      const data: CreateUserRequest = {
        username: formData.get('username') as string,
        email: formData.get('email') as string,
        password: formData.get('password') as string,
        role: formData.get('role') as any,
      };
      createUserMutation.mutate(data);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">系统设置</h1>
        <p className="text-muted-foreground">管理系统配置和用户权限</p>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">常规设置</TabsTrigger>
          <TabsTrigger value="crawling">爬取配置</TabsTrigger>
          <TabsTrigger value="processing">处理配置</TabsTrigger>
          <TabsTrigger value="users">用户管理</TabsTrigger>
          <TabsTrigger value="database">数据库</TabsTrigger>
          <TabsTrigger value="system">系统维护</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>通知设置</CardTitle>
              <CardDescription>配置系统通知和告警</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="notificationEnabled"
                    name="notificationEnabled"
                    defaultChecked={config?.notification.enabled}
                  />
                  <Label htmlFor="notificationEnabled">启用通知</Label>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="email">邮件地址</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      defaultValue={config?.notification.email}
                      placeholder="admin@example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="webhook">Webhook URL</Label>
                    <Input
                      id="webhook"
                      name="webhook"
                      type="url"
                      defaultValue={config?.notification.webhook}
                      placeholder="https://hooks.slack.com/..."
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>通知事件</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {['爬取失败', '任务完成', '系统错误', '存储告警'].map((event) => (
                      <div key={event} className="flex items-center space-x-2">
                        <Switch id={event} defaultChecked />
                        <Label htmlFor={event} className="text-sm">
                          {event}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>存储设置</CardTitle>
              <CardDescription>数据存储和清理配置</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="maxArticleAge">文章保留天数</Label>
                    <Input
                      id="maxArticleAge"
                      name="maxArticleAge"
                      type="number"
                      defaultValue={config?.storage.maxArticleAge}
                      min="1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cleanupInterval">清理间隔（小时）</Label>
                    <Input
                      id="cleanupInterval"
                      name="cleanupInterval"
                      type="number"
                      defaultValue={config?.storage.cleanupInterval}
                      min="1"
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="autoCleanup"
                    name="autoCleanup"
                    defaultChecked={config?.storage.autoCleanup}
                  />
                  <Label htmlFor="autoCleanup">自动清理旧数据</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="backupEnabled"
                    name="backupEnabled"
                    defaultChecked={config?.storage.backupEnabled}
                  />
                  <Label htmlFor="backupEnabled">启用自动备份</Label>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="backupPath">备份路径</Label>
                  <Input
                    id="backupPath"
                    name="backupPath"
                    defaultValue={config?.storage.backupPath}
                    placeholder="/var/backups/crawler"
                  />
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="crawling" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>爬取配置</CardTitle>
              <CardDescription>配置爬虫行为和限制</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleConfigSubmit} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="defaultInterval">默认爬取间隔（分钟）</Label>
                    <Input
                      id="defaultInterval"
                      name="defaultInterval"
                      type="number"
                      defaultValue={config?.crawling.defaultInterval}
                      min="1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maxConcurrent">最大并发数</Label>
                    <Input
                      id="maxConcurrent"
                      name="maxConcurrent"
                      type="number"
                      defaultValue={config?.crawling.maxConcurrent}
                      min="1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timeout">超时时间（秒）</Label>
                    <Input
                      id="timeout"
                      name="timeout"
                      type="number"
                      defaultValue={config?.crawling.timeout}
                      min="1"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="retryTimes">重试次数</Label>
                    <Input
                      id="retryTimes"
                      name="retryTimes"
                      type="number"
                      defaultValue={config?.crawling.retryTimes}
                      min="0"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="userAgent">User Agent</Label>
                  <Textarea
                    id="userAgent"
                    name="userAgent"
                    defaultValue={config?.crawling.userAgent}
                    rows={2}
                  />
                </div>
                <div className="flex space-x-2">
                  <Button type="submit">
                    <Save className="mr-2 h-4 w-4" />
                    保存配置
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => resetConfigMutation.mutate()}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    恢复默认
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="processing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>NLP处理配置</CardTitle>
              <CardDescription>文章处理和分析设置</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="enableNLP"
                      name="enableNLP"
                      defaultChecked={config?.processing.enableNLP}
                    />
                    <Label htmlFor="enableNLP">启用NLP处理</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="enableClassification"
                      name="enableClassification"
                      defaultChecked={config?.processing.enableClassification}
                    />
                    <Label htmlFor="enableClassification">启用自动分类</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="enableTagging"
                      name="enableTagging"
                      defaultChecked={config?.processing.enableTagging}
                    />
                    <Label htmlFor="enableTagging">启用自动标签</Label>
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="nlpModel">NLP模型</Label>
                    <Select name="nlpModel" defaultValue={config?.processing.nlpModel}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="bert-base-chinese">BERT中文</SelectItem>
                        <SelectItem value="roberta-chinese">RoBERTa中文</SelectItem>
                        <SelectItem value="gpt2-chinese">GPT2中文</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="minConfidence">最小置信度</Label>
                    <Input
                      id="minConfidence"
                      name="minConfidence"
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      defaultValue={config?.processing.minConfidence}
                    />
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>用户管理</CardTitle>
                  <CardDescription>管理系统用户和权限</CardDescription>
                </div>
                <Dialog open={isAddUserDialogOpen} onOpenChange={setIsAddUserDialogOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      添加用户
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editingUser ? '编辑' : '添加'}用户</DialogTitle>
                      <DialogDescription>
                        {editingUser ? '更新用户信息' : '创建新的系统用户'}
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleUserSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="username">用户名</Label>
                        <Input
                          id="username"
                          name="username"
                          defaultValue={editingUser?.username}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">邮箱</Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          defaultValue={editingUser?.email}
                          required
                        />
                      </div>
                      {!editingUser && (
                        <div className="space-y-2">
                          <Label htmlFor="password">密码</Label>
                          <Input
                            id="password"
                            name="password"
                            type="password"
                            required
                          />
                        </div>
                      )}
                      <div className="space-y-2">
                        <Label htmlFor="role">角色</Label>
                        <Select name="role" defaultValue={editingUser?.role || 'viewer'}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">管理员</SelectItem>
                            <SelectItem value="editor">编辑者</SelectItem>
                            <SelectItem value="viewer">查看者</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      {editingUser && (
                        <div className="flex items-center space-x-2">
                          <Switch
                            id="isActive"
                            name="isActive"
                            defaultChecked={editingUser.isActive}
                          />
                          <Label htmlFor="isActive">激活状态</Label>
                        </div>
                      )}
                      <div className="flex justify-end space-x-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setIsAddUserDialogOpen(false);
                            setEditingUser(null);
                          }}
                        >
                          取消
                        </Button>
                        <Button type="submit">
                          {editingUser ? '更新' : '创建'}
                        </Button>
                      </div>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {users.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <User className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <p className="font-medium">{user.username}</p>
                        <p className="text-sm text-muted-foreground">{user.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-sm text-right">
                        <p className="font-medium">
                          {user.role === 'admin' ? '管理员' : user.role === 'editor' ? '编辑者' : '查看者'}
                        </p>
                        {user.lastLogin && (
                          <p className="text-muted-foreground">
                            最后登录: {new Date(user.lastLogin).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      <div
                        className={`px-2 py-1 rounded-full text-xs ${
                          user.isActive
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {user.isActive ? '激活' : '禁用'}
                      </div>
                      <div className="flex space-x-1">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            setEditingUser(user);
                            setIsAddUserDialogOpen(true);
                          }}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            if (confirm('确定要删除这个用户吗？')) {
                              deleteUserMutation.mutate(user.id);
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="database" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>数据库信息</CardTitle>
              <CardDescription>数据库状态和管理</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-sm text-muted-foreground">数据库大小</p>
                    <p className="text-2xl font-bold">{dbInfo && formatBytes(dbInfo.size * 1024 * 1024)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">数据库版本</p>
                    <p className="text-2xl font-bold">{dbInfo?.version}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">最后备份</p>
                    <p className="text-sm">
                      {dbInfo?.lastBackup
                        ? new Date(dbInfo.lastBackup).toLocaleString()
                        : '从未备份'}
                    </p>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-3">数据表统计</h4>
                  <div className="space-y-2">
                    {dbInfo?.tables.map((table) => (
                      <div key={table.name} className="flex justify-between items-center">
                        <span className="text-sm">{table.name}</span>
                        <div className="text-sm text-muted-foreground">
                          <span>{table.rowCount} 行</span>
                          <span className="ml-4">{formatBytes(table.size * 1024 * 1024)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button onClick={() => backupMutation.mutate()}>
                    <Download className="mr-2 h-4 w-4" />
                    备份数据库
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      if (confirm('确定要清理30天前的数据吗？')) {
                        cleanupMutation.mutate(30);
                      }
                    }}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    清理旧数据
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>系统维护</CardTitle>
              <CardDescription>系统维护和优化操作</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">缓存管理</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4">
                        清理系统缓存以释放内存和提高性能
                      </p>
                      <Button onClick={() => clearCacheMutation.mutate()}>
                        <Trash2 className="mr-2 h-4 w-4" />
                        清理缓存
                      </Button>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">日志导出</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4">
                        导出系统日志用于分析和审计
                      </p>
                      <Button
                        onClick={async () => {
                          const blob = await settingsApi.exportLogs();
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `系统日志_${new Date().toISOString().split('T')[0]}.log`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          window.URL.revokeObjectURL(url);
                        }}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        导出日志
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}