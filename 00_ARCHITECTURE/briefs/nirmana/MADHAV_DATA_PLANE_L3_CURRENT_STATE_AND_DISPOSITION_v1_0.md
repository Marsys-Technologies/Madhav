---
artifact: MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION
version: "1.0"
status: W0_FOUNDATION_SAFETY_ACTIVE
observed_at: 2026-09-15T03:03:00+05:30
strategy_decision: DP-SD-017
strategy_content_commit: 793972c754b106688097dbc54536c1a9c270a793
approval_pin_commit: 04a9ab33effa23e5e9b4e89772330ae264498a9b
accepted_l2_terminal: e5307fadef42cca557a1c0ca3c1831b1296e22b4
active_identity_denominator: 22
protected_retired_identity: ka_gochara_sweep
active_packet: L3-W0-FOUNDATION-SAFETY-01
coordination_lease: MADHAV-DATA-PLANE-L3-W0-20260915
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

## 5. Migration and release collision

The accepted L1/L2 execution lineage adds migrations `1033` and `1034`, while
open planner/Pūrṇa Anveṣaṇa branches already use different migrations numbered
`1033` and `1034`. Protected main stops at `1032`; the live generation-head
relations are absent. This is a real release-integration collision, not permission
to edit an applied migration or merge either history wholesale. W0 safety work
may proceed without a migration. Any L3 schema packet must reserve an unused
number against refreshed main, all release-bound branches and the shared migration
guard, and the accepted L1/L2 migrations need an explicit compatible integration
decision before protected delivery.

## 6. Workstream ownership and recovery

| Lane | Current bounded owner | State |
|---|---|---|
| A — meaning/data/DAG | `l3_w0_dag_inventory` read-only discovery; conductor integrates evidence | ACTIVE; no mutation |
| B — performance/architecture | `l3_w0_kshetra_safety` read-only discovery; one later isolated writer owns overlapping Kshetra source | ACTIVE; no mutation |
| C — consumer integration/value | `l3_w0_bhavishya_consumer` read-only discovery; producer/data acceptance remains a gate | ACTIVE; no mutation |

Heartbeat `l3-k-la-execution-recovery` is ACTIVE at a 15-minute cadence and is
thread-attached. Recovery proof is deliberately `PENDING_FIRST_SCHEDULED_WAKE`;
configuration/read-back is not continuity proof. Durable recovery starts from
this file, the execution ledger and the exact next eligible action above.

## 7. State truth at W0 open

| State | Evidence |
|---|---|
| source producer readiness | accepted L0-L2 local contracts; L3 not yet repaired/accepted |
| physical upstream data | `HELD`; required generation-head relations absent |
| L3 physical data | legacy capital exists, but current t3 acceptance is absent and six canonical outputs are empty |
| consumer integration | `NOT_RUN` |
| protected deployment | accepted L2/L3 `NOT_DEPLOYED` |
| consumer value | `NOT_EVALUATED` |
| empirical predictive performance | excluded and not claimed |

