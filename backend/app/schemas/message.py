from pydantic import BaseModel


class MessageCreateRequest(BaseModel):
    senderId: int
    receiverId: int
    content: str
