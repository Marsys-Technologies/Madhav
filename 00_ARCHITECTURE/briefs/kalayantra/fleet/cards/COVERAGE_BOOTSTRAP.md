# COVERAGE_BOOTSTRAP — B-0c cards (DRAFT — pending the B-0c independent review; rework round 1)

Maps every applicable MUST of root CLAUDE.md §I and §N.1–§N.8, decisions D-1, D-6 (revised), D-9, findings KV-08 and KW-02, and plan §3 "Kept" (rows 1–52), plus the plan rules the cards carry beyond those (rows 53–64), to what carries it for `BOOTSTRAP.md` (BS), `BOOTSTRAP_REVIEWER.md` (BR), `FIXTURE_BUILDER.md` (FB), `FIXTURE_VERIFIER.md` (FV) and `OWNER_SURROGATE.md` (OS). Sources: `KALAYANTRA_RELAUNCH_PLAN_v2_7.md`, `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md`, `.claude/agents/kalayantra-owner-surrogate.md` as tracked at commit `e709f60d7fcd4559227a25a4d5d83d6431c396b6`; root `CLAUDE.md` v8.0; the cockpit's rework rulings R1, R3 and R7.

A card is capped at 1,500 tokens (plan §7), measured with the real program and recorded in `TOKEN_MEASUREMENT.json`. Plan §3 lets a binding rule live in a card line, a packet clause or an executable check, so a card keeps what only the model can do or refrain from doing; the rest is named here.

Cell values:
- **line ids** — carried by those card lines. An id in parentheses is another card's line, given for context only.
- **N/A — reason** — not applicable to this role.
- **packet §8.n** — not a card line: a clause the packet must carry in that section of plan §8 whenever the item touches the matter. No packet exists yet and `kypacket.py` (B-1) does not yet check for the clause, so this is an obligation on the packet's author and its reviewer. Where `FB-09` is named, the builder blocks instead of improvising when the packet is silent.
- **X-nn** — carried by the executable check of that id in the second table: it exists in the reviewed tree today, at the file and symbol named.
- **input §n** — OWNER_SURROGATE only: stated in a document that the job input binds by blob hash and that `OS-02` obliges the surrogate to read before ruling (plan §4a and §15; the owner decisions). It is the surrogate's packet.
- **partial … → carrier** — the card line carries only the stated part; the arrow names what carries the remainder.
- **GAP** — carried by nothing that exists today; the cell says what is missing. Reviewer to rule.

| # | source | MUST | BS | BR | FB | FV | OS |
|---|---|---|---|---|---|---|---|
| 1 | §I B.1 | Facts at Gaṇita; derivations at the Bodha boundary with a ledger; interpretation above only | N/A — builds control-plane scripts; emits no chart fact or interpretation | N/A — reviews control-plane changes only | packet §8.4 — when a fixture item touches a layer writer; FB-09 | partial FV-10 (a breach of the contract section is a finding) → packet §8.4 | N/A — rules on owner-waits; makes no chart claim |
| 2 | §I B.3 | Every claim above Gaṇita lists the fact ids it consumes; no unsourced "classically known" | N/A — as row 1 | N/A — as row 1 | packet §8.4 — as row 1; FB-09 | partial FV-10 → packet §8.4 | N/A — as row 1 (its analogue is `evidence` in OS-09) |
| 3 | §I B.8 | Canonical artifacts carry version, status, changelog; registries agree | BS-11 | BR-09 | packet §8.4 — when a fixture item changes a canonical artifact; FB-09 | partial FV-10 → packet §8.4 | partial OS-05 (a bundle change is veto-class `plan_bundle_change`) → X-14 |
| 4 | §I B.10 | No fabricated computation; never invent chart values | BS-10 | BR-09 | FB-10 | FV-10 | OS-03 |
| 5 | §I B.11 | Interpretive queries route through Bodha synthesis first | N/A — answers no interpretive query; X-22 gives it no chart-data server | N/A — as BS | N/A — answers no interpretive query | N/A — answers no interpretive query | N/A — answers no interpretive query |
| 6 | §I Scope | Declare what you may / must not touch before editing; respect other campaigns' `must_not_touch` | BS-04, BS-05, BS-06 | BR-02, BR-06 | FB-06, FB-07 | FV-05, FV-06, FV-10 | OS-03, OS-04 |
| 7 | §I Isolation | Never build or commit in the shared checkout; worktree + PR | BS-01, BS-15; X-21 | BR-02, BR-03 (commits nothing) | FB-05, FB-11, FB-12 | FV-05 (commits nothing) | OS-04 (the shared checkout is a hard stop) |
| 8 | §N.1 | External layer names only; never "L0–L5" externally | packet §8.4 — when the component emits a layer name; a numbered layer is a finding at review (BR-09) | BR-09 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | GAP — no line: nothing binds the wording of the surrogate's notifications and decisions |
| 9 | §N.1 | Asset ids use underscore prefixes; dot-notation retired | packet §8.4 — when the component emits an asset id | partial BR-09 (a numbered layer is a finding) → packet §8.4 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — creates no asset id |
| 10 | §N.2 | Writer is a `@register` `WriterBase` subclass with `run` or `plan_substeps` + `run_substep` | N/A — builds no writer; a writer path is outside every bootstrap scope (BS-04) | N/A — reviews no writer; a writer path in the diff is a finding (BR-06) | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — builds nothing |
| 11 | §N.2 | Runs on `ctx.db_conn`; never commits or closes it | N/A — as row 10 | N/A — as row 10 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — builds nothing |
| 12 | §N.2 | Never writes `asset_throughput` | N/A — as row 10 | N/A — as row 10 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — builds nothing |
| 13 | §N.2 | `chart_id` + `birth_params` from `ctx.config` | N/A — as row 10 | N/A — as row 10 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — builds nothing |
| 14 | §N.2 | A needed contract change → STOP, raise with the native | BS-05 | BR-06 | FB-07; X-16 | partial FV-10 (a path on the Prohibited list is a finding) → packet §8.2 | OS-04 |
| 15 | §N.3 | Brahmagyan `ON CONFLICT` on global reference tables; other layers per-chart delete-then-insert | N/A — writes no layer table (BS-04) | N/A — as row 10 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — builds nothing |
| 16 | §N.4 | Floors are aspirational; never fabricate rows | BS-10 | BR-09 | FB-10 | FV-10 | OS-03 |
| 17 | §N.4 | No audience tier in writers | N/A — builds no writer | N/A — as row 10 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — builds nothing |
| 18 | §N.4 | Deterministic-first: Python over LLM for computation | BS-08 | partial BR-07 (runs the tests and negative cases itself) → packet §8.4 | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — computes nothing; rules on evidence it inspects (OS-03) |
| 19 | §N.4 | No JH-parity oracle | N/A — verifies no chart computation | N/A — verifies no chart computation | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — verifies no chart computation |
| 20 | §N.4 | Cockpit truth: chart-scoped `count_sql` on `asset_registry` | N/A — registers no asset | N/A — as BS | packet §8.4 — only if a fixture item registers an asset; FB-09 | partial FV-10 → packet §8.4 | N/A — registers no asset |
| 21 | §N.4 | Surgical migrations, verified applied; never edit an applied migration | N/A — a migration is outside every bootstrap scope (BS-04) | N/A — a migration path in the diff is a finding (BR-06) | packet §8.5; FB-09; "verify applied" is the readback job's (plan §6) | partial FV-10 → packet §8.5 | OS-05 (a protected window is veto-class), OS-04 (its platform approval stays with the owner) |
| 22 | §N.4 | Honest verification tiers via `verification_vocab.py` constants; never `two_pass_verified` unearned | N/A — emits no chart-row tier (general rule BS-09) | N/A — as BS (general rule BR-08) | packet §8.4; FB-09 (general rule FB-10) | partial FV-10 → packet §8.4 | N/A — emits no tier (analogue OS-03) |
| 23 | §N.5 | Reference the Gaṇita `fact_id`, inherit its value; a disagreement is a halt-worthy bug; MSR constituent facts resolve | N/A — consumes no chart fact | N/A — as BS | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — consumes no chart fact |
| 24 | §N.6 | Serving density (1–4): catalog ≠ confirmed; `hardFloor`; verdict layer never empty; `density_contract` | N/A — builds no served surface | N/A — as BS | packet §8.4 — only if a fixture item touches a served surface; FB-09 | partial FV-10 → packet §8.4 | N/A — builds no served surface |
| 25 | §N.7.1 | Narration restates a cited `fact_id`; never re-derives | N/A — writes no narration | N/A — as BS | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — writes no narration |
| 26 | §N.7.2 | Single-row selection pins `fact_key` with a total `ORDER BY` | N/A — writes no selector | N/A — as BS | X-17 | X-17 | N/A — writes no selector |
| 27 | §N.7.3 | No wrapper-local constant shadows a Gaṇita value | N/A — holds no chart value | N/A — as BS | packet §8.4; FB-09 | partial FV-10 → packet §8.4 | N/A — holds no chart value |
| 28 | §N.7.4 | A verification flag has a real detector, or is null | BS-09 | BR-08 | FB-10 | FV-10 | OS-03 |
| 29 | §N.7.5 | Each narration layer has its own semantic / golden-value test | N/A — writes no narration | N/A — as BS | packet §8.6 — only if a fixture item adds narration; FB-08 | partial FV-09 (runs the tests itself) → packet §8.6 | N/A — writes no narration |
| 30 | §N.7.6 | An honest null beats an invented judgment | BS-10, BS-17 | BR-09, BR-10 | FB-10, FB-13 | FV-11, FV-13 | OS-03 |
| 31 | §N.8 | Every status, grade or PASS is computed by a detector that can fail; else null | BS-09, BS-07 | BR-08, BR-07, BR-10 | FB-10, FB-08 | FV-09, FV-10, FV-11 | OS-03, OS-06; X-10 |
| 32 | D-1 | Control-plane changes only in Wave B, scoped per packet | BS-04 | BR-06 | FB-07 (prohibited to this role) | partial FV-10 (control-plane code is on the Prohibited list) → packet §8.2 | OS-03 (cannot alter D-1) |
| 33 | D-1 | Independently reviewed | BS-15 (never reviews its own PR; the review is the reviewer's: BR-04, BR-07) | BR-04, BR-07, BR-10 | N/A — makes no control-plane change (FB-07) | N/A — reviews fixture items only | OS-08 |
| 34 | D-1 | Installed with a receipt | BS-06 (never installs), BS-17 (reports the exact head) | BR-11 (never installs), BR-05 (one head) | N/A — changes no control-plane code (FB-07) | N/A — writes nothing installable (FV-06) | input §15 (D-1, D-9); X-04 |
| 35 | D-1 | Campaign builders keep the prohibition | N/A — not a campaign builder; its own scope is BS-04 | N/A — as BS | FB-07 | partial FV-10 → packet §8.2 | OS-03 |
| 36 | D-6 revised | No PR merges to main during the certification hold; a merge authorisation is a durable local request, executed after certification-done, recorded with its actual workflow outcome | BS-15 | BR-11 | FB-11, FB-03 (no real remote or PR) | FV-12 | partial OS-08 (authorises only; never merges itself; the controller executes after the hold) → input §15 (D-6 revised) |
| 37 | D-9 | Installation uses the independently accepted immutable head bound in the receipt; no merge needed in Wave B | BS-06, BS-17 | BR-05, BR-12 (one proposed verdict at one head) | N/A — fixture items are never installed | N/A — as FB (analogue FV-08: one registered head) | input §15 (D-9); X-04 |
| 38 | KV-08 | The GitHub protected-environment approval is a human act: authorise the bounded request only; record it as an external approval dependency; no veto deadline substitutes for it | BS-13 (no protected-window dispatch) | N/A — calls no network service (BR-03) | FB-03 | FV-03 | partial OS-04 (the approval is a hard stop), OS-05 (the authorisation is veto-class `protected_window`) → input §4a (4a.3: bounded request only; external approval dependency; no veto deadline in its place); X-15 |
| 39 | KW-02 | Child jobs take no role lock and write no role-state file; they return results | BS-03, BS-16 | BR-02 (writes nothing under the run directory), BR-12 | FB-05, FB-13 | FV-07, FV-13 | OS-10 |
| 40 | §3 Kept | COVERAGE: every applicable MUST maps to a card line, a packet clause or an executable check | this table; `tests/test_cards.py` checks its ids both ways | this table | this table | this table | this table |
| 41 | §3 Kept | FROZEN manifest; conforming new writers permitted; a frozen change is STOP for native authorisation | BS-05 | BR-06 | FB-07; X-16 | partial FV-10 → packet §8.2 | OS-04 |
| 42 | §3 Kept | Tracker is the only ledger; typed guarded completion; verdict identity | partial BS-03 (writes no tracker event; its result file is its report) GAP — nothing here binds who records `KV3-B-*` progress in the tracker (plan §0.4 registers those ids) | BR-11, BR-12; its verdict becomes a review receipt only through the cockpit; X-04 | FB-11, FB-12 (fixture tracker) | FV-08, FV-12 | OS-07 (routine `ky decide`), OS-05 (nothing published for a veto class) |
| 43 | §3 Kept | Independent verifier runs the tests itself; builder results are inputs | BS-07, BS-15 | BR-04, BR-07 | FB-11 | FV-07, FV-09 | OS-08 |
| 44 | §3 Kept | Required CI checks; `Kāla DB Tests` — absent, skipped or failed is not success | BS-07, BS-17 (its own named commands; the checks are judged at review and at merge authorisation: BR-10, OS-08) | partial BR-10 (every required check ran and passed; an unrun one blocks) → packet §8.6 | partial FB-08 (runs the precheck command) → packet §8.6 | FV-11 | OS-08 |
| 45 | §3 Kept | Semantic acceptance obligations of retained items | BS-07, BS-17 | BR-07, BR-10 | FB-08 | FV-09, FV-11 | OS-03 |
| 46 | §3 Kept | Protected-window flow is an owner-approved GitHub action | BS-13 | N/A — calls no network service (BR-03) | FB-03 | FV-03 | OS-04, OS-05 |
| 47 | §3 Kept | Executor operations: request-bound pre-acceptance, backup/restore/dry-run, quiescence evidence | BS-13 (no executor submission) | N/A — calls no network service (BR-03) | FB-03 | FV-03 | N/A — owned by PRE-ACCEPT / EXECUTE jobs; OS-03 forbids waiving evidence; OS-04 hard-stops production deletion or restore |
| 48 | §3 Kept | Migration allocation | N/A — a migration is outside every bootstrap scope (BS-04) | N/A — a migration path in the diff is a finding (BR-06) | packet §8.5; FB-09 | partial FV-10 → packet §8.5 | N/A — allocates nothing |
| 49 | §3 Kept | No worker holds `DATABASE_URL` | BS-12; X-02, X-03 | BR-03; X-02, X-03 | FB-04 (a names-only check that prints no value) | partial FV-04 (reads, prints and stores none; never lists the environment) GAP — the launcher that refuses such an environment, `kyjob.sh` (plan §7, exit 78), is a B-1 deliverable; this card is first used in B-3, after it | OS-04 (credentials are a hard stop; never handles one); X-02, X-03 |
| 50 | §3 Kept | No model merges or dispatches production | BS-13, BS-14, BS-15 | BR-03, BR-11 | FB-03, FB-11 | FV-03, FV-12 | OS-08 (authorises; the controller merges), OS-05 |
| 51 | §3 Kept | Routing by rule; escalation grants no authority | N/A — model fixed by the roster; X-05 binds it | N/A — as BS | N/A — routing is the dispatcher's script; the same card binds whichever model runs | N/A — as FB | N/A — not a routed role |
| 52 | §3 Kept | One governance record pair (C-2 banner + SESSION_LOG entry; C-4 close) | N/A — written by the planner (B-5) and `finalize.sh`; BS-15 forbids ledger PRs | N/A — writes no governance record | N/A — as BS; FB-11 | N/A — writes no governance record | N/A — writes no governance record |
| 53 | plan §5; ruling R1 | Job scratch paths come from the job environment; unset or not absolute → stop, blocked, write nothing; temporary files only there | BS-02; X-01 | BR-01, BR-02; X-01 | FB-01 | FV-01, FV-06 | OS-01; X-01 |
| 54 | plan §5, §6 | Every job leaves a truthful result file; a job without one is not a success | BS-16, BS-17, BS-18; X-06, X-07, X-20 | BR-12; X-06, X-07, X-20 | FB-13; X-07 | FV-13; X-07 | OS-10; X-06, X-07 |
| 55 | plan §14 B-3 | Rehearsal isolation: the fixture tracker on its reserved port, fixture remotes and backend only; a breach is a rehearsal failure | N/A — not a rehearsal role | N/A — not a rehearsal role | FB-02, FB-03 | FV-02, FV-03 | N/A — not a rehearsal role |
| 56 | plan §7, §6; ruling R7 | A reviewer changes no source and publishes nothing; its writes are limited to evidence, caches, `TMPDIR` and the slot DB | N/A — author role | BR-02, BR-03, BR-11; X-18, X-19 | N/A — author role | FV-05, FV-06, FV-12 | N/A — reviews no source |
| 57 | plan §6 (VERIFY, ARTIFACT) | Reviewer ≠ author; exactly the registered head, before and after | N/A — author role | BR-04, BR-05 | N/A — author role | FV-07, FV-08 | OS-08 (authorises only on such a review) |
| 58 | plan §4a.3, §6 SURROGATE; rulings R3, R19a | Veto class: nothing published at proposal; the target is bound; the 30-minute window opens only on a submitted notification; only an owner veto stops a proposal; late FAILED/VETOED lines are answered as anomalies | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | OS-05, OS-06; X-08, X-09, X-10, X-12, X-23 |
| 59 | plan §4a.3 | Hard stops are never delegated: recorded, notified, that item paused | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | OS-04; X-08, X-13 |
| 60 | plan pairing rule | Surrogate authority comes from the job input's verified binding; never a retired plan or installed filenames | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | OS-02; X-11 |
| 61 | plan §4a.3, §6; ruling R19a | The surrogate appends every decision itself to DECISIONS_SURROGATE.jsonl; routine tracker decisions are published with ky decide. (I) INTERPRETATION: their awaiting items move to done after success (or when no tracker decision exists), without replacing another file. The surrogate writes or requests no action record and never executes proposed effects: the veto handler executes and records veto effects after the window; a later actor records routine effects under its own identity | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | OS-07, OS-09; X-08 |
| 62 | plan §3 Cut, §8; owner policy | One PR per packet or item; no ledger PR; no rebase or force-push; a job creates no worktree or copy | BS-01, BS-15 | BR-03 (no git verb that changes state) | FB-05; partial FB-11 (obeys the Do-not list) → packet §8.9 | N/A — commits nothing (FV-05) | N/A — commits and pushes nothing (OS-10) |
| 63 | plan §4a.2 | Reopening a circuit breaker or restarting a loop needs recorded changed evidence | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | N/A — not the surrogate | X-24 (no card line since rework 1) |
| 64 | plan §8.2, §8.8 | A builder edits only what its packet owns and exits through the packet's PR template | BS-04, BS-15 | BR-06 (every changed path is one the packet enumerates) | FB-06, FB-12 | FV-10 | N/A — builds nothing |

GAP cells (3): 8.OS, 42.BS, 49.FV

## Executable checks named above

Each exists today at the file and symbol given (`tests/test_cards.py` asserts both). What a check refuses is a statement about that code, reviewed in its own B-0c area; it is not re-proved here.

| id | file | symbol | refuses or guarantees |
|---|---|---|---|
| X-01 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `ENV_REQUIRED` | a launch whose job environment lacks `JOB_SCRATCH` or `KY_SCRATCH`, or whose `JOB_SCRATCH` is not the launch input's `job_scratch` (ruling R1) |
| X-02 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `ENV_FORBIDDEN` | a launch environment that carries `DATABASE_URL`, `*_DATABASE_URL`, `PGPASSWORD`, `ANTHROPIC_API_KEY`, `*TOKEN*` or `*SECRET*`; the job receives the allow-listed names and nothing else |
| X-03 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `EXIT_CREDENTIAL_ENV` | exit 78 when such a name is set in the supervisor's own environment (names printed, never values) |
| X-04 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `def manifest_gate` | every launch once the bootstrap manifest, one of its components or its ACCEPTED review receipt no longer matches disk |
| X-05 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `def qualification_findings` | a launch without a PASS qualification receipt that binds this model, effort, permission mode, flags, MCP configuration and environment names |
| X-06 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `no_result` | counting a job as a success when it left no `result.json`, a symbolic link, a schema-invalid one or one naming another job or item |
| X-07 | `00_ARCHITECTURE/briefs/kalayantra/fleet/schemas/job_result.json` | `ky.job_result/1` | a result with a missing or unknown key, a blocked status without its reason, a PR number without a head |
| X-08 | `00_ARCHITECTURE/briefs/kalayantra/fleet/schemas/surrogate_decision.json` | `ky.surrogate_decision/2` | a decision record with a missing or unknown key; a veto record without its deadline, `kind` or `fingerprint`; a routine record with a deadline; a hard stop in any state but PROPOSED |
| X-09 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py` | `VETO_WINDOW_S` | effectiveness earlier than 30 real minutes after the later of the handler's first sight and the notification, or before the record's own deadline |
| X-10 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py` | `notification_unverified` | a veto-class decision whose record claims a submitted notification that the notifier's own journal line does not confirm (and one whose record says it was not submitted) |
| X-11 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py` | `authority_changed` | a veto-class decision whose authority binding is missing, unknown or no longer the authorised one at expiry |
| X-12 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py` | `target_changed` | a veto-class decision whose target kind is unknown, malformed, or whose recomputed fingerprint differs from the recorded one |
| X-13 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py` | `hard_stop_never_delegated` | making a hard-stop record effective |
| X-14 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py` | `class PlanBundleChange` | a bundle change taking effect other than as the next activation record chained to the previous one, with its review receipts |
| X-15 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py` | `class Unavailable` | any success for `campaign_start` or `protected_window`: no executor exists, so no expiry starts a campaign or dispatches a window |
| X-16 | `00_ARCHITECTURE/briefs/kalayantra/fleet/precheck.sh` | `orchestrator/writers/__init__` | an item diff that touches the frozen orchestrator files, another campaign's briefs or root `CLAUDE.md` |
| X-17 | `platform/scripts/governance/check_fact_category_pinning.py` | `fact_key` | in CI, a selector that reduces `chart_facts` rows without pinning `fact_key` |
| X-18 | `00_ARCHITECTURE/briefs/kalayantra/fleet/templates/LAUNCH_CONFIG.bootstrap-reviewer.json` | `Bash(git commit*)` | in the reviewer's launch: Edit, Write and the git verbs that change state, by rule (not a sandbox: `python3` stays allowed) |
| X-19 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyqualify.py` | `denied_bash` | qualifying a reviewer configuration whose denied commands are not observed refused with no effect |
| X-20 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `EXIT_TIMED_OUT` | a job running past its deadline: its process group is terminated (exit 124) |
| X-21 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `def _git_findings` | a launch outside the job's worktree, on another branch than the launch input's, or whose base is not an ancestor of HEAD |
| X-22 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py` | `the content must be exactly {"mcpServers":{}}` | a bootstrap launch with any MCP server configured |
| X-23 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kynotify.sh` | `echo "notify=$notify"` | (guarantees) exactly one stdout line, `notify=submitted`, `notify=failed` or `notify=dry`, and a journal line ending with the same observed result |
| X-24 | `00_ARCHITECTURE/briefs/kalayantra/fleet/kyloop.py` | `def breaker_gate` | reopening an open circuit breaker on unchanged evidence |

## Rules moved out of the cards in rework round 1

The round-1 cards measured 2,049–2,115 tokens against the cap of 1,500. What left a card, and what carries it now:

| card | rule that left the card | carried by |
|---|---|---|
| BOOTSTRAP | "No MCP servers" | X-22 |
| BOOTSTRAP | stop when a credential variable is set in the environment | X-02, X-03 (the card keeps: never read, print, request or store one; never list the environment) |
| BOOTSTRAP | "never `/tmp`, the repository root or `/Users/Dev`" for temporary files | the card's "only there or under `$TMPDIR`"; the supervisor refuses a scratch root under a system temporary directory (`SCRATCH_ROOT_NEVER` in `kyboot.py`) |
| BOOTSTRAP | the contents of the PR body | packet §8.8 (PR template) |
| BOOTSTRAP | layer names and asset-id prefixes | packet §8.4 when the component emits them; a numbered layer is a reviewer finding |
| BOOTSTRAP | the D-1 narrative (Wave B only, reviewed, installed by `install.sh` with a receipt) and the D-9 explanation of `head_sha` | explanation, not a rule on the builder; its rules stay as lines (packet paths only; never install; never review its own PR; exact head) |
| BOOTSTRAP | the supervision narrative ("no dispatcher, no `kyjob.sh`") | explanation; the launcher is `kyboot.py` (X-04, X-05) |
| FIXTURE_BUILDER | build standards: writer contract, idempotency, `fact_id` citation, tier constants, no fabricated rows to a floor, no audience tier, no JH-parity oracle, Python computes, migration number and applied migrations, version/status/changelog | packet §8.4 and §8.5; the card blocks (`uncovered: <area>`) when the packet is silent; X-17 for selector pinning; the general no-fabrication and earned-signal rules stay as a card line |
| FIXTURE_BUILDER | layer names and asset-id prefixes | packet §8.4, same blocking line |
| FIXTURE_BUILDER | the list of allowed classes | packet §8.2 (Owns + allowed classes) |
| FIXTURE_BUILDER | the four frozen orchestrator paths | the manifest `fleet/FROZEN_PATHS.txt` named in the card; X-16, which the card's precheck step runs |
| FIXTURE_BUILDER | no rebase or force-push; merge `origin/main` only when DIRTY outside generated files; one PR per item; no ledger PR | packet §8.9 (Do-not list), which the card obliges it to obey |
| FIXTURE_BUILDER | test-first detail for artifact and operation packets; the `precheck.sh --item` command | packet §8.6 (Acceptance) |
| FIXTURE_BUILDER | the exact `ky review … --detail "PR #<n> @ <head>"` line | packet §8.8 (PR template) |
| FIXTURE_VERIFIER | the diff check-list of build standards and layer names | packet §8.4, §8.5, §8.9 through the card's "a breach of its contract section or Do-not list is a finding" |
| FIXTURE_VERIFIER | frozen paths, control-plane code and other campaigns' files as separate findings | packet §8.2 (Prohibited) through the card's "a path … on its Prohibited list" |
| FIXTURE_VERIFIER | "No `DATABASE_URL`" | row 49: the launcher, a B-1 deliverable — a GAP today |
| FIXTURE_VERIFIER | what the controller checks before it publishes | explanation; controller-owned (plan §6) |
| OWNER_SURROGATE | what happens at expiry (recheck, publish, execute, VETOED or FAILED; a failed notification prevents effectiveness); only an owner veto stops a proposal; late FAILED/VETOED lines are anomalies | OS-05, OS-07; X-09 to X-13 by id: X-09, X-10, X-11, X-12, X-13 |
| OWNER_SURROGATE | KV-08 detail: bounded request only; external approval dependency; no veto deadline in its place | input §4a (4a.3); X-15; the card keeps the approval as a hard stop and the authorisation as veto-class |
| OWNER_SURROGATE | D-6 revised detail: durable local request under `HOLD_MERGES`, recorded with its outcome; never remove `HOLD_MERGES` | input §15; the card keeps: never merge yourself, the controller executes after the hold, never alter an owner decision |
| OWNER_SURROGATE | D-9: installation from the accepted head bound in the receipt | input §15; X-04 |
| OWNER_SURROGATE | D-7 detail: propose the resume on `READY_TO_START`, binding the release-receipt and final-manifest digests | input §15; the fingerprint of kind `campaign_start` binds both files (X-12); X-15 |
| OWNER_SURROGATE | plan-bundle change through a `_PROPOSED` plan file and a chained activation record | the card's kind `plan_bundle_change`; X-14 |
| OWNER_SURROGATE | reopening a breaker needs changed evidence; an unchanged condition keeps its decision id | X-24 for the breaker; the decision-id half has no card line and no check today: it stays in the agent definition (mandate 7), and the dispatcher's handled-proposal check (plan §6) is a B-1 deliverable |
| OWNER_SURROGATE | worktree limit (under 8 for this campaign, at most 14 in total) | the owner decisions (B-0a block, bound input), not a card line |
| OWNER_SURROGATE | "record `submitted=false` if the notifier is not installed"; "deadline = now + 30 min" | replaced by ruling R3 in the card: the exact stdout line; the time taken after the call; that time + 30 min |
