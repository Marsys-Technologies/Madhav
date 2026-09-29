---
artifact: WP7_REVIEW_REQUEST_12_13
packet_id: "§12.13-E-012-windows-projection"
version: "1.0"
status: IMPLEMENTED_AWAITING_REVIEW
date: 2026-09-27
author: "subagent (l3/gochara-autonomous-wp0-7, E-012 — '4.0' windows projection writer)"
design_file: "GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md §12.13 (E-012); REMAINDER_FINAL_REPORT_v1_0.md §7.C"
commit: "b4acdac1d (writer), ac746434a (ledger row_counts), 36321d73d (step-7 message), 0d731f086 (tests) on l3/gochara-autonomous-wp0-7"
---

# REVIEW REQUEST — §12.13 / E-012: the '4.0' windows projection writer (branch-local closure, ADK-0012)

## What landed

E-012 is closed **branch-locally**: the '4.0' windows projection writer now exists, is
tested RED→GREEN against the real step-7 gate, and the WP10 rehearsal no longer uses a
synthetic stand-in. Five files, all on `l3/gochara-autonomous-wp0-7`:

1. **`platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py`**
   (new, ~1020 lines): the missing writer. Projects the '4.0' candidate contact ledger
   (step 6 output) into the **served** table `kala_gochara_windows` under generation
   `'4.0'`.
   - Shape: M-1 `linear_no_box_decay` (tent over `[t_in, t_out]`, vertex 1.0 at
     `t_exact`, **no ±5-day box**, exactly zero outside the span — no F-08 floor).
   - The per-class λ evaluator **is the pinned `legacy_semantics` algebra
     term-for-term** (`compute_activity_v3` / `compute_signed_channels_v3` /
     `assemble_lambda_v3`) over a disclosed relation→primitive map
     (`RELATION_TO_PRIMITIVE`, every value a real `ACTIVITY_PRIMITIVES` member).
   - H-5: **every admitted peak is stored** (the pre-H-5 cap of 3/era is removed; the
     pinned 90-day separation is retained).
   - Breakpoint augmentation: contact `t_in`/`t_exact`/`t_out` are injected into the
     daily evaluation grid, so sub-day components are visible to `find_components`
     (a uniform grid would miss them entirely).
   - Three tiers with parent linkage: `resolution` ∈ {era, month, day},
     `parent_window_id` wired day→month→era;
     `peak_basis='gochara_lambda_v3:m1_linear_no_box:step06b'`, `source='live'`.
   - Refusals: exit 3 (no candidate manifest), 4 (production DSN),
     6 (generation already published), 7 (§12.9 stale overlay fingerprint).
     Idempotent delete-then-insert scoped to the candidate; `'v1'`/`'3.0'` rows
     untouched. Delta report vs the `'3.0'` baseline with **honest `'—'` nulls** for
     absent baseline factors (no fabricated 0.0).
2. **`platform/python-sidecar/services/gochara_kernel/ledger.py`** (modified):
   `publish()` now records the **honest** `row_counts.windows` — the real count of
   `kala_gochara_windows` rows for the (chart, generation), `to_regclass`-guarded,
   0 when the table is absent — instead of a fixed placeholder.
3. **`platform/python-sidecar/scripts/kala_gochara_cutover/step07_flip_gates.py`**
   (modified): the `windows_present` gate-5 failure detail now names the writer that
   exists (`step06b_windows_projection.py`); the "E-012" token the RED assertion
   matches is kept. The gate itself is **not** weakened.
4. **`platform/python-sidecar/tests/l3/gochara/test_step06b_windows_projection.py`**
   (new, 13 tests) — see Verification.
5. **`platform/python-sidecar/tests/l3/gochara/test_wp10_cutover.py`** (modified): the
   synthetic `_seed_synthetic_4_0_window` stand-in is **removed**; both call sites
   (step-7 gate test, step-8 flip test) now run the real writer via
   `_write_4_0_windows(chart)` (`--rehearse-synthetic`). Fixture DDL upgraded: windows
   gains `parent_window_id BIGINT, resolution TEXT`; `gochara_resonance_map` is now
   the full migration-459 shape (applies idempotently on top of 1080); seeds carry the
   map rows matching step06's rehearsed synthetic contacts.

## Design decisions disclosed for review

- **era_slice_key is NULL on every '4.0' row, deliberately.** Migration
  `1091_wp10_ka_gochara_registry_repin.sql` conjunct (g) reads a non-null
  `era_slice_key` inside generation `'4.0'` as **foreign-writer contamination**. An
  earlier draft stamped `g3_2020_2030` and tripped step 8's `_integrity` check; the
  writer now never sets the column. Consequence: decade-scoped consumers that filter
  `era_slice_key LIKE 'g3_%'` will not see '4.0' rows — that is the pinned
  contract's own boundary, not a gap in the writer.
- **Date bucketing dated morning-UTC peaks one day early (FIXED, E-020/ADK-0026).**
  As originally disclosed here, `int(jd - 2440588.0)` floored at the noon-UTC
  boundary; the defect scope was understated as "midnight peaks" — the real scope
  was instants 00:00–11:59 UTC (05:30–17:29 IST) dated one day early
  (wording corrected under ADK-0026 §6). The writer's `date_of_jd` /
  `iso_date_of_jd` / `_jd_of_date` are now true inverses of `jd_of`
  (midnight-UTC anchor 2440587.5, the overlays.py:34-52 pair's shape).
- **Permission-system class context is deferred to the production set (ADK-0012).**
  The writer takes `--class-context-json`; in the branch-local tests the context names
  only `vimshottari`, and a class with contacts but no context entry is an **honest
  skip** (counted in `skipped_classes`, never silently projected with fabricated
  permissions). Wiring the full L1 timing permission systems into the context is part
  of the escalated production application set, not this packet.
- **Candidate parameter set is the E-018 candidate-1 flags** (`CANDIDATE_FLAGS`);
  candidate 2 (1.0° orb) remains unratified and the writer refuses it.

## Verification (RED→GREEN evidence)

All runs from `platform/python-sidecar`, `../../.venv/bin/python -m pytest`,
`WP6_LEDGER_DSN=postgresql://wp6:***@localhost:55435/wp6`:

- `tests/l3/gochara/test_step06b_windows_projection.py` → **13 passed**.
  Unit: M-1 decay shape; evaluator ≡ pinned algebra term-for-term;
  `find_components` single/disjoint/sub-day-bump; H-5 five-peak retention;
  relation-vocabulary; delta-report honest nulls (incl. nearest-'3.0'-peak naming).
  Integration (disposable WP6): **step07 `windows_present` RED → exit 7 → run writer
  → step07 GREEN exit 0**; era/month/day parent linkage with zero orphans; day peaks
  land on the contact `t_exact`; `'v1'`/`'3.0'` rows untouched; candidate manifest
  `row_counts.windows` equals the real count; idempotent rerun; exit 4 / 7 / 6 / 3
  negatives; unmapped contact (1) and no-context class (career) counted, never
  silently dropped.
- `tests/l3/gochara/test_wp10_cutover.py` → **17 passed** (the real-writer path drives
  the same RED→GREEN and step-8 flip tests the stand-in used to fake).
- Full directory `tests/l3/gochara/` → **357 passed, 0 failed** (344 pre-work baseline
  + 13 new; no cross-module fixture interference).
- `tests/l3/gochara/test_wp6_ledger.py` → **12 passed** (row_counts change).
- No production contact at any point; both databases are the disposable containers.

## What remains open (not claimed here)

- **E-018 item ii — §12.9 production overlay rebuild: still NOT done.** Production
  overlay rows remain unfingerprinted; the step-6 driver will refuse (exit 7) on
  production until the rebuild runs as its own reviewed change.
- **The steps 6–10 production run (enumeration → candidate build → 6b projection →
  gates → authority flip) is still NOT executed on production.** This packet makes the
  flip *reachable*, not performed.
- **Permission-system class-context wiring** for the full L1 timing set (ADK-0012).

## Notes for the reviewer

1. Nothing in this packet is marked REVIEWED; status is IMPLEMENTED_AWAITING_REVIEW.
2. The step-7 gate and step-8 refusal were **not** weakened — §12.13's instruction
   ("do not weaken those gates, and do not seed a window to get past them") is
   honoured; the synthetic stand-in that §12.13 labelled is gone.
3. DB tests skip NOT_RUN if the disposable DB is unreachable; they never fall back to
   another DSN.
