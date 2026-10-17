---
version: "1.0"
status: PREPARATION_ONLY
date: 2026-10-16
changelog: "1.0: supersede inverted historical D-RUN2 recipes with landed D-30 polarity; preserve evidence and activation gates."
---

# Wave 4 run-2 activation recipes

These are preparation recipes for the cockpit. No decision, request, queue entry,
acceptance or operation is emitted by this document or its tests.

This supersedes **only** interpretation I6 and the D-RUN2 recording/conditional
branch recipes in the historical pack at
`/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261015T223446Z-w4-prestage/STAGE/RUNBOOK.md:12`
and its final D-RUN2 command block. That immutable pack inverted the landed
mapping. Its source/model/request pins remain historical and require refresh;
this correction alone does not make any staged request ready to submit.

The actual contract is
`00_ARCHITECTURE/control/kalayantra/plan_model.json:27228-27275` (D-RUN2 and
J-RUN2-RESOLVED), `:18429-18476` (J-2c), and `:18514-18561` (J-2d).
The corresponding four-clause J-2b evidence contract is at `:18350`.

| Measured run-1 outcome | D-RUN2 outcome | Required disposition |
|---|---|---|
| All four clean clauses independently proven after J-2b | approved | Waive run 2: J-2c/J-2d and inherited J-2d-a55i become not_applicable; retain D-RUN2 skip origin and run-1 evidence. |
| Completed evidence establishes a failed clean clause | refused | Run 2 required under all existing acceptance gates; J-RUN2-RESOLVED waits for its actual dispatch/readback/teardown/absence and composite proof. |
| Evidence missing or inconclusive | insufficient_evidence or deferred | Decision stays open; no run-2 launch or waiver; join stays waiting. |

Clean means all four: (1) actual readback equals the independently expected census,
(2) teardown independently proves zero residual rows, (3) dispatch had no retry,
timeout or manual intervention, and (4) the dry-run plan matched the real run.
An unknown clause is missing evidence, not an evidenced failed clause. A severe
finding requires repair before any subsequent operation.

Before recording a final decision, earn J-2b and independently accept its step
receipts. The detail variables below must contain the actual run/request/operation
identities and references **with digests** to expected/actual census, dispatch
history, full dry-run/real-plan comparison, teardown and independent absence
(`run/ops/receipts/J-2b.absence.json`). A literal variable name or boolean is no
evidence. Execute exactly one applicable recipe through the installed wrapper
only after checking that its activated model agrees with the reviewed model.

<!-- scenario: clean -->
```sh
KY_STREAM=N ky decide D-RUN2 --as steward --delegated --outcome approved --detail "$ALL_FOUR_CLEAN_CLAUSES_EVIDENCE"
```

<!-- scenario: not_clean -->
```sh
KY_STREAM=N ky decide D-RUN2 --as steward --delegated --outcome refused --detail "$COMPLETED_RUN1_FAILED_CLAUSE_EVIDENCE"
```

<!-- scenario: unknown -->
```sh
KY_STREAM=N ky decide D-RUN2 --as steward --delegated --outcome insufficient_evidence --detail "$MISSING_OR_INCONCLUSIVE_RUN1_EVIDENCE"
```

<!-- scenario: incomplete -->
```sh
KY_STREAM=N ky decide D-RUN2 --as steward --delegated --outcome deferred --detail "$INCOMPLETE_RUN1_EVIDENCE_AND_RECHECK"
```

On approval, submit none of the historical 15/16 run-2 request templates. Verify
automatic skip propagation and J-RUN2-RESOLVED; never fabricate run-2 receipts or
manual done events. On refusal, rematerialize the conditional 15/16 requests only
after run-1 absence and required repair: `one_class_full` / `marriage`, no horizon
override, current reviewed source and unique identities. Refresh lease, expiry,
backup/restore validity, request-bound independent pre-acceptance and dry run;
retain the real single-launch/manifest identity, terminal no-later-writer proof,
numerical census, teardown rehearsal and independent absence requirements.
Earn J-2d-a55i's actual composite receipt before guarded J-2d completion.

At activation, refresh the **materialized request pack and model-activation
evidence together** against the installed script/table/writer/image/rule/migration
identities. Do not reuse the historical MODEL_PINS or placeholder requests as
current evidence. Check the inherited checklist obligation STEP-3140-03 /
J0M-Q055 and every gate in [the narrow unit-oracle handoff](NB_W4_TOOLING_HANDOFF_v1_0.json).
Require complete mandatory CI at the exact admitted head before integration or
operational reliance, including all inherited C38 rounds and launch checks;
historical timeouts and interrupted runs are not passes or connectivity deferrals.

(I) INTERPRETATION: because historical job folders are read-only evidence, publish
this explicit replacement in the governed branch and require cockpit re-materialization
at activation. Alternative: overwrite the old pack and erase its review history.
