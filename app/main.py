import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.watcher_service import WatcherService
from app.services.db_service import DBService
from app.routers import (
    resume_router,
    telegram_router,
    pipeline_router,
    watcher_router,
    profile_router
)

# Project base paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and persisted watcher state on startup
    DBService.init_db()
    WatcherService.initialize()
    yield
    # Clean up on shutdown
    if WatcherService.is_running():
        await WatcherService.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    description=(
        "Autonomous AI engine to scrape LinkedIn jobs, calculate resume match percentage, "
        "detect high-probability selection roles, and broadcast them instantly to a Telegram bot. "
        "Powered by Python, FastAPI, and 100% Free APIs."
    )
)

# Enable CORS for cross-origin client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API Routers
app.include_router(resume_router)
app.include_router(telegram_router)
app.include_router(pipeline_router)
app.include_router(watcher_router)
app.include_router(profile_router)


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def render_dashboard(request: Request):
    """Serve the interactive JobFit AI dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "default_keywords": settings.DEFAULT_JOB_KEYWORDS,
            "default_location": settings.DEFAULT_JOB_LOCATION,
        }
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health and status check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "telegram_configured": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
        "watcher_running": WatcherService.is_running()
    }
