import sys
import uvicorn
from app.config import settings

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"🌐 Dashboard available at: http://{settings.HOST}:{settings.PORT}")
    print(f"📖 Swagger Docs available at: http://{settings.HOST}:{settings.PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
