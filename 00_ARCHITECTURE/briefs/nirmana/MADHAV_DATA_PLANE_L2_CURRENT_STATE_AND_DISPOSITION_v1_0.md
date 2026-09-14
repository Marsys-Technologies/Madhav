---
artifact: MADHAV_DATA_PLANE_L2_CURRENT_STATE_AND_DISPOSITION
version: "1.0"
status: WP0_COMPLETE_IMPLEMENTATION_PENDING
observed_at: 2026-09-14T20:56:18+05:30
strategy_decision: DP-SD-015
execution_base: 18503e9c2dbb140f5d17b4bc34a5f6d087f97c38
strategy_content_commit: 86374d65f3dc742085783e352a9999e2edb48715
approval_pin_commit: 7c7d198a18db403637aaebace7f1c499647b409d
local_strategy_commits: [b30b401355427b491f05ad1832d8ee721b31c11e, 2bc299a7df73618d6af9e4af4323615f3e5bf124]
current_writer_denominator: 23
historical_formal_denominator: 22
next_stage_hold: "L3 remains WAITING_FOR_STRATEGIC_BRIEF."
---

# L2 Bodha current state and disposition

## 1. Evidence boundary

This record is the WP0 stocktake required by DP-SD-015. It does not replay or
amend the historical Nirmāṇa campaign. The current source census is exactly 23
registered `bo_*` identities in 22 Python files because `bo_laksana.py` owns two
registrations. The frozen formal receipt remains 22/22: supporting
`bo_grounding` entered after that denominator was fixed. Current producer review
therefore uses 23/23 while historical evidence continues to say 22/22.

All twelve accepted upstream blobs in the L2 brief were re-resolved at exact L1
terminal `18503e9c2dbb140f5d17b4bc34a5f6d087f97c38`; every blob matched. The
accepted L0 release remains `f6fed12c794224329f6b3b436f8b1b814499d06d`.
The first-slice L1 input digest is
`25c46b559def7e1a9f8e1a05114be5a6c306a846a23b2665b1b5c917128d3279`.
No live database was queried; population, service, delivery and value states are
therefore `NOT_RUN` or `UNPROVED`, never inferred from old counts.

## 2. Complete writer register

`P/I/E/Q/H` retain the strategy meanings preserve, integrate, correct/enrich,
qualify/limit and restricted/historical. Natural-key text is the latest checked-
in registry declaration; `legacy active` means current replace-in-place output,
not retained data-plane history.

| # | Writer / implementation | Output ownership and current natural key | Actual material inputs | Epistemic role | WP0 disposition |
|---:|---|---|---|---|---|
| 1 | `bo_laksana` / `bo_laksana.py` | `bodha_msr_signals`; owned signal classes declared by migration 930 | L1 facts/vichāra/yoga plus admitted catalogs/rules | proposition | P/I/E/Q; bind exact upstream context and rule status |
| 2 | `bo_laksana_rerank` / `bo_laksana.py` | update-only graph/rank columns on `bodha_msr_signals` (migration 940) | same signals plus CGM nodes/contradictions | navigation enrichment | P/I/Q; never count as an independent vote |
| 3 | `bo_bimba` / `bo_bimba.py` | `bodha_cgm_nodes`; `(chart, aya, snapshot, node_type, node_subject)` ownership, migration 938 partition | MSR signals and exact L1 fact roots | configuration nodes | P/I/Q; stable typed identity |
| 4 | `bo_karanajala` / `bo_karanajala.py` | `bodha_cgm_edges`, `bodha_contradictions`; writer-scoped chart/aya edge and contradiction identity | nodes, signals, L1 facts/vichāra; currently `services.ka_temporal` | signed relation | P/I/E/Q; remove L3 import and resolved windows |
| 5 | `bo_cgm_paths` / `bo_cgm_paths.py` | `bodha_cgm_paths`; `(chart, aya, snapshot, path_type, from_node, to_node)` (983) | CGM nodes/edges | ordered path candidate | P/I/Q |
| 6 | `bo_cgm_motifs` / `bo_cgm_motifs.py` | motifs `(chart,aya,snapshot,fingerprint)`, subgraphs `(chart,aya,centroid)`, topology `(chart,aya,snapshot)` (1001) | CGM nodes/edges | discovery candidate | P/I/Q |
| 7 | `bo_yantra_mechanism` / `bo_yantra_mechanism.py` | `bodha_mechanisms`; `(chart,aya,class,fingerprint)` (1010) | nodes, edges, motifs, L1 facts | mechanism candidate | P/I/E/Q; verification must be executable or null |
| 8 | `bo_sangati` / `bo_sangati.py` | CDLM `(chart,aya,snapshot,row_domain,col_domain)`, convergence `(chart,aya,snapshot,domain)`, triangulation `(chart,aya,question,tradition)` (997) | signals and contradictions | multidomain linkage | P/I/E/Q; preserve both signed sides and shared roots |
| 9 | `bo_cdlm_summary` / `bo_cdlm_summary.py` | summary `(chart,aya)` plus rollup/cluster siblings (987; sibling order defect retained as known baseline) | CDLM cells | navigation summary | P/I/Q; hydration required |
| 10 | `bo_pratijna` / `bo_pratijna.py` | `bodha_pratijna`; `(chart,aya,event_class)` (944) | signals, v4 engine, triangulation | occurrence/condition ledger | P/I/E/Q; preserve separate axes and polarity |
| 11 | `bo_arudha` / `bo_arudha.py` | MSR `signal_type_class=arudha` (927) | exact Arudha and graha L1 facts | reference-frame proposition | P/I/Q |
| 12 | `bo_special_lagna` / `bo_special_lagna.py` | MSR `signal_type_class=special_lagna` (909) | special-lagna L1 facts | specialized proposition | P/I/Q |
| 13 | `bo_sudarshana` / `bo_sudarshana.py` | MSR `signal_type_class=sudarshana_agreement` (880) | Lagna/Moon/Sun/graha sign facts | correlated-frame proposition | P/I/Q; explicitly static, non-temporal |
| 14 | `bo_vargottama_dhana` / `bo_vargottama_dhana.py` | MSR `signal_type_class IN (vargottama_amplification,dhana_axis)` (910) | varga and position facts | specialized proposition | P/I/E/Q; shared-root grouping |
| 15 | `bo_nakshatra_semantic` / `bo_nakshatra_semantic.py` | MSR `signal_type_class=nakshatra_semantic` (908) | nakshatra/L1 structural facts | symbolic structural proposition | P/I/Q |
| 16 | `bo_upaya` / `bo_upaya.py` | six remedy tables and keys declared by 1013 | signals, CDLM, motifs, admitted remedy corpus; currently chart daśā/life events | practice eligibility | P/I/Q/H; stop resolved timing/window output |
| 17 | `bo_samskara` / `bo_samskara.py` | `bodha_signal_embeddings(signal_id)` (979) | MSR text/content | navigation index | P/I/Q; similarity is not evidence |
| 18 | `bo_anveshana` / `bo_anveshana.py` | `bodha_discoveries`, `bodha_anomalies`; chart/aya detector identities | signals, graph, convergence, embeddings | discovery candidate | P/I/E/Q; detector reason and evidence required |
| 19 | `bo_drishti` / `bo_drishti.py` | `bodha_question_lenses(chart,aya,question_type)` (942) | signals and edges | inquiry obligation/navigation | P/I/E/Q; no pre-answer |
| 20 | `bo_chart_gestalt` / `bo_chart_gestalt.py` | `bodha_chart_gestalt(chart,aya)` (985) | signals, CDLM, nodes, paths, discoveries | whole-chart pointer | P/I/Q; summary cannot adjudicate |
| 21 | `bo_samvada` / `bo_samvada.py` | read/projection writer over `vw_chart_digest`; no independent durable table | L1 facts, signals, contradictions, convergence, remedies, quality | corrected navigation digest | P/I/Q; query time is not build freshness |
| 22 | `bo_pramana_mapa` / `bo_pramana_mapa.py` | `synthesis_quality_scorecard(chart)` (949) | L1/L2 tables plus reachable integrity checks | scoped quality detector | P/I/E/Q; no constant-green authority |
| 23 | `bo_grounding` / `bo_grounding.py` | `bodha_grounding_matches(chart,aya,target_kind,target_id)` (947) | yoga firings, signals, exact Sūtrāvalī rules | source/rule matcher | P/I/E/Q; support identity outside historical 22 |

All 23 identities occur in `platform/src/generated/nirmana-writer-digests.json`.
`bo_laksana` and `bo_laksana_rerank` intentionally share one source digest.
Output-digest/natural-key specifications exist for current writer partitions;
they remain historical/current-state evidence, not proof of the new contract.

## 3. Dependency vector and two-pass DAG result

The cycle-free first frontier is L1-fed proposition/reference producers:
`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`,
`bo_vargottama_dhana`, `bo_nakshatra_semantic`. The hard closure is:

`L1 facts/rules -> propositions -> bo_bimba -> bo_karanajala ->
paths/motifs/mechanisms -> bo_sangati -> bo_cdlm_summary/bo_pratijna ->
practice/navigation/discovery/quality/grounding -> bo_laksana_rerank`.

Semantic edges not fully represented by historical `asset_registry.depends_on`
are recorded here by consumed field: signal IDs/configuration/evidence roots into
nodes; typed node IDs and signed/cancelled relation fields into edges; ordered
edge IDs into paths/motifs; domain-role and signed driver arrays into CDLM;
occurrence `[0,1]` and condition-affliction `[0,10]` ledgers into Pratijñā;
source/rule IDs into grounding; underlying IDs into all navigation/quality
projections. No source-level registration cycle was found. Producer acceptance
must validate this semantic closure, not merely the registry arrays.

## 4. Cross-layer and consumer backcast

Two live L2 boundary inversions require source correction:

1. `bo_karanajala.py` imports `services.ka_temporal` and resolves
   `active_dasha_periods_jsonb`. New L2 generations must emit no resolved window;
   legacy columns/history remain readable and explicitly non-authoritative.
2. `bo_upaya.py` reads `chart_dashas` and life-event milestones to write
   `bodha_rm_dasha_windowed_prescriptions`. This is also resolved temporal
   meaning and must stop in new L2 generations. The table/history remains.

Other activation/date columns found in L2 are null compatibility hooks or
derived read fields and may remain only as `UNAVAILABLE_AT_L2`/legacy. Ordinary
`computed_at` observation timestamps are not activation semantics and are
excluded from stable identity.

Read-only consumers currently select summaries, top-ranked rows and temporal
joins across retrieval, synthesis, Paripraśna and MCP surfaces. Those consumers
remain unmodified and therefore cannot establish integration. The producer
package must retain full domains, low-rank decisive items, sign, cancellation,
shared-root groups, rivals and hydration pointers so a later integration brief
can correct first-domain, top-K, unsigned, summary-only and temporal loss.

## 5. Adjacent-authority register

| Surface | Role / callers | Authority and disposition |
|---|---|---|
| `bodha_writers/formulas.py` | shared scoring/formula kernel | preserve; calculations are not source qualification |
| `bodha_writers/_idempotency.py` | writer-scoped replacement helpers | preserve current ownership/transactions; add only compatible generation support if required |
| `bodha_writers/*_emitter.py` | satellite MSR row builders | integrate through the common L2 contract; temporal hooks stay null |
| `bodha_writers/bhavat_bhavam_registry.py` and amplifier | Bhāvat engineering machinery called by Laksana | `UNQUALIFIED_SOURCE`; positive doctrinal arm `NOT_REACHABLE` |
| `bodha_writers/grounding_matcher.py` | rule/source matching for `bo_grounding` | preserve and require exact qualification/target granularity |
| `bo_pratijna_v4_engine.py`, `bo_pratijna_karyatva.py` | non-registered occurrence/condition/denial/domain engines | preserve axes and provenance; never an additional witness |
| `brahmagyan/bodha/bo_2-5.py` through `bo_2-8.py` and sibling L2 modules | retained scaffold/service capital | read-only historical/adjacent; P/Q/H, no duplicate authority |
| L2 tables, migrations, digest and integrity specs | physical schema/current writer evidence | preserve existing migrations; new migration only for the compatible contract envelope |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/**`, grounding, synthesis, Paripraśna, MCP | read-only downstream demand/projection | observed only; no integration or serving claim |
| local TypeScript Bhāvat maps/absence declarations | local non-dossier declarations | read-only; cannot qualify the accepted source package |
| `services.ka_temporal` | L3 resolver imported by Karanajala | remove import/call from L2; do not edit L3 |

## 6. State truth at WP0

| State | Current evidence |
|---|---|
| present | 23 registered source identities and physical schemas are present |
| populated | historical checked-in/live notes exist; current live population `NOT_RUN` |
| qualified | partial legacy qualification; new L2 contract pending implementation |
| consumed | source-level reads and read-only consumer code observed |
| effect traced | producer-local semantic hazards measured; managed effects unproved |
| served | `UNPROVED` in this goal |
| value evaluated | `NO` |

## 7. Frozen exact mutation manifest

Before the first source edit, WP0 freezes these exact paths. Any expansion
requires same-session handshake update and must remain inside the approved outer
classes.

Core/runtime: all 22 registered writer source files
`platform/python-sidecar/pipeline/orchestrator/writers/bo_{anveshana,arudha,bimba,cdlm_summary,cgm_motifs,cgm_paths,chart_gestalt,drishti,grounding,karanajala,laksana,nakshatra_semantic,pramana_mapa,pratijna,samskara,samvada,sangati,special_lagna,sudarshana,upaya,vargottama_dhana,yantra_mechanism}.py`;
new `platform/python-sidecar/bodha_writers/data_plane_contracts.py` and
`data_plane_resource_mechanism_slice.py`.

Validation/fixtures: new
`platform/python-sidecar/bodha_writers/__tests__/fixtures/l2_resource_mechanism_non_person_v1.json`,
`platform/python-sidecar/bodha_writers/__tests__/test_l2_data_plane_contracts.py`,
`platform/python-sidecar/tests/l2/test_l2_writer_adoption.py`, and
`platform/python-sidecar/scripts/validate_data_plane_l2_contract.py`.

Schema/digest: new
`platform/migrations/1034_data_plane_l2_producer_generations.sql` and existing
`platform/src/generated/nirmana-writer-digests.json` only if source changes
require regeneration.

Evidence: this file, the six remaining mandatory `MADHAV_DATA_PLANE_L2_*_v1_0.md`
records named by the brief, and
`MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md`.

Preserved kernels include WriterBase/registry/orchestrator transaction ownership,
existing IDs and natural-key partitions, accepted L0/L1 semantics, formulas,
Pratijñā v4 axes, source matcher, deterministic emitters and legacy read schema.
No L0/L1/L3+, retrieval, campaign, protected pin, workflow, credential or secret
surface is in the manifest.
