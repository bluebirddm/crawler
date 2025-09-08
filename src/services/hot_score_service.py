"""文章热度计算服务"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from loguru import logger
import math

from ..models import Article, SessionLocal
from ..utils import cache, invalidate_article_cache


class HotScoreService:
    """文章热度分数计算服务"""
    
    # 权重配置
    VIEW_WEIGHT = 1.0
    LIKE_WEIGHT = 3.0
    SHARE_WEIGHT = 5.0
    
    # 时间衰减配置（小时）
    HALF_LIFE_HOURS = 72  # 72小时半衰期
    
    # 质量权重
    LEVEL_WEIGHTS = {
        1: 0.6,   # 低质量
        2: 0.8,   # 普通
        3: 1.0,   # 中等
        4: 1.3,   # 高质量
        5: 1.6    # 精品
    }
    
    @classmethod
    def calculate_hot_score(
        cls,
        article: Article,
        current_time: Optional[datetime] = None
    ) -> float:
        """
        计算文章的热度分数
        
        公式：
        hot_score = interaction_score * time_decay * quality_factor
        
        其中：
        - interaction_score = view * 1 + like * 3 + share * 5
        - time_decay = 0.5 ^ (hours_passed / half_life)
        - quality_factor = level_weight * sentiment_boost
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 1. 计算交互分数
        interaction_score = (
            article.view_count * cls.VIEW_WEIGHT +
            article.like_count * cls.LIKE_WEIGHT +
            article.share_count * cls.SHARE_WEIGHT
        )
        
        # 基础分数，确保新文章也有一定热度
        base_score = 10.0
        interaction_score = max(interaction_score, base_score)
        
        # 2. 计算时间衰减因子
        time_diff = current_time - article.crawl_time
        hours_passed = time_diff.total_seconds() / 3600
        time_decay = math.pow(0.5, hours_passed / cls.HALF_LIFE_HOURS)
        
        # 新文章加成（24小时内）
        if hours_passed < 24:
            time_decay *= 1.2
        
        # 3. 计算质量因子
        level_weight = cls.LEVEL_WEIGHTS.get(article.level or 1, 0.8)
        
        # 情感分析加成
        sentiment_boost = 1.0
        if article.sentiment:
            if article.sentiment > 0.5:
                sentiment_boost = 1.2  # 正面情感加成
            elif article.sentiment < -0.5:
                sentiment_boost = 0.9  # 负面情感轻微减分
        
        quality_factor = level_weight * sentiment_boost
        
        # 4. 计算最终热度分数
        hot_score = interaction_score * time_decay * quality_factor
        
        # 分类加成（某些分类可能更受欢迎）
        category_boosts = {
            '技术': 1.1,
            '热点': 1.2,
            '深度': 1.15
        }
        if article.category in category_boosts:
            hot_score *= category_boosts[article.category]
        
        return round(hot_score, 2)
    
    @classmethod
    def update_article_hot_score(
        cls,
        article_id: int,
        db: Session
    ) -> Optional[float]:
        """更新单篇文章的热度分数"""
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                logger.warning(f"Article {article_id} not found")
                return None
            
            current_time = datetime.now()
            hot_score = cls.calculate_hot_score(article, current_time)
            
            article.hot_score = hot_score
            article.hot_score_updated_at = current_time
            db.commit()
            
            logger.info(f"Updated hot score for article {article_id}: {hot_score}")
            return hot_score
            
        except Exception as e:
            logger.error(f"Failed to update hot score for article {article_id}: {e}")
            db.rollback()
            return None
    
    @classmethod
    def batch_update_hot_scores(
        cls,
        db: Session,
        days_back: int = 7
    ) -> int:
        """批量更新文章热度分数"""
        try:
            current_time = datetime.now()
            cutoff_date = current_time - timedelta(days=days_back)
            
            # 获取需要更新的文章
            articles = db.query(Article).filter(
                Article.crawl_time >= cutoff_date
            ).all()
            
            updated_count = 0
            for article in articles:
                hot_score = cls.calculate_hot_score(article, current_time)
                article.hot_score = hot_score
                article.hot_score_updated_at = current_time
                updated_count += 1
            
            db.commit()
            logger.info(f"Updated hot scores for {updated_count} articles")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to batch update hot scores: {e}")
            db.rollback()
            return 0
    
    @classmethod
    def get_hot_articles(
        cls,
        db: Session,
        limit: int = 10,
        category: Optional[str] = None,
        time_range: Optional[str] = None
    ) -> List[Article]:
        """获取热门文章列表（带缓存）"""
        # 构建缓存键
        cache_key = f"hot_articles:limit:{limit}:category:{category or 'all'}:range:{time_range or 'all'}"
        
        # 尝试从缓存获取
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for hot articles: {cache_key}")
            # 重建Article对象
            articles = []
            for data in cached_data:
                article = Article()
                for key, value in data.items():
                    if hasattr(article, key):
                        setattr(article, key, value)
                articles.append(article)
            return articles
        
        try:
            query = db.query(Article)
            
            # 时间范围筛选
            if time_range:
                current_time = datetime.now()
                time_filters = {
                    '1d': current_time - timedelta(days=1),
                    '7d': current_time - timedelta(days=7),
                    '30d': current_time - timedelta(days=30)
                }
                if time_range in time_filters:
                    query = query.filter(Article.crawl_time >= time_filters[time_range])
            
            # 分类筛选
            if category:
                query = query.filter(Article.category == category)
            
            # 按热度排序
            articles = query.order_by(desc(Article.hot_score)).limit(limit).all()
            
            # 存入缓存
            if articles:
                cache_data = [article.to_dict() for article in articles]
                cache.set(cache_key, cache_data, 900)  # 15分钟缓存
                logger.debug(f"Cache set for hot articles: {cache_key}")
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get hot articles: {e}")
            return []
    
    @classmethod
    def get_trending_articles(
        cls,
        db: Session,
        limit: int = 10,
        hours: int = 24
    ) -> List[Article]:
        """获取趋势上升的文章（基于交互增长率）"""
        try:
            current_time = datetime.now()
            time_threshold = current_time - timedelta(hours=hours)
            
            # 获取近期有交互的文章
            articles = db.query(Article).filter(
                and_(
                    Article.update_time >= time_threshold,
                    Article.view_count > 0
                )
            ).all()
            
            # 计算增长率并排序
            trending_articles = []
            for article in articles:
                # 简单的增长率计算
                growth_rate = (
                    article.view_count + 
                    article.like_count * 3 + 
                    article.share_count * 5
                ) / max(1, (current_time - article.crawl_time).total_seconds() / 3600)
                
                trending_articles.append((article, growth_rate))
            
            # 按增长率排序
            trending_articles.sort(key=lambda x: x[1], reverse=True)
            
            return [article for article, _ in trending_articles[:limit]]
            
        except Exception as e:
            logger.error(f"Failed to get trending articles: {e}")
            return []
    
    @classmethod
    def increment_view_count(
        cls,
        article_id: int,
        db: Session
    ) -> bool:
        """增加文章浏览次数"""
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                return False
            
            article.view_count += 1
            # 实时更新热度分数
            article.hot_score = cls.calculate_hot_score(article)
            article.hot_score_updated_at = datetime.now()
            
            db.commit()
            # 清除缓存
            invalidate_article_cache(article_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to increment view count: {e}")
            db.rollback()
            return False
    
    @classmethod
    def toggle_like(
        cls,
        article_id: int,
        is_like: bool,
        db: Session
    ) -> bool:
        """切换点赞状态"""
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                return False
            
            if is_like:
                article.like_count += 1
            else:
                article.like_count = max(0, article.like_count - 1)
            
            # 实时更新热度分数
            article.hot_score = cls.calculate_hot_score(article)
            article.hot_score_updated_at = datetime.now()
            
            db.commit()
            # 清除缓存
            invalidate_article_cache(article_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to toggle like: {e}")
            db.rollback()
            return False
    
    @classmethod
    def increment_share_count(
        cls,
        article_id: int,
        db: Session
    ) -> bool:
        """增加分享次数"""
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                return False
            
            article.share_count += 1
            # 实时更新热度分数
            article.hot_score = cls.calculate_hot_score(article)
            article.hot_score_updated_at = datetime.now()
            
            db.commit()
            # 清除缓存
            invalidate_article_cache(article_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to increment share count: {e}")
            db.rollback()
            return False