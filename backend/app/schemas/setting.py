from pydantic import BaseModel


class SettingsUpdateRequest(BaseModel):
    pushEnabled: bool | None = None
    commentEnabled: bool | None = None
    messageEnabled: bool | None = None
    publicProfile: bool | None = None
