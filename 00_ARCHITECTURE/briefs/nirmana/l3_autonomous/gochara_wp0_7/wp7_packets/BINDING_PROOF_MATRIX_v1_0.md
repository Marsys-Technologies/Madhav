---
artifact: GOCHARA_WP7_BINDING_PROOF_MATRIX
canonical_id: GOCHARA_WP7_BINDING_PROOF_MATRIX
version: "1.0"
status: IMPLEMENTED_AWAITING_REVIEW
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, §12.4)"
binding: "KALA_SYNERGY_BINDING_v1_0.md v2.3 @ 7374d8f71 (origin/l3/kala-elevation-readiness)"
verdict_tier: "COMPUTATIONAL_CORRECTNESS only (binding §B7) — conformance here proves no explanatory value and no empirical performance"
---

# Binding proof matrix — Gochara rows of KALA_SYNERGY_BINDING §B1–B7

Adoption is by reference in `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §1. The
binding was read LIVE at adoption time: **version 2.3, commit `7374d8f71`** on
`origin/l3/kala-elevation-readiness`. Per the brief: never trust a version quoted
elsewhere; this matrix records what the live file actually says, including where
the live binding's own claims about Gochara are **stale** (already closed by
§12.3 / 4.13 work).

Tests are in `platform/python-sidecar/tests/l3/gochara/`. Full battery after this
work: **334 passed, 0 failed** (`/opt/homebrew/bin/python3 -m pytest
tests/l3/gochara -q`). Layer-contract §9 test numbers refer to
`MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT_v1_0.md` §9.

## Stale claims in the live binding (recorded, not re-fixed)

| binding row | binding's claim | reality at adoption |
|---|---|---|
| B1 `time_basis` | "column exists; no production caller populates it — D-S4" | closed by 4.13d: the ledger populates `time_basis='event_time_utc'` on every written row (`test_stamp_columns_populated_on_written_rows`) |
| B1 `precision_regime` | rename "before the migration is ever applied" | done as D-S5/4.13e — `claim_grain` → `precision_regime` in 1081, the ledger, the kernel dataclasses and tests |
| B2 `completeness_state` | "live values are `qualified`" | closed by 4.13c: six-state F06 CHECK (1087), `qualified` → `applied` everywhere |
| B2 vedha stamps | "none exist on `kala_vedha_gochara` today" | closed earlier this arc: `test_wp9_stamp_columns.py::test_every_vedha_row_fully_stamped` proves the three stamps on the producer row |
| B5 `coverage: None` | `engine.py:1755` non-Moon gap | closed by 4.13a: coverage on every find_episodes branch (`test_find_episodes_non_moon_zero_contacts_returns_coverage_row`, `test_find_episodes_no_branch_returns_coverage_none`) |

## Matrix — Gochara OFFERS / DEMANDS rows

| binding row | Gochara posture | detector (Layer test) | negative fixture that fires it |
|---|---|---|---|
| B1 `t_start`/`t_end` (as `t_in`/`t_out` alias), `t_exact` — timestamptz UTC, never naive | OFFERS | `test_b_binding_conformance.py::test_tz_aware_non_utc_round_trips_as_same_utc_instant` (test 7, timezone boundary) | `test_naive_instant_rejected_at_write`, `test_naive_t_in_t_out_rejected_at_write` — naive `datetime` raises `ValueError` at write (new guard in `ledger._normalize_episode`) |
| B1 `inclusivity` — declared on every row | OFFERS (4.13b) | `test_wp6_ledger.py::test_stamp_columns_populated_on_written_rows` | `test_wp6_ledger.py::test_stamp_check_constraints_reject_out_of_vocabulary` — out-of-vocabulary value rejected by CHECK |
| B1 `time_basis` | OFFERS (4.13d) | same pair as above | same negative (out-of-vocabulary `time_basis` rejected) |
| B1 `precision_regime` (ruled name) | OFFERS (D-S5 rename done) | stamp tests above; `test_wp9_stamp_columns.py::test_bad_precision_regime_rejected_on_moorti` | `test_bad_precision_regime_rejected_on_moorti` — wrong value on the producer row rejected |
| B1 tz source — birth instant's offset, never `datetime.now()`/`date.today()` | conformant | `test_b1_no_private_temporal_conversion_real_tree` — static scan of `gochara_kernel`, `ka_gochara`, `gochara_v3` for `date.today()` / naive `now()` / `utcnow()` | `test_b1_private_conversion_detector_fires` — fabricated `date.today()` caller in a tmp tree fires the detector |
| B1 resolver — date↔instant through `services/ka_temporal/date_resolver`, no private conversion | **vacuous for Gochara** — the kernel works in JD/UTC end-to-end (`swe.revjul`, `fromtimestamp(tz=utc)` only); there is no civil date↔instant conversion to route anywhere. Note for the native: `date_resolver.py` in its current form resolves dasha activation dates (predicate→date), not instants — there is nothing in that module to adopt *for* this purpose. The detector above guards the "no private conversion" failure mode | same as tz-source row | same negative |
| B2 `epistemic_class`, `operator_role` | OFFERS | `test_stamp_columns_populated_on_written_rows` | `test_stamp_check_constraints_reject_out_of_vocabulary` |
| B2 `completeness_state` — exactly six F06 states | OFFERS (4.13c) | same; WP5 honesty rows: `test_wp5_honesty.py::test_find_threshold_crossings_emits_unqualified_interval` | `test_stamp_check_constraints_reject_out_of_vocabulary` rejects a non-F06 value at write |
| B2 `comparable_with` — four values, a relation | OFFERS (N-7 pinned; stays at 4 per D-S6) | stamp tests | out-of-vocabulary negative above |
| B2 `tier_basis` | OFFERS (4.13d) | `test_stamp_columns_populated_on_written_rows` | `test_stamp_check_constraints_reject_out_of_vocabulary` |
| B2 vedha producer-row stamps | OFFERS (WP9) | `test_wp9_stamp_columns.py::test_every_vedha_row_fully_stamped`, `test_house_vedha_stamp_values`, `test_sarvatobhadra_stamp_values`, `test_latta_stamp_values`, `test_moorti_stamp_values` | `test_wp9_stamp_columns.py::test_bad_source_qualification_rejected`, `test_conjuncts_detect_corruption` |
| B3 `contact_id` — content-addressed sha256 | OFFERS | `test_wp3a_kernel.py::test_contact_id_and_independence_group` | same test: two rows differing only in `target_deg` hash to different ids (distinct physical events never collapse) |
| B3 `generation` on every row | OFFERS (`'4.0'` candidate, gated) | every WP6 write test writes `generation='4.0'` | `test_wp6_ledger.py` published-generation refusal tests — writes to a published generation raise `PublishedGenerationRefusal` |
| B3 `window_ref` | n/a as producer (Gochara R2: a producer never targets a consumer's window); resolution form documented in WP1 §5.5 | `test_wp6_ledger.py::test_window_ref_resolves_by_primary_key` | that test's different-generation / missing-key paths fail loudly |
| B3 L2 identity (natural key from Yojaka, DP06) | **DEMAND on L2 via L3-U01** — binds nothing until L2 accepts; recorded here, no Gochara-side detector applicable | — | — |
| B4 `independence_group` column | OFFERS | `test_contact_id_and_independence_group` (test 5, duplicate/shared-root): same physical contact collapses to one group, distinct targets do not | `test_wp9_stamp_columns.py::test_duplicate_independence_group_collapses_to_one_row` vs `test_distinct_physical_events_remain_distinct` — the detector distinguishes collapse from distinctness |
| B5 `coverage` on every result, incl. every empty result | OFFERS the table; non-Moon fix done (4.13a) | `test_m3_moon_channel.py::test_find_episodes_moon_zero_contacts_still_writes_coverage`, `test_find_episodes_non_moon_zero_contacts_returns_coverage_row`, `test_find_episodes_no_branch_returns_coverage_none` (test 6, missingness) | zero-contact fixtures above are the negative: an empty result with NO coverage row would fail these tests |
| B6 contact episodes — Gochara kernel sole producer | **DECISION B8-6 — no ruling covers it; adopted as written by brief §12.4** | `test_b_binding_conformance.py::test_b6_sole_producer_real_tree` — static scan: any `INSERT INTO kala_gochara_contacts` outside `services/gochara_kernel/ledger.py` fails | `test_b6_detector_fires_on_second_writer` — fabricated second writer in a tmp tree fires the detector |
| B7 verdict tier | COMPUTATIONAL_CORRECTNESS only; nothing here proves a better reading or an outcome | this matrix | — |

## Layer §9 test 9 (served-evidence sentinel)

`test_wp7_sentinel.py::test_storage_retrieval_budget_delivery_replay` walks the
sentinel through projection, retrieval, budgets, delivery and replay, with the
`completeness_state='unqualified'` failure-path assertions as its negative
fixture — an unqualified row that reached a served surface would fail it.

## Escalations

None. B1's resolver row is recorded as vacuous (above) rather than escalated:
there is no private date↔instant conversion in Gochara to replace, and the
binding's failure mode for that row is guarded by a detector.
