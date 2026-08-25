from __future__ import annotations

from pathlib import Path

import pytest

from lumen.budget import Budget, BudgetExceeded
from lumen.contracts import BudgetConfig
from lumen.runlog import RunLog


def test_budget_breaker_runs_before_charge(tmp_path: Path) -> None:
    log = RunLog(tmp_path / "run.jsonl")
    budget = Budget(BudgetConfig(hard_cap=1, warn_at=0.5), log)
    budget.check(0.75)
    budget.charge(0.75, agent="test", model="fake", note="fixture")
    with pytest.raises(BudgetExceeded):
        budget.check(0.26)
    assert budget.snapshot().spent == 0.75
    assert len(log.read()) == 1


def test_budget_recovers_from_append_only_log(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    first = Budget(BudgetConfig(hard_cap=10, warn_at=8), RunLog(path))
    first.charge(2.25, agent="cinematographer", model="fake")
    resumed = Budget(BudgetConfig(hard_cap=10, warn_at=8), RunLog(path))
    assert resumed.state().spent_cny == 2.25
    assert resumed.state().remaining_cny == 7.75


def test_reservation_prevents_parallel_overspend(tmp_path: Path) -> None:
    budget = Budget(BudgetConfig(hard_cap=2, warn_at=1), RunLog(tmp_path / "run.jsonl"))
    budget.reserve(1.5)
    with pytest.raises(BudgetExceeded):
        budget.reserve(0.51)
    budget.charge(1.5, agent="art_director", model="fake", reserved=True)
    assert budget.snapshot().reserved == 0
    assert budget.snapshot().spent == 1.5
