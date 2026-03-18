from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.db.database import get_session
from app.db.models import AnalysisRecord

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/analyses")
def analyses(session: Session = Depends(get_session)) -> list[AnalysisRecord]:
    return list(session.exec(select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(20)).all())


@router.get("/analyses/{analysis_id}")
def analysis_detail(analysis_id: int, session: Session = Depends(get_session)) -> AnalysisRecord:
    record = session.get(AnalysisRecord, analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return record
