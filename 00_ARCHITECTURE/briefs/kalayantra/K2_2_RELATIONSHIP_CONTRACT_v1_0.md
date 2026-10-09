# K2-2 F1 relationship contract v1.0

Authority: KYD-131/KYD-132; ALGO 3.11, PLAN §8 resonance / §8.1 R1–R6.
Migration class: NEEDS-PROTECTED-WINDOW (additive CREATE TABLE/INDEX in public).
Migration: 1342_k2_2_f1_relationships.sql. Guard proposed 1340; fresh coordination
reserved 1340/1341 elsewhere. Renumbered before application; §2 reservation
ce9fcf0a90e3073e86f7e97ad26b65e500d11f06. Conductor owns production window.

New `kala_f1_target_object`: PK(chart_id uuid, ayanamsha_id text, generation text,
object_id text); object_type ∈ {graha, sign_interval}; longitude_deg nullable finite
[0,360), sign_num nullable [1,12], fact_ids jsonb array. Graha identity is the L0
canonical subject; a sign interval identity is its zodiac sign, independent of role.
No weight; an unresolved operand creates no physical object.

New `kala_f1_relationship`: PK(chart_id, ayanamsha_id, generation, edge_id text);
event_class_id text, object_id nullable FK to target_object in the same partition;
role closed to the legacy target roles plus promise_participant; frame ∈
{lagna,moon,zodiac}; mechanism_id text, rule_id text, provenance text, target_ref text,
qualifier nullable text, resolution_state ∈ {resolved,unavailable,unqualified}.
Resolved iff object_id exists. Edge id hashes class/object/ref/role/frame/mechanism/
rule/provenance/qualifier; separate roots and roles cannot collapse. Candidate-only
replacement checks both live head and retained candidate state under an exclusive candidate lock and shared head lock;
no deletes/updates to legacy map, published generations, L0/L1 or promise predicates.
Build identity is caller-owned; writer cannot commit/rollback/publish.

Reads: chart_facts (chart_id, ayanamsha_id, fact_id, fact_category, fact_subject,
fact_key, fact_value_num, fact_value_text, unit); reference_signs (sign_id,lord);
brahma_event_ontology (event_class_id,signature_model,citations); bg_transit_rules
(id,rule_type,graha,primary_house,classical_citation: house counted from Moon);
ga_yoga_firings (chart_id,ayanamsha_id,yoga_canonical_id,fired,constituent_fact_ids,
constituent_planets,constituent_houses,bhanga_active); chart_dashas (chart_id,ayanamsha_id,system_id,
level_n,lord_graha); K2-1b candidate kala_activation_predicates (chart_id,
ayanamsha_id,generation,event_class_id,mechanism_id,derivation_ledger_jsonb).
All source columns are from the governed prod_schema snapshot, except the declared
K2-1b additive graph columns. Candidate predicates are selected by exact generation.

Dispatch: explicit candidate_generation selects F1; otherwise legacy run is retained
until judge cutover. F1 never writes gochara_resonance_map; served legacy readers
remain unchanged. Candidate generation must begin candidate: and cannot name a
live or retained published head. Repeats replace only the same candidate partition.

Certification mapping (K8-K12): ka_dasha_kala → F2 typed clock identity; ka_avadhi →
F2/F1 period applicability read model (K1-2); ka_yojaka → F1 mechanism/fact/effective
state (K2-1b); ka_gochara_resonance → F1 frame/role/target projection, legacy serving
retained until judge cutover. This is a mapping, not an earned certification verdict.
Oracles: frame-before-match, distinct roles, no weight, R1–R6, candidate/published
isolation, repeat build, source absence and derived Phaladipika locators.

Version-specific certification mapping (source mapping; production verdicts remain due):

| Field | ka_dasha_kala | ka_avadhi | ka_yojaka | ka_gochara_resonance |
|---|---|---|---|---|
| kind / carriage | service / computation, served call unproved | data / derivation, legacy dossier read retained | data / derivation, legacy temporal-activation read retained | data / derivation, legacy coverage read retained; F1 candidate unserved |
| ldgr_source | F2 period IDs, K1-1 source adapter | dossier period/fact/promise refs, K1-2 | derivation_ledger_jsonb.fact_ids / source | object.fact_ids and edge.provenance / rule_id |
| vocab_alias | kala_core.clocks typed systems/lords | F2 period identity | sourced L1 fact/mechanism identity | L0 released graha_id, sign IDs; closed frame/role CHECKs |
| prose | service payload, no table | inherited dossier note; K1-2 owns new model | no new narrated fields | no new narrated fields; citation/provenance is evidence |
| null_convention | typed F2 unavailable states | K1-2 applicability / missing evidence | fact/effective state, missing target null | unavailable/unqualified edge with object_id NULL; no fabricated object |
| produced_tables | none (service) | kala_avadhi (K1-2 ownership) | kala_activation_predicates | gochara_resonance_map legacy; kala_f1_target_object / kala_f1_relationship candidate |
| density_tier_columns | no served row | inherited legacy tier gap | inherited legacy tier gap | no tier claimed for private F1; legacy coverage-only declaration retained |
| writer digest | generated inventory entry | generated inventory entry | generated inventory entry | generated inventory includes F1 import closure |
| disposition | F2 core lookup retained | F2/F1 read model (K1-2) | F1 graph (K2-1b) | F1 relationship projection; legacy writer retained to judge cutover |

Semantic-fingerprint declaration for F1 v1: the sorted physical-object identities,
geometry and L1 refs, plus sorted distinct edge IDs over class/object/ref/role/frame/
mechanism/rule/provenance/qualifier/resolution. One object with two roles, changing a
frame/rule/root, or changing a missing operand changes that structure; adding weight
is invalid. Determinism and repeated partition equality are executable item oracles.
Mapped against the checked-in criterion registry (revision 26); no earned PASS/N/A is
asserted. Ldgr source presence does not prove referential resolution; local SQL/oracles
prove this change only. Idem uses static candidate-scoped DELETEs; Build remains due
on a canonical run. Null/Dens and legacy narrative claims retain their measured
limits. Carr.D2/D3 and service Earn.service_state have NO_DETECTOR in this registry;
engine detector changes are downstream dependencies. The packet mapping does not
rewrite L0–L2 entries. The whole-file declaration hash changes; certificate
freshness and any recertification remain the certifier's responsibility.
