from __future__ import annotations

import json
from pathlib import Path

from app.schemas.analysis import AbstractToneProfile, ChainBlock, ChainRecommendation


class QuadCortexMapper:
    def __init__(self, data_dir: Path) -> None:
        self.devices = self._load_json(data_dir / "qc_devices.json")
        self.rules = self._load_json(data_dir / "qc_rules.json")

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def recommend(self, archetype: str, profile: AbstractToneProfile) -> tuple[ChainRecommendation, list[ChainRecommendation], str, str]:
        primary = self._build_chain("primary", archetype, profile)
        alternatives = [
            self._build_chain("alternative_1", archetype, profile),
            self._build_chain("alternative_2", archetype, profile),
            self._build_chain("alternative_3", archetype, profile),
        ]
        tonal_summary = self._summarize(profile, archetype)
        explanation = self._explain(profile, archetype)
        return primary, alternatives, tonal_summary, explanation

    def _build_chain(self, variant: str, archetype: str, profile: AbstractToneProfile) -> ChainRecommendation:
        presets = self.rules[archetype][variant]
        blocks: list[ChainBlock] = []
        for block in presets:
            settings = self._resolve_settings(block["type"], profile)
            blocks.append(
                ChainBlock(
                    type=block["type"],
                    device=block["device"],
                    settings=settings,
                    rationale=block["rationale"],
                )
            )
        return ChainRecommendation(name=presets[0]["chain_name"], summary=presets[0]["chain_summary"], blocks=blocks)

    def _resolve_settings(self, block_type: str, profile: AbstractToneProfile) -> dict[str, str]:
        if block_type == "gate":
            return {"threshold": f"{20 + profile.gain_level * 35:.0f}-{25 + profile.gain_level * 40:.0f}%", "release": "90-150 ms"}
        if block_type == "comp":
            return {"sustain": f"{20 + profile.compression * 45:.0f}-{30 + profile.compression * 50:.0f}%", "mix": "55-75%"}
        if block_type == "drive":
            return {"drive": f"{10 + profile.gain_level * 60:.0f}-{18 + profile.gain_level * 68:.0f}%", "tone": f"{40 + profile.brightness * 30:.0f}-{48 + profile.brightness * 30:.0f}%"}
        if block_type == "amp":
            return {
                "gain": f"{25 + profile.gain_level * 55:.0f}-{35 + profile.gain_level * 58:.0f}%",
                "bass": f"{35 + (1-profile.tightness) * 20:.0f}-{42 + (1-profile.tightness) * 18:.0f}%",
                "mid": f"{35 + profile.mid_push * 30:.0f}-{42 + profile.mid_push * 28:.0f}%",
                "treble": f"{35 + profile.brightness * 30:.0f}-{42 + profile.brightness * 26:.0f}%",
                "presence": f"{30 + profile.attack * 35:.0f}-{38 + profile.attack * 30:.0f}%",
            }
        if block_type == "cab":
            return {"mic_blend": "dynamic + ribbon", "low_cut": "75-110 Hz", "high_cut": f"{5200 + profile.brightness * 1800:.0f}-{6500 + profile.brightness * 1500:.0f} Hz"}
        if block_type == "eq":
            return {"low_cut": "70-100 Hz", "mid_focus": "650 Hz-1.6 kHz", "high_shelf": "+/- 1.5 to 3 dB"}
        if block_type == "mod":
            return {"depth": f"{10 + profile.modulation * 30:.0f}-{18 + profile.modulation * 35:.0f}%", "mix": "8-20%"}
        if block_type == "delay":
            return {"time": "360-520 ms", "feedback": f"{18 + profile.space * 25:.0f}-{24 + profile.space * 28:.0f}%", "mix": "12-24%"}
        if block_type == "reverb":
            return {"decay": f"{1.2 + profile.space * 3.8:.1f}-{1.8 + profile.space * 4.2:.1f} s", "mix": f"{8 + profile.space * 24:.0f}-{12 + profile.space * 28:.0f}%"}
        return {"note": "Use ears and context to fine-tune."}

    def _summarize(self, profile: AbstractToneProfile, archetype: str) -> str:
        return (
            f"{archetype.replace('_', ' ').title()} leaning tone with {self._describe(profile.brightness, 'brightness')} , "
            f"{self._describe(profile.mid_push, 'mid focus')}, {self._describe(profile.tightness, 'tightness')}, "
            f"and {self._describe(profile.space, 'space')}."
        ).replace("  ", " ")

    def _explain(self, profile: AbstractToneProfile, archetype: str) -> str:
        return (
            f"This recommendation aims for the closest playable Quad Cortex starting point rather than a perfect clone. "
            f"The segment reads as {archetype.replace('_', ' ')}, with gain around {profile.gain_level:.2f}, "
            f"brightness around {profile.brightness:.2f}, mid push around {profile.mid_push:.2f}, and space around {profile.space:.2f}. "
            f"That combination points toward an amp-and-cab core with support blocks chosen to shape attack, sustain, and ambience transparently."
        )

    @staticmethod
    def _describe(value: float, label: str) -> str:
        if value < 0.33:
            return f"lower {label}"
        if value < 0.66:
            return f"balanced {label}"
        return f"higher {label}"
