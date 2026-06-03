from fastapi import APIRouter

from app.schemas.analysis import FeedPostResponse
from app.services.analysis_repository import analysis_repository

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=list[FeedPostResponse])
def get_feed() -> list[FeedPostResponse]:
    return [FeedPostResponse(**item) for item in analysis_repository.list_feed()]
