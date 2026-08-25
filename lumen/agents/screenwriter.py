"""Screenwriter agent with a deterministic frozen mode and an injected live mode."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias

from lumen.contracts import FilmProject, Script, ScriptBeat, ShotAudio

ScriptPayload: TypeAlias = Script | Mapping[str, Any] | str


class ScriptLLM(Protocol):
    """Minimal boundary implemented by an injected JSON-capable LLM provider."""

    def __call__(self, system_prompt: str, user_prompt: str, /) -> ScriptPayload: ...


SYSTEM_PROMPT = """你是 LUMEN 剧组的编剧。
根据已经批准的电影契约编写结构化剧本。每个镜头必须且只能对应一个 beat，
不得增加、删除、重排 shot_id。只返回符合给定 JSON schema 的 JSON。"""


def _sound_summary(audio: ShotAudio) -> str:
    parts: list[str] = []
    if audio.voice:
        parts.append(f"台词：{audio.voice}")
    if audio.sfx:
        parts.append(f"音效：{'、'.join(audio.sfx)}")
    if audio.music:
        parts.append(f"音乐：{audio.music}")
    return "；".join(parts) if parts else "无"


def frozen_script(project: FilmProject) -> Script:
    """Derive a script from approved shots without invoking a model."""

    return Script(
        title=project.film.title,
        logline=project.film.logline,
        beats=[
            ScriptBeat(
                shot_id=shot.id,
                action=shot.intent,
                visual=f"{shot.size}；{shot.movement}；{shot.prompt_seed}",
                sound=_sound_summary(shot.audio),
                dialogue=shot.audio.voice,
            )
            for shot in project.shots
        ],
    )


def _json_from_text(payload: str) -> Any:
    text = payload.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"screenwriter returned invalid JSON: {exc}") from exc


def _coerce_script(payload: ScriptPayload) -> Script:
    if isinstance(payload, Script):
        return payload.model_copy(deep=True)
    if isinstance(payload, str):
        payload = _json_from_text(payload)
    if not isinstance(payload, Mapping):
        raise TypeError("screenwriter LLM must return Script, a mapping, or JSON text")
    return Script.model_validate(payload)


def _validate_script(script: Script, project: FilmProject) -> Script:
    expected_ids = [shot.id for shot in project.shots]
    actual_ids = [beat.shot_id for beat in script.beats]
    if script.title != project.film.title:
        raise ValueError(
            f"screenwriter changed the frozen title: {script.title!r} != {project.film.title!r}"
        )
    if script.logline != project.film.logline:
        raise ValueError("screenwriter changed the frozen logline")
    if actual_ids != expected_ids:
        raise ValueError(
            "screenwriter beats must match frozen shot ids in order: "
            f"expected {expected_ids}, got {actual_ids}"
        )
    for beat in script.beats:
        if not beat.action.strip() or not beat.visual.strip() or not beat.sound.strip():
            raise ValueError(f"{beat.shot_id}: action, visual, and sound must be non-empty")
    return script


def write_script(
    project: FilmProject,
    *,
    frozen: bool = True,
    llm: ScriptLLM | None = None,
) -> Script:
    """Return the approved offline script, or explicitly invoke an injected LLM."""

    if frozen:
        return frozen_script(project)
    if llm is None:
        raise ValueError("live screenwriter mode requires an injected llm")

    user_prompt = json.dumps(
        {
            "film": project.film.model_dump(mode="json"),
            "shots": [shot.model_dump(mode="json") for shot in project.shots],
            "output_schema": Script.model_json_schema(),
        },
        ensure_ascii=False,
    )
    return _validate_script(_coerce_script(llm(SYSTEM_PROMPT, user_prompt)), project)


@dataclass(slots=True)
class Screenwriter:
    """Injectable screenwriter used by the orchestrator."""

    llm: ScriptLLM | None = None

    def from_frozen_project(self, project: FilmProject) -> Script:
        """Compatibility entry point for offline orchestration."""

        return frozen_script(project)

    def run(self, project: FilmProject, *, frozen: bool = True) -> Script:
        return write_script(project, frozen=frozen, llm=self.llm)
