#!/usr/bin/env python3
"""Offline, machine-readable submission readiness audit."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FILM = ROOT / "projects" / "vanishing-light" / "film.yaml"
PROJECT = FILM.parent


def _placeholder_hits() -> list[str]:
    hits: list[str] = []
    for path in sorted((ROOT / "docs").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"待填证据|TODO|TBD", text, flags=re.IGNORECASE):
            hits.append(str(path.relative_to(ROOT)))
    return hits


def audit() -> dict[str, object]:
    payload = yaml.safe_load(FILM.read_text(encoding="utf-8"))
    anchors = payload.get("anchors", [])
    required = [
        "README.md",
        "LICENSE",
        "app.py",
        "requirements.txt",
        "studio/app.py",
        "notebooks/LUMEN_Quickstart.ipynb",
        "docs/RUBRIC_COMPLIANCE.md",
        ".github/workflows/ci.yml",
    ]
    missing = [item for item in required if not (ROOT / item).is_file()]
    final = PROJECT / "06_cut" / "generated" / "final.mp4"
    demo = PROJECT / "06_cut" / "generated" / "demo_15s_v1.mp4"
    go = PROJECT / "03_bible" / "GO_NO_GO.json"
    blockers: list[str] = []
    pending_anchors = [str(item.get("id")) for item in anchors if not item.get("approved")]
    if pending_anchors:
        blockers.append("视觉锚点未批准：" + ", ".join(pending_anchors))
    if not go.is_file():
        blockers.append("缺少人工试拍决策 GO_NO_GO.json")
    if not final.is_file():
        blockers.append("完整成片 final.mp4 尚未生成")
    placeholders = _placeholder_hits()
    if placeholders:
        blockers.append("创作说明仍有证据占位符")
    return {
        "static_repository_ready": not missing,
        "missing_required_files": missing,
        "demo_15s_present": demo.is_file(),
        "final_film_present": final.is_file(),
        "approved_anchors": len(anchors) - len(pending_anchors),
        "total_anchors": len(anchors),
        "evidence_placeholders": placeholders,
        "human_or_paid_blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="存在任何缺口时返回非零")
    args = parser.parse_args()
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    has_gap = bool(result["missing_required_files"] or result["human_or_paid_blockers"])
    return 1 if args.strict and has_gap else 0


if __name__ == "__main__":
    raise SystemExit(main())
