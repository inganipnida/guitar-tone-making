from __future__ import annotations

import numpy as np
import librosa

from app.schemas.analysis import AudioFeatures


class FeatureExtractor:
    def extract(self, audio: np.ndarray, sr: int) -> AudioFeatures:
        rms = librosa.feature.rms(y=audio)[0]
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        flatness = librosa.feature.spectral_flatness(y=audio)[0]
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        harmonic, percussive = librosa.effects.hpss(audio)
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)

        stft = np.abs(librosa.stft(audio))
        freqs = librosa.fft_frequencies(sr=sr)
        power = stft.mean(axis=1) + 1e-8

        low = power[(freqs >= 20) & (freqs < 180)].sum()
        mid = power[(freqs >= 180) & (freqs < 2000)].sum()
        high = power[(freqs >= 2000) & (freqs < 8000)].sum()
        total = low + mid + high

        harmonic_energy = np.mean(np.abs(harmonic)) + 1e-8
        percussive_energy = np.mean(np.abs(percussive)) + 1e-8

        distortion_score = float(np.clip((flatness.mean() * 1.8) + (zcr.mean() * 5.0), 0, 1))
        ambience_score = float(np.clip((rolloff.mean() / max(sr, 1)) + (np.std(rms) * 2.5), 0, 1))
        sustain_proxy = float(np.clip(np.mean(rms) / (np.mean(onset_env) + 1e-6), 0, 5)) / 5
        dynamic_range = float(np.percentile(rms, 95) - np.percentile(rms, 10))
        mix_likelihood = float(
            np.clip(
                0.35 * (low / total if total else 0)
                + 0.25 * (percussive_energy / (harmonic_energy + percussive_energy))
                + 0.40 * (np.std(onset_env) > np.mean(onset_env)),
                0,
                1,
            )
        )

        return AudioFeatures(
            rms_mean=float(rms.mean()),
            rms_std=float(rms.std()),
            spectral_centroid_mean=float(centroid.mean()),
            spectral_rolloff_mean=float(rolloff.mean()),
            spectral_flatness_mean=float(flatness.mean()),
            zcr_mean=float(zcr.mean()),
            harmonic_ratio=float(harmonic_energy / (harmonic_energy + percussive_energy)),
            percussive_ratio=float(percussive_energy / (harmonic_energy + percussive_energy)),
            onset_strength_mean=float(onset_env.mean()),
            sustain_proxy=float(sustain_proxy),
            low_band_ratio=float(low / total) if total else 0.0,
            mid_band_ratio=float(mid / total) if total else 0.0,
            high_band_ratio=float(high / total) if total else 0.0,
            distortion_score=distortion_score,
            ambience_score=ambience_score,
            dynamic_range=dynamic_range,
            mix_likelihood=mix_likelihood,
        )
