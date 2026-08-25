"""Standardized one-sentence-to-one-reviewed-shot entry point."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from lumen.config import load_project
from lumen.production import SpendConfirmationRequired
from lumen.providers import video_capability
from studio.app import LiveShotRequest, RequestCredentials, worst_case_quote
from studio.live_backend import ProductionLiveBackend


def plan_one_sentence(
    logline: str,
    *,
    film: str | Path,
    model: str = "wan2.6-i2v-flash",
    resolution: str = "720P",
    duration: int = 5,
) -> dict[str, Any]:
    """Validate a sentence and return a zero-network execution contract."""

    sentence = logline.strip()
    if not 8 <= len(sentence) <= 500:
        raise ValueError("一句话故事长度需在 8–500 个字符之间")
    capability = video_capability(model)
    if resolution not in capability.price_cny_per_second:
        raise ValueError(f"{model} 不支持 {resolution}")
    if not 2 <= duration <= capability.max_duration:
        raise ValueError(f"时长必须在 2–{capability.max_duration} 秒之间")
    project = load_project(film)
    quote = worst_case_quote(project.budget, model, resolution, duration)
    return {
        "mode": "dry-run",
        "input": sentence,
        "task_plan": [
            {"agent": "producer", "action": "校验输入、能力和预算"},
            {"agent": "cinematographer", "action": "以批准锚点生成单镜"},
            {"agent": "critic", "action": "均匀抽取三帧并执行四维审片"},
        ],
        "model": model,
        "resolution": resolution,
        "duration_seconds": duration,
        "worst_case_cost_cny": float(quote.max_cost_cny),
        "network_called": False,
        "requires": ["MODELSCOPE_API_KEY", "DASHSCOPE_API_KEY", "--confirm-spend"],
    }


def execute_one_sentence(
    logline: str,
    *,
    film: str | Path,
    output: str | Path,
    model: str = "wan2.6-i2v-flash",
    resolution: str = "720P",
    duration: int = 5,
    confirmed: bool,
) -> dict[str, Any]:
    """Execute one paid shot with request-scoped credentials and persist evidence."""

    if not confirmed:
        raise SpendConfirmationRequired("实跑需要显式传入 --confirm-spend")
    plan = plan_one_sentence(
        logline,
        film=film,
        model=model,
        resolution=resolution,
        duration=duration,
    )
    modelscope_key = os.getenv("MODELSCOPE_API_KEY", "").strip()
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not modelscope_key or not dashscope_key:
        raise ValueError("请通过环境变量提供轮换后的 MODELSCOPE_API_KEY 和 DASHSCOPE_API_KEY")

    request = LiveShotRequest(
        logline=plan["input"],
        model=model,
        resolution=resolution,
        duration=duration,
        max_cost_cny=plan["worst_case_cost_cny"],
    )
    backend = ProductionLiveBackend(RequestCredentials(modelscope_key, dashscope_key))
    try:
        preflight = backend.preflight(request)
        if not preflight.ok:
            raise RuntimeError(preflight.summary)
        result = backend.run_one_shot(request)
        if not result.video:
            raise RuntimeError("视频后端没有返回可交付文件")
        source = Path(result.video)
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = Path(output).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        report = {
            **plan,
            "mode": "live",
            "network_called": True,
            "output": str(destination),
            "reported_cost_cny": result.cost_cny,
            "critic": dict(result.critic_evidence),
        }
        evidence_path = destination.with_suffix(".json")
        evidence_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        report["evidence"] = str(evidence_path)
        return report
    finally:
        backend.close()
