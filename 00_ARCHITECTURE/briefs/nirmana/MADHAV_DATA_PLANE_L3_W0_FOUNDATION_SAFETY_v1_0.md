---
artifact: MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY
version: "1.0"
status: FINAL_REVIEW_PENDING
observed_at: 2026-09-15T04:02:00+05:30
strategy_decision: DP-SD-017
strategy_content_commit: 793972c754b106688097dbc54536c1a9c270a793
approval_pin_commit: 04a9ab33effa23e5e9b4e89772330ae264498a9b
accepted_l2_terminal: e5307fadef42cca557a1c0ca3c1831b1296e22b4
packet: L3-W0-FOUNDATION-SAFETY-01
implementation_tip: 1f9cedbb0
active_identity_denominator: 22
protected_retired_identity: ka_gochara_sweep
production_builds: 0
production_mutations: 0
next_stage_hold: "L4 and L5 remain WAITING_FOR_STRATEGIC_BRIEF."
---

# L3 W0 foundation and safety record

## 1. Acceptance boundary

This is the final-review candidate for the first DP-SD-017 packet. W0 establishes
a safe, measurable source/local foundation. It does not establish physical L0-L2
generation availability, L3 data acceptance, protected integration, deployment,
consumer value or empirical performance. No production build, rebuild, database
mutation, migration application, campaign event, deployment, push, PR or merge
was performed in W0.

| Required W0 output | Evidence at candidate tip | Candidate disposition |
|---|---|---|
| authority, source, environment, campaign, ownership and holds | validated session-open; exact pins; protected/deployed/live recheck; verified lease | COMPLETE |
| exact denominator and first safe frontier | 22 active plus protected retired sweep; field/DAG/owner map | COMPLETE |
| Kshetra planning/recovery safety | execution-owned preparation, zero-DML planning and real savepoint crash/resume proof | INDEPENDENTLY ACCEPTED |
| Bhavishya empty/history safety | prevalidated replacement, stable protected identity/content and partition serialization | INDEPENDENTLY ACCEPTED |
| measured baseline and independent reference | Kshetra/transit measurements, DHARA decimal oracle, source-qualified Vedha case | INDEPENDENTLY ACCEPTED |
| generation/publication/recovery design | section 6 | COMPLETE AS DESIGN; physical schema/data remain held |
| consumer sentinels | L3-U05 requested/effective filter and fallback-state tests | INDEPENDENTLY ACCEPTED |
| exact next packets | section 8 | FROZEN |

W0 may be marked accepted only after an independent reviewer checks this complete
record and exact candidate tip. Green tests or the authoring agents' reports do
not self-certify the packet.

## 2. Pinned current truth

The detailed current-state evidence remains in
`MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md`. Its controlling
facts are:

- execution started from accepted L2 terminal `e5307fadef42cca557a1c0ca3c1831b1296e22b4`;
  that commit is not an ancestor of protected main;
- `origin/main` and the web deployed revision were
  `731e311f0b8f5f84db2f152b93951e1d3d50d89a`; sidecar/build and MCP revisions
  were different deployed artifacts and none was treated as L3 acceptance;
- frozen campaign `t3-2026-09-11-8b884eac` has 128 definitions and zero L3
  events; its L3 set is 22 active identities plus retired
  `ka_gochara_sweep`;
- the connected environment lacks `l1_data_plane_generation_heads` and
  `l2_data_plane_generation_heads`; the canonical chart has zero rows in six
  governed core L3 tables; 79 current MSR references are unmatched; and the
  estimated 10,966,448-row `kala_field` population is legacy capital, not an
  accepted generation or a rebuild warrant;
- coordination lease `MADHAV-DATA-PLANE-L3-W0-20260915` was pushed and read
  back at `origin/campaign-coordination@4d71762d332dbe4867bde5f9ec894fe62db1f4d4`;
  its W0 scope expressly excluded production data mutation;
- heartbeat `l3-k-la-execution-recovery` is active at a 15-minute cadence.
  A scheduled recovery wake has not occurred during this continuously active
  turn, so unattended continuity remains `PENDING_FIRST_SCHEDULED_WAKE`.

The frozen first physical row frontier, once accepted upstream data exists, is
`ka_gochara_resonance`, `ka_kota_chakra`, `ka_moorti_nirnaya`,
`ka_vedha_gochara`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`, `ka_yojaka`
and `ka_avadhi`. Service/pure qualification can separately cover
`ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva` and the Tulana kernel.
This is eligibility, not build authority.

## 3. Dependency, ownership and preservation fence

The source-derived register contains 81 declared dependency entries and 32
active-L3-to-active-L3 edges. The computational DAG and semantic/use graph remain
separate: false or unproved Avadhi-to-Taranga, Kalasutra-to-Darshana and overlay-
to-century relationships do not become build inputs merely because a registry
edge or intended use exists. Hidden service/SQL inputs must close before their
affected packet builds.

Shared output/control ownership is fenced as follows:

- Gochara v2 and century v3 share `kala_gochara_windows_v2`; protected sweep v1
  and century v3 share `kala_gochara_windows`; Gochara generations share build
  state. The sweep remains excluded from dispatch, replacement and generic
  deletion.
- Kshetra owns only `kala_insights.lel_derived=false`; `mi_bhara` owns true rows.
  Its fifteen-table internal graph has no database-enforced full DAG and must be
  replaced only by the accepted stage plan.
- the opt-in Taranga service and writer can target the same natural keys;
  registry and substep-progress rows are shared control surfaces. Each packet
  therefore names one writer and one transaction/publication owner.

Before any later replacement, the exact transitive `CASCADE`/`SET NULL` graph
and non-FK referrers in the current state record must be rechecked. In particular,
L2 MSR deletion reaches five core L3 tables; convergence and Bhavishya deletion
reach L4 references. This is a preservation fence, not authority to edit L4.

## 4. W0 safety corrections and consumer sentinels

### 4.1 Kshetra P0

Commits `d0e5ac9a5` and `2246ff4ac` move chart-wide replacement into the first
durable `prepare:replace` substep; stage planners and dry-run are read-only;
successful empty discovery still produces the preparation plan; discovery
failure is loud. The real substep driver/savepoint test proves failed plugin
output and its progress receipt roll back together while prior committed work
survives and resume skips only committed keys.

Root validation: `443 passed, 8 skipped, 2 xfailed` in the maintained Kshetra
suite. Independent re-review returned ACCEPT with no HIGH, MED or LOW finding;
its focused result was 27 passed and 53 deselected. No production rehearsal is
inferred.

### 4.2 Bhavishya P0

The correction lineage `17a03c6b8` -> `06f612406` -> `a3e518864` was challenged
twice before acceptance. The final behavior acquires a chart-scoped transaction
advisory lock before the read/plan/write window, rejects duplicate/ambiguous or
unattachable identities before DML, preserves unchanged protected rows and IDs,
and fails before DML when an outcome/notes-bearing or Phala-anchored claim would
change. Only unprotected changed rows update in place; only unrecorded,
unreferenced stale rows can be deleted. Insert/update/skip counts are distinct.

Root focused validation was 25 passed and one environment-gated PostgreSQL skip.
The implementation owner additionally reported 1,458 passed, 41 skipped and two
expected failures across the then-current L3 suite plus a real disposable
two-connection PostgreSQL lock proof. Independent exact-tip review accepted the
history, concurrency, normalization and accounting behavior. A populated real
Bhavishya/Phala rehearsal remains not run.

### 4.3 L3-U05 consumer qualification

Commit `f3966359e` is the accepted correction over initial `57ad321a9`. Requested
and effective filters remain distinct; Bhavishya fallback retains signal/domain
constraints; explicit ayanamsha or positive minimum-strength filters make an
otherwise lossy fallback incompatible. Receipts distinguish
`served_unqualified`, `searched_empty`, `source_empty`, `incompatible_filters`
and `db_failure`. A completed build is an observation only, never accepted-current,
and zero rows are never inferred to mean unbuilt.

Root validation passed 166 files with 30 skipped files and 1,541 tests with 172
skipped tests; TypeScript compilation passed. Independent review of exact
`f3966359e` returned ACCEPT with no HIGH/MED finding after a 129-pass/12-skip
focused run. These are source-local sentinels, not integrated or served value.

## 5. Measured baseline and reference contracts

The measurement host was Darwin 25.5.0 arm64, Apple M5 Pro, 64 GiB RAM, Python
3.14.6, NumPy 2.5.1 and pyswisseph 20230604.

Small Kshetra discovery workloads measured: stage-0/integrator 47 pass plus one
skip in 0.56 s; writer 61 pass plus one skip in 15.08 s; streaming loaders seven
pass in 0.20 s; publication/hash subset 27 pass with 56 deselected in 37.02 s.
The final maintained Kshetra run at the corrected P0 tip passed 443 with eight
skips and two expected failures in 88.17 s. These are local test workloads, not
production duration or optimization evidence.

The deterministic 30-day/five-aspect Saturn transit benchmark passed all seven
tests. Cache-bypassed wall time was 3.90 ms; cold cached was 2.14 ms with 124
hits/31 misses (1.82x); warm cached was 1.72 ms with 279 hits/31 misses (2.27x).
The multi-call fanout was 38.07 ms with 2,539 hits/177 misses (93.5%). Whole-test
process measurement was 0.21 s real, 0.16 s user, 0.03 s system and 49,119,232
bytes maximum RSS. Output is bit-identical across bypassed/cold/warm paths; no
general speedup promise is made.

The DHARA packet consists of independent Decimal-60/4,096-Simpson reference
`9210b8489`, production-path clock-step detector `542a934bb`, left-limit fix
`aea1671e4`, and semantic-identity correction `1f9cedbb0`. It proved that using
the clock knot's right limit at the preceding interval end changed a minimal
integral from 2.5 to 2.6164042561333445 (+4.656%). The corrected contract uses
the preceding interval's left limit, exact right-continuous value for the next
interval, and a terminal left limit. `DHARA_SWEEP_SEMANTIC_VERSION=1.2` enters
field `config_pin`, snapshot identity and resume fingerprint; resume version 9
rejects pre-correction checkpoints. The exact numerical/tolerance contract is
`MADHAV_DATA_PLANE_L3_DHARA_NUMERICAL_CONTRACT_v1_0.md`.
Independent exact-tip re-review passed all 44 focused tests and returned ACCEPT,
closing the earlier two MED and one LOW findings without a live-build claim.

The existing source-qualified ordinary reference is the BPHS Ch.29 Sun third-
from-Moon favourable transit and paired ninth-house Vedha case, with overlapping
and disjoint interval controls. Its two pure suites passed 42 tests. The cited
Phaladeepika Lattā cases remain separately scoped; the PG353 battle-only scale is
not generalized into ordinary transit probability or adversity. Sarvatobhadra's
current algorithmic approximation remains unqualified and cannot close a
source-qualified positive gate.

The final corrected broad L3 source suite passed 1,471 tests, skipped 41
environment-gated tests and retained two expected failures in 91.74 s; process
measurement was 92.06 s real, 89.64 s user, 1.80 s system and 619,577,344 bytes
maximum RSS. Unknown integration marks and unrelated deprecations remain warnings.

## 6. Immutable generation, publication and recovery design

1. Each material asset generation is content-addressed from the canonical asset
   contract and source digest, subject/purpose/context, exact transitive upstream
   generation/partition vector, complete output partition/substep plan and every
   semantic algorithm/config version. An empty partition is an explicit immutable
   result; absence of rows is never an implicit missing or successful generation.
2. A generation records immutable planned partitions, per-partition completion,
   row/key/content digests, coverage and limitations. `BUILDING`, complete
   `CANDIDATE`, independently `ACCEPTED` and selected/current are different
   states. Completed content and receipts are never relabelled or rewritten.
3. Candidate heads are separate from selected heads. Selection occurs only after
   every required partition and compatibility check passes. One atomic layer
   publication manifest may select retained immutable per-asset generations; a
   single global build ID or one long transaction is not required.
4. Corrections create a new generation, invalidate only actual dependent
   descendants/caches and preserve the old consumed generation. Rollback repoints
   the selected head/manifest to a still-compatible accepted generation; it does
   not mutate data or metadata to make an old-vector candidate current.
5. Kshetra's fifteen tables form one content-bound stage plan over
   `S0 + S2 -> S3 -> S1 -> S4 -> S5 -> S6 -> S6.5 -> S8 -> snapshot` with direct
   S0 also pinned into S4. Every stage consumes the exact vector, config and
   semantic version. Resume accepts only matching fingerprints and completed
   receipts. Replacement preserves prior snapshots and all non-owned insight
   rows; no complete head is selectable before all accepted classes/stages and
   substrate IDs are present.
6. Bhavishya's rebuildable projection cannot own or rewrite delivered/observed/
   Phala-anchored claim content. Until the W6 stable-generation schema exists,
   P0 deliberately fails closed on protected changes or stale protected rows.
   Empty candidates are explicit and never erase issued history.
7. Shared-output assets use one named writer and publication owner per packet,
   owner-qualified partitions and locks. Retired sweep content is outside every
   active generation and delete scope. L4/L5 references are protected referrers,
   not writable participants; Lane-E/`lel_derived=true` insight rows are excluded
   from Kshetra ownership.
8. Recovery starts from the execution ledger, current-state record, accepted
   manifest and exact next eligible packet. A changed dependency or semantic
   version rejects stale resume. At most two identical transient retries are
   allowed; a repeated deterministic fingerprint becomes one root-cause packet.
   The heartbeat never dispatches a second writer over an active lease.

This design is frozen by W0 but not yet physical schema. Its implementation must
reuse the accepted L1/L2 generation machinery where sufficient and must not
modify frozen WriterBase/orchestrator transaction ownership without a separate
architecture decision.

## 7. Migration and release integration truth

Protected main still stops at migration 1032. The open planner/Purna stack is:

- PR 2597 / `codex/planner-knowledge-inquiry`: `1033_planner_inquiry_lifecycle.sql`;
- stacked Purna Wave 1 onward: `1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql`.

The accepted data-plane lineage independently contains
`1033_data_plane_l1_producer_history.sql` and
`1034_data_plane_l2_producer_generations.sql`. The connected environment lacks
their head relations, so these data-plane migrations have not been treated as
applied there. Neither lineage may be merged unchanged into the other. The next
integration packet must refresh all tips and every authorized environment's
applied-migration ledger, then reserve two unused numbers in the live
`origin/campaign-coordination` claim table from a leased scratch worktree before
authoring. It must also reconcile the current files' legacy
`platform/migrations` location with the binding protocol's active
`platform/supabase/migrations` directory, update every source/test/evidence
reference coherently, prove content identity plus apply/reapply on disposable
PostgreSQL and obtain independent migration review. It must not rename, relocate
or edit an actually applied migration, widen the legacy collision baseline, or
assume an open PR's green CI means protected integration/deployment.

## 8. Exact next packets and holds

1. `L3-RI-01-PRECURSOR-GENERATION-INTEGRATION`: reconcile fresh main and the
   open planner/Purna migration namespace; verify applied identities, reserve
   the live coordination slots, and prepare a reviewable, compatible release of
   already accepted L0/L1/L2 source plus generation migrations in the active
   directory. No semantic reopening of those layers. Exit requires migration/
   security review, protected checks and exact deployed/source proof.
2. `L3-W1-UPSTREAM-GENERATIONS-01`: only after the precursor release is accepted
   and deployed, reacquire the exact production lease, verify environment/
   identity, backup/restore/canary and materialize/select L0 -> L1 -> L2 in the
   actual DAG. Verify every contributing producer partition and rich field;
   source acceptance or legacy rows are insufficient.
3. `L3-W2-FIRST-FRONTIER-SOURCE-01`: source/service packets for resonance,
   Moorti/Kota/Vedha/Tithi/Sudarshana, Yojaka, Avadhi and the four service/pure
   identities may be prepared against immutable fixture contracts while W1 is
   held. Candidate data acceptance and descendant unlock remain blocked on W1's
   accepted physical vector.
4. `L3-W6-BHAVISHYA-STABLE-GENERATION-01` and
   `L3-W7-KSHETRA-COHERENT-PUBLICATION-01` remain named later packets. P0 does
   not substitute for stable issued identity or immutable fifteen-table
   publication.

No full-chart rebuild is authorized by W0. Century v3 retains its separate hold.
L4/L5 elevation and empirical outcome evaluation remain out of scope and
`WAITING_FOR_STRATEGIC_BRIEF`.
