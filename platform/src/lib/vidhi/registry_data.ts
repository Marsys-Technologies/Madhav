/**
 * Vidhi registry data — D-2 Lane V-1 (absorbed Track-3 authoring).
 *
 * 37 versioned primitives (design §3 targets "~30"; expanded here by 7 to guarantee full
 * §B0.4 mandatory-surface coverage + all four CR-27 improvisation instances + the CR-36
 * buried-evidence specimen are each prevented by a named floor item — see
 * `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/track3/` for the human-
 * readable source drafts this file mirrors 1:1) + 8 intent-class floors (acharya floor +
 * machine band each), matching the worked `floor(wealth_deepdive)` template in
 * DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3 verbatim for its 14 named atoms.
 *
 * SOURCE-OF-TRUTH NOTE: at runtime (post V-2 wiring) the MCP resource face reads these
 * rows from the DB (`vidhi_primitives` / `vidhi_intent_floors` / `vidhi_floor_items`,
 * migration 440, seeded by `bg_vidhi_primitives.py` / `bg_vidhi_floors.py`). This TS file
 * is V-1's own compiler-facing copy — authored to be identical in content to the DB seed
 * so the compiler is testable without a DB connection. The two are hand-synchronized by
 * this lane; V-2/V-3 should replace this file's primitives/floors constants with a real
 * DB read once the MCP resource face exists, keeping `compileContract`'s signature
 * unchanged (it already takes the registry as a parameter, not a global).
 *
 * Live-tool names verified against the deployed connector's tool catalog as surfaced to
 * this session (135 live tools per BIND context; `mcp__marsys-jis-direct__<name>` face).
 * Every `known_gap` cites only an OPEN or LOGGED CR per `cr_status.ts` — the registry
 * completeness test asserts this mechanically.
 */
import type { FloorItem, IntentFloor, VidhiPrimitive } from './types';

export const VIDHI_PRIMITIVES: readonly VidhiPrimitive[] = [
  // ── Structural / worked-example core (design §3 floor(wealth_deepdive) atoms 1-4, 6-7) ──
  {
    primitive_id: 'bhava_condition',
    version: 1,
    definition: 'Full condition of a bhava (house): occupants, lord, aspects received, dignity of occupants.',
    category: 'structural',
    live_tool: 'ganita_structural_get',
    tool_args: { chart_id: '{chart_id}', house: '{house}' },
    fallback_face: 'ganita_chart_facts_get(category=bhava)',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'bhavesha_condition',
    version: 1,
    definition: 'Condition of a bhava’s lord (bhāveśa): placement, dignity, strength, aspects on/from it.',
    category: 'structural',
    live_tool: 'ganita_condition_get',
    tool_args: { chart_id: '{chart_id}', house: '{house}', mode: 'lord' },
    fallback_face: 'ganita_structural_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'karaka_condition',
    version: 1,
    definition: 'Condition of a significator graha (naisargika or chāra kāraka) for the domain in question.',
    category: 'structural',
    live_tool: 'ganita_condition_get',
    tool_args: { chart_id: '{chart_id}', karaka: '{karaka}', mode: 'karaka' },
    fallback_face: 'ganita_strength_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: ['CR-36'],
  },
  {
    primitive_id: 'from_moon_view',
    version: 1,
    definition: 'Chandra-lagna re-derivation of house/karaka reads (bhāva reckoned from Moon, not just Lagna).',
    category: 'structural',
    live_tool: 'ganita_chart_facts_get',
    tool_args: { chart_id: '{chart_id}', reference_point: 'moon' },
    fallback_face: 'ganita_structural_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'varga_ratification',
    version: 1,
    definition: 'Compares D1 promise against operative-varga delivery per bhāveśa/kāraka; fires when dignity flips.',
    category: 'signal',
    live_tool: 'bodha_signals_get',
    tool_args: { chart_id: '{chart_id}', signal_type_class: 'varga_ratification_divergence' },
    fallback_face: 'ganita_chart_facts_get(divisional_chart={varga})',
    known_gap: null, // CR-57 CLOSED_WITH_EVIDENCE (D-1.6 S-7) — live per §F0.
    mandatory_tags: ['varga_ratification_divergence'],
    cr27_prevents: ['CR-36'],
  },
  {
    primitive_id: 'special_lagna_read',
    version: 1,
    definition: 'Reads special lagnas (Indu, Sree, Ghati, Hora, Bhava, etc.) with domain salience.',
    category: 'structural',
    live_tool: 'ganita_special_lagnas_get',
    tool_args: { chart_id: '{chart_id}', lagnas: '{lagnas}' },
    fallback_face: 'ganita_special_lagnas_get',
    known_gap: 'CR-16', // chart-keyed special-lagna access still OPEN (query_special_lagnas is BirthDataSchema-only)
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'chara_karaka_read',
    version: 1,
    definition: 'Reads a chāra kāraka (e.g. Ātmakāraka) placement and condition per Jaimini.',
    category: 'structural',
    live_tool: 'ganita_condition_get',
    tool_args: { chart_id: '{chart_id}', mode: 'chara_karaka', karaka: '{chara_karaka}' },
    fallback_face: 'ganita_structural_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'dhana_yoga_scan',
    version: 1,
    definition: 'Scans the house-lord yoga family for the domain (dhana / raja / Budha-Āditya / Sarasvatī / Lakṣmī).',
    category: 'doctrine',
    live_tool: 'ganita_yoga_firings_get',
    tool_args: { chart_id: '{chart_id}', domain: '{domain}', family: 'house_lord' },
    fallback_face: 'ganita_yogas_get',
    known_gap: 'CR-56', // house-lord yoga detector family absent — OPEN, ELEVATED (#1 acharya-grade blocker)
    mandatory_tags: [],
    cr27_prevents: ['CR-27c'],
  },
  {
    primitive_id: 'nbry_scan',
    version: 1,
    definition: 'Nīcha-Bhaṅga (debility cancellation) scan, per-varga (not D1-only).',
    category: 'doctrine',
    // D-2 gate fix (2026-07-17): routed to the firings-authoritative surface. ganita_yoga_firings_get
    // serves neecha_bhanga_raja_yoga FIRED with bhanga_active + a per-varga grounds_jsonb ledger
    // (BPHS Ch.39 rule-by-rule) since D-1.6 S-3. The prior route (ganita_yogas_get) is the catalog
    // face that does NOT evaluate NBRY — following it left the reading blind to the D9 cancellations.
    live_tool: 'ganita_yoga_firings_get',
    tool_args: { chart_id: '{chart_id}', bhanga_active: true },
    fallback_face: 'ganita_condition_get',
    known_gap: null, // CR-59 CORRECTED (D-2, 2026-07-17): L1 NBRY detector is LIVE (D9-scoped, grounds-carried) since D-1.6 S-3. Residual is L2 ranking/surfacing, not detection.
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'wealth_loss_mechanism_scan',
    version: 1,
    definition: 'Scans functional-lordship links (dusthana/maraka/badhaka aspects) that constitute a loss mechanism.',
    category: 'signal',
    // D-2 gate fix (2026-07-17): dropped the dead signal_type_class 'functional_lordship_link'
    // (0 rows on live) — it left this floor item empty and the reading blind to the adverse
    // wealth signals. Now returns the composite-ranked wealth signals (adverse valence rows —
    // e.g. Ketu→H2 major-malefic, Saturn→H9 chart-defining — surface here); the derived
    // graha-bhava-affliction MECHANISM (Rahu-occupies-dhana) is served by the fallback_face
    // judgment_query's affliction_mechanisms layer (now budget-trimmed to be floor-model-digestible).
    live_tool: 'bodha_signals_get',
    tool_args: { chart_id: '{chart_id}', domain: '{domain}' },
    fallback_face: 'judgment_query',
    known_gap: null, // CR-54 functional-lordship valence is LIVE (ga_vichara valence_pass, DR-9 doctrine) since D-2; residual taxonomy completeness tracked separately, not a route gap
    mandatory_tags: [],
    cr27_prevents: ['CR-27c'],
  },
  {
    primitive_id: 'dasha_spine_lord_capability',
    version: 1,
    definition: 'Full daśā spine enriched with per-lord capability (shadbala percentile, house class, functional lordship, ratification factor, warning tier).',
    category: 'temporal',
    live_tool: 'ganita_dasha_lord_capability_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'ganita_dashas_get',
    known_gap: null, // CR-60 CLOSED_WITH_EVIDENCE (D-1.6 S-7) — live per §F0.
    mandatory_tags: ['dasha_lord_capability'],
    // CR-27a ("4-call diff reading answered a fresh-reading question"): a compiled floor
    // that always includes the current daśā spine forces a fresh-state read regardless of
    // how the question was framed, closing the diff-vs-fresh ambiguity at the floor level.
    cr27_prevents: ['CR-36', 'CR-27a'],
  },
  {
    primitive_id: 'taranga_curve',
    version: 1,
    definition: 'Domain-scoped temporal window bundle (dasha × transit convolution) — full convergence convolution is D-3 (Kāla Taraṅga) scope; this primitive serves the pre-D-3 window bundle.',
    category: 'temporal',
    live_tool: 'kala_bundle_get',
    tool_args: { chart_id: '{chart_id}', domain: '{domain}' },
    fallback_face: 'kala_windows_get',
    known_gap: 'CR-66', // Phala wealth/domain anchors still zero — timing spine hand-assembled — OPEN, UPDATE evidence
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'lel_retrodiction',
    version: 1,
    definition: 'Joins LEL events to the signal/mechanism they retrodictively confirm, served as confirmation only (never as prediction input).',
    category: 'temporal',
    live_tool: 'mimamsa_lel_query',
    tool_args: { chart_id: '{chart_id}', domain: '{domain}' },
    fallback_face: 'mimamsa_lel_query',
    known_gap: 'CR-68', // mechanism_retrodiction surface absent — LEL walled off beyond prediction — OPEN
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'intervention_synthesis',
    version: 1,
    definition: 'Leverage-ranked remedy synthesis: domain load-bearing weight ÷ capability, forward-weighted by daśā runway.',
    category: 'remedy',
    live_tool: 'bodha_remedies_get',
    tool_args: { chart_id: '{chart_id}', leverage_ranked: true },
    fallback_face: 'bodha_remedies_get',
    known_gap: 'CR-69', // composite ranking has no leverage_index axis — OPEN
    mandatory_tags: [],
    cr27_prevents: ['CR-27b'],
  },

  // ── General-purpose primitives (non-wealth-specific; support other intent classes) ──
  {
    primitive_id: 'positions_snapshot',
    version: 1,
    definition: 'Full natal position snapshot (rasi + degree + nakshatra + retrograde flags, all grahas).',
    category: 'structural',
    live_tool: 'ganita_positions_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'ganita_positions_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'dignity_scan',
    version: 1,
    definition: 'Per-graha dignity (exaltation/own/friend/neutral/enemy/debility) across the chart.',
    category: 'strength',
    live_tool: 'ganita_condition_get',
    tool_args: { chart_id: '{chart_id}', mode: 'dignity' },
    fallback_face: 'ganita_strength_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'shadbala_rank',
    version: 1,
    definition: 'Ranked shadbala (six-fold strength) across all grahas — authoritative strength ordering.',
    category: 'strength',
    live_tool: 'ganita_strength_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'bodha_chart_digest_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'nakshatra_semantics',
    version: 1,
    definition: 'Nakshatra-semantic layer per graha: own-star, dispositor chains, tara bala, end-degree flags.',
    category: 'signal',
    live_tool: 'ganita_nakshatra_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'bodha_signals_get(signal_type_class=nakshatra_semantic)',
    known_gap: 'CR-64', // nakshatra semantics never rank — OPEN, UPDATE evidence
    mandatory_tags: [],
    cr27_prevents: ['CR-27d'],
  },
  {
    primitive_id: 'sensitive_degree_check',
    version: 1,
    definition: 'Sensitive-degree checks (mrityu-bhaga, gandanta, pushkara, kartari, 22nd drekkana) per graha.',
    category: 'structural',
    live_tool: 'ganita_sensitive_degrees_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'ganita_chart_facts_get',
    known_gap: null, // R-47 CLOSED — live.
    mandatory_tags: ['sensitive_degree'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'divisional_facts',
    version: 1,
    definition: 'Divisional-chart (varga) fact set for a named varga, including D2 varga_hora_class (Surya/Chandra hora semantics).',
    category: 'structural',
    live_tool: 'ganita_chart_facts_get',
    tool_args: { chart_id: '{chart_id}', divisional_chart: '{varga}' },
    fallback_face: null,
    known_gap: null, // CR-58 CLOSED_WITH_EVIDENCE (D-1.6 S-7) — varga_hora_class live.
    mandatory_tags: ['varga_hora_class'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'dasha_window',
    version: 1,
    definition: 'Bounded daśā window query (level-scoped, natally enriched: lord house/dignity/shadbala).',
    category: 'temporal',
    live_tool: 'ganita_dasha_periods_get',
    tool_args: { chart_id: '{chart_id}', level: '{level}', start: '{start}', end: '{end}' },
    fallback_face: 'ganita_dashas_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'yoga_activation_scan',
    version: 1,
    definition: 'Yoga activation by daśā — which catalog yogas are dated/active for the query horizon.',
    category: 'temporal',
    live_tool: 'kala_yoga_activation_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'kala_yoga_activation_get',
    known_gap: 'CR-37', // temporal stage empty — activation dates missing/undated — OPEN, UPDATE evidence
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'transit_window_scan',
    version: 1,
    definition: 'Gochara (transit) window scan for a bounded horizon.',
    category: 'temporal',
    live_tool: 'kala_windows_get',
    tool_args: { chart_id: '{chart_id}', start: '{start}', end: '{end}' },
    fallback_face: 'ref_planet_transit_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'muhurta_scan',
    version: 1,
    definition: 'Muhurta window scan for an intervention/undertaking horizon.',
    category: 'temporal',
    live_tool: 'kala_muhurta_get',
    tool_args: { chart_id: '{chart_id}', start: '{start}', end: '{end}' },
    fallback_face: 'kala_muhurta_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'mechanism_read',
    version: 1,
    definition: 'Named, valenced CGM subgraph read — chain/circuit motifs (e.g. the 10→8→12→10 specimen).',
    category: 'signal',
    live_tool: 'bodha_graph_subgraph_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'bodha_graph_subgraph_get',
    known_gap: 'CR-24', // chain/circuit motif not served as a first-class mechanism — OPEN
    mandatory_tags: [],
    cr27_prevents: ['CR-27c'],
  },
  {
    primitive_id: 'arudha_read',
    version: 1,
    definition: 'Arudha-semantic read: AL conjunctions, A2/A11 placement, AL–bhāva relationships, ranked.',
    category: 'signal',
    live_tool: 'ganita_condition_get',
    tool_args: { chart_id: '{chart_id}', mode: 'arudha' },
    fallback_face: 'bodha_signals_get(frame=arudha)',
    known_gap: 'CR-61', // arudha stored but never ranked — OPEN
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'dosha_scan',
    version: 1,
    definition: 'Per-chart bespoke dosha detection with cancellation/bhaṅga checks.',
    category: 'doctrine',
    live_tool: 'ref_doshas_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'bodha_signals_get(signal_type_class=dosha_label)',
    known_gap: 'CR-73', // bespoke detection + cancellation still narrowed-open post D-1.6 stub-half close
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'statistical_context',
    version: 1,
    definition: 'Within-chart statistical rarity / calibration context for a signal or verdict (L5 structural-mode).',
    category: 'utility',
    live_tool: 'mimamsa_calibration_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'bodha_quality_get',
    known_gap: null, // L5 sealed in STRUCTURAL mode by design — not a defect (CLAUDE.md §E).
    mandatory_tags: [],
    cr27_prevents: [],
  },
  {
    primitive_id: 'remedy_scan',
    version: 1,
    definition: 'Domain-scoped remedy scan joined to (weakest load-bearing graha × existing sādhana history × daśā runway).',
    category: 'remedy',
    live_tool: 'bodha_remedies_get',
    tool_args: { chart_id: '{chart_id}', domain: '{domain}' },
    fallback_face: 'ref_remedies_chart_get',
    known_gap: 'CR-67', // remedy engine contributes nothing to interventions today — OPEN, UPDATE evidence
    mandatory_tags: [],
    cr27_prevents: ['CR-27b'],
  },
  {
    primitive_id: 'contradiction_scan',
    version: 1,
    definition: 'Cross-signal contradiction/discovery scan.',
    category: 'utility',
    live_tool: 'bodha_discoveries_get',
    tool_args: { chart_id: '{chart_id}' },
    fallback_face: 'bodha_signals_get',
    known_gap: null,
    mandatory_tags: [],
    cr27_prevents: [],
  },

  // ── §B0.4 mandatory-surface primitives (D-1.5b/D-1.6 substrate deltas per §F0) ──
  {
    primitive_id: 'chalit_cusp_read',
    version: 1,
    definition: 'Chalit (bhāva-cuspal) chart facts: bhava_cusps, house_chalit, sandhi_flag.',
    category: 'structural',
    live_tool: 'ganita_chart_facts_get',
    tool_args: { chart_id: '{chart_id}', category: 'chalit' },
    fallback_face: 'ganita_structural_get',
    known_gap: null,
    mandatory_tags: ['chalit_cusp'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'sudarshana_agreement_check',
    version: 1,
    definition: 'Sudarśana-cakra tri-lagna (rasi/Chandra/Sūrya) agreement signal.',
    category: 'signal',
    live_tool: 'bodha_signals_get',
    tool_args: { chart_id: '{chart_id}', signal_type_class: 'sudarshana_agreement' },
    fallback_face: 'ganita_chart_facts_get',
    known_gap: null,
    mandatory_tags: ['sudarshana_agreement'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'bhavat_bhavam_check',
    version: 1,
    definition: 'Bhāvāt-bhāvam (house-from-house) amplifier signal.',
    category: 'signal',
    live_tool: 'bodha_signals_get',
    tool_args: { chart_id: '{chart_id}', signal_type_class: 'bhavat_bhavam_amplifier' },
    fallback_face: 'ganita_structural_get',
    known_gap: null,
    mandatory_tags: ['bhavat_bhavam'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'bhava_bala_scan',
    version: 1,
    definition: 'Bhāva-bala (house-strength) atoms per house (house_bhava_bala_total).',
    category: 'strength',
    live_tool: 'ganita_strength_get',
    tool_args: { chart_id: '{chart_id}', mode: 'bhava_bala' },
    fallback_face: 'ganita_structural_get',
    known_gap: null,
    mandatory_tags: ['bhava_bala'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'ashtakavarga_scan',
    version: 1,
    definition: 'Ashtakavarga bindu-sign scan (ashtakavarga_bindu_sign) per graha/house.',
    category: 'structural',
    live_tool: 'ganita_chart_facts_get',
    tool_args: { chart_id: '{chart_id}', category: 'ashtakavarga' },
    fallback_face: 'ganita_structural_get',
    known_gap: null,
    mandatory_tags: ['ashtakavarga_bindu'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'karakamsa_read',
    version: 1,
    definition: 'Karakāṃśa (Ātmakāraka-in-D9) position read.',
    category: 'structural',
    live_tool: 'ganita_condition_get',
    tool_args: { chart_id: '{chart_id}', mode: 'karakamsa' },
    fallback_face: 'ganita_special_lagnas_get',
    known_gap: null,
    mandatory_tags: ['karakamsa'],
    cr27_prevents: [],
  },
  {
    primitive_id: 'kp_cusp_sublord_read',
    version: 1,
    definition: 'Real KP cusps + sub-lords (bhāva cuspal sub-lord chain per KP).',
    category: 'structural',
    live_tool: 'ganita_chart_facts_get',
    tool_args: { chart_id: '{chart_id}', category: 'kp_cusps' },
    fallback_face: 'ganita_structural_get',
    known_gap: 'CR-30', // no dedicated MCP face for KP sub-lords yet — served via chart_facts category
                          // filter only; broad alias/capability-map dedup (CR-30) is the nearest open
                          // register pointer for "this primitive lacks a first-class face".
    mandatory_tags: ['kp_cusp_sublord'],
    cr27_prevents: ['CR-36'],
  },
] as const;

// ─────────────────────────────────────────────────────────────────────────────────────
// Floors
// ─────────────────────────────────────────────────────────────────────────────────────

/**
 * floor(wealth_deepdive) — matches DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3's worked example
 * verbatim for its 14 named atoms (items 1-14 below map 1:1 to the design doc's
 * bhava_condition(2) · bhavesha_condition(2) · karaka_condition(Jupiter) · from_moon_view ·
 * varga_ratification(D2,D9,D11) · special_lagna_read(Indu,Sree) · chara_karaka_read(AmK) ·
 * dhana_yoga_scan · nbry_scan(per-varga) · wealth_loss_mechanism_scan ·
 * dasha_spine+lord_capability · taranga_curve(wealth) · lel_retrodiction(wealth) ·
 * intervention_synthesis(leverage_ranked)); items 15+ are this lane's §B0.4-mandatory and
 * CR-27-corpus additions, making this floor a superset that alone satisfies every §B0.4
 * tag and every CR-27 instance for the gate's flagship (wealth) domain.
 */
const WEALTH_DEEPDIVE_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'bhava_condition', order: 1, band: 'acharya_floor', args_override: { house: 2 } },
  { primitive_id: 'bhavesha_condition', order: 2, band: 'acharya_floor', args_override: { house: 2 } },
  { primitive_id: 'karaka_condition', order: 3, band: 'acharya_floor', args_override: { karaka: 'jupiter' } },
  { primitive_id: 'from_moon_view', order: 4, band: 'acharya_floor' },
  { primitive_id: 'chalit_cusp_read', order: 5, band: 'acharya_floor' },
  { primitive_id: 'bhava_bala_scan', order: 6, band: 'acharya_floor' },
  { primitive_id: 'ashtakavarga_scan', order: 7, band: 'acharya_floor' },
  { primitive_id: 'sensitive_degree_check', order: 8, band: 'acharya_floor' },
  { primitive_id: 'divisional_facts', order: 9, band: 'acharya_floor', args_override: { varga: 'D2' } },
  {
    primitive_id: 'varga_ratification',
    order: 10,
    band: 'acharya_floor',
    args_override: { vargas: ['D2', 'D9', 'D11'] },
  },
  { primitive_id: 'karakamsa_read', order: 11, band: 'acharya_floor' },
  { primitive_id: 'kp_cusp_sublord_read', order: 12, band: 'acharya_floor' },
  {
    primitive_id: 'special_lagna_read',
    order: 13,
    band: 'acharya_floor',
    args_override: { lagnas: ['indu', 'sree'] },
  },
  { primitive_id: 'chara_karaka_read', order: 14, band: 'acharya_floor', args_override: { chara_karaka: 'AmK' } },
  { primitive_id: 'dhana_yoga_scan', order: 15, band: 'acharya_floor', args_override: { domain: 'wealth' } },
  { primitive_id: 'nbry_scan', order: 16, band: 'acharya_floor' },
  { primitive_id: 'wealth_loss_mechanism_scan', order: 17, band: 'acharya_floor', args_override: { domain: 'wealth' } },
  { primitive_id: 'sudarshana_agreement_check', order: 18, band: 'acharya_floor' },
  { primitive_id: 'bhavat_bhavam_check', order: 19, band: 'acharya_floor' },
  { primitive_id: 'nakshatra_semantics', order: 20, band: 'acharya_floor' },
  { primitive_id: 'mechanism_read', order: 21, band: 'acharya_floor' },
  { primitive_id: 'dasha_spine_lord_capability', order: 22, band: 'machine_band' },
  { primitive_id: 'taranga_curve', order: 23, band: 'machine_band', args_override: { domain: 'wealth' } },
  { primitive_id: 'lel_retrodiction', order: 24, band: 'machine_band', args_override: { domain: 'wealth' } },
  { primitive_id: 'statistical_context', order: 25, band: 'machine_band' },
  { primitive_id: 'intervention_synthesis', order: 26, band: 'machine_band' },
];

const CAREER_DEEPDIVE_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'bhava_condition', order: 1, band: 'acharya_floor', args_override: { house: 10 } },
  { primitive_id: 'bhavesha_condition', order: 2, band: 'acharya_floor', args_override: { house: 10 } },
  { primitive_id: 'karaka_condition', order: 3, band: 'acharya_floor', args_override: { karaka: 'sun' } },
  { primitive_id: 'divisional_facts', order: 4, band: 'acharya_floor', args_override: { varga: 'D10' } },
  { primitive_id: 'divisional_facts', order: 5, band: 'acharya_floor', args_override: { varga: 'D9' } },
  { primitive_id: 'varga_ratification', order: 6, band: 'acharya_floor', args_override: { vargas: ['D1', 'D9', 'D10'] } },
  // §B0.4 mandatory-surface floor-completeness additions (RETRIEVAL_PLANE_ELEVATION_PLAN §R-3.3):
  // brings career to the full §B0.4 tag set held by the flagship wealth floor.
  { primitive_id: 'chalit_cusp_read', order: 7, band: 'acharya_floor' },
  { primitive_id: 'bhava_bala_scan', order: 8, band: 'acharya_floor' },
  { primitive_id: 'ashtakavarga_scan', order: 9, band: 'acharya_floor' },
  { primitive_id: 'sensitive_degree_check', order: 10, band: 'acharya_floor' },
  { primitive_id: 'karakamsa_read', order: 11, band: 'acharya_floor' },
  { primitive_id: 'kp_cusp_sublord_read', order: 12, band: 'acharya_floor' },
  { primitive_id: 'sudarshana_agreement_check', order: 13, band: 'acharya_floor' },
  { primitive_id: 'bhavat_bhavam_check', order: 14, band: 'acharya_floor' },
  { primitive_id: 'dhana_yoga_scan', order: 15, band: 'acharya_floor', args_override: { domain: 'career', family: 'raja' } },
  { primitive_id: 'nakshatra_semantics', order: 16, band: 'acharya_floor' },
  { primitive_id: 'mechanism_read', order: 17, band: 'acharya_floor' },
  { primitive_id: 'dasha_spine_lord_capability', order: 18, band: 'machine_band' },
  { primitive_id: 'taranga_curve', order: 19, band: 'machine_band', args_override: { domain: 'career' } },
  { primitive_id: 'intervention_synthesis', order: 20, band: 'machine_band' },
];

const HEALTH_DEEPDIVE_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'bhava_condition', order: 1, band: 'acharya_floor', args_override: { house: 6 } },
  { primitive_id: 'bhavesha_condition', order: 2, band: 'acharya_floor', args_override: { house: 6 } },
  { primitive_id: 'karaka_condition', order: 3, band: 'acharya_floor', args_override: { karaka: 'mars' } },
  { primitive_id: 'dignity_scan', order: 4, band: 'acharya_floor' },
  { primitive_id: 'sensitive_degree_check', order: 5, band: 'acharya_floor' },
  { primitive_id: 'divisional_facts', order: 6, band: 'acharya_floor', args_override: { varga: 'D6' } },
  { primitive_id: 'dosha_scan', order: 7, band: 'acharya_floor' },
  // §B0.4 mandatory-surface floor-completeness additions (RETRIEVAL_PLANE_ELEVATION_PLAN §R-3.3):
  // brings health to the full §B0.4 tag set held by the flagship wealth floor.
  // varga_ratification carries the varga_ratification_divergence tag; D1/D6/D9 for roga vs. stamina delivery.
  { primitive_id: 'varga_ratification', order: 8, band: 'acharya_floor', args_override: { vargas: ['D1', 'D6', 'D9'] } },
  { primitive_id: 'chalit_cusp_read', order: 9, band: 'acharya_floor' },
  { primitive_id: 'bhava_bala_scan', order: 10, band: 'acharya_floor' },
  { primitive_id: 'ashtakavarga_scan', order: 11, band: 'acharya_floor' },
  { primitive_id: 'karakamsa_read', order: 12, band: 'acharya_floor' },
  { primitive_id: 'kp_cusp_sublord_read', order: 13, band: 'acharya_floor' },
  { primitive_id: 'sudarshana_agreement_check', order: 14, band: 'acharya_floor' },
  { primitive_id: 'bhavat_bhavam_check', order: 15, band: 'acharya_floor' },
  { primitive_id: 'dasha_spine_lord_capability', order: 16, band: 'machine_band' },
  { primitive_id: 'taranga_curve', order: 17, band: 'machine_band', args_override: { domain: 'health' } },
  { primitive_id: 'remedy_scan', order: 18, band: 'machine_band', args_override: { domain: 'health' } },
];

const MARRIAGE_DEEPDIVE_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'bhava_condition', order: 1, band: 'acharya_floor', args_override: { house: 7 } },
  { primitive_id: 'bhavesha_condition', order: 2, band: 'acharya_floor', args_override: { house: 7 } },
  { primitive_id: 'karaka_condition', order: 3, band: 'acharya_floor', args_override: { karaka: 'venus' } },
  { primitive_id: 'divisional_facts', order: 4, band: 'acharya_floor', args_override: { varga: 'D9' } },
  { primitive_id: 'varga_ratification', order: 5, band: 'acharya_floor', args_override: { vargas: ['D1', 'D9'] } },
  { primitive_id: 'dosha_scan', order: 6, band: 'acharya_floor' },
  { primitive_id: 'karakamsa_read', order: 7, band: 'acharya_floor' },
  // §B0.4 mandatory-surface floor-completeness additions (RETRIEVAL_PLANE_ELEVATION_PLAN §R-3.3):
  // brings marriage to the full §B0.4 tag set held by the flagship wealth floor.
  { primitive_id: 'chalit_cusp_read', order: 8, band: 'acharya_floor' },
  { primitive_id: 'bhava_bala_scan', order: 9, band: 'acharya_floor' },
  { primitive_id: 'ashtakavarga_scan', order: 10, band: 'acharya_floor' },
  { primitive_id: 'sensitive_degree_check', order: 11, band: 'acharya_floor' },
  { primitive_id: 'kp_cusp_sublord_read', order: 12, band: 'acharya_floor' },
  { primitive_id: 'sudarshana_agreement_check', order: 13, band: 'acharya_floor' },
  { primitive_id: 'bhavat_bhavam_check', order: 14, band: 'acharya_floor' },
  { primitive_id: 'dasha_spine_lord_capability', order: 15, band: 'machine_band' },
  { primitive_id: 'remedy_scan', order: 16, band: 'machine_band', args_override: { domain: 'marriage' } },
];

/** Narrow, structure-depth — "show me my D1" canonical example (design §3 §8). */
const STRUCTURE_READ_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'positions_snapshot', order: 1, band: 'acharya_floor' },
  { primitive_id: 'dignity_scan', order: 2, band: 'acharya_floor' },
  { primitive_id: 'shadbala_rank', order: 3, band: 'acharya_floor' },
  { primitive_id: 'chalit_cusp_read', order: 4, band: 'acharya_floor' },
  { primitive_id: 'bhava_bala_scan', order: 5, band: 'acharya_floor' },
];

/** Panoramic-breadth — "unleash my financial potential"-shaped wide sweep, domain-agnostic. */
const PANORAMIC_BREADTH_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'positions_snapshot', order: 1, band: 'acharya_floor' },
  { primitive_id: 'shadbala_rank', order: 2, band: 'acharya_floor' },
  { primitive_id: 'nakshatra_semantics', order: 3, band: 'acharya_floor' },
  { primitive_id: 'arudha_read', order: 4, band: 'acharya_floor' },
  { primitive_id: 'mechanism_read', order: 5, band: 'acharya_floor' },
  { primitive_id: 'contradiction_scan', order: 6, band: 'machine_band' },
  { primitive_id: 'statistical_context', order: 7, band: 'machine_band' },
  { primitive_id: 'dasha_spine_lord_capability', order: 8, band: 'machine_band' },
];

/** Retrieval-only — minimal, single-fact-shaped question (design §3 §8 canonical example). */
const RETRIEVAL_ONLY_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'positions_snapshot', order: 1, band: 'acharya_floor' },
];

/** General fallback for questions that don't cleanly map to a domain deepdive. */
const GENERAL_SYNTHESIS_ITEMS: readonly FloorItem[] = [
  { primitive_id: 'bhava_condition', order: 1, band: 'acharya_floor', args_override: { house: 1 } },
  { primitive_id: 'shadbala_rank', order: 2, band: 'acharya_floor' },
  { primitive_id: 'mechanism_read', order: 3, band: 'acharya_floor' },
  { primitive_id: 'dasha_spine_lord_capability', order: 4, band: 'machine_band' },
  { primitive_id: 'contradiction_scan', order: 5, band: 'machine_band' },
  { primitive_id: 'intervention_synthesis', order: 6, band: 'machine_band' },
];

export const VIDHI_INTENT_FLOORS: readonly IntentFloor[] = [
  {
    intent: 'wealth_deepdive',
    version: 1,
    floor_items: WEALTH_DEEPDIVE_ITEMS,
    cr27_coverage: ['CR-27a', 'CR-27b', 'CR-27c', 'CR-27d', 'CR-36'],
    notes: 'Flagship floor — worked example per DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3; §G master acceptance target.',
  },
  {
    intent: 'career_deepdive',
    version: 1,
    floor_items: CAREER_DEEPDIVE_ITEMS,
    cr27_coverage: ['CR-27c', 'CR-27d'],
    notes: 'D10/D9 multi-varga per CR-62’s wealth {D1,D2,D9,D11} / career {D1,D9,D10} map (design §12 lord-placement join).',
  },
  {
    intent: 'health_deepdive',
    version: 1,
    floor_items: HEALTH_DEEPDIVE_ITEMS,
    cr27_coverage: ['CR-27b'],
  },
  {
    intent: 'marriage_deepdive',
    version: 1,
    floor_items: MARRIAGE_DEEPDIVE_ITEMS,
    cr27_coverage: ['CR-27b'],
  },
  {
    intent: 'structure_read',
    version: 1,
    floor_items: STRUCTURE_READ_ITEMS,
    cr27_coverage: [],
    notes: 'Narrow/structure depth — the "show me my D1" canonical example; no machine band (deliberate).',
  },
  {
    intent: 'panoramic_breadth',
    version: 1,
    floor_items: PANORAMIC_BREADTH_ITEMS,
    cr27_coverage: ['CR-27a', 'CR-27c', 'CR-27d'],
    notes: 'The "unleash my financial potential"-shaped wide sweep — domain-agnostic breadth, not depth.',
  },
  {
    intent: 'retrieval_only',
    version: 1,
    floor_items: RETRIEVAL_ONLY_ITEMS,
    cr27_coverage: [],
  },
  {
    intent: 'general_synthesis',
    version: 1,
    floor_items: GENERAL_SYNTHESIS_ITEMS,
    cr27_coverage: ['CR-27a'],
  },
];
