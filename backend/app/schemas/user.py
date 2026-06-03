from pydantic import BaseModel


class FollowRequest(BaseModel):
    currentUserId: int
