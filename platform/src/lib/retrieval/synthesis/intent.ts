/**
 * synthesis/intent.ts — P-10 intent decomposition (compound question → evidence contract)
 * ========================================================================================
 * WP-1.4 stage (1). Turns a compound Lane-7-heavy question ("map the whole marriage
 * universe", "what does the chart say about moksha") into an EVIDENCE CONTRACT: the
 * explicit set of evidence families the answer must compose, decided BEFORE any retrieval.
 *
 * SKELETON (W1): a deterministic keyword→domain map with hand-authored templates for the
 * 7 Lane-7 heavy questions. This is intentionally NOT an LLM call — the skeleton must run
 * deterministically and be unit-testable. The W3 upgrade path is documented at
 * `decompose()`: swap this function's body for an LLM decomposition that emits the SAME
 * EvidenceContract shape. Everything downstream (plan → map-reduce → narrative) is agnostic
 * to how the contract was produced.
 *
 * The cross-domain families in each template are NOT guesses: they mirror the real CDLM
 * linkage structure (e.g. relationship↔career is the single strongest cross-domain cell in
 * the native chart at 6,160 shared signals) so the contract plans against evidence that
 * actually exists in the pre-aggregated surfaces.
 */

import type { Domain, EvidenceContract, EvidenceFamilyRequest } from './types'

const DOMAIN_KEYWORDS: Record<Domain, string[]> = {
  relationship: ['marriage', 'marry', 'spouse', 'wife', 'husband', 'partner', 'relationship', 'love', 'divorce', '7th', 'seventh', 'venus'],
  career: ['career', 'profession', 'job', 'work', 'vocation', 'business', 'occupation', '10th', 'tenth', 'rajayoga'],
  wealth: ['wealth', 'money', 'finance', 'income', 'prosperity', 'riches', 'dhana', '2nd', '11th'],
  health: ['health', 'disease', 'illness', 'body', 'longevity', 'ayush', 'medical', 'roga', '6th'],
  spirituality: ['moksha', 'spiritual', 'spirituality', 'liberation', 'enlightenment', 'dharma', 'renunciation', 'sannyasa', '12th', 'guru', 'jupiter', 'ketu'],
  character: ['character', 'personality', 'temperament', 'nature', 'mind', 'psychology', 'self', 'lagna', 'moon'],
  other: [],
}

/**
 * The 7 Lane-7 heavy-question templates. Each names a primary domain and the cross-domain
 * families the CHARTER §7 rubric expects a whole-chart-read to weave in (the linkages that
 * actually carry weight in the pre-aggregated CDLM surface). Coverage anchors:
 *   marriage_universe → F-0961 ; moksha → F-0973/0974 ; flat_wall antidote → F-0949.
 */
interface HeavyTemplate {
  id: string
  primary: Domain
  /** [domain, role, rationale] cross-domain / chain families to add to the contract. */
  cross: Array<[Domain, EvidenceFamilyRequest['role'], string]>
}

const HEAVY_TEMPLATES: Record<Domain, HeavyTemplate> = {
  relationship: {
    id: 'marriage_universe',
    primary: 'relationship',
    cross: [
      ['career', 'cross_domain', 'career↔relationship is the dominant cross-domain linkage — householder/duty tension bears on marriage timing and stability'],
      ['character', 'cross_domain', 'temperament/manas conditions how relationship karma is lived'],
      ['spirituality', 'cross_domain', 'the 7th↔12th (bed-pleasures/moksha) axis and detachment pulls bear on partnership'],
      ['health', 'karaka_chain', 'Venus/7th-lord condition (kāraka chain) gates marital vitality'],
    ],
  },
  spirituality: {
    id: 'moksha_universe',
    primary: 'spirituality',
    cross: [
      ['character', 'cross_domain', 'manas/lagna disposition is the ground of any moksha inclination'],
      ['relationship', 'cross_domain', 'the 7th↔12th axis — attachment vs renunciation is the moksha tension'],
      ['career', 'cross_domain', 'karma-yoga vs nivritti: worldly engagement conditions the liberation path'],
    ],
  },
  career: {
    id: 'career_universe',
    primary: 'career',
    cross: [
      ['wealth', 'cross_domain', 'artha: career fruit is read jointly with the dhana axis'],
      ['character', 'cross_domain', 'sva-dharma/temperament shapes vocational fit'],
      ['relationship', 'cross_domain', 'career↔relationship is the strongest cross-domain cell — work/home balance'],
    ],
  },
  wealth: {
    id: 'wealth_universe',
    primary: 'wealth',
    cross: [
      ['career', 'cross_domain', 'the artha engine: wealth flows from the 10th↔2nd/11th linkage'],
      ['character', 'cross_domain', 'disposition toward accumulation vs dispersal'],
    ],
  },
  health: {
    id: 'health_universe',
    primary: 'health',
    cross: [
      ['character', 'cross_domain', 'manas↔body: psychosomatic linkage'],
      ['relationship', 'cross_domain', 'the 6th↔7th (disease/partner) maraka considerations'],
    ],
  },
  character: {
    id: 'character_universe',
    primary: 'character',
    cross: [
      ['spirituality', 'cross_domain', 'the inner disposition↔dharma linkage'],
      ['career', 'cross_domain', 'temperament expressed through vocation'],
    ],
  },
  other: { id: 'generic', primary: 'other', cross: [] },
}

/** Score a domain by keyword hits in the question (lowercased). */
function scoreDomain(q: string, domain: Domain): number {
  const words = DOMAIN_KEYWORDS[domain]
  let score = 0
  for (const w of words) if (q.includes(w)) score += 1
  return score
}

/**
 * P-10 intent decomposition. SKELETON: deterministic keyword-template match.
 *
 * W3 UPGRADE PATH: replace this body with an LLM planner that reads the question +
 * the chart's gestalt central_question and emits the SAME EvidenceContract shape.
 * Downstream stages are agnostic to the producer — this is the single seam to swap.
 */
export function decompose(question: string): EvidenceContract {
  const q = (question ?? '').toLowerCase()

  // Pick the primary domain by keyword score; tie/empty → 'other' generic.
  const domains: Domain[] = ['relationship', 'career', 'wealth', 'health', 'spirituality', 'character']
  let primary: Domain = 'other'
  let best = 0
  for (const d of domains) {
    const s = scoreDomain(q, d)
    if (s > best) { best = s; primary = d }
  }

  const template = HEAVY_TEMPLATES[primary]
  const matched = best > 0 ? template.id : null

  const families: EvidenceFamilyRequest[] = []

  // Orientation family — always first (the whole-chart gestalt entry, B.11).
  families.push({
    family_key: 'orientation:whole_chart',
    domain: primary,
    role: 'orientation',
    rationale: 'Whole-chart gestalt verdict map + central question (B.11 whole-chart-read entry).',
  })

  // Primary domain family.
  families.push({
    family_key: `domain:${primary}`,
    domain: primary,
    role: 'primary',
    rationale: `Primary domain of the question ("${primary}").`,
  })

  // Cross-domain / chain families from the template.
  for (const [d, role, rationale] of template.cross) {
    families.push({
      family_key: role === 'cross_domain' ? `cross_link:${primary}×${d}` : `${role}:${d}`,
      domain: d,
      role,
      rationale,
    })
  }

  return {
    question,
    primary_domain: primary,
    families,
    matched_template: matched,
    decomposition_method: best > 0 ? 'keyword_template' : 'keyword_generic',
  }
}
