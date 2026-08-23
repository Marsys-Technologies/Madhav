---
artifact: PARISESA_BOARD
version: 0.1
status: LIVE
updated: 2026-08-16T13:03:21.319778 (Phase 0)
owner: SUTRADHARA (sole writer)
---

# PARIŚEṢA BOARD — 71 findings

**Counts:** LIVE 1/71 (F-62 code-live/data-pending-rebuild counted separately, see REBUILD_SCOPE.md) · Stage R 1 · Stage S 25 · Stage D 44 · blocked 0 (8 parked per §8, not blocked — see notes) — refreshed 2026-08-16 17:45 IST per conductor wake-up

## Phase 0 classification

| Finding | Stream | Tier | Class | Stage | Branch/note | Diag |
|---|---|---|---|---|---|---|
| F-01 | S6 | TIER1-CORRECTNESS | ALREADY-FIXED | LIVE | — |  |
| F-03 | S5 | TIER2-HONESTY | OPEN | S(S5 branch) | — |  |
| F-04 | S5 | TIER2-HONESTY | OPEN | S(S5 branch) | — | DIAGNOSIS-INCOMPLETE |
| F-05 | S5 | TIER3-EXPERIENCE | OPEN | D(S5 branch) | — |  |
| F-06 | S5 | TIER2-HONESTY | OPEN | D(S5 branch) | — |  |
| F-08 | S5 | TIER2-HONESTY | OPEN | D(S5 branch) | — |  |
| F-09 | S1 | TIER4-POLISH | OPEN | S | — |  |
| F-10 | S5 | TIER1-CORRECTNESS | OPEN | S(S5 branch, CL-03 exemplar) | — |  |
| F-11 | S1 | TIER4-POLISH | OPEN | D | — |  |
| F-12 | S2 | TIER2-HONESTY | OPEN | S | CORRECTED (S2 Stage-D): ekv/a-09-sara-kernel's committed diff is scoped only to response_budget.ts+registry_bridge.ts for assess_* composition (F-56/F-111); does not touch F-12's file at all. Reclassified from BRANCH-EXISTS. Mechanism: L1_ganita `total` = rows.length not real COUNT(*), ~20 sibling sites found across the registry. Routes to S5 to build (L1_ganita is S5's lease). |  |
| F-13 | S2 | TIER2-HONESTY | OPEN | D | CORRECTED: ekv/a-09-sara-kernel BRANCH-EXISTS label is stale/disproven for this finding (same pattern S2 found for F-12/F-36/F-37/F-45 — branch doesn't touch this file). Reclassify OPEN pending fresh diagnosis. | DIAGNOSIS-INCOMPLETE |
| F-14 | S2 | TIER1-CORRECTNESS | OPEN | S | — |  |
| F-15 | S2 | TIER1-CORRECTNESS | OPEN | D | — |  |
| F-17 | S1 | TIER3-EXPERIENCE | OPEN | S | — |  |
| F-18 | S1 | TIER3-EXPERIENCE | OPEN | D | — |  |
| F-22 | S5 | TIER2-HONESTY | OPEN | D(S5 branch) | — |  |
| F-23 | S6 | TIER3-EXPERIENCE | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — |  |
| F-25 | S1 | TIER1-CORRECTNESS | BRANCH-EXISTS | D(adopted,pushed) | ekv/a-25-dasha-sandhi-principal |  |
| F-26 | S5 | TIER2-HONESTY | OPEN | D | — |  |
| F-27 | S5 | TIER2-HONESTY | OPEN | D(S5 branch) | — | DIAGNOSIS-INCOMPLETE |
| F-28 | S2 | TIER2-HONESTY | OPEN | D | CORRECTED: ekv/a-09-sara-kernel BRANCH-EXISTS label is stale/disproven for this finding (same pattern S2 found for F-12/F-36/F-37/F-45 — branch doesn't touch this file). Reclassify OPEN pending fresh diagnosis. | DIAGNOSIS-INCOMPLETE |
| F-31 | S3 | TIER3-EXPERIENCE | OPEN | D | — | DIAGNOSIS-INCOMPLETE |
| F-33 | S3 | TIER3-EXPERIENCE | OPEN | D | — | DIAGNOSIS-INCOMPLETE |
| F-34 | S3 | TIER2-HONESTY | OPEN | S | — |  |
| F-35 | S3 | TIER4-POLISH | OPEN | S | — | DIAGNOSIS-INCOMPLETE |
| F-36 | S2 | TIER2-HONESTY | OPEN | S | CORRECTED (S2 Stage-D): same over-broad Phase-0 note as F-12 — a-09-sara-kernel doesn't touch this file. Silent offset-clamp bug, distinct mechanism from F-12/F-37 (total already correct here). File (register_d7_channel.ts) added to S5's lease. |  |
| F-37 | S2 | TIER2-HONESTY | OPEN | D | CORRECTED (S2 Stage-D): same as F-12 — a-09-sara-kernel doesn't touch this file. Same total=rows.length mechanism as F-12. Routes to S5 to build. |  |
| F-38 | S1 | TIER2-HONESTY | OPEN | D | — | DIAGNOSIS-INCOMPLETE |
| F-43 | S1 | TIER2-HONESTY | OPEN | D | — |  |
| F-44 | S2 | TIER2-HONESTY | OPEN | D | — |  |
| F-45 | S2 | TIER2-HONESTY | OPEN | S | CORRECTED (S2 Stage-D): same as F-12 — a-09-sara-kernel doesn't touch any of the 5 affected sub-tools. Different mechanism (count correct at construction, response_budget.ts trims array downstream without re-deriving count). Routes to S5 to build (register_p1_aliases.ts/register_p1_synthesis.ts/L3_kala/L2_bodha). DIAGNOSIS-INCOMPLETE gap closed. |  |
| F-46 | S2 | TIER3-EXPERIENCE | OPEN | D | — |  |
| F-47 | S3 | TIER2-HONESTY | OPEN | S | — |  |
| F-48 | S3 | TIER2-HONESTY | OPEN | S | — |  |
| F-50 | S4 | TIER3-EXPERIENCE | OPEN | D(S4 branch) | — | DIAGNOSIS-INCOMPLETE |
| F-54 | S6 | TIER3-EXPERIENCE | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — | DIAGNOSIS-INCOMPLETE |
| F-56 | S2 | TIER1-CORRECTNESS | OPEN | D | CORRECTED: ekv/a-09-sara-kernel BRANCH-EXISTS label is stale/disproven for this finding (same pattern S2 found for F-12/F-36/F-37/F-45 — branch doesn't touch this file). Reclassify OPEN pending fresh diagnosis. | DIAGNOSIS-INCOMPLETE |
| F-61 | S5 | TIER2-HONESTY | OPEN | D(S5 branch) | — | DIAGNOSIS-INCOMPLETE |
| F-62 | S6 | TIER1-CORRECTNESS | BRANCH-EXISTS | LIVE(code) | ekv/b-01-dignity-oracle (PAR-R-1 correction: origin/ekv/b-01-dignity-oracle and origin/ekv/b-01-dignity-oracle-fix now point to the SAME commit dfbdfe620, 6 ahead/23 behind main — adopt the plan-named branch, delete the -fix duplicate ref at close, never merge both) | DIAGNOSIS-INCOMPLETE |
| F-63 | S4 | TIER3-EXPERIENCE | OPEN | D(S4 branch) | — | DIAGNOSIS-INCOMPLETE |
| F-67 | S1 | TIER1-CORRECTNESS | OPEN | D | — |  |
| F-68 | S3 | TIER1-CORRECTNESS | OPEN | S | CORRECTED (S3 Stage-D): ekv/b-07-nimitta-tag only renames a string literal to a named constant (§N.4 hygiene) — does NOT fix the real claim (numeric posterior/confidence/lift served unconditionally under a non-calibrated tag, P3-b tier-suppression violation). Reclassified from BRANCH-EXISTS; branch may still be a useful starting point for the real fix but does not close the finding on its own. |  |
| F-69 | S3 | TIER2-HONESTY | OPEN | S | — |  |
| F-70 | S5 | TIER2-HONESTY | OPEN | D(S5 branch) | — |  |
| F-73 | S1 | TIER2-HONESTY | OPEN | D | — |  |
| F-78 | S3 | TIER3-EXPERIENCE | OPEN | S | — |  |
| F-79 | S6 | TIER2-HONESTY | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — |  |
| F-81 | S6 | TIER3-EXPERIENCE | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — |  |
| F-93 | S4 | TIER2-HONESTY | OPEN | D(S4 branch) | — | DIAGNOSIS-INCOMPLETE |
| F-94 | S6 | TIER2-HONESTY | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — | DIAGNOSIS-INCOMPLETE |
| F-95 | S6 | TIER2-HONESTY | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — |  |
| F-111 | S2 | TIER1-CORRECTNESS | OPEN | D | CORRECTED: ekv/a-09-sara-kernel BRANCH-EXISTS label is stale/disproven for this finding (same pattern S2 found for F-12/F-36/F-37/F-45 — branch doesn't touch this file). Reclassify OPEN pending fresh diagnosis. |  |
| F-112 | S2 | TIER2-HONESTY | OPEN | D | CORRECTED: ekv/a-09-sara-kernel BRANCH-EXISTS label is stale/disproven for this finding (same pattern S2 found for F-12/F-36/F-37/F-45 — branch doesn't touch this file). Reclassify OPEN pending fresh diagnosis. |  |
| F-116 | S4 | TIER2-HONESTY | OPEN | D(S4 branch) | — |  |
| F-117 | S3 | TIER3-EXPERIENCE | OPEN | S | — |  |
| F-120 | S4 | TIER3-EXPERIENCE | OPEN | D(S4 branch) | — |  |
| F-121 | S4 | TIER3-EXPERIENCE | OPEN | D(S4 branch) | — |  |
| F-122 | S2 | TIER2-HONESTY | OPEN | D | CORRECTED: ekv/a-09-sara-kernel BRANCH-EXISTS label is stale/disproven for this finding (same pattern S2 found for F-12/F-36/F-37/F-45 — branch doesn't touch this file). Reclassify OPEN pending fresh diagnosis. |  |
| F-123 | S1 | TIER3-EXPERIENCE | OPEN | S | — |  |
| F-124 | S2 | TIER3-EXPERIENCE | OPEN | D | — |  |
| F-125 | S2 | TIER3-EXPERIENCE | OPEN | D | — |  |
| F-126 | S3 | TIER4-POLISH | OPEN | S | — |  |
| F-129 | S4 | TIER2-HONESTY | OPEN | D(S4 branch) | — |  |
| F-130 | S4 | TIER2-HONESTY | OPEN | D(S4 branch) | — |  |
| F-132 | S4 | TIER3-EXPERIENCE | OPEN | D(S4 branch, running) | — |  |
| F-133 | S5 | TIER3-EXPERIENCE | OPEN | D(S5 branch) | — |  |
| F-134 | S3 | TIER4-POLISH | OPEN | S | — |  |
| F-135 | S4 | TIER4-POLISH | OPEN | R-INCOMPLETE(S4 branch) | — |  |
| F-136 | S6 | TIER4-POLISH | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — |  |
| F-139 | S6 | TIER3-EXPERIENCE | PARKED | PARKED (per plan §8 degrade order, honest handoff, no branch) | — |  |
| F-141 | S6 | TIER3-EXPERIENCE | OPEN | S(rescoped) | PAR-R-9: DIAGNOSIS-INCOMPLETE closed, but scope expanded — real defect is 5 stale rows (not 1), 2.47M row overstatement (not 566K); both proposed fixes (restate/rebuild) refused, no known orchestrator path produces this state, mechanism genuinely untraced. Rescoped to detector-only + honest disclosure + continued trace. Expected close: PARKED-WITH-DETECTOR, not fully green — this is the correct honest outcome per plan §9. |  |

## Notes

- F-01: desk-verified live (memory S... prior session + this session's re-check via standing_predictions_read pattern) — is_error:false, 3 open predictions. Evidence file: evidence/F-01_live.json.
- F-62 (CORRECTED post-Phase-0, PAR-R-1, PRATINIDHI): the conductor's original Phase-0 note ("ekv/b-01-dignity-oracle-fix is local-only, 5 commits ahead") went stale the moment it was pushed — PRATINIDHI independently re-derived the refs and found `origin/ekv/b-01-dignity-oracle` and `origin/ekv/b-01-dignity-oracle-fix` both now point to `dfbdfe620` (6 ahead / 23 behind main), reconfirmed live by the conductor via fresh `git ls-remote`. Adopt `ekv/b-01-dignity-oracle` (plan-named), rebase onto main in a fresh worktree; `git worktree remove` the stale nested worktree under `ekv-lead-shastra` (PRATINIDHI verified clean); delete the `-fix` duplicate ref at campaign close, never merge both.
- F-62 additional PRATINIDHI rulings for S6's build stage: **PAR-R-2** (MT-vs-Own degree boundary) — half-open `[mt_from, mt_to)`, classically grounded ("MT stated as up to N degrees"); exact-boundary goldens for every MT graha mandatory in the exit test. **PAR-R-3** (defect caught inside the adopted branch before Stage R) — `dignity_oracle.py` holds a private THIRD copy of the degree table (after migration 250 and `bg_dignity_reference.py`), violating §N.7 item 3; ruling is to extract to a shared dependency-free module both writer and oracle import, plus a DB-vs-Python contract test as the real detector (fallback of copy+equality-test only permitted if extraction breaks the FROZEN writer contract, and only by a further PRATINIDHI ruling). PRATINIDHI also flagged: F-62's claim decomposes into 3 sub-claims (missing MT tier in ga_structural_writer, ga_vargas_writer over-emission, no shared oracle) — a spec wiring all three consumers without closing the shared-oracle sub-claim is INCOMPLETE under Stage S rule 7.
- CL-00 baseline: CONFIRMED on origin/main tip already — `5ff46c2a0` (#1311, F-83/F-85) and `3f9bbabe5` (#1310, Stream D battery) are the top two commits of origin/main. The `ekv/morning-cl00-fixes` / `ekv/morning-d04-merge` branches themselves are stale refs (content already landed via squash), no merge action needed. Remaining CL-00 red = F-141 (lit-beside-error), in scope for S6, OPEN.
- `ekv/b-08-ranker`, `ekv/b-09-rebuild-runbook` exist on origin but not yet mapped to a specific F-id in the plan's stream lists — leaving as informational; owning stream lead may claim if a lane's D-stage finds it relevant.
- `ekv/lead-dharma` covers D-01..D-08 lint tooling + CL-00 battery, not a direct fix for F-79/F-81 (CL-22 governance) — left OPEN, lead-dharma is a resource not a completed branch for those findings.
- No `ekv/d-02-param-parity` branch found on origin — CL-03 (S5) findings are OPEN, no adoption available.

## Per-stream TODO

### S1
- [ ] F-09 (TIER4-POLISH, OPEN)
- [ ] F-11 (TIER4-POLISH, OPEN)
- [ ] F-17 (TIER3-EXPERIENCE, OPEN)
- [ ] F-18 (TIER3-EXPERIENCE, OPEN)
- [ ] F-25 (TIER1-CORRECTNESS, BRANCH-EXISTS)
- [ ] F-38 (TIER2-HONESTY, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-43 (TIER2-HONESTY, OPEN)
- [ ] F-67 (TIER1-CORRECTNESS, OPEN)
- [ ] F-73 (TIER2-HONESTY, OPEN)
- [ ] F-123 (TIER3-EXPERIENCE, OPEN)

### S2
- [ ] F-12 (TIER2-HONESTY, BRANCH-EXISTS)
- [ ] F-13 (TIER2-HONESTY, BRANCH-EXISTS) — DIAGNOSIS-INCOMPLETE
- [ ] F-14 (TIER1-CORRECTNESS, OPEN)
- [ ] F-15 (TIER1-CORRECTNESS, OPEN)
- [ ] F-28 (TIER2-HONESTY, BRANCH-EXISTS) — DIAGNOSIS-INCOMPLETE
- [ ] F-36 (TIER2-HONESTY, BRANCH-EXISTS)
- [ ] F-37 (TIER2-HONESTY, BRANCH-EXISTS)
- [ ] F-44 (TIER2-HONESTY, OPEN)
- [ ] F-45 (TIER2-HONESTY, BRANCH-EXISTS) — DIAGNOSIS-INCOMPLETE
- [ ] F-46 (TIER3-EXPERIENCE, OPEN)
- [ ] F-56 (TIER1-CORRECTNESS, BRANCH-EXISTS) — DIAGNOSIS-INCOMPLETE
- [ ] F-111 (TIER1-CORRECTNESS, BRANCH-EXISTS)
- [ ] F-112 (TIER2-HONESTY, BRANCH-EXISTS)
- [ ] F-122 (TIER2-HONESTY, BRANCH-EXISTS)
- [ ] F-124 (TIER3-EXPERIENCE, OPEN)
- [ ] F-125 (TIER3-EXPERIENCE, OPEN)

### S3
- [ ] F-31 (TIER3-EXPERIENCE, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-33 (TIER3-EXPERIENCE, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-34 (TIER2-HONESTY, OPEN)
- [ ] F-35 (TIER4-POLISH, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-47 (TIER2-HONESTY, OPEN)
- [ ] F-48 (TIER2-HONESTY, OPEN)
- [ ] F-68 (TIER1-CORRECTNESS, BRANCH-EXISTS)
- [ ] F-69 (TIER2-HONESTY, OPEN)
- [ ] F-78 (TIER3-EXPERIENCE, OPEN)
- [ ] F-117 (TIER3-EXPERIENCE, OPEN)
- [ ] F-126 (TIER4-POLISH, OPEN)
- [ ] F-134 (TIER4-POLISH, OPEN)

### S4
- [ ] F-50 (TIER3-EXPERIENCE, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-63 (TIER3-EXPERIENCE, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-93 (TIER2-HONESTY, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-116 (TIER2-HONESTY, OPEN)
- [ ] F-120 (TIER3-EXPERIENCE, OPEN)
- [ ] F-121 (TIER3-EXPERIENCE, OPEN)
- [ ] F-129 (TIER2-HONESTY, OPEN)
- [ ] F-130 (TIER2-HONESTY, OPEN)
- [ ] F-132 (TIER3-EXPERIENCE, OPEN)
- [ ] F-135 (TIER4-POLISH, OPEN)

### S5
- [ ] F-03 (TIER2-HONESTY, OPEN)
- [ ] F-04 (TIER2-HONESTY, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-05 (TIER3-EXPERIENCE, OPEN)
- [ ] F-06 (TIER2-HONESTY, OPEN)
- [ ] F-08 (TIER2-HONESTY, OPEN)
- [ ] F-10 (TIER1-CORRECTNESS, OPEN)
- [ ] F-22 (TIER2-HONESTY, OPEN)
- [ ] F-26 (TIER2-HONESTY, OPEN)
- [ ] F-27 (TIER2-HONESTY, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-61 (TIER2-HONESTY, OPEN) — DIAGNOSIS-INCOMPLETE
- [ ] F-70 (TIER2-HONESTY, OPEN)
- [ ] F-133 (TIER3-EXPERIENCE, OPEN)

### S6
- [x] F-01 (TIER1-CORRECTNESS, ALREADY-FIXED)
- [x] F-23 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [x] F-54 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [ ] F-62 (TIER1-CORRECTNESS, BRANCH-EXISTS) — DIAGNOSIS-INCOMPLETE
- [x] F-79 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [x] F-81 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [x] F-94 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [x] F-95 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [x] F-136 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [x] F-139 PARKED (§8 degrade order, no diagnosis, honest handoff)
- [ ] F-141 (TIER3-EXPERIENCE, OPEN) — DIAGNOSIS-INCOMPLETE
