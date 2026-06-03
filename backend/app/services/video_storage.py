from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.utils.file_utils import secure_extension


async def save_upload_file(file: UploadFile) -> tuple[str, Path]:
    ext = secure_extension(file.filename or "")
    analysis_id = f"pushup_{uuid4().hex[:12]}"
    target_path = settings.uploads_dir / f"{analysis_id}{ext}"

    size = 0
    with target_path.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            out.write(chunk)

    if size == 0:
        target_path.unlink(missing_ok=True)
        raise ValueError("빈 영상 파일은 업로드할 수 없습니다.")

    return analysis_id, target_path
