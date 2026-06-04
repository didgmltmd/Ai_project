from pydantic import BaseModel


class SettingsUpdateRequest(BaseModel):
    pushEnabled: bool | None = None
    commentEnabled: bool | None = None
    messageEnabled: bool | None = None
    publicProfile: bool | None = None
    autoPlayEnabled: bool | None = None
    mutedByDefault: bool | None = None
    saveOriginalVideo: bool | None = None
    showAiFeedback: bool | None = None
    postAfterAnalysis: bool | None = None
