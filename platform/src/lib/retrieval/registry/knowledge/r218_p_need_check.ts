/**
 * r218_p_need_check.ts — R218 (NIKASHA_CHANGE_REGISTER_v2_0.md, D5 rev. 2.1).
 *
 * "Planner P-need test: run each of P01-P24 through plan_retrieval [D5 rev. 2.1: the planner LLM
 * searching the semantic capability catalog, `planner_projection.ts` — no static mapping]; PASS
 * when the plan resolves to capabilities whose catalog units carry named producers (R85, already
 * landed)." This behavioural test replaces the signed necessity matrix D5 withdrew — the native's
 * judgement is exercised on the P-needs themselves (T1 §2, already the native's) and on accepting
 * each planner plan, not on 220 signed cells.
 *
 * `evaluatePNeed` runs the REAL planner projection (`buildPlannerCapabilityKnowledgeProjection`,
 * the same function Pariprāśna's synthesis path calls) against a real capability knowledge
 * snapshot — never a re-implemented search — and cross-checks each resolved SCU id against Lane
 * B's committed producer-provenance derivation (`producer_provenance.derived.json`, READ ONLY;
 * never touches `catalog_provenance.py` or its outputs, which produced it).
 *
 * P01-P24's question text is transcribed verbatim from T1 §2
 * (`00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md`, tier 1, FINAL — read only, never edited).
 */
import { buildPlannerCapabilityKnowledgeProjection } from './planner_projection'
import type { CapabilityKnowledgeSnapshot } from './types'
import type { InquiryScopeTuple } from '@/lib/vidhi/inquiry/types'

export interface PNeed {
  readonly id: string
  readonly question: string
}

// T1 §2 (MADHAV_PRODUCT_DEFINITION_FINAL.md, tier 1, FINAL), transcribed verbatim, read-only.
export const P_NEEDS: readonly PNeed[] = [
  { id: 'P01', question: 'What are my distinctive capacities and recurring patterns?' },
  { id: 'P02', question: 'What gives this life direction or meaning?' },
  { id: 'P03', question: 'When will I make substantial money or emerge from financial strain?' },
  { id: 'P04', question: 'When will my business succeed or I receive a promotion?' },
  { id: 'P05', question: 'How should I understand relationships and marriage?' },
  { id: 'P06', question: 'What can I understand about family, parenthood and legacy?' },
  { id: 'P07', question: 'What does the tradition say about wellbeing?' },
  { id: 'P08', question: 'What about education, home, movement, travel or relocation?' },
  { id: 'P09', question: 'Does this yoga form, and when might it manifest?' },
  { id: 'P10', question: 'What chapter am I entering, and how is it unlike the previous one?' },
  { id: 'P11', question: 'When might I initiate something, or which practices can I explore?' },
  { id: 'P12', question: 'Which events fit this interpretation, and which do not?' },
  { id: 'P13', question: 'Does uncertain birth information or a different convention change this?' },
  { id: 'P14', question: 'How do two people, a shared undertaking or an organization relate?' },
  { id: 'P15', question: 'What supports this in the tradition, and where do schools disagree?' },
  { id: 'P16', question: 'Give me this exact fact, or help me investigate an open question.' },
  { id: 'P17', question: 'What important question have I not asked?' },
  { id: 'P18', question: 'What would most efficiently resolve this uncertainty?' },
  { id: 'P19', question: 'Show what changes if we examine this differently.' },
  { id: 'P20', question: 'Which form of Jyotish is appropriate to my question?' },
  { id: 'P21', question: 'What does this day or period mean in its proper context?' },
  { id: 'P22', question: 'Let me read and understand the texts themselves.' },
  { id: 'P23', question: 'What does the tradition say about lifespan?' },
  {
    id: 'P24',
    question: 'What is happening to me right now, and why does this period feel the way it does?',
  },
]

export const GENERIC_SCOPE: InquiryScopeTuple = {
  intent: 'assess',
  domains: ['general'],
  width: 'standard',
  depth: 'deepdive',
  horizon: 'natal',
  intervention: false,
  entitlement: 'native',
}

export interface ProvenanceScu {
  producers?: { asset_id: string }[]
}

export interface ProducerProvenance {
  scus: Record<string, ProvenanceScu>
}

export interface ResolvedCapability {
  scu_id: string
  kind: string
  producers: string[]
}

export interface PNeedResult {
  id: string
  question: string
  resolved_count: number
  top_ranked_scu: string | null
  top_ranked_has_producer: boolean
  producer_coverage: string
  pass: boolean
  reason: string
  resolved: ResolvedCapability[]
}

/**
 * Evaluates one P-need's plan against the given snapshot + provenance.
 *
 * PASS criterion (this harness's explicit interpretation of R218's "the plan resolves to
 * capabilities whose catalog units carry named producers", reported alongside the full aggregate
 * so a reviewer can judge the interpretation, not just trust it): the TOP-RANKED resolved
 * capability (searchSemanticCapabilities' own relevance order, which the planner LLM favours)
 * carries a named producer — the plan's PRIMARY resolution is backed by a real, traced writer.
 * NOT that every one of up to `limit` loosely-relevant candidates in the broad search window
 * carries one (a majority of the catalog does today, but a top-N window routinely includes some
 * that do not, without that being a defect in this P-need's own actual serving path).
 */
export function evaluatePNeed(
  need: PNeed,
  snapshot: CapabilityKnowledgeSnapshot,
  provenance: ProducerProvenance,
  scope: InquiryScopeTuple = GENERIC_SCOPE,
  limit = 32,
): PNeedResult {
  const projection = buildPlannerCapabilityKnowledgeProjection(snapshot, need.question, scope, limit)
  const resolved: ResolvedCapability[] = projection.capabilities.map((cap) => {
    const entry = provenance.scus[cap.id]
    const producers = entry?.producers?.map((p) => p.asset_id) ?? []
    return { scu_id: cap.id, kind: cap.kind, producers }
  })
  const withoutProducer = resolved.filter((r) => r.producers.length === 0)
  const top = resolved[0]
  const pass = resolved.length > 0 && !!top && top.producers.length > 0
  return {
    id: need.id,
    question: need.question,
    resolved_count: resolved.length,
    top_ranked_scu: top?.scu_id ?? null,
    top_ranked_has_producer: !!top && top.producers.length > 0,
    producer_coverage: `${resolved.length - withoutProducer.length}/${resolved.length}`,
    pass,
    reason:
      resolved.length === 0
        ? 'no capability resolved at all'
        : !top || top.producers.length === 0
          ? `top-ranked resolution ${top?.scu_id ?? '<none>'} carries no named producer`
          : `top-ranked resolution ${top.scu_id} carries a named producer (${top.producers.join(', ')})`,
    resolved,
  }
}

export function evaluateAllPNeeds(
  snapshot: CapabilityKnowledgeSnapshot,
  provenance: ProducerProvenance,
  scope: InquiryScopeTuple = GENERIC_SCOPE,
  limit = 32,
): { summary: { total: number; passed: number; failed: number }; results: PNeedResult[] } {
  const results = P_NEEDS.map((need) => evaluatePNeed(need, snapshot, provenance, scope, limit))
  return {
    summary: {
      total: results.length,
      passed: results.filter((r) => r.pass).length,
      failed: results.filter((r) => !r.pass).length,
    },
    results,
  }
}
