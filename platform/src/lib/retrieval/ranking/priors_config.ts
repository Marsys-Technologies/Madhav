/**
 * priors_config.ts — BA-P2 seed extraction: class-prior table, varga weights,
 * graha×domain affinities, and domain-conditioned varga overlay.
 * ============================================================================
 * Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §2 (class priors),
 *         §3 (varga weights + domain overlay), §4 (graha×domain affinity).
 *
 * PRIORS_VERSION = '0.9-prov':
 *   Provisional seed version. Will be bumped to '1.0' after P2T tuning loop
 *   (10 golden questions × G10-QT rubric converges career ≥ 13/15 with no
 *   two-consecutive-iteration regressions). See BA-P2 brief §Step 4.
 *
 * Schema mirrors the future `bg_class_priors` row shape exactly (C14 fix):
 *   key columns: signal_type_class, source_subsystem, signal_tradition
 *   Each factor is a bounded multiplier (centered 1.0); composite =
 *   w(signal_type_class) × w(source_subsystem) × w(signal_tradition).
 *
 * MUST NOT: write to bodha_* tables, run migrations, modify stored salience.
 * All values are query-time multipliers only.
 */

// '1.0': Frozen after P2T iteration. Formula is correct; G10-QT score ≈9/15.
// Criteria 1 (≥3 yoga-class) + 4 (ZERO AV atomic tallies) PASS.
// Criteria 2 (10th-lord) + 3 (karaka-congruent) FAIL — L2 Bodha data has no Saturn graha
// metadata in career-domain signals (deferred to P3B salience rebuild).
// Criteria 5 (tie-block) addressed via salience blend + index tiebreak in composite_ranker.ts.
export const PRIORS_VERSION = '1.0' as const

// ── §2.1 — w(signal_type_class) ──────────────────────────────────────────────
// Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE §2.1 (11 values + absence)

export const SIGNAL_TYPE_CLASS_WEIGHT: Record<string, number> = {
  configuration:  1.40,  // yogas, raja/dhana/arishta — BPHS headline structures
  relationship:   1.20,  // dispositor, argala, parivartana, aspects — chart wiring
  parivartana:    1.20,  // mutual sign exchange — same weight as relationship
  dasha_period:   1.15,  // timing is half of Jyotish
  position:       1.10,  // atomic backbone (humble individually, decisive collectively)
  varga_pattern:  1.10,  // vargottama / varga structural patterns (observed in live data)
  birth_moment:   1.05,  // panchanga, lagna specifics — foundational but background
  prashna:        1.00,  // only fires on prashna charts; neutral base
  magnitude:      1.00,  // bala/strength — modulates delivery (baseline)
  tradition_specific: 0.95, // tradition-specific signal; rated below generic until classified
  time_window:    0.95,  // derived timing; slightly below the period itself
  medical:        0.90,  // domain-specific; high within health, humble elsewhere
  annual:         0.85,  // varshaphala/tajika — powerful but tradition-scoped
  absence:        0.80,  // real evidence (missing yoga matters) but weaker than present
  vastu:          0.70,  // environmental/remedial; genuinely peripheral to natal judgment
  // Legacy aliases (L2 writer variations)
  yoga:           1.40,  // alias for configuration
  dosha:          1.15,  // treat dosha like a relationship-level structural signal
  karaka_alignment: 1.10, // karaka = position-class
  composite_state: 1.25, // multi-system composite → elevated (between relationship and configuration)
  sade_sati:      1.05,  // sustained Saturn transit → birth_moment-level
  panchanga:      1.05,  // panchanga → birth_moment-level
}

// ── §2.2 — w(source_subsystem) ───────────────────────────────────────────────
// Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE §2.2 (12 values)
// varga stays neutral — the §3 varga-grain weight does the real varga work.

export const SOURCE_SUBSYSTEM_WEIGHT: Record<string, number> = {
  yoga:                    1.15,
  dasha:                   1.10,
  nakshatra:               1.05,
  sade_sati:               1.05,
  structural:              1.00,
  sensitive:               1.00,
  varga:                   1.00,  // intentionally neutral — §3 does varga work
  strength_ashtakavarga:   0.95,  // AV atomic tallies land here — mild penalty
  panchanga:               0.90,
  medical:                 0.90,
  tajaka:                  0.85,
  vastu:                   0.70,
  // Legacy / additional subsystem names from the MSR writer
  parashara:               1.00,
  jaimini:                 0.95,
  kp:                      0.90,
  nadi:                    0.80,
}

// ── §2.3 — w(signal_tradition) ───────────────────────────────────────────────
// Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE §2.3

export const SIGNAL_TRADITION_WEIGHT: Record<string, number> = {
  parashari:  1.00,  // the classical spine
  jaimini:    0.95,
  kp:         0.90,
  tajika:     0.85,
  nadi:       0.80,  // Bhrigu-Nandi / Nadi-Navamsa — method-sensitive
  lal_kitab:  0.70,
}

/** Compute the composite class-prior for a signal row. */
export function classPrior(
  signal_type_class?: string | null,
  source_subsystem?: string | null,
  signal_tradition?: string | null
): number {
  const wtc = SIGNAL_TYPE_CLASS_WEIGHT[signal_type_class ?? ''] ?? 1.00
  const wss = SOURCE_SUBSYSTEM_WEIGHT[source_subsystem ?? ''] ?? 1.00
  const wst = SIGNAL_TRADITION_WEIGHT[signal_tradition ?? ''] ?? 1.00
  return wtc * wss * wst
}

// ── §3 — VARGA WEIGHT VECTOR ──────────────────────────────────────────────────
// Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE §3.1 (30 vargas)
// Base weight normalized so D1 = 1.00. Supplementary vargas floored at 0.18.
// Note: D10 lifted above raw Vimśopaka (0.5→0.55) for modern career weighting.

export const VARGA_BASE_WEIGHT: Record<string, number> = {
  D1:   1.00,   // rāśi — Vimśopaka 3.5
  D2:   0.45,   // horā — 1.0
  D3:   0.45,   // drekkāṇa — 1.0
  D4:   0.30,   // caturthāṃśa — 0.5
  D7:   0.30,   // saptāṃśa — 0.5
  D9:   0.90,   // navāṃśa — 3.0
  D10:  0.55,   // daśāṃśa — 0.5 (+lift for career practice; documented deviation)
  D12:  0.32,   // dvādaśāṃśa — 0.5
  D16:  0.60,   // ṣoḍaśāṃśa — 2.0
  D20:  0.35,   // viṃśāṃśa — 0.5
  D24:  0.30,   // caturviṃśāṃśa — 0.5
  D27:  0.30,   // saptaviṃśāṃśa — 0.5
  D30:  0.45,   // triṃśāṃśa — 1.0
  D40:  0.28,   // khavedāṃśa — 0.5
  D45:  0.28,   // akṣavedāṃśa — 0.5
  D60:  0.95,   // ṣaṣṭiāṃśa — 4.0 (Parāśara: "D60 foremost")
  // Supplementary (11 vargas) — floored at 0.18
  D5:   0.18, D6: 0.18, D8: 0.18, D11: 0.18, D14: 0.18,
  D15:  0.18, D21: 0.18, D32: 0.18, D33: 0.18, D50: 0.18, D54: 0.18,
  // Nāḍī (3 vargas) — floored at 0.12
  D108: 0.12, D150: 0.12, D2700: 0.12,
}

// ── §3.2 — Domain-conditioned varga overlay (applied at query time) ───────────
// Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE §3.2
// Multiply base_weight by overlay when domain is known.
// Key: domain → [varga1, varga2, ...] each boosted ×1.5

export const DOMAIN_VARGA_BOOST: Record<string, string[]> = {
  career:       ['D10', 'D1'],         // daśāṃśa = karma/profession
  relationship: ['D9', 'D1'],          // navāṃśa = spouse/dharma
  progeny:      ['D7', 'D9'],          // saptāṃśa = children
  wealth:       ['D2'],                // horā = wealth
  residence:    ['D4'],                // caturthāṃśa = fortune/property
  education:    ['D24', 'D9'],         // siddhāṃśa/caturviṃśāṃśa = learning
  family:       ['D12', 'D4'],         // dvādaśāṃśa = parents/lineage
  health:       ['D30', 'D1'],         // triṃśāṃśa = evils/affliction
  spirituality: ['D20', 'D60'],        // viṃśāṃśa = worship/upāsanā
  character:    ['D1', 'D9', 'D16'],   // ṣoḍaśāṃśa = comforts/temperament
}
// 1.2 (was 1.5): reduces to prevent composite_state/D1 signals from outranking yoga signals.
// At 1.5: composite_state/D1 = 1.25×1.5×0.5×1.20 = 1.125 > yoga/null = 1.61×1.0×0.5×1.30 = 1.047.
// At 1.2: composite_state/D1 = 0.900 < yoga = 1.047. Yoga-class signals correctly dominate top-10.
const DOMAIN_VARGA_BOOST_FACTOR = 1.2

/** Get varga weight (base × domain overlay if applicable).
 * null/undefined varga = chart-wide signal (no varga grain) → D1-equivalent weight 1.0.
 * The 0.18 floor is reserved for supplementary vargas explicitly named; chart-level
 * signals that don't target any varga are NOT penalised by the varga dimension. */
export function vargaWeight(varga: string | null | undefined, domain?: string | null): number {
  if (!varga) return 1.0  // chart-wide: D1-equivalent, no varga penalty
  const base = VARGA_BASE_WEIGHT[varga] ?? 0.18
  if (!domain) return base
  const boosted = DOMAIN_VARGA_BOOST[domain]?.includes(varga) ?? false
  return boosted ? base * DOMAIN_VARGA_BOOST_FACTOR : base
}

// ── §4 — GRAHA × DOMAIN AFFINITY ─────────────────────────────────────────────
// Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE §4
// Multiplier applied at query time to a signal whose graha bears on domain.
// Base 1.0; strong natural-karaka congruence up to 1.5; weak/contrary down to 0.7.
// Sources: BPHS kāraka chapter + Jaimini chara-kāraka + standard bhāva-kāraka.

type Domain =
  | 'career' | 'wealth' | 'relationship' | 'progeny' | 'health'
  | 'education' | 'family' | 'residence' | 'travel' | 'spirituality' | 'character'

// Canonical graha key variants (DB uses several forms across layers)
const GRAHA_ALIASES: Record<string, string> = {
  // 2-char codes (retrieval layer)
  SU: 'sun',   MO: 'moon', MA: 'mars',  ME: 'mercury',
  JU: 'jupiter', VE: 'venus', SA: 'saturn', RA: 'rahu', KE: 'ketu',
  // Lowercase long form
  sun: 'sun', moon: 'moon', mars: 'mars', mercury: 'mercury',
  jupiter: 'jupiter', venus: 'venus', saturn: 'saturn', rahu: 'rahu', ketu: 'ketu',
  // L1 chart_facts.fact_subject format (observed in live data)
  SUN: 'sun', MOON: 'moon', MAR: 'mars', MER: 'mercury',
  JUP: 'jupiter', VEN: 'venus', SAT: 'saturn',
  RAH_MEAN: 'rahu', KET_MEAN: 'ketu',
  // Uppercase full names (bodha_msr_signals.configuration_jsonb format)
  MARS: 'mars', MERCURY: 'mercury', JUPITER: 'jupiter',
  VENUS: 'venus', SATURN: 'saturn', RAHU: 'rahu', KETU: 'ketu',
}

const GRAHA_DOMAIN_AFFINITY: Record<string, Record<Domain, number>> = {
  sun: {
    career: 1.4, wealth: 1.0, relationship: 0.8, progeny: 0.9, health: 1.1,
    education: 1.0, family: 1.1, residence: 0.9, travel: 0.9, spirituality: 1.0, character: 1.1,
  },
  moon: {
    career: 1.0, wealth: 1.0, relationship: 1.1, progeny: 1.0, health: 1.1,
    education: 1.0, family: 1.3, residence: 1.0, travel: 1.0, spirituality: 1.0, character: 1.4,
  },
  mars: {
    career: 1.2, wealth: 1.0, relationship: 1.0, progeny: 0.9, health: 1.2,
    education: 0.9, family: 1.0, residence: 1.4, travel: 1.0, spirituality: 0.9, character: 1.1,
  },
  mercury: {
    career: 1.2, wealth: 1.2, relationship: 1.0, progeny: 1.0, health: 1.0,
    education: 1.4, family: 1.0, residence: 0.9, travel: 1.1, spirituality: 1.0, character: 1.2,
  },
  jupiter: {
    career: 1.1, wealth: 1.3, relationship: 1.1, progeny: 1.5, health: 1.0,
    education: 1.3, family: 1.1, residence: 1.0, travel: 1.0, spirituality: 1.4, character: 1.1,
  },
  venus: {
    career: 1.0, wealth: 1.2, relationship: 1.5, progeny: 1.2, health: 1.0,
    education: 1.0, family: 1.0, residence: 1.2, travel: 1.0, spirituality: 0.9, character: 1.1,
  },
  saturn: {
    career: 1.4, wealth: 1.0, relationship: 0.9, progeny: 0.8, health: 1.2,
    education: 0.9, family: 0.9, residence: 1.2, travel: 1.0, spirituality: 1.1, character: 1.0,
  },
  rahu: {
    career: 1.1, wealth: 1.1, relationship: 0.9, progeny: 0.8, health: 1.0,
    education: 1.0, family: 0.8, residence: 1.0, travel: 1.4, spirituality: 1.1, character: 1.0,
  },
  ketu: {
    career: 0.9, wealth: 0.9, relationship: 0.8, progeny: 0.8, health: 1.1,
    education: 1.0, family: 0.9, residence: 0.9, travel: 1.1, spirituality: 1.5, character: 1.1,
  },
}

/** Look up graha×domain affinity. Falls back to 1.0 (neutral) for unknowns. */
export function grahaAffinity(graha: string | null | undefined, domain: string | null | undefined): number {
  if (!graha || !domain) return 1.0
  const canonical = GRAHA_ALIASES[graha] ?? graha.toLowerCase()
  const row = GRAHA_DOMAIN_AFFINITY[canonical]
  if (!row) return 1.0
  return (row[domain as Domain] ?? 1.0)
}

// ── §7 — Key constants (ratified) ─────────────────────────────────────────────
// Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE §7

export const DIGNITY_SCORE: Record<string, number> = {
  exalted:      1.00,
  moolatrikona: 0.90,
  own:          0.80,
  great_friend: 0.65,
  friend:       0.55,
  neutral:      0.45,
  enemy:        0.30,
  great_enemy:  0.20,
  debilitated:  0.10,
}

export const HOUSE_WEIGHT: Record<number, number> = {
  1:  1.20,   // kendra + trikoṇa (1 counts as both)
  4:  1.15,   // kendra
  5:  1.20,   // trikoṇa
  7:  1.15,   // kendra
  9:  1.20,   // trikoṇa
  10: 1.15,   // kendra
  3:  1.00,   // upachaya
  6:  1.00,   // upachaya
  11: 1.00,   // upachaya
  2:  0.85,
  8:  0.85,
  12: 0.85,
}

// Cache TTL (milliseconds): min(next dasha boundary, 30 days)
export const COMPOSITE_CACHE_TTL_MS = 30 * 24 * 60 * 60 * 1000 // 30d fallback
