"""Request-scoped real backend for the Studio single-shot BYOK flow."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from lumen.agents.critic import Critic
from lumen.config import load_project
from lumen.contracts import Shot
from lumen.media_tools import media_runtime
from lumen.production import ModelScopeCriticAdapter
from lumen.providers import DashScopeVideoProvider, ModelScopeProvider, video_capability
from lumen.providers.base import VideoResult
from studio.app import (
    LiveBackend,
    LiveShotRequest,
    OneShotResult,
    PreflightResult,
    RequestCredentials,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FILM = REPO_ROOT / "projects" / "vanishing-light" / "film.yaml"
REFERENCE = (
    REPO_ROOT
    / "projects"
    / "vanishing-light"
    / "03_bible"
    / "candidates"
    / "E06_front_v1.png"
)


class EphemeralBudget:
    """One-request budget that never writes visitor data to disk."""

    def __init__(self, hard_cap: float) -> None:
        if hard_cap < 0:
            raise ValueError("hard cap must be non-negative")
        self.hard_cap = round(float(hard_cap), 2)
        self.spent = 0.0

    def check(self, amount: float, *, note: str = "") -> None:
        value = round(float(amount), 2)
        if value < 0 or self.spent + value > self.hard_cap:
            raise RuntimeError("request would exceed the visitor-confirmed quote")

    def charge(
        self,
        amount: float,
        *,
        agent: str,
        model: str,
        note: str = "",
        details: dict[str, Any] | None = None,
        reserved: bool = False,
    ) -> None:
        self.check(amount, note=note)
        self.spent = round(self.spent + float(amount), 2)


class ProductionLiveBackend(LiveBackend):
    """One instance per callback; credentials never leave this object."""

    def __init__(self, credentials: RequestCredentials) -> None:
        self._credentials = credentials
        self._sessions: list[Any] = []

    def preflight(self, request: LiveShotRequest) -> PreflightResult:
        capability = video_capability(request.model)
        if request.resolution not in capability.price_cny_per_second:
            return PreflightResult(
                ok=False,
                summary="所选模型不支持该分辨率，未发起网络请求。",
            )
        if not 2 <= request.duration <= capability.max_duration:
            return PreflightResult(
                ok=False,
                summary=(
                    f"所选模型时长范围为 2–{capability.max_duration} 秒，"
                    "未发起网络请求。"
                ),
            )
        try:
            runtime = media_runtime()
        except FileNotFoundError:
            return PreflightResult(
                ok=False,
                summary="Studio 缺少可用的 ffmpeg 媒体审片运行时。",
            )
        if not REFERENCE.is_file():
            return PreflightResult(ok=False, summary="演示锚点不存在，未生成。")
        return PreflightResult(
            ok=True,
            summary="本地能力、锚点和审片依赖通过；尚未远程鉴权，也未产生费用。",
            details={
                "model": request.model,
                "resolution": request.resolution,
                "duration": request.duration,
                "reference": REFERENCE.name,
                "media_runtime": runtime,
                "remote_auth_checked": False,
            },
        )

    def run_one_shot(self, request: LiveShotRequest) -> OneShotResult:
        preflight = self.preflight(request)
        if not preflight.ok:
            raise RuntimeError("local preflight failed")
        project = load_project(FILM)
        budget = EphemeralBudget(request.max_cost_cny)
        video = DashScopeVideoProvider(
            budget=budget,
            api_key=self._credentials.dashscope_api_key,
            model=request.model,
        )
        vlm = ModelScopeProvider(api_key=self._credentials.modelscope_api_key)
        self._sessions.extend([video.session])
        output_dir = Path(tempfile.mkdtemp(prefix="lumen-studio-shot-"))
        output = output_dir / "live-shot.mp4"
        prompt = (
            "电影感，低照度，冷蓝灰色调，单一光源，轻微胶片颗粒，16:9。"
            "人物保持同一身份、闭嘴且动作克制。故事意图："
            + request.logline
        )
        result: VideoResult = video.generate_from_image(
            prompt,
            REFERENCE,
            output,
            resolution=request.resolution,
            duration=int(request.duration),
            reference_type="first_frame",
        )
        base_shot = next(item for item in project.shots if item.id == "S06")
        live_shot = Shot.model_validate(
            {
                **base_shot.model_dump(mode="python"),
                "id": "LIVE",
                "duration": request.duration,
                "intent": request.logline,
                "prompt_seed": prompt,
            }
        )
        critic = Critic(
            vlm=ModelScopeCriticAdapter(vlm, "Qwen/Qwen3-VL-8B-Instruct"),
            gate=project.quality_gate,
        )
        verdict = critic.review(
            live_shot,
            result.path,
            next(anchor.prompt for anchor in project.anchors if anchor.id == "B"),
        )
        return OneShotResult(
            summary="视频生成和三帧审片已完成；该 BYOK 流程不会自动重拍。",
            cost_cny=budget.spent,
            video=str(result.path),
            critic_evidence=verdict.model_dump(mode="json"),
        )

    def close(self) -> None:
        for session in self._sessions:
            close = getattr(session, "close", None)
            if callable(close):
                close()
        self._sessions.clear()
        self._credentials = RequestCredentials("", "")


def production_backend_factory(credentials: RequestCredentials) -> LiveBackend:
    return ProductionLiveBackend(credentials)
