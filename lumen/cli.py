"""Command-line interface for LUMEN."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from lumen.budget import Budget
from lumen.config import load_project, project_paths
from lumen.orchestrator import build_dag, render_dry_run, run_offline
from lumen.runlog import RunLog, redact
from lumen.state import StateStore

DEFAULT_FILM = Path("projects/vanishing-light/film.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lumen", description="一个人的 AI 电影剧组")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="运行或预演电影生产 DAG")
    run.add_argument("film", nargs="?", type=Path, default=DEFAULT_FILM)
    run.add_argument("--dry-run", action="store_true", help="仅校验并打印 DAG")
    run.add_argument(
        "--mode",
        choices=("offline", "live"),
        default="offline",
        help="offline 只物化定稿剧本/分镜；live 需要新凭据和人工门禁",
    )
    run.add_argument("--force", action="store_true", help="覆盖离线定稿 JSON")
    run.add_argument("--confirm-spend", action="store_true", help="确认 live 模式的付费上限")
    run.add_argument("--font-file", type=Path, help="成片中文字幕字体")

    validate = subparsers.add_parser("validate", help="严格校验 film.yaml")
    validate.add_argument("film", nargs="?", type=Path, default=DEFAULT_FILM)

    status = subparsers.add_parser("status", help="显示断点状态与预算")
    status.add_argument("film", nargs="?", type=Path, default=DEFAULT_FILM)

    produce = subparsers.add_parser("produce", help="按人工门禁分阶段运行真实 Provider")
    produce.add_argument("film", nargs="?", type=Path, default=DEFAULT_FILM)
    produce.add_argument(
        "--stage",
        required=True,
        choices=("anchors", "keyframes", "shot", "shots", "audio", "render"),
    )
    produce.add_argument("--shot", help="stage=shot 时的镜头 ID，例如 S03")
    produce.add_argument("--confirm-spend", action="store_true")
    produce.add_argument("--force", action="store_true")
    produce.add_argument("--font-file", type=Path)

    create = subparsers.add_parser("create", help="一句话生成标准化单镜测试")
    create.add_argument("logline", help="8–500 字的一句话故事")
    create.add_argument("--film", type=Path, default=DEFAULT_FILM)
    create.add_argument("--model", default="wan2.6-i2v-flash")
    create.add_argument("--resolution", default="720P")
    create.add_argument("--duration", type=int, default=5)
    create.add_argument("--execute", action="store_true", help="执行真实生成；默认只预演")
    create.add_argument("--confirm-spend", action="store_true")
    create.add_argument(
        "--output",
        type=Path,
        default=Path("projects/vanishing-light/06_cut/generated/one_sentence_demo.mp4"),
    )

    return parser


def command_run(args: argparse.Namespace) -> int:
    project = load_project(args.film)
    paths = project_paths(args.film)
    dag = build_dag(project, paths.root)
    if args.dry_run:
        print(render_dry_run(project, dag))
        return 0
    if args.mode == "offline":
        outputs = run_offline(args.film, force=args.force)
        print(json.dumps(outputs, ensure_ascii=False, indent=2))
        print("离线 authoring 已完成；未读取密钥、未联网、未产生费用。")
        return 0
    from lumen.production import run_live_pipeline

    outputs = run_live_pipeline(
        args.film,
        confirmed=args.confirm_spend,
        force=args.force,
        font_file=args.font_file,
    )
    print(json.dumps(outputs, ensure_ascii=False, indent=2))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    project = load_project(args.film)
    print(
        f"有效: {project.film.title} · {len(project.shots)} 镜 · "
        f"{project.shots_duration:.0f}s + {project.film.title_cards_duration:.0f}s 字幕"
    )
    return 0


def command_status(args: argparse.Namespace) -> int:
    project = load_project(args.film)
    paths = project_paths(args.film)
    dag = build_dag(project, paths.root)
    state = StateStore(paths.state, paths.config).load_or_create(dag)
    budget = Budget(project.budget, RunLog(paths.run_log)).state()
    print(json.dumps({"state": state.model_dump(mode="json"), "budget": budget.model_dump()},
                     ensure_ascii=False, indent=2))
    return 0


def command_produce(args: argparse.Namespace) -> int:
    from lumen.production import (
        generate_anchors,
        generate_keyframes,
        load_context,
        render_master,
        shoot_all,
        shoot_one,
        synthesize_audio,
    )

    context = load_context(args.film)
    if args.stage == "anchors":
        result = generate_anchors(context, confirmed=args.confirm_spend, force=args.force)
    elif args.stage == "keyframes":
        result = generate_keyframes(context, confirmed=args.confirm_spend, force=args.force)
    elif args.stage == "shot":
        if not args.shot:
            raise ValueError("stage=shot requires --shot Sxx")
        result = shoot_one(context, args.shot, confirmed=args.confirm_spend)
    elif args.stage == "shots":
        result = shoot_all(context, confirmed=args.confirm_spend)
    elif args.stage == "audio":
        result = synthesize_audio(context, confirmed=args.confirm_spend)
    else:
        result = render_master(context, font_file=args.font_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_create(args: argparse.Namespace) -> int:
    from lumen.one_sentence import execute_one_sentence, plan_one_sentence

    if args.execute:
        result = execute_one_sentence(
            args.logline,
            film=args.film,
            output=args.output,
            model=args.model,
            resolution=args.resolution,
            duration=args.duration,
            confirmed=args.confirm_spend,
        )
    else:
        result = plan_one_sentence(
            args.logline,
            film=args.film,
            model=args.model,
            resolution=args.resolution,
            duration=args.duration,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return command_run(args)
        if args.command == "validate":
            return command_validate(args)
        if args.command == "status":
            return command_status(args)
        if args.command == "produce":
            return command_produce(args)
        if args.command == "create":
            return command_create(args)
    except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as exc:
        print(f"错误: {redact(str(exc))}", file=sys.stderr)
        return 2
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
