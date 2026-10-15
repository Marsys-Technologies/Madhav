---
artifact: L5_HANDOFF_5_0
version: "1.0"
status: PREBUILD
produced_on: 2026-10-16
item: J-7b
authority: "SR-A4-01; declaration only, no production activation"
changelog:
  - "1.0: Declare existing Gochara storage, serving and calibration lineage; add executable local schema readback. Post-flip acceptance remains J-7b-b62."
---

# Gochara 5.0 → Mīmāṃsā calibration hand-off

## 1. Boundary and completion

This is the pre-built contract requested by Pravāha B6.2, not a receipt that
the prediction→outcome loop is operating. The original plan names “L5 calibration
hand-off” after A6.1 at
`/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/PRAVAHA_CAMPAIGN_PLAN_v1_0.md:189`.
The current item and independent residual are
`00_ARCHITECTURE/control/kalayantra/plan_model.json:19950` and
`00_ARCHITECTURE/control/kalayantra/plan_model.json:26344`.

**(I) INTERPRETATION:** B6.2 specifies no additional runtime interface. Use the
existing sealed-generation reader and existing storage as the hand-off, rather
than adding an adapter or a second set of computed values. A consumer implementation
and delivery/outcome operations are separate work. No consumer is activated here.

**(I) INTERPRETATION:** under SR-A4-01, local migration-schema readback qualifies
this declaration's fields only. The exact sealed-generation readback cannot be
earned by a code merge or by fixture metadata. It remains null here until the
independent J-7b-b62 `sealed_field_readback` evidence is accepted after J-6l.
No production manifest ID, horizon, count, score, calibration result or flip is
asserted by this document.

## 2. What the consumer reads

Call `services.gochara_kernel.serving_reader.read_v5(conn, chart_id, generation, ...)`
on a caller-owned read-only snapshot. Pin the canonical chart and literal `5.0`;
never select a “latest” generation or fall back to legacy windows. The reader's
definition is `platform/python-sidecar/services/gochara_kernel/serving_reader.py:557`.
The existing authenticated HTTP alternative is POST `/api/compute/gochara/v5/windows`
(`platform/python-sidecar/routers/gochara_v5.py:86`). This job changes neither route
nor access permissions.

Requests may give event classes and timezone-aware range bounds, or one instant.
The returned schema is `gochara_v5_windows/1`. Retain the entire envelope:

| Surface | Consumer discipline |
|---|---|
| Identity | Pin `chart_id`, `generation`, `manifest_id`, `manifest_status` and `seal`. The seal must name the same manifest; retain its approval brief identity/digest. |
| Scope | Keep `served_horizon`, `stored_scope`, `requested`, `effective_range`, `horizon_clipped` and every class's coverage. The manifest supplies the horizon; no century or scored edge is assumed. |
| Windows | Preserve each `window_id`, class, path/version, interval bounds, peak, score, both evidence channels, native valence, severity, objective, objective value, qualification and null-state disclosure exactly as served. |
| Members | Retain record/contact IDs, affected person, frame, physical target, interpretive role, admission/operator role, period anchor, contact times, truncation and solver metadata. Natal relations can have no contact; nullable exact times are not interpolated. |
| Accounting | Retain class completeness/reasons, `zero_window_reading` and `counts`. A truncated response is not the complete calibration population. |
| Qualification | Retain `result_policy`, `numbers_disclosure`, `ranking`, `ordering`, `scored_until` and each window's scoring status/reason. Missing scored-edge pins remain null, with the given reason. |
| Near misses | Keep the optional layer, its version, status and counts separately. Absent, incompatible or unbuilt near-miss storage is not an empty set of confirmed windows. |

Admission and refusal are implemented at
`platform/python-sidecar/services/gochara_kernel/serving_reader.py:446`.
Unknown, unpublished, unsealed, test-slice and outside-horizon requests are named
refusals, not negative outcomes. A manifest bearing a test-slice key is refused
even when its value is false. A missing result policy or scope cannot be filled
with a consumer default. Missing approval details may be returned with a reason
by the existing reader; they are insufficient for the independent hand-off receipt.

Window/member construction and total ordering are at
`platform/python-sidecar/services/gochara_kernel/serving_reader.py:248` and
`platform/python-sidecar/services/gochara_kernel/serving_reader.py:510`.
Windows sort by start, end, class, path, version and ID. Members sort by contact
entry (missing last), agent, relation, role and record ID. This chronological order
is not probability or strength rank. The HTTP limit defaults to 500 and caps at
5000 (`platform/python-sidecar/routers/gochara_v5.py:24`). There is no offset cursor:
for a complete extract use `read_v5(..., limit=None)` on the approved snapshot, or
bounded requests with explicit deduplication by window ID and counts checked for
truncation. Never label a limited page as the whole generation.

Coverage is constructed by
`platform/python-sidecar/services/gochara_kernel/scope_response.py:272`.
“Searched complete, none”, unsearched, partially searched and unverified classes
must stay distinct. Neither an empty array nor an `on_demand` scope declaration
proves absence. Moon-on-demand and named scope limits travel with the answer;
the consumer must not infer a fully stored Moon layer.

## 3. Storage and provenance declaration

The following block is the field inventory for backing-table readback. All tables
are in `public`. Chart-scoped reads bind **both chart and generation**. The global
physical-object and rule registries are reached only through the pinned member
IDs and composite rule versions; they have no invented chart/generation columns.

```json
{
  "schema": "gochara_l5_handoff/1",
  "status": "PREBUILD",
  "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
  "generation": "5.0",
  "reader": "services.gochara_kernel.serving_reader.read_v5",
  "envelope_schema": "gochara_v5_windows/1",
  "activation_gates": ["J-6l", "J-7b-b62:sealed_field_readback"],
  "sealed_generation_readback": null,
  "probability_target": null,
  "forecast_delivery": "separate_issued_forecast_lifecycle",
  "storage": {
    "kala_gochara_publication": ["chart_id", "generation", "manifest_id", "status", "writer_asset_id", "convention_id", "input_generation_vector", "ephemeris_backend", "horizon", "row_counts", "content_digest"],
    "ka_gochara_generation_seal": ["chart_id", "generation", "manifest_id", "sealed_at"],
    "ka_gochara_seal_approval": ["chart_id", "generation", "manifest_id", "brief_id", "brief_digest", "producer_execution_id", "approver_login", "workflow_commit"],
    "ka_gochara_seal_brief": ["chart_id", "generation", "manifest_id", "brief_id", "brief_digest", "state_digest", "runner_identity", "producer_commit", "image_digest", "execution_id"],
    "ka_gochara_eval_window": ["chart_id", "generation", "window_id", "event_class", "path_id", "rule_version", "interval", "peak_instant", "score", "evidence_for", "evidence_against", "outcome_valence_for_native", "severity", "objective", "objective_value", "qualification", "null_states_used", "coverage_facts"],
    "ka_gochara_eval_window_record": ["chart_id", "generation", "window_id", "record_id"],
    "ka_gochara_relationship_record": ["chart_id", "generation", "record_id", "event_class", "path_id", "rule_version", "contact_id", "object_id", "agent", "relation", "object_kind", "object_role", "affected_person", "frame_kind", "frame_arg", "operator_role", "admission_state", "provenance", "ruling_ref", "source_text", "source_page", "source_fact_ids", "temporal_support_state", "temporal_support_grain", "temporal_support_intervals", "precision", "period_anchor_lord", "period_anchor_level"],
    "ka_gochara_contact": ["chart_id", "generation", "contact_id", "physical_object_id", "occurrence_ordinal", "convention_id", "body", "relation_kind", "t_in", "t_exact", "t_out", "solver_method", "delta_lambda", "delta_t", "coverage"],
    "ka_gochara_physical_object": ["physical_object_id", "canonical_target", "body", "relation_kind", "convention_id"],
    "ka_gochara_search_input_snapshot": ["chart_id", "generation", "convention_id", "input_generation_vector", "consumed_fact_ids", "consumed_dasha_row_ids", "av_declarations", "l1_facts_digest", "dasha_digest", "input_digest"],
    "ka_gochara_search_inventory": ["chart_id", "generation", "event_class", "horizon", "input_digest", "inventory_digest", "ledger_digest", "finalized_at"],
    "ka_gochara_search_path_pin": ["chart_id", "generation", "event_class", "path_id", "rule_version", "disposition", "exclusion_reason", "ruling_ref", "basis", "committed_ob_ids"],
    "kala_gochara_coverage": ["chart_id", "generation", "partition_kind", "partition_key", "requested_horizon", "completed_horizon", "relations_searched", "unavailable_inputs", "unsearched_reason"],
    "ka_gochara_eval_window_verification": ["chart_id", "generation", "event_class", "path_id", "rule_version", "verifier_id", "verifier_version", "status", "policy_version", "windows_expected", "windows_stored", "windows_reproduced", "windows_unverified", "fields_verified", "input_digest", "derivation_inputs_digest"],
    "ka_gochara_rule_path": ["path_id", "rule_version", "provenance", "operator_role", "ruling_ref", "score_rule"],
    "ka_gochara_rule_path_seal": ["path_id", "rule_version", "sealed_at"],
    "ka_gochara_rule_path_soft_factor": ["path_id", "rule_version", "factor_id", "factor_rule_version"],
    "ka_gochara_factor": ["factor_id", "rule_version", "operand_selector", "direction", "function", "range_lower", "range_upper", "units", "calibration_status", "doctrine_ordering", "category_mapping", "null_state", "effect"]
  }
}
```

Storage authorities:

- Publication and coverage: `platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql:103`.
- Physical objects, contacts and generation seal: `platform/migrations/1153_gochara_sky_event_substrate.sql:619`.
- Factor, path, versioned membership and rule seal: `platform/migrations/1154_gochara_rule_path_registry.sql:310`.
- Relationship lineage: `platform/migrations/1155_gochara_relationship_record.sql:465`.
- Window and member grain: `platform/migrations/1156_gochara_eval_window.sql:247`.
- P1 period-anchor fields: `platform/migrations/1233_gochara_p1_period_anchor.sql:1`.
- Input snapshot, inventory and exclusions: `platform/migrations/1206_gochara_search_inventory_completeness.sql:307`.
- Objective/qualification, verification, persisted brief and approval: `platform/migrations/1240_gochara_window_verification_gate.sql:122`.

To resolve a window, join its member relation on chart, generation and window ID;
join each relationship on chart, generation and record ID. Join its contact on
chart, generation and contact ID; use a left join for natal relations. Reach the
physical object through the relationship's object ID. Carry relationship source
fact IDs plus the input snapshot's consumed fact and daśā IDs/digests. Resolve
facts to the authoritative Gaṇita rows; do not re-derive or overwrite their values.
The same input digest binds the class inventory. Unresolved source references
are a provenance failure, never permission to fabricate a fact.

For factor provenance, join the window's `(path_id, rule_version)` to its sealed
path and soft-factor membership; join `(factor_id, factor_rule_version)` from that
membership to the factor's `(factor_id, rule_version)`. Do not join factors on
version alone or select the newest mapping. Excluded paths retain their reason,
basis and ruling instead of being represented as failed predictions.

## 4. Prediction → delivery → outcome → calibration

A stored window is a model result, not an issued forecast or an observed event.
**(I) INTERPRETATION:** downstream registration uses the separately governed
issued-forecast lifecycle rather than treating every stored window as delivered.
Its upstream contract is declared by K6-5a/K6-5 at
`00_ARCHITECTURE/control/kalayantra/plan_model.json:4830` and
`00_ARCHITECTURE/control/kalayantra/plan_model.json:4876`; this item neither creates
nor changes that interface. Preserve the exact source manifest/window/member IDs
with the actual delivered statement and information cutoff. Observation, outcome
matching, episode/affected-person adjudication, censored or unknown outcomes and
the accepted evaluation protocol stay separate from transit computation. Do not
use outcome knowledge to rewrite an earlier delivered forecast or sealed source.

Scores and evidence are rank-only unless a separate calibrated event model earns
a probability claim. `calibration_status` is a **factor-registry** field, not a
window field or a generation-wide proof. A calibrated category mapping alone does
not calibrate occurrence probabilities. The doctrine explicitly reserves scale
calibration at
`00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md:165`.
The all-null policy leaves numeric results/peak null and valence unqualified;
the qualification policy passes through only stored, qualified results
(`platform/python-sidecar/services/gochara_kernel/result_policy.py:1`). Nulls
must not become zeros, midpoints, favourable defaults or confidence labels.
Evidence for and against occurrence stay distinct; valence describes the native's
outcome, not whether an event occurs. Testimony does not become scored evidence.

Calibration proposes a **new factor/rule version and, when applicable, a new
generation**. It never updates sealed windows, registries, input snapshots or
past issued forecasts in place. Retrodiction metrics, learned mapping proposals,
delivery and outcome writes are outside this declaration. No statistical fit,
quality grade, successful delivery or earned calibration is claimed here.

## 5. Independent post-flip readback

After J-6l, the authorised readback executor uses one repeatable-read, read-only
snapshot to bind the exact chart/generation/manifest/seal/approval/brief identity.
The identity query below returns evidence, not a computed PASS. It intentionally
uses left joins: a missing approval or mismatched seal remains visible.

```sql
SELECT p.chart_id, p.generation, p.manifest_id, p.status,
       p.horizon, p.input_generation_vector, p.row_counts, p.content_digest,
       s.manifest_id AS seal_manifest_id, s.sealed_at,
       a.manifest_id AS approval_manifest_id, a.brief_id, a.brief_digest,
       a.producer_execution_id, a.workflow_commit,
       b.manifest_id AS brief_manifest_id, b.brief_digest AS persisted_brief_digest,
       b.state_digest, b.producer_commit, b.image_digest, b.execution_id
FROM public.kala_gochara_publication p
LEFT JOIN public.ka_gochara_generation_seal s
  ON (s.chart_id, s.generation) = (p.chart_id, p.generation)
LEFT JOIN public.ka_gochara_seal_approval a
  ON (a.chart_id, a.generation) = (p.chart_id, p.generation)
LEFT JOIN public.ka_gochara_seal_brief b
  ON b.brief_id = a.brief_id
 AND (b.chart_id, b.generation) = (p.chart_id, p.generation)
WHERE p.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid
  AND p.generation = '5.0'
ORDER BY p.manifest_id;
```

The independent receipt must record all of the following before accepting B6.2:

1. Exactly one published row; all four manifest IDs agree; approval and persisted
   brief digests agree; the named producer execution agrees. Missing/null evidence
   fails admission. The input vector has no test-slice marker and supplies the
   actual recognised result policy and stored scope. Read the authority separately
   through the J-6l evidence; “published” alone does not prove the flip.
2. For **every column** in the JSON storage inventory, resolve it on this same
   deployed schema and perform a SELECT readback. Read chart-scoped relations
   only for this chart/generation and global relations through the pinned IDs.
   Record column presence independently of row population. Zero rows prove
   neither a searched-empty class nor missing schema; report actual counts and
   coverage, including honest nulls, exclusions and missing provenance.
3. Compare `read_v5` output with stored window/member fields on the snapshot;
   retain completeness, qualification, scope, accounting and ordering. Require
   complete extraction or explicitly mark a partial page. Do not infer semantic
   verification from field presence.
4. Bind the document/source digest, exact manifest identity, query/readback
   evidence digest and independent review to J-7b-b62's `sealed_field_readback`
   receipt. Retain all inherited prerequisites; do not close the residual from
   the local tests or this document's existence.

The local `tests/l3/gochara/test_j7b_l5_handoff.py` suite resolves the declared
columns and executes the identity SELECT in a read-only transaction against the
existing guarded disposable migration fixture. It computes no sky and creates no
sealed-generation evidence. Its mandatory CI command is the existing Gochara
database gate; all prior suites remain selected. No production operation, schema
change, grant, writer change or activation is part of J-7b's pre-build.
