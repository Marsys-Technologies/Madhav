---
artifact: PURNA_ANVESANA_CLAUDE_CODE_RESUMPTION_STRATEGY
version: "1.0"
status: PROPOSED_FOR_NATIVE_REVIEW_NOT_EXECUTION_AUTHORITY
prepared_on: "2026-09-27"
evidence_cutoff: "2026-09-27T16:32:00+05:30"
campaign_id: madhav-purna-anvesana
prepared_by: Codex product-strategy conversation
intended_executor: Anthropic Claude Code in a dedicated isolated Git worktree
execution_authority: none
production_authority: none
branch_or_worktree_created: false
supersedes: none
primary_review: 00_ARCHITECTURE/briefs/nirmana/PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md
primary_handoff: 00_ARCHITECTURE/briefs/nirmana/PURNA_ANVESANA_INDEPENDENT_REVIEW_HANDOFF_v1_0.md
---

# Pūrṇa Anveṣaṇa — Claude Code resumption strategy

## 1. Decision in one page

Pūrṇa Anveṣaṇa should resume, but it should **not** resume inside the old Codex task, the shared
Madhav repository root, the product-strategy checkout, the L3 integration checkout, or the open
PR #2705 branch. The safe resumption is a new Claude Code campaign rooted in one new, stable,
named Git worktree based on freshly fetched protected `origin/main`.

The old campaign is not discarded. Its merged foundation, open candidate, local red-first tests,
plans, evidence, and execution transcript become a read-only salvage library. The new branch takes
forward only deltas that survive a current-main and architecture review. Generated artifacts and
campaign projections are regenerated from the new branch; they are not copied as truth from the
September 20 candidate.

Recommended target:

| Item | Recommendation |
|---|---|
| Worktree | `/Users/Dev/madhav-purna/resumption` |
| Branch | `codex/purna-anvesana-resumption-v2` |
| Base | freshly fetched `origin/main`; record the exact SHA at creation |
| Executor | one Anthropic Claude Code integrator session |
| Parallel workers | only packet-specific Claude workers in separate child worktrees, if needed |
| Old Pūrṇa worktrees | read-only until salvage is accepted and the new candidate is reproducible |
| Shared root | `/Users/Dev/Vibe-Coding/Apps/Madhav` is prohibited for Pūrṇa writes |
| L3/data-plane checkouts | prohibited for Pūrṇa writes; dependencies flow through main, PRs, or recorded contracts |
| Progress control | runnable packet queue and milestone evidence; no timer-only heartbeat loop |

The resumption has two distinct macro-phases:

1. **Preparation and preservation:** prove what exists, preserve all residual work, reconcile the
   architecture against current main, create the isolated workspace, and earn a go/no-go packet.
2. **Execution resumption:** perform the independent review's P0–P9 repair sequence in product-value
   order, beginning with build/generation truth and ending with candidate and live three-door
   acceptance.

No implementation, branch creation, worktree creation, PR change, deployment, database mutation,
or campaign-state mutation is authorized by this document.

## 2. What actually happened

### 2.1 The original executor was physically separate

The original execution task, `Madhav — Planner & Inquiry Product Completion II`
(`01a0b7d8-9a90-74f3-aab9-80014919f8b2`), was attached to:

`/Users/Dev/.codex/worktrees/a4c6/Madhav`

Its command history was overwhelmingly confined to Pūrṇa-named worktrees. The observed command
working-directory counts include:

- 1,487 operations in the task's `a4c6` worktree;
- 452 in `purna-wealth-near-miss`;
- 289 in `purna-bounded-collector`;
- 249 in `purna-wealth-evidence-join`;
- smaller counts in other Pūrṇa-owned packet worktrees;
- four operations in the temporary `l3-pr2695-review` checkout.

No broad write pattern into the current L3/data-plane elevation worktrees was found. Therefore the
evidence does **not** support a conclusion that the original Pūrṇa executor generally overwrote a
data-plane worktree.

### 2.2 The conflict was nevertheless real

The conflict existed in four forms:

1. **Shared architectural surface.** Pūrṇa legitimately changed data-plane ownership, deployment,
   producer-receipt, migration, and L3-dependent surfaces. For example, its protected repair
   included `fix(data-plane): allow Purna owner schema usage`.
2. **Cross-branch coupling.** PR #2704 is a Pūrṇa golden-alignment commit whose base is the L3
   branch `codex/madhav-l3-claude-code`, not `main`. It made the Pūrṇa campaign dependent on an
   L3 branch even though the later independent review found that PR #2705's failures were
   self-generated and not a #2704 dependency.
3. **Strategic-checkout cohabitation.** The independent review read the Pūrṇa candidate worktree but
   wrote its sole artifact in the detached product-strategy checkout. That checkout also contains
   product-definition and data-plane strategic material. This was controlled and document-only,
   but it makes the folder unsuitable as the next implementation base.
4. **Unsafe shared repository root.** A recent data-plane strategy session was attached to
   `/Users/Dev/Vibe-Coding/Apps/Madhav`. That root is currently on the old
   `campaign/nirmana-autonomous` branch and has a large dirty working tree containing active and
   historical Nirmāṇa material. A Claude Code session opened there can easily confuse current main,
   campaign residue, and untracked work.

The correct diagnosis is therefore **ownership and integration collision with a high-risk shared
root**, not proven widespread physical overwrite by the original Pūrṇa task.

## 3. Current Pūrṇa estate

### 3.1 What is already protected on main

The valuable foundation is largely in protected main and should not be rebuilt:

- Inquiry Contract compilation, floors, omission challenge, graph traversal, and closure semantics;
- durable inquiry lifecycle, evidence receipts, reservations, and managed-job storage;
- response-accountability machinery and high-cardinality regressions;
- real three-door collection, tamper protection, frozen 5+30 cases, and independent assessment;
- protected release and earned-outcome gates;
- capability knowledge model and fail-closed overlays;
- technical delivery repairs through Pūrṇa events PA-E0105–PA-E0109;
- applied Pūrṇa/data-plane migrations and least-privilege ownership posture already recorded.

Protected `origin/main` was observed at `6b26f3ff0` on this review. That is an evidence point, not the
future branch pin; preparation must fetch again and record the then-current main SHA.

### 3.2 The active unmerged candidate

PR #2705, `codex/purna-wealth-near-miss`, is still open at `34991645b`:

- 41 candidate-only commits;
- 15 changed files;
- approximately 1,266 insertions and 89 deletions relative to its merge base;
- 28 protected-main commits have advanced on the other side;
- GitHub currently reports it as conflicting/dirty;
- CI has a unit-test failure and a fact-category pinning failure;
- most of its apparent completion is catalogue accounting and regenerated projections, not the
  product repairs identified by the independent review.

Its useful source deltas are concentrated in capability availability, classical attribution,
Sūtrāvalī source contracts, composite availability, and related tests. Its campaign records and
generated snapshots must not be transplanted without regeneration.

### 3.3 Local uncommitted residuals that must be preserved first

Two Pūrṇa worktrees are dirty:

1. `/Users/Dev/.codex/worktrees/purna-focused-completion`
   - untracked focused-completion plan;
   - SHA-256 `023bc0705819a92b8b2cf9605b57f9d87ef7fcc9e9c17065393d45af4d062f88`.
2. `/Users/Dev/.codex/worktrees/purna-wealth-near-miss/Madhav`
   - modified live DB integration expectation for `notably_absent_yogas`;
   - untracked red-first near-miss contract test;
   - test-file SHA-256 values recorded in the stocktake as
     `31d2a8d02cc6ea7cf08e9a0967b86e0d71e65bc63837245cd416d0db8b331e27` and
     `445b044db87e366a418f640086ba2f4de2ee24ebba345463b65b67c2abdb800f`.

The independent review explicitly says these red-first tests should be preserved. They are not yet
an approved implementation and must not be committed directly onto PR #2705 merely to save them.

### 3.4 Open review surfaces

- PR #2705 targets `main`; it is the principal salvage source, not the resumption branch.
- PR #2704 targets the L3 integration branch; it is not the dependency PR #2705 claimed it was.
- old Wave 0–7 stacked PRs remain open even though their aggregate foundation was already merged.
  They are historical clutter, not new work; close them only after an explicit ancestry check.
- the old autonomous monitor is absent. It must not be recreated as a ten-minute polling loop.

### 3.5 Campaign state

The campaign is materially advanced but not accepted. It earned source and technical-delivery
milestones, then its first live three-door wealth slice produced 0/3 accepted doors. The later
independent review established that this was not merely an evidence-collection problem: production's
build identity, replacement fence, strength attestation, near-miss production, deep planning,
continuation, and fact-delivery contracts contained real product blockers.

## 4. Architecture to resume, not the old task list

The independent review should be adopted as the diagnostic baseline, subject to a current-main
revalidation during preparation. Its central conclusion is sound: the substrate is salvageable and
does not require a rewrite, but four bounded replacements are needed.

### 4.1 Replacement A — per-asset generation truth

Replace the false chart-wide rule “latest completed build run is the active build” with one shared
per-asset generation resolver used by availability, judgment, checklist, and evidence consumers.
Use the generation-head structures already introduced by the data-plane architecture where they are
semantically valid. Do not make every consumer invent its own generation query.

### 4.2 Replacement B — accurate in-progress fencing and attestation

The replacement fence must only treat genuinely active work as in progress. Terminal-run orphan rows
cannot block consumers forever. `ga_strength` then needs one governed rebuild under the active digest
spec and a fresh receipt; a permission grant is not build completion.

### 4.3 Replacement C — a real near-miss product

`notably_absent_yogas` cannot remain hardcoded `not_computed`, and absence cannot be inferred from the
absence of fired L1 rows. Ratify a bounded yoga candidate and eligibility rule, produce qualified L2
absence/near-miss signals through `bo_laksana`, and consume them in judgment and wealth evidence.

### 4.4 Replacement D — real inquiry depth and complete delivery

Deep reasoning must reach the selected provider and use the strongest approved reasoning route;
evidence-driven continuation must be able to admit a newly relevant authorized capability, not only
fetch the next page of the same one. The fact register must cover exactly the evidence visible to
synthesis, and all three doors must enforce and expose the same accountability contract.

### 4.5 Availability proof typing

Planning resources, source queries, service probes, materialized producer outputs, and derived
composites cannot share one proof rule. Reclassify the 19 dark bindings by correct proof kind and
repair required groups by shared root, not by adding boilerplate dispositions one binding at a time.

## 5. Target workspace and ownership model

### 5.1 The integrator worktree

Create exactly one primary worktree after preparation approval:

```text
/Users/Dev/madhav-purna/resumption
  branch: codex/purna-anvesana-resumption-v2
  base: freshly fetched origin/main@<recorded-sha>
```

Why a linked worktree, not a separate clone:

- full repository history and existing refs remain available for surgical salvage;
- the new folder has an independent index and working tree;
- branches and PR ancestry remain transparent;
- no manual copying of the repository or hidden divergence is introduced.

### 5.2 Hard isolation rules for Claude Code

Before the first write, Claude Code must print and record:

- physical current directory;
- Git top-level directory;
- branch name and exact HEAD;
- `origin/main` SHA used as base;
- clean/dirty status;
- all active worktrees that own any file family it expects to change.

The session must stop if the top-level directory is not the dedicated Pūrṇa worktree, if the branch is
not the Pūrṇa resumption branch, or if unexpected pre-existing changes appear.

Claude Code must not use `git -C` to write into:

- `/Users/Dev/Vibe-Coding/Apps/Madhav`;
- `/Users/Dev/.codex/worktrees/0ee2/Madhav`;
- `/Users/Dev/madhav-l3/**`;
- `/Users/Dev/.codex/worktrees/ai-console-design/Madhav`;
- any old Pūrṇa worktree.

Old worktrees are read-only inputs. A required dependency from another campaign is obtained through a
protected main commit, a reviewed PR, or an explicit cross-campaign contract—not by editing its folder.

### 5.3 Parallel work

The default is one Claude Code integrator. If parallel writers become necessary, create separate child
worktrees under:

```text
/Users/Dev/madhav-purna/workers/<packet-name>
```

Each worker receives a disjoint file manifest and one integration commit. One integrator alone owns:

- generated capability artifacts;
- campaign state and event records;
- migrations and migration numbering;
- acceptance baselines and route goldens;
- release workflow changes;
- the final candidate branch and PR.

No worker rebases or merges another active campaign branch.

### 5.4 Private evidence

Live configurations and restricted collections must not live only inside an expendable worktree and
must never enter Git. Preparation should establish one owner-approved, access-restricted evidence root,
for example:

`/Users/Dev/Madhav-Private/purna-anvesana/`

Store only the minimum required versioned configurations, receipts, hashes, and redacted reports. Keep
credentials outside the artifacts. The repository records evidence identifiers and hashes, not private
chart payloads or secrets.

## 6. Preparation phase

Preparation is a real phase with its own exit criteria. It should take roughly 1.5–2.5 focused days,
depending on current-main drift. It does not include production mutation.

### PREP-0 — Freeze and writer census

1. Confirm the old Pūrṇa task remains stood down and no Pūrṇa monitor exists.
2. Inventory active Madhav tasks, worktrees, branches, PRs, leases, migrations, and generated-artifact
   owners.
3. Mark the shared root, product-strategy checkout, L3 checkouts, AI Console checkout, and old Pūrṇa
   worktrees `READ_ONLY_FOR_PURNA` in the handoff.
4. Record current protected main and current serving revisions as observations, not acceptance.

**Exit:** one timestamped writer/ownership map with no ambiguous shared writer.

### PREP-1 — Lossless preservation

1. Export a branch/head/worktree/PR manifest.
2. Preserve the two dirty worktrees as content-addressed patches plus untracked-file copies in a stable
   preservation directory; retain the hashes above and generate a manifest hash.
3. Preserve the old task transcript, independent review, handoff, current campaign records, and
   restricted live evidence by reference.
4. Do not clean, reset, switch, archive, or delete any old worktree during preservation.
5. Verify the preserved patch can be applied to a disposable checkout before relying on it.

**Exit:** every committed and uncommitted residual has a reproducible source or content-addressed copy.

### PREP-2 — Current-main salvage matrix

Compare `origin/main`, PR #2705, PR #2704, the two dirty residuals, and the independent review.
Classify every Pūrṇa-only delta as:

- **already protected** — no action;
- **salvage as concept and code** — transplant or rewrite against current interfaces;
- **salvage as test only** — red-first proof retained;
- **regenerate** — snapshots, census, route goldens, acceptance artifacts;
- **historical record only** — old campaign projections and intermediate evidence;
- **drop/supersede** — wrong dependency classification, stale build proxy, boilerplate darkness.

Do not rebase the full 41-commit PR #2705 chain as the first move. Build a semantic patch plan by file
and behavior; otherwise stale projections and the failed abstraction will be carried forward together.

**Exit:** a reviewed salvage ledger that accounts for all 15 PR #2705 files, four PR #2704 files, and
three dirty residual files.

### PREP-3 — Architecture reconciliation

Revalidate the independent review's RC-1 through RC-10 findings against current main and the now-current
data-plane/L0/L2/L3 contracts. Specifically confirm:

- which generation-head tables are now populated or still empty;
- the correct per-asset generation source of truth;
- the exact terminal-run orphan predicate;
- the current `ga_strength` digest spec and receipt state;
- `bo_laksana`'s present signal contract and the required near-miss candidate rule;
- current provider/model routing and reasoning parameter transport;
- synthesis-visible evidence and all three response wire formats;
- current deployment revision policy and compatibility contract;
- migration-number frontier and any active unmerged migration reservation.

This is also the point to align Pūrṇa with the final product and data-plane definitions without pulling
ongoing elevation work into the campaign. Pūrṇa consumes stable contracts; it does not become the data-
plane elevation owner.

**Exit:** architecture addendum with confirmed, changed, and retired review findings.

### PREP-4 — Resolve the minimum Native/owner decisions

Only decisions that materially change implementation remain gates:

1. **Near-miss semantics:** ratify the bounded candidate set, eligibility rule, qualification language,
   and non-claim boundary.
2. **Private evidence root:** approve the stable restricted location and owner.
3. **Production actions:** retain just-in-time authority for orphan repair, `ga_strength` rebuild,
   candidate deployment, and live acceptance. Preparation does not imply these actions.
4. **Deep route:** select by outcome—strongest approved reasoning route within the existing provider
   and cost policy—rather than hardcoding a model name in the strategy.
5. **Judge budget:** run a three-case candidate calibration first; expand to 105 door executions only
   after deterministic gates and cost telemetry are sound.

PR #2704 should be withdrawn from Pūrṇa after PREP-2 confirms no unique main-targeted delta is needed.
Its current L3 branch ownership is not a Pūrṇa completion dependency.

**Exit:** signed decision packet with no unresolved architectural choice on the critical path.

### PREP-5 — Create and seal the isolated workspace

1. Fetch and verify current protected main.
2. Create the dedicated branch/worktree at the target path.
3. Confirm clean state and record exact base SHA.
4. Install/reuse dependencies without copying build outputs from dirty worktrees.
5. Run a narrow baseline: typecheck, knowledge codegen freshness, Pūrṇa unit suites, generation resolver
   probes, three-door contract tests, and migration collision scan.
6. Record pre-existing failures separately; do not launch a broad cleanup campaign.

**Exit:** clean isolated worktree with reproducible baseline and no foreign changes.

### PREP-6 — Issue the Claude Code execution brief

The brief must contain:

- objective and non-goals;
- exact worktree, branch, and base SHA;
- authoritative artifact order;
- salvage ledger;
- architecture addendum;
- packet queue and file ownership;
- stop/continue rules;
- allowed production actions and explicit just-in-time gates;
- acceptance denominator: original five/34 routes plus 30 product cases across three doors;
- status language distinguishing source-ready, candidate-accepted, protected, deployed, live-accepted,
  and complete.

Claude Code must acknowledge the worktree and authority boundary before changing a file.

**Exit:** copy-ready brief reviewed from the new worktree, not from the shared root.

### PREP-7 — Go/no-go

Proceed only if:

- preservation is reproducible;
- the new workspace is clean and isolated;
- current-main architecture reconciliation is complete;
- no active campaign shares a write surface without an owner;
- near-miss semantics and generation ownership are decided;
- required production actions are separated from source implementation;
- the first two execution packets are runnable without waiting on another campaign.

## 7. Execution resumption

The independent review's P0–P9 sequence remains the best skeleton. The following waves turn it into a
Claude Code execution programme with explicit outcomes.

### Wave R0 — Reconciliation and branch truth

Corresponds to review P0.

- transplant only approved PR #2705 source deltas;
- regenerate its own acceptance artifact, snapshots, census, and route goldens;
- convert line-fragile allowlist entries to semantic/pattern matches after verifying the underlying
  probes are unchanged;
- correct the false #2704 dependency record;
- leave PR #2704 and L3 ownership outside this branch;
- establish one current campaign projection.

**Exit:** clean CI on the reconciled source candidate, with no generated artifact borrowed from another
branch and no claim of product completion.

### Wave R1 — Make evidence selectable and unblocked

Corresponds to review P1, P2, and source portion of P3.

1. Implement one per-asset generation resolver and migrate the four Pūrṇa consumers to it.
2. Repair replacement-fence predicates and add terminal/orphan/adversarial tests.
3. Prepare the governed `ga_strength` rebuild packet and consumer receipt verification.
4. Run a candidate-side non-wealth vertical slice to prove generation and fencing before the near-miss
   domain rule is ready, where possible.

The production orphan repair and strength rebuild are separately leased actions; source work continues
until those gates are actually required.

**Exit:** consumers select correct per-asset generations, stale terminal rows do not block, and receipt
validation fails closed for genuinely missing/stale evidence.

### Wave R2 — Close the canonical wealth path and real inquiry behavior

Corresponds to review P4, P5, and P6.

- produce the ratified L2 near-miss/absence band and consume it in judgment and wealth evidence;
- wire the deep reasoning request through the provider and correct deep/fast routing;
- allow evidence-driven authorized widening while preserving the original contract and accumulated
  evidence;
- make the synthesis model and fact register consume the same evidence set;
- enforce accountable delivery on Portal, managed MCP, and governed raw MCP;
- repair collector wire-field extraction and emit typed deterministic-gate receipts;
- prove the 200th contributing fact survives independently on every door.

P5 and P6 may proceed in parallel only after their shared response/evidence interfaces are frozen.

**Milestone M1:** one canonical candidate inquiry returns a substantive answer through all three doors,
with the same normalized evidence, explicit omissions, complete fact register, and honest closure.

### Wave R3 — Repair the estate by proof family

Corresponds to review P8 and the start of P7.

- retype planning resources, source queries, service probes, producer outputs, and composites;
- repair required strength, sidecar-probe, direct-composite, and attribution groups;
- expose qualified partial modes where evidence is genuinely partial;
- retire or repoint legacy descriptor promises;
- keep optional capabilities explicit without using them to reduce the acceptance denominator.

Run the candidate corpus progressively after M1; do not wait for all semantic cleanup before obtaining
real product feedback.

**Exit:** every required case dependency has the right executable proof contract, and no supported
capability is dark merely because the proof model is wrong.

### Wave R4 — Candidate acceptance

Corresponds to review P7.

- run the frozen five cases/34 routes plus 30 product cases across Portal, managed MCP, and raw MCP;
- 35 cases × 3 doors = 105 candidate executions;
- start with the three-case judge/cost calibration;
- deterministic evidence, closure, date, authorization, fact-accountability, and insufficiency gates
  override model-judge praise;
- preserve failures and rerun only affected cases plus the immutable core regression set;
- prove interruption, pagination, and cross-instance recovery on the candidate environment.

**Exit:** 105 candidate executions have complete, revision-pinned evidence and all mandatory gates pass.

### Wave R5 — Protected delivery and live close

Corresponds to review P9.

- integrate through cohesive PRs; do not replay one full deployment per small fix;
- use the existing protected candidate/canary/promotion path;
- verify actual web, MCP, sidecar, and pipeline revisions and compatibility, not assumed same-SHA
  identity where deployment policy intentionally differs;
- repeat the 105 executions on live traffic;
- verify one longest supported continuation/recovery path;
- reconcile campaign state once with exact accepted and excluded claims.

**Exit:** `PRODUCT_DELIVERY_COMPLETE_AUTOMATED_ACCEPTANCE` is earned only when live evidence, not source
or CI, satisfies the accepted denominator. Human-expert empirical research remains separately
`NOT_RUN` unless separately commissioned.

## 8. Execution-control rules

1. A queue item must end in a code/test/evidence delta, a named external wait, or a decision packet.
2. Waiting on CI, review, or one producer does not block independent packets.
3. No ten-minute “still blocked” heartbeat. Wait on events or continue another packet.
4. Three repeated failures trigger a diagnosis and packet rewrite, not automatic abandonment of the
   campaign and not a loop of unchanged retries.
5. No broad lint, governance, security, or historical cleanup unless a failing required scenario or
   protected release gate demonstrates the dependency.
6. Generated artifacts have one owner and are regenerated only after source stabilizes.
7. Campaign records are updated at product milestones, not every edit.
8. Production mutation, deployment, IAM, secrets, chart permissions, and expensive assessment retain
   their explicit authority boundaries.
9. A PR, green source suite, merge, deployment, or matching dark state is never product acceptance.
10. Claude Code stops immediately if it discovers it is writing outside the dedicated Pūrṇa worktree.

## 9. What must not be lost

The resumption is only successful if it preserves all of the following:

- merged foundation and protected delivery repairs;
- original five/34-route regression denominator and 30 product scenarios;
- frozen corpus fingerprint and tamper-evident collection design;
- durable lifecycle, reservation, and recovery semantics;
- existing authorization, least privilege, and migration fail-closed controls;
- source/CI/live evidence distinctions;
- PR #2705's useful availability and source-contract work after semantic review;
- the two uncommitted near-miss red-first tests;
- the focused-completion plan as historical input, not as current authority;
- independent review v1.0 and its root-cause evidence;
- failure evidence from the first live three-door slice;
- explicit declaration that human-expert research remains unrun.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Claude Code opens the shared root | hard path/branch preflight; dedicated folder; stop-on-mismatch |
| old PR is rebased wholesale | semantic salvage ledger; regenerate projections and goldens |
| Pūrṇa silently becomes data-plane owner | consume stable contracts; cross-campaign PR/lease for producer changes |
| old uncommitted tests disappear | content-addressed preservation before any cleanup |
| migration collision | just-in-time migration scan and sole migration owner |
| L3 dependency returns | main-targeted compatibility contract; no Pūrṇa PR based on L3 branch |
| catalogue accounting replaces product proof | M1 three-door answer before estate closure; 105 candidate and 105 live executions |
| timer loop stalls again | runnable packet queue and event-driven waits |
| evidence leaks into Git | restricted external evidence root; hashes and IDs only in repository |
| governance consumes the campaign | only delivery-critical controls; milestone-level records |

## 11. Effort and milestones

These are focused-engineering ranges, not calendar promises:

| Phase | Effort | Milestone |
|---|---:|---|
| Preparation | 1.5–2.5 days | isolated clean workspace and approved execution brief |
| R0 | 1–1.5 days | reconciled candidate and accurate current state |
| R1 | 3–4 days plus build wait | generation/fence/strength path sound |
| R2 | 5–8 days | M1: one complete three-door candidate inquiry |
| R3 | 3–5 days, partly parallel | required capability proof families sound |
| R4 | 1–2 days plus model/runtime time | 105 candidate executions accepted |
| R5 | 1–2 days plus CI/deploy time | 105 live executions and campaign close |

The independent review's 9–14 engineer-day critical-path estimate remains plausible for execution;
current-main reconciliation and isolation preparation add the preparation allowance above. The largest
uncertainties are the near-miss domain rule, production data repair/rebuild, and defects discovered by
the first genuinely complete three-door inquiry.

## 12. Recommended authorization sequence

The Native should authorize in stages:

1. **Preparation authorization:** preservation, read-only reconciliation, isolated worktree creation,
   baseline verification, and final Claude Code brief. No implementation or production mutation.
2. **Source-execution authorization:** R0–R3 in the dedicated worktree, with no deployment or production
   mutation except separately approved producer operations.
3. **Candidate/live authorization:** candidate environment, bounded judge spend, protected delivery,
   and live acceptance after source and deterministic gates pass.

The immediate next decision is whether to authorize **Preparation only**. If approved, the next output
from this strategic conversation should be a preservation manifest, salvage matrix, architecture
addendum, exact worktree/base record, and copy-ready Claude Code kickoff brief—not code changes.
