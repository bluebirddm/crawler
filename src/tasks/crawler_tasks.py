import subprocess
import json
import traceback
from datetime import datetime, timedelta
from typing import List, Dict
from celery import Task, group
from loguru import logger
from .celery_app import app
from ..models import Article, SessionLocal, TaskHistory, TaskStatus
from sqlalchemy import and_


class CallbackTask(Task):
    def __init__(self):
        super().__init__()
        self.start_time = None
    
    def before_start(self, task_id, args, kwargs):
        """任务开始前的回调"""
        self.start_time = datetime.now()
        session = SessionLocal()
        try:
            # 检查是否已存在该任务记录
            task_history = session.query(TaskHistory).filter_by(task_id=task_id).first()
            if not task_history:
                task_history = TaskHistory(
                    task_id=task_id,
                    task_name=self.name,
                    task_type=self._get_task_type(),
                    args=list(args) if args else [],
                    kwargs=kwargs if kwargs else {},
                    status=TaskStatus.RUNNING,
                    started_at=self.start_time,
                    worker_name=self.request.hostname if hasattr(self, 'request') and hasattr(self.request, 'hostname') else None,
                    queue_name=getattr(self.request, 'queue', None) if hasattr(self, 'request') else None
                )
                # 处理特定任务类型的参数
                if 'crawl_url' in self.name and args:
                    task_history.url = args[0]
                elif 'crawl_batch' in self.name and args:
                    task_history.urls = args[0]
                
                session.add(task_history)
            else:
                # 更新现有记录
                task_history.status = TaskStatus.RUNNING
                task_history.started_at = self.start_time
                task_history.retry_count = (task_history.retry_count or 0) + 1
            
            session.commit()
            logger.info(f"Task {task_id} started and recorded in history")
        except Exception as e:
            logger.error(f"Failed to record task start: {e}")
            session.rollback()
        finally:
            session.close()
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功的回调"""
        logger.info(f"Task {task_id} succeeded with result: {retval}")
        session = SessionLocal()
        try:
            task_history = session.query(TaskHistory).filter_by(task_id=task_id).first()
            if task_history:
                task_history.status = TaskStatus.SUCCESS
                task_history.completed_at = datetime.now()
                task_history.result = retval
                session.commit()
                logger.info(f"Task {task_id} success recorded in history")
            else:
                # 如果没有找到记录，创建一个新的
                task_history = TaskHistory(
                    task_id=task_id,
                    task_name=self.name,
                    task_type=self._get_task_type(),
                    args=list(args) if args else [],
                    kwargs=kwargs if kwargs else {},
                    status=TaskStatus.SUCCESS,
                    result=retval,
                    completed_at=datetime.now(),
                    worker_name=self.request.hostname if hasattr(self, 'request') and hasattr(self.request, 'hostname') else None
                )
                if 'crawl_url' in self.name and args:
                    task_history.url = args[0]
                elif 'crawl_batch' in self.name and args:
                    task_history.urls = args[0]
                session.add(task_history)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to record task success: {e}")
            session.rollback()
        finally:
            session.close()
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败的回调"""
        logger.error(f"Task {task_id} failed with exception: {exc}")
        session = SessionLocal()
        try:
            task_history = session.query(TaskHistory).filter_by(task_id=task_id).first()
            if task_history:
                task_history.status = TaskStatus.FAILURE
                task_history.completed_at = datetime.now()
                task_history.error_message = str(exc)
                task_history.traceback = str(einfo) if einfo else None
                session.commit()
                logger.info(f"Task {task_id} failure recorded in history")
            else:
                # 如果没有找到记录，创建一个新的
                task_history = TaskHistory(
                    task_id=task_id,
                    task_name=self.name,
                    task_type=self._get_task_type(),
                    args=list(args) if args else [],
                    kwargs=kwargs if kwargs else {},
                    status=TaskStatus.FAILURE,
                    error_message=str(exc),
                    traceback=str(einfo) if einfo else None,
                    completed_at=datetime.now(),
                    worker_name=self.request.hostname if hasattr(self, 'request') and hasattr(self.request, 'hostname') else None
                )
                if 'crawl_url' in self.name and args:
                    task_history.url = args[0]
                elif 'crawl_batch' in self.name and args:
                    task_history.urls = args[0]
                session.add(task_history)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to record task failure: {e}")
            session.rollback()
        finally:
            session.close()
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试的回调"""
        logger.warning(f"Task {task_id} retrying due to: {exc}")
        session = SessionLocal()
        try:
            task_history = session.query(TaskHistory).filter_by(task_id=task_id).first()
            if task_history:
                task_history.status = TaskStatus.RETRY
                task_history.error_message = str(exc)
                task_history.retry_count = (task_history.retry_count or 0) + 1
                session.commit()
        except Exception as e:
            logger.error(f"Failed to record task retry: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _get_task_type(self):
        """根据任务名称获取任务类型"""
        if 'crawl_url' in self.name:
            return 'crawl_url'
        elif 'crawl_batch' in self.name:
            return 'crawl_batch'
        elif 'scheduled_crawl' in self.name:
            return 'scheduled_crawl'
        elif 'cleanup' in self.name:
            return 'cleanup'
        elif 'reprocess' in self.name:
            return 'reprocess'
        else:
            return 'unknown'


@app.task(base=CallbackTask, bind=True, max_retries=3, track_started=True)
def crawl_url(self, url: str, spider_name: str = 'general') -> Dict:
    try:
        logger.info(f"Starting crawl for URL: {url}")
        
        command = [
            'scrapy', 'crawl', spider_name,
            '-a', f'start_url={url}',
            '-L', 'INFO'
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"Scrapy command failed: {result.stderr}")
        
        return {
            'status': 'success',
            'url': url,
            'timestamp': datetime.now().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Crawl timeout for URL: {url}")
        raise self.retry(countdown=60)
    except Exception as exc:
        logger.error(f"Crawl failed for URL {url}: {exc}")
        raise self.retry(exc=exc, countdown=30)


@app.task(base=CallbackTask, bind=True, track_started=True)
def crawl_batch(self, urls: List[str], spider_name: str = 'general') -> Dict:
    logger.info(f"Starting batch crawl for {len(urls)} URLs")
    
    job = group(crawl_url.s(url, spider_name) for url in urls)
    result = job.apply_async()
    
    return {
        'status': 'batch_started',
        'total_urls': len(urls),
        'task_id': result.id,
        'timestamp': datetime.now().isoformat()
    }


@app.task(base=CallbackTask, bind=True, track_started=True)
def scheduled_crawl(self) -> Dict:
    logger.info("Starting scheduled crawl")
    
    with open('config/crawl_sources.json', 'r') as f:
        sources = json.load(f)
    
    urls = []
    for source in sources.get('sources', []):
        if source.get('enabled', True):
            urls.extend(source.get('urls', []))
    
    if urls:
        result = crawl_batch.delay(urls)
        return {
            'status': 'scheduled_crawl_started',
            'urls_count': len(urls),
            'task_id': result.id
        }
    else:
        return {
            'status': 'no_urls_to_crawl'
        }


@app.task(base=CallbackTask, bind=True, track_started=True)
def cleanup_old_articles(self, days: int = 90) -> Dict:
    logger.info(f"Cleaning up articles older than {days} days")
    
    session = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted_count = session.query(Article).filter(
            and_(
                Article.crawl_time < cutoff_date,
                Article.level < 3
            )
        ).delete()
        
        session.commit()
        
        logger.info(f"Deleted {deleted_count} old articles")
        return {
            'status': 'cleanup_completed',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Cleanup failed: {e}")
        raise
    finally:
        session.close()


@app.task(base=CallbackTask, bind=True, track_started=True)
def reprocess_articles(self, article_ids: List[int] = None) -> Dict:
    logger.info("Starting article reprocessing")
    
    session = SessionLocal()
    try:
        query = session.query(Article)
        if article_ids:
            query = query.filter(Article.id.in_(article_ids))
        
        articles = query.all()
        processed_count = 0
        
        for article in articles:
            try:
                from ..nlp.processor import NLPProcessor
                processor = NLPProcessor()
                
                nlp_result = processor.process(
                    title=article.title,
                    content=article.content
                )
                
                article.category = nlp_result.get('category')
                article.tags = nlp_result.get('tags', [])
                article.level = nlp_result.get('level', 0)
                article.sentiment = nlp_result.get('sentiment')
                article.keywords = nlp_result.get('keywords', [])
                article.summary = nlp_result.get('summary')
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to reprocess article {article.id}: {e}")
        
        session.commit()
        
        return {
            'status': 'reprocessing_completed',
            'processed_count': processed_count,
            'total_count': len(articles)
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Reprocessing failed: {e}")
        raise
    finally:
        session.close()