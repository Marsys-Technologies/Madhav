# Runtime Packets

Use these packet shapes when the repository does not already provide an equivalent schema. Extend them with repository-specific fields; do not create a second control plane when accepted schemas exist.

## Layer manifest

```json
{
  "schema_version": "1.0",
  "campaign_id": "campaign-id",
  "layer_id": "layer-id",
  "definition_digest": "immutable-digest",
  "dag_digest": "immutable-digest",
  "status": "RECONCILING|FROZEN|SUPERSEDED",
  "asset_ids": ["asset-id"],
  "created_at": "RFC3339",
  "supersedes_definition_digest": null
}
```

The asset IDs are unique and ordered canonically. A frozen manifest changes only through an explicit supersession event.

## Asset Elevation Record

Use [asset-elevation-record.schema.json](asset-elevation-record.schema.json) and validate with:

```bash
python3 scripts/validate_asset_record.py path/to/asset-record.json
```

The record carries identity, lifecycle/disposition, ownership fence, DAG proof, quality/change classification, release/rebuild binding, producer-coverage binding and terminal evidence. A producer-covered member names its producer and inherits both its production rebuild and terminal acceptance receipts instead of running twice. It is deliberately smaller than the narrative analysis; large evidence lives at referenced immutable locations.

## Decision packet

```json
{
  "schema_version": "1.0",
  "decision_id": "stable-id",
  "campaign_id": "campaign-id",
  "layer_id": "layer-id",
  "asset_id": "asset-id-or-null",
  "question": "decision required",
  "evidence_refs": ["immutable-reference"],
  "options": [
    {"id": "A", "tradeoff": "...", "reversible": true, "throughput_effect": "..."}
  ],
  "recommendation": "A",
  "surrogate_ruling": "A",
  "rationale": "short evidence-backed rationale",
  "decided_at": "RFC3339"
}
```

## Lifecycle event

```json
{
  "schema_version": "1.0",
  "event_id": "uuid",
  "sequence": 1,
  "campaign_id": "campaign-id",
  "layer_id": "layer-id",
  "asset_id": "asset-id",
  "from_state": "ANALYZED",
  "to_state": "INTEGRATED",
  "actor_id": "authenticated-actor",
  "actor_role": "IMPLEMENTER|VERIFIER|SURROGATE|RELEASE",
  "definition_digest": "immutable-digest",
  "code_sha": "merged-tree-sha-or-null",
  "lease_fence": 1,
  "run_generation": 0,
  "evidence_refs": ["immutable-reference"],
  "observed_at": "RFC3339"
}
```

Only the protected verifier/acceptance actor may emit `INDEPENDENTLY_VERIFIED` or `FROZEN`. The event store rejects stale sequence, definition, code, fence or generation values.

## Lease and retry configuration

```json
{
  "schema_version": "1.0",
  "lease_seconds": 900,
  "heartbeat_seconds": 120,
  "max_transient_retries": 2,
  "max_identical_failure_fingerprints": 2,
  "max_continuations": 10,
  "task_wall_clock_seconds": 7200,
  "production_write_domains": ["shared", "chart-id"]
}
```

Set values from observed runtime and repository constraints. Do not silently inherit examples as measured limits.

## Minimum transition rules

- Ownership and fence are written before mutation.
- A state change references the definition under which it was decided.
- Integration requires a protected merged-tree SHA.
- Deployment/rebuild evidence is invalid if it predates the current definition, serving SHA or fence.
- Optimization requires equivalent output plus measured efficiency evidence.
- Correctness/enrichment requires an expected-delta contract and provenance evidence.
- Freeze requires an independent acceptance receipt written by the protected actor.
- A supersession never rewrites prior events; it makes ineligible events visibly historical.
