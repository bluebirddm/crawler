from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(200))
    publish_date = Column(DateTime)
    source = Column(String(200))
    source_domain = Column(String(200), index=True)
    
    raw_html = Column(Text)
    
    category = Column(String(100), index=True)
    tags = Column(JSON)
    level = Column(Integer, default=0)
    sentiment = Column(Float)
    keywords = Column(JSON)
    summary = Column(Text)
    
    crawl_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 热度相关字段
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    hot_score = Column(Float, default=0.0, nullable=False, index=True)
    hot_score_updated_at = Column(DateTime)
    
    # 关联爬取源
    source_id = Column(Integer, ForeignKey('crawler_sources.id', ondelete='SET NULL'))
    crawler_source = relationship("CrawlerSource", backref="articles")
    
    metadata_json = Column(JSON)
    
    __table_args__ = (
        Index('idx_publish_date', 'publish_date'),
        Index('idx_category_level', 'category', 'level'),
        Index('idx_crawl_time', 'crawl_time'),
        Index('idx_hot_score', 'hot_score'),
        Index('idx_hot_score_time', 'hot_score', 'crawl_time'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content[:500] + '...' if len(self.content) > 500 else self.content,
            'author': self.author,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'source': self.source,
            'source_domain': self.source_domain,
            'category': self.category,
            'tags': self.tags,
            'level': self.level,
            'sentiment': self.sentiment,
            'keywords': self.keywords,
            'summary': self.summary,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'share_count': self.share_count,
            'hot_score': self.hot_score,
            'hot_score_updated_at': self.hot_score_updated_at.isoformat() if self.hot_score_updated_at else None,
            'crawl_time': self.crawl_time.isoformat() if self.crawl_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }