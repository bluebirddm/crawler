from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from ...models import get_db, Article

router = APIRouter()


class ArticleResponse(BaseModel):
    id: int
    url: str
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
    
    class Config:
        orm_mode = True


class ArticleFilter(BaseModel):
    category: Optional[str] = None
    level: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_domain: Optional[str] = None
    keyword: Optional[str] = None


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
            query = query.filter(Article.level >= level)
        
        if days:
            start_date = datetime.now() - timedelta(days=days)
            query = query.filter(Article.crawl_time >= start_date)
        
        query = query.order_by(Article.crawl_time.desc())
        articles = query.offset(skip).limit(limit).all()
        
        return articles
    
    except Exception as e:
        logger.error(f"Failed to get articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


@router.get("/search/", response_model=List[ArticleResponse])
async def search_articles(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Article).filter(
            (Article.title.contains(q)) | 
            (Article.content.contains(q))
        )
        
        articles = query.order_by(Article.crawl_time.desc()).offset(skip).limit(limit).all()
        
        return articles
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/categories")
async def get_category_stats(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import func
        
        stats = db.query(
            Article.category,
            func.count(Article.id).label('count')
        ).group_by(Article.category).all()
        
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
    db: Session = Depends(get_db)
):
    try:
        from sqlalchemy import func
        
        start_date = datetime.now() - timedelta(days=days)
        
        stats = db.query(
            func.date(Article.crawl_time).label('date'),
            func.count(Article.id).label('count')
        ).filter(
            Article.crawl_time >= start_date
        ).group_by(
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