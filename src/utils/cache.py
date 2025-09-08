"""Redis缓存工具"""

import json
import redis
from typing import Optional, List, Any, Callable
from datetime import datetime, timedelta
from loguru import logger
import os
from functools import wraps

# Redis 连接配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# 缓存过期时间（秒）
CACHE_TTL = {
    'hot_articles': 900,      # 热门文章列表 15分钟
    'trending_articles': 600,  # 趋势文章 10分钟
    'article_stats': 300,      # 文章统计 5分钟
    'category_hot': 1200,      # 分类热门 20分钟
}


class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        """连接Redis"""
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self.client:
            return False
        
        try:
            json_value = json.dumps(value, default=str)
            if ttl:
                self.client.setex(key, ttl, json_value)
            else:
                self.client.set(key, json_value)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.client:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check existence of {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置键的过期时间"""
        if not self.client:
            return False
        
        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Failed to set expiry for {key}: {e}")
            return False


# 全局缓存实例
cache = RedisCache()


def cache_key_builder(prefix: str, **kwargs) -> str:
    """构建缓存键"""
    parts = [prefix]
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}:{value}")
    return ":".join(parts)


def cached(prefix: str, ttl: Optional[int] = None):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 构建缓存键
            cache_key = cache_key_builder(prefix, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache_ttl = ttl or CACHE_TTL.get(prefix, 600)
            cache.set(cache_key, result, cache_ttl)
            logger.debug(f"Cache set for {cache_key} with TTL {cache_ttl}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_article_cache(article_id: Optional[int] = None):
    """使文章相关缓存失效"""
    patterns_to_delete = [
        "hot_articles:*",
        "trending_articles:*",
        "article_stats:*"
    ]
    
    if article_id:
        patterns_to_delete.append(f"article:{article_id}:*")
    
    total_deleted = 0
    for pattern in patterns_to_delete:
        deleted = cache.delete_pattern(pattern)
        total_deleted += deleted
    
    logger.info(f"Invalidated {total_deleted} cache entries")
    return total_deleted


def get_hot_articles_cache_key(
    limit: int = 10,
    category: Optional[str] = None,
    time_range: Optional[str] = None
) -> str:
    """获取热门文章缓存键"""
    return cache_key_builder(
        "hot_articles",
        limit=limit,
        category=category,
        time_range=time_range
    )


def get_trending_articles_cache_key(
    limit: int = 10,
    hours: int = 24
) -> str:
    """获取趋势文章缓存键"""
    return cache_key_builder(
        "trending_articles",
        limit=limit,
        hours=hours
    )