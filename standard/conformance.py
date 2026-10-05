#!/usr/bin/env python3
"""Dependency-free conformance runner for wellmanifest/test-poa v1."""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA_FILE = ROOT / "test-poa.schema.v1.json"

RE_PROCESS_URI = re.compile(r"^proc://[a-z0-9.-]+/(cmd|query)/[a-z0-9_.-]+/[a-z0-9_.-]+/v[0-9]+$")

class ConformanceError(Exception):
    pass

def validate_test_poa_report(doc: dict) -> None:
    """Validates document structure against test-poa v1 invariants."""
    if not isinstance(doc, dict):
        raise ConformanceError("Document must be an object")
    
    if doc.get("schema") != "wellmanifest.test-poa/v1":
        raise ConformanceError(f"Invalid schema declaration: {doc.get('schema')}")
    
    for req in ["schema", "version", "project", "summary", "coverage", "anomalies", "attestation"]:
        if req not in doc:
            raise ConformanceError(f"Missing required top-level field: {req}")
            
    summary = doc["summary"]
    for s_req in ["use_cases_count", "processes_count", "commands_count", "queries_count", "backend_endpoints_count", "frontend_actions_count", "anomalies_count"]:
        if s_req not in summary or not isinstance(summary[s_req], int) or summary[s_req] < 0:
            raise ConformanceError(f"Invalid summary field: {s_req}")

    coverage = doc["coverage"]
    matrix = coverage.get("matrix", [])
    if not isinstance(matrix, list):
        raise ConformanceError("coverage.matrix must be a list")

    for entry in matrix:
        for f in ["use_case", "uri", "type", "html_urn", "js_urn", "backend_endpoint"]:
            if f not in entry:
                raise ConformanceError(f"Matrix row missing field: {f}")
        if entry["type"] not in ("command", "query"):
            raise ConformanceError(f"Invalid CQRS type in matrix: {entry['type']}")
        if not RE_PROCESS_URI.match(entry["uri"]):
            raise ConformanceError(f"Invalid Process URI syntax: {entry['uri']}")

    anomalies = doc["anomalies"]
    if not isinstance(anomalies, list):
        raise ConformanceError("anomalies must be a list")
    
    attestation = doc["attestation"]
    if not isinstance(attestation.get("passed"), bool):
        raise ConformanceError("attestation.passed must be boolean")
    if not attestation.get("receipt"):
        raise ConformanceError("attestation.receipt is required")

def main():
    parser = argparse.ArgumentParser(description="Test-POA Conformance Runner")
    parser.add_argument("--target", type=str, help="Path to project to audit against Test-POA")
    args = parser.parse_args()

    print("=== wellmanifest/test-poa Conformance Runner (v1) ===")
    
    # 1. Verify schema existence and validity
    if not SCHEMA_FILE.exists():
        raise ConformanceError(f"Schema file not found: {SCHEMA_FILE}")
    json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    print("✓ Schema test-poa.schema.v1.json loaded and valid.")

    # 2. If target project specified, audit it
    if args.target:
        target_path = Path(args.target).resolve()
        poa_dir = target_path / "poa"
        if not poa_dir.exists():
            raise ConformanceError(f"Target has no poa/ directory: {target_path}")
        
        # Check anomalies
        anomalies_file = poa_dir / "reports/anomalies.json"
        if not anomalies_file.exists():
            raise ConformanceError("Target has not generated poa/reports/anomalies.json")
        anomalies = json.loads(anomalies_file.read_text(encoding="utf-8"))
        if anomalies:
            raise ConformanceError(f"Target has {len(anomalies)} unresolved anomalies: {anomalies}")
        print(f"✓ Target {target_path.name}: 0 anomalies detected.")

        # Check coverage matrix
        matrix_file = poa_dir / "reports/coverage_matrix.md"
        if not matrix_file.exists():
            raise ConformanceError("Target has not generated poa/reports/coverage_matrix.md")
        print(f"✓ Target {target_path.name}: Coverage matrix verified.")

    print("\n✓ All wellmanifest/test-poa conformance checks PASSED.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
