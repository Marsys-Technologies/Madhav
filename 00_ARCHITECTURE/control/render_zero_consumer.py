#!/usr/bin/env python3
"""Render ZERO_CONSUMER_EVIDENCE_v1_0.md. Numbers come from the JSON artefacts; the prose
per asset is this KĀRAKA's reading of that evidence, and is labelled as such."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
M = json.loads((ROOT / '00_ARCHITECTURE/control/CONSUMER_MAP.json').read_text())
Z = json.loads((ROOT / '00_ARCHITECTURE/control/zero_consumer_evidence.json').read_text())
A, ZA = M['assets'], Z['assets']

# absence_reading vocabulary — deliberately three-valued
R_INPUT = ('**INPUT-ONLY** — consumed, but by writers rather than by a served surface. '
           'The absence of a serving consumer is what the asset is for, not a defect.')
R_NONE = ('**NO CONSUMER FOUND** — no writer, no surface, no capability, no view. The absence '
          'looks real on this evidence.')
R_BLIND = ('**METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot '
           'see. Recorded as UNKNOWN, not as zero.')
R_SHADOW = ('**SHADOWED** — a served surface carrying this asset\'s name exists, but the code '
            'behind it does not read this asset. The name and the data path have come apart.')
R_DESIGN = ('**BY DESIGN EMPTY / CATEGORY MISMATCH** — the consumer question as posed does not '
            'apply to this row in its current form.')

P = {
'bg_cohort': dict(
 produces='10,000 synthetic reference charts (sign/nakshatra grain) as a statistical base-rate population. Floor 10,000, measured 10,000 — met.',
 plausible='A rarity / base-rate serving surface — "how unusual is this configuration". No such capability is registered.',
 reading=R_INPUT,
 notes=['The one detected reader is `ka_kshetra`, and the registry itself declares `ka_kshetra` as the downstream dependent — code and catalogue agree.',
        '`platform/python-sidecar/services/ka_kshetra/cohort_client.py:171` — `FROM bg_synthetic_cohort`; also `:317`, `:322`, `:346` (denominator/numerator counts) and `writer.py:2146`.']),
'bg_concordance': dict(
 produces='Cross-school chunk-pointer index per (topic, school) in `classical_attributions`. Floor 800, measured 720 — 90 % of floor.',
 plausible='A classical-attribution lookup capability. One exists by name — `classical_attribution_lookup` (`platform/src/lib/contract/tool_metadata.ts:923`) — but it does not query this table.',
 reading=R_NONE + ' A prior serving path is documented as deliberately retired.',
 notes=['`platform/src/lib/router/retrieval_capability_spec.ts:406` states verbatim: "L8 — classical_attributions/classical_chunks/classical_texts retired WS-0; stub returns …". That is the code\'s own record of a retirement, not an inference.',
        'Zero read-context matches for `classical_attributions` anywhere under `platform/src`, `platform-mcp/src` or the sidecar routers/services. The only SQL statements are in its own writer and in `platform/scripts/m9/run_coverage_audit.py` (an audit script).',
        'No view or SQL function in the live DB references the table.']),
'bg_ephemeris_engine': dict(
 produces='Nothing of its own — the registry row describes the Swiss Ephemeris / pyswisseph engine plus the DE441 kernel. No `target_table`; census S2 finds no production writer.',
 plausible='Everything that computes a position. The declared API `swisseph.calc_ut` — matched on its last token `calc_ut` — occurs in 24 non-test files, one of which is a surface (`platform/src/app/api/chat/spike/route.ts`). Token occurrence, not a proven call.',
 reading=R_DESIGN + ' This row registers a third-party engine dependency as an asset; "which surface reads its table" has no referent.',
 notes=['Its single `asset_throughput` row is in state `error` (2026-06-18) and it is the only L0 asset in that state.']),
'bg_gochara_arcs': dict(
 produces='34,553 chart-independent graha-longitude arc rows over the 1900–2150 ephemeris epoch. Floor 34,553, measured 34,553 — met.',
 plausible='A gochara/transit surface. Those exist in quantity, but they read `kala_gochara_windows` (the materialized per-chart product), never the arc substrate.',
 reading=R_INPUT,
 notes=['Declared downstream dependent `ka_gochara`; detected writer consumer `ka_gochara`. Catalogue and code agree.',
        'Zero read-context matches under `platform/src` or `platform-mcp/src`.']),
'bg_kota_chakra_rings': dict(
 produces='27 Kota-Chakra ring-partition rows (stambha/durgantara/prakara/bahya). Floor 27, measured 27 — met.',
 plausible='A Kota-Chakra reading surface. `ka_kota_chakra` produces `kala_kota_chakra`, and that is what a surface would read.',
 reading=R_INPUT,
 notes=['`platform/python-sidecar/services/ka_kota_chakra/writer.py:89` — `FROM bg_kota_chakra_rings`, with `:90` selecting `MAX(table_version)`.',
        'Two unattributed statements remain, both in `platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py` (an older standalone builder that INSERTs into the table) — a second writer path, not a consumer.']),
'bg_kp_sublord_division': dict(
 produces='249 KP sub-lord division rows. Floor 249, measured 249 — met.',
 plausible='`ganita_kp_cusps_get`. It exists, and it reads `chart_facts` (`platform/src/lib/retrieval/registry/layers/L1_ganita/get_kp_cusps.ts:136`) — i.e. the derived per-chart facts, not this substrate.',
 reading=R_INPUT,
 notes=['`platform/python-sidecar/services/ka_kshetra/stage3_clocks.py:624` — `FROM bg_kp_sublord_division`; also consumed by `ga_nakshatra`.']),
'bg_panchanga': dict(
 produces='No table. The registry row declares the deterministic panchanga computation service, `provides_apis` naming `panchanga_instant(...)` and `panchanga_day(...)`.',
 plausible='The panchanga serving path. It exists and is live: `POST /api/compute/panchanga` (`platform/python-sidecar/routers/panchang.py:165`), reached from `platform/src/app/api/panchang/route.ts:33`, `platform/src/app/panchang/page.tsx:41`, the ICS feeds, the daily-refresh cron, and the `call_panchanga_service` capability.',
 reading=R_BLIND + ' The serving path is real; what this method cannot confirm is that the endpoint reaches *these* two named functions.',
 notes=['`routers/panchang.py` imports `compute_panchang` / `panchang_range` from `panchang_engine`, not the `panchanga_instant` / `panchanga_day` names the registry declares. Those two names are found in the corpus, but at `platform/python-sidecar/pipeline/orchestrator/service_probes.py:116/125` (the service probe) and in `writers/ph_muhurta.py`.',
        'That naming gap is an observation about the registry row, not a claim that the service is dead.']),
'bg_phaladeepika_latta': dict(
 produces='8 Lattā (obstruction-point) rows transcribed from Phaladeepika Adh. XXVI. Floor 8, measured 8 — met.',
 plausible='A vedha/gochara surface. One exists — `query_vedha_gochara` — and it names this table in its provenance comment while querying `kala_vedha_gochara` instead.',
 reading=R_INPUT,
 notes=['`platform/python-sidecar/services/ka_vedha_gochara/writer.py:123` — `FROM bg_phaladeepika_latta`.',
        'Named (not read) at `platform/src/lib/retrieval/registry/layers/L3_kala/query_vedha_gochara.ts:154` — the serving capability records its lineage back to this table.']),
'bg_reference': dict(
 produces='15 typed reference tables. Floor 1,485; the registry `count_sql` returns 1,242 (84 %). Largest members: `reference_topic_tags` 481, `reference_glossary` 364, `reference_yogas` 229, `reference_constants` 203.',
 plausible='The `ref_*` MCP tool family. Those tools exist and are live — but they read `reference_nakshatra` (SINGULAR, `bg_nakshatra`\'s table, `platform-mcp/src/tools/register_p1_reference.ts:534`), `brahma_yoga_catalog`, `brahma_dosha_catalog`, `bg_dignity_reference` and friends. Not one of the 15 `reference_*` tables in this asset has a read-context match anywhere in the serving corpora.',
 reading=R_INPUT + ' The reading is not "nothing uses it" — 14 L0/L1 writers do — but nothing *serves* it.',
 notes=['The near-collision `reference_nakshatra` (27 rows, `bg_nakshatra`, SERVED) vs `reference_nakshatras` (27 rows, `bg_reference`, not served) is a real hazard: the two names differ by one character and hold the same row count.',
        'Detected writer consumers: `ga_dashas`, `ga_sensitive`, `ga_nakshatra`, `ga_structural`, `ga_yoga`, `ga_ayurdaya`, `ga_sensitive_degree`, `bg_dasha_systems`, `bg_doshas`, `bg_yogas`, `bg_text_index`, `bg_concordance`, `bg_compendium_index`, `bo_pratijna`.',
        'The registry declares only `bg_compendium_index` and `ga_sensitive` as downstream dependents — the code shows 14. The dependency edge set is under-declared.']),
'bg_sarvatobhadra_grid': dict(
 produces='0 rows, and the registry says so on purpose: "registered DELIBERATELY EMPTY … SBC grid geometry varies by Jyotish tradition". Floor 0, measured 0.',
 plausible='A Sarvatobhadra-chakra surface — which cannot exist meaningfully until the table is populated.',
 reading=R_DESIGN,
 notes=['`platform/python-sidecar/services/ka_vedha_gochara/writer.py:115` — `FROM bg_sarvatobhadra_grid`; the consumer exists and reads zero rows.',
        'Named at `.../L3_kala/query_vedha_gochara.ts:26` in a comment about the empty school_tag.',
        'This is the census §"zero rows (by design)" specimen; the `volume_explanation` required by charter G4 is present.']),
'bg_sky_calendar': dict(
 produces='A chart-independent sky-event diary. Floor 31,064; the registry `count_sql` returns 31,059 — but the rows are in `bg_sky_calendar`, NOT in the `target_table` the registry names.',
 plausible='An eclipse / ingress / station surface, and `ka_gochara_v3_century_materialize` (the declared downstream dependent), whose W26 eclipse mechanism cites this table by name.',
 reading=R_BLIND + ' Two statements could not be attributed and the registry\'s own table pointer is broken, so a real reader may exist behind a name this scan did not follow.',
 notes=['**`target_table = bg_sky_events` does not exist in the live database.** It is the only asset of 128 whose `target_table` is neither a table nor a view (`information_schema` + `pg_class` both empty for that name). The real relation is `bg_sky_calendar` (31,059 rows), which is what `count_sql` actually counts.',
        'The two references found are prose in `platform/python-sidecar/services/gochara_v3/mechanisms/w26_real_eclipses.py:6` and `:27` ("actual eclipse events sourced from bg_sky_calendar") — the mechanism describes reading it; the SQL that would do so was not located by this scan.']),
'bg_vedha_malefic_scale': dict(
 produces='5 malefic-count → effect-grade rows from Phaladeepika Adh. XXVI PG353. Floor 5, measured 5 — met.',
 plausible='The vedha suppression grading in the gochara engine — which is exactly what reads it.',
 reading=R_INPUT,
 notes=['`platform/python-sidecar/services/gochara_v3/context.py:485` — `FROM bg_vedha_malefic_scale`, prefetched for "W1.3 suppression grading" (`context.py:101`); also `services/ka_vedha_gochara/writer.py:128`.',
        'Named at `.../L3_kala/query_vedha_gochara.ts:154`.']),
'bg_vidhi_floors': dict(
 produces='Per-intent-class floor rows in `vidhi_floor_items` — 286 rows live. Floor 11; last build wrote 77. Floor, live count and last write disagree three ways.',
 plausible='The vidhi/floor compiler and the MCP vidhi resource face.',
 reading=R_SHADOW,
 notes=['Both `platform/src/lib/vidhi/registry_data.ts` and `platform-mcp/src/resources/vidhi/registry_data.ts` hold the floors as TypeScript literals. The platform copy\'s own header says the DB is the runtime source ("at runtime (post V-2 wiring) the MCP resource face reads these rows from the DB (`vidhi_primitives` / `vidhi_intent_floors` / `vidhi_floor_items`, migration 440)"), but a read-context search for those three table names across `platform/src` and `platform-mcp/src` returns **no match**.',
        'This is an observation about what the scan can see, not a verdict on the V-2 wiring — a runtime read built by string concatenation would be invisible here. It is flagged precisely because the doc-comment and the greppable code disagree.']),
'bg_vidhi_primitives': dict(
 produces='Versioned vidhi primitive atoms in `vidhi_primitives` — 52 rows live. Floor 48; last build wrote 37.',
 plausible='Same as `bg_vidhi_floors`.',
 reading=R_SHADOW,
 notes=['Same TS-literal shadow: `registry_data.ts` in both packages carries the 52 primitives inline (its header: "52 versioned primitives"), with `live_tool` / `fallback_face` fields pointing at MCP tool names.',
        'The only SQL statements against `vidhi_primitives` are its own writer and two governance scripts.']),
'bo_cdlm_summary': dict(
 produces='Per-chart cross-domain linkage summary. `bodha_cdlm_chart_summary` holds 15 rows total, 5 on the native chart. Registry floor 1. A matview `mv_cdlm_static_summary` exists and holds 0 rows.',
 plausible='`query_cdlm_summary` — the capability exists (`.../L2_bodha/query_cdlm_summary.ts`) and its default tier is named `chart_summary`, but no read-context match for `bodha_cdlm_chart_summary` was found in it or anywhere else in the serving corpora.',
 reading=R_BLIND,
 notes=['**The 13 "writer consumers" reported for this asset are an artefact and should not be read as 13 readers.** Every one traces to the same line: `platform/python-sidecar/bodha_writers/_idempotency.py:190`, `DELETE FROM bodha_cdlm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s` — the shared §N.3 idempotency helper that all 13 bodha writers import. It is a delete, not a read.',
        'The matview `mv_cdlm_static_summary` is built on this table and is empty.']),
'bo_samskara': dict(
 produces='768-dim signal embeddings. `bodha_signal_embeddings` holds 150,081 rows total, 50,104 on the native chart against a floor of 60,000 (84 %).',
 plausible='A semantic/vector search surface over MSR signals.',
 reading=R_BLIND,
 notes=['`platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts:472` says in terms: "Full semantic-search path goes via bo_samskara/python-sidecar." That is the serving layer stating that the read happens on the far side of the sidecar HTTP boundary this method cannot cross.',
        'Registry declares `bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta` downstream; `ph_nimitta/engine.py:374` names "bodha_signal_embeddings precedent search" in a comment.',
        'As with `bo_cdlm_summary`, most of the 14 writer-consumer edges trace to the shared bodha idempotency helper — treat the count as an upper bound.']),
'ka_dasha_kala': dict(
 produces='No table; `asset_kind = service`; every `asset_throughput` row records `rows_written = 0` across all three charts. Registry floor 0.',
 plausible='`call_dasha_eligibility` — the capability exists and names this service in its header (`.../L3_kala/call_service_wrappers.ts:8`).',
 reading=R_SHADOW,
 notes=['That capability\'s handler does **not** call the service: it runs its own SQL, `FROM chart_dashas`, inside the TypeScript module. The python package `services/ka_dasha_kala/` (6 modules) is imported only by the `ka_sangam` writer and by `services/ph_nimitta/dasha_consensus.py`.',
        'Registry declares `ka_jivana_parva`, `ka_kshetra`, `ka_sangam` downstream; only `ka_sangam` is detected in code.']),
'ka_gochara_v3_century_materialize': dict(
 produces='`kala_gochara_windows_v2` — 1,938 rows total, 997 on the native chart. The registry `count_sql` (filtered to `generation LIKE \'g3_%\'`) returns 914. Registry floor 0. Its native throughput row is in state `error` (2026-08-21).',
 plausible='A gochara-window surface. Those read `kala_gochara_windows` (the v1/production relation), never the `_v2` staging surface.',
 reading=R_INPUT + ' The writer\'s own docstring calls `kala_gochara_windows_v2` a "calibration/staging surface", which is consistent with nothing serving it.',
 notes=['Named at `platform-mcp/src/tools/retrieval/register_gochara_windows.ts:588`, in a description of `kala_gochara_windows` — i.e. the serving tool names this writer while reading the other table.',
        'This is one of the 7 assets the plan itself annotates "No detected serving consumer (Phase 0.8c)".',
        'Charter P1 note: this asset sits next to the unrecoverable v1 gochara corpus. Nothing here touches it; this packet is read-only evidence.']),
'ka_graha_sancara': dict(
 produces='No table; `asset_kind = service`; `rows_written = 0`. Provides positions for 9 grahas at an arbitrary instant.',
 plausible='`POST /api/compute/ephemeris_at_t` — which exists (`platform/python-sidecar/routers/ephemeris.py:147`) and is called by the `call_ephemeris_at_t` capability (`call_service_wrappers.ts:219`).',
 reading=R_BLIND + ' A live serving path exists across the sidecar HTTP boundary; whether it reaches this asset\'s own package was not established.',
 notes=['`platform/python-sidecar/main.py:89-91` documents the wiring explicitly: "W2 dark-set wiring — ka_graha_sancara (GT-50) … Retrieval call_ephemeris_at_t capability calls /api/compute/ephemeris_at_t".',
        'Four writers import the package: `ka_sudarshana_varsha`, `ka_vedha_gochara`, `ka_kota_chakra`, `ka_moorti_nirnaya`.']),
'ka_kshetra': dict(
 produces='`kala_field` — **11,012,657 rows total, 8,599,775 on the native chart**. Registry floor 0. Native throughput row is `stale` (last build wrote 11,069,325 rows, 2026-08-15).',
 plausible='A temporal-field / hazard-rate surface. The MCP Kāla views know about it and report it as unavailable.',
 reading=R_BLIND,
 notes=['`platform-mcp/src/lib/kala_ritual_resonance.ts:19` carries the serving layer\'s own status line: "temporal_intensity | the field\'s λ — kala_field_windows | not_computed (field empty — ka_kshetra has written no rows; the N_e critical path)". `platform-mcp/src/tools/kala_views/ritual.ts:781` repeats it.',
        '**That serving-layer claim and the database disagree.** The relation the MCP layer names is `kala_field_windows`; the relation `ka_kshetra` writes is `kala_field`, which holds 8.6 M rows on the native chart. Whether `kala_field_windows` exists as a separate empty relation, or the name is simply wrong, is not settled by this packet — but "ka_kshetra has written no rows" is not true of `kala_field`.',
        'The only detected reader is the `mi_bhara` writer (`platform/python-sidecar/services/mi_bhara/db.py:87`, `:99`). Registry declares `mi_bhara` and `mi_sankalpa` downstream.',
        'This is the largest asset in the zero-serving set by three orders of magnitude, and therefore the most expensive one to get wrong in either direction.']),
'ka_muhurta_seva': dict(
 produces='No table; `asset_kind = service`; `rows_written = 0`.',
 plausible='`POST /api/compute/muhurta_score` — which exists (`platform/python-sidecar/routers/muhurta_score.py:72`) and is called by `call_muhurta_score` (`call_service_wrappers.ts:463`).',
 reading=R_SHADOW + ' A live endpoint named for this asset exists; the asset\'s own package is not on its path.',
 notes=['`routers/muhurta_score.py` imports `panchang_engine.muhurat` (`score_muhurat`, `EVENTS_MVP`), not `services/ka_muhurta_seva/`. Its own docstring says it "Reuses `panchang_engine.muhurat.score_muhurat()` … the SAME scoring primitive `ph_muhurta` calls internally, not a second scoring engine."',
        'The package `services/ka_muhurta_seva/` is imported only by the `ka_sangam` and `ka_vighnakara` writers.',
        'The same docstring records that the `call_muhurta_score` descriptor\'s event enum "never had a live caller (the handler unconditionally errored before this wave)" — the code\'s own account of a previously dead surface.']),
'ka_tulana': dict(
 produces='No table; `asset_kind = service`; `rows_written = 0` on all three charts. Registry describes it as a "Serve-time QT-4 ranking engine".',
 plausible='`kala_priority_ranking_get` / `pact_query` → `marsys://tool/L3/call_priority_ranking`. All three exist and are live MCP surfaces.',
 reading=R_SHADOW + ' This is the clearest specimen in the set.',
 notes=['`callPriorityRankingCapability` (`.../L3_kala/call_service_wrappers.ts:482`) describes itself as "(ka_tulana service)" and then does the ranking itself in SQL: `FROM bodha_msr_signals m` at `call_service_wrappers.ts:654`, with no `fetch()` anywhere after line 480 of that file — unlike its three sibling `call_*` wrappers, which do call `/api/compute/...` (`:138`, `:219`, `:463`).',
        '**No production module imports the `services/ka_tulana/` package** (4 modules: `__init__.py`, `ranker.py`, `writer.py`, plus the orchestrator writer). Zero non-test importers — not a surface, not another writer, not a script. The only importer found anywhere is its own unit test, `platform/python-sidecar/tests/l3/test_ka_tulana.py:8` (`from services.ka_tulana.ranker import ...`).',
        'A serve-time engine that nothing imports and that writes no rows is the one case in this set where both detectors return empty.']),
'mi_jivanaghatana': dict(
 produces='`mimamsa_event_provenance` — 64 rows, all on the native chart. Two views read it: `vw_mimamsa_admissible_clean` (51 rows) and `vw_mimamsa_held_out` (13 rows). Registry floor 0.',
 plausible='A calibration / held-out-evaluation surface, or the client learning tab.',
 reading=R_BLIND,
 notes=['`platform/src/app/api/clients/[id]/learning/route.ts:146` names the asset — but to TRIGGER it, not to read it: `void triggerProvenanceResync(chartId)` → `fetch(${sidecarUrl}/mimamsa/provenance-resync)` (`:160`). That is a write-side trigger across the sidecar boundary.',
        'Neither the base table nor either view has a read-context match in `platform/src`, `platform-mcp/src` or the sidecar routers.',
        'Detected writer consumers `mi_pramana` and `mi_pariksha` match the registry\'s declared downstream (`mi_bhavisya`, `mi_darshana`, `mi_pramana`) only partially.']),
}

L = []
w = L.append
w('# NIRMĀṆA M0-T6 (Phase 0.8c) — Zero-Consumer Evidence Packets')
w('')
w(f"**Generated:** {Z['_meta']['generated_at']}  ")
w('**Source of every number below:** `00_ARCHITECTURE/control/CONSUMER_MAP.json` and '
  '`00_ARCHITECTURE/control/zero_consumer_evidence.json` (both machine-generated, read-only DB).  ')
w('**Method and its limits:** `00_ARCHITECTURE/control/CONSUMER_MAP.md` §1–§2. Read them before '
  'acting on any packet here — several findings below exist *because* of a named method limit.  ')
w('**Status:** evidence only. **No disposition is proposed and none is taken.** Promote / retire / '
  'reclassify is ADHIKĀRIN\'s G1 power (charter §1), on this evidence. This document certifies '
  'nothing (I16 / charter H7).')
w('')
w('---')
w('')
w('## 0 — Reconciliation with the plan\'s "13"')
w('')
w('The plan states, in §1 (carried from v3.0 §1 and its Phase 0.8c row), that **13 assets have no '
  'detected consumer**. That figure was not re-derived here; it was checked, and it does not '
  'reconcile in either direction:')
w('')
w('- **The plan\'s own per-asset annotation names 7, not 13.** `grep -c "No detected serving '
  'consumer (Phase 0.8c)" 00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md` returns **7**: '
  '`bg_cohort`, `bg_concordance`, `bg_gochara_arcs`, `bg_kota_chakra_rings`, '
  '`bg_kp_sublord_division`, `bg_sky_calendar`, `ka_gochara_v3_century_materialize`. The same '
  'grep against `NIRMANA_ELEVATION_PLAN_v3_0.md` also returns 7. The summary figure 13 and the '
  'per-asset annotation count 7 disagree *inside the plan itself*.')
w(f"- **This pass finds {len(P)}**, by a method whose limits are written down. All 7 of the "
  'plan-annotated assets are in that set; the other 16 are additional.')
w('')
w('Neither figure is asserted here to be the right one. What is asserted is that the plan\'s 13 is '
  'not a checkable number as it stands — it has no per-asset list behind it — and that a '
  'disposition decision should rest on the per-asset packets below rather than on any headline '
  'count. (This mirrors the V-2 finding pattern: a plan figure that does not survive re-derivation.)')
w('')
w('## 1 — How to read a packet')
w('')
w('Each packet carries five things: what the asset produces (measured, not claimed), what a '
  'consumer would plausibly be, what was searched and not found, the live DB shape, and a '
  '**reading of the absence**. The reading is one of five values, kept apart on purpose because '
  'they call for different decisions:')
w('')
w('| reading | meaning |')
w('|---|---|')
w('| INPUT-ONLY | consumed by writers, not by a served surface. Absence of a serving consumer is the design. |')
w('| NO CONSUMER FOUND | no writer, no surface, no capability, no view. The absence looks real. |')
w('| METHOD-BLIND | a serving path plausibly exists that this method structurally cannot see. UNKNOWN, not zero. |')
w('| SHADOWED | a served surface carrying the asset\'s name exists, but the code behind it does not read the asset. |')
w('| BY DESIGN EMPTY / CATEGORY MISMATCH | the question as posed does not apply to the row in its current form. |')
w('')
w('The reading is **this KĀRAKA\'s reading of the cited evidence**, not a verdict and not a '
  'disposition. Every packet\'s evidence is quoted with a file:line or a query result so the '
  'reading can be overturned cheaply.')
w('')
w('## 2 — Summary')
w('')
w('| asset | layer | status | kind | evidence class | reading |')
w('|---|---|---|---|---|---|')
def short(r):
    return r.split('—')[0].replace('**', '').strip()
for a in sorted(P):
    v = A[a]
    w(f"| [`{a}`](#{a.replace('_', '-')}) | {v['layer'] or '—'} | {v['catalog_status']} | "
      f"{v['asset_kind'] or '—'} | {v['evidence_class']} | {short(P[a]['reading'])} |")
w('')
counts = {}
for a in P:
    counts[short(P[a]['reading'])] = counts.get(short(P[a]['reading']), 0) + 1
w('Reading distribution: ' + ' · '.join(f'**{k}** {n}' for k, n in sorted(counts.items(), key=lambda kv: -kv[1])) + '.')
w('')
w('## 3 — Packets')
w('')
for a in sorted(P):
    v, z, p = A[a], ZA[a], P[a]
    w(f'### {a}')
    w('')
    w(f"`{a}` — layer `{v['layer']}` · `{v['catalog_status']}` · `asset_kind={v['asset_kind']}` · "
      f"`is_active={v['is_active']}` · `scope={v['scope']}` · "
      f"target_table `{v['target_table'] or '(none)'}`")
    w('')
    w(f"**What it produces.** {p['produces']}")
    w('')
    if v['tables_scanned']:
        w('| relation | kind | total rows | rows on `482012f1` |')
        w('|---|---|--:|--:|')
        for t in v['tables_scanned']:
            i = z['tables'].get(t, {})
            w(f"| `{t}` | {i.get('relkind') or '**absent from the live DB**'} | "
              f"{i.get('total_rows') if i.get('total_rows') is not None else '—'} | "
              f"{i.get('rows_on_native_chart') if i.get('rows_on_native_chart') is not None else '—'} |")
        w('')
    w(f"**What would plausibly read it.** {p['plausible']}")
    w('')
    w('**What was searched, and what was not found.**')
    w('')
    w(f"- table-name scan: {v['reference_sites']} textual references, of which "
      f"{v['sql_context_reads']} read-context and {v['sql_context_writes']} write-context "
      f"statements; **{v['serving_consumer_count']} serving consumers**, "
      f"{v['writer_consumer_count']} writer consumers, "
      f"{v['unattributed_read_count']} unattributed.")
    ns = v['non_serving_references']
    if ns:
        w('- non-serving buckets: ' + ', '.join(f'`{k}` ×{x["count"]}' for k, x in sorted(ns.items())) + '.')
    im = v['asset_id_mentions']
    w(f"- asset-id name-mentions: {im['in_surface_files_count']} in surface files, "
      f"{im['in_capability_modules_count']} in capability modules, "
      f"{im['in_writers_count']} in writers, {im['in_scripts']} in scripts, "
      f"{im['in_other_modules']} in other modules.")
    if v['owning_code_module_count']:
        mc = v['module_import_consumers']
        w(f"- code-module detector: {v['owning_code_module_count']} owning modules; importers — "
          f"{len(mc['serving'])} surface, {len(mc['writers'])} writer "
          f"({', '.join('`%s`' % x for x in sorted(mc['writers'])) or 'none'}), "
          f"{mc['scripts_count']} script, {mc['other_modules_count']} other.")
    if v['db_view_indirection']:
        w('- DB view indirection: ' + ', '.join(f"`{d['view']}` (on `{d['base_table']}`)"
                                                for d in v['db_view_indirection']) + '.')
    else:
        w('- DB view indirection: no view or matview in the live database reads this asset\'s table(s).')
    if v['db_function_indirection']:
        w('- DB function indirection: ' + ', '.join(f'`{f}`' for f in v['db_function_indirection']) + '.')
    w('')
    w('**Evidence.**')
    w('')
    for n in p['notes']:
        w(f'- {n}')
    w('')
    tp = z['asset_throughput_rows']
    if tp:
        w('| throughput chart | state | rows_written | last_built_at |')
        w('|---|---|--:|---|')
        for r in tp:
            w(f"| {(r['chart_id'][:8] + '…') if r['chart_id'] else '(chart-independent)'} | "
              f"`{r['state']}` | {r['rows_written'] if r['rows_written'] is not None else '—'} | "
              f"{(r['last_built_at'] or '')[:19]} |")
        w('')
    w(f"**Registry-declared downstream dependents:** "
      f"{', '.join('`%s`' % x for x in z['declared_downstream_dependents']) or '_none_'}  ")
    w(f"**Registry `depends_on`:** {', '.join('`%s`' % x for x in (z['registry']['depends_on'] or [])) or '_none_'}")
    w('')
    w(f"**Reading of the absence.** {p['reading']}")
    w('')
    w('_No disposition proposed. G1 decision, on this evidence._')
    w('')
    w('---')
    w('')
w('## 4 — What these packets do NOT establish')
w('')
w('- They do not establish that any asset is unused. They establish what a documented static '
  'method found and did not find.')
w('- They do not settle any of the five SHADOWED / METHOD-BLIND cases. Each names the specific '
  'further check that would settle it (usually: exercise the endpoint, or read the sidecar side '
  'of an HTTP call).')
w('- They propose no promotion, retirement or reclassification, and they set no floor.')
w('- They certify nothing. Verification belongs to PARĪKṢAKA (I16); disposition to ADHIKĀRIN (G1).')
w('')

(ROOT / '00_ARCHITECTURE/control/ZERO_CONSUMER_EVIDENCE_v1_0.md').write_text('\n'.join(L) + '\n')
print('wrote ZERO_CONSUMER_EVIDENCE_v1_0.md;', len(P), 'packets')
