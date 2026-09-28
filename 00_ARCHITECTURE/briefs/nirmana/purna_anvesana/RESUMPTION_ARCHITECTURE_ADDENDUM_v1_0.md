---
artifact: PURNA_ANVESANA_RESUMPTION_ARCHITECTURE_ADDENDUM
version: 1.0
status: REVIEWED_PREPARATION_BASELINE
date: 2026-09-27
execution_authorized: false
base: 6b26f3ff05ee0aba3cdd964bce62292496ae6b62
---

# Pūrṇa Anveṣaṇa — resumption architecture addendum

## 1. Why this addendum exists

The independent review remains the primary diagnosis. This addendum reconciles it with protected
`origin/main` as of 2026-09-27 so a future Claude Code executor starts from the present system, not
from the September 20 candidate or September 22 production snapshot. It changes no product promise
and authorizes no implementation.

## 2. Product outcome

Pūrṇa Anveṣaṇa is the inquiry-control and answer-accountability product that makes Madhav's rich
astrological data plane usable as a beyond-Ācārya reading system. For every question it must:

1. understand and decompose the inquiry into all materially relevant astrological obligations;
2. discover every available capability and required adjacent evidence without asking synthesis to
   perform catalogue discovery;
3. iteratively retrieve, inspect, and widen until required evidence is exhausted or an honest,
   specific frontier remains;
4. synthesize only admitted evidence while preserving contradictions, uncertainty, provenance,
   timing scope, and chart/build identity;
5. deliver every materially used fact and its conjoint interpretation, not merely a conclusion;
6. behave consistently through Portal, managed MCP, and the governed raw-client lifecycle;
7. refuse certified completion when evidence, continuation, attribution, or delivery is incomplete.

The planner selects and sequences evidence. It does not perform the synthesizing LLM's interpretive
job. The synthesizer interprets actual admitted evidence. The accountability layer proves what was
selected, retrieved, seen, used, delivered, omitted, or left unresolved.

## 3. Retained system shape

```text
Question
  -> scope and astrological decomposition
  -> capability knowledge + chart/build availability overlay
  -> deterministic contract with high-reasoning hypothesis support
  -> bounded retrieval and evidence-admitted continuation
  -> synthesis over the admitted evidence set
  -> fact register + coverage/delivery receipt
  -> Portal / managed MCP / conforming raw client
  -> deterministic and empirical acceptance
```

Retain the federated SCU catalogue, generated snapshot, overlay, compiler, execution session,
acceptance corpus, provenance receipts, pagination contracts, and channel adapters. This is a focused
repair and integration program, not a rewrite.

## 4. Corrected generation architecture

### 4.1 Failed abstraction

Current main still contains a consumer path that derives an “active build” from the chart's latest
completed build and then requires unrelated asset facts/receipts to share that run id. A completed
run may build only one asset. Therefore chart-wide latest-build identity is not served-data identity.

### 4.2 Required abstraction

Create one shared, fail-closed per-asset generation resolver used by overlay, judgment, availability,
and direct evidence consumers. Its conceptual output is:

```text
chart_id
generation_hash
asset bindings:
  asset_id
  rows_build_id or generation_id
  receipt_version and digest specification
  freshness/provenance state
  source: per_asset_receipts | generation_heads
unresolved assets with typed reasons
```

The generation hash is derived from a stable sort of the selected asset bindings; it is not a
fictional common run id. Consumers select rows by each asset's proven served binding. An unresolved
mandatory asset remains explicit and prevents false closure.

Supabase migrations 1035/1036 define L1/L2 generation heads and producer-generation structures.
They are the intended durable source once populated and proven. Until then, the resolver may derive
per-asset bindings from fresh proven receipts under one reviewed rule. There must be no second
consumer-specific resolver.

### 4.3 Cross-layer ownership

- Pūrṇa owns the shared consumer resolver and its use by inquiry surfaces.
- The data plane owns producer-generation semantics and population of generation heads.
- Pūrṇa may prove missing/unresolved heads; it may not silently backfill or dispatch producers.
- A population/backfill/rebuild is a separate, explicitly authorized production packet.

## 5. Replacement fence

An in-progress fence represents a producer that can still mutate the selected asset. A queued or
building asset row attached to a terminal build run cannot remain “in progress” forever merely
because its row state was not normalized. The source must distinguish:

- truly active run/asset;
- terminal orphan row that requires hygiene but cannot mutate;
- later terminal mutation lacking a proven receipt;
- selected proven generation.

Repair the selection predicate and add tests for all four states. Historical orphan-row cleanup is
separate from the source fix, begins with read-only enumeration, and requires database-write
authorization. Never make the test pass by weakening proven-receipt or freshness requirements.

## 6. Near-miss as an astrological product

`notably_absent_yogas` is not a formatting field. It is a deterministic absence class: a curated
yoga candidate whose formation is almost satisfied, with the exact missing leg and evaluability
made explicit. Required decision packet before implementation:

- versioned candidate set and authoritative formation rules;
- mandatory versus optional legs and allowed tolerance, if any;
- scope rules across rāśi, relevant varga, frame, and ayanāṃśa;
- cancellation and contradiction handling;
- distinction among `near_miss`, `absent`, `present`, and `indeterminate`;
- provenance and generation binding;
- consumer wording that does not manufacture a yoga.

The existing L2 `bo_laksana` absence-signal shape is the preferred producer location if current
source verification confirms it. The judgment consumer must report actual rows or a typed
unavailability reason; permanent `not_computed` cannot satisfy the accepted wealth contract.

## 7. Planner and continuation delta — revalidate before changing

The independent review found that deep reasoning did not reach a provider and late-hop continuation
could not widen beyond the same capability. Current main has since evolved:

- the planner selects `planner_deep` for deep scope;
- the Portal and MCP routes resolve deep primary/fallback model slots;
- planning policy passes a reasoning request;
- the compiler can admit evidence-discovered frontiers into successor contracts.

Therefore future execution must begin with black-box and focused source tests, not an assumed rewrite.
Prove:

1. deep scope selects a genuinely stronger configured model at runtime;
2. the provider receives and honors the reasoning setting;
3. a retrieved fact can authorize a new, relevant capability not in the initial plan;
4. managed execution can follow more than one page/continuation until exhaustion;
5. the new contract retains prior admitted evidence and does not allow arbitrary model-selected tools;
6. iteration and cost budgets remain explicit while completeness, not latency, governs closure.

Only the failed assertion becomes implementation scope.

## 8. Complete evidence delivery

Current main contains fact-register and response-accountability construction plus Portal persistence
and MCP output. The remaining question is behavioral: does the synthesis model see the same admitted
evidence from which the register is built, and does every managed door refuse “complete” when a
material fact is not delivered?

The target contract is:

- **selected**: obligation/capability was authorized;
- **retrieved**: raw evidence arrived and passed admission;
- **seen**: the synthesis input includes the evidence;
- **used**: an interpretation depends on it;
- **delivered**: the fact and conjoint interpretation are present or explicitly dispositioned;
- **unresolved/omitted**: named with a typed reason and effect on conclusion.

The response may place facts inline, in structured evidence sections, or both. Presentation is a
channel concern; lossless material-fact accountability is not optional. The synthesis model must not
be judged against evidence it never received, and a prose substring heuristic cannot be the sole
proof of delivery.

## 9. Availability proof model

Availability must be typed by capability kind:

- row/query capability: proven selected-generation rows plus receipt/freshness;
- deterministic computation: executable dependency and input proof;
- composite judgment: mandatory child units settled for the requested mode;
- classical attribution: canonical served corpus and resolvable source identity;
- planner/resource capability: runtime configuration and callable contract;
- channel/delivery capability: route, protocol, and output receipt proof.

Reachability, a zero-row SQL probe, or a registry entry alone does not prove semantic presence.
Optional modes may be unavailable without suppressing an independently proven requested mode;
missing mandatory facets prevent complete composite status.

## 10. Execution packets after separate authorization

| Packet | Goal | Completion evidence | Production authority? |
|---|---|---|---|
| R0 | Reconcile current base, old candidate semantics, generated artifacts, and fixed denominator | reviewed salvage ledger; baseline tests; no stale hashes | no |
| R1A | Shared per-asset generation resolver and consumer migration | unit/integration tests prove mixed asset builds serve correctly and unresolved assets fail closed | no for source; yes for any DB population |
| R1B | Correct replacement fence | active/terminal/later-unreceipted/proven matrix green | no for source; yes for orphan cleanup |
| R1C | Verify/rebuild `ga_strength` under current digest spec | fresh proven receipt and served strength evidence | yes for rebuild/live proof |
| R2A | Ratify and implement near-miss product | approved domain packet; deterministic producer/consumer tests | decision required before code; live build later |
| R2B | Prove and close planner/continuation delta | deep-provider and evidence-widening/multi-page tests | no, unless live provider probe |
| R2C | Enforce complete delivery | synthesis/register parity and three-door omission negative controls | no for source |
| R3 | Repair remaining availability families by proof kind | every dark binding proven, deliberately dark with a valid reason, or removed | possible live read proof |
| R4 | Candidate acceptance | immutable cases + 30-scenario corpus + channel parity + semantic golden review | no deployment |
| R5 | Protected delivery and live close | merged/deployed identity, current receipts, real collections, blinded evaluation | explicit release/production authority |

Packets R1A/R1B and read-only R1C verification may proceed in parallel after R0. R2A waits for the
domain decision but must not stall R2B/R2C. R3 is grouped by proof family, not by arbitrary catalogue
count. R4 starts only when required source outcomes are green. R5 is a different authority phase.

## 11. Decisions still required before their packets

1. Evidence-store retention and access policy for accepted real collections.
2. Near-miss candidate set and eligibility rule.
3. Authority for orphan-row repair and ownership of generation-head population.
4. Runtime deep-slot model and acceptable reasoning/cost budget.
5. Lease/authority for any `ga_strength` rebuild.
6. Blinded judge model, budget, and acceptance threshold.

PR #2704 is not a decision dependency. It stays with L3.

## 12. Migration and concurrency rule

The historical brief reserved 1042–1069 for Pūrṇa and 1070–1119 for L3. That partition is no
longer a safe allocation rule: protected main currently reaches 1070 and an active L0/data-plane
worktree reaches at least 1127. No migration number is reserved by this preparation.

Before authoring any migration, refresh all active worktrees and remote PRs, run the repository's
migration-number guard, coordinate with current data-plane/L3 owners, and record the granted number.
Applied migrations 1033–1042 and 1070 are immutable.

## 13. Execution control

One Claude Code integrator owns the primary worktree and candidate. It maintains a small runnable
queue: next unblocked packet, evidence required, affected files, and stop condition. It may use
packet-specific child worktrees only when file ownership is disjoint. Workers never merge, rebase,
or modify another campaign's branch.

Rules:

1. A blocked packet does not block unrelated runnable packets.
2. Three repeats of the same failure require root-cause reclassification before another attempt.
3. Generated artifacts are refreshed once per packet boundary, never as speculative churn.
4. Governance is limited to decisions, evidence, and truthful status needed for delivery.
5. Monitoring is event-driven and stops when waiting for a named external action.
6. “Source green,” “candidate green,” “merged,” “deployed,” “live-proven,” and “accepted” remain
   distinct states.
7. Claude stops immediately if its cwd, branch, base, or clean-start invariant is wrong.

## 14. Acceptance definition

The campaign is not complete when catalogue coverage reaches 100%. It is complete only when the
immutable original cases and expanded product corpus produce deep, materially complete, evidence-
accountable responses through the accepted channels; current chart/build evidence is served under
correct generation semantics; required continuations are exhausted; absence, contradiction, and
unavailability are honest; protected delivery is proven; and the blinded empirical gate passes.
