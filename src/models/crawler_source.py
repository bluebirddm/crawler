from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class CrawlerSource(Base):
    __tablename__ = "crawler_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    url = Column(String(500), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    interval = Column(Integer, default=60, nullable=False)  # 爬取间隔（分钟）
    selector = Column(String(500), default='article')  # CSS选择器
    category = Column(String(100), nullable=False)
    
    # 统计信息
    last_crawled = Column(DateTime)
    article_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 索引优化
    __table_args__ = (
        Index('idx_enabled_interval', 'enabled', 'interval'),
        Index('idx_category', 'category'),
        Index('idx_last_crawled', 'last_crawled'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'enabled': self.enabled,
            'interval': self.interval,
            'selector': self.selector,
            'category': self.category,
            'lastCrawled': self.last_crawled.isoformat() if self.last_crawled else None,
            'articleCount': self.article_count,
            'successCount': self.success_count,
            'failureCount': self.failure_count,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<CrawlerSource(id={self.id}, name='{self.name}', url='{self.url}')>"