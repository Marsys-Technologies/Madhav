# K9-4b `k9_rebuild_stage`: staging the production run and candidate (ruling SR-PREP-LANES-1 (2))

`orchestrator_rebuild` refuses unless production already holds a frozen `build_runs` row (state `planned`, `plan_manifest` + digest, queued `build_run_assets`) and ONE `building`
`kala_layer_candidate` bound to that run, pinned to the live head and carrying `conventions.publication_grains` for every planned writer
(`services/kala_core/publication.py` `_run`, `_candidate`, `inspect_rebuild`). Before this kind nothing in `executor_ops.json` created them; only the sizing kit did, in a throwaway database.

| | |
|---|---|
| kinds | `k9_rebuild_stage_dryrun` (non-production; stages in a transaction it rolls back and reads the rollback back) and `k9_rebuild_stage` (production) |
| child | `python -m services.kala_core.rebuild_stage stage[-dryrun] --assets <ordered closed plan> --run-id <uuid> --natal-build <uuid> --expected-head <generation|NONE>` in `platform/python-sidecar`, builder connection only |
| item | `K9-4b` only |
| admission (production) | generic production gates (canonical chart, live lease, signer acceptance or a verified pack fill) + the owner's go for THIS kind (`run/ops/owner_go/<operation_id>.json`, `OWNER_GO_KINDS`) + a COMPLETED `k9_rebuild_stage_dryrun` of the same identity (`dryrun_receipt`) + two accepted, fresh readbacks (`absence_readback`, `exposure_readback`) of the fixed queries in `fleet/k9_stage_policy.py` |
| not | not signed-only (it neither deletes nor serves), not remote_async (it finishes with its child) |

## Request order (cockpit)
1. Choose the run id, the ordered closed plan (the child refuses any other order and names the derived one), the settled natal build, and read the served head.
2. `python3 fleet/k9_stage_policy.py sql absence <run-id>` and `... sql exposure <run-id>` print the two fixed queries; prepare each as a K9-4b `readback_sql` with `fleet/k9_readback.py prepare_readback` (it binds the digest the policy compares) and have them accepted.
3. `k9_rebuild_stage_dryrun` with the identical item / chart / commit / args. It must COMPLETE (exit 0 = rollback confirmed).
4. `k9_rebuild_stage` carrying `absence_readback`, `exposure_readback` ({name, sha256} of the readback receipts), `dryrun_receipt`, the lease and the signer's acceptance; the owner's go for it.
5. The child commits, reads the rows back and prints one `ky.k9_rebuild_stage/1` document (`STAGED`; a repeat of the identical request prints `ALREADY_STAGED` and writes nothing). Anything else that exists is refused BY NAME and nothing is written.
6. Then `orchestrator_rebuild_dryrun` / `orchestrator_rebuild` for the same run id and assets.

Staging touches no served row (the candidate is `building`, nothing is attested, the head is only read), never writes `asset_throughput`, and changes nothing of the frozen orchestrator contract (CLAUDE.md N.2).
