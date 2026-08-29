# Asset Elevation Contract

Create one record for every member of the frozen layer denominator. Populate unknowns explicitly; do not turn absent evidence into a pass. Identity, purpose/value, DAG, applicable quality, release and terminal evidence are universal. Type-specific sections may be `not_applicable` only with a concise reason; do not force a service, probe or source through irrelevant data-enrichment or row-build analysis.

## A. Identity and intent

- Asset ID, display name, version and layer.
- Asset type: global reference, chart-derived, service/probe, index, model, source-only or other.
- Epistemic type: source fact, deterministic derivation, domain rule, interpretive/model evidence, synthesis or narration.
- Unique purpose and reason for its layer placement.
- Current status and proposed terminal disposition.

## B. Inputs, DAG and lineage

- Declared upstream assets and edge types.
- Actual code, SQL, service and runtime reads.
- Required domain/calculation context, configuration and version as applicable.
- Output tables, artifacts, services and natural keys.
- Content hashes, lineage/derivation references and invalidation rules.
- False, missing, redundant or conditional DAG edges.
- Critical-path position, fan-out and shared-write constraints.

Acceptance: every hard edge names the consumed contract and has evidence; no hidden upstream read or unexplained cycle remains.

## C. Correctness and epistemic integrity

- Mathematical and domain invariants.
- Authoritative sources, legitimate variants and applicability conditions.
- Fact versus derivation versus interpretation separation.
- Precision, tolerance, ordering and deterministic-replay rules.
- Null, uncertainty, contradiction and degraded-state semantics.
- Golden, boundary, property, differential and controlled-perturbation cases.
- Verification tiers and the real detectors that earn them.

Acceptance: the asset cannot claim a stronger fact, verification level or certainty than its detectors and sources support.

## D. Data sufficiency and enrichment

- Current row/entity/relationship coverage by meaningful dimension.
- Missing entities, classifications, relations, periods, geographies, contexts, source variants or counterexamples.
- Duplicate, orphaned, contradictory or stale data.
- Provenance, source licensing and citation granularity.
- Confidence and disagreement representation.
- Specific downstream or research capability unlocked by each proposed addition.

Acceptance: additions have a named consumer or research purpose; volume alone is not value.

## E. Consumers, reuse and duplication

- Direct and transitive downstream assets.
- API, retrieval, AI, UI and report consumers.
- Actual observed use versus intended use.
- Capability used partially, bypassed or recreated downstream.
- Duplicated constants, labels, rules, computations, citations and local mappings.
- Intentional non-use and its rationale.
- Consumer migration/deprecation plan.

Acceptance: shared truth has one canonical authority; downstream exceptions are explicit and justified.

## F. AI and product readiness

- Retrieval keys, facets, pagination and density contract.
- Machine-readable facts, derivations, alternatives, citations, confidence and gaps.
- Protection against treating catalogue matches as confirmed findings.
- Narration fidelity: prose reads cited facts rather than re-deriving or inventing them.
- Product journeys, chart calculations, explanations and UI surfaces enabled.
- Empty, stale, partial and unavailable states shown honestly.
- Usage and usefulness signals needed after release.

Acceptance: a user-visible or AI-generated claim can be traced to the asset, input context, derivation and source.

## G. Implementation and build efficiency

- Writer/code path and algorithm.
- Current build and runtime baseline: p50/p90/worst, CPU, memory, I/O, database time, external calls, rows/sec, retries and failure rate.
- Measured hotspot and bound class: round-trip, I/O, CPU, algorithm, lock/contention or external dependency.
- Full versus incremental/partitioned behavior.
- Repeated upstream computations or unused work.
- Candidate optimization and plausible target.
- Pre/post output-identity method.
- Achieved build/runtime delta and resource delta.

Acceptance: no optimization without a measured hotspot; no speed claim without equal-or-better quality proof.

## H. Reliability and operations

- Idempotency and transaction ownership.
- Resume/checkpoint behavior and bounded retry classification.
- Timeout derived from observed work.
- Integrity check, freshness detector, count/status projection and failure reporting.
- Snapshot/restore or rollback requirement.
- Security, tenant/data boundary and credential exposure.
- Observability, alerts and recovery path.

Acceptance: a dispatched build terminates honestly, accounts for every planned unit and can recover without silently duplicating committed work.

## I. Change and release packet

- Decision and non-goals.
- Owned files, tables and contracts.
- Isolated worktree, branch and base commit.
- Migration and backward-compatibility plan.
- Focused test and verification plan.
- Integration/DAG order and compatible release wave.
- Deployment and rollback procedure.
- Production rebuild method and expected downstream invalidation.

## J. Final evidence

- Pre-change baseline reference.
- Implementation commit and protected merge reference.
- Independent review/verdict.
- Deployed revision and migration proof.
- Accepted rebuild receipt and input/upstream hashes.
- Post-build integrity, quality and performance results.
- Consumer/UI/AI availability proof.
- Tracker event and freeze decision.

## Disposition-specific terminal rules

- **Optimized:** output identity or declared semantic improvement proven; measured efficiency gain recorded.
- **Enriched/corrected:** new semantics, provenance and downstream compatibility proven.
- **Justified no-change:** all lenses examined, no material gap found, current production rebuild and verification accepted.
- **Merged/split:** successor mapping and consumer migration complete; no ambiguous dual authority remains.
- **Retired/superseded:** data disposition, tombstone/redirect and consumer removal proven.
- **Source-only:** ingestion, provenance, freshness and consumers verified; no writer invented.
- **Service/probe:** availability, correctness, failure semantics and product consumer verified; no row-count proxy used.
- **Producer-covered:** producer identity, inherited production-rebuild receipt and inherited terminal acceptance receipt are bound explicitly; the covered member is never rebuilt separately.

An asset is not frozen merely because code exists, rows are present, a PR merged, CI passed, or a tracker row is green.
