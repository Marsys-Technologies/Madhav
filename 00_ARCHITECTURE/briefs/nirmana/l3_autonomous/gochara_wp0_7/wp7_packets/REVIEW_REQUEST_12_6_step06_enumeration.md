---
artifact: WP7_REVIEW_REQUEST_12_6
packet_id: "§12.6-step06-enumeration"
version: "1.0"
status: SUBMITTED_FOR_REVIEW
date: 2026-09-27
author: "subagent (l3/gochara-autonomous-wp0-7, E-018 item i — step-6 driver)"
design_file: "GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md §12.6 / §12.9; REMAINDER_FINAL_REPORT_v1_0.md E-018"
commit: "see step-6 enumeration commit series on l3/gochara-autonomous-wp0-7"
---

# REVIEW REQUEST — §12.6: the step-6 episode-enumeration driver (E-018 item i, branch-local closure)

## What landed

Tranche 2 halted at step 6 (E-018) for two causes: the §12.9 staleness gate was RED on
production (unfingerprinted overlay rows), and **no episode-enumeration driver existed**.
This packet closes the second cause branch-locally; the first (production overlay rebuild)
is untouched and remains open.

Four files, all on `l3/gochara-autonomous-wp0-7`:

1. **`platform/python-sidecar/services/gochara_kernel/episodes.py`** (modified, additive
   only): `orb_override_deg` parameter on `build_episodes` / `solve_episodes`; a `refine`
   pass-through added to `solve_boundary_episodes`, which previously **hard-coded
   `refine=True`** (latent gap — callers could not request the coarse pass). No pinned
   table, constant, or default behaviour changed.
2. **`platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py`**
   (new, ~850 lines): the missing step-6 driver.
   - §2.2 target re-resolution reuses the `ka_gochara_resonance` writer's fetch functions
     and constants (single source — no re-derivation).
   - `enumerate_body`: point targets get conjunction/drishti at `--orb-deg` via the
     additive kernel override; returns pinned at 0.5° (owner-gated table value, not
     overridden); 3 boundary relations per target. Interval targets: `residence_spans`
     with `sign_ingress` only (M-5); agent restriction for mechanism_node / M-6.
   - `build_coverage_rows`; §12.9 freshness gate (exit 7) runs **before** any
     enumeration; upstream fingerprint stamps carried into the report; exit codes
     0 / 3 / 4 / 7.
3. **`platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py`**
   (modified, additive): `_coerce_episode_times` — the real-driver JSON path now parses
   ISO `t_in`/`t_exact`/`t_out` strings into tz-aware datetimes before the ledger's
   contact-id path and the B1 naive-instant rejection see them.
4. **`platform/python-sidecar/tests/l3/gochara/test_step06_enumeration.py`** (new,
   9 tests): WP1 golden loop over all 22 fixture cases; synthetic-curve enumeration
   (orb regime, return gating, N-14 Rahu, intervals/agent restriction, `t_exact=None`
   exclusion, `'both'`→NULL, `jd_to_dt`); coverage shape; two disposable-DB end-to-end
   tests (fresh → exit 0 feeding `step06_candidate_build` into real candidate rows;
   stale fingerprint → exit 7, restored in `finally`).

## Design decisions disclosed for review

- **Orb regime**: conjunction/drishti enumerated at 5.0° via the additive
  `orb_override_deg`; the pinned ORB_TABLE is untouched and each row keeps `orb_source`
  pointing at its §7 table row id (the override is disclosed, not hidden). Returns stay
  at the table's 0.5°. Boundary episodes use `orb_ingress`.
- **M-3**: Moon excluded from enumeration. **N-14**: no node drishti.
- **Honest-null discipline**: `t_exact IS NULL` episodes are excluded from candidates
  and **counted**, never fabricated; `'both'` direction stored as SQL NULL.
- **The kernel `refine` escape hatch is exercised only by synthetic-curve tests** — the
  driver itself never disables refinement.

## Defects found and fixed in flight (three)

1. `solve_boundary_episodes` hard-coded `refine=True` — fixed with an additive
   pass-through (wp3a kernel tests 17/17 green after).
2. `_resolve_bhava_arudha` subject mapping: `"BHAVA_ARUDHA_A7"` must map to
   `"ARUDHA_A7"`, not `"A7"` (F-20 discipline — the arudha cusp placeholder is never
   a degree).
3. `jd_to_dt` cumulative truncation produced `19:59:59.999651` instead of `20:00:00` —
   rewritten to round total microseconds.

## Verification

- Full battery from `platform/python-sidecar`:
  `WP6_LEDGER_DSN=postgresql://wp6:***@localhost:55435/wp6 ../../.venv/bin/python -m pytest tests/l3/gochara -q`
  → **344 passed, 0 skipped** (re-run 2026-09-27). This includes
  `test_wp10_cutover.py` 17/17 on the 55434 container (an earlier draft of this line
  said 14/14 — stale; the ADK-0013 harness fix at 537d5022c grew it to 17; corrected on
  PRAMĀṆIN's 2026-09-27 pass), proving the
  `step06_candidate_build.py` edit is non-breaking, and wp3a kernel 17/17.
- **PRAMĀṆIN independent pass, 2026-09-27 (post-dating the headline figure, per the
  native's direction):** re-created both disposable DBs, re-ran the exact command above
  → **344 passed / 0 skipped / 0 failed / 344 collected**, reproduced exactly at
  `3dda35052`; exit-7 negative and producer→consumer round-trip inspected and found
  non-vacuous; containers torn down after. The verifier's pass and the cited figure
  name the same run.
- WP1 golden loop: 22/22 fixture cases.
- Disposable-DB end-to-end: fresh fingerprints → driver exit 0, episodes feed
  `step06_candidate_build` into real candidate rows (consumer row counts equal payload
  lengths); stale fingerprint → exit 7 with restoration in `finally`.
- No production contact at any point.

## Environment deviation (disclosed)

The documented disposable containers were torn down at campaign close
(REMAINDER_FINAL_REPORT §12.12) and port 55433 is now held by an unrelated homebrew
postgres (`/tmp/l0w5/pgdata`, another campaign's fixture — not touched). Recreated:
`gochara-wp6-disposable` on **55435** (DSN override above) and
`gochara-wp10-disposable` on **55434** (default DSN matches). Both torn down after
this work.

## What remains open (not claimed here)

- **E-018 item ii — §12.9 production overlay rebuild: NOT done.** The driver now exists,
  but production overlay rows remain unfingerprinted; the gate stays RED on production
  until the rebuild runs as its own reviewed change.
- **E-012 windows projection writer: still missing** and independently bars the flip.
- **Steps 6–10 production run: still not executed.**

## Notes for the reviewer

1. All kernel changes are additive; no pinned table mutated.
2. DB tests skip NOT_RUN if the DB is unreachable; they never fall back to another DSN.
3. Nothing marked REVIEWED.
