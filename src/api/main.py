import os
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from dotenv import load_dotenv

from .routers import articles, tasks, admin, stats, monitor, sources
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
    version="1.0.0",
    # Disable built-in docs to allow custom, configurable assets (CDN/local)
    docs_url=None,
    redoc_url=None,
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
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["Monitoring"])
app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])

# Optionally serve local static assets (for offline Swagger UI)
# Put swagger-ui-dist files under ./static/swagger-ui if you want to use local assets
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    # Allow overriding asset URLs via environment variables (helpful for regions where default CDN is blocked)
    bundle_js_url = os.getenv(
        "SWAGGER_UI_BUNDLE_JS_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    )
    preset_js_url = os.getenv(
        "SWAGGER_UI_STANDALONE_JS_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js",
    )
    css_url = os.getenv(
        "SWAGGER_UI_CSS_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )
    # Prefer local files if present
    local_bundle = "/static/swagger-ui/swagger-ui-bundle.js"
    local_preset = "/static/swagger-ui/swagger-ui-standalone-preset.js"
    local_css = "/static/swagger-ui/swagger-ui.css"
    if (
        os.path.exists("static/swagger-ui/swagger-ui-bundle.js")
        and os.path.exists("static/swagger-ui/swagger-ui-standalone-preset.js")
        and os.path.exists("static/swagger-ui/swagger-ui.css")
    ):
        bundle_js_url = local_bundle
        preset_js_url = local_preset
        css_url = local_css

    html = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
      <meta charset=\"UTF-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
      <title>{app.title} - Swagger UI</title>
      <link rel=\"stylesheet\" type=\"text/css\" href=\"{css_url}\" />
      <style>body {{ margin: 0; background: #fafafa; }}</style>
    </head>
    <body>
      <div id=\"swagger-ui\"></div>
      <script src=\"{bundle_js_url}\"></script>
      <script src=\"{preset_js_url}\"></script>
      <script>
        window.onload = function() {{
          const ui = SwaggerUIBundle({{
            url: "{app.openapi_url}",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
            layout: "StandaloneLayout"
          }});
          window.ui = ui;
        }}
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_redirect():
    # Simple redirect to Swagger UI to keep a single docs entrypoint
    # Users can still access OpenAPI at /openapi.json
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
    )

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
