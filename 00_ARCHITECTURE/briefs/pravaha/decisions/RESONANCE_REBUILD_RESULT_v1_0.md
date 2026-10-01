---
artifact: RESONANCE_REBUILD_RESULT
version: "1.0"
status: "CLOSED — production resonance map rebuilt 2026-10-01 (steward run 82f8802c, 23:12Z); finding #9 re-measured read-only and CLOSED"
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — read-only re-measurement (steward M20261001T231248-60b0)
closes: "RESONANCE_REBUILD_DECISION_PACKET v1.2 (and the v1.1 pre-run packet, file ..._v1_0.md)"
authority: "Records measurements only; authorises nothing. All queries read-only (BEGIN READ ONLY … ROLLBACK); no write credential used."
---

# Resonance-map rebuild — result (finding #9 / T0-12)

Chart `482012f1-710e-4a25-994a-93821f5871aa`, table `gochara_resonance_map`. Before-values are the
measurements recorded in the decision packet (taken read-only on 2026-10-01 before the run); after-values
were re-measured by Stream B read-only after the steward reported the rebuild landed. The queries are the
runbook's own §2/§3 predicates (`resonance_rebuild_R1_R6_runbook.md`), unchanged.

## Before / after

| Finding-#9 measure | Before (packet) | After (re-measured) | Result |
|---|---|---|---|
| Sensitive-degree rows keyed to a **negative / out-of-vocabulary** check (R-1) | **154 of 176** | **0 of 21** | CLOSED |
| Sensitive-degree rows kept, and how many key a **positive** fact | 176 kept, 22 positive | **21 kept = 21 positive** (kept set is exactly the positive-fact set) | CLOSED |
| Rows with a NULL / blank / **dangling** `target_ref` (R-2/R-3) | **244** | **0** | CLOSED |
| Stored `target_resolution_state` | **765 of 765 `'resolved'`** | 623 rows: **615 `resolved` + 8 `unavailable`**; 0 NULL/invalid | CLOSED |
| Partition size | 765 | **623** | as expected (negative-keyed + dangling rows removed) |

(The packet's before-figure for positive sensitive rows is "only 22 key to positive results"; the rebuilt map
keeps 21 — the writer's own count of positive facts for the chart. The runbook's R-1 positive control is that
the kept set EQUALS the positive-fact set, which it does: 21 = 21.)

## Rows by type (after; 623 total)

yoga_constituent 162 · mechanism_node 92 · arudha 67 · bhava 67 · bhava_arudha 67 · lord 51 · karaka 43 ·
dasha_lord_portfolio 43 · sensitive_degree 21 · yamakantaka_difference 8 · gulika_mandi_distance 2.

(The original 765 had no `bhava_arudha`, `gulika_mandi_distance` or `yamakantaka_difference` types — the
corrected writer v2.2 adds them — and fewer rows of the others where unfaithful rows were dropped.)

## Stored state by type (after)

Every type is wholly `resolved` **except** `yamakantaka_difference` — all 8 rows `unavailable`
(sun/lagna-lord/fifth-star-lord minus yamakantaka, yamakantaka minus mandi; 2 rows each).
The map no longer claims authority it does not have: the stored state is derived from operand presence,
not asserted.

## Packet status

`RESONANCE_REBUILD_DECISION_PACKET` v1.2 (the record of the 2026-10-01 attempt, restore and fix) — **CLOSED
by this document**: the rebuild it was waiting on has landed and verified. The v1.1 pre-run packet
(file `…_v1_0.md`) is likewise closed. Rollback material (the certified file backup, 765 rows, joined-md5
`3d270ef0…`) is unchanged and remains the restore point of record until the steward retires it; the live
partition's current full-row digest is `(623, 718de7e471e4a02ffdf0f6141b35299f)`
(md5 of `string_agg(row_to_json(m)::text, '' ORDER BY id)` — same construction as the packet's certificate).

## L1 gap, for the L1 owner (Ganita) — not a rebuild defect

The 8 `yamakantaka_difference` rows are honestly `unavailable` because **L1 holds no
`sensitive_point_gulika_mandi` fact for YAMAKANTAKA**. For the same category L1 carries GULIKA (35 facts) and
MANDI (35 facts; keys `sign`, `longitude_sidereal`, `nakshatra`, `nakshatra_lord`, `pada`, `sign_lord`,
`house_d1`), and none for YAMAKANTAKA (count 0). What L1 does have for Yamakantaka is a **day-part window**
(`panchanga_yamakantaka` / `YAMAKANTAKA_BIRTH_DAY`: `start_iso` 1984-02-05T05:05:55.5Z, `end_iso`
1984-02-05T06:30:44Z, `duration_minutes` present with a NULL value text) — a time interval, not a longitude
or sign, so the writer correctly does not treat it as an operand for a sign/longitude difference.
**Ask of the L1 owner:** if the doctrine behind `yamakantaka_difference` requires a Yamakantaka longitude/sign
(it is a computed sensitive point in the classical corpus; this file does not cite the verse and makes no
classical claim), add a `sensitive_point_gulika_mandi` row set for YAMAKANTAKA with the same keys as MANDI;
otherwise the rows should stay `unavailable` and the 8 rows are a standing honest-gap marker. Until then
nothing downstream may read those 8 rows as resolved. (Stream B did not derive any value; B.10 — no
fabricated computation.)

## Changelog
* 1.0 (2026-10-02) — first issue; read-only before/after for finding #9; packet closed; Yamakantaka L1 gap recorded.
