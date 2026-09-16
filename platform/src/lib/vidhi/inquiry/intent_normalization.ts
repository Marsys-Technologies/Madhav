import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import { z } from 'zod'
import type { InquiryScopeNormalizationReceipt, InquiryScopeTuple } from './types'

export const INQUIRY_SCOPE_NORMALIZATION_VERSION = 'inquiry-scope-normalization-v1' as const

/**
 * Admission vocabulary for raw Inquiry lifecycle callers.
 *
 * The lifecycle is intentionally able to receive either the classifier tuple
 * (the public MCP/portal vocabulary) or the compiler tuple (the frozen
 * acceptance corpus vocabulary). Both are normalized and hashed by the
 * compiler; rejecting the latter at the transport boundary made an otherwise
 * valid signed lifecycle impossible to start. This is a closed union, not an
 * open string schema, so normalization never becomes an admission bypass.
 */
export const InquiryScopeInputSchema = z.object({
  intent: z.enum([
    'dasha_timing', 'transit_analysis', 'yoga_identification', 'planet_strength',
    'house_analysis', 'remedy_lookup', 'panchanga', 'classical_rule', 'chart_overview',
    'prediction_calibration', 'domain_assessment', 'unknown',
    'wealth_deepdive', 'career_deepdive', 'health_deepdive', 'marriage_deepdive',
    'spirituality_deepdive', 'education_deepdive', 'progeny_deepdive',
    'structure_read', 'panoramic_breadth', 'retrieval_only', 'general_synthesis',
    'undertaking_election', 'biography_narrative', 'ritual_yajna',
  ]),
  domains: z.array(z.enum([
    'wealth', 'career', 'marriage', 'health', 'children', 'education', 'spirituality',
    'litigation', 'property', 'travel', 'general', 'all',
  ])).min(1),
  width: z.enum(['narrow', 'standard', 'broad', 'panoramic']),
  depth: z.enum(['shallow', 'standard', 'deep', 'retrieval', 'structure', 'deepdive']),
  horizon: z.enum(['past', 'present', 'near', 'far', 'atemporal', 'natal', 'current', 'multi_year']),
  intervention: z.union([z.boolean(), z.enum(['none', 'remedy', 'muhurta', 'mitigation'])]),
  entitlement: z.enum(['reference', 'native', 'restricted', 'public_disclosed', 'research']),
}).strict()

const DOMAIN_ALIASES: Readonly<Record<string, string>> = {
  finance: 'wealth', financial: 'wealth', money: 'wealth', prosperity: 'wealth',
  job: 'career', profession: 'career', work: 'career', vocation: 'career',
  relationship: 'marriage', relationships: 'marriage', spouse: 'marriage',
  child: 'children', progeny: 'children',
  study: 'education', studies: 'education',
  spiritual: 'spirituality', moksha: 'spirituality',
  general: 'general', all: 'all',
}

const INTENT_ALIASES: Readonly<Record<string, string>> = {
  assess: 'domain_assessment', assessment: 'domain_assessment',
  domain_read: 'domain_assessment',
  forecast: 'transit_analysis', timing: 'dasha_timing',
  yoga: 'yoga_identification', strength: 'planet_strength',
  house: 'house_analysis', remedies: 'remedy_lookup', remedy: 'remedy_lookup',
  overview: 'chart_overview', calibration: 'prediction_calibration',
}

const DEEP_DOMAIN_INTENTS: Readonly<Record<string, string>> = {
  wealth: 'wealth_deepdive', career: 'career_deepdive', health: 'health_deepdive',
  marriage: 'marriage_deepdive', children: 'progeny_deepdive',
  education: 'education_deepdive', spirituality: 'spirituality_deepdive',
}

function token(value: unknown, fallback: string): string {
  const normalized = String(value ?? fallback).normalize('NFKD').replace(/\p{M}/gu, '')
    .trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
  return normalized || fallback
}

function uniqueSorted(values: readonly string[]): string[] {
  return [...new Set(values)].sort()
}

export interface NormalizedInquiryScope {
  readonly scope: InquiryScopeTuple
  readonly receipt: InquiryScopeNormalizationReceipt
}

export function normalizeInquiryScope(input: InquiryScopeTuple): NormalizedInquiryScope {
  const appliedRules: string[] = []
  const rawIntent = token(input.intent, 'unknown')
  let intent = INTENT_ALIASES[rawIntent] ?? rawIntent
  if (intent !== rawIntent) appliedRules.push(`intent:${rawIntent}->${intent}`)

  const rawDomains = (input.domains ?? []).map((domain) => token(domain, '')).filter(Boolean)
  const domains = uniqueSorted((rawDomains.length ? rawDomains : ['general']).map((domain) => DOMAIN_ALIASES[domain] ?? domain))
  if (stableFingerprint(rawDomains) !== stableFingerprint(domains)) appliedRules.push('domains:aliases_deduplicated_sorted')

  const rawWidth = token(input.width, 'focused')
  const width = ({ broad: 'panoramic', wide: 'panoramic', comprehensive: 'panoramic',
    narrow: 'focused', standard: 'focused', focused: 'focused', panoramic: 'panoramic' } as const)[rawWidth] ?? rawWidth
  if (width !== rawWidth) appliedRules.push(`width:${rawWidth}->${width}`)

  const rawDepth = token(input.depth, 'standard')
  const depth = ({ deep: 'deepdive', in_depth: 'deepdive', detailed: 'deepdive',
    shallow: 'retrieval', brief: 'retrieval', retrieval: 'retrieval', standard: 'standard', deepdive: 'deepdive' } as const)[rawDepth] ?? rawDepth
  if (depth !== rawDepth) appliedRules.push(`depth:${rawDepth}->${depth}`)

  const rawHorizon = token(input.horizon, 'unspecified')
  const horizon = ({ present: 'current', near: 'current', now: 'current', current: 'current',
    far: 'multi_year', future: 'multi_year', long_term: 'multi_year', multi_year: 'multi_year',
    past: 'historical', history: 'historical', historical: 'historical',
    atemporal: 'timeless_reference', timeless: 'timeless_reference', timeless_reference: 'timeless_reference' } as const)[rawHorizon] ?? rawHorizon
  if (horizon !== rawHorizon) appliedRules.push(`horizon:${rawHorizon}->${horizon}`)

  const rawIntervention = typeof input.intervention === 'string' ? token(input.intervention, 'none') : input.intervention
  const intervention = rawIntervention === false || rawIntervention === 'false' || rawIntervention === 'none'
    ? false
    : rawIntervention === true || rawIntervention === 'true'
      ? true
      : rawIntervention
  if (intervention !== rawIntervention) appliedRules.push(`intervention:${String(rawIntervention)}->${String(intervention)}`)

  const rawEntitlement = token(input.entitlement, 'native')
  const entitlement = rawEntitlement === 'reference' ? 'public_disclosed' : rawEntitlement
  if (entitlement !== rawEntitlement) appliedRules.push(`entitlement:${rawEntitlement}->${entitlement}`)

  if (intent === 'domain_assessment' && depth === 'deepdive' && domains.length === 1 && DEEP_DOMAIN_INTENTS[domains[0]!]) {
    const resolved = DEEP_DOMAIN_INTENTS[domains[0]!]!
    appliedRules.push(`intent:domain_assessment+${domains[0]}+deepdive->${resolved}`)
    intent = resolved
  }

  const scope: InquiryScopeTuple = { intent, domains, width, depth, horizon, intervention, entitlement }
  const normalizedScopeHash = stableFingerprint(scope)
  return {
    scope,
    receipt: {
      normalization_version: INQUIRY_SCOPE_NORMALIZATION_VERSION,
      applied_rules: uniqueSorted(appliedRules),
      normalized_scope_hash: normalizedScopeHash,
    },
  }
}
