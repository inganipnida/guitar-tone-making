from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, desc, select
from werkzeug.utils import secure_filename

from app.config import APP_DIR, settings
from app.db.database import get_session
from app.db.models import AnalysisRecord
from app.services.analysis_pipeline import AnalysisPipeline
from app.services.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
pipeline = AnalysisPipeline()
ffmpeg_service = FFmpegService()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "error": None,
            "form": {},
            "max_segment_length_sec": settings.max_segment_length_sec,
        },
    )


@router.get("/history", response_class=HTMLResponse)
def history(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    records = session.exec(
        select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(settings.recent_history_limit)
    ).all()
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "records": records, "history_limit": settings.recent_history_limit},
    )


@router.get("/result/{analysis_id}", response_class=HTMLResponse)
def result(request: Request, analysis_id: int, session: Session = Depends(get_session)) -> HTMLResponse:
    record = session.get(AnalysisRecord, analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    features = json.loads(record.feature_json)
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "record": record,
            "tone_profile": json.loads(record.tone_profile_json),
            "recommendation": json.loads(record.recommendation_json),
            "features": features,
            "warnings": json.loads(record.warnings_json),
            "mix_flag": features.get("mix_likelihood", 0) > 0.55,
        },
    )


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    audio_file: UploadFile | None = File(default=None),
    source_url: str = Form(default=""),
    start_sec: float = Form(default=0.0),
    end_sec: float = Form(default=10.0),
    guitar_type: str = Form(default="Strat"),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    form_state = {"start_sec": start_sec, "end_sec": end_sec, "guitar_type": guitar_type, "source_url": source_url}
    try:
        if start_sec < 0 or end_sec <= start_sec:
            raise HTTPException(status_code=400, detail="End time must be greater than start time.")
        if end_sec - start_sec > settings.max_segment_length_sec:
            raise HTTPException(
                status_code=400,
                detail=f"Please keep the analysis segment at or below {settings.max_segment_length_sec:.0f} seconds for this MVP.",
            )
        if not audio_file or not audio_file.filename:
            raise HTTPException(status_code=400, detail="Please upload an audio file for this MVP.")

        original_name = secure_filename(Path(audio_file.filename).name)
        extension = Path(original_name).suffix.lower()
        if extension not in settings.allowed_extensions:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        content = await audio_file.read()
        if len(content) > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb} MB limit.")

        stored_name = f"{uuid.uuid4().hex}{extension}"
        source_path = settings.upload_dir / stored_name
        source_path.write_bytes(content)

        duration = ffmpeg_service.probe_duration(source_path)
        if end_sec > duration:
            raise HTTPException(status_code=400, detail=f"End time exceeds file duration ({duration:.2f} s).")

        processed_name = f"{source_path.stem}_segment.wav"
        processed_path = settings.upload_dir / processed_name
        ffmpeg_service.trim_and_normalize(source_path, processed_path, start_sec, end_sec, settings.sample_rate)

        result_payload, debug_payload = pipeline.run(processed_path, guitar_type)
        record = AnalysisRecord(
            source_filename=original_name,
            stored_filename=stored_name,
            processed_filename=processed_name,
            input_mode="upload",
            source_url=source_url or None,
            guitar_type=guitar_type,
            start_sec=start_sec,
            end_sec=end_sec,
            duration_sec=end_sec - start_sec,
            archetype=result_payload.archetype,
            tonal_summary=result_payload.tonal_summary,
            confidence_label=result_payload.confidence_label,
            warnings_json=json.dumps(result_payload.warnings),
            feature_json=json.dumps(debug_payload["features"]),
            tone_profile_json=json.dumps(result_payload.tone_profile.model_dump()),
            recommendation_json=json.dumps(
                {
                    "primary": result_payload.primary_chain.model_dump(),
                    "alternatives": [chain.model_dump() for chain in result_payload.alternative_chains],
                }
            ),
            explanation=result_payload.explanation,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return RedirectResponse(url=f"/result/{record.id}", status_code=303)
    except HTTPException as exc:
        logger.warning("Validation error during analysis: %s", exc.detail)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": exc.detail,
                "form": form_state,
                "max_segment_length_sec": settings.max_segment_length_sec,
            },
            status_code=exc.status_code,
        )
    except Exception:
        logger.exception("Unexpected error during analysis")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Unexpected error while analyzing audio. Please verify the Python dependencies and FFmpeg are installed, then try again.",
                "form": form_state,
                "max_segment_length_sec": settings.max_segment_length_sec,
            },
            status_code=500,
        )
