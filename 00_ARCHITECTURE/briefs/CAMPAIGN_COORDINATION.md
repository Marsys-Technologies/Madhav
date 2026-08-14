---
artifact: CAMPAIGN_COORDINATION.md
status: LIVE — binding on all concurrent autonomous campaigns in this repo
created: 2026-08-10 (SAMPŪRTI conductor, native-directed)
write_rule: >
  Any campaign conductor MAY append entries attributed to its own campaign.
  No campaign ever rewrites, deletes, or "cleans up" another campaign's entries,
  files, worktrees, or branches — flag anomalies in §6 LOG instead.
read_rule: >
  Every conductor reads this file at session open AND re-checks it (git fetch +
  read from origin/main) immediately before any gate merge, production deploy,
  or production orchestrator build/rebuild.
---

# CROSS-CAMPAIGN COORDINATION — SAMPŪRTI ↔ GOCHARA-UTKARṢA

Native directive (2026-08-10): two fully-autonomous campaigns run concurrently on
this repo — SAMPŪRTI (gap remediation, `sampurti/*` branches, ledger
`00_ARCHITECTURE/briefs/sampurti/SAMPURTI_STATE.md`) and GOCHARA-UTKARṢA (gochara
elevation, `utkarsha/campaign` + `gochara3/*` branches, plan
`00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation/`). Worktrees
isolate files; this file coordinates the five surfaces worktrees cannot isolate:
main merges/deploys, the production DB, migration numbering, the protected sweep
corpus schema, and overlapping asset territory.

## 1. DEPLOY/REBUILD LEASE (prime rule)

Only ONE campaign may (a) deploy to production or (b) run a production orchestrator
build/rebuild at any moment. Before either action: append a lease row below, commit,
push to main's coordination branch or your own integration branch AND verify no
ACTIVE lease from the other campaign exists on origin/main or the other campaign's
integration branch. Mark RELEASED when done. A lease past its stated expiry is DEAD:
the other campaign may proceed after appending an OVERRIDE note citing the expiry.

Yield policy (native-adopted 2026-08-10, silence-adopts): under contention the
campaign NOT mid-rebuild yields; if both are idle, SAMPŪRTI yields during UTKARṢA's
cutover wave (its W6), UTKARṢA yields otherwise.

| # | campaign | purpose | started (IST) | expiry (IST) | status |
|---|---|---|---|---|---|
| L-3 | SAMPŪRTI | P-G1 ka_kshetra rebuild (fetch_orb_deg L1b fix deployed) | 08:34 IST | 10:00 IST | ACTIVE |

## 2. MIGRATION NUMBER CLAIMS (claim-at-PR-open; renumber-on-collision stands)

| number | campaign | file | status |
|---|---|---|---|
| 553–555 | SAMPŪRTI | Wave-0 migrations | MERGED to main (#1138) |
| 556 | UTKARṢA | 556_gochara_generation_schema.sql | CLAIMED (gochara3/w03, unmerged) |
| 557+ | — | next free; claim here before use | — |

## 3. TERRITORY MAP (edit-ownership during the concurrency window)

- **UTKARṢA edits:** `ka_gochara_sweep`, `gochara_v3/*`, `gochara_grammar/*`, sweep
  protection mechanism + guard tests, its lane changes to `ka_kota_chakra` /
  `ka_vedha_gochara` writers, the `kala_gochara_authority` generation seam.
- **SAMPŪRTI edits:** `ka_kshetra`/field chain, `bodha_*`/`mi_*`/`ph_*` writers,
  governance surfaces (CURRENT_STATE / SESSION_LOG / census / CLAUDE.md), facade +
  assess + serving lanes, LEL resolver.
- Either campaign may **RUN** the other's writers inside a full-DAG rebuild but never
  edits them; rebuild/acceptance evidence must **pin the commit SHA** the rebuild ran
  at, so later merges by the other campaign cannot silently invalidate it.
- Neither campaign deletes or moves the other's files, worktrees, or branches — even
  apparently orphaned ones. Flag in §6 LOG instead.

## 4. STANDING RULINGS / PROPOSALS

- **R-COORD-1 (PROPOSED by SAMPŪRTI NATIVE-PRATINIDHI — awaiting UTKARṢA ADJUDICATOR
  counter-signature):** SAMPŪRTI's Wave-2 G11 retirement of gochara-family legacy
  temporal surfaces is DEFERRED until UTKARṢA's authority-seam cutover completes;
  those retirements then execute jointly (both delegates sign, recorded in both
  ledgers, PA-7 capability-parity audits still mandatory). SAMPŪRTI's non-gochara
  retirements proceed on its own schedule.
- **R-COORD-2 (SAMPŪRTI standing note):** after migration 556 merges, SAMPŪRTI
  re-derives its sweep-corpus detectors generation-filtered before citing the
  606/606 + 16,297/19,323 baselines.

## 5. ADOPTION STATUS

| campaign | adopted | by | when |
|---|---|---|---|
| SAMPŪRTI | YES — binding, recorded in SAMPURTI_STATE.md | conductor (native-directed) | 2026-08-10 |
| UTKARṢA | PENDING — native will direct its conductor to adopt + counter-sign R-COORD-1 | — | — |

## 6. LOG

- 2026-08-10 ~05:36 IST (pre-file, recorded retroactively): a non-SAMPŪRTI session
  deleted an "orphaned SAMPURTI_STATE.md" from the primary checkout. Outcome verified
  benign (tracked copy on main + live ledger on sampurti/integration both intact).
  §3's no-cross-campaign-deletion rule exists to prevent recurrence.
- 2026-08-10: file created (SAMPŪRTI conductor); native directed adoption in both
  campaigns.

Δ3 20:13Z Aug 14 session-39 (false-positive relaunch #8+ — supervisor pattern (2) matches desk directive heading `### DESK DIRECTIVE — ... DO NOT POST FIELD-INTEGRATED`; none of the exclusion words present in that heading line; genuine sentinel = ██ MARKER-POSTED: FIELD-INTEGRATED ██) — liveness CLEAN (PID 38187=shell, stored 33518=supervisor bash run_dh_d3.sh alive/not-peer-conductor, pgrep PEERS=NONE, sole conductor); hygiene CLEAN (no RUNNING Cloud Run; lj98k/kk2m2/cl4dm/xt79g/kjvmn all Completed, last 19:33Z Aug 14); FIELD-INTEGRATED NOT POSTED; FM-09 reconcile: main HEAD 15ace43df unchanged; Δ1 integration 5f674a89c unchanged; Δ1 DOWN (SM-R-11 governing); F1-F5 NONE open (open PRs: #1189, #1180, #899, #898, #446); R1 MCP PROOF PASS×20 (20:13Z: 27 classes, 270 substeps ka_gochara_v3_century_materialize, backing_data_reachable=true, no S4-05); all Δ3 lanes complete (R1 MERGED+PROOF PASS×20; R2 DEPLOYED proof-pending; R3 DONE; R4 READY-ON-SIGNAL; R5 MERGED+DEPLOYED); ending cleanly — genuine FIELD-INTEGRATED required for R2+R4+SESSION-DONE-Δ3.
