from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


GuitarType = Literal["Strat", "Les Paul", "Tele", "Super Strat", "Other"]
Archetype = Literal[
    "clean",
    "edge_of_breakup",
    "crunch",
    "high_gain",
    "fuzz",
    "ambient_lead",
]


class AnalysisRequest(BaseModel):
    guitar_type: GuitarType
    start_sec: float = Field(ge=0, le=600)
    end_sec: float = Field(gt=0, le=600)
    source_url: HttpUrl | None = None


class AudioFeatures(BaseModel):
    rms_mean: float
    rms_std: float
    spectral_centroid_mean: float
    spectral_rolloff_mean: float
    spectral_flatness_mean: float
    zcr_mean: float
    harmonic_ratio: float
    percussive_ratio: float
    onset_strength_mean: float
    sustain_proxy: float
    low_band_ratio: float
    mid_band_ratio: float
    high_band_ratio: float
    distortion_score: float
    ambience_score: float
    dynamic_range: float
    mix_likelihood: float


class AbstractToneProfile(BaseModel):
    gain_level: float = Field(ge=0, le=1)
    brightness: float = Field(ge=0, le=1)
    mid_push: float = Field(ge=0, le=1)
    tightness: float = Field(ge=0, le=1)
    compression: float = Field(ge=0, le=1)
    space: float = Field(ge=0, le=1)
    modulation: float = Field(ge=0, le=1)
    fuzziness: float = Field(ge=0, le=1)
    attack: float = Field(ge=0, le=1)
    sustain: float = Field(ge=0, le=1)
    tags: list[str] = Field(default_factory=list)


class ChainBlock(BaseModel):
    type: str
    device: str
    settings: dict[str, str]
    rationale: str


class ChainRecommendation(BaseModel):
    name: str
    summary: str
    blocks: list[ChainBlock]


class AnalysisResult(BaseModel):
    archetype: Archetype
    tonal_summary: str
    tone_profile: AbstractToneProfile
    primary_chain: ChainRecommendation
    alternative_chains: list[ChainRecommendation]
    explanation: str
    warnings: list[str]
    confidence_label: str
