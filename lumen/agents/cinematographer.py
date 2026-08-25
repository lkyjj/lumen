"""Cinematographer agent with bounded critic-guided reshoots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from lumen.contracts import CriticVerdict, QualityGate, Shot, ShotResult
from lumen.providers.base import VideoProvider


class ClipCritic(Protocol):
    def review(
        self,
        shot: Shot,
        clip_path: str | Path,
        anchor_description: str = "",
    ) -> CriticVerdict: ...


class ShotNeedsHumanReview(RuntimeError):
    def __init__(self, result: ShotResult, attempts: list[CriticVerdict]) -> None:
        self.result = result
        self.attempts = tuple(attempts)
        super().__init__(
            f"{result.shot_id} 在 {result.attempt} 次生成后仍未通过质量门，已停止付费重试"
        )


def compose_prompt(shot: Shot, previous: CriticVerdict | None = None) -> str:
    base = (
        "电影感，低照度，冷蓝灰色调，单一光源，轻微胶片颗粒，16:9。\n"
        f"景别：{shot.size}；机位/运镜：{shot.movement}；{shot.prompt_seed}"
    )
    if previous is None:
        return base
    return (
        f"【本次最优先修正】{previous.fix_hint}\n"
        f"【上一次具体问题】{previous.critique}\n{base}"
    )


@dataclass(slots=True)
class Cinematographer:
    video_provider: VideoProvider
    critic: ClipCritic
    quality_gate: QualityGate

    def shoot(
        self,
        shot: Shot,
        keyframe: str | Path,
        output_dir: str | Path,
        *,
        resolution: str,
        anchor_description: str = "",
        api_key: str | None = None,
    ) -> ShotResult:
        if int(shot.duration) != shot.duration:
            raise ValueError(f"{shot.id}: video provider requires whole-second duration")
        source = Path(keyframe)
        if not source.is_file():
            raise FileNotFoundError(source)
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)

        verdicts: list[CriticVerdict] = []
        total_cost = 0.0
        previous: CriticVerdict | None = None
        for attempt in range(1, self.quality_gate.max_retries + 2):
            output = directory / f"{shot.id}_attempt_{attempt:02d}.mp4"
            video = self.video_provider.generate_from_image(
                compose_prompt(shot, previous),
                source,
                output,
                resolution=resolution,
                duration=int(shot.duration),
                # Every shot receives a generated keyframe, so the video boundary is
                # consistently I2V first-frame across Wan 3.0, 2.7 and 2.6.
                reference_type="first_frame",
                api_key=api_key,
            )
            total_cost = round(total_cost + video.cost_cny, 2)
            verdict = self.critic.review(shot, video.path, anchor_description)
            verdicts.append(verdict)
            review_path = directory / f"{shot.id}_attempt_{attempt:02d}_review.json"
            review_path.write_text(verdict.model_dump_json(indent=2) + "\n", encoding="utf-8")
            result = ShotResult(
                shot_id=shot.id,
                clip_path=str(video.path),
                attempt=attempt,
                score=verdict.overall,
                critique=verdict.critique,
                cost_cny=total_cost,
                passed=verdict.passed,
            )
            if verdict.passed:
                manifest = directory / f"{shot.id}_final.json"
                manifest.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
                return result
            previous = verdict

        failure_manifest = directory / f"{shot.id}_needs_human_review.json"
        failure_manifest.write_text(
            json.dumps(
                {
                    "result": result.model_dump(mode="json"),
                    "attempts": [item.model_dump(mode="json") for item in verdicts],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise ShotNeedsHumanReview(result, verdicts)
