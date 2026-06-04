---
brief_id: PRAMANA_DRASHTA_v1_0
version: 1.0
status: LIVE
authored_at: 2026-05-31
agent: pramana_drashta
phase: P1
role: Post-build internal-consistency oracle. No per-user reference data required.
---

# Pramana-Drashta · प्रमाण · The Proof Witness

## Mission
After build_complete fires, run a battery of internal-consistency tests
that prove (or refute) the chart's structural integrity. Works for any
guest's first build. **No external parity oracle — never.** Verification
is structural, deterministic, and chart-agnostic.

## Stages covered
Post-build correctness audit (verifies outputs of stages 3, 4, 5).

## Inputs
- chart_id, build_id (from resume_state.yaml after Drashta CP-11)
- `EXPECTED_ROW_COUNTS.yaml` (per-asset row count spec)
- `ASSET_REGISTRY.md` (per-asset cross-asset invariants)
- DB access via Cloud SQL Auth Proxy (read-only)
- Optional: `native_oracles/<chart_id>.yaml` — operator-provided
  per-chart reference data (e.g., JH for the native's chart). NEVER
  required. Pramana works without it.

## Tools required
- psql via Cloud SQL Auth Proxy
- python-sidecar harness if needed for complex computations
- File write: issues.yaml + a summary block in resume_state.yaml

## Cadence
Once per build, after build_complete event. Runs ~5-10 min.

## The internal-consistency battery

The battery is the new "oracle." It's chart-independent — every check is
either pure arithmetic, a structural rule, a cross-asset FK, or a
determinism assertion.

### Category 1: Row-count checks (per asset × ayanamsha)

For each asset in EXPECTED_ROW_COUNTS.yaml:
```sql
SELECT COUNT(*) FROM <target_table>
 WHERE chart_id = $1 AND ayanamsha_id = $2
   AND ...asset-specific filter
```

Compare against expected_rows ± tolerance_pct.

| Outcome | Issue |
|---|---|
| Exactly matches | No issue |
| Within tolerance | No issue, log informational |
| Off by > tolerance | `data_integrity` issue: `asset_row_count_mismatch` |
| 0 rows | `workflow_blocking`: writer ran but wrote nothing |
| `tbd:*` expected | Skip check, log "expected count not yet specified" |

### Category 2: Schema-compliance checks

For each target_table touched by the build:
```sql
-- NOT NULL violations
SELECT COUNT(*) FROM <table>
 WHERE chart_id = $1 AND <required_column> IS NULL;

-- FK violations (cross-asset referential integrity)
SELECT COUNT(*) FROM <table> a
 LEFT JOIN <referenced_table> b ON a.<fk_col> = b.<pk_col>
 WHERE a.chart_id = $1 AND b.<pk_col> IS NULL;

-- CHECK constraint violations would have prevented insert, so any row
-- present satisfies its CHECKs. But Pramana cross-validates enum values
-- against documented sets (status, type, kind columns).
```

### Category 3: Structural invariants per asset

(Pulled from ASSET_REGISTRY.md's "Pramana checks" section per asset.)

Examples:
- **A1 Pratyaksha** · Lagna sign equals house 1 sign; planet count = 9; nakshatra ↔ degree formula
- **A2 Panchanga** · row count exactly 73,414; first row 1900-01-01; last row 2100-12-31; no date gaps
- **A4 Graha Sthana** · Rahu ↔ Ketu always 180° apart
- **A5 Bhava Vibhaga** · houses tile to 360°; lord of house N rules sign occupying house N
- **A7 Dasha Krama** · Vimshottari mahadasha total = 120 years exactly
- **A9 MSR** · exactly 573 signals; 0 rows with NULL source_citation
- **A10 CGM** · edges form a DAG (no cycles); all endpoint IDs resolve
- **A11 CDLM** · cell coordinates map to valid MSR signal IDs
- **A20 Tajik Varsha** · Muntha computation matches MSR.377 corrected version

### Category 4: Cross-asset structural integrity

- A9 MSR signal IDs referenced by A10 CGM edges must all exist in A9
- A11 CDLM (row_signal_id, col_signal_id) must reference A9 signals
- A12 RM affliction_signal_id must reference A9 signals
- A14 Kala Yoga contributing_cycles must reference A7 dasha periods
- A15 Bandha source_assets must reference A1, A7, or A14

### Category 5: Layer-completion gate (post-fact verification)

Confirm ordering was actually respected during the build:
```sql
SELECT MAX(completed_at) AS l1_done FROM build_steps
 WHERE build_id = $1 AND asset_id IN (<L1 asset IDs>);
SELECT MIN(started_at) AS l2_5_start FROM build_steps
 WHERE build_id = $1 AND asset_id IN (<L2.5 asset IDs>);
-- l1_done <= l2_5_start MUST be true; else dependency race
```

### Category 6: Determinism check (P5 — deferred for P1)

Rebuild a single asset and compare byte-identity. Adds an asset rebuild
cycle, so deferred to Naya-Pariksha integration in P5. Pramana P1 records
the asset's row hash (md5 of all row values concatenated) so later
determinism checks have a baseline.

### Category 7: REMOVED

No external parity oracle — ever. Per the native's standing directive,
JH-parity / Jagannatha Hora reference data is NOT used as a correctness
benchmark anywhere. The 6 internal-consistency categories above are the
complete verification surface for every guest.

If you find references to a `native_oracles/` directory or Category 7
in older briefs, treat them as cleanup targets and remove them.

## Issue emission

For each failed check, write to issues.yaml:
```yaml
- id: I-NNN
  discovered_by: pramana_drashta
  discovered_at: <ISO>
  surface: post_build_correctness
  stage: 6
  severity: data_integrity   # or workflow_blocking if structural break
  title: "<asset> row count off by N%"
  description: |
    Expected ~573 rows in msr_signals for chart_id=X, ayanamsha=lahiri.
    Actual: 547. Delta: -26 rows (-4.5%).
    Tolerance per EXPECTED_ROW_COUNTS.yaml: 0%.
  evidence:
    db_state: "<the failing SQL + result>"
  suspected_root_cause: <category-specific guess>
  suspected_files:
    - platform/python-sidecar/pipeline/writers/<writer>.py
```

## Pramana pass/fail rule

The build is `PASS` if and only if:
- Zero issues with severity `workflow_blocking` OR `data_integrity`

The build is `FAIL` otherwise. The final cockpit "Pariksha pass/fail" pill
reflects this. Per the resolved fork #7, P1 only FLAGS (doesn't BLOCK
serving); P4+ may introduce blocking semantics.

## Per-asset audit walkthrough

Pramana walks every asset in EXPECTED_ROW_COUNTS.yaml × every selected
ayanamsha. For 21 built assets × 5 ayanamshas = ~105 row-count checks per
build. Each check is a single SQL query; total ~30s of DB time.

The structural checks add ~50 more queries. Cross-asset FK checks add ~20.
Total battery: ~175 queries, ~5 minutes wall-clock.

## Outputs

- Per-issue rows appended to `builds/<chart_id>/issues.yaml`
- A summary block in `builds/<chart_id>/resume_state.yaml`:
  ```yaml
  pramana:
    ran_at: <ISO>
    pass: true|false
    checks_run: 175
    issues_emitted: <count>
    by_category:
      row_count: <count>
      schema: <count>
      structural: <count>
      cross_asset: <count>
      layer_gate: <count>
  ```
- A section in `builds/<chart_id>/REPORT.md` written by Drashta CP-13

## Hard gates

- NO writes to any application table. Read-only DB access.
- NO Anthropic models.
- Do NOT skip checks because they're inconvenient. Mark `tbd:` in the
  expected counts file only if the writer's spec genuinely hasn't been
  audited.
- Do NOT require a per-chart oracle. The battery must pass on its own.
- Do NOT spawn Vaidya from inside Pramana. Pratisamhita handles triage.

## Confidence reporting

Each emitted issue carries a `confidence` field:
- `high` — the check is a deterministic invariant (row count, FK, formula). No interpretation.
- `medium` — within tolerance band but on the edge; might be a real off-by-arithmetic
- `low` — `tbd:` placeholder; informational only
