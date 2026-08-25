"""Persistent budget circuit breaker for every paid provider call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lumen.contracts import BudgetConfig, BudgetState
from lumen.runlog import RunLog


class BudgetExceeded(RuntimeError):
    """Raised before a request when the configured hard cap would be exceeded."""


@dataclass(frozen=True)
class BudgetSnapshot:
    spent: float
    reserved: float
    remaining: float
    hard_cap: float
    warn_at: float


class Budget:
    def __init__(self, config: BudgetConfig, run_log: RunLog) -> None:
        self.config = config
        self.run_log = run_log
        self.spent = round(
            sum(float(event.get("cost_cny", 0)) for event in run_log.read()), 2
        )
        self._reserved = 0.0

    def check(self, amount: float, *, note: str = "") -> None:
        amount = self._validate_amount(amount)
        projected = self.spent + self._reserved + amount
        if projected > self.config.hard_cap:
            raise BudgetExceeded(
                f"本次需 ¥{amount:.2f}，已花/预留 ¥{self.spent + self._reserved:.2f}，"
                f"上限 ¥{self.config.hard_cap:.2f}。已停止。"
            )

    def reserve(self, amount: float, *, note: str = "") -> None:
        amount = self._validate_amount(amount)
        self.check(amount, note=note)
        self._reserved = round(self._reserved + amount, 2)

    def release(self, amount: float) -> None:
        amount = self._validate_amount(amount)
        self._reserved = round(max(0.0, self._reserved - amount), 2)

    def charge(
        self,
        amount: float,
        *,
        agent: str,
        model: str,
        note: str = "",
        details: dict[str, Any] | None = None,
        reserved: bool = False,
    ) -> None:
        amount = self._validate_amount(amount)
        if reserved:
            self.release(amount)
        else:
            self.check(amount, note=note)
        self.spent = round(self.spent + amount, 2)
        self.run_log.append(
            event="budget.charge",
            agent=agent,
            status="succeeded",
            model=model,
            cost_cny=amount,
            details={"note": note, **(details or {})},
        )

    def snapshot(self) -> BudgetSnapshot:
        return BudgetSnapshot(
            spent=self.spent,
            reserved=self._reserved,
            remaining=round(self.config.hard_cap - self.spent - self._reserved, 2),
            hard_cap=self.config.hard_cap,
            warn_at=self.config.warn_at,
        )

    def state(self) -> BudgetState:
        snapshot = self.snapshot()
        return BudgetState(
            spent_cny=snapshot.spent,
            reserved_cny=snapshot.reserved,
            remaining_cny=snapshot.remaining,
            hard_cap_cny=snapshot.hard_cap,
            warning_reached=snapshot.spent >= snapshot.warn_at,
        )

    @staticmethod
    def _validate_amount(amount: float) -> float:
        value = round(float(amount), 2)
        if value < 0:
            raise ValueError("budget amount must be non-negative")
        return value
