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
// Two key schemes exist: legacy L-prefix (seeded by create/route.ts) and
// new build/consume/read scheme (written by the Brahma orchestrator).
export const PYRAMID_TO_BRAHMA: Record<string, BrahmaLayerId> = {
  // ── Legacy L-prefix keys (create/route.ts seeding) ──
  'L1:facts':              'brahmagyan',
  'L2:analysis_a':         'ganita',
  'L2:analysis_mode_a':    'ganita',
  'L2:analysis_b':         'bodha',
  'L2:analysis_mode_b':    'bodha',
  'L2.5:synthesis':        'kala',
  'L3:reports':            'phala',
  'L3:domain_reports':     'phala',
  'L4:query_interface':    'mimamsa',
  // ── Brahma orchestrator keys (build_runs / pipeline writers) ──
  'build:foundation':      'brahmagyan',
  'build:ephemeris':       'brahmagyan',
  'build:positions':       'ganita',
  'build:dashas':          'ganita',
  'consume:signals':       'bodha',
  'consume:timeline':      'kala',
  'consume:predictions':   'phala',
  'read:overview':         'mimamsa',
}

export const BRAHMA_LAYER_ORDER: readonly BrahmaLayerId[] = [
  'brahmagyan',
  'ganita',
  'bodha',
  'kala',
  'phala',
  'mimamsa',
] as const
