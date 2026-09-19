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
| Governing docs merged to main (B1) | 🟡 committed on integration branch, PR pending |
| DP-SD-021 authored (B2) | ✅ strategic ledger §13 |
| Governance surfaces refreshed (B3, main-branch part) | ✅ CLAUDE.md §C.5+§E, CURRENT_STATE §2, CLAUDECODE_BRIEF.md — coordination-branch part pending |
| Deployment re-verified independently (C1) | ✅ **gate is OPEN — see finding below, corrects the restart notice** |
| 22-asset baseline (C2) | 🟡 partially blocked — see finding |
| W1 function contract read (C3) | 🟡 in progress |
| Salvage packets landed (D1–D6) | 0 / 6 |
| Branch triage record (D7) | ⬜ |
| Field dossiers | 0 / 22 |

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
| D1+D3 Kshetra P0 + DHARA correction | subagent `ac646ccb3` | own worktree | TBD | **DISPATCHED 02:40 IST** | — | awaiting report |
| D2 Bhavishya P0 | subagent `a0e4039b2` | own worktree | TBD | **DISPATCHED 02:40 IST** | — | awaiting report |
| D4 Yojaka preservation | subagent `a9801fa14` | own worktree | TBD | **DISPATCHED 02:40 IST** | — | awaiting report; cautioned re: 118-commit-ahead source, forensic extraction only |
| D5 W0 field register | subagent `a41f66de3` | own worktree | — | **DONE — NO-OP, already satisfied** | The 800-line register already exists on `main` (landed via PR #2607, `fa9857f00`, 2026-09-16), and main's version is a *corrected* revision (35 row-level type/nullability fixes) vs. the source branch's stale 2026-09-15 draft — landing the branch version would regress main. No PR opened; correctly declined rather than manufacturing one. | — |
| D6 U05 registry | subagent `abbdfc3eb` | own worktree | TBD | **DISPATCHED 02:40 IST** | — | awaiting report |
| D7 branch triage | conductor (run 2) | integration | `codex/madhav-l3-claude-code` | **DONE** | `MADHAV_L3_BRANCH_TRIAGE_DISPOSITION_v1_0.md` @ `2955e2f13`; PR #2655 confirmed already closed | — |
| W1-RESEARCH (informs E1/E2) | subagent `acba0c5c8` (Opus) | read-only | — | **DISPATCHED 02:40 IST** | — | read-only research + disposable-DB rollback rehearsal; must NOT mutate production; report becomes E1/E2's dispatch plan |
| E1 W1 L1 generation | conductor (pending W1-RESEARCH) | integration | — | BLOCKED_ON W1-RESEARCH | — | dispatch real `brahma-build-pipeline-job`, not ad hoc SQL — confirmed via migration 1035 read (`open_l1_data_plane_generation` hard-gates on `session_user='data_plane_builder'`) |
| E2 W1 L2 generation | conductor | integration | — | BLOCKED_ON E1 | — | — |
| E3 ka_graha_sancara terminal | conductor | own worktree | — | BLOCKED_ON W1-RESEARCH | — | service proof (no row build); no conflicting lease (see finding) |
| E4 ka_dasha_kala terminal | conductor | own worktree | — | BLOCKED_ON W1-RESEARCH | — | service proof (no row build); reads L1 `ga_dashas` per migration 1035 `l1_data_plane_dasha_snapshots` |

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
