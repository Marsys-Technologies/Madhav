# M0-T61 — escape CR/LF in `formatServerNotice` before relaying (D-65 part 3)

**Agent:** KĀRAKA-M0-T61
**Commits:** `84a6b3a12` — `platform/scripts/migrate.ts`, 1 file, +34/−6.
`c8374b783` — `platform/scripts/__tests__/migrate_notice_listener.test.ts`, 1 file, +104/−0,
**severable** (separate commit on purpose; see §7).
**Branch:** `campaign/nirmana-autonomous` (never main, H2).
**Report location:** the tracked path `00_ARCHITECTURE/autonomy/reports/M0-T61-report.md` is
the durable copy (D-63 / D-66 part 0). The `mailbox/to_verifier/` copy is **gitignored** —
`00_ARCHITECTURE/autonomy/mailbox` is in `.gitignore`, which is exactly the mechanism that
destroyed ~50 KĀRAKA reports — so it cannot be committed and must not be treated as the record.

**Grant:** D-65 part 3, scoped to `formatServerNotice` **and nothing else**. Its three conditions
are discharged in §3, §4 and §5. I state evidence, not a verdict (I16/H7).

---

## 1 — The exact change

`platform/scripts/migrate.ts`, one new exported pure function plus its use inside
`formatServerNotice`. Nothing else in the file moved.

```diff
+export function escapeRelayedLineBreaks(value: string): string {
+  return value.replace(/\r/g, '\\r').replace(/\n/g, '\\n')
+}
+
 export function formatServerNotice(notice: ServerNoticeLike | null | undefined): string {
-  const severity = notice?.severity ?? 'NOTICE'
-  const message = notice?.message ?? '(no message)'
+  const esc = (value: string): string => escapeRelayedLineBreaks(value)
+  const severity = esc(notice?.severity ?? 'NOTICE')
+  const message = esc(notice?.message ?? '(no message)')
   const extras: string[] = []
-  if (notice?.code) extras.push(`code=${notice.code}`)
-  if (notice?.detail) extras.push(`detail=${notice.detail}`)
-  if (notice?.hint) extras.push(`hint=${notice.hint}`)
-  if (notice?.where) extras.push(`where=${notice.where}`)
+  if (notice?.code) extras.push(`code=${esc(notice.code)}`)
+  if (notice?.detail) extras.push(`detail=${esc(notice.detail)}`)
+  if (notice?.hint) extras.push(`hint=${esc(notice.hint)}`)
+  if (notice?.where) extras.push(`where=${esc(notice.where)}`)
```

**Escape, not strip** — D-65 condition 3 is the reason, and it is designed in rather than checked
afterwards: every byte of the server's text survives, only its ability to end a log line does not.

**All six interpolated fields, not the four D-65 names.** `code` and `severity` are equally
server-controlled and equally interpolated by this function; escaping `message`/`detail`/`hint`/
`where` alone would have left the same hole one field to the right. That is inside
`formatServerNotice` and therefore inside the grant, but it is wider than the four field names the
ruling lists, so I am naming it rather than letting it pass unremarked. §3's table shows the
`code` and `severity` injection points were live before this change.

**D-56 intact, measured not asserted:** `git diff -U0 | grep '^+'` for
`client.query|BEGIN|COMMIT|ROLLBACK|SAVEPOINT|pool|connect` → **0 hits**. No transaction handling,
no pool/client lifecycle, no `deploy.yml`.

## 2 — Method (reproduced from M0-T57, not invented)

Three things M0-T57 did that I did the same way, because D-65 part 1 singled them out:

1. **The deploy step body is YAML-parsed out of `deploy.yml`, never retyped.** `yaml.safe_load` →
   `jobs.migrate.steps[name == 'Run database migrations'].run` → written to `step.sh` → executed
   under `bash -e` with a stub `npx` on `PATH`. Every exit code in §3 is the shell's.
2. **Fixtures come from the production code, not from my typing.** The `before` formatter is the
   **git blob at HEAD** (`git show HEAD:platform/scripts/migrate.ts`, sha256
   `54007b639492976d5428966703303b1303681bddecc959e465f435d12711a2db` — the same sha V-38 recorded
   for the file it verified); the `after` formatter is the production file itself
   (sha256 `61eb36423102f2493f2d796ba7fca91c7b8b52ce608580be289adccfa56cc479`).
3. **I went one step further than T57 could:** T57's demonstration used the production formatter
   with a hand-supplied notice object. I drove the **whole chain** — a real PostgreSQL 17.10
   server raising a real `RAISE NOTICE`, through `pg`'s protocol, through the real
   `attachNoticeListener`, through `formatServerNotice`, to stderr — on a **throwaway cluster**,
   with byte-identical copies of `migrate.ts` in a temp package (the M0-T52 pattern). So the
   before/after pair in §4 is a measurement of the runner, not of a model of it.

**No production contact.** `DATABASE_URL` was **unset** in my shell throughout (verified:
`[<unset>]`); the only value ever set pointed at `127.0.0.1:55461`, a throwaway cluster I
`initdb`-ed into the session scratchpad and stopped at the end. **No migration in
`platform/migrations` was applied anywhere.** The only SQL applied was four probe files that live
in the scratchpad and were never added to the repo. No credential was read, printed or logged.

Harness and every log quoted below: `<scratchpad>/t61/` (`harness.py`, `step.sh`, `gen_forge.ts`,
`e2e_*.{out,err,combined}`, `clean_*`, `cleannoop_*`, `fail_*`, `before_forge.txt`,
`after_forge.txt`, `pkg*/`). Nothing under it was added to the repo.

## 3 — Condition 2: the multi-line forge no longer matches

### 3a — The same demonstration that established it (M0-T57 §6), both formatters

Eight injection points, each carrying `[migrate] MIGRATE_RUNNER_COMPLETE mode=apply …` after a
line break. `phys` = physical lines the rendered notice occupies; `bare` = matches of the literal
anywhere; `anch` = matches of the deploy's exact `^\[migrate\] MIGRATE_RUNNER_COMPLETE`.

| injection point | BEFORE phys / bare / anch | AFTER phys / bare / anch |
|---|---|---|
| `\n` in `message` (T57 §6 verbatim) | 2 / 1 / **1** | 1 / 1 / **0** |
| `\r\n` in `message` | 2 / 1 / **1** | 1 / 1 / **0** |
| bare `\r` in `message` | 2 / 1 / 0 | 1 / 1 / 0 |
| `\n` in `detail` | 2 / 1 / **1** | 1 / 1 / **0** |
| `\n` in `hint` | 2 / 1 / **1** | 1 / 1 / **0** |
| `\n` in `where` | 2 / 1 / **1** | 1 / 1 / **0** |
| `\n` in `code` | 2 / 1 / **1** | 1 / 1 / **0** |
| `\n` in `severity` | 2 / 1 / **1** | 1 / 1 / **0** |

`bare` stays 1 in every AFTER row and that is the point: **the text is relayed, not dropped.** The
forgery closes because the line boundary is gone, not because the content was censored.

The bare-`\r` row is the one honest asymmetry: `grep` splits on `\n` only, so a bare CR never
forged the *grep*. It forges the *reader* — a terminal or log viewer renders CR as a carriage
return and the second half can appear to start its own line. It is escaped for that reason, and I
am not claiming it was a grep hole.

### 3b — The same forge, end to end, through a real server and the real runner

Probe `002_probe_forged_sentinel.sql` (`RAISE NOTICE E'benign first line\n[migrate]
MIGRATE_RUNNER_COMPLETE mode=apply files_on_disk=443 …'`) applied by the real runner against the
throwaway cluster. Combined `stdout`+`stderr`, then the deploy's exact anchored grep:

```
before: combined_lines=18  bare=2  anchored=2
   6:[migrate] MIGRATE_RUNNER_COMPLETE mode=apply files_on_disk=3 ledger_rows=3 …     <- the runner's own
  16:[migrate] MIGRATE_RUNNER_COMPLETE mode=apply files_on_disk=443 ledger_rows=451 … <- THE SERVER'S
after:  combined_lines=10  bare=2  anchored=1
   6:[migrate] MIGRATE_RUNNER_COMPLETE mode=apply files_on_disk=3 ledger_rows=3 …     <- the runner's own
```

Two anchored matches become one; the one that survives is the runner's own line on stdout, and the
one that disappears is the server's. `bare` stays 2 — again, relayed, not dropped.

**stdout is byte-identical** across the two runs: sha256
`969ac651529d344e835eb87ecfe1f46b6f26315ee98dec755213c7b036f53bb5` for both, `diff` exit 0. The
runner's own completion claim is untouched by this change.

## 4 — Condition 1: the four deploy paths still pass

Step body YAML-parsed from `deploy.yml` (reproduced verbatim in the harness output; the grep line
is `if ! grep -q '^\[migrate\] MIGRATE_RUNNER_COMPLETE' /tmp/migrate.log; then`). Fixtures for
`pending`, `nothing_pending`, `failing` and `real_plus_forged` are **real captured runner output**
from the throwaway cluster; `silent_zero` is the counterfactual a real runner cannot produce
(exit 0 having printed nothing) and is a stub by necessity; `forged_only` is the real relayed
notice bytes with the runner's own sentinel absent.

| scenario | BEFORE exit | AFTER exit | bare B/A | anchored B/A |
|---|---|---|---|---|
| `pending` (3 probes applied, sentinel printed, real NOTICEs on stderr) | **0** | **0** | 1/1 | 1/1 |
| `nothing_pending` (`applied_this_run=0`, sentinel printed) | **0** | **0** | 1/1 | 1/1 |
| `failing` (probe RAISEs EXCEPTION, runner exits 1) | **1** | **1** | 0/0 | 0/0 |
| `silent_zero` (**exits 0 having printed nothing**) | **1** | **1** | 0/0 | 0/0 |
| `forged_only` (multi-line forged NOTICE, no real sentinel) | **0** ← forgery passed | **1** | 1/1 | 1/**0** |
| `real_plus_forged` (real sentinel *and* the forged NOTICE) | **0** | **0** | 2/2 | 2/**1** |
| `legit_multiline_only` (real multi-line NOTICE, no sentinel) | **1** | **1** | 0/0 | 0/0 |

**All four paths D-65 names are identical before and after.** Exactly one path changes
(`forged_only`, 0 → 1) and it changes in the granted direction.

Two guards against over-tightening, both mine rather than the ruling's: `real_plus_forged` (a
genuine run whose log also carries the forgery must still **pass** — it does, 0/0), and
`legit_multiline_only` (a real multi-line notice must never accidentally satisfy the gate, and
must never make the gate go red for a new reason — 1/1, unchanged).

## 5 — Condition 3: legitimate multi-line server detail survives, readable

The evidence is a **real** multi-line notice, not a fixture of one: probe
`001_probe_legit_multiline.sql` raises a NOTICE from a PL/pgSQL function called by another
PL/pgSQL function, with multi-line `DETAIL` and `HINT`. PostgreSQL fills `where` with the full
multi-frame CONTEXT stack — the exact case D-65 part 3 names.

**BEFORE — one notice, twelve physical lines, and only the first carries the prefix:**

```
[migrate:pg] NOTICE: migration 591: both columns and all three constraints present on 128 asset_registry rows (code=00000; detail=natural_key_partition declared on 0
dead_flag true on 0, false on 0
NULL (unadjudicated) on 128; hint=nothing was written by this migration
re-run with --dry-run to preview; where=PL/pgSQL function t61_inner() line 3 at RAISE
SQL statement "SELECT t61_inner()"
PL/pgSQL function t61_outer() line 3 at PERFORM
SQL statement "SELECT t61_outer()"
PL/pgSQL function inline_code_block line 1 at PERFORM)
```

**AFTER — one notice, one prefixed line, every byte still there:**

```
[migrate:pg] NOTICE: migration 591: both columns and all three constraints present on 128 asset_registry rows (code=00000; detail=natural_key_partition declared on 0\ndead_flag true on 0, false on 0\nNULL (unadjudicated) on 128; hint=nothing was written by this migration\nre-run with --dry-run to preview; where=PL/pgSQL function t61_inner() line 3 at RAISE\nSQL statement "SELECT t61_inner()"\nPL/pgSQL function t61_outer() line 3 at PERFORM\nSQL statement "SELECT t61_outer()"\nPL/pgSQL function inline_code_block line 1 at PERFORM)
```

**Losslessness is measured, not eyeballed.** Unescaping the entire AFTER stderr reproduces the
BEFORE stderr byte for byte:

```
AFTER lines: 4   BEFORE lines: 12
unescape(AFTER) == BEFORE byte-for-byte: True
sha256 unescape(AFTER): 7b287b532a43cbf8cdeafe228299c961a5dbe72264dacd0b44112d14add993fa
sha256 BEFORE         : 7b287b532a43cbf8cdeafe228299c961a5dbe72264dacd0b44112d14add993fa
no raw CR/LF remains inside AFTER's relayed lines: True
```

**F-A's warnings, the reason the listener exists, are untouched** — they are single-line and pass
through byte-identical in the same run:

```
[migrate:pg] WARNING: there is already a transaction in progress (code=25001)
[migrate:pg] WARNING: there is no transaction in progress (code=25P01)
```

A side effect worth naming rather than burying: V-38's F-K recorded that *a multi-line NOTICE
loses the `[migrate:pg]` prefix on continuation lines*. After this change there are no
continuation lines, so every relayed line carries the prefix. I did not set out to close F-K and I
am not claiming it as closed — that is PARĪKṢAKA's call — but the behaviour it described is gone
in the measurement above (12 lines, 1 prefixed → 4 lines, 4 prefixed).

The honest cost, stated plainly: a long multi-line notice is now **one long line** instead of
several short ones. Nothing is lost, but a human reading the Actions log will scroll sideways
where they used to scroll down. I judged that the right trade — a truncation would have been the
alternative D-65 forbids — but it is a judgement, not a measurement.

## 6 — Unit detectors, mutation-proved

`platform/scripts/__tests__/migrate_notice_listener.test.ts`: **14 tests pass** (M0-T52's original
8, unaltered, plus 6). Full migrate-related suite: `migrate.test.ts`,
`migrate_completion_report.test.ts`, `migrate_entrypoint_guard.test.ts`,
`migrate_notice_listener.test.ts`, `verify_migrations_deployed.test.ts` → **5 files, 81 tests,
all passed**. `tsc --noEmit` rc=0; `eslint` on both changed files rc=0.

A test that cannot fail is not a detector (§N.8), so I mutated the production code and re-ran:

| mutation | result |
|---|---|
| `escapeRelayedLineBreaks` returns its input unchanged | **4 of the 6 new tests fail**, 10 pass |
| escape `message` only, leave `code`/`detail`/`hint`/`where` raw (the *partial* fix) | **2 of the 6 new tests fail**, 12 pass |

The two that survive mutation 1 are the paired positives (`plain text is byte-identical`, `a
single-line notice renders exactly as before`) — they are supposed to keep passing, and they are
there so the negatives cannot pass vacuously. File restored to sha256 `61eb3642…` after each
mutation, verified.

## 7 — Reachability, re-measured by me

`platform/migrations` + `platform/supabase/migrations`, this checkout:

- **443** `.sql` files.
- **0** contain the literal `MIGRATE_RUNNER_COMPLETE`.
- **0** contain an `E'…'` string carrying `\n` or `\r` — i.e. no file on disk can put a break into
  its own notice text today.
- **10** files `RAISE NOTICE/WARNING/…` at all.

So the forgery this closes was, and remains, unreachable from today's corpus — the same as when
M0-T57 measured it. That is a statement about today's corpus, which is exactly why D-65 granted
the fix anyway.

But note the second half, which the reachability number does not cover: **multi-line relayed text
is not exotic.** The `where`/CONTEXT field is multi-line for any notice raised through nested
PL/pgSQL, with no `\n` anywhere in the file — §5's probe is that case, and it needed no escape
sequence to produce eight lines. Condition 3 was not a hypothetical.

## 8 — What I did NOT do

- Did **not** touch `.github/workflows/deploy.yml`. M0-T57's anchor is untouched and I did not add
  the explanatory comment T57 flagged as belonging to SQ-08's owner.
- Did **not** go near transaction handling. D-56's reservation stands: 0 added lines contain
  `client.query`, `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`, or any pool/client lifecycle call.
  F-A is still unfixed and this change does not claim otherwise.
- Did **not** apply any migration, and did **not** run anything against production. `DATABASE_URL`
  was unset in my shell; the throwaway cluster was `initdb`-ed into the scratchpad, listened on
  `127.0.0.1:55461` with trust auth and no credential, and was stopped at the end.
- Did **not** touch asset data (I14), any registry row, `asset_registry`, `asset_throughput`, or
  any asset (I13 — no rung is open).
- Did **not** add any file to the repo other than this report. The harness, the probe `.sql` files
  and the temp packages live in the session scratchpad.
- Did **not** change the two tests' file structure or any of M0-T52's 8 assertions.
- Did **not** certify this work (I16/H7). PARĪKṢAKA decides.

## 9 — What I am unsure about, and what I could not prove

1. **D-62 part 4's pin still stands and I did nothing to retire it: the listener has never been
   seen working in a real deploy.** Everything above ran on my machine — a throwaway cluster, a
   YAML-extracted step body under local `bash`, local `grep`. Seven simulated scenarios plus two
   real local runs are not a deploy. The first production evidence will still be a real apply of a
   self-transacting file showing F-A's 25001/25P01 pair in a real Actions log, and no agent may
   write otherwise on the strength of this report.
2. **The escape is not injective, deliberately.** I escape `\n`/`\r` but not `\` itself, so server
   text containing the two literal characters `\` `n` renders identically to an escaped newline. A
   reader cannot always tell which it was. I judged that acceptable — neither form can create a
   line boundary, so the security property is unaffected, and escaping backslashes would have
   doubled every backslash in legitimate text for a purely cosmetic gain, beyond what D-65 grants.
   It is a disclosed ambiguity, not an oversight.
3. **I escaped `code` and `severity` as well as the four fields D-65 names.** Both are inside
   `formatServerNotice` and both were live injection points (§3a), so I read this as inside the
   grant rather than beyond it — but D-65 lists four field names and I changed six, and that is
   ADHIKĀRIN's to confirm, not mine.
4. **GNU grep is still untested, same as T57's item 4.** My `^\[migrate\] MIGRATE_RUNNER_COMPLETE`
   runs used macOS BSD `grep`; `ubuntu-latest` runs GNU grep. The pattern is unchanged by me — I
   only fed it different bytes — but the portability gap T57 disclosed is not closed by this task.
5. **`silent_zero` is the one fixture no real runner produced.** It is the counterfactual the gate
   exists to catch, so it cannot be captured from a real run; it is a stub, and it behaves
   identically before and after.
6. **Whether the one-long-line rendering is the right readability trade** is a judgement (§5). If
   an operator later prefers indented continuation lines, that is a different design — and note it
   would reopen exactly this hole unless the continuation prefix is one no grep anchors on.
7. **My two mutations are not a proof of test completeness.** They show the new tests fail when the
   fix is removed and when it is half-applied. There will be mutations they do not catch.
