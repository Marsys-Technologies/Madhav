export const BRAHMA_LEXICON = {
  brahmagyan: { sanskrit: 'Brahmagyan', english: 'Foundation' },
  ganita:     { sanskrit: 'Gaṇita',     english: 'Chart Facts' },
  bodha:      { sanskrit: 'Bodha',      english: 'Chart Intelligence' },
  kala:       { sanskrit: 'Kāla',       english: 'Temporal' },
  phala:      { sanskrit: 'Phala',      english: 'Prediction' },
  mimamsa:    { sanskrit: 'Mīmāṃsā',   english: 'Learning' },
} as const

export type BrahmaLayerId = keyof typeof BRAHMA_LEXICON

// Maps pyramid_layers (layer + ':' + sublayer) → Brahma layer id.
// brahmagyan (L1/facts) is always-lit bedrock.
export const PYRAMID_TO_BRAHMA: Record<string, BrahmaLayerId> = {
  'L1:facts':           'brahmagyan',
  'L2:analysis_a':      'ganita',
  'L2:analysis_b':      'bodha',
  'L2.5:synthesis':     'kala',
  'L3:reports':         'phala',
  'L4:query_interface': 'mimamsa',
}

export const BRAHMA_LAYER_ORDER: readonly BrahmaLayerId[] = [
  'brahmagyan',
  'ganita',
  'bodha',
  'kala',
  'phala',
  'mimamsa',
] as const
