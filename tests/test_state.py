from __future__ import annotations

from pathlib import Path

from lumen.config import load_project
from lumen.orchestrator import build_dag
from lumen.state import StateStore

FILM = Path(__file__).parents[1] / "projects" / "vanishing-light" / "film.yaml"


def test_state_store_resumes_matching_config(tmp_path: Path) -> None:
    config = tmp_path / "film.yaml"
    config.write_bytes(FILM.read_bytes())
    project = load_project(config)
    dag = build_dag(project, tmp_path)
    store = StateStore(tmp_path / "state.json", config)
    state = store.load_or_create(dag)
    store.mark(state, "screenwriter", "succeeded")
    resumed = store.load_or_create(dag)
    assert resumed.steps["screenwriter"] == "succeeded"


def test_state_store_invalidates_when_config_changes(tmp_path: Path) -> None:
    config = tmp_path / "film.yaml"
    config.write_bytes(FILM.read_bytes())
    project = load_project(config)
    dag = build_dag(project, tmp_path)
    store = StateStore(tmp_path / "state.json", config)
    state = store.load_or_create(dag)
    store.mark(state, "screenwriter", "succeeded")
    config.write_text(config.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    reset = StateStore(tmp_path / "state.json", config).load_or_create(dag)
    assert reset.steps["screenwriter"] == "pending"
