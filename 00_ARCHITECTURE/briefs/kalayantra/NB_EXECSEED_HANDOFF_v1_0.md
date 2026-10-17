---
artifact: NB_EXECSEED_HANDOFF_v1_0.md
version: "1.0"
status: PREPARED_REQUIRES_PREREQUISITES
authored_on: 2026-10-16
changelog: "Initial FU-SEED-N01/N02 preparation and integrated verification for PR #3627."
---

# Executor seed review follow-up

Preparation for the branch stacked on PR #3627 (`d534d8f6f628d1107e5ac712b25301aefe2b21ea`).
Land after #3588 (CI discovery) and #3626 (executor pin repair), preserving #3627's
scratch lifecycle and exact `execute` override. This records local verification;
remote required checks and landing remain cockpit actions.

## FU-SEED-N01 — required CI discovery

`platform/scripts/governance/ci_test_suites.json:520` extends the existing
`governance-tool-tests-shard-5-0` profile with the executor test family. Its existing
operation family and every other profile are preserved. No workflow test-file
selection is added. The new checks at
`platform/scripts/governance/__tests__/test_executor_ci_discovery.py:29` verify
that the required governance shard invokes this profile, discovers the executor
file, and retains both existing operation files. The second check at `:48` proves
that future executor and operation family files are discovered automatically.

The profile was taken from the local #3588 snapshot
`647bf033e87360dae3ac1568085d2db94a1128c2`; relative to that snapshot, its only
change is the additional glob at `ci_test_suites.json:525`. The snapshot's workflow
invokes this profile on shard 1 and includes that shard in the required governance
aggregate. The new tests exercise those actual bindings in the integrated copy.

**(I) INTERPRETATION:** prepare the additive profile change against the available
immutable #3588 snapshot, without importing its workflow, runner, generated outputs,
or other infrastructure into this branch. Alternative: duplicate that infrastructure
here or leave the discovery finding as a carry-forward. Because the starting branch
has neither the runner nor the profile, this adds the complete existing profile file;
when integrating #3588, retain its profiles and apply only the executor-family addition.

The new tests explicitly skip on this starting branch because its runner is absent;
that skip is not CI acceptance. After prerequisite integration they must execute.
In the scratch integration, both tests pass; reverting only the added glob makes
both fail. The actual discovery entry point collects and passes all 11 #3627 seed
regressions. Its workflow guard prints `CI test discovery governance: current`.

## FU-SEED-N02 — existing repair confirmed, no duplicate change

No executor source, operation table, or executor pin test is changed here. The
existing #3626 repair at `b8ef33b0c863947fe9671de0f357a34bafcedc0e` already
enumerates #3607's disabled measuring bindings (`test_executor_table.py:61` at that
commit) and pins the exact reviewed function bodies (`:292` at that commit).
The review requested cross-reference and integrated confirmation of that repair,
not another normalization rule. This is why no second pin repair belongs here.

Applying only #3626's executor-test patch to a scratch copy of #3627 preserves
#3627's `W4_FUNCTION_HASHES["execute"]` override
(`00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_executor_table.py:249`), its
11 seed cases, and every earlier test. The safe integrated selection passes
65 cases, including #3626's measuring mutation checks. The three reported pin
cases pass; restoring the pre-#3626 test file makes precisely those three fail.
The starting branch still reproduces those three inherited failures, as expected
before #3626 integration. No broader normalization was introduced.

**(I) INTERPRETATION:** the job's prohibition on Git-writing commands also covers
isolated test repositories. Alternative: allow the existing `World` fixtures to
write disposable Git repositories. Consequently, 31 such cases remain unexecuted
locally and must run in CI; they are neither removed nor marked passed. All 96
integrated executor cases collect. No database suite applies to this CI-only change.

## Evidence and landing

Job: `X-20261016T152459Z-nb-execseed`, under the campaign's `fast/jobs/` scratch root.
`verification.json` records commands, exit codes and logs. `evidence.py` reproduces
the checks. `proofs/integrated`, `proofs/reverted-n01`, and `proofs/reverted-n02`
retain the tested copies. The proof harness redirects only read-only Git object
lookups to the existing checkout and rejects any other Git subprocess.

Before landing, integrate #3588 and #3626, retain #3627's execute override and all
seed cases, then rerun the discovery guard, both discovery tests, and the complete
required governance profile in CI. These are integration prerequisites, not a
production seed authorization. Campaign-level governance close remains with the
cockpit under the existing campaign handshake (root `CLAUDE.md` §G/§H).
