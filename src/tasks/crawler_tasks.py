import subprocess
import json
from datetime import datetime, timedelta
from typing import List, Dict
from celery import Task, group
from loguru import logger
from .celery_app import app
from ..models import Article, SessionLocal
from sqlalchemy import and_


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed with exception: {exc}")


@app.task(base=CallbackTask, bind=True, max_retries=3)
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


@app.task(base=CallbackTask)
def crawl_batch(urls: List[str], spider_name: str = 'general') -> Dict:
    logger.info(f"Starting batch crawl for {len(urls)} URLs")
    
    job = group(crawl_url.s(url, spider_name) for url in urls)
    result = job.apply_async()
    
    return {
        'status': 'batch_started',
        'total_urls': len(urls),
        'task_id': result.id,
        'timestamp': datetime.now().isoformat()
    }


@app.task(base=CallbackTask)
def scheduled_crawl() -> Dict:
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


@app.task(base=CallbackTask)
def cleanup_old_articles(days: int = 90) -> Dict:
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


@app.task(base=CallbackTask)
def reprocess_articles(article_ids: List[int] = None) -> Dict:
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