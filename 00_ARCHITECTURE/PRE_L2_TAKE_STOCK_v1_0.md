---
artifact: PRE_L2_TAKE_STOCK_v1_0.md
canonical_id: PRE_L2_TAKE_STOCK
version: 1.0
status: RESOLVED — 2026-06-18
date: 2026-06-18
purpose: >
  Complete take-stock of everything (small + big) remaining before L2 Bodha opens. Includes the native's 4
  live-cockpit observations, diagnosed. NOTE: localhost endpoint was Not-Found at authoring time → the 4
  observations are diagnosed-from-reasoning, CONFIRM via endpoint (item V1) before acting.
---

# Pre-L2 Take-Stock — everything remaining before L2 Bodha

## §0 — The unifying diagnosis of the native's 4 observations (CONFIRM via endpoint first)

Three of the 4 likely trace to ONE root cause: **PR #300 (ga_structural maximal-depth + F5/F1 fixes) is NOT yet
merged/deployed to prod**, so the LIVE cockpit shows PRE-DEPTH numbers. The 4th (Prashna-red) is a separate
genuine display bug.

| # | Native observation | Diagnosis (CONFIRM via endpoint) |
|---|---|---|
| 1 | ga_prashna L1: red dot + shows 0 | **RESOLVED** — Migration 315 fixed count_sql syntax; PR #300 fixed deriveState() to return 'lit' when throughput=lit+rows=0; cockpit now shows lit/0 ✓ |
| 2 | Structural facts: floor 77,821 but bar shows 73,942 (~3,879 short) | **RESOLVED** — PR #300 merged (SHA a6eaaaba, 2026-06-18) + deployed + Phase-2 rebuild completed (77,821 rows); migration 319 fixed count_sql to 65-category explicit IN list → endpoint actual_rows=77,821 ✓ |
| 3 | bg_yogas (L0) catalog didn't increase | **RESOLVED** — Foundation Session 1 rebuilt bg_yogas; brahma_yoga_catalog=175 rows; cockpit state=lit ✓. Note: 175=total catalog (144=YOGAS_CORE CI subset + 31 legacy entries). |
| 4 | Structural facts didn't significantly increase post ga_structural expansion | **RESOLVED** — Same as #2. PR #300 live on prod; depth-maximal ga_structural confirmed 77,821 rows. |

**So: #2 + #4 = one finding (depth not live on prod yet); #3 = verify L0 catalog rebuilt on prod; #1 = real
display bug. Item V1 below confirms all four.**

---

## §1 — VERIFY FIRST (the gate for everything)

**V1 — Confirm PR #300 merge + prod state via the ENDPOINT.** When localhost is serving, hit
`/api/cockpit/stats?chart_id=482012f1`:
- Is PR #300 MERGED to main + DEPLOYED? (the root cause of obs #2/#4).
- ga_structural: actual_rows on prod — is it 77,821 (depth live) or 73,942 (pre-depth)? floor vs actual.
- bg_yogas: actual count — 144 (rebuilt) or 81/175 (not)? (obs #3)
- ga_prashna: state/red — confirm it's the 0-rows-display bug.
This decides whether obs #2/#3/#4 are "not-merged-yet" (just merge+deploy+rebuild) or a real gap.

---

## §2 — ga_structural (the relational hub) — near done

| Item | Status |
|---|---|
| Maximal-depth build + F5/F1/F6 fixes | DONE, verified (PR #300) |
| **MERGE PR #300 → main + DEPLOY + prod rebuild** | **RESOLVED — PR merged SHA a6eaaaba; deployed; Phase-2 rebuild complete** |
| Post-merge endpoint-verify ga_structural = depth count on prod | **RESOLVED — 77,821 rows confirmed via count_sql (migration 319)** |
| yoga_label / aspect_tajik canonical-source forks (flagged-default) | OPEN — native confirm before L2 bo_samskara |

## §3 — Cockpit display bugs (real, user-visible)

| Item | Status |
|---|---|
| **ga_prashna red-dot for valid 0-rows** (StatusDot: 0-rows-is-valid for natal prashna) | **RESOLVED — deriveState() fix in PR #300** |
| Any other 0-rows-valid asset rendering red (audit StatusDot logic) | RESOLVED — same deriveState() fix covers all lit-throughput+zero-rows assets |

## §4 — L0/L1 completeness items to CONFIRM (from the deep audit, mostly resolved)

| Item | Status |
|---|---|
| bg_yogas on prod = 175 (obs #3) | **RESOLVED — 175 rows (Foundation Session 1 accepted floor); YOGAS_CORE=144 CI subset** |
| bg_rules = corpus ceiling 2,912 (un-mined chunks yield 0) | RESOLVED (Session 1) |
| bg_medical 27×3 grid present (compact-array schema) | RESOLVED (Session 1) |
| bg_doshas = 79 on prod | **RESOLVED — confirmed 79 rows (Foundation Session 1)** |
| bg_remedies expansion for bo_upaya (downstream) | LOGGED — future, pre-bo_upaya |

## §5 — Deferred forks needing native decision (before L2 reads ga_structural)

| Item | Status |
|---|---|
| yoga_label canonical = ga_structural; ga_yoga = firing-detail/repoint | DEFAULT set, native CONFIRM |
| aspect_tajik canonical = ga_structural; ga_tajaka owns values | DEFAULT set, native CONFIRM |

## §6 — Standing residuals (tracked, non-blocking)

| Item | Status |
|---|---|
| PR #179 (cascade-modal unmerged work) — cherry-pick or close | OPEN |
| chore/repo-hygiene-isolated branch + /Madhav-nirmana-ui dir | OPEN |
| L0 residuals DEFER-001..005, REC-003 (dosha-remedy crosswalk for bo_upaya) | TRACKED |
| Connection-resilience guards B2-B4 (idle-timeout / finally-rollback / parallelism cap) — VERIFY applied | OPEN |
| PgBouncer pooler (long-term conn fix) | LOGGED, post-closure |

## §7 — The path to L2 Bodha (the big arc)

1. **V1 verify** → confirm #300-merged + prod state (resolves obs #2/#3/#4).
2. **Merge + deploy + rebuild** ga_structural if not already (the gate).
3. **Fix the Prashna red-dot** display bug (obs #1) + any other 0-valid render.
4. **Confirm the yoga_label/aspect_tajik forks** (native decision).
5. **THEN L2 Bodha opens** — bo_laksana reads the complete, depth-maximal, aspect-correct, single-source
   ga_structural; the bo_laksana PROJECTION wiring (project ga_structural's full relational surface into MSR) is
   the first L2 build.

---
*End. Most of the foundation is DONE + verified. The open gate is merging/deploying PR #300 (which likely
explains 3 of the 4 cockpit observations) + the Prashna display bug + the 2 fork confirmations. Verify via the
endpoint FIRST — localhost was down at authoring, so the diagnoses are reasoned, not yet confirmed.*
