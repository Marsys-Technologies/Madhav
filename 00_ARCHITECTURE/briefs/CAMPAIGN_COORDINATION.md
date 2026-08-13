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
| L-3 | SAMPŪRTI | P-G1 ka_kshetra rebuild (fetch_orb_deg L1b fix deployed) | 08:34 IST | 10:00 IST | RELEASED (expired 10:00 IST; A3 mq4b8 ran 03:25–05:29 UTC, 85/534 substeps, run failed; lease void) |
| L-4 | SAMPŪRTI | A3 checkpoint-resume: ka_kshetra redispatch from substep 85/534 | 11:10 IST 2026-08-13 | 18:00 IST 2026-08-13 | ACTIVE (RENEWED 11:47 IST — build ETA ~16:00-16:30 IST; exec sd2ph RUNNING, marriage:3 @ 06:07 UTC, fingerprint-divergence re-run of stage5) |

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

### 2026-08-13 16:23 IST — SAMPŪRTI-Δ1 R18 SESSION OPEN

**SAMPŪRTI-Δ1 (DHĀRĀ) SESSION OPEN** — CONDUCTOR of SAMPŪRTI-Δ1 (three-stream architecture, supersedes α identity).

Step 0 complete: Liveness CLEAR (sole Δ1 conductor). Hygiene: exec szwkw zombie (build_run=failed at 10:10 UTC, stop_requested_at=10:06 UTC; Cloud Run exec container still alive — monitoring for exit; advisory lock untouched per n1). Native rulings in force: n1 DHĀRĀ-first, n2 DB persistence, n3 1024 replicates. Proceeding to S1 DHĀRĀ DESIGN DOC.

### 2026-08-13 11:38 IST (UTC) — DHARA-SPEC-FROZEN

**DHARA-SPEC-FROZEN** — SAMPŪRTI-Δ1 conductor posts this marker.

DHARA_DESIGN_v1_0.md has passed S1 (blind spec commitment, 1,341 lines) and S2 (adversarial design review). The spec is now FROZEN at v1.1 for implementation.

**S2 adversarial review summary (Opus VERIFIER, 2026-08-13T11:13–11:21 UTC):**
- F-01 CRITICAL: Null-shift grid bug (`range(1,R+1)` → `range(1,R)`); pre-existing in 256-replicate engine; corrected in spec
- F-02 CRITICAL: Suppression detection always true (`suppression_term != 0.0` → `!= 1.0`); corrected
- F-03 CRITICAL: Error bound h^2 cancels (bound is amplitude-dependent, not width-dependent); corrected
- F-04 MAJOR: Pin matrix stage 0-1 split (stage 1 depends on stage 3 output); corrected
- F-05 MAJOR: E1 tolerance caveat for small |gamma| added
- F-06 MAJOR: .npz schema clarification (u_m(t_k) raw column added)
- F-07 MAJOR: config_pin acknowledged as breaking change (not backward-compatible)
- F-08 MINOR: Concavity proof correct with negative beta (no change needed)
- F-09 MINOR→MAJOR: Delta-update runtime assertion added (every 100th knot)
- F-10 MINOR: Empty K_e handled correctly (no change needed)
- F-11 MINOR: GL node values correct to float64 (no change needed)
- F-12 MAJOR: Comment fix t_{i+1}^- → t_{i+1}^+ (half-open convention clarified)
- F-13 MINOR: Dead `if width > 0` guard (harmless defensive code)
- F-14 MAJOR: rho_values storage added to .npz schema for rho-refit support

**Spec commit:** `7ee9eef4a` (v1.1, sampurti/integration branch)
**Status:** FROZEN for S3 implementation

S3 (≤4 parallel Sonnet lanes) will begin dispatch now. Lanes:
- sm-d1-sweep: core DHARA sweep algorithm (dhara_sweep.py)
- sm-d1-null: vectorized null (dhara_null.py)
- sm-d1-termat: term matrix (.npz artifact, refit path)
- sm-d1-pinmat: (stage×class) pin matrix + engine_config.py

### 2026-08-13 17:55 IST — S3-IMPLEMENTATION-COMPLETE

**S3-IMPLEMENTATION-COMPLETE** — SAMPŪRTI-Δ1 conductor posts this marker.

All four DHĀRĀ S3 implementation lanes have merged to main:

| PR | Lane | Module | SHA |
|----|------|--------|-----|
| #1262 | sm-d1-sweep | `dhara_sweep.py` — event-driven sweep algorithm | MERGED |
| #1263 | sm-d1-null | `dhara_null.py` — vectorized null (1024 replicates) | MERGED |
| #1264 | sm-d1-pinmat | `engine_config.py` + `dhara_pin_matrix.py` — dual-engine flag + stage×class pin matrix | MERGED |
| #1266 | sm-d1-termat | `dhara_term_matrix.py` — term matrix artifact (section 4, F-06/F-14) | MERGED |

DHĀRĀ engine is now on `main` and importable. `dhara_available = True` in test environments.

Δ2 V3 parity battery (PR #1265) is in the merge queue at position 1 (AWAITING_CHECKS on merge group CI). Once merged, S4 PARITY-GREEN gate activates (Δ2 PARĪKṢAKA runs `PARITY_DB_TEST=1 pytest` against native's field).

**FIELD-INTEGRATED** state is now in effect.
