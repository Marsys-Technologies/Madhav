---
artifact: J7_PREBUILD
version: "1.0"
status: PREPARED — built, waiting on gate; no phase-12 acceptance
produced_on: 2026-10-16
changelog: "1.0: candidate-only Sudarshana method, local proof entry points, and explicit dispositions for all eight assigned items."
---

# J7 preparation

This packet prepares J-7's candidate method. It does not admit a method into sealed
Gochara `5.0`, retire a writer, apply a migration, issue a decision, or produce an
independent acceptance receipt. The campaign's phase order remains in
`KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:109`; the optional J-7 decision gate is at
`:220`. Amendment A6 D-40 authorizes preparation, not operational completion.

## Candidate entry point

`services/kala_core/overlays/contested_reader.py:40` exposes
`load_sudarshana_method(conn, *, chart_id, generation, ayanamsha_id, year, evidence)`.
The connection is caller-owned and the generation is explicit; this path never
resolves a published head. It loads the existing conclusion-free KA-3b envelope,
checks its fingerprint, constructs nested F2 period rows, and evaluates twelve
bhavas for each applicable annual frame. A local test invokes it inside a real
PostgreSQL read-only transaction after the registered writer stores the adapter.

`evidence` is an explicit `F1Snapshot` at the period's commencement, containing
all twelve sign records and cited F1 occupant/aspect/lord assessments. The caller
supplies completeness of occupancy and aspects, effective nature, comparable
strength and their operand references. The DB reader resolves all cited operands
against the pinned chart/build/ayanamsha. F1 remains responsible for its derived
nature/condition assessment; this method does not manufacture a new F1 producer,
compute nature from a planet-name default, or claim these inputs were admitted.
Exaltation and Saptavarga qualifications remain upstream assessments (BPHS 74.7–9,
15–16, local OCR `00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol2_rsanthanam_djvu.txt:43293`).
Missing evidence produces a per-house null and partial coverage. A nested period
can be judged by `judge_period(period, evidence)` only with its own commencement
snapshot; an annual snapshot never certifies later month/day commencements.

The rule source is `../l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md:348`:
three frames, any coincident pair judged from the birth chart, nested annual
periods, commencement conditions, declared year anchor, and no agreement flag.
Count ties use referenced strength; equal strength gives mixed results.
Commencement conditions retain their separate reasons, including conflicting
conditions, rather than becoming an aggregate score. Results remain
`method_contested` testimony, with `value = null` and `admission = candidate_only`.

## Interpretations requiring independent review

- **(I) INTERPRETATION — read-time method output.** F2 rows and conclusions are
  returned by the candidate reader, not stored in KA-3b's adapter payload.
  Migration `1384_ka_3b_contested_candidates.sql:140` expressly forbids a stored
  Sudarshana conclusion. Alternative: a separately allocated, reviewed migration
  for durable method-result storage. No migration is needed for this read path.
- **(I) INTERPRETATION — nested duration convention.** Fit the text's nominal
  360-day year, 30-day month, 2.5 days and 12.5 ghatika proportionally into the
  adapter's declared civil-birthday interval. Every child partitions its parent
  exactly; each row states the nominal duration and scaling convention.
  Alternative: fixed elapsed nominal periods, with an explicitly unassigned
  remainder or a different annual anchor. A solar return is not claimed.
- **(I) INTERPRETATION — occupation/aspect precedence.** BPHS 74.11–14 is read as
  occupants first, aspects when unoccupied, lord when neither is present
  (`00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol2_rsanthanam_djvu.txt:43329`). Alternative: combine occupants and
  aspecting grahas into one counted set. All twelve houses are retained.
- **(I) INTERPRETATION — strength reduction.** Compare sums of like-unit F1
  strength values when benefic/malefic counts tie. The output names the reduction
  and cites its facts. Alternative: strongest individual or another explicitly
  sourced reduction. Missing or incomparable strengths remain null.
- **(I) INTERPRETATION — legacy compatibility.** The removed convergence flag is
  absent from every new candidate method/F2 output. The published legacy writer,
  schema and tests retain their existing flag pending a separate retirement.
  Alternative: remove the published column/contract, requiring an allocated
  migration and compatibility approval. The plan keeps the adapter table
  (`KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:341`).

## Per-item disposition and landing work

| Item | Preparation outcome | Still required |
|---|---|---|
| J-7 | Built candidate method and F2 rows; not admitted | Exact-head independent review, D-T2 effective admission, original K1-1b/KA-3b and residual dependencies. Real F1 commencement snapshots are an input, not a fabricated completion signal. |
| J-7-a63 | Left out: operational/evidence residual | Independent A6.1 and D-T2 evidence; admitted annual Tajaka identities, eclipse/station relations and their phase-12 readback. Pravaha plan A6.3 is infrastructure, not retirement (`PRAVAHA_CAMPAIGN_PLAN_v1_0.md:157`). |
| J-7-b61 | Left out: doctrine/review residual | Effective path-by-path D-T2 admission, J2 evidence, actual doctrine specifications and independent reviews. B6.1 names Jaimini, transit-to-transit, star-limb/sign-third and SBC (`:188`); this packet does not substitute Sudarshana tests for them. |
| J-7-n-t2 | Left out: decision residual | Governed effective approved/refused outcome and original dependencies. `DECISIONS_SURROGATE.jsonl:39` is PRE-D-T2 conditional approval, expressly requiring the cockpit to record the outcome when evidence exists. No outcome is authored here. |
| J-7a | Left out: contract-phase retirement | Flip/live-reader acceptance and soak (J-6l/V-J6), reviewed registry/seed lifecycle changes, actual grep and served-response compatibility evidence; preserve all registry rows and the plan's `_v2`/`2.0` disposition (`KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:327`). |
| J-7a-pr3099 | Left out: **needs migration number** | No J7 allocation in `/Users/Dev/kalayantra/run/MIGRATION_ALLOCATION.json:6`. Re-cut inherited 1303 only after allocation and preserve flip/soak/retirement gates. Rerun its oracles on the guarded local fixture and prove each mutation, then obtain independent per-child review/CI receipts and deployed-source/readback evidence. |
| J-7a-a62 | Left out: operational/evidence residual | Actual century-writer retirement, registry/seed alignment and Disclosure 3 closure after soak; independently accepted retirement readback bound to the same operation/request. Pravaha A6.2 waits on A6.1 (`PRAVAHA_CAMPAIGN_PLAN_v1_0.md:156`). |
| J-7b-b62 | Left out: handoff/readback residual | An authoritative L5 handoff naming the fields and a sealed-generation field readback; independently accepted digest-bound evidence and original L5/flip dependencies (`PRAVAHA_CAMPAIGN_PLAN_v1_0.md:189`). No sealed-field presence is inferred from code. |

The Pravaha plan references above refer to the specified source at
`/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/PRAVAHA_CAMPAIGN_PLAN_v1_0.md`.
Runtime evidence destinations in the job prompt are read-only to this builder.
No placeholder file is written to a detector's evidence path.

PR #3099 was inspected from the existing read-only ref
`origin/pravaha/c40-revoke-orchestrator-gochara-rest`, head
`6215cf782401153e9b069b9306562bb2f9f1ab35`. No fetch/commit/push was run under the
job's prohibition on Git writes. Its historical tests start and stop their own
PostgreSQL clusters (`test_migration_1303_revoke_orchestrator_gochara_rest.py:115`),
which is incompatible with this job's required existing-cluster fixture. They
were inspected, not executed; historical SUCCESS is not renewed evidence.

## Local verification and review handoff

Run from `platform/python-sidecar` with `PYTHONDONTWRITEBYTECODE=1`,
`SE_EPHE_PATH=/Users/Dev/kalayantra/ephe`, `KALA_REQUIRE_DB=1` and
`KALA_ADMIN_DSN=postgresql://postgres@127.0.0.1:55433/postgres`:

```sh
python3 -m pytest tests/l3/kala_db/ka_adapters tests/l3/kala_db/ka_sudarshana_varsha tests/l3/ka_sudarshana_varsha tests/l3/test_ka_sudarshana_varsha.py tests/l3/test_ka_sudarshana_varsha_writer.py tests/l3/ka_adapters tests/l3/kala_core/clocks -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest-j7"
python3 -m pipeline.orchestrator.provenance_inventory --check
```

Tests are discovered by the existing `tests/` sidecar shard selection and the
`tests/l3/kala_db` dedicated required DB job (`.github/workflows/ci.yml:369,2438`).
No explicit CI path was added. The local adapter compatibility suites must be
collected together in normal directory order: with the new DB directory first,
pytest reports the inherited adapter fixture's `kala_db_dsn` missing; collecting
the inherited DB directory first passes. This is recorded, not hidden as green.
Generated writer hashes and the census input fingerprint were regenerated.

The job folder contains fixed/reverted source copies, test logs and a structured
mutation manifest; every listed semantic reversal fails its test on the copy
and passes on the fixed copy. These are builder verification, not an independent
review or campaign acceptance. The cockpit retains the worktree and job evidence
for its commit/review process; fixture databases and temporary test paths are
cleaned up without stopping or reconfiguring the provided cluster.
