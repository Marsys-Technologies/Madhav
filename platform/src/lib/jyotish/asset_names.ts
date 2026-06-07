/**
 * asset_names.ts — Brahma 6-layer instrument asset catalog.
 *
 * SINGLE SOURCE OF TRUTH for Sanskrit names across cockpit, consume, and
 * form surfaces. Rebased from legacy 28-asset L1/L2.5/L3/L4 model to the
 * Brahma 6-layer model (L0 Brahmagyan → L5 Mīmāṃsā) per PART C rebase.
 *
 * Layer key:
 *   L0  → Brahmagyan  (Global Foundation)
 *   L1  → Ganita      (Chart Facts)
 *   L2  → Bodha       (Chart Intelligence)
 *   L3  → Kala        (Temporal Fabric)
 *   L4  → Phala       (Prediction)
 *   L5  → Mimamsa     (Learning)
 */

export interface AssetEntry {
  readonly sanskrit: string
  readonly english: string
  readonly subtitle: string
  readonly layer: 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'
}

export const ASSET_NAMES = {
  // ── L0 Brahmagyan — Global Foundation ────────────────────────────────────
  bg_ephemeris:    { sanskrit: 'Graha Sphuṭa',   english: 'Ephemeris',          subtitle: 'Swiss Ephemeris DE441 — raw astronomical positions', layer: 'L0' },
  bg_reference:    { sanskrit: 'Sāraṇī',         english: 'Reference Library',  subtitle: 'Planets, nakshatras, signs, aspects, vargas — classical constants', layer: 'L0' },
  bg_texts:        { sanskrit: 'Śāstrapāṭha',    english: 'Classical Texts',    subtitle: 'BPHS, Jaimini Sutram, KP Reader, Tajaka — verse chunks',           layer: 'L0' },
  bg_ontology:     { sanskrit: 'Nāmasaṃgraha',   english: 'Ontology',           subtitle: 'Canonical entity vocabulary + synonyms — resolve_entity source',   layer: 'L0' },
  bg_text_index:   { sanskrit: 'Śabdakośa',      english: 'Text Index',         subtitle: 'Hybrid retrieval — vector + lexical + rerank',                     layer: 'L0' },
  bg_rules:        { sanskrit: 'Sūtravālī',      english: 'Rule Base',          subtitle: 'Extracted classical rules, verse-traceable',                       layer: 'L0' },
  bg_remedies:     { sanskrit: 'Upāya-kośa',     english: 'Remedy Corpus',      subtitle: 'Mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic', layer: 'L0' },
  bg_concordance:  { sanskrit: 'Samanvaya',      english: 'Concordance',        subtitle: 'Cross-school agreement/divergence index — DORMANT placeholder',    layer: 'L0' },

  // ── L1 Gaṇita — Chart Facts ───────────────────────────────────────────────
  ga_engine:       { sanskrit: 'Gaṇanā',         english: 'Engine',            subtitle: 'PyJHora chart computation — all ayanamshas',        layer: 'L1' },
  ga_positions:    { sanskrit: 'Graha Sthāna',   english: 'Positions',         subtitle: 'Swiss Ephemeris — 9 grahas, sidereal/tropical',    layer: 'L1' },
  ga_divisionals:  { sanskrit: 'Varga',          english: 'Divisionals',       subtitle: 'D1 through D60 — all 28 vargas',                   layer: 'L1' },
  ga_dashas:       { sanskrit: 'Daśākrama',      english: 'Dasha Tree',        subtitle: 'Vimshottari MD / AD / PD — canonical PyJHora',     layer: 'L1' },
  ga_strength:     { sanskrit: 'Balatva',        english: 'Strength',          subtitle: 'Shadbala + ashtakavarga + bhava bala',             layer: 'L1' },
  ga_sensitive:    { sanskrit: 'Sūkṣmabindu',   english: 'Sensitive Points',  subtitle: 'Upagrahas, special lagnas, sahams, arudhas',       layer: 'L1' },
  ga_panchanga:    { sanskrit: 'Pañcāṅga Janma', english: 'Birth Panchanga',   subtitle: 'Tithi, vara, nakshatra, yoga, karana at birth',    layer: 'L1' },
  ga_facts_store:  { sanskrit: 'Tattvakośa',     english: 'Facts Store',       subtitle: 'Typed fact store — superset of FORENSIC v8.0',    layer: 'L1' },

  // ── L2 Bodha — Chart Intelligence ────────────────────────────────────────
  bo_signals:      { sanskrit: 'Lakṣaṇa',        english: 'Signals',           subtitle: 'MSR — 573 grounded signals with salience',         layer: 'L2' },
  bo_graph:        { sanskrit: 'Kāraṇajāla',     english: 'Signal Graph',      subtitle: 'CGM — valenced edges between signals',            layer: 'L2' },
  bo_domain_links: { sanskrit: 'Anubandha',      english: 'Domain Links',      subtitle: 'CDLM — cross-domain linkage matrix',              layer: 'L2' },
  bo_resonance:    { sanskrit: 'Anunāda',        english: 'Resonance',         subtitle: 'RM — resonance map across 6 traditions',          layer: 'L2' },
  bo_lenses:       { sanskrit: 'Dṛṣṭikośa',     english: 'Lenses',            subtitle: 'Concordance + contradiction + negative space',    layer: 'L2' },
  bo_remediation:  { sanskrit: 'Upāya',          english: 'Remediation',       subtitle: 'Contradiction hubs → cited L0 remedies',         layer: 'L2' },
  bo_embeddings:   { sanskrit: 'Saṃskāra',       english: 'Embeddings',        subtitle: 'Signal vectors for semantic retrieval',           layer: 'L2' },
  bo_holistic:     { sanskrit: 'Sampūrṇadṛṣṭi', english: 'Holistic Bundle',   subtitle: 'B.11 whole-chart-read — MSR+CGM+CDLM+RM',        layer: 'L2' },

  // ── L3 Kāla — Temporal Fabric ────────────────────────────────────────────
  ka_timeline:     { sanskrit: 'Kālasūtra',      english: 'Timeline',          subtitle: 'Dasha × transit alignment series',                layer: 'L3' },
  ka_convergence:  { sanskrit: 'Sangam',         english: 'Convergence',       subtitle: 'Measured convergence windows + constituent factors', layer: 'L3' },
  ka_obstruction:  { sanskrit: 'Vikṣepa',        english: 'Obstruction',       subtitle: 'Overlapping tension windows',                     layer: 'L3' },
  ka_temporal:     { sanskrit: 'Kālavyūha',      english: 'Temporal Bundle',   subtitle: 'Composite temporal fabric for a date range',      layer: 'L3' },

  // ── L4 Phala — Prediction ─────────────────────────────────────────────────
  ph_anchors:      { sanskrit: 'Nimitta',        english: 'Event Anchors',     subtitle: 'Falsifiable, probabilistic event predictions',    layer: 'L4' },
  ph_mitigation:   { sanskrit: 'Parihāra',       english: 'Mitigation',        subtitle: 'Mitigation map — L0/L2 remediation citations',   layer: 'L4' },
  ph_rectification:{ sanskrit: 'Sūkṣmasaṃśodhana', english: 'Rectification',  subtitle: 'Birth-time rectification with train/test split',  layer: 'L4' },
  ph_muhurta:      { sanskrit: 'Muhūrta',        english: 'Electional',        subtitle: 'Best windows for action — inverts Phala',        layer: 'L4' },
  ph_outlook:      { sanskrit: 'Bhavitavya',     english: 'Outlook',           subtitle: 'Predictive picture for a horizon',               layer: 'L4' },

  // ── L5 Mīmāṃsā — Learning ────────────────────────────────────────────────
  mi_lel_intake:   { sanskrit: 'Jīvanaghaṭanā',  english: 'Life Event Log',    subtitle: '57 events — held-out, isolated from generation',  layer: 'L5' },
  mi_ledger:       { sanskrit: 'Pratijñākoṣa',   english: 'Prediction Ledger', subtitle: 'Log before outcome — no leakage',               layer: 'L5' },
  mi_outcome:      { sanskrit: 'Phala Darpaṇa',  english: 'Outcome Record',    subtitle: 'Brier / calibration / timing scoring',          layer: 'L5' },
  mi_multiplier:   { sanskrit: 'Parivardhana',   english: 'Recalibration',     subtitle: 'Bounded learning multiplier [0.8, 1.2]',        layer: 'L5' },
  mi_research:     { sanskrit: 'Anusandhāna',    english: 'Research Export',   subtitle: 'L1/L2 → Parquet → BigQuery OLAP',               layer: 'L5' },
  mi_answer_quality:{ sanskrit: 'Pramāṇa',       english: 'Answer Quality',    subtitle: 'Golden Q&A eval — distinct from prediction',    layer: 'L5' },
} as const satisfies Record<string, AssetEntry>

export type AssetKey = keyof typeof ASSET_NAMES

export const LAYER_NAMES = {
  L0: { sanskrit: 'Brahmagyan', english: 'Foundation',   subtitle: 'Global' },
  L1: { sanskrit: 'Gaṇita',    english: 'Chart Facts',   subtitle: 'Computation' },
  L2: { sanskrit: 'Bodha',     english: 'Intelligence',  subtitle: 'Synthesis' },
  L3: { sanskrit: 'Kāla',      english: 'Temporal',      subtitle: 'Time fabric' },
  L4: { sanskrit: 'Phala',     english: 'Prediction',    subtitle: 'Ensemble' },
  L5: { sanskrit: 'Mīmāṃsā',  english: 'Learning',      subtitle: 'Calibration' },
} as const

export type LayerKey = keyof typeof LAYER_NAMES

/** Returns all asset keys for a layer in declaration order. */
export function assetsByLayer(layer: LayerKey): AssetKey[] {
  return (Object.keys(ASSET_NAMES) as AssetKey[]).filter(
    (k) => ASSET_NAMES[k].layer === layer,
  )
}

/** Human-readable "Sanskrit · English" label for a given key. */
export function assetLabel(key: AssetKey): string {
  const e = ASSET_NAMES[key]
  return `${e.sanskrit} · ${e.english}`
}
