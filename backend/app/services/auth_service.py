from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import auth_repository


async def sign_up(session: AsyncSession, username: str, email: str, password: str) -> dict:
    user = await auth_repository.create_user(session, username, email, password)
    return {"user": user, **auth_repository.create_token_pair(user["id"])}


async def login(session: AsyncSession, email: str, password: str) -> dict | None:
    user = await auth_repository.authenticate(session, email, password)
    if not user:
        return None
    return {"user": user, **auth_repository.create_token_pair(user["id"])}


async def refresh(session: AsyncSession, refresh_token: str) -> dict | None:
    user_id = auth_repository.verify_token(refresh_token, "refresh")
    if not user_id:
        return None
    user = await auth_repository.get_user_by_id(session, user_id)
    if not user:
        return None
    return {"user": user, **auth_repository.create_token_pair(user["id"])}
