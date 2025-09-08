# Crawler Verification Guide

本文档记录了验证爬虫系统修复效果的各种测试命令和验证流程。

> **文档路径**: `docs/crawler-verification-guide.md`  
> **创建时间**: 2025-09-02  
> **最后更新**: 2025-09-02  
> **适用版本**: Scrapy 2.13+

## 🔧 核心组件测试

### 1. 测试NLP KeywordExtractor
验证jieba停用词设置修复是否成功：

```bash
uv run python -c "
from src.nlp.extractor import KeywordExtractor
print('正在测试NLP KeywordExtractor初始化...')
try:
    extractor = KeywordExtractor()
    print('✓ KeywordExtractor初始化成功！')
    # 测试关键词提取
    test_text = '这是一个关于人工智能和机器学习的测试文章'
    keywords = extractor.extract_keywords(test_text, 5)
    print(f'✓ 关键词提取测试成功: {keywords}')
except Exception as e:
    print(f'✗ 错误: {e}')
    import traceback
    traceback.print_exc()
"
```

### 2. 测试NLP Pipeline
验证完整的NLP处理管道：

```bash
uv run python -c "
import sys
sys.path.insert(0, '.')
from src.pipelines import NLPPipeline
print('测试NLP Pipeline初始化...')
try:
    pipeline = NLPPipeline()
    print('✓ NLP Pipeline初始化成功！')
except Exception as e:
    print(f'✗ 错误: {e}')
    import traceback
    traceback.print_exc()
"
```

## 🕷️ Scrapy系统测试

### 3. Scrapy配置检查
检查项目配置是否正确：

```bash
uv run scrapy check
```

### 4. 列出可用爬虫
验证爬虫是否能正常加载：

```bash
uv run scrapy list
```

### 5. 查看最新日志
检查是否还有Critical错误：

```bash
tail -n 20 /Users/dingmao/dm/code/taiji/crawler/logs/scrapy.log
```

## 🚀 完整爬虫测试

### 6. 简单爬虫运行测试
运行一个简单的测试爬取（如果需要）：

```bash
# 在macOS上使用gtimeout，或者直接限制条目数
uv run scrapy crawl general -s CLOSESPIDER_ITEMCOUNT=1 -a start_urls="http://httpbin.org/html"
uv run scrapy crawl general -a start_urls="http://httpbin.org/html"
```

### 7. 检查爬虫进程
查看是否有爬虫进程在运行：

```bash
lsof -i :8000  # 检查API服务端口
```

## 📊 修复验证清单

执行上述命令后，确认以下项目：

- [ ] KeywordExtractor初始化无TypeError
- [ ] NLP Pipeline初始化成功
- [ ] Scrapy配置检查通过（0 contracts）
- [ ] 能正常列出爬虫（如：general）
- [ ] 日志中无Critical错误
- [ ] 只有警告级别的废弃提示（已修复的不再出现）

## 🔍 故障排除

如果测试失败，检查以下项目：

1. **环境变量**：确保.env文件配置正确
2. **数据库连接**：PostgreSQL和Redis是否正在运行
3. **依赖包**：运行 `uv sync` 确保所有依赖已安装
4. **文件权限**：确保logs目录有写入权限

## 📝 修复历史

- ✅ 修复KeywordExtractor中jieba停用词设置的TypeError
- ✅ 添加异步process_start()方法替代废弃的process_start_requests()
- ✅ 实现process_spider_output_async()方法支持异步spider输出
- ✅ 移除废弃的REQUEST_FINGERPRINTER_IMPLEMENTATION配置
- ✅ 测试修复效果并验证爬虫能正常启动

---
*文档创建时间：2025-09-02*
*最后修复验证：2025-09-02*