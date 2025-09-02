import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from dotenv import load_dotenv

from .routers import articles, tasks, admin
from ..models import init_db

load_dotenv()

# 配置loguru日志输出
logger.remove()  # 移除默认handler
logger.add(
    "logs/api.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    level="INFO",
    enqueue=True
)
# 保留控制台输出
logger.add(
    lambda msg: print(msg, end=""),
    format="{time:HH:mm:ss} | {level} | {message}",
    level="INFO"
)

app = FastAPI(
    title="Crawler API",
    description="Web Crawler with NLP Processing API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting API server...")
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API server...")

@app.get("/")
async def root():
    return {
        "message": "Crawler API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "celery": "running"
    }

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found"}
    )

@app.exception_handler(500)
async def internal_error(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )