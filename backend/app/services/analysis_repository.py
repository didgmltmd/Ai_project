import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import settings


class SqliteAnalysisRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    exercise TEXT,
                    video_path TEXT,
                    progress_stage TEXT,
                    progress_percent INTEGER,
                    current_frame INTEGER,
                    total_frames INTEGER,
                    rep_count INTEGER,
                    total_score INTEGER,
                    metrics_json TEXT,
                    issues_json TEXT,
                    rep_issues_json TEXT,
                    feedback_json TEXT,
                    report_json TEXT,
                    shortform_url TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analyses_feed
                ON analyses(status, updated_at DESC)
                """
            )
            self._ensure_columns(conn)

    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)").fetchall()}
        migrations = {
            "progress_stage": "ALTER TABLE analyses ADD COLUMN progress_stage TEXT",
            "progress_percent": "ALTER TABLE analyses ADD COLUMN progress_percent INTEGER",
            "current_frame": "ALTER TABLE analyses ADD COLUMN current_frame INTEGER",
            "total_frames": "ALTER TABLE analyses ADD COLUMN total_frames INTEGER",
            "feedback_json": "ALTER TABLE analyses ADD COLUMN feedback_json TEXT",
        }
        for column, statement in migrations.items():
            if column not in existing:
                conn.execute(statement)

    def create(self, analysis_id: str, exercise: str, video_path: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analyses (
                    analysis_id, status, exercise, video_path, created_at, updated_at
                ) VALUES (?, 'processing', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (analysis_id, exercise, video_path),
            )

    def get(self, analysis_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM analyses WHERE analysis_id = ?",
                (analysis_id,),
            ).fetchone()
        return self._row_to_analysis(row) if row else None

    def list_feed(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM analyses
                WHERE status = 'completed'
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_feed(row) for row in rows]

    def update(self, analysis_id: str, **fields: Any) -> None:
        allowed_columns = {
            "status": "status",
            "exercise": "exercise",
            "videoPath": "video_path",
            "progressStage": "progress_stage",
            "progressPercent": "progress_percent",
            "currentFrame": "current_frame",
            "totalFrames": "total_frames",
            "repCount": "rep_count",
            "totalScore": "total_score",
            "metrics": "metrics_json",
            "issues": "issues_json",
            "repIssues": "rep_issues_json",
            "feedback": "feedback_json",
            "report": "report_json",
            "shortformUrl": "shortform_url",
            "error": "error",
        }
        json_fields = {"metrics", "issues", "repIssues", "feedback", "report"}
        assignments: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            column = allowed_columns.get(key)
            if column is None:
                continue
            assignments.append(f"{column} = ?")
            values.append(json.dumps(value, ensure_ascii=False) if key in json_fields else value)

        if not assignments:
            return

        assignments.append("updated_at = CURRENT_TIMESTAMP")
        values.append(analysis_id)
        with self._lock, self._connect() as conn:
            conn.execute(
                f"UPDATE analyses SET {', '.join(assignments)} WHERE analysis_id = ?",
                values,
            )

    def _row_to_analysis(self, row: sqlite3.Row) -> dict[str, Any]:
        feedback = self._json_or_none(row["feedback_json"]) or self._json_or_none(row["report_json"])
        report = self._json_or_none(row["report_json"]) or self._feedback_to_report(feedback)
        return {
            "analysisId": row["analysis_id"],
            "status": row["status"],
            "exercise": row["exercise"],
            "progressStage": row["progress_stage"],
            "progressPercent": row["progress_percent"],
            "currentFrame": row["current_frame"],
            "totalFrames": row["total_frames"],
            "repCount": row["rep_count"],
            "totalScore": row["total_score"],
            "metrics": self._json_or_none(row["metrics_json"]),
            "issues": self._json_or_none(row["issues_json"]),
            "repIssues": self._json_or_none(row["rep_issues_json"]),
            "feedback": feedback,
            "report": report,
            "shortformUrl": row["shortform_url"],
            "error": row["error"],
        }

    def _row_to_feed(self, row: sqlite3.Row) -> dict[str, Any]:
        feedback = self._json_or_none(row["feedback_json"]) or self._json_or_none(row["report_json"]) or {}
        return {
            "analysisId": row["analysis_id"],
            "userName": "me",
            "profileInitial": "M",
            "uploadedAt": row["updated_at"],
            "exerciseType": row["exercise"] or "pushup",
            "repCount": row["rep_count"] or 0,
            "score": row["total_score"] or 0,
            "summaryFeedback": feedback.get("summary") or "AI 분석이 완료되었습니다.",
            "caption": "푸시업 AI 자세 분석",
            "hashtags": ["#푸시업", "#AI자세분석", "#운동기록"],
            "likeCount": 0,
            "commentCount": 0,
            "liked": False,
            "videoUrl": row["shortform_url"],
        }

    @staticmethod
    def _json_or_none(value: str | None) -> Any:
        if value is None:
            return None
        return json.loads(value)

    @staticmethod
    def _feedback_to_report(feedback: dict[str, Any] | None) -> dict[str, Any] | None:
        if feedback is None:
            return None
        return {
            "summary": feedback.get("summary", ""),
            "strengths": feedback.get("good") or feedback.get("strengths") or [],
            "improvements": feedback.get("improvements", []),
            "coaching": feedback.get("coaching", ""),
        }


analysis_repository = SqliteAnalysisRepository(settings.database_path)
