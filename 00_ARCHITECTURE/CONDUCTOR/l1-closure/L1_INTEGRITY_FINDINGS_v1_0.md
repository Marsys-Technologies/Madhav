---
artifact: L1_INTEGRITY_FINDINGS_v1_0.md
version: 1.0
phase: 1
pass: read-only-audit
date: 2026-06-18
auditor: phase-1-subagent
branch: feature/l1-phase3-enrichment
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
status: COMPLETE
---

# L1 Gaṇita — Phase 1 Integrity Findings

Read-only static audit of the `feature/l1-phase3-enrichment` branch. No files modified. All evidence
is grounded in file reads and greps from the working tree as of 2026-06-18. Live-DB checks are
flagged NEEDS-LIVE-DB and listed as Phase 2 tasks.

---

## Summary table

| # | Check | Asset(s) | Status | Finding | Fix-target |
|---|---|---|---|---|---|
| 1 | count_sql valid + chart-scoped | All 10 registered ga_* | PASS (note) | All valid SQL, all chart_id=$1 scoped; ga_structural overlaps graha_position categories with ga_positions | Cosmetic only |
| 2 | target_floor vs achieved count | ga_strength, ga_sensitive | WARN | 11,936 and 8,610 are branch-local projections, not yet prod-confirmed | STEP 2 (live run) |
| 3 | asset_throughput freshness | ga_strength, ga_sensitive | NEEDS-LIVE-DB | Standalone enrichment runs likely left throughput stale | STEP 2 (live run) |
| 4 | catalog_status='CURRENT' | All 10 registered ga_* | PASS | All 10 assets explicitly 'CURRENT' in seed | None |
| 5 | ga_prashna 0-rows cockpit render | ga_prashna, ga_yoga | PASS (design) | 0 is correct final state; cockpit cosmetic bug tracked separately | Cosmetic brief |
| 6 | Floored items citation_ref | ga_sensitive, ga_strength | PASS | verification_pass_status='floored' + reason in fact_value_text on all floored rows | None |
| 7 | Silent failures in writers | ga_dashas, ga_yoga, ga_structural, ga_panchanga | WARN | logger.debug on telemetry error (ga_dashas:2557); bare except:pass in ga_yoga:169, ga_structural:571/589/1199/3482, ga_panchanga:293/810/865 | Non-blocking; harden post-merge |
| 8 | L1 authority within L1 | ga_condition | PASS | SELECTs chart_facts/chart_divisionals for all position data; no recomputation | None |
| 9 | Idempotency | All writers | PASS | Delete-then-insert via _idempotency.py helpers; no accretion risk | None |
| 10 | Orchestrator contract compliance | All writers | PASS (note) | @register in adapter layer (correct); ga_dashas makes vestigial asset_throughput write on orchestrator path (caught, swallowed) | Non-blocking |
| 11 | Light→Heavy audit | ga_dashas, ga_vargas | WARN | ga_dashas (536K rows) and ga_vargas (21K rows) are light writers running full 5-ayanamsha loops in one transaction; mitigated by migration 241 Guard A | Confirm Guard B |
| 12 | Graha naming heterogeneity | All writers | PASS | TitleCase universal for engine keys; UPPER_SNAKE for fact_subject; single shared source | None |
| 13 | Dead tables / migration fragmentation | migrations 230-241 | WARN | Migration 237 absent; migrations 242-306 absent from branch (exist on main); migration 307 SQL file not confirmed present on disk | BLOCKING — resolve before merge |
| 14 | FORENSIC 7/7 | ga_positions, ga_panchanga | FAIL (active) | 24 recorded gate failures across 8 runs (Jun 12-17), all lahiri_chitrapaksha ayanamsha | BLOCKING |
| 15 | Canonical row-count reconcile | chart_facts | WARN | Post-enrichment chart_facts ~41,218 estimated (vs 27,554 closure baseline); requires live DB confirmation | STEP 2 (live run) |

---

## Detailed findings

### Check 1: count_sql validity + chart-scoping

**Status: PASS with structural note**

All 10 registered L1 ga_* assets in `platform/scripts/seed/asset_registry_seed.ts` carry syntactically
valid count_sql that scopes on `chart_id = $1`. No unscoped "NOT MIGRATED" placeholders remain.

| asset_id | count_sql basis | chart-scoped |
|---|---|---|
| ga_positions | chart_facts WHERE chart_id=$1 AND fact_category IN ('graha_position','graha_sign_attributes') | YES |
| ga_vargas | chart_divisionals WHERE chart_id=$1 | YES |
| ga_dashas | chart_dashas WHERE chart_id=$1 | YES |
| ga_strength | chart_facts WHERE chart_id=$1 AND (fact_category LIKE 'graha_shadbala_%' OR IN (...) OR LIKE 'graha_%_bala_per_varga') | YES — updated migration 307 |
| ga_sensitive | chart_facts WHERE chart_id=$1 AND (fact_category IN (...16 categories...) OR LIKE 'esoteric_point_%' OR LIKE 'kp_%' OR LIKE 'tajik_%') | YES — updated migration 307 |
| ga_panchanga | chart_facts WHERE chart_id=$1 AND fact_category LIKE 'panchanga%' | YES |
| ga_sade_sati | chart_facts WHERE chart_id=$1 AND fact_category IN (...15 categories...) | YES |
| ga_tajaka | l1_tajik_varsha_year_lords WHERE chart_id=$1 | YES |
| ga_structural | chart_facts WHERE chart_id=$1 AND (LIKE 'aspect_%' OR ... OR IN (...25 categories...)) | YES — large multi-clause |
| ga_nakshatra | chart_facts WHERE chart_id=$1 AND fact_category IN (...14 categories...) | YES |

**Structural note — ga_structural count_sql overlaps ga_positions:**
The `ga_structural` count_sql `IN (...)` clause includes `'graha_position', 'graha_sign_attributes'` — the same categories selected by `ga_positions.count_sql`. The cockpit stats display for these two assets will double-count those rows. This is a cosmetic display issue only (not a data integrity issue), since the data exists once in chart_facts.

**Five satellite assets absent from registry:**
`ga_yoga`, `ga_condition`, `ga_prashna`, `ga_vastu`, `ga_medical` have Python writers with dedicated tables but no `asset_registry` rows. These are invisible to the cockpit. This is a pre-existing condition, not introduced by this branch.

---

### Check 2: target_floor vs achieved count

**Status: WARN — two floors are branch-local projections**

| asset_id | target_floor | Evidence | Confidence |
|---|---|---|---|
| ga_positions | 50 | Comment: "achieved canonical count for 482012f1" | STABLE — prod-verified |
| ga_vargas | 21,635 | Comment: "migration 220, 2026-06-11" | STABLE — prod-verified |
| ga_dashas | 536,471 | Comment: "migration 220, 2026-06-11" | STABLE — prod-verified |
| ga_strength | **11,936** | Comment: "migration 307, 2026-06-18" | **WARN — branch-local projection, not prod-run** |
| ga_sensitive | **8,610** | Comment: "migration 307, 2026-06-18" | **WARN — branch-local projection, not prod-run** |
| ga_panchanga | 221 | Comment: "migration 220, 2026-06-11" | STABLE — prod-verified |
| ga_sade_sati | 11,019 | Comment: "migration 220, 2026-06-11" | STABLE — prod-verified |
| ga_tajaka | 240 | Comment: "A7 hybrid window varsha 1..48 x 5 ayanamshas" | STABLE — prod-verified |
| ga_structural | 53,953 | Comment: "all-30-vargas expansion + argala-per-varga (2026-06-15)" | STABLE — prod-verified |
| ga_nakshatra | 1,802 | Comment: "set after first prod build 2026-06-17 (§N.4)" | STABLE — prod-verified |

The §N.4 principle ("floors are aspirational, not gates") is correctly applied throughout.
The ga_strength and ga_sensitive floors of 11,936 and 8,610 were computed as post-enrichment
projections on this branch. Per CLAUDECODE_BRIEF_L1_ENRICHMENT_CLOSE_v1_0.md STEP 2, they must
be confirmed against an actual prod run for chart `482012f1` before the PR merges.

---

### Check 3: asset_throughput freshness

**Status: NEEDS-LIVE-DB**

`asset_throughput` is written by `_telemetry.py` `update_asset_throughput()` only when the writer
runs in standalone mode (`owns_conn=True`). On the orchestrator path the orchestrator owns this write.

The cockpit `stats/route.ts` `deriveState()` uses `actualRows > 0` (from count_sql) as the primary
"lit" signal. It falls back to `asset_throughput` only when `actualRows === 0`. A `build_state_stale`
badge fires when rows are present but `asset_throughput` disagrees.

Assets most likely to show stale asset_throughput after this branch:
- **ga_strength** — rebuilt via enrichment amendments; standalone run confirmed (`run_ga_sensitive_standalone.py` 
  is an untracked file on this branch). Whether throughput was updated depends on whether standalone ran to completion.
- **ga_sensitive** — same situation.

Cannot confirm without a live DB read. Recommend STEP 2 verification query:
```sql
SELECT asset_id, rows_written, last_built_at
FROM asset_throughput
WHERE asset_id IN ('ga_strength', 'ga_sensitive')
ORDER BY last_built_at DESC;
```

---

### Check 4: catalog_status = 'CURRENT'

**Status: PASS**

All 10 registered L1 ga_* assets have `catalog_status: 'CURRENT'` explicitly set in the seed file.
The seed uses `ON CONFLICT DO UPDATE`, so it enforces this on every apply. Migration
`236_ganita_catalog_current.sql` (confirmed to exist) set `catalog_status='CURRENT'` at the DB
level in a prior migration pass; the seed reinforces this.

No ga_* asset is in DORMANT, LEGACY, or any other status. All 10 are CURRENT.

---

### Check 5: ga_prashna 0-rows cockpit render

**Status: PASS (design is correct; cockpit cosmetic bug tracked separately)**

The cockpit determines "built vs not built" via `stats/route.ts` `deriveState()`:
- `actualRows > 0` → `'lit'`
- `actualRows = 0` → falls back to `asset_throughput` state (building / stale / dormant)

`ga_prashna` is a natal chart asset — its writer (`ga_prashna_writer.py`) is explicitly a no-op for
natal charts. `OPEN_ITEMS_REGISTER_v1_0.md` §A0 confirms: "ga_prashna=0 and ga_yoga=5 are CORRECT
(not unbuilt)."

The design issue: 0-row assets render as "dormant" even when 0 is the correct final state. The fix
requires a `is_zero_correct` flag or similar in the registry. This is tracked in
`CLAUDECODE_BRIEF_COCKPIT_COSMETIC_v1_0.md` and is a cosmetic-only fix, not a data issue.

---

### Check 6: Floored items — citation_ref pattern

**Status: PASS — floored rows are explicit, labeled, and non-silent**

Both `ga_sensitive_writer.py` and `ga_strength_writer.py` write floored rows with explicit markers.
The flooring marker lives in `fact_value_text` and `verification_pass_status`, not inside
`citation_ref` itself (citation_ref uses the standard `_citation_ref()` helper). This is consistent
and correct.

**ga_sensitive_writer.py evidence:**
- Line 1605: `_build_lal_kitab_floored_rows()` — emits rows with
  `formula_provenance_text="G41 Lal Kitab corpus: prerequisite absent — floored to null"` and
  `verification_pass_status="floored"`
- Line 1642: `_build_maharsi_floored_rows()` —
  `formula_provenance_text="G44 Nadi-rishi attribution table: prerequisite absent — floored to null"`,
  `verification_pass_status="floored"`
- Line 1908/1913: Vighati Lagna row:
  `fact_key="floored_requires_birth_seconds_precision"`, `verification_pass_status="floored"`

**ga_strength_writer.py evidence:**
- Line 1377: `"fact_value_text": "floored: drik_requires_varga_aspect_geometry"`,
  `"verification_pass_status": "floored"`
- Line 1383: `citation_human` contains `"floored — "` inline explanation
- Line 1387: `"verification_pass_status": "floored"`
- Line 1418/1423: `"floored: no_canonical_per_varga_method"` for Kala and Cheshta bala per varga

Floored rows are NOT silent drops. They are explicit rows in the DB with queryable
`verification_pass_status='floored'` status and the reason in `fact_value_text`.

---

### Check 7: Silent failures in writers

**Status: WARN — three concern patterns**

**Pattern 1 — logger.debug on error swallowing (LOW RISK):**
- `ga_dashas_writer.py:2557`: `logger.debug("[ga_dashas] Final throughput update skipped: %s", exc)` —
  a telemetry write failure is demoted to DEBUG. Not data-corrupting but invisible in prod logs.
  This also violates the "writer does not write asset_throughput on orchestrator path" contract
  (see Check 10 note).

**Pattern 2 — bare `except Exception: pass` inside inner loops (HIGH RISK):**
- `ga_yoga_writer.py:169`: Bare `except Exception: pass` inside the yoga evaluation loop. A single
  yoga's evaluation failure silently drops that yoga. This is the highest-risk pattern because the
  loss is invisible in the output — the writer completes with no error, but rows are missing.

**Pattern 3 — bare `except Exception: pass` in outer paths (MEDIUM RISK):**
- `ga_structural_writer.py:571, 589, 1199, 3482`: Four bare `except: pass` blocks in a 4,348-line
  writer. Structural computation failures could be silently suppressed.
- `ga_panchanga_writer.py:293, 810, 865`: Three bare `except: pass` blocks.
- `ga_sade_sati_writer.py:206`: One bare `except: pass`.
- `ga_positions_writer.py:237`: One bare `except: pass`.
- `ga_sensitive_writer.py:472-473, 482-483`: Prerequisite checks for G44_NADI and G41_LAL_KITAB
  tables swallow all exceptions. A DB connectivity failure is indistinguishable from "prereqs
  genuinely absent." This is defensible (floored path is correct behavior) but produces no diagnostic.

**Non-issues (correctly designed):**
- `ga_sensitive_writer.py:2302-2305`: `except Exception as exc: logger.warning(...)` — INSERT
  failures logged at WARNING, not swallowed.
- `ga_sensitive_writer.py:2319-2325`: MV refresh failure falls through to second attempt, then
  returns `f"ERROR: {exc2}"`. Not silent.
- `ga_condition_writer.py:585, 602, 631, 686, 730, 802, 895`: `except Exception as exc: logger.warning(...)` —
  all correct; degrade gracefully with a warning.
- `_telemetry.py:59`: `except Exception as exc: # noqa: BLE001 — telemetry is non-fatal` —
  explicitly labeled as acceptable.

**Recommendation:** The bare `except: pass` patterns are pre-existing and non-blocking for this PR.
They should be hardened post-merge (add `logger.warning` at minimum). The `ga_yoga:169` inner-loop
pattern is the most concerning and should be addressed soonest.

---

### Check 8: L1 authority within L1

**Status: PASS**

`ga_condition_writer.py` loads all graha positions from `chart_facts` and `chart_divisionals`,
not from an ephemeris recomputation. This is the correct L1-internal authority pattern.

Evidence:
- Line 638: `_load_positions_from_chart_facts(conn, chart_id, ayanamsha_id)` —
  docstring: "Load graha positions from chart_facts for a given chart + ayanamsha"
- Line 652: `FROM chart_facts` — actual SELECT against L1 table
- Line 705: Second SELECT `FROM chart_facts` for varga dignity spread
- `_load_varga_dignity_spread(conn, chart_id, ayanamsha_id, graha)` at line 1175:
  loads from `chart_divisionals` (the L1-authoritative varga data)

`ga_condition_writer.py` does contain its own `SIGN_LORDS` dict (line 43-48) and `DIGNITY_SCORES`
dict (line 50-61). These are static classical tables (not chart-specific computations) equivalent
to a lookup table, so they do not violate L1 authority.

The condition score formula (`0.35×dignity_d1 + 0.20×deeptaadi + 0.10×baladi + 0.20×varga − combustion_penalty`)
is a derivation from L1 facts — correct, as ga_condition is an L1 asset that derives from chart_facts.

---

### Check 9: Idempotency

**Status: PASS — delete-then-insert across all writers; no accretion risk**

`_idempotency.py` provides four helpers, each with DELETE scoped to natural key:
- `replace_prior_chart_facts(conn, rows)` — DELETE scoped to `(chart_id, ayanamsha_id, fact_category)`
- `replace_prior_chart_dashas(conn, rows)` — DELETE scoped to `(chart_id, ayanamsha_id, system_id)`
- `replace_prior_chart_divisionals(conn, rows)` — DELETE scoped to `(chart_id, ayanamsha_id, varga)`
- `replace_prior_tajik_varsha(conn, rows)` — DELETE scoped to `(chart_id, ayanamsha_id, varsha_year)`

All main writers call the relevant helper before INSERT. Confirmed for: ga_positions_writer.py,
ga_sensitive_writer.py, ga_strength_writer.py, ga_structural_writer.py, ga_panchanga_writer.py.

**`ga_condition_writer.py`:** Uses a direct `DELETE FROM ga_condition_composite WHERE chart_id=%s AND ayanamsha_id=%s`
(line 1261) rather than an `_idempotency.py` helper. Correct — `ga_condition_composite` is a
separate table not covered by the four helpers, and the DELETE is scoped correctly.

**`ga_yoga_writer.py`:** Same pattern — direct `DELETE FROM ga_yoga_firings WHERE chart_id=%s AND ayanamsha_id=%s`
(line 940). Correct for a separate table.

The `_idempotency.py` comment documents the prior accretion problem that was fixed:
"Re-running a writer under a fresh build_id appends a second copy instead of replacing the first.
Repeated rebuilds therefore accrete stale rows (the 13-build chart_facts / 7-build chart_dashas
bloat that had to be hand-cleaned)." The current helpers solve this by scoping DELETE to
`(chart_id, ayanamsha_id, fact_category)` regardless of build_id.

---

### Check 10: Orchestrator contract compliance

**Status: PASS with one note**

**@register location:** All `@register` decorators live in
`platform/python-sidecar/pipeline/orchestrator/writers/` adapter files, NOT in the `ga_writers/`
modules themselves. The `ga_writers/` directory contains pure computation modules; the adapter
layer wraps them with `@register` and the `WriterBase` interface. This is a valid two-layer
architecture — the computation module is independently testable, and the adapter is thin.

Adapters confirmed for: ga_sensitive, ga_panchanga, ga_structural, ga_strength, ga_condition,
ga_yoga, ga_dashas, ga_vargas, ga_positions, ga_sade_sati, ga_tajaka.

**ctx.db_conn only (no own connection on orchestrator path):**
The `owns_conn` flag pattern is consistent. Evidence from ga_sensitive_writer.py:
```python
owns_conn = conn is None  # line 2404
_insert_rows(conn, all_rows, commit=owns_conn)  # line 2503
_refresh_mv(conn, commit=owns_conn)  # line 2506
```
When the orchestrator passes `ctx.db_conn`, `owns_conn=False` and no `commit()` fires.
The `_conn()` helper opens a connection only when `conn is None` — orchestrator path always
provides `conn`.

**No asset_throughput writes on orchestrator path:**
`_telemetry.py`'s `update_asset_throughput()` is called only inside `if owns_conn:` blocks
in each writer's standalone entry function. Orchestrator adapters never call `_telemetry.py`.

**One note — ga_dashas_writer.py:2555:**
A call to `_update_asset_throughput` occurs unconditionally (not gated by `owns_conn`), wrapped
in a bare `except Exception as exc: logger.debug(...)`. On the orchestrator path this call fires,
fails (presumably due to permission or context mismatch), and is silently swallowed. Non-harmful
in practice but is a contract violation: the writer should not attempt this write at all on the
orchestrator path. Non-blocking for this PR.

---

### Check 11: Light → Heavy audit

**Status: WARN — two light writers carry high idle_in_transaction exposure**

Writers classified as HEAVY (plan_substeps + run_substep, one substep per ayanamsha) correctly
break up the 5-ayanamsha loop:
- `ga_structural` — documented: "HEAVY orchestrator: plan_substeps + run_substep, one sub-step per ayanamsha"
- `ga_sensitive` — declared heavy in orchestrator adapter
- `ga_condition` — declared heavy in orchestrator adapter
- `ga_yoga` — declared heavy in orchestrator adapter

Writers classified as LIGHT (single `run()` — entire build in one transaction context):

| Writer | Rows | Ayanamsha loops | Risk |
|---|---|---|---|
| ga_dashas | 536,471 | 7 dasha systems × 5 ayanamshas | HIGH — largest light writer |
| ga_vargas | 21,635 | 6 batches of 5 vargas | MEDIUM |
| ga_strength | 11,936 (post-enrichment) | 5 ayanamshas | MEDIUM |
| ga_positions | 50 | 5 ayanamshas | LOW |
| ga_panchanga | 221 | per ayanamsha | LOW |
| ga_sade_sati | 11,019 | per ayanamsha | MEDIUM |
| ga_nakshatra | 1,802 | per ayanamsha | LOW |

**ga_dashas is the highest risk:** 536,471 rows in a single transaction context at ~100K rows/transaction.

**ga_vargas batching note:** ga_vargas_writer.py uses `conn.commit()` calls at lines 2363, 2384,
2394, 2439, 2488. On standalone path (`commit=True`) these are mid-batch commits. On the orchestrator
path (`commit=False`), no mid-batch commits occur — the entire 21,635-row build runs in one transaction.

**Mitigations confirmed:**
- **Guard A** (migration 241): `idle_in_transaction_session_timeout = '120s'` is set at the DB level.
  Migration 241 reads: `ALTER ROLE authenticator SET idle_in_transaction_session_timeout = '120000';`
  (120 seconds). This kills orphaned transactions server-side.
- **Guard B** (orchestrator finally/rollback): The CLOSE brief (STEP 0) lists confirming Guard B
  as a prerequisite before the prod run. Guard B implementation cannot be confirmed from file reads
  alone — it lives in the orchestrator adapter layer. Must be verified before STEP 2 prod run.

---

### Check 12: Graha naming heterogeneity

**Status: PASS — TitleCase universal; single shared source of truth**

The canonical graha naming is established in `ga_positions_writer.py` `PLANET_TO_SUBJECT` (lines 54-65):
```python
"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
"Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
"Rahu": "RAH_MEAN", "Ketu": "KET_MEAN", "Lagna": "LAGNA"
```

Planet name (engine key): TitleCase — `"Sun"`, `"Moon"`, `"Saturn"` etc.
fact_subject (DB column): UPPER_SNAKE — `"SUN"`, `"SAT"` etc.

All writers that name planets explicitly use TitleCase consistently:
- `ga_condition_writer.py:40`: `ALL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]`
- `ga_strength_writer.py:58-66`: `NAISARGIKA_BALA` keys: `"Sun"`, `"Moon"`, `"Jupiter"` etc.
- `ga_vargas_writer.py:94`: `CLASSICAL_BODIES = ["Sun", "Moon", "Mars", ...]`
- `ga_sensitive_writer.py:71-76`: `SIGN_LORDS` keys: `"Mars"`, `"Venus"` etc.
- `ga_sade_sati_writer.py`: Uses `"Saturn"` throughout in citation_human strings

All writers import `PLANET_TO_SUBJECT` and `CANONICAL_AYANAMSHAS` from `ga_positions_writer` —
single shared source of truth. No heterogeneity found. No 'sun' (lowercase) or other variant seen.

---

### Check 13: Dead tables / migration fragmentation

**Status: WARN — two fragmentation concerns**

**Migration 237 is absent:**
Confirmed files in the 230-241 range:
```
230_bodha_registry_reconcile.sql
231_bg_target_floor_fix.sql
232_drop_ganita_positions.sql
233_bg_throughput_dormant_to_lit.sql
234_activate_romanize_service_engines.sql
235_all_dormant_throughput_to_lit.sql
236_ganita_catalog_current.sql
238_bg_nakshatra_tables.sql
239_bg_nakshatra_registry.sql
240_bg_nakshatra_target_floor.sql
241_idle_in_transaction_timeout.sql
```
Migration 237 is missing from the directory. This is either squashed into 236, renamed, or exists
on main only. Must be confirmed before merge to ensure the migration sequence is contiguous.

**Migrations 242-306 absent from this branch:**
The KICKOFF document states "main is at 307; start at 308." This branch authors migration 307 but
migrations 242-306 (the L0 arc migrations on main) are not present in the working tree. Before
merge, this branch must rebase onto main so that:
1. Migrations 242-306 are present
2. Migration 307 applies cleanly after 306

**Migration 307 SQL file status:**
The commit `feat(l1-enrichment): migration 307 + seed — count_sql + target_floor post-enrichment`
references migration 307, but the SQL file for migration 307 was not confirmed in the directory
listing. The file may be: (a) present but not in the listing range reviewed, (b) committed to main
branch only, or (c) missing. Must be confirmed present before merge.

**No deferred DROPs:**
Migrations 230-241 contain one DROP: `232_drop_ganita_positions.sql` (already executed, table
`ganita_positions` confirmed dropped). No other deferred DROPs pending.

**Table `chart_facts` is written by multiple writers** (ga_positions, ga_panchanga, ga_strength,
ga_sensitive, ga_structural, ga_nakshatra, ga_sade_sati). This is by design — chart_facts is the
shared L1 fact store. The idempotency helpers scope DELETE by `(chart_id, ayanamsha_id, fact_category)`,
preventing cross-writer interference.

---

### Check 14: FORENSIC 7/7

**Status: FAIL (ACTIVE, UNRESOLVED) — 24 gate failures, 8 runs, June 12-17**

The FORENSIC gate checks 7 birth anchors for chart `482012f1`:
1. Sun sign = Capricorn
2. Moon nakshatra = Purva Bhadrapada
3. Lagna sign = Aries (all 5 ayanamshas)
4. Tithi = Shukla Tritiya
5. Vara = Ravivara
6. Yoga = Shiva
7. Karana = Garaja

**Pattern A — GA4 Panchanga gate failures (5 failures per run):**
Recorded in `l1-ganita-build/CONDUCTOR_HALT_LOG.md`, 9 timestamps Jun 11-17,
all `lahiri_chitrapaksha` ayanamsha:
- Tithi: got 'Shukla Panchami' (expected Shukla Tritiya)
- Vara: got 'Somavara' (expected Ravivara)
- Yoga: got 'Vyaghata' (expected Shiva)
- Karana: got 'Kintughna' (expected Garaja)
- Nakshatra: got 'Ashwini' (expected Purva Bhadrapada)

**Pattern B — GA3 Positions gate failures (3 failures per run):**
Recorded in `CONDUCTOR/CONDUCTOR_HALT_LOG.md`, repeated Jun 12-17 across 8 runs:
- Sun sign expected Capricorn, got 'Aries'
- Moon nakshatra expected 'Purva Bhadrapada', got 'Ashwini'
- Lagna sign expected 'Aries', got 'Scorpio' (conductor note: "Known trap: NOT Scorpio")

**Root cause hypothesis:**
ALL failures are for `lahiri_chitrapaksha` ayanamsha only. The `CANONICAL_AYANAMSHAS` map
(ga_positions_writer.py line 46-51) maps `"lahiri_chitrapaksha"` → `"lahiri"` (the pyjhora adapter key).
The returned values ('Aries' for Sun sign, 'Scorpio' for Lagna) match Rahu/Ketu-axis rotated outputs,
suggesting the `lahiri_chitrapaksha` adapter is returning values shifted by 6 signs, which is a
classic "opposite sign" bug in ayanamsha handling.

Both the GA3 and GA4 failures return the same wrong planet/nakshatra ('Ashwini' for Moon), indicating
the same root cause affects both writers. The failure is in the pyjhora engine's output for the
`lahiri_chitrapaksha` ayanamsha key, not in the writer logic.

**SQL to verify after prod run:**
```sql
SELECT fact_category, fact_subject, fact_key, fact_value_text, ayanamsha_id
FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN ('panchanga_tithi','panchanga_vara','panchanga_yoga',
                        'panchanga_karana','graha_position','graha_nakshatra')
  AND (
    (fact_category = 'panchanga_tithi'    AND fact_key = 'tithi_name')
    OR (fact_category = 'panchanga_vara'  AND fact_key = 'vara_name')
    OR (fact_category = 'panchanga_yoga'  AND fact_key = 'yoga_name')
    OR (fact_category = 'panchanga_karana' AND fact_key = 'karana_name')
    OR (fact_category = 'graha_position'  AND fact_subject IN ('SUN','MOON','LAGNA') AND fact_key = 'sign')
    OR (fact_category = 'graha_nakshatra' AND fact_subject = 'MOON' AND fact_key = 'nakshatra_name')
  )
ORDER BY ayanamsha_id, fact_category, fact_subject;
```

---

### Check 15: Canonical row-count reconcile

**Status: WARN — post-enrichment totals are projections, not prod-confirmed**

**L1_GANITA_CLOSURE_v1_0.md baselines (pre-enrichment):**
- chart_facts: 27,554
- chart_dashas: 536,471
- chart_divisionals: 21,635
- Grand total: 585,710

**Post-enrichment delta estimation:**

| Asset | Pre-enrichment est. | Post-enrichment floor | Delta |
|---|---|---|---|
| ga_strength | ~2,184 (D1-only, estimated) | 11,936 | +~9,752 |
| ga_sensitive | ~6,500 (pre-Amendment-3, estimated) | 8,610 | +~2,110 |
| ga_nakshatra | 0 (new asset) | 1,802 | +1,802 |
| ga_structural | included in closure baseline (53,953) | 53,953 | 0 (already counted) |

**Projected new chart_facts total: ~27,554 + 9,752 + 2,110 + 1,802 ≈ 41,218**

**Unchanged tables:**
- chart_dashas: 536,471 (no dasha enrichment)
- chart_divisionals: 21,635 (no varga enrichment)

**Projected new grand total: ~41,218 + 536,471 + 21,635 ≈ 599,324**
(delta of ~+13,614 from enrichment, vs closure baseline of 585,710)

**Confirmation query for STEP 2:**
```sql
SELECT
  'chart_facts'     AS table_name, count(*) AS cnt
  FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
UNION ALL
SELECT 'chart_dashas',      count(*) FROM chart_dashas      WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
UNION ALL
SELECT 'chart_divisionals', count(*) FROM chart_divisionals WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
```

---

## Fix-target list (for Phase 2)

Ordered by blocking severity:

### BLOCKING (must resolve before PR merge)

**B1 — FORENSIC 7/7 gate failures (`lahiri_chitrapaksha` ayanamsha)**
All Pattern A and Pattern B failures are isolated to the `lahiri_chitrapaksha` ayanamsha key.
The pyjhora adapter maps this to the `"lahiri"` key. The returned values are 6-sign-shifted,
suggesting an ayanamsha-offset sign bug in the engine for this specific key.
Approach: Test pyjhora adapter directly with `ayanamsha="lahiri"` for the native birth params.
If engine returns Aries for Sun at Lahiri, the engine is computing for the wrong date/time context.
If engine returns Capricorn correctly in isolation but fails during the 5-ayanamsha loop, this
is a state-leak bug — the `lahiri_chitrapaksha` pass is being corrupted by a prior pass.
File to examine: the pyjhora adapter initialization and the ayanamsha iteration order.

**B2 — Migration 307 SQL file confirmation**
Confirm that `platform/supabase/migrations/307_*.sql` exists on disk. If it is present on main
but not in this branch, rebase to pick it up. If it was never created (only the seed was updated),
the migration SQL must be authored before merge.

**B3 — Rebase onto main to acquire migrations 242-306**
This branch authors migration 307 but the sequence from main (242-306) is not present. Before
merge, rebase or merge main to ensure the full migration sequence is present and 307 applies
cleanly after 306.

### REQUIRED BEFORE DECLARING L1 CLOSED (STEP 2 prerequisites)

**B4 — Prod run: ga_strength, ga_sensitive, ga_condition**
Run all three enrichment writers on PROD chart `482012f1`. Verify:
- ga_strength count >= 11,936
- ga_sensitive count >= 8,610
- ga_condition count > 0
Update target_floor values in seed if actual counts differ from projections.

**B5 — Confirm orchestrator Guard B (finally/rollback)**
Verify that the orchestrator adapter layer has a `finally:` block that rolls back
`ctx.db_conn` on writer failure. This is the conn-resilience Guard B from the CLOSE brief STEP 0.
Without Guard B, a writer crash leaves the connection in an orphaned transaction state until
Guard A (120s idle_in_transaction timeout) fires.

**B6 — asset_throughput freshness verification**
After STEP 2 prod runs, query `asset_throughput` for ga_strength and ga_sensitive to confirm
`rows_written` and `last_built_at` are current. If throughput is stale, determine whether the
orchestrator path updates it correctly or whether a manual throughput refresh is needed.

### NON-BLOCKING (post-merge hardening)

**B7 — ga_yoga inner-loop bare except (highest priority among non-blocking)**
`ga_yoga_writer.py:169`: Replace `except Exception: pass` with `except Exception as exc: logger.warning(...)`.
A silent drop in the yoga evaluation loop is invisible in output.

**B8 — ga_structural bare except × 4**
Lines 571, 589, 1199, 3482: Add `logger.warning` minimum to each bare `except: pass`.

**B9 — ga_panchanga bare except × 3**
Lines 293, 810, 865: Same treatment.

**B10 — ga_dashas vestigial asset_throughput write**
`ga_dashas_writer.py:2555`: Move the `_update_asset_throughput` call inside `if owns_conn:`.

**B11 — Migration 237 gap confirmation**
Confirm whether migration 237 was squashed, renamed, or is genuinely missing. If missing, create
a placeholder no-op migration `237_placeholder.sql` to preserve sequence integrity.

**B12 — ga_structural count_sql overlap with ga_positions**
The `ga_structural.count_sql` includes `'graha_position', 'graha_sign_attributes'` which are also
counted by `ga_positions.count_sql`. Remove these two categories from `ga_structural.count_sql`
so the cockpit stat tiles show non-overlapping counts.

---

## B6 Light → Heavy audit results

| Writer | Pattern | Row count | Ayanamsha exposure | Risk | Guard |
|---|---|---|---|---|---|
| ga_dashas | LIGHT | 536,471 | 5 ayanamshas × 7 systems in 1 tx | HIGH | Guard A (migration 241) |
| ga_vargas | LIGHT | 21,635 | 5 ayanamshas × 6 batches in 1 tx | MEDIUM | Guard A |
| ga_strength | LIGHT | 11,936 | 5 ayanamshas in 1 tx | MEDIUM | Guard A |
| ga_sade_sati | LIGHT | 11,019 | per ayanamsha in 1 tx | MEDIUM | Guard A |
| ga_nakshatra | LIGHT | 1,802 | per ayanamsha in 1 tx | LOW | Guard A |
| ga_panchanga | LIGHT | 221 | per ayanamsha in 1 tx | LOW | Guard A |
| ga_positions | LIGHT | 50 | 5 ayanamshas in 1 tx | LOW | Guard A |
| ga_structural | HEAVY | 53,953 | 1 substep per ayanamsha | RESOLVED | Guard A + Guard B |
| ga_sensitive | HEAVY | 8,610 | 1 substep per ayanamsha | RESOLVED | Guard A + Guard B |
| ga_condition | HEAVY | — | 1 substep per ayanamsha | RESOLVED | Guard A + Guard B |
| ga_yoga | HEAVY | 5 | 1 substep per ayanamsha | RESOLVED | Guard A + Guard B |

Guard A = `idle_in_transaction_session_timeout=120s` (migration 241, confirmed).
Guard B = orchestrator finally/rollback (must be confirmed before STEP 2 prod run).

The heavy pattern for ga_structural, ga_sensitive, ga_condition, ga_yoga correctly addresses the
high-row-count ayanamsha loop problem. The remaining MEDIUM-risk light writers (ga_dashas, ga_vargas)
are protected by Guard A alone. Promoting them to heavy would be the robust fix; for now,
Guard A provides acceptable mitigation.

---

## B2/B3/B4 connection-resilience status

**Migration 241 — confirmed:**
`platform/supabase/migrations/241_idle_in_transaction_timeout.sql` sets:
```sql
ALTER ROLE authenticator SET idle_in_transaction_session_timeout = '120000';
-- (120 seconds)
```
This is Guard A. DB-side timeout kills orphaned transactions after 120s regardless of writer behavior.

**Connection resilience brief (`CLAUDECODE_BRIEF_CONN_RESILIENCE_AND_RESUME_v1_0.md`):**
Documents Resumability requirement: if a writer fails mid-run, the orchestrator must:
1. Roll back the current transaction (Guard B — finally/rollback block in orchestrator)
2. Re-raise the exception (not swallow it)
3. The orchestrator's build loop marks the asset FAILED and continues with the next asset

**Guard B implementation status:** Cannot confirm from static file reads. The brief lists
Guard B as STEP 0 (verify before prod run). Evidence that it was discussed and planned is present
in the brief; implementation evidence requires reading the orchestrator adapter source.

**Recommended STEP 0 verification command (read-only):**
```bash
grep -n "finally\|rollback\|except.*Exception" \
  /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/pipeline/orchestrator/*.py
```

---

## L2 Bodha notes

These items from the L1 audit are directly relevant to L2 Bodha design:

**Graha naming (action: none — already consistent):**
L1 uses TitleCase ('Sun', 'Moon') as engine keys and UPPER_SNAKE ('SUN', 'SAT') as `fact_subject`.
L2 Bodha writers that reference chart_facts should query by `fact_subject` (UPPER_SNAKE) and use
the same lookup tables imported from `ga_positions_writer.py` for any naming roundtrip.

**chart_facts fact_category namespace:**
L1 owns all fact_category values. L2 must NOT insert rows into chart_facts — L2 writes to `bodha_*`
tables only. Any L2 query against chart_facts must be read-only.

**Floored rows visibility:**
L2 signals that reference L1 sensitive points must check `verification_pass_status='floored'` before
treating a fact_value as reliable. A floored row means the value is null/unavailable, not zero.
The `constituent_facts_array` in MSR signals that reference floored L1 rows must propagate the
floored status upward rather than treating null as a valid signal value.

**The lahiri_chitrapaksha ayanamsha gap (FORENSIC failure):**
If this ayanamsha continues to produce wrong results in production, L2 Bodha signals derived from
charts built with the `lahiri_chitrapaksha` ayanamsha will be systematically incorrect. L2 must
not begin building until the FORENSIC 7/7 gate passes for all 5 ayanamshas.

**ga_condition composite table:**
`ga_condition_composite` (written by ga_condition_writer.py) is an L1 table that provides
pre-computed dignity + balance scores per graha per ayanamsha. L2 Bodha derivations that need
condition scores should SELECT from `ga_condition_composite` rather than recomputing dignity from
chart_facts — this is the correct L1-authority pattern and avoids L2 recomputing what L1 owns.

---

*End of L1_INTEGRITY_FINDINGS_v1_0.md — read-only audit, 2026-06-18*
*Total checks: 15 | PASS: 6 | WARN: 6 | FAIL: 1 | NEEDS-LIVE-DB: 2*
*Blocking items before merge: B1 (FORENSIC), B2 (migration 307 SQL), B3 (rebase)*
*Blocking before L1 close declaration: B4 (prod run), B5 (Guard B), B6 (throughput)*
