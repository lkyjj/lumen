from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lumen.contracts import BudgetConfig, PricingConfig
from studio import app


def _budget(*, price: float = 1.23, discount: float = 0.1) -> BudgetConfig:
    return BudgetConfig(
        hard_cap=100,
        warn_at=50,
        video_model="test-video",
        pricing=PricingConfig(
            video_cny_per_second={"test-video": {"720P": price}},
            image_cny_each=9.99,
            discount_multiplier=discount,
        ),
    )


def test_demo_missing_assets_degrades_without_backend(tmp_path: Path) -> None:
    snapshot = app.load_demo_snapshot(tmp_path)

    assert "尚未生成" in snapshot.film_yaml
    assert snapshot.run_events == []
    assert snapshot.critic_evidence == []
    assert snapshot.final_video is None
    assert any("final" in notice or "成片" in notice for notice in snapshot.notices)


def test_demo_reads_redacted_runlog_and_critic_evidence(tmp_path: Path) -> None:
    (tmp_path / "film.yaml").write_text("film:\n  title: demo\n", encoding="utf-8")
    event = {
        "timestamp": "2026-08-26T00:00:00Z",
        "event": "critic.review",
        "agent": "critic",
        "status": "succeeded",
        "details": {
            "shot_id": "S01",
            "attempt": 1,
            "overall": 5.5,
            "passed": False,
            "critique": "构图偏离",
            "fix_hint": "固定机位",
            "api_key": "not-a-real-value",
        },
    }
    (tmp_path / "run.jsonl").write_text(
        json.dumps(event, ensure_ascii=False) + "\nnot-json\n",
        encoding="utf-8",
    )
    final = tmp_path / "06_cut" / "final.mp4"
    final.parent.mkdir()
    final.write_bytes(b"placeholder")

    snapshot = app.load_demo_snapshot(tmp_path)

    assert snapshot.final_video == str(final)
    assert snapshot.run_events[0]["details"]["api_key"] == "[REDACTED]"
    assert snapshot.critic_evidence[0]["shot_id"] == "S01"
    assert snapshot.critic_evidence[0]["fix_hint"] == "固定机位"
    assert any("第 2" in notice for notice in snapshot.notices)


def test_quote_uses_configured_list_price_and_ignores_discount() -> None:
    budget = _budget(price=1.23, discount=0.1)

    quote = app.worst_case_quote(budget, "test-video", "720P", 3)
    markdown = app.format_quote(budget, "test-video", "720P", 3)

    assert str(quote.max_cost_cny) == "3.69"
    assert "¥3.69" in markdown
    assert "0.42" not in markdown
    assert "不采用未确认优惠" in markdown


def test_unconfirmed_request_never_constructs_backend() -> None:
    called = False

    def factory(credentials: app.RequestCredentials) -> app.LiveBackend:
        nonlocal called
        called = True
        return app.UnconfiguredBackend()

    result = app.execute_live_request(
        confirmed=False,
        modelscope_key="request-model-key",
        dashscope_key="request-video-key",
        logline="这是一个足够长且可验证的一句话故事。",
        model="test-video",
        resolution="720P",
        duration=3,
        budget=_budget(),
        backend_factory=factory,
    )

    assert not result.ok
    assert not called
    assert "确认" in result.status_markdown


def test_preflight_failure_prevents_paid_method() -> None:
    class Backend:
        ran = False

        def preflight(self, request: app.LiveShotRequest) -> app.PreflightResult:
            return app.PreflightResult(ok=False, summary="鉴权未通过")

        def run_one_shot(self, request: app.LiveShotRequest) -> app.OneShotResult:
            self.ran = True
            raise AssertionError("must not run")

        def close(self) -> None:
            return None

    backend = Backend()
    result = app.execute_live_request(
        confirmed=True,
        modelscope_key="request-model-key",
        dashscope_key="request-video-key",
        logline="这是一个足够长且可验证的一句话故事。",
        model="test-video",
        resolution="720P",
        duration=3,
        budget=_budget(),
        backend_factory=lambda credentials: backend,
    )

    assert not result.ok
    assert not backend.ran
    assert "未生成" in result.status_markdown


def test_concurrent_byok_requests_are_isolated_and_never_touch_environment() -> None:
    barrier = threading.Barrier(2)
    created: list[tuple[int, str]] = []
    created_lock = threading.Lock()

    class Backend:
        def __init__(self, marker: str, credential_id: int) -> None:
            self.marker = marker
            self.credential_id = credential_id

        def preflight(self, request: app.LiveShotRequest) -> app.PreflightResult:
            barrier.wait(timeout=3)
            return app.PreflightResult(ok=True, summary=f"{self.marker} ready")

        def run_one_shot(self, request: app.LiveShotRequest) -> app.OneShotResult:
            return app.OneShotResult(
                summary=f"{self.marker} complete",
                cost_cny=request.max_cost_cny,
                critic_evidence={"request": self.marker},
            )

        def close(self) -> None:
            return None

    def factory(credentials: app.RequestCredentials) -> app.LiveBackend:
        marker = "A" if credentials.modelscope_api_key.endswith("alpha") else "B"
        with created_lock:
            created.append((id(credentials), marker))
        return Backend(marker, id(credentials))

    environment_before = dict(os.environ)

    def invoke(suffix: str) -> app.LiveUiResult:
        return app.execute_live_request(
            confirmed=True,
            modelscope_key=f"model-{suffix}",
            dashscope_key=f"video-{suffix}",
            logline="这是一个足够长且可验证的一句话故事。",
            model="test-video",
            resolution="720P",
            duration=3,
            budget=_budget(),
            backend_factory=factory,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(invoke, ["alpha", "beta"]))

    assert all(result.ok for result in results)
    assert {result.evidence["request"] for result in results} == {"A", "B"}
    assert len({credential_id for credential_id, _ in created}) == 2
    assert dict(os.environ) == environment_before


def test_backend_output_cannot_echo_request_credentials() -> None:
    model_key = "model-request-secret"
    video_key = "video-request-secret"

    class Backend:
        def preflight(self, request: app.LiveShotRequest) -> app.PreflightResult:
            return app.PreflightResult(ok=True, summary="ready")

        def run_one_shot(self, request: app.LiveShotRequest) -> app.OneShotResult:
            return app.OneShotResult(
                summary=f"used {model_key}",
                cost_cny=0,
                critic_evidence={"authorization": video_key},
            )

        def close(self) -> None:
            return None

    result = app.execute_live_request(
        confirmed=True,
        modelscope_key=model_key,
        dashscope_key=video_key,
        logline="这是一个足够长且可验证的一句话故事。",
        model="test-video",
        resolution="720P",
        duration=3,
        budget=_budget(),
        backend_factory=lambda credentials: Backend(),
    )

    rendered = f"{result.status_markdown} {result.evidence}"
    assert result.ok
    assert model_key not in rendered
    assert video_key not in rendered
    assert "[REDACTED]" in rendered

