---
artifact: ISSUED_FORECAST_LIFECYCLE_CONTRACT
version: "1.0"
status: IMPLEMENTED — fixture/rehearsal contract; protected production application and registrar cutover pending
item: K6-5a
authority: D-R11 / KYD-5; PLAN sections 8 and 12 R-11; ALGO section 3.8
produced_on: 2026-10-10
changelog:
  - "1.0 (2026-10-10): additive L5 issue/outcome storage, immutable retries, restrictive reference protection, legacy L4 compatibility oracles."
---

# Issued forecast lifecycle

L5 beside Samīkṣā owns delivered history and observed outcomes. L3 supplies the
registrar interface and the referenced Kāla manifest. This contract adds
`public.issued_forecast` and `public.issued_forecast_outcome`; it registers no
new asset. The existing `ka_bhavishya_lekha` writer and L4 protective read remain
active. K6-5b owns registrar integration and any later replacement of that read.

## Three identities

| Identity | Stored key | Meaning |
|---|---|---|
| Issue | `(issue_id uuid, version integer > 0)` | An immutable delivered statement; refinements append a new version. |
| Episode | `(chart_id, event_class, phase, affected_person, episode)` | The event identity used to cluster outcome credit across refinements and different issue ids. |
| Delivery | `delivery_channel`, `delivered_at` | Named delivery to the native, provided by the registrar after transport confirms delivery. |

An evaluated or generated candidate creates no issue by itself. This item has
no issuer, automatic candidate copy, backfill, delivery dispatcher or live
scoring path. The future registrar must receive actual delivery confirmation;
fixture channel names prove the storage contract, not delivery to a person.

## Exact issue columns

All columns must be supplied to `insert_immutable_checked` on insertion and
retry, including the explicitly nullable `probability_target`. No generated
column or server default adds a hidden field to its equality check.

| Columns | PostgreSQL type / invariant |
|---|---|
| `issue_id`, `version` | UUID and positive integer; composite primary key supports the existing `ON CONFLICT (issue_id, version)` helper. |
| `chart_id`, `generation` | UUID and text; composite `RESTRICT` FK to `kala_layer_candidate`'s actual manifest key. |
| `event_class`, `phase`, `affected_person`, `episode` | Nonblank text supplied from canonical event identity; no keyword inference or rank identity. |
| `issued_at`, `information_cutoff` | `timestamptz`; cutoff cannot be after issuance. |
| `delivered_at`, `delivery_channel` | Required timestamp and nonblank channel; delivery cannot be after issuance. |
| `delivered_statement` | Nonblank text, kept verbatim, including historically delivered uncalibrated claims in the statement. |
| `result_policy` | Nonblank manifest-selected policy identifier; no policy is inferred from a score. |
| `calibration_status` | `calibrated`, `uncalibrated` or `unqualified`; explicitly supplied qualification. |
| `intervals` | Nonempty `tstzmultirange`, preserving disconnected windows; finite half-open `[start,end)` intervals. PostgreSQL coalesces overlapping/adjacent windows without changing their covered instants. |
| `disclosed_grain` | Nonblank text; the registrar discloses the producer's resolution. |
| `point_functional` | Nonblank declared functional identifier, or explicit `none`; storage does not select a point or manufacture precision. |
| `probability_target` | Nullable numeric in `[0,1]`; nonnull only when calibrated and policy is not `all_null`. Calibration alone does not require a number. |
| `falsifier` | JSON object with nonblank string `ontology_locator` and `observation_predicate`; extra source-backed predicate parameters can remain in this object. |

The referenced manifest row cannot be deleted or have its identity rewritten
while an issue references it. The future registrar must pin the completed
manifest's actual qualification and source fields before delivery; this FK
establishes referential identity and does not certify producer qualification or
allow publication of an unverified candidate.

## Exact outcome columns

`issued_forecast_outcome` contains `outcome_id uuid` (primary key), `issue_id
uuid`, `version integer`, `observed_at timestamptz`, `recorded_at timestamptz`,
and a nonempty JSON object `observation`. Every field is required. The composite
FK `(issue_id, version)` references the exact delivered version with `ON DELETE
RESTRICT ON UPDATE RESTRICT`; there is no cascade and no nullable orphan path.
No success classification or probability is inferred from an observation.

Multiple observations and multiple issues can belong to one episode. An
evaluator joins outcomes to issues and clusters on the full episode key above,
never counts issues or versions as independent successes. For example two
versions for `(chart, career_change, fruition, native, career:1)` remain two
stored issues and yield one episode cluster. This item supplies the identity
and fixture oracle, not an evaluation score or a new outcome credit policy.

## Immutable operations and null discipline

The existing L3 interface is unchanged:

```python
insert_immutable_checked(conn, "issued_forecast", {"issue_id": issue_id, "version": version}, row)
```

It returns `True` for a new issue, `False` for a fully equal retry, and raises
`ImmutableIssueConflict` for any changed or omitted field on a reused key.
The caller owns commit/rollback. SQL triggers independently refuse `UPDATE`,
`DELETE` and `TRUNCATE` of either lifecycle table with SQLSTATE `55000`, including
unreferenced issues. A correction appends history; it never rewrites it.

No missing manifest, episode identity, delivery, predicate, functional or grain
is replaced with an invented value. Only `probability_target` is nullable.
An uncalibrated archived statement retains its exact words, with no new numeric
probability inferred from those words. This migration backfills no legacy rows
and changes none of the existing archived statements.

## Compatibility and protected application

Migration `1351_issued_forecast_lifecycle.sql` creates only the new lifecycle
tables, constraints, validation/immutability functions and triggers. It performs
no legacy row or schema mutation and changes no privileges. `migrate.ts` owns
each file's transaction; retrying unapplied DDL preserves the same tables and
history. Already-applied files retain their migration-ledger hash.

Rehearsal applied 1351 before the final explicit-infinity regression was added.
Its applied bytes are retained. Guard-numbered supplemental migration
`1352_issued_forecast_finite_intervals.sql` strengthens the new interval
validation function to reject PostgreSQL's explicit `infinity`/`-infinity`
timestamp endpoints as well as open unbounded ranges. It rewrites no row.
Both migrations travel in this item; the necessary follow-up is disclosed
despite the brief's original single-migration ownership entry.

Both files are `NEEDS-PROTECTED-WINDOW`. Both the routine runner and protected
deploy job now consume `platform/scripts/kala_protected_migrations.txt`; that
single list receives both filenames in this PR. The brief's former two inline
array sites have already been consolidated, so no runner or workflow source
change is necessary. The routine production runner skips the pending file;
the operator/conductor uses the existing Kāla protected window under the
campaign's production gates. No production application is performed by k4.

In particular `phala_anchors.bhavishya_id -> kala_bhavishya.id` and the existing
writer's protective query remain intact. A planted stale projection referenced
by L4 still makes that writer refuse before deletion. An L5 FK is not evidence
that every L4 reference has been migrated; removal awaits explicit registrar
cutover and downstream acceptance.

## Tests and implementation sequence

1. Pin the typed issue/outcome contract and show the lifecycle oracle failing
   on the unchanged dependency base (missing lifecycle migration).
2. Add the guard-numbered DDL and protected-list entry; exercise the real
   `insert_immutable_checked` helper against the shipped schema in an isolated
   PostgreSQL database.
3. Prove reference protection twice: normal immutable delete refusal, and
   the FK refusing a planted delete even with the row trigger removed locally.
4. Exercise changed/identical retries, refinements with clustered identity,
   mutation refusal, delivery/qualification/null/interval constraints,
   manifest and issue FK absence, and repeat-application preservation.
5. Run the unchanged L4 stale-reference, protected-matched-claim and lock-before-
   reference-preflight tests; run item precheck and apply the migration to
   `ky_k4`, then push a protected-window PR and hand it to PARĪKṢAKA.

The database oracles live in
`platform/python-sidecar/tests/l3/kala_db/issued_forecast/test_lifecycle.py`
and use the existing guarded throwaway-database fixture. The legacy oracles
remain in `tests/l3/test_bhavishya_p0_safety.py`. Required CI, independent review,
dependency completion, protected production application and post-deploy
readback remain the campaign's completion gates.
