---
artifact: CANONICAL_L1_OFFLINE_FIXTURE_SPEC
version: "1.1"
status: PREPARATION_ONLY — no canonical bundle inspected by this job
produced_on: 2026-10-16
changelog:
  - "1.1 (2026-10-16): madhav-6d ruling — profiles excluded, transactional replica-mode row load, exhaustive post-restore FK audit, exact schema/grants coverage and exclusion provenance."
  - "1.0 (2026-10-16): Initial J3C-BINDINGS offline rehearsal input contract."
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
**`public.profiles` is never exported.** Its parent rows contain personal data
outside the four-table rehearsal scope; the madhav-6d ruling (2026-10-16)
excludes them. Preserve `charts.client_id` exactly as approved, including a
reference to an excluded parent. Do not fabricate a profile, null the key,
rewrite an ID, or copy personal parent data to make the FK resolve.

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
column grants, RLS, and function EXECUTE permissions. It covers **exactly the
objects that `schema.sql` creates**, with neither grants for absent objects nor
silent omissions of restored objects. The independently reviewed
`grants_origin.json` records `excluded_relations` and `excluded_objects`, with
the identity and reason for every exclusion from the source export's grant
surface. Excluded objects are not restored merely to satisfy source grants;
the reviewer reconciles the created-object inventory, grant targets and both
exclusion lists. Excluding profile **rows** does not itself exclude a schema
object or excuse missing grants on an object that `schema.sql` creates. A
schema-only parent definition may retain the FK without exporting its rows.
No passwords, connection
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

### Row restore and session boundary (madhav-6d)

After independently qualified schema/grants and governed seed restoration,
load `charts.json`, `chart_facts.json`, `chart_dashas.json` and `life_events.json`
into the throwaway database inside **one transaction**. Check that the load
session starts at `session_replication_role = origin`, then run
`SET LOCAL session_replication_role = replica` inside that transaction. FK
triggers do not fire **for the row load only**. Insert the four approved row
arrays without altering or inventing a row; keep the input file bytes exactly
as approved and compare their manifest digests before and after restoration.
Do not reserialize them to produce replacement bundle bytes. A load failure
rolls back all four tables' inserts together.

Commit that transaction, then assert `SHOW session_replication_role` returns
`origin` on the **same load session** before running any other rehearsal step.
`SET LOCAL` also unwinds on rollback. Do not use a session-wide `SET`, disable
constraints permanently, or run measured build operations while in replica mode.
The admin's load privilege is not the measured builder's privilege.

### Mandatory post-restore FK audit

Before permitting the rehearsal, call
`audit_foreign_keys(throwaway_dsn)` from
`platform/scripts/gochara/canonical_l1_snapshot.py`. The guarded suite supplies
the DSN of its own newly created database on `127.0.0.1:55433` (CI's guarded
loopback service may use port 5432); the inspector never creates, drops or
repairs a database. It uses a read-only, repeatable-read transaction, checks
its own session is at `origin`, and refuses incomplete restored-table inventory,
hidden RLS rows, unsupported FK forms, connection/query errors and timeouts.
A fresh audit connection does not replace the load-session `origin` check above.

The audit enumerates **every FK touching any restored table** through
`pg_catalog.pg_constraint`: incoming and outgoing edges, including edges to
governed seed tables, self-references, composite keys and `NOT VALID` constraints.
It measures actual dangling rows, using the FK's equality operators and
`MATCH SIMPLE` / `MATCH FULL` NULL semantics; re-enabling triggers alone does
not validate rows inserted under replica mode. Any unresolved reference other
than the exact single-column edge
`public.charts(client_id) → public.profiles(id)` fails closed.
Constraint names are not an allowlist: both relation and column identities
must match that edge exactly. Record it with this exact reason:

> intentional: parent personal data excluded by ruling (madhav-6d 2026-10-16)

**(I) INTERPRETATION:** the allowed edge is classified
`intentional_exclusion`, with `unresolved_rows=null`. Its resolution is not
probed: reading profile rows just to count missing parents would violate the
ruling. It passes whether the excluded parent happens to resolve or dangles;
all other FK counts must be zero. Alternative: probe `public.profiles` for a
numeric count, which violates the no-read scope and §N.7.6's honest-null rule.
Any other FK requiring a profiles read is reported as `profiles_scope_defect`,
without querying that table.

The returned `ky.canonical_l1_fk_audit/1` verdict includes `passed`, `status`
(`FK_AUDIT_PASSED` or `FK_AUDIT_FAILED`), a `constraints` inventory with relation/
column identities, classification and unresolved-row count, and `errors`.
The suite must require `passed is True`, retain the verdict through independent
review/teardown, and refuse to continue on failure. No row values are emitted;
`production_acceptance` remains false. A pass proves the FK condition only.

**If any rehearsal step reads `public.profiles`, report a scope defect.**
Do not satisfy such a dependency by exporting, seeding, synthesizing or granting
access to personal parent rows. A need for profiles is not canonical-fixture
readiness, even if every other check passes.

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
SQL, or recomputes L1. The separate `audit_foreign_keys(dsn)` API connects only
when explicitly called after restore; the byte-validation CLI never invokes it.
Neither can establish the source's truth, grant parity or runtime readiness by
itself. Synthetic transport fixtures in their tests are explicitly not canonical
data.

**(I) INTERPRETATION:** `grants_origin.json` is separately reviewed provenance
whose bytes are bound in the independent schema/grant review evidence. It is
required for that review, but is not a seventh member of the unchanged v1
manifest inventory. The byte validator does not inspect or certify its content;
the reviewer must check its binding and reconcile its exclusions before restore.
Alternative: change the byte-validator inventory/schema, contrary to this
ruling's requirement to keep its behavior unchanged otherwise.

**(I) INTERPRETATION:** restoration remains owned by the guarded rehearsal suite;
this preparation delivers its contract and reusable FK inspector, without adding
a loader to the offline byte CLI. The approved data and deployment-faithful
restored fixture remain external inputs. Alternative: add a loader to the CLI,
changing its offline-only boundary. Treating synthetic AM5 fixtures as canonical
would still contradict the rehearsal finding and §N.8.
