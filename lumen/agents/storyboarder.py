"""Storyboard agent that preserves approved shots unless regeneration is explicit."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias

from lumen.contracts import FilmProject, Script, Shot

StoryboardPayload: TypeAlias = (
    Sequence[Shot | Mapping[str, Any]] | Mapping[str, Any] | str
)


class StoryboardLLM(Protocol):
    """Minimal boundary implemented by an injected JSON-capable LLM provider."""

    def __call__(self, system_prompt: str, user_prompt: str, /) -> StoryboardPayload: ...


SYSTEM_PROMPT = """你是 LUMEN 剧组的分镜师。
依据结构化剧本重新生成镜头契约。镜头数量、shot_id 及顺序必须与批准版本完全一致；
总时长、人物、场景、锚点和 reference_type 必须满足项目契约。只返回 {\"shots\": [...]} JSON。"""


def _json_from_text(payload: str) -> Any:
    text = payload.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"storyboarder returned invalid JSON: {exc}") from exc


def _coerce_shots(payload: StoryboardPayload) -> list[Shot]:
    if isinstance(payload, str):
        payload = _json_from_text(payload)
    if isinstance(payload, Mapping):
        if "shots" not in payload:
            raise ValueError("storyboarder response mapping must contain 'shots'")
        payload = payload["shots"]
    if isinstance(payload, (str, bytes)) or not isinstance(payload, Sequence):
        raise TypeError("storyboarder LLM must return a shot sequence or {'shots': [...]} mapping")

    shots: list[Shot] = []
    for item in payload:
        if isinstance(item, Shot):
            shots.append(item.model_copy(deep=True))
        elif isinstance(item, Mapping):
            shots.append(Shot.model_validate(item))
        else:
            raise TypeError("each regenerated storyboard item must be a Shot or mapping")
    return shots


def _validate_script_alignment(script: Script, project: FilmProject) -> None:
    expected_ids = [shot.id for shot in project.shots]
    script_ids = [beat.shot_id for beat in script.beats]
    if script_ids != expected_ids:
        raise ValueError(
            "script beats must match frozen shot ids in order before storyboarding: "
            f"expected {expected_ids}, got {script_ids}"
        )


def _validate_regenerated_shots(shots: list[Shot], project: FilmProject) -> list[Shot]:
    expected_ids = [shot.id for shot in project.shots]
    actual_ids = [shot.id for shot in shots]
    if actual_ids != expected_ids:
        raise ValueError(
            "regenerated shots must preserve frozen shot ids and order: "
            f"expected {expected_ids}, got {actual_ids}"
        )

    project_payload = project.model_dump(mode="python")
    project_payload["shots"] = [shot.model_dump(mode="python") for shot in shots]
    validated = FilmProject.model_validate(project_payload)
    return [shot.model_copy(deep=True) for shot in validated.shots]


def build_storyboard(
    project: FilmProject,
    script: Script,
    *,
    regenerate: bool = False,
    llm: StoryboardLLM | None = None,
) -> list[Shot]:
    """Return frozen shots by default; regenerate only when explicitly requested."""

    _validate_script_alignment(script, project)
    if not regenerate:
        return [shot.model_copy(deep=True) for shot in project.shots]
    if llm is None:
        raise ValueError("storyboard regeneration requires an injected llm")

    user_prompt = json.dumps(
        {
            "script": script.model_dump(mode="json"),
            "frozen_shot_ids": [shot.id for shot in project.shots],
            "cast_ids": [member.id for member in project.cast],
            "location_ids": [location.id for location in project.locations],
            "anchor_ids": [anchor.id for anchor in project.anchors],
            "style": project.style.model_dump(mode="json"),
            "quality_gate": project.quality_gate.model_dump(mode="json"),
            "shot_schema": Shot.model_json_schema(),
        },
        ensure_ascii=False,
    )
    regenerated = _coerce_shots(llm(SYSTEM_PROMPT, user_prompt))
    return _validate_regenerated_shots(regenerated, project)


@dataclass(slots=True)
class Storyboarder:
    """Injectable storyboarder used by the orchestrator."""

    llm: StoryboardLLM | None = None

    def from_frozen_project(self, project: FilmProject) -> list[Shot]:
        """Compatibility entry point that returns contract objects, never dictionaries."""

        return [shot.model_copy(deep=True) for shot in project.shots]

    def run(
        self,
        project: FilmProject,
        script: Script,
        *,
        regenerate: bool = False,
    ) -> list[Shot]:
        return build_storyboard(project, script, regenerate=regenerate, llm=self.llm)
