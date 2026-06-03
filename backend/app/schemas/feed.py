from pydantic import BaseModel


class UserActionRequest(BaseModel):
    userId: int | None = None


class CommentCreateRequest(BaseModel):
    userId: int | None = None
    content: str
