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

### `mirror_enforcer.py` (RETIRED 2026-05-27)
Mirror enforcer retired per native directive ND.1 close-out. Gemini collaboration declared inactive; the script + mirror-pair inventory were removed in the atomic 5-surface retirement PR.

### `manifest_reader.py`
Shared library: loads `CAPABILITY_MANIFEST.json` and `manifest_overrides.yaml`, returning a
`CanonicalArtifacts`-compatible object. Imported by other scripts; not run directly. The
`mirror_pairs:` section in overrides retired 2026-05-27 — loader returns an empty dict.

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

### `check_fact_category_pinning.py`
Permanent CI lint (ŚUDDHA-VĀCA C.7) flagging any `chart_facts` selection reduced to one row by
`fact_category` alone (no `fact_key` pin, no deterministic `ORDER BY ... LIMIT 1`/`DISTINCT ON`).
`--self-test` runs the bundled `fact_category_pin_fixtures/`; default scans the live repo tree
against `fact_category_pin_allowlist.json`. Wired into `ci.yml` (static, no network).

### `check_reconciliation_cadence.py` ← **PARIŚODHANA Phase C2**
The standing reconciliation cadence recommended by `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md`'s
"ships-but-register-never-flips" standing note: cross-references `cr_status.ts`'s
OPEN_CRS/LOGGED_CRS/CLOSED_CRS allowlists (both the `platform` and `platform-mcp` copies) and every
`known_gap: 'CR-N'` citation in `registry_data.ts` against the live disposition recorded in
`POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` / `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` / the
`ELEVATION_REGISTER_v1_0.md` prose blocks. Reports six divergence classes — the headline one being
a register row still marked OPEN for an id the code already treats as CLOSED (or the mirror-image).
Also catches the two copies of `cr_status.ts`/`registry_data.ts` disagreeing with each other
directly (`DUAL_COPY_DRIFT`).

**Not part of `ci.yml`.** `--live` performs real network calls against the deployed MCP server
(needs `MCP_CANARY_KEY`) — a different risk profile than every other script in this directory, so
it is invoked manually or via the opt-in `.github/workflows/reconciliation-cadence.yml`
(`workflow_dispatch`; its `schedule:` trigger is commented out — a maintainer must opt in). The
default (no `--live`) pass is static, network-free, and safe to run anytime.

```
python platform/scripts/governance/check_reconciliation_cadence.py --self-test   # hermetic
python platform/scripts/governance/check_reconciliation_cadence.py               # static scan
MCP_CANARY_KEY=... python platform/scripts/governance/check_reconciliation_cadence.py --live
```

### `schema_pin_mimamsa_predictions.py` ← **SAMĀPTI B-PB-SCHEMA-PIN**
The real schema HASH pin for `mimamsa_predictions`, replacing the prose-only "286 rows matching the
BIND pin" + opaque `b730b9f3…` fingerprint `REPORT_PB-3.md` §G item 1 recorded with nothing
reproducible behind it. Computes a SHA-256 over the table's deterministically-ordered
columns/constraints/indexes (never row count — that's tracked separately as informational context,
since `MEMO_PB-3_0.md` expects it to move legitimately via L5 rebuilds) and compares against the
committed baseline in `MIMAMSA_PREDICTIONS_SCHEMA_PIN.json`.

```
python platform/scripts/governance/schema_pin_mimamsa_predictions.py --self-test        # DB-free, CI-safe
DATABASE_URL=... python platform/scripts/governance/schema_pin_mimamsa_predictions.py --verify
DATABASE_URL=... python platform/scripts/governance/schema_pin_mimamsa_predictions.py --print-canonical
```

Full runbook: `00_ARCHITECTURE/briefs/pariprashna_build/PB_SCHEMA_HASH_PIN_v1_0.md`.

---

## Shared library: `_ca_loader.py`

Internal loader for `CANONICAL_ARTIFACTS_v1_0.md`. Imported by `drift_detector.py` and
`manifest_reader.py`. Do not import directly from application code.
