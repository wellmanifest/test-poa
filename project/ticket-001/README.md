# Ticket 001: Support TUI/GUI/CLI URNs and wire validate_test_poa_report into CLI

- **ID**: ticket-001
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-01

## Scope
1. Extend `standard/test-poa.schema.v1.json` and `standard/conformance.py` so `coverage.matrix` supports `gui_urn`, `tui_urn`, and `cli_urn` alongside `(html_urn + js_urn)` for unified TUI/GUI parity verification.
2. Wire `validate_test_poa_report()` into `standard/conformance.py` CLI (`--report`, `--target <report.json>`, and automatic `poa/reports/test-poa-report.json` discovery) with fail-closed exit code 1 on `ConformanceError`.
3. Add unit tests in `tests/test_conformance.py`.
