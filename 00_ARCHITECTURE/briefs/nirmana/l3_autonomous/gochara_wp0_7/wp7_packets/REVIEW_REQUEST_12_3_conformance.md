---
artifact: WP7_REVIEW_REQUEST_12_3
packet_id: "§12.3-conformance-4.13a-i"
version: "1.0"
status: REVIEWED_BY_ADHIKARIN
disposition: "REVIEWED_BY_ADHIKARIN 2026-09-27 per ADK-0013 — ACCEPT; scope matches §12.3/§4.13a–i item for item, values are the D-S1/D-S2-ruled values. NOT marked REVIEWED: the native's K3/O-2 independent review is a separate mechanism and is unaffected."
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, §12.3 run)"
design_file: "GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md §12.3 / §4.13; GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md §1 (D-S1, D-S2, D-S4)"
commit: "8b5d7f4ed, c2eb8a780, 660e12129, a54ee98c1, 3d606523b, 82e320cb8, 5ca1e17e7, 854907160, 8c8dd2a1f, 42bab892d"
---

# REVIEW REQUEST — §12.3: D-S1/D-S2 conformance fixes (§4.13a–i) + ruling §7.6

## What landed

- **4.13a** coverage object on every `find_episodes` branch (non-Moon zero-contact and
  no-branch paths return a coverage row; `bodies_on_demand`) — `8b5d7f4ed`.
- **4.13b** `inclusivity` column (`closed_closed` — both endpoints are in-orb threshold
  crossings) — in `660e12129`.
- **4.13c** `completeness_state` CHECK-constrained to the six F06 states; live `qualified`
  migrates to `applied`; `removed_by_ruling_N14` λ-key becomes `inapplicable` + sibling
  `removed_by_ruling: 'N-14'` — `c2eb8a780`.
- **4.13d** `time_basis` CHECK + `tier_basis` column; WP1 §3.1 pins — `660e12129`.
- **4.13e** `claim_grain` → `precision_regime` rename (D-S4) in migration 1081, ledger,
  kernel dataclasses, tests — before 1081 was ever applied outside a disposable DB.
- **4.13f** `primitives.py` comment corrected (BPHS Ch.26 citation refuted by F-29;
  retained only for the legacy `nodal_drishti` arm).
- **4.13g** per-call node-mode assertion in this family's readers (RAH_MEAN/KET_MEAN,
  raises rather than degrades).
- **4.13h** `window_ref` documentation + PK-resolution test
  (`test_wp6_ledger.py::test_window_ref_resolves_by_primary_key`).
- **4.13i** `comparable_with` stays at four values; `unstable_key` declined (D-S6),
  recorded in §6.
- **Ruling §7.6**: N-15 citation correction (`854907160`); Mercury id 21 unstamped
  (`8c8dd2a1f`); cutover step04 APPLY_SET +1087, step06 `applied` (`42bab892d`).
- Migration **1087** (E-011; number from a fresh all-head scan + MIG-1 guard PASS);
  disposable WP6 DB only, production application WP10-gated.

## Tests

- Full battery from `platform/python-sidecar`: **327 passed, 0 failed**
  (`/opt/homebrew/bin/python3 -m pytest tests/l3/gochara -q`) at completion of §12.3.
- Stamp/CHECK negatives: `test_wp6_ledger.py::test_stamp_check_constraints_reject_out_of_vocabulary`
  rejects out-of-vocabulary inclusivity / time_basis / tier_basis / completeness_state at write.
- `cd platform && npm run guard:migration-numbers` → PASS (MIG-1).

## Notes for the reviewer

1. 1087 is additive-only and applied to the disposable WP6 Postgres (55433) by the test
   harness after 1081 — never to a shared database (E-011).
2. The six F06 states and the `closed_closed` value are the D-S1/D-S2 ruled values; the
   CHECKs make a deviation a write-time error, not a lint.
3. Nothing marked REVIEWED.
