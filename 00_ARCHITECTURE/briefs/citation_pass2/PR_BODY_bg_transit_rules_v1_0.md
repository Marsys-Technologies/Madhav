# bg_transit_rules: Citation Pass 2 (decision OS-2026-10-05-CITATIONS), form (b)

Branch `suvarna/land/citations-transit` (squashed from the engine branch `suvarna/engine-citation-transit`, renumbered). Migration **1320**. Un-queued until the L0 data batch after S-L2.

## What changes
Six rows of `bg_transit_rules` (graha rahu / ketu x primary_house 3 / 6 / 11, rule_type favourable). `classical_citation` and `rule_notes` only. 76 rows before and after (69 writer-owned + 7 migration-owned), none added or removed, ids unchanged; `rule_type`, `primary_house`, `vedha_house` (3->9, 6->12, 11->5) and the 3 + 3 shape are exactly as before.

SS ruled form (b) via Pravaha: the citation still STARTS with `UNSOURCED` for the vedha partner and carries the K1 transit result after it:
`UNSOURCED (vedha partner: inference, not in the cited verses) - transit result: Phaladipika Adh. XXVI, Sl. <24 for Rahu, 2 for Ketu> [machine locus phaladeepika:PG331:C1 / PG321:C1] "<excerpt, at most 25 words>"`.
The vedha field is not cited. The pass-2 TSV is unchanged; the choices inside the ruling (which verse per graha, per-row excerpts) are listed in `E5.7/CITATION_AMBIGUOUS.md`.

## Required statements
1. **L3 staleness (accepted).** `ka_vedha_gochara` stores the citation verbatim and its upstream fingerprint includes it, so that parked L3 asset reads stale after the change (by design; the owner accepts L3 staleness). The node rows stay stamped `unsourced` there (its stamps read the `UNSOURCED` prefix, which is kept).
2. **Loader digest.** The citation text sits inside `pairs_content_digest` (`services/gochara_rules/vedha_derive.py:90`), which changes when the rebuild runs. It is the L0 binding of the AM-16 input vector (`services/gochara_kernel/input_vector.py:74`). **Pravaha gets a day-before notice.**
3. **HOLD the governed transit rebuild until the L0 data batch after S-L2.**

## Loader compatibility (proved, tests/l0/test_citation_pass2_transit.py, real Postgres)
`vedha_derive.load_pairs` on the rebuilt table: no `VedhaPairsError`, 36 classical pairs + 3 Rahu + 3 Ketu node rows (census 42), the same pair mapping as on the pre-change rows. A node row that does not start with UNSOURCED still refuses (that is why the prefix stays).

## Migration 1320 (registry metadata, ONE column)
Replaces the pinned hash inside `integrity_check_sql` (1dbdd265... -> d78583ae...) by a guarded `replace()` (old pin exactly once; already-resealed is a no-op; anything else refuses). `english_description` is NOT touched (SS / Pravaha rule: unchanged; it still matches `platform/scripts/seed/asset_registry_seed.ts`). `SET LOCAL lock_timeout = '5s'`. SERVING EFFECT: the UPDATE fires `nirmana_registry_receipt_invalidation` (migration 596) and stales bg_transit_rules' freshness rows; the rebuild writes fresh receipts.
**Order:** apply 1320, then the governed rebuild (dispatch tool, expected-change mode, `00_ARCHITECTURE/briefs/suvarna/citation_pass2/expected_change_bg_transit_rules.json`: 112 rows, fingerprint c4ae7d00...). Between the two the stored check reads FALSE by design. Falsifiers after the rebuild: stored check `t`; `UNSOURCED%` = 6; `UNSOURCED (vedha partner:%` = 6; `Phaladipika Adh. XXVI, Sloka%` = 36; BPHS Ch.29 = 19.

## Tests run
- `platform/python-sidecar/tests/l0/test_citation_pass2_transit.py` (12, disposable Postgres): rows by natural key, pins, loader, migration (apply / idempotent / refuse), expected-change fingerprint, generic Ldgr predicate.
- `platform/tests/unit/migrations/nirmana_l0_transit_integrity_contract.test.ts` (the CI step `ci.yml:923`, real Postgres): updated for the deployed order 613, 1078, 1079, then 1320 (the 1078 check is false on the rebuilt rows, 1320 makes it true); run on a disposable cluster, 6 / 6 pass.
- Governance: `test_e6_l0_batch2_declarations`, `test_e5_7_fingerprint_declarations` (the seed keeps the line numbers FINGERPRINT_DECLARATIONS.json cites).

## Census
The census's generic Ldgr predicate treats `UNSOURCED...` as a placeholder; the six rows are read through the declared `split_citation` of branch `suvarna/engine-ldgr-split-citation` (the transit result must resolve to a corpus chunk). Known finding on this table: vedha partner unsourced, pending owner ruling ND-NODE-VEDHA.

## Row diff
`00_ARCHITECTURE/briefs/suvarna/citation_pass2/BG_TRANSIT_RULES_ROW_DIFF.md`.
