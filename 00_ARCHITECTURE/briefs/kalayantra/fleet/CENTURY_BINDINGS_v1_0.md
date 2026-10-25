---
artifact: CENTURY_BINDINGS
version: "1.0"
status: ENABLED_WAITING_ON_GATE — no century operation executed or accepted
produced_on: 2026-10-18
changelog: Initial. SR-PREBUILD-ALL enablement of the century family (enabled_by J-4d, request item J-4e); SR-TEARDOWN-AUTHORITY-GATE items 2 and 3. 2026-10-19 (SR-EDGES-PROOF 2, SR-HORIZON-PUBLIC): `century_contract.json` + its generator `century_contract.py`; a century dispatch and its dry run carry `century_contract_sha256` and the executor binds it (`century_contract_problem`).
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
| `century_resume` | `fleet/century_launch.py --resume` | builder + gcloud | true, `remote_async` | **disabled** (SR-RESUME-NOW: the launcher mode and the writer's ledger are separate items) |
| `century_teardown_dryrun` | `platform/scripts/teardown_v5_small_test_job.py` | owner | false | enabled |
| `century_teardown` | same script, `--execute --i-am-steward` | owner | true | enabled (W3W4 pack verify E1; signed-only) |
| `century_cancel_dryrun` | `fleet/century_cancel.py` (`--dry-run`) | gcloud | false | enabled (W3W4 pack verify E1) |
| `century_cancel` | `fleet/century_cancel.py` | gcloud | true | enabled (W3W4 pack verify E1; signed-only; fence-exempt; `ky.century_cancel/1`) |

Requests carry `item_id=J-4e`, the canonical chart and exactly five `args` (F-CHANNEL, SR-W34-PREP-RULINGS 1, OD-1 SR-OD1-NUMERICAL; all five required): `classes` = `all`,
`final_rules` = `true`/`false`, `defer_in_build_verify` = `true`/`false` (`true` only with `final_rules` `true`), `horizon` = `<start>,<end>`, the two derived
D-G9 bounds as tz-aware ISO timestamps, and `result_policy` = `all_null_candidate/1` or `window_qualification/1` (OD-1: the century build is the first NUMERICAL-policy build; the policy is named, never defaulted). No run name, no small-test horizon pair: **the launcher chooses no horizon, class set or rule version of its own** — the
values are the request's. The production orchestrator hands the writer `chart_id` and `birth_params` only, so the dispatch STAGES the four in
`plan_manifest["gochara_v5_century_config"]` (validated by the writer's own `validate_century_config`, canonical UTC form); that manifest is covered by
`plan_manifest_digest`, which the writer verifies on every read, and the writer overlays the values on `ctx.config`. The request digest covers `args`, so the
acceptance and the pack fill bind all five. The writer refuses (`run_rule_profile_required`, `run_horizon_required`, and — for a final-rules run — `run_result_policy_required`) a run that is not a test slice and arrives
without an explicit rule profile or horizon — it never defaults to the measuring profile or to `DEFAULT_HORIZON`. A test slice (the measuring build) is unaffected.
The horizon pair is public (SR-HORIZON-PUBLIC: start = the writer's `DEFAULT_HORIZON[0]`, end = the §B birth date + 100 years) and is committed verbatim in `fleet/century_contract.json`; test fixtures use synthetic bounds.

## Gates, per kind

* `century_dispatch_dryrun` runs the real staging transaction (chart lock, frozen-generation refusal, one active run per chart, registry-row shape,
  N-137 end state, no generation '5.0' output) and **rolls it back**: zero cloud writes. It prints `ky.century_staging/1` — status `ROLLED_BACK`,
  the plan manifest and digest, `triggered_by='gochara-v5-century'`, and `launch_plan`: the exact `gcloud run jobs execute` argv the real kind will run
  (a test pins it to the launcher's actual argv). The previous (measuring) lifecycle must already be independently absent.
* `century_dispatch` demands, from reviewed source (`v5_small_test_shared.century_request_problem`): that absence, ~~a fresh scoped backup restore
  proof~~ (removed by SR-A12-BACKUP-REMOVAL), and the receipt of a `century_dispatch_dryrun` whose manifest digest, args and source equal the new staging (a measuring dry run, a marked
  manifest, another trigger or a different digest refuse). The executor adds the lease, the single V acceptance, `dry_run_passed`, the production
  fence and the merged reviewed commit. The wrapper stages once and launches exactly that run with `PUBSUB_DISABLED=1` for that execution only (so the
  J-3 log read sees the sub-step lines); `ky.century_launch/1` is the executor's launch evidence. Completion is never the launch: it is read back by
  `readback_sql` for the recorded run id, and the Cloud Run execution is observed through `cloudrun_job_readback`.
* `century_resume` (SR-RESUME-NOW; **shipped disabled**) continues a killed or failed century build over the substeps the writer's committed-substep ledger holds, instead of a
  teardown and a fresh dispatch. Same principal, production fence, contract binding (`century_contract_sha256`, plus `program_identity.writer_digest` = the contract's
  `image.writer_source_digest`) and launch evidence as the dispatch; its **own** owner go (a go names its kind, so neither kind's go opens the other); no dry-run twin, so a V
  lane's acceptance is required. Its absence gate (`v5_small_test_shared.resume_evidence`) is the only one that admits a partly present generation '5.0', and only a
  ledger-attested one: the request cites the launch receipt it resumes (`resumes`, `resume_run_id`) and states its `program_identity` (manifest digest, writer source digest,
  runtime library digest, horizon); an accepted `readback_sql` of `resume_readback_sql()` (`resume_receipt`, `resume_acceptance`) must show one ledger program equal to the
  request's, every substep committed by an execution of the resumed lineage, per-table counts exactly equal to the ledger's `scope_counts` (an unattested row, or a ledger that
  accounts for more than is present, refuses naming its table), no verification rows, and one candidate manifest. The per-substep `scope_digest` is recomputed by the writer at
  plan time; the executor cannot. `century_cancel` also cancels a resume's execution. The ledger table and columns are the writer lane's migration 1410: the gate reads the names
  in `RESUME_LEDGER_TABLE` / `RESUME_LEDGER_COLUMNS` (one edit reconciles the query and the gate). To enable: land the writer ledger and `century_launch.py --resume`, flip `enabled`,
  and replace oracle X8 of `tests/test_executor_century_resume.py` (and add a pin shard).
* `century_teardown_dryrun` / `century_teardown` (SR-TEARDOWN-AUTHORITY-GATE item 3) reuse the scoped teardown with a **run_id scope**
  (`century_scope`: run id, manifest id, input-vector digest, the accepted `century_dispatch` receipt). **Evidence that today's scope did not cover a
  century candidate:** it selects runs by the small-test trigger and proves ownership by a test-slice stamp, so it refuses a century candidate by
  name (`test_todays_scoped_teardown_refuses_a_century_candidate`, real SQL). The extension keeps every guard (locks, frozen-generation refusal, rowset
  digest rollback proof, absence census) and swaps two things: the owned trigger, and an ordinary-candidate proof
  (`century_generation_ownership`: status `candidate`, default `stored_scope`, no `test_slice` component, unmarked staged manifest, snapshot / inventory /
  coverage tied to the one run). It refuses a stamped test-slice candidate, and a test-slice teardown refuses a century one.

## The launch contract (`century_contract.json`; SR-EDGES-PROOF 2, SR-HORIZON-PUBLIC, SR-W34-LEASE)

`fleet/century_contract.json` (schema `ky.century_contract/1`) is the one committed statement of the century launch's facts: `horizon` (ISO 8601 UTC strings, half-open
`[start, end)`; start = `DEFAULT_HORIZON[0]` of the writer, end = the §B birth date + 100 years, committed verbatim — both bounds are public), `classes`, `policy` (STRICT contact
certification = the writer's unmarked-run `raise` policy; final rules and the in-build-verify deferral from the pack's VERIFY_DEFERRAL.json carrier), `cap` (migration 1395's
72,000 s watchdog), `timeout` (the pipeline job's Cloud Run task timeout), `image` (job, project, region, repository, the writer-source digest the deployed image must carry), and the
facts `century/rebind_pins.py` binds into CENTURY_BINDINGS.json (`generation`, `triggered_by`, `stored_scope`, `launch_args`, `output_tables`, `cancel_schema`). **Nothing in it is typed**:
`fleet/century_contract.py --write --pack <PACK>` derives every value from its owning source, and `--check` (and `tests/test_executor_century_contract.py`, with
`tests/test_century_contract_smalltest_image.py` for the writer-source digest) refuses a file that differs from what the sources give. A writer or deploy change that moves one of those
sources makes the file stale by name until it is regenerated — the same discipline as `implementation_digest.lock.json`.

**Binding.** A `century_dispatch` / `century_dispatch_dryrun` request carries `century_contract_sha256`; `executor.century_contract_problem` (at the tail of `validate`, so again right
before execution) admits it only when it equals the sha256 of the contract file read with `git show <reviewed_commit>:…` — a fill built against any other contract is refused — and the
file's `launch_args` are exactly the request's `args`. The pack's template pins the field (its fill is then bound to the same sha through its own digest). The contract's `launch_args` are the five request args (`classes` `all`, `final_rules`, `defer_in_build_verify` and
`result_policy` as `true`/`false`/policy name from the pack's VERIFY_DEFERRAL carrier — which must therefore carry `result_policy` — and `horizon` as `<start>,<end>` from the committed horizon): a request whose args differ from them in any value is refused.

## Interpretations (I) and what is left open

* **(I) INTERPRETATION C1:** the launch script is written now (SR-PREBUILD-ALL) although the plan model's J-4d/J-4e brief only names the op and the G8
  gates; the missing specification (horizon, rules) belongs to the writer, so the launcher is horizon-agnostic. Alternative: leave `century_dispatch`
  disabled with `TO_BE_SET_BY_J-4d` until N-G9 is decided.
* **(I) INTERPRETATION C2:** `needs` changes from `gcloud` to `builder` + `also_needs: [gcloud]` (it stages with the builder connection, like
  `measuring_dispatch`; W4_EXECUTOR_BINDINGS asked "confirm any staging builder requirement"). Alternative: launch an already-staged run, gcloud only.
* **(I) INTERPRETATION C3:** request item is `J-4e` (the plan's dispatch item, `op: century_dispatch`); the table's `enabled_by` stays `J-4d` as pinned.
  The teardown kinds use the same item.
* **SUPERSEDED by SR-A12-BACKUP-REMOVAL (2026-10-22):** a century dispatch no longer requires or judges a scoped backup (`century_request_problem` no longer calls `scoped_backup_problem`); every other check of that policy stays. The text below is the historical reading.
* **(I) INTERPRETATION C4:** a real century dispatch requires the scoped backup proof (`scoped_backup_problem`) as `smalltest_dispatch` does, because
  SR-PREBUILD-ALL lists "scoped backup by content hash" among the J3C gates; `measuring_dispatch` does not. Alternative: drop it to match measuring.
* **(I) INTERPRETATION C6 (W3W4 pack verify E1/E3):** `century_teardown` is now **enabled** because its dry-run twin exists and the W3W4 pack's bind predicate (`century/rebind_pins.py`) needs all six century kinds enabled; every `*_teardown` stays signed-only, and the pack's own teardown gate still reads the owner authority named in C5. `century_cancel(+dryrun)` bind to the `century_dispatch` receipt (J-4e) and an ABORT/stall verdict, exactly as `measuring_cancel` does for the measuring build. The scoped backup of C4 is now the **`century` scope** (`backup_v5_century_scope.json`, digest pinned in `v5_small_test_shared.SCOPED_BACKUP_SCOPE_SHA256S`): same tables as the small-test scope (the unmarked run writes no other table), its own name and digest, so a small-test proof no longer admits a century dispatch. Alternative: keep accepting the small-test scope's proof.
* **(I) INTERPRETATION C5 (superseded by C6 for the enabled flag):** `century_teardown` was added **disabled**: SR-TEARDOWN-AUTHORITY-GATE says no century teardown executes until an owner
  authority naming century candidate rows (OWNER-AUTH-TEARDOWN-v2) is recorded and `teardown_gate` reads it. Flipping `enabled` is a table-only edit.
* Still open, not decided here: N-G9 (the horizon '5.0' answers), P06b, D-G9, the measured cap and Cloud Run timeout readback, D-CLOUD, the
  `teardown_gate` ledger check and OWNER-AUTH-TEARDOWN-v2.
