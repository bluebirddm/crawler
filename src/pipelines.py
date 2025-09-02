import hashlib
from datetime import datetime
from urllib.parse import urlparse
from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from loguru import logger
from .models import Article, SessionLocal
from .nlp.processor import NLPProcessor


class ValidationPipeline:
    def process_item(self, item, spider):
        if not item.get('url'):
            raise DropItem(f"Missing URL in item")
        
        if not item.get('title'):
            raise DropItem(f"Missing title in item")
        
        if not item.get('content'):
            raise DropItem(f"Missing content in item")
        
        if len(item.get('content', '')) < 50:
            raise DropItem(f"Content too short: {item.get('url')}")
        
        item['crawl_time'] = datetime.now()
        item['source_domain'] = urlparse(item['url']).netloc
        
        return item


class DuplicatesPipeline:
    def __init__(self):
        self.seen_urls = set()
        self.content_hashes = set()
    
    def process_item(self, item, spider):
        if item['url'] in self.seen_urls:
            raise DropItem(f"Duplicate URL: {item['url']}")
        
        content_hash = hashlib.md5(item['content'].encode()).hexdigest()
        if content_hash in self.content_hashes:
            raise DropItem(f"Duplicate content: {item['url']}")
        
        self.seen_urls.add(item['url'])
        self.content_hashes.add(content_hash)
        
        return item


class NLPPipeline:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
    
    def process_item(self, item, spider):
        try:
            nlp_result = self.nlp_processor.process(
                title=item['title'],
                content=item['content']
            )
            
            item['category'] = nlp_result.get('category')
            item['tags'] = nlp_result.get('tags', [])
            item['level'] = nlp_result.get('level', 0)
            item['sentiment'] = nlp_result.get('sentiment')
            item['keywords'] = nlp_result.get('keywords', [])
            item['summary'] = nlp_result.get('summary')
            
            logger.info(f"NLP processed: {item['title'][:50]}...")
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            item['category'] = 'uncategorized'
            item['tags'] = []
            item['level'] = 0
        
        return item


class PostgreSQLPipeline:
    def __init__(self):
        self.session = None
    
    def open_spider(self, spider):
        self.session = SessionLocal()
        logger.info("Database session opened")
    
    def close_spider(self, spider):
        if self.session:
            self.session.close()
            logger.info("Database session closed")
    
    def process_item(self, item, spider):
        try:
            article = Article(
                url=item['url'],
                title=item['title'],
                content=item['content'],
                author=item.get('author'),
                publish_date=item.get('publish_date'),
                source=item.get('source'),
                source_domain=item['source_domain'],
                raw_html=item.get('raw_html'),
                category=item.get('category'),
                tags=item.get('tags'),
                level=item.get('level', 0),
                sentiment=item.get('sentiment'),
                keywords=item.get('keywords'),
                summary=item.get('summary'),
                metadata_json=item.get('metadata', {})
            )
            
            self.session.add(article)
            self.session.commit()
            logger.info(f"Article saved: {item['title'][:50]}...")
            
        except IntegrityError:
            self.session.rollback()
            logger.warning(f"Article already exists: {item['url']}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save article: {e}")
            raise
        
        return item