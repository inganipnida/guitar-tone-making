from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np


class AudioPreprocessor:
    def load_audio(self, file_path: Path, sample_rate: int) -> tuple[np.ndarray, int]:
        audio, sr = librosa.load(file_path, sr=sample_rate, mono=True)
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
        return audio.astype(np.float32), sr
