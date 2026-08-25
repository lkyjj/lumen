"""Sound designer agent for the frozen dialogue inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lumen.contracts import FilmProject
from lumen.providers.base import AudioResult, TTSProvider


@dataclass(slots=True)
class SoundDesigner:
    provider: TTSProvider

    def synthesize_dialogue(
        self,
        project: FilmProject,
        output_dir: str | Path,
        *,
        voices: dict[str, str],
        api_key: str | None = None,
    ) -> dict[str, AudioResult]:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        results: dict[str, AudioResult] = {}
        for shot in project.shots:
            if not shot.audio.voice:
                continue
            role = shot.audio.voice_role
            voice = voices.get(role)
            if not voice:
                raise ValueError(f"missing enabled TTS voice for role: {role}")
            results[shot.id] = self.provider.synthesize(
                shot.audio.voice,
                directory / f"{shot.id}_{role}.wav",
                voice=voice,
                language_hint="zh",
                api_key=api_key,
            )
        return results


def dialogue_timeline(project: FilmProject) -> list[tuple[str, int, str]]:
    """Return (shot_id, start_ms, text) for deterministic mix placement."""

    elapsed_ms = 0
    lines: list[tuple[str, int, str]] = []
    for shot in project.shots:
        if shot.audio.voice:
            lines.append((shot.id, elapsed_ms, shot.audio.voice))
        elapsed_ms += round(shot.duration * 1000)
    return lines
