#!/usr/bin/env python
"""数据库初始化脚本"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.models import init_db, SessionLocal, Article
from loguru import logger


def main():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 创建所有表
        init_db()
        
        # 验证数据库连接
        session = SessionLocal()
        count = session.query(Article).count()
        session.close()
        
        logger.success(f"数据库初始化成功！当前有 {count} 篇文章")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()