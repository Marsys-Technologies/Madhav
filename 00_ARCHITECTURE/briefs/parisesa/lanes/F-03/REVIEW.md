---
lane: F-03
stream: S5 MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-03/SPEC.md, F-03/DIAGNOSIS.md, F-03/repro_raw.json (existence confirmed). No REVIEW_LEADS.md present.

Source traced line-by-line at `/Users/Dev/par-night/main-ro`:
- `register_d7_channel.ts`: read lines 1528–1608 (listRemediesByCategoryCapability), 1669–1750 (queryTantricRemediesCapability), 1752–1823 (queryRemediesByPlanetCapability), 1825–1899 (queryMantrasCapability).
- `register_p1_aliases.ts`: read lines 1560–1628 (all four alias registrations).

No exit test file exists yet (new file per spec — correct, not a deficiency).

## Q1 — Mechanism vs symptom

The spec targets the mechanism: `input_schema` on each of the four capabilities in `register_d7_channel.ts` omits `limit`/`offset`; the handler reads neither field; the SQL has no `LIMIT`/`OFFSET` clause. The downstream truncation in `response_budget.ts` is correctly identified as the symptom and explicitly excluded from the fix target. Mechanism addressed.

## Q2 — Sub-claim mapping

All three Stage D §2 sub-claims map directly to spec elements:
- (a) limit/offset are no-ops in the handler → SPEC §2: add schema fields + read args + apply SQL clause for all four capabilities.
- (b) entire category always fetched → same SQL change closes this.
- (c) response_budget mid-JSON truncation → SPEC §7 maps this as indirect fix (capped payload no longer hits the trim path for the common case); §2 explicitly states `response_budget.ts` unchanged, correctly so.

All three DIAGNOSIS §4 siblings map to SPEC §4 coverage table with stated dispositions.

## Q3 — Exit test genuinely fails on current code

Traced against source: `listRemediesByCategoryCapability.handler(args)` at line 1572 reads only `args['category']`; `args['limit']`/`args['offset']` are never read. SQL at lines 1584–1591 has no LIMIT/OFFSET. Calling with `{category:'mantra'}` and `{category:'mantra', limit:5}` executes identical SQL — identical rows returned, identical result_hash. The test assertion "assert different result_hash / different row counts" FAILS on current code.

Same verdict for the other three siblings: queryTantricRemediesCapability (handler lines 1712–1749, SQL 1725–1733, no LIMIT) reads only `deity`/`planet`; queryRemediesByPlanetCapability (handler 1791–1822, SQL 1799–1806) reads only `planet`; queryMantrasCapability (handler 1863–1898, SQL 1874–1882) reads only `planet`. All four miss limit/offset identically.

Exit test would be RED on current code. ✓

## Q4 — Sibling coverage

DIAGNOSIS §4 identifies exactly 3 live siblings: `query_tantric_remedies`, `query_remedies_by_planet`, `query_mantras`. All three are:
1. Confirmed in source to have `input_schema` lacking `limit`/`offset` (verified above).
2. Confirmed in source to have SQL with no LIMIT/OFFSET (verified above).
3. Covered in SPEC §4 with explicit disposition "COVERED — built in this spec" and a stated reason (conductor-confirmed lease addition for `register_d7_channel.ts`).

No uncovered sibling sites. The non-siblings listed in DIAGNOSIS §4 (`query_remedies_for_chart`, sutravali capabilities, `list_classical_texts`, `find_verses_about`) are correctly excluded. Coverage complete.

## Q5 — Recurrence guard

SPEC §5 describes two layers:
1. Immediate: the exit test itself detects all four instances (param declared, alias forwards it, handler ignores it → result_hash identical).
2. Durable: CL-03 shared param-parity harness (spec'd separately off F-10 exemplar), walks every registered capability's JSONSchema and asserts every declared param provably changes `result_hash` or is explicitly marked advisory.

The immediate guard detects the defect class exactly (not a weak proxy). The durable harness is referenced as a separate lane spec rather than claimed as part of this fix — this is honest. Guard is adequate.

## Q7 — Unverified assumptions / file:line citations

All checked against source:
- `listRemediesByCategoryCapability` at ~1528–1608: CONFIRMED (starts 1529, ends 1608). ✓
- `queryTantricRemediesCapability` at 1712–1749: CONFIRMED. ✓
- `query_remedies_by_planet` capability at 1791–1822: CONFIRMED (1791–1823). Off by one on close brace, inconsequential. ✓
- `queryMantrasCapability` at 1863–1898: CONFIRMED. ✓
- SQL citations: 1584–1591, 1725–1733, 1799–1806, 1874–1882 — all CONFIRMED. ✓
- `name: 'query_tantric_remedies'` at line 1674: CONFIRMED. ✓
- `name: 'query_remedies_by_planet'` at line 1757: CONFIRMED. ✓
- `name: 'query_mantras'` at line 1830: CONFIRMED. ✓
- `register_p1_aliases.ts` alias block 1570–1580 forwarding `{category, limit, offset}`: CONFIRMED at lines 1570–1580. ✓
- `ref_tantric_remedies_get` (~1594–1604, spreads params including GlobalBase): CONFIRMED at 1594–1604. ✓
- `ref_remedies_by_planet_get` (1606–1616, explicit `{planet, limit, offset}`): CONFIRMED at 1606–1616. ✓
- `ref_mantras_get` (~1618–1628, spreads params): CONFIRMED at 1618–1628. ✓
- SPEC §2 claim "No change needed to `register_p1_aliases.ts`": CONFIRMED — all four aliases correctly wire limit/offset. ✓
- SPEC §2 claim "No change needed to `response_budget.ts`": aligned with DIAGNOSIS §5 which confirms truncation is a downstream symptom of the unbounded fetch. ✓

`writer_asset` / `data_delta` / RS-A not referenced in the spec — this is correct. F-03 is a pure query-layer fix (no data written, no writer layer), so rebuild policy does not apply.

## Named deficiencies

None.

## Verdict: COMPLETE

All spec claims map to verified source. Exit test would be RED on current code. All sibling sites covered. Recurrence guard is sound. No unverified assumptions. No deficiencies.
