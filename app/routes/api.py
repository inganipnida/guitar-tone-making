from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.config import settings
from app.db.database import get_session
from app.db.models import AnalysisRecord

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "history_limit": settings.recent_history_limit}


@router.get("/analyses")
def analyses(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    records = session.exec(
        select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(settings.recent_history_limit)
    ).all()
    return [serialize_record(record) for record in records]


@router.get("/analyses/{analysis_id}")
def analysis_detail(analysis_id: int, session: Session = Depends(get_session)) -> dict[str, object]:
    record = session.get(AnalysisRecord, analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return serialize_record(record)



def serialize_record(record: AnalysisRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "source_filename": record.source_filename,
        "processed_filename": record.processed_filename,
        "input_mode": record.input_mode,
        "source_url": record.source_url,
        "guitar_type": record.guitar_type,
        "start_sec": record.start_sec,
        "end_sec": record.end_sec,
        "duration_sec": record.duration_sec,
        "archetype": record.archetype,
        "tonal_summary": record.tonal_summary,
        "confidence_label": record.confidence_label,
        "warnings": json.loads(record.warnings_json),
        "features": json.loads(record.feature_json),
        "tone_profile": json.loads(record.tone_profile_json),
        "recommendation": json.loads(record.recommendation_json),
        "explanation": record.explanation,
        "created_at": record.created_at.isoformat(),
    }
