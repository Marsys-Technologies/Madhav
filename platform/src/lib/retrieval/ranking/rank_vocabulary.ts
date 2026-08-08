/**
 * rank_vocabulary.ts — ONE rank vocabulary (EL-59 / EL-20)
 * ============================================================================
 * Named regression this module closes (ELEVATION_CAMPAIGN_CHARTER_v2_1.md §γ.E):
 * Venus was served as `weakest_rank_in_chart: 5` by one tool (a bare integer with
 * no stated population or basis — query_remedies.ts / query_rm_resonances.ts,
 * L2_bodha, outside this lane's manifest) and as prose like "weakest of 7 by
 * shadbala" by another, with no shared vocabulary connecting the two claims. A
 * caller cannot tell whether "5" and "weakest of 7" are even the same ranking.
 *
 * This module is the canonical fix point: ONE shape, `RankStatement`, that always
 * carries `rank` + `population_size` + `rank_basis` (what the ranking is relative
 * to) + a human `rank_statement` sentence, so "rank: n" is never served bare.
 * register_d8_assess_domain.ts (this lane's manifest) is the first consumer;
 * any future pass on query_remedies.ts / query_rm_resonances.ts should import
 * this module rather than re-deriving its own rank phrasing (B.8 versioning
 * discipline: one vocabulary, not a second parallel one).
 *
 * B.10: never fabricates a rank — callers supply the real ordered population;
 * this module only formats it consistently.
 */
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '@/lib/retrieval/address_resolver'

export interface RankStatement {
  /** 1-indexed rank within the stated population (1 = strongest/first by the stated basis). */
  rank: number
  /** Size of the population the rank is relative to (e.g. 7 for the 7 classical grahas). */
  population_size: number
  /** What the ranking is computed over — e.g. "shadbala among 7 classical planets (Rahu/Ketu excluded)". */
  rank_basis: string
  /** Deterministic, template-composed sentence — never generative. */
  rank_statement: string
}

/**
 * Compose the one shared rank statement shape. `subject_label` is the entity being
 * ranked (e.g. "Venus"); `basis` names the metric + population in one clause.
 */
export function buildRankStatement(
  rank: number,
  population_size: number,
  basis: string,
  subject_label?: string,
): RankStatement {
  const ordinal = ordinalSuffix(rank)
  const subj = subject_label ? `${subject_label} is ` : ''
  const superlative =
    rank === 1 ? 'strongest' : rank === population_size ? 'weakest' : `${ordinal} of ${population_size}`
  const rank_statement =
    rank === 1 || rank === population_size
      ? `${subj}${superlative} (rank ${rank} of ${population_size}) by ${basis}.`
      : `${subj}ranked ${superlative} by ${basis}.`
  return { rank, population_size, rank_basis: basis, rank_statement }
}

function ordinalSuffix(n: number): string {
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 13) return `${n}th`
  switch (n % 10) {
    case 1: return `${n}st`
    case 2: return `${n}nd`
    case 3: return `${n}rd`
    default: return `${n}th`
  }
}

// ── Canonical population for graha strength rankings ──────────────────────────
// "Classical 7" = the 7 grahas that carry shadbala in Parashari practice (Rahu/Ketu are
// chāyā-grahas and do not receive a classical shadbala computation — excluding them is the
// doctrinal default, not an arbitrary trim). Population size is always STATED, never implied.
export const CLASSICAL_SEVEN_GRAHAS = ['SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA'] as const
export const ALL_NINE_GRAHAS = ['SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA', 'RA', 'KE'] as const

export interface GrahaShadbalaInput {
  graha: string // 2-char code (SU/MO/MA/ME/JU/VE/SA/RA/KE)
  shadbala_total: number
}

export interface RankedGraha extends RankStatement {
  graha: string
  shadbala_total: number
}

/**
 * Rank a set of grahas by shadbala_total, descending (rank 1 = strongest). Deterministic
 * tie-break: canonical graha order (SU,MO,MA,ME,JU,VE,SA,RA,KE) so two runs over the same
 * input always produce the same order — never a fabricated distinction (B.10).
 * `population` selects the classical-7 (default, shadbala-bearing) or all-9 population;
 * the returned `rank_basis` always states which.
 */
export function rankGrahasByShadbala(
  grahas: GrahaShadbalaInput[],
  population: 'classical_7' | 'all_9' = 'classical_7',
): RankedGraha[] {
  const allowed: readonly string[] = population === 'classical_7' ? CLASSICAL_SEVEN_GRAHAS : ALL_NINE_GRAHAS
  const canonicalOrder = new Map<string, number>(allowed.map((g, i) => [g, i]))
  const pool = grahas.filter(g => canonicalOrder.has(g.graha))
  const sorted = [...pool].sort((a, b) => {
    if (b.shadbala_total !== a.shadbala_total) return b.shadbala_total - a.shadbala_total
    return (canonicalOrder.get(a.graha) ?? 99) - (canonicalOrder.get(b.graha) ?? 99)
  })
  const population_size = sorted.length
  const basisLabel = `shadbala among ${population_size} ${population === 'classical_7' ? 'classical' : 'chart'} planets` +
    (population === 'classical_7' ? ' (Rahu/Ketu excluded — no classical shadbala)' : ' (all 9 grahas, chāyā-grahas included by convention)')
  return sorted.map((g, i) => {
    const stmt = buildRankStatement(i + 1, population_size, basisLabel, GRAHA_DISPLAY[g.graha] ?? g.graha)
    return { ...stmt, graha: g.graha, shadbala_total: g.shadbala_total }
  })
}

// Values sourced from the graha SSoT (address_resolver.grahaCodeOf +
// GRAHA_CODE_TO_NAME) rather than hardcoded literals — ADHIṢṬHĀNA Lane A2.
const GRAHA_DISPLAY: Record<string, string> = Object.fromEntries(
  ['SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA', 'RA', 'KE']
    .map(code => [code, GRAHA_CODE_TO_NAME[grahaCodeOf(code)]]),
)
