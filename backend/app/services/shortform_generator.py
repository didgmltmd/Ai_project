from pathlib import Path
import shutil

from app.core.config import settings


def generate_shortform(analysis_id: str, source_video_path: Path, result: dict) -> str:
    target_path = settings.shortforms_dir / f"{analysis_id}{source_video_path.suffix or '.mp4'}"
    shutil.copyfile(source_video_path, target_path)
    return f"/media/shortforms/{target_path.name}"
