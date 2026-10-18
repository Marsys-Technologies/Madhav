---
artifact: J4C_B_PREBUILD
version: "1.0"
status: SOURCE_PREPARATION — built portions wait on the campaign gate
produced_on: 2026-10-16
base: 349d12afb
---

# J4C-B source preparation

This branch prepares two code children. It issues no child verdict, merge,
protected-window, deployment or operational acceptance receipt.

| Item | Preparation | Missing before the residual can close |
| --- | --- | --- |
| J-4c-pr3187 | Independent ND-H / ND-P2 verifier tables, near-miss verifier library, current measuring-report oracles and mutation runner ported | Exact-head independent review; original dependencies; P06b's separately owned stationless / precision / seal integration |
| J-4c-pr3188 | Versioned eight-class builder, P1 permission, K-A/K-B metadata, independent inventory/record derivation, density extraction/report and persisted-schema oracles prepared | Exact-head independent review, earlier phases and final-candidate / seal gates |
| J-4c-pr3141 | Left out | **needs migration number**: G8's absent migration 1306 cannot be created or renumbered without an allocation |
| J-4c-a55l | Left out with its G8 implementation | **needs migration number**; later census readback and original dependencies |
| J-4c-pr3191 | Left out | **needs migration number**: near-miss storage's absent migration 1308; P06b cannot substitute for this allocation |
| J-4c-pr3193 | Left out | **needs migration number**: G12's absent snapshot-copy migration 1305 |
| J-4c-a55m | Left out | Protected apply and disabled-provision readback at the declared phase; SR-A4-01 authorizes preparation only |

The allocation ledger `/Users/Dev/kalayantra/run/MIGRATION_ALLOCATION.json`
contains no allocation to these J4C-B children. No migration file was changed.

## Runtime isolation

(I) INTERPRETATION: preparing final rules must preserve the measuring/default
writer. `rule_registry.rule_profile(final_rules=True)` selects the prepared
catalogue; the default remains the five 1.0.0 paths. Context-local state restores
on exit and does not change another caller's selection. The alternative was the
inherited implicit 1.2.0 default, which changed the measuring catalogue.

The writer opts in through the strictly boolean `gochara_v5_final_rules` config
key. A test-slice marker together with that flag is refused
`final_rules_require_candidate`, before enumeration. The independent verifier
entry point has the matching explicit `--final-rules` option. These options do
not constitute authority to run a final build or protected operation.

Implementation: `platform/python-sidecar/services/gochara_kernel/rule_registry.py:97`,
`platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:414`,
`platform/python-sidecar/pipeline/orchestrator/verification_job.py:80`.

## Inherited overlaps and salvage

The pinned original heads are #3141 `35ceffb7f`, #3187 `6d3966b23`,
#3188 `ab3454188`, #3191 `276ba4cb6` and #3193 `7e66f3362`.
P06's `origin/kalayantra/w4-p06` follow-ups are used for the relevant ND-H
corrections; G12/storage changes are not silently carried with them.
`SURROGATE_ANSWER_18` §§1–6 resolves CORE/DVI absorption, SUPPORT's explicitly
unstored annotation, the authored K-A mapping, karakatva scope and density guard.
The stored inventory JSON carries absorption keys and per-edge metadata without
altering record identity or the frozen coverage-facts payload. The independent
record stage checks K-A values, tiers, absorption context and missing/extra K-B
records. It runs before window attestation.

The near-miss library retains its named limits: stationless-body certification,
stored precision metadata checks and ephemeris-backed job/seal wiring are P06b
work. Its pure non-interference detector is not evidence of five live endpoint
comparisons under a completed final candidate.

The salvage also fixes level forwarding at both record-store withholding
callers: a lord's AD karakatva must not license its PD dispositorship testimony.
The database regression records one AD record and withholds the PD record.
A supporting golden-fixture change cleans its database even when substrate
setup fails before yielding.

## Verification and remaining gate

The six new suites are explicitly selected in the current required A5.3 DB CI
step; automatic discovery has not landed at this branch's main base. That step
also runs `platform/scripts/gochara/mutation_check_verifier_side.py`, which uses
retained tree copies, structured assertion failures, no pytest cache and a
required scratch parent. No mutation edits the active checkout.

The inherited literal stored-row goldens remain unchanged. Builder/verifier/
FB35 fixture equality, whole-catalogue independent pin bytes, real schema
persistence, K-A rank-only behavior, K-B restrictions, the strict 40% guard,
legacy profile restoration, CLI selection and actual job refusal are exercised.
The measuring golden keeps SQL, counts, outcomes and all non-implementation
manifest inputs pinned. (I) INTERPRETATION: source implementation identities
must change in geometry (version-aware record store), evaluation (independent
derivation) and window (factor/job code); their current module digests are
recomputed instead of treating old source hashes as output equality.

(I) INTERPRETATION: local branch objects at the packet's pinned inherited heads
substitute for fetching; the job prohibits Git writes, and all required objects
were already present. The alternative is a cockpit-managed ref refresh.

Builder logs, named negative fixtures, exact revert copies and per-item outcomes
are in this job's `JOB_SCRATCH/result.json`. They are inputs to independent
review, not independent acceptance. The cockpit must rebase against accepted
main, regenerate affected aggregates, run exact-head CI and enumerate the child
IDs in its review. The campaign handshake/close covers this fleet job.


## Local verification record

The job records 724 passing core/integration tests (one explicitly excluded
birth-anchor case), 87 passing final closure checks and 77 passing Vitest tests
(two skipped). The last Vitest invocation used a 60-second default timeout on
this busy host; the test's explicit determinism timeout was unchanged. All
110 named mutations were caught with passing fixed baselines. Seven concrete
finding reversions have retained counterfactual trees and test logs.

The current legacy golden oracle passed across 13 substeps through the suite's
real `_World` clone: SQL shapes/order, counts, outcomes and non-implementation
manifest inputs equal the pinned golden. The original long-lived pytest process
had loaded the earlier two-stage source-hash allowance and retains that single
identity-only failure in its log; the current oracle and current source module
identities were rechecked successfully. No golden data fixture was edited.

(I) INTERPRETATION: the current replay reuses this job's already solved,
pinned-Swiss template through the canonical suite clone, rather than computing
the identical eight-body template again. No computation or output is mocked.
(I) INTERPRETATION: the job's `done` means this source preparation and explicit
left-out dispositions are finished; it does not mean campaign/operation closure.

Implementation lock, writer digests, capability census, unchanged knowledge
snapshot, registry coverage regeneration check, Python syntax, CI YAML and scope
checks pass. The generator wrapper's macOS IPC path limit was handled by running
the same TypeScript generator entry points through `node --import tsx`.

Finished preliminary copies, local dependencies and caches are removed. The
seven revert-proof trees and logs stay in JOB_SCRATCH for cockpit review. The
existing worktree is left uncommitted for the launcher; no worktree was created
or deleted. The pre-existing local cluster is left running as required. The
attributed interrupted fixture was dropped with its guarded helper and absence
was independently checked; unrelated databases were untouched.
