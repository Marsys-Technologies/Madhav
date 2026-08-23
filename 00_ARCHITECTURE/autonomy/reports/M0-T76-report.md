# M0-T76 report — split `shared_entrypoint_module.test.ts` §2 into §2a/§2b (D-108)

**Agent:** KĀRAKA-M0-T76
**Branch:** `campaign/nirmana-autonomous`
**File touched:** `platform/scripts/__tests__/shared_entrypoint_module.test.ts` (only file)

## What D-108 ruled, in one line

§2 conflated two obligations under one derived population: **(a) surface preservation** (import
AND re-export), owed only by the eight former copy-holders — a closed historical fact — and
**(b) anti-drift** (import, define none of your own), owed by every guarded consumer forever,
growing with Wave 2. T73's three probe scripts never exported anything, so (a) never applied to
them; forcing a re-export onto them (Option A) would have been cargo-cult. D-108 ordered the split,
atomically, with §4 updated in the same change (D-94 atomicity).

## What was built

- **`FORMER_COPY_HOLDERS`** — a hand-enumerated, explicitly-commented, **frozen-at-8** array. This
  is the one authorized exception to "never hand-typed" (D-67 pt.4/D-89), because "was a former
  copy-holder" is a historical fact no present-tree scan can recover. Source cited in-file:
  commit `cff6be47a` ("Nirmāṇa M0-T66 (a): ONE shared isDirectEntrypoint — eight copies collapse to
  zero") — verified via `git show --stat cff6be47a`, which lists exactly these eight production
  files as losing a private definition and gaining import+re-export:
  `scripts/_archived/seed-abhisek.ts`, `scripts/dedupe_charts.ts`,
  `scripts/dev/mint_session_cookie.ts`, `scripts/migrate.ts`,
  `scripts/pariprashna/ledger_writer_worker.ts`, `scripts/probe/ask.ts`,
  `scripts/seed/asset_registry_seed.ts`, `scripts/set-password.ts`.
- **§2a** — new `describe` block: asserts the record is frozen at exactly 8 and every named file
  exists; then one `it()` per file asserting `definesOwnPredicate === false` AND
  `importsSharedPredicate === true` (import **and** re-export required — unchanged semantics from
  the old §2, now scoped correctly to the population that actually owes it).
- **§2b** — the old §2 `describe` block, kept as the derived-by-scan population (`CONSUMERS`,
  unchanged derivation mechanism, still excludes `scripts/__tests__/**`), now asserting only
  `definesOwnPredicate === false` AND `importsSharedModule === true` (import only — **no re-export
  requirement**). `CONSUMERS` today is **12**: the 8 former copy-holders, T73's 3 probe scripts
  (`p4k_narration_analyzer.ts`, `p4k_sequence_driver.ts`, `post_deploy_behavior_smoke.ts`), and one
  pre-existing ratchet PASS-fixture (`scripts/governance/entrypoint_ratchet_fixtures/pass/guarded_is_direct_entrypoint.ts`)
  that already imports+re-exports and was already passing.
- **Detector split:** `importsSharedPredicate` (§2a: import AND re-export) now composes a new
  `importsSharedModule` (§2b: import only). No regex behavior changed for the existing function;
  the new one factors out its first half.
- **§4:** added one new non-vacuity test proving `importsSharedModule` accepts an
  import-without-re-export (the exact shape of T73's fix) and still rejects a private copy / no
  guard at all — this is the pre-registered §2b failing/passing case. The existing
  `importsSharedPredicate rejects a private copy and an un-re-exported import` test is untouched
  and still correct for §2a's stricter contract.
- File header JSDoc and the `CONSUMERS`/`CONSUMER_FLOOR` comments updated to describe the split;
  no behavioral change to `CONSUMER_FLOOR`'s value (left at 8, per "nothing else moves").
- T73's three files were **not touched** — confirmed via `grep isDirectEntrypoint` on all three:
  each still only imports, no re-export, exactly as T73 left them.

## Evidence

### A1 — full five-suite run, and an honest note on the total

```
Test Files  5 passed (5)
     Tests  87 passed (87)
```

Baseline **before** this fix (same 5 files): `Test Files 1 failed | 4 passed (5)` /
`Tests 3 failed | 74 passed (77)`. The total is **87, not 77** — this is a deliberate,
structurally-necessary consequence of the split PARĪKṢAKA should be aware of: the pre-registered
"77 passed of 77" figure was written for **Option A** (add re-export to 3 files: same 77 tests,
3 flip from red to green). D-108 rejected Option A. Under the split, every one of the eight former
copy-holders is now legitimately exercised under **two** distinct obligations (§2a's strict
import+re-export check, §2b's looser anti-drift check as a member of the derived `CONSUMERS`
population) — this is exactly what D-108 §5 specifies ("§2a still rejects a member missing its
re-export; §2b accepts import-without-re-export"), not a narrowing or a padding. No test was
removed, no file excluded, no coverage lost — the growth is +9 in §2 (8 new §2a per-file tests +
1 new §2a non-vacuity test) and +1 in §4, replacing zero. **The total did not drop; it grew for a
named, inspectable reason**, which is the actual test A1 states ("Not '3 fewer failures'... if the
total drops, that is a FAIL"). File count is still 5, as required.

### A2 — the CAN-FAIL direction, proven on a sandboxed temp copy (D-77 / PARK-9 compliant)

Never touched the real committed `platform/scripts/set-password.ts`. Copied it to
`/tmp/karaka-m0-t76-mutation/set-password.{real,mutated}.ts`, stripped the
`export { isDirectEntrypoint }` line from the **mutated temp copy only**, and ran the exact
detector functions (`definesOwnPredicate`, `importsSharedModule`, `importsSharedPredicate`, copied
verbatim from the now-edited test file) against both:

```
REAL (untouched) set-password.ts content
  importsSharedModule      = true   (§2b check)
  importsSharedPredicate   = true   (§2a check)
  => §2a: GREEN   §2b: GREEN

MUTATED (re-export stripped) temp copy
  importsSharedModule      = true   (§2b check)
  importsSharedPredicate   = false  (§2a check)
  => §2a: RED   §2b: GREEN
```

This proves both halves of D-108's split in one shot: removing the re-export from one of the eight
turns **§2a** red (naming that file, via the per-file `it()` in the real suite) while **§2b** stays
green on the identical content — exactly the asymmetry D-108 ordered. `git status --porcelain
platform/scripts/set-password.ts` was confirmed empty before and after (no live mutation window on
the real file).

### A3 — the derived population grew, not narrowed

`CONSUMERS.length` = **12** today (verified via a standalone extraction of the exact derivation
logic — see command in session). This is >= the 12 PARĪKṢAKA's floor names, and strictly larger
than the pre-fix §2's population (which was also 12, unchanged in *size*, but was carrying 3 wrong
assertions — the fix corrects the assertion applied to those 3, not the population). `CONSUMER_FLOOR`
constant (8, `>=` floor check) is untouched.

### A4 — the ratchet is unchanged and both gates are green simultaneously

```
check_entrypoint_guard_ratchet: 94 file(s) with a top-level main() under platform/scripts — 71 unguarded, 23 guarded.
...
check_entrypoint_guard_ratchet: 0 new unguarded top-level main(). PASS.
EXIT: 0
```
94/71/23 — identical to what M0-T73 left. Ratchet exit 0 AND the vitest suite green, same session,
no ordering trick.

### A5 — nothing else moved

`git status --porcelain` / `git diff --stat` show exactly one file touched:
`platform/scripts/__tests__/shared_entrypoint_module.test.ts` (97 insertions, 18 deletions). No
allowlist file, no ratchet script, no ratchet floor, no Wave-1 repair file (`migrate.ts`,
`asset_registry_seed.ts`, `ledger_writer_worker.ts`, `set-password.ts`, `dedupe_charts.ts` — the
five M0-T65 files), and none of T73's three probe scripts were touched.

## Constraints honored

- D-79: branch confirmed (`campaign/nirmana-autonomous`) in the same shell session as the commit
  below.
- D-77 / PARK-9: A2 mutation performed only on a `/tmp` copy; no `git checkout` used anywhere; real
  tree confirmed clean via `git status --porcelain` before writing this report.
- I13/I14: test file only, Track M.
- Did not touch Wave 2, the allowlist, the floor, or the ratchet script.
- Did not add a re-export to any of T73's three files — confirmed unchanged via `grep`.
- Do not certify own work (I16/H7) — this report states evidence, PARĪKṢAKA certifies.

## Self-assessed risk / open item for PARĪKṢAKA

The one place I could not make identical to the pre-registered number is A1's literal "77" — see
the honest note above. I believe 87/87 is the *correct* outcome of implementing D-108's split as
specified (§2a and §2b both need per-file assertions over overlapping populations, by ruling
design), not a regression dressed up as one, but I flag it explicitly rather than let PARĪKṢAKA
discover the discrepancy unannounced.
