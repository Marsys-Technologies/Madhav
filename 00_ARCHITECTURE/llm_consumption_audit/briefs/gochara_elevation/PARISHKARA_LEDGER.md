# PARIṢKĀRA LEDGER — remediation campaign for MASTER_REMEDIATION_REGISTER_v2_0

CAMPAIGN-STATUS: OPEN
plan_of_record: MASTER_REMEDIATION_REGISTER_v2_0.md (v2.1, this directory)
branch: parishkara/campaign (home) · parishkara/integration (lanes → main via gates)
proxy_port: 5434 (own; 5433 is SAMPŪRTI's — never touch)
marker_duty: post W6-COMPLETE to campaign-coordination §6 after MR-01..08,10,13,14,15,24 gates pass

## MR STATUS

| MR | Item (short) | Status | Evidence |
|---|---|---|---|
| MR-01 | Schema parity (8 cols) → tools un-500 | BUILDING | agent a07974c83ba407711 · worktree pk-mr01 · migration 564 claimed |
| MR-02 | Coverage gate authority-aware | BUILDING | combined with MR-01+05 in pk-mr01 |
| MR-03 | Truthful '3.0' citation | QUEUED | after MR-01+02+05 spine lands |
| MR-04 | Valence vocabulary contract | QUEUED | after MR-01+02+05 spine lands |
| MR-05 | Corrected deprecation migration (FK-safe) | BUILDING | combined with MR-01+02 in pk-mr01; 563 FK root cause: asset_throughput 1 row blocks DELETE |
| MR-06 | Seed/542 durability + gen-3.0 protection | QUEUED | after MR-05 |
| MR-07 | Cockpit truth (count_sql) | QUEUED | after MR-01+02+05 |
| MR-08 | Flip/rollback/probe tooling | QUEUED | after MR-30 scripts committed |
| MR-09 | Naming coherence + health + pointers | BUILDING | agent ab40b67cf15832352 · worktree pk-mr09 |
| MR-10 | Promote 54 point rows | QUEUED | needs MR-01 cols first |
| MR-11 | Resolution bar + hierarchy windows | QUEUED (ADJUDICATOR bar ruling first) | — |
| MR-12 | Chain rows (marriage first) | QUEUED | — |
| MR-13 | Honest valence + calibration tier restamp | QUEUED | — |
| MR-14 | term_breakdown → rebuild → refit | QUEUED | needs MR-01 cols |
| MR-15 | AV gating contributes (bhava_num) | QUEUED | — |
| MR-16 | 27-class expansion (POST-MARKER only) | QUEUED | — |
| MR-17 | ka_kshetra seam (SAMPŪRTI's — track only) | EXTERNAL | coordination file |
| MR-18 | Validators generation stance | BUILDING | agent a6d113847284979ce · worktree pk-mr18 · TDD red (7 failing tests committed, fixing now) |
| MR-19 | Ablations → re-adjudicated admissions | QUEUED | — |
| MR-20 | Real no-loss gate (35,620 windows) | QUEUED | — |
| MR-21 | Quantitative evidence chain published | QUEUED | — |
| MR-22 | Suppression detector + count | QUEUED | — |
| MR-23 | Remaining unrun acceptance artifacts | QUEUED | — |
| MR-24 | Product-level E2E battery (standing) | QUEUED | — |
| MR-25 | Citations resolve in serving | BUILDING | dispatching this session |
| MR-26 | Honest amended close report | QUEUED | — |
| MR-27 | Prod-sync + deploy discipline | QUEUED | — |
| MR-28 | Five retro adjudications | QUEUED | — |
| MR-29 | Ledger reconciliation + re-close verdict (LAST) | QUEUED | — |
| MR-30 | Hygiene (w61 scripts FIRST, worktrees, docstrings) | BUILDING | agent a9391cd8e146c20e8 · worktree pk-mr30 |
| MR-31 | SAMPŪRTI branch merge (theirs — track only) | EXTERNAL | coordination file |
| MR-32 | DR-13 → Stage C seeding | QUEUED | — |
| MR-33 | CRPS honest-deferred (verify L5 wiring, record trigger) | QUEUED | — |
| MR-34 | Third-chart scope statement | BUILDING | re-dispatching (prior task not found) |
| MR-35 | Serving-outage smoke probe (CI) | BUILDING | agent a688496f098af7485 · worktree pk-mr35 |
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
