from app.routers.resume import router as resume_router
from app.routers.telegram import router as telegram_router
from app.routers.pipeline import router as pipeline_router
from app.routers.watcher import router as watcher_router
from app.routers.profile import router as profile_router

__all__ = [
    "resume_router",
    "telegram_router",
    "pipeline_router",
    "watcher_router",
    "profile_router",
]
