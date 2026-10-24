# K3-2 sealed-producer pre-build

Version 1.0; status: PREBUILD, SR-A4-01; changelog: initial v2 consumer,
private candidate persistence and current K8-K3 evidence mapping. This is code
preparation. No real export, schema application, independent acceptance or
production build is claimed by the planted tests.

## Dispatch and compatibility

`KaVighnakaraWriter.run(ctx)` selects this path only when
`ctx.config.negative_space_sealed` exists. A simultaneous
`negative_space_fixture_inputs` selection is refused. Dry runs need no inputs.
Without the new selection, the existing fixture and legacy dispatch remains.
The writer uses `ctx.db_conn`, `ctx.build_id`, and `ctx.config.chart_id`; it
never owns the connection or transaction and does not publish a head.

The build-bound `kala_layer_candidate` must be `building`, have a nonempty
`candidate:` generation, be absent from the published head and have
`conventions.negative_space` exactly equal to the expected producer pins.
`conventions.fixture=true` is refused. The common advisory publication lock
is taken before the candidate lifecycle lock. Validation and F2 reads precede
partition replacement. All other generations and legacy rows are retained.
query_obstruction_periods.ts:70 serves the head's generation when it holds rows, else the legacy `generation IS NULL` partition
(SR-K9-WRITE-SCOPE; before it filtered `generation IS NULL` only).

**(I) INTERPRETATION I1:** implement the separately required live-storage
prerequisite with this pre-build under owner A3, rather than label a real
producer `fixture_only`. Migration 1388 adds a v2-only CHECK and private natural-key index to the existing
candidate columns and is on the protected list. It changes neither migration
1349 nor the v1 model/storage contract. The writer requires the validated v2
CHECK and unique index before deletion. This migration still needs a protected application and
verified schema receipt; its presence in source is not activation.

## Complete input artifact

**(I) INTERPRETATION I2:** a new internal TSV transport wraps the full raw
rows; it is not a claim that a pending producer already exports this format.
The cockpit/executor supplies `negative_space_sealed={receipt,expected}`:

- `receipt`: the executor's `status=COMPLETED`, `exit_code=0`, `output_file`,
  `output_sha256`, `output_bytes` (fleet/executor.py:224-231).
- `expected`: independently obtained `pins`, logical `row_count` (excluding
  the single header) and `keys`, a mapping of every supported kind to its
  exact sorted natural-key set, including empty sets. Never derive this
  expected inventory from the file being checked.
- TSV has exactly `kind`, `key`, `payload` columns. `payload` is complete JSON,
  not a projection or stdout tail. Exactly one `pins` row has key `pins`.
  Quoted/multiline cells use csv.reader, matching fleet/readback_sql.sh:40-42.
  Duplicate JSON keys, source natural keys, headers, malformed bytes and
  mismatched byte/hash/count/key inventories are refused.

Kinds and full raw source rows:

| Kind | Source / natural key |
| --- | --- |
| seal | ka_gochara_generation_seal: chart_id, generation (1153:892-902) |
| publication | kala_gochara_publication: manifest_id (1081:103-123) |
| verifier | ka_gochara_seal_brief: chart_id, generation, execution_id (1240:698-713) |
| record | ka_gochara_relationship_record: record_id (1155:465-505, 1233:66-78) |
| coverage | kala_gochara_coverage: chart_id, generation, partition_kind, partition_key (1081:225-248) |
| vedha_header | KA-3a's specified kala_vedha_gochara_candidate parent four-key |
| vedha_interval | KA-3a's specified parent four-key plus graha, t_in |
| correspondence | separately admitted record_id + graha/factor/primary-span-to-producer mapping |
| f1 | kala_activation_predicates: id, full conclusion_state_jsonb and derivation_ledger_jsonb (1339:10-34) |
| fact | chart_facts: fact_id with chart/build/ayanamsha and source fact metadata |

The expected pins separately name chart_id, judge_generation (`5.0`),
manifest_id, verifier_execution_id, judge_build_id, natal_build_id, vedha_generation,
f1_generation, ayanamsha_id, convention_id, explicit f2_scenario_id and the complete producer
upstream_fingerprint. The seal/publication/verifier must agree, a full
published manifest is required and a test_slice manifest is refused. The
complete raw record, coverage, header, interval, callback, F1 and F2 evidence
survives in each assertion's provenance, alongside the complete executor
receipt and a commitment to the independently verified key inventory;
evidence_against remains testimony.

**(I) INTERPRETATION I3:** correspondence is an explicit prerequisite,
independently pinned by the export's key inventory and receipt. Each disjoint record/primary-span
mapping names record_id, source assertion_id, explicit exposure, event class, frame/contact/fact
identities, Moon fact, graha, factor, primary_span, source locator, full
vedha_callback_result, upstream fingerprint, f1_id and f2_system. There is no
join guessed from dates, scores, valence or admission. Until an accepted
producer wiring supplies this evidence, rows remain unavailable. Licensed F1
protections must additionally retain their target, nonempty L1 fact ids,
source and exact interval; the current F1 edges lack intervals and therefore
remain `f1_protection_interval_unassessed`. No interval is extended to a whole
window. Consumers must not represent this unfulfilled gate as live admission.

## Meaning and partitioning

The consumer checks both each callback factor and its interval rows,
including every field, exact boundaries, Moon exclusion, unknown-obstructor
reasons and fingerprint. It never reconstructs a segment from an aggregate.
Active/inactive/unqualified become obstructed/none/inputs_missing with the
producer's reasons. `not_applicable` is factor-only and never F2 inapplicability
or silence. The Moon reference resolves to this build's Moon longitude fact;
no L1 value is recomputed. PostgreSQL half-open range strings and the exact
ka_gochara_coverage_facts horizon shape (1155:361-382) are supported.
KA-3a's specified SkyCoverage JD arrays are checked through the shared type.

**(I) INTERPRETATION I4:** the universe is exported coverage requested spans
plus actual record supports, producer segments/gaps and F2/protection
endpoints; no fixed horizon, sample limit, guessed count or Cartesian roster.
Uncovered parts of a requested partition retain named unavailable rows.
Removed daily mechanisms emit no natal row. Badhaka without a served source
remains `source_not_served`; other mechanisms without evaluated producer
bindings remain `mechanism_evaluation_absent`. Scalar adverse testimony never
substitutes for that missing evaluation.

The five axes stay separate. Coverage/knowledge gaps outrank operational
states. Unresolved/deferred conclusions remain unavailable; contest outranks
full defeat, partial defeat and active. Protections keep the original adverse
conclusion and all consumed L1 ids. `source_assertion_id` identifies the
original F1 target, while output assertion ids hash candidate/record/interval;
protecting edges are never retargeted to a convenient alias. Active vedha
release uses its original producer endpoint, or a licensed protection onset;
otherwise release is unknown or an explicit conditional predicate. A later F2 cut
is never relabelled as the onset of a protection that already began; that
cell retains an unknown release and the original edge onset in provenance.

**(I) INTERPRETATION I5:** the existing public F2 boundaries reader rejects
inapplicable methods, so the adapter reads its pinned stored rows for exact
endpoints and calls period_context at every half-open cell. It copies actual
period ids, lords, parent lineage, bounds, method sources, build, convention,
explicitly pinned scenario and TWO_PASS_VERIFIED input tier. It never computes
periods. ClockUnavailable retains its exact reason on only the affected cell;
SQL/programming errors stop before replacement. Outputs retain their own
honest single verification tier, not the input tier.

## Remaining activation gates

Protected schema application/receipt; accepted KA-3a and judge callback wiring;
accepted scoped F1 protections/correspondence; real same-snapshot sealed 5.0
export with independent inventory and verifier execution pins; candidate
opening by the cockpit; independent exact-head V-K3b review and current K8
readings. Publication and v2 downstream serving admission stay with K9-4b.
No production operation is enabled here, and detector NONE remains
NO_DETECTOR in certification_mapping.json. Local tests and mutations establish
code behavior only, never a production PASS.

**(I) INTERPRETATION I6 — stale anchors:** plan_model.brief.spec names a
"PLAN §9 row K3", but the pinned relaunch plan's §9 is routing (line 563).
Use this item's explicit plan-model contract, packet and ALGO §3.4/§3.21,
not an invented row. K3-2's KA-3a spec_sources[2] hash is historical:
`080e196f...` resolves at commit `0f95e21af89ff25818e94a143cce3fcfe8177fad`;
the working base's packet hashes to `2686e1df...`. The pinned historical
packet's cited header/interval/SkyCoverage contract was recovered and read;
its fields agree with this consumer. The cockpit must reconcile/repin the
packet digest before live admission. No packet, plan, card or control-plane
file is changed by this job.

I2 continued: complete independent key arrays are verified before writing.
Each assertion retains the receipt, independent logical count, per-kind counts
and SHA-256 of the complete canonical key inventory, whose keys are also in
the full hash-bound export. This preserves an auditable commitment without
copying the global key arrays into every assertion (quadratic storage).
