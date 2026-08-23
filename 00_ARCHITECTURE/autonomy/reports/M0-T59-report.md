# KĀRAKA-M0-T59 — report (observation, not verdict)

- **Task:** `M0-T59` / Standing Queue `SQ-23` / ADHIKĀRIN `D-49` / from M0-T50's self-flagged loose end
- **Branch:** `campaign/nirmana-autonomous`
- **I16/H7:** I do not certify this work. Everything below is an observation with the command that produced it.

## 1 — What I wrote

**One file changed: `platform/scripts/audit/A3_env_matrix.md`** (+209 lines, no deletions).

1. **Frontmatter:** added an `addenda:` list entry (date, by, what). I deliberately did **not**
   change `status: COMPLETE`, `executed_at: 2026-04-28`, `executor` or `verdict` — those describe
   the April 2026 audit, and flipping them would be a false claim that the audit was re-run.
   Findings A3.1–A3.3 and every existing matrix row are untouched.
2. **Matrix row** for `IMPORT_ONLY`, inserted alphabetically between `GOOGLE_GENERATIVE_AI_API_KEY`
   and `INSTANCE_CONNECTION_NAME`, marking `.env.example` / `.env.local` / prod as
   **"must stay absent"** rather than merely "❌", because for this variable absence is the contract,
   not a gap.
3. **`# Addendum A3.4 — IMPORT_ONLY`**, seven sections:
   - **A3.4.1 What it is** — semantics table: `'1'` = do not run the CLI; *anything else, including
     unset, `''`, `'0'`, `'true'`* = RUN; strict `!== '1'` comparison, no coercion, no shared helper.
   - **A3.4.2 What sets it / what reads it** — the measured enumeration below, with both searches shown.
   - **A3.4.3 Why an explicit opt-out and not `NODE_ENV`** — the `V-28` reproduction, the three
     `ci.yml` jobs, and **M0-T50's asymmetry argument as a four-row table** (mutating script's hazard
     is *running* → default DO NOT RUN → `isDirectEntrypoint`; a gate's hazard is *failing to run* →
     default RUN → `IMPORT_ONLY`; an entrypoint check is silent whenever the module is loaded
     indirectly, which re-keys the same silent-pass class onto the load path). Plus `V-36`'s six
     behavioural rows, including the one that matters most — an *earned* exit 0 (137 bytes) is
     distinguishable from a *silent* one (0 bytes).
   - **A3.4.4 Operator rules** — five, including "never set it in an environment", "clear it for
     child processes", "a third gate CLI uses this contract", and "a worker is not a gate".
   - **A3.4.5 The invariants, and which have a detector** — an explicit four-row §N.8 table
     (INV-1 none / INV-2 yes / INV-3 yes / INV-4 none), not a prose gloss.
   - **A3.4.6 Does any CI assert this matrix? No** — stated in the document itself, with the search.
   - **A3.4.7 The open question, recorded not resolved** — M0-T50's `vi.hoisted` doubt, verbatim in
     substance, plus what can be said without deciding it.

The reason the addendum is this long: SQ-23's premise is that the reasoning is the perishable part.
A one-line matrix row would have recorded the variable and lost the argument.

## 2 — Enumeration of current usage, with the search shown

```
$ git grep -l 'IMPORT_ONLY' -- .
00_ARCHITECTURE/autonomy/state/CAMPAIGN_STATE.json      ← campaign bookkeeping
00_ARCHITECTURE/autonomy/state/DECISIONS.jsonl          ← "
00_ARCHITECTURE/autonomy/state/DIGEST-2026-08-23.md     ← "
00_ARCHITECTURE/autonomy/state/HEARTBEAT.jsonl          ← "
00_ARCHITECTURE/autonomy/state/STANDING_QUEUE.jsonl     ← "
00_ARCHITECTURE/autonomy/state/VERDICTS.jsonl           ← "
00_ARCHITECTURE/autonomy/state/WORK_QUEUE.jsonl         ← "
00_ARCHITECTURE/control/nirmana_tracker.html            ← "
platform/scripts/__tests__/dispatch_gate.test.ts              ← SETTER
platform/scripts/__tests__/verify_migrations_deployed.test.ts ← SETTER
platform/scripts/ci/dispatch_gate.ts                          ← READER
platform/scripts/ci/verify_migrations_deployed.ts             ← READER
```

Line level (`git grep -n 'IMPORT_ONLY' -- platform/ .github/`), each verified against source with
`awk 'NR==<n>'` rather than trusted from the grep:

| Role | Site | Content |
|---|---|---|
| READER | `platform/scripts/ci/dispatch_gate.ts:193` | `if (process.env.IMPORT_ONLY !== '1') {` |
| READER | `platform/scripts/ci/verify_migrations_deployed.ts:252` | `if (process.env.IMPORT_ONLY !== '1') {` |
| SETTER | `platform/scripts/__tests__/dispatch_gate.test.ts:12–14` | `vi.hoisted(() => { process.env.IMPORT_ONLY = '1' })` |
| SETTER | `platform/scripts/__tests__/verify_migrations_deployed.test.ts:33–35` | same |
| CLEARER | `dispatch_gate.test.ts:249` | `runGate({ NODE_ENV: 'test', IMPORT_ONLY: '' })` |
| CLEARER | `verify_migrations_deployed.test.ts:279`, `:327` | `IMPORT_ONLY: ''` in the child env |

The task brief predicted "both test files set it via `vi.hoisted`" and named the two changed
scripts. **That prediction is exactly right and I found nothing beyond it.** I checked for a fourth
surface two ways so the "nothing else" is a boundary rather than an artefact of where I looked:

```
$ grep -rln 'IMPORT_ONLY' --include='.env*' --include='*.yml' --include='*.yaml' --include='*.tf' \
    --exclude-dir=node_modules --exclude-dir=.clone --exclude-dir=worktrees .
(no matches)

$ grep -rn 'IMPORT_ONLY' --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
    platform/ .github/ | grep -v <the four known files>
(no matches — i.e. untracked/ignored files too, not just tracked ones)
```

**No usage nobody has mentioned. Zero occurrences in `.github/`, in any `.env*`, or in Terraform.**
(Worktree copies under `.claude/worktrees/` and `.clone/worktrees/` were excluded deliberately —
they are stale checkouts of this same repo, not independent usage. I say so rather than silently
filtering.)

## 3 — Does a CI check read `A3_env_matrix.md`? No — and I looked before I wrote

This was the part of the brief I treated as the real question, since writing an undetected
convention *about* an undetected convention was the named failure mode.

```
$ grep -rn 'A3_env_matrix' <repo, worktrees excluded>
platform/scripts/audit/.audit_state.json          ← records A.3 COMPLETE, points at this file as its report
platform/scripts/audit/MASTER_AUDIT_REPORT.md     ← prose, "Created A1…A4"
99_ARCHIVE/BRIEFS_RETIRED/MASTER_AUDIT_BRIEF_v1_0.md, …/MACRO_PLAN_SYSTEM_AUDIT_v1_0.md  ← archived briefs
00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/STATE_D-3.md:217  ← one prose mention
00_ARCHITECTURE/autonomy/state/*, 00_ARCHITECTURE/control/nirmana_tracker.html ← this campaign

$ grep -n 'A3_env_matrix\|scripts/audit' 00_ARCHITECTURE/CAPABILITY_MANIFEST.json   → nothing
$ git grep -ln "audit/A1_\|audit/A3_" -- '*.ts' '*.py' '*.yml' '*.sh'               → nothing
$ grep -rn 'env_matrix\|env matrix' .github/ platform/scripts/ci/ platform/scripts/governance/ → nothing
```

**Nothing reads it.** No workflow, no script, no test, no governance tool, and it is not in
`CAPABILITY_MANIFEST.json`, so `drift_detector.py` / `schema_validator.py` do not cover it either.

**What I did about it:** I said so, in the document, in its own section (§A3.4.6), in the sentence
"appending here buys documentation, not enforcement", and again in the §A3.4.5 invariant table as
`INV-4 — detector: NONE`. I did **not** build a CI check. That is `V-36` finding **F-I**'s
recommendation (a greppable assertion that no workflow sets `IMPORT_ONLY`), it is not in SQ-23 —
whose own text says "if nothing does, say so" — and a guard I wrote and then documented as its own
detector would need PARĪKṢAKA to verify it detects anything (I16). Routed to the conductor as an
ask for a Standing Queue item.

## 4 — What I verified myself rather than copying from V-36 or the commit message

| Claim in the doc | How I checked it |
|---|---|
| `ci.yml` sets job-level `NODE_ENV: test` on three jobs, lines 137/219/410 | `grep -n 'NODE_ENV: test' .github/workflows/ci.yml` → 137, 219, 410; job names read from source: **Unit Tests**, **DB Integration Tests (SAMĪKṢĀ…)**, **Planner Regression Gate** |
| Every line number cited in the addendum | `awk 'NR==<n>'` on each file. **One correction made:** I first wrote `verify_migrations_deployed.test.ts:32–34` for the `vi.hoisted` block; it is **33–35**. Fixed before commit. |
| The guard tests are really in CI's `npm test`, not just present on disk | `npx vitest list --project node scripts/__tests__/dispatch_gate.test.ts scripts/__tests__/verify_migrations_deployed.test.ts` → both entrypoint-guard cases listed. The `node` project in `platform/vitest.config.ts` declares no `include`, so vitest's default glob picks up `scripts/__tests__/`. `ci.yml`'s Unit Tests job runs `npm test`. |
| `ledger_writer_worker.ts:159` still carries the old form | `awk 'NR==159'` → `if (process.env.NODE_ENV !== 'test') {` |
| `dispatch_gate`'s `main()` is quiet with no `GATE_EVENT_NAME` | **Read from source, NOT executed** — `evaluateDispatchGate` returns `allowed: true, mode: 'not-a-dispatch'` when `eventName !== 'workflow_dispatch'`, and `main()` then only `console.log`s. Labelled as read-not-run in the doc too. |

## 5 — What I did NOT do

- **Did not touch the mechanism.** `dispatch_gate.ts`, `verify_migrations_deployed.ts` and both test
  files are byte-identical to their `V-36`-certified state. `git status` shows one changed non-state
  file. I also declined to add a back-pointer comment from the code to the new doc — it would be a
  harmless comment, but it would edit files a verdict already covers, and the boundary was explicit.
  Recommended as a follow-up instead.
- **Did not build the F-I CI guard.** See §3.
- **Did not resolve M0-T50's `vi.hoisted` question.** Recorded it in §A3.4.7 as open, gave my view
  as a view in the conductor finding, changed nothing.
- **Did not fix `ledger_writer_worker.ts:159`** (M0-T50's open finding, still live). Documented in
  the addendum's operator rule 5 so the new contract is not misapplied to a worker.
- **Did not touch** `.github/workflows/deploy.yml` (T57), `check_asset_catalogue_contract.py` (T56),
  `00_ARCHITECTURE/autonomy/reports/` (T58), any asset data, registry row, migration, or `main`.
- **Did not run** any DB-touching command, any build, or the vitest suite itself (only `vitest list`,
  which collects without executing).

## 6 — What I am unsure about, plainly

1. **Whether `A3_env_matrix.md` is the right home at all.** SQ-23 named it, so I used it, but it is a
   closed April-2026 audit report — `status: COMPLETE`, a point-in-time verdict, no validator — and
   appending a live 2026-08 contract to it is slightly against its grain. I handled this by adding an
   `addenda` frontmatter entry and leaving `status`/`verdict` alone, and by saying inside the document
   that it buys no enforcement. If ADHIKĀRIN would rather this live in a living surface (e.g. a
   `CAPABILITY_MANIFEST.json`-registered doc, or `ONGOING_HYGIENE_POLICIES`), the text moves as-is.
   **I did not decide that question; I followed the queue item literally and am flagging the tension.**
2. **My §A3.4.7 view against a vitest config-level `env` is reasoning, not measurement.** I did not
   try the config-level variant and observe what it does to spawned children. The argument reads
   sound to me (it would make "silenced" the ambient default across the whole suite, which is the
   shape the `NODE_ENV` repair removed) but it is an argument.
3. **INV-3 is verified by collection, not by a green run.** `vitest list` proves the files are
   *selected* by the `node` project. It does not prove the four subprocess tests currently *pass* —
   I did not run them (they spawn `npx tsx` with 60s timeouts each). `V-36` ran the underlying gate
   behaviours directly and PASSed; I did not re-run those either.
4. **"No usage anywhere else" is scoped to this working tree at 2026-08-23T15:2x.** It excludes
   `.claude/worktrees/` and `.clone/worktrees/` copies by choice. Nothing sets it in CI *today*,
   which is exactly the short-shelf-life measurement F-I is about.
5. **I cannot tell whether the doc will be read.** That is the honest residue of the whole task:
   a document with no detector is better than a convention with no detector, and it is still not a
   detector. The addendum says so about itself rather than implying otherwise, which is the most I
   can do inside this scope.

## 7 — Files touched

| Path | Change |
|---|---|
| `platform/scripts/audit/A3_env_matrix.md` | +209 lines — frontmatter `addenda`, one matrix row, Addendum A3.4 |
| `00_ARCHITECTURE/autonomy/state/WORK_QUEUE.jsonl` | one appended completion line, id `M0-T59` |
| `00_ARCHITECTURE/autonomy/mailbox/to_conductor/20260823T153028Z-M0-T59-import-only-contract-has-no-detector.md` | the finding |
| `00_ARCHITECTURE/autonomy/mailbox/to_verifier/` (this file) | the report |
| `00_ARCHITECTURE/autonomy/state/HEARTBEAT.jsonl` | heartbeats |

Committed with `git commit --only <explicit paths>`, never a directory.
