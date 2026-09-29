---
artifact: SUVARNA_INDEPENDENT_REVIEW_ASTRA_DISPOSITION
canonical_id: SUVARNA_INDEPENDENT_REVIEW_ASTRA_DISPOSITION
version: "1.0"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-30
produced_in: session "Strategic Suvarṇa"
disposes: "reviews/INDEPENDENT_REVIEW_GPT6_ASTRA_v1_0.md (L.9; verdict DO NOT APPROVE; F1–F18; ten launch conditions; Q1–Q22; §5)"
folded_into: "plan set v1.5 (SUVARNA_CAMPAIGN_PLAN_v1_5.md and companions; plan_model.json)"
changelog:
  - "1.0 (2026-09-30): every finding and every launch condition disposed: FIXED in a document, CODE→spec (CODE-36…CODE-65, for the tracker code agent), SUPERSEDED by N-28/N-29 (with the reason), or DEFERRED to a named item. Two native rulings (N-28, N-29) changed the design between the review and this fold; where they change a finding's premise it says so."
---

# Disposition of the GPT-6 Astra independent review

**The verdict stands for v1.4.1.** Astra's central point — an unearned green can become permission for autonomous
action (Q21) — is accepted in full. v1.5 answers it three ways: (1) one fail-closed gate evaluator in code (CODE-36);
(2) authority, holds and the builder credential moved behind the OS boundary the swarm cannot cross (N-35–N-37);
(3) ten launch gates LG.1–LG.10 in the plan model, each with a detector or a validated evidence item, all prerequisites
of N-1 (FI-7).

**Two rulings changed the premises after the review.** N-28 takes the native out of every loop except physical setup,
scope changes and the go signal: gates Astra assigned to the native (merges, L0 dispatches, re-seals, J1) are now decided
by Strategic Suvarṇa (SS), with independent reviews where the plan names them. N-29 makes data-plane rows regenerable:
destructive operations need a rebuild plan, a serving guard and a recorded fingerprint, not a dump or a native approval.
Where this changes a finding, the row says **SUPERSEDED** and why; the underlying safety property is kept in a new form.

**Counts.** Findings (18, primary disposition): **FIXED 7** (F2, F9, F13, F14, F16, F17, F18) · **CODE→spec 9** (F1, F3,
F4, F6, F7, F8, F10, F11, F12) · **SUPERSEDED 2** (F5 in part, F15) · **DEFERRED 0** as primary (F14's per-asset part is
deferred to Track A). Conditions (10): **9 become launch gates** with a detector (LG.1–LG.8, LG.10); **1 becomes
evidence items on existing gates** (condition 9 → E5.6, E5.7, F3.PROOF, which block J1 and W0); **4 are modified** by
the rulings (5 by N-25b, 6 by N-34, 9 by N-29, 10 by N-28), none dropped.

## §1 · Findings

| # | Sev | Disposition | Where it landed |
|---|---|---|---|
| F1 | BLOCKER | **CODE→spec** (CODE-36, CODE-47) + doc | A decision item is done only through the fail-closed evaluator: a parseable log, a typed affirmative `outcome` for the exact `revision`, an allowed writer for that id, and every prerequisite done; an item event can never complete a decision item; a malformed log line blocks evaluation. Negative tests: absent, refused, revoked, superseded-by-corrupt-line, forged item event, wrong revision, premature (prerequisite open). Gate **LG.1**. Plan §9; arch §11.2. N-28 moves most decisions to SS; the finding applies unchanged to SS's decisions. |
| F2 | BLOCKER | **FIXED** (N-36, N-37, NATIVE_SETUP NS.1–NS.4) + CODE-37, CODE-38 | Separate user `suvarna`; the decisions log, the hold-clear ledger, the settings and the control code (hook, Monitor, tracker, broker, merge gate) are native-owned and read-only to the swarm, whole ancestry included (`authority/`, `config/`, `control/`); the builder credential is held by `_suvarnabuild` and used only through the broker. Residual (stated in charter §13): the reader credential and the swarm's own GitHub and Claude tokens are readable by swarm code; the reader is read-only by privilege (D6). Gate **LG.2** proves it as `suvarna` (replace-through-parent, hook edit, native-secret read, builder-secret read). |
| F3 | BLOCKER | **CODE→spec** (CODE-38) + doc | Stage-aware Monitor matrix: S0 setup · S1 launch and analysis · S2 builds · S3 global L0. S1 requires the reader readable **to the swarm** and every native secret unreadable **to the swarm** (both measured as `suvarna`, so they no longer contradict); `builder_scope` reads `not_applicable` before S2 (never warn, never a launch blocker); a required check that fails to measure blocks. Native paths and UIDs pinned in config, never `~`-expanded. Gate **LG.3**. Runbook §2. |
| F4 | BLOCKER | **CODE→spec** (CODE-39, CODE-53) + doc N-35 | Holds enforced at the dispatch boundary — the broker and the merge gate refuse while any hold is active, whatever the command text; the hook fails closed on any malformed payload for Bash and Agent; holds live in an append-only ledger the swarm can add to but never truncate or delete (`uappnd`, native-owned directory); a native hold clears only by the native. Gate **LG.4** (malformed payload, missing interpreter, indirect script dispatch, hold removal attempt, truncation attempt). |
| F5 | BLOCKER | **SUPERSEDED in part** by N-25b/N-28; rest **CODE→spec** (CODE-40, CODE-43) | The claim tested changed: the swarm is now *meant* to merge (N-25b: CI green, a recorded gate ACCEPT for the head SHA, path guards; no required human review). What Astra asked for still holds for the new claim: identities pinned by login; every rule of ruleset 20141220 read; an unverifiable bypass policy reads unknown; server refusal demonstrated. Gate **LG.5**: a direct push to `main` refused; a PR with a failing or missing required check refused; a ruleset edit by the bot refused; a green PR merged only through `merge_gate`; the post-merge audit flags a planted violation. |
| F6 | BLOCKER | **CODE→spec** (CODE-41, CODE-42, CODE-63) + doc N-34 | `/loop` dropped; the durable supervised runtime is an N-1 prerequisite (L.14): launchd services as `suvarna`, change-triggered stateless passes with backoff, one fenced owner per queue, a heartbeat per session, the watchdog in the Monitor's repair, idempotent lane launch (atomic claim, duplicate refusal, caps, PID recorded before spawn, reconciliation at pass start). Gate **LG.6**. |
| F7 | MAJOR | **CODE→spec** (CODE-44) | The tracker calls `elevated_assets(ref, repo)` at the committed ref; E6.3t's detector becomes `elevated_interface_ok`, which exercises the real caller (reads unknown until built). |
| F8 | MAJOR | **CODE→spec** (CODE-45) | Wave membership only from the frozen `LEVEL_MAP.json`, pinned by hash with `FAMILY_ASSETS.json`; exact population; the family set validated as the union; terminal dispositions stay in the denominator; a map change needs an SS decision id in the file. Wave items carry the hash pins (`pinned_by` SS at J1). |
| F9 | MAJOR | **FIXED** (N-32; F3.GUARD, F3.PROOF) + CODE-46 | F-3's concrete form: all eight keys dropped (`no_fk`: zero keys of any kind); `assert_l2_msr_delete_safe` replaced without its refusal; the delete/reinsert path proved on the rehearsal database with referencing rows present; the transitive footprint measured (plan §5.3). The `allow` escape removed from `fk_no_cascade`. |
| F10 | MAJOR | **CODE→spec** (CODE-48) | `scorecard_pass` binds the scorecard to the inspector's blob hash at the ref, the registry revision, a successful CI run on that commit (run id, conclusion, head SHA) and a non-empty population; E1.7's engine checks validated too. |
| F11 | MAJOR | **CODE→spec** (CODE-47, CODE-49, CODE-50) | Presence predicates replaced on acceptance items: `ci_job_passed` for tests (E4.1c, E5.1–E5.5), `evidence_verified` with value checks for the cut-over equality (E4.3), strict schema for `registry_coverage` (non-null revisions, ancestry, pinned expected cell count, N/A rules each citing an SS decision). The plan-model lint (**LG.8**) refuses a presence-only detector on an item marked `acceptance`. |
| F12 | MAJOR | **CODE→spec** (CODE-51) | Fetch failures are errors; a result carries its source commit and measure time; per-type maximum age; expired or failed-refresh evidence reads unknown and blocks dependants; a deadline on each detector run. |
| F13 | MAJOR | **FIXED** (Track E E7.1, E5.3, E5.9) + CODE-52, CODE-53 | Server enforcement in E7.1: the route rejects an asset outside scope, any family asset (read from `FAMILY_ASSETS.json` at the deployed commit), `clear_before`, another chart, a concurrent run, and a stale `expect_job_image_tag` (the check-to-dispatch race); the global-L0 grant (N-31) is its own scope. `wave_deployed` binds exact head ref, PR, squash merge commit and writer hashes. The transitive write/delete footprint is measured per wave (E5.9). |
| F14 | MAJOR | **FIXED** (arch §12.16, Track E E5.5) + DEFERRED→A.Lx (per-asset fingerprint declarations) | Semantic fingerprint contract (natural-key order, canonical JSON, declared volatile columns excluded, an equivalence policy for embeddings); certificate generations; an invalidation watermark `elevated_assets` requires; an acceptance epoch per layer close with at most two re-walks before SS reviews. Each asset brief declares its fingerprint (Track A). |
| F15 | MAJOR | **SUPERSEDED** by N-29 | The dump and restore drill protected data N-29 declares regenerable. The property kept is recovery: E5.7 becomes the **L0 rebuild drill** (rebuild L0 on the rehearsal database from sources; fingerprints compared with production); pre/post fingerprints and diffs are retained to campaign close (cheap), not purged at certification; other charts' exposure is covered by the serving guard (N-33). |
| F16 | MAJOR | **FIXED** (Track E E5.6) + CODE-47 | Rehearsal environment defined and owned: a local PostgreSQL cluster run by `suvarna` (no production identity), schema by `migrate.ts` at the landing commit, seeded from reader dumps, orchestrator from source at the job image's commit (residual: source, not the image); global L0 writes isolated by construction; six executable acceptance cases; artifacts validated by `evidence_verified`. |
| F17 | MAJOR | **FIXED** (plan §6.6, §6.7) + SUPERSEDED in part by N-28 + CODE-41, CODE-42, CODE-59 | Native latency and review windows no longer exist (N-28); SS decision latency has an SLA and an escalation ladder; review effort is in the estimates (25–40 % of build effort); stage throughput assumptions stated; passes trigger on actionable change with backoff; spend metered per pass; reforecast after E5.6 and at G2. |
| F18 | MINOR | **FIXED** | E5 is 40–65 h everywhere; 31 listed vs 32 claimed stays explicitly E2.1's reconciliation; the heartbeat threshold is three times the maximum pass backoff (one rule); the document map no longer calls the package stale; plan §3.5 is the freeze rule of record (the register header's broader wording is aligned by E4.1-build-002). |

## §2 · Launch conditions

| # | Astra's condition | Disposition | Plan-model gate |
|---|---|---|---|
| 1 | Authorization gates pass negative tests | gate | **LG.1** `evidence_verified` `launch/LG1_GATE_EVAL.json` (CODE-36 suite at the control release) |
| 2 | Swarm identity cannot alter authority or control code, read native secrets; untrusted tests without builder credentials | gate | **LG.2** `evidence_verified` `launch/LG2_ISOLATION.json` + L.16a `monitor_check_ok isolation` |
| 3 | Stage-aware, executable launch check matrix | gate | **LG.3** `monitor_check_ok stage_ready_S1` (CODE-38) |
| 4 | Hold enforcement end-to-end negative test | gate | **LG.4** `evidence_verified` `launch/LG4_HOLD.json` |
| 5 | GitHub refuses the swarm's merge/update attempts | **modified by N-25b**: the swarm may merge, only through `merge_gate`; GitHub must refuse everything else | **LG.5** `main_protected` (v2) + `evidence_verified` `launch/LG5_MERGE.json` |
| 6 | Interim runtime proves exclusive ownership and recoverable launch | **modified by N-34**: proved on the durable runtime (no interim) | **LG.6** `evidence_verified` `launch/LG6_RUNTIME.json` + L.14 |
| 7 | Pinned control release passes independent regression and real-CLI integration | gate | **LG.7** `evidence_verified` `launch/LG7_CONTROL_RELEASE.json` (commit = the pinned tag) |
| 8 | Later-stage acceptance gated by substantive evidence | gate + model edits (E6.3t, B.W*, E4.3, F3.*, E7.1, freshness) | **LG.8** `evidence_verified` `launch/LG8_MODEL_LINT.json` (CODE-58) |
| 9 | Rehearsal and recovery plans with owners, identities, acceptance cases; completion blocks J1 or the wave | **modified by N-29** (recovery = rebuild) | evidence items on existing gates: E5.6, E5.7 (rebuild drill), F3.PROOF → J1.6 and B.W0 |
| 10 | Native accepts an operating schedule; attendance windows; family notice acknowledged; spend reporting | **modified by N-28**: no native schedule or attendance; replaced by SS's decision runtime with an SLA, decisions enumerated with their owner (plan §8), the notice acknowledged by exact version (gates A.L3f, not N-1) | **LG.10** `evidence_verified` `launch/LG10_OPERATIONS.json` (SS runtime answered a test park within its SLA; metric events from the first passes) |

## §3 · Answers that changed decisions (Q1–Q22)

- **Q2** (first wave depends on others): F-3 no longer waits on another session (decided by principle; Track E lands
  the migration). A small off-production rehearsal (E5.6) precedes W0, as recommended.
- **Q4** (native as bottleneck): Astra counted 42–44 native acts to G2. v1.5: **zero** decisions, merges or dispatches;
  the native's acts are NATIVE_SETUP NS.1–NS.10 before N-1 and NP.1 after E7.1.
- **Q5** (convergence): acceptance epoch and bounded re-walks (F14).
- **Q6** (forged decisions): OS ownership (N-37), typed outcomes (CODE-36), corruption blocks; the N-25 prose classifier is retired (CODE-61).
- **Q17** (standing spend): change-triggered passes (CODE-41) replace the fixed ten-minute cadence.
- **Q18** (granularity): logical waves kept; landing groups may be smaller dependency-closed groups within a wave (plan §5.4 step 4).
- **Q19** (failure modes): each row mapped to CODE-41, -42, -62, -63 or accepted with its residual (Mac loss: hold-and-park; state in git and files).
- **Q22**: N-25a/b, N-26, N-27, N-14.R236 decided as Astra agreed; F-3 decided with the guard, generation and downstream proof Astra required (F9); N-23 decided (subscription to G2, metered, revisited at G2 — Astra's "meter first"); G16 decided with the bounded class rule; N-4 stays one batch of agendas decided by SS, re-seals ordered and independently reviewed.

## §4 · What Astra could not assess (§5) — now

| Item | v1.5 |
|---|---|
| Production privileges, FKs, guard, images | FKs and the guard read 2026-09-30 as `suvarna_reader` (plan App. A); images via the broker preflight (E7) |
| D6 still effective | Monitor `credential_readonly`, continuous |
| Claude Code permission behaviour | LG.7 real-CLI matrix under `suvarna` at 2.1.239 |
| Tier documents, ledgers, populations | bundle v2.1 adds nothing new here; still excluded (size); figures sourced |
| Current tests / CI of the tracker | LG.7 records the run at the pinned control release |
| Rehearsal, kill switch, incident drills | LG.4, LG.6, E5.6 |
| Family acknowledgements and dates | Pravāha's tracker read by `peer_tracker_item`; Saṅgam/Kṣetra design now Suvarṇa's (Track F) |
| Completion date and money | reforecast after E5.6 and G2 from measured throughput and spend (plan §6.6) |

## §5 · CODE→ specs for the tracker code agent (CODE-36 … CODE-65)

All in `platform/scripts/governance/suvarna_tracker/` unless named. Each lands with failing-first tests. A detector type
not yet built reads **unknown**, never done.

1. **CODE-36 · Fail-closed gate evaluator** (the code agent's `gates.py`, in progress on 2026-09-30, already removes the item-event fallthrough and reads a `revision=` marker from `detail`; this spec supersedes the marker with typed fields). A `done_by: decision` item is
   done iff: the authoritative log was supplied and every line parsed (any malformed line → the whole evaluation reads
   `unknown` with detail "decisions log corrupt at line n"); the latest line for the id has `state: decided`,
   `outcome` ∈ the item's `accept_outcomes` (default `["approve"]`), `revision` equal to the item's `revision` pin when
   one is set, and `writer` ∈ the item's `writers` (default `["strategic-suvarna"]`; N-1 is recorded by SS with the
   native's words as its source). **Prerequisites are checked at recording time, not re-litigated later:** `decide`
   refuses an `approve` for an item-bound decision while any `depends_on` item reads not done, and stores
   `prereq_snapshot` (each prerequisite's id, status source and evidence at that moment); the evaluator treats an
   `approve` line without a valid snapshot (for an item with prerequisites) as not decided. Ongoing safety after the
   decision is the Monitor's stage checks, which stop dispatch, not an un-deciding of past gates. `decide.py` gains required `--outcome`, `--revision`, `--rationale`; lines without
   `outcome` are legacy and read `approve` only if `detail` was recorded before 2026-09-30 (grandfather list pinned by
   id). `events.validate` refuses `--state done` on a decision item; `state.py` ignores item events for them. Tests: the
   seven negative cases in §1 F1.
2. **CODE-37 · Authority paths and integrity.** `decisions.default_path()` → `$SUVARNA_HOME/authority/DECISIONS.jsonl`;
   readers never open the lock file for writing; Monitor check `decision_log_integrity`: file and directory owned by the
   pinned native UID, not writable by the running (swarm) user, and the log's previously seen prefix (sha256 of the first
   N bytes, stored in `run/monitor_state.json`) unchanged — any change other than an append blocks.
3. **CODE-38 · Stage-aware Monitor.** Config `monitor_config.json` pins `native_user=Dev`, `native_uid`, `native_home=/Users/Dev`,
   `swarm_user=suvarna`, the probe list and the stage. Stages S0–S3 with required checks per stage; new status
   `not_applicable`; a required check that raises or cannot measure → `block`; composite checks `stage_ready_S1`,
   `stage_ready_S2`, `stage_ready_S3`. `isolation` (run as `suvarna`): the process user; every probe path unreadable; a
   `find` sweep for readable credential-like files under the native home (the NATIVE_SETUP NS.3 pattern) empty; the
   reader file readable and mode 600; `authority/`, `config/`, `control/` unwritable; settings hash equals the recorded one.
4. **CODE-39 · Hold ledger.** `hold.py`: `--set [--native] --reason` appends `{id, actor, native, reason, ts}` to
   `authority/HOLDS.jsonl` (O_APPEND only); `--clear <id> [--native]` appends to `authority/HOLD_CLEARS.jsonl` (fails for
   the swarm user by permission; a native hold's clear requires `--native` and the native writer); `active()` = set ids
   without a matching clear, plus `run/SUVARNA_HOLD` if present. `hold_guard.py` reads `active()`; any malformed or
   unreadable payload → exit 2 for Bash and Agent; refuses any command naming a hold or authority file for write or
   delete. Invert `test_main_malformed_stdin_exits_0_and_logs` and the wrapper test.
5. **CODE-40 · `main_protected` v2.** Spec: `ruleset_id`, `required_checks` (list, must be a subset of the rule's
   contexts), `required_approvals` (0), `merge_queue: true`, `bypass_actors: []`, `bot_login`, `native_login`. Read the
   ruleset by id and every rule; missing or malformed `bypass_actors`, or an unreadable ruleset → unknown; the bot's
   repository permission via the collaborators API must be `push` without `maintain`/`admin`.
6. **CODE-41 · Durable runner.** `runner.py --session engine|exec`: idle until N-1 is decided (CODE-36); each tick runs a
   deterministic readiness check (new events since the committed offset, ready queue items, decision changes, failures,
   due timers); invokes one `claude -p` Conductor pass only on actionable change, else backs off (1, 2, 4 … 30 minutes);
   one fenced owner per queue (`run/locks/queue_<session>.lock` with a fencing token written into the queue state line; a
   pass whose token changed refuses to commit); heartbeat `--session`; usage-limit errors classified and waited out; env
   `DISABLE_AUTOUPDATER=1`, `CLAUDE_CODE_OAUTH_TOKEN` from `~/.config/suvarna/claude_oauth.env`. launchd plist templates
   `runtime/launchd/com.marsys.suvarna.{tracker,monitor,runner.engine,runner.exec}.plist` (`UserName suvarna`,
   `KeepAlive`), and `com.marsys.suvarna.strategic.plist` (user agent of the native). Monitor `repair` relaunches a
   stale runner with `launchctl kickstart -k system/<label>`, at most three per hour, then sets a hold.
7. **CODE-42 · Lane launcher.** Atomic claim `run/claims/<qid>` (O_CREAT|O_EXCL) before anything; refuse if a live pid
   holds it; caps per kind from config enforced at claim time; the model and effort actually passed to the CLI; an
   `item running` intent event written before spawn, the pid recorded after; at pass start, claims with dead pids are
   reconciled (remote branch pushed → review; else failed, retry once).
8. **CODE-43 · Merge gate and audit.** `merge_gate.py --pr <n>`: CI green on the head SHA (all required checks); a
   gate-reviewer ACCEPT event naming that SHA; the path guard (`path_guard.py`, shared with the CI job
   `Suvarṇa path guard`: family paths from `FAMILY_ASSETS.json` and family code globs, other workstreams' reserved paths
   from `CAMPAIGN_COORDINATION.md`, migrations outside 1200–1299, `.claude/**`, `.github/**`, `CLAUDE.md`); no active
   hold; decisions re-read; then enqueue with `gh pr merge <n> --squash --auto` and emit the event. Monitor check
   `merge_audit`: every PR merged by the bot has an ACCEPT for its merged head, green checks, a clean path guard; a
   violation → hold + a revert PR opened.
9. **CODE-44 · Exact ELEVATED in the tracker.** `levels_elevated`/`assets_elevated` call
   `asset_elevation_tracker.elevated_assets(ref, repo)`; new detector type `elevated_interface_ok` (imports the module at
   the committed ref in a temporary worktree, calls it through the tracker's own caller, done iff it returns a set and a
   planted unreadable input raises).
10. **CODE-45 · Frozen membership.** Spec keys `level_map`, `level_map_sha256`, `family_assets_sha256`; denominator = every
    asset at the level range in the frozen map; family exclusion = exactly `family_set`, validated as the union of the six
    lists; a terminal disposition counts only if recorded in the ledger; a map whose `authorized_by` is not a decided SS id
    → unknown.
11. **CODE-46 · `fk_no_cascade` strict.** `target: no_fk` → done iff zero foreign keys of any kind reference the table;
    `set_null` → every one `confdeltype='n'`; remove `allow`; anything else pending.
12. **CODE-47 · `evidence_verified` detector type.** Spec `{path, expect: {key: value}, required: [keys], max_age_hours,
    commit_key, commit}`: the JSON under `$SUVARNA_HOME/evidence/` parses; every `expect` value equals; every `required`
    key non-empty; age within bound; `commit_key`'s value equals the pinned commit when given. `events.validate`: evidence
    for `done` must be an existing path under `evidence/` or a PR/commit reference that resolves.
13. **CODE-48 · `scorecard_pass` bound.** Add `inspector_sha256` (the inspector file's blob at the ref), `registry_revision`,
    `ci_run_id`; verify the CI run (conclusion success, head SHA = the commit that introduced the scorecard); non-empty
    `population` per test; `engine_build_checks` non-empty and all PASS when the spec lists `engine_checks: true`.
14. **CODE-49 · `registry_coverage` strict.** Non-null `registry_revision` and `inspector_commit` (an ancestor of main);
    `covered_cells` equal to the spec's pinned `expected_cells`; each `per_asset_pending` entry names asset and criterion;
    each N/A rule cites a decided SS decision id.
15. **CODE-50 · `ci_job_passed` detector type.** Spec `{workflow, job, paths}`: the newest completed run of that job on a
    `main` commit containing every path concluded success.
16. **CODE-51 · Detector freshness.** Check every `git fetch` return code; stamp a refresh only on success; results carry
    `source_commit` and `measured_at`; per-type `max_age` (default 30 min); expired → unknown; a 120 s deadline per run.
17. **CODE-52 · `wave_deployed` v2.** `LANDING.json` `{wave, head_ref, pr, merge_commit, writer_hashes, components}`: exact
    head ref (no prefix match), base `main`, the PR's merge (squash) commit an ancestor of `job_sha` (and of `deployed_sha`
    for serving components), writer-file hashes at `job_sha` equal the recorded.
18. **CODE-53 · Build broker.** `broker.py` (run only as `_suvarnabuild` through sudo): refuses while any hold is active;
    `--assets` must be ⊆ the frozen level minus `family_set` at `origin/main` (chart scope) or ⊆ active L0 assets (global
    scope, N-31); never `--level`, never clear; reads `builder.env` itself; passes `expect_job_image_tag` from its own
    preflight; logs every request to `run/broker.log` without secrets. `~/.config/suvarna/bin/suvarna-build` for the swarm
    is a two-line wrapper calling exactly the sudoers command.
19. **CODE-54 · `peer_tracker_item` detector type** (built by the code agent on 2026-09-30, uncommitted; matches this spec and adds an optional `evidence_required` and a loopback-only host rule). Spec `{url, item, expect}` (default `done`): GET the peer tracker's
    `/api/state`, find the item by id anywhere in the payload, compare `status`; unreachable → unknown.
20. **CODE-55 · `acks_from` v2.** Detail must equal the marker exactly (e.g. `ACK FI-8 notice v1.3`), timestamp after the
    spec's `since`; actors as listed.
21. **CODE-56 · Decisions loader.** Folded into CODE-36 (corruption blocks; typed fields).
22. **CODE-57 · `native_setup_verify.py`.** Runs every NATIVE_SETUP check as `suvarna`; writes
    `evidence/launch/NS_VERIFY.json` as a flat map `{"NS.1": "PASS", …, "NS.9": "PASS", "all_pass": true,
    "control_commit": "<sha>", "details": {…}}` (flat keys, so `evidence_verified` can check each); prints the fix
    command for each failure. The Monitor re-runs it every 24 hours, so a setup that later breaks reads stale and blocks
    the stage check.
23. **CODE-58 · Plan-model lint.** `plan_model_lint.py`: unique ids; every `depends_on` resolves; acyclic; every detector
    type registered or in the pinned CODE list; no item with `acceptance: true` uses `main_has_file(s)`, `main_file_contains`
    or `branch_merged`; every `done_by: decision` item has a decision id; writes `evidence/launch/LG8_MODEL_LINT.json`.
24. **CODE-59 · Spend metering.** The runner and launcher read `usage` from `claude -p --output-format json` and emit
    `metric` events per pass (session, role, model, input/output/cache tokens); the digest totals them.
25. **CODE-60 · SS decision runtime support.** `strategic_runner.py` (native account): triggers an SS pass on a new
    `decision requested` event or a gate whose prerequisites all read done; records SLA metrics; escalates a park older than
    24 h in the digest and older than 72 h by a macOS notification to the native (information only).
26. **CODE-61 · Retire the N-25 prose classifier** (`_classify_n25_outcome`); isolation reads the decided N-25 by typed outcome.
27. **CODE-62 · Event log robustness.** `read_since_offset` tracks the inode and restarts from 0 on rotation; short writes
    retried and checked; a malformed complete line is counted and surfaced as a Monitor `warn`.
28. **CODE-63 · Heartbeat freshness by receipt.** The Monitor judges heartbeats by the event log's own append order and
    file mtime, never by the event's `ts`; a future `ts` reads stale; one heartbeat per session.
29. **CODE-64 · Guard test for pending types.** `test_every_detector_type_in_the_real_plan_model_has_a_registered_detector`
    (`tests/test_detectors_v13.py`) fails on the v1.5 plan model today, by design, for the four CODE→ types
    (`evidence_verified`, `ci_job_passed`, `elevated_interface_ok`; `peer_tracker_item` has since been built; 685 of
    686 tests passed on 2026-09-30 against the v1.5 model). Either land those four types first, or let the test accept a type listed in the model's
    `notes.code_types_pending` **only while** the tracker reads such an item `unknown` (assert that too); remove the
    allowance when the list is empty.
30. **CODE-65 · Review bundle for v1.5.** `review_bundle.default_entries`: the plan `SUVARNA_CAMPAIGN_PLAN_v1_5.md` (not
    v1_4), plus `NATIVE_SETUP_v1_0.md`; `superseded_entries` covers v1_0…v1_4; the decisions snapshot from
    `authority/DECISIONS.jsonl` (falling back to `run/DECISIONS.jsonl` only before NS.4); one bundle serves both
    reviewers (N-30).
