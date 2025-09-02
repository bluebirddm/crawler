from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ...tasks import crawl_url, crawl_batch, reprocess_articles

router = APIRouter()


class CrawlRequest(BaseModel):
    url: HttpUrl
    spider_name: Optional[str] = "general"


class BatchCrawlRequest(BaseModel):
    urls: List[HttpUrl]
    spider_name: Optional[str] = "general"


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    timestamp: datetime


@router.post("/crawl", response_model=TaskResponse)
async def create_crawl_task(request: CrawlRequest):
    try:
        task = crawl_url.delay(str(request.url), request.spider_name)
        
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Crawl task created for {request.url}",
            timestamp=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Failed to create crawl task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl/batch", response_model=TaskResponse)
async def create_batch_crawl_task(request: BatchCrawlRequest):
    try:
        urls = [str(url) for url in request.urls]
        task = crawl_batch.delay(urls, request.spider_name)
        
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Batch crawl task created for {len(urls)} URLs",
            timestamp=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Failed to create batch crawl task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    try:
        from celery.result import AsyncResult
        from ...tasks import app
        
        result = AsyncResult(task_id, app=app)
        
        response = {
            "task_id": task_id,
            "status": result.state,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": result.result if result.ready() else None
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reprocess")
async def reprocess_articles_task(article_ids: Optional[List[int]] = None):
    try:
        task = reprocess_articles.delay(article_ids)
        
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Reprocessing task created",
            timestamp=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Failed to create reprocess task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_tasks():
    try:
        from ...tasks import app
        
        inspect = app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {"active_tasks": []}
        
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "id": task['id'],
                    "name": task['name'],
                    "worker": worker,
                    "args": task.get('args', []),
                    "kwargs": task.get('kwargs', {})
                })
        
        return {"active_tasks": all_tasks}
    
    except Exception as e:
        logger.error(f"Failed to get active tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduled")
async def get_scheduled_tasks():
    try:
        from ...tasks import app
        
        inspect = app.control.inspect()
        scheduled_tasks = inspect.scheduled()
        
        if not scheduled_tasks:
            return {"scheduled_tasks": []}
        
        all_tasks = []
        for worker, tasks in scheduled_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "id": task.get('request', {}).get('id'),
                    "name": task.get('request', {}).get('name'),
                    "worker": worker,
                    "eta": task.get('eta')
                })
        
        return {"scheduled_tasks": all_tasks}
    
    except Exception as e:
        logger.error(f"Failed to get scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    try:
        from ...tasks import app
        
        app.control.revoke(task_id, terminate=True)
        
        return {"message": f"Task {task_id} cancelled"}
    
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=str(e))