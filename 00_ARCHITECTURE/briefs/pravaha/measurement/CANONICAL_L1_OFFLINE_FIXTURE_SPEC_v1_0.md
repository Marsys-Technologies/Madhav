---
artifact: CANONICAL_L1_OFFLINE_FIXTURE_SPEC
version: "1.0"
status: PREPARATION_ONLY — approved canonical bundle not supplied
produced_on: 2026-10-16
changelog: Initial J3C-BINDINGS offline rehearsal input contract.
---

# Canonical L1 offline rehearsal input

This specifies an input for the next measuring rehearsal; it does not certify the
existing AM5 test fixture. The rehearsal's synthetic/rounded facts and periods
cannot establish canonical L1 readiness. Root `CLAUDE.md:26` makes `chart_facts`
the L1 authority; `CLAUDE.md:119` prohibits re-deriving or replacing those values.
The current daśā reader consumes stored `chart_dashas` row identities and exact
ISO intervals (`platform/python-sidecar/services/gochara_kernel/dasha_read.py:237`).

## Bundle and independent approval

The cockpit supplies a previously authorized **offline export**, with no live
connection or credentials in this job. Required files are `charts.json`,
`chart_facts.json`, `chart_dashas.json`, `life_events.json`, `schema.sql`,
`grants.sql`, `manifest.json`, and `approval.json`. Each JSON table is an array of
complete stored rows, preserving types, row IDs, fact keys, values, precision,
ayanamsha identity, provenance/build references, timestamps and period bounds.
No rounding, synthetic replacement, chart re-computation or fallback data.
Only chart `482012f1-710e-4a25-994a-93821f5871aa` is included. The chart, facts and
dashas arrays are nonempty; life events may be empty under MB-1's explicit rule.

`manifest.json` uses `schema=ky.canonical_l1_snapshot/1`, `chart_id`,
`source=governed_offline_export`, `canonical=true`, `builder_role=data_plane_builder`,
`source_commit` (40 lowercase hex), timezone-qualified `captured_at`, and `files`.
The exact six-file inventory maps each filename to its byte `sha256` and integer
`bytes`. Hash the stored bytes, not reparsed/reserialized JSON. A duplicate JSON
field, symlink, missing file, empty chart/facts/dashas, duplicate row ID, foreign
chart, changed byte or inventory mismatch refuses validation.

`approval.json` uses `schema=ky.canonical_l1_snapshot_approval/1`,
`result=ACCEPTED`, `by` (independent v1/v2/v3/v4 lane), `manifest_sha256` (digest of
manifest bytes), `canonical_source_verified=true`, `schema_grants_verified=true`.
The approving lane must independently establish the export's governed origin,
raw-value and row-count equality to its existing authorized source evidence,
birth parameters, stable fact/dasha identities and their provenance references.
It must also qualify the following schema/grant fixture. A declaration by the
exporter or an invented approval is insufficient. Approval custody follows the
campaign's verifier-owned evidence directories; this validator checks the supplied
artifact, and does not authenticate its author or create approval authority.

## Deployment-faithful local fixture

`schema.sql` is the reviewed deployment schema, including the full migration
inventory, production-only digest-spec seeds and referenced authority relations;
it must not truncate migration 598 as `_runner_world.py:10` describes for its
minimal test fixture. `grants.sql` holds the corresponding reviewed grants for
`data_plane_builder`, verifier, and sealer, including PUBLIC revocations, ownership,
column grants, RLS, and function EXECUTE permissions. No passwords, connection
strings, role memberships or credentials are exported. Referenced upstream receipt
and registry rows required by these inputs must be supplied by the existing
suite's governed seed path, with stable IDs and independent parity readback;
a partial fixture is not deployment-faithful.

Restore is owned by the guarded suite, into its newly isolated database on
`127.0.0.1:55433`, never into an existing database. Do not execute these SQL files
merely because the byte validator passed: the independent schema/grant review
must precede the guarded fixture's restoration. The fixture creates/drops only
its own database and leaves the cluster configuration unchanged. Rehearse through
`SET ROLE data_plane_builder` with the exact production privileges; admin can
construct the fixture but cannot substitute for the measured build principal.

Before execution, compare the restored row IDs, counts and exact values against
the approved source, and read back migrations, grants, role identity and the
writer digest. Pin `SE_EPHE_PATH=/Users/Dev/kalayantra/ephe`; verify the corpus
manifest, use one worker, and route all temp/cache output under JOB_SCRATCH.
The offline bundle must retain its approval and manifest through teardown and
independent absence. The suite drops its own database in `finally`.

## Validation and limits

`python3 platform/scripts/gochara/canonical_l1_snapshot.py <offline-bundle>`
reads only local files, verifies the inventory/approval byte binding and row
identity envelopes, and emits `OFFLINE_BYTES_VALIDATED` with
`production_acceptance=false`. It never connects, exports, restores, executes
SQL, or recomputes L1. It cannot establish the source's truth, grant parity or
runtime readiness by itself. Synthetic transport fixtures in its unit tests are
explicitly not canonical data.

**(I) INTERPRETATION:** this job delivers the input specification and fail-closed
byte validator; the approved data and deployment-faithful restored fixture remain
external inputs. Alternative: treating the existing synthetic AM5 fixture as
canonical, which would contradict the rehearsal finding and §N.8.
