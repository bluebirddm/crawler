from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import math
from sqlalchemy import desc, asc, and_, or_
from sqlalchemy.orm import Session
from loguru import logger

from ...tasks import crawl_url, crawl_batch, reprocess_articles
from ...models import get_db, TaskHistory, TaskStatus

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
async def cancel_task(task_id: str, db: Session = Depends(get_db)):
    try:
        from ...tasks import app
        
        app.control.revoke(task_id, terminate=True)
        
        # 更新数据库中的任务状态
        task_history = db.query(TaskHistory).filter_by(task_id=task_id).first()
        if task_history:
            task_history.status = TaskStatus.REVOKED
            task_history.completed_at = datetime.now()
            db.commit()
        
        return {"message": f"Task {task_id} cancelled"}
    
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TaskHistoryResponse(BaseModel):
    total: int
    page: int
    page_size: int
    tasks: List[Dict[str, Any]]


class BatchDeleteRequest(BaseModel):
    task_ids: List[str]


def _parse_datetime_query_param(value: Optional[str], param_name: str) -> Optional[datetime]:
    """支持 ISO 字符串或 Unix 时间戳（秒/毫秒）的查询参数解析"""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

    if not value:
        return None

    # 数值类型：支持秒或毫秒级时间戳（字符串形式）
    try:
        numeric_value = float(value)
        if math.isfinite(numeric_value):
            if abs(numeric_value) > 1e12:  # 13 位以上视为毫秒
                numeric_value /= 1000.0
            try:
                return datetime.fromtimestamp(numeric_value)
            except (OverflowError, OSError, ValueError):
                raise HTTPException(status_code=400, detail=f"Invalid {param_name}: {value}")
    except ValueError:
        numeric_value = None

    # ISO 字符串: 支持日期、日期时间及带时区
    normalized_value = value.replace('Z', '+00:00') if isinstance(value, str) else value
    try:
        dt = datetime.fromisoformat(normalized_value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {param_name}: {value}")

    if dt.tzinfo:
        dt = dt.astimezone().replace(tzinfo=None)

    return dt


@router.get("/history", response_model=TaskHistoryResponse)
async def get_task_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|completed_at|status|task_type)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """获取任务历史记录"""
    try:
        query = db.query(TaskHistory)
        
        # 应用过滤条件
        if status:
            try:
                status_enum = TaskStatus(status)
                query = query.filter(TaskHistory.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if task_type:
            query = query.filter(TaskHistory.task_type == task_type)
        
        parsed_start = _parse_datetime_query_param(start_date, "start_date")
        parsed_end = _parse_datetime_query_param(end_date, "end_date")

        if parsed_start:
            query = query.filter(TaskHistory.created_at >= parsed_start)
        
        if parsed_end:
            query = query.filter(TaskHistory.created_at <= parsed_end)
        
        # 获取总数
        total = query.count()
        
        # 排序
        if order == "desc":
            query = query.order_by(desc(getattr(TaskHistory, sort_by)))
        else:
            query = query.order_by(asc(getattr(TaskHistory, sort_by)))
        
        # 分页
        offset = (page - 1) * page_size
        tasks = query.offset(offset).limit(page_size).all()
        
        return TaskHistoryResponse(
            total=total,
            page=page,
            page_size=page_size,
            tasks=[task.to_dict() for task in tasks]
        )
    
    except Exception as e:
        logger.error(f"Failed to get task history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{task_id}")
async def get_task_history_detail(task_id: str, db: Session = Depends(get_db)):
    """获取单个任务历史详情"""
    try:
        task = db.query(TaskHistory).filter_by(task_id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return task.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/batch")
async def delete_batch_task_history(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量删除任务历史记录"""
    try:
        if not request.task_ids:
            raise HTTPException(status_code=400, detail="No task IDs provided")

        if len(request.task_ids) > 100:
            raise HTTPException(status_code=400, detail="Too many task IDs (max 100)")

        # 查找所有存在的任务
        existing_tasks = db.query(TaskHistory).filter(
            TaskHistory.task_id.in_(request.task_ids)
        ).all()

        if not existing_tasks:
            raise HTTPException(status_code=404, detail="No matching tasks found")

        existing_task_ids = [task.task_id for task in existing_tasks]
        not_found_ids = [tid for tid in request.task_ids if tid not in existing_task_ids]

        # 删除存在的任务
        deleted_count = db.query(TaskHistory).filter(
            TaskHistory.task_id.in_(existing_task_ids)
        ).delete(synchronize_session=False)

        db.commit()

        response = {
            "message": f"Successfully deleted {deleted_count} task history records",
            "deleted_count": deleted_count,
            "deleted_task_ids": existing_task_ids
        }

        if not_found_ids:
            response["not_found_task_ids"] = not_found_ids
            response["message"] += f", {len(not_found_ids)} tasks not found"

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete batch task history: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{task_id}")
async def delete_task_history(task_id: str, db: Session = Depends(get_db)):
    """删除任务历史记录"""
    try:
        task = db.query(TaskHistory).filter_by(task_id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        db.delete(task)
        db.commit()
        
        return {"message": f"Task history {task_id} deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/stats/summary")
async def get_task_stats(db: Session = Depends(get_db)):
    """获取任务统计信息"""
    try:
        # 获取最近24小时的统计
        last_24h = datetime.now() - timedelta(days=1)
        
        # 总任务数
        total_tasks = db.query(TaskHistory).count()
        
        # 各状态任务数
        status_counts = {}
        for status in TaskStatus:
            count = db.query(TaskHistory).filter(
                TaskHistory.status == status
            ).count()
            status_counts[status.value] = count
        
        # 最近24小时任务数
        recent_tasks = db.query(TaskHistory).filter(
            TaskHistory.created_at >= last_24h
        ).count()
        
        # 计算成功率
        success_count = status_counts.get(TaskStatus.SUCCESS.value, 0)
        failure_count = status_counts.get(TaskStatus.FAILURE.value, 0)
        total_completed = success_count + failure_count
        success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0
        
        # 获取平均执行时间（成功的任务）
        from sqlalchemy import func
        avg_duration = db.query(
            func.avg(
                func.extract('epoch', TaskHistory.completed_at - TaskHistory.started_at)
            )
        ).filter(
            and_(
                TaskHistory.status == TaskStatus.SUCCESS,
                TaskHistory.started_at.isnot(None),
                TaskHistory.completed_at.isnot(None)
            )
        ).scalar()
        
        return {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "recent_tasks_24h": recent_tasks,
            "success_rate": round(success_rate, 2),
            "avg_duration_seconds": round(avg_duration, 2) if avg_duration else None
        }
    
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/cleanup/old")
async def cleanup_old_history(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """清理旧的任务历史记录"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        deleted_count = db.query(TaskHistory).filter(
            TaskHistory.created_at < cutoff_date
        ).delete()

        db.commit()

        return {
            "message": f"Deleted {deleted_count} task history records older than {days} days",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old history: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
