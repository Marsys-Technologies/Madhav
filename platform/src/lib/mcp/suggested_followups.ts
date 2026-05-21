/**
 * suggested_followups.ts — Heuristic generator for MCP follow-up questions.
 *
 * Returns 2-3 plausible next questions for ask_madhav responses.
 * Phase 1 implementation is heuristic (template-based). A richer LLM-driven
 * version is planned for post-v1.
 *
 * Sources for follow-ups:
 *   1. Query classes NOT triggered by the current query → suggest that angle.
 *   2. Domains touched → suggest adjacent or cross-domain questions.
 *   3. Forward-looking queries → suggest the historical/contextual counterpart.
 *   4. Predictive queries → suggest a "what does the LEL say" ground-truth check.
 *
 * Deduplication: the returned array is deduplicated and capped at 3.
 */

import type { PipelinePlan } from '@/lib/pipeline/types'

// ── Domain adjacency map ──────────────────────────────────────────────────────

const DOMAIN_ADJACENT: Record<string, string[]> = {
  career:        ['finance', 'reputation', 'dharma'],
  finance:       ['career', 'property', 'family'],
  health:        ['longevity', 'mental', 'spiritual'],
  relationships: ['marriage', 'children', 'family'],
  marriage:      ['relationships', 'partnerships', 'dharma'],
  children:      ['relationships', 'creativity', 'education'],
  education:     ['children', 'dharma', 'career'],
  dharma:        ['spiritual', 'education', 'career'],
  spiritual:     ['dharma', 'mental', 'health'],
  mental:        ['spiritual', 'health', 'relationships'],
  property:      ['finance', 'family', 'foreign'],
  foreign:       ['travel', 'property', 'career'],
  travel:        ['foreign', 'health', 'spirituality'],
  reputation:    ['career', 'dharma', 'social'],
  family:        ['relationships', 'property', 'finance'],
}

// ── Query-class follow-up templates ──────────────────────────────────────────

const CLASS_TEMPLATES: Partial<Record<string, string>> = {
  holistic:      'What are the key timing windows to watch in the current dasha?',
  predictive:    'What does the life event log reveal about similar periods in the past?',
  factual:       'How does this placement interact with the current dasha lord?',
  interpretive:  'What specific life domains does this influence, and how strongly?',
  cross_domain:  'Which of these domains is the most active right now given the dasha?',
  discovery:     'What are the top three contradictions or tensions in the chart today?',
  remedial:      'How do these prescriptions interact with the current planetary period?',
  classical_grounding: 'How does the multi-school consensus compare on this point?',
  multi_school_triangulation: 'Which school reading has the strongest historical validation in the life event log?',
}

// ── Domain follow-up templates ────────────────────────────────────────────────

function domainFollowup(domain: string): string {
  const adjacents = DOMAIN_ADJACENT[domain]
  const adj = adjacents?.[0] ?? 'spiritual'
  return `How does the ${domain} domain interact with ${adj} in the current dasha?`
}

// ── Main generator ────────────────────────────────────────────────────────────

/**
 * Generate 2-3 plausible follow-up questions based on the pipeline plan.
 *
 * @param plan     The PipelinePlan that produced the current response.
 * @param domains  Optional override for domains — uses plan.domains by default.
 * @returns        Array of 2-3 non-duplicate follow-up question strings.
 */
export function generateSuggestedFollowups(
  plan: PipelinePlan,
  domains?: string[],
): string[] {
  const candidates: string[] = []

  // Source 1: Suggest the "other" query class angle.
  const queryClass = plan.query_class
  const oppositeClass =
    queryClass === 'factual'  ? 'holistic' :
    queryClass === 'holistic' ? 'predictive' :
    queryClass === 'predictive' ? 'holistic' :
    queryClass === 'interpretive' ? 'predictive' :
    queryClass === 'cross_domain' ? 'holistic' :
    queryClass === 'discovery' ? 'predictive' :
    queryClass === 'remedial' ? 'holistic' :
    null

  if (oppositeClass && CLASS_TEMPLATES[oppositeClass]) {
    candidates.push(CLASS_TEMPLATES[oppositeClass]!)
  }
  if (CLASS_TEMPLATES[queryClass]) {
    candidates.push(CLASS_TEMPLATES[queryClass]!)
  }

  // Source 2: Domain-adjacent follow-ups.
  const effectiveDomains = domains ?? plan.domains ?? []
  for (const domain of effectiveDomains.slice(0, 2)) {
    const lc = domain.toLowerCase()
    if (DOMAIN_ADJACENT[lc]) {
      candidates.push(domainFollowup(lc))
    }
  }

  // Source 3: Forward-looking → suggest historical comparison.
  if (plan.forward_looking) {
    candidates.push(
      'What does the life event log show about similar dasha periods in the past?'
    )
  }

  // Source 4: Non-predictive → suggest a timing question.
  if (!plan.forward_looking && queryClass !== 'predictive') {
    candidates.push(
      'What are the key timing windows for this theme in the current dasha phase?'
    )
  }

  // Source 5: Always useful fallback.
  candidates.push(
    'Which MSR signals are most relevant to this question and at what confidence?'
  )

  // Deduplicate (preserve insertion order) and cap at 3.
  const seen = new Set<string>()
  const result: string[] = []
  for (const c of candidates) {
    if (!seen.has(c) && result.length < 3) {
      seen.add(c)
      result.push(c)
    }
  }

  return result
}
