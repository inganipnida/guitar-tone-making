from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.schemas.analysis import AnalysisResult
from app.services.audio_preprocess import AudioPreprocessor
from app.services.feature_extractor import FeatureExtractor
from app.services.guitar_compensation import GuitarCompensationService
from app.services.qc_mapper import QuadCortexMapper
from app.services.tone_classifier import ToneClassifier


class AnalysisPipeline:
    def __init__(self) -> None:
        self.preprocessor = AudioPreprocessor()
        self.extractor = FeatureExtractor()
        self.classifier = ToneClassifier()
        self.guitar_comp = GuitarCompensationService()
        self.mapper = QuadCortexMapper(settings.data_dir)

    def run(self, file_path: Path, guitar_type: str) -> tuple[AnalysisResult, dict[str, object]]:
        audio, sr = self.preprocessor.load_audio(file_path, settings.sample_rate)
        features = self.extractor.extract(audio, sr)
        archetype, profile, warnings, confidence_label = self.classifier.classify(features)
        compensated_profile = self.guitar_comp.apply(profile, guitar_type)
        primary, alternatives, tonal_summary, explanation = self.mapper.recommend(archetype, compensated_profile)
        result = AnalysisResult(
            archetype=archetype,
            tonal_summary=tonal_summary,
            tone_profile=compensated_profile,
            primary_chain=primary,
            alternative_chains=alternatives,
            explanation=explanation,
            warnings=warnings,
            confidence_label=confidence_label,
        )
        return result, {"features": features.model_dump(), "raw_profile": profile.model_dump()}
