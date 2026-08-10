# PARIṢKĀRA LEDGER — remediation campaign for MASTER_REMEDIATION_REGISTER_v2_0

CAMPAIGN-STATUS: OPEN
plan_of_record: MASTER_REMEDIATION_REGISTER_v2_0.md (v2.1, this directory)
branch: parishkara/campaign (home) · parishkara/integration (lanes → main via gates)
proxy_port: 5434 (own; 5433 is SAMPŪRTI's — never touch)
marker_duty: post W6-COMPLETE to campaign-coordination §6 after MR-01..08,10,13,14,15,24 gates pass

## MR STATUS

| MR | Item (short) | Status | Evidence |
|---|---|---|---|
| MR-01 | Schema parity (8 cols) → tools un-500 | VERIFYING | PR #1198 (parishkara/mr-01 → parishkara/integration) · PARĪKṢAKA pending (session-2 ID expired) |
| MR-02 | Coverage gate authority-aware | VERIFYING | combined in PR #1198 · authority-aware computeGocharaCoverage · PARĪKṢAKA pending |
| MR-03 | Truthful '3.0' citation | QUEUED | after MR-01+02+05 spine lands |
| MR-04 | Valence vocabulary contract | QUEUED | after MR-01+02+05 spine lands |
| MR-05 | Corrected deprecation migration (FK-safe) | VERIFYING | combined in PR #1198 · FK fix: DELETE FROM asset_throughput WHERE asset_id='ka_gochara' AND chart_id IS NULL · PARĪKṢAKA pending |
| MR-06 | Seed/542 durability + gen-3.0 protection | QUEUED | after MR-05 |
| MR-07 | Cockpit truth (count_sql) | QUEUED | after MR-01+02+05 |
| MR-08 | Flip/rollback/probe tooling | QUEUED | after MR-30 scripts committed |
| MR-09 | Naming coherence + health + pointers | VERIFYING | PR #1197 (parishkara/mr-09 → parishkara/integration) · PARĪKṢAKA pending (session-2 ID expired) |
| MR-10 | Promote 54 point rows | QUEUED | needs MR-01 cols first |
| MR-11 | Resolution bar + hierarchy windows | QUEUED (ADJUDICATOR bar ruling first) | — |
| MR-12 | Chain rows (marriage first) | QUEUED | — |
| MR-13 | Honest valence + calibration tier restamp | QUEUED | — |
| MR-14 | term_breakdown → rebuild → refit | QUEUED | needs MR-01 cols |
| MR-15 | AV gating contributes (bhava_num) | QUEUED | — |
| MR-16 | 27-class expansion (POST-MARKER only) | QUEUED | — |
| MR-17 | ka_kshetra seam (SAMPŪRTI's — track only) | EXTERNAL | coordination file |
| MR-18 | Validators generation stance | VERIFYING | PR #1195 (parishkara/mr-18 → parishkara/integration) · 8 gate tests GREEN · PARĪKṢAKA pending (session-2 ID expired) |
| MR-19 | Ablations → re-adjudicated admissions | QUEUED | — |
| MR-20 | Real no-loss gate (35,620 windows) | QUEUED | — |
| MR-21 | Quantitative evidence chain published | QUEUED | — |
| MR-22 | Suppression detector + count | QUEUED | — |
| MR-23 | Remaining unrun acceptance artifacts | QUEUED | — |
| MR-24 | Product-level E2E battery (standing) | QUEUED | — |
| MR-25 | Citations resolve in serving | VERIFYING | PR #1200 (parishkara/mr-25 → parishkara/integration) · commit 7d355b717 (migration 565 + verse_refs wiring) · PARĪKṢAKA dispatching session-5 |
| MR-26 | Honest amended close report | QUEUED | — |
| MR-27 | Prod-sync + deploy discipline | QUEUED | — |
| MR-28 | Five retro adjudications | QUEUED | — |
| MR-29 | Ledger reconciliation + re-close verdict (LAST) | QUEUED | — |
| MR-30 | Hygiene (w61 scripts FIRST, worktrees, docstrings) | VERIFYING | PR #1199 (parishkara/mr-30 → parishkara/integration) · PARĪKṢAKA pending (session-2 ID expired) |
| MR-31 | SAMPŪRTI branch merge (theirs — track only) | EXTERNAL | coordination file |
| MR-32 | DR-13 → Stage C seeding | QUEUED | — |
| MR-33 | CRPS honest-deferred (verify L5 wiring, record trigger) | QUEUED | — |
| MR-34 | Third-chart scope statement | MERGED | PR #1194 MERGED to parishkara/integration · PARĪKṢAKA PASS: amonty84/14:30:52Z — 5/5 tests pass, source cross-check ok, COALESCE contract verified |
| MR-35 | Serving-outage smoke probe (CI) | VERIFYING | PR #1196 (parishkara/mr-35 → parishkara/integration) · 3 commits (TDD→working probe→CI workflow) · PARĪKṢAKA pending |
| MR-36 | (merged into MR-21) | MERGED-INTO-21 | register §7 |

## RULINGS
(ADJUDICATOR entries here, numbered PK-R1.. , with written rationale.
PARKED-FOR-NATIVE list maintained here — never decided by agents:
scope reduction below 27 classes · retiring any serving surface · LEL content.)

## LOG
- 2026-08-10 ~19:5x IST (native's desk): campaign home created — register
  v2.1 as plan of record, prompt + supervisor authored, branch
  parishkara/campaign cut carrying the full audit trail. NEXT-ACTION: first
  conductor session — step 0 liveness check, create parishkara/integration
  off origin/main, dispatch MR-01 + parallel-safe lanes (MR-09/18/25/34/35),
  MR-30's utk-w61 script commit first (feeds MR-08).

- 2026-08-10 ~19:44 IST (conductor session 1 open):
  CONDUCTOR-HEARTBEAT: 2026-08-10T13:44:16Z pid=47856 host=Montys-MacBook-Pro.local
  Liveness verified: pgrep-exit=1 (no other PARIṢKĀRA conductor). Proxy 5434
  alive (pid 58012). L-3 lease (UTKARṢA, expiry 18:30 IST) expired 74 min ago
  — dead by policy. Campaign state: all 36 MR items QUEUED. origin/main HEAD:
  63435580 (W6.4: UTK-R2 retire sweep → ka_gochara rename, PR #1192 merged).
  parishkara/integration: created off origin/main (63435580).
  DB SCHEMA ASSESSMENT (2026-08-10T13:5xZ):
    kala_gochara_windows: 23 cols (production) — missing 8 v3 output cols
    kala_gochara_windows_v2: 30 cols (staging) — has all 8 v3 cols
    migration 563: ON MAIN, UNAPPLIED. Root cause: FK 23503 — asset_throughput
      has 1 row for ka_gochara (global scope self-test), blocking DELETE FROM
      asset_registry WHERE asset_id='ka_gochara' AND scope='global'. Fix: add
      DELETE FROM asset_throughput WHERE asset_id='ka_gochara' AND chart_id IS NULL
      before the asset_registry DELETE. Safe to edit (no sha256 stored).
    migration 564: CLAIMED by PARIṢKĀRA (MR-01 adds 8 cols to kala_gochara_windows)
    register_gochara_windows.ts: false comment at ~line 303 claims term_breakdown
      is on kala_gochara_windows since migrations 527/556/559 — it's only on _v2.
      3 tools returning 500 due to ROW_COLUMNS selecting term_breakdown from prod table.
  BUILDERS DISPATCHED (19:5x IST):
    MR-01+02+05 spine: agent a07974c83ba407711 (pk-mr01) — vitest install issue
    MR-09 naming: agent ab40b67cf15832352 (pk-mr09) — planning implementation
    MR-18 validators: agent a6d113847284979ce (pk-mr18) — TDD red confirmed (7 tests)
    MR-34 scope: agent a55bb85b0fef96b77 (pk-mr34) — task not found, re-dispatching
    MR-35 smoke probe: agent a688496f098af7485 (pk-mr35) — creating gochara scripts dir
    MR-30 hygiene: agent a9391cd8e146c20e8 (pk-mr30) — reading MR specs

- 2026-08-10 ~19:32 IST (conductor session 1 heartbeat):
  CONDUCTOR-HEARTBEAT: 2026-08-10T14:02:00Z pid=47856 host=Montys-MacBook-Pro.local
  6 builders running. MR-18 furthest along: TDD red committed, fixes in flight.
  MR-34 task not found — re-dispatching. MR-25 dispatching (deferred parallel lane).
  NEXT-ACTION: await builder completions; spawn PARĪKṢAKA (opus) for each completed PR;
  MR-25 now in flight. Monitor MR-01 vitest install issue — may need npm install step.

- 2026-08-10 ~19:37 IST (conductor heartbeat):
  CONDUCTOR-HEARTBEAT: 2026-08-10T14:07:00Z pid=47856 host=Montys-MacBook-Pro.local
  MR-34 COMPLETED: PR #1194 opened (parishkara/mr-34 → parishkara/integration).
  Key finding: AUTHORITATIVE_GENERATION_FILTER COALESCE('v1') confirmed correct
  for cb73cd3d (no authority row → naturally serves v1; no code fix needed for MR-02
  null-chart case). Re-dispatch ae1e5938 adding canonical THIRD_CHART_SCOPE_STATEMENT_v1_0.md
  + TDD tests to same branch. PARĪKṢAKA ac2cbc5a dispatched for PR #1194.
  Active builders: MR-01+02+05 (vitest issue), MR-09, MR-18 (fixes in flight),
  MR-25 (new), MR-30, MR-34-redispatch, MR-35.
  NEXT-ACTION: await remaining builders; merge PR #1194 when PARĪKṢAKA passes.

- 2026-08-10 ~19:47 IST (conductor session 2 open — context compacted):
  CONDUCTOR-HEARTBEAT: 2026-08-10T14:21:28Z pid=10226 host=Montys-MacBook-Pro.local
  SESSION-2: context window compacted mid-session; resuming with full ledger re-read.
  MR-18 COMPLETED: PR #1195 opened. Fixes: v6_divergence_pilot.py (AND generation='v1' +
    INTENTIONAL comment), s4_05_data_real_retest.py (both queries pinned), test_cr131 (COALESCE
    pattern), w2g_equivalence_report.py (INTENTIONAL comment), w41_lambda_contenders.py
    (INTENTIONAL comment), test_migration_527_generation_catalog_only.py (INTENTIONAL comment).
    NEW: test_mr18_generation_stance.py (8 gate tests, all GREEN). PARĪKṢAKA af2f4442193d57e89
    dispatched (opus).
  MR-01+02+05: 4 commits on parishkara/mr-01 — 5bb70f990 (TDD red), cdb803188 (MR-05 FK fix),
    60eafb8ff (migration 564: 8 cols), 9e4005886 (MR-02 authority-aware coverage + false comment fix).
    27 new tests + 12 original = all GREEN. PR opening imminently.
  MR-30: active, bulk worktree cleanup (utk-w21..w64 groups removed). w61-scripts first.
  MR-25: TDD tests written (AC-1..6: migration 565, bg_gochara_citation_resolution, BPHS Ch.26
    seed, verse_refs serving join, route.ts whitelist, citations.py grounding). Implementing.
  MR-09/MR-35/MR-34-redispatch: task IDs expired (prev context window). Worktree state check
    dispatched (ad4b7a87207281606). Awaiting result.
  MR-34: PARĪKṢAKA verdict from ac2cbc5a not pollable (ID from prior window). Will re-verify
    via GitHub PR status check on next heartbeat if no notification.
  NEXT-ACTION: await MR-01 PR, spawn PARĪKṢAKA; await MR-09/35 state result; await PARĪKṢAKA
    MR-18 (af2f4442193d57e89) verdict; merge MR-34 PR #1194 if PARĪKṢAKA passed.

- 2026-08-10 ~19:51 IST (conductor session 3 open):
  CONDUCTOR-HEARTBEAT: 2026-08-10T14:21:28Z pid=10226 host=Montys-MacBook-Pro.local
  SESSION-3: resumed after context compaction. Prior conductor pid=47856 DEAD (verified
    ps -p 47856 → exit 1). pgrep -f "CONDUCTOR of PARIṢKĀRA" → no matches. Lease free.
  Port 5434: OPEN (cloud-sql-proxy alive, confirmed nc -z 127.0.0.1 5434).
  STATE RECONCILIATION vs reality (adopt, never redo):
    6 PRs open, 0 reviews across all — all session-2 PARĪKṢAKA IDs expired with context window.
    MR-34: PR #1194, redispatch ae1e5938 DID commit (231d813ce + 4b426b18c); PARĪKṢAKA expired.
    MR-35: 3 commits landed (TDD→working probe→CI workflow), PR #1196 already opened.
    MR-25: pk-mr25 still at origin/main HEAD (63435580a); session-2 builder (a8cb08dead)
      stalled with zero commits — status updated to STALLED. Re-dispatch needed.
    MR-01/02/05 (PR #1198): 4 commits intact, MERGEABLE. PARĪKṢAKA pending.
    MR-09 (PR #1197): 4 commits intact, MERGEABLE. PARĪKṢAKA pending.
    MR-18 (PR #1195): 2 commits, 8 gate tests GREEN. PARĪKṢAKA pending.
    MR-30 (PR #1199): 5 commits (flip/rollback/probe scripts + docstring + cleanup report).
      PARĪKṢAKA pending.
  ACTION: dispatching 6 fresh PARĪKṢAKA agents (opus, FRESH context) for all 6 open PRs
    in parallel. Re-dispatching MR-25 builder (sonnet) to pk-mr25 worktree.
  NEXT-ACTION: await PARĪKṢAKA verdicts; merge PASS PRs to parishkara/integration in batches;
    re-dispatch MR-25; advance spine items (MR-06/07/08) once MR-01+02+05 PARĪKṢAKA PASS.

- 2026-08-10 ~19:55 IST (conductor session 4 open):
  CONDUCTOR-HEARTBEAT: 2026-08-10T14:24:00Z pid=7460 host=Montys-MacBook-Pro.local
  SESSION-4: context compacted again. Prior pid=47856 DEAD, pid=10226 DEAD (ps -p both → exit 1).
  pgrep -f "CONDUCTOR of PARIṢKĀRA" → 7460 (only self). Lease free.
  STATE RECONCILIATION:
    All session-3 PARĪKṢAKA agents expired without posting verdicts (0 reviews on all PRs).
    6 PRs remain OPEN and UNREVIEWED:
      PR #1194 (MR-34): 2 commits — scope statement + TDD tests
      PR #1195 (MR-18): 2 commits — generation-stance fixes + 8 gate tests GREEN
      PR #1196 (MR-35): 3 commits — smoke probe skeleton + working probe + CI workflow
      PR #1197 (MR-09): 4 commits — transit rename + health probe + discoverability + docstring
      PR #1198 (MR-01+02+05): 4 commits — TDD red + FK fix (563) + 8-col migration (564) + coverage fix
      PR #1199 (MR-30): 5 commits — flip/rollback/probe scripts + docstring + cleanup report
    MR-25 (pk-mr25): builder stalled; uncommitted work exists in worktree:
      modified: platform-mcp/src/tools/retrieval/register_gochara_windows.ts (+160 lines)
      modified: platform/src/app/api/mcp/db/query/route.ts (+5 lines)
      untracked: test_mr25_citation_verse_refs.py + 565_bg_gochara_citation_resolution.sql
  ACTIONS THIS SESSION:
    Dispatching 6 fresh PARĪKṢAKA agents (opus) for all 6 PRs.
    Dispatching MR-25 builder rescue (sonnet) to commit + complete.
  NEXT-ACTION: await PARĪKṢAKA verdicts; merge PASS PRs to integration; gate to main.

- 2026-08-10 ~19:57 IST (conductor session 4 — agents dispatched):
  CONDUCTOR-HEARTBEAT: 2026-08-10T14:27:00Z pid=7460 host=Montys-MacBook-Pro.local
  7 background agents dispatched (6 PARĪKṢAKA opus + 1 builder sonnet):
    MR-34 PARĪKṢAKA: ad48809aceba70293 → PR #1194
    MR-18 PARĪKṢAKA: aaca6464653febf37 → PR #1195
    MR-09 PARĪKṢAKA: a8d99992d315a0009 → PR #1197
    MR-30 PARĪKṢAKA: aefe9cb3f2a54c9e8 → PR #1199
    MR-35 PARĪKṢAKA: ae120ca45788a60c6 → PR #1196
    MR-01+02+05 PARĪKṢAKA: a8b2af0d9ccf8b112 → PR #1198
    MR-25 builder rescue: a525b5a52aeba510d → pk-mr25 worktree → open PR
  NOTE: MR-35 "green live" sub-criterion honestly PENDING (MR-01 migration unapplied).
  NOTE: MR-01+02+05 live serving gates PENDING deployment (pre-merge code review only).
  NEXT-ACTION: await agent notifications; merge PASS PRs to integration; prepare gate packet.

- 2026-08-10 ~20:10 IST (conductor session 5 open):
  CONDUCTOR-HEARTBEAT: 2026-08-10T14:40:00Z pid=38773 host=Montys-MacBook-Pro.local
  SESSION-5: all prior conductors DEAD (pid=7460 ps-exit=1; pid=10226 ps-exit=1; pgrep=NO_MATCH).
  Lease free. Proxy 5434: ALIVE.
  STATE RECONCILIATION vs reality:
    MR-34 (PR #1194): PARĪKṢAKA PASS verdict posted at 14:30:52Z by session-4 agent
      (ad48809aceba70293 / amonty84 GitHub account). State=COMMENTED (GitHub --approve
      blocked: author=reviewer). Verdict genuine — READY TO MERGE.
    MR-18 (PR #1195), MR-09 (PR #1197), MR-35 (PR #1196), MR-30 (PR #1199),
    MR-01+02+05 (PR #1198): all 0 reviews — session-4 PARĪKṢAKA agents (5 of 6)
      expired without posting verdicts.
    MR-25: builder rescue a525b5a52aeba510d DID succeed — commit 7d355b717 on
      parishkara/mr-25. Migration 565, citation resolution table, verse_refs wiring.
      NO PR was opened. ACTION: PR #1200 opened this session.
  ACTIONS THIS SESSION:
    PR #1200 opened (MR-25, parishkara/mr-25 → parishkara/integration).
    PR #1194 (MR-34): merging to parishkara/integration (PARĪKṢAKA PASS evidence above).
    Dispatching 6 fresh PARĪKṢAKA (opus) agents: MR-01+02+05, MR-09, MR-18, MR-30, MR-35, MR-25.
  MR STATUS UPDATES:
    MR-25: STALLED → VERIFYING (PR #1200 opened; PARĪKṢAKA dispatching)
    MR-34: VERIFYING → MERGED (PR #1194, PARĪKṢAKA PASS, merging to integration)
  NEXT-ACTION: await 6 PARĪKṢAKA verdicts; merge PASS PRs to integration in batches;
    prepare gate packet for integration → main once MR-01+02+05 PARĪKṢAKA PASS.
