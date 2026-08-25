from __future__ import annotations

import socket
from pathlib import Path

from lumen.cli import main
from lumen.config import load_project, project_paths
from lumen.orchestrator import build_dag, dag_totals, render_dry_run

FILM = Path(__file__).parents[1] / "projects" / "vanishing-light" / "film.yaml"


def test_dag_is_complete_and_within_hard_cap() -> None:
    project = load_project(FILM)
    dag = build_dag(project, FILM.parent)
    assert len(dag) == 50
    ids = {step.id for step in dag}
    assert "screenwriter" in ids
    assert "art_director.anchor.A" in ids
    assert "cinematographer.S14" in ids
    assert "critic.S14" in ids
    assert "sound_designer" in ids
    assert "editor" in ids
    expected, worst = dag_totals(dag)
    assert 0 < expected < worst < project.budget.hard_cap


def test_dry_run_report_is_explicit() -> None:
    project = load_project(FILM)
    report = render_dry_run(project, build_dag(project, FILM.parent))
    assert "50. editor" in report
    assert "未读取 API Key" in report
    assert "含最多重拍" in report


def test_cli_dry_run_has_no_network_or_state_side_effect(
    monkeypatch, capsys
) -> None:
    paths = project_paths(FILM)
    before_state = paths.state.exists()
    before_log = paths.run_log.exists()

    def forbidden_socket(*args, **kwargs):
        raise AssertionError("dry-run attempted network access")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    assert main(["run", str(FILM), "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "LUMEN DRY RUN" in output
    assert paths.state.exists() is before_state
    assert paths.run_log.exists() is before_log
