---
artifact: COV-S7_BRIEF_v1_0.md
session_id: COV-S7
campaign: M5_COVERAGE_REMEDIATION
stream: cov
audit_section: §G.7
status: ACTIVE
version: 1.0
authored_on: 2026-05-21
spec_artifact: 00_ARCHITECTURE/CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md
spec_section: §G.7
may_touch:
  - platform/scripts/governance/**
  - .github/workflows/**
  - platform/tests/governance/**
must_not_touch:
  - platform/src/**
  - platform/supabase/migrations/**
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - platform/scripts/governance/schema_validator.py
  - platform/scripts/governance/drift_detector.py
  - platform/scripts/governance/manifest_reader.py
gates:
  - tsc
  - vitest_changed
  - synthetic_pr_coverage_gate_fails
---

# COV-S7 Brief — CI Coverage Gate

## §A — Goal

Add a CI check that fails any PR landing a new `RETRIEVAL_TOOLS[]` entry without a corresponding manifest entry, and fails any PR adding a new asset folder without at least one tool binding declared. The check runs as part of `MANIFEST_AUDIT_v1_0.md`'s scheduled job and as a pre-merge gate. This is the long-term enforcement layer that prevents the gaps documented in §C of the audit spec from re-accreting: every new tool wired into the retrieval pipeline must be declared in `CAPABILITY_MANIFEST.json`, and every new asset folder under the canonical layer directories must be reachable by at least one bound retrieval tool. Without this gate, the coverage drift documented in §C (tools present in `RETRIEVAL_TOOLS[]` with no manifest entry; asset folders with no tool binding) will recur with each new session that adds retrieval capability or data.

## §B — Files to touch

### B.1 — New coverage gate script

**`platform/scripts/governance/coverage_gate.py`** — New file. This is the enforcement script. It reads `CAPABILITY_MANIFEST.json` (via `manifest_reader.py` — import only, do not modify) and compares against two live sources:

- `platform/src/lib/retrieve/index.ts` — parses the `RETRIEVAL_TOOLS[]` array to extract declared tool names.
- The canonical asset layer directories (`00_ARCHITECTURE/`, `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, etc.) — scans for folders or files that represent data assets and checks whether each has at least one `tool_name` binding in the manifest.

Exit codes:
- `0` — all tools have manifest entries; all asset folders have at least one tool binding.
- `1` — one or more tools missing from manifest (`COVERAGE_GATE_MANIFEST` failure).
- `2` — one or more asset folders with no tool binding (`COVERAGE_GATE_ASSETS` failure).
- `3` — both failure categories present.

The script must emit a structured JSON report to stdout (so the scheduled audit job can consume it) and a human-readable summary to stderr. The JSON report shape:

```json
{
  "verdict": "PASS | FAIL",
  "categories": {
    "COVERAGE_GATE_MANIFEST": { "status": "PASS | FAIL", "missing": ["tool_name", ...] },
    "COVERAGE_GATE_ASSETS": { "status": "PASS | FAIL", "unbound": ["folder/path", ...] }
  },
  "run_at": "<ISO timestamp>"
}
```

### B.2 — GitHub Actions workflow update

**`.github/workflows/governance.yml`** (or the equivalent scheduled-audit workflow — verify the exact filename on disk before editing) — Add a new job step that calls `coverage_gate.py` after the existing audit steps. Do NOT remove or reorder any existing step. The new step:

```yaml
- name: Coverage gate
  run: python platform/scripts/governance/coverage_gate.py
```

This step runs on both the scheduled cadence and as a required check on PRs. If the file is a scheduled-only workflow, also update (or create) the PR check workflow at `.github/workflows/pr_checks.yml` to add the coverage gate step as a required pre-merge gate.

### B.3 — CI documentation

**`platform/scripts/governance/README.md`** (create if it does not exist; append if it does) — Document the new `coverage_gate.py` script: purpose, invocation, exit codes, JSON output shape, and how it integrates with the scheduled audit and PR gate.

## §C — Acceptance criteria

1. **Synthetic PR adding a tool without a manifest entry fails CI.** A test at `platform/tests/governance/coverage_gate.test.ts` calls `coverage_gate.py` with a synthetic `RETRIEVAL_TOOLS[]` input containing a tool name absent from the manifest, and asserts the script exits with a non-zero code (specifically exit code 1 or 3). The test must pass — meaning the gate correctly rejects the synthetic bad input.

2. **Synthetic PR adding an asset folder with no reachability fails CI.** The same test file (or a second `describe` block) calls `coverage_gate.py` with a synthetic asset directory that has no tool binding in the manifest, and asserts the script exits with a non-zero code (specifically exit code 2 or 3). The test must pass — meaning the gate correctly rejects the synthetic unbound asset.

3. **The scheduled audit's verdict adds two new categories.** The JSON report emitted by `coverage_gate.py` contains both `COVERAGE_GATE_MANIFEST` and `COVERAGE_GATE_ASSETS` keys in its `categories` block, each with a `status` field of `PASS` or `FAIL`. On the current codebase (after COV-S2 wires all tools), both categories must report `PASS` — confirming the gate passes on clean input.

## §D — Hard rules

Per CLAUDE.md §I (file placement rule) and the scope boundaries declared in this brief's frontmatter:

1. **Do not edit any file outside the `may_touch` list.** The scope is strictly `platform/scripts/governance/**`, `.github/workflows/**`, and `platform/tests/governance/**`. No application source, no migrations, no manifest JSON, no existing validator scripts.

2. **Do not modify `schema_validator.py`, `drift_detector.py`, `manifest_reader.py`, or `CAPABILITY_MANIFEST.json`.** These are read-only dependencies for this session. The coverage gate imports `manifest_reader.py` for manifest access but does not alter it.

3. **The coverage gate script must be a NEW file** at `platform/scripts/governance/coverage_gate.py`. It must not be implemented as a modification of any existing script in that directory. If functionality from existing scripts is needed, import it — do not inline-copy or merge.

4. **The GitHub Actions workflow update must only ADD a new step or job.** Do not remove, rename, rename, or reorder any existing step. If the workflow does not exist yet, create the minimal file with only the new step — do not replicate or consolidate existing workflow logic.

5. **Gate `synthetic_pr_coverage_gate_fails` is fulfilled by a vitest test**, not by actual GitHub CI execution. The sub-agent writes `platform/tests/governance/coverage_gate.test.ts` which calls `coverage_gate.py` as a subprocess (using Node's `child_process.execSync` or equivalent) with controlled synthetic inputs and asserts non-zero exit. No actual CI pipeline is spun up during this session. The test must pass under `vitest run` in the local environment.

## §E — Gate definitions

- **`tsc`**: `cd platform && npx tsc --noEmit` exits 0. TypeScript compilation must be clean across the entire platform tree after this session's changes. Since COV-S7 adds only a Python script, a YAML workflow update, and a TypeScript test file, the primary risk is the test file itself introducing type errors.

- **`vitest_changed`**: `cd platform && npx vitest run --changed` — all test suites that cover changed files pass. At minimum, `platform/tests/governance/coverage_gate.test.ts` must pass. No regression in any pre-existing governance test suite (e.g., `smoke_planner_register_tools.ts` if present from COV-S8).

- **`synthetic_pr_coverage_gate_fails`**: The test file `platform/tests/governance/coverage_gate.test.ts` exercises two scenarios:
  - **Scenario A (manifest gap)**: Call `coverage_gate.py` with a synthetic tool name injected into a temporary copy of `RETRIEVAL_TOOLS[]` that has no corresponding manifest entry. Assert exit code is 1 or 3 (non-zero).
  - **Scenario B (asset gap)**: Call `coverage_gate.py` with a synthetic asset folder path that has no tool binding in the manifest. Assert exit code is 2 or 3 (non-zero).
  - **Scenario C (clean baseline)**: Call `coverage_gate.py` with the live manifest and live `RETRIEVAL_TOOLS[]` (post-COV-S2). Assert exit code is 0 (PASS on clean input).
  
  All three scenarios must pass for the gate to be satisfied. The gate name `synthetic_pr_coverage_gate_fails` refers specifically to Scenarios A and B passing — the gate script correctly fails on bad input.
