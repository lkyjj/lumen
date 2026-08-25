"""Producer agent: readable DAG construction, dry-run and resumable execution."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from lumen.config import ensure_project_directories, load_project, project_paths
from lumen.contracts import DagStep, FilmProject
from lumen.pricing import estimate_image_cost, estimate_video_cost
from lumen.runlog import RunLog
from lumen.state import StateStore


class HumanGateRequired(RuntimeError):
    """Raised when production reaches a decision that only the filmmaker can make."""


def build_dag(project: FilmProject, project_root: Path | None = None) -> list[DagStep]:
    root = project_root or Path(".")
    steps: list[DagStep] = [
        DagStep(
            id="screenwriter",
            agent="screenwriter",
            model="Qwen/Qwen3.5-35B-A3B",
            output=str(root / "01_script" / "script.json"),
            execution_plane="hybrid",
        ),
        DagStep(
            id="storyboarder",
            agent="storyboarder",
            depends_on=["screenwriter"],
            model="Qwen/Qwen3.5-35B-A3B",
            output=str(root / "02_shots" / "shots.json"),
            execution_plane="hybrid",
        ),
    ]

    image_cost = estimate_image_cost(project.budget)
    art_steps: list[str] = []
    for anchor in project.anchors:
        step_id = f"art_director.anchor.{anchor.id}"
        art_steps.append(step_id)
        steps.append(
            DagStep(
                id=step_id,
                agent="art_director",
                depends_on=["storyboarder"],
                model=project.budget.image_model,
                output=str(root / anchor.image),
                estimated_cost_cny=image_cost,
                worst_case_cost_cny=image_cost,
                paid=True,
                execution_plane="cloud",
                requires_human_gate=True,
            )
        )

    keyframe_steps: dict[str, str] = {}
    for shot in project.shots:
        step_id = f"art_director.keyframe.{shot.id}"
        keyframe_steps[shot.id] = step_id
        dependencies = ["storyboarder"]
        if shot.anchor:
            dependencies.append(f"art_director.anchor.{shot.anchor}")
        steps.append(
            DagStep(
                id=step_id,
                agent="art_director",
                depends_on=dependencies,
                model=project.budget.image_model,
                output=str(root / "03_bible" / "generated" / f"{shot.id}_keyframe.png"),
                estimated_cost_cny=image_cost,
                worst_case_cost_cny=image_cost,
                paid=True,
                execution_plane="cloud",
            )
        )

    critic_steps: list[str] = []
    for shot in project.shots:
        video_cost = estimate_video_cost(
            project.budget,
            project.budget.video_model,
            project.film.resolution,
            shot.duration,
        )
        camera_id = f"cinematographer.{shot.id}"
        critic_id = f"critic.{shot.id}"
        critic_steps.append(critic_id)
        steps.extend(
            [
                DagStep(
                    id=camera_id,
                    agent="cinematographer",
                    depends_on=[keyframe_steps[shot.id]],
                    model=project.budget.video_model,
                    output=str(root / "04_clips" / "generated" / f"{shot.id}_final.mp4"),
                    estimated_cost_cny=video_cost,
                    worst_case_cost_cny=round(
                        video_cost * (project.quality_gate.max_retries + 1), 2
                    ),
                    paid=True,
                    execution_plane="cloud",
                ),
                DagStep(
                    id=critic_id,
                    agent="critic",
                    depends_on=[camera_id],
                    model="Qwen/Qwen3-VL-8B-Instruct",
                    output=str(root / "04_clips" / "generated" / f"{shot.id}_review.json"),
                    execution_plane="hybrid",
                ),
            ]
        )

    voice_characters = sum(len(shot.audio.voice or "") for shot in project.shots)
    try:
        tts_rate = project.budget.pricing.tts_cny_per_10k_characters[
            project.budget.tts_model
        ]
    except KeyError as exc:
        raise ValueError(f"no TTS price configured for {project.budget.tts_model}") from exc
    tts_cost = round(voice_characters / 10_000 * tts_rate, 2)
    steps.extend(
        [
            DagStep(
                id="sound_designer",
                agent="sound_designer",
                depends_on=["storyboarder"],
                model=project.budget.tts_model,
                output=str(root / "05_audio" / "generated"),
                estimated_cost_cny=tts_cost,
                worst_case_cost_cny=tts_cost,
                paid=tts_cost > 0,
                execution_plane="cloud",
            ),
            DagStep(
                id="editor",
                agent="editor",
                depends_on=[*critic_steps, "sound_designer"],
                model="ffmpeg",
                output=str(root / "06_cut" / "generated" / "final.mp4"),
                execution_plane="local",
            ),
        ]
    )
    return steps


def dag_totals(dag: list[DagStep]) -> tuple[float, float]:
    expected = round(sum(step.estimated_cost_cny for step in dag), 2)
    worst = round(sum(step.worst_case_cost_cny for step in dag), 2)
    return expected, worst


def render_dry_run(project: FilmProject, dag: list[DagStep]) -> str:
    expected, worst = dag_totals(dag)
    lines = [
        f"LUMEN DRY RUN · {project.film.title} / {project.film.title_en}",
        f"镜头: {len(project.shots)} · 镜头时长: {project.shots_duration:.0f}s · "
        f"终片目标: {project.film.duration_target:.0f}s",
        f"预算上限: ¥{project.budget.hard_cap:.2f} · 单次预计: ¥{expected:.2f} · "
        f"含最多重拍: ¥{worst:.2f}",
        "",
        "DAG:",
    ]
    for index, step in enumerate(dag, start=1):
        dependencies = ", ".join(step.depends_on) if step.depends_on else "-"
        cost = (
            f"¥{step.estimated_cost_cny:.2f}"
            f" / worst ¥{step.worst_case_cost_cny:.2f}"
            if step.paid
            else "free"
        )
        lines.append(
            f"{index:02d}. {step.id} [{step.agent}] deps={dependencies} "
            f"plane={step.execution_plane} gate={'human' if step.requires_human_gate else '-'} "
            f"model={step.model or '-'} cost={cost}"
        )
    lines.extend(
        [
            "",
            "安全保证: dry-run 未创建 Provider、未读取 API Key、未发起网络请求、未记账。",
        ]
    )
    return "\n".join(lines)


def run_offline(config_path: str | Path, *, force: bool = False) -> dict[str, str]:
    """Materialize frozen authoring artifacts without network or paid calls."""

    project = load_project(config_path)
    paths = project_paths(config_path)
    ensure_project_directories(paths)
    dag = build_dag(project, paths.root)
    state_store = StateStore(paths.state, paths.config)
    state = state_store.load_or_create(dag)
    run_log = RunLog(paths.run_log)

    from lumen.agents.screenwriter import Screenwriter
    from lumen.agents.storyboarder import Storyboarder

    authoring: list[tuple[str, Path, Callable[[], object]]] = [
        ("screenwriter", paths.script, lambda: Screenwriter().from_frozen_project(project)),
        ("storyboarder", paths.shots, lambda: Storyboarder().from_frozen_project(project)),
    ]
    outputs: dict[str, str] = {}
    for step_id, output_path, factory in authoring:
        if output_path.exists() and not force:
            state_store.mark(state, step_id, "skipped")
            run_log.append(
                event=f"{step_id}.offline",
                agent=step_id,
                status="skipped",
                details={"output": str(output_path), "reason": "existing frozen artifact"},
            )
            outputs[step_id] = str(output_path)
            continue
        state_store.mark(state, step_id, "running")
        result = factory()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(result, "model_dump_json"):
            content = result.model_dump_json(indent=2)  # type: ignore[attr-defined]
        elif isinstance(result, list) and all(hasattr(item, "model_dump") for item in result):
            content = json.dumps(
                [item.model_dump(mode="json") for item in result],  # type: ignore[attr-defined]
                ensure_ascii=False,
                indent=2,
            )
        else:
            content = json.dumps(result, ensure_ascii=False, indent=2)
        output_path.write_text(content + "\n", encoding="utf-8")
        state_store.mark(state, step_id, "succeeded")
        run_log.append(
            event=f"{step_id}.offline",
            agent=step_id,
            status="simulated",
            details={"output": str(output_path), "source": "frozen film.yaml"},
        )
        outputs[step_id] = str(output_path)
    return outputs
