from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.user import FollowRequest, ProfileUpdateRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


@router.get("/search")
async def search_users(q: str, currentUserId: int | None = None, session: AsyncSession = Depends(get_db)):
    return await user_service.search_users(session, q, currentUserId)


@router.get("/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_profile(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@router.get("/{user_id}/profile")
async def get_profile(user_id: int, currentUserId: int | None = None, session: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_profile(session, user_id, currentUserId)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@router.patch("/{user_id}/profile")
async def patch_profile(user_id: int, payload: ProfileUpdateRequest, session: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.update_user_profile(session, user_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@router.post("/{user_id}/follow")
async def follow_user(user_id: int, payload: FollowRequest, session: AsyncSession = Depends(get_db)):
    if user_id == payload.currentUserId:
        raise HTTPException(status_code=400, detail="자기 자신을 팔로우할 수 없습니다.")
    try:
        result = await user_service.toggle_follow(session, user_id, payload.currentUserId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return result


@router.get("/{user_id}/followers")
async def get_followers(user_id: int, session: AsyncSession = Depends(get_db)):
    return await user_service.list_followers(session, user_id)


@router.get("/{user_id}/following")
async def get_following(user_id: int, session: AsyncSession = Depends(get_db)):
    return await user_service.list_following(session, user_id)


@router.get("/{user_id}/workout-summary")
async def get_workout_summary(user_id: int, session: AsyncSession = Depends(get_db)):
    return await user_service.workout_summary(session, user_id)


@router.put("/{user_id}/profile-image")
async def upload_profile_image(
    user_id: int,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    # Validate content type
    content_type = image.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="허용되지 않는 이미지 형식입니다. JPEG, PNG, WebP만 지원합니다.",
        )

    # Read file content and validate size
    content = await image.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="빈 이미지 파일은 업로드할 수 없습니다.")
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="이미지 크기는 5MB를 초과할 수 없습니다.",
        )

    # Determine file extension from content type
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    ext = ext_map.get(content_type, ".jpg")

    # Save file to profile_images directory
    profile_images_dir = settings.uploads_dir / "profile_images"
    profile_images_dir.mkdir(parents=True, exist_ok=True)

    filename = f"profile_{user_id}_{uuid4().hex[:8]}{ext}"
    file_path = profile_images_dir / filename
    file_path.write_bytes(content)

    # Build the URL for the saved image
    image_url = f"/media/profile_images/{filename}"

    # Update user's profile_image_url in the database
    try:
        user = await user_service.update_user_profile(
            session, user_id, {"profileImageUrl": image_url}
        )
    except ValueError as exc:
        # Clean up saved file on DB error
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not user:
        # Clean up saved file if user not found
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return {"profileImageUrl": image_url}
