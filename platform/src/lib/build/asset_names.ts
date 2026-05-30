export interface AssetMeta {
  id: string
  sanskrit: string
  english: string
  layer: 'L1' | 'L25' | 'L3' | 'L4'
  sortOrder: number
  categoryPrefix: string
  retired?: boolean
}

export const ASSET_MAP: Record<string, AssetMeta> = {
  A1:  { id: 'A1',  sanskrit: 'Pratyaksha',       english: 'Direct Perception (Engine)',   layer: 'L1',  sortOrder: 1,  categoryPrefix: 'a1_' },
  A2:  { id: 'A2',  sanskrit: 'Janma-Patra',      english: 'The Birth Chart',              layer: 'L1',  sortOrder: 2,  categoryPrefix: 'a2_' },
  A3:  { id: 'A3',  sanskrit: 'Mula-Lakshana',    english: 'Root Marks',                   layer: 'L1',  sortOrder: 3,  categoryPrefix: 'a3_' },
  A4:  { id: 'A4',  sanskrit: 'Panchanga',        english: 'Five Limbs of Time',           layer: 'L1',  sortOrder: 4,  categoryPrefix: 'a4_' },
  A5:  { id: 'A5',  sanskrit: 'Marma-Bindu',      english: 'Key Pressure Points',          layer: 'L1',  sortOrder: 5,  categoryPrefix: 'a5_' },
  A6:  { id: 'A6',  sanskrit: 'Shodashvarga',     english: 'The Sixteen Mirrors',          layer: 'L1',  sortOrder: 6,  categoryPrefix: 'a6_' },
  A7:  { id: 'A7',  sanskrit: 'Dasha-Kala',       english: 'Time Lords',                   layer: 'L1',  sortOrder: 7,  categoryPrefix: 'a7_' },
  A8:  { id: 'A8',  sanskrit: 'Bala-Yoga',        english: 'Strengths & Patterns',         layer: 'L25', sortOrder: 8,  categoryPrefix: 'a8_' },
  A9:  { id: 'A9',  sanskrit: 'Sade-Sati',        english: "Saturn's Long Walk",           layer: 'L25', sortOrder: 9,  categoryPrefix: 'a9_' },
  A10: { id: 'A10', sanskrit: 'Lakshana-Sangraha',english: 'The Signal Catalog',           layer: 'L25', sortOrder: 10, categoryPrefix: 'a10_' },
  A11: { id: 'A11', sanskrit: 'Bhava-Sambandha',  english: 'Life-Domain Linkages',         layer: 'L25', sortOrder: 11, categoryPrefix: 'a11_' },
  A12: { id: 'A12', sanskrit: 'Chakra-Jala',      english: 'The Chart Web',                layer: 'L25', sortOrder: 12, categoryPrefix: 'a12_' },
  A13: { id: 'A13', sanskrit: 'Aushadhi',         english: 'The Remedies',                 layer: 'L25', sortOrder: 13, categoryPrefix: 'a13_' },
  A14: { id: 'A14', sanskrit: '',                 english: '(Retired)',                    layer: 'L25', sortOrder: 14, categoryPrefix: '',  retired: true },
  A15: { id: 'A15', sanskrit: 'Sangat-Kala',      english: 'Convergence Windows',          layer: 'L3',  sortOrder: 15, categoryPrefix: 'a15_' },
  A16: { id: 'A16', sanskrit: 'Sankalpa-Phala',   english: 'Predicted Events',             layer: 'L3',  sortOrder: 16, categoryPrefix: 'a16_' },
  A17: { id: 'A17', sanskrit: 'Yantra',           english: 'Sacred Geometries',            layer: 'L3',  sortOrder: 17, categoryPrefix: 'a17_' },
  A18: { id: 'A18', sanskrit: 'Vedha',            english: 'Obstructions',                 layer: 'L3',  sortOrder: 18, categoryPrefix: 'a18_' },
  A19: { id: 'A19', sanskrit: 'Bhrigu-Bindu',     english: 'Lifetime Hits',                layer: 'L3',  sortOrder: 19, categoryPrefix: 'a19_' },
  A20: { id: 'A20', sanskrit: 'Varshesha',        english: 'Annual Lords',                 layer: 'L3',  sortOrder: 20, categoryPrefix: 'a20_' },
  A21: { id: 'A21', sanskrit: 'Drishti-Patrika',  english: 'Aspect Calendar',              layer: 'L3',  sortOrder: 21, categoryPrefix: 'a21_' },
  A22: { id: 'A22', sanskrit: 'Varsha-Darshan',   english: 'Yearly Vision',                layer: 'L3',  sortOrder: 22, categoryPrefix: 'a22_' },
  'META-α': { id: 'META-α', sanskrit: 'Trikala-Darshan',  english: 'Vision of Three Times', layer: 'L3', sortOrder: 23, categoryPrefix: 'meta_alpha_' },
  'META-β': { id: 'META-β', sanskrit: 'Yantra-Sangraha',  english: 'Pattern Atlas',         layer: 'L3', sortOrder: 24, categoryPrefix: 'meta_beta_' },
  'META-γ': { id: 'META-γ', sanskrit: 'Sampradaya',       english: 'Schools Speak',         layer: 'L3', sortOrder: 25, categoryPrefix: 'meta_gamma_' },
  'META-δ': { id: 'META-δ', sanskrit: 'Shunya',           english: 'The Empty',             layer: 'L3', sortOrder: 26, categoryPrefix: 'meta_delta_' },
  'META-ε': { id: 'META-ε', sanskrit: 'Pramana',          english: 'Evidence Trail',        layer: 'L3', sortOrder: 27, categoryPrefix: 'meta_epsilon_' },
  'META-ζ': { id: 'META-ζ', sanskrit: 'Kala-Darpana',     english: 'Time Mirror',           layer: 'L3', sortOrder: 28, categoryPrefix: 'meta_zeta_' },
}

export function getAssetDisplayName(assetId: string): string {
  const meta = ASSET_MAP[assetId]
  if (!meta) return assetId
  return meta.sanskrit ? `${meta.sanskrit} · ${meta.english}` : meta.english
}

export function getAssetSanskrit(assetId: string): string {
  return ASSET_MAP[assetId]?.sanskrit ?? assetId
}

export function getAssetEnglish(assetId: string): string {
  return ASSET_MAP[assetId]?.english ?? assetId
}
