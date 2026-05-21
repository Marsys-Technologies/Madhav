# platform/scripts/governance — MARSYS-JIS Governance Scripts

This directory contains Python scripts that enforce the governance invariants described in
`00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`. All scripts are **detectors and
validators** — they never modify the files they inspect.

---

## Scripts

### `drift_detector.py`
Runs the eight cross-surface drift checks declared in `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §H.3`.
Checks canonical path parity, fingerprint matches, STEP_LEDGER consistency, phantom references,
and unreferenced artifacts.

### `schema_validator.py`
Validates SESSION_OPEN / SESSION_CLOSE artifacts against their JSON schemas.

### `mirror_enforcer.py`
Checks that Claude-side mirror pairs (CLAUDE.md ↔ .geminirules, etc.) are in sync.
Exits non-zero on desync per `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K.3`.

### `manifest_reader.py`
Shared library: loads `CAPABILITY_MANIFEST.json` and `manifest_overrides.yaml` mirror pairs,
returning a `CanonicalArtifacts`-compatible object. Imported by other scripts; not run directly.

### `coverage_gate.py` ← **COV-S7**
CI coverage gate that enforces two invariants:

1. **`COVERAGE_GATE_MANIFEST`** — Every tool registered in `RETRIEVAL_TOOLS[]`
   (`platform/src/lib/retrieve/index.ts`) must have a corresponding entry in
   `CAPABILITY_MANIFEST.json` with a non-empty `tool_name` field.

2. **`COVERAGE_GATE_ASSETS`** — Every canonical asset layer directory
   (`01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, etc.) must have at least one
   manifest entry whose `path` falls within that directory AND carries a `tool_name`.

#### Exit codes

| Code | Meaning |
|------|---------|
| `0`  | All checks pass (PASS) |
| `1`  | `COVERAGE_GATE_MANIFEST` failure only (tools missing from manifest) |
| `2`  | `COVERAGE_GATE_ASSETS` failure only (asset folders with no tool binding) |
| `3`  | Both failure categories present |
| `4`  | Script-internal error |

#### JSON output (stdout)

```json
{
  "verdict": "PASS | FAIL",
  "categories": {
    "COVERAGE_GATE_MANIFEST": {
      "status": "PASS | FAIL",
      "missing": ["tool_name_a", "tool_name_b"]
    },
    "COVERAGE_GATE_ASSETS": {
      "status": "PASS | FAIL",
      "unbound": ["01_FACTS_LAYER", "025_HOLISTIC_SYNTHESIS"]
    }
  },
  "run_at": "<ISO 8601 UTC timestamp>"
}
```

The human-readable summary is written to stderr.

#### Invocation

```bash
# Standard (from repo root):
python platform/scripts/governance/coverage_gate.py

# With overrides (for testing or debugging):
python platform/scripts/governance/coverage_gate.py \
  --repo-root /path/to/repo \
  --retrieve-index /path/to/retrieve/index.ts \
  --manifest-path /path/to/CAPABILITY_MANIFEST.json \
  --asset-dirs 01_FACTS_LAYER 025_HOLISTIC_SYNTHESIS
```

#### CI integration

The `coverage-gate` job in `.github/workflows/ci.yml` runs this script on every push and PR.
It runs **after** the existing `typecheck`, `unit-tests`, and `planner-regression` jobs.

#### Tests

`platform/tests/governance/coverage_gate.test.ts` verifies three scenarios:

- **Scenario A**: Tool in `RETRIEVAL_TOOLS[]` absent from manifest → exit 1 or 3 (gate rejects bad input)
- **Scenario B**: Asset folder with no manifest binding → exit 2 or 3 (gate rejects unbound asset)
- **Scenario C**: Clean state (all tools and folders bound) → exit 0 (gate passes clean input)

Run with: `cd platform && npx vitest run tests/governance/coverage_gate`

---

## Shared library: `_ca_loader.py`

Internal loader for `CANONICAL_ARTIFACTS_v1_0.md`. Imported by `drift_detector.py` and
`manifest_reader.py`. Do not import directly from application code.
