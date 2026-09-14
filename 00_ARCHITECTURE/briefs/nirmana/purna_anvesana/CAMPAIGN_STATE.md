---
artifact: MADHAV_PURNA_ANVESANA_CAMPAIGN_STATE
canonical_id: MADHAV_PURNA_ANVESANA_CAMPAIGN_STATE
version: 0.2.0
status: LIVE
campaign_id: madhav-purna-anvesana
definition: 00_ARCHITECTURE/briefs/nirmana/purna_anvesana/CAMPAIGN_DEFINITION.json
events: 00_ARCHITECTURE/briefs/nirmana/purna_anvesana/EVENTS.jsonl
last_event: PA-E0009
last_updated: 2026-09-14T18:09:30+05:30
---

# MADHAV PŪRṆA ANVEṢAṆA — Campaign State

This file is a human-readable projection. The immutable campaign definition and append-only event
stream named above are the evidence authority. It is separate from the existing
`nirmana-elevation` production campaign and does not mutate that campaign's definitions, events,
layer state, queue or authority.

## Current position

- Wave: 0 complete; Wave 1 producer-contract packets are the next frontier.
- Branch: `codex/purna-anvesana-wave0`, stacked exactly on FC0
  `fccfbb5ab11eadb33259ff987738068753d12ebc`.
- PR #2597: frozen unchanged; it remains a source/review candidate, not merged or deployed proof.
- Lease: `MADHAV-PURNA-ANVESANA-20260914`, remote claim
  `5c82e4813336b6454e3b63b485fefe47e84333b7`.
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
| Static-any-spec / current source-active | 111/128; 17 gaps | Ever named by a static INSERT across both migration trees; not current deployed state. |
| Static-any-spec / formal frozen receipt | 110/128; 18 gaps | Same rule on the different formal membership set. |
| Runtime descriptors / planner-addressable | 185 / 182 | Three calibration-only descriptors excluded from planning. |
| Registrar resolution | 59 verified / 3 ambiguous / 123 unresolved | Source-text route evidence; distinct from SCU metadata. |
| SCUs | 182 | Five editorial, 177 descriptor-derived stubs. |
| SCU bindings | 185 | 179 executable, six unavailable; seven publicly named across five SCUs. |
| Semantic graph | 53 edges; 26 incident / 156 isolated nodes | `ORPHAN_DESCRIPTOR=0` does not measure graph connectivity. |
| Inline concepts | 219 | No typed concept universe; unbound-concept count is currently unmeasurable. |

Current-source-active static-any-spec gaps:

`bg_ephemeris_engine`, `bg_gochara_citation_resolution`, `bg_nakshatra_medical`, `bg_panchanga`,
`bg_sign_medical`, `bg_transit_engine`, `ka_avadhi`, `ka_dasha_kala`,
`ka_gochara_v3_century_materialize`, `ka_graha_sancara`, `ka_kalasutra`, `ka_muhurta_seva`,
`ka_tulana`, `ka_vighnakara`, `lel_events`, `mi_abhilekha`, `mi_seva`.

The formal frozen receipt gap set adds `ka_gochara_sweep`.

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
| W1-P1 producer output contracts | QUEUED | W0-P3 | required at packet close |
| W1-P2 routes/provenance/pagination/dark states | QUEUED | W0-P3 | required at packet close |
| W2–W6 | QUEUED | exact DAG in campaign definition | one independent reviewer per packet |

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
