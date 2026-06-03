from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from app.schemas.analysis import AnalyzeStartResponse, AnalysisStatusResponse, ShortformResponse
from app.services.analysis_pipeline import run_pushup_analysis
from app.services.analysis_repository import analysis_repository
from app.services.video_storage import save_upload_file

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("/pushup", response_model=AnalyzeStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_pushup_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> AnalyzeStartResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="업로드할 파일 이름이 없습니다.")

    try:
        analysis_id, saved_path = await save_upload_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    analysis_repository.create(analysis_id=analysis_id, exercise="pushup", video_path=str(saved_path))
    background_tasks.add_task(run_pushup_analysis, analysis_id, saved_path)
    return AnalyzeStartResponse(
        analysisId=analysis_id,
        status="processing",
        exercise="pushup",
        message="분석 작업이 시작되었습니다. GET /api/v1/analyze/{analysisId}로 결과를 조회하세요.",
    )


@router.get("/{analysis_id}", response_model=AnalysisStatusResponse)
def get_analysis(analysis_id: str) -> AnalysisStatusResponse:
    record = analysis_repository.get(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="분석 ID를 찾을 수 없습니다.")
    return AnalysisStatusResponse(**record)


@router.get("/{analysis_id}/shortform", response_model=ShortformResponse)
def get_shortform(analysis_id: str) -> ShortformResponse:
    record = analysis_repository.get(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="분석 ID를 찾을 수 없습니다.")
    if record.get("status") == "failed":
        raise HTTPException(status_code=409, detail="분석이 실패하여 숏폼을 제공할 수 없습니다.")

    shortform_url = record.get("shortformUrl")
    if not shortform_url:
        return ShortformResponse(analysisId=analysis_id, status=record["status"], shortformUrl=None)
    return ShortformResponse(analysisId=analysis_id, status=record["status"], shortformUrl=shortform_url)
