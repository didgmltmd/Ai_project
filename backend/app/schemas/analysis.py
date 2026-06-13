from typing import Literal, Union
from pydantic import BaseModel, Field

AnalysisStatus = Literal["pending", "processing", "completed", "failed"]


class AnalyzeStartResponse(BaseModel):
    analysisId: str
    status: AnalysisStatus
    exercise: str | None = None
    message: str | None = None


class Metrics(BaseModel):
    depthScore: int = Field(ge=0, le=35)
    alignmentScore: int = Field(ge=0, le=30)
    consistencyScore: int = Field(ge=0, le=20)
    stabilityScore: int = Field(ge=0, le=15)


class ShoulderPressMetrics(BaseModel):
    symmetryScore: int = Field(ge=0, le=100)
    overextensionScore: int = Field(ge=0, le=100)
    alignmentScore: int = Field(ge=0, le=100)
    consistencyScore: int | None = Field(default=None, ge=0, le=100)


class Issue(BaseModel):
    type: str
    reps: list[int] = []
    message: str


class Feedback(BaseModel):
    summary: str
    good: list[str]
    improvements: list[str]
    coaching: str


class Report(BaseModel):
    summary: str
    strengths: list[str]
    improvements: list[str]
    coaching: str


class AnalysisStatusResponse(BaseModel):
    analysisId: str
    status: AnalysisStatus
    exercise: str | None = None
    progressStage: str | None = None
    progressPercent: int | None = Field(default=None, ge=0, le=100)
    currentFrame: int | None = None
    totalFrames: int | None = None
    repCount: int | None = None
    totalScore: int | None = None
    metrics: Union[Metrics, ShoulderPressMetrics, None] = None
    issues: list[Issue] | None = None
    feedback: Feedback | None = None
    report: Report | None = None
    shortformUrl: str | None = None
    error: str | None = None


class ShortformResponse(BaseModel):
    analysisId: str
    status: AnalysisStatus
    shortformUrl: str | None = None


class FeedPostResponse(BaseModel):
    analysisId: str
    userName: str
    profileInitial: str
    uploadedAt: str
    exerciseType: str
    repCount: int
    score: int
    summaryFeedback: str
    caption: str
    hashtags: list[str]
    likeCount: int
    commentCount: int
    liked: bool
    videoUrl: str | None = None
