---
artifact: MADHAV_PURNA_ANVESANA_CAMPAIGN_STATE
canonical_id: MADHAV_PURNA_ANVESANA_CAMPAIGN_STATE
version: 0.4.0
status: LIVE
campaign_id: madhav-purna-anvesana
definition: 00_ARCHITECTURE/briefs/nirmana/purna_anvesana/CAMPAIGN_DEFINITION.json
events: 00_ARCHITECTURE/briefs/nirmana/purna_anvesana/EVENTS.jsonl
last_event: PA-E0019
last_updated: 2026-09-14T21:09:04+05:30
---

# MADHAV PŪRṆA ANVEṢAṆA — Campaign State

This file is a human-readable projection. The immutable campaign definition and append-only event
stream named above are the evidence authority. It is separate from the existing
`nirmana-elevation` production campaign and does not mutate that campaign's definitions, events,
layer state, queue or authority.

## Current position

- Wave: 0 through Wave 2 complete; Wave 3 inquiry compiler and omission-challenger packets are next.
- Branch: `codex/purna-anvesana-wave2`, stacked on governed Wave 1 head `0c4a6e341`;
  technical evidence head `402319736611441812d15f9d4954a908d21ca25f`.
- PR #2597: frozen unchanged; it remains a source/review candidate, not merged or deployed proof.
- Lease: `MADHAV-PURNA-ANVESANA-W2-20260914`, remote claim `19f5105c1`; release is due
  after the stacked Wave 2 PR is durably published.
- Authority: CCD-011. Source/local/disposable work and focused/stacked PRs are allowed. Merge,
  deployment, shared/production migration or mutation, credentials/infrastructure, retirement,
  doctrine ratification and production/empirical acceptance claims are prohibited.

## Wave 0 finding that blocked execution

The FC0 census reported 33 assets with a static reviewed output-digest specification and 95 active
gaps. Its generator scanned only `platform/supabase/migrations`, even though governed current
migrations live in `platform/migrations` and the runner reads both. The same static-INSERT rule over
both trees yields 111/128 current-source-active assets ever named by a reviewed spec and 17 gaps.
The generator, regression test and provenance source set were corrected in commit `4fe02619e`.
The artifact was then regenerated and committed separately in `503c0f616`, so its
`source_revision` now identifies the committed dual-tree generator. Independent re-review approved
the correction after the focused tests and codegen drift check passed.

This is still a source-history metric. The number of deployed current rows remains unresolved until
an ordered migration replay or separately authorized read-only live query proves it. It is not
semantic coverage: explicit SCU producer links cover only eight unique assets, seven with reviewed
hashes.

## Frozen non-vacuous denominators

| Metric | Result | Meaning |
|---|---:|---|
| Portfolio identities | 129 | Full seed inventory. |
| Formal frozen receipt set | 128 | Excludes supporting `bo_grounding`; includes retained `ka_gochara_sweep`. |
| Current source-active set | 128 | Excludes retired `ka_gochara_sweep`; includes supporting `bo_grounding`. |
| Static-any-spec / current source-active | 117/128; 11 gaps | Ever named by a static INSERT across both migration trees, including unapplied migration 1034; not current deployed state. |
| Current-source-intended relational contracts / current source-active | 116/128 | Ordered source intent; remaining assets have other explicit dispositions or named blockers. |
| Runtime descriptors / planner-addressable | 185 / 182 | Three calibration-only descriptors excluded from planning. |
| Runtime route dispositions | 185 total: 71 exposed / 114 not exposed | 70 exact URI and nine parallel same-name routes; zero ambiguous or unresolved. |
| Served full MCP authority | 129 unique names | Exact authored authority and registration set equality; three lifecycle handlers are profile-gated. |
| SCUs | 182 | Five editorial, 177 descriptor-derived stubs. |
| SCU bindings | 185 | 182 executable, three explicitly unavailable calibration descriptors; semantic quality remains Wave 2 scope. |
| Semantic graph | 53 edges; 26 incident / 156 isolated nodes | `ORPHAN_DESCRIPTOR=0` does not measure graph connectivity. |
| Inline concepts | 219 | No typed concept universe; unbound-concept count is currently unmeasurable. |

Current-source-active static-any-spec gaps after migration 1034 source:

`bg_ephemeris_engine`, `bg_panchanga`, `ka_dasha_kala`,
`ka_gochara_v3_century_materialize`, `ka_graha_sancara`, `ka_muhurta_seva`,
`ka_tulana`, `ka_vighnakara`, `lel_events`, `mi_abhilekha`, `mi_seva`.

The formal frozen receipt gap set adds `ka_gochara_sweep`.

## Wave 1 outcome

Every one of the 128 current-active producers now has an explicit, machine-checked disposition:
116 current-source-intended relational digest contracts, six service probes, two service-effect
contracts, one user-authored-source contract, one deliberately nondeterministic exclusion and two
named relational blockers. All 267 referenced implementation and test paths resolve. Migration
1034 adds six reviewed digest specifications; a disposable PostgreSQL 16.15 replay proved the
schema/key contracts and service effects without touching any shared or production database.

The exact served full MCP surface is 129 unique names. Registration now fails closed against an
authored full-route authority, including the three inquiry lifecycle handlers previously outside
the profile gate. The 185 runtime descriptors have explicit dispositions: 71 exposed and 114 not
exposed; 70 exact URI routes and nine parallel same-name routes are source-verified, with zero
ambiguous or unresolved route records. Pagination is explicit (96 paginated, one reviewed
exhaustible, 95 non-exhaustible), and inquiry finalization cannot claim completion without an
exhaustion receipt. Hybrid `pact_query` provenance now unions stored and computed lineage.

These are source/local/disposable results. The deployed-current producer state was not read; the
older relational contracts were not replayed in this wave; service probes are not release smoke;
and the `mi_abhilekha` effect remains deliberately unratified product behavior.

## Wave 2 outcome

All 182 planner-addressable Semantic Capability Units are now editorial: 177 reviewed descriptor
units and five authored declarations, with zero descriptor-derived stubs. Every unit carries
meaningful full descriptions and reviewed domains, concepts, intents, horizons and outputs. The
128 current-source-active producers have exact, unique semantic bindings backed by the Wave 1
contract registry; contract and semantic drift rotate independent fingerprints and fail closed.

The typed universe contains 250 concepts with zero unbound concepts. The 53 source-backed edges
are exactly 15 authored relations plus 38 drill-child contracts. All 156 isolated SCUs carry an
explicit reviewed disposition, leaving zero unresolved isolated nodes, producer SCUs or semantic
gaps. The bounded planner projection preserves at least one source-backed adjacency whenever one
is available. Both independent reviewers approved the semantic and graph packets, including the
narrow golden-receipt amendment at exact head `402319736611441812d15f9d4954a908d21ca25f`.

The editorial estate legitimately changes two deterministic career-branch streams from two
required omission obligations to one because `scu.catalog.judgment_query` now satisfies the bhava
obligation directly. A disposable recapture changed only one line in each affected baseline; the
focused tests and the full 12,304-test unit gate then passed. This is source/local compatibility
evidence, not merge, deployment, runtime health or empirical acceptance proof.

## Reproduction

From the repository root:

```bash
cd platform
npm run test -- --run scripts/__tests__/generate_capability_estate_census.test.ts
npm run codegen:capability-estate-census
npm run codegen:capability-estate-census:check
npm run codegen:capability-knowledge:check
```

Set extraction remains explicit:

```bash
jq -r '.details.producer_assets.active_asset_ids[]' platform/src/generated/capability_estate_census.json
jq -r '.details.reviewed_output_digest_coverage.active_assets_without_any_reviewed_spec[]' platform/src/generated/capability_estate_census.json
jq -r '.scus[] | select(.editorial == false) | .scu_id' platform/src/generated/capability_knowledge.snapshot.json
jq -r '.edges[] | [.from_scu_id,.relation,.to_scu_id] | @tsv' platform/src/generated/capability_knowledge.snapshot.json
```

## Packet frontier

| Packet | State | Dependency | Independent review |
|---|---|---|---|
| W0-P1 authority/control/FC0 freeze | COMPLETE | none | governance/control-plane audit complete |
| W0-P2 denominator correction/freeze | COMPLETE | W0-P1 | initial review refuted stale provenance; corrected result independently approved |
| W0-P3 delivery DAG | COMPLETE | W0-P1, W0-P2 | Git/PR decomposition audit complete |
| W1-P1 producer output contracts | COMPLETE | W0-P3 | initial refutation corrected; denominator and migration reviews approved |
| W1-P2 routes/provenance/pagination/dark states | COMPLETE | W0-P3 | initial refutations corrected; exact-route review approved |
| W2-P1 editorial SCUs | COMPLETE | W1-P1, W1-P2 | semantic reviewer approved exact head |
| W2-P2 typed semantic graph | COMPLETE | W2-P1 | graph reviewer approved exact head |
| W3-P1 normalized intent and ontology traversal | NEXT | W2-P2 | required at packet close |
| W3-P2 omission challenger and frontier closure | QUEUED | W3-P1 | required at packet close |
| W4–W6 | QUEUED | exact DAG in campaign definition | one independent reviewer per packet |

## Delivery decomposition

FC0 is 37 commits ahead of `origin/main`, 184 files and +38,520/−1,156. Its final diff separates
into 24 authority/governance files, two generated artifacts, 92 file-disjoint lint/UI baseline
files, and 66 substantive planner/inquiry files. The safe campaign path is not a history rewrite:
keep #2597 frozen, stack Wave 0 from its exact head, then use focused successor PRs along the packet
DAG. The lint/UI packet is the only mechanically file-disjoint extraction candidate, and extraction
would require separate authorization.

## Residual discipline

The FC0 implementation brief's R1–R12 remain authoritative inputs and must be mapped without
renumbering. No packet can close a missing live, migration, route, semantic, graph, inquiry,
response or acceptance proof by citing green CI, a PR, a local fixture or this state projection.
Authority-bound production remainder is quarantined for a future separately authorized operation;
the terminal state available to this campaign is
`SOURCE_SCOPE_COMPLETE_WITH_AUTHORITY_BOUND_REMAINDER`.
