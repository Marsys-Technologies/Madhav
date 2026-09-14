import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import type { InquiryScopeTuple, OmissionChallengeReceipt, OmissionFinding } from './types'

const RULES = [
  { rule_id: 'OMIT-BHAVA-BHAVAT', terms: ['house', 'bhava', 'wealth', 'career', 'marriage', 'health'], scu_id: 'scu.catalog.judgment_query', rationale: 'Material domain reads require bhāvat-bhāvam / bhava-lord cross-checks.' },
  { rule_id: 'OMIT-YOGA-CANCEL', terms: ['yoga', 'wealth', 'prosperity'], scu_id: 'scu.yoga.firing_and_cancellation', rationale: 'A yoga label is incomplete without firing, strength, and cancellation.' },
  { rule_id: 'OMIT-VARGA-CONTRA', terms: ['wealth', 'career', 'marriage', 'health', 'varga'], scu_id: 'scu.catalog.get_divisionals', rationale: 'Operative-varga contradiction can reverse a natal-only claim.' },
  { rule_id: 'OMIT-INHIBITOR', terms: ['wealth', 'prosperity', 'success', 'outlook'], scu_id: 'scu.bodha.mechanism.network', rationale: 'Supportive promise must be checked against inhibiting mechanisms.' },
  { rule_id: 'OMIT-TEMPORAL-PREREQ', terms: ['now', 'current', 'when', 'timing', 'period', 'outlook', 'wealth'], scu_id: 'scu.kala.temporal_activation', rationale: 'Current or prospective claims require temporal prerequisites.' },
  { rule_id: 'OMIT-CROSS-DOMAIN', terms: ['complete', 'deep', 'prosperity', 'life'], scu_id: 'scu.catalog.query_contradictions', rationale: 'Deep inquiry must surface cross-domain contradiction and convergence.' },
] as const

export function challengeInquirySelection(args: {
  readonly snapshot: CapabilityKnowledgeSnapshot
  readonly question: string
  readonly scope: InquiryScopeTuple
  readonly selected_scu_ids: readonly string[]
}): OmissionChallengeReceipt {
  const available = new Set(args.snapshot.scus.map((scu) => scu.scu_id))
  const selected = new Set(args.selected_scu_ids)
  const semanticQuery = `${args.question} ${args.scope.intent} ${args.scope.domains.join(' ')}`.toLowerCase()
  const findings: OmissionFinding[] = []

  for (const rule of RULES) {
    if (rule.terms.some((term) => semanticQuery.includes(term)) && available.has(rule.scu_id) && !selected.has(rule.scu_id)) {
      findings.push({
        rule_id: rule.rule_id,
        severity: 'material',
        missing_scu_id: rule.scu_id,
        rationale: rule.rationale,
        source: 'rule',
        relation: null,
        source_ref: `omission-rule:${rule.rule_id}`,
      })
    }
  }

  for (const edge of args.snapshot.edges) {
    if (!edge.edge_source || !edge.source_ref || !selected.has(edge.from_scu_id)
      || selected.has(edge.to_scu_id) || !available.has(edge.to_scu_id)
      || (edge.relation !== 'requires' && edge.relation !== 'contradicts')) continue
    findings.push({
      rule_id: `GRAPH-${edge.relation.toUpperCase()}-${edge.from_scu_id}->${edge.to_scu_id}`,
      severity: 'material',
      missing_scu_id: edge.to_scu_id,
      rationale: edge.rationale,
      source: 'graph',
      relation: edge.relation,
      source_ref: edge.source_ref,
    })
  }

  findings.sort((a, b) => `${a.rule_id}\u0000${a.missing_scu_id}`.localeCompare(`${b.rule_id}\u0000${b.missing_scu_id}`))
  const normalized = {
    challenge_version: 'inquiry-omission-challenger-v1' as const,
    selected_scu_ids: [...selected].sort(),
    findings,
  }
  return { ...normalized, challenge_hash: stableFingerprint(normalized) }
}
