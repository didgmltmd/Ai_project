from pathlib import Path

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi"}


def secure_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError("지원하지 않는 영상 확장자입니다. mp4, mov, m4v, avi만 허용합니다.")
    return ext
