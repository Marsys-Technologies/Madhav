---
artifact: K9_FINAL_PREBUILD_v1_0.md
version: '1.0'
status: BUILT_WAITING_ON_GATE
authority: 'A6 D-40; SR-A4-01; production operations remain disabled'
changelog:
  - '2026-10-16 (K9-FINAL-N01/N02): remove branch-authored aggregates, require CI/scratch generation and declare the public published-response density contract.'
  - '1.0 (2026-10-16): explicit published-stage serving, Portal handover adapter, offline final rebuild/readback and complete census inspection.'
---

# K9 final-layer preparation

This package prepares K9-6, K9-4a and K9-4b. It does not dispatch a build, take a backup, claim a lease, verify production, publish, roll back, or create an acceptance receipt. Every operational acceptance step remains pending. No migration, writer, FROZEN orchestrator file, L0–L2 asset or Portal host is changed.

The source contracts are PLAN `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:238` (candidate lifecycle), `:253` (serving), `:293` (full-layer scope), and `:301` (governance). The ordered 19-writer roster comes from `platform/python-sidecar/services/kala_core/rehearsal.py:28`. The 25-asset census population includes historical assets and the delivery registrar; it is deliberately larger than the replaceable rebuild set. The registrar never enters the rebuild.

## K9-6: explicit published requests

All seven established public names accept an optional `published_request` object with the existing stage selectors: `at`, `date_from`, `date_to`, `event_class`, `assertion_id`, `source_table`, `record_id`, `limit`, `offset`. For example:

```json
{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","published_request":{"at":"2026-10-16T12:00:00Z"}}
```

Call `kala_now_get` with this object to receive the published NOW stage envelope. AHEAD requires explicit `date_from` and `date_to`; ELECT/RITUAL additionally require the stored `event_class`; EXPLAIN requires an assertion ID or an exact source/record drill. Required selectors stay with the existing stage descriptor. A request never supplies its own chart inside `published_request`.

**(I) INTERPRETATION:** explicit opt-in is additive. Requests without the field retain the old contracts and their existing MCP callbacks; the web legacy adapter remains unavailable. The alternative, inferring stage instants/classes/IDs from old dates, undertakings or domains, has no sourced mapping and would break compatibility. Ritual's Mode-3 redirect stays prior to I/O.

The unchanged Vidhi bridge resolves the same public URI; the MCP alias forwards to that public registry identity after chart authorization. Registry execution delegates to the existing stage reader. Query failures and absent publication are disclosed; neither becomes `evaluated_silent`. Manifest/chart/generation bindings are checked at the MCP boundary. Budget trimming retains the existing confirmed-row floor.

**(I) INTERPRETATION (K9-FINAL-N02):** each public descriptor's `density_contract` declares the explicit `published_request` response: per-source pagination, `event_class`/`source_table` facets, and `empty_reason` discipline. The alternative, applying that declaration to the legacy envelope, would assert a contract the compatibility adapter does not add. Requests without `published_request` keep their existing legacy behavior.

`platform/src/lib/retrieval/registry/layers/L3_kala/arrival_state.ts` supplies `arrivalFromPublishedNow(chart_id, payload)`. It restates the returned page's published negative-space states as labels suitable for ArrivalLine's existing `arrival` prop. Missing, private, unknown or context-only states produce null. It derives no daśā or release time. Real-SQL fixtures render both planted sentinels through the unchanged component.

### Portal custody request — draft for posting, not posted

`PA-REQ-06` is proposed, subject to the cockpit checking that the ID is still unused before posting on **campaign-coordination**. That branch's `CAMPAIGN_COORDINATION.md:300–326` assigns Portal door code to Pūrṇa Anveṣaṇa; this checkout cannot post to that branch or the external run folder.

Requested change: in the Portal custodian's live arrival-line host, make the authenticated `kala_now_get` call with the explicit current instant under `published_request.at`, pass its returned payload to `arrivalFromPublishedNow`, and feed the result to ArrivalLine's existing `arrival` prop within the host's session lifecycle. Render `information unavailable` for a planted `information_unavailable`; never replace it with evaluated silence, a release date or a guessed daśā. Keep an unavailable/unpublished response as null. The custodian owns error/loading handling and integration acceptance. No live host hookup is asserted by this package.

After the gate opens, independently capture each view's real response, URI, arguments, published manifest, serving head and timestamp. The job-folder captures are explicitly **local guarded fixtures**, not live acceptance and not `K9_6_LIVE.json`.

## K9-4a/K9-4b: offline preparation

Run from `platform/python-sidecar`:

```sh
python -B -m services.kala_core.final_rebuild prepare --plan /path/to/k9-1-preparation.json --run /path/to/frozen-run.json > /path/to/final-bundle.json
python -B -m services.kala_core.final_rebuild census --census /path/to/k9-5-census.json --expectations /path/to/independent-expectations.json > /path/to/census-inspection.json
python -B -m services.kala_core.final_rebuild inspect --bundle /path/to/final-bundle.json --readback /path/to/executor-readback-payload.json --phase rebuilt
```

These three commands read files and emit JSON only. There is no DSN or execute option. `--phase verified` additionally requires current-input verification; `--phase published` requires the candidate head and retained previous publication. The readback input is the JSON value of the single SQL column `evidence`, extracted from an independently captured executor result. Preserve the executor request, operation, reviewed head, output digest and independently accepted receipt beside it; this importer does not authenticate files or replace that chain.

The plan is K9-1's complete prepared object, with `conventions.publication_grains` supplied by the real upstream plans for **every** frozen writer. Materialized entries must agree exactly with `grains_by_asset`. The frozen run must match the canonical chart, complete 20-asset roster in stage order, asset-set target and `action=rebuild`; `clear_before` remains false. Reserved generation `NONE` is only the K9-23 CLI encoding for an absent expected head, never a generation name.

**(I) INTERPRETATION:** K9-23's per-writer publication requirement includes services/adapters. Their actual grain keys must be supplied; this tool does not infer them from successful rows. The alternative, inventing a default service grain or omitting those writers, would conceal unplanned work.

**(I) INTERPRETATION:** peers inside a dependency wave retain the actual frozen run order. The K9-23 `assets` argument uses that order exactly. The alternative, imposing the spelling order of the K9-1 roster on peers, would reject otherwise valid scheduler output.

The bundle supplies disabled operation templates, exact K9-23 arguments and one read-only SELECT for the full per-writer/candidate/grain/verification/head readback. It contains no executable request. The previous head is pinned for CAS and rollback; if no previous head exists, rollback is explicitly unavailable. `OBSERVED_COMPLETE` means the named phase's stored run, writer intervals, grain results and publication bindings matched; `semantic_verification` and `production_acceptance` remain null.

K9-23 is not imported by this PR. The interface inspected here is `origin/kalayantra/k9-23` at `bc590494f9a1f4db69cae23f8f935462832fd9a5`: `platform/python-sidecar/services/kala_core/publication.py:104–155`. Its accepted parent is recorded separately in `K9_23_N2_CUSTODY_v1_0.md`. Requalify the landed interface before activation. In particular, `rebuild-dryrun` returns `PLAN_ONLY` with `dry_run_passed=null`; it cannot satisfy the execution dry-run gate. `verify` records an independently supplied input digest and explicitly leaves all-writer semantic verification unset. Neither return code discharges operational acceptance.

### Complete census expectations

The independent file has this shape, with **all 25 assets and all nine gates**:

```json
{"schema":"kala.final_expectations/1","author":"independent reviewer identity","basis":["source path and line / oracle reference"],"expectations":{"ka_avadhi":{"Ldgr":"PASS","Idem":"PASS","Earn":"PASS","Null":"PARTIAL","Vocab":"PASS","Carr":"NO_DETECTOR","Narr":"PARTIAL","Dens":"PASS","Build":"PASS"}}}
```

This fragment illustrates shape only; it is incomplete and is refused as an actual input. These values are not predictions for the canonical chart. The reviewer authors the real expectations before comparing measurements. The importer never fills them from observations. It reuses K9-5's registry/declaration bindings, applicability/caps and detector-NONE refusals. A missing asset/criterion/expectation, an errored measurement or a mismatched expectation refuses inspection. A matching predicted FAIL remains listed under `non_passing_gates`; a census match is not certification or production authority.

### Gate sequence still owed

1. Land/requalify K9-23 and its open regression/activation prerequisites. Supply authoritative upstream/candidate inputs, all real grain plans and the frozen canonical run. Independently inspect all-writer semantic evidence and the full K9-5 census against authored expectations.
2. For each real production request, the executor/surrogate must establish the live exclusive lease, backup and verified restore, accepted execution dry run, single slot, request-bound PARĪKṢAKA pre-acceptance, reviewed merged head and remaining campaign gates. No template here establishes any of them.
3. K9-4a: prepare backup/restore and orchestrator operations through the existing executor only. The builder never dispatches. After dispatch, independently read the recorded run through executor `readback_sql`; no exit-code acceptance.
4. K9-4b: inspect all writer/grain results, dispatch the independent verifier with its separately derived digest and semantic oracles, inspect the verification, then CAS-publish through K9-23 and read back the head plus retained previous publication. Rollback stays the K9-23 retained-head CAS under the same gates.
5. K9-6: capture the seven live views and the custodian's planted-sentinel arrival-line acceptance against the actual published head. Only the independent review may write canonical step receipts.

## CI and retained evidence

The required Kāla DB job discovers the new tests under `tests/l3/kala_db/`; no explicit test-path list is added to CI. Its dependency setup now installs both serving packages because the discovered suite exercises the actual SDK, registry and SQL boundaries. The existing DB Integration serving test receives the same MCP dependency. Normal platform test discovery covers the registry and arrival adapter.

Machine-owned outputs, including the capability estate census and knowledge snapshot, are generated by CI from main under A5 D-33. This rework removes PR #3622's aggregate changes by restoring the pre-PR base bytes; do not refresh or commit those outputs in this branch. At integration, preserve the then-current CI-owned outputs from main. If a test requires fresh outputs, use the landed `platform/scripts/governance/ci_generated.py generate --destination "$JOB_SCRATCH/generated"` via `python3` and point that test at the scratch copy. This stacked checkout predates `ci_generated.py`, `ci_discovery.py` and `ci_test_suites.json`: generation/discovery verification remains an integration prerequisite after those mechanisms land. At that head, run the actual discovery guard and require `current`; add any needed test glob to a profile in `ci_test_suites.json`, never explicit test paths to `.github/workflows/ci.yml`. Writer digest locks remain untouched.

Job-local logs, local response captures and fail-on-revert copies are referenced by `result.json`. Those copies stay for cockpit review; the cockpit removes them and this working copy after landing or abandonment under the owner cleanup policy. The campaign's one handshake/close remains the cockpit's responsibility; this fleet job does not append shared session state.
