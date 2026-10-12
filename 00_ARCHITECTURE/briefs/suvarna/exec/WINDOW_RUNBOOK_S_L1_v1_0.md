---
artifact: WINDOW_RUNBOOK_S_L1
version: "1.0"
status: DRAFT-FOR-ANNOUNCEMENT (SS names the window from this file; every approval point is marked A:)
produced_by: Exec Suvarṇa
date: 2026-10-02
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: the window sequence given in messages of 2026-10-02; plan CANONICAL_CHART_REBUILD_PLAN_v1_0.md SL1.8-SL1.11 remain the reasoning
changelog:
  - "1.0 (2026-10-02): first version. Incorporates SS corrections: ONE integration PR for the S-L1 writers; 1221 + 1226 (+ 1222 + 1223, see section 3) merged back to back in W1 as ONE deploy; F-A2 writer + reader pre-window as late as the deploy cycle allows; final regeneration freeze 15 minutes' notice, under one hour."
---

# S-L1 window runbook v1.0

Legend: **A:** = approval point (SS approves; Exec does not proceed without it). **LC** = launch checklist (plan LC-1..LC-5). **Gate** = `run_gated.sh` / gate v2: non-completed main deploy runs = 0 AND planned/running/paused build_runs = 0, read in the same invocation.

## 0. Rules that hold throughout
1. A merge is not a deployment (LC-5): per component (web, mcp, sidecar, pipeline job) read `DEPLOY_SHA` from the deploy log AND the Cloud Run label, `git merge-base --is-ancestor`, `_migrations_applied` per migration. A prerequisite is live only when the component that RUNS it carries it (writers: pipeline job image; served: web/mcp; sidecar endpoints: sidecar).
2. No merge by anyone to main during the window after W1 (a merge starts a deploy, whose gate skip/cancel pattern is documented in `DEPLOY_STATE_AND_GATE_FINDING.md`). SS asks the engine session and Pravāha to hold.
3. Every executor runs through the gate; no executor applies on gate v1. Executors v3 carry gate v2, the gate's sha256 in the plan hash, the launch marker, and an outcome file.
4. Nothing is dispatched on a chart with a planned/running/paused run; dispatch protocol (plan LC.1): `started_at` set within 60 s, never re-dispatch before closing the first run through a supported path.
5. The window is announced to the owner and Pūrṇa (Pūrṇa has no run in flight); no `ka_*` or Pravāha dispatch on the chart during it; `fresh_chart_smoke` (Wednesday 03:00 UTC) does not coincide.
6. Serving restored is verified by the RESOLVER SQL (`orphan_receipts/resolver_verdicts.sql`), never by `asset_freshness` alone.
7. Stop rules: any refusal other than a designed one, any C1-C7 failure, any unexpected build state: STOP, report the exact text to SS.

## 1. PRE-WINDOW (any time before W1)
| # | Step | Evidence | A: |
|---|---|---|---|
| P0 | Independent review of each member lane on its own diff (nothing above LOW); integration branch built (one commit per lane), census/digests regenerated ONCE at the end; ONE short integration review (conflict resolutions, regenerated pins, hooks incl. `tiers.json`, `flip_detector --validate-hooks`). Final regeneration FREEZE: Exec tells SS 15 minutes before; SS asks the engine session and Pravāha to hold merges until the integration PR merges or is abandoned; freeze under one hour. | member table in the PR body (PR, reviewed head, verdict) | A: SS arms the integration PR |
| P1 | Integration PR ("S-L1 writers": #2851 argala+1219 (see section 3 for 1219's digest-spec part), #2892, #2890, #2854+tier-honesty, #2878, #2886, #2883, #2893) merged; deployed; LC-5 per component; `_migrations_applied` has 1219. Before arming AND after any other merge lands before the deploy applies it: re-check the live md5 of `ga_strength` and `ga_condition` `count_sql` against the 1219 guards (if they differ: do not arm, tell SS). | deploy run id, per-component DEPLOY_SHA, pipeline job image tag, resolver SQL BEFORE list | |
| P2 | F-A2 third review; F-A2 built on the integration head (rebase once); its D6 plan dry-run on the rebased hash. F-A2 WRITER + reader commit merged as LATE as the deploy cycle allows before W1 and deployed (inert until the D6 widens the key: any `ga_vargas` build in between fails loudly and rolls back). | review, dry-run output, deploy evidence | A: dry-run approval; A: SS arms |
| P3 | Executors v3 built and delta-reviewed: orphan-receipts v3 (apply version), D6 index executor (independent of S-L1), F-A2 D6 executor, G-IDX executor. 1224 (`chart_grants`) may merge any time. | hashes, delta reviews | A: v3 hashes approved for apply in the window |
| P4 | Held migration PR for W1 ready and reviewed: 1221, 1226, and per section 3 1222 + 1223 (+ 1219's digest-spec part if SS adopts the split). All CLEAN and CI-green on their exact heads, rebased on the post-P2 main. | PR heads, guard verdicts | |

## 2. WINDOW
Window opens when W1's migrations apply. Budget: 1.5-2.5 h typical, 3 h hard (plus the W1 deploy cycle, 25-30 min).

| Step | Action | Verify | A: |
|---|---|---|---|
| W0 | Announce (SS to owner and Pūrṇa). Gate must read 0/0 in the same invocation as W1's arming check. Record resolver SQL BEFORE; orphan-count (5 expected); `0` active runs. | counts | A: SS opens the window |
| W1 | Merge the held migration PRs back to back (1221, 1226, 1222, 1223 [, 1219-part3]): ONE deploy carries all (a later merge cancels the earlier deploy; the migrate job applies first, then images roll). Wait for the deploy to finish; LC-5 per component; verify by PRODUCTION STRUCTURE: `_migrations_applied`, the four `depends_on` arrays + acyclicity, the integrity texts (a29, clause (e)), the active digest specs (82 categories; seven-column key), freshness stale ONLY on the intended assets (ga_structural, ga_vargas, ga_dashas, ga_yoga). | structure queries | A: SS arms the migration PRs |
| W2 | Dispatch `ga_positions` (single-asset, LC-1..LC-5, token approved). Verify by direct DB read: declared receipt proven/fresh after the dispatch start; FORENSIC 7/7 anchors; backend recorded `swieph` in WriterResult.notes (G-EPH pipeline half). | receipt rows, notes | A: stage approval token |
| W3 | Orphan v3: dry run with `--min-build-after` = the dispatch time; verdict diff must be exactly `ga_positions: receipt_not_proven -> RESOLVED`; then apply. | outcome file, resolver diff | A: evidence digest; A: apply |
| W4 | Dispatch `ga_sensitive`; verify (karaka assignments, YAMAKANTAKA rows appear: golden). | counts | |
| W5 | F-A2 D6 apply (key widened with `fact_subject`), then `ga_vargas` watched to completion with C1-C7 (`s_l1_ga_vargas_acceptance_check.sql`: 38,596 total; 7,718 per ayanamsha; 6 INVARIANT; 12 house_lord + 96 ashtakavarga per ayanamsha x varga; 60 D30 per ayanamsha; no seven-column duplicates). | C1-C7 | A: D6 apply; A: continue after C1-C7 |
| W6 | The rest in dependency order, single-asset: ga_nakshatra, ga_panchanga, ga_strength, ga_dashas (heavy), ga_structural (heavy), ga_yoga, ga_vichara, ga_condition, ga_medical, ga_vastu, ga_sade_sati, ga_tajaka, ga_ayurdaya, ga_transit_anchors, ga_sensitive_degree, ga_prashna. `ga_dashas` acceptance: `karaka_roles/s_l1_ga_dashas_roles_acceptance_check.sql` (R1-R3). Check-ins after `ga_dashas` and after `ga_structural`. | per-asset post-run compare | A: ONE batch approval with stop rules; check-ins |
| W7 | Exit: resolver SQL AFTER (list of assets that resolve before vs after; expected 39/13 incl. ga_positions and ga_strength); orphan-count 0 for the stage; flip report from actual output (no unattributed class change); attribution hooks; FORENSIC 7/7 report; the new L1 build id(s). Then G-IDX (rebuild `chart_fact_identity`; `bo_pratijna` never before it). Then census 3. | exit record | A: G-IDX executor hash + apply |

## 3. Which migration stales what (the reason for the W1 grouping)
| migration | what it changes | effect on serving at apply | slot |
|---|---|---|---|
| 1219 ownership rows + count_sql narrowing | `fact_category_ownership` rows; `count_sql` (not in the trigger columns) | none | integration (pre-window) |
| 1219 part 3: `ga_structural` digest spec 81 -> 82 categories | retires the old spec | receipts under the retired spec read `receipt_spec_retired` (`served_generation.ts:265`): `ga_structural` UNRESOLVED from apply until rebuilt | W1 if SS splits it out of 1219 (decision pending); otherwise it degrades `ga_structural` serving from the integration deploy |
| 1221 a29 conjunct | `UPDATE OF integrity_check_sql` (trigger 596) | `ga_structural` freshness stale on every chart | W1 |
| 1222 clause (e) | `UPDATE OF integrity_check_sql` for `ga_vargas` (trigger 596) | `ga_vargas` freshness stale on every chart | W1 |
| 1223 seven-column digest spec | retires the old `ga_vargas` spec | `ga_vargas` receipts read `receipt_spec_retired` | W1 |
| 1226 four edges | `UPDATE OF depends_on` (trigger 596) | `ga_vargas`, `ga_dashas`, `ga_yoga` stale | W1 |
| 1253 two L2 edges | `UPDATE OF depends_on` | `bo_laksana`, `bo_upaya` stale | S-L2 hard gate |
| 1227 node-series index | index only (after the D6) | none | held; D6 first, then merge |

The set of assets whose serving is degraded at W1 is {`ga_structural`, `ga_vargas`, `ga_dashas`, `ga_yoga`}; all four are rebuilt inside the window.

## 4. Abort and rollback
Before W1: nothing to undo. After W1: migrations are append-only guarded; the effect is staleness, cleared by the rebuild; abort = rebuild the four assets (about 37 min typical compute) or restore nothing. After W2/W3: the orphan apply is reversible from `before_images.json`/`reversal.sql`. After W5's D6: reversal per the F-A2 plan.
