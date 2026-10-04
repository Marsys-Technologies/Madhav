---
artifact: S_L1_WINDOW_RUNBOOK
version: 1.3
status: DRAFT-FOR-SS-REVIEW (local, writable; v1.2 is kept unchanged beside it; lock with chmod a-w only when SS has reviewed and it is final)
date: 2026-10-04
produced_by: runbook-writer (docs-only worker, Exec Suvarṇa)
canonical_chart: 482012f1-710e-4a25-994a-93821f5871aa
scope: the production runbook for the S-L1 window (rebuild of the canonical chart's 18 ga_* assets) with the W1 migrations, the D6 owner-path apply, the W2-W6 builds, W7, SETTLED-1, and the ordered POST-WINDOW list
authority: rehearsal_final/r2/STEPS.tsv (second rehearsal) for order and commands; the integration documents merged with PR #2984 for the checks; the rulings listed in section 1.7
changelog:
  - "1.3 (2026-10-04): applies N-122 (SS answers to all 25 open questions of v1.2: 25 of 25 RESOLVED, 4 items still open, PART 8) and SS's independent review of v1.2 (READY AFTER FIXES, items 1-25, evidence table in the author's report). New: W0.2B (on-demand Cloud SQL backup, window does not start until SUCCESSFUL; restore is the owner's decision alone), W1.4B (close the six source PRs), gate A6 (explicit GO before the first dispatch), merge FREEZE and Pravāha hold (G-13), explicit-list dispatch with exact asset counts (G-12), runx/bash logging so the stderr banner is always seen, the D6 exit-1 reading rule, the in-process credential helper (Q-01 finding), route-B image verification with a proved script, hash-pinned production scripts under window_scripts/, post-window list renumbered (PW.2 = 1256, PW.9 = tests-only PR). Nothing was pushed, merged or commented; production was read through rq.sh and read-only gcloud calls only."
  - "1.2 (2026-10-04): first written document. 'Runbook v1.1' was searched for by the W1 preparer in main, all origin/suvarna/* branches and the working trees and does not exist; v1.0/v1.1/v1.2 had been lines in one session's notes. Written from the second rehearsal's executed sequence; every statement taken from the executor's running notes was verified against an artifact or is marked TO CONFIRM (PART 8). Production baselines quoted as 'read 2026-10-04' were re-measured through rq.sh (suvarna_reader) while writing. No production write, no push, no PR comment, no merge."
---

# S-L1 WINDOW RUNBOOK v1.3 (DRAFT for SS review)

Chart `482012f1-710e-4a25-994a-93821f5871aa` only. The HOLD stays in force until SS's RELEASE. Sections: CHECKLIST (below) | PART 1 Orientation | PART 2 W0 | PART 3 W1 and D6 | PART 4 W0.P, W2, W3 | PART 5 W7 | PART 6 abort matrix, Pravāha, the SETTLED-1 notice | PART 7 POST-WINDOW | PART 8 QUESTIONS (25/25 resolved, 4 items open) | Appendices A-D.

# ONE-PAGE CHECKLIST (step IDs and abort points; the blocks below give the commands)

SS gates: **A1** RELEASE + slot (W0.1) | **A2** GO to arm W1 (W1.2) | **A3** dry-run approval, **A4** apply approval (D6.4) | **A6** explicit GO before the FIRST dispatch (W0.P) | **A5** acceptance and S-L1 CLOSE (W7.17). **SS-run steps:** W0.14, W7.14 (served calls via MCP), merge FREEZE (W0.16). ABORT always means: stop, leave the step's safe state, ALERT SS and Pravāha; never a workaround; the backup (W0.2B) is the last resort and restoring it is the OWNER's decision alone. Bash only (`bash -l`); gated commands run through `runx`. Order is execution order (note W0.P sits between D6 and W2).

| ID | do | ABORT if |
|---|---|---|
| W0.1 | RELEASE, slot, Pravāha notice, evidence root | no RELEASE / slot, their freeze on |
| W0.2 | proxy up; reader `suvarna_reader\|on`; PG major 15 | major != 15; not read-only |
| W0.2B | **on-demand Cloud SQL backup** `gcloud sql backups create` (instance `amjis-postgres`); window does NOT start until SUCCESSFUL | not SUCCESSFUL; proxy serves another instance |
| W0.3 | `.se1` pins `shasum -a 256 -c PINS.txt` | any hash differs |
| W0.4 | clean `$MAIN` worktree; main sha; #2984 #2986 #2858 + E3.2 ancestors; deploy settled; `ga_vargas` digest `9212b478...`; no `ga_*` digest drift | missing ancestor; deploy running; digest moved |
| W0.5 | one `PY`; executor `0437cc8f...`; `make_plan.py` = `f7915138...`; gate pins; tool shas | any hash differs (bound hash void) |
| W0.6 | ledger 1219 / 1243 / 1255; ownership 236; candidate rows; function md5 `1e079261...`; `verify_before_apply.sql` PASS | any differs; D6 already applied |
| W0.7 | zero non-terminal runs, CLASSIFIED by assets (recalibration let finish) | foreign `ga_*` / unclassifiable run |
| W0.8 | counts `143299\|8524\|24392\|483870` + all-charts baseline | any mismatch |
| W0.9 | 4 id maps captured read-only + sha256 | cannot capture = S-L1 does not open |
| W0.10 | flip snapshot, special-lagna, vichara, CS6 margins (before W1) | exit 5/6; margin within bound |
| W0.11 | H1-H26 BEFORE (50 blocks + BS) | a BEFORE value differs from its baseline |
| W0.12 | build ids, categories, freshness, md5s, receipts baselines | differs from the documented state |
| W0.13 | image tag + env names on record | (record only) |
| W0.14 | **SS** runs `judgment_query` + `assess_*` via MCP: flag FALSE, normal sentence | flag already true / check-failed set |
| W0.15 | owner states he is not using the chart (2026-10-02) + foreign-run check (KNOWN LIMIT) | owner IS using it / corpus run scheduled |
| W0.16 | window-open note; **SS merge FREEZE on main**; Pravāha holds its flow; backup SUCCESSFUL | a lane cannot freeze; a merge lands |
| W1.1 | W1 PR = the SEVEN SQL FILES only (+ census commit): 7 shas, only 7 unapplied files in BOTH migrate.ts folders, guard, CI green on exact head | sha / extra file / CI red |
| W1.2 | **A2** arm + merge = apply; record `M1` | queue rejects; anything else deploys |
| W1.3 | deploy success, migrate job as `amjis_app`, DEPLOY_SHA = `M1` | migrate fails (forward-only; no D6) |
| W1.4 | ledger: 7 rows, filename + sha256 | row missing / sha differs / extra row |
| W1.4B | `gh pr close` #2900 #2943 #2896 #2898 #2957 #2959 "carried by W1; must not merge"; verify 6 CLOSED | any not closed / already merged |
| W1.5 | md5s, edges, specs 1\|2, EXACTLY 6 assets fresh to stale, ownership 236 | any difference |
| W1.6 | image repeat 1: tag = deploy sha, NEWER than `a5b3b7b26`; re-set `$MAIN` to `IMG_SHA`; env names | mismatch / override / `ORCHESTRATOR_WRITER_GAP_CHECK` present |
| W1.7 | image repeat 2 = ROUTE B (streamed, no docker): `image_routeB.py` `ROUTE_B PASS` | ANY pyswisseph / PyJHora / `.se1` diff = STOP |
| W1.8 | image repeat 3: inventory `--check`, `ga_*` unchanged, `ka_gochara*` moved, E3.7, no runs | `ga_*` digest moved / check fails |
| W1.9 | confirmatory lanes (`ga_positions` `ga_panchanga` `ga_sensitive` `ga_vargas` `ga_dashas`) only if numpy / scipy / psycopg differ | any lane differs |
| D6.1 | PG 15, no runs, md5 pre, `verify_before_apply` PASS, `WC` = image sha, `git fetch` + `cat-file -e $WC` | any fails |
| D6.2 | `--count` via `runx ... run_gated.sh "$PY"` | any REFUSED; `pre_writer_first` = hash void |
| D6.3 | `--dry-run`: ALL HOLD, evidence digest `EVD`, window <= 100 stmts | failed check; lock timeout |
| D6.4 | **A3** then **A4**; owner line | no approval |
| D6.5 | `--apply` with `--expect-evidence "$EVD"`, SAME `PY` | 92 / 93 / **exit 1 WITHOUT `REFUSED_ROLLED_BACK` in the JSON = D6.8** |
| D6.6 | `verify_after_apply.sql` PASS; md5s `b2f4242f` `873ee5da` `31d005e8`; 7-col index; triggers 7 / 9 | any non-PASS (D6.7 rollback only before the first build) |
| D6.7 | conditional rollback leg (before any widened rows) | refuses once widened rows exist |
| D6.8 | commit-state-unknown procedure | partial state = STOP, call SS |
| W0.P | **A6 GO**; record all planned/running runs, **pause `watchdog-reaper`**, verify PAUSED, `CAP_T` = +6 h (the cap always wins) | cannot verify PAUSED = do not dispatch |
| W2.1 | pre-dispatch gate: classified foreign runs, PAUSED, tag = checkout, rows present, writer-gap env absent | foreign `ga_*` run; tag moved; not PAUSED; writer-gap env present |
| W2.2 | dispatcher LIVE dry run via `with_app_db.py`; `PLAN PASS` = EXACTLY 1 asset; token | `PLAN FAIL`; `ROLE_MISMATCH`; any refusal code |
| W2.3 | commit; record `RUN_P`, `EXEC_P` | exit 3 / 6 / 7 (ACTIVE_RUN check first) |
| W2.4 | poll every 10 min; 30-min no-progress rule; never kill a tail | foreign `ga_*` run |
| W2.5 | accept: 1,205 rows, 5 FORENSIC, swieph line; NO G-IDX | no swieph line / `passed=False` / failed run |
| W3.1 | pre-dispatch gate again | as W2.1 |
| W3.2 | dry run, ONE explicit list, `PLAN PASS` = EXACTLY 17 assets, 6 waves, token | `PLAN FAIL`; refusal; wave map differs |
| W3.3 | commit; record `RUN_17`, `EXEC_17` | as W2.3 |
| W3.4 | poll; reference timings; cap rule | no progress > 30 min = investigate |
| W3.5 | run `completed`, 17/17 `complete`/`build`, 18 lit | any asset not complete (W3.8) |
| W3.6 | logs: all 16 reachable gate sites ran (47 + 10 lines, 13 forms, per-asset `uniq -c`), 0 `passed=False`, swieph for all 10 decorated assets, 0 `WRITER GAP`, 0 ERROR | missing / other backend = STOP |
| W3.7 | MV left knowingly stale | - |
| W3.8 | failure handling (mixed generation, SS decides) | - |
| W7.1 | **resume `watchdog-reaper`**, verify ENABLED | cannot resume = ALERT |
| W7.2 | G-IDX `--check` via `with_app_db.py`: 147751 / 133832 / 13919 / 0 / 100%, 15 reasons, all 7 clauses PASS | rc 4/2/3; new reason; gap > 0; **any NOT_EVALUATED = failure** |
| W7.3 | flip detector, 24 stems: NOT_CHECKED exit 4; operative reading = 0 failures incl. DECLARED_BUT_ABSENT, 76/76 `ok:true`, 19/19 anchors; `--validate-hooks` exit 0 | FAIL 2 / ALERT 3 / any failure class |
| W7.4 | CS1-CS6, special lagna, vichara A1-A12, F-A2 C1-C7 | any exit != 0 / `f` |
| W7.5 | H1-H26 AFTER vs BEFORE (H10, H22, H23, H24, H25, H26 hard) | outside any expected value |
| W7.6 | id check `147751\|147750\|1`; orphans 0 | uuid36 > 1 / orphan |
| W7.7 | proven receipt newer for all 18 | any missing |
| W7.8 | T4 survivors == 0 | any survivor |
| W7.9 | `wstep_checks_prod.py` 18/18; zero-longitude SQL over ALL vargas = 0 | any `ok: false` |
| W7.10 | heads proxy (iii) 18/18; 18 integrity TRUE | any `f` |
| W7.11 | other charts' counts unchanged; ALL runs since window open excluding ours listed | any moved; foreign `ga_*` run |
| W7.12 | MV recorded stale (1256 later) | - |
| W7.13 | freshness effect as adopted (no non-`ga_*` freshness change) | unexplained change |
| W7.14 | **SS**, after >= 3 min: `l2_receipts_predate_l1` TRUE, check-failed NOT set | flag false / check-failed set |
| W7.15 | reaper tick observed, no dead running run | no tick / dead run |
| W7.16 | final detector with `--allow-not-checked` exit 0 | exit != 0 |
| W7.17 | window report + SETTLED-1 notice (incl. Vimshottari build id, tier of the ten rows, shift tolerance); **A5** = S-L1 CLOSE (S-L2 clock starts) | not accepted |
| PW.1 | rotate `suvarna_reader` password (FIRST) via `rotate_reader_password.py` (no argv); tell all sessions to re-source | any FAIL |
| PW.2 | migration 1256 (MV refresh), right after the rotation | RAISE |
| PW.3 | #3040 then 1259 (routine) | md5 refusal / RAISE |
| PW.4 | 1265 owner-path (BOUND `368dbc48...`, exec `64ed08de...`) after #3040 + 1259, before 1275 | refusal; commit unknown (96) |
| PW.5 | 1275 (#3064) | RAISE |
| PW.6 | ONE slot: deploy #3047, 1288, 1274 (BOUND `4c8b8629...`) dry run then apply, scoped delete #3072 MERGED (BOUND `26539e35...`); builder memberships empty, `rolsuper(postgres)=f`; no build between | any refusal |
| PW.7 | #3045 (BOUND `af946cb4...`, exec `72879feb...`) | refusal; 94 / 96 |
| PW.8 | 1262 (#3073) | RAISE |
| PW.9 | ONE tests-only PR landing the six source PRs' migration tests (conditional change-scope guard form) | a test needs a migration edit |
| PW.10 | the rest (1260, 1261, 1276, curation, L0, N-117, S-L2 prep, correctness items) | per item |

Stop-the-window rules in one line: any pyswisseph / PyJHora / `.se1` difference; a missing or non-`swieph` backend line; a foreign run that would write `ga_*`; a dry-run plan with other than exactly 1 / 17 assets; FORENSIC `passed=False` or an ALERT exit 3; a D6 `COMMIT STATE UNKNOWN`; G-IDX rc 4 or NOT_EVALUATED; any W7 expectation outside its row; the 6-hour watchdog cap always wins and every abort ends with a verified resume.

---

# PART 1. ORIENTATION (read this first, once, before W0)

## 1.1 What this document is

The production runbook for the S-L1 window: the rebuild of the owner's canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`) across the 18 `ga_*` assets of the Gaṇita layer, with the seven W1 migrations and the D6 owner-path apply that precede it, the W7 acceptance that follows it, and the ordered POST-WINDOW list.

It is written so that a fresh operator with no other context can execute it. Every step has the same block: ID, who acts, precondition, the exact command (credentials are referenced by path or helper name only), the expected output, the ABORT rule, the SAFE STATE after an abort, and the evidence to record.

AUTHORITY (in order): (1) the SECOND REHEARSAL's executed sequence, `rehearsal_final/r2/STEPS.tsv` (sha256 `a02cfb04b4704d37bfa54371aef2c906f0292bd98ca6a1e717fa0cf017c3e053`) and `rehearsal_final/REHEARSAL_FINAL_REPORT_2.md` (sha256 `a9be02f3c12d8ae02936cd354b046fff039dfea049514fa4c80fecb028a41824`) decide the step ORDER and the commands; (2) the integration documents merged to main with PR #2984 (`S_L1_BETWEEN_STATE_v1_0.md` v1.5, `HOOKS_W7_HAND_READBACK_v1_0.md` v1.9, `HOOKS_COMPLETENESS_v1_0.md`, `FLIP_DETECTOR_README.md`, `L1_MV_REFRESH_AFTER_REBUILD_v1_0.md`) decide what is checked and the expected values; (3) the rulings in section 1.7 decide every conduct rule; (4) `RUNBOOK_INPUTS_CHECKLIST.md` (a running notes file, sha256 at read `e95d43cc083315024bd37af346e3d89fb5f699d5156676166c08c01e5a1af9fb`) was used only as an INPUT and each statement taken from it was verified against an artifact or is marked TO CONFIRM. The first rehearsal (`REHEARSAL_FINAL_REPORT.md`, `rehearsal_final/STEPS.tsv`) is background only: where it differs from the second (D6 writer-first bypass, the stand-in F-A2 hook, G-IDX after W2) the second wins and the first is obsolete.

Where a number or value could not be verified from the artifacts it is marked TO CONFIRM and listed in PART 8 (OPEN QUESTIONS; v1.3 resolves all 25 questions of v1.2 with the N-122 rulings and measurements; 4 items remain open). Nothing is invented.

## 1.2 Naming (SS-confirmed)

| name | meaning |
|---|---|
| W0 | prechecks, baselines, and the watchdog pause (the pause is listed under W0 by name but EXECUTED LATE, step W0.P, immediately before the first build_run is created; N-93) |
| W1 | the seven migrations 1221, 1222, 1223, 1224, 1226, 1252, 1254, ONE PR, applied by merge-and-deploy as `amjis_app`. 1243 is already applied (2026-10-03 15:57Z). 1219 is already applied (2026-10-03 19:21Z). 1255 is already applied. 1259 is NOT in the window |
| D6 | the owner-path apply of the data-plane capture repair plus the F-A2 key widening (PR #2964), at the point where the second rehearsal ran it (after W1, before any build) |
| W2 | the `ga_positions` build (one run) |
| W3-W6 | the other 17 `ga_*` assets (one run, the dispatcher derives the waves) |
| W7 | G-IDX, then the machine verdict and the hand read-backs, then the between-state check, then SETTLED-1 |
| SETTLED-1 | the close of S-L1: every W7 check recorded as passing, SS acceptance recorded, the notice to Pravāha sent (PART 6) |

NOTE (mislabel): the D6 plan document `D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN_DRAFT.md` section 9a ends its "final sequence" with "apply -> W1". That "W1" is a MISLABEL: in this runbook W1 is the migration step and it comes BEFORE D6, exactly as in the second rehearsal. The plan document is NOT to be edited (editing it would change its sha256 and, through the pinned-docs list, the CI state; its sha256 is quoted outside the file in the owner's authorisation).

## 1.3 Roles and identities

| who | acts as | does |
|---|---|---|
| operator = the production session of Exec Suvarṇa | OS user of the production host; database role per step (below) | runs every step; records evidence; stops at every ABORT |
| SS (Strategic Suvarna) | approves | RELEASE, window slot, W1 arming, D6 dry-run approval and apply approval, every ABORT decision, SETTLED-1 acceptance |
| Pravāha steward | informed | receives the slot notice (6 h ahead), the pause and resume notes, the SETTLED-1 notice |
| SS (additional duties, N-122) | the MCP server | runs the live served calls (`judgment_query` / `assess_*` for the canonical chart) at W0.14 and W7.14 and saves the outputs under `/Users/Dev/suvarna-evidence/S_L1/window/`; issues the MERGE FREEZE on main at W0.16; gives the GO before the first dispatch (A6) |
| nobody else | - | no worker, reviewer or other session writes to production during the window; Pravāha holds its OWN flow on this chart from window start to SETTLED-1 (G-13) |

| database role | used for | credential SOURCE (never print, never grep, never cat) |
|---|---|---|
| `suvarna_reader` (read-only session, SELECT only) | every read | `/Users/Dev/suvarna-evidence/S_L1/rq.sh <one SELECT>` (the ONE approved helper, HELPER AUDIT 2026-10-03) or the documented subshell `( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '\|' ... )`; the source file is `~/.config/suvarna/pgenv.sh` |
| `amjis_app` | G-IDX (W7.2), the dispatcher `DATABASE_URL` (W2/W3), the routine migrate job (W1, run by the deploy pipeline, not by hand) | NO literal is ever typed. The in-process path (Q-01 finding): `window_scripts/with_app_db.py --expect-role amjis_app -- <command>` reads Secret Manager secret `amjis-pipeline-db-url` with the operator's own gcloud identity, points it at the standing proxy `127.0.0.1:5433`, logs in once to assert the role (prints only `with_app_db: role=<name> OK`) and `exec`s the command with `DATABASE_URL` in its environment only. This is the documented path of the earlier production dispatches (`dispatch_sampurti_*.py`: "DATABASE_URL set via gcloud secrets, never .env.local"; `gochara/flip_authority.py`). The role behind that secret was NOT verified by the author (reading it is a login); the helper refuses on any other role (SS rules, Q-01) |
| `postgres` (CREATEROLE, non-superuser, cloudsqlsuperuser member) | the D6 executor and the post-window owner-path executors | fetched INSIDE the executor process from Secret Manager, only after the plan hash matched; connection 127.0.0.1:5433; never printed or saved |
| `data_plane_builder` | the Cloud Run job `brahma-build-pipeline-job` (the builds) | the job's own secret reference; the operator never holds it. NEVER used for G-IDX |

## 1.4 Global rules (apply to every step)

G-1. No secrets in any command line you type, any file you write or any message: reference sources by path or helper name only. NEVER run `grep`, `sed`, `cat` or any command that can echo an environment or credential line (`pgenv.sh`, `.env*`, the wrappers). Do not `set -x`. Do not `env` or `printenv`.
G-2. Stop or kill ONLY a process you yourself started and whose PID you recorded. Never kill a Cloud Run execution (see N-93 rule (c), G-6).
G-3. Never set `git config user.*` (use per-command `-c` flags if a commit is ever needed). Never run a plain `git push`: push only with an explicit refspec.
G-4. A failed check is a runbook ABORT or a stop-and-report, NEVER a workaround or a bypass (SS standing rule 3). Production in doubt: stop, leave the step's SAFE STATE, ALERT SS and Pravāha (every ABORT line in this runbook means exactly that: message SS AND the Pravāha steward at once, stating the step id and the state left behind). The 6-hour watchdog cap ALWAYS wins, and EVERY abort path ends with a verified watchdog resume (W7.1 form) once the abort's own safe state is verified.
G-5. Exit-code reading: read the stderr banner and `outcome.json`, not the number alone. The gate and the executors reuse numbers (table in Appendix C). In particular 96 FROM THE GATE (`run_gated: gate exit=96; target NOT started` on stderr) means "wrong role or database, nothing ran"; 96 FROM THE 1265 / #3045 EXECUTORS (their own `WARNING: COMMIT STATE UNKNOWN` banner and `outcome.json` status `commit_state_unknown`) means "the commit may or may not have happened: nothing else runs until the database is read". After ANY non-zero exit of an owner-path executor: read the banner, read `outcome.json`, re-read the database as the reader, decide, record.
G-6. N-93 rule (c), standing: "A reaper stamp (failed / error / incomplete / a watchdog lit) on a run whose execution is alive is not a failure and not a completion. Check the execution before any action. Never stop or kill a job during its post-write tail (integrity check, digest, receipt). A finishing job overwrites the stamp; stale text in build_runs.last_error / build_run_assets.error is expected and is cleared by the next successful write, not by hand."
G-7. The dispatcher and the executors are started with ONE explicit interpreter: an absolute path to a Python 3.11 (or 3.12+) that has psycopg 3 (`PY`, chosen and recorded at W0.5). The D6 dry run and the D6 apply (and every later executor's dry run and apply) use the SAME absolute path. A different path, psycopg or libpq exits 92 before any connection. `run_gated.sh` is started with that absolute path as its target: `run_gated.sh "$PY" <executor.py> ...`, never an ambient `python3`.
G-8. Record the wall-clock duration (UTC start and end) of every step in `$EV/TIMELINE.tsv`: `UTC<TAB>step<TAB>result<TAB>evidence path`.
G-9. Evidence root `EV=/Users/Dev/suvarna-evidence/S_L1/window` (create at W0.1; one folder per step id; files are never overwritten: new attempt = new suffix). Output files that contain only counts, ids and hashes are fine; no birth inputs, no private event text, no credentials.
G-10. Variables and the logging helper (bash ONLY: the steps use process substitution and `PIPESTATUS`; under zsh `${PIPESTATUS[0]}` is EMPTY. Start the window shell with `bash -l` and check `echo $BASH_VERSION` prints a version). They hold no secret:
```
export C=482012f1-710e-4a25-994a-93821f5871aa
export EV=/Users/Dev/suvarna-evidence/S_L1/window
export WS=/Users/Dev/suvarna-evidence/S_L1/window_scripts           # hash-pinned local scripts; MANIFEST.sha256 checked at W0.5
export RQ=/Users/Dev/suvarna-evidence/S_L1/rq.sh
export JOB=brahma-build-pipeline-job REGION=asia-south1 PROJECT=madhav-astrology
export MAIN=<set at W0.4, re-set at W1.6>      # /Users/Dev/suvarna-window/main_<sha>: a clean detached worktree; every git command below starts with: cd "$MAIN"
export D6=<set at W0.5>                      # /Users/Dev/suvarna-window/d6_<sha>: clean detached worktree of the #2964 head
export PY=<set at W0.5>                       # ONE absolute python3.11+ path with psycopg 3 (G-7)
# run a command, keep stdout/stderr in files WITHOUT hiding either from the terminal, and report the exit code of the COMMAND (not of tee):
runx() { local n="$1"; shift; "$@" 2> >(tee "$n.stderr" >&2) | tee "$n.stdout"; local rc=${PIPESTATUS[0]}; sleep 1; echo "exit=$rc" | tee "$n.exit"; return $rc; }
```
`runx` is used for every gated or executor command: the stderr banner (`run_gated: ...`, `GATE_V2 ...`, `WARNING: COMMIT STATE UNKNOWN`) is therefore always SEEN on the terminal AND kept in `<name>.stderr`. The reader is invoked as `"$RQ" "<ONE SELECT>"`; its output format is psql unaligned, `|`-separated, no header. For a multi-statement file use the documented subshell form with `-f`.
G-11. PEOPLE-ENTERED DATA IS NEVER CHANGED OR DELETED by anything in this runbook (`life_events`, the LEL tables, every table people write to through the app). No step reads `life_events` content; the one scoped delete (PW.6(4)) removes derived rows only and its executor proves no private text is touched. A LEL write by a person during the window is allowed and is never blocked (N-46).
G-12. EXPLICIT LISTS, NO CASCADE: every dispatch names its assets explicitly (W2: `ga_positions` alone; W3: the other 17 as ONE explicit list). The dry-run plan must contain EXACTLY 1 and EXACTLY 17 assets (`asset_count` in the dispatcher summary and the flattened `waves` equal the list) or the step ABORTS; nothing is added by a dependency or a level.
G-13. MERGE FREEZE and Pravāha hold (SS ruling, N-122): SS issues a merge FREEZE on main to ALL lanes at W0.16 for the whole window (until SETTLED-1); Pravāha holds its OWN flow on this chart (dispatches, runs, writes to `482012f1` tables) from window start to SETTLED-1. A deploy later than `M1` (ours) means W1.4-W1.8 are REDONE on the new image before any further step.
G-14. BACKUP AS LAST RESORT (N-122): an on-demand Cloud SQL backup of `amjis-postgres` is taken at W0.2B and the window does NOT start until it reports SUCCESSFUL. RESTORING it is DESTRUCTIVE and is THE OWNER'S DECISION ALONE. Every abort path in this runbook reaches a safe state WITHOUT a restore; the backup is the last resort and no step in this runbook restores it.
G-15. UNVERIFIED assumptions are marked UNVERIFIED where they occur (W2.4 advisory-lock wait; PW.1 REST call; the role behind `amjis-pipeline-db-url`); an UNVERIFIED assumption never decides a gate.

## 1.5 The state between S-L1 and S-L2 (N-91, condition 4; text of S_L1_BETWEEN_STATE section 1, adopted)

S-L1 re-runs the whole L1 (Gaṇita) layer for the owner's chart: all 18 `ga_*` lanes, including `ga_positions`, `ga_dashas` and `ga_vargas`. The fact_id formula in force drops `build_id` from the hash, so about 99% of the chart's fact ids change once: 142,094 of the 143,299 `chart_facts` rows get a new id; the 1,205 `ga_positions` rows (graha_position 430, bhava_cusps 360, house_chalit 225, graha_sign_attributes 100, sandhi_flag 90) keep theirs. The new ids are deterministic and stable from then on (a second rebuild reproduces them). The L2 (Bodha), L3 and L5 rows that cite the old ids are rebuilt only at S-L2, so between the two windows those citations point at ids that no longer exist (the L2 citations DANGLE until S-L2). No chart value is wrong and nothing errors; the one value-level move at S-L1 is the ephemeris backend (Moshier to the pinned `.se1` files): sub-arcsecond on graha longitudes, about +1 h 56 m on Vimshottari boundaries, about +40 h 18 m on Kalachakra boundaries, Saturn ingress instants up to about 17 minutes, a handful of level-4 dasha rows appearing or disappearing per ayanamsha. The owner gets a quiet degradation (served picture: S_L1_BETWEEN_STATE section 3) that clears when S-L2 closes. Accepted by owner-surrogate ruling N-91 option (a). The S-L2 clock (day 7 checkpoint, day 14 absolute, 48 h override) runs from S-L1 CLOSE (SETTLED-1).

Facts the operator must know and must not "fix":
- The figure "1,340 vargottama signal_ids move at the first MSR regeneration after a `ga_vargas` rebuild" (N-91 condition 8) is a LOWER BOUND, not an exact count. Recorded outside the window.
- The disclosure detector (PR #2986) flag `l2_receipts_predate_l1` goes TRUE after S-L1 BY DESIGN. It is the between-state acceptance signal (W7.14), not a W7 failure. `l2_lineage_check_failed` set is a failed detector and IS a failure.
- `ga_positions` rebuild empties `chart_fact_identity` by FK cascade, and every later `ga_*` delete-then-insert empties the rows of the facts it replaces. It stays near 1,205 rows (the surviving `ga_positions` ids) until G-IDX runs ONCE at the start of W7. That is expected, not a defect. The fact_id one-time flip is expected.
- Freshness effect (sentence adopted verbatim by SS): "On 482012f1 after S-L1 the writer-digest move changes no `asset_freshness` row and the L2+ receipts stay proven/fresh and keep serving; what reads stale is `asset_throughput` (cockpit/planner/DEP-ASSERT) for the lit L2/L3 assets downstream of the rebuilt `ga_*` and, only if #2986 is deployed, the `l2_receipts_predate_l1` flag, both by design until S-L2, and neither is a W7 failure." (FRESHNESS_EFFECT.md; up to 16 downstream L2/L3 assets, an upper bound: bo_arudha, bo_bimba, bo_grounding, bo_karanajala, bo_laksana, bo_laksana_rerank, bo_nakshatra_semantic, bo_samskara, bo_sangati, bo_special_lagna, bo_sudarshana, bo_vargottama_dhana, ka_dasha_kala, ka_kota_chakra, ka_sudarshana_varsha, ka_tithi_pravesha.) Note: W1 itself DOES change `asset_freshness`: exactly six `ga_*` rows go fresh to stale (W1.5) and the builds make them fresh again.
- Conditions of N-91 that bind this window: the owner states he is not using the chart (2026-10-02) and no foreign build run exists (N-122 replaced "zero open inquiries", which the reader cannot count: KNOWN LIMIT, W0.15; an inquiry open across S-L1 gets 409 `CAPABILITY_OVERLAY_STALE`); NO corpus or calibration run from S-L1 open to S-L2 close; D1 (`query_ucd`) fix and the echo-class disclosure (#2986) deployed and observed live before the window.

## 1.6 Bound artifacts (the numbers an operator compares against)

| item | value |
|---|---|
| D6 executor `d6_dataplane_capture_fa2_exec.py` sha256 | `0437cc8fd128d3adc3bb16cb79c09060de9839a4a2202978311c5377983db5e5` |
| D6 plan hash UNBOUND | `8410f83cdf5348e965e506146e5cb78d225201d17563a2aaaa9e15c1751bc677` |
| D6 plan hash BOUND (the `--expect-plan` value) | `f7915138b0a9ba8ad5fea98d3d7ba9311a1acbcd2065138d58ff0a595250b706` (reproduced 2026-10-04 by `make_plan.py` in `/Users/Dev/suvarna-d6rf` at 217349ff6) |
| D6 WRITER_DIGEST (`ga_vargas` writer digest the apply requires) | `9212b478621c3572e75f606819e865de768b6212def695cf67bd368e0510e8a1` |
| D6 F-A2 module `d6_f_a2_key_widening_DRAFT.py` sha256 | `c911c239c7344976b0c223b4835f0417c1b9b44ba247e8a790e6e7fbca2d0565` |
| gate pins (`exec/gate_v2`) | `prerun_gate.py` `01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e`; `run_gated.sh` `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076`; `executor_standards.py` `bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135` |
| `flip_detector.py` sha256 | `cabb8186868a5757707110b18b37baec321d137364a4a8db18be8129e58e624e` |
| `composite_shift_check.py` sha256 | `1a7dc58e1a62cd210e20c682647bd812044f8affab738a68ba84d2269a17e728` (verified equal to `origin/main` 2026-10-04) |
| `.se1` pins | `sepl_18.se1` `ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66`; `semo_18.se1` `1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7`; `seas_18.se1` `a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2` (sizes 484061 / 1304771 / 223004) |
| pyswisseph binary (image) sha256 | `3911614ca013be4520e355306620a3fcd27a39374a960a2063b056cfbd093338` (3,240,953 B; baseline recorded 2026-10-03, no earlier hash existed) |
| image versions (baseline) | pyswisseph 2.10.3.2, PyJHora 4.8.6, numpy 2.4.6, scipy 1.17.1, psycopg 3.3.6, psycopg-binary 3.3.6, psycopg2-binary 2.9.13, timezonefinder 9.0.0; Python 3.11.17 |
| W1 file shas | Appendix B |

THE D6 BOUND HASH IS VOID if ANY bound input changes: the executor, any D6 module, the live definitions, the gate files, or the `ga_vargas` writer digest (a change in any module in the `ga_vargas` import closure moves it; the executor then refuses at `--apply`, writer-first check, and a re-freeze plus a new SS approval of the new hash is required). Post-window bound hashes are in PART 7.

## 1.7 Rulings in force (every ruling made so far; cited by N-id or date)

| ruling | source | where it binds |
|---|---|---|
| N-93 watchdog pause: pause `watchdog-reaper` immediately before the first build_run is CREATED (not at session open), record every planned/running build_runs row on ALL charts first as the resume baseline, verify PAUSED, 6-hour hard cap from the recorded pause timestamp, resume at W7 / at the end of an abort after rollback is verified / at the cap, whichever first; verify ENABLED plus one observed tick; act as the watchdog for every chart during the pause (any run >30 min with no progress: investigate the execution, never a blind kill, never silent waiting); if the run died during the pause wait for the first post-resume tick and reconcile only via the governed `POST /api/cockpit/watchdog`; tell other workstreams at pause and at resume; put pause and resume in the window report; rule (c) is standing | `OwnerDecisions/N-93_watchdog_pause_ruling_v1_0.md` | W0.P, W3.4, W7.1, G-6 |
| N-91 between-state accepted until S-L2, conditions 1-8 (W0 maps captured read-only or S-L1 does not open; D1 fix and disclosure live; owner not using the chart + no foreign runs (N-122); no corpus/calibration run; false statements corrected; S-L2 prep top priority; clock from S-L1 CLOSE) | `OwnerDecisions/N-91_between_state_ruling_v1_0.md` | W0.9, W0.14, W7.14, 1.5 |
| N-46 / FRESHNESS_EFFECT ruling: never block people's entries; a LEL recalibration run (assets `mi_jivanaghatana`, `mi_pramana`, `ph_rectification`, `ph_pramana`, enqueued by any `lel_event_record` write) is LET FINISH; list foreign build_runs before every dispatch and at W7; only a foreign run that would write `ga_*` is an ABORT trigger | `FRESHNESS_EFFECT.md` (2) | W2.1, W3.1, W3.4 |
| Image verification REPEATED on the then-current image (W2 PRECONDITION, SS): expect a NEWER tag, IDENTICAL `.se1` hashes and versions, `ga_*` digests unchanged (`ga_vargas` `9212b478...`), Pravāha's `ka_gochara` digests moved; ANY difference in pyswisseph / PyJHora / `.se1` = STOP; numpy / scipy / psycopg only = confirmatory lanes first (the 4 ephemeris lanes plus `ga_dashas` against a disposable database) | checklist; `IMAGE_VERIFICATION_W2.md` | W1.6-W1.9 |
| pip / `.se1` rule: the sidecar requirements float (`numpy>=`, `scipy>=`, `psycopg[binary]>=`) so the exact match is a today-only fact; the three `.se1` files are hash-pinned in `Dockerfile.pipeline`; `sefstars.txt` / `seleapsec.txt` are not pinned | `IMAGE_VERIFICATION_W2.md` item 3; HOOKS_COMPLETENESS 11(b) | W1.7 |
| W2 backend log-line STOP rule: one `<asset> ephemeris_backend=swieph rows=<n> path=/app/ephe` INFO line per decorated asset (10 assets); a missing line or any other backend or path = STOP | HOOKS_COMPLETENESS section 10 (SS 2026-10-03) | W2.5, W3.6 |
| W1 is applied AS `amjis_app` (the routine migrate job), with a ledger read-back (filename plus sha256 per file); the ownership precondition 67 to 236 is already done by 1219; W1's expected effect is 6 assets fresh to stale; no CREATE on schema public is needed | `W1_PRIVILEGE_AUDIT.md`; `W1_PR_BODY_DRAFT.md` | W1 |
| P2 rule: every GRANT migration ends with an asserting `has_*_privilege` that RAISES (a non-owner GRANT silently grants nothing) | `W1_PRIVILEGE_AUDIT.md` P2 | W1.1, PART 7 |
| D6 interpreter rule: the SAME absolute interpreter path for dry run and apply; exit 92 on mismatch (path, `sys.version`, psycopg, libpq are bound into the evidence digest) | `D6_COMBINED..._PLAN_DRAFT.md` section 6; executor | G-7, D6.2-D6.5 |
| Exit codes: read the banner and `outcome.json`; 96 from an executor is commit_state_unknown, the gate's 96 is "nothing ran" | SS ruling (this task) | G-5, Appendix C |
| D6 admin grant is PG15-ONLY (`GRANT <role> TO CURRENT_USER` by `postgres` works under PG15 CREATEROLE rules; PG16+ needs ADMIN OPTION and re-opens it): pre-flight `show server_version`, STOP if the major is not 15 | `D6_ADMIN_GRANT_CHECK.md`; checklist | W0.2, D6.1 |
| G-IDX at the START of W7, after ALL builds, as `amjis_app` or `role_orchestrator`, NEVER `data_plane_builder`, with `--check`, with the AMENDED reason set (14 known plus `scope_cap_sentinel`; any other reason = abort; gap target 0) | S_L1_BETWEEN_STATE v1.5 section 4; GIDX_PARSER_REPORT; SS 2026-10-04 | W7.2 |
| Flip detector: 24 stems (23 plus `fa2_ga_vargas`), expected verdict NOT_CHECKED exit 4 with zero failure lists, 76/76 expectations, 19/19 anchors; `--validate-hooks --require-lanes` exit 0; the hook is paired with F-A2 C1-C7 and H26 | `FA2_HOOK_REPORT.md`; rehearsal 2 | W7.3 |
| CS1-CS6 composite shift check; H1-H26 hand read-backs; H25 tier census (the only guard on dasha tiers); H26 Aries bindus row | HOOKS_W7_HAND_READBACK v1.9 | W7.4, W7.5 |
| FORENSIC criterion: every gate that can run on the orchestrator path RUNS (0 skipped, 0 `passed=False`), 13 distinct line forms (47 `passed=True` plus 10 `assertion=none` = 57 lines in the rehearsal); the two log-only sites (`ga_vichara`, `ga_yoga` log-only branch) say `assertion=none` | `FORENSIC_GATES_REPORT.md`; rehearsal 2 | W3.6 |
| Heads proxy (iii): run state plus receipt binding plus stamped fact rows (`w7_heads_proxy.sql`); NOT a read of the heads table (the reader has no SELECT on it) | checklist; `w1_privilege_audit/w7_heads_proxy.sql` | W7.10 |
| T4: stale survivors (rows carrying a pre-window build_id) == 0; per-asset W-step checks 18/18; id check; orphans 0 | S_L1_BETWEEN_STATE section 5; rehearsal 2 | W7.6-W7.9 |
| Pravāha coordination: their protected train PRECEDES; the window slot is posted by SS with 6 h notice to Pravāha; nothing of ours merges during their freeze; our W1 PR triggers a deploy and the image verification is repeated AFTER that deploy | checklist; SS | W0.1, W1.2, W1.6 |
| N-95 standing pre-approval (stricter-only / tests-docs-evidence-only changes arm after a clean independent review); EVERY S-L1 window step is REVIEW to SS first | checklist | whole window |
| N-122 (SS answers to the open questions, 2026-10-04): the SS-run served calls; owner-not-using-the-chart statement; explicit GO before the first dispatch (A6); backup before start (G-14); standing delegation for owner-path plans at SS-approved hashes (approved D6 hash `f7915138...`); normal merge queue; W1 forward-only; no docker (route B only); password rotation without argv; migration 1256 is PW.2; final scoped-delete package = #3072 (MERGED) BOUND `26539e35...`; production-parameterised scripts under `window_scripts/` | `RUNBOOK_INPUTS_CHECKLIST.md`; coordinator messages | W0.2B, W0.14, W0.15, W0.P, W1.2, W1.7, D6.4, PW.1, PW.2, PW.6 |
| SS review of v1.2 (READY AFTER FIXES) and the rulings 4, 9, 14: dispatch shape = `ga_positions` alone then the other 17 as ONE explicit list (G-12); FORENSIC criterion = all 16 orchestrator-reachable gate sites ran, 0 skipped; merge FREEZE at W0.16 (G-13) | coordinator message | G-12, G-13, W3.6, W0.16 |
| Brief rulings for post-window items: 1265 conditional approval, 1288 before the scoped delete, scoped-delete extension, N-117 acharya rulings | checklist | PART 7 |

## 1.8 What the rehearsal did and did not prove (so nobody over-trusts it)

PROVED (second rehearsal, integration head `e751e9307` plus #2858 plus the W1 migrations plus the real 1243 SQL plus the D6 apply; real dispatcher, real orchestrator `main --run-id`, `SE_EPHE_PATH` on the real `.se1` files, no shims, no bypassed check): 18/18 lanes lit; 17-asset run `completed` 17/17 in 16 m 41 s on a laptop-emulated amd64; FORENSIC 57 lines in 13 forms with 0 skipped; 67 backend lines; 0 ERROR; G-IDX at the start of W7 measured gap 0 and coverage 100%; flip detector NOT_CHECKED exit 4 with 76/76; CS1-CS6 pass; H1-H26 as expected; D6 count, dry run and apply with the real writer-first check; apply under another interpreter exits 92.

NOT PROVED (REHEARSAL_FINAL_REPORT_2 section 7; re-stated): Cloud SQL 15.18 behaviour (the rehearsal used PostgreSQL 15.19 and a `postgres_mimic` role); the node `migrate.ts` runner (psql emulation, no hash or renumber guards); `run_gated.sh` / GATE_V2 (reads production deploy runs); the real `gcloud run jobs describe` and the job image built from `Dockerfile.pipeline` (Python 3.11.17 versus the rehearsal's 3.11.16); Cloud Run limits; the watchdog; the other two canonical charts; L2+ tables (empty in the rehearsal: H3 L2 counts and L2-side dangling behaviour untested); prior L1 generation history; production-scale timings (the `ga_structural` tail was 34 s in the first rehearsal against 658 to 1,323 s in production). Differences between the rehearsal and production that an operator will SEE: the rehearsal W1 set included 1219, 1243 and 1259 (production: 1219 and 1243 are already applied, 1259 is out of the window); production run ids, receipts timestamps and evidence digests differ by construction.

---

# PART 2. STEPS: W0 (prechecks and baselines; NO production write in W0 except the non-destructive backup of W0.2B)

Conventions for every block: **Who** = who acts; **Pre** = precondition; **Cmd** = the exact command; **Expect** = expected output; **ABORT** = the abort rule; **Safe** = the safe state after the abort; **Evid** = evidence to record (paths under `$EV`). W0 writes nothing to production (the on-demand backup of W0.2B is non-destructive), so the safe state of every W0 abort is "production untouched; the window does not open". ALERT SS and Pravāha.

### W0.1 Authority, slot, notices, shell, evidence root
- **Who:** operator; SS.
- **Pre:** SS has sent the explicit RELEASE (the HOLD on pushes, arming, merging and PR comments ends only with that message). The merge train is complete (#2984, #2986, #2858 merged) and Pravāha's protected train has finished ("done") and its freeze is lifted. SS has posted the window slot, with 6 hours' notice to Pravāha. The D6 re-freeze commits are pushed to #2964 and merged per the plan after Pravāha's "done" (N-122, Q-03).
- **Cmd:** `bash -l` (check `echo $BASH_VERSION`), set the G-10 variables, then `mkdir -p "$EV"/{W0,W1,D6,W2,W3,W7,POST} && date -u +%FT%TZ | tee -a "$EV/TIMELINE.tsv"` (then one line `W0.1<TAB>start`).
- **Expect:** the RELEASE message id and the slot start/end time written to `$EV/W0/W0.1_authority.txt` (message ids and times only).
- **ABORT:** no RELEASE, no slot, or Pravāha's freeze still on: do not start; ALERT SS and Pravāha. **Safe:** nothing started.
- **Evid:** `$EV/W0/W0.1_authority.txt`.

### W0.2 Host, proxy, reader identity, PostgreSQL major
- **Who:** operator.
- **Pre:** W0.1 done.
- **Cmd:**
```
date -u +%FT%TZ
nc -z 127.0.0.1 5433 && echo proxy_up            # the EXISTING proxy; start or stop one only if you started it, by recorded PID (G-2)
"$RQ" "select current_user, current_setting('transaction_read_only'), current_setting('server_version'), current_setting('server_version_num'), current_database()"
gcloud config get-value account 2>/dev/null ; gcloud config get-value project 2>/dev/null
```
- **Expect:** `proxy_up`; `suvarna_reader|on|15.<minor>|1500xx|amjis` (last read 2026-10-04: `15.18`, `150018`); project `madhav-astrology`; the gcloud account is the production identity that can `scheduler jobs pause|resume`, `run jobs execute|describe`, `logging read`.
- **ABORT:** `current_user` not `suvarna_reader`, or `transaction_read_only` not `on`, or the server MAJOR is not 15 (the D6 admin grant is PG15-only; a PG16+ upgrade re-opens it), or the proxy is down. **Safe:** production untouched; tell SS (a major upgrade needs a new D6 proof before the window). ALERT SS and Pravāha.
- **Evid:** `$EV/W0/W0.2_host.txt`.

### W0.2B On-demand Cloud SQL BACKUP (N-122; the window does NOT start until it reports SUCCESSFUL)
- **Who:** operator. **Pre:** W0.2. Non-destructive.
- **Cmd:**
```
ps -axo command | grep -o 'madhav-astrology:[a-z0-9-]*:[a-z0-9-]*' | sort -u                  # the standing proxy's instance: expect madhav-astrology:asia-south1:amjis-postgres
export SQL_INSTANCE=amjis-postgres                                                           # the other instance, amjis-ri02-validation-c720f1832, is NOT production
gcloud sql instances describe $SQL_INSTANCE --project=madhav-astrology --format='value(connectionName,state,settings.backupConfiguration.enabled,settings.backupConfiguration.pointInTimeRecoveryEnabled)'
gcloud sql backups create --instance=$SQL_INSTANCE --project=madhav-astrology --description="S-L1 pre-window $(date -u +%FT%TZ)"      # waits for completion
gcloud sql backups list --instance=$SQL_INSTANCE --project=madhav-astrology --limit=3 --format='value(id,type,status,enqueuedTime,endTime)'
```
- **Expect:** the proxy serves `amjis-postgres` (verified 2026-10-04); instance `RUNNABLE`, automated backups enabled, point-in-time recovery DISABLED (read 2026-10-04: so the on-demand backup is the only restore point of the pre-window state apart from the daily automated one); the new row is `ON_DEMAND` `SUCCESSFUL`. Record its ID and completion time in `$EV/W0/W0.2B_backup.txt`. (Precedent: ON_DEMAND backups `1790969348793` 2026-10-02 and `1790839159164` 2026-10-01 were SUCCESSFUL.)
- **ABORT:** the backup is not SUCCESSFUL, or the proxy serves another instance: the window does not start. ALERT SS and Pravāha. **Safe:** production untouched.
- **RESTORE RULE (G-14):** restoring this backup is destructive (it replaces the instance's data) and is THE OWNER'S DECISION ALONE; no step of this runbook restores it, and every abort path reaches a safe state without it.
- **Evid:** `$EV/W0/W0.2B_backup.txt` (backup id, completion time).

### W0.3 Ephemeris corpus pins (host copy)
- **Who:** operator. **Pre:** W0.2.
- **Cmd:** `cd /Users/Dev/suvarna-evidence/Se1 && shasum -a 256 -c PINS.txt && shasum -a 256 sepl_18.se1 semo_18.se1 seas_18.se1`
- **Expect:** three `OK` lines; the three hashes equal section 1.6. (Use `shasum -a 256 -c PINS.txt`; do NOT hand-roll a loop: an earlier hand-rolled zsh check printed a FALSE `OK` because `set -- $p` did not word-split and an empty hash matched an empty hash.)
- **ABORT:** any hash differs. **Safe:** untouched; tell SS (every local runner and the image comparison use this corpus). ALERT SS and Pravāha.
- **Evid:** `$EV/W0/W0.3_se1.txt`.

### W0.4 Code and merge state; deploy settled; digest facts; the clean checkout
- **Who:** operator. **Pre:** W0.2.
- **Cmd** (a worktree is a clean checkout: the dirty state of `/Users/Dev/Vibe-Coding/Apps/Madhav` does not carry; a fetch updates remote-tracking refs only):
```
git -C /Users/Dev/Vibe-Coding/Apps/Madhav fetch origin
TIP=$(git -C /Users/Dev/Vibe-Coding/Apps/Madhav rev-parse origin/main) ; echo "$TIP"
git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree add --detach /Users/Dev/suvarna-window/main_$TIP $TIP
export MAIN=/Users/Dev/suvarna-window/main_$TIP ; cd "$MAIN"                 # EVERY git command below runs in $MAIN
for s in e9e96d759 f035d9e21 a5b3b7b26 297c09c79 a043398c6; do git merge-base --is-ancestor $s HEAD && echo "ancestor $s"; done
#   e9e96d759 = #2984 integration, f035d9e21 = #2986 between-state disclosure, a5b3b7b26 = #2858 F-A2 writer,
#   297c09c79 / a043398c6 = E3.2 build-engine landing commits (E3.7)
gh run list --workflow=deploy.yml --branch=main --limit 6 --json databaseId,status,conclusion,headSha,createdAt      # workflow file name: deploy.yml (W1 privilege audit)
python3 - <<'PY'
import json,subprocess
def inv(ref):
    return json.loads(subprocess.check_output(["git","show",ref+":platform/src/generated/nirmana-writer-digests.json"]))
a,b=inv("a5b3b7b26"),inv("HEAD")
wa,wb=a.get("writers",a),b.get("writers",b)
print("ga_vargas at HEAD:",wb["ga_vargas"])
bad=[k for k in sorted(wa) if k.startswith("ga_") and wa[k]!=wb.get(k)]
print("ga_* digests that differ from a5b3b7b26:",bad)
PY
```
- **Expect:** five `ancestor` lines; the newest `deploy.yml` run on main `completed` / `success` (no run in progress); `ga_vargas at HEAD: 9212b478621c3572e75f606819e865de768b6212def695cf67bd368e0510e8a1`; `ga_* digests that differ ...: []`.
- **ABORT:** a missing ancestor; a deploy still running; `ga_vargas` digest different from `9212b478...` or any `ga_*` digest differs from the rehearsed tree (the rehearsal and the D6 bound hash assumed these bytes). **Safe:** untouched. ALERT SS and Pravāha. The D6 bound hash is VOID if the `ga_vargas` digest moved: SS re-freezes and re-approves.
- **Evid:** `$EV/W0/W0.4_code_state.txt`.

#   e9e96d759 = #2984 integration, f035d9e21 = #2986 between-state disclosure, a5b3b7b26 = #2858 F-A2 writer,
#   297c09c79 / a043398c6 = E3.2 build-engine landing commits (E3.7)
gh run list --workflow=deploy.yml --branch=main --limit 6 --json databaseId,status,conclusion,headSha,createdAt
python3 - <<'PY'
import json,subprocess
def inv(ref):
    return json.loads(subprocess.check_output(["git","show",ref+":platform/src/generated/nirmana-writer-digests.json"]))
a,b=inv("a5b3b7b26"),inv("origin/main")
wa,wb=a.get("writers",a),b.get("writers",b)
print("ga_vargas at origin/main:",wb["ga_vargas"])
bad=[k for k in sorted(wa) if k.startswith("ga_") and wa[k]!=wb.get(k)]
print("ga_* digests that differ from a5b3b7b26:",bad)
PY
```
- **Expect:** five `ancestor` lines; the newest `deploy.yml` run on main `completed` / `success` (no run in progress); `ga_vargas at origin/main: 9212b478621c3572e75f606819e865de768b6212def695cf67bd368e0510e8a1`; `ga_* digests that differ ...: []`.
- **ABORT:** a missing ancestor; a deploy still running; `ga_vargas` digest different from `9212b478...` or any `ga_*` digest differs from the rehearsed tree (the rehearsal and the D6 bound hash assumed these bytes). **Safe:** untouched. The D6 bound hash is VOID if the `ga_vargas` digest moved: SS re-freezes and re-approves; if another `ga_*` digest moved, SS decides whether the rehearsal still covers it. ALERT SS and Pravāha.
- **Evid:** `$EV/W0/W0.4_code_state.txt`.

### W0.5 Tooling checkout, interpreter, hash-pinned scripts, bound hashes reproduced
- **Who:** operator. **Pre:** W0.4. The D6 checkout is a CLEAN checkout of the PR #2964 head AFTER the re-freeze commits `be83fc6fc`, `217349ff6` and the tests-only `299f2b6e9` (the local head of `/Users/Dev/suvarna-d6rf` on 2026-10-04; tests only, the plan hash is unchanged by it) are pushed and merged per the plan (N-122)  (the sha is known only then, S-4).
- **Cmd:**
```
git -C /Users/Dev/Vibe-Coding/Apps/Madhav fetch origin
D6SHA=<the #2964 head sha after the push and merge>
git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree add --detach /Users/Dev/suvarna-window/d6_$D6SHA $D6SHA
export D6=/Users/Dev/suvarna-window/d6_$D6SHA
export PY=<ONE absolute path to a python3.11+ with psycopg 3>        # chosen once; recorded; reused for EVERY dry run and apply (G-7)
"$PY" -c "import sys,psycopg;print(sys.executable, sys.version.split()[0], psycopg.__version__, psycopg.pq.version())"
cd "$WS" && shasum -a 256 -c MANIFEST.sha256                         # the hash-pinned local scripts (with_app_db.py, image_routeB.py, t4_stale_prod.py, wstep_checks_prod.py, h_extract.py, rotate_reader_password.py): every line OK
"$PY" with_app_db.py --selftest                                       # synthetic urls only: no secret is touched
cd "$D6/00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening"
shasum -a 256 d6_dataplane_capture_fa2_exec.py d6_f_a2_key_widening_DRAFT.py
"$PY" make_plan.py                       # NO --write: prints, writes nothing
cd ../gate_v2 && shasum -a 256 prerun_gate.py run_gated.sh executor_standards.py
cd "$MAIN" && shasum -a 256 platform/scripts/governance/flip_detector.py 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/composite_shift_check.py platform/python-sidecar/scripts/build_fact_identity_index.py
```
- **Expect:** executor `0437cc8f...db5e5`; F-A2 module `c911c239...0565`; `make_plan.py` last line `PLAN HASH : f7915138b0a9ba8ad5fea98d3d7ba9311a1acbcd2065138d58ff0a595250b706 (NOT FINAL: the plan is not frozen)` (the approved hash, N-122) and `plan hash unbound : 8410f83c...`; the three gate shas equal the pins in section 1.6; `flip_detector.py` `cabb8186...`; `composite_shift_check.py` `1a7dc58e...e728`; the MANIFEST check all `OK`.
- **ABORT:** any hash differs (bound hash void). **Safe:** untouched. ALERT SS and Pravāha.
- **Evid:** `$EV/W0/W0.5_tooling.txt`.

### W0.6 Registry, ledger and D6 pre-state preconditions (read-only)
- **Who:** operator. **Pre:** W0.2.
- **Cmd:**
```
"$RQ" "select filename, left(sha256,12), applied_at from _migrations_applied where filename ~ '^(1219|1243|1255)_' order by filename"
"$RQ" "select count(*) from fact_category_ownership"
"$RQ" "select asset_id, is_active, has_writer from asset_registry where asset_id like 'ka_gochara%' order by 1"
"$RQ" "select md5(prosrc), length(prosrc) from pg_proc where proname='l1_data_plane_capture_row'"
"$RQ" "select md5(pg_get_functiondef(p.oid)) from pg_proc p where proname='l1_data_plane_capture_row'"
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f "$D6"/00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening/verify_before_apply.sql )
```
- **Expect:** `1219_...|dc9d65c0c23b`, `1243_ka_gochara_inert_registry_rows.sql|88be3ed59aaa` (the rewritten rows-only file, sha `88be3ed5...`), `1255_...|dbc3e567cb4f`; ownership `236`; six `ka_gochara*` rows including `ka_gochara_v4_41_candidate|f|t` and `ka_gochara_v5|f|t` (the writer-gap pre-flight needs these rows to EXIST; `ORCHESTRATOR_WRITER_GAP_CHECK` stays unset = enforce; the warn env is NOT the route); `md5(pg_get_functiondef)` = `1e079261aa42eb97a1885a48035e7520` (D6 NOT yet applied; the second query's `prosrc` md5 differs by definition and is informational); `verify_before_apply.sql` every row PASS (rows 60 and 61 = migration 1255 prerequisites).
- **ABORT:** a ledger row missing or a different sha; ownership not 236; a candidate row missing; function md5 already the patched `b2f4242f...` (D6 already applied: the window plan changes, tell SS); any `verify_before_apply.sql` row not PASS. **Safe:** untouched. ALERT SS and Pravāha.
- **Evid:** `$EV/W0/W0.6_registry.txt`, `$EV/W0/verify_before_apply.out`.

### W0.7 No foreign runs (classified); active-run counts; no execution in flight
- **Who:** operator. **Pre:** W0.2. This is the FOREIGN-RUN CHECK reused before every dispatch (W2.1, W3.1) and at W7.11.
- **Cmd:**
```
# every non-terminal run on ANY chart, CLASSIFIED by its assets (the join is what makes it classifiable)
"$RQ" "select r.id, r.chart_id, r.state, r.triggered_by, r.created_at, coalesce(string_agg(a.asset_id, ',' order by a.position), '<no run assets: see scope_target ' || coalesce(left(r.scope_target,80),'') || '>') as assets, coalesce(bool_or(a.asset_id like 'ga\_%'), false) as writes_ga from build_runs r left join build_run_assets a on a.run_id=r.id where r.state not in ('completed','failed','stopped') group by r.id order by r.created_at"
"$RQ" "select a.asset_id, count(*) from build_runs r join build_run_assets a on a.run_id=r.id where a.asset_id in ('ga_vargas','ga_medical') and r.state not in ('completed','failed','stopped') group by 1"
gcloud run jobs executions list --job=$JOB --region=$REGION --project=$PROJECT --limit=5
```
- **Expect:** zero non-terminal runs on any chart (read 2026-10-04: 0); no `ga_vargas` / `ga_medical` run; no running execution.
- **Classification (used everywhere a foreign run is found):** (a) RECALIBRATION = every asset in `{mi_jivanaghatana, mi_pramana, ph_rectification, ph_pramana}` (enqueued by any `lel_event_record` write): LET FINISH, wait (poll every 10 minutes), never kill, never block people's entries (N-46); (b) FOREIGN `ga_*` = `writes_ga` true, or a run with no assets and a scope that could include `ga_*` (a layer/chart scope): ABORT TRIGGER; (c) anything else (other layers, other charts): let finish, record; (d) UNCLASSIFIABLE = treated as (b) until classified. A foreign run that would write `ga_*` is an ABORT trigger: do not proceed. **Safe:** untouched. ALERT SS and Pravāha.
- **Evid:** `$EV/W0/W0.7_runs.txt`.

### W0.8 Row-count baselines
- **Who:** operator. **Pre:** W0.7.
- **Cmd:** `"$RQ" "select (select count(*) from chart_facts where chart_id='$C'), (select count(*) from chart_vichara where chart_id='$C'), (select count(*) from chart_divisionals where chart_id='$C'), (select count(*) from chart_dashas where chart_id='$C')"`; and, as the 'nothing else moved' baseline for W7.11: `"$RQ" "select 'chart_facts', chart_id, count(*) from chart_facts group by 2 union all select 'chart_dashas', chart_id, count(*) from chart_dashas group by 2 union all select 'chart_divisionals', chart_id, count(*) from chart_divisionals group by 2 union all select 'chart_vichara', chart_id, count(*) from chart_vichara group by 2 order by 1,2" > "$EV/W0/pre_counts_all_charts.tsv"`.
- **Expect:** `143299|8524|24392|483870` (read 2026-10-04); the all-charts file is a record (the other two canonical charts, `1c826d5a-41cb-4450-b4dc-59d440e5f75a` and `cb73cd3d-9eba-4220-9902-0de91566e980`, are NOT rebuilt by S-L1; compared at W7.11).
- **ABORT:** any mismatch ("a mismatch stops W0": the baselines this runbook's expected values derive from are no longer the production state). **Safe:** untouched; tell SS. ALERT SS and Pravāha.
- **Evid:** `$EV/W0/W0.8_counts.txt`.

### W0.9 The four W0 id maps (N-91 condition 1; the rows are unrecoverable after the rebuild)
- **Who:** operator. **Pre:** W0.8 equal. If a map cannot be captured read-only, S-L1 DOES NOT OPEN.
- **Cmd:**
```
D=/Users/Dev/suvarna-evidence/FactId/W0_S_L1_$(date -u +%Y%m%dT%H%M%SZ) ; mkdir -p "$D"
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -v ON_ERROR_STOP=1 <<SQL
\copy (select fact_id, fact_category, fact_subject, fact_key, ayanamsha_id, formula_id, build_id from chart_facts where chart_id='$C' order by fact_id) to '$D/chart_facts_map.tsv'
\copy (select id, ayanamsha_id, vichara_family, subject, target, domain, varga_id, formula_version, constituent_fact_ids from chart_vichara where chart_id='$C' order by id) to '$D/chart_vichara_map.tsv'
\copy (select id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject from chart_divisionals where chart_id='$C' order by id) to '$D/chart_divisionals_map.tsv'
\copy (select dasha_row_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso from chart_dashas where chart_id='$C' order by dasha_row_id) to '$D/chart_dashas_map.tsv'
SQL
)
wc -l "$D"/*.tsv ; shasum -a 256 "$D"/*.tsv | tee "$D/MAPS.sha256" ; chmod a-w "$D"/* ; export MAPS="$D"      # MAPS is used by W7.8
```
- **Expect:** line counts `143299`, `8524`, `24392`, `483870` (equal W0.8). Column layouts are those of the second rehearsal's maps (chart_facts 7 columns; chart_vichara 9; chart_divisionals: id plus graha, ayanamsha, varga, category, key, fact_subject; chart_dashas: dasha_row_id, ayanamsha, system, level, lord, start_iso). NOTE: the dasha map carries no parent-lord path; per-system shifts by "chain identity" (H23) are taken from the detector report in W7.4, not from this map.
- **ABORT:** a copy error, a count mismatch, or a non-sorted/partial file. **Safe:** untouched (a partial map is discarded under a new folder name; never overwrite). ALERT SS and Pravāha.
- **Evid:** `$D/MAPS.sha256` and the path recorded in `$EV/W0/W0.9_maps.txt` (this path is quoted in the SETTLED-1 notice as "the id-map path").

### W0.10 Detector baselines: flip snapshot, special-lagna snapshot, vichara acceptance, composite margins
- **Who:** operator. **Pre:** W0.9. These MUST be taken before W1 is merged (once W1 applies, the "before" state of the registry is gone; a bad baseline is sticky, re-take it under a new name).
- **Cmd** (from `cd "$MAIN"`; direct connection to the proxy, no pooler, no wrapper):
```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; export FLIP_TIMEOUT_SEC=300 FLIP_SNAPSHOT_DIR="$EV/W0/flip_snapshots"
  python3 platform/scripts/governance/flip_detector.py --snapshot native --out "$EV/W0/snapshot_pre.json.gz" ) | tee "$EV/W0/snapshot_pre.txt"
H=00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; python3 $H/evidence/special_lagna_offset_check.py --snapshot $C --out "$EV/W0/special_lagna_pre.json" )
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f $H/evidence/ga_vichara_writer_ACCEPTANCE.sql ) > "$EV/W0/vichara_acceptance_pre.txt"
python3 $H/evidence/composite_shift_check.py --margins "$EV/W0/snapshot_pre.json.gz" | tee "$EV/W0/composite_margins_pre.txt"
```
- **Expect:** the snapshot's printed `counts:` line equals W0.8 for chart_facts / chart_divisionals / chart_dashas, and `panchanga_daily` equals the reader's own `select count(*) from panchanga_daily` (544 rows on 2026-10-04; the table has no chart column); a `.sha256` sidecar is written; the margins run reports `0 of 1,500 varga labels, 0 of 135 sensitive_degree_check margins and 0 of 15 ayurdaya class margins within bound` with the tightest ratios varga 1.76 (D2700), sensitive_degree_check about 93, ayurdaya about 6,713.
- **ABORT:** exit 5 (READ_ERROR) or 6 (refused: existing file), counts mismatch, a margin within bound (a label could flip: STOP, tell SS). **Safe:** untouched; re-take under a new `--out`. ALERT SS and Pravāha.
- **Evid:** the four files above.

### W0.11 The H hand read-backs, BEFORE
- **Who:** operator. **Pre:** W0.10.
- **Cmd:**
```
python3 "$WS/h_extract.py" "$MAIN/00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/HOOKS_W7_HAND_READBACK_v1_0.md" "$EV/W0/h_sql"     # 50 blocks (H1..H26) + index.tsv
mkdir -p "$EV/W0/h_pre"
while IFS=$'\t' read -r sec k fn n; do [ -z "$sec" ] && continue
  ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -v ON_ERROR_STOP=1 -f "$fn" ) > "$EV/W0/h_pre/${sec}_${k}.out" 2> "$EV/W0/h_pre/${sec}_${k}.err" || echo "ERR $sec $k"
done < "$EV/W0/h_sql/index.tsv"
```
Also run the four S_L1_BETWEEN_STATE statements (Appendix B, BS-0 identity count, BS-1 formula match, BS-2 orphans, BS-3 receipts) into `$EV/W0/h_pre/BS_*.out`.
- **Expect:** 50 `.out` files, no `ERR`; the BEFORE values equal the baselines printed in the H document (H1 Sun 5, H2 1,620, H6 8,524 / 8,250, H10 per-ayanamsha level counts, H22 ten rows with `id_identical` t and build `1c092ffb-72eb-4614-8422-552ca6eae985`, H23 five groups with build `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb`, H24 the 20 digest lines, H25 the 161-row census whose sha256 must equal `515cfe9ab0c2e964c844e91b3346e42af3ecf1330e90e3cdbd341e1d6b900353` = `H_TIER_BASELINE_2026-10-03.tsv`, H26 1,200 Aries rows, BS-0 `1205`, BS-1 `143299|1205|2925`, BS-2 `chart_vichara|22108|0` and `ga_yoga_firings|145|0`).
- **ABORT:** a BEFORE value differs from its documented baseline (the expected AFTER values were derived from that baseline): STOP and tell SS before W1. **Safe:** untouched. ALERT SS and Pravāha.
- **Evid:** `$EV/W0/h_pre/`.

### W0.12 Build-id, category and receipt baselines (for T4 and the receipt check)
- **Who:** operator. **Pre:** W0.10.
- **Cmd:**
```
"$RQ" "select 'chart_facts', build_id::text, count(*) from chart_facts where chart_id='$C' group by 2 union all select 'chart_divisionals', build_id::text, count(*) from chart_divisionals where chart_id='$C' group by 2 union all select 'chart_dashas', build_id::text, count(*) from chart_dashas where chart_id='$C' group by 2 union all select 'chart_vichara', build_id::text, count(*) from chart_vichara where chart_id='$C' group by 2 order by 1,2" > "$EV/W0/pre_build_ids.tsv"
"$RQ" "select ayanamsha_id, fact_category, count(*) from chart_facts where chart_id='$C' group by 1,2 order by 1,2" > "$EV/W0/pre_cat_facts.tsv"
"$RQ" "select system_id, ayanamsha_id, level_n, count(*) from chart_dashas where chart_id='$C' group by 1,2,3 order by 1,2,3" > "$EV/W0/pre_cat_dashas.tsv"
"$RQ" "select ayanamsha_id, varga, fact_category, count(*) from chart_divisionals where chart_id='$C' group by 1,2,3 order by 1,2,3" > "$EV/W0/pre_cat_divs.tsv"
"$RQ" "select asset_id, freshness_state, count(*) from asset_freshness where chart_id='$C' and asset_id like 'ga\_%' group by 1,2 order by 1,2" > "$EV/W0/pre_freshness.tsv"
"$RQ" "select asset_id, md5(integrity_check_sql) from asset_registry where asset_id in ('ga_structural','ga_vargas','ga_medical','ga_sensitive') order by 1" > "$EV/W0/pre_integrity_md5.tsv"
"$RQ" "select asset_id, array_to_string(depends_on, ',') from asset_registry where asset_id in ('ga_dashas','ga_yoga','ga_vargas') order by 1" > "$EV/W0/pre_depends_on.tsv"
"$RQ" "select asset_id, count(*) filter (where retired_at is null), count(*) from asset_output_digest_specs where asset_id in ('ga_structural','ga_vargas') group by 1 order by 1" > "$EV/W0/pre_digest_specs.tsv"
"$RQ" "select asset_id, freshness_state, count(*) from asset_freshness where chart_id='$C' group by 1,2 order by 1,2" > "$EV/W0/pre_freshness_all_assets.tsv"      # for the W7.13 freshness-effect check
"$RQ" "select asset_id, state, last_built_at from asset_throughput where chart_id='$C' order by 1" > "$EV/W0/pre_throughput_all_assets.tsv"
"$RQ" "select asset_id, max(observed_at) filter (where receipt_state='proven'), count(*) filter (where receipt_state<>'proven') from asset_provenance_receipts where chart_id='$C' and asset_id like 'ga\_%' group by 1 order by 1" > "$EV/W0/pre_receipts_ga.tsv"      # = S_L1_BETWEEN_STATE section 6 BEFORE table
```
- **Expect:** `pre_build_ids.tsv` identical to the rehearsal's `rehearsal_final/r2/out/pre/build_ids.tsv` (read identical on production 2026-10-04): 13 rows, `chart_dashas` one build `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb` 483870; `chart_divisionals` one build `0663e31b-f33c-4782-b8fe-1cc4ca37a940` 24392; `chart_vichara` one build `bc1755d5-a576-4fc7-9b7b-faa824f43523` 8524; `chart_facts` ten builds (`15402831...` 335, `1c092ffb...` 1205 [the `ga_positions` build], `1cb0bc48...` 106707, `3001b5ab...` 437, `3ea96f6a...` 8775, `6d8fbbe2...` 6287, `781d6e28...` 130, `7a6f34fb...` 2925, `a1702479...` 2847, `aa9602ce...` 13651); the six assets `fresh`; integrity md5s `ga_medical 0b5d65e4933f10ec95b2db2e7d82289d`, `ga_sensitive 77099c39ae07a2dfb18c8812d9345c2d`, `ga_structural bb9803524a61427e7f4f179a59911e33`, `ga_vargas 255af7c5194553e19f7009c1e8774d8a`; depends_on `ga_dashas {ga_positions}`, `ga_yoga {ga_structural,ga_dashas}`, `ga_vargas {ga_positions}`; digest specs `1|1` for both.
- **ABORT:** any difference from these (W1's before/after tables assume them). **Safe:** untouched. ALERT SS and Pravāha.
- **Evid:** the files above.

### W0.13 Image baseline on record
- **Who:** operator. **Pre:** W0.4.
- **Cmd:** `gcloud run jobs describe $JOB --region $REGION --project $PROJECT --format='value(spec.template.spec.template.spec.containers[0].image)'` and the env-names-only snippet of HOOKS_COMPLETENESS section 10 (prints names, never values).
- **Expect:** the pre-W1 image tag (verified 2026-10-03: `.../amjis/brahma-pipeline:a5b3b7b263a3a41873b939b6b29df28a2025073a`, job generation 625); no `SE_EPHE_PATH` among the env var names (it is baked into the image as `/app/ephe`).
- **ABORT:** none (record only). **Evid:** `$EV/W0/W0.13_image_before.txt`. ALERT SS and Pravāha.

### W0.14 Between-state acceptance call, BEFORE (N-91 condition 3) — **SS**
- **Who:** **SS** (N-122): SS runs the live served calls through the MCP server and saves the outputs under `/Users/Dev/suvarna-evidence/S_L1/window/W0/pre_calls/`. The operator confirms the files exist and reads them.
- **Pre:** #2986 deployed (W0.4).
- **Cmd:** one `judgment_query` and one `assess_*` (for example `assess_career`) on the canonical chart.
- **Expect:** `judgment_flags` does NOT carry `l2_receipts_predate_l1` (flag false); the normal reading-contract sentence "grounded in N resolvable L1 fact reference(s)"; `assess_*`: flag false in `kernel.flags`. `l2_lineage_check_failed` is not set.
- **ABORT:** the flag is already true, or `l2_lineage_check_failed` is set (the detector is broken or L2 is already behind L1): the between-state acceptance cannot work; do not open. ALERT SS and Pravāha. **Safe:** untouched.
- **Evid:** `$EV/W0/pre_calls/` (response bodies, saved by SS).

### W0.15 The owner is not using the chart; no foreign build runs (N-122; KNOWN LIMIT)
- **Who:** operator and SS. N-122 replaces "zero open inquiries": the reader has no SELECT on any `planner_inquiry_*` table (verified 2026-10-04), so open inquiries cannot be counted.
- **Cmd:** (1) record SS's statement that the owner stated he is NOT using the chart (2026-10-02) and that no corpus or calibration run is scheduled until S-L2 closes; (2) the W0.7 foreign-run check (done); (3) nothing else.
- **KNOWN LIMIT (recorded, not closed):** an inquiry started before S-L1 and still open across it gets 409 `CAPABILITY_OVERLAY_STALE` and is simply restarted; no step of this runbook can detect it.
- **ABORT:** the owner states he IS using the chart (the S-L2 clock then collapses to 48 h from that statement, N-91 ruling 3: tell SS before opening), or a scheduled corpus/calibration run. ALERT SS and Pravāha. **Safe:** untouched.
- **Evid:** `$EV/W0/W0.15_owner_statement.txt`.

### W0.16 Window-open announcement, MERGE FREEZE, Pravāha hold
- **Who:** operator; **SS** issues the freeze. **Pre:** W0.2-W0.15 all PASS and W0.2B reports SUCCESSFUL (the window does NOT start otherwise).
- **Cmd:** tracker/STATUS note to SS for Pravāha and the other workstreams: window open at `<UTC>`, expected end, the 6-hour cap, "pause of `watchdog-reaper` will follow at W0.P" (N-93 condition 9). **SS issues a MERGE FREEZE on main to ALL lanes (G-13) for the whole window, until SETTLED-1**, and Pravāha holds its own flow on `482012f1` from now to SETTLED-1. Record the freeze message id.
- **Expect:** the freeze and the hold are acknowledged by every lane. A deploy later than `M1` (ours) means W1.4-W1.8 are redone.
- **ABORT:** a lane cannot freeze, or a merge lands after the freeze: SS decides; do not open W1 until main is stable. ALERT SS and Pravāha. **Safe:** untouched.
- **Evid:** the note text and the freeze message id in `$EV/W0/W0.16_announce.txt`.

**W0 GO / NO-GO.** GO only if W0.2-W0.15 are all PASS, W0.2B reports SUCCESSFUL, and SS has said GO for W1 (gate A2 below). Anything else: the window does not open and production has not been touched.

SS GATES in the window (each is a written message, ids recorded): **A1** RELEASE plus slot (W0.1); **A2** GO to arm and merge the W1 PR (W1.2); **A3** approval of the D6 dry run (D6.4); **A4** approval of the D6 apply (D6.4); **A5** acceptance and S-L1 CLOSE (W7.17); **A6** explicit GO from SS before the FIRST dispatch, after the D6 STATUS (W0.P, N-122); a STATUS message after every part (W1, D6, W2, W3-6, W7), and an immediate ALERT at any abort. The explicit GO before the first dispatch is RULED (N-122, Q-07): gate A6.

---

# PART 3. STEPS: W1 (the seven migrations) and D6 (the owner-path apply)

Ordering rules carried by the migration files themselves: 1221, 1222, 1223, 1226 in ONE deploy, numeric order; 1222 and 1223 BEFORE the F-A2 `ga_vargas` rebuild, never after (1223 applied after leaves the first receipt computed with tied ordering and needs one more rebuild); 1252 AFTER the ga_medical band-lane writer is deployed (it is, via #2984) and BEFORE the `ga_medical` rebuild (its integrity clause reads FALSE on today's rows until that rebuild, by construction); 1254 BEFORE the `ga_sensitive` rebuild (otherwise conjunct (a) fails on the `single` / `computed_extension` tiers the rebuild writes). MERGE = APPLY: `migrate.ts` runs on every deploy, before that deploy's images roll, as `amjis_app`; therefore the W1 PR merges ONLY inside the window and is NEVER armed earlier.

### W1.1 W1 PR readiness (before arming)
- **Shape:** the W1 PR is the SEVEN SQL FILES ONLY (plus the census-regeneration commit `62d0281b2` if the census check requires it), byte-identical to the reviewed source heads; no test, no intent doc, no other file rides in it.
- **Who:** operator. **Pre:** RELEASE (the PR is created and pushed only after it); W0 PASS.
- **Cmd:**
```
cd /Users/Dev/suvarna-w1      # local branch local/w1-migrations: e6ce97f30 = the seven files, 62d0281b2 = census regeneration
git fetch origin && git log --oneline origin/main..HEAD && git rev-list --left-right --count HEAD...origin/main     # expect the two local commits; the right-hand count is how far main has moved since a5b3b7b26 (it HAS moved: merge origin/main into the branch, re-run the number guard, regenerate the census only if its check fails)
for f in 1221_nirmana_l1_ga_structural_a29_integrity_conjunct 1222_nirmana_l1_ga_vargas_integrity_nonvacuity 1223_nirmana_l1_ga_vargas_output_digest_spec_seven_column_key 1224_chart_grants_select_schema_of_record 1226_asset_registry_four_pre_s_l1_edges 1252_nirmana_l1_ga_medical_integrity_band_cut_canonical_scope 1254_nirmana_l1_ga_sensitive_integrity_tier_vocabulary; do shasum -a 256 platform/migrations/$f.sql; done
git ls-tree --name-only HEAD platform/migrations/ | sed 's#platform/migrations/##' | grep '\.sql$' | sort > "$EV/W1/tree_migs.txt"
"$RQ" "select filename from _migrations_applied order by filename" | sort > "$EV/W1/applied.txt"
comm -23 "$EV/W1/tree_migs.txt" "$EV/W1/applied.txt"
( cd platform && npx tsx scripts/ci/migration_number_guard.ts )
```
Push ONLY with an explicit refspec (never a plain `git push`; the branch may carry a remote upstream by default): `git push origin local/w1-migrations:refs/heads/<agreed branch name>` then open the PR with the body `W1_PR_BODY_DRAFT.md` (`gh pr create`). The PR trailer rules of this repository apply.
- **Expect:** the seven shas equal Appendix B (byte-identical to the source PR heads #2900, #2943, #2896, #2898, #2957, #2959); `comm -23` prints EXACTLY the seven W1 filenames and nothing else (anything else would be applied by the same deploy: STOP and tell SS); the number guard prints `PASS - no new migration-number collision` (two advisory header-mismatch warnings are normal: the 1221 header says "Migration 1219", the 1226 header says "Migration 1210"; the files stay byte-identical). If main moved and `capability_estate_census.json` is now stale, regenerate it as a SEPARATE commit (`62d0281b2` regenerated it with `--generated-at=2026-10-04T00:00:00.000Z --source-revision=a5b3b7b263a3a41873b939b6b29df28a2025073a`; member_count 92 to 94, +2 members 1221 and 1223); the seven files must stay unchanged. `migrate.ts` reads TWO folders, `platform/migrations/*.sql` and `platform/supabase/migrations/*.sql` (read from `migrate.ts` at origin/main 2026-10-04, Q-08): compare both against the ledger the same way (902 files on main, 0 unapplied on 2026-10-04). CI green on the EXACT head: the Governance aggregate is a REQUIRED check (rerun only a timeout, never a real failure).
- **ABORT:** a sha differs; an unexpected unapplied migration; CI red on the exact head. **Safe:** nothing merged; production untouched. ALERT SS and Pravāha.
- **Evid:** `$EV/W1/W1.1_pr_ready.txt`, the PR number and head sha.

### W1.2 Arm and merge the W1 PR (SS gate A2)
- **Who:** operator arms after SS says GO (A2). **Pre:** W1.1 PASS; W0.7 repeated immediately before arming (zero non-terminal runs; zero `ga_vargas` / `ga_medical` runs); Pravāha's freeze lifted; nothing else in the merge queue.
- **Cmd:** arm the PR the same way #2984, #2986 and #2858 were armed (N-122: the normal merge queue; arm on SS's approval at the slot; verify by the ledger, W1.4). Record `T_W1 = <UTC>` and the merge commit sha `M1`.
- **Expect:** the PR merges; the deploy of `M1` starts.
- **ABORT:** the queue rejects it, or anything but this PR would deploy. **Safe:** nothing applied; production untouched. ALERT SS and Pravāha.
- **Evid:** `$EV/W1/W1.2_merge.txt`.

### W1.3 The deploy completes; the migrate job ran as `amjis_app`
- **Who:** operator watches. **Pre:** W1.2.
- **Cmd:** `gh run list --workflow=deploy.yml --branch=main --limit 3 --json databaseId,status,conclusion,headSha` then `gh run view <id> --json jobs` and read the real deployed sha from the run log line `Deploying immutable source SHA <sha>` (do NOT trust the run's `headSha` metadata: Trap 103). Poll every 2-3 minutes.
- **MERGE FREEZE (G-13):** a deploy LATER than `M1` (ours) means W1.4-W1.8 are REDONE on the new image before any further step.
- **Expect:** all jobs `success` (gate, migrations "Apply Routine DB Migrations", sidecar, web, "Pipeline Job Image", outcome gate; the MCP job is normally skipped); the `DEPLOY_SHA` equals `M1`; the "Re-point Cloud Run Job" step re-pointed `brahma-build-pipeline-job` to the image tagged `M1`.
- **ABORT:** the migrations job fails. ALERT SS and Pravāha. Consequences (from the W1 privilege audit): the runner is one transaction PER FILE, so files before the failing one stay applied and recorded; the failing file and later ones are not applied; the web and sidecar deploys `need` the migrate job, so the images do NOT roll; the chart data is untouched; the six assets that an applied file already staled stay stale. **Safe state:** W1 is FORWARD-ONLY (accepted, N-122, Q-12: no W1 rollback artifact). Do not proceed to D6. ALERT SS and Pravāha with the failing filename and the error. SS decides roll-forward (retry the deploy) or a corrective migration; nothing is hand-edited.
- **Evid:** `$EV/W1/W1.3_deploy.txt` (run id, conclusion per job, DEPLOY_SHA).

### W1.4 Ledger read-back: filename plus sha256 for each of the seven
- **Who:** operator. **Pre:** W1.3 success.
- **Cmd:**
```
"$RQ" "select filename, sha256 from _migrations_applied where filename ~ '^12(21|22|23|24|26|52|54)_' order by filename"
"$RQ" "select filename from _migrations_applied where applied_at >= '<T_W1 as timestamptz>' order by filename"
```
- **Expect:** seven rows whose sha256 equal Appendix B (1222 = `10b6aac633287d10d13049baacc650a223f5f481f13417a02e02e167c87e3212`, the canonical #2943 file); the second query returns exactly those seven (1224's guarded GRANT is a NOTICE no-op in production).
- **ABORT:** a row missing, a different sha256, or an extra filename. **Safe:** as W1.3 (stop; no D6). ALERT SS and Pravāha.
- **Evid:** `$EV/W1/W1.4_ledger.txt`.

### W1.4B Close the six source PRs (SS ruling): "carried by W1; must not merge"
- **Who:** operator. **Pre:** W1.4 PASSED (the seven ledger rows are in). Same treatment as #2851.
- **Cmd:**
```
W1PR=<number of the W1 PR>
for N in 2900 2943 2896 2898 2957 2959; do gh pr close $N --comment "Carried by W1 (PR #$W1PR, merge $M1); must not merge (double apply of the same migration file)."; done
for N in 2900 2943 2896 2898 2957 2959; do gh pr view $N --json number,state,mergedAt --jq '[.number,.state,(.mergedAt // "not merged")]|@tsv'; done
```
  (#2943 carries two files, 1222 and 1223; #2900 1221; #2896 1224; #2898 1226; #2957 1252; #2959 1254.)
- **Expect:** all six `CLOSED`, none merged. Record the six lines.
- **ABORT:** any PR not CLOSED, or any already MERGED (a double apply is then possible on the next deploy: STOP, ALERT SS and Pravāha). **Safe:** the migrations are already applied once; the open PRs are the only hazard until closed.
- **Evid:** `$EV/W1/W1.4B_prs_closed.txt`.

### W1.5 W1 effect read-back (what changed, and that nothing else did)
- **Who:** operator. **Pre:** W1.4.
- **Cmd:** repeat the `pre_*` queries of W0.12 into `post_*` files, plus `"$RQ" "select count(*) from fact_category_ownership"` and `"$RQ" "select has_table_privilege('data_plane_builder','public.chart_grants','SELECT')"`; then `diff "$EV/W0/pre_freshness.tsv" "$EV/W1/post_freshness.tsv"`.
- **Expect:**
  - integrity md5s: `ga_medical ae453edf2afeeaba086a444c66681676`, `ga_sensitive d6dc29259125e4007c3506a42d983296`, `ga_structural c56f9e12b2002269eb5f27a7abc42105`, `ga_vargas d2f897535c8c6237f464c81f11624701` (before: `0b5d65e4...`, `77099c39...`, `bb980352...`, `255af7c5...`);
  - depends_on: `ga_dashas {ga_positions,ga_sensitive,ga_vargas}`, `ga_yoga {ga_structural,ga_dashas,ga_vargas}`, `ga_vargas {ga_positions,ga_sensitive}`;
  - digest specs: `ga_structural 1|2` and `ga_vargas 1|2` (one active of two total; the old spec is retired, not deleted);
  - freshness: EXACTLY SIX `ga_*` rows went fresh to stale (`ga_structural`, `ga_vargas`, `ga_dashas`, `ga_yoga`, `ga_medical`, `ga_sensitive`), reason `registry_changed`; every other `ga_*` row is unchanged (this is the "6 assets fresh to stale" expectation; it is bounded by the window because all six are rebuilt);
  - `fact_category_ownership` still `236` (the 67 to 236 move was 1219, already applied); `has_table_privilege(...)` `t` (1224 no-op);
  - `ga_medical`'s own integrity clause reads FALSE until the ga_medical rebuild (15 canonical rows still labelled `mild`): expected, not a failure.
- **ABORT:** any md5 or edge differs; a seventh stale row or a different set; a spec count other than 1|2. **Safe:** stop; no D6; ALERT SS and Pravāha (forward-only).
- **Evid:** `$EV/W1/W1.5_effect.txt`, `post_*.tsv`.

### W1.6 Image verification REPEATED, part 1: job definition and tag
- **Who:** operator. **Pre:** W1.5 PASS. (W2 precondition, SS: the image that exists AFTER the W1 deploy; Pravāha's train and our W1 PR each trigger a deploy, so the tag at this point is NEWER than the one verified on 2026-10-03, `a5b3b7b26`.)
- **Cmd:**
```
gcloud run jobs describe $JOB --region $REGION --project $PROJECT --format='value(spec.template.spec.template.spec.containers[0].image)'
gcloud run jobs describe $JOB --region $REGION --project $PROJECT --format=json | python3 -c "import sys,json;j=json.load(sys.stdin);c=j['spec']['template']['spec']['template']['spec']['containers'][0];print([e['name'] for e in c.get('env',[])]);print(c.get('command'),c.get('args'),c.get('resources'));print(j.get('metadata',{}).get('generation'))"
git -C "$MAIN" rev-parse $M1   # and the Deploying-immutable-source-SHA line of W1.3
```
- **Expect:** image `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:<DEPLOY_SHA>` where the tag is a NEWER commit than `a5b3b7b26`, EQUAL to `M1` (or to a later deploy if Pravāha deployed after us: then it equals that deploy's sha, and the checkout used for W2/W3 must be that sha); env names: `MARSYS_REPO_ROOT, GCP_PROJECT, PUBSUB_TOPIC, ORCHESTRATOR_WORKER_LIMIT, WRITER_TIMEOUT_SECONDS, KA_KSHETRA_HASH_SPILL_DIR, DATABASE_URL` and NO `SE_EPHE_PATH` (it is baked into the image as `/app/ephe`); no command / args override; cpu 4, memory 16Gi. Call this sha `IMG_SHA` from here on (it is also the `--writer-commit` and the dispatcher `--deployed-sha`). RE-SET THE CHECKOUT: `git -C /Users/Dev/Vibe-Coding/Apps/Madhav fetch origin && git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree add --detach /Users/Dev/suvarna-window/main_$IMG_SHA $IMG_SHA && export MAIN=/Users/Dev/suvarna-window/main_$IMG_SHA` (from now on `cd "$MAIN"` is HEAD == `IMG_SHA`; `git -C "$MAIN" rev-parse HEAD` must print `$IMG_SHA`).
- **ABORT:** tag not equal to the deploy sha; an env override of the ephemeris path; a command override; `ORCHESTRATOR_WRITER_GAP_CHECK` among the env NAMES (the writer-gap pre-flight must stay in `enforce` mode, unset: abort if it appears).  **Safe:** untouched beyond W1; no D6, no builds; ALERT SS and Pravāha.
- **Evid:** `$EV/W1/W1.6_image_job.txt`.

### W1.7 Image verification REPEATED, part 2: ephemeris files, library versions, source layers (route B, STREAMED, read-only)
- **Who:** operator. **Pre:** W1.6. N-122: NO docker login, NO pull. One route only: the registry layers are STREAMED and hashed in memory (nothing written but a small JSON). The route is proved: `window_scripts/image_routeB.py` (generalised from the image-verify worker's `reg.py` / `lay.py` / `cmp.py`; it finds the pip layer as the largest layer and the ephemeris layers by content, honours whiteouts, and needs no hard-coded layer index) was run read-only on 2026-10-04 against the then-current image `a5b3b7b26`: `config`, the three `.se1` files, the eight library versions and the `swisseph` binary all PASS (about 10 minutes, mostly the 3.5 GB pip layer); the source-layer comparison PASSes after the one path mapping `/app/requirements.txt` to `platform/python-sidecar/requirements.txt` (`Dockerfile.pipeline` line 30).
- **Cmd:**
```
cd "$WS" && runx "$EV/W1/image_routeB" "$PY" image_routeB.py "$IMG_SHA" --src "$MAIN" --out "$EV/W1/image_routeB.json"
```
  (The access token is read in-process from `gcloud auth print-access-token`; it is never printed.)
- **Expect:** `PASS config` (Python 3.11.17, `SE_EPHE_PATH=/app/ephe`, amd64, entrypoint `python -m pipeline.orchestrator.main`); `PASS ephe sepl_18.se1 / semo_18.se1 / seas_18.se1` (sizes 484061 / 1304771 / 223004, sha256 equal the pins of section 1.6); `PASS version` for pyswisseph 2.10.3.2, pyjhora 4.8.6, numpy 2.4.6, scipy 1.17.1, psycopg 3.3.6, psycopg-binary 3.3.6, psycopg2-binary 2.9.13, timezonefinder 9.0.0; `PASS swisseph binary` (sha256 `3911614ca013be4520e355306620a3fcd27a39374a960a2063b056cfbd093338`); `PASS source layers == worktree` (about 865 files, 0 diff, 0 missing); last line `ROUTE_B PASS`, exit 0.
- **ABORT / STOP:** ANY FAIL line for pyswisseph, pyjhora, the binary or any `.se1` = STOP (the whole rehearsal and the expected shifts are void). A FAIL ONLY on numpy, scipy, psycopg, psycopg-binary, psycopg2-binary or timezonefinder = go to W1.9 (confirmatory lanes) before anything else. A source-layer diff = STOP (the image is not the commit). ALERT SS and Pravāha. **Safe:** no D6, no builds.
- **Evid:** `$EV/W1/image_routeB.*`.

### W1.8 Image verification REPEATED, part 3: writer inventory, ancestors, foreign runs
- **Who:** operator. **Pre:** W1.6.
- **Cmd:**
```
cd "$MAIN"                                                   # already detached at IMG_SHA (W1.6)
( cd "$MAIN/platform/python-sidecar" && SE_EPHE_PATH=/Users/Dev/suvarna-evidence/Se1 PYTHONPATH=$PWD "$PY" -m pipeline.orchestrator.provenance_inventory --check ; echo rc=$? )
python3 - <<'PY'      # ga_* digests unchanged versus the rehearsed tree; list what moved
import json,subprocess,os
def inv(ref): return json.loads(subprocess.check_output(["git","-C",os.environ["MAIN"],"show",ref+":platform/src/generated/nirmana-writer-digests.json"]))
a,b=inv("a5b3b7b26"),inv("HEAD")
wa,wb=a.get("writers",a),b.get("writers",b)
print("ga_vargas:",wb["ga_vargas"])
print("ga_* moved:",[k for k in sorted(wa) if k.startswith("ga_") and wa[k]!=wb.get(k)])
print("ka_gochara* moved:",[k for k in sorted(wa) if k.startswith("ka_gochara") and wa[k]!=wb.get(k)])
PY
git merge-base --is-ancestor 297c09c79 $IMG_SHA && git merge-base --is-ancestor a043398c6 $IMG_SHA && echo E3.7_ancestors_ok
"$RQ" "select count(*) from build_runs where state not in ('completed','failed','stopped')"
```
- **Expect:** `provenance_inventory --check` rc 0; `ga_vargas: 9212b478621c3572e75f606819e865de768b6212def695cf67bd368e0510e8a1`; `ga_* moved: []`; `ka_gochara* moved:` the list of Pravāha's writers (Pravāha's `ka_gochara` digests MOVED, as expected); `E3.7_ancestors_ok` (the build-engine landing commits E3.2-build-001 `297c09c79` and E3.2-build-002b `a043398c6` are ancestors of the running job image's source commit: the plan item E3.7); zero non-terminal runs.
- **ABORT:** inventory check rc != 0; any `ga_*` digest moved (including `ga_vargas`: D6 hash void); ancestors missing; a non-terminal run (foreign-run rule of W0.7). **Safe:** no D6, no builds; ALERT SS and Pravāha.
- **Evid:** `$EV/W1/W1.8_inventory.txt`.

### W1.9 Confirmatory lanes (ONLY if W1.7 showed a numpy / scipy / psycopg-family difference)
- **Who:** operator with SS. **Named lanes (N-122, Q-09; taken from `REHEARSAL_LINUX_REPORT.md` T1, the lanes compared Linux against macOS):** the four ephemeris-calling lanes `ga_positions`, `ga_panchanga`, `ga_sensitive`, `ga_vargas`, plus `ga_dashas` (T1 rows: dashas 483,855 / divisionals 38,596 / panchanga 437 / positions 146 rows differing by at most 1.02e-12 deg / sensitive 564 rows differing only in the last printed digit of `citation_human`). Run these five lanes inside the NEW image against a disposable database and compare with the second rehearsal's outputs.
- **Expect:** identical row sets and values within the T1 tolerances. **ABORT:** any difference: STOP, ALERT SS and Pravāha. If W1.7 was fully identical this step is "not triggered" (record that).
- **Evid:** `$EV/W1/W1.9_confirmatory.txt`.

---

### D6.1 D6 pre-flight (all read-only)
- **Who:** operator. **Pre:** W1.4-W1.8 PASS (the gate refuses while any deploy run is not completed).
- **Cmd:** repeat W0.2 (PostgreSQL major; STOP if not 15), W0.7 (no run on any chart), W0.6 last two queries (function md5 `1e079261aa42eb97a1885a48035e7520`; `verify_before_apply.sql` every row PASS, run from the D6 checkout), and set:
```
WC=$IMG_SHA                          # --writer-commit: the deployed image tag; the executor refuses unless tag == WC and the ga_vargas digest == 9212b478...
PLAN=f7915138b0a9ba8ad5fea98d3d7ba9311a1acbcd2065138d58ff0a595250b706       # the SS-approved bound hash (N-122)
cd "$D6/00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening" ; GATE=../gate_v2/run_gated.sh
git fetch origin && git cat-file -e "$WC^{commit}" && echo "WC present in the D6 repo"      # pre_writer_first reads `git show $WC:...nirmana-writer-digests.json` IN THIS REPO
test -w /Users/Dev/suvarna-evidence && echo "evidence parent writable"                      # the executor itself creates /Users/Dev/suvarna-evidence/DataPlaneCaptureFA2 and the run directories
```
- **The three causes of a `pre_writer_first` refusal (read from `d6_f_a2_key_widening_DRAFT.py` `writer_check`):** (1) `writer image check failed` / UNVERIFIED: `WC` is not a full 40-hex sha, or the commit is not present in the D6 repo (`git show` fails: fetch and cat-file as above), or `gcloud run jobs describe` fails; (2) the job image TAG is not exactly `WC` (another deploy landed, or `WC` is wrong); (3) the `ga_vargas` digest at `WC` is not `9212b478...` (the frozen digest moved: the bound hash is VOID, re-freeze).
- **Expect:** all as W0; `PY` is the W0.5 interpreter; `WC present in the D6 repo`.
- **ABORT:** major != 15; any run in flight; function md5 already patched; a PASS row missing; `WC` absent. ALERT SS and Pravāha. **Safe:** untouched.
- **Evid:** `$EV/D6/D6.1_preflight.txt`.

### D6.2 D6 `--count` (read-only, always rolled back)
- **Who:** operator (executor connects as `postgres` through the proxy; the credential is fetched in-process after the plan hash matches). Run under bash; the banner is SEEN (G-10 `runx`).
- **Cmd:** `runx "$EV/D6/count" "$GATE" "$PY" d6_dataplane_capture_fa2_exec.py --count --expect-plan "$PLAN" --writer-commit "$WC"`
- **Expect:** terminal and `count.stderr`: `run_gated: python3=... gh=... psql=... bash=...`, then `GATE_V2 deploy_runs_not_completed=0 build_runs_in_flight=0 role=suvarna_reader OK`, then `run_gated: gate OK; GATE_V2_LAUNCH set; starting target`; stdout JSON status `COUNT_READ_ONLY_OK`; the writer-first line `ga_vargas digest at <WC first 12> = 9212b478621c...`; the interpreter record (path, full `sys.version`, psycopg, libpq); `exit=0`; `outcome.json` in the new run directory.
- **ABORT:** any `REFUSED:` line, `exit` != 0. Read the banner first (G-5): the gate's own codes are 1 (a deploy or build in flight), 2 (a read failed), 94 (missing binary), 95 (test env), 96 (wrong role/database: nothing ran), 97 (pgenv failed), 98 (target not executable), 64 (usage); the executor's are 92 (interpreter / driver), 93 (not launched by the gate or a gate pin unbound), 95 (test env), 1 (refused), 2 (dry run or count refused). A `pre_writer_first` refusal: the three causes of D6.1. ALERT SS and Pravāha. **Safe:** count changes nothing.
- **Evid:** `$EV/D6/count.*` and the run directory path.

### D6.3 D6 `--dry-run` (applies everything, runs every commit condition, ROLLS BACK)
- **Who:** operator.
- **Cmd:** `runx "$EV/D6/dry" "$GATE" "$PY" d6_dataplane_capture_fa2_exec.py --dry-run --expect-plan "$PLAN" --writer-commit "$WC"` and then re-run `verify_before_apply.sql` (the dry run must have left everything unchanged).
- **Expect:** `exit=0`; status `DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD`; `commit conditions: ALL HOLD`; NO `REFUSED: the administrator cannot assume the owner roles` (the PG15 `GRANT <role> TO CURRENT_USER` works for `postgres`); `post_membership_equals_pre_state_after_revoke` true; the ACCESS EXCLUSIVE window measured (rehearsal: 170 ms, 65 statements; the plan refuses above 100 statements; `lock_timeout` 5 s, `statement_timeout` 120 s); the printed EVIDENCE DIGEST (record it exactly: `EVD`; the rehearsal's `bfe08a3c...` is NOT comparable, it binds the interpreter path); `outcome.json` status `dry_run`; `verify_before_apply.sql` still every row PASS (32 rows: 31 PASS + 1 INFO on 2026-10-04); function md5 still `1e079261...`.
- **ABORT:** any failed check (`exit=2`, `failed_checks` non-empty), any `REFUSED`, a lock timeout (a concurrent reader of `chart_divisionals` or `chart_vichara` made the rehearsal fail after 5.0 s and roll back clean: retry once the table is quiet, as a NEW dry run with a NEW digest). ALERT SS and Pravāha. **Safe:** nothing changed; verify with the function md5.
- **Evid:** `$EV/D6/dry.*`, `EVD`.

### D6.4 SS gates A3 and A4; the owner's authorisation line
- **Who:** SS; operator sends. **Pre:** D6.3 PASS.
- **Cmd:** send SS: `EVD`, the checks list, the measured window, the interpreter record, `PLAN`, the plan file path and its sha256 (`shasum -a 256` of `D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN_DRAFT.md`; its module-sha lines were re-frozen, so the sha256 differs from any earlier quoted value). The owner's authorisation (plan section 1) names the plan hash, the plan file path and sha, the five items (option A / N-84; patch B and patch C / N-85; K1; F-A2) and the transient grants `GRANT data_plane_l1_owner, amjis_app TO CURRENT_USER` revoked in the same transaction; RULED (N-122, Q-10): the standing delegation covers, verbatim, "running owner-path plans on production for plan hashes Strategic Suvarna approves"; the approved hash is `f7915138b0a9ba8ad5fea98d3d7ba9311a1acbcd2065138d58ff0a595250b706`. SS still gives A3 and A4 as written messages.
- **Expect:** A3 (approval of the dry run) THEN A4 (approval to apply), both as written messages with ids.
- **ABORT:** no approval: do not apply. **Safe:** dry run left nothing; the window can pause here (the watchdog is NOT yet paused). ALERT SS and Pravāha.
- **Evid:** `$EV/D6/D6.4_approvals.txt`.

### D6.5 D6 `--apply`
- **Who:** operator. **Pre:** D6.4; the SAME `PY`, the SAME checkout; re-run W0.7 (no run in flight).
- **Cmd:** `runx "$EV/D6/apply" "$GATE" "$PY" d6_dataplane_capture_fa2_exec.py --apply --expect-plan "$PLAN" --expect-evidence "$EVD" --writer-commit "$WC"`
- **Expect:** `exit=0`; stdout JSON status `COMMITTED`; `commit conditions: ALL HOLD`; `interpreter check: same interpreter as dry run`; `outcome.json` status `applied`; membership of `postgres` equals the pre-state (the transient grants are revoked in the same transaction).
- **READING `exit=1` (verified against the executor's `main()`, `execute()` and `refuse()` in `d6_dataplane_capture_fa2_exec.py`; exit 1 has THREE shapes and the number alone cannot tell them apart):**
  1. stdout JSON with `"status": "REFUSED_ROLLED_BACK"` (and `failed_checks`): the transaction was rolled back; the state is the pre-state (verify with the function md5).
  2. stderr `REFUSED: ...` with NO JSON (a `SystemExit` string raised before any connection: plan-hash mismatch, missing `--expect-evidence`, missing `--writer-commit`): nothing connected, nothing changed.
  3. stdout `failed: <ExceptionClass> ...` and/or stderr `WARNING: COMMIT STATE UNKNOWN (...)`: `conn.commit()` itself raised, or `run_leg` raised: the server MAY have committed.
  **THE RULE: `exit=1` WITHOUT a `REFUSED_ROLLED_BACK` status in the JSON = go to D6.8 (read-only verification) and run NOTHING else until it has decided.** D6.8 is harmless in shapes 1 and 2 (it will read the pre-state).
- **Other codes:** 92 interpreter or driver differs from the dry run (nothing connected): use the SAME path; if it cannot be reproduced, repeat the dry run (new digest, new A3/A4). 93 / 95 / gate codes (94, 96, 97, 98): the launch was refused before anything ran (`run_gated: gate exit=N; target NOT started` on stderr).
- **Safe:** before the commit everything rolls back; after it D6 is applied (D6.7 is the only rollback window). ALERT SS and Pravāha on any ABORT.
- **Evid:** `$EV/D6/apply.*` (`apply.stderr`, `apply.stdout`, `apply.exit`), the run directory under `/Users/Dev/suvarna-evidence/DataPlaneCaptureFA2/`.

### D6.6 D6 verification (reader)
- **Who:** operator. **Pre:** D6.5 `COMMITTED`.
- **Cmd:**
```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f verify_after_apply.sql ) | tee "$EV/D6/verify_after_apply.out"
"$RQ" "select p.proname, md5(pg_get_functiondef(p.oid)) from pg_proc p where p.proname in ('l1_data_plane_capture_row','capture_l1_data_plane_dasha_partition','complete_l1_data_plane_partition') order by 1"
"$RQ" "select pg_get_indexdef(i.indexrelid) from pg_index i join pg_class c on c.oid=i.indexrelid where c.relname='chart_divisionals_unique_idx'"
"$RQ" "select tgrelid::regclass, pg_get_triggerdef(t.oid) from pg_trigger t where tgname='l1_data_plane_capture' and tgrelid in ('chart_divisionals'::regclass,'chart_vichara'::regclass)"
```
- **Expect:** every `verify_after_apply.sql` row (32 rows: 30 PASS and 2 INFO, 0 FAIL (the rehearsal: 30 PASS, 0 non-PASS; the file has 32 rows on production, read 2026-10-04; before D6 it reads 12 PASS / 18 FAIL / 2 INFO, which is the expected pre-state)); function md5s `capture_row b2f4242f034d1a3983edb08c625dc353`, `capture_l1_data_plane_dasha_partition 873ee5da411f4e6366ec3faed98c3ae2`, `complete_l1_data_plane_partition 31d005e8ecacf40547f0537e24d717d5`; the unique index lists seven columns ending `fact_subject` (NULLS NOT DISTINCT); the `chart_divisionals` trigger has 7 arguments (adds `'fact_subject'`) and the `chart_vichara` trigger 9 (adds `'constituent_fact_ids'`).
- **ABORT:** any FAIL or mismatch. ALERT SS and Pravāha. **Safe:** D6 is applied; NO build has started; SS decides between D6.7 (rollback) and a forward repair; the watchdog is not yet paused.
- **Evid:** `$EV/D6/D6.6_verify.txt`. Then send SS the D6 STATUS (Q-07).

### D6.7 D6 rollback leg (CONDITIONAL; the only rollback window is BEFORE the first `ga_vargas` rebuild)
- **Who:** operator on SS's decision. **Pre:** no build has run since D6.5 (no widened `chart_divisionals` rows exist; the rollback refuses otherwise: "once a rebuild stored the extra `ga_vargas` rows the old narrow index cannot be re-created; those rows must be deleted first", and no such deletion is authorised in this runbook); no run in flight; the gate green.
- **Cmd:** `runx "$EV/D6/rollback_dry" "$GATE" "$PY" d6_dataplane_capture_fa2_exec.py --rollback-dry-run --expect-plan "$PLAN"` then `runx "$EV/D6/rollback" "$GATE" "$PY" d6_dataplane_capture_fa2_exec.py --rollback --expect-plan "$PLAN" --expect-evidence "<digest printed by the rollback dry run>"`, then `verify_before_apply.sql`. The same `exit=1` rule as D6.5 applies.
- **Expect:** `--rollback` `COMMITTED`; every function md5, attestation row, index, trigger, comment and ACL back to the pre-state (function md5 `1e079261...`); `verify_before_apply.sql` every row PASS.
- **ABORT:** the rollback refuses (widened rows exist): do NOT improvise; ALERT SS and Pravāha (forward repair only). **Safe state after a successful rollback:** the capture path is exactly as before D6; the deployed image already holds the F-A2 writer (seven-column key) which fails CLOSED on the old six-column index, so NO build may be dispatched until SS decides; if the watchdog was paused, resume it as the LAST step of the rollback (N-93 rule 4) after the rollback is verified.
- **Evid:** `$EV/D6/rollback.*`.

### D6.8 `commit_state_unknown` (or a missing `outcome.json`) procedure (plan section 8a; nothing else runs until decided)
1. Read the run's `outcome.json` (status `dry_run` | `applied` | `failed` | `commit_state_unknown`, `evidence_digest`, warning `commit_raised:<ExceptionClass>`) in the run directory and the printed result.
2. As the reader run `verify_after_apply.sql` and `verify_before_apply.sql`.
3. Read the catalog directly: the three function md5s, the trigger arguments (7 / 9 or 6 / 8), the three function-attestation rows and the two trigger-attestation rows.
4. Decide. **Applied** (after-file every row PASS; patched md5s): record it and go to D6.6. **Not applied** (before-file every row PASS; pre-state md5s): nothing changed; re-run from D6.3 with a NEW dry run, a NEW digest and a NEW A3/A4. **Partial**: impossible by construction (one transaction); if ever seen STOP, change nothing, call SS and the owner.
5. Only after the state is decided and recorded does anything else run.

---

# PART 4. STEPS: the watchdog pause (W0.P), W2 (`ga_positions`), W3-W6 (the other 17 assets)

### W0.P Pause the watchdog (N-93). Executed HERE: immediately before the first build_run is created
- **Who:** operator, with the SAME production identity that will resume (N-93 condition 1). **Pre:** D6.6 PASS; SS has given the explicit GO before the first dispatch (**gate A6**, N-122, after the D6 STATUS: a written message, id recorded); W2.1 checks are about to run. NEVER at session open; NEVER earlier than this step.
- **Cmd:**
```
# 1) the resume baseline: every planned/running build_runs row on ALL charts, read-only, BEFORE pausing
"$RQ" "select r.id, r.chart_id, r.state, r.created_at, r.started_at, r.current_asset_id, coalesce(string_agg(a.asset_id, ',' order by a.position),'') as assets from build_runs r left join build_run_assets a on a.run_id=r.id where r.state in ('planned','running','paused') group by r.id order by r.created_at" | tee "$EV/W2/watchdog_baseline_runs.tsv"
# 2) describe (record the schedule and last attempt), pause, verify
gcloud scheduler jobs describe watchdog-reaper --location=asia-south1 --project=madhav-astrology --format='value(state,schedule,lastAttemptTime)' | tee "$EV/W2/watchdog_before.txt"
gcloud scheduler jobs pause watchdog-reaper --location=asia-south1 --project=madhav-astrology
gcloud scheduler jobs describe watchdog-reaper --location=asia-south1 --project=madhav-astrology --format='value(state)' ; PAUSE_T=$(date -u +%FT%TZ) ; echo "PAUSE_T=$PAUSE_T"
```
  Compute `CAP_T = PAUSE_T + 6 h` and write both into `$EV/W2/watchdog.txt` and the tracker note.
- **Expect:** the baseline is normally EMPTY (read 2026-10-04: 0 non-terminal runs); `describe` shows `PAUSED`; the pause output and the UTC timestamp go into the window ledger AND a tracker note (N-93 condition 3). Tell the other workstreams NOW (pause time, expected end, hard cap `CAP_T`; N-93 condition 9). The pause covers `watchdog-reaper` ONLY.
- **During the pause the operator IS the watchdog for EVERY chart (N-93 condition 8):** any run (any chart) with no progress for more than 30 minutes triggers a live investigation of its Cloud Run execution; never a blind kill, never indefinite silent waiting; the wall-clock duration of every step is recorded (G-8).
- **ABORT:** the pause cannot be performed or `describe` does not read `PAUSED`: do NOT dispatch. Per N-93, if the production identity cannot pause/resume then do not pause at all: rule (c) only, with an operator present for each tail; that is an SS decision, not the operator's. ALERT SS and Pravāha. **Safe:** no run exists; the scheduler is as it was.
- **Resume** is step W7.1, or the last step of ANY abort once the abort's safe state is verified, or `CAP_T`, whichever is first. THE 6-HOUR CAP ALWAYS WINS: at `CAP_T` the watchdog is resumed regardless; if an execution is still alive rule (c) governs and nothing is killed. EVERY abort path therefore ends with a VERIFIED resume (`describe` ENABLED plus the tick of W7.15).
- **Evid:** `$EV/W2/watchdog_baseline_runs.tsv`, `watchdog_before.txt`, `watchdog.txt`.

### W2.1 Pre-dispatch gate (REUSED before EVERY dispatch: W2.3 and W3.3)
- **Who:** operator. **Pre:** W0.P.
- **Cmd / checks (all must hold at the moment of dispatch):**
```
# (1) foreign runs, ALL charts, CLASSIFIED (the W0.7 query: it joins build_run_assets so a run can be told apart)
"$RQ" "select r.id, r.chart_id, r.state, r.triggered_by, r.created_at, coalesce(string_agg(a.asset_id, ',' order by a.position), '<no run assets: scope_target ' || coalesce(left(r.scope_target,80),'') || '>') as assets, coalesce(bool_or(a.asset_id like 'ga\_%'), false) as writes_ga from build_runs r left join build_run_assets a on a.run_id=r.id where r.state not in ('completed','failed','stopped') group by r.id order by r.created_at"
gcloud scheduler jobs describe watchdog-reaper --location=asia-south1 --project=madhav-astrology --format='value(state)'                                  # (2) PAUSED, and now < CAP_T
gcloud run jobs describe $JOB --region $REGION --project $PROJECT --format='value(spec.template.spec.template.spec.containers[0].image)'               # (3) tag == IMG_SHA, unchanged since W1.6
git -C "$MAIN" rev-parse HEAD                                                                                                                              # (4) == IMG_SHA
"$RQ" "select asset_id, is_active, has_writer from asset_registry where asset_id in ('ka_gochara_v4_41_candidate','ka_gochara_v5') order by 1"        # (5) writer-gap rows still present
gcloud run jobs describe $JOB --region $REGION --project $PROJECT --format=json | python3 -c "import sys,json;c=json.load(sys.stdin)['spec']['template']['spec']['template']['spec']['containers'][0];n=[e['name'] for e in c.get('env',[])];print(n);print('WRITER_GAP_ENV_PRESENT' if 'ORCHESTRATOR_WRITER_GAP_CHECK' in n else 'writer-gap env absent (enforce mode)')"   # (6)
```
- **Expect:** (1) EMPTY, except classification (a) RECALIBRATION runs (W0.7) which are LET FINISH: wait for them (poll every 10 minutes), never kill them, never block people's entries (N-46); (2) `PAUSED`; (3)/(4) equal; (5) both rows inactive with writers; (6) `writer-gap env absent (enforce mode)`.
- **ABORT:** a FOREIGN `ga_*` run (`writes_ga` true, or unclassifiable: W0.7 rule): STOP, no dispatch; the tag changed since W1.6 (another deploy landed): redo W1.4-W1.8 first; the watchdog not PAUSED; `now >= CAP_T`: resume per N-93 and re-plan with SS; **`ORCHESTRATOR_WRITER_GAP_CHECK` appears among the job env names** (the writer-gap pre-flight must stay in `enforce` mode, unset: `warn`/`off` is not the route). ALERT SS and Pravāha. **Safe:** nothing dispatched.
- **Evid:** `$EV/W2/W2.1_gate_<UTC>.txt` (one file per dispatch).

### W2.2 Dispatcher LIVE dry run: `ga_positions` (mandatory before the first `--commit`); explicit list, no cascade
- **Who:** operator. **Pre:** W2.1 PASS. The dispatcher inserts the planned run and then ROLLS BACK. The database credential is NEVER typed: `with_app_db.py` (Q-01 finding, section 1.3) puts `DATABASE_URL` in the dispatcher's environment in-process after asserting role `amjis_app`. The dispatcher is NOT started through `run_gated.sh` (that launcher is for owner-path executors); it has its own refusals.
- **Cmd:**
```
disp() { local out="$1" assets="$2"; shift 2
  ( cd "$MAIN" && "$PY" "$WS/with_app_db.py" --expect-role amjis_app -- "$PY" platform/scripts/governance/suvarna_level_wave.py \
      --chart-id "$C" --assets "$assets" --deployed-sha "$IMG_SHA" --deployed-job-sha "$IMG_SHA" --repo . --family-ref origin/main "$@" ) \
    2> >(tee "$out.stderr" >&2) | tee "$out.jsonl"; local rc=${PIPESTATUS[0]}; sleep 1; echo "exit=$rc" | tee "$out.exit"; return $rc; }
plan_check() { python3 - "$1" "$2" "$3" <<'PY'
import json,sys
ev=[json.loads(l) for l in open(sys.argv[1]) if l.startswith('{')]; last=ev[-1]
want=sorted(sys.argv[3].split(',')); plan=sorted(a for w in last.get('waves',[]) for a in w)
ok = last.get('event')=='summary' and last.get('asset_count')==int(sys.argv[2]) and plan==want
print('PLAN', 'PASS' if ok else 'FAIL', '| asset_count =', last.get('asset_count'), '| assets equal the explicit list:', plan==want, '| token =', last.get('confirm_token_single_run'))
sys.exit(0 if ok else 1)
PY
}
disp "$EV/W2/dispatch_dry_ga_positions" ga_positions && plan_check "$EV/W2/dispatch_dry_ga_positions.jsonl" 1 ga_positions
```
  `--deployed-job-sha` is the LIVE job image sha read from the job definition (W1.6), never a deploy run's `head_sha` (Trap 103).
- **Expect:** stderr `with_app_db: role=amjis_app OK`; `exit=0`; JSON lines, a final `summary`, no `refused`; `PLAN PASS`: **EXACTLY 1 asset** (`asset_count` 1, the single wave `[ga_positions]`, nothing added by a dependency or a level); the live manifest digest and the confirm token `1ASSETS_<12 hex>_FROZEN_REBUILD` (record whatever is printed; the rehearsal's `1ASSETS_593D49EB2DBA_FROZEN_REBUILD` is NOT expected to repeat); outside dependencies satisfied.
- **ABORT:** `PLAN FAIL` (any asset count other than exactly 1, or a different asset); `with_app_db` exit 3 (secret unreadable / proxy down / login refused) or 4 (`ROLE_MISMATCH`: SS rules, Q-01); dispatcher exit 4 with a refusal code. `IMAGE_SKEW` / `CODE_DIGEST_UNAVAILABLE` / `JOB_SHA_MISMATCH` = the checkout is not the deployed image: STOP; `FAMILY_REF_STALE` / `FAMILY_REF_UNVERIFIED` = `git fetch origin` and repeat; `DEPENDENCY_NOT_READY` = STOP and report which dependency; `ACTIVE_RUN` = go back to W2.1(1); `FAMILY_ASSET` should not occur for `ga_*`; exit 2/6: read the JSON error. ALERT SS and Pravāha. **Safe:** the dry run persisted nothing.
- **Evid:** `$EV/W2/dispatch_dry_ga_positions.*` (token recorded in `$EV/W2/token_ga_positions.txt`).

### W2.3 Dispatcher COMMIT: `ga_positions` (this CREATES the first build_run)
- **Who:** operator. **Pre:** W2.2 `PLAN PASS`; W2.1 repeated within the last 2 minutes; the watchdog is PAUSED; gate A6 given.
- **Cmd:** `TOKEN=<confirm_token_single_run of W2.2>; disp "$EV/W2/dispatch_commit_ga_positions" ga_positions --commit --mode single-run --confirm "$TOKEN"`. Record the `run_committed` run id (`RUN_P`) and the `run_dispatched` execution name (`EXEC_P`) the moment they print, in `$EV/W2/ids.txt`.
- **Expect:** events `run_committed` (run id), `run_dispatched` (the `gcloud run jobs execute ... --async` execution name); `exit=0` or the dispatcher stays attached and prints the wall-time report.
- **ABORT / exits:** 3 = dispatch failed AFTER the run was committed (the run is terminalised, or the summary carries a chart-blocking warning: read it); 6 = unexpected error, a connection that dropped during COMMIT is reported as `COMMIT outcome unknown` with the run id: run the ACTIVE_RUN check (W2.1(1)) before ANY relaunch; 7 = interrupted: a `planned` run not yet dispatched BLOCKS the chart until dispatched or terminalised (follow the summary; never hand-edit `build_runs`). ALERT SS and Pravāha. **Safe:** the chart is blocked only while a planned/running run exists; no data has been written by the dispatcher.
- **Evid:** the files above; `RUN_P`, `EXEC_P` in `$EV/W2/ids.txt`.

### W2.4 Monitor (10-minute poll; reused in W3.4)
- **Who:** operator. **Cmd** (every 10 minutes, and once about 2 minutes after dispatch; also check `gcloud scheduler ... value(state)` still `PAUSED` and `now < CAP_T`):
```
"$RQ" "select r.id, r.chart_id, r.state, r.current_asset_id, r.created_at, r.started_at, (select count(*) from build_run_assets a where a.run_id=r.id and a.state='complete') n_complete, (select count(*) from build_run_assets a where a.run_id=r.id) n_assets, (select max(coalesce(a.ended_at,a.started_at)) from build_run_assets a where a.run_id=r.id) last_progress from build_runs r where r.state not in ('completed','failed','stopped') order by r.created_at"
"$RQ" "select a.position, a.asset_id, a.state, a.disposition, a.output_changed, a.started_at, a.ended_at, left(coalesce(a.error,''),120) from build_run_assets a where a.run_id='<RUN_ID>' order by a.position"
gcloud run jobs executions list --job=$JOB --region=$REGION --project=$PROJECT --limit=3
```
- **Expect:** the canonical chart shows our run `running`, then `completed`; any OTHER non-terminal run on any chart is a FOREIGN run: list it in the poll record; a LEL recalibration run is let finish (a `planned` one on the canonical chart simply waits on the chart's advisory lock behind ours); only a foreign run that would write `ga_*` is an abort trigger (W2.1).
- **FOREIGN RUN APPEARS DURING OUR RUN (mid-run safe state):** classify it with the W0.7 query (it joins `build_run_assets`). (a) A LEL RECALIBRATION run (a `planned` one on the canonical chart is expected to wait behind ours on the chart's advisory lock: UNVERIFIED assumption, not relied on): let it finish, never kill it, never block the person's entry. (b) A FOREIGN `ga_*` run (or an unclassifiable one): **STOP DISPATCHING** (do not start the next dispatch), let OUR run finish its CURRENT asset (never kill an execution, G-6), then ABORT by the matrix of 6.1 (the chart is then a MIXED generation: W3.8 rules 3-5); ALERT SS and Pravāha at once.
- **Rules:** no progress (no new `started_at` / `ended_at`, no new log lines) for more than 30 minutes = live investigation of the execution (`gcloud run jobs executions describe`, the log read of W3.6), never a blind kill. NEVER stop or kill an execution during its post-write tail (integrity check, digest, receipt): stale `last_error` text from an earlier reaper stamp is expected and is cleared by the next successful write (G-6). Record the wall-clock duration of every asset.
- **Evid:** `$EV/<step>/poll_<UTC>.txt` per poll.

### W2.5 `ga_positions` acceptance (NO G-IDX here)
- **Who:** operator. **Pre:** `RUN_P` terminal.
- **Cmd:**
```
"$RQ" "select r.state, a.state, a.disposition, a.output_changed, a.error is null from build_runs r join build_run_assets a on a.run_id=r.id where r.id='$RUN_P' and a.asset_id='ga_positions'"
"$RQ" "select fact_category, count(*), count(distinct build_id), min(build_id::text) from chart_facts where chart_id='$C' and fact_category in ('graha_position','bhava_cusps','house_chalit','graha_sign_attributes','sandhi_flag') group by 1 order by 1"
"$RQ" "select state, last_error is null from asset_throughput where asset_id='ga_positions' and chart_id='$C'"
"$RQ" "select count(*) from chart_fact_identity i join chart_facts f using (fact_id) where f.chart_id='$C'"
```
  and the log read of W3.6 for this execution (`EXEC_P`).
- **Expect:** run `completed`, asset `complete` / `build` (`output_changed` t); the five categories 430 / 360 / 225 / 100 / 90 = 1,205 rows, ONE build id equal to `RUN_P`; `lit`, `last_error` NULL; FORENSIC: five lines `FORENSIC gate ga_positions executed passed=True chart=canonical ayanamsha=<each of the five>`; exactly the line `ga_positions ephemeris_backend=swieph rows=1205 path=/app/ephe`; zero ` ERROR ` lines and zero `Traceback`; ZERO `WRITER GAP` log lines and zero `run.writer_gap` events (the pre-flight must not fire); the identity count is now 0 or near 1,205 (cascade; informational). DO NOT run G-IDX now: every later `ga_*` delete-then-insert would undo it (rehearsal: 129,421 after W2, back to 1,205 after W6).
- **ABORT / STOP:** the `swieph` line missing or another backend or path (STOP: a Moshier build never reaches a write: the decorator raises `SwissBackendError` first, so the symptom is a failed asset with no line); any FORENSIC `passed=False` (the writer raises: the asset fails); run `failed`/asset error. **Safe:** `ga_positions` is delete-then-insert inside the orchestrator's transaction and savepoint: a failed asset leaves its PRIOR rows (verify: build id still `1c092ffb-72eb-4614-8422-552ca6eae985` and 1,205 rows) or the complete new set, never a mix. Do NOT re-dispatch blindly: ALERT SS and Pravāha with the run id, the asset error and the log excerpt (counts and lines only). The watchdog stays PAUSED until SS decides and the state is terminal and consistent; then resume per W7.1.
- **Evid:** `$EV/W2/W2.5_accept.txt`, `$EV/W3/job_$EXEC_P.log` (mode 600, do not paste: job logs can contain birth instants).

### W3.1 Pre-dispatch gate for the 17-asset run
- **Who:** operator. **Cmd:** W2.1 again (all five checks; it is a new dispatch).

### W3.2 Dispatcher LIVE dry run: the 17 assets
- **Who:** operator. **Cmd:** as W2.2, `ASSETS17=` the ONE explicit list below, `disp "$EV/W3/dispatch_dry_17" "$ASSETS17" && plan_check "$EV/W3/dispatch_dry_17.jsonl" 17 "$ASSETS17"`, with
`ASSETS17=ga_ayurdaya,ga_condition,ga_dashas,ga_medical,ga_nakshatra,ga_panchanga,ga_sade_sati,ga_sensitive,ga_sensitive_degree,ga_strength,ga_structural,ga_tajaka,ga_transit_anchors,ga_vargas,ga_vastu,ga_vichara,ga_yoga`
(17 ids; `ga_positions` is done and is an outside dependency that must be lit and fresh; `ga_prashna` is NOT rebuilt). Explicit list, no cascade (G-12).
- **Expect:** `exit=0`, no refusal; `PLAN PASS` = **EXACTLY 17 assets** (`asset_count` 17, the flattened waves equal the list); the live wave list derived from the post-1226 registry: w0 `[ga_ayurdaya ga_nakshatra ga_panchanga ga_sensitive ga_sensitive_degree ga_transit_anchors]`, w1 `[ga_vargas]`, w2 `[ga_dashas ga_strength]`, w3 `[ga_condition ga_structural ga_tajaka]`, w4 `[ga_medical ga_sade_sati ga_vastu ga_yoga]`, w5 `[ga_vichara]` (the critical path is vargas then dashas then structural then yoga then vichara; the live dry run decides, this list is the rehearsal's); the token `17ASSETS_<12 hex>_FROZEN_REBUILD`; outside dependencies (`ga_positions`, the `bg_*` globals `bg_kp_sublord_division`, `bg_nakshatra`, `bg_panchanga`, `bg_reference`) lit and fresh.
- **ABORT:** as W2.2; `PLAN FAIL` (any count other than exactly 17, an asset added or missing); a wave list that differs structurally from the above (an edge missing: 1226 not applied?) = STOP and compare with W1.5. ALERT SS and Pravāha. **Safe:** persisted nothing.

### W3.3 Dispatcher COMMIT: the 17 assets
- **Who:** operator. **Cmd:** as W2.3: `TOKEN=<confirm_token_single_run of W3.2>; disp "$EV/W3/dispatch_commit_17" "$ASSETS17" --commit --mode single-run --confirm "$TOKEN"`; record `RUN_17`, `EXEC_17`. (`--mode single-run`: one run, no pause hook is possible between waves; a documented limitation. The wave-by-wave mode was not rehearsed and is NOT used.)
- **ABORT / exits:** as W2.3. **Evid:** `$EV/W3/dispatch_commit_17.jsonl`, ids. ALERT SS and Pravāha.

### W3.4 Monitor the 17-asset run
- **Who:** operator. **Cmd:** W2.4 every 10 minutes. Reference timings (second rehearsal, laptop-emulated amd64, NOT production scale): whole run 16 m 41 s; `ga_dashas` 8:49, `ga_structural` 5:18, `ga_vargas` 1:13, `ga_condition` 0:26, `ga_vichara` 0:25, `ga_sensitive` 0:19, `ga_nakshatra` 0:06, `ga_yoga` 0:02, the rest under 2 s. Production `ga_structural` has run 658 to 1,323 s historically. Do not treat a long `ga_dashas` / `ga_structural` tail as a failure; apply the 30-minute no-progress rule and G-6.
- **Hard cap:** if `now` reaches `CAP_T` (6 h after the pause) resume the watchdog regardless; if an execution is still alive rule (c) governs and NOTHING is killed.

### W3.5 Run acceptance
- **Who:** operator. **Pre:** `RUN_17` terminal.
- **Cmd:**
```
"$RQ" "select r.state, count(*) filter (where a.state='complete'), count(*) filter (where a.disposition='build'), count(*) from build_runs r join build_run_assets a on a.run_id=r.id where r.id='$RUN_17' group by 1"
"$RQ" "select a.position, a.asset_id, a.state, a.disposition, a.output_changed, a.started_at, a.ended_at from build_run_assets a where a.run_id='$RUN_17' order by a.position"
"$RQ" "select asset_id, state, last_error is null from asset_throughput where chart_id='$C' and asset_id like 'ga\_%' order by 1"
```
- **Expect:** run `completed`; 17 assets `complete` / `build` (`ga_vastu` ended `output_changed = f` in the rehearsal: its output equals the stored one, not a failure; every other lane `t`); `asset_throughput` `lit` and `last_error` NULL for all 18 `ga_*` rebuilt assets (`ga_prashna` untouched, 19 registered).
- **ABORT:** run `failed` / `stopped`, any asset not `complete` / `build`, any `blocked_by_asset_id`: go to W3.8. **Safe:** see W3.8. ALERT SS and Pravāha.
- **Evid:** `$EV/W3/W3.5_accept.txt` (include the dispatcher's wall-time report).

### W3.6 Log evidence for BOTH executions (`EXEC_P`, `EXEC_17`)
- **Who:** operator. **Cmd:** read the job logs (the execution filter below was TESTED read-only on 2026-10-04 on a recent production execution: it returned that execution's lines; `--freshness` is REQUIRED because the default window is 1 day; the documented backend filter is `resource.type="cloud_run_job" resource.labels.job_name="brahma-build-pipeline-job" textPayload:"ephemeris_backend=swieph"`):
```
for E in $EXEC_P $EXEC_17; do
  gcloud logging read "resource.type=\"cloud_run_job\" AND resource.labels.job_name=\"$JOB\" AND labels.\"run.googleapis.com/execution_name\"=\"$E\"" --project=$PROJECT --order=asc --limit=200000 --freshness=2d --format='value(textPayload)' > "$EV/W3/job_$E.log" ; chmod 600 "$EV/W3/job_$E.log"
done
# counts and anchored fields only (never paste the log)
LOGS="$EV/W3/job_$EXEC_P.log $EV/W3/job_$EXEC_17.log"
cat $LOGS | grep -o 'FORENSIC gate ga_[a-z_]* executed [a-z_]*=[A-Za-z]*' | sort | uniq -c           # per-asset counts (the criterion above)
cat $LOGS | grep -c 'WRITER GAP' ; cat $LOGS | grep -c 'run.writer_gap'
cat $LOGS | grep -c 'FORENSIC gate .* executed passed=True'
cat $LOGS | grep -c 'FORENSIC gate .* executed assertion=none'
cat $LOGS | grep -c 'FORENSIC gate .* passed=False'
cat $LOGS | grep -o 'ga_[a-z_]* ephemeris_backend=[a-z]* rows=[0-9]* path=[^ ]*' | sed -E 's/ rows=[0-9]+//' | sort | uniq -c
cat $LOGS | grep -c ' ERROR ' ; cat $LOGS | grep -c 'Traceback'
cat $LOGS | grep -o 'MV mv_chart_sade_sati_lifetime_summary NOT refreshed[^.]*'
```
- **Expect (FORENSIC criterion, SS ruling): ALL 16 ORCHESTRATOR-REACHABLE GATE SITES RAN, 0 SKIPPED.** The arithmetic (`FORENSIC_GATES_REPORT.md` table): 18 gate sites; the two CLI-only sites (4: `ga_structural` full build; 7: `ga_sensitive` preflight) are OUT OF SCOPE (not reachable on the orchestrator path, they log nothing in this run); the other 16 sites produce 13 distinct line forms (the four sites inside `ga_dashas`, 9-12, share ONE per-ayanamsha line). Counts expected (second rehearsal): `passed=True` 47, `assertion=none` 10 (57 lines), `passed=False` 0. Per asset, from the line `uniq -c` below: `ga_positions` 5, `ga_nakshatra` 5, `ga_panchanga` 1, `ga_sensitive` 5, `ga_strength` 5, `ga_structural` 5, `ga_tajaka` 1, `ga_transit_anchors` 5, `ga_vargas` 5, `ga_dashas` 5, `ga_yoga` 5 `passed=True` plus 5 `assertion=none`, `ga_vichara` 5 `assertion=none`. The two log-only sites (`ga_vichara`, `ga_yoga`'s log-only branch) say `assertion=none`. A skipped gate would show only at DEBUG as `skipped chart=skipped-non-canonical`; the positive criterion is therefore: every expected (asset, form) present with its count and none `passed=False`.
  **Backend evidence (STOP rule):** one or more `ephemeris_backend=swieph ... path=/app/ephe` line for EACH of the ten decorated assets `ga_positions, ga_nakshatra, ga_panchanga, ga_dashas, ga_sade_sati, ga_sensitive, ga_strength, ga_structural, ga_tajaka, ga_vargas`; the rehearsal counts were `ga_dashas` 41, `ga_nakshatra` 6, `ga_sensitive` 5, `ga_structural` 5, `ga_vargas` 5, `ga_panchanga` 1, `ga_positions` 1, `ga_sade_sati` 1, `ga_strength` 1, `ga_tajaka` 1 = 67 lines, none with another backend or path. **Writer gap:** ZERO `WRITER GAP` lines and ZERO `run.writer_gap` events. `ERROR` and `Traceback`: 0 (the Python log format is `<logger> ERROR <message>`; the ` ERROR ` token was verified on a real production execution log on 2026-10-04, and `severity>=ERROR` can be added to the `gcloud logging read` filter). The MV line `[ga_sade_sati_writer] MV mv_chart_sade_sati_lifetime_summary NOT refreshed: this connection does not own it (owner=amjis_app) -- left stale ...` is expected (W3.7). Cloud SQL server-side ERROR/FATAL entries inside the window attributed to the builder or the dispatcher sessions: 0 (filter tested read-only 2026-10-04: `gcloud logging read 'resource.type="cloudsql_database" AND severity>=ERROR AND timestamp>="<T_open>"' --project=madhav-astrology --freshness=1d`; other entries, for example permission errors of unrelated sessions, are recorded, not aborts; Q-15).
- **ABORT / STOP:** a missing backend line or any non-`swieph` / non-`/app/ephe` line for a decorated asset = STOP (ALERT SS and Pravāha: the rebuilt values may not be on the pinned corpus); any `passed=False`, ERROR or Traceback. **Safe:** the data is written but NOT accepted; do not run G-IDX or declare anything; SS decides.
- **Evid:** the counts in `$EV/W3/W3.6_log_counts.txt` (the raw logs stay mode 600).

### W3.7 The materialized view is left KNOWINGLY STALE (L1_MV_REFRESH_AFTER_REBUILD)
- **Who:** operator. **Cmd:** `"$RQ" "select count(*), count(distinct chart_id), count(distinct build_id) from mv_chart_sade_sati_lifetime_summary"`.
- **Expect:** unchanged from the BEFORE record (60 rows, 3 builds, read 2026-10-02): the builder does not own the view, so the in-writer refresh is skipped with the INFO line of W3.6. Do NOT refresh it in the window. The refresh is migration 1256, PW.2 (right after the password rotation). Record "knowingly stale".
- **ABORT:** none. **Evid:** `$EV/W3/W3.7_mv.txt`. ALERT SS and Pravāha.

### W3.8 Failure handling (a failed, stopped or dead run; a runner abort)
- **Who:** operator, then SS. **Rules:**
  1. A runner abort before mutation is a SAFE ABORT (for example the image-skew check: the dispatch manifest carries the writer digests and the runner refuses before mutating if the job image's hashes differ). The run ends `failed` with nothing written.
  2. An asset that fails mid-run: the orchestrator owns the transaction and a savepoint per sub-step; the assets after it are `blocked`; earlier assets stay committed. A heavy asset (`ga_dashas` has 41 sub-steps) can be PARTIALLY built: it is not complete until a run finishes its plan (SATYA-DĪPA predicate), so never read a partial asset as done.
  3. The chart is then in a MIXED state (new ids for the assets that completed, old for the rest). Serving remains the quiet degradation of 1.5 plus a mixed generation; `chart_fact_identity` is empty or near 1,205 until G-IDX. Do NOT run G-IDX, the W7 checks or SETTLED-1.
  4. Do NOT re-dispatch blindly and never workaround (G-4). SS decides: re-dispatch the incomplete assets (the dispatcher requires their dependencies lit and fresh; the writers are idempotent per natural key) or hold. Never insert, edit or delete a `build_runs` / `build_run_assets` row by hand.
  5. A run that died during the pause (execution gone, run still `running`): resume the watchdog (W7.1 steps 1-3 only), wait for the FIRST post-resume tick to reap it, and reconcile only through the governed `POST /api/cockpit/watchdog`; never a hand-crafted row (N-93 condition 7).
  6. The fact_id one-time flip is expected and is NOT a failure; a failed `integrity_check_sql` of a not-yet-rebuilt asset (for example `ga_medical` after 1252) is expected until that asset's rebuild.
- **Safe state:** D6 stays applied (its rollback is no longer available once `ga_vargas` stored widened rows); the watchdog stays PAUSED until the run is terminal and consistent, then resume (N-93 condition 4); other workstreams are told.
- **Evid:** `$EV/W3/W3.8_incident.txt`.

---

# PART 5. STEPS: W7 (G-IDX, machine verdict, hand read-backs, between-state check, SETTLED-1)

Order inside W7 matters: resume the watchdog (W7.1), then G-IDX FIRST (W7.2: before any read-back that counts identity), then the machine verdict, then the hand checks. W7 reads production only as the reader, except G-IDX (writes `chart_fact_identity` as `amjis_app`).

### W7.1 Resume the watchdog (N-93 condition 4 and 6)
- **Who:** operator, the SAME identity that paused. **Pre:** `RUN_P` and `RUN_17` are terminal and W3.5 and W3.6 PASSED (resume is "at W7"; an abort path resumes only after its own state is verified; the 6-hour cap `CAP_T` resumes regardless).
- **Cmd:**
```
gcloud scheduler jobs resume watchdog-reaper --location=asia-south1 --project=madhav-astrology
gcloud scheduler jobs describe watchdog-reaper --location=asia-south1 --project=madhav-astrology --format='value(state,lastAttemptTime)' ; RESUME_T=$(date -u +%FT%TZ) ; echo "RESUME_T=$RESUME_T"
```
- **Expect:** `ENABLED`; resume time recorded; pause duration `RESUME_T - PAUSE_T` is under 6 h; other workstreams told (tracker note: resumed at `<UTC>`). Verification of the ACTUAL TICK and of "no dead run remains `running`" is W7.15 (it needs a tick to pass).
- **ABORT:** cannot resume: ALERT SS and Pravāha at once (a paused reaper is a production gap: until it is resumed the operator remains the watchdog for every chart). **Safe:** keep acting as the watchdog.
- **Evid:** `$EV/W7/W7.1_resume.txt`. PAUSE and RESUME times go into the WINDOW REPORT (W7.17).

### W7.2 G-IDX: `build_fact_identity_index.py --check`, ONCE, now (after ALL builds)
- **Who:** operator as **`amjis_app`** through the in-process helper (no literal is typed). NEVER `data_plane_builder` (no privilege on the table), never `data_plane_migrator`, never the reader. **Pre:** W3.5 and W3.6 PASS; W7.1 done; no build in flight.
- **What exists for this credential (stated exactly, Q-01):** `scripts/build_fact_identity_index.py` reads ONLY the environment variable `DATABASE_URL` (exit 3 if it is unset or the driver is missing); it has no `gcloud` fallback and no other source; it connects as whatever role that URL names, and `chart_fact_identity` is writable only by its owner `amjis_app` (arwdDxt) and `role_orchestrator` (arwd). `window_scripts/with_app_db.py --expect-role amjis_app` supplies it in-process from Secret Manager secret `amjis-pipeline-db-url`; whether that secret is `amjis_app` was not verified by the author (the helper refuses on any other role and SS rules, Q-01).
- **Cmd:**
```
cd "$MAIN/platform/python-sidecar"
runx "$EV/W7/gidx" "$PY" "$WS/with_app_db.py" --expect-role amjis_app -- "$PY" scripts/build_fact_identity_index.py --chart-id $C --check
"$RQ" "select count(*) from chart_fact_identity i join chart_facts f using (fact_id) where f.chart_id='$C'"
"$RQ" "select count(*) from chart_facts where chart_id='$C'"
```
- **Expect (the AMENDED check; measured on the second rehearsal and equal to the offline projection):** `exit=0` and the final line `CHECK: PASS`; `total_facts=147751`; `parsed=133832`; `identity_free=13919`; `gap=0`; `coverage_of_identity_bearing_pct=100.0`; `rows_in_table=133832`; seven clauses `[PASS]` (`facts_present`, `rows_equal_parsed`, `partition_sums_to_total` = 133832 + 13919 + 0 = 147751, `reason_counts_sum_to_identity_free`, `gap_within_limit` limit 0, `coverage_of_identity_bearing` >= 99.98%, `identity_free_reason_set`); the reason set is EXACTLY the 15: the 14 known (`sade_sati_cycle_phase_label_moon_relative_not_lagna_house` 4792, `saham_arabic_part_label` 2800, `special_point_or_aggregate_marker` 2303, `dhaiya_subperiod_label_moon_relative_not_lagna_house` 1495, `tajik_hadda_degree_term_index_not_house` 1200, `jaimini_karaka_role_label` 530, `bhrigu_nadi_chakra_index_not_house` 280, `fixed_reference_lookup_table_row_not_natal_placement` 195, `panchanga_constant_label` 147, `ashtakavarga_kakshya_index_not_house` 120, `yoga_label_catalog_label` 34, `ayurdaya_method_label` 15, `dosha_label_catalog_label` 6, `nakshatra_name_fifth_dimension_out_of_scope` 1) plus `scope_cap_sentinel` 1; the reader count equals `parsed`, and `count(*) from chart_facts` equals `total_facts`. Count changes WITHIN the known reasons are recorded, not an abort.
- **`CHECK: NOT_EVALUATED` IS A FAILURE.** A clause with no detector reads NOT_EVALUATED (it is never green, CLAUDE.md N.8; `rows_equal_parsed` reads NOT_EVALUATED in a dry run). On this real `--check` run every one of the seven clauses must read `[PASS]`: any `NOT_EVALUATED`, any `[FAIL]`, or anything but the final line `CHECK: PASS` is a failure.
- **ABORT:** `exit=4` (the corrected check FAILED: the chart's transaction is ROLLED BACK, the prior index is left as the cascade made it, about 1,205 rows); `exit=2` (database error mid-transaction, rolled back); `exit=3` (no `DATABASE_URL` or driver) or `with_app_db` exit 3/4; ANY identity_free reason outside the 15; `gap` > 0 (the target is 0); coverage < 99.98%; any NOT_EVALUATED clause. ALERT SS and Pravāha. **Safe state:** the 18 builds are complete and valid; `chart_fact_identity` is incomplete, so serving that joins through it (`bo_pratijna` provenance, `ChartReaderV4.lord_of`) stays degraded; the window is NOT declared complete. Do not loop re-runs: a parser change moves the `ga_panchanga` writer digest and needs a merge and deploy (decision for SS).
- **Evid:** `$EV/W7/gidx.*`.

### W7.3 Machine verdict, part 1: the 24-stem flip detector (Part 1 of the W7 report)
- **Who:** operator. **Pre:** W7.2 PASS. Direct connection to the proxy (no pooler, no wrapper); `FLIP_TIMEOUT_SEC=300`.
- **Cmd:**
```
cd "$MAIN" ; H=00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks
LANES=$(cd $H && ls *.json | sed 's/\.json$//' | paste -sd, -) ; echo "$LANES" | tr , '\n' | wc -l        # must print 24
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; export FLIP_TIMEOUT_SEC=300 FLIP_SNAPSHOT_DIR="$EV/W7/flip_snapshots"
  python3 platform/scripts/governance/flip_detector.py --snapshot native --out "$EV/W7/snapshot_post.json.gz" ) | tee "$EV/W7/snapshot_post.txt"
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; export FLIP_TIMEOUT_SEC=300
  python3 platform/scripts/governance/flip_detector.py --compare "$EV/W0/snapshot_pre.json.gz" --hooks-dir $H --require-lanes "$LANES" --out "$EV/W7/flip_report_live.json" ) | tee "$EV/W7/flip_compare_live.txt" ; echo rc=${PIPESTATUS[0]}
python3 platform/scripts/governance/flip_detector.py --compare "$EV/W0/snapshot_pre.json.gz" --against "$EV/W7/snapshot_post.json.gz" --hooks-dir $H --require-lanes "$LANES" --out "$EV/W7/flip_report_offline.json" | tee "$EV/W7/flip_compare_offline.txt" ; echo rc=${PIPESTATUS[0]}
python3 platform/scripts/governance/flip_detector.py --validate-hooks --require-lanes "$LANES" ; echo rc=$?
```
  The 24 stems are: `argala, argala_other_charts, ashtakavarga_bindu_contributor, band_table, chandra_bala_birth_moon_sign, dasha_scope_cap, ephemeris_backend_shift, fa2_ga_vargas, ga_condition_fallback, ga_strength_invariant_rows, ga_structural_chart_geometry, ga_vargas_invariant_sentinels, gandanta, karaka_dasha_roles, karaka_roles, karaka_web_order, karaka_web_order_other_charts, sade_sati_placeholder_null, special_lagna_offset, special_lagna_offset_other_charts, sun_required_rupa, tiers, tiers_other_charts, yamakantaka` (23 plus `fa2_ga_vargas`; the F-A2 hook is schema-valid in the detector's own schema).
- **Expect:** the snapshot's counts line = the post-build counts (chart_facts 147,751; chart_divisionals 38,596); BOTH compares: `VERDICT: NOT_CHECKED   exit 4` with the seven failure classes at 0 (`UNDECLARED_CHANGE`, `KIND_MISMATCH`, `DECLARED_BUT_ABSENT`, `EXPECTATION_MISMATCH`, `DASHA_SHIFT_UNDECLARED`, `HOOK_ERROR`, `EMPTY_READ`); `changes ... 35312, not attributed to any lane: 0`; `compared` true for the four tables; `--validate-hooks --require-lanes` `VERDICT: PASS`, rc 0. The standing NOT CHECKED registry (never silent, never a pass): `chart_dashas.tier` (H25 is the guard), `l1_tajik_varsha_year_lords.tier` (H9), `chart_vichara` (H6 / A1-A12), `ga_yoga_firings.strength`, `bodha_msr_signals`, `bodha_rm_resonances` (S-L2), `ga_condition_composite`, `ga_medical`, `ga_vastu_*`, `ga_prashna_*`, `prashna_charts`, and two `tiers[...]` entries.
- **THE OPERATIVE READING (the verdict is NOT_CHECKED BY DESIGN, so the verdict word alone proves nothing):** (i) all seven failure classes are 0, and in particular `DECLARED_BUT_ABSENT` is 0; (ii) in the JSON report's `expectations` list EVERY entry has `ok: true` (76 entries: `ephemeris_backend_shift` entries 6-29 = 24, `fa2_ga_vargas` 7 with observed 1200, 1200, 750, 50, 1, 0, 0, and the other lanes' 45); (iii) all 19 `anchors` have `ok: true` (the text summary prints `anchors: 7 of 7 OK`, the distinct anchors; the JSON lists 19). Check it mechanically:
```
python3 - "$EV/W7/flip_report_offline.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); e=r['expectations']
print(len(e), all(x['ok'] for x in e), sorted(x['entry'] for x in e if x['lane']=='ephemeris_backend_shift')==list(range(6,30)),
      len(r['anchors']), all(a['ok'] for a in r['anchors']), r['failure_counts'])
PY
```
  which must print `76 True True 19 True {...every count 0...}` (verified on the second rehearsal's report).
- **The `dasha_shift` entries (reconciled against the hook file `ephemeris_backend_shift.json`, 30 entries):** there are SIX `dasha_shift` entries, indices 0-5: 0 Vimshottari [6955, 7030] s; 1 Vimshottari KP [3, 7030]; 2 Kalachakra lahiri / krishnamurti / raman [145055, 145140]; 3 Kalachakra surya_siddhanta [150280, 150340]; 4 Kalachakra pairing-noise band [-400000, 701000] (OPTIONAL); 5 Mudda [-65, -3] (OPTIONAL). Entries 0-3 are NON-optional: they are the proof that the rebuild ran on the `.se1` backend, and on an unchanged chart they read `DECLARED_BUT_ABSENT` (a FAIL). Entries 4-5 are optional. (The README says "four non-optional `dasha_shift` entries"; the hook file has six entries of which four are non-optional.) They do not appear in `expectations` (they are not count entries); `DECLARED_BUT_ABSENT` = 0 is what proves 0-3 present, and the per-system numbers are in the `dashas` block below.
- **Per-system dasha shifts (source for the SETTLED-1 notice):** from `flip_report_offline.json`, block `dashas`, key `<ayanamsha>|<system>`, field `mode_shift_sec`. Second-rehearsal values (seconds, current minus snapshot): Vimshottari krishnamurti 6,992, lahiri_chitrapaksha 6,992, raman 6,992, surya_siddhanta_classical 6,991, true_chitra 6,993; Vimshottari KP krishnamurti 6,992, lahiri 6,993, raman 6,992, surya_siddhanta 6,991, true_chitra 6,993; Kalachakra krishnamurti, lahiri and raman 145,089, true_chitra 145,110, surya_siddhanta_classical 150,309; yogini, ashtottari, chara_karaka, narayana, naisargika 0 (max 0, min 0); Mudda 0 to +1 s with one bisection step (true_chitra, 425 rows, mode -42, min -43). The detector's per-row scatter for KP and Kalachakra (KP 1,049 to 6,590 s; Kalachakra about -374,000 to +701,000 s) is PAIRING NOISE (nearest-start within 10 days mis-pairs repeated paths): the per-system value is the `mode_shift_sec`, i.e. by chain identity; the wide bands are attribution only (H23: `start_iso(after) - start_iso(before)` within ±35 s of the system's value).
- **ABORT:** verdict FAIL (exit 2), ALERT (exit 3: a FORENSIC anchor changed: the worst case, STOP at once), READ_ERROR (5), REFUSED (6), or exit 4 with ANY non-zero failure class or any unattributed change; a Python traceback (exit 1). **Safe:** the data stays as built; the window is not declared complete; ALERT SS and Pravāha; no re-build without SS.
- **Evid:** the four files above plus `flip_detector.py` sha256.

### W7.4 Machine verdict, part 2: composite shift CS1-CS6, special lagna, vichara acceptance, F-A2 C1-C7
- **Who:** operator. **Pre:** W7.3.
- **Cmd:**
```
python3 $H/evidence/composite_shift_check.py --compare "$EV/W0/snapshot_pre.json.gz" "$EV/W7/snapshot_post.json.gz" | tee "$EV/W7/composite_shift.txt"        # CS1-CS5
python3 $H/evidence/composite_shift_check.py --margins "$EV/W0/snapshot_pre.json.gz" | tee "$EV/W7/composite_margins.txt"                                       # CS6 (BEFORE snapshot)
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; python3 $H/evidence/special_lagna_offset_check.py --compare "$EV/W0/special_lagna_pre.json" $C ) | tee "$EV/W7/special_lagna.txt"
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f $H/evidence/ga_vichara_writer_ACCEPTANCE.sql ) | tee "$EV/W7/vichara_acceptance.txt"
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f "$D6"/00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening/s_l1_ga_vargas_acceptance_check.sql ) | tee "$EV/W7/fa2_c1_c7.txt"
```
- **Expect:** `composite_shift_check: PASS`, exit 0, changed rows `{'varga_position': 900, 'sensitive_degree_check': 20, 'ayurdaya': 12}` inside 900..1,140 / 10..74 / 0..120; CS6: 0 within bound; `special_lagna_offset_check` PASS, 0 failures, 245 rows (20 longitudes move by -0.23243 deg; INDU / SREE / VARNADA inside their own bands); vichara acceptance 39 lines, all `ok = t` (A1-A12: valence_pass 7,500, chart_vichara 7,774, per ayanamsha 1,556 / 1,556 / 1,556 / 1,553 / 1,553, duplicates 0, unsorted 0, orphan ids 0, leverage 175 with `as_of`); F-A2 acceptance ACCEPTED: C1 `chart_divisionals` 38,596; C2 7,718 per ayanamsha x5; C3 6 `scope_cap`; C4-C7 0 offending (C4 12 rows per (ayanamsha, varga, graha) for the bindus; C5 96 per ayanamsha x varga; C6 60 `varga_d30_lord_per_amsa` per ayanamsha). The F-A2 lane is NOT accepted on the machine verdict alone: it is the pair (hook plus C1-C7 plus H26).
- **ABORT:** any exit != 0; a margin within bound; any `ok = f`; any offending count. **Safe:** as W7.3. ALERT SS and Pravāha.

### W7.5 The H1-H26 hand read-backs, AFTER, and the comparison with BEFORE
- **Who:** operator. **Pre:** W7.2 PASS (H22's identity count needs G-IDX).
- **Cmd:** the W0.11 loop with `h_post` as the output folder (50 blocks) plus the four BS statements (Appendix B); then `for f in $EV/W0/h_pre/*.out; do b=$(basename $f); cmp -s $f $EV/W7/h_post/$b || echo "DIFF $b"; done`.
- **Expect (the rehearsal showed every post output byte-identical to the first pass except run/build ids, receipt timestamps and the identity count; on production the BEFORE/AFTER differences are exactly the declared ones):**

| H | what | expected AFTER |
|---|---|---|
| H1 | Sun required_rupa and ratios | SUN `6.5`, JUP 6.5, MAR 5, MER 7, MOON 6, SAT 5, VEN 5.5; tier `single` on all; ratios 1.3031 / 1.3031 / 1.3723 / 1.3738 / 1.3031; per-graha "vs required" text |
| H2 | node composite rows | `bphs_weighted` `floored` 120 (120 NULL); `cross_formula_divergence` and `simple_multiplication` no rows; `graha_in_house_composite_strength` 1,620 to 1,380 |
| H3 | tables outside the detector | `ga_yoga_firings` 53, `bodha_msr_signals` 50,678, `bodha_rm_resonances` 45 (counts unchanged; L2 rows change only at S-L2) |
| H4 | Gandanta twins | per ayanamsha 10 NULL-`formula_id` + 10 `strict_0_48` (100); no `true` on the canonical chart; no detail rows |
| H5 | special lagna | script PASS (W7.4) |
| H6 | chart_vichara | `7774` total and `7500` valence_pass; acceptance all `t` |
| H7 | leverage_index as-of | ONE group, 175 rows, `as_of` = the UTC date of `RUN_17`'s creation, `as_of_source` `build_run_created_at` |
| H8 | argala | `argala_natal_matrix` 4,320 per ayanamsha with `n_num_null = n_no_occupant` 672 / 700 / 672 / 692 / 708 (krishnamurti, lahiri, raman, surya_siddhanta, true_chitra; 3,444); `argala_graha_natal` 32 / 32 / 32 / 28 / 32 (156) |
| H9 | tier tables | `mudda` L1 `classical_match`; `narayana`, `yogini`, `ashtottari`, `chara_karaka`, `naisargika` L1 `single`; `vimshottari` `two_pass_verified`; `l1_tajik_varsha_year_lords` 240 `single` |
| H10 | Vimshottari levels | 0 not `two_pass_verified`; levels 1-3 EXACT; level 4 lahiri 8,165 to **8,177** (+12), true_chitra 8,164 to **8,166** (+2), krishnamurti 8,155 to **8,156** (+1), raman 8,043 to **8,034** (-9), surya_siddhanta 7,983 to **7,977** (-6). The five-ayanamsha total is NOT a check (the nets cancel to 0) |
| H11 / H11b | karaka dasha roles | `role_differs_from_kn_rao` 0 on all ten rows; `active_elem_differs` 0 and `lord_missing` 0; role NULL count falls by about 26,703 (offline estimate 26,708; 5 = the level-4 row moves) |
| H12 | karaka labels | STRIKARAKA 0; PITRIKARAKA 35; one `strikaraka_alias` per ayanamsha (5) |
| H13 | karaka web | 429 / 440 / 425 / 424 / 456 per ayanamsha (krishnamurti ... true_chitra), total inside the 950..1,300 delta band; conjunction rows doubled |
| H14 | Mudda counts | UNCHANGED: 20,473 / 20,474 / 20,476 / 20,477 / 20,475 |
| H15 | placeholders | overlay `0/10/10`, phase `0/30/30` (pending / null_text / reason_cited); Saturn ingress `*_iso` rows within the declared bounds plus one resolution step (Krishnamurti up to about 1,950 s) |
| H16 | Chandra Bala | 9 classification changes; surya_siddhanta `cites_meena 12`, `cites_kumbha 0`; the other four unchanged |
| H17 | INVARIANT sentinels | `scope_cap` 6 rows; chart_divisionals 38,596; `graha_shadbala_naisargika` 9 and `required_rupa` 7 unchanged |
| H18 | first-time rows | `ashtakavarga_bindu_contributor` 3,360; `dasha_scope_cap` 1; GULIKA 35, MANDI 35, YAMAKANTAKA 35; record each optional category that appeared and its count (rehearsal: `bhava_chalit_rasi_divergence` 11) |
| H19 | band table / fallback | `ga_medical` mild 20 to 5, moderate 20 to 35 (15 rows), strong unchanged; vastu direction map neutral 31 / strengthened 4 / weakened 5; `ga_condition_composite` unchanged |
| H20 | category counts | 223 categories, 147,751 rows; +156 `argala_graha_natal`, +3,360 contributor, +1 `dasha_scope_cap`, +35 YAMAKANTAKA, +50 gandanta, -240 composite, karaka_chara_position 525 to 530, `karaka_web_per_varga` about +1,074; chart_divisionals 24,392 to 38,596 |
| H21 | other tables | counts unchanged except where a lane says otherwise |
| H22 | ten graha_position rows | ten rows returned; `fact_id` IDENTICAL on all ten (`id_identical` t); `build_id` NEW and one value = `RUN_P`; tier `single`; `abs(after - before) <= 0.0003` deg AND equal to the independent `.se1` values to 1e-6 deg (lahiri_chitrapaksha: MOON 327.055045, JUP 249.787441, SAT 202.432028, MAR 198.519155, VEN 259.172686, MER 270.838758, SUN 291.962617, RAH_MEAN 49.033044, KET_MEAN 229.033044, LAGNA 12.431150); family 1,205 rows, one build; identity count = `parsed` (133,832). ZERO rows returned = the ids changed: STOP |
| H23 | Vimshottari build, run row, receipt | five groups, ONE new `build_id` (the `ga_dashas` build in `RUN_17`), 0 not `two_pass_verified`; n lahiri 9,217, true_chitra 9,206, krishnamurti 9,195, raman 9,054, surya_siddhanta 8,992; newest `ga_dashas` run row `complete` / `build` / output_changed `t` with `run_id` = the new build id; a `proven` receipt NEWER than 2026-09-07 20:14:04 with `output_digest_12` DIFFERENT from `483dd7787c48` (rehearsal: `6576459504d8`); the per-system shifts of W7.3 within ±35 s of the table |
| H24 | composite labels | all 20 digest lines IDENTICAL to BEFORE |
| H25 | dasha tier census | differs from the BEFORE census ONLY by the declared tier moves (mudda 240 two_pass_verified to classical_match; narayana 105 to single; yogini 175, ashtottari 65, chara_karaka 106, naisargika 40 classical_match to single) and the declared row-set moves; vimshottari non-KP ALL `two_pass_verified` (45,664), vimshottari_kp 5,670 `single`; the one-query VIOLATION check returns **0 rows**; ANY other movement = ABORT |
| H26 | F-A2 | C1-C6 ACCEPTED (W7.4) and the 1,200 surviving Aries `varga_ashtakavarga` `bindus` rows IDENTICAL before == after on every key (any difference must be explained key by key by the varga move; else ABORT) |
- **ABORT:** any value outside its row (STOP rules inside the H doc: H10/H23 any level-4 count outside its delta or a level 1-3 change; H22 zero rows or a move beyond 0.0003 deg; H25 any other movement; H24 any differing digest). **Safe:** as W7.3; ALERT SS and Pravāha; nothing is re-run to "make it pass".
- **Evid:** `$EV/W7/h_post/` and `$EV/W7/h_diff.txt`.

### W7.6 The id check and orphans (S_L1_BETWEEN_STATE section 5; N-91 condition 4 acceptance)
- **Who:** operator. **Cmd:** statements BS-1 and BS-2 (Appendix B) plus the non-matching-row listing.
- **Expect:** BS-1 `147751|147750|1` (assert `n_uuid36 = 1` and `n_rows - n_formula_match = 1`; the row count itself is read, not asserted); the single non-formula row is `dasha_scope_cap | PRANA_DASHA | level_5_not_computed | INVARIANT` (a UUID5 of 36 characters by design); BS-2 `chart_vichara|<n_cited>|0` and `ga_yoga_firings|<n_cited>|0` (rehearsal: 20,608 and 145 cites; `n_cited` for chart_vichara moves with the dedupe).
- **ABORT:** `n_uuid36 > 1`, or a non-matching row other than that one, or `n_orphan > 0` (an orphan means `ga_vichara` or `ga_yoga` ran before `ga_structural` / `ga_strength` finished): STOP, tell SS. **Evid:** `$EV/W7/W7.6_ids.txt`. ALERT SS and Pravāha.

### W7.7 Receipts: every rebuilt `ga_*` asset has a PROVEN receipt newer than its pre-window one (SS 2026-10-03)
- **Who:** operator. **Cmd:** BS-3 (Appendix B) into `$EV/W7/post_receipts_ga.tsv`; compare with `$EV/W0/pre_receipts_ga.tsv`.
- **Expect:** for each of the 18 rebuilt assets `newest_proven_receipt` is later than the BEFORE value and later than the window-open time; `n_not_proven` 0 except `ga_positions` 1 (the pre-existing non-proven row); `ga_prashna` unchanged (2026-09-07 11:32:06). The flag of W7.14 only sees S-L1 if the rebuilt assets get NEW receipts.
- **ABORT:** a rebuilt asset without a newer proven receipt = the window is not complete. **Evid:** the files above. ALERT SS and Pravāha.

### W7.8 T4: stale survivors == 0, and the category-level accounting
- **Who:** operator. **Cmd:** the hash-pinned production copy `window_scripts/t4_stale_prod.py` (built from the rehearsal's `t4_stale.py`: connection from the sourced reader environment, read-only session asserted, pre files and maps by argument; sha256 in `MANIFEST.sha256`, checked at W0.5; tested read-only against production on 2026-10-04 where, against the unrebuilt chart, it correctly reports every row a survivor):
```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; cd "$WS" && "$PY" t4_stale_prod.py --pre "$EV/W0" --maps "$MAPS" ) | tee "$EV/W7/W7.8_t4.txt"
```
  (`$MAPS` is the W0.9 maps folder; the pre files are the W0.12 outputs `pre_build_ids.tsv`, `pre_cat_facts.tsv`, `pre_cat_dashas.tsv`, `pre_cat_divs.tsv`.) Plain SQL form of the headline number:
```
"$RQ" "select count(*) from chart_facts where chart_id='$C' and build_id::text = any(string_to_array('<comma list of the pre-window chart_facts build ids from pre_build_ids.tsv>', ','))"     # repeat for chart_divisionals, chart_dashas, chart_vichara
```
- **Expect:** survivors with a pre-window build id: **0** in each of the four tables; `stored-not-emitted` 0 at category / system / varga level; `emitted-not-stored` 4 fact categories (`argala_graha_natal`, `ashtakavarga_bindu_contributor`, `bhava_chalit_rasi_divergence`, `dasha_scope_cap`); 275 natural keys removed from re-emitted categories (240 composite-strength + 35 STRIKARAKA); last line `T4 PASS`.
- **ABORT:** any survivor (a stale row left behind by a delete-then-insert that did not cover it), any stored-not-emitted, `T4 FAIL`. ALERT SS and Pravāha. **Evid:** `$EV/W7/W7.8_t4.txt`.

### W7.9 Per-asset W-step checks, 18 of 18, and the zero-longitude query
- **Who:** operator. **Cmd:** the hash-pinned `window_scripts/wstep_checks_prod.py` (production copy of the rehearsal's `wstep_checks.py`; the build-log path is now `--log` arguments = the W3.6 job logs; the receipts baseline is the W0.12 `pre_receipts_ga.tsv`):
```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; cd "$WS" && "$PY" wstep_checks_prod.py "$RUN_P" "$RUN_17" --log "$EV/W3/job_$EXEC_P.log" --log "$EV/W3/job_$EXEC_17.log" --receipts-pre "$EV/W0/pre_receipts_ga.tsv" ) | tee "$EV/W7/wstep_checks.jsonl"
# the zero-longitude check as PLAIN reader SQL over ALL vargas (also inside the script):
"$RQ" "select count(*) from chart_facts where chart_id='$C' and fact_category='graha_position' and fact_key='longitude_sidereal' and fact_value_num=0"
"$RQ" "select varga, count(*) from chart_divisionals where chart_id='$C' and fact_category='varga_position' and fact_key='degree_in_sign' and fact_value_num=0 group by 1 order by 1"
"$RQ" "select count(*) from chart_facts where chart_id='$C' and fact_category='special_lagna' and verification_pass_status='floored'"
```
  Per asset: C1 `asset_throughput` `lit` and `last_error` NULL; C2 `build_run_assets` `complete` / `build` in the S-L1 run and the run `completed`; C3 ALL stored rows of the asset's footprint carry ONE build id equal to its run id (assets whose target table has no `build_id` column: row count > 0, flagged `no_build_id_col`); C4 the newest receipt is `proven`, bound to the run id and newer than the W0 receipt; C5 the rows the writer reported (log line `asset <id> complete - N rows`) equal the rows stored.
- **Expect:** 18 JSON lines with `ok: true`; the zero-longitude statements return `0`, NO rows, and `0`; last line `WSTEP PASS`. (Run against the unrebuilt chart on 2026-10-04 the three global statements already read 0 / no rows / 0.)
- **ABORT:** any `ok: false`, any non-zero global count, `WSTEP FAIL`. ALERT SS and Pravāha. **Evid:** `$EV/W7/wstep_checks.jsonl`.

### W7.10 Heads proxy (iii) and the 18 integrity checks
- **Who:** operator. **Why a proxy:** the reader has no SELECT on the generation-heads tables; the accepted evidence is (iii): run state plus receipt binding plus stamped fact rows. NOT a head-row read.
- **Cmd:**
```
for R in $RUN_P $RUN_17; do ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -v R="$R" -f /Users/Dev/suvarna-evidence/S_L1/w1_privilege_audit/w7_heads_proxy.sql ) > "$EV/W7/heads_proxy_$R.txt"; done
for A in ga_ayurdaya ga_condition ga_dashas ga_medical ga_nakshatra ga_panchanga ga_positions ga_sade_sati ga_sensitive ga_sensitive_degree ga_strength ga_structural ga_tajaka ga_transit_anchors ga_vargas ga_vastu ga_vichara ga_yoga; do
  printf '%s|' $A ; ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -q -X -A -t <<SQL
set statement_timeout='15min';
select integrity_check_sql from asset_registry where asset_id='$A' \gexec
SQL
  )
done | tee "$EV/W7/integrity_18.txt"
```
- **Expect:** heads proxy: 18 assets with `run_asset_no_error` t, `receipt_state` `proven`, `receipt_bound_to_R` t (the 19th line is the pre-existing non-proven `ga_positions` receipt row); `owned_fact_rows_at_R` > 0 for every asset whose output is in `chart_facts`; integrity: 18 lines ending `t` (including the new clauses of 1221, 1222 clause (e), 1252, 1254; `ga_medical` now TRUE because it was rebuilt). MEASURED as the reader on 2026-10-04 (Q-17): all 19 registered `ga_*` integrity texts (the 18 plus `ga_prashna`) run unparameterised through `\gexec` and returned `t` on the current data, EXCEPT that `ga_structural`'s text exceeds the reader's role default `statement_timeout=120s` (`canceling statement due to statement timeout`); with `set statement_timeout='15min'` in the session it completed and returned `t`. Hence the `set statement_timeout` line above (a session-level override; the role setting is only a default).
- **ABORT:** any `f` or non-proven/unbound row. **Evid:** the files above. ALERT SS and Pravāha.

### W7.11 Nothing else moved; other charts untouched
- **Who:** operator. **Cmd:** repeat the all-charts count query of W0.8 into `post_counts_all_charts.tsv`; `diff` with `pre_counts_all_charts.tsv`; and list ALL runs created since window open, excluding ours (foreign-run record, classified as W0.7): `"$RQ" "select r.id, r.chart_id, r.state, r.triggered_by, r.created_at, coalesce(string_agg(a.asset_id, ',' order by a.position),'<no run assets>') as assets, coalesce(bool_or(a.asset_id like 'ga\\_%'), false) as writes_ga from build_runs r left join build_run_assets a on a.run_id=r.id where r.created_at >= '<T_open as timestamptz>' and r.id not in ('$RUN_P','$RUN_17') group by r.id order by r.created_at"`.
- **Expect:** the run list is EMPTY, or holds only classification (a)/(c) runs (recalibration runs and non-`ga_*` runs, each recorded with its outcome); a `writes_ga` row is a finding: STOP, tell SS and Pravāha. The canonical chart's rows are the new totals (147,751 / 38,596 / dasha rows within the declared level-4 deltas / 7,774); the other two canonical charts' counts are IDENTICAL to BEFORE (S-L1 is canonical-only; the D6 capture change applies to every chart's future writes but changes no existing row).
- **ABORT:** any other chart's count moved. ALERT SS and Pravāha. **Evid:** the diff file.

### W7.12 The materialized view (record only)
- **Cmd:** W3.7 once more. **Expect:** knowingly stale, unchanged, to be refreshed by migration 1256 (PW.2). **Evid:** `$EV/W7/W7.12_mv.txt`.

### W7.13 Freshness-effect check (the sentence adopted by SS, section 1.5)
- **Who:** operator. **Cmd:** `"$RQ" "select asset_id, freshness_state, count(*) from asset_freshness where chart_id='$C' group by 1,2 order by 1,2"` and `"$RQ" "select asset_id, state, last_built_at from asset_throughput where chart_id='$C' order by 1"`; diff against `pre_freshness_all_assets.tsv` and `pre_throughput_all_assets.tsv`.
- **Expect:** the 18 rebuilt `ga_*` rows `fresh` again (by design, a proven receipt resets them; NOT measured in either rehearsal: if a rebuilt row stays `stale` after its proven receipt, record it and tell SS, it is not an automatic abort); every non-`ga_*` `asset_freshness` row UNCHANGED (L2+ receipts stay proven/fresh and keep serving); `asset_throughput` shows `stale` for up to 16 lit L2/L3 assets downstream of the rebuilt `ga_*` (a subset of: bo_arudha, bo_bimba, bo_grounding, bo_karanajala, bo_laksana, bo_laksana_rerank, bo_nakshatra_semantic, bo_samskara, bo_sangati, bo_special_lagna, bo_sudarshana, bo_vargottama_dhana, ka_dasha_kala, ka_kota_chakra, ka_sudarshana_varsha, ka_tithi_pravesha). Record the actual list. Both are BY DESIGN until S-L2 and NEITHER is a W7 failure.
- **ABORT:** a non-`ga_*` `asset_freshness` row changed, or an asset outside the 16 went stale (unexplained propagation: tell SS). **Evid:** the diff. ALERT SS and Pravāha.

### W7.14 Between-state acceptance, AFTER (N-91 condition 3; SS wording of 2026-10-03) — **SS**
- **Who:** **SS** (N-122): SS runs the live served calls through the MCP server and saves the outputs under `/Users/Dev/suvarna-evidence/S_L1/window/W7/post_calls/`; the operator confirms the files and reads them. **Pre:** at least **3 minutes** after the last L1 receipt landed (`"$RQ" "select max(observed_at) from asset_provenance_receipts where chart_id='$C' and asset_id like 'ga\_%'"`); the served detector result is memoised for 60 seconds and `pact_query` is uncached; three minutes clears the memo.
- **Cmd:** the same two calls as W0.14 (`judgment_query`, and one `assess_*`), made by SS.
- **Expect:** `judgment_query`: the flag `l2_receipts_predate_l1` in `judgment_flags` is TRUE (by design) AND the reading-contract sentence is the not-anchored one ("Its reading is NOT yet anchored to resolvable L1 fact references in this envelope; drill via the pointers before treating it as confirmed. Cause: the L2 receipts behind these fact_ids predate the current L1 (chart_facts) rebuild ..."); `assess_*`: the flag TRUE in `kernel.flags`. `l2_lineage_check_failed` must NOT be set (that is a failed detector, not a passing check).
- **ABORT / fail:** the flag is FALSE after S-L1 (the detector does not see S-L1: check W7.7 receipts) or the check-failed flag is set: the between-state acceptance FAILS: tell SS. **Evid:** `$EV/W7/post_calls/`. ALERT SS and Pravāha.

### W7.15 The reaper tick (N-93 condition 6)
- **Who:** operator. **Pre:** W7.1; wait for one scheduled tick (the schedule was recorded at W0.P).
- **Cmd:** `gcloud scheduler jobs describe watchdog-reaper --location=asia-south1 --project=madhav-astrology --format='value(state,lastAttemptTime)'` and `"$RQ" "select id, chart_id, state from build_runs where state not in ('completed','failed','stopped')"`.
- **Expect:** `ENABLED`; `lastAttemptTime` LATER than `RESUME_T` (one actual tick observed); the window's runs are terminal and consistent with the outcome; no dead run remains `running` on any chart (a LEL recalibration run that is alive is fine).
- **ABORT:** no tick after two schedule periods, or a dead `running` run: reconcile only via the governed `POST /api/cockpit/watchdog`, never a hand-crafted row; ALERT SS and Pravāha. **Evid:** `$EV/W7/W7.15_tick.txt`.

### W7.16 Final detector repeat with `--allow-not-checked` (only after W7.5-W7.14 are recorded)
- **Cmd:** the live compare of W7.3 plus `--allow-not-checked` (out `$EV/W7/flip_report_final.json`). **Expect:** exit 0 (the summary still prints every NOT CHECKED item and states the exit is 0 only because of the flag). `--allow-not-checked` only converts exit 4 into 0; it never softens 2 or 3.
- **ABORT:** any exit other than 0. **Evid:** the report. ALERT SS and Pravāha.

### W7.17 The WINDOW REPORT, the SETTLED-1 notice and the close
- **Who:** operator writes; SS accepts (gate **A5**). **Cmd:** write `$EV/W7/WINDOW_REPORT.md` containing: the timeline (every step start and end, G-8); the pause and resume lines (PAUSE_T, RESUME_T, CAP_T, the verified tick); every step's PASS/FAIL with evidence paths; the image digest and tag read at W1.6-W1.8 next to the backend log lines; both execution names and run ids; D6 evidence run directories and digests; the W0 map path and sha256s; the problems found. Then send the SETTLED-1 notice (PART 6) to Pravāha through SS, and the tracker events.
- **Expect:** SS records acceptance. **S-L1 CLOSE** is recorded at that moment: this starts the S-L2 clock (N-91 ruling 3: day 7 checkpoint, day 14 absolute, 48 h override if the owner says he is using the chart). From S-L1 close S-L2 preparation is the top priority (I-20 incl. the signal ids that embed `chart_divisionals.id`, I-21 with its short L1 re-run, the restored digest spec, the runway ruling, the rehearsal). No corpus or calibration run until S-L2 closes.
- **ABORT:** SS does not accept: the window stays OPEN as to acceptance; nothing further runs. **Evid:** the report, the notice text, the acceptance message id. ALERT SS and Pravāha.

---

# PART 6. ABORT / ROLLBACK MATRIX, PRAVĀHA COORDINATION, THE SETTLED-1 NOTICE

## 6.1 Consolidated abort and safe-state matrix

| point | what has changed in production | abort triggers (any) | safe state | rollback available |
|---|---|---|---|---|
| W0.1-W0.16 | nothing (reads, local evidence files only) | any W0 expectation not met | window does not open | n/a |
| W1.1-W1.2 | nothing applied | CI red, sha differs, queue rejects | nothing merged | n/a |
| W1.3-W1.5 | the migrate job applies one transaction PER FILE as `amjis_app`; each applied file stays | migrate job fails; ledger or effect mismatch | images may NOT have rolled (web and sidecar `need` the migrate job); chart data untouched; the assets staled by already-applied files read `receipt_not_fresh` (UNRESOLVED for serving) until a governed rebuild; no D6, no builds | NONE authored (forward-only; Q-12). SS decides roll-forward or a corrective migration |
| W1.4B | the six source PRs are closed | a PR not closed / already merged | the migrations are applied once; open source PRs are the only double-apply hazard until closed | n/a |
| W1.6-W1.9 | W1 applied; images rolled | tag mismatch, any pyswisseph / PyJHora / `.se1` difference, inventory failure, any `ga_*` digest moved | as above plus: no D6, no builds. The six staled assets stay UNRESOLVED for serving until SS decides | n/a (nothing new written) |
| D6.2-D6.4 | nothing (count and dry run roll back) | any refusal / failed check | pre-state (function md5 `1e079261...`) | automatic |
| D6.5 | ONE transaction: three functions, one index, two triggers, attestation rows, comments | exit 92/93/95/gate codes (nothing connected); `REFUSED_ROLLED_BACK` | pre-state; or applied (D6.6) | rolled back by the database; if `commit_state_unknown` follow D6.8 |
| D6.6-before the first build | D6 applied | any verify non-PASS | D6 applied, no build; watchdog NOT paused | D6.7 (`--rollback`) only while no widened `chart_divisionals` rows exist |
| W0.P | watchdog-reaper paused | cannot pause / verify PAUSED | scheduler as before, no run created | resume |
| W2 | `ga_positions` replaced inside the run's transaction/savepoint | failed run, no `swieph` line, FORENSIC `passed=False`, ERROR | prior rows or the complete new set, never a mix; NO re-dispatch without SS | none (delete-then-insert; the W0 maps are id maps, NOT row backups) |
| W3-W6 | 17 assets replaced wave by wave | failed/dead run, missing backend line, FORENSIC fail | MIXED generation (completed assets new, the rest old); D6 stays applied (its rollback is gone once `ga_vargas` stored widened rows); watchdog stays paused until terminal and consistent, then resume; no G-IDX | none; re-dispatch of incomplete assets only on SS word (W3.8) |
| W7.2 | `chart_fact_identity` rewritten for the chart in one transaction | rc 4 / 2 / 3, a reason outside the 15, gap > 0 | script rolled the chart back: the index is as the cascade left it (about 1,205 rows); builds valid; window not complete | automatic (rolled back) |
| W7.3-W7.14 | nothing (reads) | any failed expectation | the rebuilt data stays; window NOT declared complete; ALERT SS and Pravāha; nothing is re-run to make a check pass | NO restore step exists in this runbook. The W0.2B on-demand backup is the LAST RESORT; restoring it is destructive and is THE OWNER'S DECISION ALONE (G-14). Every row of this matrix reaches its safe state WITHOUT a restore |
| W7.15 | nothing | no tick / dead run | reconcile only via the governed `POST /api/cockpit/watchdog` | n/a |

Expected-by-design states that are NOT aborts: the fact_id one-time flip; `ga_positions` rebuild emptying `chart_fact_identity` until W7.2; the `l2_receipts_predate_l1` flag TRUE after S-L1; `asset_throughput` stale for the downstream L2/L3 assets; `mv_chart_sade_sati_lifetime_summary` left stale; `ga_medical` integrity FALSE between W1 and its rebuild; the N-91 "1,340 signal_ids move" figure (a LOWER BOUND) at the first MSR regeneration; L2 citations dangling until S-L2.

## 6.2 Pravāha coordination (rules)

0. **Pravāha is told at ANY abort, at once, together with SS** (every ABORT line of this runbook reads "ALERT SS and Pravāha"): a message stating the step id, what was left behind (the safe state of 6.1) and whether the watchdog is paused. From window start to SETTLED-1 Pravāha HOLDS its OWN flow on this chart (dispatches, runs, writes to `482012f1` tables); SS issues the merge FREEZE on main to all lanes at W0.16 for the whole window (G-13). A deploy later than `M1` (ours) means W1.4-W1.8 are redone.

1. Their protected train PRECEDES ours. SS posts the window slot with 6 hours' notice to Pravāha. Nothing of ours merges during their freeze; the W1 PR is not armed until SS says GO after their freeze is lifted (W1.2).
2. Our W1 PR triggers a deploy; so may theirs. The image verification is repeated AFTER the LAST deploy that precedes W2 and the tag read at W1.6 is the one used for the `--writer-commit`, the dispatcher `--deployed-sha` and the checkout. If another deploy lands between W1.6 and W2.3, W2.1(3) fails and W1.6-W1.8 are redone.
3. Pravāha's `ka_gochara*` writer digests MOVE across their deploy (expected); no `ga_*` digest may move (W1.8). Their inert registry rows (`ka_gochara_v4_41_candidate`, `ka_gochara_v5`, migration 1243) must exist (writer-gap pre-flight).
4. The dispatcher refuses their family assets (`ka_gochara*`, `ka_vedha_gochara*`, `gochara_*`, `bg_gochara_*`, `kala_gochara_*`) by design (`FAMILY_ASSET`); never route around it.
5. Other workstreams are told at window open (W0.16), at pause (W0.P), at resume (W7.1) and at close (W7.17), with start, expected end and the 6-hour cap.

## 6.3 The SETTLED-1 notice for Pravāha (what MUST be in it, and where each item comes from)

Sent through SS after SS records acceptance (W7.17). It states facts and numbers only; no birth inputs, no private event text. Required contents:

| # | content | source |
|---|---|---|
| 1 | window identity: chart `482012f1-710e-4a25-994a-93821f5871aa`; window open and S-L1 CLOSE UTC; `RUN_P`, `RUN_17`, `EXEC_P`, `EXEC_17`; the deployed image tag = `IMG_SHA`; the D6 evidence run directories and digests | `$EV/TIMELINE.tsv`, `$EV/W2/ids.txt`, W1.6, D6.3/D6.5 |
| 2 | PER-ASSET BACKEND and the `.se1` hashes: for each of the ten decorated assets (`ga_positions, ga_nakshatra, ga_panchanga, ga_dashas, ga_sade_sati, ga_sensitive, ga_strength, ga_structural, ga_tajaka, ga_vargas`) the line count and the statement `ephemeris_backend=swieph path=/app/ephe`; the three `.se1` sha256 (`sepl_18` `ca1393ce...99a66`, `semo_18` `1ca07bd6...82ca4f7`, `seas_18` `a2cd8fc3...8b2e2`, full values in section 1.6) with sizes; pyswisseph 2.10.3.2 and its binary sha256; the image tag/digest | W3.6 counts (job logs), W1.7 |
| 3 | PER-SYSTEM SHIFTS: for every (ayanamsha, system) the `mode_shift_sec` (Vimshottari about +6,992 s, KP the same as its parent, Kalachakra about +145,089 s / +150,309 s on surya_siddhanta, yogini / ashtottari / chara_karaka / narayana / naisargika exactly 0, Mudda 0 to +1 s with one -43 s step) and the statement that the per-system value is by chain identity and that the detector's KP / Kalachakra per-row scatter is pairing noise | W7.3 `flip_report_offline.json` block `dashas`; H23 |
| 4 | THE LEVEL-4 DELTAS per ayanamsha (lahiri / true_chitra / krishnamurti / raman / surya_siddhanta): Vimshottari +12 / +2 / +1 / -9 / -6 (levels 1-3 exact); Kalachakra +3 / 0 / +10 / -8 / -20; the five-ayanamsha total is not a check; the cause (a period whose UTC start date is not before its end date is dropped, so the shift moves sub-day Sukshma rows across a UTC midnight); Vimshottari non-KP 100% `two_pass_verified` (0 not); the NEW VIMSHOTTARI BUILD ID (the `ga_dashas` build in `RUN_17`, H23 query 1; the BEFORE build was `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb`) and its run row / receipt (H23) | W7.5 H10, H23, H25; `ephemeris_backend_shift` entries in the detector report |
| 5 | THE TEN `graha_position` ROWS (lahiri_chitrapaksha `longitude_sidereal`: JUP, KET_MEAN, LAGNA, MAR, MER, MOON, RAH_MEAN, SAT, SUN, VEN): the `fact_id` (identical before and after), before and after values, the delta in degrees (bound 0.0003) and the independent `.se1` value, the new `build_id` (= `RUN_P`), the TIER of the ten rows (`single` before and after, the H22 `tier` column), and the SHIFT TOLERANCE (`abs(after - before) <= 0.0003` deg = 1.08 arcsec, and equal to the independent `.se1` value to 1e-6 deg; the measured moves are Moon about -1.85e-4 deg, Jupiter -5.6e-5, Saturn +4.2e-5, Mars -3.3e-5, Venus -1.0e-5, Mercury +4.4e-6, Sun / nodes / Lagna about 0) | W7.5 H22 (BEFORE from `h_pre/H22_1.out`, AFTER from `h_post/H22_1.out`) |
| 6 | THE ID-MAP PATH: the W0 maps folder (`/Users/Dev/suvarna-evidence/FactId/W0_S_L1_<UTC>/`, four TSV files with row counts 143,299 / 8,524 / 24,392 / 483,870 and `MAPS.sha256`); the id facts: 142,094 `chart_facts` ids changed once and are stable from now on, the 1,205 `ga_positions` ids kept; `chart_vichara.id`, `chart_divisionals.id` and `dasha_row_id` are NOT stable (they change at every rebuild); Pravāha's `gochara_resonance_map.target_ref` (88 rows, 17 distinct ids in `arudha_pada` / `sensitive_degree_check`) cites ids that changed; no re-link is run (N-91 refused option (b)); the table is read by natural key | W0.9; S_L1_BETWEEN_STATE sections 2 and 10 |
| 7 | THE W0 BASELINE PATH: `$EV/W0/` (`snapshot_pre.json.gz` and its `.sha256`, `h_pre/`, the `pre_*` files, the special-lagna and vichara baselines) | W0.10-W0.12 |
| 8 | what moved and what did not: all 18 `ga_*` digests unchanged (`ga_vargas` `9212b478...`); `chart_divisionals` 24,392 to 38,596 rows (F-A2 key widening); chart_facts 143,299 to 147,751; `chart_fact_identity` rebuilt (133,832 rows, gap 0); the capture path now carries `fact_subject` and `constituent_fact_ids` | W7.2, W7.5 H17 / H20, D6.6 |
| 9 | the between-state: L2 / L3 / L5 citations dangle until S-L2; the `l2_receipts_predate_l1` flag is TRUE by design; `asset_throughput` stale for the downstream L2/L3 assets; the S-L2 clock (day 7, day 14); no corpus or calibration run until S-L2 closes; anything keyed on an exact longitude or an exact dasha boundary instant of this chart (L3 windows, calibration data) moves once | 1.5, W7.13, W7.14 |
| 10 | the pause and resume times of `watchdog-reaper` and the verified tick | W0.P, W7.1, W7.15 |

---

# PART 7. THE POST-WINDOW LIST (in SS's order)

General rules for every item here: it starts only after SETTLED-1 is accepted and the watchdog is resumed and ticking; it is REVIEW to SS before any production action (N-95: migrations, production actions and shared workflows are never covered by the stricter-only pre-approval); one item at a time; zero non-terminal build runs on any chart immediately before and after (the W0.7 query); every owner-path executor is started ONLY through `run_gated.sh "$PY" <executor>` with the SAME interpreter for the dry run and the apply (exit 92 otherwise); every bound hash is VOID if any input of its package changes (re-bind, new SS approval); evidence goes to `$EV/POST/<item>/`; no secrets in any command (G-1).

Generic owner-path command skeleton (substitute the package values below; the flags each executor documents differ and are listed per item):
```
cd <checkout of the PR head>/00_ARCHITECTURE/briefs/suvarna/exec/<package>
PLAN=<BOUND hash> ; GATE=../gate_v2/run_gated.sh
"$GATE" "$PY" <executor>.py --count   --expect-plan "$PLAN"                                  # read-only (where the executor has it)
"$GATE" "$PY" <executor>.py --dry-run --expect-plan "$PLAN" [--writer-commit "$WC"]          # prints the EVIDENCE DIGEST
#   SS approves the dry run (record the digest)
"$GATE" "$PY" <executor>.py --apply   --expect-plan "$PLAN" --expect-evidence "$EVD" [--writer-commit "$WC"]
# afterwards: outcome.json status, the stderr banner, the reader re-count (G-5)
```

## PW.1 Rotate the `suvarna_reader` password (FIRST), without argv exposure

- **Why/when:** after SETTLED-1 (SS standing rule 1: the rotation after SETTLED-1 is covered; the owner typed the current value in the operator's window). The one source every surviving helper reads is `~/.config/suvarna/pgenv.sh` (HELPER AUDIT 2026-10-03). N-122: read the instance name from `gcloud sql instances list`; set the password WITHOUT argv exposure; the value is generated in-process.
- **Who:** operator. **Pre:** the window is closed; SS has said GO; bash.
- **Mechanism:** `window_scripts/rotate_reader_password.py` (hash-pinned in `MANIFEST.sha256`; its layout check was run read-only on 2026-10-04 and PASSed: `~/.config/suvarna/pgenv.sh` holds exactly one `PGPASSWORD` assignment). It generates the new value in-process (`secrets.token_urlsafe`, never printed, never in a history file), sends it in the BODY of a Cloud SQL Admin API `users.update` request authenticated with the operator's own `gcloud auth print-access-token` (read in-process), NOT on any command line (this replaces the `--password=` argument form, which was briefly visible in a process listing). The equivalent gcloud form is `gcloud sql users set-password suvarna_reader --instance=<NAME> --prompt-for-password` (the value is read from a TTY, no argv). The script then rewrites the single `PGPASSWORD` assignment of the credential source in place (same mode, atomic replace), logs in with the new credential asserting `current_user` and the read-only session, and confirms the OLD password is refused. Output = timestamps and PASS/FAIL only.
- **Cmd:**
```
set +o history 2>/dev/null ; set +x
ps -axo command | grep -o 'madhav-astrology:[a-z0-9-]*:[a-z0-9-]*' | sort -u          # the proxy's instance
gcloud sql instances list --project=madhav-astrology --format='value(name,databaseVersion,state)'      # TWO instances: amjis-postgres (production) and amjis-ri02-validation-c720f1832 (NOT production)
cd "$WS" && "$PY" rotate_reader_password.py --instance amjis-postgres --dry-run          # layout + token only: nothing changes
"$PY" rotate_reader_password.py --instance amjis-postgres
```
- **Expect:** dry run: two `PASS` lines and `dry-run: nothing changed`. Real run: `PASS layout`, `PASS access token read in-process`, `PASS set-password operation DONE`, `PASS credential source rewritten, mode 0o600 preserved`, `PASS new credential: current_user + read-only session`, `PASS old password no longer logs in`. Then `"$RQ" "select current_user, current_setting('transaction_read_only')"` once (`suvarna_reader|on`).
- **UNVERIFIED:** the REST `users.update` call and its operation polling have never been exercised (it is a write); the first real use is this step. If it FAILs before the file is rewritten, the old password is still valid (use the `--prompt-for-password` form).
- **ABORT:** any `FAIL`. After a failure BEFORE set-password: nothing changed. After a failure AFTER set-password: the reader is locked out of every helper until the procedure is repeated (no data risk: the role is read-only; the `postgres` admin path can always set the password again). ALERT SS and Pravāha.
- **Then TELL EVERY SESSION to re-source** `~/.config/suvarna/pgenv.sh` (a session that sourced it earlier keeps the old `PGPASSWORD` in its environment): through SS to Engine, Pravāha, Exec A, Exec B and any running worker. The proxy needs no restart (it authenticates the instance by IAM; the database authenticates the role).
- **Evid:** `$EV/POST/PW1/rotation.txt` = the timestamped PASS/FAIL lines and the notice time. No password, no hash.

## PW.2 Migration 1256: refresh `mv_chart_sade_sati_lifetime_summary` (right after the rotation; SS N-122)

- **What:** the first post-window PR (`L1_MV_REFRESH_AFTER_REBUILD_v1_0.md` section 3): an ordinary guarded migration run by `migrate` as `amjis_app` (the view's owner), idempotent, `lock_timeout` set first: `SET LOCAL lock_timeout = '10s'; REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_chart_sade_sati_lifetime_summary;` (unique index `mv_sade_sati_summary_idx` exists; `CONCURRENTLY` runs inside a transaction block, proven on a disposable PG 15). It is NOT YET WRITTEN (the document says do not write it before); number 1256 is free (no file `1256_*` on main at 2026-10-04 and no branch carries it). Views without a unique index (`mv_cross_ayanamsha_consensus`, `mv_sensitive_points_cross_ayanamsha`) would need the plain statement; whether 1256 also covers the other views is SS's call (a refresh touches no table data); parents before dependents (`mv_chart_sensitive_points_summary` before `mv_sensitive_points_cross_ayanamsha`).
- **Pre:** zero non-terminal runs (W0.7 query); the BEFORE counts of W3.7 / L1_MV doc 5.1 (sade_sati 60 rows, 3 builds) on record.
- **Verify (reader):** the ledger row (filename + sha256); the build-coverage statements (both result sets EMPTY): `SELECT DISTINCT chart_id, build_id FROM public.mv_chart_sade_sati_lifetime_summary EXCEPT SELECT DISTINCT chart_id, build_id FROM public.chart_facts WHERE fact_category = 'sade_sati_cycle'` and the reverse; the definition-exact freshness diff `differing_rows = 0` for each refreshed view (the `\gexec` statement of the MV document 5.2); counts AFTER recorded.
- **ABORT:** a refusal or RAISE (one transaction: the view simply stays stale and the migration is safe to re-run). ALERT SS and Pravāha. **Evid:** `$EV/POST/PW2/`.

## PW.3 #3040 (mi_bhavisya append-only) plus migration 1259

- **#3040:** PR "mi_bhavisya never deletes or rewrites a `mimamsa_predictions` / `mimamsa_manifestation_sets` row" (insert-if-absent by the two-part natural key; the cockpit clear route preserves the asset), branch `suvarna/land/TI-mi-bhavisya-appendonly-001`, head `13c8f3b0e` at the addendum (CI 34 pass / 0 fail then; TO CONFIRM the head at the slot). Routine merge-and-deploy. Effect on production: a rebuild of `mi_bhavisya` inserts 0 rows on both charts (measured read-only: 0 of 60 anchors match a stored `prediction_id`, 60 of 60 match a stored `source_pramana_id`).
- **1259 (#3019):** `platform/migrations/1259_integrity_checks_claim_only_own_output.sql`, head `78361538b`, sha256 `dc8dabe06dfdf65b4426b0bf6687b2a240d3e5dd7c3fd9621a94c868388f87a0` (the earlier filename `..._own_family_ph_nimitta_mi_bhavisya.sql` is stale). Routine migration as `amjis_app`: four md5-guarded UPDATEs (ph_nimitta keeps only identity <= 4 and C13; mi_bhavisya loses its `phala_anchors` branch; ph_sankrama gains `source_anchor_id`; ph_pratikara gains `linked_anchor_id`), an ownership precondition (refuses if an owner lost its term) and an active-run DO guard (planned/running/paused for the four assets). Owners that already carry their term are untouched (ph_phaladesa `false` stays honestly false: 6 dangling `top_anchor_id` plus 7 `anchor_count` drift).
- **Order and pre-flight:** merge #3040 first (so the append-only writer is deployed), then 1259 (it may ride the same deploy; a single deploy applies the migration before the images roll). Pre-flight: zero non-terminal runs (the migration itself RAISES on a planned/running/paused run of the four assets); the live integrity texts equal the md5s the file guards on (a refusal means the live text moved: STOP).
- **Verify:** `"$RQ" "select filename, sha256 from _migrations_applied where filename like '1259_%'"` (sha256 as above); `select asset_id, md5(integrity_check_sql) from asset_registry where asset_id in ('ph_nimitta','mi_bhavisya','ph_sankrama','ph_pratikara')` equals the new md5s stated in the PR; `asset_freshness` has no `ph_*` / `mi_bhavisya` rows, so 0 rows move; the new `ph_nimitta` / `mi_bhavisya` integrity reads TRUE only on a replica (the reader lacks EXECUTE on `phala_anchor_identity`): record the stored text md5 instead (a KNOWN LIMIT, Q-21: the TRUE cannot be evaluated by the reader).
- **ABORT:** a md5 refusal, a precondition RAISE, an unexpected ledger row. **Safe:** the migration is one transaction: nothing applied; the deploy blocks until resolved (forward-fix by SS). ALERT SS and Pravāha.
- **Evid:** `$EV/POST/PW2/`.

## PW.4 The 1265 package (L5 frozen-row guards; owner-path executor, PR #3033)

- **Package:** `00_ARCHITECTURE/briefs/suvarna/exec/l5_frozen_guard_1265/` (`l5_frozen_guard_exec.py`; forward SQL sha256 `7796388aa8b17e979d362ba1a51f5b8d1f26d72415d48b4e7c3804baf6ccfe3d`, rollback SQL `8a1ef606104922651e255794124b92e803cf8dd58ad995033325bcac464e9c42`). **BOUND plan hash** `368dbc48c120786d8603249f9703a6675d74891b5fd2ed67c7c4ab3cab5e588d`; UNBOUND `b9c33108e7c4a63df339466afb0d49288cb3a7e63e9315ab09cb309e4dabe86b`; **executor sha256** `64ed08de6de86aeacba766196443731dd2eae979bbaec6bf6bbe3d5d6916b773` (reproduced on the local worktree `/Users/Dev/suvarna-m1265`, head `25bc1eb78`).
- **Approval:** SS's approval is CONDITIONAL on the plan hash recomputing IDENTICAL under Python 3.11 (run `make_plan.py` under the chosen `PY` and compare before the dry run).
- **Order:** apply after S-L1 settled AND #3040 AND 1259, BEFORE 1275. Dry run first; same interpreter; `--writer-commit` = the deployed image sha (the executor requires the image tag to equal it and that the writer files at that commit contain no DELETE of the frozen tables, so it must be a commit AFTER #3040 is deployed).
- **What it does:** as `postgres` takes transient membership of `data_plane_schema_owner` and `amjis_app` (PG15 CREATEROLE rule), opens `CREATE` on schema public for `amjis_app` for the install, installs 6 functions and 8 triggers (frozen-row guards on the four L5 history tables; consent-withdrawal and chart-delete DELETE exceptions; builder-guard captured byte for byte; builder grants asserted exactly, never repaired), closes the window, revokes the memberships; commits only if everything else equals the pre-state.
- **Notes that bind the operator:** (a) the helpers `l5_frozen_*` MUST be owned by `amjis_app` (installing as a superuser makes `postgres` the owner and `amjis_app` then gets `permission denied for function`; the executor path is correct, never install by hand); (b) STANDING CONSTRAINT: no `FORCE ROW LEVEL SECURITY` on `charts` without first revisiting the 1265 guard (with FORCE on, consent-withdrawal erasure fails: loud, not unsafe; the executor checks `pre_`/`post_standing_constraint_charts_not_force_rls` and RAISES at run time if it is ever true); (c) a role granted DELETE later gets `permission denied for function l5_frozen_...` until it is granted EXECUTE on the helper.
- **Pre-flight:** PG major 15; `select relforcerowsecurity from pg_class where oid='public.charts'::regclass` = `f`; zero non-terminal runs; the executor's own first-statement target assertion (exit 94: user, session_user, database, major, not superuser, CREATEROLE) and the `pg_read_all_stats` hidden-session check (an idle builder session counts as busy: refuses).
- **Exit codes (verified from the package report):** 0 ok; 1 refused (rolled back); 2 dry run refused; 92 interpreter/driver differs; 93 not launched by the gate; 94 wrong target; 95 test env; **96 commit state unknown (the gate's own 96 is "wrong role or database, nothing ran": tell them apart by the banner, G-5)**.
- **Expect (mirror):** dry run `DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD`, 6 functions and 8 triggers added, every other catalog class identical, membership equals the pre-state, `amjis_app` CREATE on public false; apply `COMMITTED`; then the package's `sql/verify_after_apply.sql` and `sql/verify_charts_rls_constraint.sql` as the reader: every row PASS.
- **ABORT / Safe:** any refusal or non-PASS: stop; before COMMIT the transaction rolls back (pre-state); after a `commit_state_unknown` banner run nothing until the reader's catalog read decides (the same procedure as D6.8); the rollback leg (`--rollback-dry-run`, `--rollback`) restores the pre-state exactly (rehearsed) and needs no CREATE capability. ALERT SS and Pravāha.
- **Evid:** `$EV/POST/PW3/`.

## PW.5 Migration 1275 (PR #3064): per-chart rows leave when their chart is deleted

- Routine migration as `amjis_app` (all 29 tables owned by `amjis_app`: no owner-path package). Head `8d6ec1d93` at park (CI 34 pass / 0 fail then); the vendored 1265 SQL md5 in its tests is `d598ac28...`: if 1265's head changes, 1275 must be RE-BOUND to it (slot-time check, S-4). Adds `chart_id -> charts(id) ON DELETE CASCADE` links for `phala_muhurta`, `phala_mitigation`, `phala_phaladesa` and the `mimamsa_*` per-chart tables (27 plus the two brahma_* ledgers; `mimamsa_pool_contributions` relinked NO ACTION to CASCADE).
- **Order (standing constraint, in its header and PR body):** S-L1 -> #3040 + 1259 -> 1265 -> 1275 -> the L5 rebuild. A 1275 BEFORE 1265's discriminator is refused by 1265's guards; its pre-flight RAISES if `charts` has `relforcerowsecurity = true`.
- **Verify:** ledger filename + sha256; the 29 FKs exist, validated, `confdeltype c`; row counts of the 29 tables unchanged. **ABORT:** a RAISE; the migration is one transaction. **Evid:** `$EV/POST/PW4/`. ALERT SS and Pravāha.

## PW.6 ONE slot: #3047, then 1288 (#3096), then 1274 (executor of #3061) [dry run then apply], then the scoped delete (#3072)

ACTIVE-RUN GUARD for the whole slot: zero non-terminal runs before, and NO build between any two of these steps. Order is binding: **deploy #3047, then 1288, then 1274 (dry run then apply), then the scoped delete.**

1. **#3047 (L4 readers made chart-scoped):** `ph_pramana` stores the `life_events` id reference and resolves text only for entitled roles through the chart-scoped helper; `ph_rectification` degrades only on UndefinedTable/UndefinedColumn. Routine merge and deploy (it moves the `ph_pramana` / `ph_rectification` writer digests; whichever of #2984 / #3047 merged second already regenerated the inventory). It works with or without 1274 (falls back to the table with the same predicate), but 1274 REVOKEs the builder's five column grants on `life_events`, so #3047 must be live first.
2. **1288 (PR #3096; ph_pramana integrity check made chart-scoped; routine migration as `amjis_app`):** head `6c557135a` (at the revision after REVIEW_3096; slot-time check, S-4); new check text md5 **`c3f1b7949ebfda27ab959e55c2a14898`** (3,398 characters; sha256 `040cf925736b063b41b894812835d6c97fcc0083544c899efa2978020f46267f`); old live text md5 `45f89d4853b157e22507ffccdb9af0e0` (1,284 characters), md5-guarded like 1259. **Verify:** the ledger (filename + sha256) AND read back the stored text md5 (`select md5(integrity_check_sql), length(integrity_check_sql) from asset_registry where asset_id='ph_pramana'`). Effect: `ph_pramana`'s registry generation moves; 0 freshness rows exist for `ph_*`.
3. **1274 (owner-path executor, PR #3061; the `life_events` chart-scoped security-barrier view):** package `00_ARCHITECTURE/briefs/suvarna/exec/mig_1274_life_events_view/`, executor sha256 **`972ce71403b2c0efea7e34b7c25a023677e3ef11e1093f23af1ad6875345a658`**, UNBOUND `4cafce87920e54b6cc80f3007c037f6da9ef6e2eb7e8e5b3164ba7fb2662266d`, **BOUND `4c8b86292eae63b9947e0786f11bbff19f7e962fa489e5c2e23683369d3252fe`** (forward SQL `0ba21466368e4ce98e7cb40eb6676e4c46502facd466d8591f903a7e9467dd33`, rollback SQL `5d6432d0875993468ae0e34a5278fbc359d480a2422b22d3d962a118424ca62d`). **Pre-flight (SS): the builder's role memberships must be EMPTY:** `"$RQ" "select r.rolname from pg_auth_members m join pg_roles r on r.oid=m.roleid where m.member=(select oid from pg_roles where rolname='data_plane_builder')"` returns no rows. One transaction creates `public.life_events_chart_scoped` (security barrier, 6 columns: `id, event_id, event_date, category, domain, chart_id`; owner `amjis_app`; SELECT to `data_plane_builder` only), REVOKEs the builder's five column SELECTs on `life_events` (`id, event_date, category, description, outcome_observed`), asserts (RAISE and executor re-read), with `data_plane_schema_owner` granting `amjis_app` CREATE for one statement and revoking it (schema ACL byte-identical). First check: database `amjis` / administrator `postgres` / non-superuser / major 15. Exit codes (re-bound report): 92 interpreter, 93 gate, 95 test env, **91 commit state unknown**; there is no distinct wrong-target code (Q-14: the connection check is a failing check). Dry run, SS approval, apply, rollback leg available (`--rollback-dry-run` / `--rollback`; restores the whole state image including the column ACL text). Verify: the builder reads only its own chart through the view and has NO direct SELECT on the table; the other roles have nothing on the view. Accepted limit: the chart scope is a transaction-local GUC a hostile builder session could set (protects against accidental cross-chart reads).
4. **Scoped delete (#3072, MERGED; the 25-row one-shot gated DELETE; owner-path executor; N-122 final package):** run from a clean checkout of main containing it, after `shasum -a 256 scoped_delete_8_exec.py` equals the executor sha below; package `00_ARCHITECTURE/briefs/suvarna/exec/scoped_delete_8/`, executor sha256 **`49112fcdfa503a205877ea9be569dbfc332a7f28e3c5eff81c6d7493e2404033`**, SQL `22c683eba776cb7974ebba0ae0c11abd2e4926752be97f7a762197c98188ab92`, UNBOUND `d1ff556ee700f47bef9c05d26c2056b27d67465507328a5c7dad783cb65b8648`, **BOUND `26539e35db5038a7de5106444722da2e8d7da60757814d6eac52caada2b89efa`**. **Pre-flight: `"$RQ" "select rolsuper from pg_roles where rolname='postgres'"` must read `f`** (the executor pins the name, not the flag) and 1288 must be applied (ORDER). It deletes the 8 `life_event_miss` rows of `phala_pramana`, the 16 of `phala_pramana__ssv_20260728b` and the 1 of `phala_phaladesa__ssv_20260728b` for chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (rows derived from another chart's private events; no private text is read or printed; ids in the package report). The ŚUDDHA-VĀCA rollback baseline is AMENDED ON PURPOSE (SS accepted: `phala_pramana__ssv_20260728b` 138 to 122, `phala_phaladesa__ssv_20260728b` 7 to 6): the amendment and the counts are recorded in the plan text, `outcome.json` (`rollback_baseline_amendment`), the PR body and the evidence. Commands: `"$GATE" "$PY" scoped_delete_8_exec.py --count --expect-plan "$PLAN"` (optional), `--dry-run --expect-plan "$PLAN"` (expect `DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD`, `failed_checks []`, the 8 / 16 / 1 ids, `total_rows_deleted_in_transaction 25`, chart totals 56/48, 138/122, 7/6, other charts 4 / 3 / 7, live `phala_phaladesa` unchanged), then `--apply --expect-plan "$PLAN" --expect-evidence "$EVD"`. Evidence under `/Users/Dev/suvarna-evidence/ScopedDelete8/dry-run_<ts>/`. Exit codes: 0 ok; **1 = apply refused (rolled back) OR commit_state_unknown (read `outcome.json` `status` and the banner, then re-count with the reader)**; 2 dry run/count refused; 92; 93; 95; gate codes 94-98. Post-apply reader checks: `select chart_id, count(*) from phala_pramana group by 1` = 1c826d5a 48, 482012f1 4; the same on `phala_pramana__ssv_20260728b` = 122 / 3 and `phala_phaladesa__ssv_20260728b` = 6 / 7; `phala_phaladesa` 26 rows unchanged; zero rows of the listed ids. Afterwards `ph_pramana` must be rebuilt for 1c826d5a BEFORE any `ph_pramana` build for another chart (the delete leaves 8 anchors without a pramana row; with 1288 applied another chart's build is no longer failed by it; the 1c826d5a rebuild itself waits for that chart's own end-to-end gate: not part of this slot).
- **ABORT:** any refusal; a non-empty membership list; `rolsuper` true; a build in flight. **Safe:** each item is single-transaction; a refusal rolls back; the order is not re-arranged to "get past" a refusal. ALERT SS and Pravāha.
- **Evid:** `$EV/POST/PW5/<item>/`.

## PW.7 #3045 (dp_builder_privileges: migration numbers 1272 and 1273; owner-path executor)

- Package `00_ARCHITECTURE/briefs/suvarna/exec/dp_builder_privileges/` on branch `suvarna/land/TI-dp-builder-privileges-1272-1273-001` (`dp_builder_privileges_exec.py`, `bind_patch.py`, the two history SQL files, `live_defs/bind_l2_exact_inputs.LIVE.sql`). **Executor sha256 `72879febad9f5358e8b6c44ef68ed6995d63db1f2d7a162c117a7c9fde9a88a4`** (reproduced from the branch); UNBOUND `f9f85371546e8b186de9e1cd0f948f68994db4a1a9a76411b1feb34bbf0d94e7`; **BOUND `af946cb456f1d481f2331cb8f0e260158cb8664b6d923040ff826148d7d3548f`** (the earlier `50f45db8...5766` is WITHDRAWN). Live bind function md5 `7bf8987517a7b76bd7ffae1c2bcf32ee` (5,678 chars) and patched md5 `44c7e524a082ada7c919afd8d325ba8a` (2 hunks).
- 1272: `bind_l2_exact_inputs(uuid,jsonb)` gets one hunk granting SELECT on the transaction-local shadow tables it creates to `data_plane_builder` only; 1273: `GRANT EXECUTE` on the eight `bodha_*_identity` functions (and namespaces) to `data_plane_builder`, issued as `amjis_app`. The SQL files carry the numbers as history text only and are never run by `migrate.ts`.
- **Pre-flight:** PG major 15; the administrator `postgres` is a `pg_read_all_stats` member (asserted and printed; an idle builder session otherwise counts as busy); zero non-terminal runs; the first statement asserts the target (user, session_user, database, major, not superuser, CREATEROLE).
- **Exit codes (verified from the PR body):** 92 interpreter, 93 gate, **94 wrong target**, 95 test env, **96 commit state unknown**, 0 ok, 1 refused/rolled back, 2 dry run refused; the gate's own 94 (missing binary) and 96 (wrong role/database) mean "nothing ran": read the banner (G-5).
- **Expect (mirror):** dry run exit 0 with 67 checks; apply COMMITTED with 68; rollback dry run 65; rollback COMMITTED 66; restored state identical. Verify as the reader: the builder holds EXECUTE on the eight functions (`has_function_privilege`), the bind function md5 equals the patched md5, and the executor's asserting post-checks RAISED nothing.
- **Does NOT unblock `bo_*` by itself:** migration 1262 (B5 `chart_fact_identity`), the wrapper fixes (#3008, #3029), B7 (`bo_laksana` strict count), the reader/heads dependency and the standing N-93 pause remain; see `DP_BUILDER_PRIVILEGES_PLAN_v1_0.md` section 8 and the S-L2 runbook.
- **ABORT / Safe:** as PW.4. **Evid:** `$EV/POST/PW6/`. ALERT SS and Pravāha.

## PW.8 Migration 1262 (PR #3073): register `chart_fact_identity` as asset `ga_fact_identity`

- Routine migration as `amjis_app` (the table's owner; a guard refuses a non-owner executor), head `7aa127564a39925f4099834e6f28741dffec120a` at the report (slot-time check, S-4). INSERTs one `asset_registry` row (`ga_fact_identity`, ganita/L1, per_chart, `has_writer=false`, `is_active=true`, `count_sql` `SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1`), grants the builder SELECT only (asserting RAISEs: SELECT true, none of INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER), `lock_timeout` 5 s, an active-run DO guard (RAISES on planned/running/paused). Apply POST-window with no active build; it is a precondition of S-L2.
- **Verify:** the ledger row; `has_table_privilege('data_plane_builder','chart_fact_identity','SELECT')` true and write false; the registry row as intended; `asset_freshness` unchanged (it only INSERTs, the invalidation trigger cannot fire); `count_sql` returns the G-IDX `parsed` (133,832) for the canonical chart. The integrity claim is "non-empty and no identity row inconsistent with its current chart_facts row"; COMPLETENESS (the Python corrected check) stays with `build_fact_identity_index.py --check` and is NOT detected by the SQL (a consistent but incomplete index reads true). Noted for SS: the cockpit clear route has no `has_writer` filter, so a layer or global Clear derives a DELETE from `count_sql` (an `EXPLICIT_CLEAR_OPS` entry is a TS decision).
- **ABORT:** a RAISE; **Safe:** one transaction. **Evid:** `$EV/POST/PW7/`. ALERT SS and Pravāha.

## PW.9 ONE tests-only PR: the migration tests of the six source PRs (after SETTLED-1; SS ruling)

- **What:** a single PR that lands ONLY the migration tests carried by the six closed source PRs (#2900 1221; #2943 1222 and 1223; #2896 1224; #2898 1226; #2957 1252; #2959 1254) after SETTLED-1, so the carried files regain their tests. Tests/docs/evidence only: eligible for the N-95 stricter-only pre-approval after one clean independent review and green CI on the exact head.
- **THE GUARD FORM (required):** the change-scope guard in each migration test must be the CONDITIONAL form `if F... in added: assert added <= {F...}` (the file's own name inside the set of files the PR adds), not an unconditional `assert added == {F...}`. The 1219 test on main has the same defect (Pravāha Stream B is fixing it) and the 1221 test in #2900 has it; no other migration test across the 26 PRs reviewed does. Fix the guard in the 1221 test while landing it.
- **Verify:** the tests pass against the migration files AS ON MAIN (byte-identical to the W1 files, Appendix B); no migration file is touched; the number guard still PASSes.
- **ABORT:** a test needs a change to a migration file (the files are applied and must never be edited). **Evid:** `$EV/POST/PW9/`. ALERT SS and Pravāha.

## PW.10 The rest, per the checklist (pointers; each needs its own SS go and, where marked, its own slot)

1. **Migration 1256** is PW.2 (N-122).
2. **Migrations 1260 (#3025) and 1261 (#3031):** HELD drafts. 1260 drops seven cross-asset FKs and adds `chart_id -> charts(id)` cascade links on five L4 tables; 1261 grants the builder SELECT/INSERT/DELETE on `phala_rectification*` (apply after the S-L3 `ka_kshetra` build, before S-L4; `life_events` gets no direct builder grant).
3. **Migration 1276 (#3080)** (two stale CI failures, undiagnosed), **curation 1283-1287** (1282 released), **L0 data 1277-1281 and the #3055 gate** (parked, relaunch only on SS word, N-115).
4. **N-117 acharya rulings (BINDING for the parked L0 / L4 / L5 lanes when they resume;** `/Users/Dev/suvarna-evidence/ACHARYA/ACHARYA_RULINGS_v1_0.md`, 27 rulings: 9 corpus, 9 tradition-not-corpus, 7 honest-null, 2 native/SS): Phaladeepika XXVI sl.2 node-Sun equivalence accepted; Ketu-12th becomes UNFAVOURABLE (sl.11/24); all #3049 mappings confirmed but the migration keys rows by (graha, house), NEVER by id; nodes never combust (node combustion orbs NULL; Moon one orb 12; 'deep' 10 and Mars/Jupiter/Saturn deep orbs unsourced NULL); transit motion values keep numbers, relabel 'classical BPHS Ch.22' as modern mean motion, Mercury/Venus sign-residence honest null; seven yoga/dosha names resolve to YOGA on ties and an input containing 'Yoga' never resolves to a dosha; honesty cluster (`direct` evidence label renamed; direction NULL not 'mixed'; one-instant grade is not a muhurta; transition-to-travel rows removed; 7 CLASSICAL_CITED families downgraded; channel priors and the 0.5 default NULL; 171 class priors recorded as unratified judgment seeds); anything 'tradition, not corpus-verified' is stored as attributed to tradition. Nothing applied before the L0 wave.
5. **Scoped-delete extension (local commit `35fe8200`, hashes `c8d01120` / BOUND `427b75ec`, not pushed)** and the other parked items: bhakoot (local `6e0b94aa1`), the 1268 pair review, review-3076, PR3 (#3078) / PR4 (#3076), the admin user-delete route guard PR, the chart-delete design (#3070). Reconcile with the 25-row `26539e35...` package of PW.6 first (RULED N-122, Q-22: #3072 MERGED, BOUND `26539e35...` is final).
6. **S-L2 preparation is the top priority from S-L1 close** (N-91 condition 7): the `bo_*` UUID chart_id fix (all 22 `@l2_producer` adapters raise on a UUID chart_id; a separate small PR, merged before S-L2 = an S-L2 BLOCKER), the S-L2 runbook and rehearsal, the attribution hooks, I-20 (signal ids embedding `chart_divisionals.id`), I-21.
7. **Queued behind S-L1 (no worker until after SETTLED-1):** E3.4 (run-level error text always written, R217); E1.5 (timing verdicts live, R55); E3.6 / E1.10 (freeze blockers R39, R34, R36: confirm each closed by evidence or say what is missing); E1.8 (R24 production L3 census); E3.7 was closed by W1.8. The tracker emits through `python3 -m suvarna_tracker.emit item --actor exec-suvarna --item <ID> --state running|done|blocked --detail "..." --evidence "<commit|PR|path>"` (branch `strategy/suvarna-plan`, worktree `/Users/Dev/madhav-suvarna-plan/platform/scripts/governance`); events normally ride in STATUS messages and SS emits them.
8. **Post-window correctness and tooling items recorded by the window:** the `forensic_pass` signal on NON-canonical charts still reads True while the gates skip (record as not-run: NULL or an explicit `skipped_non_canonical`, after checking which readers expect a bool; S-L1 is canonical-only); `verification_method = two_pass_classical_reconstruction` is a mislabel on rows stored as `single` (437,860 of 483,870 `chart_dashas` rows; fix in a separate lane); teach `flip_detector.py` to compare `chart_dashas.verification_pass_status`; the silent omission of short level-4 dasha periods (quantify per system and ayanamsha); the `Dockerfile.pipeline` pins for `sefstars.txt` / `seleapsec.txt` and the N-79 library pin recommendation (the requirements float); no workflow runs `python -m panchang_engine.swiss_backend` on the pushed image; `panchanga_daily.ephemeris_version` records the library version, not the backend; the `ga_nakshatra.py` code comment "Canonical rows keep the exact id they always had" (a writer source file: editing it moves a digest); a Kiran (`cb73cd3d`) rebuild WOULD move 27,634 non-KP vimshottari rows `single` to `two_pass_verified` (`tiers_other_charts.json`); the 5 swallowed `_derive_ashtakavarga failed: missing 'ayanamsha_id'` errors in `ga_structural` (pre-existing, no category exists before or after); the floor warnings for `ga_yoga` and `ga_vichara` (floors are aspirational); the cosmetic detector summary `anchors: 7 of 7 OK` against 19 anchors in the JSON report (N-122 (e)).
9. **Verdict-movers ruling (SS):** none arms; #3106 (TI-L0-24 Build.history) not accepted as built (rework only if the window boundary is a committed checkout-independent fact AND it requires at least one passing run after that digest AND no failed run after it, else DROP); #3105 (TI-L0-04) HOLD; #3104 (TI-L0-02) HOLD for the engine's view; 29 (`bg_panchanga` Build.dag PASS to NO_DETECTOR) rides with 1269; SS sends #3104 / #3105 to the engine after RELEASE.

---

# PART 8. OPEN QUESTIONS: 25 of 25 RESOLVED (N-122 and measurements); 4 items still open

Status key: **RESOLVED** = answered by an N-122 ruling and/or measured/read from an artifact on 2026-10-04 (the ruling or evidence is cited); **KNOWN LIMIT** = resolved by recording a limit that cannot be closed.

| Q | question (v1.2) | status and resolution |
|---|---|---|
| Q-01 | credential path for the `amjis_app` DATABASE_URL (dispatcher; G-IDX) | **RESOLVED (named; see the Q-01 finding below) with ONE residual SS ruling (S-1).** N-122: use the existing in-process path, never parse a file, never print. FOUND: the documented path of all earlier production dispatches is Secret Manager secret `amjis-pipeline-db-url` read with the operator's gcloud identity, pointed at the standing proxy `127.0.0.1:5433` (`platform/scripts/dispatch_sampurti_*.py`: "DATABASE_URL set via gcloud secrets, never .env.local"; `platform/scripts/gochara/flip_authority.py`, `rollback_authority.py`, `probes/probe_p1_identity.py`). Implemented non-interactively as `window_scripts/with_app_db.py` (used at W2.2, W2.3, W3.2, W3.3, W7.2) |
| Q-02 | clean checkout path on the operator host | **RESOLVED (N-122):** `/Users/Dev/suvarna-window/main_<sha>` as a detached `git worktree` (W0.4 at the then-tip, re-set at W1.6 to `IMG_SHA`); D6: `/Users/Dev/suvarna-window/d6_<sha>` (W0.5) |
| Q-03 | D6 re-freeze commits are local only | **RESOLVED (N-122):** pushed to #2964 AFTER Pravāha's "done", merged per the plan; the window runs from a clean checkout of that head (W0.1, W0.5). Local head today `299f2b6e9` = the re-freeze commits plus one tests-only commit; executor sha and bound plan hash re-verified unchanged on it (2026-10-04) |
| Q-04 | who makes the live served calls | **RESOLVED (N-122):** SS, through the MCP server, at W0.14 and W7.14 (both steps marked **SS**), outputs saved under `/Users/Dev/suvarna-evidence/S_L1/window/` |
| Q-05 | "zero open inquiries" | **RESOLVED (N-122) as a KNOWN LIMIT:** replaced by "the owner states he is not using the chart (2026-10-02)" plus the foreign-build_runs check (W0.15); open inquiries cannot be counted (the reader has no SELECT on `planner_inquiry_*`) |
| Q-06 | expected `panchanga_daily` count in the flip snapshot | **RESOLVED:** 544 rows on 2026-10-04 (the table has no chart column), W0.10 |
| Q-07 | explicit GO before the first dispatch | **RESOLVED (N-122):** yes, gate **A6** after the D6 STATUS (W0.P) |
| Q-08 | folders `migrate.ts` reads | **RESOLVED:** `platform/migrations/*.sql` and `platform/supabase/migrations/*.sql` (read from `migrate.ts` at origin/main, header lines 3-4); both folders: 902 files on main, 0 unapplied on 2026-10-04 (W1.1) |
| Q-09 | confirmatory lanes | **RESOLVED (N-122):** `ga_positions`, `ga_panchanga`, `ga_sensitive`, `ga_vargas` (the lanes compared Linux against macOS in `REHEARSAL_LINUX_REPORT.md` T1) plus `ga_dashas` (W1.9). Inference: T1 lists dashas, divisionals (= `ga_vargas`), panchanga, positions and sensitive; the report's own sentence "4 ephemeris lanes + `ga_vargas`" is looser |
| Q-10 | owner's D6 line | **RESOLVED (N-122):** the standing delegation covers verbatim "running owner-path plans on production for plan hashes Strategic Suvarna approves"; approved hash `f7915138b0a9ba8ad5fea98d3d7ba9311a1acbcd2065138d58ff0a595250b706` (D6.4) |
| Q-11 | merge/arm form | **RESOLVED (N-122):** the normal merge queue, armed on SS's approval at the slot, verified by the ledger (W1.2, W1.4) |
| Q-12 | W1 rollback | **RESOLVED (N-122):** W1 FORWARD-ONLY ACCEPTED (W1.3, 6.1) |
| Q-13 | docker pull for the image check | **RESOLVED (N-122):** NO docker login or pull; route B only, reproducible and PROVED: `window_scripts/image_routeB.py`, run read-only 2026-10-04 on the then-current image `a5b3b7b26`: config, three `.se1`, eight versions, `swisseph` binary and 865 source files all PASS (W1.7) |
| Q-14 | exit codes | **RESOLVED by reading the code:** D6 `commit_state_unknown` exits **1** (main()'s generic handler) with stderr `WARNING: COMMIT STATE UNKNOWN` and stdout `failed: <Exc>`; exit 1 has three shapes (D6.5); rule: exit 1 WITHOUT `REFUSED_ROLLED_BACK` in the JSON = D6.8. The 1274 executor has NO distinct wrong-target exit code (only 91, 92, 93, 95 are defined; the target check is a failing check, exit 1/2). 96 = commit unknown only for 1265 and #3045; 91 for 1274; 1 for #3072. Appendix C |
| Q-15 | Cloud Logging filters | **RESOLVED (tested read-only 2026-10-04):** the execution filter (`resource.type="cloud_run_job" AND resource.labels.job_name="brahma-build-pipeline-job" AND labels."run.googleapis.com/execution_name"="<EXEC>"` with `--freshness=2d`) returned a recent execution's lines; `resource.type="cloudsql_database" AND severity>=ERROR` with `--freshness` works (it shows routine entries from unrelated sessions, so the criterion is window-scoped and role-scoped, W3.6); the job log format is `<logger> ERROR <message>`, so the ` ERROR ` token is valid |
| Q-16 | production-parameterised `t4_stale.py` / `wstep_checks.py` | **RESOLVED (N-122):** built as LOCAL hash-pinned files `window_scripts/t4_stale_prod.py` and `wstep_checks_prod.py` (+ `MANIFEST.sha256`), exercised read-only against production on 2026-10-04 (against the unrebuilt chart they correctly report every row a survivor / FAIL; the zero-longitude statements read 0). A reviewed repo PR comes after the RELEASE |
| Q-17 | which integrity texts need parameters | **RESOLVED (measured as the reader, 2026-10-04):** all 19 registered `ga_*` texts run unparameterised and return `t`; `ga_structural`'s exceeds the reader's role default `statement_timeout=120s` and needs the session override `set statement_timeout='15min'` (completed, `t`) (W7.10) |
| Q-18 | backup / restore | **RESOLVED (N-122):** on-demand Cloud SQL backup at W0.2B, window does not start until SUCCESSFUL; restoring is the OWNER'S decision alone; every abort reaches a safe state without a restore (G-14, 6.1). Read 2026-10-04: instance `amjis-postgres` (the proxy's instance), automated backups on, PITR disabled |
| Q-19 | instance name; password without argv | **RESOLVED (N-122):** `gcloud sql instances list` shows two instances; the proxy serves `amjis-postgres`; PW.1 uses `rotate_reader_password.py` (REST body, no argv; layout check PASSed read-only). The REST call itself is UNVERIFIED until first use (S-2) |
| Q-20 | place of migration 1256 | **RESOLVED (N-122):** PW.2, right after the rotation; the post-window list is renumbered PW.1-PW.10 |
| Q-21 | showing the TRUE of the new `ph_nimitta` / `mi_bhavisya` integrity text | **RESOLVED as a KNOWN LIMIT:** the reader has no EXECUTE on `phala_anchor_identity`, so the TRUE cannot be evaluated on production; the evidence is the ledger sha256, the stored text md5 equal to the PR's, and the migration's own in-transaction post-checks (PW.3) |
| Q-22 | scoped-delete package | **RESOLVED (N-122):** final = #3072 (MERGED), BOUND `26539e35db5038a7de5106444722da2e8d7da60757814d6eac52caada2b89efa` (PW.6(4)); the checklist's `427b75ec` extension note is superseded |
| Q-23 | rows of `verify_after_apply.sql` | **RESOLVED (run read-only 2026-10-04):** 32 rows; before D6: 12 PASS / 18 FAIL / 2 INFO; `verify_before_apply.sql` 31 PASS / 1 INFO / 0 FAIL; expected after D6: 30 PASS / 2 INFO / 0 FAIL (D6.6) |
| Q-24 | `composite_shift_check.py` sha on main | **RESOLVED:** `1a7dc58e1a62cd210e20c682647bd812044f8affab738a68ba84d2269a17e728` equals `origin/main` (2026-10-04) |
| Q-25 | Nirmāṇa "evidence must be re-bound" after 1221 | **RESOLVED:** `evidence_refresh_required` exists only in the Nirmāṇa campaign-snapshot UI (`CampaignSnapshotStrip.tsx`: "Accepted registry evidence changed."), not in the dispatcher or the runner; the Suvarna dispatcher builds its manifest fresh from the live registry (a registry change moves the digest and the token), and the second rehearsal had NO re-bind step between W1 and the builds. The runbook requires NOTHING; the cockpit may display "Evidence refresh required" for `ga_structural`: not a W7 failure (the Nirmāṇa per-layer pins are historical, superseded by Nikaṣa 2026-09-29) |

**Still open (4):**
- **S-1 (SS ruling; Q-01 residual):** the ROLE behind secret `amjis-pipeline-db-url` was not verified (reading it is a login, which the author did not do). Per `infra/secrets/secret_inventory.yaml` it is the web/sidecar runtime `DATABASE_URL` (also the build job's legacy binding); the helper refuses unless `current_user` is `amjis_app`. SS rules whether this secret is the sanctioned source for the dispatcher AND for G-IDX (G-IDX has no path of its own: it reads only `DATABASE_URL` from the environment). If the helper reports `ROLE_MISMATCH`, no step proceeds.
- **S-2 (UNVERIFIED until first use):** PW.1's Cloud SQL Admin REST `users.update` call and its operation polling; the `--prompt-for-password` form is the fallback.
- **S-3 (UNVERIFIED, never a gate):** a foreign `planned` run on the canonical chart waiting on the chart's advisory lock behind our run (W2.4).
- **S-4 (slot-time confirmations, not questions):** the pushed/merged state of #2964 after Pravāha's "done" (the D6 checkout sha is known only then); the heads of #3040, #3019, #3033, #3064, #3096, #3061, #3045, #3073 at their slots.

**The Q-01 finding (for SS to rule on).** What exists today: (1) every earlier production dispatch (the 15 `l3-lane-frozen-manifest-rebuild` runs of 2026-10-01 in `build_runs.triggered_by`; the 69 earlier runs of 2026-09 were created through the cockpit API by a user identity) used a script that reads ONLY the environment variable `DATABASE_URL` (`dispatch_frozen_rebuild.py`, `suvarna_level_wave.py`; both "never read credential files"); the documented way those scripts' `DATABASE_URL` was produced is `gcloud secrets versions access latest --secret=amjis-pipeline-db-url` plus the proxy on 127.0.0.1:5433 (`dispatch_sampurti_*.py`, `flip_authority.py`); the alternative is `POST /api/cockpit/runs`, which needs a Firebase-authenticated user session the operator does not have. (2) The L3 helper `/Users/Dev/madhav-l3/dbenv.sh` reads secret `amjis-db-password` (the `amjis_app` password) but FORCES `default_transaction_read_only=on` and exports `PG*` variables, so it cannot dispatch or write; `dbenv_builder.sh` reads `data-plane-builder-db-url`. (3) `build_fact_identity_index.py` has NO path of its own: only `DATABASE_URL` from the environment (exit 3 otherwise). (4) NOT found: any pre-configured wrapper that exports a write-capable `amjis_app` URL; `rq.sh` is the reader only. Hence `with_app_db.py` (documented secret, no literal typed, role asserted, nothing printed), subject to ruling S-1.

# APPENDIX A. Evidence layout

`EV=/Users/Dev/suvarna-evidence/S_L1/window` with `TIMELINE.tsv`, `bin/` (unmodified copies of the tooling, each with its sha256), and one folder per part: `W0/`, `W1/`, `D6/`, `W2/`, `W3/`, `W7/`, `POST/<item>/`. Outside `$EV`: the W0 id maps under `/Users/Dev/suvarna-evidence/FactId/W0_S_L1_<UTC>/` (read-only, with `MAPS.sha256`); the D6 run directories under `/Users/Dev/suvarna-evidence/DataPlaneCaptureFA2/` (the executor's fixed root; `outcome.json` and `result.json` per mode); scoped-delete runs under `/Users/Dev/suvarna-evidence/ScopedDelete8/`. Raw Cloud Run job logs are mode 600 and never pasted or shared (they can contain birth instants); reports carry counts, ids and hashes only. Lock a finished folder `chmod -R a-w` when the window is accepted. The hash-pinned local scripts live in `/Users/Dev/suvarna-evidence/S_L1/window_scripts/` (`MANIFEST.sha256`; checked at W0.5): `with_app_db.py`, `image_routeB.py`, `t4_stale_prod.py`, `wstep_checks_prod.py`, `h_extract.py` (unmodified copy of the rehearsal's), `rotate_reader_password.py`. `MAPS` = the W0.9 maps folder.

# APPENDIX B. W1 files and the four BETWEEN_STATE statements

B.1 The seven W1 files (each byte-identical to its source PR head blob; sha256 verified by the preparer on 2026-10-04 and equal to the second rehearsal):

| # | file in `platform/migrations/` | source PR @ head | sha256 |
|---|---|---|---|
| 1221 | `1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql` | #2900 `0b6c857c5d0bfc6d72d130ec0b393ebbfe7d67b6` | `42b1c7c0f4cb695c1190d7c46385bd90fc37c8f95b9e07e3355356538fb41dbc` |
| 1222 | `1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql` (190 lines) | #2943 `8f056ca6f4c90e6ef259f5eff6af43c5e2c5cc85` | `10b6aac633287d10d13049baacc650a223f5f481f13417a02e02e167c87e3212` |
| 1223 | `1223_nirmana_l1_ga_vargas_output_digest_spec_seven_column_key.sql` | #2943 (same head) | `7dd8bf53c5fe3bd6ca916125149052088822c7e6bfee09fdedaffdf6b125e9f9` |
| 1224 | `1224_chart_grants_select_schema_of_record.sql` | #2896 `b07ecf491290eb2ef9b94152104c6c3c25b278a9` | `1635f68fa69546b3995ffe920d954661bff832bde305750cad84d3f02e972538` |
| 1226 | `1226_asset_registry_four_pre_s_l1_edges.sql` | #2898 `e0106d30c6fa7f141b1dd57e2c4fb9b8b8fa59e0` | `35461a64a6e23938827a3902cc215a1cb34b1b31d3a6dce9b08925a961c9802a` |
| 1252 | `1252_nirmana_l1_ga_medical_integrity_band_cut_canonical_scope.sql` | #2957 `e08dc10596db4af620bba630284f227ec5fdd2f3` | `84bfe19dded029b344d8d3d0e98046ae9206b7c6eab369ea823a6cd71d6fcea3` |
| 1254 | `1254_nirmana_l1_ga_sensitive_integrity_tier_vocabulary.sql` | #2959 `a4182a0c7d75d0e67043e971df599f9628fb4bc1` | `698090ef8d10775743160027d5ccf31f6cac00237897a8094d4e5914aa71197e` |

Already applied, NOT part of W1: 1219 (sha `dc9d65c0c23b...`), 1243 (rewritten rows-only, sha `88be3ed59aaa...`, PR #2996), 1255. NOT in the window: 1259 (PW.2).

B.2 The four S_L1_BETWEEN_STATE statements (canonical chart literal; run as the reader):
```sql
-- BS-0 identity count (section 4)
SELECT count(*) AS identity_rows FROM chart_fact_identity i JOIN chart_facts f USING (fact_id) WHERE f.chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- BS-1 formula match and the uuid36 row (section 5.1)  BEFORE 143299|1205|2925   AFTER 147751|147750|1
SELECT count(*) AS n_rows, count(*) FILTER (WHERE fact_id = left(encode(sha256(convert_to(k,'UTF8')),'hex'),16) OR fact_id = left(encode(sha256(convert_to(k||'|'||coalesce(formula_id,''),'UTF8')),'hex'),16)) AS n_formula_match, count(*) FILTER (WHERE length(fact_id)=36) AS n_uuid36 FROM (SELECT fact_id, formula_id, fact_category||'|'||fact_subject||'|'||fact_key||'|'||chart_id::text||'|'||ayanamsha_id AS k FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa') s;
-- BS-1b list the non-matching rows (expect exactly dasha_scope_cap | PRANA_DASHA | level_5_not_computed | INVARIANT | 1)
SELECT fact_category, fact_subject, fact_key, ayanamsha_id, count(*) FROM (SELECT fact_id, formula_id, fact_category, fact_subject, fact_key, ayanamsha_id, fact_category||'|'||fact_subject||'|'||fact_key||'|'||chart_id::text||'|'||ayanamsha_id AS k FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa') s WHERE NOT (fact_id = left(encode(sha256(convert_to(k,'UTF8')),'hex'),16) OR fact_id = left(encode(sha256(convert_to(k||'|'||coalesce(formula_id,''),'UTF8')),'hex'),16)) GROUP BY 1,2,3,4;
-- BS-2 zero orphans (section 5.2)  BEFORE chart_vichara|22108|0 and ga_yoga_firings|145|0   AFTER n_orphan = 0 on both
SELECT 'chart_vichara' AS t, count(*) AS n_cited, count(*) FILTER (WHERE f.fact_id IS NULL) AS n_orphan FROM chart_vichara v CROSS JOIN LATERAL unnest(v.constituent_fact_ids) AS c(id) LEFT JOIN chart_facts f ON f.fact_id = c.id AND f.chart_id = v.chart_id WHERE v.chart_id='482012f1-710e-4a25-994a-93821f5871aa' UNION ALL SELECT 'ga_yoga_firings', count(*), count(*) FILTER (WHERE f.fact_id IS NULL) FROM ga_yoga_firings y CROSS JOIN LATERAL jsonb_array_elements_text(y.constituent_fact_ids) AS c(id) LEFT JOIN chart_facts f ON f.fact_id = c.id AND f.chart_id = y.chart_id WHERE y.chart_id='482012f1-710e-4a25-994a-93821f5871aa' ORDER BY 1;
-- BS-3 receipts (section 6)
SELECT asset_id, max(observed_at) FILTER (WHERE receipt_state = 'proven') AS newest_proven_receipt, count(*) FILTER (WHERE receipt_state <> 'proven') AS n_not_proven FROM asset_provenance_receipts WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND asset_id LIKE 'ga\_%' GROUP BY asset_id ORDER BY asset_id;
```
BS-1 and BS-1b were re-run on production on 2026-10-04: `143299|1205|2925` and 142,094 non-matching rows (the old-id baseline).

# APPENDIX C. Exit-code reading (G-5): the same number means different things; read the banner and `outcome.json`

| tool | codes |
|---|---|
| `run_gated.sh` / `prerun_gate.py` (banner `GATE_V2 FAIL <reason>` and `run_gated: gate exit=N; target NOT started`; the target never started) | 0 OK; 1 a deploy run not completed or a build in flight; 2 a read failed / malformed / internal error; 64 usage; 94 missing binary; 95 test env refused; **96 wrong role or database (nothing ran)**; 97 pgenv sourcing failed; 98 target not executable; 128+n a termination signal |
| D6 executor | 0 ok; **1 has three shapes: stdout JSON `REFUSED_ROLLED_BACK` (rolled back) / stderr `REFUSED: ...` without JSON (before any connection) / stdout `failed: <Exc>` + stderr `WARNING: COMMIT STATE UNKNOWN` (commit may have happened): exit 1 WITHOUT `REFUSED_ROLLED_BACK` = D6.8**; 2 dry run or count refused; 92 interpreter or driver differs (before any connection); 93 not launched by the gate or a gate pin unbound; 95 test env. `outcome.json` status: `dry_run` / `applied` / `failed` / `commit_state_unknown` |
| 1265 and #3045 executors | as D6 plus **94 wrong target** (first-statement assertion) and **96 commit state unknown** (their own banner `WARNING: COMMIT STATE UNKNOWN`; NOT preceded by the gate's `target NOT started` line) |
| 1274 executor (#3061) | 92, 93, 95 as D6; **91 commit state unknown**; NO distinct wrong-target code (the connection check is a failing check, exit 1/2) |
| scoped delete (#3072) | 0 ok; **1 apply refused (rolled back) OR commit_state_unknown: read `outcome.json` `status`**; 2 dry run / count refused; 92; 93; 95; gate codes 94-98 |
| level-wave dispatcher | 0 ok / dry run done; 1 `DATABASE_URL` missing; 2 bad input; 3 dispatch failed after commit; 4 a gate refused (JSON `refusals`); 5 wave-by-wave stopped; 6 unexpected error or database error (a COMMIT that dropped is `COMMIT outcome unknown`: run the ACTIVE_RUN check before relaunch); 7 interrupted (a `planned` run blocks the chart until dispatched or terminalised) |
| `build_fact_identity_index.py` | 0 completed; 2 population failed (rolled back); 3 could not proceed (no `DATABASE_URL` or driver); 4 `--check` and the corrected check FAILED (rolled back) |
| `flip_detector.py` | 0 PASS (or NOT_CHECKED with `--allow-not-checked`); 1 traceback (treat as failure); 2 FAIL (or usage error / invalid hooks); 3 ALERT (a FORENSIC anchor changed); 4 NOT_CHECKED; 5 READ_ERROR; 6 REFUSED |
| `composite_shift_check.py` | 0 PASS; 2 violations listed; 6 a snapshot of another chart |

# APPENDIX D. Inputs consulted (paths; all read in this session)

`/Users/Dev/suvarna-evidence/S_L1/`: `rehearsal_final/r2/STEPS.tsv` and `r2/bin`, `r2/out`, `r2/logs`; `rehearsal_final/REHEARSAL_FINAL_REPORT_2.md`, `REHEARSAL_FINAL_REPORT.md`, `rehearsal_final/STEPS.tsv`; `RUNBOOK_INPUTS_CHECKLIST.md`; `W1_PRIVILEGE_AUDIT.md`; `IMAGE_VERIFICATION_W2.md`; `WINDOW_PREP_REPORT.md`; `W1_PR_BODY_DRAFT.md`; `GIDX_PARSER_REPORT.md`; `FA2_HOOK_REPORT.md`; `FORENSIC_GATES_REPORT.md`; `FRESHNESS_EFFECT.md`; `D6_ADMIN_GRANT_CHECK.md`; `MIG_1259_1261_REPORT.md`; `MIG_1262_REPORT.md`; `MIG_1265_REPORT.md`; `MIG_1275_REPORT.md`; `MI_BHAVISYA_APPENDONLY_REPORT.md` (+ addendum); `REVIEW_3040.md`; `REVIEW_3096.md`; `w1_privilege_audit/w7_heads_proxy.sql`. `/Users/Dev/suvarna-evidence/`: `Rebuild/` (q.sh, ps.sh, counts.py, progress.md: planning and read scripts, all reader-only), `/Users/Dev/madhav-l3/dbenv.sh` and `dbenv_builder.sh` (structure only), `REHEARSAL_LINUX_REPORT.md` (T1), `OwnerDecisions/N-91_...`, `OwnerDecisions/N-93_...`; `S_L2/REVIEW_3045_ROUND2.md`, `S_L2/work/pr_body_dpbp.md`; `TrackI/SCOPED_DELETE_8_REPORT.md`, `TrackI/REVIEW_3072.md`, `TrackI/PH_LIFEEVENTS_SCOPE_REPORT.md`; `Ephemeris/SE1_SHIFT_ANALYSIS.md`. Repository (`origin/main`, read via `git show`): `00_ARCHITECTURE/briefs/suvarna/exec/S_L1_BETWEEN_STATE_v1_0.md` (v1.5), `s_l1_attribution_hooks/HOOKS_W7_HAND_READBACK_v1_0.md` (v1.9), `HOOKS_COMPLETENESS_v1_0.md`, `L1_MV_REFRESH_AFTER_REBUILD_v1_0.md`, `gate_v2/run_gated.sh`, `platform/scripts/governance/FLIP_DETECTOR_README.md`, `README_level_wave.md`, `suvarna_level_wave.py`, `platform/python-sidecar/scripts/build_fact_identity_index.py`. The D6 branch `/Users/Dev/suvarna-d6rf` (read-only): the plan document, `d6_dataplane_capture_fa2_exec.py`, `make_plan.py`. Also read in the second pass (read-only): `platform/scripts/dispatch_frozen_rebuild.py`, `dispatch_sampurti_*.py`, `gochara/flip_authority.py`, `probes/probe_p1_identity.py`, `platform/scripts/migrate.ts`, `infra/secrets/secret_inventory.yaml`, `.github/workflows/deploy.yml` (secret names only), `python-sidecar/pipeline/orchestrator/runner.py` (writer-gap event), the executors of D6, 1265, 1274, #3072 and #3045 (exit codes), Cloud Logging (a recent execution; read-only), `gcloud sql instances/backups list` (read-only), the Cloud Run job and Secret Manager secret NAMES (never a value). Production was read only through `rq.sh` (suvarna_reader): the baselines quoted as "read 2026-10-04" were re-measured while writing (counts, build ids, tracker rows, `server_version` 15.18, function md5 `1e079261...`, receipts, freshness, integrity md5s, builder memberships empty, `rolsuper(postgres) = f`, `relforcerowsecurity(charts) = f`, `ph_pramana` text md5 `45f89d48...`).

*End of S_L1_WINDOW_RUNBOOK v1.3 (DRAFT for SS review).*
