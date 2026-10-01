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
