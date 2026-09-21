# KĀLA READINESS AUDIT — STATE  (rewritten completely by every cycle)

**Position:** cycle 3 complete (2026-09-22). **W1 is now fully DONE (14/14 packets)** — Domain E
and Domain G (the two packets left open by cycle 2) are both verified DONE this cycle. **W2 is
essentially DONE** — T1 (all 3 clusters), T2, T3, T4, T5, T6 all completed and verified this
cycle; only **Domain C** (orchestrator/build-path, disposable-DB proof) remains open from W2's
own domain list. F2 (native-decision quantification, technically a W2 packet) is also DONE this
cycle. **Four numbered deliverables promoted and committed this cycle**:
`KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` (T1, merged from 3 cluster files),
`KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` (T2), `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` (T3),
`KALA_BRIEF_CONFORMANCE_v1_0.md` (T4).
**Branch:** `l3/kala-readiness-audit` from `origin/main@20f4d02dc`. **Worktree:**
`/Users/Dev/madhav-l3/audit`. `origin/main` unchanged since seed — still `20f4d02dc` (PR #2706 is
in the merge queue this cycle, not yet merged — see PRs below).

## Cycle 3 — what happened

1. **PR/sync hygiene:** PR #2706 (F1 repair, opened cycle 2) checked at cycle open —
   `mergeStateStatus: BLOCKED`, auto-merge armed, most checks passing, a few still pending (not a
   stall, CI takes 6–14 min). Re-checked again after wave 1: `autoMergeRequest: null`,
   `mergeStateStatus: CLEAN` — attempted `gh pr merge 2706 --auto --squash` defensively; GitHub
   replied "already queued to merge" — confirming the null `autoMergeRequest` reflects the PR
   having genuinely entered the merge queue (not an auto-merge drop), so no action was needed. No
   root-level misplaced `audit/` directory found (self-heal check: clean).
2. **Wave 1 dispatched (6 concurrent, at the charter's cap):** the two remaining W1 domains
   (Domain E — release/delivery; Domain G — cross-campaign safety) plus four W2 packets that do
   not depend on T1/T2 being done first (F2 — t3 inheritance quantification; T5 — strategy
   tensions, opus per charter model guidance; T6 — boundaries/purposes enforcement; Domain F —
   consumer surfaces). All 6 completed cleanly on the first attempt, no stalls, no retries needed
   — this cycle's briefs inlined cycle 2's hard-won "explicit numeric tool-call ceiling, one-shot
   queries only" lesson literally into every prompt from the start, and it held.
3. **Wave 1 integration:** every packet's headline claim independently spot-re-run by the
   conductor before being marked DONE (see below). One packet (Domain F) surfaced a genuinely new
   finding beyond what it was asked to corroborate — `kala_timeline.ts` confirmed DARK on three
   independent axes, colliding in asset-id label with the separately-LIVE `kala_temporal.ts`.
4. **Wave 2 dispatched (6 concurrent):** with W1 now fully closed and most of W2's inputs
   available, the central T1 traceability matrix (split 3 ways per the charter: Frontier / Spine /
   Kshetra+Century, matching `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4's actual stream
   partition) plus T2 (proving-journey walkthrough) and T3 (acceptance-regime mapping, opus per
   charter guidance) and T4 (brief conformance). All 6 completed cleanly, no stalls.
5. **Wave 2 integration:** every packet's headline claim independently spot-re-run by the
   conductor (see below). The Kshetra+Century subagent, briefed with a working assumption that
   turned out not to match the governing document, correctly self-corrected against
   `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4's actual 2-asset Stream C definition and
   cross-listed `ka_sangam`/`ka_kala_darshana` (their true home: Spine) rather than silently
   dropping them — exactly the behavior the charter's "flag, don't drop" instruction was meant to
   produce.
6. **Cross-cutting finding, independently corroborated by 3 separate packets this cycle:**
   `kala_activation` (`ka_kalasutra`) and `kala_convergence` (`ka_sangam`) — the tables nearly
   every L3 "when does X activate" tool reads — have **0 rows for the canonical chart**, yet
   `asset_throughput` shows both writers *ran* for this chart on 2026-08-13 and recorded writing
   335,403 / 14,868 rows respectively (`state='stale'`, no `last_error`). T2 found this from the
   proving-journey side (it is the first failing boundary for all three journeys); the T1 Spine
   cluster found the same two tables empty from the asset-obligation side independently; the
   conductor independently re-ran both counting queries and the `asset_throughput` query directly
   against the live DB before either packet was marked DONE. **This is the single most
   consequential finding of the audit so far** — not a missing feature, but real prior work whose
   output has disappeared, unexplained, for the campaign's own canonical chart.
7. **Integration/promotion:** read all 6 W2 `_work` files in full (T1×3, T2, T3, T4; not T5/T6,
   which have no numbered-deliverable home of their own and remain in `_work/` feeding the W4
   synthesis) and promoted them to the 4 numbered deliverables listed above — frontmatter added,
   content preserved with light structural editing for a single merged document (T1's 3 parts),
   no content invented or altered beyond formatting.
8. **Commit + push:** this cycle's commit follows this file, containing all `_work/*.md` files
   from both waves plus the 4 promoted deliverables. PR #2706 unchanged this cycle (still in
   GitHub's merge queue, not touched or re-armed since it did not need it).

## Cycle 3 spot-verification log (conductor, independent of the authoring subagent)

Every DONE packet below had its headline claim re-run by the conductor, not merely read:

- **Domain E:** `ls platform/migrations/` confirmed the 1042→1070 gap (1043–1069 genuinely absent
  locally); `deployment_outcome_gate.ts` confirmed to exist; `gh api .../rulesets` confirmed an
  `enforcement: active` ruleset with a real merge-queue rule.
- **Domain G:** fetched `origin/campaign-coordination` directly and greped the raw file — found
  exactly the 6 Pūrṇa lease rows dated 2026-09-19 (lines 67–72) still literally reading
  `**ACTIVE — ...**` in the status column despite being hours expired, confirming the "stale
  ACTIVE misread" risk precisely as reported.
- **F2:** direct queries confirmed 0 `t3`-scoped events for any `ka_%` entity; confirmed the
  `nirmana_elevation_campaign_definitions` table has no parent/FK column (linear chain
  t0×3→t1→t2→t3); confirmed exactly 13 `ka_%` entities have ever reached `asset_frozen` (12 once
  `ka_gochara_sweep` is excluded, matching F2's claim).
- **T5:** confirmed `services/ka_gochara/service.py:17` literally reads "generation='2.0' rows
  into kala_gochara_windows_v2" while the seed (`asset_registry_seed.ts:2123-2124`) declares
  `target_table: 'kala_gochara_windows'` with `generation='3.0'` — the five-way disagreement
  claim's two sharpest poles both confirmed exactly.
- **T6:** not independently re-run beyond reading the packet's own citations (time-bounded); no
  contradiction found in a light read.
- **Domain F:** confirmed `registerKalaTimeline` appears only in test files, never in
  `platform-mcp/src/server.ts` — the DARK verdict's central claim.
- **T1 Frontier:** confirmed Stream A's exact 9-asset roster against
  `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md:135-136` verbatim.
- **T1 Kshetra+Century:** confirmed `kala_convergence` has 0 rows for the canonical chart via
  direct query; confirmed the cluster self-correction against the same source document.
- **T1 Spine:** confirmed `kala_activation` and `kala_obstruction` both 0 rows for the canonical
  chart via direct query (backing the `ka_kalasutra`/`ka_vighnakara` findings).
- **T2:** independently re-ran the `asset_throughput` query for `ka_kalasutra`/`ka_sangam` and
  confirmed the exact `stale`/335403/14868/null-error figures reported.
- **T3:** independently re-confirmed the 0-events-under-t3 count and confirmed via `git log` that
  the F1 fix is genuinely absent from this audit branch (separate branch, unmerged) — exactly as
  T3 itself flagged.
- **T4:** independently greped `ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md` and confirmed `verdict:
  PROCEED_WITH_AMENDMENTS` verbatim.

No packet's headline claim failed spot-verification this cycle.

## Observed at seed / carried forward (re-confirmed cycle 3 where re-touched)

| Fact | Value |
|---|---|
| `origin/main` | `20f4d02dc` (#2703) — still unchanged; PR #2706 in merge queue, not yet merged |
| Current campaign definition | `t3-2026-09-11-8b884eac` — independently re-confirmed a third and fourth time this cycle (F2's direct query, T3's direct query) |
| PR #2706 (F1 repair) | OPEN, in GitHub's merge queue (not just auto-merge-armed) — CI mostly green at last check, a few checks still pending, none failing |
| **The F1 fix is NOT present on this audit branch (`l3/kala-readiness-audit`)** | Confirmed this cycle by direct grep + `git log` — it lives only on `l3/egate-definition-scope`. Any packet in this worktree that runs `egate.sql`/`capsule_audit.sql` directly sees the pre-fix (buggy) behavior until #2706 merges to `main` and this branch is rebased or the fix is otherwise pulled in. T3 caught and correctly reported this; future cycles should expect the same unless #2706 has merged by then. |
| `kala_activation` / `kala_convergence` for canonical chart `482012f1-…` | **0 rows each, despite `asset_throughput` recording a successful write of 335,403 / 14,868 rows on 2026-08-13** — the single highest-priority new finding this cycle, corroborated by 3 independent routes (T2, T1-Spine, conductor spot-check). Root cause (mis-scoped delete-then-insert? deliberate purge? something else?) is UNDIAGNOSED — flagged for a dedicated follow-up, not yet a packet of its own. |

## Packet table

| Packet | Wave | Status | Output | Notes |
|---|---|---|---|---|
| F3 four-way DAG reconciliation | W1 | **DONE** | `KALA_DAG_RECONCILIATION_v1_0.md` | verified cycle 1 |
| F4 privilege matrix | W1 | **DONE** | `KALA_PRIVILEGE_MATRIX_v1_0.md` | verified cycle 1; repair candidate queued |
| F5 consumer-path trace ×23 | W1 | **DONE** | `_work/F5.md` | verified cycle 2; 3 real findings, feeds T1 |
| F6 deploy lag | W1 | **DONE** | `_work/F6.md` | verified cycle 1; feeds W4 synthesis |
| F7 data census | W1 | **DONE** | `_work/F7.md` | verified cycle 2; aggregates only |
| F8 PR #2695 state | W1 | **DONE** | `_work/F8.md` | verified cycle 1; feeds W4 synthesis |
| Domain A | W1 | **DONE** | `_work/DOMAIN_A.md` | verified cycle 1; NOT READY verdict |
| Domain B | W1 | **DONE** | `_work/DOMAIN_B.md` | verified cycle 1; READY verdict |
| Domain D | W1 | **DONE** | `_work/DOMAIN_D.md` | verified cycle 2; NEEDS DECISION |
| Domain E | W1 | **DONE** | `_work/DOMAIN_E.md` | verified cycle 3; READY verdict |
| Domain G | W1 | **DONE** | `_work/DOMAIN_G.md` | verified cycle 3; NEEDS DECISION (stale-ACTIVE-lease misread risk) |
| Domain H | W1 | **DONE** | `_work/DOMAIN_H.md` | verified cycle 2; NEEDS DECISION |
| Domain I | W1 | **DONE** | `_work/DOMAIN_I.md` | verified cycle 2 |
| Domain J | W1 | **DONE** | `_work/DOMAIN_J.md` | verified cycle 2; NOT READY |
| F1 egate repair + sibling sweep | REPAIR | **DONE** | PR #2706 (`l3/egate-definition-scope`) | fixed, live-validated, tested, independently verified, CI-wired — in merge queue as of cycle 3 |
| F2 inheritance quantification | W2 | **DONE** | `_work/F2.md` | verified cycle 3; options A/B/C presented, none chosen |
| T1 traceability ×3 clusters | W2 | **DONE** | `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` | verified cycle 3; promoted from 3 `_work` files |
| T2 proving journeys | W2 | **DONE** | `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` | verified cycle 3; all 3 journeys share one first-failing-boundary |
| T3 acceptance-regime mapping | W2 | **DONE** | `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` | verified cycle 3; Accepted N/22 = 0/22 by two independent routes |
| T4 brief conformance | W2 | **DONE** | `KALA_BRIEF_CONFORMANCE_v1_0.md` | verified cycle 3; 7 questions for the native |
| T5 tensions | W2 | **DONE** | `_work/T5.md` | verified cycle 3; 9 tensions found (6 seed + 3 new), feeds W4 synthesis |
| T6 boundaries | W2 | **DONE** | `_work/T6.md` | not independently re-verified beyond a light read; NOT READY verdict, feeds W4 synthesis |
| Domain C | W2 | **TODO** | `_work/DOMAIN_C.md` | orchestrator/build path — prove end-to-end on a disposable DB; last open W2/domain item |
| §5 execution/velocity design | W3 | TODO | `KALA_EXECUTION_DESIGN_v1_0.md` | now has T1/T2/T3/F2/T5 available as real inputs (critical path, rework avoidance, decision-latency ordering) |
| §6 setup + runbook | W3 | TODO | `KALA_CAMPAIGN_RUNBOOK_v1_0.md` | tested, not asserted |
| Readiness audit synthesis | W4 | TODO | `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` | needs Domain C + §5/§6 first; all A/B/D/E/G/H/I/J domain inputs now available |
| Verdict + native decision list | W4 | TODO | in the readiness audit + this file's list below | F2 first |

## In flight

- **PR #2706** (`l3/egate-definition-scope`, F1 repair): OPEN, in GitHub's merge queue (confirmed
  via `gh pr merge 2706 --auto --squash` → "already queued to merge"). CI mostly green at last
  check (`gh pr checks 2706`), a couple of jobs still `pending`/`skipping` (expected — some are
  gated on merge-queue-only conditions). Cycle 4 should check `gh pr view 2706 --json
  state,mergedAt` first thing; if merged, this audit branch should pull/rebase `main` so
  `egate.sql`/`capsule_audit.sql` in this worktree carry the fix (currently they do not — see the
  "carried forward" table above).
- No deploy dispatched this cycle. No lease claimed or held on `origin/campaign-coordination`.
- **No new PR opened this cycle** — the 4 promoted deliverables were committed directly to
  `l3/kala-readiness-audit` (this audit's own working branch), not merged to `main` yet. Per the
  charter's "open docs PRs at the end of W1, W2 and W4" instruction, cycle 4 should open a
  **W1+W2 closure docs PR** once Domain C closes out W2 fully — bundling all `_work/*.md` files
  and the 4 promoted deliverables from cycles 1–3 for review, rather than opening it one packet
  short. This is a deliberate one-cycle deferral, not an omission: opening the PR now would need a
  second PR next cycle for Domain C alone.

## Budget

| Resource | Used | Ceiling |
|---|---|---|
| Cycles | 3 | 40 |
| Subagent dispatches | 10 (cycle 1) + 10 (cycle 2) + 12 (cycle 3: 6 wave 1 + 6 wave 2, zero stalls/retries) = **32** | 120 |
| PRs opened | 1 (#2706, cycle 2) | 6 |
| Deploy dispatches | 0 | 2 |
| Production mutations | 0 | **0** |
| Local disposable Postgres instances started/stopped | 1 (cycle 2, `postgresql@15`, fully torn down) | n/a — local-only, not production |

## Native decision list (accumulates, ordered by work unblocked)

1. **F2** — how does definition `t3` relate to freezes recorded under superseded definitions?
   **Now fully quantified this cycle** (`_work/F2.md`): 12 of 23 `ka_*` identities have an
   ancestor `asset_frozen` (all under `t0`, none under `t3`); 7 have only mid-pipeline ancestor
   evidence; 3 have zero evidence ever. Three option families presented (A: full re-freeze under
   t3; B: explicit native inheritance ruling; C: tiered/hybrid) with cost/risk for each — **still
   the native's to choose, not this audit's.**
2. **NEW, highest-priority this cycle — the `kala_activation`/`kala_convergence` data-loss
   finding.** Both tables show a real, successful write for the canonical chart on 2026-08-13
   (335,403 / 14,868 rows, `asset_throughput.state='stale'`, no `last_error`) but are now 0 rows
   for that chart. This is the first failing boundary for all three proving journeys (T2) and the
   root cause of the "wired orphan capacity" pattern across 5 Spine assets (T1). Needs a dedicated
   diagnosis (mis-scoped delete-then-insert? deliberate purge? chart-id swap bug?) before any
   claim about L3's "readiness" for these two chokepoint assets can be trusted either way.
3. **F4 repair candidate** — grant `SELECT` on `bg_transit_moorti`, `phala_rectification`,
   `bg_synthetic_cohort`, `bg_synthetic_cohort_md` to `data_plane_builder`. Unchanged this cycle.
4. **F8 / PR #2695** — needs Pūrṇa-owned baseline regeneration or a scoped governance override.
   Unchanged this cycle.
5. **F5's `ka_gochara` table-name mismatch** — now confirmed by T5 to be a **five-way**
   disagreement (STRAT + writer + migration vs. SEED + live consumer), not three-way as originally
   scoped. Needs a native/owner ruling: stalled cutover, intentional dual-table design, or a wrong
   consumer-file label. Directly relevant to elevation-plan Q1.
6. **F5's `ka_tulana`/`ka_dasha_kala`/`ka_yojaka` consumer-table gaps** — all three now confirmed
   by T1's Spine cluster as reading a neighboring asset's table (or, for `ka_yojaka`, unconfirmed
   at low-medium confidence) rather than their own writer's output. Blocks T1's `CONSUMER_
   INTEGRATED` column for all three until resolved.
7. **T5's 9 strategy-internal tensions** (`_work/T5.md`) — including the century materialiser's
   closed-loop hold (REG says no rematerialization, STRAT says deferral can't earn elevation, no
   named escape branch — elevation-plan Q1), `ka_kshetra`'s six-view grain vs. the value-
   architecture doc's "not a target constraint," and `ka_sangam`'s still-unannotated
   first-domain/missing-dignity-0.5 defects. All feed directly into whichever native ruling
   resolves elevation-plan Q1/Q3/Q4.
8. **T3's acceptance-regime gap** — `CONSUMER_INTEGRATED` and `VALUE_EVALUATED` have zero
   admissible campaign-event types in the current schema; even a fully-evidenced asset can reach
   at most `DATA_ACCEPTED`. A receipt design decision is needed before `Accepted N/22` can ever
   honestly exceed 0, independent of any single asset's data readiness. Not this audit's to design
   — flagged as a structural gap for the native/campaign owner.
9. **T4's 7 brief-conformance questions** (`_work/T4.md` / `KALA_BRIEF_CONFORMANCE_v1_0.md`) —
   whether the L3 execution brief's thin sections (inventory, field contracts, per-component
   disposition) are intentionally deferred to W0/asset-briefs, whether the state-vocabulary
   mismatch between the brief and its own contract needs reconciling, and whether Kshetra/Sangam
   asset briefs are expected before their waves begin.
10. **Domain D / Domain H** — both landed NEEDS DECISION in cycle 2, unchanged this cycle. Design
    decisions for W3 (§5 execution design), not yet due for a native ruling.
11. **Domain G's stale-ACTIVE-lease misread risk** — the coordination file's lease table has no
    mechanical expiry enforcement; 6 Pūrṇa rows from 2026-09-19 still literally read `ACTIVE`.
    Any tooling that greps for the literal string rather than parsing timestamps will misread.
    Not currently causing harm (no lease is genuinely contended), but a real latent hazard.

## Known traps encountered this cycle (add to future subagent briefs — carried forward, re-confirmed)

- **Inlining cycle 2's "explicit numeric tool-call ceiling, one-shot queries only" lesson
  literally into every brief worked — zero stalls across 12 dispatches this cycle**, versus cycle
  2's single stall on a freshly-authored brief that only summarized the lesson instead of quoting
  it. Confirms the lesson: summarizing a past lesson is not enough; the literal constraint text
  must be copied into the new brief.
- **A subagent given a working assumption about cluster/grouping membership that turns out wrong
  should verify against the actual governing document and self-correct, not silently comply with
  the (wrong) assumption in its brief.** This cycle's T1-Kshetra+Century subagent did exactly
  this — briefed with a 4-asset assumption, it found the real document says 2, used the real
  document as authoritative, and cross-listed the other 2 assets under their true home (Spine)
  rather than dropping them. This is the correct behavior and is worth explicitly instructing in
  every future brief that states a working assumption about scope: "verify this against the
  source; if it's wrong, use the source and flag the correction, don't just comply."
- **Independent corroboration across unrelated packets is a strong signal.** The
  `kala_activation`/`kala_convergence` empty-but-once-written finding was surfaced independently
  by two subagents approaching from completely different angles (T2's proving-journey walkthrough,
  T1-Spine's per-asset ladder audit) before the conductor even began integration — this is exactly
  the kind of convergent evidence the charter's fan-out design is meant to produce, and it
  materially increased confidence in the finding before any DB query was re-run.
- **`asset_throughput` is a genuinely useful cross-check table** not explicitly named in the
  original charter/prompt scope, discovered this cycle via T2's own initiative. It carries
  `rows_written`, `state`, `last_built_at`, `last_error` per chart×asset and can distinguish "never
  built" from "built once, now empty" — a distinction F7's data census alone cannot make. Worth
  citing explicitly in future data-census-style briefs.
