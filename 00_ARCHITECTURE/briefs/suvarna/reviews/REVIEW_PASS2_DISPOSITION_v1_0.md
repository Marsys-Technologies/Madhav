---
artifact: SUVARNA_REVIEW_PASS2_DISPOSITION
canonical_id: SUVARNA_REVIEW_PASS2_DISPOSITION
version: "1.1"
status: "DONE — the disposition of every review-pass-2 finding in the v1.4 plan set"
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
inputs:
  - briefs/suvarna/reviews/REVIEW_PASS2_SUBSTANCE_v1_0.md (30 findings, prefix S)
  - briefs/suvarna/reviews/REVIEW_PASS2_CONSISTENCY_v1_0.md (40 findings, prefix C)
  - briefs/suvarna/reviews/REVIEW_PASS1_DISPOSITION_v1_0.md; $SUVARNA_HOME/run/DECISIONS.jsonl (latest line per id)
changelog:
  - "1.1 (2026-09-30): §6 pass-3 follow-up added (which pass-2 fixes review pass 3 found not done or partial, and where each now lives). No pass-2 row re-graded in place."
  - "1.0 (2026-09-29): first disposition, with plan set v1.4."
---

# Review pass 2 — disposition

**Dispositions.** FIXED: changed in the v1.4 set now. ALREADY FIXED: fixed before this pass. SUPERSEDED: a decision
changed the premise. DEFERRED→item: the work is a named plan-model item. CODE→spec: the remaining work is tracker code
under `platform/scripts/governance/suvarna_tracker/`, specified in §3 for the code agent (not edited here).
NATIVE→decision: needs a native ruling, prepared in plan §8. Each finding is counted once, by where its substantive
risk now sits; many FIXED rows also carry a CODE spec, named in the note.

**Scope of this revision.** Plan v1.4 (new file; v1.3 marked SUPERSEDED), charter v1.4, architecture v1.4, runbook
v1.2, L3 focus families v1.3, document map v1.2, D6 runbook v1.3, Track E and Track A briefs v1.1, all ten role files
v1.2, both start prompts v1.2, the three family prompts v1.2, the correction notice v1.1, `runtime/INTERIM_RUNTIME_v1_0.md`
v1.1 (L.15's document, aligned to the settings-file location), the review package marked STALE, and
`plan_model.json`. Nothing committed; no database write (the cascade and the level map were measured
read-only as `suvarna_reader`); no event or decision was emitted.

**Measured for this pass (2026-09-29, read-only).** Eight `ON DELETE CASCADE` foreign keys into
`bodha_msr_signals(signal_id)`: from `kala_convergence`, `kala_darshana`, `kala_bhavishya`, `kala_activation`,
`kala_obstruction`, `bodha_signal_embeddings`, `bodha_contradictions` (×2). Seven writers target
`bodha_msr_signals`: two in W0 (`bo_sudarshana` 1, `bo_vargottama_dhana` 2), three in W1, two in W2. L0 by level:
24/11/4/1 (`bg_concordance` at 3). All 26 decision lines are written by `strategic-suvarna`.

## 1 · Counts

| | FIXED | ALREADY FIXED | SUPERSEDED | DEFERRED | CODE | NATIVE | Total |
|---|---|---|---|---|---|---|---|
| Substance (S) | 25 | 0 | 0 | 2 | 2 | 1 | 30 |
| Consistency (C) | 30 | 0 | 0 | 2 | 7 | 1 | 40 |
| **Total** | **55** | **0** | **0** | **4** | **9** | **2** | **70** |

## 2 · Findings

### Substance (REVIEW_PASS2_SUBSTANCE_v1_0.md)

| # | Sev | Disposition | Where | Note |
|---|---|---|---|---|
| S1 | BLOCKER | NATIVE→N-25 | arch §2.4; charter §13, P1, P13, R7, R10; plan §3.8, §5.0b, §8; runbook §2 step 2a; plan_model L.16d, L.16a, L.16g, L.16b → FI-7 | Separate macOS user, Suvarṇa settings file with explicit denies and hold-guard hook, own GitHub identity, branch protection, decisions log read-only to the swarm; what launch needs either way. CODE-11, CODE-12 |
| S2 | BLOCKER | FIXED | charter §2, §7.5, P14; arch §12.10, §11.3; ROLE_STEWARD step 4; ROLE_COMMON §1, §5; both start prompts' scopes | Only Strategic Suvarṇa, native present, writes the log; the Steward carries answers. OS-level protection is N-25. CODE-13, CODE-14 |
| S3 | BLOCKER | FIXED | plan §1.2, §4.2 G2, §5.3, §5.4 table, §8 F-3; charter R1, §6.6; arch §6.4, §12.9; families §4, §6, §7; plan_model F3.FK → B.W0, B.W1, B.W2, B.U, B.FS | Cascade set measured; F-3 = cascade removed on all eight keys; G2 waits for F-3 **and** the applied change, accepted explicitly. CODE-9 |
| S4 | BLOCKER | FIXED | plan §1.2, §5.2, §8; Track A §1, §9; plan_model A.L1a–A.L5a (N-10.Lx.i), G3.Lx (N-10.Lx.c), I.W* | Instance accepted after revalidation, before the layer's waves; the banner lifts there |
| S5 | BLOCKER | FIXED | plan_model E4.1, E4.3, J1.6; plan §4.2 row 10, §5.1 E4 | E4.1 without ledgers; E4.3 detects the ledgers on `main`; E4.3 a J1 input |
| S6 | BLOCKER | FIXED | arch §12.2; ROLE_COMMON §2; ROLE_CONDUCTOR step 8; Engine prompt "Where"; plan §5.1; Track E §2 | One rule: lanes from `suvarna/trunk`; source branches read or cherry-picked |
| S7 | BLOCKER | FIXED | charter §6.4; ROLE_BUILD_OPERATOR check 4; arch §6.2, §11.7; plan §4.2 row 9, §6.4, §5.1 E5.3 | Ancestry plus writer hashes at the running commit. CODE-1 (see C5) |
| S8 | MAJOR | FIXED | plan §1.1, §5.1 E6.3/E6.3t, §5.4 L5 row; plan_model E6.3t → J1.6, B.N14 → B.W0; arch §11.6 | Proxy reads unknown; exact function honours terminal dispositions; `lel_events` ruled before W0 (N-14.R236). CODE-8 |
| S9 | MAJOR | CODE→CODE-2, CODE-4 | Track E §8 (FAMILY_ASSETS keys, registry-coverage schema) | (a) path fixed in docs to `00_ARCHITECTURE/control/FAMILY_ASSETS.json`; (b) head-ref resolution; (c) schemas pinned |
| S10 | MAJOR | CODE→CODE-5, CODE-6, CODE-7 | plan §4.2 rows 1, 5, 6, 12; plan_model E1.7, E4.2/E4.2r, J1.R; Track E §5, §8 | (d) FIXED: E4.2 now detects the merged test file; R244 state moved to E4.2r |
| S11 | MAJOR | FIXED | plan §2.1, §5.1 E6.5, §4.2 row 12; Track E §8 | "Required, per-asset detector pending": NO_DETECTOR cells block ELEVATED; counts as covered; post-J1 registry changes by native-approved revision |
| S12 | MAJOR | FIXED | plan_model I.W0–I.W5 replace I.L0–I.L5, I.L3t; B.WnM depend on them; plan §5.4 step 4 | Fix items derived from the level map, any layer |
| S13 | MAJOR | FIXED | arch §12.7; ROLE_SCRIBE; ROLE_CONDUCTOR step 4; Engine prompt; plan_model L.17, E4.3 | Fold lanes pushed as fast-forwards to `campaign/nikasha-test`; tracker reads `origin/campaign/nikasha-test`; register in the E4.3 equality; Strategic owns the re-point. CODE-17 |
| S14 | MAJOR | FIXED | arch §2.1, §12.12; runbook §1, §2 step 7; ROLE_COMMON §5; ROLE_MONITOR; prompts; plan_model L.17 | Tracker and Monitor run from committed code in hq; Strategic restarts them after each merge |
| S15 | MAJOR | FIXED | charter G11; arch §2.1, §12.2; plan §6.4; ROLE_CONDUCTOR step 5 | Landing branches cut from `origin/main`; main merged into trunk every pass (charter change confirmed with N-1) |
| S16 | MAJOR | FIXED | plan_model FI-8 (detector) → FI-7; plan §5.0; notice v1.1 | Acknowledgement notes close FI-8. CODE-10 |
| S17 | MAJOR | FIXED | plan §4 diagram, §5.0b, §5.4 steps 1–2; Exec prompt §2; Track A §10; plan_model I.W* ← J1.0 | Track I starts at N-24, tier-independent designs to trunk only |
| S18 | MAJOR | FIXED | plan §6.7; arch §5.5; ROLE_CONDUCTOR inputs, steps 8, 11; runbook §2 | `/loop 10m`; snapshot plus event tail from a committed offset; lane launcher. CODE-18, CODE-19 |
| S19 | MAJOR | DEFERRED→E1.9 | plan §5.1 E1; Track E §5; plan_model E1.9 → J1.6 | `--assets` for census and emit, before J1 |
| S20 | MAJOR | FIXED | plan §3.7, §7, App. A, §5.0b; plan_model E3.3, L.12, L.12r → L.9 | Facts corrected (10 commits; 1094–1096); package marked stale, rebuilt by L.12r; renumbering is N-26 (C23) |
| S21 | MAJOR | FIXED | plan_model J1.1a–J1.3; plan §8 N-4, §6.6 | Agendas approved together; re-seals ordered |
| S22 | MAJOR | FIXED | plan §4.2 row 3, §5.1 E3; Track E §3.2 E3.6 | R39 closes on the census's Build checks in the scorecard |
| S23 | MAJOR | DEFERRED→E5.6, E5.7 | plan §4.2 row 15, §5.1 E5; Track E §7; plan_model E5.6, E5.7 → J1.6, E5.7 → B.L0.0 | Rehearsal off production; L0 dump as the reader; the serving canary is in E5.3 now |
| S24 | MAJOR | FIXED | plan §5.4 table, §6.4b, §6.6; runbook §7; ROLE_BUILD_OPERATOR; plan_model B.L0.0–B.L0.3 | Four native dispatches, batched |
| S25 | MINOR | FIXED | plan_model A.L0v → J1.5; plan §4.2 row 8 | |
| S26 | MINOR | FIXED | charter G16; plan §8 N-1 | G16 decided with N-1 |
| S27 | MINOR | FIXED | plan_model F1.G/S/K (SEAL-G/S/K); family prompts v1.2; notice | |
| S28 | MINOR | FIXED | ROLE_SCRIBE step 3; arch §12.7 | No ledger emit before E5.2 |
| S29 | MINOR | FIXED | plan_model B.U | Depends on B.W2M, F3.LOCK, F3.FK |
| S30 | MINOR | FIXED | plan_model J1.0d → J1.0; plan §5.0b | Drafted after A.L0 |

### Consistency (REVIEW_PASS2_CONSISTENCY_v1_0.md)

| # | Sev | Disposition | Where | Note |
|---|---|---|---|---|
| C1 | BLOCKER | FIXED | as S6; plan §5.1 E4; charter G6 | Split built fresh; #2736 left for the native to close |
| C2 | BLOCKER | FIXED | as S13 (option A) | CODE-17 |
| C3 | BLOCKER | FIXED | plan §5.1 E7.1–E7.3; arch §8; Track E §8; runbook §6, §7; ROLE_MONITOR | `builder_scope` read from the authenticated preflight, compared with the provisioning record. CODE-15 |
| C4 | BLOCKER | FIXED | as S5 | |
| C5 | MAJOR | CODE→CODE-1 | docs fixed under S7 | |
| C6 | MAJOR | CODE→CODE-1 | Track E §8 pins the interface | Absolute path, no `--json`, keys `job_sha`, `deployed_sha`, `builder` |
| C7 | MAJOR | CODE→CODE-4 | docs keep `00_ARCHITECTURE/control/FAMILY_ASSETS.json` | |
| C8 | MAJOR | CODE→CODE-5 | Track E §8; arch §11.7; plan §5.1 E6.5 | |
| C9 | MAJOR | CODE→CODE-2 | Track E §3.2; plan_model `pinned_by` on E3.2, E3.7 | |
| C10 | MAJOR | FIXED | plan_model E6.3t → J1.6; plan §4.2 row 16 | CODE-8 |
| C11 | MAJOR | FIXED | as S12; G3.L0 ← B.W1; B.U; plan §6.4b; ROLE_BUILD_OPERATOR | |
| C12 | MAJOR | FIXED | plan §3.8, §5.0b, §6.5, §7; charter R10; arch §2.2, §8; runbook; ROLE_MONITOR; Track A §2; D6 runbook status and §0; map | |
| C13 | MAJOR | FIXED | plan §5.0, §5.0b; map v1.2; plan_model notes; Track E and A findings lines | |
| C14 | MAJOR | DEFERRED→L.12r | plan_model L.12 retitled to its actual scope; L.12r → L.9, FI-7; package marked STALE | Recommend Strategic Suvarṇa emit a `note` correcting the L.12 event (not emitted here) |
| C15 | MAJOR | FIXED | family prompts v1.2 (all three); notice v1.1 | Relay as FI-8 |
| C16 | MAJOR | FIXED | plan §3.7, §5.1 E3, §7, App. A | |
| C17 | MAJOR | FIXED | runbook §6; D6 runbook §3 note | Re-issue by `--apply`, never the rollback |
| C18 | MAJOR | FIXED | D6 runbook §1 | Run in bash; zsh form given |
| C19 | MAJOR | FIXED | arch §12.14; Track A §3; Track E E1.2 (docstring drift row) | |
| C20 | MAJOR | FIXED | arch §12.12; plan §5.1 E7.3; Track E §8; runbook; ROLE_COMMON §5 | Tracker code has one owner; E7.3 PRs to strategy |
| C21 | MAJOR | FIXED | plan §1.2; arch §6.5; ROLE_BUILD_OPERATOR; E7.1 scope | L3 close = asset-list run |
| C22 | MAJOR | FIXED | arch §2.4, §5.5; runbook §1, §2 steps 9, 11; ROLE_COMMON §12 | Untracked settings file passed with `--settings` |
| C23 | MAJOR | NATIVE→N-26 | plan §3.7, §4.2 row 9, §7, §8; plan_model E3.2n, E3.3 (`pinned_by`) | |
| C24 | MAJOR | FIXED | plan §1.1(4), §5.2, §5.4; charter G16; ROLE_STEWARD; ROLE_ANALYST; Track A §5, §10 | |
| C25 | MAJOR | FIXED | arch §7 | |
| C26 | MINOR | FIXED | plan §6.6; Track E §9 | |
| C27 | MINOR | DEFERRED→E2.1 | plan §3.6, §5.1 E2 | 31 listed vs 32 ruled; E2.1 reports the reconciled count |
| C28 | MINOR | FIXED | plan §5.2 | |
| C29 | MINOR | FIXED | arch §3.1, §3.3; plan §6.2; ROLE_GATE_REVIEWER | |
| C30 | MINOR | FIXED | arch §8 | |
| C31 | MINOR | CODE→CODE-3, CODE-6 | arch §11.7 (empty spec reads unknown); Track E §5 scorecard schema | |
| C32 | MINOR | CODE→CODE-16 | arch §12.11, §12.12; ROLE_COMMON §3; ROLE_CONDUCTOR step 11; ROLE_STEWARD | Exact command quoted |
| C33 | MINOR | FIXED | arch §12.10; map; runbook §2 step 7 | Mirror on hq only, one writer |
| C34 | MINOR | FIXED | D6 runbook §2, §3 | |
| C35 | MINOR | FIXED | family prompts; notice | Absolute `/Users/Dev/suvarna/evidence/l3-<family>-<date>` |
| C36 | MINOR | FIXED | plan §5.3; arch §6.4 | Shown as `blocked`, detail `waiting_on_family: <asset>` |
| C37 | MINOR | FIXED | plan §5.0; plan_model FI-6 | Done for the two sessions that exist; recommend Strategic Suvarṇa re-emit FI-6 evidence with the exact names |
| C38 | MINOR | FIXED | plan_model decisions N-19, N-10.L0.c; plan §8 | |
| C39 | MINOR | FIXED | plan §0.2 | |
| C40 | MINOR | FIXED | plan_model L.8 | |

## 3 · CODE specs (for the code agent; `platform/scripts/governance/suvarna_tracker/` only)

Until these land, `test_every_detector_type_in_the_real_plan_model_has_a_registered_detector` fails on the three new
types (`acks_from`, `fk_no_cascade`, `main_protected`); the other 371 tests pass. At runtime an unknown type reads
error (unknown), never done.

| Id | Findings | Spec |
|---|---|---|
| CODE-1 | S7, C5, C6 | `d_deployed_contains`, `d_wave_deployed`: run `os.path.expanduser("~/.config/suvarna/bin/suvarna-build") --preflight` (no `--json`; output is one JSON object: `job_image_tag`, `job_sha`, `deployed_sha`, `builder`). Running commit = `job_sha` (fallback: the hex SHA in `job_image_tag`) for `component: job`, `deployed_sha` for `web`. `git fetch -q origin`, then `git merge-base --is-ancestor <merge_sha> <running_sha>`: 0 → done, 1 → pending ("not deployed yet"), else error. Spec key `test: ancestor` (the only mode; drop substring and equality). Script missing → pending. |
| CODE-2 | S9(b), C9 | `d_prs_merged`, `d_deployed_contains`: when `prs` is empty and `head_refs` given, resolve each with `gh pr list --head <ref> --base <base> --state all --json number,state,mergedAt,mergeCommit`; no PR yet → pending; closed unmerged → blocked. |
| CODE-3 | C31 | A spec whose required list is empty (`prs` and `head_refs` both empty; `numbers: []`; `paths: []`) returns `error` ("unknown: parameters not set; pinned_by: <value>"), shown as unknown, never pending/not-started. |
| CODE-4 | S9(a), C7 | `FAMILY_ASSETS_REL_PATH = "00_ARCHITECTURE/control/FAMILY_ASSETS.json"`; read keys per Track E §8 (`family_gochara`, `family_sangam`, `family_kshetra`, `family_readers_L3/L4/L5`, `family_set`); a missing named key → error. |
| CODE-5 | S10(a), C8 | `d_registry_coverage`: read `00_ARCHITECTURE/control/registry_coverage_report.json` at `origin/main`; require `registry_revision`, `inspector_commit`, `covered_cells`, `uncovered_required_criteria` (list); any missing → error; non-empty list → pending (list it); done only when empty. Absence of keys never reads as pass. |
| CODE-6 | S10(b), C31 | `d_scorecard_pass`: require `generator`, `generator_sha256` equal to the sha256 of `git show <ref>:<generator>`; `tests[T].verdict == "PASS"` for each listed test (objects, per Track E §5); `inspector_commit` an ancestor of the ref. Any check unmet → pending with the reason; unreadable → error. |
| CODE-7 | S10(c) | `d_register_freeze_clean`: spec `expect_rows`; any listed row absent from the parsed register → error; zero BLOCKS_FREEZE rows found → error; otherwise as today with `allow_deferred`. |
| CODE-8 | S8, C10 | `levels_elevated`, `assets_elevated`: return error ("unknown: exact ELEVATED not wired, E6.3t") instead of the proxy until the E6.3 function is loadable from `asset_elevation_tracker.py` at the committed ref; then call it (terminal dispositions honoured) and delete the proxy. Fix the docstring (E6.3, not E4.1). E6.3t's event records the commit. |
| CODE-9 | S3 | New `d_fk_no_cascade` (spec `referenced`): read-only `select conrelid::regclass, conname from pg_constraint where contype='f' and confrelid = '<referenced>'::regclass and confdeltype='c'` via `_psql`; 0 rows → done; rows → pending listing them; error on failure. TTL ~10 min. |
| CODE-10 | S16 | New `d_acks_from` (spec `actors`, `marker`): scan `EVENTS.jsonl` for `kind: note` from each actor whose `detail` starts with `marker`; done when all present; progress = fraction; else pending listing the missing actors. |
| CODE-11 | S1 | New `d_main_protected` (spec `branch`, `bypass_only`): `gh api repos/{owner}/{repo}/rules/branches/<branch>` (rulesets) and, if none, `.../branches/<branch>/protection`; done when a pull-request rule with ≥1 required approving review applies; report the bypass actors in the detail; 403/404 → error. |
| CODE-12 | S1 | Monitor check `isolation` (stat/access only, never opens a credential): expected user (from N-25's decided line: `suvarna` if yes; the native otherwise); `/Users/Dev/madhav-l3/dbenv.sh` and `dbenv_builder.sh` mode 600 (and unreadable under N-25); under N-25 also unreadable `/Users/Dev/.config/madhav-admin`, `/Users/Dev/.codex`, and `run/DECISIONS.jsonl` not writable; sha256 of `$SUVARNA_HOME/config/claude-settings.json`, the running user's `~/.claude/settings.json` and hq's `.claude/settings.json` equal the baseline `$SUVARNA_HOME/config/settings_baseline.json` (written by the native). Any miss → block. Counted in the heartbeat's check total. |
| CODE-13 | S2 | Monitor check `decision_writers`: any line in `run/DECISIONS.jsonl` with `state: decided` and `writer` ≠ `strategic-suvarna` → block, listing ids (today: none). |
| CODE-14 | S2 | `decide.py`: accept `--writer strategic-suvarna` only (reject `steward`); for `--state decided` require an interactive TTY and a typed confirmation of the id (`--yes` refused); `state.py` `ALLOWED_DECISION_WRITERS = {"strategic-suvarna"}` so a steward line shows as a conflict. Update the Steward-writer tests. |
| CODE-15 | C3 | Monitor check `builder_scope` (E7.3's code, landing on `strategy/suvarna-plan`): run the preflight; read `builder.{principal_id, role, status, grants}`; block unless role `guest`, status `active`, grants exactly `[(482012f1-710e-4a25-994a-93821f5871aa, build)]` and equal to `$SUVARNA_HOME/run/builder_identity.json`; a missing script or failed preflight blocks once `builder_identity.json` exists, and the check is absent before it. |
| CODE-16 | C32 | `hq_commit.py --add-new`: inside the lock, `git add -- <path>` only for listed paths git does not track; still refuse `.`, `-A`, `-a`, `--all`, globs. |
| CODE-17 | S13, C2 | `run_tracker.sh`: `export NIKASHA_REF="${NIKASHA_REF:-origin/campaign/nikasha-test}"`; detectors `git fetch -q origin <branch>` (TTL-cached) before `git show` when the ref starts with `origin/`; `NIKASHA_ROOT` may be any checkout (default the hq worktree). |
| CODE-18 | S18 | New `lane_launch.py` (`python3 -m suvarna_tracker.lane_launch --qid --role --model --effort [--prompt-file]`): refuses if the hold is set or `$SUVARNA_HOME/lanes/<qid>` is missing; runs `claude -p <prompt> --settings $SUVARNA_HOME/config/claude-settings.json --permission-mode dontAsk --model <model>` with cwd the lane, detached, log to `evidence/<qid>/agent.log`, pid to `run/lanes/<qid>.pid`; never passes a bypass flag; emits `running` for the qid. |
| CODE-19 | S18 | `events.py` (or a CLI): `--since-offset <n>` prints events after a byte offset and the new offset, for Conductor passes. |
| CODE-20 | C22 | `runtime_settings.py`: also accept the target `$SUVARNA_HOME/config/claude-settings.json` (keep refusing any `settings.json` inside a repository); `--check` against it is what the `isolation` check calls. |
| CODE-21 | S1, C22 | `runtime/settings.template.json`: add the arch §2.4 denies it lacks: `Bash(gh api*)`, `mcp__github__*` merge tools (`mcp__github__merge_pull_request`), `mcp__postgres__*`, `Read`/`Bash` on `/Users/Dev/madhav-l3/dbenv*` and `**/.env*`, `Edit(/Users/Dev/suvarna/config/**)`, `Edit(/Users/Dev/suvarna/run/DECISIONS.jsonl)`, `Bash(claude *)` except the lane launcher; narrow `Bash(psql *)` to the reader form (`bash -c 'source ~/.config/suvarna/pgenv.sh && psql …'`); allow `python3 -m suvarna_tracker.lane_launch *` and `git push origin suvarna/lane/*`. |

(The hold-guard hook, `runtime_settings.py`, the template and `conductor_heartbeat` come from L.15's work, in
progress in the same tree; CODE-20 and CODE-21 amend them.)

## 4 · NATIVE decisions needed (plan §8)

| Id | Question | Recommendation |
|---|---|---|
| **N-25** | Run the swarm as a separate macOS user with its own settings, its own GitHub identity (can push and open PRs, cannot merge) and a read-only view of the decisions log; `chmod 600` the two `dbenv` files; branch protection on `main` requiring your review | **Yes to all three.** Without the separate user, R7 and P14 rest on deny rules and prompt text only |
| **N-26** | Build-engine migrations 1094–1096 sit in L3's reserved range 1070–1119 | **Renumber at landing** (never applied, so legal); the plan model pins the numbers with the decision |
| **N-14.R236** | `lel_events` has no writer; without a disposition W0 can never complete | **Declared no-writer asset**, Build and Idem N/A by registry rule (with N-13/N-22), ruled before W0 |
| **F-3** (delegated; now needed before W0) | Remove `ON DELETE CASCADE` from all eight keys into `bodha_msr_signals`; name who lands the migration | **Drop the keys** (a restricting key would refuse the L2 rebuild); integrity by detector; before wave 0 |
| **N-1 with G16** | Approve the v1.4 set; say yes or no to G16 | Approve after L.9, with G16 |
| N-4.T1–T3 | Now approved as one batch | Review the three agendas together |

## 5 · Left for Strategic Suvarṇa (not done here, by instruction)

- Emit a `note` correcting the L.12 `done` event (the review package was not rebuilt) and re-emit FI-6's evidence with
  the exact session names.
- Merge the v1.4 set into hq and restart the tracker and Monitor from hq (L.17) once committed.
- Build L.12r (package and bundle) before L.9; draft J1.0d after A.L0.

## 6 · Pass-3 follow-up (2026-09-30)

Review pass 3 (`REVIEW_PASS3_v1_0.md`) checked 62 of these findings and all 21 CODE specs: 56 findings verified; 12 CODE
specs implemented as specified, 8 partial, 1 not implemented. The rows above are left as written; where pass 3 found a
fix missing or partial, the follow-up lives in `REVIEW_PASS3_DISPOSITION_v1_0.md`:

| Pass-2 item | Pass-3 finding | Now |
|---|---|---|
| S1 · CODE-12 (not implemented), CODE-20 wiring, CODE-11 bypass | isolation hard-coded `warn`; L.16a and runbook steps 2a/6 never completable (B1) | CODE-22, CODE-33; documents accept `warn` until N-25 |
| S2 · CODE-14 (partial) | any process can append `decided` as `strategic-suvarna` (B6) | CODE-27 (the swarm is denied `decide`/`decisions`) |
| C3 · CODE-15 (partial) | `builder_scope` `ok` before provisioning; E7.3 read done (B2) | CODE-23; documents: `warn` until E7.2 |
| S10(b) · CODE-6 (partial) | generator pin ignored (B7) | CODE-24 |
| S14 (partial) | hold-guard hook runs from Strategic's worktree and fails open | CODE-25; documents: hq path, fail closed for dispatches |
| C22/S1 · CODE-21 (partial) | broad `git push *` kept; psql quoting differs (B5, B10/B11) | CODE-26, CODE-28 |
| CODE-8, CODE-17, CODE-18 (partial, cosmetic) | docstring; `NIKASHA_ROOT` default; `lane_launch` item | CODE-34 |
| S10(c)-adjacent: J1.R | R34, R36 BLOCKS_FREEZE with no owner (B3) | FIXED: E1.10 |
| §4 N-26 | every Suvarṇa migration denied by main's settings (B4) | NATIVE: N-27 (N-26 now renumbers into its range) |
| R244-deferred finding | E4.2r did not pin the withholding (B8) | FIXED: E4.2r spec |
