# wellmanifest/test-poa Specification (v1)

## 1. Terminology

- **POA**: Process-Oriented Architecture (`wellmanifest/poa`).
- **Code URN**: Uniform Resource Name identifying static code entities (`urn:<ns>:code:<layer>:<module>#<symbol>`).
- **Process URI**: Uniform Resource Identifier addressing executable operations (`proc://<ns>/<type>/<domain>/<action>/<version>`).
- **CQRS**: Command Query Responsibility Segregation.
- **Closed-Loop Audit**: Verification pattern transitioning from observation of anomalies to resolved attestation.

---

## 2. The Tri-Layer Traceability Matrix

Every business use case (UC) maps to a verifiable chain across the system:

```text
[Use Case] 
    ├── HTML URN: urn:<ns>:view:html:<component>
    ├── JS URN:   urn:<ns>:code:js:<module>#<function>
    ├── Process:  proc://<ns>/<cmd|query>/<domain>/<op>/<v>
    └── Backend:  urn:<ns>:code:py:<module>#<handler> -> <METHOD> <PATH>
```

---

## 3. CQRS Invariants & Testing Contracts

### 3.1 Commands
- **URI Structure**: `proc://<ns>/cmd/<domain>/<action>/<v>`
- **HTTP Mapping**: `POST`, `PUT`, `PATCH`, `DELETE`
- **Required Assertions**:
  1. Actor authorization verified.
  2. Input validated against strictly typed schema (fail-closed).
  3. Immutable receipt issued:
     ```json
     {
       "receipt_id": "<uuid>",
       "process_uri": "proc://...",
       "state": "completed",
       "actor": "<id>",
       "input_hash": "sha256:...",
       "created_at": 1726938000
     }
     ```
  4. Audit event appended to append-only log.

### 3.2 Queries
- **URI Structure**: `proc://<ns>/query/<domain>/<action>/<v>`
- **HTTP Mapping**: `GET`, `HEAD`
- **Required Assertions**:
  1. No state mutation or receipt creation.
  2. Idempotent execution (multiple calls return identical results for static state).
  3. No credential or secret leakage into query string or projection payload.

---

## 4. Anomaly Taxonomy & Severity Levels

| Anomaly Type | Severity | Description | Remediation |
| :--- | :--- | :--- | :--- |
| `dead_action` | **HIGH** | Action exists in HTML/JS with no backend endpoint or active dispatcher handler. | Delete action or implement missing handler. |
| `unmapped_endpoint` | **MEDIUM** | API endpoint exists in backend router without declared Process URI. | Register Process URI in `PROCESS_MAP` and catalog. |
| `obsolete_alias` | **LOW** | Multiple actions triggering identical operations without formal deprecation. | Consolidate to canonical action name. |
| `state_leakage` | **CRITICAL** | Sensitive data or secrets passed into query params or projection. | Strip secrets at client boundary. |
