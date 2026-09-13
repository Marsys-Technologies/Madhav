---
artifact: MADHAV_DATA_PLANE_L0_CURRENT_STATE_AND_DISPOSITION
version: "1.0"
status: WP0_EVIDENCE_PINNED
produced_on: 2026-09-13
execution_task: "Execution - Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
execution_branch: codex/madhav-data-plane-execution
observed_revision: 60a379d2dc7e2fbc05c95f425d9eacc7b2b6863c
foundation_revision: d838af45524369e804ca17ac63331237b6b8e100
strategy_decision: DP-SD-009
scope: "Revision-pinned L0 producer stocktake and exact mutation manifest; no private-row, deployment, consumer-value or empirical proof."
---

# L0 Brahmagyan current state and disposition

## 1. Evidence boundary

This is the L0-WP0 receipt required before producer mutation. The generated files
`platform/src/generated/nirmana-writer-digests.json` and
`platform/src/generated/nirmana-analysis-layer-pins.json` deterministically report
36 `bg_*` writer identities and four non-writers. The checked-in writer inventory
contains 32 Python writer files because `bg_medical_mappings` also registers the
nakshatra/sign medical identities, `bg_phaladeepika_vedha` registers two identities,
and the transit writer is also registered for the non-writer service alias. That
co-ownership does not change the 40-identity denominator.

The observations below are repository/source observations at the pinned revision.
`DATABASE_URL` was not available to this execution, so present code, generated
identity, checked-in receipt and historical population evidence are kept separate.
No production database, private chart/subject row, deployment, service endpoint or
source acquisition was inspected. `present` therefore never implies populated,
qualified, consumed, effect-traceable, served or value-evaluated.

## 2. Exact mutation manifest fixed before source edits

Only these implementation paths are admitted. A listed file is permission to make
the evidence-justified delta named here, not general edit permission. All other
files remain read-only, including every L1-L5 writer and retrieval/inquiry/synthesis/
MCP consumer.

| Path | Reason and preserved kernel | Rollback |
|---|---|---|
| `platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json` (new) | Canonical versioned identity release; preserve existing IDs and legacy bare-node defaults while separating explicit physical variants. | Remove new immutable release; adapters return to prior local vocabularies. |
| `platform/python-sidecar/brahmagyan/l0_semantic_release.py` (new) | Strict Python adapter and release validator; no database or chart dependency. | Remove module and revert adapter import. |
| `platform/python-sidecar/brahmagyan/l0_resource_config_slice_v1.json` (new) | Immutable `L0-SLICE-RESOURCE-CONFIG-01` object/fixture package, with honest source gap. | Remove package; historical map remains unchanged. |
| `platform/python-sidecar/brahmagyan/l0_resource_config_slice.py` (new) | Fail-closed schema, grain, state, rights and global-scope validator. | Remove module; no stored rows to migrate. |
| `platform/python-sidecar/brahmagyan/graha_vocabulary.py` | Derive known aliases from the release, expose strict resolver, preserve permissive legacy wrapper, stop folding explicit true nodes into mean nodes. | Revert file; no persisted ID rewrite. |
| `platform/src/lib/retrieval/graha_labels.ts` | Version-pinned TypeScript release adapter with the same aliases, physical variants and strict unknown behavior. | Revert file; existing public names remain compatible. |
| `platform/src/lib/jyotish/bhavat_bhavam_map.ts` | Preserve exact 12-key map while attaching release, method, restraint and qualification metadata. | Revert adapter; map values stay identical. |
| `platform/src/lib/jyotish/__tests__/bhavat_bhavam_map.test.ts` | Durable TS detector for map invariants, release parity, physical variants and negative states. | Revert tests. |
| `platform/python-sidecar/tests/test_l0_semantic_release.py` (new) | Python identity, alias, ambiguity, unknown and physical-variant detector. | Remove test. |
| `platform/python-sidecar/tests/test_l0_resource_config_slice.py` (new) | Qualification, rights, grain, forbidden-scope, boundary, duplication, omission and rollback detector. | Remove test. |
| `platform/python-sidecar/routers/ephemeris.py` | Add producer-owned service context and serialized Swiss-state handling; correct Ketu to the same signed angular speed as antipodal Rahu. | Revert response metadata/validation/speed correction; no persisted row rewrite. |
| `platform/python-sidecar/pipeline/orchestrator/service_probes.py` | Reuse existing backend/file verification as detector-backed service context. | Revert metadata addition. |
| `platform/python-sidecar/tests/test_ephemeris_ayanamsha.py` | Context, precision, backend and unsupported-convention negative fixtures. | Revert tests. |
| `platform/python-sidecar/routers/panchang.py` | Reject incomplete location tuples and expose timezone/sunrise/computation context; preserve engine. | Revert validation/metadata. |
| `platform/python-sidecar/tests/test_panchanga_get.py` | Location/timezone boundary and honest-failure fixtures. | Revert tests. |
| `platform/python-sidecar/pipeline/orchestrator/writers/bg_gochara_arcs.py` | If focused proof confirms it, stop deleting compatible historical substrate versions. | Revert scoped delete change. |
| `platform/python-sidecar/brahmagyan/l0_kp_sublord_division.py` | If focused proof confirms it, preserve prior table versions instead of cross-version deletion. | Revert scoped delete change. |
| `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_primitives.py` | If parity proof confirms it, add the existing TS-only Vastu discovery primitive with restriction metadata. | Revert row; writer upsert returns to prior mirror. |
| `platform/src/lib/vidhi/registry_data.ts` | Attach L0 release/qualification/restriction metadata only if the existing compiler accepts it without consumer change. | Revert metadata. |
| `platform/scripts/census/check_vidhi_registry_parity.mjs` | Remove a parity exception only if both authoritative mirrors become exact. | Revert gate. |
| `platform/scripts/census/__tests__/vidhi_parity_gate.test.ts` | Negative parity fixture if the exception is removed. | Revert test. |
| Eight `MADHAV_DATA_PLANE_L0_*_v1_0.md` records named by the execution brief | Required versioned producer contracts and evidence; no rival registry. | Revert local documentation commit. |
| `MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md` | Record the actual L0 terminal receipt and withheld states. | Revert ledger row. |

No migration is admitted: the first slice is an immutable producer object, and no
queryable persistence need has been proved. Existing migrations are immutable.

## 3. Complete 40-identity current-state and terminal target

Legend: `P` preserve, `I` integrate into the producer contract, `E` enrich/correct,
`Q` qualify/limit, `H` retain restricted/historical. `generated` means identity and
digest are present in the pinned generated inventory; it is not runtime health.

| # | Identity | Implementation / owned data or service | Current evidence and actual boundary | Terminal disposition |
|---:|---|---|---|---|
| 1 | `bg_ontology` | `writers/bg_ontology.py` -> `brahmagyan/l0_ontology.py`; `brahma_ontology` | Generated; seed owns stable concepts/aliases but has no release, ambiguity or physical-variant envelope. | P/I/E/Q: retain rows; make ontology the identity owner through release adapters. |
| 2 | `bg_reference` | `writers/bg_reference.py` -> `l0_reference.py`; typed Brahmagyan reference tables | Generated; specialized semantics depend on ontology; missing IDs currently warn rather than create lexical authority. | P/I/E/Q: bind semantics to released IDs; do not revive duplicate nakshatra seeding. |
| 3 | `bg_nakshatra` | `writers/bg_nakshatra.py` -> `l0_nakshatra.py`; nakshatra/pada reference | Generated; static geometry/reference producer. | P/I/Q: preserve 27/28 system and scope; integration remains later L1 proof. |
| 4 | `bg_dignity_reference` | `writers/bg_dignity_reference.py`; dignity/friendship/avastha/combustion tables | Generated; distinct orb/retrograde meanings conflict with formula/L1 conventions. | P/I/E/Q: publish named variants and unresolved conflict; no blind replacement. |
| 5 | `bg_formula_constants` | `writers/bg_formula_constants.py` -> `l0_formula_constants.py`; formula constants | Generated; current natural-key upsert can overwrite meaning and observed values differ from L1. | P/I/E/Q: qualify units/meaning/source/consumer in contract; do not change L1. |
| 6 | `bg_dasha_systems` | `writers/bg_dasha_systems.py` -> `l0_dasha_systems.py`; dasha catalog | Generated; catalog presence does not prove executable/applicable method. | P/I/E/Q: expose catalogued/executable/applicable distinction. |
| 7 | `bg_kp_sublord_division` | `writers/bg_kp_sublord_division.py` -> `l0_kp_sublord_division.py`; versioned sign-cut geometry | Generated; depends on nakshatra and currently deletes earlier table versions. | P/I/Q: pin convention and preserve compatible generations. |
| 8 | `bg_texts` | `writers/bg_texts.py` -> `l0_texts.py`; texts/chunks/source manifest | Generated; held works have object/edition/license metadata, but no admitted exact Bhavat passage for the fixed scope. | P/I/E/Q: preserve corpus and rights evidence; exact passage identity required. |
| 9 | `bg_text_index` | `writers/bg_text_index.py`; topic/tag discovery over text chunks | Generated; ranking/navigation only. | P/I/E/Q: expose misses and hydration path; never testimony. |
| 10 | `bg_compendium_index` | `writers/bg_compendium_index.py`; chapter/topic navigation | Generated; synopsis/navigation is not passage authority. | P/I/E/Q: preserve source links and mechanical status. |
| 11 | `bg_rules` | `writers/bg_rules.py` -> `l0_rules.py`; `sutravali_rules` | Generated; regex/extraction score lacks edition/rights/ancestry/operator qualification. | P/I/E/Q: qualification overlay; preserve extracted rows and confidence meaning. |
| 12 | `bg_yogas` | `writers/bg_yogas.py` -> `l0_yogas.py`; yoga definitions | Generated; formation labels/citations do not by themselves prove occurrence or stronger interpretation. | P/I/E/Q: clause/prerequisite/failed/cancellation/variant contract. |
| 13 | `bg_doshas` | `writers/bg_doshas.py` -> `l0_doshas.py`; dosha catalog | Generated; attributed definitions require exception and safe-framing limits. | P/I/E/Q: preserve; prohibit inevitable-harm semantics. |
| 14 | `bg_concordance` | `writers/bg_concordance.py`; source/topic/school navigation | Generated; empty chunk IDs, text-level rule aggregation and abundance-derived confidence are not passage agreement. | P/I/E/Q: retain navigation; exact ancestry stays unqualified until linked. |
| 15 | `bg_remedies` | `writers/bg_remedies.py`; remedy corpus/review queue | Generated; allowlist/review/contraindication capital exists but efficacy is not established. | P/I/E/Q/H: attributed, voluntary, burden/contraindication and purpose restriction. |
| 16 | `bg_ghatana` | `writers/bg_ghatana.py` -> `l0_ghatana.py`; event/state/activity vocabulary | Generated; global vocabulary, not observation storage. | P/I/E/Q: stable criteria/chain shapes; no private evidence. |
| 17 | `bg_prashna_rules` | `writers/bg_prashna_rules.py` -> `l0_prashna.py`; method rules | Generated; method prerequisites and question-moment scope not uniformly qualified. | P/I/E/Q: preserve method-native outputs and unsupported states. |
| 18 | `bg_parihara_rules` | `writers/bg_parihara_rules.py`; cancellation/activity/census tables | Generated; factor status exists but source/application and absence states need qualification. | P/I/E/Q: distinguish absent, unavailable and inapplicable. |
| 19 | `bg_vastu_directions` | `writers/bg_vastu_directions.py` -> `l0_vastu_directions.py`; direction/remedial tables | Generated; traditional research capital can read prescriptively without explicit purpose envelope. | P/Q/H: retain attributed research only; no spatial service/horizon activation. |
| 20 | `bg_medical_mappings` | shared `writers/bg_medical_mappings.py` -> `l0_medical.py`; graha/body/dosa mapping | Generated; code states non-diagnostic intent but row shape lacks purpose/restriction version. | P/Q/H: traditional testimony only; no diagnosis or individual prediction. |
| 21 | `bg_nakshatra_medical` | co-owned by medical writer; nakshatra/body mapping | Generated with shared digest; distinct table semantics. | P/Q/H: same restriction and source qualification. |
| 22 | `bg_sign_medical` | co-owned by medical writer; rasi/body mapping | Generated with shared digest; distinct table semantics. | P/Q/H: same restriction and source qualification. |
| 23 | `bg_ephemeris` | `writers/bg_ephemeris.py`; `ephemeris_daily` | Generated; global noon-UT tropical daily samples, mean nodes, 1900-2150, verified file/backend, but stored rows lack full service generation context. | P/I/E/Q: state sample/frame/resolution/generation/interpolation limits. |
| 24 | `bg_gochara_arcs` | `writers/bg_gochara_arcs.py`; monotone longitude arcs | Generated; search substrate has bounds/version but writer removes prior substrate generations. | P/I/E/Q: preserve history and exact-refinement contract. |
| 25 | `bg_sky_calendar` | `writers/bg_sky_calendar.py`; `bg_sky_calendar` | Generated; deterministic ingress/station/eclipse/conjunction geometry with versioning gaps. | P/I/E/Q: separate geometry, visibility and personal relevance; retain precision. |
| 26 | `bg_muhurta_lattice` | `writers/bg_muhurta_lattice.py`; lattice/factor tables | Generated; fixed reference location and sunrise-midpoint approximation are disclosed in code. | P/I/E/Q: carry location, timezone, precision, provenance and horizon. |
| 27 | `bg_transit_engine` | non-writer identity registered to transit writer/service substrate | Generated writer identity shares digest/implementation with transit rules; average motion is not arbitrary-instant observation. | P/I/E/Q: keep mean-motion substrate separately typed and unqualified for precision. |
| 28 | `bg_transit_rules` | `writers/bg_transit_rules.py` -> `l0_transit.py`; attributed transit rules | Generated; rules lack complete method/frame/exception/executable envelope. | P/I/E/Q: preserve rule/native-reference scope; no probability meaning. |
| 29 | `bg_kota_chakra_rings` | `writers/bg_kota_chakra_rings.py` -> `l0_kota_chakra_rings.py`; ring geometry | Generated; pure reference data. | P/I/Q: preserve school/version and require actual geometry at later integration. |
| 30 | `bg_vedha_malefic_scale` | shared `writers/bg_phaladeepika_vedha.py`; obstruction scale | Generated with shared digest. | P/I/E/Q: separate obstruction scale from contact/probability; root-aware support. |
| 31 | `bg_phaladeepika_latta` | shared `writers/bg_phaladeepika_vedha.py`; latta rules | Generated with shared digest. | P/I/E/Q: preserve distinct rule/source family. |
| 32 | `bg_class_priors` | `writers/bg_class_priors.py` -> `l0_class_priors.py`; typed priors | Generated; reference coordinate, not personal probability. | P/I/E/Q: type unit/population/source/method and restrict purpose. |
| 33 | `bg_class_lifetime_counts` | `writers/bg_class_lifetime_counts.py`; count/incidence rows | Generated; shared-table placement does not merge semantic authority. | P/I/E/Q: preserve population/source/horizon and skip missing classes honestly. |
| 34 | `bg_cohort` | `writers/bg_cohort.py`; synthetic cohort and dasha chains | Generated; explicitly synthetic engineering population; generation key omits some method version inputs. | P/I/Q/H: label synthetic and preserve generation context; never human validation. |
| 35 | `bg_vidhi_primitives` | `writers/bg_vidhi_primitives.py`; `vidhi_primitives`; TS registry mirror | Generated; parity gate currently allowlists a TS-only Vastu primitive. | P/I/E/Q: exact versioned parity if safely attainable; discovery is not truth. |
| 36 | `bg_vidhi_floors` | `writers/bg_vidhi_floors.py`; floor/item tables | Generated; floors are mutable current minima rather than historical release authority. | P/I/E/Q: publish release/gap boundary; remain expandable minima. |
| 37 | `bg_ephemeris_engine` | `routers/ephemeris.py`, service probes, numerical backend | Generated non-writer; arbitrary-instant service supports multiple ayanamshas but response omits full frame/node/backend/precision/generation context. | P/I/E/Q: add fail-closed service context; no chart or personal meaning. |
| 38 | `bg_panchanga` | `routers/panchang.py`, `panchang_engine/**` | Generated non-writer; rich internal context exists, but router permits incomplete coordinate/timezone defaults. | P/I/E/Q: strict date/place/timezone/sunrise convention and failure. |
| 39 | `bg_gochara_citation_resolution` | migration-owned citation resolver | Generated non-writer; migration retains unresolved cases but lacks generation; citation resolution is not qualification. | P/I/E/Q: preserve unresolved state; do not edit historical migration or promote it. |
| 40 | `bg_sarvatobhadra_grid` | migration-owned school/version geometry | Generated non-writer; checked-in admission intentionally has zero rows because school/source conflict is unresolved. | P/I/Q/H: retain `EMPTY_BY_DESIGN`/contested receipt; no inferred availability. |

## 4. Gap classification and demand boundary

| Gap class | Confirmed examples | L0 action |
|---|---|---|
| Absent admitted source | No exact passage + edition/translation + existing rights pin for fixed Bhavat odd-house scope | `UNQUALIFIED_SOURCE`; positive fixture `NOT_REACHABLE`. |
| Unqualified semantics | Dignity/combustion constants; text-level concordance; transit/method rules | Named variants or explicit unresolved qualification; preserve rows. |
| Wrong mapping | Explicit true lunar nodes fold to mean in Python and are absent in TS | Correct release adapters; bare legacy Rahu/Ketu remain explicit mean defaults. |
| Computation/context | Service responses omit context; partial Panchanga coordinates can default silently | Add context and fail-closed input validation without changing kernels. |
| Serving/integration | D8 blanket absence and D9/L2 narrower implementation coexist | Record read-only demand; do not edit L2/retrieval or claim integration. |
| Operation | Current aggregate population/service health unavailable in this checkout | Keep rung `unavailable`; do not infer health from source or historical receipts. |
| Unproven value | No authorized user/empirical exercise | Compare only against the legacy representation as a prevented-error fixture. |

Adjacent answer authorities remain read-only: L1 facts/configurations, L2
interpretation/amplification, L3-L5 temporal/manifestation/evaluation, retrieval
catalog/ranking, Pariprashna, synthesis, MCP and persistence/export. Their presence
establishes downstream demand only. `INTEGRATED`, served, consumer-value and
empirical states are not reached by WP0.

## 5. Preservation gates

- no identity is retired, renamed or removed;
- no historical source row, map value, rule row, reading, forecast or receipt is
  rewritten;
- no generic citation is promoted into an exact witness;
- no existing migration is edited and no database rebuild is run;
- frozen orchestrator ownership, WriterBase and upsert/idempotency contracts remain
  unchanged;
- source rights, safety, consent and restricted-capital authority do not expand;
- the exact odd/even map, no-generation/no-chain/no-outrank restraints remain
  invariant; and
- L1 remains `WAITING_FOR_STRATEGIC_BRIEF`.
