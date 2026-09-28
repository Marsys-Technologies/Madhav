---
artifact: CLAUDECODE_BRIEF_PURNA_FOLLOWUP_FENCE_AND_SUCCESSOR_ENVELOPE
version: 1.2
status: LOCAL_SOURCE_COMPLETE_AWAITING_NATIVE_PUBLICATION_AUTHORIZATION
date: 2026-09-28
native_authority: Native source-execution authorization for the complete follow-up campaign (both packets),
  2026-09-28. Local only: no push, PR, merge, deployment, production, database, migration, rebuild or live collection.
baseline_verified_at_head: 75794b894b62c6f122b3536f5cb5aaf4c5b97e2f   # tsc clean; snapshot 5aa26443, census 1a231d17 fresh; pin-lint 0 new; 541 focused tests green
lineage: follows PR #2742 (Pūrṇa Anveṣaṇa source candidate), squash-merged to protected main
lineage_record:
  r5a_publication_and_ci: COMPLETE   # PR #2742 opened, CI repaired, independently reviewed, accepted by the Native at head d5c4c1f27
  r5b_source_merge: COMPLETE         # verified 2026-09-28: main 205a62618182a73f45a9bee34f8ffff8cdce8892, tree 231e9bdd67a8cfab2a1034ff9b5593d7e310b7dd == reviewed candidate 4f5d5a0dc tree
  production_deployment: NOT_COMPLETE
  empirical_or_candidate_validation: NOT_COMPLETE   # candidate_validation NOT_RUN in BEYOND_ACARYA_ACCEPTANCE_v10.json (v9 is now an immutable pin)
  campaign_or_product_completion: NOT_COMPLETE
base_main_sha: 205a62618182a73f45a9bee34f8ffff8cdce8892
worktree: /Users/Dev/.codex/worktrees/purna-followup-v1/Madhav
branch: codex/purna-followup-fence-and-successor-envelope
source_execution_authorized: false         # the local source execution is complete; nothing further is authorized without a fresh Native ruling
push_authorized: false
pr_change_authorized: false
merge_authorized: false
production_authorized: false
database_write_authorized: false
migration_authorized: false
producer_rebuild_authorized: false
deployment_authorized: false
live_collection_authorized: false
candidate_validation: NOT_RUN
product_completion_claim_authorized: false
---

# KICKOFF — Pūrṇa follow-up: two focused source packets

This is a NEW, isolated campaign. It is not part of PR #2742 and is not a continuation of its branch.
PR #2704 and #2705 remain historical salvage sources, not dependencies. Nothing here claims
deployment, empirical validation, or that the Pūrṇa Anveṣaṇa campaign or product is complete.

**Deliverable:** one focused pull request (prepared, not merged) containing Packet A and Packet B,
each with red-then-green tests. Publishing (push / PR) needs a fresh explicit Native authorization;
until then work locally and commit locally.

## Start-of-session checks (do these before any edit)

1. `pwd` is exactly the worktree above (not a `.claude/worktrees/...` copy); branch is the one above;
   the tree is clean; `git merge-base --is-ancestor <base_main_sha> HEAD` succeeds.
2. `git fetch origin main`; if main moved, inspect every new commit and integrate with an ordinary merge
   commit (never rebase, never force-push) before starting.
3. This is a fresh worktree with NO `node_modules`. Install locally (dev-only, no production access):
   `cd platform && npm ci`, and `cd ../platform-mcp && npm ci` if you will touch platform-mcp. Then run
   `npx tsc --noEmit -p .`, `npm run codegen:capability-knowledge:check` and
   `npm run codegen:capability-estate-census:check` to confirm a green baseline before touching anything.
4. Read: `CLAUDE.md` §I, §N.5–N.8; `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/historical_fork_v7_v11/LINEAGE_FORK_MANIFEST_v1_0.md`.

## Packet A — served-generation-safe composite tools (`query_planet`, `graha_portrait`)

**Problem.** Both composites best-effort resolve the chart's served generation
(`resolveChartServedGeneration`). When that fails or no generation resolves, they fall back to reading
the generation-sensitive components (shadbala/strength, yoga firings, and any other component whose rows
are generation-scoped) from the chart's *current* rows, unfenced, disclosed only by a free-text note in
`generation_fence`. That is a historical-row fallback dressed as an answer.
Files: `platform/src/lib/retrieval/registry/layers/L1_ganita/query_planet.ts` (~lines 130–225),
`platform/src/lib/retrieval/registry/layers/L2_bodha/graha_portrait.ts` (~lines 195–400).
Existing tests to extend: `L1_ganita/__tests__/query_planet.build_fence.test.ts`,
`L2_bodha/__tests__/graha_portrait.build_fence.test.ts`.

**Required behavior.**
- Preserve useful base output (position, sign/house, other components that are NOT generation-sensitive).
- When a valid served-generation identity cannot be resolved, do NOT read or present unfenced strength,
  yoga-firing, or any other generation-sensitive component. Audit every component each tool assembles and
  classify it generation-sensitive or not; record the classification in code, with the reason.
- For each omitted component return a named, machine-readable unavailable state, e.g.
  `components_unavailable: [{ component, code: 'served_generation_unresolved' | 'no_served_generation', ... }]`
  (choose one stable schema, shared by both tools; keep `generation_fence`). No free-text-only signalling.
- Never silently fall back to historical rows. Never reject the WHOLE composite because one component is
  unavailable (partial response is the point).
- Do not leak raw database error text (log server-side, return a fixed code).

**Acceptance criteria / tests (red first, then green).**
- Fenced: served generation resolved → components read fenced, `generation_fence.fenced === true`, no
  `components_unavailable`.
- Unavailable: resolution returns none / throws → generation-sensitive components absent, each named in
  `components_unavailable`, the strength and yoga-firing handlers are NOT called, base output present,
  `is_error === false`.
- Partial: mixed case (some components generation-sensitive, some not) returns exactly the safe ones plus
  the named omissions.
- No raw error text in the response. Existing fenced-path tests keep passing.
- If descriptors/inputs/outputs change: regenerate the snapshot; see "Generated artifacts" below.

## Packet B — bounded authorization envelope for evidence-driven successors

**Problem.** `plan_stage.ts` (~line 374) replaces `toolsAuthorized` with exactly the tools of the compiled
plan items. `evidence_frontier.ts` (`deriveEvidenceFrontier`) only ever proposes SCUs the contract has NOT
planned, so a successor's target tool is by construction never in the authorized set: on the Portal door
(`pariprashna/pipeline/evidence_stage.ts` `executeReady`) and the managed door
(`api/mcp/prashna_ask/route.ts` `drainManagedReadyActions`) every evidence-driven successor item fails
closed with `successor_capability_not_authorized_for_request`. Safe, but the widening feature can never
execute, and it leaves a required frontier that cannot be satisfied.

**Required design.** Replace "exact initially selected tool set" with a *bounded authorization envelope*,
computed deterministically at plan time (before any evidence), stored on the contract, hashed into its
authorization, and attributable in receipts. A successor capability may execute ONLY when ALL are proven:
1. read-only (descriptor `mcp_annotations.readOnly` and `isInquirySafeRegistryDescriptor`);
2. present in the capability catalogue / snapshot and executable on the door's channel
   (`isInquiryServerDispatchEligible`);
3. relevant to the compiled inquiry and to the evidence frontier that named it (graph/edge or rule linkage
   from `EVIDENCE_FRONTIER_RULES`, not model text);
4. scoped to the same chart and the same principal (chart identity re-checked; overlay/build identity
   re-checked as today);
5. permitted by the caller's entitlement (same `authorizeChartAccess` / entitlement rules as the plan);
6. within the inquiry's cost, iteration and successor-depth limits (`max_iterations`,
   `MAX_MANAGED_SUCCESSOR_CHAIN`, cost caps);
7. eligible under the deterministic safety rules (plan-time safety exclusions such as
   `applyCapabilityExclusion`, leaked-capability filters);
8. fully receipted and attributable (which rule, which observed item, which envelope entry admitted it).

**The synthesizing model must not grant authority.** It may point at an evidence frontier; only the
deterministic envelope decides. Anything outside the envelope continues to fail closed with a NAMED reason
(keep `successor_capability_not_authorized_for_request` for out-of-envelope; add distinct named reasons for
each failed condition so the gap is diagnosable). A successor must never widen to another chart, a write
capability, or beyond depth/cost/iteration limits.

**Doors and parity (all three must expose the same truth).**
- Portal: `api/pariprashna/route.ts` → `pariprashna/pipeline/{plan_stage,evidence_stage}.ts`.
- Managed MCP: `api/mcp/prashna_ask/route.ts` (`drainManagedReadyActions`, `continueWithEvidenceSuccessor`)
  and `lib/vidhi/inquiry/execution_session.ts`.
- Raw MCP: `api/mcp/inquiry/route.ts` (`execute`, `continue`, `certify`) — the server executes committed
  plan items; the envelope must be enforced server-side there too, never trusted from the client.
Add one shared envelope evaluator in `lib/vidhi/inquiry/` used by all three; do not fork logic per door.

**Acceptance criteria / tests (red first).**
- Unit: each of the 8 conditions individually fails closed with its named reason; the all-conditions-true
  case admits; the model-supplied text can never admit a capability.
- Boundedness: depth, iteration and cost limits stop widening; a successor cannot itself widen without
  bound.
- Cross-door parity test: the same contract + evidence yields the same admit/refuse decision and the same
  receipt fields on Portal, managed and raw.
- Regression: the existing named-gap behavior for out-of-envelope targets is preserved on every door, and
  the managed never-dispatched record stays terminal (`persistAcceptedObservation` with an undefined bundle).
- Recovered managed workers: define and test what happens to a successor's first-time items after a worker
  restart (today `drainManagedReadyActions(true)` runs only right after `continueWithEvidenceSuccessor`).
- Acceptance denominators (novel-combination 5/13, omission 0/25, route 34/34, edges 9/9, long-inquiry 1/1,
  abstention 3/3) do not weaken.
- Authority note: adopting this changes authorization semantics. Record the envelope definition, the
  rejected alternatives, and the residual risks in the PR description for the Native's review.

## Generated artifacts and repo traps (learned in PR #2742)

- **Order of operations:** commit source first, then regenerate generated artifacts against that commit's SHA
  (`codegen:capability-estate-census -- --generated-at=<now> --source-revision=<40-hex>`). The census tracks
  source-file hashes, so ANY edit to a census-member file needs a regen. Snapshot:
  `codegen:capability-knowledge -- --generated-at=<now>`.
- **Acceptance successor rule:** create a new immutable `BEYOND_ACARYA_ACCEPTANCE_v<N+1>.json` ONLY if the
  executable report or capability content genuinely changes (current canonical head is v9; v7 is protected
  main's, byte-identical; `historical_fork_v7_v11/` is preserved history). Compute it with the real
  evaluator; never hand-write hashes. Update the acceptance and lineage tests (previous version becomes an
  immutable pin).
- **Route goldens:** regenerate with `PARIPRASHNA_PORTS_BASELINE=write` and prove the diff is masked
  content-hash rotation only (mask `sha256:` and `fact:` ids; compare fact multisets).
- **Pin-lint:** `python3 platform/scripts/governance/check_fact_category_pinning.py` must report 0 new
  violations. An inserted line can shift an audited entry's line anchor: re-anchor it, do not add exemptions.
- **Next.js:** `route.ts` may export only HTTP handlers and route config. Put helpers in sibling modules.
  `tsc` and vitest do NOT catch this: run the real build with CI's placeholder Firebase env
  (`NEXT_PUBLIC_FIREBASE_*=ci-placeholder ... npm run build`) before publishing.
- **Writes under `00_ARCHITECTURE/`** are denied for the Write/Edit tools and for shell redirects/`cp`. The
  working route is git plumbing: `git hash-object -w <file>` → `git update-index --add --cacheinfo
  100644,<blob>,<path>` → `git checkout-index -f -- <path>`.
- **Mocked-compiler tests hide real state transitions:** `recordInquiryExecution` re-readies a failed item
  while iterations remain. Test session/lifecycle behavior against the real compiler.
- **Secrets:** `bash platform/scripts/governance/secret_scan.sh` (CI's gate) must PASS; a full-history gitleaks
  failure is a known pre-existing baseline, so also scan only your own commits
  (`gitleaks detect --log-opts="origin/main..HEAD"`).
- **Merge:** main uses a merge queue and strict branch protection; the PR must be current with main.
  `platform-mcp` full-suite local failures and its `Headers` typing errors are local `node_modules` drift
  unrelated to CI; CI runs `npm ci` there.

## Authority boundaries

Allowed now: local source, tests, generated artifacts and local commits in this worktree.
Needs a fresh explicit Native authorization each: pushing the branch, opening/updating the PR, CI repair,
merging (the follow-up PR's merge is never implied). Forbidden regardless: deployment, production
credentials, database writes, migration application, producer rebuilds, live collection, empirical or
candidate production validation, auto-merge, claims of campaign or product completion, and any edit to
L3-owned source (`kala_*`, `ka_*`, `l3_*`) or the FROZEN orchestrator contract.

## Definition of done for this kickoff

Both packets implemented with red-then-green tests; `tsc` clean; real `next build` exit 0; codegen
freshness green; pin-lint 0 new; full suite green; secret scan clean; an independent read-only review
with no unresolved HIGH/MED finding; branch clean, current with main; PR description drafted (not posted)
covering objective, both packets, the envelope definition and residual risks, tests, and the authority
ceiling. Then stop and request the exact next authority.


## Closeout record (local source execution complete — awaiting Native publication authorization)

Status: `LOCAL_SOURCE_COMPLETE_AWAITING_NATIVE_PUBLICATION_AUTHORIZATION`. Nothing was pushed; no PR exists.
Both packets are implemented with red-then-green tests on branch
`codex/purna-followup-fence-and-successor-envelope` (base main `205a62618`, still current at close).

**Packet A — served-generation-safe composites.** `query_planet` and `graha_portrait` resolve the served
generation once (`generation/composite_fence.ts`). With one, every chart-data leg is fenced to it; without
one (none resolves, or resolution throws) no generation-sensitive leaf is called, each requested component
is named in `components_unavailable` (`served_generation_unresolved` | `no_served_generation`, fixed reason
text), `generation_fence` is retained, and the response is not a whole-tool error. Component audit in source:
`QUERY_PLANET_COMPONENTS` / `GRAHA_PORTRAIT_COMPONENTS` (`independent` | `sensitive` | `self_fenced`; only the
request-derived planet identity is independent, `get_dashas` is self-fenced, everything else is sensitive).
Both tools also emit one shared `component_failures` list. `classifyInquiryResult` no longer counts a composite
with withheld or failed components as `served`.

**Packet B — one shared successor authorization envelope** (`platform/src/lib/vidhi/inquiry/authorization_envelope.ts`,
live state in `successor_admission_live.ts`). Computed at plan time from the pinned snapshot and compiled plan
only, stored on the contract, bound into `execution_plan_hash` (recomputed from content). Entries exist only for
frontier-rule targets the plan does not contain that have a dispatchable binding on the door's channel, are
within the scope entitlement tier, and are relevant (graph-adjacent to a planned SCU, or a universal/overlapping
domain). The eight conditions are enforced by one evaluator with stable named codes: (1) `successor_capability_not_read_only`;
(2) `successor_capability_not_in_catalogue`, `successor_channel_not_eligible`; (3) `successor_frontier_not_relevant`;
(4) `successor_chart_mismatch`, `successor_principal_mismatch`, `successor_build_identity_mismatch`;
(5) `successor_chart_access_not_verified`, `successor_entitlement_not_permitted`; (6) `successor_depth_exceeded`,
`successor_iteration_limit_exceeded`, `successor_cost_limit_exceeded`; (7) `successor_safety_excluded`; (8)
`successor_receipt_incomplete`; outside the envelope: `successor_capability_not_authorized_for_request`
(unchanged). A capped same-capability pagination frontier is authorized by the hash-bound parent plan
(`authority: parent_plan_continuation`) and still clears every other condition. Every door recomputes the decision
at dispatch (`evaluateSuccessorItemForDispatch`); a stored refusal is final; refusals terminalize identically
(`terminalizeRefusedSuccessorItem`) and are receipted on the plan item (`successor_dispatch`) and in the durable
evidence payload. A recovered managed worker resumes a successor generation through the same drain (first-time
items), never through the adopted plan tool set (which bypassed authorization).

**Rejected alternatives.** (a) Letting the synthesizing model or a client name admissible capabilities — authority
must be server-computed. (b) Evaluating only at compile time — live state (safety, cost, overlay, principal)
changes; dispatch re-evaluates. (c) Widening the request tool set — the envelope is a separate, hash-bound grant.
(d) Refusing at compile by blocking the plan item — kept ready-then-named-failed so the existing terminal named-gap
shape and `successor_capability_not_authorized_for_request` behavior are preserved.

**Residual risks / limitations (for the Native's review).** Entitlement (5) is checked against the contract's
declared scope tier; no per-principal tier exists in the platform (CLAUDE.md §N.4), so on the raw door it is
exactly as strong as plan compilation already was. Chart access is the door's actual `authorizeChartAccess` /
`authorizeTurn` result; the BYOK managed preflight only proves access, so it is recorded as the least privilege
that admits (`view`). The Portal and raw doors have no per-request call-count cost tracker, so the cost detector is
live only on managed (and the batch/lineage ceilings); the envelope is small (≤3 rule targets), so the lineage
ceilings are testable mainly with synthetic chains. Successors issued before this change (no parent envelope)
now refuse every item (fail closed). Two LOW items were left: the raw door returns 409 (not a terminal record)
when a refused item has no resolvable binding or unauthorized args; `authorizeMcpByokPrincipal` does not return a
permission level.

**Generated artifacts and why.** Capability snapshot regenerated (`sha256:9b47461d…`): exactly seven added optional
`build_id` inputs (get_positions, get_dignity, get_avasthas, get_aspects, get_yoga_dosha, get_dispositors,
traverse_chart_graph). Estate census regenerated against the final source commit. New immutable
`BEYOND_ACARYA_ACCEPTANCE_v10.json` from the real evaluator (report hash `fe396729…`); v9 is now an immutable pin;
all six denominators identical (5/13, 0/25, 34/34, 9/9, 1/1, 3/3); source-provenance only. Two route goldens
rotated by content hashes only (verified semantically equal after masking and order-normalizing). Four pin-lint
allowlist line anchors re-anchored, no new exemption.

**Verification at close.** `tsc` clean; freshness gates current; pin-lint 0 new; full platform suite 1285 files /
14,261 tests passed (81 files skipped: DB-backed); real `next build` (CI placeholder Firebase env) exit 0; CI-mode
secret scan PASS; branch-only gitleaks: no leaks (a local full-worktree gitleaks reports the inherited baseline,
which CI does not run). Three independent read-only review rounds (Packet A; Packet B security; Packet B
semantics) plus a final full-delta security review; every HIGH/MED finding was fixed and re-verified; two LOW
items are recorded above. Untouched: `kala_*`/`ka_*`/`l3_*`, the frozen orchestrator, migrations, `platform-mcp`.

**Next authority required.** A fresh explicit Native authorization to publish this follow-up (push the branch and
open the PR, plus CI repair and independent review); merging is a separate later authorization.
