---
artifact: J3_MEASURING_PREBUILD
version: "1.0"
status: BUILT_WAITING_ON_GATE
date: 2026-10-16
scope: J-3a-b44, J-3d-a54, J-3d-a55 preparation only (A6 D-40)
source_base: a3ccc8ade9715ad02d69add40071f29cf29687df
---

# J3 measuring preparation

This packet adds an independent stored-column golden exporter and a draft
report for the measuring contract's MB-3/MB-7
(`decisions/MEASURING_BUILD_CONTRACT_v1_0.md:82`, `:84`, `:110`). It neither dispatches a build
nor supplies a residual, acceptance receipt, deployment, teardown, publication
or inherited-prerequisite completion. Production steps below are prepared,
not executed. The twelve-phase sequence and all original dependencies remain.

## Item dispositions

| Item | Preparation | Still required at its declared phase |
|---|---|---|
| J-3a-b44 | **Left out.** No 4.1 baseline is fabricated. | Historical 4.1 build/extract, accepted protocol and score receipts, independently bound to B4.2, A2.6 and B4.6; original detector file and digest, or explicit delegated disposition. |
| J-3d-a54 | Golden export and read-only/local rehearsal built. | Original ten projection/overlay obligations, actual candidate capture, golden commit in sitting log, and independent `golden_capture_accepted` receipt after J-0m/J-3c. |
| J-3d-a55 | Draft report, named missing-evidence checks and executable rehearsal tests built. | Full inherited oracle battery with literal fixtures/mutations, independent K3/O-2 review, real report/readback, terminal execution, guarded teardown, and independent absence acceptance after J-0m/J-3c. |

**(I) INTERPRETATION — preparation boundary.** The supplied packet explicitly
cites capture/report/teardown prerequisites for A5.4/A5.5; this pre-build
supplies those missing tools without repeating or certifying the original
repairs. Alternative: treat a tooling merge as the original repairs or event
completion. That would contradict the packet's evidence-only detectors and
earned-signal rule. Existing repair code and other lanes' in-flight files
are untouched. PR #3194's ordinary-golden review remains J-3c scope.

**(I) INTERPRETATION — B4.4.** Keep it left out until historical evidence or an
explicit disposition is supplied. Alternative: relabel a 5.0 measuring golden
as the 4.1 scored baseline. Surrogate answer 17 Q6 explicitly excludes that
substitution. The detector path in `00_ARCHITECTURE/control/pravaha/plan_model.json:1191` B4.4
(`/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/BASELINE_4_1_v1_0.md`)
was absent at this job's local read. This is not an exhaustive archive search
and not a historical-closure or supersession decision.

## Export and comparison contract

`platform/python-sidecar/services/gochara_kernel/measuring_capture.py` imports
no builder rules. `read_candidate` requires the caller's transaction to be
READ ONLY with REPEATABLE READ or SERIALIZABLE isolation **before any
candidate query**. It requires an unsealed, non-authoritative candidate
marked `test_slice/all_classes_full`, the marker schema/64-hex digest syntax,
all 26 classes and the ruled horizon. This is stamp syntax, not the steward's
digest proof. Every candidate read pins chart and generation. A stored basis
is preserved verbatim; its schema/meaning is not reinterpreted or re-derived.
Main's outcome-free `ruled_horizon` basis under `horizon_basis/1` remains usable
(`services/gochara_kernel/horizon.py:166`); verifier B owns its
acceptance and the separate log/horizon readback. At this base,
`services/gochara_kernel/measuring_report.py:331` still accepts the legacy
`ruling7+ruling13` basis rule, while `horizon.py:167` emits
`ruled_scope+birth_centenary`. J-3b must reconcile independent acceptance
before a real measuring event. This packet does not change that other lane.

The export contains exactly the six MB-3.4 files and `MANIFEST.sha256`:

| File | Content |
|---|---|
| `contacts.jsonl` | Contact id, physical obligation, bounds/exact instant and angular tolerance from stored rows. |
| `records.jsonl` | Independent canonical gkey/hash, stored id, admission, operator role, and support intervals. Ordered prerequisites come from the stored prerequisite rows. |
| `windows.jsonl` | Stored class/path/rule/bounds. |
| `horizon_basis.json` | Manifest's basis, without consulting or modifying life events. |
| `stretch_sink.jsonl` | Supplied same-run exported sink records, preserved as observations. No recount or sink validation is claimed. |
| `digests.json` | Per class/path sorted-key **and payload** digests, per physical-obligation contact digests, windows digest, source/run/manifest binding and informational input vector. |

The gkey omits chart and generation, reconstructs the stored frame, and
includes P1 anchors iff present. This follows `services/gochara_kernel/evaluator.py:137`'s natural-key
definition without importing it. Real migration tests compare it against
stored ids, seed a second stored generation, compare their generation-free
digests, and prove its row ids differ. The same fixture checks generation
isolation of contacts, records and windows. Payload
digests additionally bind admission, role and supports: moving support by one
second must change the class/path digest, even though the gkey does not.
Multiplicity is preserved. Timestamps are UTC, not database-session strings.
Empty, unbounded or non-half-open stored support ranges refuse rather than flatten.

Exports create a new directory; they never overwrite an existing capture.
The manifest is written last. Verification checks the exact file set, every
SHA-256, canonical manifest order and duplicate/malformed entries, and refuses
symlinks. A digest proves byte integrity, never semantic or independent
acceptance. Source commit and run id are operator declarations; both exports
and reports leave source attestation and independent acceptance null.

## Prepared capture procedure — not executed against production

First satisfy MB-8 and the campaign's production gates: exact reviewed head
and CI, deployed same image, pinned ephemeris, protected window, live lease,
backup/restore and dry-run receipts, small-test timing projection, teardown
role and terminal-run readback. No code in this packet grants those powers.
The separate J-3c job owns dispatch preparation.

In an independently authorised, read-only capture environment, supply the
real run id, verified deployed source SHA, approved DSN, a same-day exported
sink JSONL, and a new output directory. Do not print credentials. From
`platform/python-sidecar`, the callable is:

```python
import json
import os
from pathlib import Path
import psycopg
from services.gochara_kernel.measuring_capture import read_candidate, write_bundle

sink = [json.loads(line) for line in Path(os.environ["MEASURING_SINK_FILE"]).read_text().splitlines()]
with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        export = read_candidate(
            conn, chart_id="482012f1-710e-4a25-994a-93821f5871aa", generation="5.0",
            run_id=os.environ["MEASURING_RUN_ID"],
            source_commit=os.environ["MEASURING_SOURCE_COMMIT"], stretch_sink=sink)
write_bundle(os.environ["MEASURING_GOLDEN_DIR"], export)
```

An active transaction is checked in addition to session settings; autocommit
with read-only/repeatable defaults does not qualify. The snapshot is held for the reads only; the connection/transaction belong to
the caller. Capture twice on the unchanged candidate and compare all bytes.
Rehash offline:

```sh
python3 -B -m services.gochara_kernel.measuring_delivery verify --golden "$MEASURING_GOLDEN_DIR"
```

Have verifier B inspect the stored rows, perform Group-I recount and Group-R
checks, and bind all raw observations to the **same** export digest and
chart/generation/run/manifest/source binding. Then commit `digests.json`,
`MANIFEST.sha256`, and `horizon_basis.json` at the contract's measurement
fixture path and record the actual commit in the sitting log. The full
export must remain available. A successful offline rehash is not the
independent `golden_capture_accepted` receipt.

## Draft report inputs and use

`measuring_delivery.build_report` verifies the entire export before consuming
it. Its observations JSON must carry `binding` exactly as in `digests.json`
and `golden_manifest_sha256` exactly as in the verified receipt. Required
sections are `timings` (run/asset seconds, `by_phase`, `by_class_substep`),
`runtime` (raw MB-4.7 states and final index/total, with the 298-step full plan required), `row_counts` (including
the three captured core tables), `sink_recount`, `horizon_readback`,
`teardown`, `acceptance`, and `golden_commit`. The executable test fixture
`tests/l3/kala_db/test_j3_measuring_delivery.py::golden` shows the exact
shape, deliberately using **unearned** review/teardown/commit values.

The report computes both share grids, P4's instant intersection, lengths,
per-agent contributions, the eight-class path census, export hashes and
bereavement's labelled 2.61% comparison. It excludes testimony from scored
shares and refuses admitted scored rows whose rule version is not bound by
the protocol. Missing numbered observations, incorrect denominators/calendars,
incorrect ratios, missing scope/60-second limits, failed runtime, missing
golden commit, unexecuted teardown and missing review remain explicit
refusals. No field says the emitter independently accepted the build.

```sh
python3 -B -m services.gochara_kernel.measuring_delivery report \
  --golden "$MEASURING_GOLDEN_DIR" \
  --observations "$MEASURING_OBSERVATIONS_FILE" \
  --output "$MEASURING_REPORT_FILE"
```

Exit 0 means a **draft file was written**, including any refusals; exit 2
means input/export/IO refusal, including overwrite. Every report has
`DRAFT_AWAITING_INDEPENDENT_ACCEPTANCE` and null independent acceptance.
Observations/review pointers are reported, not authenticated by this tool.
The report does not implement ephemeris recount, 4.1 scoring, runtime
attestation, independent review or teardown. All MB-5.5 limitations and the
shared-reconstruction/60-second limit are carried in it.

## Teardown and independent absence — not executed

After the capture commit is in the sitting log, apply MB-4.5: actual Cloud
Run execution terminal and no later substep event. A released advisory lock
does not establish thread exit. Use the existing reviewed
`platform/scripts/teardown_v5_small_test_job.py` through its governed executor
path: same-operation rollback-confirmed dry run, then explicitly authorised
execution, then a **separate independent absence readback**. Its
`COMMITTED_AWAITING_ABSENCE` state is not acceptance. Preserve protected
window, ownership/grant, candidate-only and global-substrate controls.
This packet changes neither script nor those controls. The controller alone
can write the digest-bound phase-5 step/residual receipts after independent
acceptance and every original dependency; no fixture or draft report goes
to those paths.

## Local verification and CI

The two new suites are under `tests/l3/kala_db/`, already discovered by
`.github/workflows/ci.yml:369`'s `kala-db-tests` directory selection. No explicit CI path list,
aggregate or digest lock needs modification. The integration test uses
the existing guarded `isolated_kala_db_dsn` lifecycle, the actual AM5
migration chain, existing literal L1 fixtures, and the pinned Swiss corpus.
It builds bounded ordinary output, then seeds a measuring marker/basis for
exporter tests. That controlled seed is not a successful full measuring run.
The fixture also applies the existing 527 authority and 1236 refusal migrations
inside that isolated database; it drops the database and closes all its connections.

```sh
mkdir -p "${JOB_SCRATCH:?required}/tmp"
KALA_REQUIRE_DB=1 \
KALA_ADMIN_DSN=postgresql://postgres@127.0.0.1:55433/postgres \
SE_EPHE_PATH=/Users/Dev/kalayantra/ephe \
TMPDIR="${JOB_SCRATCH:?required}/tmp" PYTHONDONTWRITEBYTECODE=1 \
python3 -B -m pytest tests/l3/kala_db/test_j3_measuring_capture.py \
  tests/l3/kala_db/test_j3_measuring_delivery.py \
  -q -p no:cacheprovider --basetemp="${JOB_SCRATCH:?required}/pytest-j3"
```

Scope extensions: only the two new services, their two discovery-covered
test modules, and this runbook. No migrations, writers, FROZEN files,
L0–L2 assets, residual paths, fleet controllers, activation, or publication
state are changed. Final test commands, failing mutations/revert copies and
local verification limits are recorded in the job result. The selected inherited
measuring/projection/oracle battery returned 495 passed and 16 expected failures
on this preparation head; their names/reasons remain in the job evidence. Those
known gaps are not closed by the new exporter or report, and no full A5.5 oracle
closure is asserted. Independent K3/O-2 review remains a landing prerequisite.
