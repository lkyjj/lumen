"""Typed contracts shared by every LUMEN agent.

The models in this module are deliberately strict: a pipeline should fail at the
boundary where invalid data appears, not several paid calls later.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    """Base contract that rejects accidental or misspelled fields."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class FilmInfo(Contract):
    title: str
    title_en: str
    logline: str
    duration_target: float = Field(gt=0)
    title_cards_duration: float = Field(default=0, ge=0)
    aspect_ratio: str = "16:9"
    resolution: Literal["480P", "720P", "1080P"] = "720P"
    language: str = "zh-CN"


class StyleConfig(Contract):
    look: str
    palette: list[str] = Field(default_factory=list)
    camera: str
    forbidden: list[str] = Field(default_factory=list)


class CastMember(Contract):
    id: str
    name: str
    anchor_prompt: str
    anchor_image: str | None = None


class Location(Contract):
    id: str
    name: str
    anchor_prompt: str
    anchor_image: str | None = None


class VisualAnchor(Contract):
    id: str
    image: str
    prompt: str
    source_cast: str | None = None
    source_location: str | None = None
    approved: bool = False


class PricingConfig(Contract):
    """Configurable list prices; discounts must be confirmed outside the code."""

    video_cny_per_second: dict[str, dict[str, float]] = Field(
        default_factory=lambda: {
            "wan3.0-video": {"480P": 0.30, "720P": 0.60, "1080P": 1.20},
            "wan2.7-i2v-2026-04-25": {"720P": 0.60},
            "wan2.6-i2v-flash": {"720P": 0.15},
        }
    )
    image_cny_each: float = Field(default=0.20, ge=0)
    tts_cny_per_10k_characters: dict[str, float] = Field(
        default_factory=lambda: {
            "cosyvoice-v3-flash": 1.0,
            "cosyvoice-v3-plus": 2.0,
            "cosyvoice-v3.5-plus": 1.5,
        }
    )
    discount_multiplier: float = Field(default=1.0, gt=0, le=1)


class BudgetConfig(Contract):
    currency: Literal["CNY"] = "CNY"
    hard_cap: float = Field(default=300, gt=0)
    warn_at: float = Field(default=200, ge=0)
    video_model: str = "wan3.0-video"
    stable_video_model: str = "wan2.7-i2v-2026-04-25"
    fallback_video_model: str = "wan2.6-i2v-flash"
    image_model: str = "wan2.6-t2i"
    tts_model: str = "cosyvoice-v3-flash"
    pricing: PricingConfig = Field(default_factory=PricingConfig)

    @model_validator(mode="after")
    def warning_must_precede_cap(self) -> BudgetConfig:
        if self.warn_at > self.hard_cap:
            raise ValueError("budget.warn_at must not exceed budget.hard_cap")
        return self


class QualityGate(Contract):
    min_score: float = Field(default=7.0, ge=1, le=10)
    min_dimension_score: float = Field(default=6.0, ge=1, le=10)
    max_retries: int = Field(default=2, ge=0, le=10)
    dimensions: list[str] = Field(
        default_factory=lambda: [
            "角色一致性",
            "构图符合分镜",
            "光线氛围",
            "无明显崩坏",
        ]
    )


class ShotAudio(Contract):
    voice: str | None = None
    voice_role: Literal["system", "human"] = "system"
    sfx: list[str] = Field(default_factory=list)
    music: str | None = None


ReferenceType = Literal[
    "first_frame",
    "last_frame",
    "reference_image",
    "reference_video",
    "reference_audio",
    "file",
    "link",
]


class Shot(Contract):
    id: str
    duration: float = Field(gt=0, le=30)
    size: str
    movement: str
    anchor: str | None = None
    reference_type: ReferenceType | None = None
    cast: list[str] = Field(default_factory=list)
    location: str
    intent: str
    prompt_seed: str
    audio: ShotAudio = Field(default_factory=ShotAudio)

    @model_validator(mode="after")
    def anchor_has_reference_type(self) -> Shot:
        if self.anchor and not self.reference_type:
            self.reference_type = "first_frame"
        if not self.anchor and self.reference_type:
            raise ValueError(f"{self.id}: reference_type requires an anchor")
        return self


class FilmProject(Contract):
    film: FilmInfo
    style: StyleConfig
    cast: list[CastMember]
    locations: list[Location]
    anchors: list[VisualAnchor]
    budget: BudgetConfig
    quality_gate: QualityGate
    shots: list[Shot]

    @model_validator(mode="after")
    def validate_references_and_duration(self) -> FilmProject:
        cast_ids = [member.id for member in self.cast]
        location_ids = [location.id for location in self.locations]
        anchor_ids = [anchor.id for anchor in self.anchors]
        shot_ids = [shot.id for shot in self.shots]
        for name, values in (
            ("cast", cast_ids),
            ("locations", location_ids),
            ("anchors", anchor_ids),
            ("shots", shot_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {name} id")

        for shot in self.shots:
            missing_cast = sorted(set(shot.cast) - set(cast_ids))
            if missing_cast:
                raise ValueError(f"{shot.id}: unknown cast ids: {missing_cast}")
            if shot.location not in location_ids:
                raise ValueError(f"{shot.id}: unknown location id: {shot.location}")
            if shot.anchor and shot.anchor not in anchor_ids:
                raise ValueError(f"{shot.id}: unknown anchor id: {shot.anchor}")

        for anchor in self.anchors:
            if anchor.source_cast and anchor.source_cast not in cast_ids:
                raise ValueError(f"{anchor.id}: unknown source_cast: {anchor.source_cast}")
            if anchor.source_location and anchor.source_location not in location_ids:
                raise ValueError(
                    f"{anchor.id}: unknown source_location: {anchor.source_location}"
                )

        total = sum(shot.duration for shot in self.shots) + self.film.title_cards_duration
        if abs(total - self.film.duration_target) > 0.01:
            raise ValueError(
                "film.duration_target must equal shot durations plus title_cards_duration "
                f"({self.film.duration_target} != {total})"
            )
        return self

    @property
    def shots_duration(self) -> float:
        return sum(shot.duration for shot in self.shots)


class ScriptBeat(Contract):
    shot_id: str
    action: str
    visual: str
    sound: str
    dialogue: str | None = None


class Script(Contract):
    title: str
    logline: str
    beats: list[ScriptBeat]


class CriticScores(Contract):
    character_consistency: float = Field(ge=1, le=10)
    composition: float = Field(ge=1, le=10)
    lighting: float = Field(ge=1, le=10)
    integrity: float = Field(ge=1, le=10)

    @property
    def average(self) -> float:
        return round(
            (
                self.character_consistency
                + self.composition
                + self.lighting
                + self.integrity
            )
            / 4,
            2,
        )


class CriticVerdict(Contract):
    scores: CriticScores
    overall: float = Field(ge=1, le=10)
    passed: bool
    critique: str
    fix_hint: str

    @classmethod
    def adjudicate(
        cls,
        *,
        scores: CriticScores,
        critique: str,
        fix_hint: str,
        gate: QualityGate,
    ) -> CriticVerdict:
        overall = scores.average
        lowest = min(
            scores.character_consistency,
            scores.composition,
            scores.lighting,
            scores.integrity,
        )
        return cls(
            scores=scores,
            overall=overall,
            passed=overall >= gate.min_score and lowest >= gate.min_dimension_score,
            critique=critique,
            fix_hint=fix_hint,
        )


class ShotResult(Contract):
    shot_id: str
    clip_path: str
    attempt: int = Field(ge=1)
    score: float = Field(ge=1, le=10)
    critique: str
    cost_cny: float = Field(ge=0)
    passed: bool


class RunEvent(Contract):
    timestamp: datetime
    event: str
    agent: str
    status: Literal["started", "succeeded", "failed", "skipped", "simulated"]
    model: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    cost_cny: float = Field(default=0, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)


class BudgetState(Contract):
    spent_cny: float = Field(default=0, ge=0)
    reserved_cny: float = Field(default=0, ge=0)
    remaining_cny: float = Field(ge=0)
    hard_cap_cny: float = Field(gt=0)
    warning_reached: bool = False


class DagStep(Contract):
    id: str
    agent: str
    depends_on: list[str] = Field(default_factory=list)
    model: str | None = None
    output: str | None = None
    estimated_cost_cny: float = Field(default=0, ge=0)
    worst_case_cost_cny: float = Field(default=0, ge=0)
    paid: bool = False


class PipelineState(Contract):
    config_sha256: str
    steps: dict[str, Literal["pending", "running", "succeeded", "failed", "skipped"]]
    needs_human_review: list[str] = Field(default_factory=list)
    updated_at: datetime


class ProjectPaths(Contract):
    root: Path
    config: Path
    script: Path
    shots: Path
    bible: Path
    clips: Path
    audio: Path
    cut: Path
    run_log: Path
    state: Path
