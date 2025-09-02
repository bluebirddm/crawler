import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    'crawler',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['src.tasks.crawler_tasks']
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=4,
    
    beat_schedule={
        'hourly-crawl': {
            'task': 'src.tasks.crawler_tasks.scheduled_crawl',
            'schedule': crontab(minute=0),
            'args': ()
        },
        'daily-cleanup': {
            'task': 'src.tasks.crawler_tasks.cleanup_old_articles',
            'schedule': crontab(hour=2, minute=0),
            'args': ()
        },
    }
)

if __name__ == '__main__':
    app.start()