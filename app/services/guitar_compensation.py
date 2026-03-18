from __future__ import annotations

from app.schemas.analysis import AbstractToneProfile


class GuitarCompensationService:
    def apply(self, profile: AbstractToneProfile, guitar_type: str) -> AbstractToneProfile:
        updated = profile.model_copy(deep=True)
        if guitar_type == "Strat":
            updated.brightness = min(1.0, updated.brightness + 0.05)
            updated.mid_push = max(0.0, updated.mid_push - 0.04)
        elif guitar_type == "Les Paul":
            updated.gain_level = max(0.0, updated.gain_level - 0.05)
            updated.brightness = max(0.0, updated.brightness - 0.06)
            updated.sustain = min(1.0, updated.sustain + 0.05)
        elif guitar_type == "Tele":
            updated.attack = min(1.0, updated.attack + 0.06)
            updated.brightness = min(1.0, updated.brightness + 0.07)
        elif guitar_type == "Super Strat":
            updated.gain_level = max(0.0, updated.gain_level - 0.03)
            updated.tightness = min(1.0, updated.tightness + 0.05)
            updated.compression = min(1.0, updated.compression + 0.03)
        updated.tags.append(f"compensated_for_{guitar_type.lower().replace(' ', '_')}")
        return updated
