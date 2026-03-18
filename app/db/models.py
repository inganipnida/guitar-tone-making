from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AnalysisRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_filename: str
    stored_filename: str
    processed_filename: str
    input_mode: str = "upload"
    source_url: Optional[str] = None
    guitar_type: str
    start_sec: float
    end_sec: float
    duration_sec: float
    archetype: str
    tonal_summary: str
    confidence_label: str
    warnings_json: str
    feature_json: str
    tone_profile_json: str
    recommendation_json: str
    explanation: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
