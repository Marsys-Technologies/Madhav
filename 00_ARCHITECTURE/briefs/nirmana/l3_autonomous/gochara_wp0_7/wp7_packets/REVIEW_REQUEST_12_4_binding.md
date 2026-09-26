---
artifact: WP7_REVIEW_REQUEST_12_4
packet_id: "§12.4-binding-adoption"
version: "1.0"
status: REVIEWED_BY_ADHIKARIN
disposition: "REVIEWED_BY_ADHIKARIN 2026-09-27 per ADK-0013 — ACCEPT WITH CONDITIONS: (a) the B1-resolver vacuous-adoption note and the B6 adopted-while-unruled note stay in BINDING_PROOF_MATRIX_v1_0.md verbatim as standing disclosures (B8-6 remains an unruled DECISION; any future native ruling reopens that row); (b) the adoption-by-reference pin stays at binding v2.3 @ 7374d8f71, not the §12.4-quoted v2.2. NOT marked REVIEWED: K3/O-2 is separate and unaffected."
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, §12.4 binding run)"
design_file: "KALA_SYNERGY_BINDING_v1_0.md v2.3 @ 7374d8f71 (origin/l3/kala-elevation-readiness); BINDING_PROOF_MATRIX_v1_0.md v1.0"
commit: dc2d05b46
---

# REVIEW REQUEST — §12.4: KALA_SYNERGY_BINDING §B1–B7 adoption

## What landed

- **Adoption by reference** in `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §1 (+ new §6.11):
  binding read LIVE — **version 2.3 at `7374d8f71`**, not the 2.2 @ 8211c2dc6 quoted in §12.4.
- **Proof matrix** `wp7_packets/BINDING_PROOF_MATRIX_v1_0.md` v1.0: one row per Gochara
  OFFERS/DEMANDS row, Layer §9 tests 5/6/7/9, each with a named negative fixture.
- **New code** `services/gochara_kernel/ledger.py::_normalize_episode`: naive `t_in`/`t_exact`/`t_out`
  rejected at write with ValueError (B1 failure mode made real).
- **New detectors** `tests/l3/gochara/test_b_binding_conformance.py` (7 tests, all green):
  - B1/test 7: naive-instant rejection (negative) ×3; +05:30 tz-aware write round-trips as the
    same UTC instant on the disposable WP6 DB.
  - B6 (adopted as written; DECISION B8-6 unruled — noted): static sole-producer detector over the
    real tree + fabricated-second-writer negative fixture in a tmp tree.
  - B1 resolver row: no-private-temporal-conversion detector (`date.today()` / naive `now()` /
    `utcnow()` scan) + tmp-tree negative.

## Tests run

- `pytest tests/l3/gochara/test_b_binding_conformance.py -q` → **7 passed**.
- Full battery `pytest tests/l3/gochara -q` → **334 passed, 0 failed** (327 baseline + 7).

## Rows proven by existing tests (cited in the matrix, not duplicated)

- Test 5 (duplicate/shared-root): `test_wp3a_kernel.py::test_contact_id_and_independence_group`;
  WP9 `test_duplicate_independence_group_collapses_to_one_row` / `test_distinct_physical_events_remain_distinct`.
- Test 6 (missingness): 4.13a zero-contact coverage tests in `test_m3_moon_channel.py`.
- Test 9 (sentinel): `test_wp7_sentinel.py::test_storage_retrieval_budget_delivery_replay`.
- Stamps/vocabulary: `test_wp6_ledger.py::test_stamp_columns_populated_on_written_rows`,
  `test_stamp_check_constraints_reject_out_of_vocabulary`, `test_window_ref_resolves_by_primary_key`;
  WP9 stamp suite with its own negatives.

## Notes for the reviewer

1. **Stale claims in the live binding** (recorded in the matrix, not re-fixed): `time_basis`
   population, `completeness_state` "qualified", vedha stamps, and the `engine.py:1755` coverage
   gap are all already closed by §12.3 / 4.13 commits.
2. **B1 resolver row is recorded as vacuous**: Gochara has no civil date↔instant conversion
   (JD/UTC end-to-end; `revjul`/`fromtimestamp(tz=utc)` only), and `ka_temporal/date_resolver.py`
   in its current form resolves dasha activation *dates*, not instants — there is nothing to adopt
   *for*. Flagged in the matrix for the native rather than escalated: the binding's failure mode
   (private conversion) is guarded by a detector, and nothing contradicts existing behavior.
3. **B6 posture**: adopted as written per §12.4 even though binding §B8-6 marks it an unruled
   DECISION — the matrix states both facts.
4. Nothing here is marked REVIEWED; verdict tier is COMPUTATIONAL_CORRECTNESS only.
