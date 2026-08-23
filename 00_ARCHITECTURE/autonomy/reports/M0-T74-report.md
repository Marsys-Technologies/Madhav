# M0-T74 — D-101's assertion (iii), salvaged by the conductor after an API error

**KĀRAKA-M0-T74 was terminated mid-response by a genuine API connection error** ("Connection
lost mid-response") right after its own last message said "Good, I see the format conventions.
Now let's write the report." Its code change was complete and uncommitted; it never wrote the
report. This report is authored by SŪTRADHĀRA, on the same basis as M0-T71's salvage: substance
complete, discard would be wasteful, disclosure over silence. **Not a certification — PARĪKṢAKA
verifies in full.**

## What I verified before committing

- `python3 -m py_compile` on `check_entrypoint_guard_ratchet.py` — clean.
- `--self-test` — **PASS**: *"6 pass fixture(s) silent, 4 fail fixture(s) caught, 5/5 guard
  idioms exercised, 11 floor case(s) proven in both directions, **5 stale-amnesty case(s)
  proven in both directions**."* This satisfies PARĪKṢAKA's pre-registered requirement
  (`baseline-for-D-101-assertion-iii-starts-green`) that the new assertion be shown failing on
  a mutated case, not only passing on the real, clean tree.
- The self-test's internal simulation writes to a `tempfile`-backed sandbox
  (`tmp / "sync" / "fresh_floor.json"`), confirmed via `find` and `git status` to be nowhere
  near the real repo — the committed `entrypoint_guard_floor.json` and allowlist are
  **byte-unchanged** (`git diff --stat` empty on both).
- The diff is **1 line removed, ~207 added**, entirely additive except for one summary string
  extended to report the new stale-amnesty count alongside the existing floor-case count. No
  existing logic for assertions (i) or the floor (ii) was touched.
- No `UPDATE`/`INSERT`/`DELETE`/`ALTER` anywhere in the diff.
- No other agent's files were touched.

## What the diff contains

`stale_amnesty_check()` (new function, ~line 1052): asserts no entry in the current allowlist
names a file that is **currently guarded** — reusing the existing guard-detection logic already
built for assertion (i) rather than re-implementing it (per D-101's own framing and the D-94
"one implementation" lesson). Reports via the file's established `Result`/`check=` shape,
consistent with the existing two assertions' error reporting.

`run_stale_amnesty_self_test()` (new function, ~line 1335): the mandatory can-fail proof PARĪKṢAKA
required — a "guarded_now.ts" fixture proves RED (naming the file), a "still_unguarded.ts"
fixture proves the assertion stays GREEN for a genuinely-unguarded allowlisted file. Both run
against synthetic in-memory/sandbox data, not the real allowlist.

## What I did not do

- Did not run the ratchet's live/production check against the real allowlist myself beyond
  `--self-test` (which is sandboxed by design).
- Did not touch assertions (i) or (ii)/the floor mechanism.
- Did not touch Wave 2, any of the 71 unguarded files, or any asset data.

I certify nothing here (I16/H7). PARĪKṢAKA verifies, and should treat the unusual provenance
(conductor-salvaged after an API error, not self-reported) as grounds for full scrutiny.
