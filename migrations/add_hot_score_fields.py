#!/usr/bin/env python
"""添加文章热度相关字段的数据库迁移脚本"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.models import SessionLocal
from loguru import logger


def migrate():
    """执行数据库迁移，添加热度相关字段"""
    session = SessionLocal()
    
    try:
        logger.info("开始添加热度相关字段...")
        
        # 添加新字段
        alter_statements = [
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS like_count INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS share_count INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS hot_score FLOAT DEFAULT 0.0 NOT NULL",
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS hot_score_updated_at TIMESTAMP"
        ]
        
        # 创建索引
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_hot_score ON articles(hot_score)",
            "CREATE INDEX IF NOT EXISTS idx_hot_score_time ON articles(hot_score, crawl_time)"
        ]
        
        # 执行ALTER语句
        for stmt in alter_statements:
            logger.info(f"执行: {stmt}")
            session.execute(text(stmt))
        
        # 执行索引创建
        for stmt in index_statements:
            logger.info(f"创建索引: {stmt}")
            session.execute(text(stmt))
        
        # 初始化现有文章的热度分数（基于level和发布时间）
        logger.info("初始化现有文章的热度分数...")
        init_hot_score = """
        UPDATE articles 
        SET hot_score = COALESCE(level, 1) * 10.0 + 
                       COALESCE(sentiment + 1, 1) * 5.0,
            hot_score_updated_at = NOW()
        WHERE hot_score = 0
        """
        session.execute(text(init_hot_score))
        
        session.commit()
        logger.success("热度字段添加成功！")
        
        # 验证迁移结果
        result = session.execute(text("""
            SELECT COUNT(*) as total,
                   AVG(hot_score) as avg_score,
                   MAX(hot_score) as max_score
            FROM articles
        """)).first()
        
        logger.info(f"文章总数: {result[0]}, 平均热度: {result[1]:.2f}, 最高热度: {result[2]:.2f}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"迁移失败: {e}")
        raise
    finally:
        session.close()


def rollback():
    """回滚迁移（删除添加的字段）"""
    session = SessionLocal()
    
    try:
        logger.info("回滚热度相关字段...")
        
        # 删除索引
        drop_index_statements = [
            "DROP INDEX IF EXISTS idx_hot_score",
            "DROP INDEX IF EXISTS idx_hot_score_time"
        ]
        
        # 删除字段
        drop_column_statements = [
            "ALTER TABLE articles DROP COLUMN IF EXISTS view_count",
            "ALTER TABLE articles DROP COLUMN IF EXISTS like_count",
            "ALTER TABLE articles DROP COLUMN IF EXISTS share_count",
            "ALTER TABLE articles DROP COLUMN IF EXISTS hot_score",
            "ALTER TABLE articles DROP COLUMN IF EXISTS hot_score_updated_at"
        ]
        
        for stmt in drop_index_statements:
            logger.info(f"删除索引: {stmt}")
            session.execute(text(stmt))
        
        for stmt in drop_column_statements:
            logger.info(f"删除字段: {stmt}")
            session.execute(text(stmt))
        
        session.commit()
        logger.success("回滚成功！")
        
    except Exception as e:
        session.rollback()
        logger.error(f"回滚失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="热度字段数据库迁移")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    args = parser.parse_args()
    
    if args.rollback:
        rollback()
    else:
        migrate()