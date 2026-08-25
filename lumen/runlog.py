"""Append-only, secret-safe JSONL run logging."""

from __future__ import annotations

import json
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lumen.contracts import RunEvent

_SECRET_KEY = re.compile(r"(api[_-]?key|token|password|authorization|secret)", re.I)
_SECRET_VALUE = re.compile(
    r"(?<![A-Za-z0-9])(?:github_pat_|gh[pousr]_|ms-|sk-)[A-Za-z0-9._-]{8,}"
)


def redact(value: Any, key: str | None = None) -> Any:
    """Recursively remove credentials before anything reaches disk or stdout."""

    if key and _SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _SECRET_VALUE.sub("[REDACTED]", value)
    return value


class RunLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def append(
        self,
        *,
        event: str,
        agent: str,
        status: str,
        model: str | None = None,
        duration_ms: int | None = None,
        cost_cny: float = 0,
        details: dict[str, Any] | None = None,
    ) -> RunEvent:
        item = RunEvent(
            timestamp=datetime.now(UTC),
            event=event,
            agent=agent,
            status=status,
            model=model,
            duration_ms=duration_ms,
            cost_cny=cost_cny,
            details=redact(details or {}),
        )
        payload = redact(item.model_dump(mode="json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return item

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {self.path}:{line_number}") from exc
            events.append(redact(parsed))
        return events
