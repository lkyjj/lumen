#!/usr/bin/env python3
"""Conservative repository secret scan that never prints matched values."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERNS = {
    "github": re.compile(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}"),
    "modelscope": re.compile(r"ms-[A-Za-z0-9._-]{20,}"),
    "dashscope": re.compile(r"sk-[A-Za-z0-9._-]{20,}"),
}

IGNORED_DIRS = {".git", ".venv", ".uv-cache", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".env",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    if any(word in lowered for word in ("replace", "example", "xxxx", "dummy")):
        return True
    body = value.split("-", 1)[-1].replace("_", "").replace(".", "")
    return len(set(body.lower())) <= 2


def scan(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(lines, start=1):
            for kind, pattern in PATTERNS.items():
                for match in pattern.finditer(line):
                    if not looks_like_placeholder(match.group(0)):
                        findings.append((path.relative_to(root), line_number, kind))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    findings = scan(args.root.resolve())
    if findings:
        print("Potential credentials found (values intentionally hidden):", file=sys.stderr)
        for path, line, kind in findings:
            print(f"- {path}:{line} [{kind}]", file=sys.stderr)
        return 1
    print("Secret scan passed; no credential-shaped values found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
