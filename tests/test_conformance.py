"""Unit tests for wellmanifest/test-poa v1 schema and CLI conformance validator."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from standard.conformance import ConformanceError, main, validate_test_poa_report


def _sample_report() -> dict:
    return {
        "schema": "wellmanifest.test-poa/v1",
        "version": "1.1.0",
        "project": "heyasa/heyasa",
        "summary": {
            "use_cases_count": 3,
            "processes_count": 3,
            "commands_count": 2,
            "queries_count": 1,
            "backend_endpoints_count": 3,
            "frontend_actions_count": 3,
            "anomalies_count": 0,
        },
        "coverage": {
            "endpoint_mapping_percentage": 100.0,
            "matrix": [
                {
                    "use_case": "UC-01-ChatDispatch",
                    "uri": "proc://heyasa.local/cmd/chat/send/v1",
                    "type": "command",
                    "html_urn": "urn:html:hud:chat-input",
                    "js_urn": "urn:js:hud:sendCommand",
                    "tui_urn": "urn:tui:shellmux:pane-A:prompt",
                    "backend_endpoint": "POST /api/commands",
                },
                {
                    "use_case": "UC-02-TuiOnlyHandoff",
                    "uri": "proc://heyasa.local/cmd/workspace/handoff/v1",
                    "type": "command",
                    "tui_urn": "urn:tui:shellmux:ctrl-b-g",
                    "gui_urn": "urn:gui:willmux:workspace-state",
                    "backend_endpoint": "GET /?mode=gui&focus=A",
                },
                {
                    "use_case": "UC-03-CliProjection",
                    "uri": "proc://heyasa.local/query/ui/contract/v1",
                    "type": "query",
                    "cli_urn": "urn:cli:willcore:project-tui",
                    "backend_endpoint": "CLI willcore --project-tui",
                },
            ],
        },
        "anomalies": [],
        "attestation": {
            "passed": True,
            "timestamp": "2026-11-01T18:30:00Z",
            "receipt": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        },
    }


def test_validate_report_supports_web_gui_tui_and_cli_urns():
    doc = _sample_report()
    validate_test_poa_report(doc)


def test_validate_report_rejects_row_without_any_surface_urn():
    doc = _sample_report()
    bad_row = {
        "use_case": "UC-MissingSurface",
        "uri": "proc://heyasa.local/query/ui/state/v1",
        "type": "query",
        "backend_endpoint": "GET /api/state",
    }
    doc["coverage"]["matrix"].append(bad_row)
    with pytest.raises(ConformanceError, match="surface URN"):
        validate_test_poa_report(doc)


def test_cli_validates_report_and_fails_closed_on_invalid_report(tmp_path):
    good = tmp_path / "good-report.json"
    good.write_text(json.dumps(_sample_report()), encoding="utf-8")
    assert main(["--report", str(good)]) == 0
    assert main(["--target", str(good)]) == 0

    bad_doc = copy.deepcopy(_sample_report())
    bad_doc["coverage"]["matrix"][0]["uri"] = "http://not-a-proc-uri"
    bad = tmp_path / "bad-report.json"
    bad.write_text(json.dumps(bad_doc), encoding="utf-8")
    assert main(["--report", str(bad)]) == 1

    # Project directory with poa/reports/test-poa-report.json also runs validate_test_poa_report
    proj = tmp_path / "proj"
    reports_dir = proj / "poa" / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "anomalies.json").write_text("[]", encoding="utf-8")
    (reports_dir / "coverage_matrix.md").write_text("# Matrix\n", encoding="utf-8")
    (reports_dir / "test-poa-report.json").write_text(json.dumps(bad_doc), encoding="utf-8")
    assert main(["--target", str(proj)]) == 1

    (reports_dir / "test-poa-report.json").write_text(json.dumps(_sample_report()), encoding="utf-8")
    assert main(["--target", str(proj)]) == 0
