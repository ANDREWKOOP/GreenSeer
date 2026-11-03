"""Reject private or oversized artifacts before the GreenSeer public release."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {
    ".css", ".csv", ".cff", ".html", ".js", ".json", ".md", ".py",
    ".srt", ".svg", ".txt", ".yml", ".yaml",
}
ARCHIVE_SUFFIXES = {".7z", ".gz", ".rar", ".tar", ".tgz", ".zip"}
INTERNAL_DIRECTORIES = {".agents", ".aws", ".codex", ".venv", "rawdata", "viya_transfer"}
AUDIT_EXCLUDED_PREFIXES = {"tests"}
AUDIT_EXCLUDED_FILES = {"scripts/audit_public_package.py"}
TEXT_RULES = (
    ("local-path", re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE), "local user path"),
    ("sas-tenant", re.compile(r"https?://[^\s\"']*engage\.sas\.com", re.IGNORECASE), "SAS tenant URL"),
    (
        "credential",
        re.compile(r"\b(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
        "credential-like assignment",
    ),
    ("credential", re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"), "API-key-like token"),
)


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    rule: str
    message: str


def audit_tree(root: Path, max_bytes: int = 50_000_000) -> list[Finding]:
    """Return all release-blocking findings below *root*."""
    root = Path(root).resolve()
    findings: list[Finding] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        display = relative.as_posix()
        if relative.parts[0].lower() in AUDIT_EXCLUDED_PREFIXES or display in AUDIT_EXCLUDED_FILES:
            continue
        internal = next((part for part in relative.parts if part.lower() in INTERNAL_DIRECTORIES), None)
        if internal:
            findings.append(Finding(display, "internal-directory", f"private directory: {internal}"))
        if path.suffix.lower() in ARCHIVE_SUFFIXES:
            findings.append(Finding(display, "archive", "archives are not permitted in the public package"))
        size = path.stat().st_size
        if size > max_bytes:
            findings.append(Finding(display, "file-size", f"{size} bytes exceeds {max_bytes}"))
        if path.suffix.lower() not in TEXT_SUFFIXES or size > 5_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding(display, "encoding", "declared text file is not UTF-8"))
            continue
        for rule, pattern, label in TEXT_RULES:
            if pattern.search(content):
                findings.append(Finding(display, rule, label))
    return sorted(set(findings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--max-bytes", type=int, default=50_000_000)
    args = parser.parse_args()
    findings = audit_tree(args.root, args.max_bytes)
    for finding in findings:
        print(f"{finding.rule}: {finding.path}: {finding.message}")
    if findings:
        print(f"PUBLIC_AUDIT_FAILED={len(findings)}")
        return 1
    print("PUBLIC_AUDIT_PASSED=0 findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
