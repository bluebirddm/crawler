# Crawler Frontend

Web爬虫系统的前端管理界面，使用React + TypeScript + Tailwind CSS + shadcn/ui构建。

## 功能特性

- 📊 **仪表板** - 系统概览、实时统计、图表展示
- 📝 **文章管理** - 查看、搜索、筛选、删除爬取的文章
- ⚡ **任务管理** - 创建爬取任务、监控任务状态
- 🔧 **系统管理** - Worker监控、数据库管理、系统配置

## 技术栈

- **React 19** - 用户界面框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 原子化CSS框架
- **shadcn/ui** - 基于Radix UI的组件库
- **React Query** - 服务端状态管理
- **React Router** - 路由管理
- **Recharts** - 图表库
- **Axios** - HTTP客户端

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 项目结构

```
src/
├── api/              # API调用层
│   ├── client.ts    # Axios客户端配置
│   ├── articles.ts  # 文章相关API
│   ├── tasks.ts     # 任务相关API
│   └── admin.ts     # 管理相关API
├── components/       # 组件
│   ├── layout/      # 布局组件
│   └── ui/          # UI组件
├── lib/             # 工具函数
├── pages/           # 页面组件
│   ├── Dashboard.tsx
│   ├── Articles.tsx
│   └── Tasks.tsx
├── types/           # TypeScript类型定义
├── App.tsx          # 主应用组件
├── main.tsx         # 应用入口
└── index.css        # 全局样式
```

## 环境变量

创建 `.env` 文件：

```env
VITE_API_URL=http://localhost:8000
```

## API代理

开发环境下，所有 `/api` 请求会自动代理到 `http://localhost:8000`。

## 主要页面

### 仪表板 (/)
- 系统状态概览
- 文章统计
- 爬取趋势图表
- 分类分布图表
- Workers状态监控

### 文章管理 (/articles)
- 文章列表展示
- 搜索和筛选功能
- 分类/级别筛选
- 文章详情查看
- 批量删除

### 任务管理 (/tasks)
- 单个URL爬取
- 批量URL爬取
- 活动任务监控
- 定时任务查看
- 任务取消功能

## 开发指南

### 添加新页面

1. 在 `src/pages/` 创建页面组件
2. 在 `src/App.tsx` 添加路由
3. 在 `src/components/layout/Sidebar.tsx` 添加导航项

### 添加新API

1. 在 `src/api/` 创建API模块
2. 在 `src/types/index.ts` 添加类型定义
3. 在页面中使用React Query调用

### 自定义主题

编辑 `src/index.css` 中的CSS变量来自定义颜色主题。

## 注意事项

- 确保后端API服务运行在 `http://localhost:8000`
- 开发时使用Chrome DevTools的Network面板调试API请求
- 使用React Query DevTools调试缓存状态

## License

MIT
