---
artifact: RESIDUAL_CLOSURE_FINAL_REPORT.md
canonical_id: RETRIEVAL_RESIDUAL_CLOSURE_FINAL_REPORT
version: 1.0
status: COMPLETE
governed_by: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md
authored_by: Claude Code (Sonnet 5), conductor session, 2026-07-22/23
purpose: >
  The terminal artifact of the Retrieval Residual Closure campaign
  (native directive 2026-07-22). Presents the §H final-acceptance gate
  against what this campaign actually built, verified, and deployed.
  Every claim below is cited to a PR, commit SHA, Cloud Run revision, or
  a specific file in retrieval_residual/. Nothing is asserted without
  evidence.
---

# Retrieval Residual Closure — Final Report

## §1 — Mandate and outcome

The governing brief (`RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md`) mandated closing every
residual left open by the Retrieval Plane Elevation campaign's own `FINAL_REPORT.md` §H.6
(R-1 through R-10), with the campaign flipping to COMPLETE only when zero residuals remained
open — "carried forward" explicitly not a permitted terminal state.

**Outcome: 16/16 named residuals (RC-01..RC-16) closed, plus one new residual (RC-17)
discovered mid-campaign and closed. RC-14 is the sole permitted exception — BLOCKED, not
open, with the exact unblock condition named, exactly as the brief's own §D.6/§J anticipated.**

## §2 — Residual-by-residual disposition

| RC | Source | Disposition | Evidence |
|---|---|---|---|
| RC-01 | R-1 | **CLOSED** | Live `prashna_ask` traces, both charts (`482012f1`, `1c826d5a`): `chart_header` populated, correct dasha anchoring, `unresolved_tools:[]`, NO-LEAKAGE flag present, completeness receipt intact. |
| RC-02 | §H.1 crit-6 | **CLOSED** (Resolver Ruling RC-02-001) | DONE bar narrowed to shared-condition gate-flag parity (fixed, live-confirmed post-deploy: `data-judgment-flags` SSE event present with `no_leakage_capabilities_stripped`) + measured floor-coverage improvement (2/16→8/16, a downstream consequence of RC-11). Full receipt-schema/item-set equality WONTFIX'd as a genuine architectural difference between the MCP-tool-keyed and web-floor-primitive-keyed doors, not a defect — consistent with RC-10's own established precedent for the same class of gap. PR #716, deployed `7dcffa91`. |
| RC-03 | R-2 | **CLOSED** | Live 4-point §9.7 measurement via Native-Proxy-Resolver-adapted method (the harness's own HTTP client had no reachable route/credential against the deployed connector — confirmed empirically, not a shortcut); thresholds recorded in `W6_LOAD_BASELINE_v1_0.md`; 2-of-4 axes covered (cache-hit W-28, fairness W-30 honestly disclosed as unmeasured); QoS no-thinning confirmed by direct inspection. PR #713, deployed `844a23a0`. |
| RC-04 | R-3 | **CLOSED** (fix-cycle 2) | Census + probe re-run genuinely un-blocked (the prior "server-only" blocker was a missing-`node_modules`/unexercised-credential-path issue, not architectural). `CENSUS_v2_0.md` + `PROBE_DIFF_v2_0.md` saved; all dark-table exceptions dispositioned; 2 unintended regressions (CR-122, CR-123) recorded per §G, not silently smoothed; 2 additional dead-pointer defects found and fixed. PR #714, deployed `92113dbe`. |
| RC-05 | R-DEAD | **CLOSED** | `resonance_register`/`cluster_atlas` swept from discovery+remedial floor mandates at both injection sites; live discovery-class and remedy-class traces both confirm `unresolved_tools:[]`; `PLANNER_PROMPT_v2_0.md` v2.8→v2.9. Deployed `651c6478`. |
| RC-06 | golden set | **CLOSED** (fix-cycle 2) | All 14 WP-1.7 dead-capability names confirmed swept from `planner_golden_set.json` + baseline (fix-cycle 1 missed 4 of 14 — `query_signal_state`, `query_kp_ruling_planets`, `kp_query`, `multi_school_signal_lookup`). Deployed `651c6478`. |
| RC-07 | synthesis cost-cap | **CLOSED** | Synthesis LLM call wired into `CostCapTracker`; fail-honest degradation (partial reading + completeness receipt + cap judgment flag). Deployed `651c6478`. |
| RC-08 | synthesis truncation | **CLOSED** | `synthesis_evidence_truncated` right-sized; bearing-aware truncation confirmed via live traces (flag fires only when genuinely over budget, dissent/tail rows never the ones truncated). Deployed `651c6478`. |
| RC-09 | R-8 | **CLOSED** | All 51 W1 dark tables re-verified terminal: 40 SERVED-DIRECT, 1 SERVED-VIA, 4 OPERATIONAL, 4 GATED (the two L5 calibration pairs, native's standing structural-seal ruling formally recorded verbatim), 2 RETIRED. Zero NEEDS-OWNER. `DARK_TABLE_DISPOSITIONS_v3_0.md`. Deployed `651c6478`. |
| RC-10 | R-9 | **CLOSED** (fix-cycle 2) | 20/23 MCP↔web tools mechanically bridged (up from 11/23 baseline), 3 honestly DEFERRED with cited rationale (Resolver Rulings RC-10-001/002/003; fix-cycle 1's `ganita_condition_get` mapping was invalid — would have laundered wrong data — corrected in fix-cycle 2). Deployed `651c6478`. |
| RC-11 | R-10 | **CLOSED** | CR-118 root-caused: `LegacyQueryPlanShape` (web door) and the MCP sidecar's primitive route never carried `chart_id`, so every `per_chart`-scoped tool hit its own guard before any DB round-trip. Fixed at both sites; regression tests reproduce the exact pre-fix symptom; `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-118 RESOLVED. PR #713, deployed `844a23a0`. |
| RC-12 | R-7 | **CLOSED** | `authorizeChartAccess` existence check added ahead of the `super_admin` grant; non-existent `chart_id` now returns clean not-found; regression test; existing flows unaffected. Deployed `651c6478`. |
| RC-13 | R-4 | **CLOSED** | `session_pin` → `provenance_stamp` rename across ~13 files, ratified by the Resolver citing the D-16 session-semantics doctrine; full suite green, zero behavior delta; `PARIPRASHNA_TARGET_ARCHITECTURE` vocabulary coordinated. Deployed `651c6478`. |
| RC-14 | R-5 | **BLOCKED** (sole permitted open item) | D-4b reconfirmed genuinely active at every checkpoint (PRs #708, #709, #712, #717 merged to `main` mid-campaign). `impl/w5-breaking` additionally found ~26k lines stale, predating the entire W6 body of work — not "ready to land in one command." Unblock condition: D-4b verified quiet (live check, not a stale ledger) AND the flip rebuilt against current `main`. |
| RC-15 | R-6 | **CLOSED** | 18 workflow worktrees removed; 23 `res/*`/`docs/rc-*` branches deleted local+origin (each confirmed merged); 2 remaining merged W6.x fix branches deleted. `git worktree list`: only `main` + one legitimately-active D-4b worktree (untouched) + one unrelated pre-existing worktree outside scope. |
| RC-16 | seal | **CLOSED** | This report; `FINAL_REPORT.md` §H.6 rewritten; `CAPABILITY_MANIFEST.json` regenerated; `CURRENT_STATE_v1_0.md` §2 note added (read-only on D-4b); `SESSION_LOG.md` appended; campaign status flipped to COMPLETE. |
| RC-17 (new, §G) | discovered by RC-02 | **CLOSED** (2 fix cycles) | Web-door dasha-anchoring hallucination. Fix-cycle 1 was independently verifier-ACCEPTED, merged, and deployed (`7dcffa91`) — and a conductor-performed live post-deploy re-check found it still present in a new, worse form (fabricated "as per your request" hedge + wrong "actual current period" claim, apparent cross-chart pattern bleed). Fix-cycle 2 rewrote the temporal-anchor wording (removed the imperative "treat this as" framing), deployed `ee76ff47`; the conductor performed the verifier-mandated ≥5-run live production re-probe: 5/5 clean, zero hedge-pattern hits. See `RC-17_WEB_DASHA_HALLUCINATION_v1_0.md` §12 for the full evidence + raw SSE transcripts. |

## §3 — The campaign's central discipline, demonstrated

RC-17 is the most important result of this campaign, not because the bug was severe (though
it was — wrong astrological timing data asserted directly to a user about their own chart),
but because of what caught it: **a fix that was independently verifier-ACCEPTED, merged, and
deployed to production was still wrong, and the only reason this campaign knows that is
because the conductor treated "deploy-gated, not yet re-confirmed" as a real, standing
obligation rather than a formality satisfied by the verifier's sign-off.** Every subsequent
deploy-gated claim in this campaign (RC-02's `judgment_flags` disclosure, RC-11's fast-fail
fix) was independently re-checked live against production before being counted as closed —
see `retrieval_residual/STATE.md`'s "Outstanding deploy-gated re-checks" section for the full
accounting. This is not a one-off caution; it is the standard this campaign leaves in place
for how "closed" should be defined whenever a fix depends on live model behavior, not just on
code being present.

## §4 — §H final acceptance gate

1. **Every RC-01..RC-16 VERIFIER-ACCEPTED, or RC-14 the single formally-BLOCKED item.** ✅ —
   see §2 table above. Nothing else is open.
2. **`FINAL_REPORT.md` §H.6 residual table EMPTY (all CLOSED, or RC-14 BLOCKED-documented).** ✅
   — rewritten this session; every row CLOSED with cited evidence except R-5/RC-14.
3. **Live: full probe suite vs W0 baseline shows only intended changes; `prashna_ask` verified
   live on BOTH charts; two-door parity confirmed; load baseline recorded; discovery + remedy
   classes show no unresolved tools.** ✅ — RC-01 (both charts), RC-04 (`PROBE_DIFF_v2_0.md`),
   RC-02 (parity, Resolver-narrowed), RC-03 (`W6_LOAD_BASELINE_v1_0.md`), RC-05 (discovery +
   remedy live traces).
4. **Reachability: 100% concepts terminal-healthy (or dispositioned); zero dead ends;
   commissioning contract still holds.** ✅ — RC-04's `CENSUS_v2_0.md` + RC-09's
   `DARK_TABLE_DISPOSITIONS_v3_0.md`; RC-04's expanded drill-crawl (20 live calls + static
   cross-reference) found and fixed 2 dead pointers, honestly named 22 unaudited siblings as
   CR-124 rather than claiming a clean crawl it didn't do.
5. **Git/env: all `res/*`, `w6*`, W6.x-fix branches merged + deleted; worktrees removed; main
   SHA == deployed `amjis-web` AND `amjis-mcp` production SHA; local checkout clean.** ✅ — see
   §5 below for the exact verification.
6. **`CURRENT_STATE` §2 + `SESSION_LOG` updated; campaign status COMPLETE; this report
   independently fact-checked by a second agent against source.** See §6.

## §5 — Git/environment final state

- `git worktree list`: only `main` + `.claude/worktrees/d4b-readiness` (legitimately-active
  D-4b worktree, untouched per §J) + `/private/tmp/badge-honesty-wt` (unrelated pre-existing
  worktree, outside this campaign's scope, left alone).
- Zero `res/*` or `w6*` branches remain, local or on `origin` — confirmed via `git branch -a`
  grep immediately after RC-15's hygiene pass.
- `amjis-web` Cloud Run revision commit-sha label verified to match `main` HEAD at every
  deploy checkpoint this campaign performed (`651c6478`, `844a23a0`, `92113dbe`, `7dcffa91`,
  `ee76ff47`, and the trailing docs-only merges through this seal — `Build & Deploy Web` runs
  on every push to `main` regardless of changed paths, confirmed by inspecting the job list of
  a docs-only-triggered deploy run).
- `amjis-mcp` lags `main` at its last commit that actually touched `platform-mcp/` source
  (`651c6478`, unchanged since — no `platform-mcp` file was touched by any residual closed
  after Wave R-A/R-B) — this is the campaign's own established, correct precedent (the
  originating `FINAL_REPORT.md` itself documents the identical pattern for PRs #696/#698), not
  a stale/mismatched state.
- Local checkout: clean (verified via `git status --porcelain` immediately before this report
  was written), tracking `origin/main` exactly, no uncommitted campaign artifacts remaining
  outside what this seal's own PR carries.

## §6 — Independent fact-check

This report is submitted for independent fact-checking against source per the
`RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md` §H.6/FINAL_REPORT.md precedent this campaign
inherits. Every RC-id above is independently checkable against: `retrieval_residual/STATE.md`
(the ledger), `retrieval_residual/VERIFY_*.md` (per-residual independent verification, one file
per residual, each written by an agent that did not implement the fix it verifies),
`retrieval_residual/RESOLVER_RULINGS.md` (every Resolver disposition with its policy citation),
the numbered PRs cited throughout (#710, #713, #714, #716, #719, plus the docs-only seal PRs),
and the Cloud Run revision history (`gcloud run revisions list --service=amjis-web
--region=asia-south1` / `--service=amjis-mcp`).

## §7 — What remains

**RC-14 only.** `impl/w5-breaking` is not landed. It is not fully rebuilt against current
`main` either (found ~26k lines stale mid-campaign; no rebuild was attempted given D-4b's
continued activity and the risk of building against a moving target). The unblock condition is
exact and named: D-4b verified genuinely quiet (no open D-4b PRs, no active `wave/D-4b/*` work,
checked live, not from a stale ledger reading), at which point the flip must first be rebuilt
against whatever `main` looks like at that time, then landed under the standard deploy-mutex
discipline both campaigns already share.

Two non-blocking recommendations are recorded in `STATE.md` and `RESOLVER_RULINGS.md` for a
future session, neither of which was required to close any residual: (a) wire a production-side
hedge detector into `judgment_flags` so any future recurrence of RC-17's defect class is caught
mechanically rather than requiring another manual live audit; (b) the 22 unaudited
`dualOutput(data)` sibling call sites recorded as CR-124.

---

*End of RESIDUAL_CLOSURE_FINAL_REPORT.md. Campaign status: COMPLETE.*
