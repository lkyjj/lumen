from __future__ import annotations

from pathlib import Path

from lumen.runlog import RunLog, redact


def test_recursive_redaction() -> None:
    fake_github = "github_pat_" + "x" * 40
    fake_modelscope = "ms-" + "a" * 24
    fake_dashscope = "sk-" + "b" * 24
    value = {
        "api_key": fake_modelscope,
        "nested": [f"Bearer {fake_dashscope}", f"remote={fake_github}"],
        "safe": "wan3.0-video",
    }
    cleaned = redact(value)
    assert cleaned["api_key"] == "[REDACTED]"
    assert fake_dashscope not in cleaned["nested"][0]
    assert fake_github not in cleaned["nested"][1]
    assert cleaned["safe"] == "wan3.0-video"


def test_runlog_never_writes_credentials(tmp_path: Path) -> None:
    fake_token = "ms-" + "c" * 24
    path = tmp_path / "run.jsonl"
    log = RunLog(path)
    log.append(
        event="provider.error",
        agent="test",
        status="failed",
        details={"authorization": f"Bearer {fake_token}", "error": f"bad {fake_token}"},
    )
    raw = path.read_text(encoding="utf-8")
    assert fake_token not in raw
    assert raw.count("[REDACTED]") >= 2
