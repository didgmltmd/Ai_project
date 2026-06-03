from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.analyze import router as analyze_router
from app.api.routes.feed import router as feed_router
from app.api.routes.health import router as health_router
from app.core.config import settings


app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api/v1")
app.include_router(feed_router, prefix="/api/v1")
app.include_router(health_router)
app.mount("/media/shortforms", StaticFiles(directory=str(settings.shortforms_dir)), name="shortforms")
