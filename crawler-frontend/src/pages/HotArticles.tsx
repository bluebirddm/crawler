import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { articlesApi } from '@/api/articles';
import type { Article } from '../types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Flame,
  TrendingUp,
  Eye,
  Heart,
  Share2,
  User,
  Calendar,
  RefreshCw,
  ExternalLink,
  Award,
  Zap,
} from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export function HotArticles() {
  const queryClient = useQueryClient();
  const [timeRange, setTimeRange] = useState<'1d' | '7d' | '30d' | 'all'>('7d');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [likedArticles, setLikedArticles] = useState<Set<number>>(new Set());

  // 从 localStorage 加载点赞状态
  useEffect(() => {
    const saved = localStorage.getItem('likedArticles');
    if (saved) {
      setLikedArticles(new Set(JSON.parse(saved)));
    }
  }, []);

  // 保存点赞状态到 localStorage
  const saveLikedArticles = (articles: Set<number>) => {
    localStorage.setItem('likedArticles', JSON.stringify(Array.from(articles)));
  };

  // 获取热门文章
  const { data: hotArticles, isLoading: isHotLoading } = useQuery({
    queryKey: ['hotArticles', timeRange, selectedCategory],
    queryFn: () => articlesApi.getHotArticles({
      limit: 20,
      time_range: timeRange,
      category: selectedCategory === 'all' ? undefined : selectedCategory,
    }),
    refetchInterval: 60000, // 每分钟刷新
  });

  // 获取趋势文章
  const { data: trendingArticles, isLoading: isTrendingLoading } = useQuery({
    queryKey: ['trendingArticles'],
    queryFn: () => articlesApi.getTrendingArticles({
      limit: 10,
      hours: 24,
    }),
    refetchInterval: 120000, // 每2分钟刷新
  });

  // 获取分类统计
  const { data: categories } = useQuery({
    queryKey: ['categoryStats'],
    queryFn: articlesApi.getCategoryStats,
  });

  // 浏览量增加
  const viewMutation = useMutation({
    mutationFn: articlesApi.incrementView,
  });

  // 点赞/取消点赞
  const likeMutation = useMutation({
    mutationFn: ({ id, isLike }: { id: number; isLike: boolean }) =>
      articlesApi.toggleLike(id, isLike),
    onSuccess: (_, variables) => {
      const newLiked = new Set(likedArticles);
      if (variables.isLike) {
        newLiked.add(variables.id);
      } else {
        newLiked.delete(variables.id);
      }
      setLikedArticles(newLiked);
      saveLikedArticles(newLiked);
      queryClient.invalidateQueries({ queryKey: ['hotArticles'] });
    },
  });

  // 分享
  const shareMutation = useMutation({
    mutationFn: articlesApi.recordShare,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hotArticles'] });
    },
  });

  // 更新热度分数
  const updateScoresMutation = useMutation({
    mutationFn: articlesApi.updateHotScores,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hotArticles'] });
      queryClient.invalidateQueries({ queryKey: ['trendingArticles'] });
    },
  });

  const handleArticleClick = (article: Article) => {
    // 增加浏览量
    viewMutation.mutate(article.id);
    // 在新标签页打开
    window.open(article.url, '_blank');
  };

  const handleLike = (article: Article, e: React.MouseEvent) => {
    e.stopPropagation();
    const isLiked = likedArticles.has(article.id);
    likeMutation.mutate({ id: article.id, isLike: !isLiked });
  };

  const handleShare = (article: Article, e: React.MouseEvent) => {
    e.stopPropagation();
    shareMutation.mutate(article.id);
    // 复制链接到剪贴板
    navigator.clipboard.writeText(article.url);
  };

  const getHotIcon = (score: number) => {
    if (score > 100) return <Flame className="h-5 w-5 text-red-500" />;
    if (score > 50) return <Flame className="h-5 w-5 text-orange-500" />;
    if (score > 20) return <Flame className="h-5 w-5 text-yellow-500" />;
    return <Flame className="h-5 w-5 text-gray-400" />;
  };

  const getLevelBadge = (level: number) => {
    const levels = [
      { color: 'bg-gray-500', text: '普通' },
      { color: 'bg-green-500', text: '良好' },
      { color: 'bg-blue-500', text: '优质' },
      { color: 'bg-purple-500', text: '精品' },
      { color: 'bg-red-500', text: '必读' },
    ];
    const levelInfo = levels[level - 1] || levels[0];
    return (
      <Badge className={`${levelInfo.color} text-white`}>
        {levelInfo.text}
      </Badge>
    );
  };

  const formatTimeAgo = (date: string) => {
    const now = new Date();
    const articleDate = new Date(date);
    const diffInHours = (now.getTime() - articleDate.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) return '刚刚';
    if (diffInHours < 24) return `${Math.floor(diffInHours)}小时前`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}天前`;
    return format(articleDate, 'MM月dd日', { locale: zhCN });
  };

  const ArticleCard = ({ article, rank }: { article: Article; rank?: number }) => {
    const isLiked = likedArticles.has(article.id);
    
    return (
      <Card 
        className="hover:shadow-lg transition-shadow cursor-pointer"
        onClick={() => handleArticleClick(article)}
      >
        <CardHeader>
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                {rank && rank <= 3 && (
                  <Award className={`h-5 w-5 ${
                    rank === 1 ? 'text-yellow-500' : 
                    rank === 2 ? 'text-gray-400' : 
                    'text-orange-600'
                  }`} />
                )}
                {rank && <span className="text-lg font-bold text-muted-foreground">#{rank}</span>}
                {getHotIcon(article.hot_score || 0)}
                <span className="text-sm font-medium">热度 {article.hot_score?.toFixed(1)}</span>
                {getLevelBadge(article.level || 1)}
              </div>
              <CardTitle className="text-lg line-clamp-2">{article.title}</CardTitle>
            </div>
          </div>
          <CardDescription className="flex items-center gap-4 mt-2">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatTimeAgo(article.crawl_time)}
            </span>
            {article.author && (
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {article.author}
              </span>
            )}
            {article.category && (
              <Badge variant="outline">{article.category}</Badge>
            )}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-3">
            {article.summary || article.content}
          </p>
          
          {article.keywords && article.keywords.length > 0 && (
            <div className="flex gap-2 mt-3 flex-wrap">
              {article.keywords.slice(0, 5).map((keyword, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
        
        <CardFooter>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => handleLike(article, e)}
                className={isLiked ? 'text-red-500' : ''}
              >
                <Heart className={`h-4 w-4 mr-1 ${isLiked ? 'fill-current' : ''}`} />
                {article.like_count || 0}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => handleShare(article, e)}
              >
                <Share2 className="h-4 w-4 mr-1" />
                {article.share_count || 0}
              </Button>
              
              <span className="flex items-center text-sm text-muted-foreground">
                <Eye className="h-4 w-4 mr-1" />
                {article.view_count || 0}
              </span>
            </div>
            
            <Button variant="ghost" size="sm">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </CardFooter>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Flame className="h-8 w-8 text-orange-500" />
            热门文章
          </h2>
          <p className="text-muted-foreground">发现最受欢迎的内容</p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => updateScoresMutation.mutate(7)}
            disabled={updateScoresMutation.isPending}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${updateScoresMutation.isPending ? 'animate-spin' : ''}`} />
            更新热度
          </Button>
        </div>
      </div>

      {/* 主要内容 */}
      <Tabs defaultValue="hot" className="space-y-4">
        <TabsList>
          <TabsTrigger value="hot" className="flex items-center gap-2">
            <Flame className="h-4 w-4" />
            热门榜单
          </TabsTrigger>
          <TabsTrigger value="trending" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            上升最快
          </TabsTrigger>
        </TabsList>

        {/* 热门榜单 */}
        <TabsContent value="hot" className="space-y-4">
          {/* 筛选器 */}
          <div className="flex gap-4">
            <Select value={timeRange} onValueChange={(value: any) => setTimeRange(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="选择时间范围" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1d">今日热门</SelectItem>
                <SelectItem value="7d">本周热门</SelectItem>
                <SelectItem value="30d">本月热门</SelectItem>
                <SelectItem value="all">全部时间</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="所有分类" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有分类</SelectItem>
                {categories?.map((cat) => (
                  <SelectItem key={cat.category} value={cat.category}>
                    {cat.category} ({cat.count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 文章列表 */}
          {isHotLoading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {hotArticles?.map((article, index) => (
                <ArticleCard key={article.id} article={article} rank={index + 1} />
              ))}
            </div>
          )}
          
          {hotArticles?.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <Flame className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-muted-foreground">暂无热门文章</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 上升最快 */}
        <TabsContent value="trending" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                24小时内上升最快
              </CardTitle>
              <CardDescription>基于互动增长率计算</CardDescription>
            </CardHeader>
          </Card>
          
          {isTrendingLoading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <div className="grid gap-4">
              {trendingArticles?.map((article, index) => (
                <ArticleCard key={article.id} article={article} rank={index + 1} />
              ))}
            </div>
          )}
          
          {trendingArticles?.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-muted-foreground">暂无上升趋势文章</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}