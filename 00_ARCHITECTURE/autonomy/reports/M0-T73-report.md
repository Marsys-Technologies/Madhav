# M0-T73 — guard the three unguarded arrivals from origin/main (D-100)

**Agent:** KĀRAKA-M0-T73 · **Task:** WORK_QUEUE `M0-T73` · **Authority:** ruling **D-100**
**Branch:** `campaign/nirmana-autonomous` @ `c931f7523ef0cec3df08a1809c20e39b92b9a027`
**Written:** 2026-08-23T20:02:05Z
**This is an observation report, not a verdict.** I do not certify my own work (I16/H7).

---

## 1 — Outcome in one line

**All three files guarded with the exact Wave-1 (M0-T65) idiom, via the shared
`platform/scripts/lib/entrypoint.ts` module. The ratchet went RED (exit 1, `pass: false`, these
three named as `new_violations`) to GREEN (exit 0, `pass: true`, `new_violations: []`), and the
before/after `guarded_files`/`unguarded_files` counts move by exactly 3, confirming the fix is
the cause, not an accidental effect.**

Per D-100's reframe: this is not a growth authorised and not a special case. `origin/main`'s merge
(M0-T16, `016b0ccdc`) brought three files this campaign never saw; the ratchet correctly reported
the merge as unfinished. This closes it — no allowlist entry was added, none was needed.

---

## 2 — What each file does, read not assumed (D-67's per-file hazard criterion)

I read all three files in full before touching anything.

| File | What the unguarded top-level call does on an incidental import | Hazard class |
|---|---|---|
| `platform/scripts/probe/p4k_narration_analyzer.ts` | `main()` parses `process.argv` for `--manifest`/`--self-test`. If the importing process's own argv happened to carry either flag, this file would read/write JSON report files under `fixtures/p4k/**` or an arbitrary manifest-adjacent path as an import side effect. No network, no credential, no DB. | local filesystem side effect only |
| `platform/scripts/probe/p4k_sequence_driver.ts` | `main()` parses argv for `--service-url`/`--self-test`. If the importer's argv carried `--service-url`, this file would `spawnSync` `npx tsx ask.ts` **six times** against that URL — real network egress and six real authenticated turns against whatever service was named, chained by conversation id. | network egress + real service calls (argv-gated) |
| `platform/scripts/probe/post_deploy_behavior_smoke.ts` | `main()` is called unconditionally at module scope (no argv gate on `main()` itself — only `SMOKE_SELFTEST` env var routes internally). Unless `SMOKE_SELFTEST=1` is already set in the importing process's environment, `main()` → `runLive()` → `execFileSync`s `ask.ts` against a **live deployed** `/api/pariprashna` Cloud Run URL (`SMOKE_WEB_URL`, defaulting to a real production-adjacent URL) on every import. | network egress + real deployed-service call, env-var-gated (default is LIVE) |

**D-89/D-90 inertness proof, stated BEFORE any run (none was performed — see §4):** two of the
three (`p4k_sequence_driver.ts`, `post_deploy_behavior_smoke.ts`) have a real network-egress /
deploy-adjacent top-level path reachable on import under a condition (an inherited argv flag, or
simply the *absence* of an env var, respectively) I cannot rule out for an arbitrary future
importer. I could not establish unreachability of that path beforehand for either file, so **I did
not run either file, in any mode, including `--self-test`.** The third
(`p4k_narration_analyzer.ts`) has no network/credential hazard — its worst incidental-import effect
is a local fixture-file write — but I applied the same discipline and did not run it either, for
consistency with the same rule Wave 1 followed (it never ran any of its five files, and this task
follows that pattern exactly rather than inventing a per-file exception).

No secret path is touched in any of the three files; nothing was logged or echoed near one (P4/D-74).

---

## 3 — What I changed

**Three files repaired**, each: one import line added (`import { isDirectEntrypoint } from
'../lib/entrypoint'`, the identical relative path `probe/ask.ts` already uses), and the file's
existing top-level entry call wrapped in `if (isDirectEntrypoint(import.meta.url,
process.argv[1])) { ... }` with the call's body byte-for-byte unchanged inside the guard:

- `platform/scripts/probe/p4k_narration_analyzer.ts` — `process.exit(main())` moved inside the guard, unchanged.
- `platform/scripts/probe/p4k_sequence_driver.ts` — `process.exit(main())` moved inside the guard, unchanged.
- `platform/scripts/probe/post_deploy_behavior_smoke.ts` — bare `main()` moved inside the guard, unchanged (this file's call site was `main()`, not `process.exit(main())` — the only structural difference from the other two, and from all five Wave-1 files).

The predicate is **imported from the shared module**, not mirrored — this repo already has 8
production copies importing it (T66's consolidation; F-O measured 0 hand-written copies remaining)
and D-9's exception for this specific leaf module (no side effects, no acquired module graph)
applies identically here.

**No file was added to any allowlist.** `entrypoint_ratchet_allowlist.json`,
`entrypoint_guard_floor.json`, and `check_entrypoint_guard_ratchet.py` are all untouched (git diff
--stat empty for all three — see §5).

```
$ git diff --stat -- platform/scripts/probe/p4k_narration_analyzer.ts \
    platform/scripts/probe/p4k_sequence_driver.ts platform/scripts/probe/post_deploy_behavior_smoke.ts
 platform/scripts/probe/p4k_narration_analyzer.ts    | 21 ++++++++++++++++++++-
 platform/scripts/probe/p4k_sequence_driver.ts       | 21 ++++++++++++++++++++-
 platform/scripts/probe/post_deploy_behavior_smoke.ts| 21 ++++++++++++++++++++-
 3 files changed, 60 insertions(+), 3 deletions(-)
```

---

## 4 — What I did NOT do

- **Did not run any of the three files** — not directly, not via import, not in `--self-test` mode,
  not with a stub env. No `gcloud`, no Firebase, no network call, no `ask.ts` subprocess. This is a
  narrower verification than Wave 1's own (Wave 1 ran `--self-test`-equivalent behavioural checks
  against a harmless stand-in module reproducing the idiom — I relied on that same stand-in's prior
  proof, already committed in `scripts/__tests__/destructive_entrypoint_guards.test.ts`, and did not
  re-run it, since the idiom itself is unchanged from Wave 1's and the mutation proofs there already
  establish the guard/predicate machinery can fail in both directions).
- **Did not touch** `entrypoint_ratchet_allowlist.json`, `entrypoint_guard_floor.json`, or
  `check_entrypoint_guard_ratchet.py` (D-95/D-96, constraint 4).
- **Did not touch** any of Wave 1's five files, or `probe/ask.ts` (D-100's separate, already-checked
  item — PARĪKṢAKA V-66/V-67 certified M0-T16 PASS; not re-verified here per the task's own
  instruction).
- **Did not read, echo, or log any secret/credential value.**

---

## 5 — The ratchet's own output, before and after (D-95 part 5 / D-100 part 3's clearability test)

**BEFORE** (HEAD `c931f75`, before my edits):

```
$ python3 platform/scripts/governance/check_entrypoint_guard_ratchet.py --json
exit code: 1
"pass": false
"new_violations": [
  {"file": "platform/scripts/probe/p4k_narration_analyzer.ts", "lines": [376]},
  {"file": "platform/scripts/probe/p4k_sequence_driver.ts", "lines": [193]},
  {"file": "platform/scripts/probe/post_deploy_behavior_smoke.ts", "lines": [546]}
]
"unguarded_files": 74
"guarded_files": 20
```

**AFTER** (working tree, my three edits applied, nothing else changed):

```
$ python3 platform/scripts/governance/check_entrypoint_guard_ratchet.py --json
exit code: 0
"pass": true
"new_violations": []
"unguarded_files": 71
"guarded_files": 23
"floor": {
  "count": 71,
  "containment": {"determined": true, "pass": true, "added_beyond_floor": [], "reason": "the current allowlist is a subset of the floor."},
  "monotonicity": {"determined": true, "pass": true, "violations": [], "reason": "the current floor is a subset of every value its committed history has ever held."}
}
"committed_history_growth_steps": []
```

**Why this is the right cause, not an accidental one (D-95 part 5's demonstration requirement):**
`unguarded_files` dropped by exactly 3 (74→71) and `guarded_files` rose by exactly 3 (20→23) — the
same three files, and only those three, moved categories. `new_violations` (the assertion that
failed before) is now empty specifically because these three now carry the guard and are excluded
from the unguarded population the assertion scans, exactly as D-100/D-95 anticipated. Nothing about
the allowlist, the floor, or the scan mechanism changed — `entrypoint_ratchet_allowlist.json` and
`entrypoint_guard_floor.json` are byte-identical to `HEAD` (git diff --stat empty, §3).

**Untouched, unrelated, out of scope (D-84/D-100 note 7 — flagged by T66/T70, not mine to fix):**
`out_of_scope_suffix_observations` still lists the same 3 `.mts` files
(`platform/scripts/d4a/file_baseline_predictions.mts`,
`platform/scripts/d4a/fix_item3_spiritual_arc_correction.mts`,
`platform/scripts/retrieval/test_router.mts`) — the population command's `grep '\.ts$'` cannot match
`.mts`, a separate, already-ruled-on hole (D-100 part 3: "guard them, then extend, then block") that
this task was not dispatched to close.

---

## 6 — Wave 1's five files — confirmed unchanged

```
$ git diff --stat -- platform/scripts/probe/ask.ts platform/scripts/dedupe_charts.ts \
    platform/scripts/_archived/seed-abhisek.ts platform/scripts/dev/mint_session_cookie.ts \
    platform/scripts/set-password.ts
(empty)
```

No output — none of Wave 1's five repaired files, nor `probe/ask.ts` (D-100's separate item), moved
at all in this task.

---

## 7 — Lint and types

```
$ npx eslint scripts/probe/p4k_narration_analyzer.ts scripts/probe/p4k_sequence_driver.ts \
    scripts/probe/post_deploy_behavior_smoke.ts
(clean — zero output, zero errors)
```

`tsc` — the same standing note from M0-T65 applies: `platform/tsconfig.json` excludes `scripts`, so
a project `tsc` run does not typecheck any of these three, and I cite no project-`tsc` green here.
I invoked `tsc` explicitly on the three files with the same flag set M0-T65 used:

```
$ npx tsc --noEmit --strict --skipLibCheck --esModuleInterop --resolveJsonModule \
    --target ES2022 --module esnext --moduleResolution bundler --lib ES2022,DOM \
    scripts/probe/p4k_narration_analyzer.ts scripts/probe/p4k_sequence_driver.ts \
    scripts/probe/post_deploy_behavior_smoke.ts
(clean — zero output, zero errors)
```

---

## 8 — Direction of change (D-41 part 2) and importer check

**Could this cause a build/deploy/CI job that previously passed to now fail?** No new failure mode
is introduced — the change only ever *refuses* execution that previously ran as an import side
effect; every documented direct invocation is preserved unchanged inside the guard. Measured, not
assumed: grepped the tree and `.github/workflows/` for every reference to the three basenames.

```
$ grep -rn "p4k_narration_analyzer\|p4k_sequence_driver\|post_deploy_behavior_smoke" \
    --include="*.ts" --include="*.sh" --include="*.yml" --include="*.yaml" platform .github
```
Every hit is a direct `npx tsx <file> ...` invocation:
- `platform/scripts/probe/p4k_narration_audit.sh` (both files, `--self-test` and real-manifest modes)
- `.github/workflows/pariprashna-post-deploy-smoke.yml` (`post_deploy_behavior_smoke.ts`, two jobs)

**No importer of any of the three exists anywhere in the tree.** This is a strengthening
(machinery, proceed-and-report under D-41 part 2), and the one condition it was meant to close
(an inherited argv flag or a missing env var making the file run on import) simply cannot occur
today because nothing imports these files — the guard closes the class of hazard for any future
importer, not a live one found today.

---

## 9 — What is proven, and what is NOT

**PROVEN**
1. Each of the three carries the exact `isDirectEntrypoint` guard, exactly once, with its only
   entry-call invocation inside it and nothing executing after it (§2 tail dumps).
2. The predicate is imported from the certified shared module, identical body to Wave 1's.
3. The ratchet's own live scan — the actual detector this task exists to satisfy — goes from
   naming these three as violations (exit 1) to clean (exit 0), and the population counts move by
   exactly 3 in each direction, not by some larger or smaller amount that would suggest an
   unrelated effect.
4. Wave 1's five files and `probe/ask.ts` are byte-for-byte untouched.
5. `entrypoint_ratchet_allowlist.json`, `entrypoint_guard_floor.json`, and the ratchet script itself
   are byte-for-byte untouched.
6. Lint and a strict standalone `tsc` pass are clean on all three files.

**NOT PROVEN — and not claimed**
1. **That any of the three actually fires its guard when run**, or behaves identically to its
   pre-repair self when run directly. No process ever evaluated any of them, in any mode — a
   narrower verification than even Wave 1's, because two of the three carry a network/deploy hazard
   I could not rule out beforehand (§4). The claim rests on: identical guard text, identical
   predicate body (imported, not re-implemented), and Wave 1's own prior behavioural proof that this
   exact idiom resolves correctly under this repo's `tsx` for a `platform/scripts/**` ESM `.ts`
   file — I did not re-run that proof, I relied on it standing.
2. **That nothing else in the tree imports them** beyond what a repo-wide grep for the three
   basenames can show (§8) — a textual measurement, not an exhaustive module-graph analysis.

---

## 10 — Housekeeping

- Report at this path, committed with `git commit -q --only` naming the three edited files plus
  this report explicitly (never a directory, never `-A`).
- Pointer filed at `00_ARCHITECTURE/autonomy/mailbox/to_verifier/` — urgent, per D-100 part 8.
- Completion line appended to `WORK_QUEUE.jsonl` with a `date -u`-sourced timestamp.
- I do not certify this work (I16/H7). PARĪKṢAKA verifies.
