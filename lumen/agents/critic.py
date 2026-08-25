"""VLM-backed clip critic with deterministic local frame extraction."""

from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, TypeAlias

from lumen.contracts import CriticScores, CriticVerdict, QualityGate, Shot
from lumen.media_tools import resolve_ffmpeg

CriticPayload: TypeAlias = CriticVerdict | Mapping[str, Any] | str


class CriticVLM(Protocol):
    """Request-level VLM adapter injected by the provider layer."""

    def __call__(
        self,
        shot: Shot,
        frame_data_urls: tuple[str, ...],
        anchor_description: str,
        /,
    ) -> CriticPayload: ...


def probe_duration(clip_path: str | Path, *, ffprobe_bin: str = "ffprobe") -> float:
    """Read duration through ffprobe, falling back to imageio-ffmpeg metadata."""

    clip = Path(clip_path)
    if not clip.is_file():
        raise FileNotFoundError(clip)
    try:
        completed = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(clip),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        try:
            duration = float(completed.stdout.strip())
        except ValueError as exc:
            raise ValueError(
                f"ffprobe returned an invalid duration: {completed.stdout!r}"
            ) from exc
    except FileNotFoundError:
        import imageio_ffmpeg

        reader = imageio_ffmpeg.read_frames(str(clip), pix_fmt="rgb24")
        try:
            metadata = next(reader)
        finally:
            reader.close()
        duration = float(metadata.get("duration") or 0)
    if duration <= 0:
        raise ValueError(f"clip duration must be positive, got {duration}")
    return duration


def extract_frame_data_urls(
    clip_path: str | Path,
    *,
    frame_count: int = 3,
    ffprobe_bin: str = "ffprobe",
    ffmpeg_bin: str = "ffmpeg",
) -> tuple[str, ...]:
    """Extract evenly spaced JPEG frames and remove all temporary files afterward."""

    if frame_count <= 0:
        raise ValueError("frame_count must be positive")
    clip = Path(clip_path)
    duration = probe_duration(clip, ffprobe_bin=ffprobe_bin)
    timestamps = [duration * (index + 1) / (frame_count + 1) for index in range(frame_count)]

    encoded: list[str] = []
    with tempfile.TemporaryDirectory(prefix="lumen-critic-") as temp_dir:
        temp_root = Path(temp_dir)
        for index, timestamp in enumerate(timestamps):
            frame = temp_root / f"frame-{index + 1:02d}.jpg"
            command = [
                    ffmpeg_bin,
                    "-v",
                    "error",
                    "-y",
                    "-ss",
                    f"{timestamp:.6f}",
                    "-i",
                    str(clip),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    str(frame),
                ]
            try:
                subprocess.run(command, check=True, capture_output=True)
            except FileNotFoundError:
                command[0] = resolve_ffmpeg(ffmpeg_bin)
                subprocess.run(command, check=True, capture_output=True)
            if not frame.is_file() or frame.stat().st_size == 0:
                raise RuntimeError(f"ffmpeg did not produce frame {index + 1}")
            encoded.append(
                "data:image/jpeg;base64,"
                + base64.b64encode(frame.read_bytes()).decode("ascii")
            )
    return tuple(encoded)


def _json_from_text(payload: str) -> Any:
    text = payload.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"critic returned invalid JSON: {exc}") from exc


def _score_value(scores: Mapping[str, Any], names: Sequence[str]) -> Any:
    for name in names:
        if name in scores:
            return scores[name]
    raise ValueError(f"critic response is missing score: {' / '.join(names)}")


def _coerce_scores(payload: Mapping[str, Any]) -> CriticScores:
    raw_scores = payload.get("scores")
    if isinstance(raw_scores, CriticScores):
        return raw_scores.model_copy(deep=True)
    if not isinstance(raw_scores, Mapping):
        raise ValueError("critic response must contain a 'scores' mapping")
    return CriticScores(
        character_consistency=_score_value(
            raw_scores, ("character_consistency", "角色一致性")
        ),
        composition=_score_value(raw_scores, ("composition", "构图符合分镜", "构图")),
        lighting=_score_value(raw_scores, ("lighting", "光线氛围", "光线")),
        integrity=_score_value(raw_scores, ("integrity", "无明显崩坏", "画面完整性")),
    )


def adjudicate(payload: CriticPayload, gate: QualityGate) -> CriticVerdict:
    """Ignore model-supplied overall/passed fields and enforce the local quality gate."""

    if isinstance(payload, CriticVerdict):
        scores = payload.scores.model_copy(deep=True)
        critique = payload.critique
        fix_hint = payload.fix_hint
    else:
        if isinstance(payload, str):
            payload = _json_from_text(payload)
        if not isinstance(payload, Mapping):
            raise TypeError("critic VLM must return CriticVerdict, a mapping, or JSON text")
        scores = _coerce_scores(payload)
        critique = payload.get("critique")
        fix_hint = payload.get("fix_hint")
        if not isinstance(critique, str) or not critique.strip():
            raise ValueError("critic response must contain a non-empty critique")
        if not isinstance(fix_hint, str) or not fix_hint.strip():
            raise ValueError("critic response must contain a non-empty fix_hint")

    return CriticVerdict.adjudicate(
        scores=scores,
        critique=critique,
        fix_hint=fix_hint,
        gate=gate,
    )


def review_clip(
    shot: Shot,
    clip_path: str | Path,
    *,
    vlm: CriticVLM,
    gate: QualityGate | None = None,
    anchor_description: str = "",
    ffprobe_bin: str = "ffprobe",
    ffmpeg_bin: str = "ffmpeg",
) -> CriticVerdict:
    """Extract exactly three frames, invoke the VLM, and enforce local thresholds."""

    quality_gate = gate if gate is not None else QualityGate()
    frames = extract_frame_data_urls(
        clip_path,
        frame_count=3,
        ffprobe_bin=ffprobe_bin,
        ffmpeg_bin=ffmpeg_bin,
    )
    return adjudicate(vlm(shot, frames, anchor_description), quality_gate)


@dataclass(slots=True)
class Critic:
    """Injectable critic used by the orchestrator."""

    vlm: CriticVLM
    gate: QualityGate = field(default_factory=QualityGate)
    ffprobe_bin: str = "ffprobe"
    ffmpeg_bin: str = "ffmpeg"

    def review(
        self,
        shot: Shot,
        clip_path: str | Path,
        anchor_description: str = "",
    ) -> CriticVerdict:
        return review_clip(
            shot,
            clip_path,
            vlm=self.vlm,
            gate=self.gate,
            anchor_description=anchor_description,
            ffprobe_bin=self.ffprobe_bin,
            ffmpeg_bin=self.ffmpeg_bin,
        )
