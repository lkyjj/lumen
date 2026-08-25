from __future__ import annotations

import json
from pathlib import Path

import pytest

from lumen.agents.art_director import AnchorApprovalRequired
from lumen.cli import main
from lumen.config import load_project, project_paths
from lumen.production import (
    GoNoGoRequired,
    SpendConfirmationRequired,
    load_context,
    require_go_decision,
    require_spend_confirmation,
    run_live_pipeline,
)

FILM = Path(__file__).parents[1] / "projects" / "vanishing-light" / "film.yaml"


def test_paid_stage_requires_explicit_confirmation() -> None:
    with pytest.raises(SpendConfirmationRequired):
        require_spend_confirmation(False)
    require_spend_confirmation(True)


def test_batch_requires_recorded_go(tmp_path: Path) -> None:
    config = tmp_path / "film.yaml"
    config.write_bytes(FILM.read_bytes())
    paths = project_paths(config)
    paths.bible.mkdir(parents=True)
    with pytest.raises(GoNoGoRequired):
        require_go_decision(paths)
    (paths.bible / "GO_NO_GO.json").write_text(
        json.dumps({"decision": "PLAN_B"}), encoding="utf-8"
    )
    with pytest.raises(GoNoGoRequired):
        require_go_decision(paths)
    (paths.bible / "GO_NO_GO.json").write_text(
        json.dumps({"decision": "GO", "test_shots": ["S03", "S06", "S12"]}),
        encoding="utf-8",
    )
    assert require_go_decision(paths)["decision"] == "GO"


def test_cli_refuses_paid_stage_before_provider_creation(capsys) -> None:
    assert main(["produce", str(FILM), "--stage", "anchors"]) == 2
    assert "--confirm-spend" in capsys.readouterr().err


def test_context_does_not_read_credentials(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("MODELSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    config = tmp_path / "film.yaml"
    config.write_bytes(FILM.read_bytes())
    context = load_context(config)
    assert context.project == load_project(config)
    assert context.budget.state().spent_cny == 0


def test_live_harness_stops_at_anchor_gate_without_network(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "film.yaml"
    config.write_bytes(FILM.read_bytes())
    source_project = FILM.parent
    for relative in (
        "03_bible/candidates/anchor_A_lighthouse_back_v1.png",
        "03_bible/candidates/E06_front_v1.png",
        "03_bible/candidates/E06_hands_v1.png",
        "03_bible/candidates/E06_evolved_eyes_v1.png",
    ):
        source = source_project / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())

    def forbidden_provider(*args, **kwargs):
        raise AssertionError("provider constructed before anchor approval")

    monkeypatch.setattr("lumen.production.DashScopeT2IProvider", forbidden_provider)
    with pytest.raises(AnchorApprovalRequired):
        run_live_pipeline(config, confirmed=True)
    state = json.loads((tmp_path / ".lumen-state.json").read_text(encoding="utf-8"))
    assert "art_director.anchor.A" in state["needs_human_review"]


def test_cli_live_harness_requires_confirmation(capsys) -> None:
    assert main(["run", str(FILM), "--mode", "live"]) == 2
    assert "--confirm-spend" in capsys.readouterr().err
