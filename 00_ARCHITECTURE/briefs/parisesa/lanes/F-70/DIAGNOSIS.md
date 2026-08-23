# F-70 Diagnosis — CL-02 dead-backend class: calibration_maturity hardcoded zero-stub in all 8 kala_* view facades

Stage: DIAGNOSE (Stage D) · Campaign: PARIŚEṢA · Stream: S5 MŪLA · Lane: F-70 (CL-02, widest blast radius in stream — 8 sibling sites)
Severity: TIER2-HONESTY · Status: **CONFIRMED LIVE — NOT FIXED**
Diagnosed: 2026-08-16, live prod DB + MCP tools, chart_id `482012f1-710e-4a25-994a-93821f5871aa`

## 1. Live reproduction

Called live via `mcp__marsys-jis-direct__*` against the canonical chart. Raw JSON saved to
`lanes/F-70/repro_raw.json`.

- `kala_now_get` → `calibration_maturity: {n_events:0, prospective_resolutions:0, event_class_coverage:0, weights_version:null, skill_score:null}`
- `kala_priority_get` → identical zero-stub: `calibration_maturity: {n_events:0, prospective_resolutions:0, event_class_coverage:0, weights_version:null, skill_score:null}`
- `mimamsa_insight_get({chart_id: same, insight_type:'calibrated_outlook'})` → `calibration_summary: {total_matches:57, confirmed:"2", partial:"23", refuted:"7", unresolved:"25", mean_composite_score:0.495}`, with 6 `calibrated_outlook` insight units whose `n_support` values are `[7,12,18,3,13,4]` — **sum = 57, exactly matching `total_matches`.**

**Verdict: the contradiction is CONFIRMED STILL PRESENT today.** For the identical chart_id, `kala_now_get`/`kala_priority_get` claim zero calibration events exist while `mimamsa_insight_get` reports 57 real, internally-consistent calibration matches. This is not ALREADY-FIXED.

## 2. Claim decomposition

**(a) All 8 kala_* views hardcode the zero-stub.** Confirmed — see §3/§4 below, all 8 files call `noLelCalibrationMaturity()` unconditionally with no chart-specific branch.

**(b) Tool descriptions actively assert "no calibration plane exists yet" (§N.7 violation).** Confirmed. The live `kala_priority_get` tool description (fetched via ToolSearch this session) reads verbatim:

> "...3-state coverage (honestly flags that the W2 five-axis salience vector — informativeness/consequence/relevance/reliability/actionability — is not yet built; today's priority_score is the legacy single-scalar salience), freshness, and **calibration_maturity (always the honest zero stub at W0 — no calibration plane exists yet)**. ... [ṢAḌ-DARŚANA W0.4]"

This is a §N.7-item-4 violation ("a verification flag must have a real detector behind it, or be null") one layer up — the *description itself* asserts a global absence ("no calibration plane exists yet") that is false: the plane exists, computes, and persists (§2c below). The source code carries the same false framing — `platform-mcp/src/lib/kala_envelope.ts:447-452`, the docstring on `noLelCalibrationMaturity()` itself, frames the LEL-absent zero value as the universally-correct W0/W1 answer: "Every W0/W1 facade over a chart with no LEL entries should serve exactly this — never a null `calibration_maturity` block." The code never actually checks whether the target chart has LEL entries or persisted calibration rows before returning this — it treats the LEL-absent case as the only case.

**(c) A real computation exists and writes real data (mi_bhara.py).** Confirmed. `compute_calibration_maturity()` (`platform/python-sidecar/services/mi_bhara/living_lel.py:234-268`, imported at `pipeline/orchestrator/writers/mi_bhara.py:102`, invoked at `mi_bhara.py:163-176`) runs as part of the `MiBharaWriter` build and its results are persisted via `services/mi_bhara/db.py`:
- `kala_field_weight_versions` — INSERT at `db.py:230-254` (`ON CONFLICT (version_id) DO NOTHING`)
- `kala_field_skill` — INSERT at `db.py:291-320`
- `kala_field_gof` — INSERT at `db.py:323-338+` (`insert_gof_row`)

Census (CL02_CENSUS.md) already confirmed these tables are non-empty in prod: weight_versions=1, skill=7, gof=6.

**(d) Never read by ANY serving-layer file.** Confirmed by grep (see §3.4). Zero hits for the three table names in `platform-mcp/src` or `platform/src`. The only non-writer/non-migration/non-test hit is a seed script's `count_sql` catalog entry (`platform/scripts/seed/asset_registry_seed.ts:2921-2938`), which is cockpit bookkeeping, not a serving read.

**(e) A contradictory sibling surface reports real numbers for the same chart.** Confirmed — §1 above. `mimamsa_insight_get`'s `calibrated_outlook` insight units are a working, independently-verifiable (n_support sums exactly to total_matches) calibration surface for the identical `chart_id`.

## 3. Mechanism to file:line

### 3.1 — The 8 call sites (verified live this session; **no drift** from the corpus's original citations)

| # | File | Line | Quote |
|---|---|---|---|
| 1 | `platform-mcp/src/tools/kala_views/now.ts` | 1970 | `calibrationMaturity: noLelCalibrationMaturity(),` |
| 2 | `platform-mcp/src/tools/kala_views/priority.ts` | 434 | `calibrationMaturity: noLelCalibrationMaturity(),` |
| 3 | `platform-mcp/src/tools/kala_views/ahead.ts` | 1984 | `calibrationMaturity: noLelCalibrationMaturity(),` |
| 4 | `platform-mcp/src/tools/kala_views/upaya.ts` | 427 | `calibrationMaturity: noLelCalibrationMaturity(),` |
| 5 | `platform-mcp/src/tools/kala_views/ritual.ts` | 572 | `calibrationMaturity: noLelCalibrationMaturity(),` |
| 6 | `platform-mcp/src/tools/kala_views/explain.ts` | 699 | `calibrationMaturity: noLelCalibrationMaturity(),` |
| 7 | `platform-mcp/src/tools/kala_views/story.ts` | 756 | `calibrationMaturity: noLelCalibrationMaturity(),` |
| 8 | `platform-mcp/src/tools/kala_views/elect.ts` | 761 | `calibrationMaturity: noLelCalibrationMaturity(),` |

`priority.ts:14` additionally carries a source comment matching the tool-description language verbatim: `honest 'noLelCalibrationMaturity()' stub at W0 — no calibration plane exists yet` — confirming the false framing is baked into the code comments too, not just the MCP-facing description string.

### 3.2 — `noLelCalibrationMaturity()` definition

`platform-mcp/src/lib/kala_envelope.ts:453-461`:
```ts
export function noLelCalibrationMaturity(): CalibrationMaturity {
  return {
    n_events: 0,
    prospective_resolutions: 0,
    event_class_coverage: 0,
    weights_version: null,
    skill_score: null,
  }
}
```
Docstring (lines 447-452) asserts this is the correct universal W0/W1 answer, never conditioned on chart state.

### 3.3 — mi_bhara.py's real computation, confirmed writing to all 3 tables

See §2c above for the three INSERT sites in `services/mi_bhara/db.py`. Column lists confirm chart-scoping intent: `kala_field_skill` and `kala_field_gof` both insert `chart_id` directly per row; `kala_field_weight_versions` inserts `fitted_from_chart_id` (nullable) + `scope` (`'global'`/`'per_chart'`).

### 3.4 — Grep confirmation: zero serving-layer consumers

`rg -n "kala_field_weight_versions|kala_field_skill|kala_field_gof"` across `platform-mcp/src` and `platform/src`: **zero hits.** All references are confined to:
- **Writer (Python):** `services/mi_bhara/{weights.py:79, living_lel.py:19, db.py:211/233/280/295/327, skill.py:38}`, `services/ka_kshetra/stage4_field.py:774,780`, `pipeline/orchestrator/writers/mi_bhara.py:7,116,190,191`
- **Migration:** `supabase/migrations/491_kala_field_weights_seed.sql` (CREATE TABLE `kala_field_weight_versions` + seed), `supabase/migrations/497_kala_field_skill_gof.sql` (CREATE TABLE `kala_field_skill` + `kala_field_gof`)
- **Seed/cockpit script (not serving code):** `platform/scripts/seed/asset_registry_seed.ts:2921-2938` (asset_registry catalog `count_sql` row)
- **Test:** `platform/python-sidecar/tests/l3/ka_kshetra/{fixtures.py:38, fake_db.py:74/76, test_writer.py:157/422, test_circularity_guard.py:258}`

Confirms claim (d): no serving-layer file anywhere reads these three tables.

### 3.5 — The chart_id join path (the item the census flagged as needing tracing, not assuming)

`kala_field_weight_versions` schema (`supabase/migrations/491_kala_field_weights_seed.sql:67-81`):
```sql
CREATE TABLE IF NOT EXISTS kala_field_weight_versions (
  version_id            TEXT PRIMARY KEY,
  status                TEXT NOT NULL CHECK (status IN ('active','superseded','rejected')),
  fitted_from_chart_id  UUID,                      -- NULL for v0_classical (global structural prior)
  scope                 TEXT NOT NULL CHECK (scope IN ('global','per_chart')),
  x_schema_version      TEXT NOT NULL,
  n_events_used         INT  NOT NULL DEFAULT 0,
  n_prospective_used    INT  NOT NULL DEFAULT 0,
  tau_shrinkage         DOUBLE PRECISION NOT NULL,
  any_clipped           BOOLEAN NOT NULL DEFAULT FALSE,
  fit_loglik            DOUBLE PRECISION,
  holdout_loglik        DOUBLE PRECISION,
  activated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes                 TEXT
);
```
No bare `chart_id` column — but there IS `fitted_from_chart_id` (nullable UUID) + `scope`. The table is a deliberate hybrid: global rows (`fitted_from_chart_id=NULL`, e.g. the seeded `v0_classical` structural prior) coexist with per-chart rows (`fitted_from_chart_id` set, `scope='per_chart'`).

`kala_field_skill` and `kala_field_gof` (`497_kala_field_skill_gof.sql:59-99, 122-157`) both carry a plain `chart_id UUID NOT NULL` column directly, plus `weights_version TEXT NOT NULL` as the value-FK back to `kala_field_weight_versions.version_id` — trivially joinable (`WHERE chart_id = :chart_id`, indexed via `idx_kala_field_skill_chart` / `idx_kala_field_gof_chart`).

**A real, already-implemented, production-used join/resolution function already exists** — `services/mi_bhara/weights.py:77-84` (`_SELECT_ACTIVE`), called from `resolve_weights_version(conn, chart_id)` at `weights.py:133-161`:
```sql
SELECT version_id, scope, fitted_from_chart_id, x_schema_version, activated_at
  FROM kala_field_weight_versions
 WHERE status = 'active'
   AND (scope = 'global' OR fitted_from_chart_id = %s)
 ORDER BY (fitted_from_chart_id = %s) DESC, activated_at DESC, version_id DESC
 LIMIT 1
```
This picks the chart's own per-chart weight version if one exists, else falls back to the global structural prior. It is real, tested, production writer-path code — just never called from (or mirrored into) the MCP serving layer.

**Secondary note:** `services/ka_kshetra/stage4_field.py:772-776` reads this table with a narrower, unscoped query (`WHERE status='active' ORDER BY activated_at DESC LIMIT 1`, no `fitted_from_chart_id`/`scope` filter) — a separate, smaller defect (doesn't prefer a chart-specific fit even when one exists) worth flagging to the conductor but out of F-70's direct scope.

**Conclusion: `calibration_maturity` is NOT architecturally global-only.** A working per-chart join path exists (`resolve_weights_version`) plus directly chart-scoped `kala_field_skill`/`kala_field_gof` tables. This is a wiring gap in the serving layer, not a schema/design limitation — the fix shape is "read these tables / call this resolver from the MCP facade," not "invent a new join."

## 4. Sibling census

The 8 file:line sites in §3.1 constitute the complete sibling census for this finding — confirmed exact, zero drift from the corpus.

## 5. Blast radius — lease flags

**PAR-F-70-NEEDS-LEASE — S2** (owns `elect.ts`, `story.ts`, `ritual.ts`, `priority.ts`, `shared.ts` per plan §2.1 lease split): 4 of the 8 hardcoded call sites live in S2's lease (`elect.ts:761`, `story.ts:756`, `ritual.ts:572`, `priority.ts:434`). S2 also owns `shared.ts`, the natural home for a shared calibration-maturity resolver if the cross-stream fix lands there.

**PAR-F-70-NEEDS-LEASE — S4** (owns `now.ts`, `explain.ts`, `ahead.ts`, `upaya.ts`): the remaining 4 sites (`now.ts:1970`, `explain.ts:699`, `ahead.ts:1984`, `upaya.ts:427`).

Neither half is in S5's OWNS list. S5 (this lane) has done the census/root-cause tracing per plan §2's "Known" line; the actual code fix must land in S2's and S4's files.

**Recommendation to the conductor:** this is a strong candidate for a single shared-helper fix rather than 8 independent repairs. A function like `resolveCalibrationMaturity(chartId, dbConn)` — wrapping the existing `resolve_weights_version`-equivalent join logic (§3.5) plus reads of `kala_field_skill`/`kala_field_gof` scoped to `chart_id` — placed in `platform-mcp/src/lib/kala_envelope.ts` (alongside `noLelCalibrationMaturity()`, which becomes the honest fallback ONLY when the chart genuinely has no calibration rows, not unconditionally) would let all 8 sites call one corrected function. This needs coordination between S2 (owns `shared.ts`, 4 of the 8 sites) and S4 (4 of the 8 sites, plus `kala_envelope.ts` itself may be a shared-lib file outside both leases — verify ownership before either stream edits it). Also recommend fixing the tool-description string (§2b) and the `priority.ts:14` comment in the same pass — both currently assert a false "no calibration plane exists yet," a §N.7 narration-fidelity violation independent of the data-wiring fix itself.
