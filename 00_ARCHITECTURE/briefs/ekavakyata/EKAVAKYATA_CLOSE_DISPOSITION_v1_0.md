---
artifact: EKAVAKYATA_CLOSE_DISPOSITION_v1_0.md
campaign: EKAVĀKYATĀ (एकवाक्यता)
version: 1.0
status: CURRENT
campaign_disposition: CLOSED-PARTIAL (confirmed; unchanged from the conductor's own terminal marker)
authored: 2026-08-22, wrapped-campaign close-out pass (native-delegated decision)
supersedes: nothing — this is the first written disposition; ekv_manifest.json lane statuses are
  deliberately NOT hand-edited (they are the historical record of where each lane stood at the
  conductor's terminal marker, 2026-08-15T23:38Z)
evidence_basis: >
  origin/main at bf077499e; ekv_manifest.json (40 lanes); LEDGER_C.md; LEDGER_CONDUCTOR.md
  (reconciled 22,661-byte version, PR #1488); per-lane git-log / git-grep against origin/main
  and 00_ARCHITECTURE/briefs/parisesa/; branch ahead/diff against merge-base.
---

# EKAVĀKYATĀ — Close Disposition

## §1 — Why this document exists

The conductor closed the campaign at `CAMPAIGN TERMINAL MARKER: EKAVAKYATA-CLOSED-PARTIAL —
2026-08-15T23:38Z` with 18 of 40 lanes unlanded (`LIVE 21 / MERGED 1 / CLAIMED 15 / BUILT 2 /
CI_FAILED 1`). No disposition was ever written for those 18: the morning session that followed
recorded only CL-00's triage and then stopped. Seven days later the repo still carried 27
EKAVĀKYATĀ worktrees and 36 `ekv/*` branches with no statement of what any of them were for.

This document records, per lane, what actually happened to the underlying defect — so that the
branches can be left alone (or pruned) without anyone having to re-derive this, and so that the
three lanes with real stranded work are findable by name rather than by archaeology.

**It asserts no new completion.** Where a lane is marked SUPERSEDED, the evidence is a merged PR
on `origin/main` that resolves the same defect, cited by SHA. Where it is marked PARKED, the work
is explicitly *not* done.

## §2 — Disposition table (18 unlanded lanes)

| Lane | Manifest status | Disposition | Evidence / pointer |
|---|---|---|---|
| **B-01** dignity oracle | CI_FAILED | **SUPERSEDED** | Landed anyway as `7459f8837` (#1296, F-72); extended by PARIŚEṢA `cfef54a25` (#1416, F-62) and `01082bc0f` (#1452, F-153). Branch `ekv/b-01-dignity-oracle` is a strict subset of main. |
| **D-01** lint battery | BUILT | **SUPERSEDED** | `3f9bbabe5` (#1310) merged all five `check_*.py` + `ekv-lints.yml`. Status was stale, not unlanded. |
| **D-04** CL-00 harness | BUILT | **SUPERSEDED** | `3f9bbabe5` (#1310) landed `ekv_controls.py`; `5ff46c2a0` (#1311) fixed F-83/F-85; maintained through `740915826` (#1450). |
| **A-18** gochara URI | CLAIMED | **SUPERSEDED** | PARIŚEṢA `c192d56d7` (#1390, F-73) fixed the exact phantom `marsys://tool/L4/gochara_forecast_get` URI. No EKV branch ever existed. |
| **B-06** muhurta honesty | CLAIMED | **SUPERSEDED** | PARIŚEṢA `c6d956eb0` (#1410, F-48) — same file, same earned-signal defect. No EKV branch ever existed. |
| **D-05** governance record | CLAIMED | **SUPERSEDED** | PARIŚEṢA `8a5fc4d0a` (#1422, F-94) + `F94_GOVERNANCE_DRIFT_RECONCILIATION_PLAN_v1_0.md`. No EKV branch ever existed. |
| **D-06** build-state honesty | CLAIMED (F-141/F-102) | **SUPERSEDED** | `51096a655` (#1314) landed the lit-beside-error detector. The 5 violating data rows are `EXTERNAL_HOLD` in `PARISESA_V4_FINAL_CLOSE_AND_TEARDOWN.md` — owner-parked, not forgotten. |
| **B-08** salience ranker | CLAIMED | **SUPERSEDED** | PARIŚEṢA `b9ac7a26f` (#1424, F-114) + `F114_RANKING_DESIGN_CONTRACT_v1_0.md` (IMPLEMENTED) resolved the identical byte-identical-top-10 defect in `composite_ranker.ts`. The EKV domain-affinity multiplier on `ekv/b-08-ranker` (one own commit, `408c4fae8`) is redundant. |
| **B-09** rebuild runbook | CLAIMED | **PARKED — real work** | `ekv/b-09-rebuild-runbook` (on origin, +6, 9 files, +1119): `EKV_E03_GOCHARA_REBUILD_RUNBOOK.md`, both `dispatch_ekv_e03_gochara_*.py`, `test_b09_runbook_artifacts.py`. None of it is on main; no successor. Manifest names the branch `b-09-rebuild-prep`, which does not exist — the rename is the reason it reads as "no work" to a manifest-only audit. |
| **E-03** gochara rebuild | CLAIMED (deps B-01/02/03) | **PARKED — pairs with B-09** | Dispatch tooling lives on `ekv/b-09-rebuild-runbook`; the rebuild itself was never executed. Pick up together with B-09 only if a gochara rebuild becomes needed. |
| **B-07** nimitta epistemic enum | CLAIMED | **PARKED — real work, half-superseded** | PARIŚEṢA `31efce9ee` (#1378, F-68) covers the numeric-suppression half. The shared `brahmagyan/phala/confidence_vocab.py` + `tests/l4/test_b07_confidence_basis_vocab.py` (107 lines) on `ekv/b-07-nimitta-tag` (on origin, +6) are not on main. Manifest names it `b-07-phnimitta` (nonexistent). |
| **A-10** middleware | CLAIMED | **NEVER CODED — re-file** | No branch on origin; no chart-existence precondition exists in `platform-mcp/src`. |
| **C-04** outcomes lifecycle | CLAIMED | **NEVER CODED — re-file as product gap** | `EKV-C-04-BLOCKED` (LEDGER_C.md:156): no dismiss/withdraw write path exists; still none on main. Blocked by design, not by neglect. |
| **D-02** param parity | CLAIMED | **NEVER CODED — re-file** | No branch, no artifact. |
| **D-03** reachability CI | CLAIMED | **NEVER CODED — re-file** | The "whitelist + live-callable + URI-resolves" check does not exist. Adjacent only: `740915826` (#1450) repointed dead governance checks. |
| **C-05** auto-filing | CLAIMED | **NEVER CODED — re-file** | Spec only (`EKV-C-05-BUILT` = spec; handoff markers `EKV-C05-SPEC-B/E` never picked up). |
| **A-14** register gloss | CLAIMED | **NEVER CODED — re-file** | Detector exists (`check_no_raw_token_in_narrative.py`, #1310) but `ekv-lints.yml` is `continue-on-error: true` with non-empty allowlists. The actual work — flip to blocking, drain the allowlist across the 125-tool sweep — was never started. |
| **E-04** verification battery | CLAIMED | **PROCESS LANE — partially discharged, nothing to merge** | CL-00 full 27-control battery ran in the morning session: `PASS-AFTER-TRIAGE` (17 PASS / 1 FAIL / 7 SKIP / 2 WARN). |

**Totals:** SUPERSEDED 8 · PARKED (real work) 3 · NEVER CODED 6 · PROCESS 1.

## §3 — Morning-session residuals (LEDGER_CONDUCTOR.md, MORNING SESSION ITEMS 1–7)

| # | Item | Status on origin/main |
|---|---|---|
| 1 | CL-00: merge `ekv_controls.py`, re-run | **DONE** — #1310, #1311, #1450 |
| 2 | B-01: rebase onto main | **DONE by other means** — #1296 landed F-72; conflicted files reconciled on main; branch never rebased and is now stale |
| 3 | TAP SC-17/18/19 pointer validation | **NOT DONE** — no commit after 2026-08-15 references SC-17/18/19 |
| 4 | W1 evidence files for 8 drain lanes | **DONE** — the 10 `evidence/*.json` land on main via PR #1488 (they had existed only in a working tree) |
| 5 | Gate fidelity: W1 evidence-file-exists check in `ekv_gate.py` | **NOT DONE** — `ekv_gate.py` never landed anywhere on main |
| 6 | PR #1287 web-build first-deploy failure root cause | **NOT DONE / no trace** |
| 7 | A-15 canary key transient 401 | **NOT DONE / no trace** |

Items 3, 5, 6, 7 are open residuals. None is P3-blocking. They are recorded here so they are not
lost; they are not re-filed into any other campaign's register by this document.

## §4 — Decisions taken in this close-out (2026-08-22, native-delegated)

1. **No EKV lane is re-implemented now.** All three PARKED branches are 6–11 commits behind a
   `main` that has moved ~90k lines; "finish" is a rewrite, not a merge, and none is a P3
   precondition.
2. **`ekv/*` branches are retained on origin unchanged.** The three PARKED branches are the
   pointers; the rest are historical. `rescue/ekv-a-25-dasha-sandhi-principal-20260819` and
   `rescue/ekv-b-01-dignity-oracle-20260819` (pre-existing, 2026-08-19) remain the durable copies of
   the two branches whose local tips had diverged from origin.
3. **All 27 EKAVĀKYATĀ worktrees were removed** (2026-08-22). Worktree removal never deletes a
   branch or commit; uncommitted content in `ekv-lead-dharma` (`ekv_controls.py` edit) and
   `ekv-lead-shastra` (`test_b08_ranker.py`) was committed in place on those branches first
   (`8306e6f17`, `47817629e`).
4. **`ekv_manifest.json` is not edited.** Its lane statuses are the record of the terminal-marker
   moment. This document is the disposition layer on top of it.

## §5 — What would reopen this

Only E-03 (a gochara rebuild becoming necessary) has a concrete trigger. If that happens, start
from `ekv/b-09-rebuild-runbook`, rebase, and treat B-08's one commit as discardable (F-114 already
resolved the ranker).
