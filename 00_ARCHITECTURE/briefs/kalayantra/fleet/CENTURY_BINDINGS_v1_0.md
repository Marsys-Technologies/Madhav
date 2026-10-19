---
artifact: CENTURY_BINDINGS
version: "1.0"
status: ENABLED_WAITING_ON_GATE — no century operation executed or accepted
produced_on: 2026-10-18
changelog: Initial. SR-PREBUILD-ALL enablement of the century family (enabled_by J-4d, request item J-4e); SR-TEARDOWN-AUTHORITY-GATE items 2 and 3.
---

# Century bindings (SR-PREBUILD-ALL)

The century launch is **the measuring launch minus the test slice**: the same accepted request, live lease, scoped backup, rollback-confirmed staging
dry run, single durable no-retry launch claim and "previous lifecycle independently absent" gate (J3C_BINDINGS_PREBUILD_v1_0.md), but the staged run
carries **no `gochara_v5_test_slice` marker**, so the candidate the writer builds is the ordinary, sealable one (a marked run is stamped `test_slice`
and unsealable by construction, MEASURING_BUILD_CONTRACT_v1_0 MB-1).

| Kind | Script | needs | production | state |
| --- | --- | --- | --- | --- |
| `century_dispatch_dryrun` | `platform/scripts/dispatch_v5_century_job.py` | builder | false | enabled |
| `century_dispatch` | `fleet/century_launch.py` | builder + gcloud | true, `remote_async` | enabled |
| `century_teardown_dryrun` | `platform/scripts/teardown_v5_small_test_job.py` | owner | false | enabled |
| `century_teardown` | same script, `--execute --i-am-steward` | owner | true | **disabled** |

Requests carry `item_id=J-4e`, the canonical chart and `args={"classes":"all"}` only. No run name, no horizon: **the launcher chooses no horizon, class
set or rule version** — what generation '5.0' answers after 2026-04-17 is the owner's open N-G9 decision and the writer code J-4d lands.

## Gates, per kind

* `century_dispatch_dryrun` runs the real staging transaction (chart lock, frozen-generation refusal, one active run per chart, registry-row shape,
  N-137 end state, no generation '5.0' output) and **rolls it back**: zero cloud writes. It prints `ky.century_staging/1` — status `ROLLED_BACK`,
  the plan manifest and digest, `triggered_by='gochara-v5-century'`, and `launch_plan`: the exact `gcloud run jobs execute` argv the real kind will run
  (a test pins it to the launcher's actual argv). The previous (measuring) lifecycle must already be independently absent.
* `century_dispatch` demands, from reviewed source (`v5_small_test_shared.century_request_problem`): that absence, a fresh scoped backup restore
  proof, and the receipt of a `century_dispatch_dryrun` whose manifest digest, args and source equal the new staging (a measuring dry run, a marked
  manifest, another trigger or a different digest refuse). The executor adds the lease, the single V acceptance, `dry_run_passed`, the production
  fence and the merged reviewed commit. The wrapper stages once and launches exactly that run with `PUBSUB_DISABLED=1` for that execution only (so the
  J-3 log read sees the sub-step lines); `ky.century_launch/1` is the executor's launch evidence. Completion is never the launch: it is read back by
  `readback_sql` for the recorded run id, and the Cloud Run execution is observed through `cloudrun_job_readback`.
* `century_teardown_dryrun` / `century_teardown` (SR-TEARDOWN-AUTHORITY-GATE item 3) reuse the scoped teardown with a **run_id scope**
  (`century_scope`: run id, manifest id, input-vector digest, the accepted `century_dispatch` receipt). **Evidence that today's scope did not cover a
  century candidate:** it selects runs by the small-test trigger and proves ownership by a test-slice stamp, so it refuses a century candidate by
  name (`test_todays_scoped_teardown_refuses_a_century_candidate`, real SQL). The extension keeps every guard (locks, frozen-generation refusal, rowset
  digest rollback proof, absence census) and swaps two things: the owned trigger, and an ordinary-candidate proof
  (`century_generation_ownership`: status `candidate`, default `stored_scope`, no `test_slice` component, unmarked staged manifest, snapshot / inventory /
  coverage tied to the one run). It refuses a stamped test-slice candidate, and a test-slice teardown refuses a century one.

## Interpretations (I) and what is left open

* **(I) INTERPRETATION C1:** the launch script is written now (SR-PREBUILD-ALL) although the plan model's J-4d/J-4e brief only names the op and the G8
  gates; the missing specification (horizon, rules) belongs to the writer, so the launcher is horizon-agnostic. Alternative: leave `century_dispatch`
  disabled with `TO_BE_SET_BY_J-4d` until N-G9 is decided.
* **(I) INTERPRETATION C2:** `needs` changes from `gcloud` to `builder` + `also_needs: [gcloud]` (it stages with the builder connection, like
  `measuring_dispatch`; W4_EXECUTOR_BINDINGS asked "confirm any staging builder requirement"). Alternative: launch an already-staged run, gcloud only.
* **(I) INTERPRETATION C3:** request item is `J-4e` (the plan's dispatch item, `op: century_dispatch`); the table's `enabled_by` stays `J-4d` as pinned.
  The teardown kinds use the same item.
* **(I) INTERPRETATION C4:** a real century dispatch requires the scoped backup proof (`scoped_backup_problem`) as `smalltest_dispatch` does, because
  SR-PREBUILD-ALL lists "scoped backup by content hash" among the J3C gates; `measuring_dispatch` does not. Alternative: drop it to match measuring.
* **(I) INTERPRETATION C5:** `century_teardown` is added **disabled**: SR-TEARDOWN-AUTHORITY-GATE says no century teardown executes until an owner
  authority naming century candidate rows (OWNER-AUTH-TEARDOWN-v2) is recorded and `teardown_gate` reads it. Flipping `enabled` is a table-only edit.
* Still open, not decided here: N-G9 (the horizon '5.0' answers), P06b, D-G9, the measured cap and Cloud Run timeout readback, D-CLOUD, the
  `teardown_gate` ledger check and OWNER-AUTH-TEARDOWN-v2.
