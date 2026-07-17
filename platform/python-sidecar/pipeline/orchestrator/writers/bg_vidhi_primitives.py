"""
bg_vidhi_primitives writer — D-2 Lane V-1 (Vidhi registry + compiler).

Populates `vidhi_primitives` (migration 440) with the ~30-atom vidhi primitive
registry: definition, live-tool mapping + args, fallback face, known_gap CR
pointer, §B0.4 mandatory-surface tags, and CR-27 improvisation-corpus coverage.

This Python seed is a content mirror of `platform/src/lib/vidhi/registry_data.ts`
(VIDHI_PRIMITIVES) — the TS file is what the compiler and its tests read; this
writer is what makes the same data live in the DB for V-2's MCP-resource face.
The two are hand-synchronized by this lane (see registry_data.ts's header note).

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

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult

logger = logging.getLogger(__name__)

# Each tuple: (primitive_id, version, definition, category, live_tool, tool_args,
#              fallback_face, known_gap, mandatory_tags, cr27_prevents)
PRIMITIVE_ROWS: list[tuple] = [
    ("bhava_condition", 1,
     "Full condition of a bhava (house): occupants, lord, aspects received, dignity of occupants.",
     "structural", "ganita_structural_get", {"chart_id": "{chart_id}", "house": "{house}"},
     "ganita_chart_facts_get(category=bhava)", None, [], []),
    ("bhavesha_condition", 1,
     "Condition of a bhava's lord (bhaveśa): placement, dignity, strength, aspects on/from it.",
     "structural", "ganita_condition_get", {"chart_id": "{chart_id}", "house": "{house}", "mode": "lord"},
     "ganita_structural_get", None, [], []),
    ("karaka_condition", 1,
     "Condition of a significator graha (naisargika or chara karaka) for the domain in question.",
     "structural", "ganita_condition_get", {"chart_id": "{chart_id}", "karaka": "{karaka}", "mode": "karaka"},
     "ganita_strength_get", None, [], ["CR-36"]),
    ("from_moon_view", 1,
     "Chandra-lagna re-derivation of house/karaka reads (bhava reckoned from Moon, not just Lagna).",
     "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "reference_point": "moon"},
     "ganita_structural_get", None, [], []),
    ("varga_ratification", 1,
     "Compares D1 promise against operative-varga delivery per bhaveśa/karaka; fires when dignity flips.",
     "signal", "bodha_signals_get",
     {"chart_id": "{chart_id}", "signal_type_class": "varga_ratification_divergence"},
     "ganita_chart_facts_get(divisional_chart={varga})", None,
     ["varga_ratification_divergence"], ["CR-36"]),
    ("special_lagna_read", 1,
     "Reads special lagnas (Indu, Sree, Ghati, Hora, Bhava, etc.) with domain salience.",
     "structural", "ganita_special_lagnas_get", {"chart_id": "{chart_id}", "lagnas": "{lagnas}"},
     "query_special_lagnas", "CR-16", [], []),
    ("chara_karaka_read", 1,
     "Reads a chara karaka (e.g. Atmakaraka) placement and condition per Jaimini.",
     "structural", "ganita_condition_get",
     {"chart_id": "{chart_id}", "mode": "chara_karaka", "karaka": "{chara_karaka}"},
     "ganita_structural_get", None, [], []),
    ("dhana_yoga_scan", 1,
     "Scans the house-lord yoga family for the domain (dhana / raja / Budha-Aditya / Sarasvati / Lakshmi).",
     "doctrine", "ganita_yoga_firings_get",
     {"chart_id": "{chart_id}", "domain": "{domain}", "family": "house_lord"},
     "ganita_yogas_get", "CR-56", [], ["CR-27c"]),
    # D-2 gate fix (2026-07-17): route to the firings-authoritative surface. ganita_yoga_firings_get
    # serves neecha_bhanga_raja_yoga FIRED with bhanga_active + a per-varga grounds_jsonb ledger
    # (BPHS Ch.39) since D-1.6 S-3; the prior route (ganita_yogas_get catalog face) does NOT evaluate
    # NBRY. known_gap CR-59 cleared: L1 detection is live; residual is L2 ranking/surfacing, not detection.
    ("nbry_scan", 1,
     "Nicha-Bhanga (debility cancellation) scan, per-varga (not D1-only).",
     "doctrine", "ganita_yoga_firings_get",
     {"chart_id": "{chart_id}", "bhanga_active": True},
     "ganita_condition_get", None, [], []),
    # D-2 gate fix (2026-07-17): dropped dead signal_type_class 'functional_lordship_link' (0 rows
    # on live) — it left this floor item empty. Now returns composite-ranked wealth signals
    # (adverse valence rows surface here); the derived Rahu-occupies-dhana MECHANISM is served by
    # fallback judgment_query.affliction_mechanisms (budget-trimmed to be floor-model-digestible).
    # known_gap CR-54 cleared: functional-lordship valence is LIVE (ga_vichara, DR-9) since D-2.
    ("wealth_loss_mechanism_scan", 1,
     "Scans functional-lordship links (dusthana/maraka/badhaka aspects) that constitute a loss mechanism.",
     "signal", "bodha_signals_get",
     {"chart_id": "{chart_id}", "domain": "{domain}"},
     "judgment_query", None, [], ["CR-27c"]),
    ("dasha_spine_lord_capability", 1,
     "Full dasha spine enriched with per-lord capability (shadbala percentile, house class, "
     "functional lordship, ratification factor, warning tier).",
     "temporal", "ganita_dasha_lord_capability_get", {"chart_id": "{chart_id}"},
     "ganita_dashas_get", None, ["dasha_lord_capability"], ["CR-36", "CR-27a"]),
    ("taranga_curve", 1,
     "Domain-scoped temporal window bundle (dasha x transit convolution); full convergence "
     "convolution is D-3 (Kala Taranga) scope — this primitive serves the pre-D-3 window bundle.",
     "temporal", "kala_temporal_bundle", {"chart_id": "{chart_id}", "domain": "{domain}"},
     "kala_windows_get", "CR-66", [], []),
    ("lel_retrodiction", 1,
     "Joins LEL events to the signal/mechanism they retrodictively confirm, served as "
     "confirmation only (never as prediction input).",
     "temporal", "lel_query", {"chart_id": "{chart_id}", "domain": "{domain}"},
     "mimamsa_lel_query", "CR-68", [], []),
    ("intervention_synthesis", 1,
     "Leverage-ranked remedy synthesis: domain load-bearing weight / capability, forward-weighted "
     "by dasha runway.",
     "remedy", "bodha_remedies_get", {"chart_id": "{chart_id}", "leverage_ranked": True},
     "get_remedies", "CR-69", [], ["CR-27b"]),

    ("positions_snapshot", 1,
     "Full natal position snapshot (rasi + degree + nakshatra + retrograde flags, all grahas).",
     "structural", "ganita_positions_get", {"chart_id": "{chart_id}"},
     "get_positions", None, [], []),
    ("dignity_scan", 1,
     "Per-graha dignity (exaltation/own/friend/neutral/enemy/debility) across the chart.",
     "strength", "ganita_condition_get", {"chart_id": "{chart_id}", "mode": "dignity"},
     "ganita_strength_get", None, [], []),
    ("shadbala_rank", 1,
     "Ranked shadbala (six-fold strength) across all grahas — authoritative strength ordering.",
     "strength", "ganita_strength_get", {"chart_id": "{chart_id}"},
     "bodha_chart_digest_get", None, [], []),
    ("nakshatra_semantics", 1,
     "Nakshatra-semantic layer per graha: own-star, dispositor chains, tara bala, end-degree flags.",
     "signal", "ganita_nakshatra_get", {"chart_id": "{chart_id}"},
     "bodha_signals_get(signal_type_class=nakshatra_semantic)", "CR-64", [], ["CR-27d"]),
    ("sensitive_degree_check", 1,
     "Sensitive-degree checks (mrityu-bhaga, gandanta, pushkara, kartari, 22nd drekkana) per graha.",
     "structural", "ganita_sensitive_degrees_get", {"chart_id": "{chart_id}"},
     "ganita_chart_facts_get", None, ["sensitive_degree"], []),
    ("divisional_facts", 1,
     "Divisional-chart (varga) fact set for a named varga, including D2 varga_hora_class "
     "(Surya/Chandra hora semantics).",
     "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "divisional_chart": "{varga}"},
     None, None, ["varga_hora_class"], []),
    ("dasha_window", 1,
     "Bounded dasha window query (level-scoped, natally enriched: lord house/dignity/shadbala).",
     "temporal", "ganita_dasha_periods_get",
     {"chart_id": "{chart_id}", "level": "{level}", "start": "{start}", "end": "{end}"},
     "ganita_dashas_get", None, [], []),
    ("yoga_activation_scan", 1,
     "Yoga activation by dasha — which catalog yogas are dated/active for the query horizon.",
     "temporal", "kala_yoga_activation_get", {"chart_id": "{chart_id}"},
     "yoga_activation_by_dasha", "CR-37", [], []),
    ("transit_window_scan", 1,
     "Gochara (transit) window scan for a bounded horizon.",
     "temporal", "kala_windows_get", {"chart_id": "{chart_id}", "start": "{start}", "end": "{end}"},
     "query_planet_transit", None, [], []),
    ("muhurta_scan", 1,
     "Muhurta window scan for an intervention/undertaking horizon.",
     "temporal", "kala_muhurta_get", {"chart_id": "{chart_id}", "start": "{start}", "end": "{end}"},
     "muhurta_finder", None, [], []),
    ("mechanism_read", 1,
     "Named, valenced CGM subgraph read — chain/circuit motifs (e.g. the 10->8->12->10 specimen).",
     "signal", "get_cgm_subgraph", {"chart_id": "{chart_id}"},
     "bodha_graph_subgraph_get", "CR-24", [], ["CR-27c"]),
    ("arudha_read", 1,
     "Arudha-semantic read: AL conjunctions, A2/A11 placement, AL-bhava relationships, ranked.",
     "signal", "ganita_condition_get", {"chart_id": "{chart_id}", "mode": "arudha"},
     "bodha_signals_get(frame=arudha)", "CR-61", [], []),
    ("dosha_scan", 1,
     "Per-chart bespoke dosha detection with cancellation/bhanga checks.",
     "doctrine", "ref_doshas_get", {"chart_id": "{chart_id}"},
     "bodha_signals_get(signal_type_class=dosha_label)", "CR-73", [], []),
    ("statistical_context", 1,
     "Within-chart statistical rarity / calibration context for a signal or verdict "
     "(L5 structural-mode).",
     "utility", "mimamsa_calibration_get", {"chart_id": "{chart_id}"},
     "bodha_quality_get", None, [], []),
    ("remedy_scan", 1,
     "Domain-scoped remedy scan joined to (weakest load-bearing graha x existing sadhana "
     "history x dasha runway).",
     "remedy", "bodha_remedies_search", {"chart_id": "{chart_id}", "domain": "{domain}"},
     "query_remedies_for_chart", "CR-67", [], ["CR-27b"]),
    ("contradiction_scan", 1,
     "Cross-signal contradiction/discovery scan.",
     "utility", "bodha_discoveries_get", {"chart_id": "{chart_id}"},
     "get_signals", None, [], []),

    ("chalit_cusp_read", 1,
     "Chalit (bhava-cuspal) chart facts: bhava_cusps, house_chalit, sandhi_flag.",
     "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "category": "chalit"},
     "ganita_structural_get", None, ["chalit_cusp"], []),
    ("sudarshana_agreement_check", 1,
     "Sudarshana-cakra tri-lagna (rasi/Chandra/Surya) agreement signal.",
     "signal", "bodha_signals_get",
     {"chart_id": "{chart_id}", "signal_type_class": "sudarshana_agreement"},
     "ganita_chart_facts_get", None, ["sudarshana_agreement"], []),
    ("bhavat_bhavam_check", 1,
     "Bhavat-bhavam (house-from-house) amplifier signal.",
     "signal", "bodha_signals_get",
     {"chart_id": "{chart_id}", "signal_type_class": "bhavat_bhavam_amplifier"},
     "ganita_structural_get", None, ["bhavat_bhavam"], []),
    ("bhava_bala_scan", 1,
     "Bhava-bala (house-strength) atoms per house (house_bhava_bala_total).",
     "strength", "ganita_strength_get", {"chart_id": "{chart_id}", "mode": "bhava_bala"},
     "ganita_structural_get", None, ["bhava_bala"], []),
    ("ashtakavarga_scan", 1,
     "Ashtakavarga bindu-sign scan (ashtakavarga_bindu_sign) per graha/house.",
     "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "category": "ashtakavarga"},
     "ganita_structural_get", None, ["ashtakavarga_bindu"], []),
    ("karakamsa_read", 1,
     "Karakamsa (Atmakaraka-in-D9) position read.",
     "structural", "ganita_condition_get", {"chart_id": "{chart_id}", "mode": "karakamsa"},
     "ganita_special_lagnas_get", None, ["karakamsa"], []),
    ("kp_cusp_sublord_read", 1,
     "Real KP cusps + sub-lords (bhava cuspal sub-lord chain per KP).",
     "structural", "ganita_chart_facts_get", {"chart_id": "{chart_id}", "category": "kp_cusps"},
     "ganita_structural_get", "CR-30", ["kp_cusp_sublord"], ["CR-36"]),
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
