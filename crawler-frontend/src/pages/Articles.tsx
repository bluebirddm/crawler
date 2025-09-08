import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { articlesApi } from '@/api/articles';
import type { Article } from '../types';
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Search, Trash2, Eye, RefreshCw, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export function Articles() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedLevel, setSelectedLevel] = useState<number | undefined>();
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const pageSize = 10;
  const queryClient = useQueryClient();

  const {
    data: articles,
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ['searchArticles', searchQuery, selectedCategory, selectedLevel, currentPage],
    queryFn: () =>
      articlesApi.searchArticles({
        q: searchQuery || undefined,
        category: selectedCategory || undefined,
        level: selectedLevel,
        skip: currentPage * pageSize,
        limit: pageSize,
      }),
  });

  const {
    data: selectedArticle,
    isLoading: isSelectedArticleLoading,
  } = useQuery({
    queryKey: ['article', selectedArticleId],
    queryFn: () => articlesApi.getArticle(selectedArticleId!),
    enabled: !!selectedArticleId,
  });

  const deleteMutation = useMutation({
    mutationFn: articlesApi.deleteArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['searchArticles'] });
    },
  });

  const getLevelColor = (level: number) => {
    const colors = ['bg-gray-500', 'bg-green-500', 'bg-blue-500', 'bg-purple-500', 'bg-red-500'];
    return colors[level - 1] || colors[0];
  };

  const getSentimentText = (sentiment?: number) => {
    if (!sentiment) return '中性';
    if (sentiment > 0.3) return '正面';
    if (sentiment < -0.3) return '负面';
    return '中性';
  };

  const handleViewArticle = (articleId: number) => {
    setSelectedArticleId(articleId);
    setIsViewDialogOpen(true);
  };

  const handleCloseViewDialog = () => {
    setIsViewDialogOpen(false);
    setSelectedArticleId(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">文章管理</h2>
          <p className="text-muted-foreground">查看和管理爬取的文章</p>
        </div>
        <Button onClick={() => refetch()}>
          <RefreshCw
            className={`mr-2 h-4 w-4 ${
              isFetching ? 'animate-spin' : ''
            }`}
          />
          刷新
        </Button>
      </div>

      {/* 搜索和筛选 */}
      <Card>
        <CardHeader>
          <CardTitle>搜索筛选</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="搜索文章标题或内容..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(0);
                  }}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setCurrentPage(0);
              }}
              className="rounded-md border border-input bg-background px-3 py-2"
            >
              <option value="">所有分类</option>
              <option value="科技">科技</option>
              <option value="财经">财经</option>
              <option value="教育">教育</option>
              <option value="健康">健康</option>
              <option value="娱乐">娱乐</option>
              <option value="体育">体育</option>
              <option value="政策">政策</option>
              <option value="社会">社会</option>
              <option value="文化">文化</option>
              <option value="国际">国际</option>
            </select>
            <select
              value={selectedLevel || ''}
              onChange={(e) => {
                setSelectedLevel(e.target.value ? Number(e.target.value) : undefined);
                setCurrentPage(0);
              }}
              className="rounded-md border border-input bg-background px-3 py-2"
            >
              <option value="">所有级别</option>
              <option value="1">级别 1</option>
              <option value="2">级别 2</option>
              <option value="3">级别 3</option>
              <option value="4">级别 4</option>
              <option value="5">级别 5</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* 文章列表 */}
      <div className="space-y-4">
        {isLoading ? (
          <Card>
            <CardContent className="text-center py-8">
              <p className="text-muted-foreground">加载中...</p>
            </CardContent>
          </Card>
        ) : articles && articles.length > 0 ? (
          articles.map((article: Article) => (
            <Card key={article.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <CardTitle className="text-xl">{article.title}</CardTitle>
                    <CardDescription>
                      {article.source_domain} · {article.author || '未知作者'} ·{' '}
                      {format(new Date(article.crawl_time), 'yyyy-MM-dd HH:mm', {
                        locale: zhCN,
                      })}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <span
                      className={`px-2 py-1 text-xs text-white rounded ${getLevelColor(
                        article.level
                      )}`}
                    >
                      L{article.level}
                    </span>
                    {article.category && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {article.category}
                      </span>
                    )}
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                      {getSentimentText(article.sentiment)}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {article.summary || article.content.substring(0, 200)}...
                </p>
                {article.tags && article.tags.length > 0 && (
                  <div className="flex gap-2 mt-3">
                    {article.tags.slice(0, 5).map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-gray-100 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex justify-between items-center mt-4">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    查看原文
                  </a>
                  <div className="flex gap-2">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleViewArticle(article.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => deleteMutation.mutate(article.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="text-center py-8">
              <p className="text-muted-foreground">暂无文章</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 分页 */}
      <div className="flex justify-center gap-2">
        <Button
          variant="outline"
          onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
          disabled={currentPage === 0}
        >
          上一页
        </Button>
        <span className="flex items-center px-4">
          第 {currentPage + 1} 页
        </span>
        <Button
          variant="outline"
          onClick={() => setCurrentPage(currentPage + 1)}
          disabled={!articles || articles.length < pageSize}
        >
          下一页
        </Button>
      </div>

      {/* 文章详情弹窗 */}
      <Dialog open={isViewDialogOpen} onOpenChange={handleCloseViewDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>
              {selectedArticle ? selectedArticle.title : '加载中...'}
            </DialogTitle>
          </DialogHeader>
          
          {isSelectedArticleLoading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-muted-foreground">加载中...</p>
            </div>
          ) : selectedArticle ? (
            <div className="space-y-4 overflow-y-auto max-h-[70vh]">
              {/* 基本信息 */}
              <div className="flex flex-wrap gap-2 pb-4 border-b">
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{selectedArticle.source_domain}</span>
                  <span>·</span>
                  <span>{selectedArticle.author || '未知作者'}</span>
                  <span>·</span>
                  <span>
                    {format(new Date(selectedArticle.crawl_time), 'yyyy-MM-dd HH:mm', {
                      locale: zhCN,
                    })}
                  </span>
                </div>
              </div>

              {/* 标签信息 */}
              <div className="flex flex-wrap gap-2">
                <span
                  className={`px-2 py-1 text-xs text-white rounded ${getLevelColor(
                    selectedArticle.level
                  )}`}
                >
                  L{selectedArticle.level}
                </span>
                {selectedArticle.category && (
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                    {selectedArticle.category}
                  </span>
                )}
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                  {getSentimentText(selectedArticle.sentiment)}
                </span>
              </div>

              {/* 文章内容 */}
              <div className="prose prose-sm max-w-none">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">文章内容</h4>
                <div className="whitespace-pre-wrap text-sm leading-relaxed bg-gray-50 p-4 rounded-md">
                  {selectedArticle.content}
                </div>
              </div>

              {/* 摘要 */}
              {selectedArticle.summary && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">文章摘要</h4>
                  <p className="text-sm bg-blue-50 p-3 rounded-md">
                    {selectedArticle.summary}
                  </p>
                </div>
              )}

              {/* 关键词 */}
              {selectedArticle.keywords && selectedArticle.keywords.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">关键词</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedArticle.keywords.map((keyword, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 标签 */}
              {selectedArticle.tags && selectedArticle.tags.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">标签</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedArticle.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 操作按钮 */}
              <div className="flex justify-between items-center pt-4 border-t">
                <a
                  href={selectedArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-blue-600 hover:underline"
                >
                  <ExternalLink className="h-4 w-4" />
                  查看原文
                </a>
                <Button onClick={handleCloseViewDialog}>
                  关闭
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <p className="text-muted-foreground">文章未找到</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
