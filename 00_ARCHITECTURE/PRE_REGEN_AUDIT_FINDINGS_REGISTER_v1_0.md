---
artifact: PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0.md
canonical_id: PRE_REGEN_AUDIT_FINDINGS_REGISTER
version: 1.2
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
purpose: >
  Per-asset findings register for the Pre-Regeneration Full Audit Campaign (L0–L4).
  One row per audited file × 3 axes × PASS/FAIL. Becomes the fix plan when all
  waves complete.
waves_complete: W0
waves_pending: W1, W2, W3, W4, W5
changelog:
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

## Wave 1 — Pending

*Pending — scheduled for Wave 1 session.*

Planned scope: L1 Gaṇita writer deep-dive (remaining `ga_*` writers not covered
in Wave 0: `ga_ashtakavarga`, `ga_bhava`, `ga_dasha`, `ga_divisionals`,
`ga_yoga`, plus `ga_chart_service`). Axis A + C static; Axis B SQL checks
on native chart (482012f1) once DB is confirmed accessible.

---

## Wave 2 — Pending

*Pending — scheduled for Wave 2 session.*

Planned scope: Axis B (SQL data-correctness) sweep of all L1 tables for the
native chart. Use B1–B7 templates from `PRE_REGEN_AUDIT_HARNESS_v1_0.md §2`.

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
