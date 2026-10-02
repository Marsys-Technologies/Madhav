# E6.3 golden certificate ledgers

`ledger_clean.jsonl` and `ledger_after_invalidation.jsonl` were produced ONCE by `make_golden.py` (this directory),
over the E6.3 mini registry (`_e6_3_fixtures.MINI_CENSUS`), for two L1 assets `ga_alpha` and `ga_beta`, with NO shim:

* the certificate lines (`kind: gate`) were written by the REAL E5.1 write path `nikasha_certify.write_certification`
  (branch `suvarna/e5.1-certify`, commit cbe51e065 plus its working tree at generation time: seq + prev_sha256 chain,
  census file committed under the trusted root, writer hashes verified, `cross_checked: true`);
* the event lines (`type: watermark` / `type: invalidation`, no cert_key) were written by the REAL E5.5
  `nikasha_stale_certs.invalidate()` (branch `suvarna/e5.5-stale-certs`, commit ac7982210 plus its working tree),
  which appends through E5.1's `append_records`. `ledger_clean` is the first walk (nothing stale; watermark covers_seq 14);
  `ledger_after_invalidation` is a second walk in which `ga_beta`'s semantic fingerprint moved (seven invalidation events,
  watermark covers_seq 15).

E5.1 and E5.5 were still being finished at that time: regenerate with `python3 make_golden.py <out dir>` when they land and
re-run `test_e6_3_e5_reconcile.py` (its parity tests run the sibling modules' own verifiers on the same bytes).
The writer file bodies the records hash are `# writer of <asset>, v1\n` (see `test_e6_3_e5_reconcile.py`).

## ledger_v2.jsonl (N-74 citation_state, record_version 2)

Produced ONCE by `make_golden_v2.py` with the REAL E5.1 citation-state writer (`nikasha_certify.write_certification`, branch
`suvarna/engine-E5.1-citation-state`, worktree at generation time) and the real E5.5 `invalidate()` (one clean walk), over the mini
registry, with the writer's `CITATION_CRITERIA` patched to the mini registry's `Ldgr.src` / `Idem.alt`. Four assets: `ga_alpha`
sourced; `ga_beta` Ldgr.src `sourced_ocr_unverified` (caveat true); `ga_gamma` Ldgr.src PASS with a NULL state (caveat true, still
a PASS); `ga_delta` Idem.alt NO_DETECTOR / `unsourced` (the census caps it). Every record is `record_version` 2 with
`citation_state` (null except on the citation gates) and `citation_state_caveat`. Regenerate when the writer's shape changes.

## citation_verdicts.json (E5.1's verdicts on the citation-state parity variants)

Recorded ONCE from the REAL E5.1 reader (`nikasha_certify.parse_ledger` of branch `suvarna/engine-E5.1-citation-state`, commit in the
file) by `python platform/scripts/governance/__tests__/_e6_3_citation_variants.py`: for each of the 32 variants (golden `ledger_v2.jsonl`
mutated in one citation field and re-chained) it stores the variant's sha256, the verdict (OK / REFUSED + code) and, when OK, the parsed
`[citation_state, citation_state_caveat]` of every certificate. `test_e6_3_citation_parity.py` checks E6.3's parser against it in CI (no
E5.1 worktree needed) and, where the worktree exists, against the live reader. The variants run with E5.1's `CITATION_CRITERIA` patched to
`Ldgr.src` / `Idem.alt` and `CITATION_STRICT` to `Idem.alt` (the mini registry has no Carr.D1); real Carr.D1 strictness is checked by a
direct-call test. Re-record when the variants or E5.1's citation rules change.
