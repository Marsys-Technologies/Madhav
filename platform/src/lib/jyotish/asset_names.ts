/**
 * asset_names.ts — canonical Sanskrit name map for all 28 build assets.
 *
 * SINGLE SOURCE OF TRUTH for Sanskrit names across cockpit, consume, and
 * form surfaces. Never inline Sanskrit strings elsewhere — always import
 * from here. Created by Stream C, C-S1.
 *
 * Layer key:
 *   L1    → Adhara      (Foundation)
 *   L2_5  → Sambandha   (Synthesis)
 *   L3    → Sutra       (Meta-threads)
 *   L4    → Vyavahara   (Interface)
 */

export interface AssetEntry {
  readonly sanskrit: string
  readonly english: string
  readonly subtitle: string
  readonly layer: 'L1' | 'L2_5' | 'L3' | 'L4'
}

export const ASSET_NAMES = {
  // ── Adhara · L1 · Foundation ──────────────────────────────────────────────
  pratyaksha:        { sanskrit: 'Pratyaksha',        english: 'Direct perception',      subtitle: 'Forensic chart',                   layer: 'L1'   },
  panchanga:         { sanskrit: 'Panchanga',         english: 'Five limbs',              subtitle: 'Daily almanac',                    layer: 'L1'   },
  drishti_lakshana:  { sanskrit: 'Drishti Lakshana',  english: 'Sensitive points',        subtitle: 'ARMC, ASC, Vertex',                layer: 'L1'   },
  graha_sthana:      { sanskrit: 'Graha Sthana',      english: 'Planet positions',        subtitle: 'Across ayanamshas',                layer: 'L1'   },
  bhava_vibhaga:     { sanskrit: 'Bhava Vibhaga',     english: 'House divisions',         subtitle: 'Cusps + lords',                    layer: 'L1'   },
  varga:             { sanskrit: 'Varga',             english: 'Divisional charts',       subtitle: 'D1 through D60',                   layer: 'L1'   },
  dasha_krama:       { sanskrit: 'Dasha Krama',       english: 'Period sequence',         subtitle: 'Vimshottari + Yogini + Chara',     layer: 'L1'   },
  yoga_sambandha:    { sanskrit: 'Yoga Sambandha',    english: 'Yoga relationships',      subtitle: 'Raja, Dhana, Pancha-Mahapurusha',  layer: 'L1'   },

  // ── Sambandha · L2_5 · Synthesis ──────────────────────────────────────────
  lakshana_kosha:    { sanskrit: 'Lakshana Kosha',    english: 'Treasury of indicators', subtitle: 'MSR · 573 signals',                layer: 'L2_5' },
  karana_jala:       { sanskrit: 'Karana Jala',       english: 'Net of causes',           subtitle: 'CGM · conditional graph',          layer: 'L2_5' },
  anubandha_mandala: { sanskrit: 'Anubandha Mandala', english: 'Matrix of linkages',      subtitle: 'CDLM · cross-domain',              layer: 'L2_5' },
  upaya_kosha:       { sanskrit: 'Upaya Kosha',       english: 'Treasury of remedies',    subtitle: 'RM · 6 traditions',                layer: 'L2_5' },
  sangam:            { sanskrit: 'Sangam',            english: 'Confluence',              subtitle: 'UCD · folded into Karana + Anubandha', layer: 'L2_5' },

  // ── Sutra · L3 · Meta-threads ──────────────────────────────────────────────
  kala_yoga:         { sanskrit: 'Kala Yoga',         english: 'Time-synchronicity',      subtitle: 'A15 · convergence map',            layer: 'L3'   },
  bandha:            { sanskrit: 'Bandha',            english: 'Phase-locked anchors',    subtitle: 'A16 · M6 ground truth',            layer: 'L3'   },
  chakra_vichara:    { sanskrit: 'Chakra Vichara',    english: 'Chakra analysis',         subtitle: 'A17',                              layer: 'L3'   },
  vedha_drishti:     { sanskrit: 'Vedha Drishti',     english: 'Vedha aspects',           subtitle: 'A18',                              layer: 'L3'   },
  bhrigu_kshetra:    { sanskrit: 'Bhrigu Kshetra',    english: 'Bhrigu transit field',    subtitle: 'A19',                              layer: 'L3'   },
  tajik_varsha:      { sanskrit: 'Tajik Varsha',      english: 'Annual revolution',       subtitle: 'A20',                              layer: 'L3'   },
  sphurana:          { sanskrit: 'Sphurana',          english: 'Aspect ignition',         subtitle: 'A21 · exact aspects',              layer: 'L3'   },
  kala_smriti:       { sanskrit: 'Kala Smriti',       english: 'Per-varsha digest',       subtitle: 'A22',                              layer: 'L3'   },

  // ── Vyavahara · L4 · Interface ─────────────────────────────────────────────
  prashna:           { sanskrit: 'Prashna',           english: 'Inquiry',                 subtitle: 'Consume chat',                     layer: 'L4'   },
  yantra_mcp:        { sanskrit: 'Yantra',            english: 'MCP surface',             subtitle: 'Tool access',                      layer: 'L4'   },
  marga:             { sanskrit: 'Marga',             english: 'API path',                subtitle: 'REST routes',                      layer: 'L4'   },

  // ── Extended L3 — multi-ayanamsha synthesis META assets ───────────────────
  trikala_darshan:   { sanskrit: 'Trikala Darshan',   english: 'Vision of Three Times',   subtitle: 'META-α · lattice',                 layer: 'L3'   },
  yantra_sangraha:   { sanskrit: 'Yantra Sangraha',   english: 'Pattern Atlas',           subtitle: 'META-β · pattern catalog',         layer: 'L3'   },
  sampradaya:        { sanskrit: 'Sampradaya',        english: 'Schools Speak',           subtitle: 'META-γ · divergence ledger',       layer: 'L3'   },
  shunya:            { sanskrit: 'Shunya',            english: 'The Empty',               subtitle: 'META-δ · negative space',          layer: 'L3'   },
  pramana:           { sanskrit: 'Pramana',           english: 'Evidence Trail',          subtitle: 'META-ε · derivation trail',        layer: 'L3'   },
} as const satisfies Record<string, AssetEntry>

export type AssetKey = keyof typeof ASSET_NAMES

export const LAYER_NAMES = {
  L1:   { sanskrit: 'Adhara',    english: 'Foundation'    },
  L2_5: { sanskrit: 'Sambandha', english: 'Synthesis'     },
  L3:   { sanskrit: 'Sutra',     english: 'Meta-threads'  },
  L4:   { sanskrit: 'Vyavahara', english: 'Interface'     },
} as const

export type LayerKey = keyof typeof LAYER_NAMES

/** Returns all asset keys grouped by layer in display order. */
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
