# 爬虫系统文档目录

本目录包含了爬虫系统的完整技术文档。

## 📚 文档列表

### 系统架构与流程
- **[scrapy-pipeline-flow.md](./scrapy-pipeline-flow.md)** - Scrapy Request到Pipeline调用流程详解
  > 详细分析从Request开始到数据存储的完整调用流程，包括微服务架构说明

### 运维与维护
- **[crawler-verification-guide.md](./crawler-verification-guide.md)** - 爬虫修复验证命令集合
  > 包含验证爬虫系统修复效果的各种测试命令和验证流程

## 🚀 快速开始

1. **理解系统架构**：先阅读 `scrapy-pipeline-flow.md` 了解整体架构
2. **验证系统状态**：使用 `crawler-verification-guide.md` 中的命令验证系统是否正常运行
3. **故障排除**：参考验证指南中的故障排除章节

## 📋 文档约定

- 所有命令都假设在项目根目录执行
- 使用 `uv` 作为包管理工具
- Python 环境：3.11+
- Scrapy 版本：2.13+

## 🔗 相关链接

- [项目根目录](../)
- [源代码](../src/)
- [配置文件](../CLAUDE.md)
- [环境配置](../.env.example)

---
*文档维护：定期更新以保持与代码同步*