"""
bg_vidhi_primitives writer — D-2 Lane V-1 (Vidhi registry + compiler).

Populates `vidhi_primitives` (migration 440) with the ~30-atom vidhi primitive
registry: definition, live-tool mapping + args, fallback face, known_gap CR
pointer, §B0.4 mandatory-surface tags, and CR-27 improvisation-corpus coverage.

This Python seed is a content mirror of `platform/src/lib/vidhi/registry_data.ts`
(VIDHI_PRIMITIVES) — the TS file is what the compiler and its tests read; this
writer is what makes the same data live in the DB for V-2's MCP-resource face.

PARIŚODHANA B2: PRIMITIVE_ROWS below was regenerated from the canonical TS registry
(52 primitives, incl. the Ω8 argala_read / dispositor_closure_read + the widened
special_lagna_read / ashtakavarga_scan) and is now held in lockstep with it by a CI
DRIFT GATE — platform/scripts/census/check_vidhi_registry_parity.mjs deep-compares the
`--dump-json` output of this writer against dump_vidhi_registry.ts. The previous "hand-
synchronized" note is retired: the gate, not hand-discipline, keeps the copies in sync.

§N.3: L0 idempotency — ON CONFLICT DO UPDATE (global, not per-chart).
§N.2: Frozen orchestrator contract — run(ctx) → WriterResult, never commits.

Every known_gap below cites only an OPEN or LOGGED CR per BRIEF_D2.md §B0.1 — see
platform/src/lib/vidhi/cr_status.ts for the allowlist and the documented CR-55
status conflict (BRIEF §B0.1 says CLOSED; the register body text still reads
OPEN — ELEVATED as of this lane's read). No primitive below cites CR-55.
"""
from __future__ import annotations

import json
import logging
import time

try:
    from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
except ImportError:  # PARIŚODHANA B2: standalone `--dump-json` (parity gate) — no orchestrator on path.
    # Minimal stand-ins so the module still loads and the writer class still DEFINES when run as a
    # script for the parity gate. `from __future__ import annotations` (above) makes the run(ctx)
    # annotations lazy strings, so ContextSpec/WriterResult are never evaluated in dump mode, and
    # run() itself is never called. Under the orchestrator the real import always succeeds and these
    # fallbacks are unused — the FROZEN WriterBase contract (§N.2) is unchanged.
    def register(_asset_id):  # type: ignore[misc]
        def _wrap(cls):
            return cls
        return _wrap

    class WriterBase:  # type: ignore[no-redef]
        pass

    ContextSpec = object  # type: ignore[assignment,misc]
    WriterResult = object  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Each tuple: (primitive_id, version, definition, category, live_tool, tool_args,
#              fallback_face, known_gap, mandatory_tags, cr27_prevents)
PRIMITIVE_ROWS: list[tuple] = [
    ("argala_read", 1, "Argala (intervention) + virodha-argala matrix per varga for a house/point — the natal argala_natal_matrix, virodha_argala_natal_matrix, and net_argala_per_varga (intervention structure on the bhāvas). A structural sweep, not a single-fact read.", "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "category": "net_argala_per_varga"}, "ganita_structural_get", None, [], []),
    ("arudha_read", 1, "Arudha-semantic read: AL conjunctions, A2/A11 placement, AL–bhāva relationships, ranked.", "signal", "ganita_condition_get", {"chart_id": "{chart_id}", "mode": "arudha"}, "bodha_signals_get(frame=arudha)", None, [], []),
    ("ashtakavarga_scan", 1, "Full Ashtakavarga family scan (per-varga bindu / bindu-sign / pinda / shodhana / kakshya) per graha/house — not D1-only.", "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "category": "ashtakavarga"}, "ganita_structural_get", None, ["ashtakavarga_bindu"], []),
    ("ayurdaya_read", 1, "Classical longevity (Āyurdāya) computation: Piṇḍa/Aṃśa/Naisarga āyus totals + longevity band (alpāyu/madhyāyu/pūrṇāyu), applicable_method, and the maraka grahas — a longevity-band + maraka-load read, NOT a death prediction.", "doctrine", "ganita_ayurdaya_get", {"chart_id": "{chart_id}"}, None, None, [], []),
    ("bhava_bala_scan", 1, "Bhāva-bala (house-strength) atoms per house (house_bhava_bala_total).", "strength", "ganita_strength_get", {"chart_id": "{chart_id}", "mode": "bhava_bala"}, "ganita_structural_get", None, ["bhava_bala"], []),
    ("bhava_condition", 1, "Full condition of a bhava (house): occupants, lord, aspects received, dignity of occupants.", "structural", "ganita_structural_get", {"chart_id": "{chart_id}", "house": "{house}"}, "ganita_chart_facts_get(category=bhava)", None, [], []),
    ("bhavat_bhavam_check", 1, "Bhāvāt-bhāvam (house-from-house) amplifier signal.", "signal", "bodha_signals_get", {"chart_id": "{chart_id}", "signal_type_class": "bhavat_bhavam_amplifier"}, "ganita_structural_get", None, ["bhavat_bhavam"], []),
    ("bhavesha_condition", 1, "Condition of a bhava’s lord (bhāveśa): placement, dignity, strength, aspects on/from it.", "structural", "ganita_condition_get", {"chart_id": "{chart_id}", "house": "{house}", "mode": "lord"}, "ganita_structural_get", None, [], []),
    ("chalit_cusp_read", 1, "Chalit (bhāva-cuspal) chart facts: bhava_cusps, house_chalit, sandhi_flag.", "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "category": "chalit"}, "ganita_structural_get", None, ["chalit_cusp"], []),
    ("chara_karaka_read", 1, "Reads a chāra kāraka (e.g. Ātmakāraka) placement and condition per Jaimini.", "structural", "ganita_condition_get", {"chart_id": "{chart_id}", "mode": "chara_karaka", "karaka": "{chara_karaka}"}, "ganita_structural_get", None, [], []),
    ("chart_digest_read", 1, "Whole-chart UCD digest (bodha_chart_digest_get): msr_signal/yoga/dosha counts, contradiction_count, weakest_graha (shadbala-derived), composite-ranked entity_profiles (one row per graha and per BHAVA_1..12), convergence_domains, and top signals — the layered digest/rollup that leads the Pūrṇa-Ādhāra foundational floor.", "structural", "bodha_chart_digest_get", {"chart_id": "{chart_id}", "mode": "summary"}, "get_chart_orientation", None, [], []),
    ("contradiction_scan", 1, "Cross-signal contradiction/discovery scan.", "utility", "bodha_discoveries_get", {"chart_id": "{chart_id}"}, "bodha_signals_get", None, [], []),
    ("cross_ayanamsha_variation", 1, "Cross-ayanamsha agreement for a planet/point: dignity, bhāva-shift, and vargottama deltas computed across the 5 REAL ayanamshas (INVARIANT sentinel excluded), emitting ayanamsha_agreement \"n/5\" as a confidence field. Full agreement compresses; disagreement surfaces as a rarity signal (EL-56 family-collapse-safe). The planner's only ayanamsha axis.", "signal", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "about": "{point}", "ayanamsha_axis": ["krishnamurti", "lahiri_chitrapaksha", "raman", "surya_siddhanta_classical", "true_chitra"]}, "ganita_chart_facts_get(ayanamsha_id={ayanamsha})", None, [], []),
    ("dasha_spine_lord_capability", 1, "Full daśā spine enriched with per-lord capability (shadbala percentile, house class, functional lordship, ratification factor, warning tier).", "temporal", "ganita_dasha_lord_capability_get", {"chart_id": "{chart_id}"}, "ganita_dashas_get", None, ["dasha_lord_capability"], ["CR-36", "CR-27a"]),
    ("dasha_window", 1, "Bounded daśā window query (level-scoped, natally enriched: lord house/dignity/shadbala).", "temporal", "ganita_dasha_periods_get", {"chart_id": "{chart_id}", "level": "{level}", "start": "{start}", "end": "{end}"}, "ganita_dashas_get", None, [], []),
    ("dhana_yoga_scan", 1, "Scans the house-lord yoga family for the domain (dhana / raja / Budha-Āditya / Sarasvatī / Lakṣmī).", "doctrine", "ganita_yoga_firings_get", {"chart_id": "{chart_id}", "domain": "{domain}", "family": "house_lord"}, "ganita_yogas_get", None, [], ["CR-27c"]),
    ("dignity_scan", 1, "Per-graha dignity (exaltation/own/friend/neutral/enemy/debility) across the chart.", "strength", "ganita_condition_get", {"chart_id": "{chart_id}", "mode": "dignity"}, "ganita_strength_get", None, [], []),
    ("dispositor_closure_read", 1, "Full dispositor-chain closure: composite_dispositor_strength facts + the convergent- dispositor-chain / dispositor-cycle mechanism classes (the who-ultimately-controls-whom lordship closure across the chart).", "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "category": "composite_dispositor_strength"}, "bodha_mechanisms_get", None, [], []),
    ("divisional_facts", 1, "Divisional-chart (varga) fact set for a named varga, including D2 varga_hora_class (Surya/Chandra hora semantics).", "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "divisional_chart": "{varga}"}, None, None, ["varga_hora_class"], []),
    ("dosha_scan", 1, "Per-chart bespoke dosha detection with cancellation/bhaṅga checks.", "doctrine", "ref_doshas_get", {"chart_id": "{chart_id}"}, "bodha_signals_get(signal_type_class=dosha_label)", "CR-73", [], []),
    ("election_read", 1, "Gochara (D-5) election-avoidance view (gochara_election_avoidance_get): ADVERSE kala_gochara_windows to avoid for an undertaking, each carrying the full DR-16 payload (clarity_statement, probabilistic framing, falsifier, mitigation-paired BPHS remedy, confidence_disclosure). Bind when the question is an undertaking / timing / muhūrta ask.", "temporal", "gochara_election_avoidance_get", {"chart_id": "{chart_id}"}, "kala_muhurta_get", "CR-131", [], []),
    ("from_moon_view", 1, "Chandra-lagna re-derivation of house/karaka reads (bhāva reckoned from Moon, not just Lagna).", "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "reference_point": "moon"}, "ganita_structural_get", None, [], []),
    ("full_domain_dossier", 1, "Whole-domain gather-then-compose sweep: pages the domain's ENTIRE concept slice (all Ω1-inventory concepts) in budget-capped pages via the Ω5 `dossier` engine, structurally withholding every interpretive surface until coverage is 100% accounted (synthesis_gate OPEN). The planner's guaranteed route to FULL domain coverage — the atom-by-atom floor reads single facts; this reads the whole territory. Call it FIRST; follow `cursor` to exhaustion before composing. Flagship slices: {wealth, career} × the two canonical charts.", "utility", "dossier", {"domain": "{domain}", "chart_id": "{chart_id}", "budget_kb": 24}, None, None, [], []),
    ("gochara_activation_read", 1, "Gochara (D-5) activation view (gochara_activation_get): kala_gochara_windows rows ACTIVE on the current date — \"is this event-class configuration firing right now?\" over the signed λ_e intensity field, carrying the DR-16 honest-clarity + structural_prior envelope. Bind at horizon=current in every deepdive machine band.", "temporal", "gochara_activation_get", {"chart_id": "{chart_id}"}, "kala_windows_get", "CR-131", [], []),
    ("gochara_forecast_read", 1, "Gochara (D-5) forecast view (gochara_forecast_get): kala_gochara_windows overlapping a forward date range (point/interval/chain shapes, is_irreversibility_milestone flagged) over the signed λ_e field, DR-16-enveloped — the forward temporal spine. Bind where horizon=multi_year.", "temporal", "gochara_forecast_get", {"chart_id": "{chart_id}"}, "kala_windows_get", "CR-131", [], []),
    ("intervention_synthesis", 1, "Leverage-ranked remedy synthesis: domain load-bearing weight ÷ capability, forward-weighted by daśā runway.", "remedy", "bodha_remedies_get", {"chart_id": "{chart_id}", "leverage_ranked": True}, "bodha_remedies_get", None, [], ["CR-27b"]),
    ("karaka_condition", 1, "Condition of a significator graha (naisargika or chāra kāraka) for the domain in question.", "structural", "ganita_condition_get", {"chart_id": "{chart_id}", "karaka": "{karaka}", "mode": "karaka"}, "ganita_strength_get", None, [], ["CR-36"]),
    ("karakamsa_read", 1, "Karakāṃśa (Ātmakāraka-in-D9) position read.", "structural", "ganita_condition_get", {"chart_id": "{chart_id}", "mode": "karakamsa"}, "ganita_special_lagnas_get", None, ["karakamsa"], []),
    ("kp_cusp_sublord_read", 1, "Real KP cusps + sub-lords (bhāva cuspal sub-lord chain per KP).", "structural", "ganita_kp_cusps_get", {"chart_id": "{chart_id}"}, "ganita_chart_facts_get", None, ["kp_cusp_sublord"], ["CR-36"]),
    ("lel_retrodiction", 1, "Joins LEL events to the signal/mechanism they retrodictively confirm, served as confirmation only (never as prediction input).", "temporal", "mechanism_retrodiction_get", {"chart_id": "{chart_id}", "domain": "{domain}"}, "mimamsa_lel_query", None, [], []),
    ("mechanism_read", 1, "Named, valenced CGM subgraph read — chain/circuit motifs (e.g. the 10→8→12→10 specimen).", "signal", "bodha_mechanisms_get", {"chart_id": "{chart_id}"}, "bodha_graph_subgraph_get", None, [], ["CR-27c"]),
    ("medical_read", 1, "Vaidya-phala medical watch-indications per graha: dosha aggravated (vāta/pitta/kapha), organ_watch, body_part_watch, and indication tier, with BPHS Ch.18 / Aṣṭāṅga Hṛdayam citations. NOT a diagnosis — classical watch-indications only.", "structural", "ganita_medical_get", {"chart_id": "{chart_id}"}, "ref_sign_medical_get", None, [], []),
    ("muhurta_scan", 1, "Muhurta window scan for an intervention/undertaking horizon.", "temporal", "kala_muhurta_get", {"chart_id": "{chart_id}", "start": "{start}", "end": "{end}"}, "kala_muhurta_get", None, [], []),
    ("nakshatra_semantics", 1, "Nakshatra-semantic layer per graha: own-star, dispositor chains, tara bala, end-degree flags.", "signal", "ganita_nakshatra_get", {"chart_id": "{chart_id}"}, "bodha_signals_get(signal_type_class=nakshatra_semantic)", None, [], ["CR-27d"]),
    ("nbry_scan", 1, "Nīcha-Bhaṅga (debility cancellation) scan, per-varga (not D1-only).", "doctrine", "ganita_yoga_firings_get", {"chart_id": "{chart_id}", "bhanga_active": True}, "ganita_condition_get", None, [], []),
    ("positions_snapshot", 1, "Full natal position snapshot (rasi + degree + nakshatra + retrograde flags, all grahas).", "structural", "ganita_positions_get", {"chart_id": "{chart_id}"}, "ganita_positions_get", None, [], []),
    ("remedy_scan", 1, "Domain-scoped remedy scan joined to (weakest load-bearing graha × existing sādhana history × daśā runway).", "remedy", "bodha_remedies_get", {"chart_id": "{chart_id}", "domain": "{domain}"}, "ref_remedies_chart_get", None, [], ["CR-27b"]),
    ("sensitive_degree_check", 1, "Sensitive-degree checks (mrityu-bhaga, gandanta, pushkara, kartari, 22nd drekkana) per graha, plus the Yogi/Avayogi/Duplicate-Yogi/Sahayogi Tajika construct (fact_category=sensitive_point_yogi; MC-029, Śodhana Builder T6) — same tool, both categories served, distinguishable by fact_category.", "structural", "ganita_sensitive_degrees_get", {"chart_id": "{chart_id}"}, "ganita_chart_facts_get", None, ["sensitive_degree"], []),
    ("shadbala_rank", 1, "Ranked shadbala (six-fold strength) across all grahas — authoritative strength ordering.", "strength", "ganita_strength_get", {"chart_id": "{chart_id}"}, "bodha_chart_digest_get", None, [], []),
    ("special_lagna_read", 1, "Reads the FULL special-lagna + saham set — 7 special lagnas (Indu, Sree, Ghati, Hora, Bhava, Varnada, Vighati) + 70 sahams + Upapada — with domain salience.", "structural", "ganita_special_lagnas_get", {"chart_id": "{chart_id}"}, "ganita_special_lagnas_get", None, [], []),
    ("spiritual_yoga_scan", 1, "Scans the Jaimini spiritual/renunciate yoga family (pravrajyā, sannyāsa, tāpasa — 4+ grahas in one bhāva, Ketu/Saturn/12th-lord involvement) for the mokṣa domain.", "doctrine", "ganita_yoga_firings_get", {"chart_id": "{chart_id}", "domain": "spirituality", "family": "spiritual"}, "ganita_yogas_get", "CR-130", [], []),
    ("standing_predictions_read", 2, "Standing prospective-ledger read (standing_predictions_read → brahma_prospective_ledger): the OPEN filed, falsifiable predictions for the domain — each with claim, event_class, temporal shape + window/milestones, confidence, a MANDATORY FALSIFIER, generator_class (reading_synthesis | engine | native_intuition | anchor_engine) and source_citation. Non-domain-matching open predictions are still returned (other_domain_predictions) — never silently dropped. Makes every reading falsifier-bearing by default. Confirmation/disclosure ONLY — never a calibration or filing write (§11: predictions exist by explicit filing only).", "temporal", "standing_predictions_read", {"chart_id": "{chart_id}", "domain": "{domain}"}, "phala_predictive_anchors_get", None, [], []),
    ("statistical_context", 1, "Within-chart statistical rarity / calibration context for a signal or verdict (L5 structural-mode).", "utility", "mimamsa_calibration_get", {"chart_id": "{chart_id}"}, "bodha_quality_get", None, [], []),
    ("sudarshana_agreement_check", 1, "Sudarśana-cakra tri-lagna (rasi/Chandra/Sūrya) agreement signal.", "signal", "bodha_signals_get", {"chart_id": "{chart_id}", "signal_type_class": "sudarshana_agreement"}, "ganita_chart_facts_get", None, ["sudarshana_agreement"], []),
    ("tail_divergence_read", 1, "Tail-divergence read (synth_tail_divergence_get): the bottom-decile dissent/tail signals (BA-P4 70/20/10 attention budget) that contradict or diverge from the dominant synthesis — the rarity / \"where THIS chart departs from the typical\" surface the insight band mines for the non-obvious, beyond-acharya finding.", "signal", "synth_tail_divergence_get", {"chart_id": "{chart_id}", "domain": "{domain}"}, "bodha_discoveries_get", None, [], []),
    ("taranga_curve", 1, "Domain-scoped temporal window bundle (dasha × transit convolution) — full convergence convolution is D-3 (Kāla Taraṅga) scope; this primitive serves the pre-D-3 window bundle.", "temporal", "kala_bundle_get", {"chart_id": "{chart_id}", "domain": "{domain}"}, "kala_windows_get", "CR-66", [], []),
    ("transit_window_scan", 1, "Gochara (transit) window scan for a bounded horizon.", "temporal", "kala_windows_get", {"chart_id": "{chart_id}", "start": "{start}", "end": "{end}"}, "ref_planet_transit_get", None, [], []),
    ("upapada_read", 1, "Upapada Lagna (UL/UPA) read for the marriage/relationship domain: the UPA bhava-arudha position (sign + house) and Arudha A12 (ARUDHA_A12), plus the 2nd-from-UL bhāva as an answerer-side derivation off the UPA house (sustenance / longevity-of-union significator). Raw arudha positions are data-backed; salience ranking shipped (CR-61, see known_gap).", "signal", "ganita_condition_get", {"chart_id": "{chart_id}", "facet": "karakas"}, "bodha_signals_get(frame=arudha)", None, [], []),
    ("varga_ratification", 1, "Compares D1 promise against operative-varga delivery per bhāveśa/kāraka; fires when dignity flips.", "signal", "bodha_signals_get", {"chart_id": "{chart_id}", "signal_type_class": "varga_ratification_divergence"}, "ganita_chart_facts_get(divisional_chart={varga})", None, ["varga_ratification_divergence"], ["CR-36"]),
    ("wealth_loss_mechanism_scan", 1, "Scans functional-lordship links (dusthana/maraka/badhaka aspects) that constitute a loss mechanism.", "signal", "bodha_signals_get", {"chart_id": "{chart_id}", "domain": "{domain}"}, "judgment_query", None, [], ["CR-27c"]),
    ("yoga_activation_scan", 1, "Yoga activation by daśā — which catalog yogas are dated/active for the query horizon.", "temporal", "kala_yoga_activation_get", {"chart_id": "{chart_id}"}, "kala_yoga_activation_get", None, [], []),
    ("yoga_firings_read", 1, "Firings-authoritative yoga surface (ganita_yoga_firings_get): every FIRED yoga for the chart (dhana / raja / nīcha-bhaṅga / pañca-mahāpuruṣa / budha-āditya / sarasvatī …) with fire_reason, per-varga grounds and strength — the \"confirmed firings\" layer (never a catalog/label match) the whole-chart foundation reads.", "doctrine", "ganita_yoga_firings_get", {"chart_id": "{chart_id}"}, "ganita_yogas_get", None, [], []),
]


@register('bg_vidhi_primitives')
class VidhiPrimitivesWriter(WriterBase):
    asset_id = 'bg_vidhi_primitives'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(PRIMITIVE_ROWS),
                duration_seconds=time.time() - t0,
                notes=f"dry_run — would upsert {len(PRIMITIVE_ROWS)} vidhi_primitives rows",
            )

        with ctx.db_conn.cursor() as cur:
            upserted = 0
            for (pid, version, definition, category, live_tool, tool_args,
                 fallback_face, known_gap, mandatory_tags, cr27_prevents) in PRIMITIVE_ROWS:
                cur.execute(
                    """
                    INSERT INTO vidhi_primitives
                      (primitive_id, version, definition, category, live_tool, tool_args,
                       fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s::JSONB, %s, %s, %s, %s, now())
                    ON CONFLICT (primitive_id) DO UPDATE SET
                        version         = EXCLUDED.version,
                        definition      = EXCLUDED.definition,
                        category        = EXCLUDED.category,
                        live_tool       = EXCLUDED.live_tool,
                        tool_args       = EXCLUDED.tool_args,
                        fallback_face   = EXCLUDED.fallback_face,
                        known_gap       = EXCLUDED.known_gap,
                        mandatory_tags  = EXCLUDED.mandatory_tags,
                        cr27_prevents   = EXCLUDED.cr27_prevents,
                        updated_at      = now()
                    """,
                    (pid, version, definition, category, live_tool, json.dumps(tool_args),
                     fallback_face, known_gap, mandatory_tags, cr27_prevents),
                )
                upserted += 1

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=upserted,
            duration_seconds=time.time() - t0,
            notes=f"vidhi_primitives: {upserted} rows ({len(PRIMITIVE_ROWS)} defined atoms)",
        )


def _dump_json() -> None:
    """--dump-json: emit the primitives half of the canonical-normalized Vidhi registry for the
    parity gate (platform/scripts/census/check_vidhi_registry_parity.mjs). No DB needed — prints
    PRIMITIVE_ROWS as JSON in the SAME shape as platform/scripts/census/dump_vidhi_registry.ts's
    `primitives` array (sorted by primitive_id; keys sorted for a stable byte form)."""
    import json as _json
    prims = []
    for (pid, version, definition, category, live_tool, tool_args,
         fallback_face, known_gap, mandatory_tags, cr27_prevents) in PRIMITIVE_ROWS:
        prims.append({
            "primitive_id": pid, "version": version, "definition": definition,
            "category": category, "live_tool": live_tool, "tool_args": tool_args,
            "fallback_face": fallback_face, "known_gap": known_gap,
            "mandatory_tags": list(mandatory_tags), "cr27_prevents": list(cr27_prevents),
        })
    prims.sort(key=lambda p: p["primitive_id"])
    print(_json.dumps({"primitives": prims}, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    import sys
    if '--dump-json' in sys.argv:
        _dump_json()
    else:
        raise SystemExit(
            "bg_vidhi_primitives.py is an orchestrator writer; run it via the orchestrator. "
            "The only standalone entrypoint is `--dump-json` (used by the vidhi registry parity gate)."
        )
