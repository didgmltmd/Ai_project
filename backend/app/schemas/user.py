from pydantic import BaseModel


class FollowRequest(BaseModel):
    currentUserId: int


class UserResponse(BaseModel):
    id: int
    username: str
    displayName: str
    email: str | None = None
    profileImageUrl: str | None = None
    bio: str | None = None
    workoutIntro: str | None = None
    followerCount: int
    followingCount: int
    postCount: int
    isMock: bool


class ProfileUpdateRequest(BaseModel):
    username: str | None = None
    displayName: str | None = None
    profileImageUrl: str | None = None
    bio: str | None = None
    workoutIntro: str | None = None
