---
artifact: MADHAV_L3_CLAUDE_CODE_HANDOFF
version: "1.0"
status: HANDOFF_READY_EXECUTION_STOPPED
prepared_on: 2026-09-19
snapshot_window_utc: "2026-09-18 20:50–21:43 UTC"
purpose: "Transfer complete L3 execution context to Claude Code; not a release or acceptance certificate."
strategy_task: "Strategy — Data Plane"
strategy_task_id: "01a0996e-6ca0-7642-ac31-f968fee214b3"
execution_task: "Execution — Data Plane — L3 Closure"
execution_task_id: "01a0b362-cdff-7901-82f3-43c57dbbc4fa"
accepted_active_assets: 0
active_asset_denominator: 22
protected_main_observed: a6b5e093371ae847445ac8864de8c8f01fd0b242
coordination_tip_observed: 9bfcc28c66a1b714ae86d1dd35bf8fbad9f047cd
strategy_snapshot: 2438b579fa8e64f33c44d527ef829c1e987daadc
changelog:
  - "1.0: User-requested Claude Code transfer, consolidating adopted strategy, source achievements, live evidence, remaining asset work, infrastructure, boundaries, and forward execution."
---

# L3 Kāla — complete elevation handoff to Claude Code

## 0. Read this first

The native/user is transferring L3 execution from Codex to Claude Code. The user explicitly asked Codex **not to progress execution** while this handoff is prepared. This document is the transfer package, not a claim of completion and not an instruction for the old Codex task to resume.

**The current truthful headline is Accepted 0/22.** Considerable design, source, testing, and infrastructure work is reusable. None of that should be discarded; none should be counted as terminal asset acceptance.

Three corrections to older status reports are particularly important:

1. The protected data-plane ownership/generation migrations **1035 and 1036 are now applied in production**, and the builder job is bound to its dedicated identity and database secret. Do not repeat that completed cutover merely because older documents call it pending.
2. The immediate delivery predecessor is now **Pūrṇa migration 1040 and its protected ownership/bootstrap route**. The latest ordinary deployment workflows reported overall success with the migration and service deployment jobs **skipped**. That is not a delivered L3 release.
3. The current campaign definition has **zero L3 evidence events and zero L3 freeze events**. Six checked canonical-chart L3 tables and both upstream L1/L2 selected-generation-head queries return zero rows. Existing historical rows or old-campaign events do not fill this gap.

The successor must elevate the entire layer and every active asset, including actual data and product use, in dependency order. It must not stop at producer readiness, passing tests, a merged PR, an unblocking report, or deployment alone.

### Package and provenance

This Markdown is the self-contained operational narrative. The accompanying reference package contains the original strategy documents, the protected-main execution/contract documents, selected release-source files, and a sanitized live-evidence snapshot. Original documents are deliberately retained rather than replaced with this summary.

Repository: https://github.com/Marsys-Technologies/Madhav

File paths below are repository-relative unless explicitly absolute. Most named campaign documents reside in `00_ARCHITECTURE/briefs/nirmana/`. The reference package preserves that directory structure under separate snapshot roots.

Evidence labels used here:

- **LIVE** — checked through read-only GitHub/GCP/database/repository inspection during this handoff.
- **RECORDED** — exact existing source/review/coordination record; tests were not rerun during this documentation-only handoff.
- **PLAN** — approved remaining scope or a proposed execution ordering, not a completed fact.
- **UNKNOWN** — not established by the current inspection.

Snapshot facts will age. Refresh mutable facts before any future write. No credentials, database connection strings, private event narratives, or credential values are included.

## 1. Product → data plane → L3: what we are trying to achieve

### 1.1 Adopted product definition

The governing product target is `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md`, adopted under **CCD-010**. Consult its review/adoption record too. It is the adopted target, not a certificate that the product already implements it.

Madhav must help its user:

- **Understand:** explain the actual structures, mechanisms, tensions, counter-evidence, and uncertainties in the available evidence.
- **Navigate:** distinguish meaningful alternatives, timing, opportunities, constraints, and the next useful question or computation.
- **Account:** retain provenance, original claims, what was known when, actual observations, revisions, and honest limits.

The intended value is an **earned distinction**: evidence changes the answer, ranking, explanation, uncertainty, or next action in a defensible way. More assets, rows, prose, scores, tools, or passing tests do not independently establish value. The aspirational “Beyond-Acharya” ambition is not an empirical performance claim.

L3 is central because a correct static structure without a defensible time model cannot adequately distinguish “why now,” “not yet,” “nearest versus strongest,” “which mechanism is engaged,” or “what changes across life chapters.”

### 1.2 Layer responsibilities

| Layer | Responsibility that L3 must respect |
|---|---|
| L0 Brahmagyan | Qualified definitions, source/rule meanings, conventions, methods, ontology and reusable knowledge. |
| L1 Ganita | Canonical astronomical/chart facts, conditions and clocks. L1 remains factual authority. |
| L2 Bodha | Structural propositions, mechanisms, relationships, promises, contradictions and applicability. |
| L3 Kāla | Explain when and how those same structures are engaged, supported, obstructed, repeated and compared through time. |
| L4 manifestation | Downstream manifestation/claim assembly. Only explicitly scoped interfaces are admitted here; not an L4 campaign. |
| L5 investigation/evaluation | Challenge, observation and evaluation. No same-run feedback or outcome-contaminated generation. |

Never replace canonical L1 facts with convenient L2/L3 recomputation. Carry canonical fact IDs and contextual identities forward.

### 1.3 Data-plane mandate

The adopted planning basis is `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md` under **DP-SD-009**, together with the contribution register, foundation contracts/gates, inventory baseline, and layer/asset execution-brief contracts.

The full documents enumerate DP-01 through DP-18, the core product-question portfolio, acceptance semantics, and contribution obligations. Read them; do not reconstruct their exact text from the shorthand here.

For L3, the essential obligations are:

1. Preserve structure rather than flatten it prematurely: participants and roles, sign/polarity, all applicable domains, occurrence versus condition, cancellation, rivals, applicability, source/method and canonical fact references.
2. Distinguish activity, intensity, agreement, salience, confidence, event probability and eventual outcome. They are not interchangeable.
3. Retain temporal structure: exact intervals, overlaps, ordering, recurrence, horizons, method disagreement, uncertainty, chart/convention sensitivity and search completeness.
4. Carry content-generation lineage through dependencies, publication and consumers. A timestamp is not a generation identity.
5. Keep definition, computation, serving, evaluation and admitted-next-generation edges distinct. No undeclared same-run feedback.
6. Separate four purposes: event-free generation; permitted historical explanation; protected C3 evaluation; and proposed future context-conditioned forecasts. A purpose bridge must be explicitly admitted.
7. Enforce **knowledge-time**, not merely event-date, boundaries. Event-derived selectors, rectification, weights and historical fit can leak outcomes even if direct event rows are absent.
8. Preserve issued claims, original evidence, observations, historical windows and supersession. A rebuild must not rewrite what the system originally said.
9. Publish complete, compatible data generations and honest absence states; do not silently fall back to stale/default/public data.
10. Prove actual value at the consumer boundary. Portal Paripraśna and managed MCP `prashna_ask` should preserve the same evidence and semantics. Raw tools have narrower supplied-evidence contracts; identical prose is not required.
11. Optimize cost without changing qualified meaning, coverage, determinism or uncertainty dishonestly.
12. Preserve viable assets and legitimate variants. Retirement, approximation or a narrowed horizon requires an evidenced disposition, not a speed-driven disappearance.

DP-07/08 are especially relevant to L3's temporal meaning. DP-09/13–15/18 include relevant interface obligations; they do not authorize wholesale L4/L5 elevation.

### 1.4 The L3 value questions

The L3 strategy's Q-01–Q-13 ask, in substance:

1. What is active now, and why?
2. What is nearest in the future versus strongest later?
3. Which complete yoga/structure is being activated, by what route?
4. Where is activity accompanied by strain or obstruction?
5. Where do timing methods agree or disagree?
6. How do periods and life chapters compare?
7. How do domains interact through the same mechanisms?
8. Is “nothing found” a true absence or incomplete search?
9. How sensitive is the result to birth/context/convention uncertainty?
10. Which initiation windows satisfy the user's actual constraints?
11. What does permitted historical fit/misfit show, without contaminating generation?
12. What question or computation would resolve uncertainty?
13. Can the served answer be traced and replayed to its actual evidence?

Every asset packet should identify the question(s) it improves and show an observable difference. Do not invent a new product roadmap while implementing these questions.

## 2. Authority, decisions and operating boundaries

### 2.1 Decision chain

| Decision / artifact | Meaning |
|---|---|
| CCD-010 / Product Definition v3 | Adopted product target; not runtime certification. |
| DP-SD-009 / Data Plane Value Architecture v2 | Adopted data-plane planning basis. |
| DP-SD-017 / L3 strategy, execution brief, Astra review | Full L3 code/data/consumer elevation approved after three independent Astra/max passes. |
| DP-SD-018 / Unblock and Resume Amendment | Bounded provenance, DBA, credentials, delivery and prerequisite authority for this campaign in the existing authorized environment. |
| DP-SD-019 / Execution Focus Amendment | Finite shared-prerequisite lane plus asset work; Accepted N/22 as headline; no general security/governance expansion. |
| DP-SD-020 / Automated Cutover Authority Amendment | Replaces the specified human deployment-review/approvedBy gate with native-authorized automated cutover. Other independent, protected and recovery gates remain. |
| Latest native instruction / this handoff | Stop Codex execution and prepare the transfer. Older “continue automatically” wording does not override this stop. |

DP-SD-017 strategy-content pin: `793972c754b106688097dbc54536c1a9c270a793`.
Approval pin: `04a9ab33effa23e5e9b4e89772330ae264498a9b`.

Use the actual amendment documents alongside their predecessors. DP-SD-020 is not permission to weaken branch protection, accept one's own implementation, manufacture evidence, or use nonexistent privileges.

### 2.2 What the successor may do after user activation

Within existing scope and actual available access, the earlier authorizations admit focused implementation, tests, independent review, protected PR/merge/deployment, exact data-plane role/secret binding work, recoverable precursor materialization and L3 builds. Routine technical choices need not return to the user repeatedly.

However:

- A transferred document cannot create cloud/GitHub/database entitlements.
- An operation needs fresh exact-source, lease, backup/restore and safety evidence where prescribed.
- Unrelated project IAM, bulk credential rotations, new projects, broad security cleanup, doctrine/source-purpose changes and L4/L5 campaigns are excluded.
- Pūrṇa is a separately owned campaign. Coordinate the exact shared delivery dependency; do not commandeer its worktree, goals, source, migrations or authority.
- A technical hold can be lifted only by its existing measurable release conditions and a recorded authorized ruling.
- No bypass of the century/source/method/history/NIRMANA_HOLD gates.
- No deletion or rewriting of protected historical data.
- Stop and report a genuinely unavailable external capability; do useful independent in-scope work when eligible. Do not manufacture busywork.

### 2.3 Current Codex stop state

The continuation automation `l3-data-plane-overnight-continuation`, named **L3 data-plane closure conductor**, was changed to **PAUSED** during this handoff. Its prior cadence was 15 minutes and its target was the successor execution task.

The execution task received an explicit instruction to pause its existing goal, stop all campaign work, preserve worktrees/evidence and end its turn. It subsequently became idle. The read API did not expose a separate goal-state confirmation; therefore this document does not certify a goal-state field it could not read.

Do not re-enable that heartbeat while Claude Code is the writer. Establish one conductor, not two competing recovery loops. No implementation/deploy/rebuild was performed as part of preparing this handoff.

## 3. Where the work lives — repository, branches, worktrees

### 3.1 Verified branch map

| Purpose | Absolute local path | Branch / observed HEAD |
|---|---|---|
| Strategy / this document | `/Users/Dev/.codex/worktrees/50a6/Madhav` | `codex/madhav-data-plane-strategy` / `2438b579fa8e64f33c44d527ef829c1e987daadc` |
| Current successor execution checkout | `/Users/Dev/.codex/worktrees/4683/Madhav` | **`codex/madhav-data-plane-routine-schema-bootstrap`** / `c9e385dfab4b76888aa262e16756291be926d900` |
| DP047 routine repair | `/Users/Dev/.codex/worktrees/dp047-routine-schema-repair` | `codex/data-plane-routine-schema-repair` / `840345a4461c5560acf936d0964d54b9aa4b4479` |
| Yojaka source packet | `/Users/Dev/.codex/worktrees/data-plane-l3-yojaka` | `codex/data-plane-l3-yojaka` / `7697c43b31da3655c2add7cda128a57ca4afd44e` |
| Earlier routine delivery | `/Users/Dev/.codex/worktrees/data-plane-ri02-routine-delivery` | observed `1fa8f1f8f16afa30ae5142227149b5afbdb80214` |
| Coordination checkout | `/Users/Dev/.codex/worktrees/dp041-coordination` | `codex/madhav-dp041-coordination`; refresh against coordination remote |

The current execution checkout is clean at the observed checkpoint. The strategy checkout already contained an unrelated-to-this-write, untracked recovery diagnosis:
`verification_artifacts/L3_VELOCITY_DIAGNOSIS_AND_RECOVERY_2026-09-18.md`.
It has been preserved and is included as historical diagnostic context, not live acceptance evidence.

Other preserved repair worktrees include:

- `/Users/Dev/.codex/worktrees/dp040-ownership-admin-repair/Madhav`
- `/Users/Dev/.codex/worktrees/dp040-ownership-route-bind/Madhav`
- `/Users/Dev/.codex/worktrees/dp040-source-acceptance-successor/Madhav`

Do not prune or delete worktrees, including ones Git labels prunable, during takeover without an exact inventory and explicit need.

### 3.2 Important branch trap

The earlier replacement task was created around `codex/madhav-data-plane-l3-closure`. That is **not** the current branch of its checkout.

That earlier branch remains at `8a7bbeca07dcc6c77cf09b47fa34894af9cb2996`. Its PR **#2655 remains open, with no auto-merge request**, and is superseded by merged #2656. Do not merge #2655 simply because the task name still says “L3 Closure.”

Old archived task: `Execution — Data Plane`, ID `01a0998a-8240-7631-97ce-36c6d4734fde`; old branch `codex/madhav-data-plane-execution`. Its old `c9bd` path is historical and was not established as available now.

### 3.3 Recommended Claude Code starting point

**Recommendation, not an already-created branch:** create one isolated successor worktree from freshly fetched protected `origin/main`, with a task branch such as `codex/madhav-l3-claude-code`. First compare all unmerged L3/source packets against main and preserve any required unmerged work by exact reviewed commits. Do not blindly merge all old branches or reset the existing execution checkout.

If using Claude Code in a remote/cloud environment, local absolute paths and credentials will not exist automatically. Clone the repository through authorized access, use the reference package for strategy documents missing from main, fetch the exact necessary refs, and establish authenticated access through approved secret mechanisms. Never paste secret values into the handoff or task prompt.

The package is **reference context**, not a replacement for the repository, installed dependencies, Git history, runtime credentials or protected release infrastructure.

### 3.4 Read-only takeover commands

Run from the receiver's repository, with its actual path:

```sh
git status --short
git branch --show-current
git worktree list --porcelain
git remote -v
git fetch origin main campaign-coordination
git rev-parse HEAD origin/main origin/campaign-coordination
gh pr view 2655 --repo Marsys-Technologies/Madhav --json state,headRefName,headRefOid,autoMergeRequest
gh pr view 2670 --repo Marsys-Technologies/Madhav --json state,mergeCommit
gh pr view 2673 --repo Marsys-Technologies/Madhav --json state,mergeCommit
```

Do not hardcode an old main SHA as the new write base; record a fresh one. Preserve the source snapshots in this package for provenance.

## 4. Current state: verified facts versus milestones

### 4.1 Acceptance denominator and database evidence — LIVE

Canonical chart: `482012f1-710e-4a25-994a-93821f5871aa`. The old `362f9f17-…` phantom is not a valid substitute.

| Observation | Result |
|---|---|
| Campaign | `nirmana-elevation` |
| Current definition | `t3-2026-09-11-8b884eac`, frozen |
| Manifest digest | `8b884eac2a950ca1d8d44c3b4af34288b2a7fbc177dba3903da301fad610a0b6` |
| Active L3 identities | 22: 18 row-backed/materialized and 4 service/pure identities |
| Retired identity outside denominator | `ka_gochara_sweep`; preserve history, do not rebuild |
| Current-definition L3 events | 0 |
| Current-definition L3 freeze events | 0 |
| Canonical-chart `kala_activation` | 0 rows |
| `kala_convergence` | 0 rows |
| `kala_obstruction` | 0 rows |
| `kala_darshana` | 0 rows |
| `kala_bhavishya` | 0 rows |
| `kala_field_snapshots` | 0 rows |
| L1 selected-generation heads, canonical chart | 0 rows |
| L2 selected-generation heads, canonical chart | 0 rows |
| `kala_activation_predicates`, canonical chart | 50,678 rows; 0 null signal refs; **79 unmatched same-chart MSR references** |

The last row demonstrates why old row existence is not current correctness. Old t0/t1/t2 L3 events must not be relabeled as current t3 evidence. The six-table check is not a claim that every table in the database is empty.

### 4.2 Meaning of “complete”

Track distinct states:

- Source contract and independent source acceptance.
- Physical content/generation and dependency acceptance.
- Layer data acceptance.
- Scoped consumer integration.
- Actual protected deployment.
- Product-value evaluation.
- Empirical predictive-performance evaluation, which remains a separate excluded programme.

The L3 target is **LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED**. Count an asset only through the actual type-appropriate terminal-evidence/freeze mechanism at the current definition. Do not fabricate row builds for service/probe identities.

### 4.3 Milestone reconciliation

| Milestone | State at transfer |
|---|---|
| Adopted product/data-plane/L3 strategy and asset-level plan | Established; reuse rather than re-audit from scratch. |
| W0 source safety and numerical contract work | Significant independently reviewed source work complete; physical replacement/publication still open. |
| First W2 source frontier | Reviewed source packet exists; not terminal assets. |
| Durable provenance/release admission machinery | Source work exists; preserve exact receipts and reconstruction. |
| Protected data-plane owner cutover, 1035/1036 | Applied; dedicated builder binding live. |
| End-to-end routine delivery and current service release | Not complete; 1040 predecessor and service/image gap remain. |
| Physical accepted L0→L1→L2 selected generations | Not established; current heads empty. |
| First accepted L3 asset | Not achieved. |
| Upstream L3 frontier / repeated closure cadence | Not achieved as terminal acceptance. |
| Entire L3 and all 22 active assets | Not achieved. |

Do not calculate an overall percentage by averaging source packets, tests and terminal assets. The headline remains **0/22 = 0% terminal asset closure**, with separately reported intermediate achievements.

## 5. What has already been built and must be retained

The following is **RECORDED source/review evidence**, unless explicitly marked live. Historical counts refer to their exact packet revisions; they are not a fresh test run on today's main.

### 5.1 W0 safety, field contracts and historical preservation

- Kshetra's planner became mutation-free; complete 15-table/referrer preflight and lock handling were added. Its ownership boundary includes only `kala_insights.lel_derived=false`; `mi_bhara` owns the true side. A populated unsafe replacement is stopped before DML. This is deliberate protection, not a license to disable the guard to get a build through. Reference source includes `3f109869d`; later resume-v10 behavior supersedes old numerical-document v9 assumptions.
- Bhavishya candidate computation and complete historical/referrer checks occur before destructive mutation. Unchanged protected records are retained; changed history-bearing records fail closed. Reference source `a3e518864`.
- The W0 field register records **39 relation/service partitions and 699 explicit fields**, digest components for 14 assets, Kshetra partitions and four service shapes. This exact register is in the reference pack; it is the field-level worklist, not a new summary-created schema.
- Full rebuild/publication must preserve issued claims, outcomes and referrers. A source guard that blocks unsafe publication is source progress, not completion of a safe replacement mechanism.

Read:
`MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md`,
`MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md`,
`MADHAV_DATA_PLANE_L3_W0_BENCHMARK_BASELINE_v1_0.md`.

### 5.2 DHARA numerical corrections

The numerical contract distinguishes the previous segment's left limit from the next segment's exact right-continuous endpoint; the final horizon uses its left limit. Floating-point `nextafter` handling is tested against independent high-precision/Decimal reasoning and a 4096-subinterval Simpson reference, not merely old-output parity.

Recorded tolerances include log-linear error 5e-13, crossings 0.003 day, integral error 0.3%, and window error 0.5%, in their specified fixtures/scopes.

A midpoint correction (recorded source `87cc8c9`) fixes a concrete 1515-versus-300 discrepancy and the 40/202 fractions. Recorded focused verification includes 37 tests, Kshetra 259 with 3 skips, and an independent 110-test review scope.

Read the complete `MADHAV_DATA_PLANE_L3_DHARA_NUMERICAL_CONTRACT_v1_0.md`. An optimization must meet the corrected mathematical contract; reproducing the old bug is not successful parity.

### 5.3 W2 first frontier

Reviewed source `47131772b355ae2c67b1f6fb2b90e9fa007e2202` covers eight first-frontier writers and four service/pure identities. Changes include preparation before delete, applicability/coverage checks, fail-before-mutation behavior, and service boundary tests.

Recorded results: 482 focused tests with 5 skips; all-L3 suite 1,521 passed, 41 skipped, 2 xfailed; independent review without blocking findings at that scope.

Read `MADHAV_DATA_PLANE_L3_W2_FIRST_FRONTIER_SOURCE_v1_0.md`. Preserve its evidence, then determine what later main changed. Do not announce eight accepted assets from eight reviewed writers.

### 5.4 Yojaka meaning preservation

A rejected maximum-domain reduction was replaced with preservation of complete signed multi-domain compatible promises. Primary-domain scalar matching remains where `ph_nimitta` compatibility requires it; do not flatten the richer representation back to that scalar.

Reference source `7697c43b31da3655c2add7cda128a57ca4afd44e`, integrated via recorded `fbf7803dc`. Recorded checks include 116 focused tests and all-L3 1,525/41 skips/2 xfails; independent 81/3 skips. No production speedup is proved by these counts.

Current physical predicates still have 79 unmatched MSR references. Rebuild only after accepted upstream generation binding and history-safe dependency handling.

### 5.5 Provenance durability and generation architecture

The precursor/RI02 work introduces protected L1/L2 generation/history/head/partition mechanisms and exact-source receipt/pin handling, rather than trusting mutable upstream rows.

A provenance-successor packet uses reachable ancestry and an explicit 23-blob manifest, including a fresh single-branch-clone reconstruction test. Recorded tests include 27 durability, 59 Python and 31 TypeScript focused checks. Historical references include `66a85047`; consult full source receipts for exact pins.

The architecture separates:

1. A selected immutable producer generation.
2. Declared contributing partitions and exact content/dependency identities.
3. Builder lifecycle operations.
4. Independent verification/terminal acceptance.
5. Compatible publication/replay and supersession.

The relevant tables now exist in production, including L1 generation/partition/head tables and L2 generation/head/partition/run and producer-generation tables. **Existence is not population or accepted selection.**

Read RI01, RI02, provenance-successor, security-source acceptance v1.0/v1.1 and the cutover contract. Do not modify historical accepted receipt bytes to silence a mismatch. Issue a reviewed versioned successor when necessary.

### 5.6 Muhurta and compatibility delivery

Recorded `475f5ab5a` restored `/api/compute/muhurat` compatibility and chart authorization, retained native instant/timezone semantics and avoids incomplete caching. Recorded evidence: 79 Python, 34 TypeScript and 12 local E2E checks.

A 10-window local diagnostic took approximately 0.66–0.71s; that is not a deployed production SLO or complete L3 consumer acceptance.

### 5.7 Source gates and deployment adapter repairs

Broad source suites and generated-pin/receipt checks have passed at named historical candidates. They must be reused as evidence of those candidates, then rerun proportionately for actual changes. A source green does not imply current service revision, fresh physical generations or acceptance.

The ordinary migration runner now avoids an unnecessary tracker-table CREATE when its tracker already exists. This is the final reviewed direction; do not reinstate the earlier attempted routine-owner grant described below.

## 6. Immediate blocker and release history

### 6.1 What is actually blocked now

The ordinary release path encountered:

`platform/migrations/1040_planner_inquiry_successor_lifecycle.sql`

after the data-plane schema ownership transfer. Migration 1040 belongs to the Pūrṇa inquiry lifecycle. The routine application role intentionally lacks schema CREATE and owner membership. It cannot be made broadly owner-capable merely to make this migration pass.

PR #2673 added 1040 to the controlled Pūrṇa migration route **when that lifecycle is armed**. The latest observation does not establish that the required one-shot Pūrṇa owner/bootstrap preparation has occurred. The read-only role check found `purna_inquiry_owner` but no `purna_inquiry_bootstrap` role; both the routine app and Pūrṇa owner lacked public-schema CREATE.

**Smallest forward dependency:** the owning Pūrṇa/release operator must reconcile the existing ownership lifecycle, exact 1040 migration route, fresh one-shot authority/credentials and actual application state; then perform the already-reviewed protected delivery with independent postflight. Coordinate narrowly. Do not reopen the entire Pūrṇa programme.

Migration 1040 explicitly checks for a normalized NOLOGIN owner, freshly provisioned direct temporary owner membership with admin option for the session user, and temporary public-schema CREATE for that owner before SET LOCAL ROLE. These are one-shot protected lifecycle conditions, not permanent grants to the routine application. The owner must arrange their legitimate provision and cleanup through the reviewed route.

Migration 1041 also remains unapplied:

`platform/supabase/migrations/1041_data_plane_public_schema_migration_grant.sql`

At current source it is a tracked compatibility **SELECT 1 no-op**, not a schema privilege grant. Verify its bytes at the selected candidate. 1040 must be resolved before treating the later migration or service release as successful.

### 6.2 Key PRs and runs

| Item | Observed result / lesson |
|---|---|
| #2637, #2638 | Admin credential separation and production-proxy route binding source repairs. #2638 merged at `ea9b27bfeba607c5332c51e10b037e100e97b717`. |
| #2655 | Open superseded duplicate; no auto-merge request. Do not merge. |
| #2656 | Merged `558a61d916a920cbcb0456dfb0fddac11efdc9e4`; pgcrypto provision in protected cutover. |
| DP046 / run 35335514577 | Protected cutover and builder rebind succeeded; subsequent strict step failed on GOOGLE_CLOUD_REGION/GCP_REGION environment wiring. Do not reinterpret as “nothing applied.” |
| #2664 | Merged `4c6e6daaed71125945ac99896d9fc098bf76b85a`; an intermediate ordinary-schema-grant approach. |
| #2666 | Merged `37c5dae709dd02c2c8938b8cb748b2513b63148e`; intermediate bootstrap approach hit 42501, permission denied to set role data_plane_schema_owner. |
| #2670 | Merged `a5c7dde5c0f2dc7a53377c9609473ff9ab86671f`; preserves strict routine isolation, fixes tracker initialization and makes 1041 a compatibility no-op. |
| CI 35368302580 | DP047 source checks passed. |
| Deploy 35369415078 | Pre-mutation source/route/ownership/isolation/Nirmana/Pūrṇa checks passed; then failed at 1040 before 1041 or service deployment. |
| #2673 | Merged `6b9323989011a2da8fb002ffc7a4df3cc9b2562b`; controlled successor-migration routing. |
| Run 35392578639 | Overall success; migration/service mutation jobs skipped. Not deployment proof. |
| Run 35395619243 | Head `a6b5e09`, overall success; gate/detection/DB inspection ran, migrations/bootstrap/pipeline/web/MCP/sidecar deployment jobs skipped. Not deployment proof. |

Links are reproducible as:
`https://github.com/Marsys-Technologies/Madhav/pull/<number>` and
`https://github.com/Marsys-Technologies/Madhav/actions/runs/<run-id>`.

### 6.3 Coordination/recovery receipts

The latest coordination row inspected is **DP047, RELEASED**, with the 1040 predecessor blocker. It is not an active lease for a new operation. Refresh `origin/campaign-coordination` and `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` before taking any future shared-write lease.

Recent history, to avoid repeating already diagnosed failures:

- DP041: backup `1789718208479`, isolated restore `0c46538f-1dd8-4016-8d6a-1a6f0000002f`; route failure before cutover, cleanup recorded.
- DP042: backup `1789719254747`, restore `3816629a-6e90-4126-a269-14e50000002f`; aborted on protected-tip drift, no dispatch.
- DP043: backup `1789720842502`, restore `5a41c78e-70d9-48a3-a87a-e0240000002f`; pgcrypto failure, transactional stop before mutation.
- DP044: duplicate #2655 CI cancellation; no release.
- DP045: a healthy CI was cancelled prematurely near six minutes. The clean exact Python 3.13 command subsequently completed in 315.72s with 7,047 passed, 93 skipped, 158 deselected, 3 xfailed and 7 subtests. Do not declare a stall merely because a quiet job takes several minutes.
- DP046: backup `1789727194788`, isolated restore `ceaf6125-917c-4ec8-ba8b-6a160000002f` on `amjis-ri02-validation-c720f1832`; successful ownership cutover/rebind followed by environment-wiring failure.
- DP047: routine delivery source repair passed its source/isolation gates; 1040 blocked migration and service release.

Old one-shot authorization, lease and direct-postgres carrier were cleaned up after DP046 and the temporary password rotated. **Terminal receipts must not be reused**, even if a nominal time window appears unexpired. These backup IDs explain history, not permission to mutate now.

## 7. Infrastructure and architecture inventory

### 7.1 Live environment

| Resource | Observed identity / state |
|---|---|
| GCP project | `madhav-astrology` |
| Region | `asia-south1` |
| Production Cloud SQL | `amjis-postgres`, RUNNABLE; connection `madhav-astrology:asia-south1:amjis-postgres`; database `amjis` |
| Isolated restore-validation SQL | `amjis-ri02-validation-c720f1832`, RUNNABLE; distinct instance |
| Web | `amjis-web`; https://amjis-web-qm256lasva-el.a.run.app |
| Managed MCP | `amjis-mcp`; https://amjis-mcp-qm256lasva-el.a.run.app |
| Sidecar | `amjis-sidecar`; https://amjis-sidecar-qm256lasva-el.a.run.app |
| Build job | `brahma-build-pipeline-job` |
| Other observed jobs | `amjis-sidecar-release-smoke`, `brahma-foundation-bootstrap` |
| Artifact Registry image family | `asia-south1-docker.pkg.dev/madhav-astrology/amjis/` |

This is an identity snapshot, not a global infrastructure-health audit.

### 7.2 Actual served revisions — LIVE

Each listed service had 100% traffic to its observed ready revision:

| Service | Actual ready revision | Source evidence |
|---|---|---|
| web | `amjis-web-probe-93a3a5eb8d85-35069281039-1` | revision NIRMANA_DEPLOYED_SHA `93a3a5eb8d8552656efc6582d92dfbdf7555b0e1` |
| MCP | `amjis-mcp-probe-93a3a5eb8d85-35069281039-1` | same actual revision environment SHA |
| sidecar | `amjis-sidecar-probe-079e77ef92f2-35203145002-1` | immutable digest below; NIRMANA_DEPLOYED_SHA absent. Template tag `079e77ef92f25217921f02e4956162f43fe3f824` is a hint, not verified environment SHA. |

Immutable revision image digests:

- web: `sha256:53d83145c6712aa2b56dcfde7be9c29b433c36c9d6f1b1c069a1f00e2479983d`
- MCP: `sha256:e2b622a9e6ce7c7fd4a5c87ec9545523e277b85c1ade06ce60459ac4d500ce58`
- sidecar: `sha256:1c6cdee7290d823469726b68da8c278ce4dbdc3c4998c48860c3198aed6ee479`

Read the actual ready revision, then its image/environment. A workflow HEAD or service template alone is not the deployment oracle.

Runtime service identities observed: `amjis-web-runtime`, `amjis-mcp-runtime`, `amjis-sidecar-runtime` in this project's `iam.gserviceaccount.com` domain.

### 7.3 Builder binding — LIVE

`brahma-build-pipeline-job`:

- Service account: `data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com`.
- DATABASE_URL secret reference: `data-plane-builder-db-url:latest` — resource name only; secret value was not read.
- Image: `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:c63cb804840db9928ccdebabdf98c2d2abbb74ba`.
- CPU 4; memory 16 GiB.
- Latest created execution observed: `brahma-build-pipeline-job-xfrpr`, succeeded 2026-09-12T01:47:39Z. This predates current physical acceptance work and is not L3 closure evidence.

### 7.4 Database roles and migrations — LIVE

The `public` schema owner is `data_plane_schema_owner`. Routine `amjis_app` cannot CREATE there.

Protected owners `data_plane_schema_owner`, `data_plane_l1_owner`, `data_plane_l2_owner` are NOLOGIN/NOINHERIT and not superuser/create-role/create-db/bypass-RLS actors.

Dedicated builder, verifier and migrator logins are NOINHERIT and not superuser/create-role/create-db/bypass-RLS actors. The inspected membership rows give the migrator the three mapped owner memberships, without admin option. This is not permission to mount the migrator in application/build runtime.

Migration 1035 and 1036 application timestamp:
**2026-09-18T10:48:47.660Z**.

| Migration | File SHA-256 | SQL identity |
|---|---|---|
| 1035 | `80e49dc7460f829c52af41e398422dd891e993cc7aa3dbfeaaad312a149765b0` | `6d50fa16186996f245a63bc20e9d88c45c4f74926b7531c0f794f18f8bea05a4` |
| 1036 | `9fd38140dca82efb379a6af1b575b94b60236501d9f5ce65cb4e4fcb6e4f890d` | `133d90b9f9e1432db3a2a3833f7f9cbf808a2bb4129588eb43ae84cba0e8264b` |

1033/1034/1037/1038/1039 were also recorded applied. 1040/1041 were absent from the inspected applied-migration result. Do not edit applied 1035/1036; reserve reviewed append-only follow-ups if genuinely needed.

### 7.5 Important code surfaces

- Writers: `platform/python-sidecar/pipeline/orchestrator/writers/ka_*.py`.
- L3 algorithms/tests: find exact imports from the selected writer closure in `platform/python-sidecar/`; do not assume the registry captures every read.
- Consumers: `platform-mcp/src/tools/kala_views/`, `platform-mcp/src/tools/retrieval/kala_temporal.ts`, `platform-mcp/src/tools/kala_timeline.ts`, associated `platform-mcp/src/lib/kala_*` and tests.
- Delivery: `.github/workflows/deploy.yml`, `platform/scripts/migrate.ts`, `platform/scripts/validate-migration-database-routes.ts`.
- Data-plane scripts: `data-plane-ownership-status.ts`, `data-plane-ownership-preflight.ts`, `data-plane-migration-attestation.ts`, `data-plane-protected-cutover.ts`, `data-plane-cutover-preflight.ts`, `data-plane-secret-isolation-preflight.ts`, `data-plane-admin-credential-diagnostic.ts`, all under `platform/scripts/`.
- Pūrṇa scripts: `purna-inquiry-ownership-status.ts`, `purna-inquiry-ownership-preflight.ts`, `purna-inquiry-ownership-postflight.ts`.
- Provenance generation: `platform/scripts/generate/nirmana_analysis_layer_pins.py`; resolve the actual writer inventory generator and its imports before modifying it.
- Generated artifacts: `platform/src/generated/nirmana-analysis-layer-pins.json`, `nirmana-writer-digests.json`, `nirmana-analysis-receipts.ts`.
- Migrations use both governed directories. **1040 is in platform/migrations; 1035/1036/1041 are in platform/supabase/migrations.** Do not copy a migration into the other directory to force execution.
- Infrastructure source includes `infra/iam/main.tf`; identify the exact resource block before changing any binding.

Credential variables and secret resources must be read from the selected workflow/script contract. Relevant data-plane variable names include PROD_DATABASE_URL, DATA_PLANE_ADMIN_DATABASE_URL, DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL, DATA_PLANE_MIGRATOR_DATABASE_URL and DATA_PLANE_RESTORE_VALIDATION_DATABASE_URL. Never confuse routine, migrator, validation and direct one-shot administrative credentials. Never export their payloads into chat, source, argv or the reference pack.

## 8. All 22 assets: purpose, existing work and remaining closure

**Every row below remains terminally unaccepted at this snapshot.** “W2 source” means the reviewed first-frontier source packet, not finished semantic/data/consumer elevation. Exact field-level obligations are in the 699-field register and asset contribution register.

| # | Asset / type | Value and existing work | Remaining elevation / acceptance focus |
|---|---|---|---|
| 01 | `ka_graha_sancara` — service | Ephemeris/motion substrate; service fixtures exist, no row build invented. | Actual deployed arbitrary-chart/convention, bounds/errors and correct consumer use; candidate for earliest type-appropriate acceptance if current gates are satisfied. |
| 02 | `ka_dasha_kala` — service | Seven-system clock interface; partial/aborted handling improved. | Accepted L1 clock generations, hierarchy, applicability, interval overlaps, complete response and downstream testimony semantics. |
| 03 | `ka_muhurta_seva` — service | Calendar/election; route/chart-auth compatibility and instant/timezone fixes recorded. | Actual constraints, applicability, positive qualified route, no incomplete-cache masquerade, deployed consumer evidence; W7 completion. |
| 04 | `ka_tulana` — pure/service | Period comparison; rejects duplicates/non-finite/invalid inputs; forensic 0.7950 versus 0.4234 preserved in source evidence. | Real accepted input windows, ties, context, nearest/strongest distinctions and reproducible comparative value; W7. |
| 05 | `ka_gochara_resonance` — rows | `gochara_resonance_map`; target/rule preparation before delete; 27-class coverage source work. | Preserve target, role, method and root evidence; accepted L0/L1 inputs and physical root materialization; W2. |
| 06 | `ka_moorti_nirnaya` — rows | `kala_moorti_nirnaya`; W2 coverage/daily safety. | Rolling -60/+400-day Lahiri overlay is not century proof; applicability, context and physical coverage; W2. |
| 07 | `ka_kota_chakra` — rows | `kala_kota_chakra`; W2 preparation safety. | Ring/version/applicability meaning, actual context, consumer usage; distinguish unused declared century edge; W2. |
| 08 | `ka_vedha_gochara` — rows | `kala_vedha_gochara`; daily coverage safety. | Signed target-specific obstruction, method distinctions, no duplicate attenuation; actual Sangam dependency must be represented; W2. |
| 09 | `ka_tithi_pravesha` — rows | `kala_tithi_pravesha`; safe annual return preparation. | Qualify actual Moon-return method and boundary/context semantics before promotion; century code does not currently consume it just because registry says so; W2. |
| 10 | `ka_sudarshana_varsha` — rows | `kala_sudarshana_varsha`; three-frame annual overlay. | Shared natal roots are not three independent votes; physical coverage and real consumer route; W2. |
| 11 | `ka_yojaka` — rows | `kala_activation_predicates`; safe preparation plus richer signed/multi-domain promise preservation. | Repair stale references via accepted generation, retain full compatible structure/participants and source/method identity; no maximum-domain reduction; W2. |
| 12 | `ka_avadhi` — rows | `kala_avadhi`; canonical chara_karaka and seven-system MD/AD coverage, mutation-free dry-run. | Actual interval/applicability/context coverage; assess missing ayanamsa in the key, fixed domains and ten-row limits; no fictitious Avadhi→Taranga data read; W2. |
| 13 | `ka_gochara` — rows | `kala_gochara_windows_v2`, generation-2 materialized windows, bounded ±3-year scope. | Geometry/recurrence/completeness and safe shared staging; current Sangam uses on-demand computation rather than this materialized table; W3. |
| 14 | `ka_gochara_v3_century_materialize` — rows | Century/gen-3 materializer with shared v2 staging; hold remains. | Resolve full century versus explicitly qualified compact/refinement architecture; prove coverage and cost. Kota/Tithi are declared but unused inputs. No deferral disguised as acceptance; W3 hold must legitimately close. |
| 15 | `ka_sangam` — rows | `kala_convergence`; combines predicates, clocks and transits. | All applicable predicates rather than hidden caps, actual Vedha input, shared geometry without lost testimony, interval intersections and meaningful independence; W3. |
| 16 | `ka_kalasutra` — rows | `kala_activation`; temporal activation/recurrence. | Indexed complete recurrences, explicit as-of/horizon and no hidden eight-match truncation; W4. |
| 17 | `ka_vighnakara` — rows | `kala_obstruction`; resistance/opposition. | Complete targeted opposition, no top-500 blind spot, missing versus clear state, prevent duplicate roots/attenuation; W4. |
| 18 | `ka_taranga` — rows | `kala_taranga`; chart-month scope historically 1950–2100. | Actual Sangam/clock/Pratijna inputs, class-specific meanings not domain-max flattening, safe shared writer/service keys; Avadhi is not an actual read today; W4. |
| 19 | `ka_kala_darshana` — rows | `kala_darshana`; coherent temporal view. | Use actual Sangam/Vighnakara dependencies, preserve real zero rather than 0.5 fallback, remove unjustified top-750 loss, distinguish coverage/uncertainty; W5. |
| 20 | `ka_jivana_parva` — rows | `kala_jivana_parva`; life chapters. | Exact ordered clock intervals instead of unordered LIMIT 1, cross-domain mechanisms and chapter evidence; W6. |
| 21 | `ka_bhavishya_lekha` — rows | `kala_bhavishya`; prospective/historical window ledger, W0 history protection. | Stable issued identity not rank, explicit five-year/top-100 scope, preserve outcomes/referrers, qualified future projection and original issuance; W6. |
| 22 | `ka_kshetra` — staged rows | 15-table temporal field pipeline; W0 guard and DHARA corrections. | All internal stages, exact null/geometry optimizations, compatible complete immutable publication, resumability, selective ownership, full consumer value; through W7. |

**Retired history asset:** `ka_gochara_sweep` is outside the 22 active denominator. Preserve its protected snapshot/history and shared-table compatibility; never rebuild it merely to obtain a new green status.

### 8.1 Required per-asset packet

For each asset, maintain one existing-governance-compatible packet containing:

- Identity/type, qualified purpose and product questions.
- Exact writer/import closure and source/method/convention contracts.
- Field/partition dispositions: preserved, corrected, extended, unavailable/held with reason, or legitimately retired. No untracked information loss.
- Actual input/output and shared-write/FK edges, including hidden SQL/service reads.
- Accepted upstream content-generation vector, partitions, as-of/horizon and purpose.
- Implementation and safe materialization/publication plan.
- Discriminating fixtures, independent review, numerical/performance evidence.
- Actual source, migration, runtime, physical-generation, consumer and terminal-event references.
- History/rollback behavior and the next finite action.

Do not create a second manual truth ledger when the existing authenticated evidence/registry mechanism can carry this.

## 9. Dependency-first elevation: source and data together

### 9.1 Do not trust the registry as the whole DAG

The live registry still contains false or unused edges and misses source reads. Its exact 23-row dependency snapshot is included in the live evidence JSON.

Examples requiring reconciliation:

- Sangam actually reads Vedha and on-demand transit geometry; its registry materialized-Go­chara edge does not prove that materialized table is consumed.
- Taranga declares Avadhi, but current implementation does not read it.
- Darshana declares Kalasutra, but its present computation reads Sangam/Vighnakara.
- Century declares Kota/Tithi inputs that its current code does not consume.

Correct source contracts, scheduler dependencies and deployed registry through the governed route. Do not silently bypass the current scheduler, and do not declare the registry fixed because a document has the right diagram.

### 9.2 Working source-derived order

```text
accepted L0 definitions + accepted L1 facts/clocks + accepted L2 structures
 ├─ resonance → materialized Go­chara v2
 ├─ overlays / Avadhi / Yojaka
 └─ Kshetra S0 + S2
resonance + Vedha + Moorti + raw L1 context → century v3 (hold)
Yojaka + Vedha + live geometry/calendar + L0–L2 → Sangam
Sangam + Yojaka + applicable L0–L2 → Kalasutra / Vighnakara
Sangam + actual clock/structure/ontology inputs → Taranga
Sangam + Vighnakara → Darshana
Darshana + convergence + predicate/clock context → Jivana Parva
Darshana + convergence/MSR → Bhavishya
accepted temporal products → data-bound Tulana / Muhurta / consumers
```

This is a planning summary of actual reads, not a replacement for exact per-packet dependency manifests.

### 9.3 Kshetra's internal DAG

The stage names are not numerical execution order:

```text
S0 kinematics       S2 structure
                         ↓
                      S3 clocks
S0 + S2 + S3 → S1 primitives → S4 field
S4 + prerequisite context → S5 null/windows/provenance
→ S6 salience → S6.5 insights → S8 timeline → complete compatible snapshot
```

A partially completed stage set cannot be selected as a complete snapshot. Resume signatures must invalidate only genuinely changed dependencies and must prevent an old late worker from publishing over a newer accepted generation.

### 9.4 Shared-write and deletion hazards

- Seven L2 producer identities and their contributing partitions matter. A single “latest L2 head” is not the entire dependency vector.
- MSR deletion can cascade through activation, Bhavishya, convergence, Darshana and obstruction.
- Convergence deletion can affect Darshana, obstruction and manifestation anchors.
- Bhavishya deletion can null historical anchor references.
- v2/century share staging/output surfaces; retired sweep history may share the main table.
- Kshetra must not delete `kala_insights.lel_derived=true` rows owned by `mi_bhara`.
- Taranga service/writer paths share natural keys.
- Build-state/registry/publication and generation-head surfaces are shared serialized responsibilities.

The frozen writer/orchestrator contract remains: registered WriterBase writers, caller-owned `ctx.db_conn`, no writer commit/close, no hand-written `_telemetry`/throughput, and correct whole-run/substep semantics. L0 upsert and L1+ rebuild conventions are constrained by the newer history/publication protections; a blanket chart DELETE is not justified by the old shorthand.

## 10. Performance programme — faster without losing meaning

### 10.1 What is known

The slowest assets warrant architectural work, not just more CPU or repeated rebuilds. Existing measurements are microbenchmarks, not production end-to-end evidence:

| Recorded diagnostic | Result / limitation |
|---|---|
| Kshetra preparation | ~0.47s fixture |
| Hash/publication work | ~6.99s fixture |
| Null diagnostic | ~0.31s fixture |
| Structured diagnostic | 0.315060s; 61 rows; 263,206 bytes |
| Transit diagnostic | ~4.56ms bypass, 2.42ms cold, 1.92ms warm; ~44.51ms fan-out, with Moshier fallback context |
| Muhurta 10 windows | ~0.66–0.71s local |

No production I/O/WAL profile or complete-century runtime is established by those figures. Do not promise a speedup factor from them.

### 10.2 Prioritized optimization work

| Priority | Target / method | Proof required |
|---|---|---|
| P0 | Safe planning and historical preservation | Retain W0 protections; optimization cannot move validation after destructive work. |
| P1 | Kshetra null programme: avoid approximately 372M scalar operations / 37M heap-value scale by blocked exact float64/order-statistic work | Full shift/domain coverage, corrected numerical contract, bounded memory and deterministic equivalent result; no hidden sampled-null substitution. |
| P2 | Shared preparation, event boundaries, clocks, sparse active structures | Exact context/version cache keys; no stale reuse or cross-chart/convention contamination. |
| P3 | Unique geometric targets, boundary halos, batched parent-preserving transit work | Preserve each rule/parent/method testimony and exact recurrence/boundary coverage. |
| P4 | Sangam shared geometry and full predicate processing | No early top-N cap, no apparent independence from shared roots, same qualified semantics. |
| P5 | Kalasutra interval/indexed recurrence work | Every in-scope recurrence remains recoverable; explicit as-of/horizon. |
| P6 | Kshetra interval indexes, bounded streaming and recoverable publication | Complete generation only, immutable history, interruption/restart safety, retained counter-evidence. |

Before/after evidence must use the same input-generation vector, chart/conventions, horizon, methodology, hardware and cache regime. Capture wall/CPU time, peak memory, row/byte counts, I/O where available, and numerical/value differences.

Keep the complete Swiss global-state serialization boundary. Narrowing the lock or introducing process parallelism needs the approved architecture/contract review, not an unexamined speed tweak.

## 11. Consumer and cross-layer elevation — U01–U11

The layer is not complete if rich data is produced and then discarded or distorted in serving.

| Interface obligation | Required outcome |
|---|---|
| U01 | Full signed L2 structure, participants and domains survive into Yojaka/Kshetra and the answer. |
| U02 | Simultaneous clock intersection, meaningful method/root independence; not equality of arbitrary date pairs or union mislabeled as agreement. |
| U03 | Targeted obstructions, deduplicated roots and explicit missing/clear states. |
| U04 | Nearest future versus strongest later, complete recurrence ladder, explicit horizon/coverage; calibration claims separate. |
| U05 | Fallback preserves requested/effective filters and does not return unrelated results under an echoed request. |
| U06 | PACT/promise stages carry actual qualification/as-of; incomplete chains are not called complete. |
| U07 | Manifestation distinguishes activity from valence/probability; real zero, event subtype and duplicate-anchor roots are preserved. |
| U08 | Signed cross-domain relations use actual interval bridges and mechanisms. |
| U09 | Historical echo, outcome-derived selection and rectification are separated from prospective generation. |
| U10 | Stable temporal claim identity, original issuance/evidence/outcomes and revised windows remain accountable. |
| U11 | Capability/coverage fields and low-ranked delivery sentinels prove evidence is not silently lost at retrieval/budgeting. |

The existing first engineering slice `L3-SLICE-STRUCTURE-TIME-01` has recorded digest
`9a5f2f53892c72a8671bae373dd25e75a29982a3635884b99c1233fd8168a013`.
Its status remains **ENGINEERING_ONLY / UNQUALIFIED_SOURCE / non-promotable**. It is not product acceptance. Add a real qualified positive route, not just convincing negative “unavailable” behavior.

Compare actual Portal Paripraśna and managed MCP behavior using the same admitted evidence. Raw tool responses can be narrower, but must remain faithful. Show where the new information changes the answer or next action; a field merely existing in JSON does not prove value.

## 12. Forward execution plan after Claude Code activation

### 12.1 One conductor, finite prerequisite lane, asset lane

Use a single execution owner/conductor and independent review. The three original substantive workstreams are semantic/data-DAG, cost architecture, and consumer value. They can work in parallel when file and data ownership permit; they are not three competing campaign conductors.

For recovery, organize two operational lanes:

- **Lane A — bounded delivery prerequisite:** finish only the exact 1040/Pūrṇa route and protected migration/service delivery dependency. One named owner, one next action, measurable exit.
- **Lane B — asset closure:** preserve/reuse accepted source, advance the earliest genuinely eligible asset and independent semantic/performance/consumer work. Do not wait to perfect every asset's source before closing the first eligible asset.

Serialize migration reservations, generated files, merge integration, production writes and generation publication. Keep verifier independence. The user authorized high velocity, not unsafe concurrent writers.

### 12.2 First takeover interval

1. Read root `CLAUDE.md`, applicable directory instructions and its mandatory-reading/session-open sequence. If `CLAUDECODE_BRIEF.md` is active for another scope, reconcile it instead of overwriting it silently.
2. Read this handoff and governing authority documents. Confirm the user has activated Claude Code execution; keep old Codex continuation paused.
3. Refresh exact Git/worktree/PR/coordination/deployed revision/migration/head/evidence state. Compare against this snapshot; report only meaningful drift.
4. Inventory clean/unmerged source and create the isolated successor worktree as described in §3.
5. Set the goal to the full outcome in §15, without an arbitrary token budget. Set up a durable progress/next-action mechanism supported by the receiving environment, not an assumed Codex API.
6. Name the finite release dependency owner and ask the owning Pūrṇa lane for only its exact required lifecycle action if still absent. Do not repeat unsuccessful broad grant attempts.
7. Select the earliest asset acceptance candidate using actual type-specific/current-definition gates. `ka_graha_sancara` is a candidate, not automatic proof of independence.
8. Run implementation/review/materialization/acceptance packets, not another open-ended campaign-wide audit.

### 12.3 Dependency waves and exits

| Wave | Work | Measurable exit |
|---|---|---|
| W0 | Reconcile exact field/DAG/history contracts and benchmarks; retain accepted safety work | No unowned destructive/shared edges; tests and exact packet scope current. This is not permission for a global audit restart. |
| W1 | Finish protected delivery; materialize/select already-approved L0→L1→L2 compatible generations | Actual applied identities, served source/job image and independent generation/partition acceptance; current heads populated legitimately. |
| W2 | First-frontier roots/overlays/Avadhi/Yojaka and type-appropriate service work; Kshetra S0/S2 | Exact upstream vector, safe physical root results and terminal acceptance for eligible identities. |
| W3 | v2 windows, legitimately resolved century capability, Sangam; Kshetra S3 | Complete scoped transit/convergence coverage and correct testimony; no unresolved required century capability hidden. |
| W4 | Kalasutra, Vighnakara, Taranga; Kshetra S1 | Complete recurrence/opposition/class semantics from accepted upstream content. |
| W5 | Darshana; Kshetra S4 | Correct coherent temporal view and corrected field numerics, no missing/zero coercion. |
| W6 | Jivana Parva, Bhavishya; Kshetra S5 | Evidence-backed chapters/windows, history-safe issued identity, exact null/window/provenance. |
| W7 | Kshetra salience/insight/timeline and compatible snapshot; real data-bound Tulana/Muhurta | Complete publication/resume/rollback and constraint/comparison value. |
| W8 | U01–U11 serving and scoped consumers; independent reconciliation | Every one of 22 active identities legitimately terminal; layer data, deployment, consumer and value targets all earned. |

Waves identify dependency frontiers, not a rule that all source work must be serial. Data builds must obey accepted upstream order. Unchanged accepted content can be reused when its full dependency identity remains valid.

### 12.4 Essential operation sequence

For a production-changing packet:

1. Exact source, independent review, current upstream/definition and narrow authority.
2. Fresh coordination and actual build-run lock truth; operation-specific recoverability.
3. Protected merge and exact deployment/migration route.
4. Verify application identities and actual runtime revision/image, not workflow color.
5. Build/materialize against admitted upstream content; keep publication atomic/compatible.
6. Independent actual data, semantic, numerical, completeness and consumer checks.
7. Authenticate the proper acceptance/freeze event; update Accepted N/22 only then.
8. Preserve evidence, release only owned lease, immediately take the next eligible packet.

No builder self-certification. No direct terminal-event SQL shortcut. No old receipt repurposed as new evidence. A legitimate unchanged generation replay should be handled by its designed mechanism, not rebuilt unnecessarily.

### 12.5 Cadence and anti-stall rules

- Every packet names one next executable action and which asset acceptance condition it advances.
- Report `Accepted N/22; delta since last report; newly accepted IDs; current asset; exact blocker/owner/next action`.
- Keep source/data/deployed/consumer evidence separate; do not use test totals as a progress denominator.
- At most two identical transient retries; a deterministic repeat gets one finite root-cause packet, not more of the same.
- Use observed job duration, fresh build_runs and documented stale-log criteria. An unchanged log or six minutes of CI is not enough to cancel healthy work.
- While waiting, perform genuinely independent eligible work. If none exists, preserve an honest external block and a resumable next action; do not invent governance tasks to stay busy.
- Reuse accepted analyses/tests unchanged by the packet. No recurring full audit, repeated handoff rewrite, or unnecessary branch churn.
- Do not expand release recovery into global security, credential hygiene, unrelated planner work or a new orchestration platform.
- Existing essential safety is not “unnecessary governance.” Keep the finite checks that protect data/history/source/ownership and actual acceptance.

## 13. Definition of done and quality gates

A terminal asset disposition must be type-appropriate and evidenced at the current campaign definition. The exact current contract is authoritative; the checklist below summarizes the required dimensions:

1. Qualified purpose, source/method/context, full semantic/field obligations.
2. Correct current implementation closure; independent review; reproducible tests.
3. Actual upstream content-generation and partition lineage, not just code SHAs.
4. Complete compatible physical output where row-backed; actual invocation/serving evidence where service/pure.
5. Correct applicability, empty/unavailable/error, horizon and coverage states.
6. Corrected mathematical/numerical behavior with meaningful independent oracles.
7. Measured cost on representative cases; any approximation explicitly admitted.
8. History-safe publication/replay/rollback; no collateral shared-owner mutation.
9. Actual protected deployment/source/migration/runtime binding.
10. Actual consumer use and discriminating value, including positive qualified examples.
11. Independent authenticated terminal verification/freeze; truthful tracker reconciliation.

The complete campaign additionally needs coherent cross-asset behavior, the U01–U11 interfaces, all required active holds legitimately resolved, preserved retired history, a final exact-source/deployed/data-generation manifest, and **22/22**.

Do not claim empirical predictive performance as a by-product of engineering closure. Do not enter L4/L5 elevation automatically; return to Strategy for their separate planning.

## 14. Source reading map and reference-pack structure

### 14.1 Read in this order

1. **Repository operating context:** root `CLAUDE.md`, `AGENTS.md`, capability manifest, project architecture, applicable session/governance/current-state/CCD documents and directory instructions. Root cached layer-complete language is historical; current L3 elevation evidence is separate.
2. **Product:** Product Definition v3 and adoption/review record.
3. **Data plane:** Value Architecture v2; contribution register; strategic ledger; foundation contracts/acceptance; inventory baseline; layer and asset-interface execution-brief contracts.
4. **L3 intent:** Kāla Strategy, Execution Brief and Astra Review Record, then DP-SD-018/019/020.
5. **Current L3 evidence:** this live snapshot, coordination DP041–DP047, W0 safety/field/benchmark/numerical records, W2 source packet, RI01/RI02/provenance/security acceptance/cutover records, execution ledger.
6. **Upstream interfaces:** L0/L1/L2 strategy, producer-ready acceptance, semantic/source/context/fact/clock/structural/mechanism/compatibility contracts.
7. **Implementation:** exact current writer/import closure, consumer route, tests, migrations and delivery scripts for the next packet.

The pack's strategy snapshot contains L3 strategy/brief/Astra/DP-SD-018 documents not all present in the inspected main tree. Do not assume absence from main means these decisions never existed. Conversely, do not overwrite newer execution source with the older strategy checkout.

### 14.2 Critical named artifacts

All paths in this subsection are under `00_ARCHITECTURE/briefs/nirmana/` unless noted:

**Strategy**

- `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md`
- `MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md`
- `MADHAV_DATA_PLANE_STRATEGIC_LEDGER_v1_0.md`
- `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md`
- `MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md`
- `MADHAV_DATA_PLANE_L3_ASTRA_REVIEW_RECORD_v1_0.md`
- `MADHAV_DATA_PLANE_L3_UNBLOCK_AND_RESUME_AMENDMENT_v1_0.md`
- `MADHAV_DATA_PLANE_L3_EXECUTION_FOCUS_AMENDMENT_v1_0.md`
- `MADHAV_DATA_PLANE_L3_AUTOMATED_CUTOVER_AUTHORITY_AMENDMENT_v1_0.md`

**Execution and acceptance**

- `MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md` and foundation acceptance record.
- `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md` — detailed history; its older header is not live status.
- `MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md`
- `MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md`
- `MADHAV_DATA_PLANE_L3_W0_BENCHMARK_BASELINE_v1_0.md`
- `MADHAV_DATA_PLANE_L3_DHARA_NUMERICAL_CONTRACT_v1_0.md`
- `MADHAV_DATA_PLANE_L3_W2_FIRST_FRONTIER_SOURCE_v1_0.md`
- `MADHAV_DATA_PLANE_L3_RI01_PRECURSOR_INTEGRATION_v1_0.md`
- `MADHAV_DATA_PLANE_L3_RI02_AUTHORIZED_UNBLOCK_v1_0.md`
- `MADHAV_DATA_PLANE_L3_RI02_PROVENANCE_SUCCESSOR_v1_0.md`
- `MADHAV_DATA_PLANE_RI02_SECURITY_SOURCE_ACCEPTANCE_v1_0.md` and `v1_1.md`
- `MADHAV_DATA_PLANE_RI02_SECURITY_CUTOVER_v1_0.md`
- `MADHAV_DATA_PLANE_DP019_SOURCE_ACCEPTANCE_v1_0.md`
- `MADHAV_DATA_PLANE_DP019_KSHETRA_GATE_ACCEPTANCE_v1_0.md`
- `MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md`

**Earlier-layer producer readiness is not physical closure**

- L0 recorded producer-ready source `f6fed12c794224329f6b3b436f8b1b814499d06d`.
- L1 recorded terminal producer-ready source `18503e9c2dbb140f5d17b4bc34a5f6d087f97c38`.
- L2 recorded terminal producer-ready source `e5307fadef42cca557a1c0ca3c1831b1296e22b4`.

Read their complete acceptance and compatibility records, especially L1 condition/relation/clock and L2 structural-proposition/relation, mechanism/contradiction/investigator and resource-mechanism contracts. These are approved inputs to implement/materialize, not grounds to claim populated current generation heads.

**Historical predecessor references**

The old `L3_W1_ANALYSIS_*`, `L3_W2_DECIDE`, six-views/Kāla transformation records and old session state explain existing implementation/history. They do not override the current data-plane elevation campaign or create t3 acceptance. The package includes a bounded set of these contextual documents, not every archival campaign.

### 14.3 Unknowns and fresh checks still required

- Exact provider access available to the receiving Claude Code environment.
- Whether Pūrṇa ownership preparation or 1040 application occurs after this snapshot.
- Fresh branch/check/deployment/main drift.
- Full current end-to-end pipeline benchmark and century cost.
- Every asset's current source-to-main delta and noncanonical-chart behavior.
- All actual consumers' deployed value/positive-path evidence.
- Current live owner leases/build locks at the instant of a future operation.
- No global security/infra audit is implied by the read-only samples.

## 15. Copy-ready Claude Code kickoff

Use this only when the user is ready to activate Claude Code. It is included for transfer convenience; it has not been dispatched by Codex.

> Task name: **Execution — Data Plane — L3 Kāla Completion (Claude Code)**.
>
> Read MADHAV_L3_CLAUDE_CODE_HANDOFF_2026-09-19.md and its reference package, then root CLAUDE.md and the required governing documents. The adopted target is Product Definition v3 under CCD-010, Data Plane Value Architecture v2 under DP-SD-009, and full L3 elevation under DP-SD-017 with DP-SD-018/019/020 amendments.
>
> Goal: Complete the elevation of all 22 active L3 Kāla assets and the coherent layer, in actual source-and-data dependency order, to LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED. Preserve qualified meaning, canonical facts, full signed relationships, corrected numerics, history and issued claims, purpose boundaries, compatible generation lineage and protected retired ka_gochara_sweep. Obtain independent type-appropriate terminal acceptance/freeze for every active identity. Do not stop at source readiness, unblocking, PRs, tests or deployment. Do not begin L4/L5 elevation or empirical outcome-validation work.
>
> Begin with a bounded fresh takeover reconciliation, not a new full audit. Codex execution is stopped and its continuation heartbeat must remain paused. Establish one Claude Code conductor and independent verification. Start an isolated task worktree from freshly verified protected main, preserving any required reviewed unmerged packets. Suggested branch is codex/madhav-l3-claude-code; it has not been created. Do not use the stale closure branch or merge superseded PR #2655.
>
> At handoff, accepted progress is 0/22. Data-plane migrations 1035/1036 and dedicated builder binding are already live. The immediate release predecessor is Pūrṇa migration 1040 and its protected ownership lifecycle; 1041 is a compatibility no-op and remains unapplied. Recent green workflows skipped migrations/service deployment. Coordinate the smallest exact dependency with its owner; do not grant broad routine ownership, weaken isolation or reopen unrelated campaigns.
>
> Execute the finite delivery lane and genuinely independent asset/performance/consumer work in parallel where ownership permits. Preserve the reviewed W0/W2/Yojaka/DHARA/provenance work. Materialize/select accepted L0→L1→L2 generations before dependent L3 data; their current selected heads were empty. Follow the actual read/shared-write DAG, not registry declarations alone, through W2–W8.
>
> Use existing bounded authority autonomously for routine implementation, review, protected delivery and approved infrastructure/data operations, with fresh exact-operation evidence and actual available credentials. Do not ask for routine reapprovals already delegated; do not infer missing external entitlements or new policy authority. Keep independent review, leases, recovery, protected release, immutable history and authenticated acceptance. Never expose credentials or fabricate evidence.
>
> Drive every packet toward an identified asset's terminal acceptance. Report Accepted N/22 and the delta, source/data/deployed/consumer evidence separately, the exact next asset/action and any real external blocker. Avoid repeated whole-campaign audits, unrelated security/governance cleanup, unnecessary branch churn and premature cancellation of healthy work. If a prerequisite is unchanged, advance eligible independent work; if none exists, record the genuine blocker and resumable next action without manufacturing activity.
>
> Finish only when all 22 assets and the layer-level delivery/value gates are actually earned, then return the exact closure manifest to Strategy — Data Plane. The user will plan the next layer separately.

## 16. Handoff preparation scope and limitations

This handoff consolidates canonical strategy and recorded reviews, then refreshes Git/PR/run, Cloud Run/SQL/job and aggregate database state. It does not rerun the entire test suite or independently recertify every historical review.

The only external control changes during preparation were pausing the existing L3 continuation automation and sending the user-requested execution stop. A temporary local SQL proxy was used for read-only diagnostics and has been stopped. No database DML, migration, IAM/secret change, rebuild, merge or deployment was performed.

The task-specific asset-elevation and layer-value methodologies were used to separate product purpose, per-asset information, dependencies, source progress, physical acceptance and consumer value. They do not supersede the native's stop or the adopted contracts.

**The desired transfer outcome is continuity without false closure:** Claude Code receives the product intent, exact decisions, preserved achievements, current live gap, all 22 asset obligations, data DAG, cost programme, infrastructure and a finite execution path. The actual implementation remains to be completed.
