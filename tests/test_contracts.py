from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from lumen.config import load_project
from lumen.contracts import CriticScores, CriticVerdict, FilmProject

FILM = Path(__file__).parents[1] / "projects" / "vanishing-light" / "film.yaml"


def test_frozen_film_contract_is_complete() -> None:
    project = load_project(FILM)
    assert project.film.title == "消失的光芒"
    assert len(project.shots) == 14
    assert project.shots_duration == 95
    assert project.film.title_cards_duration == 5
    assert project.film.duration_target == 100
    assert {anchor.id for anchor in project.anchors} == {"A", "B", "HANDS", "EVOLVED_EYES"}
    assert next(shot for shot in project.shots if shot.id == "S11").anchor == "B"


def test_contract_rejects_unknown_anchor() -> None:
    payload = yaml.safe_load(FILM.read_text(encoding="utf-8"))
    broken = deepcopy(payload)
    broken["shots"][0]["anchor"] = "MISSING"
    broken["shots"][0]["reference_type"] = "first_frame"
    with pytest.raises(ValidationError, match="unknown anchor"):
        FilmProject.model_validate(broken)


def test_contract_rejects_duration_drift() -> None:
    payload = yaml.safe_load(FILM.read_text(encoding="utf-8"))
    broken = deepcopy(payload)
    broken["shots"][0]["duration"] = 8
    with pytest.raises(ValidationError, match="duration_target"):
        FilmProject.model_validate(broken)


def test_critic_adjudication_ignores_model_boolean() -> None:
    project = load_project(FILM)
    verdict = CriticVerdict.adjudicate(
        scores=CriticScores(
            character_consistency=5.9,
            composition=9,
            lighting=9,
            integrity=9,
        ),
        critique="角色特征不一致",
        fix_hint="把人物左眼光学元件特征放到提示词首句",
        gate=project.quality_gate,
    )
    assert verdict.overall > 7
    assert verdict.passed is False
