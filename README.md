# test-poa — Testing Standard for Process-Oriented Architecture

**`wellmanifest/test-poa`** is the versioned normative standard for testing, auditing, and continuous verification of systems adhering to **`wellmanifest/poa`** (Process-Oriented Architecture) and **CQRS** (Command Query Responsibility Segregation).

---

## 1. Scope and Purpose

Building systems with Process-Oriented Architecture (POA) replaces ad-hoc UI mutations and unconstrained tool execution with typed, addressable, auditable **Process URIs** (`proc://...`).

`wellmanifest/test-poa` standardizes how such architectures are proven correct across:
1. **Tri-Layer Code Identification (URN)**:
   - **HTML URN** (`urn:<ns>:view:html:...`): Declares user-facing surfaces, components, and form triggers.
   - **JS URN** (`urn:<ns>:code:js:...`): Orchestrates client-side state, validation, and CQRS dispatch.
   - **Python/Backend URN** (`urn:<ns>:code:py:...`): Executes business transactions, side-effects, and generates signed receipts.
2. **Process Addressability (URI)**:
   - Commands: `proc://<ns>/cmd/<domain>/<action>/<v>` (mutations, receipts, audit).
   - Queries: `proc://<ns>/query/<domain>/<action>/<v>` (idempotent, side-effect free reads).
3. **Closed-Loop Audit Cycle**:
   $$\text{Observed} \longrightarrow \text{Diagnosed} \longrightarrow \text{Authorized} \longrightarrow \text{Repairing} \longrightarrow \text{Verifying} \longrightarrow \text{Resolved}$$

---

## 2. Normative Invariants

A system conforms to `wellmanifest/test-poa` if and only if it satisfies all of the following rules:

### Invariant 1: Zero Dead Code (Orphan Free)
Every declared interactive element (`data-action`, `data-form`) must resolve to a registered `Code URN` and execute an active `Process URI`. Any unhandled action is classified as dead code and fails the audit.

### Invariant 2: 100% Backend Process Coverage
Every public and protected route in the API catalog must declare its associated `Process URI` (e.g. via `x-clonerd-process` in OpenAPI / AsyncAPI).

### Invariant 3: CQRS Purity & Receipt Generation
- **Commands** (`proc://.../cmd/...`) MUST emit structured audit events and receipts containing an immutable input hash (`input_hash`), timestamp, actor, and execution outcome.
- **Queries** (`proc://.../query/...`) MUST NEVER perform database mutations or produce persistent side-effects.

### Invariant 4: Continuous Machine Attestation
The architecture must provide a machine-readable audit report adhering to `test-poa.schema.v1.json`, suitable for automated CI/CD gating and static verification.

---

## 3. Conformance Validation

Run the standalone, dependency-free conformance test runner:

```bash
python3 standard/conformance.py
```

Expected exit code: `0` (Zero anomalies, schema compliant, positive/negative test vectors verified).
