from __future__ import annotations

import pytest

from studio.app import LiveShotRequest, RequestCredentials
from studio.live_backend import EphemeralBudget, ProductionLiveBackend


def test_ephemeral_budget_is_request_local() -> None:
    first = EphemeralBudget(1)
    second = EphemeralBudget(1)
    first.charge(0.75, agent="test", model="fake")
    assert first.spent == 0.75
    assert second.spent == 0
    with pytest.raises(RuntimeError):
        first.check(0.26)


def test_preflight_is_local_and_reports_missing_ffmpeg(monkeypatch) -> None:
    monkeypatch.setattr("studio.live_backend.shutil.which", lambda _: None)
    backend = ProductionLiveBackend(RequestCredentials("model-key", "video-key"))
    result = backend.preflight(
        LiveShotRequest(
            logline="一个足够长的测试故事句子。",
            model="wan2.6-i2v-flash",
            resolution="720P",
            duration=5,
            max_cost_cny=0.75,
        )
    )
    assert result.ok is False
    assert "ffmpeg" in result.summary
    backend.close()


def test_preflight_rejects_unsupported_duration_without_network(monkeypatch) -> None:
    monkeypatch.setattr("studio.live_backend.shutil.which", lambda _: "/bin/tool")
    backend = ProductionLiveBackend(RequestCredentials("model-key", "video-key"))
    result = backend.preflight(
        LiveShotRequest(
            logline="一个足够长的测试故事句子。",
            model="wan2.6-i2v-flash",
            resolution="720P",
            duration=20,
            max_cost_cny=3,
        )
    )
    assert result.ok is False
    assert "2–15" in result.summary
    backend.close()
