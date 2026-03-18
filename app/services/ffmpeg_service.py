from __future__ import annotations

import json
import subprocess
from pathlib import Path

from fastapi import HTTPException

from app.config import settings


class FFmpegService:
    def probe_duration(self, file_path: Path) -> float:
        command = [
            settings.ffprobe_binary,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(file_path),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            payload = json.loads(result.stdout)
            return float(payload["format"]["duration"])
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail="ffprobe is not installed or not available on PATH.") from exc
        except (subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail="Could not inspect audio file duration.") from exc

    def trim_and_normalize(self, source_path: Path, output_path: Path, start_sec: float, end_sec: float, sample_rate: int) -> Path:
        duration = max(end_sec - start_sec, 0.01)
        command = [
            settings.ffmpeg_binary,
            "-y",
            "-ss",
            f"{start_sec:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(source_path),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            str(output_path),
        ]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail="FFmpeg is not installed or not available on PATH.") from exc
        except subprocess.CalledProcessError as exc:
            raise HTTPException(status_code=400, detail="FFmpeg failed to trim or normalize the selected segment.") from exc
        return output_path
