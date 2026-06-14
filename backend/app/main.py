from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.analyze import router as analyze_router
from app.api.routes.auth import router as auth_router
from app.api.routes.feed import router as feed_router
from app.api.routes.feeds import router as feeds_router
from app.api.routes.health import router as health_router
from app.api.routes.messages import router as messages_router
from app.api.routes.settings import router as settings_router
from app.api.routes.users import router as users_router
from app.core.config import settings


# Ensure profile_images directory exists before mounting
profile_images_dir = settings.uploads_dir / "profile_images"
profile_images_dir.mkdir(parents=True, exist_ok=True)


app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(feed_router, prefix="/api/v1")
app.include_router(feeds_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(health_router)
app.mount("/media/shortforms", StaticFiles(directory=str(settings.shortforms_dir)), name="shortforms")
app.mount("/media/profile_images", StaticFiles(directory=str(settings.uploads_dir / "profile_images")), name="profile_images")
