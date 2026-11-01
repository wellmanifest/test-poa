#!/usr/bin/env python3
"""Dependency-free conformance runner for wellmanifest/test-poa v1."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
SCHEMA_FILE = ROOT / "test-poa.schema.v1.json"

RE_PROCESS_URI = re.compile(r"^proc://[a-z0-9.-]+/(cmd|query)/[a-z0-9_.-]+/[a-z0-9_.-]+/v[0-9]+$")
ALLOWED_ROW_KEYS = {
    "use_case",
    "uri",
    "type",
    "html_urn",
    "js_urn",
    "gui_urn",
    "tui_urn",
    "cli_urn",
    "backend_endpoint",
}


class ConformanceError(Exception):
    pass


def _has_nonempty_str(entry: dict, key: str) -> bool:
    val = entry.get(key)
    return isinstance(val, str) and bool(val.strip())


def validate_test_poa_report(doc: dict) -> None:
    """Validates document structure against test-poa v1 invariants (Web, GUI, TUI, and CLI surfaces)."""
    if not isinstance(doc, dict):
        raise ConformanceError("Document must be an object")

    if doc.get("schema") != "wellmanifest.test-poa/v1":
        raise ConformanceError(f"Invalid schema declaration: {doc.get('schema')}")

    for req in ["schema", "version", "project", "summary", "coverage", "anomalies", "attestation"]:
        if req not in doc:
            raise ConformanceError(f"Missing required top-level field: {req}")

    if not isinstance(doc["version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", doc["version"]):
        raise ConformanceError(f"Invalid SemVer version: {doc.get('version')}")

    summary = doc["summary"]
    if not isinstance(summary, dict):
        raise ConformanceError("summary must be an object")
    for s_req in [
        "use_cases_count",
        "processes_count",
        "commands_count",
        "queries_count",
        "backend_endpoints_count",
        "frontend_actions_count",
        "anomalies_count",
    ]:
        if s_req not in summary or type(summary[s_req]) is not int or summary[s_req] < 0:
            raise ConformanceError(f"Invalid summary field: {s_req}")

    coverage = doc["coverage"]
    if not isinstance(coverage, dict):
        raise ConformanceError("coverage must be an object")
    pct = coverage.get("endpoint_mapping_percentage")
    if not isinstance(pct, (int, float)) or isinstance(pct, bool) or not (0 <= pct <= 100):
        raise ConformanceError("coverage.endpoint_mapping_percentage must be a number in [0, 100]")
    matrix = coverage.get("matrix")
    if not isinstance(matrix, list):
        raise ConformanceError("coverage.matrix must be a list")

    for entry in matrix:
        if not isinstance(entry, dict):
            raise ConformanceError("Matrix row must be an object")
        extra = set(entry) - ALLOWED_ROW_KEYS
        if extra:
            raise ConformanceError(f"Matrix row has unsupported field(s): {sorted(extra)}")
        for f in ["use_case", "uri", "type", "backend_endpoint"]:
            if not _has_nonempty_str(entry, f):
                raise ConformanceError(f"Matrix row missing field: {f}")
        has_web_pair = _has_nonempty_str(entry, "html_urn") and _has_nonempty_str(entry, "js_urn")
        has_surface_urn = any(_has_nonempty_str(entry, k) for k in ("gui_urn", "tui_urn", "cli_urn"))
        if not (has_web_pair or has_surface_urn):
            raise ConformanceError(
                "Matrix row must bind at least one UI/surface URN ((html_urn + js_urn), gui_urn, tui_urn, or cli_urn)"
            )
        if entry["type"] not in ("command", "query"):
            raise ConformanceError(f"Invalid CQRS type in matrix: {entry['type']}")
        if not RE_PROCESS_URI.match(entry["uri"]):
            raise ConformanceError(f"Invalid Process URI syntax: {entry['uri']}")

    anomalies = doc["anomalies"]
    if not isinstance(anomalies, list):
        raise ConformanceError("anomalies must be a list")

    attestation = doc["attestation"]
    if not isinstance(attestation, dict) or not isinstance(attestation.get("passed"), bool):
        raise ConformanceError("attestation.passed must be boolean")
    if not _has_nonempty_str(attestation, "timestamp"):
        raise ConformanceError("attestation.timestamp is required")
    if not _has_nonempty_str(attestation, "receipt"):
        raise ConformanceError("attestation.receipt is required")


def _load_report_json(report_path: Path) -> dict:
    if not report_path.is_file():
        raise ConformanceError(f"Report file not found: {report_path}")
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConformanceError(f"Invalid JSON report {report_path}: {exc}") from exc


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Test-POA Conformance Runner")
    parser.add_argument("--target", type=str, help="Path to project directory or JSON report to audit against Test-POA")
    parser.add_argument(
        "--report",
        action="append",
        default=[],
        help="Explicit Test-POA v1 JSON report path(s) to validate via validate_test_poa_report()",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        print("=== wellmanifest/test-poa Conformance Runner (v1) ===")

        if not SCHEMA_FILE.exists():
            raise ConformanceError(f"Schema file not found: {SCHEMA_FILE}")
        json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
        print("✓ Schema test-poa.schema.v1.json loaded and valid.")

        for rep in args.report:
            rep_path = Path(rep).resolve()
            validate_test_poa_report(_load_report_json(rep_path))
            print(f"✓ Report {rep_path.name}: Test-POA v1 contract verified.")

        if args.target:
            target_path = Path(args.target).resolve()
            if target_path.is_file() and target_path.suffix == ".json":
                validate_test_poa_report(_load_report_json(target_path))
                print(f"✓ Target report {target_path.name}: Test-POA v1 contract verified.")
            else:
                poa_dir = target_path / "poa"
                if not poa_dir.exists():
                    raise ConformanceError(f"Target has no poa/ directory: {target_path}")

                anomalies_file = poa_dir / "reports/anomalies.json"
                if not anomalies_file.exists():
                    raise ConformanceError("Target has not generated poa/reports/anomalies.json")
                anomalies = json.loads(anomalies_file.read_text(encoding="utf-8"))
                if anomalies:
                    raise ConformanceError(f"Target has {len(anomalies)} unresolved anomalies: {anomalies}")
                print(f"✓ Target {target_path.name}: 0 anomalies detected.")

                matrix_file = poa_dir / "reports/coverage_matrix.md"
                if not matrix_file.exists():
                    raise ConformanceError("Target has not generated poa/reports/coverage_matrix.md")
                print(f"✓ Target {target_path.name}: Coverage matrix verified.")

                for candidate in (
                    poa_dir / "reports/test-poa-report.json",
                    poa_dir / "reports/report.json",
                    poa_dir / "report.json",
                ):
                    if candidate.is_file():
                        validate_test_poa_report(_load_report_json(candidate))
                        print(f"✓ Target {target_path.name}: {candidate.name} validated against Test-POA v1.")

        print("\n✓ All wellmanifest/test-poa conformance checks PASSED.")
        return 0
    except ConformanceError as exc:
        print(f"✗ Test-POA conformance FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
