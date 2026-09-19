# L3 KĀLA — AUTONOMOUS EXECUTION STATE

> Durable "you are here" for the L3 Kāla autonomous campaign. Updated and **pushed** at every
> packet close. Companion append-only ledger: `EVENTS.jsonl`.
> Governing prompt: `../MADHAV_L3_AUTONOMOUS_EXECUTION_PACKAGE_v1_0.md` §B.
> Governing plan: `../MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`.

## Headline

| Metric | Value |
|---|---|
| **Accepted N/22** | **0 / 22** |
| Newly accepted this run | — |
| Campaign definition | `t3-2026-09-11-8b884eac` |
| Canonical chart | `482012f1-710e-4a25-994a-93821f5871aa` |
| Run started | 2026-09-20 ~02:10 IST |

## Phase-0 scorecard (SEPARATE — never merged into Accepted N/22)

| Item | State |
|---|---|
| Preservation branches on origin | **9 / 9 ✅** |
| Integration worktree + branch | ✅ `codex/madhav-l3-claude-code` @ `cdc701afa` |
| Governing docs staged in worktree | ✅ 4 / 4 extracted + 3 planning docs |
| Governing docs merged to main (B1) | 🟡 PR #2692 green, in protected merge queue |
| DP-SD-021 authored (B2) | ✅ strategic ledger §13 |
| Governance surfaces refreshed (B3) | ✅ CLAUDE.md §C.5+§E, CURRENT_STATE §2, CLAUDECODE_BRIEF.md (PR #2692) + CAMPAIGN_COORDINATION.md L3 party row (pushed directly to `campaign-coordination` per its own protocol) — **all done** |
| Deployment re-verified independently (C1) | ✅ **gate is OPEN — see finding below, corrects the restart notice** |
| 22-asset baseline (C2) | ✅ done to the extent credentials allow — live MCP-based serving snapshot (8 assets sampled); raw row counts blocked, recorded as BL-3 |
| W1 function contract read (C3) | ✅ complete — full dispatch plan ready, see finding |
| Salvage packets verified (D1–D6) | **6 / 6 ✅ — all already satisfied on `main` via PR #2607, zero PRs needed** |
| Branch triage record (D7) | ✅ 112 branches classified |
| Field dossiers | 2 / 22 (ka_graha_sancara, ka_dasha_kala — full field-contract dossier complete) |

## Per-asset state (22 active identities)

Columns: producer / data / integrated / deployed / value / **terminal**.
All rows start `— / — / — / — / — / NO`.

| # | Asset | Type | P | D | I | Dep | V | Terminal |
|---|---|---|---|---|---|---|---|---|
| 01 | ka_graha_sancara | service | — | — | — | — | — | NO |
| 02 | ka_dasha_kala | service | — | — | — | — | — | NO |
| 03 | ka_muhurta_seva | service | — | — | — | — | — | NO |
| 04 | ka_tulana | pure/service | — | — | — | — | — | NO |
| 05 | ka_gochara_resonance | rows | — | — | — | — | — | NO |
| 06 | ka_moorti_nirnaya | rows | — | — | — | — | — | NO |
| 07 | ka_kota_chakra | rows | — | — | — | — | — | NO |
| 08 | ka_vedha_gochara | rows | — | — | — | — | — | NO |
| 09 | ka_tithi_pravesha | rows | — | — | — | — | — | NO |
| 10 | ka_sudarshana_varsha | rows | — | — | — | — | — | NO |
| 11 | ka_yojaka | rows | — | — | — | — | — | NO |
| 12 | ka_avadhi | rows | — | — | — | — | — | NO |
| 13 | ka_gochara | rows | — | — | — | — | — | NO |
| 14 | ka_gochara_v3_century_materialize | rows (HOLD) | — | — | — | — | — | NO |
| 15 | ka_sangam | rows | — | — | — | — | — | NO |
| 16 | ka_kalasutra | rows | — | — | — | — | — | NO |
| 17 | ka_vighnakara | rows | — | — | — | — | — | NO |
| 18 | ka_taranga | rows | — | — | — | — | — | NO |
| 19 | ka_kala_darshana | rows | — | — | — | — | — | NO |
| 20 | ka_jivana_parva | rows | — | — | — | — | — | NO |
| 21 | ka_bhavishya_lekha | rows | — | — | — | — | — | NO |
| 22 | ka_kshetra | staged rows | — | — | — | — | — | NO |

`ka_gochara_sweep` — retired, protected history, outside the denominator, never rebuilt.

## Packet queue

| Packet | Owner | Worktree | Branch | Status | Exit evidence | Next action |
|---|---|---|---|---|---|---|
| A1 preservation push | strategy session | main checkout | — | **DONE** | 9/9 SHAs match origin (see EVENTS) | — |
| A2 integration worktree | strategy session | `/Users/Dev/madhav-l3/integration` | `codex/madhav-l3-claude-code` | **DONE** | clean @ `cdc701afa` | — |
| A3 durable state | strategy session | integration | — | **DONE** | this file + EVENTS.jsonl | — |
| B1 governing docs → main | conductor (run 2) | integration | `codex/madhav-l3-claude-code` | **DONE (committed), PR next** | 10 files at `9e3a9c1c4`, docs-only, verified diff-only vs main | open PR from this branch tip |
| B2 DP-SD-021 | conductor (run 2) | integration | `codex/madhav-l3-claude-code` | **DONE** | `MADHAV_DATA_PLANE_STRATEGIC_LEDGER_v1_0.md` §13 | include in B1 PR |
| B3 governance refresh | conductor (run 2) | integration | `codex/madhav-l3-claude-code` | **DONE (main-branch part)** | CLAUDE.md v7.5, CURRENT_STATE v6.79, CLAUDECODE_BRIEF.md v1.0 ACTIVE | include in B1 PR; still owe CAMPAIGN_COORDINATION.md L3 row (separate push to `campaign-coordination` branch) |
| C1 deploy re-verify | conductor (run 2) | read-only | — | **DONE** | see finding below: web@`cdc701afa` 100% traffic, MCP/sidecar@`66b962f29`, builder image@`66b962f29`, both deploy runs' job-level status independently read via `gh run view --json jobs`, Codex lease independently read as RELEASED on `origin/campaign-coordination` | — |
| C2 22-asset baseline | conductor (run 2) | read-only | — | **PARTIAL / BLOCKED_STRUCTURAL(no-read-role-on-public-schema)** | `retrieval_census_ro` (the only documented read-only DB role, `platform/scripts/harvest/_db.ts`) has USAGE only on `information_schema`/`pg_catalog` — **not** `public`, where `kala_*` and the generation-head tables live. Did not escalate to a stronger credential (out of proportionality/role-separation scope for an ad hoc query). Row-count baseline deferred to the orchestrator's own build-time reporting in Wave E rather than hand-queried. | native ruling optional: authorize a scoped read-only grant on `public` for verification, or accept orchestrator-reported state as sufficient (recommend the latter — matches doctrine that builders/orchestrator, not ad hoc sessions, are the legitimate reader/writer of `public`) |
| C3 W1 function contract | conductor (run 2) | read-only | — | **DONE (signatures)** | `open_l1_data_plane_generation` (migration 1035) requires literal `session_user = 'data_plane_builder'` — **SECURITY DEFINER but caller-identity-gated**; W1 generation can only be executed by the real `brahma-build-pipeline-job` authenticated as `data_plane_builder`, never by an ad hoc session even with elevated creds. This resolves E1/E2 planning: dispatch the real builder job, do not hand-write SQL. | — |
| D1+D3 Kshetra P0 + DHARA correction | subagent `ac646ccb3` | own worktree | — | **DONE — NO-OP, already satisfied** | All 17 touched files byte-identical on `main` via the same PR #2607 squash (from a *further-corrected* generation of this work on `codex/madhav-data-plane-execution`, dated one day after the 4 assigned branches). Verified both safety properties by reading live code (15-table `_OWNED_TABLES` scoped to `lel_derived=FALSE`; mutation-free planner + `KshetraReplacementHeld` refusal). Fresh tests: 720/11-skip/2-xfail full suite, 86 DHARA-specific, 112 P0-safety-specific. No PR opened. | — |
| D2 Bhavishya P0 | subagent `a0e4039b2` | own worktree | — | **DONE — NO-OP, already satisfied** | All 3 target files (`ka_bhavishya_lekha.py` + 2 test files) byte-identical on `main` already — the exact reviewed commits landed via the same squash-merge PR #2607 (`fa9857f00`). Verified the safety properties are genuinely implemented (fail-closed refusal on protected-row mutation, not just present) and ran tests fresh today: 25/26 passed (1 DB-integration skip) on the target files, 1525/41-skip/2-xfail on the full L3 suite. No PR opened (would be an empty diff). | — |
| D4 Yojaka preservation | subagent `a9801fa14` | own worktree | — | **DONE — NO-OP, already satisfied** | Forensically isolated the exact commits (`06c3d944d`, `7697c43b3`/`fbf7803dc`) out of the 118-commit-ahead branch; both target files byte-identical on `main` via PR #2607. Proved it by actually attempting the cherry-pick and confirming the conflict was pure history-shape, not content gap. Verified in code that the full lossless multi-domain projection is retained and the scalar exists only for the genuine `ph_nimitta` compatibility path. Fresh tests: 4/4 target, 1525/41-skip/2-xfail full L3 suite. **Noted 2 other commits in the same branch** (`b0c5652ba`, `47131772b`, "harden L3 first frontier source contracts") touch 9 *other* L3 writers incl. `ka_dasha_kala.py` — worth checking whether those are ALSO already on main (relevant to E4). | — |
| D5 W0 field register | subagent `a41f66de3` | own worktree | — | **DONE — NO-OP, already satisfied** | The 800-line register already exists on `main` (landed via PR #2607, `fa9857f00`, 2026-09-16), and main's version is a *corrected* revision (35 row-level type/nullability fixes) vs. the source branch's stale 2026-09-15 draft — landing the branch version would regress main. No PR opened; correctly declined rather than manufacturing one. | — |
| D6 U05 registry | subagent `abbdfc3eb` | own worktree | — | **DONE — NO-OP, already satisfied** | Isolated the real U05 fix to 2 commits (`7cba13281`, `01a64ca53`) touching `L3_kala/query_temporal_activation.ts`/`query_projections.ts`. `query_projections.ts` byte-identical on main; `query_temporal_activation.ts` on main is a strict superset (has everything the branch has plus later closure/pagination work) — force-applying the branch version would regress main. Verified requested_filters/effective_filters are genuinely distinct fields by reading main's code directly. Ran fresh tests: 146/158 L3_kala suite, 1943/2121 full registry suite, both green modulo pre-existing skips. No PR opened (nothing to merge). | — |
| D7 branch triage | conductor (run 2) | integration | `codex/madhav-l3-claude-code` | **DONE** | `MADHAV_L3_BRANCH_TRIAGE_DISPOSITION_v1_0.md` @ `2955e2f13`; PR #2655 confirmed already closed | — |
| W1-RESEARCH (informs E1/E2) | subagent `acba0c5c8` (Opus) | read-only | — | **DONE** — full precise dispatch plan produced, disposable-DB rollback rehearsal completed | see §★ FINDING below | — |
| E1 W1 L1 generation | conductor | integration | — | **BLOCKED_STRUCTURAL(no-authenticated-dispatch-credential)** | see §★ FINDING below | native must supply either a `/api/cockpit/runs`-capable session or an authorized write DB credential |
| E2 W1 L2 generation | conductor | integration | — | not needed tonight (L2/`bo_*` is off the critical path for E3/E4 — see finding) | — | — |
| E3 ka_graha_sancara terminal | conductor | own worktree | — | **BLOCKED_STRUCTURAL** — needs no W1 at all (chart-agnostic, reads only L0 `bg_ephemeris`/live swisseph), but the value test must target the actually-live `call_ephemeris_at_t` router path per the dossier finding; ready to execute the moment the campaign wants a service-proof-only pass | full dossier ready | — |
| E4 ka_dasha_kala terminal | conductor | own worktree | — | **BLOCKED_STRUCTURAL(same credential gate as E1)** | reads L1 `ga_dashas`/`chart_dashas` directly (not through any generation table); the canonical `get_dashas`/`ganita_dashas_get` serving path honestly refuses pending a completed L1 generation for this chart, while other paths (e.g. `kala_muhurta_get`) read the same table's real data successfully — W1 makes the canonical path consistent, it does not fix a broken table | dispatch plan ready | — |

## Observed environment (re-verify before acting)

| Fact | Value | Observed |
|---|---|---|
| `origin/main` | `cdc701afad40c1ffe8d83468df5127b26e370fba` (#2691, docs-only) | independently re-read 02:20 IST |
| web ready revision | `amjis-web-probe-cdc701afad40-35467786237-1`, 100% traffic → source `cdc701afa` | **independently read via `gcloud run services describe`, 02:20 IST** |
| MCP ready revision | `amjis-mcp-probe-66b962f2994f-35464335676-1` → source `66b962f29` | independently read, 02:20 IST |
| sidecar ready revision | `amjis-sidecar-probe-66b962f2994f-35464335676-1` → source `66b962f29` | independently read, 02:20 IST |
| builder job image | `brahma-pipeline:66b962f2994f0a7500c285025740cd5861534d8c` | independently read via `gcloud run jobs describe`, 02:20 IST |
| Deploy run 35464335676 (head `66b962f29`) | ALL jobs success: migrate, sidecar, web, MCP, pipeline-job, earned-outcome | independently read via `gh run view --json jobs`, 02:16 IST |
| Deploy run 35467786237 (head `cdc701afa`, docs-only PR #2691) | migrate ✅ web ✅; MCP/sidecar/pipeline-job correctly **skipped** (no-deployable-change); earned-outcome ✅ | independently read via `gh run view --json jobs`, 02:16 IST |
| Migration 1040/1041 | applied at head `66b962f29`, corroborated by the successful "Apply Routine DB Migrations" job on both runs above (CI is fail-closed on migration error, so job success is real evidence, not self-report) | independently corroborated, not directly SELECTed (see C2 finding) |
| Migration high-water | `platform/migrations` 1040 · `platform/supabase` 1041 | unchanged |
| **L3 migration range** | **1070–1119** (Pūrṇa 1042–1069; shared ≥1120) | DP-SD-021, ratified §13 |
| Codex lease | `MADHAV-PURNA-DELIVERY-DATA-PLANE-ALLOWLIST-SUCCESSOR-20260920` — **RELEASED at 01:50 IST**, ~2h40m before its stated 04:30 IST expiry: "EXACT PROTECTED TECHNICAL DELIVERY VERIFIED AT `66b962f29`; DOCS PR #2691 PROTECTED-MERGED AT `cdc701afa`; PRODUCT ACCEPTANCE REMAINS OPEN" | **independently read from `origin/campaign-coordination` (not from the restart notice or any Codex self-report doc), 02:16 IST — this corrects the restart notice's "active until 04:30 IST" claim; confirmed this is the topmost/most-recent lease row, no newer conflicting lease exists** |

## ★ FINDING — the delivery gate opened earlier than believed, and the Codex lease is already clear

The restart notice (and the execution package it was based on) assumed the Codex lease
`MADHAV-PURNA-DELIVERY-DATA-PLANE-ALLOWLIST-SUCCESS` was active until 04:30 IST. Reading the
**live** `origin/campaign-coordination` branch (not the slow `main` mirror, and not any Codex
narrative document) shows the actual current lease name is
`...-SUCCESSOR-20260920` and its status is **RELEASED**, timestamped 01:50 IST — before this
conductor run even started. Independently corroborated via Cloud Run + GitHub Actions (see table
above): production is genuinely in sync with `cdc701afa`, all deploy jobs that should have run did,
and the ones that correctly skipped (MCP/sidecar/pipeline for a docs-only PR) skipped for the right
reason. **Practical effect: Wave E's precondition #2 ("no conflicting active lease") is already
satisfied, ~2 hours earlier than planned.** Wave E may proceed once C is complete and this
campaign's own lease is claimed — it does not need to wait for 04:30 IST.

## ★ FINDING — W1 dispatch plan is complete and ready; execution deliberately withheld tonight (credential gate + missing backup precondition)

**Scope is smaller than assumed.** `ka_graha_sancara` needs **no** L1/L2 generation data at all — it
is chart-agnostic, reading only L0 `bg_ephemeris`/live swisseph. `ka_dasha_kala` needs **only L1**
(`ga_positions` → `ga_dashas`); **zero `bo_*`/L2 work is on the critical path** for either E3 or
E4 tonight. Migration 1036's whole L2 bind-receipt apparatus is irrelevant to this wave.

**The real dispatch mechanism** (verified from `jobInvoker.ts`, `main.py`'s argparse, and
`deploy.yml`'s SA binding — not assumed): `POST /api/cockpit/runs` with
`{chart_id, scope:'asset_set', scope_target:'ga_positions,ga_dashas', action:'rebuild',
clear_before:false}`. This inserts `build_runs`/`build_run_assets` rows, then calls
`invokeRunJob()` which runs `brahma-build-pipeline-job --run-id <uuid>` (no other CLI args exist
— scope is frozen into the DB row before dispatch). The job authenticates as `data_plane_builder`
via secret `data-plane-builder-db-url`, satisfying every `session_user` gate in migration 1035.
A CLI alternative exists (`platform/scripts/dispatch_frozen_rebuild.py --asset-id --chart-id
--commit --confirm <ASSET>_FROZEN_REBUILD`) but only accepts one asset at a time and needs its own
write-capable `DATABASE_URL`.

**Rollback rehearsed on a disposable local cluster (not production)**: transaction-abort recovery
is clean (zero orphans, proven). But `rollback_l1_data_plane_generation` is **not** a safety net
for tonight specifically — for a chart's *first* generation there is no prior complete generation
to roll back to, and calling it anyway produces a degenerate self-pointing head. The real safety
net is Postgres atomicity (proven) plus re-dispatching the same or a fresh `run_id` on failure —
never hand-editing `build_runs`.

**Live corroboration, then a correction to keep this precise**: querying the canonical chart's
dashas via the `ganita_dashas_get` MCP tool (`lahiri_chitrapaksha`, `lahiri`, and bare default,
all three) returned `{code: "ga_dashas_replacement_in_progress", restart_required: true, rows: [],
total: 0}` — confirmed via `gcloud run jobs executions list` that this is **not** an active/stuck
builder job (nothing has run since 2026-09-12), so it's a database-state guard, not a live process
to avoid racing. **Correction, from a follow-up live sample across 8 other `kala_*` MCP tools**:
`kala_muhurta_get` and `kala_now_get`'s internal dasha-lord-transit computation both
**successfully** read real MD/AD values (Mercury exalted, Saturn neutral) from the very same
`chart_dashas` table, for the same chart, essentially the same moment. **The guard is applied at
one specific serving layer (`get_dashas`/`ganita_dashas_get`/`kala_dasha_sandhi_get`), not
uniformly on the table** — other code paths that query `chart_dashas` directly bypass it entirely.
So: `chart_dashas` itself is not down; one canonical, provenance-conscious read path honestly
refuses until a completed generation exists, while older/parallel paths haven't been updated to
check for one. W1 would make the *canonical* path consistent with the data that's already there —
a real, worthwhile fix, but not "production reads are broken" as first framed. Corrected here per
this project's own Narration Fidelity doctrine (§N.7) — precision over the more dramatic-sounding
first read.

**Why I am not dispatching it tonight despite having a complete, reviewed plan:**
1. **No authenticated path available to me.** Both `/api/cockpit/runs` and `/api/cockpit/stats`
   require a Firebase-authenticated user session (`getServerUser()`) — unavailable in this
   session. `dispatch_frozen_rebuild.py` needs a write-capable `DATABASE_URL` I have not been
   given and did not self-serve from Secret Manager: reading `amjis-pipeline-db-url` or similar
   myself to manufacture write access would cross from "using an already-authorized secret for
   its intended purpose" into "the campaign inventing its own authority," which the runtime
   doctrine and this campaign's forbidden list are explicit should not happen without a clear
   provisioning decision. I did not attempt it.
2. **A mandatory precondition is unmet.** The execution package's own Wave E preconditions
   require "an operation-specific backup/restore point recorded" before this — the FIRST-EVER
   write under this brand-new generation-tracking system in production deserves that, and I have
   not taken one (I don't hold the credential to take one either).
3. **This is exactly a Native Surrogate-scale decision**, not a routine implementation
   choice: irreversibility is low (atomicity is proven clean) but this is a first-of-its-kind
   write with real product impact if scoped wrong, and the honest, safe answer is to hand the
   native a complete, ready-to-execute plan rather than manufacture credentials to avoid an
   honest stop.

**What unblocks this**: the native (or a session holding proper credentials) either (a) calls
`POST /api/cockpit/runs` with the exact payload above through an authenticated browser/API
session, or (b) provisions a write-capable `DATABASE_URL` for `dispatch_frozen_rebuild.py`
(run twice: `ga_positions` first, then `ga_dashas`, checking `build_run_assets.state` between).
Either path, then verify with the exact SQL in the full research report (§EVENTS.jsonl
`W1_DISPATCH_MECHANISM_CONFIRMED` / this session's transcript) — heads populated, `build_runs.state
='succeeded'`. E3 needs no W1 at all and can run independently the moment a session wants to
spend the effort on its consumer-route value test.

## ★ C2 progress — live-serving snapshot via MCP tools (not a DB row-count baseline, but real signal)

Since raw DB access is blocked (BL-3), sampled 8 `kala_*` MCP tools live against the canonical
chart to see what currently has real serving data vs. empty vs. explicit refusal — a legitimate,
credential-free proxy for part of C2:

| Tool / backing asset(s) | Result |
|---|---|
| `kala_windows_get` (`ka_kalasutra`) | Empty — `empty_reason: "ka_kalasutra may not be built for this chart"` |
| `kala_bundle_get` (`ka_avadhi`/`ka_sangam`/`ka_vighnakara`/`ka_kala_darshana`) | Mixed — `ka_avadhi` has real data (2 dasha-dossier rows); convergence/obstruction empty; `kala_readiness.score: null` |
| `kala_priority_ranking_get` (`ka_tulana`) | Empty — 0 ranked signals |
| `kala_life_arc_get` (`ka_jivana_parva`) | **Real data** — 5 parva rows, `computed_at: 2026-08-13` (still serving from ~5 weeks ago) |
| `kala_dasha_sandhi_get` | Honest empty — same `ga_dashas` gate as above |
| `kala_yoga_activation_get` | Empty (0 activated yogas) — but its own live orphan check found 73,049 MSR references, 0% orphaned, so upstream L2 MSR is substantial and healthy |
| `kala_muhurta_get` (`ka_muhurta_seva`) | **Real data** — 15 dated/scored windows citing live `chart_dashas` MD/AD |
| `kala_now_get` (composite) | Mostly real — `ka_kota_chakra`, `ka_sudarshana_varsha`, `ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_tithi_pravesha` all `"computed"`; `ka_kshetra`'s `field_snapshot_state: "field_not_yet_built"` (never written for this chart); `kala_darshana_confluence` honest-empty |

Not a substitute for real row counts, but a genuine, honest signal: several `ka_*` assets already
serve real, substantive data for the canonical chart today (avadhi, jivana_parva, muhurta_seva,
kota_chakra, sudarshana_varsha, moorti_nirnaya, vedha_gochara, tithi_pravesha) — this campaign's
0/22 headline is about *terminal acceptance* under the current definition, not about whether these
assets compute anything at all. `ka_kshetra`'s field snapshot is confirmed never built for this
chart (matches the handoff's PARK-5 note). `ka_kalasutra`/`ka_tulana`/`ka_sangam`/`ka_vighnakara`/
`ka_kala_darshana` show empty on these particular calls — worth deeper investigation in a future
session, not concluded as "broken" from a handful of calls.

## ★ FINDING — the named `ka_graha_sancara`/`ka_dasha_kala` service modules are not on the live consumer path

Full dossier: `l3_autonomous/dossiers/KA_GRAHA_SANCARA_KA_DASHA_KALA_DOSSIER_v1_0.md`. Grounded,
code-cited research (not inference) found that for **both** E3/E4 target assets, the
orchestrator-registered writer's actual compute engine is exercised only by the self-test/health
probe — the **live, actually-reachable consumer route uses a separate, independent
implementation**:

- `ka_graha_sancara`: `POST /api/compute/ephemeris_at_t` (the router `call_ephemeris_at_t`
  proxies) has its own swisseph integration; it never imports
  `services/ka_graha_sancara/engine.py`. Different ayanamsha vocabularies between the two
  (`{lahiri,raman,kp,krishnamurti,yukteshwar,surya_siddhanta}` vs.
  `{lahiri_chitrapaksha,true_chitra,krishnamurti,raman,surya_siddhanta_classical}`) — they can
  silently drift with no test catching it.
- `ka_dasha_kala`: the TS tool `call_dasha_eligibility` queries `chart_dashas` directly with its
  own simpler grouping logic; it never imports `KaDashaKalaService`. The named service's
  eligibility-band pruning tree-walk is exercised only by the writer's self-test. **Also found: a
  real, unverified risk** — `call_dasha_eligibility`'s default `ayanamsha_id='lahiri'` differs
  from the writer/probe's `'lahiri_chitrapaksha'`; if `chart_dashas` rows are stored under the
  latter, a caller omitting `ayanamsha_id` gets a silent empty result, not an error. Not yet
  verified against live data (was out of the dossier's read-only scope) — **this must be checked
  before E4's value test is trusted**, since it could make the "live" consumer path silently
  broken today regardless of anything Wave E does.

**Consequence for E3/E4's acceptance-test design**: the campaign's own Wave E language already
named the correct target (`call_ephemeris_at_t`, and by implication `call_dasha_eligibility` for
E4) — a test that only exercises the self-test-only Python service or the DB-free proxy probe
would certify something a real caller never touches. The value-test sketches in the dossier
(§1.8, §2.10) are grounded at the correct, actually-live layer and should be used directly when
E3/E4 execute. The divergent-implementation finding itself is a genuine, disclosed architectural
risk — not something to quietly fix as a side effect of an acceptance test, and not something
that blocks tonight's narrower goal (proving the live path's own contract), but worth a named
follow-up for the native.

## ★ FINDING — PR #2607 already squash-merged much of the "stranded" W0 source work

Both D2 and D5 independently found their target content **already on `main`**, landed via
`fa9857f00` ("feat(data-plane): deliver governed L0-L3 source execution (#2607)", 2026-09-16) —
a large squash-merge whose commit list includes the identically-described fixes the handoff
document called "stranded" and "never an ancestor of main". The handoff's stranded-commit claim
was accurate for the exact SHAs it named (`a3e518864` etc. are indeed not ancestors of `main`),
but the **content** of several of those commits was independently re-delivered through a
different, later, already-merged PR — so "not an ancestor" did not mean "not present." **Every
remaining Wave D packet's first real step is now: diff against current `main` before assuming
anything needs salvaging** — this was already in each dispatched packet's instructions
(methodology, not luck), and D1+D3/D4/D6 are expected to make the same check. Do not be surprised
if more Wave D packets close as no-ops; that is a good outcome, not a wasted dispatch — it means
less risk, not less progress.

## Active leases held by this campaign

None yet — claim one on `origin/campaign-coordination` before any Wave E production mutation.

## Open blockers

| Id | Blocker | Owner | Next action |
|---|---|---|---|
| BL-1 | `WATCHDOG_SECRET` literal in tagged zero-traffic revision `amjis-web-02826-huf` | **human (native)** | rotate/revoke + audit tag exposure; neither campaign may act |
| BL-2 | ~~Codex lease active until 04:30 IST~~ **RESOLVED — lease independently confirmed RELEASED at 01:50 IST** | — | none; re-check `origin/campaign-coordination` immediately before claiming L3's own lease, per standing doctrine |
| BL-3 (new) | No documented read-only DB role can read `public` schema (`kala_*`, generation-head tables) — `retrieval_census_ro` is scoped to `information_schema`/`pg_catalog` only. Confirmed the legitimate app-level route (`GET /api/cockpit/stats`, which reads `asset_registry.count_sql`/`asset_throughput` — the actual §N.4 "cockpit truth" mechanism) requires an authenticated Firebase user session with chart read-permission; no such session is available to this conductor without native-provided browser/API credentials. | native (optional) | either authorize a scoped read grant for verification, provide a session/token for `/api/cockpit/stats`, or accept orchestrator/CI-reported state as the legitimate evidence source (recommended — matches the role-separation doctrine already in force) |

## Budget consumed

| Resource | Used | Ceiling |
|---|---|---|
| Subagent dispatches | 0 | 80 |
| Worktrees | 1 | 12 |
| PRs opened | 0 (B1 PR next) | 15 |
| Merges to main | 0 | 12 |
| Deploy dispatches | 0 | 4 |
| Production mutations | 0 | 2 |
| Surrogate invocations | 0 | 10 |
