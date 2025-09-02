import React from 'react';

export function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">仪表板</h2>
        <p className="text-gray-600">系统运行状态概览</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium">文章总数</h3>
          <p className="text-2xl font-bold">0</p>
          <p className="text-xs text-gray-500">累计爬取文章数量</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium">数据库状态</h3>
          <p className="text-2xl font-bold">未知</p>
          <p className="text-xs text-gray-500">PostgreSQL连接状态</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium">Celery状态</h3>
          <p className="text-2xl font-bold">未知</p>
          <p className="text-xs text-gray-500">任务队列运行状态</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium">活动Workers</h3>
          <p className="text-2xl font-bold">0</p>
          <p className="text-xs text-gray-500">正在运行的工作进程</p>
        </div>
      </div>
    </div>
  );
}