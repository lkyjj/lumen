"""Explicit, gated production stages for real providers.

Nothing in this module runs from import. Paid stages are called only by the CLI
after an explicit spend confirmation and the relevant human gates.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lumen.agents.art_director import (
    AnchorApprovalRequired,
    ArtDirector,
    require_anchor_approval,
    unapproved_anchors,
)
from lumen.agents.cinematographer import Cinematographer, ShotNeedsHumanReview
from lumen.agents.critic import Critic
from lumen.agents.editor import Editor
from lumen.agents.sound_designer import SoundDesigner
from lumen.budget import Budget
from lumen.config import ensure_project_directories, load_project, project_paths
from lumen.contracts import FilmProject, ProjectPaths, Shot
from lumen.providers import (
    DashScopeT2IProvider,
    DashScopeTTSProvider,
    DashScopeVideoProvider,
    ModelScopeProvider,
    ProviderResponseError,
    ProviderTransportError,
    UnsupportedModelError,
)
from lumen.providers.base import VideoResult
from lumen.runlog import RunLog
from lumen.state import StateStore


class SpendConfirmationRequired(RuntimeError):
    pass


class GoNoGoRequired(RuntimeError):
    pass


CRITIC_SYSTEM = """你是严格的影视执行导演，职责是拦截崩坏而不是鼓励。
按角色一致性、构图符合分镜、光线氛围、无明显崩坏四维各打 1-10 分。
critique 必须指出画面中的具体问题；fix_hint 必须是下一次视频 prompt 可直接执行的修正。
只返回 JSON：{"scores":{"character_consistency":0,"composition":0,"lighting":0,
"integrity":0},"critique":"...","fix_hint":"..."}。"""


@dataclass(slots=True)
class ModelScopeCriticAdapter:
    provider: ModelScopeProvider
    model: str

    def __call__(
        self,
        shot: Shot,
        frame_data_urls: tuple[str, ...],
        anchor_description: str,
    ) -> dict[str, Any]:
        text = (
            f"【镜头】{shot.id}\n【导演意图】{shot.intent}\n"
            f"【景别】{shot.size}\n【运镜】{shot.movement}\n"
            f"【角色/机位锚点】{anchor_description or '无固定角色锚点'}"
        )
        return self.provider.vision_json(
            model=self.model,
            system=CRITIC_SYSTEM,
            text=text,
            image_data_urls=frame_data_urls,
        )


class FallbackVideoProvider:
    """Fall back only on verified model permission/capability failures."""

    def __init__(self, providers: list[DashScopeVideoProvider]) -> None:
        if not providers:
            raise ValueError("at least one video provider is required")
        self.providers = providers

    def generate_from_image(
        self,
        prompt: str,
        image_path: str | Path,
        output_path: str | Path,
        **kwargs: Any,
    ) -> VideoResult:
        errors: list[str] = []
        for index, provider in enumerate(self.providers):
            try:
                return provider.generate_from_image(
                    prompt,
                    image_path,
                    output_path,
                    **kwargs,
                )
            except UnsupportedModelError as exc:
                errors.append(f"{provider.model}: {exc}")
            except ProviderTransportError as exc:
                if exc.status_code not in {403, 404}:
                    raise
                errors.append(f"{provider.model}: permission/unavailable")
            except ProviderResponseError as exc:
                code = (exc.code or "").lower()
                if not any(term in code for term in ("permission", "forbidden", "model_not_found")):
                    raise
                errors.append(f"{provider.model}: permission/unavailable")
            if index + 1 == len(self.providers):
                break
        raise RuntimeError("所有视频路线均不可用：" + "; ".join(errors))


@dataclass(slots=True)
class ProductionContext:
    project: FilmProject
    paths: ProjectPaths
    run_log: RunLog
    budget: Budget


def load_context(config_path: str | Path) -> ProductionContext:
    project = load_project(config_path)
    paths = project_paths(config_path)
    ensure_project_directories(paths)
    run_log = RunLog(paths.run_log)
    return ProductionContext(project, paths, run_log, Budget(project.budget, run_log))


def require_spend_confirmation(confirmed: bool) -> None:
    if not confirmed:
        raise SpendConfirmationRequired(
            "该阶段可能产生费用；请先查看 dry-run，并显式传入 --confirm-spend"
        )


def _go_no_go_path(paths: ProjectPaths) -> Path:
    return paths.bible / "GO_NO_GO.json"


def require_go_decision(paths: ProjectPaths) -> dict[str, Any]:
    decision_path = _go_no_go_path(paths)
    if not decision_path.is_file():
        raise GoNoGoRequired(
            f"批量生成前需要 D9 决策文件：{decision_path}（decision 必须为 GO）"
        )
    payload = json.loads(decision_path.read_text(encoding="utf-8"))
    if payload.get("decision") != "GO":
        raise GoNoGoRequired("D9 决策不是 GO；已停止批量生成")
    return payload


def generate_anchors(
    context: ProductionContext,
    *,
    confirmed: bool,
    force: bool = False,
) -> list[str]:
    require_spend_confirmation(confirmed)
    provider = DashScopeT2IProvider(
        budget=context.budget,
        model=context.project.budget.image_model,
        price_cny_each=context.project.budget.pricing.image_cny_each,
    )
    results = ArtDirector(provider).generate_anchor_candidates(
        context.project,
        context.paths,
        force=force,
    )
    paths = [str(result.path) for result in results]
    context.run_log.append(
        event="art_director.anchors",
        agent="art_director",
        status="succeeded",
        model=context.project.budget.image_model,
        details={"outputs": paths, "approved": False},
    )
    return paths


def generate_keyframes(
    context: ProductionContext,
    *,
    confirmed: bool,
    force: bool = False,
) -> dict[str, str]:
    require_spend_confirmation(confirmed)
    require_anchor_approval(context.project)
    provider = DashScopeT2IProvider(
        budget=context.budget,
        model=context.project.budget.image_model,
        price_cny_each=context.project.budget.pricing.image_cny_each,
    )
    results = ArtDirector(provider).generate_keyframes(
        context.project,
        context.paths,
        force=force,
    )
    outputs = {shot_id: str(result.path) for shot_id, result in results.items()}
    context.run_log.append(
        event="art_director.keyframes",
        agent="art_director",
        status="succeeded",
        model=context.project.budget.image_model,
        details={"outputs": outputs},
    )
    return outputs


def _anchor_description(project: FilmProject, shot: Shot) -> str:
    parts: list[str] = []
    if shot.anchor:
        anchor = next(item for item in project.anchors if item.id == shot.anchor)
        parts.append(anchor.prompt)
    for cast_id in shot.cast:
        member = next(item for item in project.cast if item.id == cast_id)
        parts.append(member.anchor_prompt)
    return "\n".join(parts)


def _video_provider(context: ProductionContext) -> FallbackVideoProvider:
    models = [
        context.project.budget.video_model,
        context.project.budget.stable_video_model,
        context.project.budget.fallback_video_model,
    ]
    unique_models = list(dict.fromkeys(models))
    return FallbackVideoProvider(
        [DashScopeVideoProvider(budget=context.budget, model=model) for model in unique_models]
    )


def shoot_one(
    context: ProductionContext,
    shot_id: str,
    *,
    confirmed: bool,
) -> str:
    require_spend_confirmation(confirmed)
    require_anchor_approval(context.project)
    try:
        shot = next(item for item in context.project.shots if item.id == shot_id)
    except StopIteration as exc:
        raise ValueError(f"unknown shot id: {shot_id}") from exc
    manifest = context.paths.clips / "generated" / f"{shot.id}_final.json"
    if manifest.is_file():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        cached = Path(str(payload.get("clip_path", "")))
        if cached.is_file() and payload.get("passed") is True:
            context.run_log.append(
                event="cinematographer.cache_hit",
                agent="cinematographer",
                status="skipped",
                details={"shot_id": shot.id, "clip_path": str(cached)},
            )
            return str(cached)
    keyframe = context.paths.bible / "generated" / f"{shot.id}_keyframe.png"
    critic = Critic(
        vlm=ModelScopeCriticAdapter(
            provider=ModelScopeProvider(),
            model=os.getenv("LUMEN_VLM_MODEL", "Qwen/Qwen3-VL-8B-Instruct"),
        ),
        gate=context.project.quality_gate,
    )
    cinematographer = Cinematographer(
        video_provider=_video_provider(context),
        critic=critic,
        quality_gate=context.project.quality_gate,
    )
    try:
        result = cinematographer.shoot(
            shot,
            keyframe,
            context.paths.clips / "generated",
            resolution=context.project.film.resolution,
            anchor_description=_anchor_description(context.project, shot),
        )
    except ShotNeedsHumanReview as exc:
        context.run_log.append(
            event="cinematographer.needs_human_review",
            agent="cinematographer",
            status="failed",
            details={"shot_id": shot.id, "result": exc.result.model_dump(mode="json")},
        )
        raise
    context.run_log.append(
        event="cinematographer.complete",
        agent="cinematographer",
        status="succeeded",
        details={"shot_id": shot.id, "result": result.model_dump(mode="json")},
    )
    return result.clip_path


def shoot_all(context: ProductionContext, *, confirmed: bool) -> dict[str, str]:
    require_go_decision(context.paths)
    outputs: dict[str, str] = {}
    for shot in context.project.shots:
        outputs[shot.id] = shoot_one(context, shot.id, confirmed=confirmed)
    return outputs


def synthesize_audio(context: ProductionContext, *, confirmed: bool) -> dict[str, str]:
    require_spend_confirmation(confirmed)
    default_voice = os.getenv("LUMEN_TTS_VOICE")
    voices = {
        "system": os.getenv("LUMEN_TTS_VOICE_SYSTEM") or default_voice or "",
        "human": os.getenv("LUMEN_TTS_VOICE_HUMAN") or default_voice or "",
    }
    try:
        rate = context.project.budget.pricing.tts_cny_per_10k_characters[
            context.project.budget.tts_model
        ]
    except KeyError as exc:
        raise ValueError(
            f"no TTS price configured for {context.project.budget.tts_model}"
        ) from exc
    provider = DashScopeTTSProvider(
        budget=context.budget,
        model=context.project.budget.tts_model,
        price_cny_per_10k_chars=rate,
    )
    results = SoundDesigner(provider).synthesize_dialogue(
        context.project,
        context.paths.audio / "generated",
        voices=voices,
    )
    return {shot_id: str(result.path) for shot_id, result in results.items()}


def _find_final_clips(context: ProductionContext) -> dict[str, Path]:
    clips: dict[str, Path] = {}
    directory = context.paths.clips / "generated"
    for shot in context.project.shots:
        manifest = directory / f"{shot.id}_final.json"
        if not manifest.is_file():
            continue
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        clip = Path(str(payload.get("clip_path", "")))
        if clip.is_file():
            clips[shot.id] = clip
    return clips


def _find_dialogue(context: ProductionContext) -> dict[str, Path]:
    dialogue: dict[str, Path] = {}
    directory = context.paths.audio / "generated"
    for shot in context.project.shots:
        if not shot.audio.voice:
            continue
        path = directory / f"{shot.id}_{shot.audio.voice_role}.wav"
        if path.is_file():
            dialogue[shot.id] = path
    return dialogue


def find_font(explicit: str | Path | None = None) -> Path:
    candidates = [
        Path(explicit) if explicit else None,
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise FileNotFoundError("no CJK font found; pass --font-file")


def render_master(
    context: ProductionContext,
    *,
    font_file: str | Path | None = None,
) -> str:
    clips = _find_final_clips(context)
    output = context.paths.cut / "generated" / "final.mp4"
    rendered = Editor().render_master(
        context.project,
        clips,
        _find_dialogue(context),
        output,
        work_dir=context.paths.cut / "generated" / "work",
        font_file=find_font(font_file),
    )
    context.run_log.append(
        event="editor.complete",
        agent="editor",
        status="succeeded",
        model="ffmpeg",
        details={"output": str(rendered)},
    )
    return str(rendered)


PILOT_SHOTS = ("S03", "S06", "S12")


def run_live_pipeline(
    config_path: str | Path,
    *,
    confirmed: bool,
    force: bool = False,
    font_file: str | Path | None = None,
) -> dict[str, Any]:
    """Run the resumable production harness until completion or a human gate.

    The harness reuses approved artifacts and passed clip manifests. It never
    crosses a billable boundary without ``confirmed`` and never invents a human
    approval or Go/No-Go decision.
    """

    require_spend_confirmation(confirmed)
    from lumen.orchestrator import build_dag, run_offline

    authoring = run_offline(config_path, force=force)
    context = load_context(config_path)
    dag = build_dag(context.project, context.paths.root)
    state_store = StateStore(context.paths.state, context.paths.config)
    state = state_store.load_or_create(dag)
    report: dict[str, Any] = {"authoring": authoring}

    missing_anchors = [
        anchor for anchor in context.project.anchors
        if not (context.paths.root / anchor.image).is_file()
    ]
    if missing_anchors:
        report["anchors"] = generate_anchors(context, confirmed=True, force=force)
    for anchor in context.project.anchors:
        step = f"art_director.anchor.{anchor.id}"
        state_store.mark(state, step, "succeeded" if anchor.approved else "pending")

    pending = unapproved_anchors(context.project)
    if pending:
        for anchor_id in pending:
            state_store.mark(
                state,
                f"art_director.anchor.{anchor_id}",
                "pending",
                needs_human=True,
            )
        context.run_log.append(
            event="producer.human_gate",
            agent="producer",
            status="failed",
            details={"gate": "anchor_approval", "anchor_ids": pending},
        )
        raise AnchorApprovalRequired(pending)

    report["keyframes"] = generate_keyframes(context, confirmed=True, force=force)
    for shot in context.project.shots:
        state_store.mark(state, f"art_director.keyframe.{shot.id}", "succeeded")

    decision_path = _go_no_go_path(context.paths)
    if not decision_path.is_file():
        pilots: dict[str, str] = {}
        for shot_id in PILOT_SHOTS:
            pilots[shot_id] = shoot_one(context, shot_id, confirmed=True)
            state_store.mark(state, f"cinematographer.{shot_id}", "succeeded")
            state_store.mark(state, f"critic.{shot_id}", "succeeded")
        report["pilot_shots"] = pilots
        context.run_log.append(
            event="producer.human_gate",
            agent="producer",
            status="failed",
            details={"gate": "go_no_go", "pilot_shots": list(PILOT_SHOTS)},
        )
        raise GoNoGoRequired(
            f"三镜试拍已完成；请审核后填写 {decision_path}，decision 必须为 GO。"
        )

    require_go_decision(context.paths)
    report["shots"] = shoot_all(context, confirmed=True)
    for shot in context.project.shots:
        state_store.mark(state, f"cinematographer.{shot.id}", "succeeded")
        state_store.mark(state, f"critic.{shot.id}", "succeeded")
    report["audio"] = synthesize_audio(context, confirmed=True)
    state_store.mark(state, "sound_designer", "succeeded")
    report["final"] = render_master(context, font_file=font_file)
    state_store.mark(state, "editor", "succeeded")
    context.run_log.append(
        event="producer.pipeline_complete",
        agent="producer",
        status="succeeded",
        details={"final": report["final"]},
    )
    return report
