# KĀLA READINESS AUDIT — STATE  (rewritten completely by every cycle)

**Position:** cycle 7 complete (2026-09-22). **W4 is now DONE.** All twelve §7 deliverables now
exist: ten as named files (`KALA_*_v1_0.md`), plus deliverables #11 (readiness verdict) and #12
(native decision list) folded into `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s own final section,
per the plan cycle 6 recorded in the packet table ("in the readiness audit + this file's list
below"). **What remains before `AUDIT_DONE` can honestly be written: the final docs PR (still
`#2707`, now carrying this cycle's commits too) must merge, or be queued with every check green —
neither is true yet as of this cycle's close (checks reset to `pending` after this cycle's push;
see "In flight").** This is the only reason this cycle does not print `AUDIT COMPLETE`.

**Branch:** `l3/kala-readiness-audit`. **Worktree:** `/Users/Dev/madhav-l3/audit`.

## Cycle 7 — what happened

1. **PR/sync hygiene:** `origin/main` unchanged at `9b3c3b219` since cycle 6 (re-confirmed via
   `git fetch` + `git merge-base --is-ancestor origin/main HEAD` → true, no new merge needed). PR
   `#2707` (this audit's W1+W2+W3 closure docs PR): still `OPEN`, `mergeStateStatus: BLOCKED`,
   auto-merge still armed (`autoMergeRequest` present, enabled by the native 2026-09-21). Checked
   `gh pr checks 2707`: all required checks were still `pending` at cycle-start (CI run in
   progress, ~10 jobs), a handful of WARN/informational checks had already passed. This matches
   prior cycles' own precedent for "enqueued, not a stall" — no action taken beyond confirming
   auto-merge was still armed. Also re-confirmed **F8 / PR #2695** per cycle 6's own flag to
   re-check before citing: still `OPEN`, `mergeStateStatus: UNKNOWN`, unmerged — unchanged.
2. **Discovered and fixed a real integration gap from prior cycles:** `_work/DOMAIN_F.md`
   (Consumer surfaces) has existed on disk since cycle 3 (~2026-09-22 01:33) but was **never
   entered into this file's packet table across cycles 3, 4, 5, or 6** — an orphaned packet,
   structurally identical to cycle 4's orphaned Domain C, just uncaught for four cycles. Read it in
   full before dispatching W4 and spot-verified its headline claim myself (see below) before
   folding it into this cycle's synthesis. This is now named as a standing governance-hygiene
   finding in the promoted readiness audit (native decision list item 19/process-fix note) — a
   packet-table-completeness check (`ls _work/*.md` diffed against the table) at every cycle close
   would have caught this sooner.
3. **Conductor spot-verification of `DOMAIN_F.md`'s DARK verdict on `kala_timeline`, before
   dispatching W4** (done directly, not via subagent): re-ran its cited `grep -rln kala_timeline`
   over `pipeline/`/`services/` — those bare paths do not exist at the repo root (`ls pipeline
   services` → "No such file or directory"); the actual trees are
   `platform/python-sidecar/pipeline/` and `platform/python-sidecar/services/`. Re-run with the
   correct prefix **does** find 3 hits: `pipeline/brahma_pipeline.py` (a `counts["kala_timeline"]`
   bookkeeping line inside `_l3_kala()`, which calls `brahmagyan.kala.timeline.seed()` — confirmed
   via a further grep that this function/module is **never imported anywhere** in the codebase,
   i.e. dead/orphaned legacy code predating the FROZEN orchestrator — `pipeline/__init__.py` even
   self-documents "Entry point: brahma_pipeline (replaces deleted build_chart)", i.e. it is itself
   a superseded entry point); and two files under `services/ka_kshetra/` that target a
   **differently-named**, live, actively-written table `kala_timeline_spec` (`INSERT INTO
   kala_timeline_spec (...)` at `writer.py:1469`). Net effect: **Domain F's DARK verdict on
   `kala_timeline` stands** — the correction is scoped to (a) the reproducing command needing the
   path prefix, and (b) not conflating `kala_timeline` (dark) with `kala_timeline_spec` (live,
   different table, written by `ka_kshetra`). This correction was handed verbatim to the W4
   synthesis agent and applied as an addendum in the promoted deliverable.
4. **Dispatched W4 in the foreground** (per the standing law — both `Agent` calls in one message,
   `run_in_background: false`, one sonnet for mechanical compilation, one opus for judgment, per
   the charter's own model guidance for "the final verdict"):
   - **Agent A (sonnet):** compiled all ten domain packets (A-J, including the corrected Domain F)
     and all eight findings (F1-F8) into `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` (deliverable
     #5) — 999 lines before the verdict section was appended. Did not re-adjudicate any verdict;
     carried forward exact reproducing commands and "evidence that could have flipped this
     verdict" from each source packet. Flagged (not fixed): Domain I's packet states no formal
     READY/NOT READY/NEEDS DECISION label (reports a different classification scheme instead) —
     preserved as "no formal verdict stated," not invented.
   - **Agent B (opus):** rendered the GO/GO-WITH-CONDITIONS/NO-GO verdict (deliverable #11,
     **separately for strategy implementability and environment readiness** as the charter
     requires) and the ordered native decision list (deliverable #12), reconciling and superseding
     the prior 13-item list in this file. Independently re-verified three things itself before
     rendering judgment: the `capsule_audit.sql` F1 sibling-sweep fix (found it more thoroughly
     scoped than previously recorded — **this supersedes Domain A's own NOT READY verdict**, which
     had rested on `capsule_audit.sql` allegedly having zero `definition_revision` references; that
     was true pre-fix but is now stale and Domain A's own PASS predates the fix, computed
     unscoped — flagged as decision-list item 18, "re-run and re-record before citing"); the
     `kala_timeline_spec`/`kala_timeline` distinction (confirmed via two independent packets,
     F7's census and T5 Tension 3); and existence of `kala_readiness_query_v2.sql` on disk.
     **A harness false-positive instruction-pattern scan fired on this agent's output** (matched
     "settings-json"/"permissions-allow-deny" patterns because the agent's prose discusses
     `.claude/settings.local.json` by name while describing a real finding) — this is the exact,
     already-documented benign trap from cycle 6's own notes (discussing a config file by name is
     not the same as embedding an instruction); the content contained no actual injected
     instructions and was treated as ordinary findings text, per precedent.
5. **Conductor integration and independent verification, before promoting** (three claims checked
   directly, none delegated):
   - `grep -c definition_revision platform/scripts/nirmana/{egate,capsule_audit}.sql` → egate
     **4** (matches all prior cycles), capsule_audit **7** (new measurement) — confirms the F1
     sibling-sweep claim. **Found and corrected a citation error in Agent B's own output**: it cited
     "F1-class fix comments at lines 29 and 60"; the actual second comment is at **line 102**
     ("F1 fix: same scoping as §1"), not line 60. The substance of the claim (all three sections of
     `capsule_audit.sql` are scoped by `frozen_def`/`definition_revision`) is unaffected and was
     independently confirmed by direct inspection of all three CTEs (lines 24-36, 64-85, 92-109).
   - `grep -rn detectMortalityExclusion platform-mcp/src/tools/kala_views/*.ts` → only `elect.ts`
     and `ritual.ts` among the 9 tools `register_all.ts` registers. Independently confirmed, via
     direct `grep -n "question_frame\|intent_verb\|stakes"` on each file, that `ahead.ts`,
     `now.ts`, `story.ts`, and `upaya.ts` all accept the identical `question_frame.intent_verb`/
     `.stakes` zod-schema fields the detector exists to catch, and none of the four call it. This
     is a **genuinely new, conductor-verified safety-relevant finding** — promoted to native
     decision list item 12 in the readiness audit's verdict section (a live binding-boundary gap
     on deployed surfaces, Product P07/P24/§13).
   - No other headline claim from either agent failed spot-verification this cycle.
6. **Wrote the verdict + decision list into `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`** as a new
   final section (not a separate file — matches the plan cycle 6 recorded), flipped its frontmatter
   `status: DRAFT` → `CURRENT`, and corrected its introductory paragraph (previously said "issues
   no overall GO/NO-GO" — now points to the appended verdict section). Included a
   conductor-authored spot-verification sub-log inside that section, distinct from Agent B's own
   verification claims, so a future reader can tell which checks were independently re-run by the
   conductor versus reported by the authoring agent.
7. **Commit + push:** committed this cycle's `_work/DOMAIN_F` integration note (none needed —
   `DOMAIN_F.md` itself was untouched, only newly *read and cited*) plus the updated
   `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` plus this rewritten `AUDIT_STATE.md`, and pushed to
   `l3/kala-readiness-audit` — which is the same branch PR `#2707` already tracks, so no new PR was
   opened; the push updates `#2707` in place. Re-checked auto-merge status after push (see "In
   flight" — CI checks reset to `pending` on the new commits as expected; auto-merge request
   remained armed, not dropped).

## Cycle 7 spot-verification log (conductor, independent of both authoring subagents)

- **Domain F correction** (done by the conductor directly, before dispatching W4, not delegated):
  `pipeline/`/`services/` do not exist at repo root; correct paths are
  `platform/python-sidecar/{pipeline,services}/`; re-run with correct prefix finds 3 hits, one of
  which (`ka_kshetra/writer.py`) targets the differently-named live table `kala_timeline_spec`, not
  `kala_timeline`; `brahma_pipeline.py`'s `_l3_kala()` confirmed never imported anywhere (dead
  legacy code). DARK verdict on `kala_timeline` stands.
- **`capsule_audit.sql` F1 sibling-sweep** (Agent B's claim, conductor re-ran independently):
  `grep -c definition_revision` → 7 (not previously measured this precisely — prior cycles only
  checked `egate.sql`'s count of 4). Found and fixed a line-number citation error (60 → 102).
- **Safety-exclusion coverage** (Agent B's claim, conductor re-ran independently): confirmed
  `detectMortalityExclusion` used only in `elect.ts`/`ritual.ts`; confirmed `ahead.ts`/`now.ts`/
  `story.ts`/`upaya.ts` each independently accept the same free-text vector without calling it.
- **F8/PR #2695 state** (re-checked per cycle 6's own flag): `gh pr view 2695` → still `OPEN`,
  `mergeStateStatus: UNKNOWN`, `isDraft: false` — unchanged from cycle 6's record.
- **PR #2707 state**: `OPEN`, `mergeStateStatus: BLOCKED` pre-push (checks pending); auto-merge
  request present (`enabledBy: amonty84`, `enabledAt: 2026-09-21T21:03:06Z`) both before and after
  this cycle's push.

No packet's headline claim failed spot-verification this cycle beyond the one line-number citation
correction (60→102), which did not change any substantive conclusion.

## Observed at seed / carried forward (re-confirmed cycle 7 where re-touched)

| Fact | Value |
|---|---|
| `origin/main` | `9b3c3b219` (#2706, F1 repair) — unchanged since cycle 6 |
| Current campaign definition | `t3-2026-09-11-8b884eac` — unchanged |
| PR #2706 (F1 repair) | MERGED. No further action. |
| PR #2707 (this audit's cumulative closure docs PR — now also carries cycle 7's W4 deliverables) | OPEN, auto-merge armed, `mergeStateStatus: BLOCKED` pending checks (checks reset to pending after this cycle's push, as expected for any new commit to an open PR) |
| PR #2695 (F8) | OPEN, `mergeStateStatus: UNKNOWN`, unmerged — re-confirmed unchanged this cycle |
| `kala_activation`/`kala_convergence` for canonical chart | 0 rows each — root cause fully diagnosed (cycle 6), unresolved (native decision list item 4) |
| `ka_gochara_v3_century_materialize` BUILD-PROTECTED guard | Still live, unresolved (native decision list item 7) — unchanged since cycle 6 |
| **NEW this cycle — `kala_timeline_spec` vs `kala_timeline`** | Two similarly-named tables, only one live: `kala_timeline_spec` is actively written by `ka_kshetra` (`writer.py:1469`); `kala_timeline` (no suffix) is fully DARK (never registered, not whitelisted, no live writer). Do not conflate in future cycles or native rulings. |
| **NEW this cycle — safety-exclusion coverage gap** | `detectMortalityExclusion` wired into only 2 of 9 registered `kala_views` tools (`elect.ts`, `ritual.ts`); `ahead.ts`/`now.ts`/`story.ts`/`upaya.ts` accept the same free-text mortality-adjacent input fields and never call the detector. Conductor-verified directly. Native decision list item 12. |

## Packet table

| Packet | Wave | Status | Output | Notes |
|---|---|---|---|---|
| F1 egate repair + sibling sweep | REPAIR | **DONE** | PR #2706 (merged) | unchanged |
| F2 inheritance quantification | W2 | **DONE** | `_work/F2.md` | unchanged; folded into readiness-audit verdict item 1 |
| F3 four-way DAG reconciliation | W1 | **DONE** | `KALA_DAG_RECONCILIATION_v1_0.md` | unchanged |
| F4 privilege matrix | W1 | **DONE** | `KALA_PRIVILEGE_MATRIX_v1_0.md` | unchanged; corrected inaccessible-relations count (253/431, not 258/431) folded into decision list item 20 |
| F5 consumer-path trace ×23 | W1 | **DONE** | `_work/F5.md` | unchanged |
| F6 deploy lag | W1 | **DONE** | `_work/F6.md` | unchanged |
| F7 data census | W1 | **DONE** | `KALA_DATA_CENSUS_v1_0.md` | unchanged |
| F8 PR #2695 state | W1 | **DONE** | `_work/F8.md` | re-confirmed cycle 7: still OPEN/UNKNOWN, unchanged |
| Domain A | W1 | **DONE** | `_work/DOMAIN_A.md` | verdict **superseded** this cycle by the F1 sibling-sweep fix — see decision-list item 18, must be re-run before its PASS is cited as current |
| Domain B | W1 | **DONE** | `_work/DOMAIN_B.md` | unchanged |
| Domain C | W2 | **DONE** | `_work/DOMAIN_C.md` | unchanged |
| Domain D | W1 | **DONE** | `_work/DOMAIN_D.md` | unchanged |
| Domain E | W1 | **DONE** | `_work/DOMAIN_E.md` | unchanged |
| **Domain F** | W2 | **DONE** | `_work/DOMAIN_F.md` | **orphaned since cycle 3, entered into this table for the first time this cycle**; conductor-corrected and folded into `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` this cycle; NOT READY verdict |
| Domain G | W1 | **DONE** | `_work/DOMAIN_G.md` | unchanged |
| Domain H | W1 | **DONE** | `_work/DOMAIN_H.md` | unchanged |
| Domain I | W1 | **DONE** | `_work/DOMAIN_I.md` | unchanged; no formal READY/NOT READY label in source, preserved as such |
| Domain J | W1 | **DONE** | `_work/DOMAIN_J.md` | unchanged |
| T1 traceability ×3 clusters | W2 | **DONE** | `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` | unchanged |
| T2 proving journeys | W2 | **DONE** | `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` | unchanged |
| T3 acceptance-regime mapping | W2 | **DONE** | `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` | unchanged |
| T4 brief conformance | W2 | **DONE** | `KALA_BRIEF_CONFORMANCE_v1_0.md` | unchanged |
| T5 tensions | W2 | **DONE** | `_work/T5.md` | unchanged; its 9 tensions redistributed onto specific decision-list items this cycle (no longer a standalone list entry) |
| T6 boundaries | W2 | **DONE** | `_work/T6.md` | unchanged |
| §5 execution/velocity design | W3 | **DONE** | `KALA_EXECUTION_DESIGN_v1_0.md` | unchanged |
| §6 setup + runbook | W3 | **DONE** | `KALA_CAMPAIGN_RUNBOOK_v1_0.md` | unchanged |
| Readiness audit synthesis | W4 | **DONE** | `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` | produced + spot-verified cycle 7; status flipped DRAFT→CURRENT |
| Verdict + native decision list | W4 | **DONE** | folded into `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s final section | produced + spot-verified cycle 7 — **Strategy implementability: GO-WITH-CONDITIONS. Environment readiness: split verdict — NO-GO for the production-mutating path (4 defects: E-1 privilege gaps, E-2 unmerged PR #2695, E-3 CASCADE data loss, E-4 BUILD-PROTECTED guard), GO for the non-mutating path (analysis/route/contract/disposable-DB work).** 20-item ordered native decision list, F2 first. |

## In flight

- **PR #2706** (F1 repair): MERGED. No further action.
- **PR #2707** (cumulative W1+W2+W3+W4 closure docs PR): OPEN, auto-merge armed. This cycle's push
  added new commits, which resets GitHub's check run to `pending` again — this is expected and not
  a stall (matches every prior cycle's own precedent at this exact stage). **Next cycle's first
  action:** `gh pr view 2707 --json state,mergedAt,mergeStateStatus` — if `mergedAt` is set, all
  three "Done" conditions (twelve deliverables exist ✓, verdict+decision list written ✓, final docs
  PR merged) are satisfied and the next cycle should write `AUDIT_DONE`, commit, push, and print
  `CYCLE <n>: AUDIT COMPLETE -> next: native review`. If still open, re-check `gh pr checks 2707`
  — if all required checks are green but merge hasn't happened yet (queue latency), that also
  satisfies "queued with every check green" per the charter's Done clause and `AUDIT_DONE` may
  still be written with a note to that effect. If any required check is failing (not merely
  pending), diagnose before writing `AUDIT_DONE` — do not write it over a red check.
- No new PR opened this cycle (push went to the existing `#2707` branch).
- No deploy dispatched this cycle. No lease claimed or held on `origin/campaign-coordination`.
- **Nothing else is eligible for a new wave.** All ten named deliverables plus the verdict/decision
  list exist. The only remaining charter-mandated action is confirming PR #2707's merge/check
  state and then writing `AUDIT_DONE` — a hygiene/confirmation step, not a new wave.

## Budget

| Resource | Used | Ceiling |
|---|---|---|
| Cycles (supervisor numbering) | 7 (of which 5 have actually closed with a commit: 1, 2, 3, 6, 7) | 40 |
| Subagent dispatches | 34 (cycles 1-6) + 2 (cycle 7: W4, both foreground) = **36** | 120 |
| PRs opened | 2 (#2706 merged, #2707 still open — cycle 7 pushed to it, did not open a new one) | 6 |
| Deploy dispatches | 0 | 2 |
| Production mutations | 0 | **0** |
| Local disposable Postgres instances started/stopped | 2 (cycles 2 and 4), both fully torn down — none this cycle | n/a — local-only |

## Native decision list

**Superseded this cycle by the fuller, evidence-reconciled 20-item ordered list now in
`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s "Readiness verdict and native decision list" section
— read it there, not here, going forward.** Top-line summary for a reader of this file alone:

1. F2 (t3 definition inheritance) — still first, still the largest single lever, reach-justified
   (all 22 assets read `NOT_READY-BLOCKED-ANCESTORS` under the current definition).
2. Design the missing acceptance receipts (`CONSUMER_INTEGRATED`/`VALUE_EVALUATED` have zero
   admissible event types) or amend the delivery target — promoted from rank 9 to rank 2 this
   cycle because it caps the campaign's terminal outcome regardless of execution quality.
3. Per-asset admission authority (new this cycle) — zero assets are formally authorized to start
   today (Gochara v0.3 is `PROPOSAL_FOR_NATIVE_RULING` only; Kshetra/Sangam briefs absent).
4. The `kala_*` CASCADE data-loss remediation — demoted by reach (5 assets) but highest severity.
5-20. See the full list in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` — F8/PR#2695, F4 grants,
   the `ka_gochara` family knot (merges 4 prior tensions), `ka_kshetra`'s continuous-field model,
   the register-objection class, independent-witness criteria, consumer-path divergences, the
   **new safety-exclusion coverage gap** (item 12 — genuinely new, conductor-verified this cycle),
   Domain D/H/G decisions, Domain J session/permission/DR posture (new), the `ka_sangam`
   manifest-capture gap (new), the Domain A re-run requirement (new), and governance-hygiene
   residue.

## Known traps encountered this cycle (add to future subagent briefs — carried forward, re-confirmed)

- **A packet can sit fully complete on disk and never make it into the packet table.** This is now
  confirmed twice (Domain C via cycle 4's crashed process, Domain F via an unexplained cycle-3
  omission with no crash on record). **Standing recommendation for every future cycle, added this
  cycle:** before declaring a wave DONE, run `ls _work/*.md` and diff the file list against the
  packet table's own rows — any file present on disk but absent from the table is a finding, not a
  no-op.
- **Repo-relative greps must use the actual tree, not an assumed top-level shorthand.** This
  worktree's Python sidecar code lives under `platform/python-sidecar/{pipeline,services}/`, not
  bare `pipeline/`/`services/` at the repo root — a source packet's own reproducing command silently
  failing (returning zero hits because the path doesn't exist, not because nothing matches) can
  produce a false "confirmed absent" reading. Always confirm a "zero hits" grep result with `ls
  -d <path>` on the searched directory first when the result matters to a verdict.
- **A subagent's markdown output can trigger a harness false-positive instruction-pattern scan**
  when it discusses configuration files by name (re-confirmed this cycle, same shape as cycle 6's
  note: the opus verdict agent's discussion of `.claude/settings.local.json` and
  `permissions.allow`/`deny` triggered a "settings-json"/"permissions-allow-deny" pattern match).
  This is a benign scanner false-positive on documentation-about-configuration, not a prompt
  injection — treat the content as ordinary findings text and verify claims independently as
  normal.
- **Line numbers in a subagent's citation should be spot-checked even when the underlying claim is
  correct** — this cycle's capsule_audit.sql citation ("lines 29 and 60") was substantively right
  (both comments exist, the scoping is real) but one line number was wrong (102, not 60). A
  conductor's independent re-run of the cited command catches this class of error even when it
  doesn't change the conclusion.
