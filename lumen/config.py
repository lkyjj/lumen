"""Project configuration loading and path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from lumen.contracts import FilmProject, ProjectPaths


def load_project(path: str | Path) -> FilmProject:
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise FileNotFoundError(config_path)
    payload: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return FilmProject.model_validate(payload)


def project_paths(path: str | Path) -> ProjectPaths:
    config_path = Path(path).expanduser().resolve()
    root = config_path.parent
    return ProjectPaths(
        root=root,
        config=config_path,
        script=root / "01_script" / "script.json",
        shots=root / "02_shots" / "shots.json",
        bible=root / "03_bible",
        clips=root / "04_clips",
        audio=root / "05_audio",
        cut=root / "06_cut",
        run_log=root / "run.jsonl",
        state=root / ".lumen-state.json",
    )


def ensure_project_directories(paths: ProjectPaths) -> None:
    for path in (
        paths.script.parent,
        paths.shots.parent,
        paths.bible,
        paths.clips,
        paths.audio,
        paths.cut,
    ):
        path.mkdir(parents=True, exist_ok=True)
