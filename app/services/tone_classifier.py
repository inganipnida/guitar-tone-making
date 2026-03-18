from __future__ import annotations

from app.schemas.analysis import AbstractToneProfile, AudioFeatures


class ToneClassifier:
    def classify(self, features: AudioFeatures) -> tuple[str, AbstractToneProfile, list[str], str]:
        warnings: list[str] = []
        gain_level = self._clamp((features.distortion_score * 0.55) + (features.rms_mean * 0.65) + (features.zcr_mean * 1.8))
        brightness = self._clamp((features.spectral_centroid_mean / 3500) * 0.6 + (features.high_band_ratio * 0.7))
        mid_push = self._clamp(features.mid_band_ratio * 1.2)
        tightness = self._clamp((features.onset_strength_mean / 8.0) * 0.55 + (1 - features.low_band_ratio) * 0.45)
        compression = self._clamp((1 - min(features.dynamic_range / 0.25, 1)) * 0.6 + features.rms_mean * 0.4)
        space = self._clamp(features.ambience_score * 0.8 + (1 - features.harmonic_ratio) * 0.2)
        modulation = self._clamp(max(0.0, space - 0.45) * 0.6)
        fuzziness = self._clamp(features.distortion_score * 0.7 + features.spectral_flatness_mean * 0.7 - tightness * 0.25)
        attack = self._clamp((features.onset_strength_mean / 10.0) * 0.7 + (1 - features.sustain_proxy) * 0.3)
        sustain = self._clamp(features.sustain_proxy * 0.65 + compression * 0.35)

        if features.mix_likelihood > 0.55:
            gain_level *= 0.88
            tightness *= 0.9
            warnings.append("Source appears to include a fuller mix, so gain and tightness estimates were de-emphasized.")
        if features.percussive_ratio > 0.55:
            warnings.append("Strong percussive content was detected; pick attack-related suggestions as a starting point only.")

        if fuzziness > 0.72 and gain_level > 0.52:
            archetype = "fuzz"
        elif space > 0.68 and sustain > 0.58 and gain_level > 0.35:
            archetype = "ambient_lead"
        elif gain_level > 0.72:
            archetype = "high_gain"
        elif gain_level > 0.52:
            archetype = "crunch"
        elif gain_level > 0.3:
            archetype = "edge_of_breakup"
        else:
            archetype = "clean"

        tags: list[str] = []
        tags.append("bright" if brightness >= 0.55 else "dark")
        tags.append("mid_forward" if mid_push >= 0.52 else "scooped")
        tags.append("tight" if tightness >= 0.55 else "loose")
        if space < 0.3:
            tags.append("dry")
        elif space < 0.6:
            tags.append("roomy")
        else:
            tags.append("washed")
        tags.append("smooth" if compression >= 0.55 else "aggressive")

        profile = AbstractToneProfile(
            gain_level=self._clamp(gain_level),
            brightness=self._clamp(brightness),
            mid_push=self._clamp(mid_push),
            tightness=self._clamp(tightness),
            compression=self._clamp(compression),
            space=self._clamp(space),
            modulation=self._clamp(modulation),
            fuzziness=self._clamp(fuzziness),
            attack=self._clamp(attack),
            sustain=self._clamp(sustain),
            tags=tags,
        )
        confidence_label = "medium"
        if features.mix_likelihood < 0.3 and features.harmonic_ratio > 0.55:
            confidence_label = "high"
        elif features.mix_likelihood > 0.65:
            confidence_label = "low"
            warnings.append("Confidence is lower because the source behaves more like a mixed production than an isolated guitar stem.")
        return archetype, profile, warnings, confidence_label

    @staticmethod
    def _clamp(value: float) -> float:
        return float(max(0.0, min(1.0, value)))
