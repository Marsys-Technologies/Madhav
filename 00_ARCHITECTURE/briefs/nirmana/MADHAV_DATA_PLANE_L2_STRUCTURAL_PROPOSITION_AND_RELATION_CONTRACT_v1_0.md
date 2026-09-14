---
artifact: MADHAV_DATA_PLANE_L2_STRUCTURAL_PROPOSITION_AND_RELATION_CONTRACT
version: "1.0"
status: PRODUCER_READY_ACCEPTED
authority: DP-SD-015
runtime_contract: platform/python-sidecar/bodha_writers/data_plane_contracts.py
accepted_l0_release: f6fed12c794224329f6b3b436f8b1b814499d06d
accepted_l1_terminal: 18503e9c2dbb140f5d17b4bc34a5f6d087f97c38
---

# L2 structural proposition and signed-relation contract

## Contract

Every registered L2 producer adopts
`MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0` without changing WriterBase. Before
execution the runtime requires non-empty chart/build identity, rejects an
explicit L0/L1 pin that differs from the accepted releases, resolves the exact
selected transitive L1/L2 generation vector and semantic digests, derives one
generation context plus exact per-partition calculation contexts, and rejects
mixed or stale inputs. Stored dependency keys must equal the current recursive
registry topology as well as the selected head identities/digests, so topology
addition or removal invalidates an old generation. The caller owns transaction,
savepoint, commit and close. Dry-run entry paths perform no SQL mutation.

Stable `configuration`, `proposition`, `relationship`, `contradiction` and
`mechanism` identities are SHA-256 content identities over semantic payloads.
Build IDs and observation/query timestamps are forbidden identity material;
non-finite numbers fail closed in both application validation and database
capture. Replay equality covers the exact per-run row identity set as well as
the semantic-output digest, so row omission cannot pass. The surrounding producer observation carries
contract, accepted releases, generation/partition context, build and the
dependency-aware transitive writer-source digest.

## Required proposition shape

A material proposition retains: exact rule/method and qualification state;
chart/context/generation/ayanāṃśa/frame/varga; every participant and
configuration role; complete domains and semantic domain roles; original L1
fact/configuration roots; occurrence ledger with its unit and polarity;
condition ledger with its different unit and polarity; satisfied/failed clauses,
exceptions and missingness; cancellation target plus target's original sign;
epistemic class and executable verification detector.

Occurrence `[0,1]` and condition-affliction `[0,10]` are separate. Legacy grades
are compatibility projections only. Cancellation of opposition yields
`attenuated_opposition`; cancellation of support yields `attenuated_support`.
Neither produces a promised outcome. Bhāvat Bhāvam is
`UNQUALIFIED_SOURCE`; its positive doctrinal arm is `NOT_REACHABLE`.

## Required relation shape

Every relationship carries actor, relation, target, original polarity `-1|+1`,
magnitude semantics, basis, direct/transitive/candidate class, configuration
membership, exact evidence roots and shared-root group. Cancelled edges remain
visible. Opposition is never converted to unsigned conductance. Ordered paths
retain ordered edge identities; repeated wrappers/paths sharing a root count as
one independent group. Support and opposition roots are grouped and counted
separately; opposition never inflates independent support. Domain or display
ordering is non-semantic.

## Failure and compatibility

Wrong chart/context/generation/ayanāṃśa/varga or unqualified-rule promotion
fails the partition. Explicit states are `present`, `zero`, `unavailable`,
`floored`, `inapplicable`, `unqualified_source`, `failed` and `unexplored`.
Legacy null activation fields remain readable but are
`UNAVAILABLE_AT_L2`; they carry no timing authority.
