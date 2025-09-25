from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, field_validator
from loguru import logger

from ...models import get_db, Article
from ...services import HotScoreService
from ..utils.datetime import parse_datetime_param, apply_datetime_filters

router = APIRouter()


class ArticleResponse(BaseModel):
    id: int
    url: Optional[str]
    title: str
    content: str
    author: Optional[str]
    publish_date: Optional[datetime]
    source: Optional[str]
    source_domain: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    level: int
    sentiment: Optional[float]
    keywords: Optional[List[str]]
    summary: Optional[str]
    crawl_time: datetime
    update_time: datetime
    
    view_count: int
    like_count: int
    share_count: int
    hot_score: float
    hot_score_updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ArticleCreate(BaseModel):
    """创建文章的请求模型"""
    url: Optional[str] = None
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    source: Optional[str] = None
    source_domain: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    level: int = 0
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None

    @field_validator("url", mode="before")
    @classmethod
    def normalize_url(cls, value: Optional[str]) -> Optional[str]:
        """Return None for blank URLs so the DB unique index allows multiple missing values."""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            return stripped
        return value


class ArticleUpdate(BaseModel):
    """更新文章的请求模型"""
    url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    source: Optional[str] = None
    source_domain: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    level: Optional[int] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None

    @field_validator("url", mode="before")
    @classmethod
    def normalize_url(cls, value: Optional[str]) -> Optional[str]:
        """Treat blank strings as missing when updating URLs."""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            return stripped
        return value


class ArticleFilter(BaseModel):
    category: Optional[str] = None
    level: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_domain: Optional[str] = None
    keyword: Optional[str] = None


class ArticleBatchDeleteRequest(BaseModel):
    """批量删除文章的请求模型"""
    article_ids: List[int]


@router.get("/", response_model=List[ArticleResponse])
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    level: Optional[int] = None,
    days: Optional[int] = Query(None, description="获取最近N天的文章"),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Article)
        
        if category:
            query = query.filter(Article.category == category)
        
        if level is not None:
            query = query.filter(Article.level == level)
        
        if days:
            start_date = datetime.now() - timedelta(days=days)
            query = query.filter(Article.crawl_time >= start_date)
        
        query = query.order_by(Article.crawl_time.desc())
        articles = query.offset(skip).limit(limit).all()
        
        return articles
    
    except Exception as e:
        logger.error(f"Failed to get articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[ArticleResponse])
async def search_articles(
    q: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="文章分类"),
    level: Optional[int] = Query(None, description="文章级别"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="筛选开始时间，支持 epoch 秒/毫秒或 ISO 字符串"),
    end_date: Optional[str] = Query(None, description="筛选结束时间，支持 epoch 秒/毫秒或 ISO 字符串"),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Article)

        # 文本搜索条件
        if q:
            query = query.filter(
                (Article.title.contains(q)) | 
                (Article.content.contains(q))
            )
        
        # 分类筛选条件
        if category:
            query = query.filter(Article.category == category)
        
        # 级别筛选条件
        if level is not None:
            query = query.filter(Article.level == level)

        try:
            parsed_start = parse_datetime_param(start_date, "start_date")
            parsed_end = parse_datetime_param(end_date, "end_date")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

        query = apply_datetime_filters(query, Article.crawl_time, parsed_start, parsed_end)

        articles = query.order_by(Article.crawl_time.desc()).offset(skip).limit(limit).all()

        return articles

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


@router.get("/stats/categories")
async def get_category_stats(
    start_date: Optional[str] = Query(None, description="筛选开始时间"),
    end_date: Optional[str] = Query(None, description="筛选结束时间"),
    db: Session = Depends(get_db)
):
    try:
        from sqlalchemy import func

        try:
            parsed_start = parse_datetime_param(start_date, "start_date")
            parsed_end = parse_datetime_param(end_date, "end_date")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

        query = db.query(
            Article.category,
            func.count(Article.id).label('count')
        )
        query = apply_datetime_filters(query, Article.crawl_time, parsed_start, parsed_end)
        stats = query.group_by(Article.category).all()

        return {
            "categories": [
                {"category": stat[0], "count": stat[1]} 
                for stat in stats
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get category stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/daily")
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30),
    start_date: Optional[str] = Query(None, description="筛选开始时间"),
    end_date: Optional[str] = Query(None, description="筛选结束时间"),
    db: Session = Depends(get_db)
):
    try:
        from sqlalchemy import func
        
        now = datetime.now()
        try:
            parsed_start = parse_datetime_param(start_date, "start_date")
            parsed_end = parse_datetime_param(end_date, "end_date")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        range_end = parsed_end or now
        range_start = parsed_start or (range_end - timedelta(days=days))

        if range_start > range_end:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

        stats_query = db.query(
            func.date(Article.crawl_time).label('date'),
            func.count(Article.id).label('count')
        )
        stats_query = apply_datetime_filters(stats_query, Article.crawl_time, range_start, range_end)
        stats = stats_query.group_by(
            func.date(Article.crawl_time)
        ).order_by('date').all()
        
        return {
            "daily_stats": [
                {"date": stat[0].isoformat(), "count": stat[1]} 
                for stat in stats
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get daily stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{article_id}")
async def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        db.delete(article)
        db.commit()
        return {"message": "Article deleted successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/batch/delete")
async def delete_articles_batch(
    request: ArticleBatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量删除文章"""
    if not request.article_ids:
        raise HTTPException(status_code=400, detail="No article IDs provided")
    
    # 记录删除结果
    deleted_ids = []
    failed_ids = []
    
    try:
        # 查找所有要删除的文章
        articles_to_delete = db.query(Article).filter(
            Article.id.in_(request.article_ids)
        ).all()
        
        # 获取实际存在的文章ID
        existing_ids = {article.id for article in articles_to_delete}
        
        # 找出不存在的文章ID
        not_found_ids = [aid for aid in request.article_ids if aid not in existing_ids]
        failed_ids.extend(not_found_ids)
        
        # 批量删除存在的文章
        if articles_to_delete:
            for article in articles_to_delete:
                try:
                    db.delete(article)
                    deleted_ids.append(article.id)
                except Exception as e:
                    logger.error(f"Failed to delete article {article.id}: {e}")
                    failed_ids.append(article.id)
            
            # 提交事务
            db.commit()
            logger.info(f"Batch deleted {len(deleted_ids)} articles")
        
        return {
            "message": f"Batch delete completed",
            "deleted_count": len(deleted_ids),
            "deleted_ids": deleted_ids,
            "failed_ids": failed_ids,
            "total_requested": len(request.article_ids)
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to batch delete articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot/", response_model=List[ArticleResponse])
async def get_hot_articles(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    category: Optional[str] = Query(None, description="文章分类"),
    time_range: Optional[str] = Query(None, pattern="^(1d|7d|30d|all)$", description="时间范围"),
    start_date: Optional[str] = Query(None, description="筛选开始时间"),
    end_date: Optional[str] = Query(None, description="筛选结束时间"),
    db: Session = Depends(get_db)
):
    """获取热门文章列表"""
    try:
        try:
            parsed_start = parse_datetime_param(start_date, "start_date")
            parsed_end = parse_datetime_param(end_date, "end_date")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

        articles = HotScoreService.get_hot_articles(
            db=db,
            limit=limit,
            category=category,
            time_range=time_range,
            start_time=parsed_start,
            end_time=parsed_end
        )
        return articles
    
    except Exception as e:
        logger.error(f"Failed to get hot articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending/", response_model=List[ArticleResponse])
async def get_trending_articles(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    db: Session = Depends(get_db)
):
    """获取趋势上升的文章"""
    try:
        articles = HotScoreService.get_trending_articles(
            db=db,
            limit=limit,
            hours=hours
        )
        return articles
    
    except Exception as e:
        logger.error(f"Failed to get trending articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{article_id}/view")
async def increment_view(
    article_id: int,
    db: Session = Depends(get_db)
):
    """增加文章浏览次数"""
    try:
        success = HotScoreService.increment_view_count(article_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return {"message": "View count incremented", "article_id": article_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to increment view count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{article_id}/like")
async def toggle_like(
    article_id: int,
    is_like: bool = Query(..., description="true为点赞，false为取消点赞"),
    db: Session = Depends(get_db)
):
    """点赞或取消点赞"""
    try:
        success = HotScoreService.toggle_like(article_id, is_like, db)
        if not success:
            raise HTTPException(status_code=404, detail="Article not found")
        
        action = "liked" if is_like else "unliked"
        return {"message": f"Article {action}", "article_id": article_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle like: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{article_id}/share")
async def record_share(
    article_id: int,
    db: Session = Depends(get_db)
):
    """记录文章分享"""
    try:
        success = HotScoreService.increment_share_count(article_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return {"message": "Share recorded", "article_id": article_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record share: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-hot-scores")
async def update_hot_scores(
    days_back: int = Query(7, ge=1, le=30, description="更新最近N天的文章热度"),
    db: Session = Depends(get_db)
):
    """批量更新文章热度分数"""
    try:
        updated_count = HotScoreService.batch_update_hot_scores(db, days_back)
        return {
            "message": "Hot scores updated successfully",
            "updated_count": updated_count
        }
    
    except Exception as e:
        logger.error(f"Failed to update hot scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ArticleResponse)
async def create_article(
    article_data: ArticleCreate,
    db: Session = Depends(get_db)
):
    """创建新文章"""
    try:
        normalized_url = article_data.url
        # 检查 URL 是否已存在（仅当提供了 URL 时）
        if normalized_url is not None:
            existing_article = db.query(Article).filter(Article.url == normalized_url).first()
            if existing_article:
                raise HTTPException(status_code=400, detail="Article with this URL already exists")
        
        # 创建新文章实例
        new_article = Article(
            url=normalized_url,
            title=article_data.title,
            content=article_data.content,
            author=article_data.author,
            publish_date=article_data.publish_date,
            source=article_data.source,
            source_domain=article_data.source_domain,
            category=article_data.category,
            tags=article_data.tags,
            level=article_data.level,
            keywords=article_data.keywords,
            summary=article_data.summary,
            # 设置默认值
            view_count=0,
            like_count=0,
            share_count=0,
            hot_score=0.0
        )
        
        # 保存到数据库
        db.add(new_article)
        db.commit()
        db.refresh(new_article)
        
        logger.info(f"Created new article: {new_article.id} - {new_article.title}")
        return new_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create article: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    db: Session = Depends(get_db)
):
    """更新文章"""
    try:
        # 查找文章
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # 更新非空字段
        update_data = article_data.dict(exclude_unset=True)
        
        # 如果更新 URL，检查唯一性
        if 'url' in update_data and update_data['url'] is not None:
            existing_article = db.query(Article).filter(
                Article.url == update_data['url'],
                Article.id != article_id
            ).first()
            if existing_article:
                raise HTTPException(status_code=400, detail="Article with this URL already exists")
        
        for field, value in update_data.items():
            setattr(article, field, value)
        
        # 保存更改
        db.commit()
        db.refresh(article)
        
        logger.info(f"Updated article: {article.id} - {article.title}")
        return article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update article {article_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
