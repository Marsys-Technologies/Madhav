# bg_vastu_directions: Citation Pass 2 (decision OS-2026-10-05-CITATIONS)

Branch `suvarna/engine-citation-vastu`. Migration **1321**. Queued after S-L2.

## What changes
One row: `direction = Southwest` (Rahu). `classical_citation` becomes the decided K1 string (Muhurta Chintamani Gocara-prakarana v.9 tika, `muhurta_chintamani:PG66:C1`, plus the Hora Sara Ch.2 direction table as analogue). `favorable_color` stays NULL (no source; not invented). 8 direction rows and 24 remedial rows before and after; the other seven directions and every remedial row are byte-identical.

## Migration 1321 (registry metadata)
Guarded replace of the directions pin inside `integrity_check_sql` (1d18e307... -> 27155f57...; the remedials half is untouched). The cosmetic `english_description` edit is NOTICE-and-skip: it is applied only when the stored text is exactly migration 643's, otherwise left as stored (a cosmetic field never blocks a deploy). `SET LOCAL lock_timeout = '5s'`. SERVING EFFECT: the UPDATE fires `nirmana_registry_receipt_invalidation` (migration 596) and stales bg_vastu_directions' freshness rows; the rebuild writes fresh receipts.
**Order:** apply 1321, then the governed rebuild (expected-change mode, `00_ARCHITECTURE/briefs/suvarna/citation_pass2/expected_change_bg_vastu_directions.json`: 32 rows, fingerprint 99d9c4b4...). Between them the stored check reads FALSE by design.

## Readers
`query_vastu_directions.ts` serves the citation verbatim; `ga_vastu` reads the direction-to-graha map only. No reader branches on the citation text.

## Left alone on purpose (not decisions; listed for SS in `E5.7/CITATION_AMBIGUOUS.md`)
The Southwest remedial row's bare tradition label, the seven Mayamata sibling direction rows (pass-2 recommendation 5), other remedial labels.

## Tests run
`platform/python-sidecar/tests/l0/test_citation_pass2_vastu.py` (8, disposable Postgres): row pins, Ldgr predicate, 612's pin reproduced by the pre-change seed, migration apply / idempotent / refuse / description notice, expected-change fingerprint. Governance declaration and fingerprint tests pass.
