from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Index
from sqlalchemy.sql import func
from .database import Base
import enum


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskHistory(Base):
    __tablename__ = "task_history"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    task_name = Column(String(200), nullable=False, index=True)
    task_type = Column(String(100))  # crawl_url, crawl_batch, reprocess, cleanup 等
    
    # 任务参数
    url = Column(String(500))  # 单个 URL 爬取时使用
    urls = Column(JSON)  # 批量 URL 爬取时使用
    args = Column(JSON)  # 其他任务参数
    kwargs = Column(JSON)  # 关键字参数
    
    # 任务状态和结果
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    result = Column(JSON)  # 任务执行结果
    error_message = Column(Text)  # 错误信息
    traceback = Column(Text)  # 完整的错误堆栈
    retry_count = Column(Integer, default=0)
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 执行信息
    worker_name = Column(String(200))
    queue_name = Column(String(100))
    
    # 元数据
    metadata_json = Column(JSON)
    
    __table_args__ = (
        Index('idx_task_created_at', 'created_at'),
        Index('idx_task_status_created', 'status', 'created_at'),
        Index('idx_task_type', 'task_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'task_type': self.task_type,
            'url': self.url,
            'urls': self.urls,
            'args': self.args,
            'kwargs': self.kwargs,
            'status': self.status.value if self.status else None,
            'result': self.result,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.get_duration(),
            'worker_name': self.worker_name,
            'queue_name': self.queue_name
        }
    
    def get_duration(self):
        """计算任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None