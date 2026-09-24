# REVIEW REQUEST — §8.4 (G-9: bg_transit_rules vedha repair, migration 1085)

**Brief:** `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §8.4
**Branch:** `l3/gochara-autonomous-wp0-7`
**Commit:** `8a6b94a86`
**Sheet item:** G-9 (Kṣetra L0 data repair, file only — applied to the disposable DB only)

## What changed

- `platform/migrations/1085_nirmana_l0_bg_transit_rules_vedha_repair.sql`:
  - Adds `uncited_extension BOOLEAN NOT NULL DEFAULT FALSE` to `bg_transit_rules`.
  - Re-cites the 35 Sun/Moon/Mars/Saturn rows to `phaladeepika:PG322:C1` and Mercury/Jupiter/Venus rows to `phaladeepika:PG323:C1` (spec said "32"; the verified per-spec row enumeration totals 35 — see unsure-of below).
  - UPDATEs `vedha_house` on Venus ids 35→1, 44→5, 45→11 (never deletes).
  - INSERTs the Mercury 8th-house pair (vedha from the 1st, `PG323:C1`, phala "Gain of wealth and birth of children" from the cited Phaladīpikā ch.26 śl.17 text).
  - Strikes `"BPHS Ch.29 (Gochara Phala — Transit Results)"` from every `classical_citation` (G-8), guarded by a DO block that raises if any matching row remains (the strike text itself avoids the literal so the guard cannot self-trip).
  - Marks the six Rāhu/Ketu rows (187–189, 196–198) `uncited_extension = TRUE` with an N-14 disposition note; the UPDATE carries `AND uncited_extension = FALSE` for idempotency.
  - Down-block included and exercised.
- `platform/python-sidecar/tests/l3/gochara/test_g9_vedha_row_repair.py`: 4/4 green on the disposable DB (before-state fixture, after-state asserts, idempotency, down-reversal).

## Verification of the attributed spec

Each spec claim was checked against OCR-independent evidence before writing:
`brahmagyan/l0_transit.py::BG_TRANSIT_RULES` (68 seed rows carry the wrong pairs by value) and the cited Phaladīpikā ch.26 text (śl.6 Mercury (8,1); śl.8 Venus (3,1)(8,5)(9,11); śl.17 Mercury-8th phala used verbatim).

## Unsure of

- The spec's headline says "re-cite 32 rows" but its own §-by-§ enumeration produces 35 (Sun/Moon/Mars/Saturn on PG322 + Mercury/Jupiter/Venus on PG323, excluding the six nodal rows). The migration implements the enumerated set, not the headline number.
- Numbering: 1085 reserved as E-009 after an all-head re-scan (max applied prefix 1084).
