---
artifact: PARISHODHANA_REPORT
canonical_id: PARISHODHANA_REPORT_v1_0
version: 1.1
status: CLOSED
created: 2026-07-28
author: PARIŚODHANA Conductor
mode: FULLY AUTONOMOUS per PARISHODHANA_BRIEF_v1_0.md — native-confirmed real-time authorization
  this session (see PARISHODHANA_RECONCILIATION_v1_0.md §5 for the T3-7 disposition).
changelog:
  - "v1.1: filled in §4 (dark-corpus re-measurement, real sampled numbers from PR #865) and §10
    (cleanup, actual result) — both were placeholders in v1.0 pending a still-running background
    agent. No other section changed."
---

# PARIŚODHANA — Close Report

## §1 — Summary

PARIŚODHANA ran Phase A (reconciliation) → Phase B (fix confirmed defects) → Phase C
(institutionalize) end to end, autonomously, per the brief. The campaign's own premise — that the
corpus's ~90 "open" items are wrong in both directions — held: **21 item-groups were already fixed
and undocumented** (register drift, now annotated in place), and **19 item-groups were genuinely
LIVE-OPEN**, two of them newly discovered this session rather than previously documented. 12
Phase-B PRs and 4 Phase-C/follow-up PRs merged to `main`; both `amjis-web` and `amjis-mcp` were
redeployed and independently verified live against production by a dedicated Opus Verifier that
wrote no code. Truth over completion: **one item (`holistic_bundle`'s residual self-call bug)
remains genuinely open after two fix attempts, and is closed here as PARKED-HONEST, not claimed
fixed.**

## §2 — Phase outcomes

**Phase A (reconciliation).** 8 parallel Sonnet probers (A1-A8) verified every ledger Tier-1/
Tier-2 item live against production (chart `482012f1-710e-4a25-994a-93821f5871aa`) or against the
working tree. Output: `PARISHODHANA_RECONCILIATION_v1_0.md` (the disposition table) plus
append-only closure annotations in `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md`,
`ELEVATION_REGISTER_v1_0.md`, `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`, and `ledgers/anchors.jsonl`.
Landed as PR #826.

**Phase B (fix).** Routed from Phase A's LIVE-OPEN items:
- **B1 (cluster fixes, 6 builders + 1 follow-up):** varga-confirmed receipt honesty (CR-2/63/R-38,
  PR #828); `mimamsa_lel_query` query/offset wiring (PR #847); a newly-discovered `ref_*`
  timeout/400 regression on `ref_dasha_systems_get`/`ref_dignity_reference_get`/
  `ref_nakshatra_get` — two distinct root causes, a missing DB-table allowlist entry and an
  unbounded embedding call (PR #830); `leverage_index` wiring into `assess_wealth` (R-10, PR #827);
  `bodha_remedies_get` gemstone-tradition matching + surfacing `maraka_contraindication_verdict`
  onto the default response (R-29/EL-51, PR #829 — this also refuted the reconciliation's
  premise that the verdict field didn't exist; it did, just unreachable); `pact_query` TRIGGER
  x-api-key forwarding + `holistic_bundle` chart_id threading (CR-40/CR-39/CR-14, PR #848); and a
  follow-up (PR #859) applying the same chart_id fix to a second, previously-missed duplicate copy
  of the bundle logic that turned out to be the one actually live.
- **B2 (the reachability triangle, centerpiece):** Opus-designed, Sonnet-implemented. Sub-problem
  1 (discoverability) found the `assess_*`/`judgment_query` → dossier bridge was **already shipped**
  by prior campaigns — only `tool_search` indexing was missing; fixed by PR #833. Sub-problem 2
  (Ω8 floor wiring) reconciled all four copies of the Vidhi registry (canonical TS, generated
  mirror, DB-seed SQL, and DB-seed Python writers — the last of which had silently drifted to
  37/8 vs the canonical 52/11, a latent regression bomb defused in the same PR), added the 2
  missing primitives + widened 2 more, and shipped a new anti-drift CI gate with a hermetic
  induced-drift test (PR #834). Sub-problem 3 (re-measure) ran post-deploy — see §4.
- **B3 (ready-to-ship trivia):** the R-42/EL-58 lapsed-prediction migration (reviewed by the
  migration-guard subagent), a strict-schema-gate comment, stale `defect_001_alert` prose, and the
  `bodha_discoveries_get` deprecated-alias fix (PR #831, #832); 11 confirmed-merged stale branches
  deleted directly. `ka_avadhi.py`, `query_house`, and `reading_notes_get` accretion were correctly
  left PARKED rather than forced past their proper scope.

**Phase C (institutionalize).**
- **C1 — deploy-pipeline parity for `amjis-mcp`** (PR #857): built the `--no-traffic` → smoke →
  promote pattern `amjis-web` already had. Found the `mcp-canary-key` verification secret already
  existed in Secret Manager but the deploying service account lacks `secretmanager.secretAccessor`
  on it — **native action still required**: `gcloud secrets add-iam-policy-binding mcp-canary-key
  --member="serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com"
  --role="roles/secretmanager.secretAccessor" --project=madhav-astrology`. Until granted, the new
  pipeline fails safely closed (old revision keeps serving) rather than silently skipping the gate.
- **C2 — reconciliation cadence detector** (PR #860): a new script cross-references every
  `known_gap: 'CR-N'` citation against live disposition. Its first real dry run found 14 genuine
  divergences, including a brand-new discovery — `cr_status.ts` itself exists in two copies that
  have drifted apart, the same class of bug B2 found and fixed in the Vidhi registry, just never
  caught here. This is the mechanism meant to prevent PARIŚODHANA-scale drift from recurring.
- **C3 — harness certification** (PR #858): executed both sealed graders for real, never modified
  either. `consumption_grader.ts` scored 0/12450 for a diagnosed (not fixed) structural reason —
  it can't credit orchestrating tools that aggregate primitives server-side. The LLM rubric grader
  honestly returned `NOT_LLM_GRADED` (no API keys in this sandbox — a real negative result, not a
  fabricated score). It also found live evidence that the historically-separate 2/13
  naive-routing and ≥12/13 dossier-paging baselines may have converged in current production,
  flagged for a blind re-run before being treated as sealed.

## §3 — Opus Verifier verdict + Conductor re-verification

The Verifier (one Opus agent, wrote no code, four dispositions, no "passed with caveats") ran
against live production post-deploy and returned: **7/10 CONFIRMED** (leverage_index, receipt
honesty, gemstone remedies, lel_query filtering, dossier discoverability, Ω8 floor wiring,
full preserve-list with zero regressions), **1 split** (pact_query CONFIRMED, holistic_bundle
NOT-CONFIRMED), and **1 initially NOT-CONFIRMED** (`ref_*` tools).

The Conductor re-investigated both non-clean findings directly (per rail §6.7 — verify agent
state directly, merge-state ≠ verification-state):
- **`ref_dasha_systems_get`/`ref_nakshatra_get`:** re-tested with the Verifier's exact failing
  parameters immediately after its report — 4/4 clean successes with real content. Disposition
  upgraded to **CONFIRMED on re-verification**; the Verifier's finding is most likely a
  transient/cold-start artifact rather than a standing defect, flagged for light monitoring.
- **`holistic_bundle`:** investigation found the fix in PR #848 had landed in the wrong one of
  two duplicate implementations of the same logic. PR #859 fixed the real, live-serving copy and
  was deployed. Post-fix re-test confirms `chart_id` is now correctly present in every sub-tool
  call (the diagnosed bug is genuinely fixed) — but the same 5 sub-tools still fail, now with a
  different, undiagnosed error. Calling the underlying primitives directly (outside the bundle)
  succeeds cleanly, isolating the residual bug to the bundle's internal self-call path
  specifically. **Disposition: PARKED-HONEST.** Two real defects existed in this one item; one is
  now fixed twice over (both copies), the second remains open. This is disclosed here rather than
  claimed closed — the standing "PARKED-HONEST beats a false close" rule applied to the
  Conductor's own closing judgment, not just to Phase-B builders.

## §4 — Dark-corpus re-measurement

Ran post-deploy (PR #865), against the final head, on both canonical charts, via the unmodified
sealed harness (`evals/omega7/darkcorpus_match.py` + `build_report.py`). **Sampled, not full
coverage — disclosed explicitly:** 5 of 21 replay questions per domain per chart (20 fresh runs
total), not the full 21/21. The served-universe denominator was regenerated live and found
**unchanged** from the stale 2026-07-25 snapshot for chart `482012f1` (12,450 wealth / 12,455
career) — expected, since B1/B2 were serving-layer wiring fixes, not data rebuilds; chart
`1c826d5a`'s denominator (12,203 wealth / 12,207 career) was computed for the first time.

| Domain | Chart | Served | Bright | Dark | Coverage |
|---|---|---|---|---|---|
| wealth | 482012f1 | 12,450 | 89 | 12,361 | 0.71% |
| career | 482012f1 | 12,455 | 125 | 12,330 | 1.00% |
| wealth | 1c826d5a | 12,203 | 80 | 12,123 | 0.66% |
| career | 1c826d5a | 12,207 | 363 | 11,844 | 2.97% |

**A raw comparison to the stale 5.58%/8.47% baseline (full 21/21) is invalid** — bright count
accumulates over however many questions are run, so a 5-question sample mechanically scores lower
than a 21-question one regardless of any underlying change. Re-scoring the *same 5 question IDs*
against the archived pre-deploy transcripts showed a large bright-count drop (wealth 506→89,
career 1,048→125) that could look like a regression — but the agent traced it to a **tool-choice
confound, not a defect**: the archived transcripts called the raw fact-dump tool
(`ganita_chart_facts_get`, whose output the matcher string-matches easily) heavily, while this
session's fresh replay runs answered the same questions via composed/prose tools (`assess_wealth`,
`judgment_query`) that are plausibly richer for a real user but harder for the harness's literal
token-matcher to credit. **No regression or improvement is concluded either way** — that requires
either a full 21/21 run or a substance-level grader, neither of which this session performed. This
honest ambiguity, the sample method, and the full per-question detail are appended to
`capability_map/DARK_CORPUS_REPORT_v1_0.md`.

## §5 — Preserve-list result

Verified live, no regressions found: `chart_snapshot`, `judgment_query` decomposition, special
lagnas, AV (ashtakavarga) gating, a `kala_windows` family call, yoga-firings `grounds_jsonb`
(fully populated on `neecha_bhanga_raja_yoga`), gemstone acharya-review gating, and the
honesty-field vocabulary (`timing_anchored_forced_false`, `varga_confirmed_forced_false` both
fire correctly).

## §6 — Certified harness numbers + baseline reconciliation

See PR #858 / the appended §5 of `SEALED_EVALUATOR_HARNESS_v1_0.md` for full detail. In brief:
`consumption_grader.ts`'s Ω3-scale metric and the R5 LLM-rubric grader measure genuinely different
consumer regimes (client-visible primitive calls vs. an LLM-judged answer battery) and neither
number should be quoted without naming which regime it describes. The historical "2/13 naive vs
≥12/13 dossier-paging" framing may no longer describe two different outcomes in current
production — both regimes now appear to reach the served-family ceiling in one call — but this is
flagged as needing a blind fresh-subagent confirmation before being treated as a formal re-seal,
not asserted as settled fact.

## §7 — Decisions log (`decisions[]`)

| # | Decision | Made by | Rationale |
|---|---|---|---|
| 1 | Proceed with full autonomy as scripted, T3-7 carried forward unresolved | Native (direct real-time confirmation) | Resolves authorization for this run only; does not adjudicate the standing authorization-chain concern |
| 2 | CI-allowlist line-drift fix (PR #849) applied ahead of the Phase-B merge queue | Conductor | A different concurrent campaign's new governance gate broke on an unrelated line-number shift caused by PR #827; fixed the allowlist entry, not the underlying (already-tracked, separately-owned) defect |
| 3 | Native asked to update/merge PR #834 via GitHub UI | Native | This session's `gh` token lacks the `workflow` OAuth scope needed to push branch updates touching `.github/workflows/*.yml`; the web UI isn't scope-limited the same way |
| 4 | R-09 (dosha-linking), CR-19/66/EL-17 (`ph_nimitta.py`), `ka_avadhi.py`, `query_house` build, `bo_upaya.py` remedy-scope widening left PARKED, not fixed | Builders + Conductor (Dvārapāla-style conservative bias) | Root cause lives in L1/L2/L4 python-sidecar writer files, explicitly out of this authorization's serving-/planner-/registry-data-side scope |
| 5 | `holistic_bundle` closed as PARKED-HONEST despite two fix attempts | Conductor | Live re-verification after the second fix still shows the same-shaped failure from a different, undiagnosed cause; disclosed rather than claimed fixed |
| 6 | Secret Manager IAM binding for `mcp-canary-key` not applied by this session | Conductor (Dvārapāla-style) | Real IAM mutation on a production project, outside a documentation/code-fix campaign's authorization; exact command handed to native |

## §8 — Carried-forward open list

AS-7 (bench-side auth divergence, unprobable this session) · CR-85/CR-86 (dead CGM passenger
field / dead edge type, narrow residuals) · T1-11 (gochara health/adverse event class — explicitly
out of scope per brief §4) · chart `1c826d5a` staleness (needs an upstream `ka_gochara_sweep`
re-run — a rebuild, not authorized here) · EL-07 (absence-lint hygiene metric, non-blocking) ·
R-09 (dosha-linking, L2 writer) · CR-19/CR-66/EL-17 (`ph_nimitta.py` first-element array bug, L4
writer — root-caused precisely, not fixed) · `ka_avadhi.py` stale tuple (brief §2 B3 lists it, rail
§6.2's stricter scope excludes it — flagged as an internal brief inconsistency for native
attention) · EL-31/`query_house` (capability-addition, not a bugfix) · R-43/EL-60a
(`reading_notes_get` accretion, still blocked) · `holistic_bundle`'s residual self-call bug (§3) ·
T3-7 (authorization-chain concern, NATIVE-GATED per §5 of the reconciliation doc) · VIDHI-PŪRṆATĀ,
GOCHARA-SWEEP-2.0, KP sub-lord engine, near-miss yoga detection, birth-time rectification, WL-7/
WL-8 native data, and the T3 native-gated rulings — all explicitly out of scope per brief §4,
carried here per its instruction not to silently drop them.

## §9 — Close checklist (brief §7)

1. ✅ All PRs merged (#826-834, #847-849, #857-860 — 16 total); `amjis-mcp`/`amjis-web` deployed
   per §6.5 (merged-main → build → real authenticated verify → 100% traffic on `latestRevision`,
   never a pinned name); production confirmed == main HEAD by direct image-tag inspection.
2. ⏳ Worktree/branch cleanup — see §10.
3. ✅ `PARISHODHANA_RECONCILIATION_v1_0.md` — full disposition table + §6 Phase B/C outcomes.
4. ✅ `PARISHODHANA_REPORT_v1_0.md` — this document.
5. ✅ Source registers annotated in place; `PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md` bumped
   to v1.1, pointing to the reconciliation doc as the authoritative current-state artifact rather
   than duplicating ~90 rows (itself an anti-drift choice).
6. Consumption register → not bumped to ADDRESSED-v2 this session; the registers touched were
   `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` et al., already annotated in place at their
   existing versions per Phase A.

## §10 — Cleanup

All 12 Phase-B/C-follow-up agent worktrees (`.claude/worktrees/agent-*` for every PARIŚODHANA
branch) removed. All 15 corresponding local branches force-deleted after independently confirming
each PR's `MERGED` state via `gh pr view` (squash-merges aren't `git merge-base --is-ancestor`
detectable, so PR state was the correct check, not ancestry). Remote branches for every merged PR
were deleted automatically by GitHub's default merge behavior.

**Residual, disclosed rather than forced:** 3-4 local branches used directly in the shared main
working directory (`parishodhana/phase-a-reconciliation`, `parishodhana/phase-close`,
`parishodhana/dark-corpus-remeasure`, and this closing branch) remain undeleted. This directory is
visibly shared with other concurrently-running sessions/campaigns (SUDDHA-VACA, PARIPRASHNA-BUILD,
and others observed mid-flight throughout this campaign); switching its checked-out branch to
free these names up risked disrupting another session's in-progress state for a purely cosmetic
gain. Left in place rather than force-switched. A stray, uncommitted, superseded draft of root
`CLAUDECODE_BRIEF.md` (belonging to the SUDDHA-VACA campaign, already superseded by their own
later commit on `main`) was found sitting in this shared working tree partway through the session
— per rail §6, it was never staged, committed, or discarded, only worked around.

`git status` on `origin/main` (the authoritative state): clean. Production confirmed == `main`
HEAD by direct Cloud Run image-tag inspection for both `amjis-web` and `amjis-mcp` (§2).
