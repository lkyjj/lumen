from __future__ import annotations

from pathlib import Path

from scripts.scan_secrets import scan


def test_scan_ignores_placeholders(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "MODELSCOPE_API_KEY=ms-replace-with-a-new-token\n"
        "DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx\n",
        encoding="utf-8",
    )
    assert scan(tmp_path) == []


def test_scan_reports_location_without_exposing_value(tmp_path: Path) -> None:
    token = "ms-" + "Ab3Cd5Ef7Gh9Jk2Lm4Np6Qr8"
    (tmp_path / "bad.env").write_text(f"TOKEN={token}\n", encoding="utf-8")
    findings = scan(tmp_path)
    assert findings == [(Path("bad.env"), 1, "modelscope")]
    assert token not in repr(findings)
