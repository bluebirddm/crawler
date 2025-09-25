from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from loguru import logger
import requests
from urllib.parse import urlparse

from ...models import get_db, CrawlerSource
from ...tasks import crawl_url
from ..utils.datetime import parse_datetime_param, apply_datetime_filters

router = APIRouter()


class CreateSourceRequest(BaseModel):
    name: str
    url: HttpUrl
    interval: int = 60
    selector: str = "article"
    category: str
    enabled: bool = True


class UpdateSourceRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    interval: Optional[int] = None
    selector: Optional[str] = None
    category: Optional[str] = None
    enabled: Optional[bool] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    url: str
    enabled: bool
    interval: int
    selector: str
    category: str
    lastCrawled: Optional[datetime] = None
    articleCount: int
    createdAt: datetime
    updatedAt: datetime


@router.get("", response_model=List[SourceResponse])
async def get_sources(
    category: Optional[str] = Query(None, description="Filter by category"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    start_date: Optional[str] = Query(None, description="Filter by creation start time"),
    end_date: Optional[str] = Query(None, description="Filter by creation end time"),
    db: Session = Depends(get_db)
):
    """获取所有爬取源"""
    try:
        query = db.query(CrawlerSource)
        
        if category:
            query = query.filter(CrawlerSource.category == category)
        if enabled is not None:
            query = query.filter(CrawlerSource.enabled == enabled)

        try:
            parsed_start = parse_datetime_param(start_date, "start_date")
            parsed_end = parse_datetime_param(end_date, "end_date")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

        query = apply_datetime_filters(query, CrawlerSource.created_at, parsed_start, parsed_end)
        
        sources = query.order_by(desc(CrawlerSource.created_at)).all()
        
        return [
            SourceResponse(
                id=source.id,
                name=source.name,
                url=source.url,
                enabled=source.enabled,
                interval=source.interval,
                selector=source.selector,
                category=source.category,
                lastCrawled=source.last_crawled,
                articleCount=source.article_count,
                createdAt=source.created_at,
                updatedAt=source.updated_at
            )
            for source in sources
        ]
    
    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: int, db: Session = Depends(get_db)):
    """获取单个爬取源详情"""
    source = db.query(CrawlerSource).filter(CrawlerSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        enabled=source.enabled,
        interval=source.interval,
        selector=source.selector,
        category=source.category,
        lastCrawled=source.last_crawled,
        articleCount=source.article_count,
        createdAt=source.created_at,
        updatedAt=source.updated_at
    )


@router.post("", response_model=SourceResponse)
async def create_source(request: CreateSourceRequest, db: Session = Depends(get_db)):
    """创建新的爬取源"""
    try:
        # 检查名称是否已存在
        existing = db.query(CrawlerSource).filter(CrawlerSource.name == request.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Source with this name already exists")
        
        source = CrawlerSource(
            name=request.name,
            url=str(request.url),
            interval=request.interval,
            selector=request.selector,
            category=request.category,
            enabled=request.enabled
        )
        
        db.add(source)
        db.commit()
        db.refresh(source)
        
        logger.info(f"Created new source: {source.name}")
        
        return SourceResponse(
            id=source.id,
            name=source.name,
            url=source.url,
            enabled=source.enabled,
            interval=source.interval,
            selector=source.selector,
            category=source.category,
            lastCrawled=source.last_crawled,
            articleCount=source.article_count,
            createdAt=source.created_at,
            updatedAt=source.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create source: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int, 
    request: UpdateSourceRequest, 
    db: Session = Depends(get_db)
):
    """更新爬取源"""
    try:
        source = db.query(CrawlerSource).filter(CrawlerSource.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # 更新字段
        if request.name is not None:
            # 检查新名称是否已被其他源使用
            existing = db.query(CrawlerSource).filter(
                CrawlerSource.name == request.name,
                CrawlerSource.id != source_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Source with this name already exists")
            source.name = request.name
        
        if request.url is not None:
            source.url = str(request.url)
        if request.interval is not None:
            source.interval = request.interval
        if request.selector is not None:
            source.selector = request.selector
        if request.category is not None:
            source.category = request.category
        if request.enabled is not None:
            source.enabled = request.enabled
        
        db.commit()
        db.refresh(source)
        
        logger.info(f"Updated source: {source.name}")
        
        return SourceResponse(
            id=source.id,
            name=source.name,
            url=source.url,
            enabled=source.enabled,
            interval=source.interval,
            selector=source.selector,
            category=source.category,
            lastCrawled=source.last_crawled,
            articleCount=source.article_count,
            createdAt=source.created_at,
            updatedAt=source.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update source: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """删除爬取源"""
    try:
        source = db.query(CrawlerSource).filter(CrawlerSource.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        source_name = source.name
        db.delete(source)
        db.commit()
        
        logger.info(f"Deleted source: {source_name}")
        
        return {"message": f"Source '{source_name}' deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete source: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_id}/test")
async def test_source(source_id: int, db: Session = Depends(get_db)):
    """测试爬取源连通性"""
    try:
        source = db.query(CrawlerSource).filter(CrawlerSource.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # 测试URL连通性
        try:
            response = requests.head(source.url, timeout=10, allow_redirects=True)
            status_code = response.status_code
            
            if status_code < 400:
                return {
                    "success": True,
                    "message": f"连接成功 (状态码: {status_code})",
                    "data": {
                        "url": source.url,
                        "status_code": status_code,
                        "final_url": response.url if response.url != source.url else None
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"连接失败 (状态码: {status_code})",
                    "data": {
                        "url": source.url,
                        "status_code": status_code
                    }
                }
        
        except requests.RequestException as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
                "data": {
                    "url": source.url,
                    "error": str(e)
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_id}/crawl")
async def trigger_crawl(source_id: int, db: Session = Depends(get_db)):
    """触发单个源的爬取任务"""
    try:
        source = db.query(CrawlerSource).filter(CrawlerSource.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # 触发爬取任务
        task = crawl_url.delay(source.url, spider_name="general")
        
        # 更新最后爬取时间
        source.last_crawled = datetime.now()
        db.commit()
        
        logger.info(f"Triggered crawl for source: {source.name}")
        
        return {
            "taskId": task.id,
            "message": f"爬取任务已启动",
            "source": source.name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger crawl: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_sources_stats(db: Session = Depends(get_db)):
    """获取爬取源统计信息"""
    try:
        total_sources = db.query(func.count(CrawlerSource.id)).scalar()
        enabled_sources = db.query(func.count(CrawlerSource.id)).filter(
            CrawlerSource.enabled == True
        ).scalar()
        total_articles = db.query(func.sum(CrawlerSource.article_count)).scalar() or 0
        
        # 按分类统计
        category_stats = db.query(
            CrawlerSource.category,
            func.count(CrawlerSource.id).label('count'),
            func.sum(CrawlerSource.article_count).label('articles')
        ).group_by(CrawlerSource.category).all()
        
        return {
            "totalSources": total_sources,
            "enabledSources": enabled_sources,
            "totalArticles": int(total_articles),
            "categoryStats": [
                {
                    "category": stat.category,
                    "sourceCount": stat.count,
                    "articleCount": int(stat.articles or 0)
                }
                for stat in category_stats
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get sources stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
