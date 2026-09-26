---
artifact: WP7_REVIEW_REQUEST_7C_T2
packet_id: "§7.C-tranche-2"
version: "1.0"
status: REVIEWED_BY_ADHIKARIN
disposition: "REVIEWED_BY_ADHIKARIN 2026-09-27 per ADK-0013 — ACCEPT as an accurate halt record; its three decision items are disposed elsewhere in the register (owners: this lane branch-local per ADK-0011/0012; overlay rebuild: escalated to the native as a production write per ADK-0011(ii); M-1 candidate-1 parameters CONFIRMED as recorded, activity_shape=linear_no_box, orb_max_deg=5.0). NOT marked REVIEWED: K3/O-2 is separate and unaffected."
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, §7.C tranche-2 attempt)"
design_file: "GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9 steps 6–10; NATIVE RULING 2026-09-24T11:39:01Z (ESCALATIONS.md)"
commit: 476c808ce
---

# REVIEW REQUEST — §7.C tranche 2 (steps 6–10): HALTED at step 6 (E-018)

## What happened

The native authorized tranche 2 notwithstanding the merge-state preconditions
(ruling recorded verbatim in ESCALATIONS.md and `evidence/step06_evidence.md`).
Tranche 1 was completed first (step 5 resumed GREEN). Step 6 was then entered
and **halted on its precondition gate**, per the standing order:

1. **§12.9 staleness gate — exists, tests green, RED on production.** With
   fresh disposable DBs (55433/55434, torn down after) the fingerprint/honesty
   gate tests pass 40/40 (13 previously NOT_RUN now run). Against production,
   `check_overlay_freshness` reports **stale** for both authority charts: every
   `kala_vedha_gochara` / `kala_moorti_nirnaya` row predates 1082 and carries
   NULL `upstream_fingerprint` (135/135 + 72/72 on `1c826d5a…`; 132/132 +
   71/71 on `482012f1…`; zero mismatched). Step 6 would exit 7 REFUSED.
2. **The episode enumeration driver does not exist.** step06 consumes
   `--episodes-json`/`--coverage-json` "from the kernel pipeline"; nothing on
   the branch produces them (only tests and step06 call
   `ledger.write_contacts`). Building it is the '4.0' writer's core — new
   engineering, not a tranche artifact; §10 bars live-chart writes before the
   proof-matrix gates run for it. Not improvised.
3. **E-012 carried:** the '4.0' windows projection writer does not exist; step
   7's `windows_present` gate is RED by design; step 8 refuses to flip.

Steps 6–10 NOT RUN. Production untouched by tranche 2 (no '4.0' rows;
generations v1=38287 / 3.0=1830; authorities both '3.0').

## What the reviewer/native is asked to decide (E-018)

- Owners for (a) the step-6 episode enumeration driver and (b) the '4.0'
  windows projection writer (E-012's owner question carries).
- Whether the overlay fingerprint rebuild for the two authority charts runs now
  as its own reviewed change (branch writers are ready, gate-tested, and carry
  M-8 + the §12.10b honesty fix) so §12.9 is green at the next step-6 attempt.
- Confirm the M-1 candidate-1 parameters for that attempt
  (`activity_shape=linear_no_box, orb_max_deg=5.0`; 1.0° = candidate 2, not
  ratified; 0.5° rejected).

Nothing marked REVIEWED. Evidence: `evidence/step06_evidence.md`.
