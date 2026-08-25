"""Gradio front end for LUMEN's local evidence and request-scoped BYOK flow.

Demo mode only reads files under one project directory. Live mode never puts a
visitor credential in process environment, module state, files, logs, or Gradio
State. A fresh backend is built for each callback and closed before it returns.
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import ROUND_UP, Decimal
from pathlib import Path
from typing import Any, Protocol

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lumen.config import load_project  # noqa: E402
from lumen.contracts import BudgetConfig  # noqa: E402
from lumen.runlog import redact  # noqa: E402

DEFAULT_FILM_YAML = REPO_ROOT / "projects" / "vanishing-light" / "film.yaml"
MAX_DEMO_FILE_BYTES = 2_000_000


@dataclass(frozen=True, slots=True)
class DemoSnapshot:
    film_yaml: str
    run_events: list[dict[str, Any]]
    critic_evidence: list[dict[str, Any]]
    final_video: str | None
    notices: tuple[str, ...]

    @property
    def run_jsonl(self) -> str:
        if not self.run_events:
            return ""
        return "\n".join(
            json.dumps(event, ensure_ascii=False, sort_keys=True)
            for event in self.run_events
        )


@dataclass(frozen=True, slots=True)
class PriceQuote:
    model: str
    resolution: str
    duration: float
    list_price_per_second: Decimal
    max_cost_cny: Decimal


@dataclass(frozen=True, slots=True)
class RequestCredentials:
    """Credentials that exist only for one callback invocation."""

    modelscope_api_key: str = field(repr=False)
    dashscope_api_key: str = field(repr=False)

    def values(self) -> tuple[str, str]:
        return self.modelscope_api_key, self.dashscope_api_key


@dataclass(frozen=True, slots=True)
class LiveShotRequest:
    logline: str
    model: str
    resolution: str
    duration: float
    max_cost_cny: float


@dataclass(frozen=True, slots=True)
class PreflightResult:
    ok: bool
    summary: str
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OneShotResult:
    summary: str
    cost_cny: float
    video: str | None = None
    critic_evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LiveUiResult:
    ok: bool
    status_markdown: str
    evidence: Mapping[str, Any] = field(default_factory=dict)
    video: str | None = None


class LiveBackend(Protocol):
    """Request-local backend contract for external services.

    ``preflight`` must be non-billable. ``run_one_shot`` must enforce the
    request's ``max_cost_cny`` before it creates any paid task. Implementations
    must not log or persist credentials and should release clients in ``close``.
    """

    def preflight(self, request: LiveShotRequest) -> PreflightResult: ...

    def run_one_shot(self, request: LiveShotRequest) -> OneShotResult: ...

    def close(self) -> None: ...


BackendFactory = Callable[[RequestCredentials], LiveBackend]


class LiveInputError(ValueError):
    """A safe validation error that can be shown to a visitor."""


class BackendContractError(RuntimeError):
    """Raised when an injected backend violates the request boundary."""


class UnconfiguredBackend:
    """Safe default: local validation only, with no network activity."""

    def preflight(self, request: LiveShotRequest) -> PreflightResult:
        return PreflightResult(
            ok=False,
            summary="外部单镜后端尚未配置；本地输入与价格检查已通过，未发起网络请求。",
            details={
                "mode": "local-preflight-only",
                "model": request.model,
                "resolution": request.resolution,
                "duration": request.duration,
                "max_cost_cny": request.max_cost_cny,
            },
        )

    def run_one_shot(self, request: LiveShotRequest) -> OneShotResult:
        raise BackendContractError("external single-shot backend is not configured")

    def close(self) -> None:
        return None


def unconfigured_backend_factory(credentials: RequestCredentials) -> LiveBackend:
    """Return the zero-network backend without retaining ``credentials``."""

    return UnconfiguredBackend()


def _bounded_text(path: Path, *, missing: str, notices: list[str]) -> str:
    if not path.is_file():
        notices.append(f"缺少 {path.name}，该区域使用空状态展示。")
        return missing
    if path.stat().st_size > MAX_DEMO_FILE_BYTES:
        notices.append(f"{path.name} 超过演示读取上限，未加载。")
        return missing
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        notices.append(f"{path.name} 无法读取，未影响其他演示内容。")
        return missing
    safe = redact(text)
    return safe if isinstance(safe, str) else missing


def _load_run_events(path: Path, notices: list[str]) -> list[dict[str, Any]]:
    if not path.is_file():
        notices.append("尚无 run.jsonl；运行和审片证据将在生成后出现。")
        return []
    if path.stat().st_size > MAX_DEMO_FILE_BYTES:
        notices.append("run.jsonl 超出演示读取上限，未加载。")
        return []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        notices.append("run.jsonl 无法读取，未影响 film.yaml 或成片展示。")
        return []

    events: list[dict[str, Any]] = []
    invalid_lines: list[int] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines.append(line_number)
            continue
        if not isinstance(payload, dict):
            invalid_lines.append(line_number)
            continue
        safe = redact(payload)
        if isinstance(safe, dict):
            events.append(safe)
    if invalid_lines:
        rendered = ", ".join(str(line) for line in invalid_lines[:8])
        suffix = "…" if len(invalid_lines) > 8 else ""
        notices.append(f"run.jsonl 的第 {rendered}{suffix} 行无效，已跳过。")
    return events


def _critic_evidence(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    critic_fields = {"scores", "overall", "passed", "critique", "fix_hint"}
    for event in events:
        details = event.get("details")
        details = details if isinstance(details, dict) else {}
        agent = str(event.get("agent", "")).lower()
        event_name = str(event.get("event", "")).lower()
        if (
            "critic" not in agent
            and "critic" not in event_name
            and not critic_fields.intersection(details)
        ):
            continue
        item = {
            "timestamp": event.get("timestamp"),
            "shot_id": details.get("shot_id", event.get("shot_id")),
            "attempt": details.get("attempt", event.get("attempt")),
            "scores": details.get("scores", event.get("scores")),
            "overall": details.get("overall", event.get("overall")),
            "passed": details.get("passed", event.get("passed")),
            "critique": details.get("critique", event.get("critique")),
            "fix_hint": details.get("fix_hint", event.get("fix_hint")),
            "clip": details.get("clip_path", details.get("clip")),
        }
        evidence.append({key: value for key, value in item.items() if value is not None})
    return evidence


def load_demo_snapshot(project_dir: str | Path) -> DemoSnapshot:
    """Read demo artifacts locally; this function has no backend or network path."""

    root = Path(project_dir).expanduser().resolve()
    notices: list[str] = []
    film_yaml = _bounded_text(
        root / "film.yaml",
        missing="# film.yaml 尚未生成或不可读取。",
        notices=notices,
    )
    events = _load_run_events(root / "run.jsonl", notices)
    evidence = _critic_evidence(events)
    if not evidence:
        notices.append("尚无可展示的审片证据。")

    final_candidates = (
        root / "06_cut" / "generated" / "final.mp4",
        root / "06_cut" / "final.mp4",
    )
    final_path = next((path for path in final_candidates if path.is_file()), None)
    final_video = str(final_path) if final_path is not None else None
    if final_video is None:
        notices.append("最终成片尚不存在；film.yaml 与现有证据仍可浏览。")

    return DemoSnapshot(
        film_yaml=film_yaml,
        run_events=events,
        critic_evidence=evidence,
        final_video=final_video,
        notices=tuple(notices),
    )


def worst_case_quote(
    budget: BudgetConfig,
    model: str,
    resolution: str,
    duration: float,
) -> PriceQuote:
    """Quote list-price video cost, deliberately ignoring unconfirmed discounts."""

    if not math.isfinite(float(duration)) or float(duration) <= 0:
        raise LiveInputError("镜头时长必须是大于零的有限数值。")
    try:
        raw_unit_price = budget.pricing.video_cny_per_second[model][resolution]
    except KeyError as exc:
        raise LiveInputError(f"当前价格表不支持 {model} / {resolution}。") from exc

    unit_price = Decimal(str(raw_unit_price))
    amount = (unit_price * Decimal(str(duration))).quantize(
        Decimal("0.01"), rounding=ROUND_UP
    )
    return PriceQuote(
        model=model,
        resolution=resolution,
        duration=float(duration),
        list_price_per_second=unit_price,
        max_cost_cny=amount,
    )


def format_quote(budget: BudgetConfig, model: str, resolution: str, duration: float) -> str:
    try:
        quote = worst_case_quote(budget, model, resolution, duration)
    except LiveInputError as exc:
        return f"### 当前组合无法报价\n\n{exc} 请更换模型或分辨率。"
    return (
        f"### 当前单镜最坏价格：**¥{quote.max_cost_cny:.2f} CNY**\n\n"
        f"{quote.model} · {quote.resolution} · {quote.duration:g} 秒 · "
        f"配置表原价 ¥{quote.list_price_per_second:.2f}/秒。"
        "报价不采用未确认优惠，只覆盖当前单镜视频接口；后端不得增加未报价的"
        "图像、声音或额外镜头调用。实际价格仍以服务商确认页为准。"
    )


def _request_data(
    *,
    modelscope_key: str,
    dashscope_key: str,
    logline: str,
    model: str,
    resolution: str,
    duration: float,
    budget: BudgetConfig,
) -> tuple[RequestCredentials, LiveShotRequest]:
    ms_value = modelscope_key.strip()
    ds_value = dashscope_key.strip()
    if not ms_value or not ds_value:
        raise LiveInputError("请提供本次请求所需的两项 BYOK 凭据。")
    clean_logline = logline.strip()
    if not 8 <= len(clean_logline) <= 500:
        raise LiveInputError("一句话故事长度需在 8–500 个字符之间。")
    quote = worst_case_quote(budget, model, resolution, duration)
    if quote.max_cost_cny > Decimal(str(budget.hard_cap)):
        raise LiveInputError("当前单镜最坏价格超过项目硬上限。")
    credentials = RequestCredentials(ms_value, ds_value)
    request = LiveShotRequest(
        logline=clean_logline,
        model=model,
        resolution=resolution,
        duration=float(duration),
        max_cost_cny=float(quote.max_cost_cny),
    )
    return credentials, request


def _scrub(value: Any, credentials: RequestCredentials) -> Any:
    safe = redact(value)
    secrets = tuple(secret for secret in credentials.values() if secret)
    if isinstance(safe, str):
        for secret in secrets:
            safe = safe.replace(secret, "[REDACTED]")
        return safe
    if isinstance(safe, dict):
        return {str(key): _scrub(item, credentials) for key, item in safe.items()}
    if isinstance(safe, (list, tuple)):
        return [_scrub(item, credentials) for item in safe]
    return safe


def _close_backend(backend: LiveBackend | None) -> None:
    if backend is None:
        return
    try:
        backend.close()
    except Exception:
        # Closing is best-effort and must never expose backend details or credentials.
        return


def preflight_live_request(
    *,
    modelscope_key: str,
    dashscope_key: str,
    logline: str,
    model: str,
    resolution: str,
    duration: float,
    budget: BudgetConfig,
    backend_factory: BackendFactory = unconfigured_backend_factory,
) -> LiveUiResult:
    """Run non-billable checks with one request-local backend instance."""

    backend: LiveBackend | None = None
    try:
        credentials, request = _request_data(
            modelscope_key=modelscope_key,
            dashscope_key=dashscope_key,
            logline=logline,
            model=model,
            resolution=resolution,
            duration=duration,
            budget=budget,
        )
        backend = backend_factory(credentials)
        result = backend.preflight(request)
        if not isinstance(result, PreflightResult):
            raise BackendContractError("preflight returned an unsupported result")
        summary = _scrub(result.summary, credentials)
        details = _scrub(dict(result.details), credentials)
        icon = "✅" if result.ok else "⚠️"
        return LiveUiResult(
            ok=result.ok,
            status_markdown=f"{icon} **安全预检**：{summary}",
            evidence=details if isinstance(details, dict) else {},
        )
    except LiveInputError as exc:
        return LiveUiResult(ok=False, status_markdown=f"⚠️ **输入未通过**：{exc}")
    except Exception as exc:
        return LiveUiResult(
            ok=False,
            status_markdown=(
                "❌ **安全预检失败**：后端未通过检查。"
                f"错误类型：`{type(exc).__name__}`。未显示后端错误内容。"
            ),
        )
    finally:
        _close_backend(backend)


def _safe_video_value(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith(("https://", "http://")):
        return value
    path = Path(value).expanduser()
    return str(path.resolve()) if path.is_file() else None


def execute_live_request(
    *,
    confirmed: bool,
    modelscope_key: str,
    dashscope_key: str,
    logline: str,
    model: str,
    resolution: str,
    duration: float,
    budget: BudgetConfig,
    backend_factory: BackendFactory = unconfigured_backend_factory,
) -> LiveUiResult:
    """Preflight then run one quoted shot; no credential escapes this call."""

    if not confirmed:
        return LiveUiResult(
            ok=False,
            status_markdown="⚠️ 请先阅读动态最坏价格，并勾选确认后再实跑。",
        )

    backend: LiveBackend | None = None
    try:
        credentials, request = _request_data(
            modelscope_key=modelscope_key,
            dashscope_key=dashscope_key,
            logline=logline,
            model=model,
            resolution=resolution,
            duration=duration,
            budget=budget,
        )
        backend = backend_factory(credentials)
        preflight = backend.preflight(request)
        if not isinstance(preflight, PreflightResult):
            raise BackendContractError("preflight returned an unsupported result")
        if not preflight.ok:
            summary = _scrub(preflight.summary, credentials)
            details = _scrub(dict(preflight.details), credentials)
            return LiveUiResult(
                ok=False,
                status_markdown=f"⚠️ **未生成**：安全预检未通过。{summary}",
                evidence=details if isinstance(details, dict) else {},
            )

        result = backend.run_one_shot(request)
        if not isinstance(result, OneShotResult):
            raise BackendContractError("single-shot call returned an unsupported result")
        reported_cost = Decimal(str(result.cost_cny))
        quoted_cost = Decimal(str(request.max_cost_cny))
        if not reported_cost.is_finite() or reported_cost < 0 or reported_cost > quoted_cost:
            raise BackendContractError("backend reported cost outside the confirmed quote")

        summary = _scrub(result.summary, credentials)
        evidence = _scrub(dict(result.critic_evidence), credentials)
        video = _safe_video_value(result.video)
        media_note = ""
        if result.video and video is None:
            media_note = " 返回的本地素材不存在，已隐藏播放器。"
        return LiveUiResult(
            ok=True,
            status_markdown=(
                f"✅ **单镜完成**：{summary} 本次后端报告费用 "
                f"¥{reported_cost:.2f}，不高于已确认上限 ¥{quoted_cost:.2f}.{media_note}"
            ),
            evidence=evidence if isinstance(evidence, dict) else {},
            video=video,
        )
    except LiveInputError as exc:
        return LiveUiResult(ok=False, status_markdown=f"⚠️ **输入未通过**：{exc}")
    except Exception as exc:
        return LiveUiResult(
            ok=False,
            status_markdown=(
                "❌ **单镜失败**：请求已停止。"
                f"错误类型：`{type(exc).__name__}`。未显示后端错误内容。"
            ),
        )
    finally:
        _close_backend(backend)


def _notice_markdown(snapshot: DemoSnapshot) -> str:
    if not snapshot.notices:
        return "✅ 本地演示素材齐全。"
    return "\n".join(f"- {notice}" for notice in snapshot.notices)


def build_app(
    *,
    project_config: str | Path = DEFAULT_FILM_YAML,
    backend_factory: BackendFactory | None = None,
) -> Any:
    """Build the two-tab Gradio app without constructing an external backend."""

    import gradio as gr

    if backend_factory is None:
        from studio.live_backend import production_backend_factory

        backend_factory = production_backend_factory

    config_path = Path(project_config).expanduser().resolve()
    snapshot = load_demo_snapshot(config_path.parent)
    project = None
    config_error: str | None = None
    try:
        project = load_project(config_path)
    except Exception as exc:
        config_error = type(exc).__name__

    budget = project.budget if project is not None else None
    if budget is not None:
        models = list(budget.pricing.video_cny_per_second)
        resolutions = sorted(
            {
                resolution
                for prices in budget.pricing.video_cny_per_second.values()
                for resolution in prices
            }
        )
        default_model = (
            budget.video_model if budget.video_model in models else models[0]
        )
        default_resolution = project.film.resolution
        if default_resolution not in resolutions:
            default_resolution = resolutions[0]
        initial_quote = format_quote(budget, default_model, default_resolution, 5)
        default_logline = project.film.logline
    else:
        models = ["unavailable"]
        resolutions = ["720P"]
        default_model = models[0]
        default_resolution = resolutions[0]
        initial_quote = "### 暂时无法报价\n\n项目配置不可用，实跑模式已安全停用。"
        default_logline = ""

    def update_quote(model: str, resolution: str, duration: float) -> tuple[str, bool]:
        if budget is None:
            return initial_quote, False
        return format_quote(budget, model, resolution, duration), False

    def run_preflight_ui(
        ms_key: str,
        ds_key: str,
        logline: str,
        model: str,
        resolution: str,
        duration: float,
    ) -> tuple[str, Mapping[str, Any], str, str, bool]:
        if budget is None:
            result = LiveUiResult(
                ok=False,
                status_markdown=(
                    "⚠️ 项目配置不可用，预检未运行。"
                    f"错误类型：`{config_error or 'UnknownError'}`。"
                ),
            )
        else:
            result = preflight_live_request(
                modelscope_key=ms_key,
                dashscope_key=ds_key,
                logline=logline,
                model=model,
                resolution=resolution,
                duration=duration,
                budget=budget,
                backend_factory=backend_factory,
            )
        return result.status_markdown, result.evidence, "", "", False

    def run_one_shot_ui(
        ms_key: str,
        ds_key: str,
        logline: str,
        model: str,
        resolution: str,
        duration: float,
        confirmed: bool,
    ) -> tuple[str, str | None, Mapping[str, Any], str, str, bool]:
        if budget is None:
            result = LiveUiResult(
                ok=False,
                status_markdown=(
                    "⚠️ 项目配置不可用，实跑未运行。"
                    f"错误类型：`{config_error or 'UnknownError'}`。"
                ),
            )
        else:
            result = execute_live_request(
                confirmed=confirmed,
                modelscope_key=ms_key,
                dashscope_key=ds_key,
                logline=logline,
                model=model,
                resolution=resolution,
                duration=duration,
                budget=budget,
                backend_factory=backend_factory,
            )
        return (
            result.status_markdown,
            result.video,
            result.evidence,
            "",
            "",
            False,
        )

    with gr.Blocks(
        title="LUMEN · 一个人的 AI 电影剧组",
        analytics_enabled=False,
    ) as demo:
        gr.Markdown("# LUMEN\n### 一个人的 AI 电影剧组 ·《消失的光芒》")

        with gr.Tab("演示模式（零成本）"):
            gr.Markdown(
                "该页只读取仓库中的预生成文件，不接受 Key、不调用模型、不创建远程任务。"
            )
            gr.Markdown(_notice_markdown(snapshot))
            gr.Video(
                value=snapshot.final_video,
                label="最终成片（存在时显示）",
                interactive=False,
            )
            with gr.Accordion("电影的源代码 · film.yaml", open=True):
                gr.Code(value=snapshot.film_yaml, language="yaml", interactive=False)
            with gr.Accordion("运行账本 · run.jsonl（已脱敏）", open=False):
                gr.Code(value=snapshot.run_jsonl, language="json", interactive=False)
            gr.Markdown("## 审片闭环证据")
            gr.JSON(value=snapshot.critic_evidence, label="尝试、评分、打回理由与修正建议")

        with gr.Tab("实跑模式（请求级 BYOK）"):
            gr.Markdown(
                "> 🔒 两项凭据仅传给当前回调创建的后端实例；不会写入环境变量、"
                "文件、日志或跨请求状态。每次预检或实跑后输入框都会清空。\n\n"
                "当前边界是**非计费安全预检 + 单个视频镜头**。不运行未报价的图像、"
                "声音或额外镜头步骤。"
            )
            with gr.Row():
                ms_key = gr.Textbox(label="魔搭 BYOK", type="password")
                ds_key = gr.Textbox(label="百炼 BYOK", type="password")
            logline = gr.Textbox(
                label="一句话故事",
                value=default_logline,
                lines=3,
                max_lines=6,
            )
            with gr.Row():
                model = gr.Dropdown(models, value=default_model, label="视频模型")
                resolution = gr.Dropdown(
                    resolutions,
                    value=default_resolution,
                    label="分辨率",
                )
                duration = gr.Slider(
                    minimum=2,
                    maximum=30,
                    value=5,
                    step=1,
                    label="单镜时长（秒）",
                )
            quote = gr.Markdown(initial_quote)
            confirmed = gr.Checkbox(
                label="我已阅读并确认上方当前最坏价格",
                value=False,
            )
            with gr.Row():
                preflight_button = gr.Button("安全预检（不计费）")
                run_button = gr.Button("确认后实跑一个镜头", variant="primary")
            status = gr.Markdown("尚未发起请求。")
            live_video = gr.Video(label="本次单镜结果", interactive=False)
            live_evidence = gr.JSON(label="预检详情 / 审片结果")

            quote_inputs = [model, resolution, duration]
            for component in quote_inputs:
                component.change(
                    fn=update_quote,
                    inputs=quote_inputs,
                    outputs=[quote, confirmed],
                    queue=False,
                    api_visibility="private",
                )

            live_inputs = [ms_key, ds_key, logline, model, resolution, duration]
            preflight_button.click(
                fn=run_preflight_ui,
                inputs=live_inputs,
                outputs=[status, live_evidence, ms_key, ds_key, confirmed],
                concurrency_limit=4,
                concurrency_id="request-scoped-byok",
                api_visibility="private",
            )
            run_button.click(
                fn=run_one_shot_ui,
                inputs=[*live_inputs, confirmed],
                outputs=[
                    status,
                    live_video,
                    live_evidence,
                    ms_key,
                    ds_key,
                    confirmed,
                ],
                concurrency_limit=4,
                concurrency_id="request-scoped-byok",
                api_visibility="private",
            )

    return demo.queue(default_concurrency_limit=4)


def _launch_port() -> int:
    raw = os.getenv("PORT") or os.getenv("GRADIO_SERVER_PORT") or "7860"
    try:
        value = int(raw)
    except ValueError:
        return 7860
    return value if 1 <= value <= 65535 else 7860


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=_launch_port())
