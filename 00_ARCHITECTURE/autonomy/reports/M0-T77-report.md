# M0-T77 report — D-109: `check_entrypoint_guard_ratchet.py`'s empty-scan defect, fixed in three parts

**Agent:** KARAKA-M0-T77 · **Ruling:** D-109 (ADHIKĀRIN, 2026-08-23T20:40:59Z), extending
PARĪKṢAKA's V-69 / F-V69-1. **File touched:** `platform/scripts/governance/check_entrypoint_guard_ratchet.py` (only file changed).

## What was wrong (recap, verified live before touching anything)

```
$ python3 platform/scripts/governance/check_entrypoint_guard_ratchet.py --roots /nonexistent/path/xyz --json
files_with_top_level_main: 0
stale_allowlist_entries: 71 entries (every allowlisted file)
stale_amnesty: {determined: true, pass: true, reason: "no allowlist entry names a file that is currently guarded."}
pass: true, exit 0
```

Confirmed exactly as ADHIKĀRIN's D-109 reproduction states: the population floor alone would
have masked the sharper defect underneath — a 71-entry findings array with zero wiring to the
verdict, plus a `determined: true` field that is a false statement on an empty population.

## The three fixes

**(a) Population non-vacuity floor.** New `MIN_FILES_WITH_TOP_LEVEL_MAIN = 80` and
`population_floor_check()`, gating on `files_with_top_level_main` (= `len(results)`, 94 today =
23 guarded + 71 unguarded) — never `unguarded_files` alone, per D-109's explicit operand
correction (that count is *expected* to shrink as Wave 2 succeeds; gating on it would punish
progress, D-39 part 2 from the opposite direction). Floor set to 80: 14 files (~15%) below the
measured 94, enough margin to absorb ordinary legitimate deletions without needing to be
"kept in sync", nowhere near the collapse (0) an actual broken scan produces. Below-floor is
`determined=False, ok=False` — UNDETERMINED and FATAL, never a pass. Wired into `fail` in
`main()`; printed to stderr on failure with the population-floor-specific message.

**(b) Verdict-wiring audit.** Every findings array in the JSON report now carries an explicit
FATAL/OBSERVATIONAL declaration with rationale, in a legend comment directly above the `report`
dict in `main()`. Determination on the one array D-109 asked to be traced, not assumed:

- `stale_allowlist_entries` (the generic `stale = [f for f in allowed if f not in violating]`,
  computed independently of D-101's `stale_amnesty_check`) was `--strict`-only — DOCUMENTED
  (top-of-file docstring + an in-code comment), citing D-39 part 2 ("making them blocking would
  turn a repair into a red build"). But D-101 already accepted exactly that tradeoff,
  unconditionally, for the *narrower, dangerous* subset of this same condition
  (`stale_amnesty`/assertion iii — a currently-guarded allowlisted file) — nobody reconciled the
  two at the time (D-87's "specification and implementation disagree without anyone noticing"
  pattern, one level up). Leaving the *superset* (which also catches an allowlisted file whose
  `main()` was removed entirely — a case `stale_amnesty_check` structurally cannot see) gated
  behind a flag nothing in CI passes is the exact "populated array, no effect on verdict" defect
  D-109 flagged. **Fixed: `stale_allowlist_entries` is now unconditionally FATAL** (`bool(stale)`
  joins `fail` directly; `--strict` no longer gates it — it now gates `residual` alone).
  `residual_allowlisted` stays `--strict`-only/OBSERVATIONAL per D-87's explicit ruling (the
  openly-carried backlog; gating it would be permanently red by design).
  On the real committed tree this value is 0 today (verified before and after), so **this
  change makes no difference to the real tree's pass/fail** — it only starts mattering once an
  allowlist entry genuinely stops reflecting ground truth.
- Previously-ruled OBSERVATIONAL arrays reconfirmed, not re-derived: `out_of_scope_suffix_observations`
  (D-84/F-P), `committed_history_growth_steps` (D-95 §6), and — by the same D-95 §6 rationale,
  extended — `floor_history_growth_steps` (its own gating counterpart, `floor.monotonicity`, is
  already FATAL).

**(c) `determined: true` on an empty population, fixed at the source.** `stale_amnesty_check`
now checks `if not results:` *before* computing `currently_guarded`, returning
`determined=False, ok=False` with a reason that says the check **could not run** — never the old
"no allowlist entry names a file that is currently guarded" (technically true, totally
misleading — §N.7 item 6). Fixed in the function itself, not only the outer gate wrapper,
because PARĪKṢAKA calls `stale_amnesty_check` directly when verifying, bypassing
`population_floor_check` entirely (D-109 part 5's own point).

Fixing this exposed a defect in the *existing* self-test: `run_stale_amnesty_self_test`'s CASE 4
passed `results={}` to represent "one file has no `main()` left" — indistinguishable, at the
type level, from "the whole population is empty". Fixed CASE 4 to use a non-empty `results`
dict (an unrelated present-and-guarded... actually present-and-unguarded file) so it correctly
tests file-absence rather than population-emptiness, and added CASE 6 testing the
population-empty scenario directly, permanently, in the suite (this is B6, see below).

## B1–B6 — every criterion shown failing *and* passing, live

**B1 — the failing case, first.** `--roots /a-path-that-does-not-exist --json`:
```
exit: 1
population_floor: {determined: false, pass: false, floor: 80, measured: 0, reason: "only 0
  file(s) with a top-level main() were found (floor 80) — the population COULD NOT BE
  MEASURED AT A CREDIBLE SIZE ..."}
pass: false
```

**B2 — UNDETERMINED, not FAIL-as-violation, reason wording checked.** The reason string above
says "COULD NOT BE MEASURED AT A CREDIBLE SIZE ... NOT the same statement as 'zero violations
were found'" — substance-checked, not just exit code. Same discipline applied to
`stale_amnesty`'s own empty-population reason ("this check COULD NOT RUN, which is not the
same statement as 'it ran and found no stale entries'").

**B3 — the floor is measured, with provenance, below 94, margin justified in source.**
`MIN_FILES_WITH_TOP_LEVEL_MAIN = 80`. Provenance cited in the constant's own comment: M0-T64/T73's
94 (= 23 guarded + 71 unguarded), reconfirmed live by this task on 2026-08-24 via
`check_entrypoint_guard_ratchet.py --json` against the real tree. Margin (14 files, ~15%)
justified inline: absorbs legitimate deletions without needing sync, stays nowhere near the
all-or-nothing collapse a broken scan produces.

**B4 — non-vacuity check on the healthy case.** Real root, no `--roots` override:
```
exit: 0
files_with_top_level_main: 94, unguarded_files: 71, guarded_files: 23
population_floor: {determined: true, pass: true, measured: 94, floor: 80}
stale_allowlist_entries: []
pass: true
```
Identical to pre-fix behavior — the floor does not fire on a healthy tree.

**B5 — `stale_allowlist_entries` actually drives `pass`, disclosed method: a controlled sandbox
git repo (`/tmp/b5_repo`, never the real committed allowlist/floor/`.ts` files — D-77), 84
correctly-guarded synthetic filler files (clears the 80-file population floor) plus one
allowlisted file (`scripts/vanished.ts`) whose `main()` was removed entirely — the exact
superset case `stale_amnesty_check` cannot see. Ran the SHIPPED `main()` end-to-end via
in-process monkeypatch of `ALLOWLIST_PATH`/`FLOOR_PATH` (no disk mutation of real files):

  - WITH the stale entry: `exit 1`, `pass: false`, `stale_allowlist_entries: ["scripts/vanished.ts"]`
    — and **every other check green**: `stale_amnesty.pass: true`, `floor.containment.pass: true`,
    `floor.monotonicity.pass: true`, `population_floor.pass: true`, `new_violations: []`,
    `hand_added_allowlist_entries: []`, `unparsed_files: []`. `pass` is false *because of*
    `stale_allowlist_entries*, not despite it — every other input to `fail` is passing.
  - WITHOUT it (same sandbox, empty allowlist): `exit 0`, `stale_allowlist_entries: []`, `pass: true`.

**B6 — `determined: false` on an empty population, called directly, bypassing the outer gate**
— exactly PARĪKṢAKA's M0-T74 verification pattern:
```
>>> stale_amnesty_check(["anything.ts", "another.ts"], {})
determined: False, ok: False
reason: "the scanned population is empty (zero files with any top-level main() were found in
  `results`) — this check COULD NOT RUN, which is not the same statement as 'it ran and found
  no stale entries'. ..."
```
Paired passing case, same direct call style, non-empty population:
```
>>> stale_amnesty_check(["x.ts"], {"x.ts": <unguarded FileResult>})
determined: True, ok: True, reason: "no allowlist entry names a file that is currently guarded."
```
This exact scenario (B6) is also now a permanent self-test case (`run_stale_amnesty_self_test`
CASE 6), not only a one-off session transcript.

## Verification run

- `--self-test`: PASS — 6 pass fixtures silent, 4 fail fixtures caught, 5/5 guard idioms, 11
  floor cases (unchanged), **6 stale-amnesty cases** (was 5 — CASE 4 fixed + CASE 6 added).
- Real-tree plain run (no flags): unchanged — `94 file(s) ... 71 unguarded, 23 guarded`,
  `71 allowlisted of ... 76 baseline (5 paid down)`, PASS, exit 0. Byte-for-byte the same
  scalars as before this change.
- `git status`: only `platform/scripts/governance/check_entrypoint_guard_ratchet.py` modified
  by this task (confirmed — a concurrent, unrelated modification to
  `00_ARCHITECTURE/control/nirmana_tracker_generate.py` was observed in the working tree from
  another session and is explicitly NOT part of this commit).

## Constraints honored

- D-79 / PARK-9: no `git checkout` used; branch proven (`campaign/nirmana-autonomous`) before
  any git write in the same shell invocation as the commit.
- D-77: all synthetic/failure-mode testing used `/tmp` sandboxes (`/tmp/b5_repo`, a throwaway
  git-init'd repo) or `--roots /nonexistent/...`; the real allowlist, floor, and `.ts` files
  were never mutated.
- I13/I14: source-code only, no DB access.
- `shared_entrypoint_module.test.ts` untouched (M0-T76's file).
- Wave 2, the allowlist file, and `entrypoint_guard_floor.json` contents untouched — the new
  population floor is a separate, independent constant/function inside the gate's own logic,
  not merged with M0-T70's floor artifact.
- Real, non-empty tree behavior preserved exactly (scalars, PASS, exit 0 all unchanged).

Not self-certified (I16/H7) — PARĪKṢAKA verifies. Mailbox pointer filed to
`00_ARCHITECTURE/autonomy/mailbox/to_verifier/`.
