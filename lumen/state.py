"""Small, inspectable checkpoint store for resumable orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from lumen.contracts import DagStep, PipelineState


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class StateStore:
    def __init__(self, path: str | Path, config_path: str | Path) -> None:
        self.path = Path(path)
        self.config_hash = sha256_file(config_path)

    def load_or_create(self, dag: list[DagStep]) -> PipelineState:
        expected = {step.id: "pending" for step in dag}
        if not self.path.exists():
            return PipelineState(
                config_sha256=self.config_hash,
                steps=expected,
                updated_at=datetime.now(UTC),
            )
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        state = PipelineState.model_validate(payload)
        if state.config_sha256 != self.config_hash:
            return PipelineState(
                config_sha256=self.config_hash,
                steps=expected,
                updated_at=datetime.now(UTC),
            )
        for step_id in expected:
            state.steps.setdefault(step_id, "pending")
        state.steps = {key: value for key, value in state.steps.items() if key in expected}
        return state

    def save(self, state: PipelineState) -> None:
        state.updated_at = datetime.now(UTC)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def mark(
        self,
        state: PipelineState,
        step_id: str,
        status: str,
        *,
        needs_human: bool = False,
    ) -> None:
        if step_id not in state.steps:
            raise KeyError(step_id)
        state.steps[step_id] = status  # type: ignore[assignment]
        if needs_human and step_id not in state.needs_human_review:
            state.needs_human_review.append(step_id)
        self.save(state)
