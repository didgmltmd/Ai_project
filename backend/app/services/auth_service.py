from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import auth_repository


async def sign_up(session: AsyncSession, username: str, email: str, password: str) -> dict:
    user = await auth_repository.create_user(session, username, email, password)
    return {"user": user, "accessToken": auth_repository.make_mock_token(user["id"]), "tokenType": "mock"}


async def login(session: AsyncSession, email: str, password: str) -> dict | None:
    user = await auth_repository.authenticate(session, email, password)
    if not user:
        return None
    return {"user": user, "accessToken": auth_repository.make_mock_token(user["id"]), "tokenType": "mock"}
