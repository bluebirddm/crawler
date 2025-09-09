#!/usr/bin/env python3
"""
迁移工具：将config/crawl_sources.json中的配置导入到数据库
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from src.models import init_db, SessionLocal, CrawlerSource


def load_config_sources():
    """加载配置文件中的爬取源"""
    config_path = Path(__file__).parent / "config" / "crawl_sources.json"
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return []
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config.get('sources', [])


def migrate_sources_to_db():
    """将配置文件中的爬取源迁移到数据库"""
    
    # 初始化数据库
    logger.info("初始化数据库表...")
    init_db()
    
    # 加载配置文件
    config_sources = load_config_sources()
    
    if not config_sources:
        logger.warning("没有找到要迁移的爬取源")
        return
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        migrated_count = 0
        skipped_count = 0
        
        for source_config in config_sources:
            name = source_config.get('name', '')
            urls = source_config.get('urls', [])
            enabled = source_config.get('enabled', False)
            category = source_config.get('category', '未分类')
            spider = source_config.get('spider', 'general')
            
            # 为每个URL创建一个爬取源
            for url in urls:
                # 生成唯一名称
                source_name = f"{name} - {url.split('/')[2] if '/' in url else url}"
                
                # 检查是否已存在
                existing = db.query(CrawlerSource).filter(
                    CrawlerSource.url == url
                ).first()
                
                if existing:
                    logger.info(f"跳过已存在的源: {source_name} ({url})")
                    skipped_count += 1
                    continue
                
                # 创建新的爬取源
                source = CrawlerSource(
                    name=source_name,
                    url=url,
                    enabled=enabled,
                    interval=60,  # 默认60分钟
                    selector='article',  # 默认选择器
                    category=category
                )
                
                db.add(source)
                migrated_count += 1
                logger.info(f"添加爬取源: {source_name}")
        
        # 提交事务
        db.commit()
        
        logger.success(f"迁移完成! 成功迁移 {migrated_count} 个爬取源，跳过 {skipped_count} 个已存在的源")
    
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


def add_sample_sources():
    """添加示例爬取源（用于测试）"""
    
    db = SessionLocal()
    
    try:
        sample_sources = [
            {
                "name": "Hacker News",
                "url": "https://news.ycombinator.com",
                "category": "科技",
                "selector": ".athing",
                "interval": 30,
                "enabled": True
            },
            {
                "name": "Reddit - Programming",
                "url": "https://www.reddit.com/r/programming",
                "category": "技术社区",
                "selector": "[data-testid='post-container']",
                "interval": 60,
                "enabled": True
            },
            {
                "name": "GitHub Trending",
                "url": "https://github.com/trending",
                "category": "开源项目",
                "selector": ".Box-row",
                "interval": 120,
                "enabled": False
            }
        ]
        
        added_count = 0
        
        for source_data in sample_sources:
            # 检查是否已存在
            existing = db.query(CrawlerSource).filter(
                CrawlerSource.name == source_data['name']
            ).first()
            
            if existing:
                logger.info(f"跳过已存在的示例源: {source_data['name']}")
                continue
            
            source = CrawlerSource(**source_data)
            db.add(source)
            added_count += 1
            logger.info(f"添加示例源: {source_data['name']}")
        
        db.commit()
        logger.success(f"成功添加 {added_count} 个示例爬取源")
    
    except Exception as e:
        logger.error(f"添加示例源失败: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="爬取源数据迁移工具")
    parser.add_argument("--sample", action="store_true", help="添加示例爬取源")
    args = parser.parse_args()
    
    if args.sample:
        logger.info("添加示例爬取源...")
        add_sample_sources()
    else:
        logger.info("开始迁移爬取源配置...")
        migrate_sources_to_db()