---
artifact: phase2_fixes.md
phase: 2
date: 2026-06-18
status: COMPLETE
---

# Phase 2 Fix Summary — L1 Gaṇita Closure Pass

## B1 — FORENSIC 7/7 Investigation

**STATUS: LIKELY RESOLVED in commit e68206bf — needs prod orchestrator build to confirm.**

Root cause traced: `ga_sensitive_writer.py` imports `forensic_gate` from `ga_positions_writer` and calls it inside `_build_all_sensitive_rows_for_ayanamsha`. The CONDUCTOR_HALT_LOG failures (Jun 16-17) occurred before the heavy-writer conversion (commit e68206bf, Jun 18 02:28am).

Before e68206bf: the code was passing the canonical_id directly to both `compute_chart` and `forensic_gate`. The interaction with PyJHora's process-global ayanamsha mode (`drik.set_ayanamsa_mode`) in the 5-ayanamsha loop produced wrong positions for `lahiri_chitrapaksha` (6-sign shifted outputs: Sun→Aries, Moon→Ashwini, Lagna→Scorpio).

After e68206bf (current code): `_build_all_sensitive_rows_for_ayanamsha` receives distinct `ayanamsha_key` (canonical) and `ayanamsha_id` (adapter). Line 2048 passes `ayanamsha_id="lahiri"` to `compute_chart`; line 2052 passes `ayanamsha_id="lahiri"` to `forensic_gate`. The error message would now say `ayanamsha=lahiri`, not `lahiri_chitrapaksha`.

Current pyjhora_adapter/_ayanamsha.py does NOT have "lahiri_chitrapaksha" as a key — silent fallback to LAHIRI. This is correct behavior. No fix needed in the adapter.

**Action needed:** Run an orchestrator build for chart 482012f1 after merging to main. Verify FORENSIC passes for all 5 ayanamshas. Do NOT use standalone runners.

---

## B2 — Migration 307 SQL File

**STATUS: CONFIRMED PRESENT — was in platform/migrations/ not platform/supabase/migrations/**

`platform/migrations/307_l1_enrichment_target_floors.sql` exists on this branch (committed in `360e697c`). Phase 1 audit looked in the wrong directory (`platform/supabase/migrations/`). Non-issue.

---

## B3 — Rebase status

**STATUS: NOT BLOCKING — platform/migrations/ has 242-307; correct migration path.**

This branch has both:
- `platform/supabase/migrations/` (migrations 220-241, older format)
- `platform/migrations/` (migrations 242-307, current format)

Main has additional commits since PR #298 merged (cockpit fixes, G52 elimination, brief purge, ga_structural floor fix 53953→74644). This branch needs rebasing before the closure PR is merged. The rebase will resolve with the correct values from this closure pass.

---

## B4 — Floor prod verification

**STATUS: PENDING — requires prod orchestrator run after rebase+merge.**

Target floors for ga_strength (11,936) and ga_sensitive (8,610) were set in migration 307. Cannot confirm actual prod counts without a live build. Post-merge orchestrator build will confirm.

---

## B5 — Orchestrator Guard B (finally/rollback)

**STATUS: CONFIRMED — runner.py has finally + rollback; asset_runner.py has rollback on exception.**

Confirmed grep results:
- `pipeline/orchestrator/runner.py:167: finally:` → `runner.py:173: conn.rollback()` — top-level runner rolls back on any exception/interrupt. SIGTERM also converted to SystemExit so finally blocks run (runner.py:100).
- `pipeline/orchestrator/asset_runner.py:303: conn.rollback()` — per-asset runner also rolls back on substep failure.

Guard A (migration 241: `idle_in_transaction_session_timeout=120s`) confirmed in prior phase.
Guard B confirmed here. Both connection-resilience guards are in place.

---

## B6 — asset_throughput freshness

**STATUS: PENDING — requires live DB query after prod build.**

Query after prod build:
```sql
SELECT asset_id, rows_written, last_built_at
FROM asset_throughput
WHERE asset_id IN ('ga_strength', 'ga_sensitive')
ORDER BY last_built_at DESC;
```

---

## Non-blocking code fixes applied

### B7 — ga_yoga inner-loop bare except (DONE)
- `platform/python-sidecar/ga_writers/ga_yoga_writer.py:169`
- Changed: `except Exception: pass` → `except Exception as exc: logger.warning("[ga_yoga] Family mapping load failed: %s", exc)`
- NOTE: Phase 1 audit identified this as an inner yoga-evaluation loop, but inspection shows it's actually the `_load_yoga_families` function (family mapping). The yoga evaluation loop itself is different. Still the right fix.

### B8 — ga_structural bare except × 4 (DONE by Phase 2 agent)
- `platform/python-sidecar/ga_writers/ga_structural_writer.py` lines 571, 589, 1199, 3482
- Each: `except Exception: pass` → `except Exception as exc: logger.warning("[ga_structural] ...")`

### B9 — ga_panchanga bare except × 3 (DONE by Phase 2 agent)
- `platform/python-sidecar/ga_writers/ga_panchanga_writer.py` lines 293, 810, 865
- Each: `except Exception: pass` → `except Exception as exc: logger.warning("[ga_panchanga] ...")`

### B10 — ga_dashas vestigial throughput write (FALSE POSITIVE)
- `build_ga_dashas` (line 2362) is standalone-only (no `conn` parameter). The throughput write is correct in standalone mode.
- FIX APPLIED: changed `logger.debug` → `logger.warning` for error visibility in standalone runs.
- No `owns_conn` gate needed.

---

## Seed fixes applied

### ga_structural target_floor
- `platform/scripts/seed/asset_registry_seed.ts`
- Changed: `74644` → `87169` (actual prod count, post all-30-vargas + argala-per-varga expansion)
- Comment updated to reflect closure audit date

### ga_structural count_sql (B12 — cockpit double-count fix)
- Removed `'graha_position', 'graha_sign_attributes'` from `ga_structural.count_sql IN (...)` clause
- These categories are already counted by `ga_positions.count_sql`; removing them prevents cockpit double-counting
- NOTE: This REDUCES the ga_structural count_sql result. The floor of 87,169 was set against the OLD count_sql (which included those categories). After this fix, the actual count from the new count_sql will be LOWER. Floor needs prod re-verification.
- **IMPORTANT:** The 87,169 floor may be wrong after the B12 count_sql fix. Prod build needed to confirm.

---

## Migration 308 created

- `platform/migrations/308_l1_closure_floor_corrections.sql`
- Updates:
  - `ga_structural.target_floor = 87169`
  - `ga_structural.count_sql` — removes 'graha_position', 'graha_sign_attributes' overlap
  - `ga_yoga.target_floor = 5`

---

## B11 — Migration 237 gap (FALSE POSITIVE)
- `platform/migrations/237_drop_signal_type_registry.sql` exists on main/this branch
- Phase 1 audit looked in `platform/supabase/migrations/` (wrong directory)
- Not a gap.

---

## CRITICAL: ga_structural floor likely needs re-confirmation

The B12 fix (removing graha_position/graha_sign_attributes from count_sql) means the count_sql now returns FEWER rows than 87,169. The actual new count must be verified by running the updated count_sql against prod. Recommendation: do NOT seal the closure until this is prod-verified.

The two categories removed contributed approximately:
- graha_position: ~9 grahas × 5 ayanamshas × [rows/graha] rows
- graha_sign_attributes: similar count

Rough estimate: ~27,554 rows total in chart_facts for ga_positions; the subcategories 'graha_position'+'graha_sign_attributes' may account for ~10,000-15,000 of these. The new ga_structural count would be ~87,169 - ~12,000 = ~75,000 (rough). Needs prod confirmation.

---

## Remaining items for Phase 3+

1. **Prod orchestrator build** for chart 482012f1 — confirms FORENSIC 7/7, actual floors, throughput freshness
2. **Guard B verification** — read orchestrator runner source for finally/rollback guard
3. **Branch rebase onto main** — needed before closure PR
4. **ga_structural floor re-verification** — after B12 count_sql fix, the 87,169 floor may need adjustment

*End of Phase 2 smriti — 2026-06-18*
