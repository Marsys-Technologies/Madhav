# KĀLA READINESS AUDIT — STATE  (rewritten completely by every cycle)

**Position:** cycle 6 complete (2026-09-22). **W1 and W2 are now fully DONE.** Domain C
(orchestrator/build-path, disposable-DB proof — the last open W2/domain item) was integrated this
cycle from cycle 4's orphaned-but-uncommitted output, independently spot-verified, and promoted.
**W3 is now fully DONE** — both `KALA_EXECUTION_DESIGN_v1_0.md` (§5) and
`KALA_CAMPAIGN_RUNBOOK_v1_0.md` (§6) were dispatched in the foreground this cycle (per the
standing law) and promoted after conductor verification. `KALA_DATA_CENSUS_v1_0.md` (deliverable
#8, from F7) was also promoted this cycle — a straightforward promotion, not new work.
**Only W4 remains: the readiness-audit synthesis (deliverable #5), the GO/GO-WITH-
CONDITIONS/NO-GO verdict (#11), and the native decision list (#12).** 9 of 12 numbered
deliverables now exist as promoted files; the remaining 3 all belong to W4.

**Branch:** `l3/kala-readiness-audit`. **Worktree:** `/Users/Dev/madhav-l3/audit`. **This cycle
merged `origin/main` into the branch** (`git merge origin/main --no-edit`, clean, no conflicts) —
`origin/main` had advanced to `9b3c3b219` (PR #2706, the F1 repair, merged 2026-09-21T20:22:55Z)
since this branch was seeded at `20f4d02dc`. **The F1 fix (`egate.sql`/`capsule_audit.sql`
definition-scoping) is now genuinely present on this branch** — confirmed by
`git merge-base --is-ancestor 9b3c3b219 HEAD` → true, and by direct grep (4
`definition_revision` refs in `egate.sql`). Prior cycles' notes that the fix was absent are now
stale; do not re-flag it as missing.

**Numbering note for future cycles:** the supervisor's cycle counter (this cycle = "6") does not
match this file's own cycle count (this is only the 4th cycle to actually close with a commit —
cycles 1, 2, 3, and now this one; a crashed "cycle 4" attempt left orphaned files but no commit,
and the strategic session's law-update commit `122e5357e` was not itself a numbered audit cycle).
This file uses the **supervisor's number** (6) as authoritative for the Position line, per the
charter's "rewrite completely... with its own cycle number" instruction — do not try to reconcile
the two counters retroactively; just keep using whatever number the supervisor gives each cycle.

## Cycle 6 — what happened

1. **PR/sync hygiene:** confirmed PR #2706 (F1 repair) is `MERGED` (`mergedAt:
   2026-09-21T20:22:55Z`) and `origin/main` head is now `9b3c3b219`. **Discovered this audit
   branch had NOT yet pulled that fix** (`git merge-base --is-ancestor 9b3c3b219 HEAD` → false at
   cycle start, despite the commit appearing in `git log --all` — that was a chronological
   listing artifact, not topological ancestry). Fixed via `git merge origin/main --no-edit`
   (clean 4-file merge: `.github/workflows/ci.yml`, `capsule_audit.sql`, `egate.sql`, the new
   `nirmana_egate_definition_scope.db.test.ts`). No root-level misplaced `audit/` directory found
   (self-heal check: clean). No open PR existed yet for `l3/kala-readiness-audit` itself — opened
   one this cycle (see step 5).
2. **Integrated cycle 4's orphaned outputs** (present on disk, committed by the strategic session
   in `122e5357e`, but never spot-verified or promoted): `_work/DOMAIN_C.md` and
   `_work/DATA_LOSS_DIAGNOSIS.md`. **Conductor independently re-ran, before promoting either:**
   `build_runs` state distribution (`failed|429, completed|369, stopped|19` — exact match), the
   `ka_*` writer registration count (`discover_all()` → 123 total, 22 `ka_*` — exact match), the
   FK constraint type on both `kala_activation_signal_id_fkey`/`kala_convergence_signal_id_fkey`
   (`confdeltype='c'` = CASCADE — exact match), and the canonical chart's `kala_activation`/
   `kala_convergence` row counts (0/0 — exact match). All four independent checks passed; both
   packets marked DONE. Domain C's verdict: **READY** (orchestrator/build-path mechanics — advisory
   lock, fleet cap, `build_runs` lifecycle, the two preflight verify functions, writer
   registration, substep-plan partial-completion including the SATYA-DĪPA fix — proven live on a
   disposable Postgres 15 instance plus 141 passing unit tests). `DATA_LOSS_DIAGNOSIS.md`'s
   verdict: **ROOT CAUSE FULLY IDENTIFIED** — a deliberate `ON DELETE CASCADE` from `kala_*.signal_id`
   to `bodha_msr_signals.signal_id` (migration `403_kala_signal_fk_cascade.sql`), which fires
   whenever L2 Bodha rebuilds MSR signals (minting fresh `signal_id` UUIDs, per §N.3) after an L3
   build — proven with a decisive join on a second chart (`cb73cd3d`) showing 100% of surviving
   rows resolve only to the *original* signal generation, 0% to the rebuilt one.
3. **W3 dispatched in the foreground** (per the standing law — both `Agent` calls in one message,
   `run_in_background: false`): the §5 execution/velocity design and the §6 environment setup.
   Both completed cleanly on the first attempt, no stalls, no retries. **Conductor
   spot-verification, before promoting either:** re-ran `grep -c definition_revision egate.sql`
   (→4, matches), re-ran the F1-sibling sweep greps for `capsule_audit.sql`/`nrec`/
   `l1_integrity_check_dry_run.sql` (all matched the runbook's claims exactly), and — most
   substantially — **executed the new `kala_readiness_query_v2.sql` artifact live against the
   read-only replica from scratch**, independently reproducing the exact claimed output: 22 rows
   `NOT_READY-BLOCKED-ANCESTORS` + 1 row (`ka_muhurta_seva`) `NOT_READY-BLOCKED-NO-ROUTE`, zero
   `READY`-shaped rows, and the verbatim `BUILD-PROTECTED`/`PARISHKARA MR-06` guard-refusal error
   text for `ka_gochara_v3_century_materialize`. This last item is a **genuinely new finding**
   surfaced by this cycle's own verification pass, not merely inherited: at least one L3 asset
   (the century materialiser) has a live, currently-firing build-time protection guard refusing a
   DELETE against `kala_gochara_windows` rows for the canonical chart, citing a named
   native-decision-required rationale — cross-references T5 Tension 1 (the five-way `ka_gochara`
   table-identity dispute) and elevation-plan Q1 (century materialisation). Both packets promoted
   to their numbered deliverables (`KALA_EXECUTION_DESIGN_v1_0.md`, `KALA_CAMPAIGN_RUNBOOK_v1_0.md`).
4. **`KALA_DATA_CENSUS_v1_0.md` promoted from `_work/F7.md`** (deliverable #8) — a straightforward
   frontmatter-and-copy promotion of already-DONE cycle-2 work; no new content, no re-verification
   needed beyond what cycle 2/3 already performed.
5. **Commit + push:** one commit this cycle (`2159ca021`) containing the merge of `origin/main`
   plus the three new promoted deliverables plus the new `_work/artifacts/kala_readiness_query_v2.sql`.
6. **Opened the deferred W1+W2(+W3) closure docs PR** — `#2707`, base `main`, head
   `l3/kala-readiness-audit`. Cycle 3 had deliberately deferred this PR pending Domain C's close;
   Domain C closed this cycle, so the PR was opened now, bundling all of cycles 1–6's `_work/*.md`
   files and all 9 promoted numbered deliverables. Auto-merge armed
   (`gh pr merge 2707 --squash --auto` → GitHub redirected it into the merge-queue path since
   "the merge strategy for main is set by the merge queue"; confirmed via `gh pr view 2707`:
   `autoMergeRequest` is set, `mergeStateStatus: BLOCKED` pending checks — this is the expected
   "enqueued, not yet clear" state per prior cycles' own precedent with #2706, not a stall).

## Cycle 6 spot-verification log (conductor, independent of the authoring subagent)

- **Domain C (promoted from cycle 4's orphan):** `build_runs` state distribution, `ka_*` writer
  count (22/123) — both re-run live, exact match.
- **DATA_LOSS_DIAGNOSIS (promoted from cycle 4's orphan):** FK `confdeltype='c'` on both
  `kala_activation_signal_id_fkey`/`kala_convergence_signal_id_fkey`, canonical-chart row counts
  (0/0) — both re-run live, exact match.
- **§6 runbook (F1 sibling sweep):** `grep -c definition_revision platform/scripts/nirmana/egate.sql`
  → 4 (matches); `grep -n "F1-class fix" platform/scripts/nirmana/capsule_audit.sql` → present at
  line 29 (matches); `grep -rn nirmana_elevation_campaign_events nrec l1_integrity_check_dry_run.sql`
  → zero matches in both (matches the runbook's "not applicable" verdict).
- **§6 runbook (readiness query v2):** executed the actual SQL file
  (`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/_work/artifacts/kala_readiness_query_v2.sql`)
  live against the read-only replica, from a fresh conductor invocation (not copy-pasted from the
  subagent's transcript) — reproduced the exact 23-row output distribution and the verbatim
  `BUILD-PROTECTED`/`PARISHKARA MR-06` error text for `ka_gochara_v3_century_materialize`.
- **§5 execution design:** not independently re-run beyond citation-tracing (it is a synthesis
  document over already-verified prior packets, not a new empirical claim) — spot-checked that its
  T0–T5 tier lists and depends_on sets match T5.md's own tables (light read, no contradiction
  found).
- **PR merge state:** `git merge-base --is-ancestor 9b3c3b219 HEAD` on this branch → true, confirmed
  after the merge (was false before it).

No packet's headline claim failed spot-verification this cycle.

## Observed at seed / carried forward (re-confirmed cycle 6 where re-touched)

| Fact | Value |
|---|---|
| `origin/main` | `9b3c3b219` (#2706, F1 repair) as of this cycle's fetch — moved from the prior `20f4d02dc` |
| Current campaign definition | `t3-2026-09-11-8b884eac` — unchanged, re-confirmed via this cycle's own live readiness-query run (all 23 rows carry this definition_revision) |
| PR #2706 (F1 repair) | **MERGED** 2026-09-21T20:22:55Z. Now genuinely present on this audit branch (merged in this cycle). |
| PR #2707 (this audit's own W1+W2+W3 closure docs PR) | **OPEN**, auto-merge armed (queued via merge-queue path), `mergeStateStatus: BLOCKED` pending checks — not a stall, matches #2706's own prior behavior at this stage. |
| `kala_activation` / `kala_convergence` for canonical chart `482012f1-…` | **0 rows each — root cause now FULLY DIAGNOSED, not merely observed** (see `_work/DATA_LOSS_DIAGNOSIS.md`, promoted this cycle after independent re-verification): `ON DELETE CASCADE` from `signal_id` to `bodha_msr_signals.signal_id` (migration 403), fired by an L2 `bo_laksana`/`bo_laksana_rerank` rebuild (2026-09-08/09-11) that postdated the L3 build (2026-08-13) by nearly a month, deleting 100% of the referenced signal rows. **This is reproducible and will recur** on any chart whenever L2 rebuilds after L3, unless L3 is rebuilt in lockstep — nothing currently enforces that. Also affects `kala_bhavishya`, `kala_darshana`, `kala_obstruction` per the same migration (not independently re-verified for those three tables this cycle — flagged, not re-derived). |
| `ka_gochara_v3_century_materialize` build-time guard (NEW this cycle) | Currently `state='error'` for the canonical chart with a live `BUILD-PROTECTED` PL/pgSQL guard refusing a DELETE against `kala_gochara_windows` rows, citing "PARISHKARA MR-06 protection rationale" and requiring a native decision to override. Surfaced by the cycle-6 conductor's own live re-run of the new readiness query — not previously documented in this audit. Feeds T5 Tension 1 and elevation-plan Q1. |

## Packet table

| Packet | Wave | Status | Output | Notes |
|---|---|---|---|---|
| F3 four-way DAG reconciliation | W1 | **DONE** | `KALA_DAG_RECONCILIATION_v1_0.md` | verified cycle 1 |
| F4 privilege matrix | W1 | **DONE** | `KALA_PRIVILEGE_MATRIX_v1_0.md` | verified cycle 1; repair candidate queued |
| F5 consumer-path trace ×23 | W1 | **DONE** | `_work/F5.md` | verified cycle 2; 3 real findings, feeds T1 |
| F6 deploy lag | W1 | **DONE** | `_work/F6.md` | verified cycle 1; feeds W4 synthesis |
| F7 data census | W1 | **DONE** | `KALA_DATA_CENSUS_v1_0.md` | verified cycle 2; **promoted cycle 6** |
| F8 PR #2695 state | W1 | **DONE** | `_work/F8.md` | verified cycle 1; feeds W4 synthesis — re-confirm PR #2695 state next cycle before citing as unchanged |
| Domain A | W1 | **DONE** | `_work/DOMAIN_A.md` | verified cycle 1; NOT READY verdict |
| Domain B | W1 | **DONE** | `_work/DOMAIN_B.md` | verified cycle 1; READY verdict |
| Domain C | W2 | **DONE** | `_work/DOMAIN_C.md` | produced cycle 4 (orphaned, uncommitted), independently spot-verified and promoted cycle 6; READY verdict |
| Domain D | W1 | **DONE** | `_work/DOMAIN_D.md` | verified cycle 2; NEEDS DECISION |
| Domain E | W1 | **DONE** | `_work/DOMAIN_E.md` | verified cycle 3; READY verdict |
| Domain G | W1 | **DONE** | `_work/DOMAIN_G.md` | verified cycle 3; NEEDS DECISION (stale-ACTIVE-lease misread risk) |
| Domain H | W1 | **DONE** | `_work/DOMAIN_H.md` | verified cycle 2; NEEDS DECISION |
| Domain I | W1 | **DONE** | `_work/DOMAIN_I.md` | verified cycle 2 |
| Domain J | W1 | **DONE** | `_work/DOMAIN_J.md` | verified cycle 2; NOT READY |
| F1 egate repair + sibling sweep | REPAIR | **DONE** | PR #2706 (merged) + this cycle's runbook sibling-sweep confirmation | fixed, live-validated, tested, independently verified, CI-wired, merged, and now present on this audit branch |
| F2 inheritance quantification | W2 | **DONE** | `_work/F2.md` | verified cycle 3; options A/B/C presented, none chosen; costs quantified further in `KALA_EXECUTION_DESIGN_v1_0.md` §4 |
| T1 traceability ×3 clusters | W2 | **DONE** | `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` | verified cycle 3 |
| T2 proving journeys | W2 | **DONE** | `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` | verified cycle 3 |
| T3 acceptance-regime mapping | W2 | **DONE** | `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` | verified cycle 3 |
| T4 brief conformance | W2 | **DONE** | `KALA_BRIEF_CONFORMANCE_v1_0.md` | verified cycle 3 |
| T5 tensions | W2 | **DONE** | `_work/T5.md` | verified cycle 3; 9 tensions, feeds W4 synthesis |
| T6 boundaries | W2 | **DONE** | `_work/T6.md` | not independently re-verified beyond a light read; NOT READY verdict, feeds W4 synthesis |
| §5 execution/velocity design | W3 | **DONE** | `KALA_EXECUTION_DESIGN_v1_0.md` | produced + spot-verified cycle 6 |
| §6 setup + runbook | W3 | **DONE** | `KALA_CAMPAIGN_RUNBOOK_v1_0.md` | produced + spot-verified cycle 6; new v2 readiness-query artifact tested live |
| Readiness audit synthesis | W4 | **TODO** | `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` | all inputs now available (domains A/B/C/D/E/G/H/I/J done, F1-F8 done) — this is the next cycle's main task |
| Verdict + native decision list | W4 | **TODO** | in the readiness audit + this file's list below | F2 first; depends on the readiness audit above |

## In flight

- **PR #2706** (F1 repair): MERGED. No further action needed.
- **PR #2707** (this cycle's W1+W2+W3 closure docs PR): OPEN, auto-merge armed via merge-queue
  path, `mergeStateStatus: BLOCKED` pending checks at time of writing. Next cycle should check
  `gh pr view 2707 --json state,mergedAt` first thing; if merged, no action; if checks are still
  pending after a reasonable interval, re-check via `gh pr checks 2707` and re-arm auto-merge only
  if it was dropped (do not re-run `gh pr merge` speculatively if it's already queued).
- No deploy dispatched this cycle. No lease claimed or held on `origin/campaign-coordination`.
- **Next cycle's task is squarely W4**: dispatch (in the foreground, per the standing law) the
  readiness-audit synthesis over the now-complete domain/finding set, then the GO/GO-WITH-
  CONDITIONS/NO-GO verdict (separately for strategy implementability and environment readiness)
  and the native decision list, then a final W4 docs PR, then `AUDIT_DONE`. Given the volume of
  source material (10 domains + 8 findings + 6 top-down packets + 2 design docs), consider
  splitting W4 into two dispatches: (a) the environment readiness audit synthesis itself
  (mechanical compilation with severity/owner columns, sonnet-appropriate), and (b) the verdict +
  decision list (needs full-context judgment across every packet — use opus per the charter's own
  model guidance for "the final verdict").

## Budget

| Resource | Used | Ceiling |
|---|---|---|
| Cycles (supervisor numbering) | 6 (of which 4 have actually closed with a commit: 1, 2, 3, 6 — see "Numbering note" above) | 40 |
| Subagent dispatches | 32 (cycles 1-3) + 2 (cycle 6: W3, both foreground) = **34** | 120 |
| PRs opened | 2 (#2706 cycle 2, now merged; #2707 cycle 6) | 6 |
| Deploy dispatches | 0 | 2 |
| Production mutations | 0 | **0** |
| Local disposable Postgres instances started/stopped | 1 (cycle 2) + 1 (cycle 4, Domain C's advisory-lock proof, promoted cycle 6) = 2, both fully torn down | n/a — local-only, not production |

## Native decision list (accumulates, ordered by work unblocked)

1. **F2** — how does definition `t3` relate to freezes recorded under superseded definitions?
   Fully quantified (`_work/F2.md`, cost/risk further detailed in `KALA_EXECUTION_DESIGN_v1_0.md`
   §4): 12 of 23 `ka_*` identities have an ancestor `asset_frozen` (all under `t0`, none under
   `t3`); 7 have only mid-pipeline ancestor evidence; 3 have zero evidence ever. Five option
   families now on the table (A full re-freeze, B inheritance ruling, C1/C2/C3 tiered variants)
   with cost/risk for each — **still the native's to choose.**
2. **The `kala_activation`/`kala_convergence` data-loss finding — now FULLY DIAGNOSED, decision
   still needed.** Root cause: `ON DELETE CASCADE` from `signal_id` to `bodha_msr_signals` (migration
   403), fired by an out-of-lockstep L2 rebuild. Three remediation directions proposed in the
   diagnosis (auto-rebuild-on-upstream-change; replace CASCADE with explicit reconciliation; add a
   "stale AND empty" alert gate) — none chosen. `KALA_EXECUTION_DESIGN_v1_0.md` §3 additionally
   specifies what any interim rebuild of the five CASCADE-linked assets must do to avoid
   reproducing this exact loss (sequence after / gate on the latest `bo_laksana` rebuild time).
3. **NEW this cycle — `ka_gochara_v3_century_materialize`'s live BUILD-PROTECTED guard.** A
   PL/pgSQL guard (`build_gen3_gochara_guard_row()`) is currently refusing a DELETE against
   `kala_gochara_windows` rows for the canonical chart, citing "PARISHKARA MR-06 protection
   rationale" and requiring `app.allow_protected_sweep_rewrite=on` plus a native decision to
   override. This directly intersects T5 Tension 1 (five-way `ka_gochara` table-identity dispute)
   and elevation-plan Q1 (full century materialisation vs. compact substrate) — needs a native
   ruling on whether/how this asset should ever be rebuilt under the current design.
4. **F4 repair candidate** — grant `SELECT` on `bg_transit_moorti`, `phala_rectification`,
   `bg_synthetic_cohort`, `bg_synthetic_cohort_md` to `data_plane_builder`. Unchanged.
5. **F8 / PR #2695** — needs Pūrṇa-owned baseline regeneration or a scoped governance override.
   Not re-checked this cycle — re-confirm its state before the W4 synthesis cites it as unchanged.
6. **F5's `ka_gochara` table-name mismatch** — confirmed by T5 as a five-way disagreement. Needs a
   native/owner ruling: stalled cutover, intentional dual-table design, or a wrong consumer-file
   label. Directly relevant to elevation-plan Q1 and item 3 above.
7. **F5's `ka_tulana`/`ka_dasha_kala`/`ka_yojaka` consumer-table gaps** — confirmed by T1's Spine
   cluster. Blocks T1's `CONSUMER_INTEGRATED` column for all three until resolved.
8. **T5's 9 strategy-internal tensions** (`_work/T5.md`) — unchanged this cycle; feed Q1/Q3/Q4.
9. **T3's acceptance-regime gap** — `CONSUMER_INTEGRATED` and `VALUE_EVALUATED` have zero
   admissible campaign-event types; even a fully-evidenced asset can reach at most `DATA_ACCEPTED`.
   `KALA_CAMPAIGN_RUNBOOK_v1_0.md` §8 specifies how a ledger should honestly render this gap
   (`NO_ADMISSIBLE_EVENT_TYPE`, not a blank cell) but does not design the receipt itself — still a
   structural gap for the native/campaign owner to close.
10. **T4's 7 brief-conformance questions** — unchanged this cycle.
11. **Domain D / Domain H** — both NEEDS DECISION, unchanged this cycle.
12. **Domain G's stale-ACTIVE-lease misread risk** — unchanged this cycle; `KALA_CAMPAIGN_RUNBOOK_v1_0.md`
    §6 restates the "compute expiry from wall-clock, never string-match `ACTIVE`" rule for every
    future L3 conductor.
13. **`KALA_EXECUTION_DESIGN_v1_0.md`'s decision-latency queue (§5)** — a fuller ordered ruling
    queue (F2 first, then Q4, Q1, Q8, Q3, Q2, Q7, Q6, Q5, then T4/T5 residuals) is now available as
    a single reference; supersedes ad hoc prioritization of the elevation-plan's Q1-Q8 questions
    for future cycles.

## Known traps encountered this cycle (add to future subagent briefs — carried forward, re-confirmed)

- **`git log --all` lists commits chronologically by author/commit date across ALL branches, not
  topologically by ancestry to your current HEAD.** A commit appearing "between" two of your own
  commits in that listing does NOT mean it is an ancestor of your branch. This cycle opened
  believing (from a stale AUDIT_STATE.md note plus a misleading `git log --all` read) that the F1
  fix might already be present; `git merge-base --is-ancestor <sha> HEAD` is the correct check and
  should be the default way to verify "is this fix on my branch" going forward, not a `git log`
  read of any kind.
- **`cd` in a Bash tool call persists across tool calls in the same session** (the tool description
  says so explicitly, and this cycle was bitten by it: a `cd platform/python-sidecar && python3 -c
  ...` command inside a W3 subagent-verification step left the CONDUCTOR's own shell inside that
  subdirectory for several subsequent commands, causing spurious "No such file or directory"
  errors on paths that were in fact correct relative to the repo root). **Always `cd
  /Users/Dev/madhav-l3/audit` (absolute) at the start of any command block that follows one which
  used a bare relative `cd`**, or avoid bare `cd` entirely and prefix the one command that needs a
  different directory with `(cd dir && cmd)` in a subshell instead.
- **A subagent's markdown output can trigger a harness false-positive instruction-pattern scan**
  when it discusses configuration files by name (this cycle's §6 runbook packet, which discusses
  `.claude/settings.json` as part of describing a session-persistence hazard, triggered a
  "settings-json"-pattern match and had its `<`/`>` characters neutralized in the returned text).
  This is a benign scanner false-positive on documentation-about-configuration, not an actual
  prompt-injection attempt — treat the content as ordinary research findings, verify its claims
  independently as normal, and do not treat the warning itself as a finding to escalate unless the
  content genuinely contains embedded instructions (it did not, here).
- **Independent corroboration across unrelated packets remains a strong signal** — carried forward
  from cycle 3, re-confirmed this cycle by Domain C and DATA_LOSS_DIAGNOSIS's mutually-reinforcing
  (but independently produced) accounts of the same `kala_activation`/`kala_convergence` emptiness.
- **`asset_throughput` continues to be the highest-value single table for this audit's cross-checks**
  — this cycle's readiness-query verification additionally surfaced that `asset_throughput.last_error`
  can carry a full embedded Python/PL-pgSQL traceback (not just a short message), which is itself a
  useful signal: a traceback-shaped `last_error` reliably indicates a real, specific, reproducible
  failure rather than a generic timeout or transient issue.
