---
artifact: MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION
version: "1.0"
status: RI02_AUTHORIZED_UNBLOCK_ACTIVE
observed_at: 2026-09-15T11:55:00+05:30
strategy_decision: DP-SD-017_PLUS_DP-SD-018
strategy_content_commit: 793972c754b106688097dbc54536c1a9c270a793
approval_pin_commit: 04a9ab33effa23e5e9b4e89772330ae264498a9b
accepted_l2_terminal: e5307fadef42cca557a1c0ca3c1831b1296e22b4
active_identity_denominator: 22
protected_retired_identity: ka_gochara_sweep
active_packet: L3-RI-02-AUTHORIZED-UNBLOCK
implementation_tip: 47131772b355ae2c67b1f6fb2b90e9fa007e2202
w2_reviewed_tip: 47131772b355ae2c67b1f6fb2b90e9fa007e2202
ri01_reviewed_tip: 6a7ecc17117163debcc4b742aa183f17588ef621
w0_accepted_source_tip: 00a161195
coordination_lease: MADHAV-DATA-PLANE-L3-RI02-20260915
heartbeat_id: l3-k-la-execution-recovery
next_stage_hold: "L4 and L5 remain WAITING_FOR_STRATEGIC_BRIEF."
---

# L3 Kāla current state and disposition

## 1. Authority and execution position

`DP-SD-017` and its immutable content/approval pins authorize this existing
Execution — Data Plane task to execute the L3 strategy. The accepted L2 terminal
is the clean local base. It is deliberately not represented as protected-main or
deployed state: `git merge-base --is-ancestor e5307fade origin/main` returned 1.

The nine accepted upstream bindings were re-resolved from the pinned brief:

| Contract | Exact blob |
|---|---|
| Foundation contract and gates | `2fda304d627183b380e36ee1e817e08a8391119c` |
| Layer execution brief contract | `2ea6becdcff6232921bb3ad1521db2ecfc01f3a7` |
| Asset/interface brief contract | `71ff974ec92d03dbe755a53cd1d1f6b189543f07` |
| L1 condition/relation/clock contract | `99953b54749a794efee48760d718e387bc8743e2` |
| L2 producer-ready acceptance | `543a48354d31f76a8a7b7e932003f078055a7c33` |
| L2 proposition/relation contract | `0cc75ffcf1e3a018265a3efed6cd8b666388f586` |
| L2 mechanism/contradiction/investigator contract | `3ffcfd00275f1be3f9dd7238dfe00cc1b5e07b34` |
| L2 resource/mechanism slice | `4a3245cc5c8a4d4bceefb54886e853904882e7ce` |
| L2 compatibility/correction/rollback | `cd56f0112c8ffb812a67b73e7fd4a7d5e92df680` |

The governed session-open handshake is
`verification_artifacts/madhav_data_plane_l3_session_open.yaml`; schema validation
returned exit 0 with zero violations. The live coordination row was pushed and
read back at `origin/campaign-coordination@4d71762d332dbe4867bde5f9ec894fe62db1f4d4`.

## 2. Exact denominator and protected history

The frozen current campaign definition `t3-2026-09-11-8b884eac` contains 128
assets: L0 40, L1 19, L2 22, L3 23, L4 9 and L5 15. Its L3 denominator is exactly
22 active identities plus one inactive `RETIRED` / `RETAINED_AS_CAPITAL`
`ka_gochara_sweep`. The live public registry matches that 23-row set.

Active identities:

`ka_avadhi`, `ka_bhavishya_lekha`, `ka_dasha_kala`, `ka_gochara`,
`ka_gochara_resonance`, `ka_gochara_v3_century_materialize`,
`ka_graha_sancara`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`,
`ka_kota_chakra`, `ka_kshetra`, `ka_moorti_nirnaya`, `ka_muhurta_seva`,
`ka_sangam`, `ka_sudarshana_varsha`, `ka_taranga`, `ka_tithi_pravesha`,
`ka_tulana`, `ka_vedha_gochara`, `ka_vighnakara`, `ka_yojaka`.

The retired sweep is excluded from dispatch, implementation changes, retained
corpus replacement and generic deletion. Its shared historical target table does
not make it an active Gochara producer.

## 3. Current source, deployment and physical-data truth

| Surface | Rechecked state | Qualification |
|---|---|---|
| Execution source | `codex/madhav-data-plane-execution@e5307fadef42cca557a1c0ca3c1831b1296e22b4` | Accepted L2 terminal and L3 implementation base; not merged or deployed. |
| Protected main | `origin/main@731e311f0b8f5f84db2f152b93951e1d3d50d89a` | Fetched current at W0 open. |
| Web | `amjis-web-02258-jj2`, 100%; image and `NIRMANA_DEPLOYED_SHA` `731e311f…` | Deployed main, not accepted L2/L3. |
| Sidecar | `amjis-sidecar-probe-c558e60d3267-34615542574-1`, 100%; image `c558e60d…` | Deployed image evidence only; not L3 acceptance. |
| Build job | ready; image `brahma-pipeline:c558e60d…` | No execution dispatched. |
| MCP | `amjis-mcp-00630-4zs`, 100%; image `f5c1ab02…` | Receiving surface remains unproved for this campaign. |
| Frozen campaign definition | `t3-2026-09-11-8b884eac`, manifest `8b884eac…` | Current definition has zero L3 events. Historical t0-t2 events are not carried forward as current acceptance. |
| Physical generation infrastructure | `public.l1_data_plane_generation_heads` and `public.l2_data_plane_generation_heads` absent | Accepted source contracts are not physical upstream generations in the connected environment. |
| Governed chart core outputs | six tables each exactly 0 rows | `kala_activation`, `kala_convergence`, `kala_obstruction`, `kala_darshana`, `kala_bhavishya`, `kala_field_snapshots`. Missing computation must not be narrated as absence of an effect. |
| Predicate/MSR join | 50,678 predicates; 0 null IDs; 79 rows / 79 IDs unmatched on chart+signal | A physical reconciliation gate; cause not inferred. |
| Existing field capital | estimated 10,966,448 `kala_field` rows and 5,622,169,600 total bytes | `pg_stat_user_tables` estimate, not accepted useful coverage or a rebuild warrant. |

The connected read path was first verified as `retrieval_census_ro`. Access to
the governed campaign schema was denied to that role as designed; the necessary
campaign-only queries then used `amjis_app` with
`default_transaction_read_only=on`. No writer, migration, build, data mutation,
deployment or campaign event was executed.

## 4. First safe frontier and holds

The current frozen definition has no L3 event chain. It contains only partial L2
events (8 `asset_frozen` rows) and no L0/L1 event rows under t3. Therefore no
physical L3 build is eligible at W0 open. The first safe frontier is source/local/
disposable work only:

1. Make Kshetra planning/dry-run/resume mutation-free and prove crash/resume and
   content-bound publication behavior.
2. Preserve Bhavishya issued/history identity across replacement, including an
   empty candidate result.
3. Freeze the exact code/data/field DAG, FK/non-FK blast radius and first
   independent numerical fixtures.
4. Begin consumer sentinels that fail on missing, partial, stale or unqualified
   state without claiming integration.

Physical W1 remains held on compatible L0-L2 generations, exact source/release
integration and accepted dependency vectors. Century v3 retains its named hold.
No full-chart rebuild is authorized by this packet.

### 4.1 Source-derived DAG and producer/use map

The current source and corrected registry migrations contain 81 declared
dependency entries, of which 32 are active-L3-to-active-L3 edges. Historical
edge-audit counts are not reused as current truth. The first physical row frontier,
after accepted L0-L2 data exists, is `ka_gochara_resonance`, `ka_kota_chakra`,
`ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_tithi_pravesha`,
`ka_sudarshana_varsha`, `ka_yojaka` and `ka_avadhi`. Service qualification can
independently cover `ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva` and
the pure Tulana kernel. This is packet eligibility, not rebuild authority.

| Identity | Physical/service output owner | Actual material L3 input / principal use | W0 disposition |
|---|---|---|---|
| `ka_gochara_resonance` | `gochara_resonance_map` | L0-L2 transit/fact/clock/rule capital; used by gen2, century and Kshetra | first frontier after upstream data |
| `ka_kota_chakra` | `kala_kota_chakra` | no L3 input; century dependency is declared but not read | preserve; integration decision owed |
| `ka_moorti_nirnaya` | `kala_moorti_nirnaya` | no L3 input; read by century v3 | first frontier |
| `ka_vedha_gochara` | `kala_vedha_gochara` | no L3 input; read by century v3 and undeclared by Sangam | first frontier; close hidden edge |
| `ka_tithi_pravesha` | `kala_tithi_pravesha` | no L3 input; declared century dependency not read | preserve; method/use decision owed |
| `ka_sudarshana_varsha` | `kala_sudarshana_varsha` | no L3 input; annual evidence | preserve; receiving operator owed |
| `ka_yojaka` | `kala_activation_predicates` | broad L0-L2 graph/proposition inputs; used by Sangam/Kalasutra/Vighnakara/Jivana and consumers | first frontier; non-FK signal refs guarded |
| `ka_avadhi` | `kala_avadhi` | L1 clocks plus L2 propositions; current Taranga code does not read it | first frontier; false edge removed from execution DAG |
| `ka_gochara` | `kala_gochara_windows_v2`, generation 2.0 | resonance plus global arcs; downstream catalog/consumer use | after resonance; seed target mismatch held |
| `ka_gochara_v3_century_materialize` | `kala_gochara_windows_v2` staging, `kala_gochara_windows` generation 3, shared build state | resonance, Vedha, Moorti plus L0-L2; not Kota/Tithi in current source | specific hold; protected v1 coexistence required |
| `ka_sangam` | `kala_convergence` | Yojaka, Vedha, services and L1-L2; invokes on-demand Gochara, not materialized `ka_gochara` | dependent; registry edges corrected before build |
| `ka_kalasutra` | `kala_activation` | Yojaka + Sangam + L2 | dependent; recurrence coverage required |
| `ka_vighnakara` | `kala_obstruction` | Sangam + Yojaka + Muhurta + L0/L1 | dependent; cascade/referrer protection required |
| `ka_taranga` | `kala_taranga` shared with opt-in service upsert | Sangam + clocks + propositions; no Avadhi read | dependent; shared-owner fence required |
| `ka_kala_darshana` | `kala_darshana` | Sangam + Vighnakara; does not read Kalasutra activation | dependent; false edge removed from execution DAG |
| `ka_jivana_parva` | `kala_jivana_parva` | Darshana + Sangam + Yojaka + clocks/services | dependent |
| `ka_bhavishya_lekha` | `kala_bhavishya` | Darshana + Vighnakara + Sangam + L2 | P0 history repair before dependent build |
| `ka_kshetra` | 15-table field family | staged L0-L3 inputs and internal S0→S2→S3→S1→S4→S5/6/6.5/8/snapshot DAG | P0 planning repair before any trial |
| `ka_graha_sancara` | service only | ephemeris; service consumers | independent proof |
| `ka_dasha_kala` | service only | accepted L1 clocks; Sangam/Jivana/Kshetra | independent proof after physical clock data |
| `ka_muhurta_seva` | service only | pure/reference inputs; Sangam/Vighnakara | independent proof |
| `ka_tulana` | comparative service/result | Sangam + Vighnakara + Darshana | kernel tests early; data-bound acceptance late |

Shared ownership that must be fenced: gen2 and century v3 share
`kala_gochara_windows_v2`; protected sweep v1 and century v3 share
`kala_gochara_windows`; Gochara generations share `kala_gochara_v2_build_state`;
Kshetra owns `kala_insights.lel_derived=false` while `mi_bhara` owns true rows;
the opt-in Taranga service can write the same natural keys as the writer; registry
and substep-progress rows are shared control surfaces.

The field/partition contract register expands this asset view to 39 producer
relation/service partitions and 699 unique explicit fields across all 22 active
identities. Every row names its producer, type/shape, unit, grain, key/partition
role, null/empty/failure semantics, qualification, transformation/persistence,
receiver and falsifying test. It reconciles 14 digest-bearing assets/26 accepted
components, marks Kshetra's 13 included and two QX relations separately, models
four service-only payloads with zero domain DML, and fences the retired sweep.
Q2/Q4/QX and open JSON shapes remain closed gates.

### 4.2 Replacement blast radius

Deleting/replacing `bodha_msr_signals` cascades to `kala_activation`,
`kala_bhavishya`, `kala_convergence`, `kala_darshana` and `kala_obstruction`, as
well as L2 embeddings/contradictions. Deleting convergence cascades obstruction
and Darshana, nulls Bhavishya convergence, and cascades through `phala_anchors`
into multiple L4 tables. Deleting Bhavishya nulls `phala_anchors.bhavishya_id`.
These are preservation obligations, not authorization to edit L4.

Non-FK referrers include Yojaka signal IDs; Avadhi JSON roots; resonance target
refs; Gochara fact/source/parent structures; activation clock/contribution
structures; Jivana summaries; Bhavishya source chains; Taranga components;
overlay fact/source refs; all Kshetra cross-stage IDs and snapshot substrate
maps; and Phala signal/discovery/top-anchor IDs. Kshetra's fifteen tables have no
database-enforced internal DAG, so deletion/reconstruction order and content-bound
resume must be proved explicitly.

### 4.3 W0 P0 corrections and bounded baselines

Kshetra planning/recovery is corrected at `3f109869d`: a transaction-scoped
chart/asset lock and all-15-table preflight precede writer DML; only
`kala_insights.lel_derived=false` is owned. Any populated slice, including stale
snapshot or empty-discovery state, fails before DML and remains unchanged.
Genuinely empty/no-event-class preparation performs no DML or progress receipt;
resume identity is v10. The real substep driver/savepoint test still proves
failed output/receipt rollback. Root maintained validation passed 461 with 8
skips and 2 expected failures; independent review passed 27 focused and 133
expanded tests plus one skip and returned ACCEPT. Populated replacement is held
until W7 immutable publication; no backup/atomic-replacement claim is made.

Bhavishya is corrected at `a3e518864`: a chart transaction lock covers the full
read/plan/write span; the entire candidate and referrer set is validated before
DML; unchanged protected rows retain identity/content; any changed or stale
outcome/notes-bearing or Phala-anchored row fails closed. Root focused validation
passed 25 with one environment-gated skip; a disposable two-connection lock proof
and broad suite were reported by the implementation owner; independent review
returned ACCEPT. Stable issued-history generation remains a W6 packet.

DHARA's clock-knot endpoint defect is corrected through `1f9cedbb0` and the
`MADHAV_DATA_PLANE_L3_DHARA_NUMERICAL_CONTRACT_v1_0.md` contract. The preceding
interval uses the left limit and the next interval the exact right-continuous
value; v1.2 enters field snapshot and resume identity. Independent review passed
44 focused tests. The final integrated broad L3 suite passed 1,488, skipped 41
environment-gated cases and retained 2 expected failures in 91.00 s.

The reproducible baseline record contains exact commands and five raw matched
runs. Small-fixture medians: preparation 0.47 s process wall; publication/hash
6.99 s; null 0.31 s; structured build 0.315060 s with 61 rows, 263,206 canonical
bytes and stable output/content hashes. Transit medians: 4.56 ms bypassed,
2.42 ms cold, 1.92 ms warm and 44.51 ms fanout; the host used explicitly pinned
Moshier fallback. Database SQL/I/O/WAL/storage and qualified live first-result
latency remain unmeasured. These are local test workloads, not production
runtime or a general optimization claim.

### 4.4 W0 generation/publication design

The complete frozen design and exact next packets are recorded in
`MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md`. Generations are
content-addressed by source/contract/context, the exact transitive upstream vector,
partition plan and semantic versions; empty partitions are explicit. Immutable
candidate and selected heads remain separate, layer publication is an atomic
compatible manifest, corrections create new generations, and rollback repoints a
head rather than rewriting history. Kshetra's fifteen tables share one content-
bound stage plan; Bhavishya fails closed on protected content until its W6 stable-
generation packet. This is reviewed design, not physical infrastructure.

### 4.5 W2 first-frontier source candidate

W0 permits `L3-W2-FIRST-FRONTIER-SOURCE-01` source/service work while W1 is
held. Initial candidate `b0c5652ba`, corrected at `a1767bb91` and `47131772b`,
covers the eight named first-row-frontier writers and all four independent service/pure identities.
Every row writer now prepares
its candidate before chart-partition DELETE; empty candidates preserve prior
capital. Gochara requires all 27 event-class partitions; Kota/Moorti/Vedha
require an exact unique contiguous daily horizon for every body; and Avadhi
requires canonical `chara_karaka` plus both MD and AD coverage across all seven
systems. Yojaka and Avadhi dry runs open no database cursor.

Dasha now fails the whole request when one named system read fails rather than
returning a partial payload as complete. Tulana rejects non-finite, duplicate or
unqualified inputs while retaining its fixed forensic result. The DB-free W2
contract freezes all four service payload shapes. The initial exact-tip review
rejected `b0c5652ba` with two HIGH and four MED findings. Correction `a1767bb91`
passes 57 behavioral contracts, 482 affected tests with 5 environment-gated
skips, and complete `tests/l3` at 1,521 passes, 41 skips and 2 expected failures.
Final exact-tip review PASSes `47131772b355ae2c67b1f6fb2b90e9fa007e2202`
with zero CRITICAL/HIGH/MED/LOW findings. Exactly ten reviewed W2 writer digests
and the L3 aggregate were reconciled locally; the whole checker still reports
only protected L0/L1/L2/L4 drift. This accepts source only and does not unlock
physical W1.

## 5. Migration and release collision

The accepted L1/L2 execution lineage originally used 1033/1034, colliding with
the open planner/Pūrṇa Anveṣaṇa stack. RI-01 positively confirmed all four
filenames and their semantic side effects absent from the only authorized
shared target, reserved 1035/1036 at live coordination commit `ef132c87d`, and
relocated the two data-plane candidates to the active
`platform/supabase/migrations` directory. Their initial normalized SQL identities
were unchanged by relocation. Independent security review then found three HIGH
admission/history defects. The candidate now intentionally changes executable SQL
to add declared L1/L2 partition contexts, immutable L2 build intents, foreign-key
closure, generation-state/cardinality guards and mutation-free exact replay.
Hardened SQL identities are `9de44b8285da2d85a1a335f2698e41491f1bedc149114abe1531b2b3d37b572f`
for 1035 and `eef1dc67912fcde2e58544410e2e91d7676997c1c15d03c8965b5450fc12a982`
for 1036; neither is applied to the shared target.

The candidate migration guard passes with next number 1037. Direct
apply/reapply, 75 focused contracts, 67 migration tests and expanded L1/L2
admission/replay negatives pass on disposable PostgreSQL. ESLint has zero errors
and TypeScript passes. The full unit run remains red only in eight frozen L0
receipt assertions: current aggregate `3dda2611...` differs from reserved frozen
`5125cccb...`, and precedent forbids an L3-owned repin. RI-01 reconciled only its
two changed writer digests and L3 aggregate `139bde31...` to reviewed W0 tip
`00a161195`; the whole-file checker still reports non-L3 stale pins for L0, L1,
L2 and L4, none of which L3 restated.

One reviewed HIGH security gate also remains open. Production migration/build
identity `amjis_app` owns newly created objects; `role_orchestrator` is NOLOGIN
and has no membership path from `amjis_app`. PUBLIC revocation and intended grants
do not isolate an owner. Protected owner roles, a distinct build login and the
role/credential/ownership cutover require administrator authority outside this
candidate. RI-01 therefore remains held before PR/shared apply; it needs
protected non-L3 pin reconciliation and database cutover authority, followed by
exact-tip review and full checks. This is not protected delivery.

Independent exact-tip re-challenge at `6a7ecc17117163debcc4b742aa183f17588ef621`
returned PASS for all code-owned findings with no additional
CRITICAL/HIGH/MED/LOW finding. It explicitly retained the separate HIGH
production-owner cutover hold and authorized no PR, shared apply, deployment or
build.

## 6. Workstream ownership and recovery

| Lane | Current bounded owner | State |
|---|---|---|
| A — meaning/data/DAG | bounded source-local Bhavishya and first-frontier contract owners; conductor integrates evidence | W2 SOURCE ACCEPTED LOCALLY; physical data held |
| B — performance/architecture | bounded Kshetra/DHARA owners and independent reviewers | SAFETY/REFERENCE ACCEPTED; production trial held |
| C — consumer integration/value | L3-U05 implementation and independent reviewer | SENTINELS ACCEPTED; integration/value not run |

Heartbeat `l3-k-la-execution-recovery` is ACTIVE at a 15-minute cadence and is
thread-attached. Recovery proof is deliberately `PENDING_FIRST_SCHEDULED_WAKE`;
configuration/read-back is not continuity proof. Durable recovery starts from
this file, the execution ledger and the exact next eligible action above.

## 7. State truth at W0 open

| State | Evidence |
|---|---|
| source producer readiness | accepted L0-L2 contracts; W0 terminal PASS at `00a161195`; W2 source accepted at reviewed `47131772b`; hardened precursor held on two external authorities |
| physical upstream data | `HELD`; required generation-head relations absent |
| L3 physical data | legacy capital exists, but current t3 acceptance is absent and six canonical outputs are empty |
| consumer integration | `NOT_RUN` |
| protected deployment | accepted L2/L3 `NOT_DEPLOYED` |
| consumer value | `NOT_EVALUATED` |
| empirical predictive performance | excluded and not claimed |

## 8. Pre-amendment recovery action (superseded by §9)

W0 terminal PASS is recorded at exact source tip `00a161195`; W2 source is
accepted at exact reviewed tip `47131772b355ae2c67b1f6fb2b90e9fa007e2202`.
Before DP-SD-018, no further bypass packet was opened. RI-01 remained held before PR/shared
apply on reconciliation of protected non-L3 provenance pins, including frozen
L0, and administrator-owned database role/credential/ownership cutover. No L3
build is eligible until that precursor is accepted/deployed and compatible
L0-L2 physical heads exist.

## 9. DP-SD-018 resumption state

DP-SD-018 content `6b6ce9c06ce54fb7c474d97c70257a505bf2ed84` and approval
`7f21f27b14a7909424591a530096dc2f5d6e2b13` now authorize the two formerly
external remediation domains without declaring them complete. The full L3 goal
continues; its platform state remains `blocked` and is treated as a fresh blocker
audit during this owner-directed resumption, never as permission to mark an
unfinished objective complete.

Fresh reconciliation preserves `origin/main@731e311f0b8f5f84db2f152b93951e1d3d50d89a`,
the clean execution checkpoint `5142109f7f219ea860f859e322646f79d875bee8`,
no open execution-branch PR, and the active Pūrṇa Recovery Wave 7 source-local
lease. The old W0 and RI-01 leases were closed/superseded; the new remotely
verified source-design fence is
`origin/campaign-coordination@754aa9ffe24a0865378c8c9cd148847abfec2b02`.
The existing heartbeat was updated in place for RI-02.

Lane P provenance supersession is independently accepted at exact tip
`8ebb3737cedfd4fde802f30845d94f8e8a641c33` and integrated serially through
`7b1576d59`; its immutable decision, identity, retired-sweep and historical-chain
proofs pass in the integration worktree. Lane S exact candidate `70417f577` is
rejected: adversarial restricted-login probes reproduced direct-DML lifecycle
bypass, fabricated generation heads and semantic-status false greens, while
source review found fail-open IAM isolation, unsafe deployment ordering and
incomplete migration identity attestation. A bounded correction may adapt only
individual protected L1/L2 writer call sites to the scoped lifecycle APIs; it
does not reopen `WriterBase` or producer semantics.

Production role, credential, IAM, migration, deployment, build and data
mutations remain held under this source-design lease. The next eligible gate is
independent exact-tip acceptance of corrected Lane S and integrated review,
followed by a separate exclusive cutover lease.

The first reconstructed Lane S correction through exact tip `add01c4ed` is also
rejected. Independent review found a CRITICAL transaction-ordering window where
ownership/DML grants could commit before mutation guards, plus residual old-row
and shared-table ownership, effective IAM/literal credential, restore-evidence,
role-topology, catalog-completeness and dispatcher rollback gaps. The source
lease elapsed during this review; mutation was paused and the unchanged scope
was renewed at coordination pin `754aa9ffe` through 2026-09-16 02:00 IST before
the next correction. No rejected Lane S commit is integrated or production
eligible.
