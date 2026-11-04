"""Run the complete, local GreenSeer public-release verification."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_public_package import audit_tree


MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


class LocalReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src"):
            value = values.get(key)
            if value:
                self.references.append(value)


@dataclass(frozen=True)
class VerificationReport:
    passed: bool
    tests_passed: bool | None
    tests_run: int
    audit_findings: int
    broken_links: int
    invalid_json: int
    source_issues: int
    largest_file_bytes: int
    details: tuple[str, ...]


def _is_local(reference: str) -> bool:
    return not reference.startswith(("#", "http://", "https://", "mailto:", "data:"))


def _target(root: Path, source: Path, reference: str) -> Path:
    clean = reference.split("#", 1)[0].split("?", 1)[0]
    if clean.startswith("/"):
        return root / clean.lstrip("/")
    return source.parent / clean


def _broken_links(root: Path) -> list[str]:
    broken: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        references: list[str] = []
        if path.suffix.lower() in {".md", ".cff"}:
            references = MARKDOWN_LINK.findall(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".html":
            parser = LocalReferenceParser()
            parser.feed(path.read_text(encoding="utf-8"))
            references = parser.references
        for reference in references:
            if not _is_local(reference) or not reference.split("#", 1)[0]:
                continue
            if not _target(root, path, reference).resolve().exists():
                broken.append(f"{path.relative_to(root).as_posix()} -> {reference}")
    return broken


def _invalid_json(root: Path) -> list[str]:
    invalid: list[str] = []
    for path in sorted(root.rglob("*.json")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            invalid.append(f"{path.relative_to(root).as_posix()}: {error}")
    return invalid


def _source_issues(root: Path) -> list[str]:
    path = root / "docs" / "data" / "source-manifest.json"
    if not path.exists():
        return ["docs/data/source-manifest.json is missing"]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    issues = []
    for index, item in enumerate(manifest.get("sources", []), start=1):
        if not str(item.get("public_url", "")).startswith("https://"):
            issues.append(f"source {index} has no HTTPS public URL")
        if not item.get("project_use"):
            issues.append(f"source {index} has no project-use description")
    if not manifest.get("sources"):
        issues.append("source manifest is empty")
    return issues


def _run_tests(root: Path) -> tuple[bool, int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    combined = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"Ran (\d+) tests?", combined)
    return result.returncode == 0, int(match.group(1)) if match else 0, combined.strip()


def verify_release(root: Path, run_tests: bool = True) -> VerificationReport:
    root = Path(root).resolve()
    findings = audit_tree(root)
    broken = _broken_links(root)
    invalid = _invalid_json(root)
    source_issues = _source_issues(root)
    files = [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]
    largest = max((path.stat().st_size for path in files), default=0)
    tests_passed: bool | None = None
    tests_run = 0
    test_output = "Tests skipped for library check"
    if run_tests:
        tests_passed, tests_run, test_output = _run_tests(root)
    details = [
        f"tests: {'PASS' if tests_passed else 'SKIPPED' if tests_passed is None else 'FAIL'} ({tests_run})",
        f"public audit findings: {len(findings)}",
        f"broken local links: {len(broken)}",
        f"invalid JSON files: {len(invalid)}",
        f"source-manifest issues: {len(source_issues)}",
        f"largest public file: {largest} bytes",
    ]
    details.extend(f"audit: {item.path} [{item.rule}]" for item in findings)
    details.extend(f"link: {item}" for item in broken)
    details.extend(f"json: {item}" for item in invalid)
    details.extend(f"source: {item}" for item in source_issues)
    if tests_passed is False:
        details.append(f"test output:\n{test_output}")
    passed = (tests_passed is not False) and not findings and not broken and not invalid and not source_issues and largest < 50_000_000
    return VerificationReport(passed, tests_passed, tests_run, len(findings), len(broken), len(invalid), len(source_issues), largest, tuple(details))


def _write_markdown(root: Path, report: VerificationReport) -> None:
    status = "PASS" if report.passed else "FAIL"
    lines = [
        "# GreenSeer public-release verification",
        "",
        f"**Status: {status}**",
        "",
        "Generated by `python scripts/verify_public_release.py --root .`.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {line}" for line in report.details)
    lines.extend(
        [
            "",
            "## Meaning",
            "",
            "A PASS confirms the checked-in tests, public-package audit, JSON parsing, local links, source manifest and 50 MB file limit. It does not certify causal validity or re-run the private SAS Viya tenant.",
            "",
        ]
    )
    (root / "VERIFICATION.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    report = verify_release(args.root, run_tests=True)
    _write_markdown(Path(args.root).resolve(), report)
    for line in report.details:
        print(line)
    print(f"PUBLIC_RELEASE_{'PASSED' if report.passed else 'FAILED'}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
