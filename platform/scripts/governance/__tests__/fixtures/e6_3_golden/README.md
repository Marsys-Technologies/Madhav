# E6.3 golden certificate ledgers

`ledger_clean.jsonl` and `ledger_after_invalidation.jsonl` were produced ONCE by `make_golden.py` (this directory),
over the E6.3 mini registry (`_e6_3_fixtures.MINI_CENSUS`), for two L1 assets `ga_alpha` and `ga_beta`:

* the certificate lines (`kind: gate`) were written by the REAL E5.1 write path,
  `nikasha_certify.write_certification` (branch `suvarna/e5.1-certify`, working tree at generation time: seq +
  prev_sha256 chain, census file committed under the trusted root, writer hashes verified);
* the watermark and invalidation lines were written by the REAL E5.5 `nikasha_stale_certs.invalidate()` (branch
  `suvarna/e5.5-stale-certs`): `ledger_clean` is the first walk (nothing stale, watermark @1); `ledger_after_invalidation`
  is a second walk in which `ga_beta`'s semantic fingerprint moved (seven `invalidation` lines, watermark @2).

Two DEVIATIONS, both because E5.5 had not yet been rebased on E5.1's chain when this was generated, and both
serialisation-only (no decision logic): E5.5's append has no `seq`, so a `json.dumps` shim adds it; E5.5 unpacks
`nikasha_certify._parse(...)` as two values while E5.1 now returns three, so the call is wrapped to drop the third.
Regenerate (and delete both shims) once E5.5 is rebased: `python3 make_golden.py <out dir>`.

The writer file bodies the records hash are `# writer of <asset>, v1\n` (see `test_e6_3_e5_reconcile.py`).
