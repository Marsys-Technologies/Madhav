---
artifact: PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0.md
canonical_id: PRE_REGEN_AUDIT_FINDINGS_REGISTER
version: 1.4
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
purpose: >
  Per-asset findings register for the Pre-Regeneration Full Audit Campaign (L0–L4).
  One row per audited file × 3 axes × PASS/FAIL. Becomes the fix plan when all
  waves complete.
waves_complete: W0, W1, W2
waves_pending: W3, W4, W5
changelog:
  - version: 1.4
    date: 2026-06-26
    author: Claude (Cowork)
    note: Wave 2 complete — 13 ga_* L1 Gaṇita assets audited; contamination fixes committed (dce44b91); 4 majors + 3 minors found.
  - version: 1.3
    date: 2026-06-26
    author: Claude (Cowork)
    note: Wave 1 complete — 18 bg_* L0 Brahmagyan assets audited; 2 majors + 1 minor found.
  - version: 1.2
    date: 2026-06-26
    author: Claude (Cowork)
    note: Wave 0 widened guard results — 9-site authoritative vulnerable list added; fetch_birth_params docstring fix noted.
  - version: 1.1
    date: 2026-06-26
    author: Claude (Cowork)
    note: Schema corrected to match §3 spec — added A3/A4/A5 and fix_owner_phase columns; B2-B7 and C2-C5 noted as N/A with deferred rationale.
  - version: 1.0
    date: 2026-06-26
    author: Claude (Cowork)
    note: Initial creation. Wave 0 findings populated (16 files audited).
---

# Pre-Regeneration Audit Findings Register v1.0

## How to Read This Register

Each row represents one audited file. Columns follow the 3-axis rubric defined
in `PRE_REGEN_AUDIT_HARNESS_v1_0.md §5–§6`. Cell values: `PASS`, `FAIL`, `WARN`,
or `N/A` (check not applicable to this file/layer).

**Severity:** `none` | `minor` | `major` | `blocker`

**VERDICT:** `PASS` | `FIX-REQUIRED` | `REVIEW-NEEDED`

---

## Wave 0 — Static Architecture Sweep (2026-06-26)

**Scope:** Python sidecar files — orchestrator, writers, routers, shared compute,
L0 scripts. Axis A (static grep + code read) and Axis C (WriterBase conformance).
Axis B (SQL data checks) deferred to Wave 2 (requires live DB).

### Wave 0 Findings Table

<!-- Spec schema (§3): asset_id | layer | A1 | A2..A7 | B1..B7 | C1..C5 | VERDICT | severity | fix summary | fix_owner_phase -->
<!-- Wave 0 note: B2–B7 require live DB query (harness §2 templates); all N/A here. C2–C5 apply to L2+ interpretation assets; all N/A for Wave 0 shared-compute files. Columns included in full for Waves 1–5. -->

| asset_id / file | layer | A1 | A2 | A3 | A4 | A5 | A6 | A7 | B1 | C1 | VERDICT | severity | fix summary | fix_owner_phase |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `pyjhora_adapter/compute.py` | shared_compute | CHART-INDEPENDENT | N/A | N/A | N/A | N/A | PASS | PASS | N/A | PASS | **PASS** | none | None | — |
| `pipeline/orchestrator/birth_params.py` | orchestrator | CORRECTLY-GUARDED | N/A | N/A | N/A | N/A | PASS | WARN | N/A | N/A | **FIX-REQUIRED** | major | "no row" path for non-native must RAISE not return None | Wave 0 ✅ DONE |
| `pipeline/writers/panchanga_writer.py` | L1 writer | CHART-INDEPENDENT | FAIL | FAIL | N/A | N/A | PASS | PASS | N/A | PASS | **FIX-REQUIRED** | minor | Convert ON CONFLICT DO UPDATE → delete-then-insert; wrap in WriterBase adapter | Fix Plan (post-W5) |
| `routers/pyhora.py` | shared_compute | CHART-INDEPENDENT | N/A | N/A | N/A | N/A | PASS | PASS | N/A | PASS | **PASS** | none | None | — |
| `brahmagyan/l0_ephemeris.py` | L0 | CHART-INDEPENDENT | PASS | N/A | N/A | N/A | PASS | PASS | N/A | PASS | **PASS** | none | None | — |
| `brahmagyan/ephemeris_routes.py` | L0 router | CHART-INDEPENDENT | N/A | N/A | N/A | N/A | PASS | PASS | N/A | N/A | **PASS** | none | None | — |
| `brahmagyan/ganita/engine.py` | L1 engine | CHART-INDEPENDENT | PASS | N/A | N/A | N/A | PASS | PASS | N/A | PASS | **PASS** | none | None | — |
| `build_ephemeris_1900_2150.py` | L0 script | NATIVE-ONLY-BY-DESIGN | N/A | N/A | N/A | N/A | PASS | WARN | N/A | N/A | **REVIEW-NEEDED** | minor | Remove hardcoded DB credentials (lines 26–29) | Fix Plan (post-W5) |
| `pipeline/orchestrator/writers/ga_positions.py` | L1 orchestrator | CORRECTLY-GUARDED | N/A | PASS | N/A | N/A | PASS | PASS | N/A | N/A | **PASS** | none | None — reference correct pattern | — |
| `pipeline/orchestrator/writers/ga_sensitive.py` | L1 orchestrator | CORRECTLY-GUARDED | N/A | PASS | N/A | N/A | PASS | PASS | N/A | N/A | **PASS** | none | None — reference correct pattern | — |
| `pipeline/orchestrator/writers/ga_nakshatra.py` | L1 orchestrator | VULNERABLE (major) | N/A | PASS | N/A | N/A | PASS | PASS | N/A | N/A | **FIX-REQUIRED** | major | Change `ctx.config.get("birth_params", ctx.config)` → `ctx.config.get("birth_params")` | Wave 2 |
| `pipeline/orchestrator/writers/ga_transit_anchors.py` | L1 orchestrator | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | N/A | N/A | **PASS** | none | None | — |
| `pipeline/orchestrator/writers/ka_graha_sancara.py` | L3 orchestrator | NATIVE-ONLY-BY-DESIGN | N/A | PASS | N/A | N/A | PASS | PASS | N/A | N/A | **PASS** | none | None | — |
| `pipeline/orchestrator/writers/ph_rectification/__init__.py` | L4 orchestrator | NATIVE-ONLY-BY-DESIGN | PASS | PASS | N/A | N/A | PASS | PASS | N/A | N/A | **PASS** | none | None | — |
| `panchang_engine/jaimini_chara.py` | shared_compute | VULNERABLE | N/A | N/A | N/A | N/A | FAIL | FAIL | N/A | N/A | **FIX-REQUIRED** | blocker | Remove NATIVE_FALLBACK_LONGITUDES / NATIVE_LAGNA_RASHI_INDEX fallbacks; make params required | Fix Plan (post-W5) |
| `routers/jaimini.py` | shared_compute | VULNERABLE | N/A | N/A | N/A | N/A | FAIL | FAIL | N/A | N/A | **FIX-REQUIRED** | blocker | Guard: non-native birth_date must raise HTTPException(400) until ephemeris lookup is wired | Fix Plan (post-W5) |

> **B2–B7 (Axis B data checks):** All Wave 0 files: N/A — static code audit only; SQL data checks require live DB (harness templates §2). Columns will be populated for all assets in Waves 1–5.
> **C2–C5 (Axis C additional):** All Wave 0 files: N/A — C2–C5 apply to L2+ interpretation assets (classical-source fidelity, FORENSIC cross-check, spot re-derivation). Waves 1–5 will populate these.

### Wave 0 Summary

- **Files audited:** 16
- **PASS:** 11
- **FIX-REQUIRED:** 4
- **REVIEW-NEEDED:** 1
- **Blockers:** 2
  - `panchang_engine/jaimini_chara.py` — silent native-longitude contamination on non-native Chara Dasha
  - `routers/jaimini.py` — no guard; non-native request falls through to native fallback silently
- **Majors:** 2
  - `pipeline/orchestrator/birth_params.py` — "absent row" path returns None for non-native instead of raising
  - `pipeline/orchestrator/writers/ga_nakshatra.py` — wrong fallback: `ctx.config.get("birth_params", ctx.config)` passes entire config as fallback, masking missing birth_params
- **Minors:** 2
  - `pipeline/writers/panchanga_writer.py` — idempotency violation (ON CONFLICT DO UPDATE) and not wrapped in WriterBase
  - `build_ephemeris_1900_2150.py` — hardcoded DB credentials in lines 26–29

### Structural Guard Assessment

`pipeline/orchestrator/birth_params.py::fetch_birth_params` is structurally the
correct canonical helper for the orchestrator path. It correctly identifies the
native (returns a marker) and validates non-native fields. The single gap is the
"absent row" path for non-native charts: it currently returns `None` silently
instead of raising a `ValueError`. Once this gap is fixed and `ga_nakshatra.py`
is corrected, the guard is airtight end-to-end for all orchestrator-path writers.

The Jaimini router contamination (`panchang_engine/jaimini_chara.py` +
`routers/jaimini.py`) is independent of the orchestrator path. It is an
engine-level issue: the Chara Dasha engine carries hardcoded native longitude
fallbacks that activate silently when a non-native caller does not supply
`planet_longitudes` and `lagna_longitude`. The fix must be made at both layers —
the engine (remove fallbacks, make params required) and the router (guard the
endpoint before the engine is invoked).

### Wave 0 Fix List (Required Before Any Regeneration)

Ordered by severity:

1. **[BLOCKER]** `panchang_engine/jaimini_chara.py`  
   Remove `NATIVE_FALLBACK_LONGITUDES` and `NATIVE_LAGNA_RASHI_INDEX` constants
   and their fallback usage. Make `planet_longitudes` and `lagna_longitude`
   required parameters with no defaults. Any call that does not supply them must
   raise immediately.

2. **[BLOCKER]** `routers/jaimini.py`  
   Guard the `/chara_dasha` and `/chara_dasha/full` endpoints. If the request
   carries a non-native `birth_date` without explicit `planet_longitudes`, raise
   `HTTPException(400, detail="planet_longitudes required for non-native charts")`.
   Do not proceed to the engine until ephemeris lookup is wired for the router path.

3. **[MAJOR]** `pipeline/orchestrator/birth_params.py`  
   In the "no row" path (approximately lines 55–59): when the DB returns no row
   for a non-native `chart_id`, raise `ValueError(f"No birth params found for
   chart_id={chart_id}")` instead of returning `None`. Returning `None` silently
   allows downstream writers to fall through to undefined behavior.

4. **[MAJOR]** `pipeline/orchestrator/writers/ga_nakshatra.py`  
   Change line 254 from:
   ```python
   birth_params = ctx.config.get("birth_params", ctx.config)
   ```
   to:
   ```python
   birth_params = ctx.config.get("birth_params")
   ```
   The fallback `ctx.config` passes the entire config dict as `birth_params` when
   the key is absent, masking a missing-birth-params bug and potentially using
   wrong data for non-native charts.

   > **Note (Wave 2 widened guard):** The full vulnerable site count across the
   > codebase is **9 sites** (7 `or NATIVE_BIRTH` or-fallback assignments + 2
   > `CANONICAL_CHART_ID` signature defaults in `ga_tajaka_writer.py`). See the
   > "Widened Guard — Vulnerable Site List" section below for the authoritative list.

**[MAJOR]** `pipeline/orchestrator/birth_params.py` + `tests/test_ga_writer_generalization.py` (Wave 0 follow-on):  
   `fetch_birth_params` absent-row raise (Wave 0 ✅ DONE) was shipped without
   updating the corresponding unit test (`test_missing_row_returns_none` asserted
   `is None`; now fixed to assert `ValueError`) and without updating the module
   docstring. Both corrected on branch.

5. **[MINOR]** `build_ephemeris_1900_2150.py`  
   Remove hardcoded DB credentials from lines 26–29. Replace with environment
   variable lookups (`os.environ["DB_HOST"]` etc.) or a shared config helper.

6. **[MINOR]** `pipeline/writers/panchanga_writer.py`  
   Convert idempotency from `ON CONFLICT DO UPDATE` to delete-then-insert scoped
   to `(chart_id × natural key)` per §N.3. Wrap writer in a `WriterBase` subclass
   with the `@register` decorator and `run(ctx) -> WriterResult` interface per the
   FROZEN orchestrator contract.

---

### Wave 0 Widened Guard — Complete Vulnerable Site List (Wave 2 Work List)

### Widened Guard — Vulnerable Site List (Wave 2 remediation targets)

Captured by the extended `test_no_raw_native_birth_fallback` guard (5-pattern, Wave 2 extended).
Groups 2 (ternary), 3 (dict.get) found 0 hits — patterns are proactive guards for future writers.

**Group 1 — or-fallback assignments** (`= (birth_params|bp) or NATIVE_`) — 7 sites:

| file | line | pattern |
|------|------|---------|
| `ga_writers/ga_tajaka_writer.py` | 179 | `bp = birth_params or NATIVE_BIRTH` |
| `ga_writers/ga_tajaka_writer.py` | 206 | `bp = birth_params or NATIVE_BIRTH` |
| `ga_writers/ga_tajaka_writer.py` | 593 | `bp = birth_params or NATIVE_BIRTH` |
| `ga_writers/ga_panchanga_writer.py` | 1247 | `bp = birth_params or NATIVE_BIRTH` |
| `ga_writers/ga_structural_writer.py` | 4589 | `bp = birth_params or NATIVE_BIRTH` |
| `ga_writers/ga_structural_writer.py` | 5787 | `bp = birth_params or NATIVE_BIRTH` |
| `ga_writers/ga_strength_writer.py` | 1525 | `bp = birth_params or NATIVE_BIRTH` |

**Group 2 — ternary forms** (`(birth_params|bp) if ... else NATIVE_`) — 0 hits (proactive guard)

**Group 3 — dict.get defaults** (`.get(..., NATIVE_BIRTH)`) — 0 hits (proactive guard)

**Group 4 — signature defaults** (`def ... chart_id ... = CANONICAL_CHART_ID`) — 2 sites (NEW — not in prior count):

| file | line | pattern |
|------|------|---------|
| `ga_writers/ga_tajaka_writer.py` | 544 | `def compute_varsha(chart_id: str = CANONICAL_CHART_ID, ...)` |
| `ga_writers/ga_tajaka_writer.py` | 568 | `def build_ga_tajaka(chart_id: str = CANONICAL_CHART_ID, ...)` |

**Group 5 — generic** (`(=|return).*or NATIVE_BIRTH`) — 7 sites (fully overlapping with Group 1, no additional sites)

**Total unique vulnerable sites: 9** (7 Group 1 + 2 Group 4)

Note: Group 1 and Group 5 fully overlap — all `or NATIVE_BIRTH` occurrences are already the `= bp or NATIVE_BIRTH` assignment form.

---

## Wave 1 — L0 Brahmagyan Audit (2026-06-26)

**Scope:** All 18 `bg_*` orchestrator writer adapters + their corresponding `l0_*`
source modules. Axis A (code correctness + contract conformance) + Axis C (classical
rule fidelity). Axis B (SQL data checks) deferred — all B2–B7 require live DB.

**Key A1 finding:** All 18 L0 assets are correctly CHART-INDEPENDENT. Zero native-birth
contamination risk in L0. All writers operate on global reference tables only.

**Key A6 finding:** Zero generative LLM use in any L0 writer. All data is deterministic
Python constants or deterministic transforms (embeddings via Vertex AI). §N.4
Deterministic-First upheld across all 18 assets.

### Wave 1 Findings Table

<!-- Wave 1 note: A4/A5 N/A (L0 writers carry no chart-scoped fact_ids or DERIVATION_LEDGER entries). B2–B7 deferred to Wave 2 (live DB required). C2–C5 N/A (L0 is reference data, not per-native interpretive content). -->

| asset_id / file | layer | A1 | A2 | A3 | A4 | A5 | A6 | A7 | B1 | C1 | VERDICT | severity | fix summary | fix_owner_phase |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `bg_reference` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None | — |
| `bg_nakshatra` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None | — |
| `bg_dasha_systems` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None | — |
| `bg_dignity_reference` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | **FAIL** | PASS | **FIX-REQUIRED** | minor | No asset_registry entry in any migration; docstring cites migration 250 which does not exist (250 = l3_count_sql_param_fix.sql). Add migration with `count_sql = 'SELECT count(*) FROM bg_dignity_reference'`. | Fix Plan (post-W5) |
| `bg_rules` | L0 | CHART-INDEPENDENT | PASS | **FAIL** | N/A | N/A | PASS | PASS | PASS | N/A | **FIX-REQUIRED** | major | `l0_rules.py` line 1286: direct `conn.rollback()` in exception handler — violates FROZEN orchestrator contract. Orchestrator owns all transaction boundaries. Remove rollback; re-raise or log+continue. | Wave 2 |
| `bg_yogas` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None | — |
| `bg_texts` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | Latent: `l0_texts.seed_texts()` has bare `conn.commit()` but is NOT called by orchestrator writer (writer imports TEXTS constant only). Hygiene-clean in follow-up pass. | — |
| `bg_text_index` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | N/A | **PASS** | none | count_sql intentionally measures DISTINCT topic_tag coverage, not row count — documented and correct. | — |
| `bg_compendium_index` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | N/A | **PASS** | none | None | — |
| `bg_ontology` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | `l0_ontology.seed_ontology()` defaults `autocommit=True` — writer correctly passes `False`; default is a latent trap for standalone callers. Hygiene-clean in follow-up pass. | — |
| `bg_medical_mappings` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None | — |
| `bg_remedies` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | REVIEW-NEEDED | PASS | **PASS** | minor | B1 unconfirmed: count_sql for `bg_remedies` not found in examined migrations; verify `count_sql = 'SELECT COUNT(*) FROM brahma_remedy_corpus'` is registered. `l0_remedy_corpus.seed_remedy_corpus()` also defaults `autocommit=True` — same latent trap as bg_ontology. | Fix Plan (post-W5) |
| `bg_ephemeris` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | WARN | PASS | PASS | N/A | **PASS** | minor | A6 WARN: `computed_at` uses `datetime.now()` per row — does not affect domain correctness but means computed_at varies across partial rebuilds. Replace with build-epoch timestamp from ctx if reproducibility matters. | — |
| `bg_transit_rules` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | **FAIL** | **FIX-REQUIRED** | major | Venus gochara rules missing 6 of 9 BPHS Ch.29 favourable houses — only 1/2/3 present; 4/5/8/9/11/12 with correct vedha pairs absent. Will cause L2 Bodha Venus transit synthesis to be materially incomplete. Add missing houses to `BG_TRANSIT_RULES`. | Wave 2 |
| `bg_prashna_rules` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None | — |
| `bg_doshas` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | WARN | PASS | PASS | **PASS** | none | A7 WARN: `cur.fetchone()['count']` dict-style table-existence check safe on orchestrator path (psycopg v3 dict_row) but would break on plain psycopg2 cursor in standalone use. Not a blocker. | — |
| `bg_vastu_directions` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None | — |
| `bg_concordance` | L0 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | N/A | **PASS** | none | `source_chunk_ids` stored as empty BIGINT[] due to schema mismatch — tracked in file header as known debt. | — |

> **B2–B7 (Axis B data checks):** All Wave 1 assets: deferred — require live DB. Will be folded into Wave 2 SQL sweep.
> **A4/A5:** N/A for all L0 assets — no per-chart fact_ids or DERIVATION_LEDGER entries at L0.
> **C2–C5:** N/A for all L0 assets — C2–C5 apply to L2+ interpretation and native-specific derivation.

### Wave 1 Summary

- **Assets audited:** 18 (all bg_* orchestrator writers + source modules)
- **PASS:** 15
- **FIX-REQUIRED:** 3
- **REVIEW-NEEDED:** 0
- **A1 (contamination) clean:** 18/18 — all correctly CHART-INDEPENDENT
- **Blockers:** 0
- **Majors:** 2
  - `bg_rules` / `l0_rules.py` — `conn.rollback()` in exception handler (A3 orchestrator contract violation; silently unwinds orchestrator transaction)
  - `bg_transit_rules` / `l0_transit.py` — Venus gochara rules materially incomplete (6 of 9 BPHS Ch.29 favourable houses missing; C1 fail)
- **Minors:** 1
  - `bg_dignity_reference` — no asset_registry entry in any migration; cockpit stats route cannot count rows (B1 fail)
- **REVIEW-NEEDED (non-blocking):** 1
  - `bg_remedies` — B1 count_sql not confirmed in examined migrations; needs targeted check

### Wave 1 Fix List

Ordered by severity:

1. **[MAJOR]** `l0_rules.py` line 1286  
   Remove `conn.rollback()` from the exception handler. Replace with:
   ```python
   except Exception as exc:
       logger.warning("[l0_rules] rule processing error: %s", exc)
       continue  # or raise — do NOT rollback; orchestrator owns the transaction
   ```
   Must be fixed before any multi-asset orchestrator build that includes bg_rules.

2. **[MAJOR]** `l0_transit.py` — Venus gochara rules  
   Expand `BG_TRANSIT_RULES` Venus entries to cover the full BPHS Ch.29 set.
   Missing houses with correct vedha pairs (BPHS Ch.29):
   - house=4, vedha=10
   - house=5, vedha=9
   - house=8, vedha=1
   - house=9, vedha=2
   - house=11, vedha=3
   - house=12, vedha=6
   Also evaluate adding Rahu/Ketu basic gochara rules or document the exclusion.
   Must be fixed before L2 Bodha Venus gochara synthesis.

3. **[MINOR]** `bg_dignity_reference` — missing asset_registry migration  
   Create a migration (next available number) adding bg_dignity_reference to asset_registry:
   ```sql
   INSERT INTO asset_registry (asset_id, layer, target_table, count_sql, scope, is_active)
   VALUES ('bg_dignity_reference', 'brahmagyan', 'bg_dignity_reference',
           'SELECT count(*) FROM bg_dignity_reference', 'global', true)
   ON CONFLICT (asset_id) DO NOTHING;
   ```
   Update writer docstring to reference the actual migration number.

4. **[REVIEW-NEEDED]** `bg_remedies` — confirm count_sql  
   Locate the migration registering bg_remedies in asset_registry. Verify
   `count_sql = 'SELECT COUNT(*) FROM brahma_remedy_corpus'` is present and correct.
   If missing or pointing at `asset_throughput`, treat as minor + add to fix list.

---

## Wave 2 — L1 Gaṇita Audit (2026-06-26)

**Scope:** All `ga_*` orchestrator writer adapters + `ga_writers/*` source modules.
Two parallel tracks executed in this session:

**Track A — Contamination fixes (Wave 0 debt):** All 9 vulnerable sites from Wave 0
widened guard + 2 Wave 1 source fixes committed at `dce44b91`.
`test_no_raw_native_birth_fallback` is now **GREEN** (all 6/6 contamination guard tests pass).

**Track B — Full ga_* audit:** Axis A + B1 + C1 for all 13 `ga_*` writers.

**Key meta-finding:** `ga_dashas_writer.py` contains a NATIVE_BIRTH contamination via
local alias constants (`BIRTH_IST`, `BIRTH_LAT`, `BIRTH_LON`) using the pattern
`(birth or {}).get(...) or BIRTH_IST`. This evades the structural grep guard (which
searches for `NATIVE_BIRTH` literally). The bug class is identical but the name differs.
Wave 2 carry-over: fix ga_dashas + widen grep guard to catch local-alias patterns.

**Wave 2 contamination fixes (committed at `dce44b91`):**
- `ga_tajaka_writer.py`: 3 or-fallback sites (179, 206, 593) + 2 signature defaults (544, 568) → `resolve_birth_params()` + `if bp is None: bp = NATIVE_BIRTH`
- `ga_panchanga_writer.py`: 1 or-fallback site (1247) → `resolve_birth_params()`
- `ga_structural_writer.py`: 2 or-fallback sites (4589, 5787) + 1 additional signature default on `build_ga_structural` → fixed
- `ga_strength_writer.py`: 1 or-fallback site (1525) → `resolve_birth_params()`
- `pipeline/orchestrator/writers/ga_nakshatra.py`: wrong fallback `ctx.config.get("birth_params", ctx.config)` → `ctx.config.get("birth_params")`
- `brahmagyan/l0_rules.py`: `conn.rollback()` at line 1286 → removed (Wave 1 carry-over)
- `brahmagyan/l0_transit.py`: Venus gochara 6 missing houses (BPHS Ch.29) → added (Wave 1 carry-over)

### Wave 2 Findings Table

<!-- A4/A5 N/A: L1 writers do not carry per-row DERIVATION_LEDGER entries at the writer level (derivation ledger is L2+ Bodha). B2–B7 deferred: require live DB with native chart data. C2–C5 N/A: apply to L2+ interpretation only. -->

| asset_id / file | layer | A1 | A2 | A3 | A4 | A5 | A6 | A7 | B1 | C1 | VERDICT | severity | fix summary | fix_owner_phase |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ga_writers/ga_condition_writer.py` | L1 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | N/A† | PASS | **PASS** | none | None. B1 must be verified against asset_registry separately. | — |
| `ga_writers/ga_dashas_writer.py` | L1 | **VULNERABLE** | PASS | WARN | N/A | N/A | PASS | PASS | N/A† | PASS | **FIX-REQUIRED** | major | A1: `build_system()` uses `(birth or {}).get(...) or BIRTH_IST/LAT/LON` — local-alias NATIVE_BIRTH pattern evades structural grep guard. Non-native with birth_params=None silently computes native's Vimshottari. Fix: add `resolve_birth_params(chart_id, birth_params)` before `_get_moon_position()`. Secondary (A3): extract `conn.commit()` + `_update_asset_throughput()` from source module to CLI wrapper. | Wave 2 carry-over |
| `ga_writers/ga_medical_writer.py` | L1 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | N/A† | PASS | **PASS** | none | None. | — |
| `ga_writers/ga_prashna_writer.py` | L1 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | WARN | N/A† | PASS | **PASS** | none | A7 WARN: if prashna chart exists but chart_facts absent (DAG order violated), emits 0 rows + WARNING instead of raising. Not a blocker for production DAG; harden in future. | — |
| `ga_writers/ga_sade_sati_writer.py` | L1 | CHART-INDEPENDENT | PASS | **FAIL** | N/A | N/A | PASS | PASS | N/A† | PASS | **FIX-REQUIRED** | minor | A3: `conn.commit()` + `_update_asset_throughput()` in source module (guarded by `owns_conn=False` on orchestrator path — safe in production but structural contract violation). Extract to CLI wrapper. Also: `moon_pada` fallback to `NATIVE_MOON_PADA` for non-native charts — replace with neutral default (1). | Fix Plan (post-W5) |
| `ga_writers/ga_panchanga_writer.py` | L1 | VULNERABLE → **FIXED** | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | A1 fix: line 1247 → `resolve_birth_params()` (committed `dce44b91`). | Wave 2 ✅ DONE |
| `ga_writers/ga_strength_writer.py` | L1 | VULNERABLE → **FIXED** | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | A1 fix: line 1525 → `resolve_birth_params()` (committed `dce44b91`). C1 depth gaps noted (simplified Kala bala; no Mooltrikona distinction) — pre-existing, backlog. | Wave 2 ✅ DONE |
| `ga_writers/ga_structural_writer.py` | L1 | VULNERABLE → **FIXED** | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | A1 fixes: lines 4589 + 5787 + build_ga_structural signature default → `resolve_birth_params()` (committed `dce44b91`). Legacy `build_ga_structural()` `ay_conn.commit()` at line 4738 not on orchestrator path — cleanup backlog. | Wave 2 ✅ DONE |
| `ga_writers/ga_tajaka_writer.py` | L1 | VULNERABLE → PARTIALLY FIXED | PASS | **FAIL** | N/A | N/A | **FAIL** | WARN | PASS | PASS | **FIX-REQUIRED** | major | A1 or-fallback sites (179, 206, 593) + signature defaults (544, 568) fixed (`dce44b91`). **NEW unresolved site:** `compute_varsha()` line ~555 unconditionally uses `{**NATIVE_BIRTH}` regardless of chart — not an or-fallback form; requires adding `birth_params` param + `resolve_birth_params()` call. A3: `compute_varsha()` opens its own `_conn()` instead of accepting injected conn (design gap; companion fix to A1). | Wave 2 carry-over |
| `ga_writers/ga_vargas_writer.py` | L1 | CORRECTLY-GUARDED | **FAIL** | **FAIL** | N/A | N/A | PASS | PASS | PASS | **FAIL** | **FIX-REQUIRED** | major | A2: INVARIANT sentinel rows not in DELETE scope — accretion risk across rebuilds (add explicit DELETE for `ayanamsha_id='INVARIANT'` rows at build start). A3: `_telemetry` import + `_update_asset_throughput()` in source module (guarded `owns_conn=False`; structural violation — extract to CLI wrapper). **C1 CRITICAL:** D9 Navamsha uses `_compute_general_varga()` instead of correct `_compute_divisional_sign()` (trikona-start rule) — analytically significant error for all downstream Bodha varga analysis. | pre-regen blocker |
| `ga_writers/ga_vastu_writer.py` | L1 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | **PASS** | none | None. | — |
| `ga_writers/ga_yoga_writer.py` | L1 | CHART-INDEPENDENT | PASS | PASS | N/A | N/A | PASS | WARN | PASS | WARN | **REVIEW-NEEDED** | minor | A7 WARN: per-row INSERT failures silently swallowed — partial yoga set passes FORENSIC. Add suppressed-error counter with threshold assertion. C1 WARN: `ChartState._SUBJECT_NORM` coupling to `ga_positions_writer.PLANET_TO_SUBJECT` has no enforcement guard — drift would silently drop planets from yoga detection. Add test or assertion. | pre-regen |
| `brahmagyan/ganita/engine.py` (ga_chart_service) | L1 service | CORRECTLY-GUARDED | N/A | N/A | N/A | N/A | N/A | WARN | N/A | PASS | **REVIEW-NEEDED** | minor | A7 WARN: `write_positions()` stub returns `len(positions)` as phantom count (table dropped). Fix: return 0. Not an orchestrator writer — no WriterBase contract applies. Confirm in CAPABILITY_MANIFEST.json that absence of orchestrator writer is intentional. | pre-regen |

> **B1 (†):** B1 count_sql for ga_condition, ga_dashas, ga_medical, ga_prashna, ga_sade_sati could not be confirmed from source files; requires querying asset_registry directly. These 5 assets' count_sql must be verified against the live DB before regeneration.
> **B2–B7:** All Wave 2 assets: deferred (live DB required). B2–B7 are post-regen correctness checks.
> **A4/A5:** N/A — these apply to L2+ DERIVATION_LEDGER entries, not L1 raw writers.
> **C2–C5:** N/A — apply to L2+ native-specific interpretive derivations.

### Wave 2 Summary

- **Assets audited:** 13 ga_* writers
- **PASS:** 6 (ga_condition, ga_medical, ga_prashna, ga_panchanga✅, ga_strength✅, ga_structural✅, ga_vastu)
- **FIX-REQUIRED:** 5
- **REVIEW-NEEDED:** 2
- **A1 contamination — structural guard now GREEN:** `test_no_raw_native_birth_fallback` passes after `dce44b91`
- **A1 contamination — carry-overs (evade grep guard):** 2 sites
  - `ga_dashas_writer.py` — local alias `BIRTH_IST/LAT/LON` pattern (different constant name, same bug class)
  - `ga_tajaka_writer.py` `compute_varsha()` — unconditional `{**NATIVE_BIRTH}` hardcoding (not an or-fallback form)
- **Blockers (pre-regen):** 1
  - `ga_vargas_writer.py` C1: D9 Navamsha wrong formula — incorrect varga assignments corrupt all downstream Bodha varga analysis
- **Majors:** 3
  - `ga_dashas_writer.py` — NATIVE_BIRTH via local alias (evades grep guard; same contamination class)
  - `ga_tajaka_writer.py` — `compute_varsha()` unconditional NATIVE_BIRTH (unresolved after fix set 1)
  - `ga_vargas_writer.py` — INVARIANT accretion + telemetry violation + D9 wrong formula
- **Minors:** 3
  - `ga_sade_sati_writer.py` — commit + asset_throughput in source module (orchestrator-path safe)
  - `ga_yoga_writer.py` — silent error swallowing + subject-norm coupling drift
  - `brahmagyan/ganita/engine.py` — phantom count from stub

### Wave 2 Fix List (Remaining — carry-overs to next session)

Ordered by severity:

1. **[BLOCKER → C1]** `ga_vargas_writer.py` — D9 Navamsha formula  
   Change D9 routing from `_compute_general_varga()` to `_compute_divisional_sign()`
   (trikona-start rule). Audit all 24 `PYJHORA_NAMED_VARGAS` to verify correct routing.
   This must be fixed before any regeneration run — incorrect D9 placements corrupt
   all varga-based analysis in L2 Bodha synthesis.

2. **[MAJOR → A1]** `ga_dashas_writer.py` — local-alias contamination  
   Add `resolve_birth_params(chart_id, birth_params)` before `_get_moon_position()`.
   The `(birth or {}).get(...) or BIRTH_IST/LAT/LON` pattern is functionally identical
   to `bp = birth_params or NATIVE_BIRTH` but uses locally-named constants.
   Also widen `test_no_raw_native_birth_fallback` grep guard to catch `or BIRTH_IST`,
   `or BIRTH_LAT`, `or BIRTH_LON`, `or BIRTH_LON_E` (local NATIVE_BIRTH aliases).

3. **[MAJOR → A1]** `ga_tajaka_writer.py` `compute_varsha()` — unconditional NATIVE_BIRTH  
   Add `birth_params: dict | None = None` parameter; replace unconditional
   `{**NATIVE_BIRTH}` at line ~555 with `resolve_birth_params(chart_id, birth_params) or NATIVE_BIRTH`.
   Companion: add `conn` parameter injection to eliminate internal `_conn()` call (A3 fix).

4. **[MAJOR → A2/A3]** `ga_vargas_writer.py` — INVARIANT accretion + telemetry  
   (a) Add `DELETE FROM chart_divisionals WHERE chart_id=%s AND ayanamsha_id='INVARIANT'`
   at build start to prevent sentinel-row accretion.
   (b) Remove `_telemetry` import and all `_update_asset_throughput` calls from source
   module; move to CLI wrapper.

---

---

## Wave 3 — Pending

*Pending — scheduled for Wave 3 session.*

Planned scope: L2 Bodha writers (`bo_*` assets) — Axis A + C static checks.
L2 is pre-build so no Axis B SQL checks yet; focus on contamination guards
and WriterBase conformance before first L2 build.

---

## Wave 4 — Pending

*Pending — scheduled for Wave 4 session.*

Planned scope: L3 Kāla (`ka_*`) and L4 Phala (`ph_*`) writer static checks
plus any shared compute files not yet covered.

---

## Wave 5 — Pending

*Pending — scheduled for Wave 5 session.*

Planned scope: Cross-wave synthesis. Consolidate all FIX-REQUIRED and
REVIEW-NEEDED items, assign owners, produce the ordered fix backlog, and
declare the campaign COMPLETE once all blockers and majors are resolved.

---

*End of PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0.md*
