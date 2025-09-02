from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from loguru import logger

from ...models import get_db, Article

router = APIRouter()


class SystemInfo(BaseModel):
    database_status: str
    celery_status: str
    total_articles: int
    last_crawl_time: Optional[datetime]
    system_time: datetime


@router.get("/system/info", response_model=SystemInfo)
async def get_system_info(db: Session = Depends(get_db)):
    try:
        total_articles = db.query(Article).count()
        
        last_article = db.query(Article).order_by(
            Article.crawl_time.desc()
        ).first()
        
        last_crawl_time = last_article.crawl_time if last_article else None
        
        from ...tasks import app
        inspect = app.control.inspect()
        stats = inspect.stats()
        celery_status = "running" if stats else "not running"
        
        return SystemInfo(
            database_status="connected",
            celery_status=celery_status,
            total_articles=total_articles,
            last_crawl_time=last_crawl_time,
            system_time=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/cleanup")
async def cleanup_database(
    days: int = 90,
    db: Session = Depends(get_db)
):
    try:
        from datetime import timedelta
        from sqlalchemy import and_
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted_count = db.query(Article).filter(
            and_(
                Article.crawl_time < cutoff_date,
                Article.level < 3
            )
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Cleaned up {deleted_count} articles older than {days} days",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Database cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/reset")
async def reset_database(
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Please confirm database reset by setting confirm=true"
        )
    
    try:
        deleted_count = db.query(Article).delete()
        db.commit()
        
        return {
            "message": "Database reset successfully",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Database reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/status")
async def get_workers_status():
    try:
        from ...tasks import app
        
        inspect = app.control.inspect()
        
        stats = inspect.stats()
        active = inspect.active()
        reserved = inspect.reserved()
        
        workers = []
        if stats:
            for worker_name, worker_stats in stats.items():
                worker_info = {
                    "name": worker_name,
                    "status": "online",
                    "pool": worker_stats.get("pool", {}).get("implementation", "unknown"),
                    "active_tasks": len(active.get(worker_name, [])) if active else 0,
                    "reserved_tasks": len(reserved.get(worker_name, [])) if reserved else 0,
                    "total_tasks": worker_stats.get("total", {})
                }
                workers.append(worker_info)
        
        return {"workers": workers}
    
    except Exception as e:
        logger.error(f"Failed to get workers status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/restart")
async def restart_workers():
    try:
        from ...tasks import app
        
        app.control.broadcast('pool_restart', arguments={'reload': True})
        
        return {"message": "Workers restart command sent"}
    
    except Exception as e:
        logger.error(f"Failed to restart workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        "database": {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "name": os.getenv("DB_NAME")
        },
        "redis": {
            "host": os.getenv("REDIS_HOST"),
            "port": os.getenv("REDIS_PORT")
        },
        "crawler": {
            "user_agent": os.getenv("USER_AGENT"),
            "download_delay": os.getenv("DOWNLOAD_DELAY"),
            "concurrent_requests": os.getenv("CONCURRENT_REQUESTS")
        }
    }
    
    return config