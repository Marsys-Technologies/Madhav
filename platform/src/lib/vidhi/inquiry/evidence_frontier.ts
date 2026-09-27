/**
 * Evidence-driven frontier (Pūrṇa R2B.4 / review RC-5.4).
 *
 * A late hop must be able to add a DIFFERENT capability because of what was observed — a yoga
 * that fired with an active cancellation calls for the cancellation analysis and the bhāva
 * judgment; a debilitated graha calls for the nīcha-bhaṅga check; a firing that carries its
 * activation periods calls for those dashas. Pagination alone only ever re-pages the same SCU.
 *
 * Each rule is deterministic, keyed on explicit structured fields (never prose), and names an
 * SCU that must exist in the pinned snapshot. A rule never proposes the observed SCU itself or
 * a capability the contract already plans, and the result is bounded. The frontier item it
 * yields is admitted only through the existing successor gate: a fresh contract, compiled by
 * the deterministic compiler from a served, evidence-bearing observation — never a tool the
 * model chose.
 */
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import type { InquiryContract } from './types'

export interface EvidenceFrontierRule {
  readonly rule_id: string
  readonly target_scu_ids: readonly string[]
  readonly matches: (row: Readonly<Record<string, unknown>>) => boolean
}

const MAX_DISCOVERED_PER_OBSERVATION = 4
const MAX_WALKED_OBJECTS = 2_000

function nonEmptyArray(value: unknown): boolean {
  return Array.isArray(value) && value.length > 0
}

export const EVIDENCE_FRONTIER_RULES: readonly EvidenceFrontierRule[] = [
  {
    // A fired yoga whose bhaṅga (cancellation) is active: the cancellation and the bhāva it
    // modifies must be analysed, not just the firing.
    rule_id: 'evidence_bhanga_active',
    target_scu_ids: ['scu.yoga.firing_and_cancellation', 'scu.catalog.judgment_query'],
    matches: (row) => row['bhanga_active'] === true,
  },
  {
    // A debilitated graha requires the nīcha-bhaṅga (cancellation of debilitation) check.
    rule_id: 'evidence_debilitation_requires_nichabhanga_check',
    target_scu_ids: ['scu.yoga.firing_and_cancellation'],
    matches: (row) => row['dignity_state'] === 'debilitated'
      || (row['fact_key'] === 'dignity_state' && row['fact_value_text'] === 'debilitated'),
  },
  {
    // A firing that carries its activation periods requires those dashas for timing.
    rule_id: 'evidence_activation_periods_require_dashas',
    target_scu_ids: ['scu.catalog.get_dashas'],
    matches: (row) => nonEmptyArray(row['activation_dasha_periods']) || nonEmptyArray(row['activation_dasha_lords']),
  },
  {
    // A mechanism that names the houses it links requires the judgment of those bhāvas.
    rule_id: 'evidence_mechanism_names_houses',
    target_scu_ids: ['scu.catalog.judgment_query'],
    matches: (row) => typeof row['mechanism_class'] === 'string'
      && (nonEmptyArray(row['houses']) || nonEmptyArray(row['house_numbers']) || typeof row['house'] === 'number'),
  },
]

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Structured objects inside an evidence payload, including JSON carried in `content` strings. */
function structuredObjects(payload: unknown): Record<string, unknown>[] {
  const out: Record<string, unknown>[] = []
  const stack: unknown[] = [payload]
  while (stack.length && out.length < MAX_WALKED_OBJECTS) {
    const value = stack.pop()
    if (typeof value === 'string') {
      const trimmed = value.trim()
      if ((trimmed.startsWith('{') || trimmed.startsWith('[')) && trimmed.length < 1_000_000) {
        try { stack.push(JSON.parse(trimmed)) } catch { /* prose, not structure */ }
      }
      continue
    }
    if (Array.isArray(value)) { for (const item of value) stack.push(item); continue }
    if (isRecord(value)) {
      out.push(value)
      for (const child of Object.values(value)) stack.push(child)
    }
  }
  return out
}

export interface DiscoveredEvidenceFrontier {
  readonly scu_id: string
  readonly materiality: 'required' | 'supporting'
  readonly reason: string
}

/**
 * Derive cross-capability frontier items from one observed item's evidence payload. The
 * materiality follows the observed item's obligations (a required obligation's evidence
 * makes its follow-up required), mirroring the pagination frontier.
 */
export function deriveEvidenceFrontier(args: {
  readonly contract: InquiryContract
  readonly item_id: string
  readonly evidence_payload: unknown
  readonly snapshot: CapabilityKnowledgeSnapshot
}): DiscoveredEvidenceFrontier[] {
  const item = args.contract.plan_items.find((candidate) => candidate.item_id === args.item_id)
  if (!item) return []
  const planned = new Set([
    ...args.contract.obligations.flatMap((obligation) => obligation.scu_ids),
    ...args.contract.plan_items.map((candidate) => candidate.scu_id),
    ...args.contract.material_frontier.map((frontier) => frontier.scu_id),
  ])
  const known = new Set(args.snapshot.scus.map((scu) => scu.scu_id))
  const materiality = args.contract.obligations.some((obligation) => item.obligation_ids.includes(obligation.obligation_id)
    && obligation.materiality === 'required') ? 'required' as const : 'supporting' as const
  const rows = structuredObjects(args.evidence_payload)
  const discovered = new Map<string, DiscoveredEvidenceFrontier>()
  for (const rule of EVIDENCE_FRONTIER_RULES) {
    if (!rows.some((row) => rule.matches(row))) continue
    for (const scuId of rule.target_scu_ids) {
      if (scuId === item.scu_id || planned.has(scuId) || !known.has(scuId) || discovered.has(scuId)) continue
      discovered.set(scuId, {
        scu_id: scuId,
        materiality,
        reason: `${rule.rule_id}: observed in ${item.item_id} (${item.scu_id})`,
      })
    }
  }
  return [...discovered.values()].slice(0, MAX_DISCOVERED_PER_OBSERVATION)
}
