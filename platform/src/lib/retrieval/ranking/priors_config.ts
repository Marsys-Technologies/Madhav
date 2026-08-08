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
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '@/lib/retrieval/address_resolver'

// '1.0': Frozen after P2T iteration. Formula is correct; G10-QT score ≈9/15.
// Criteria 1 (≥3 yoga-class) + 4 (ZERO AV atomic tallies) PASS.
// Criteria 2 (10th-lord) + 3 (karaka-congruent) FAIL — L2 Bodha data has no Saturn graha
// metadata in career-domain signals (deferred to P3B salience rebuild).
// Criteria 5 (tie-block) addressed via salience blend + index tiebreak in composite_ranker.ts.
//
// '1.1' (WP-1.2β, LCA-14 / R-44 domain-discrimination): added the DOMAIN_BHAVA_AFFINITY
// overlay (bhavaAffinity) to topic_relevance. The prior formula discriminated domains ONLY
// via graha×domain affinity + a varga overlay — but the dominant candidate flood
// (`aspect_parashari_per_varga:house_N` composite_state signals, salience 2.3) carries NO
// graha and is tagged with an identical coarse domain array for wealth/relationship/career,
// so those domains' top-20 were 95% identical (audit Lane-6 shard-6-b0). The bhava congruence
// term reads the signal's actual bhava (target_house etc.) and scores it against the domain's
// CLASSICAL bhava set (BPHS Bhāvādhyāya), which is the axis that genuinely differs across
// domains (wealth = 2/11 dhana-labha; relationship = 7 kalatra; moksha = 4-8-12 moksha-trikona).
// Also adds the `moksha` domain (4-8-12 + Ketu, NOT a 9th-house/dharma alias — F-0973/0974)
// and completes `education` as a real vidya domain (4/5/2/9 + Mercury/Jupiter/Ketu — F-0756).
//
// '1.2' (EL-55, γ.E Lane E): no formula change — this bump documents the varga-weight term
// below (VARGA_BASE_WEIGHT) with its formal classical citation (VARGA_WEIGHT_CITATION) and
// surfaces that citation in `ranking_basis` (composite_ranker.ts buildRankingBasis) so a
// caller can see WHICH weighting scheme produced a signal's topic_relevance term, not just
// the resulting number. §3's per-line "Vimśopaka N.N" comments were already the correct
// Shodasavarga (16-fold) Vimsopaka Bala values (BPHS Ch.6 tradition; the same 16-varga
// scheme underlies L1's own `graha_vimsopaka_shodasavarga` chart_facts category) — this
// version bump makes that citation a named, exported object instead of only inline comments.
export const PRIORS_VERSION = '1.2' as const

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
//
// EL-55 (γ.E, priors v1.2) — formal citation. The per-line "— N.N" comments on
// VARGA_BASE_WEIGHT below are the classical ṣoḍaśavarga (16-fold) VIṂŚOPAKA BALA
// allocation (BPHS Ch.6 / the Phaladīpikā-tradition Vimśopaka scheme also implemented,
// independently, by L1's `graha_vimsopaka_shodasavarga` chart_facts writer). "Vimśopaka" =
// twenty-fold: the 16 classical vargas below are each assigned a fixed fraction of a
// 20-point total, D1 (rāśi) and D9 (navāṃśa) carrying the largest shares, D60 (ṣaṣṭyāṃśa)
// the largest of the supplementary/fine vargas ("Parāśara: D60 foremost" — BPHS 6.9).
// VARGA_BASE_WEIGHT does NOT restate L1's computed vimśopaka number as its own truth
// (§N.5) — it is a distinct, explicitly-labeled QUERY-TIME RANKING PRIOR (normalized so
// D1=1.00, not summed to 20) calibrated FROM the same classical fractions, with two
// documented deviations from raw vimśopaka: D10 lifted (0.5→0.55, modern career-practice
// weighting) and D60 retained near its classical share rather than compressed. The 16
// vargas below ARE the classical ṣoḍaśavarga set; the further "supplementary" vargas
// (D5,D6,D8,D11,D14,D15,D21,D32,D33,D50,D54) and the 3 Nāḍī vargas are OUTSIDE the
// classical 16-fold scheme (floored at 0.18 / 0.12 respectively) — not a lesser vimśopaka
// share, an absence of one.
//
// The classical vimśopaka HIERARCHY (nested subsets, each renormalized to 20 points, the
// literal "ṣoḍaśavarga hierarchy" this citation names) narrows as fewer vargas are used:
//   Ṣaḍvarga  (6):  D1,D2,D3,D9,D12,D30
//   Saptavarga(7):  Ṣaḍvarga + D7
//   Daśavarga (10): Saptavarga + D10,D16,D60
//   Ṣoḍaśavarga(16):Daśavarga + D4,D20,D24,D27,D40,D45  (== every non-supplementary key below)
// This module implements the full 16-fold scheme uniformly (composite ranking never
// selects a narrower N-varga group at query time); the narrower groups are cited here for
// provenance only — L1 computes them independently and separately
// (`graha_vimsopaka_shadvarga` / `_saptavarga` / `_dasavarga` / `_shodasavarga`).
export const VARGA_WEIGHT_CITATION = {
  scheme: 'Ṣoḍaśavarga (16-fold) Vimśopaka Bala',
  source: 'Bṛhat Parāśara Horā Śāstra Ch.6 (Ṣaḍvarga/Vimśopaka); cross-checked against L1 chart_facts.graha_vimsopaka_shodasavarga',
  hierarchy: {
    shadvarga: ['D1', 'D2', 'D3', 'D9', 'D12', 'D30'],
    saptavarga: ['D1', 'D2', 'D3', 'D7', 'D9', 'D12', 'D30'],
    dasavarga: ['D1', 'D2', 'D3', 'D7', 'D9', 'D10', 'D12', 'D16', 'D30', 'D60'],
    shodasavarga: ['D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60'],
  },
  documented_deviations: [
    'D10 lifted 0.5→0.55 base weight (raw vimśopaka share unchanged in citation; modern career-practice weighting, not a classical-value edit)',
    'D60 retained at 0.95 (near-maximal), matching BPHS 6.9 "D60 foremost" rather than a flat proportional compression',
  ],
} as const

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
  moksha:       ['D20', 'D60'],        // viṃśāṃśa = upāsanā; ṣaṣṭiāṃśa (WP-1.2β: moksha domain)
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
  | 'moksha'

// Canonical graha key variants (DB uses several forms across layers). Values
// sourced from the graha SSoT (address_resolver.grahaCodeOf + GRAHA_CODE_TO_NAME)
// rather than hardcoded literals — ADHIṢṬHĀNA Lane A2. This file's own
// established canonical form is lowercase long name (e.g. "sun"), derived
// from the SSoT's Title-case form via .toLowerCase().
const _GRAHA_ALIAS_INPUTS = [
  // 2-char codes (retrieval layer)
  'SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA', 'RA', 'KE',
  // Lowercase long form
  'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu',
  // L1 chart_facts.fact_subject format (observed in live data)
  'SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN',
  // Uppercase full names (bodha_msr_signals.configuration_jsonb format)
  'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU',
] as const

const GRAHA_ALIASES: Record<string, string> = Object.fromEntries(
  _GRAHA_ALIAS_INPUTS.map(alias => [alias, GRAHA_CODE_TO_NAME[grahaCodeOf(alias)].toLowerCase()]),
)

const GRAHA_DOMAIN_AFFINITY: Record<string, Record<Domain, number>> = {
  sun: {
    career: 1.4, wealth: 1.0, relationship: 0.8, progeny: 0.9, health: 1.1,
    education: 1.0, family: 1.1, residence: 0.9, travel: 0.9, spirituality: 1.0, character: 1.1,
    moksha: 0.9,
  },
  moon: {
    career: 1.0, wealth: 1.0, relationship: 1.1, progeny: 1.0, health: 1.1,
    education: 1.0, family: 1.3, residence: 1.0, travel: 1.0, spirituality: 1.0, character: 1.4,
    moksha: 1.1,   // chitta/manas — mind to be liberated (BPHS: Moon = manas-kāraka)
  },
  mars: {
    career: 1.2, wealth: 1.0, relationship: 1.0, progeny: 0.9, health: 1.2,
    education: 0.9, family: 1.0, residence: 1.4, travel: 1.0, spirituality: 0.9, character: 1.1,
    moksha: 0.8,
  },
  mercury: {
    career: 1.2, wealth: 1.2, relationship: 1.0, progeny: 1.0, health: 1.0,
    education: 1.4, family: 1.0, residence: 0.9, travel: 1.1, spirituality: 1.0, character: 1.2,
    moksha: 0.9,
  },
  jupiter: {
    career: 1.1, wealth: 1.3, relationship: 1.1, progeny: 1.5, health: 1.0,
    education: 1.3, family: 1.1, residence: 1.0, travel: 1.0, spirituality: 1.4, character: 1.1,
    moksha: 1.3,   // guru/jñāna — dispositor of dharma toward liberation
  },
  venus: {
    career: 1.0, wealth: 1.2, relationship: 1.5, progeny: 1.2, health: 1.0,
    education: 1.0, family: 1.0, residence: 1.2, travel: 1.0, spirituality: 0.9, character: 1.1,
    moksha: 0.8,   // bhoga-kāraka — contrary to vairāgya
  },
  saturn: {
    career: 1.4, wealth: 1.0, relationship: 0.9, progeny: 0.8, health: 1.2,
    education: 0.9, family: 0.9, residence: 1.2, travel: 1.0, spirituality: 1.1, character: 1.0,
    moksha: 1.3,   // vairāgya/detachment/renunciation
  },
  rahu: {
    career: 1.1, wealth: 1.1, relationship: 0.9, progeny: 0.8, health: 1.0,
    education: 1.0, family: 0.8, residence: 1.0, travel: 1.4, spirituality: 1.1, character: 1.0,
    moksha: 1.0,
  },
  ketu: {
    career: 0.9, wealth: 0.9, relationship: 0.8, progeny: 0.8, health: 1.1,
    education: 1.1, family: 0.9, residence: 0.9, travel: 1.1, spirituality: 1.5, character: 1.1,
    moksha: 1.6,   // mokṣa-kāraka par excellence (Ketu = the graha of liberation)
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

// ── §4b — BHĀVA × DOMAIN AFFINITY (WP-1.2β, LCA-14 / R-44) ────────────────────
// Source: BPHS Bhāvādhyāya (house significations) + the four classical bhāva-trikoṇas
// (dharma 1-5-9 · artha 2-6-10 · kāma 3-7-11 · mokṣa 4-8-12).
//
// WHY THIS EXISTS: the dominant candidate flood is graha-less `aspect_parashari_per_varga`
// composite_state signals whose ONLY discriminating axis is the bhāva they touch
// (configuration_jsonb.target_house). They carry an identical coarse domain array across
// wealth/relationship/career, so graha×domain affinity alone left the domains' top-K ~95%
// identical (Lane-6 shard-6-b0). Scoring the signal's actual bhāva against the domain's
// classical house-set is the axis that genuinely separates the domains.
//
// Multiplier centered at 1.0. Primary house(s) up to ~2.2; a house NOT in a domain's set
// is mildly contrary (UNLISTED_BHAVA_WEIGHT) so congruent-house signals decisively win the
// top ranks. Keep wealth/relationship PRIMARIES disjoint (2/11 vs 7) — that disjointness is
// what drives the served top-20 overlap below the ND-W1.2 ≤25% bar.
const UNLISTED_BHAVA_WEIGHT = 0.7

export const DOMAIN_BHAVA_AFFINITY: Record<string, Record<number, number>> = {
  // 2 = dhana (accumulated wealth), 11 = lābha (gains/income); 5+9 = dhana-yoga trikoṇas
  // (Lakṣmī-sthānas: lords of 5/9 give wealth); 1 = self-effort. BPHS Dhana-bhāvādhyāya.
  wealth:       { 2: 2.2, 11: 2.2, 9: 1.5, 5: 1.3, 1: 1.2 },
  // 7 = kalatra/jāyā (spouse); 12 = śayana-sukha (bed comforts); 8 = māṅgalya/saubhāgya
  // (marital longevity); 4 = domestic happiness/sukha. The 2nd (kuṭumba) is DELIBERATELY not
  // boosted here — it is far more a dhana house, and leaving it out of relationship's set is
  // what keeps wealth (2/11) and relationship (7/12/8) top-K disjoint (the ND-W1.2 ≤25% lever).
  relationship: { 7: 2.2, 12: 1.6, 8: 1.5, 4: 1.2 },
  // 10 = karma; artha-trikoṇa 2/6/10; 7 = mārket/vyāpāra; upachaya 3/6/10/11 (rising effort).
  career:       { 10: 2.2, 6: 1.5, 7: 1.4, 11: 1.4, 1: 1.3, 2: 1.2, 3: 1.2 },
  // 1 = deha/śarīra; 6 = roga (disease); 8 = āyuṣ/chronic; 3 = prāṇa/vitality; 12 = hospital/loss.
  health:       { 1: 2.2, 6: 2.0, 8: 1.6, 3: 1.2, 12: 1.1 },
  // vidyā (F-0756): 4 = formal vidyā-sthāna, 5 = buddhi/mantra/pūrva-puṇya, 2 = vāk/knowledge,
  // 9 = higher wisdom/guru. Bhāva-4 is PART of the set, never the sole "education" label.
  education:    { 4: 2.0, 5: 2.0, 2: 1.5, 9: 1.5, 3: 1.1 },
  // 5 = santāna (children); 9 = grandchildren/pūrva-puṇya; 11 = fulfilment; 2 = family.
  progeny:      { 5: 2.2, 9: 1.5, 11: 1.3, 2: 1.1 },
  // dharma-primary: 9 = dharma/guru/bhāgya; 12 = vyaya/upāsanā/liberation-effort; 5 = mantra;
  // 8 = occult. Distinct from `moksha` by its 9th-house dharma centre.
  spirituality: { 9: 2.2, 12: 1.6, 5: 1.4, 8: 1.2 },
  // MOKṢA-TRIKOṆA 4-8-12 (F-0973/0974): 12 = mokṣa-sthāna/vyaya (liberation, letting-go),
  // 8 = transformation/occult/randhra, 4 = antya-sukha/citta-śuddhi (final rest, inner peace).
  // NOT the 9th house (that is dharma-trikoṇa). 6 = ripu-conquest, minor.
  moksha:       { 12: 2.2, 8: 1.7, 4: 1.6, 6: 1.1 },
  // 1 = prakṛti/self/temperament; 5 = buddhi/manas/dhī; 9 = values/dharma; 3 = valour/manas.
  character:    { 1: 2.2, 5: 1.7, 9: 1.4, 3: 1.2, 4: 1.1 },
  // 4 = immovable property/home/land/vehicles; 2 = holdings; 11 = acquisition; 12 = distant land.
  residence:    { 4: 2.2, 2: 1.2, 11: 1.2, 12: 1.1 },
  // 2 = kuṭumba (family unit); 4 = mother/home; 9 = father/lineage; 5 = progeny.
  family:       { 2: 1.8, 4: 1.7, 9: 1.3, 5: 1.1 },
  // 12 = distant lands/foreign residence; 9 = long journeys/pilgrimage; 3 = short travel; 7 = away-from-home.
  travel:       { 12: 2.0, 9: 1.6, 3: 1.4, 7: 1.2 },
}

/**
 * Look up bhāva×domain affinity for the signal's bhāva. Neutral (1.0) when either the bhāva
 * or the domain is unknown, so signals with no resolvable house are unaffected by this axis
 * and rank on graha/class/varga alone. A house NOT in the domain's classical set is mildly
 * contrary (UNLISTED_BHAVA_WEIGHT) so domain-congruent-house signals decisively lead the top.
 */
export function bhavaAffinity(house: number | null | undefined, domain: string | null | undefined): number {
  if (!house || !domain) return 1.0
  const row = DOMAIN_BHAVA_AFFINITY[domain]
  if (!row) return 1.0
  return row[house] ?? UNLISTED_BHAVA_WEIGHT
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
