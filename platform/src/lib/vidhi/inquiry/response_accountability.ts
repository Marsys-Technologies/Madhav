import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type {
  InquiryContract,
  InquiryFactRegister,
  InquiryRegisteredFact,
  InquiryResponseAccountability,
  InquiryResponseCoverageReceipt,
  InquiryResponseDeliveryPart,
} from './types'

const HASH_RE = /^sha256:[a-f0-9]{64}$/

function uniqueSorted(values: readonly string[]): string[] {
  return [...new Set(values)].sort()
}

function factIdentity(kind: InquiryRegisteredFact['kind'], contract: InquiryContract, sourceId: string): string {
  return `fact:${stableFingerprint({ kind, semantic_contract_hash: contract.semantic_contract_hash, source_id: sourceId }).slice('sha256:'.length)}`
}

/**
 * Build the response denominator independently from the synthesizer. Required
 * deterministic-floor and omission-challenger obligations therefore cannot be
 * dropped merely because the response author never mentioned them.
 */
export function buildInquiryFactRegister(contract: InquiryContract): InquiryFactRegister {
  const validationErrors: string[] = []
  const obligationIds = new Set<string>()
  const facts: InquiryRegisteredFact[] = []

  for (const obligation of contract.obligations) {
    if (obligationIds.has(obligation.obligation_id)) {
      validationErrors.push(`duplicate obligation ${obligation.obligation_id}`)
    }
    obligationIds.add(obligation.obligation_id)
    if (obligation.materiality === 'required'
      && (obligation.disposition === 'served' || obligation.disposition === 'empty')
      && obligation.evidence_refs.length === 0) {
      validationErrors.push(`required obligation ${obligation.obligation_id} lacks evidence refs`)
    }
    facts.push({
      fact_id: factIdentity('obligation', contract, obligation.obligation_id),
      kind: 'obligation',
      obligation_id: obligation.obligation_id,
      frontier_id: null,
      materiality: obligation.materiality,
      meaning: {
        label: obligation.label,
        rationale: obligation.rationale,
        scu_ids: uniqueSorted(obligation.scu_ids),
        disposition: obligation.disposition,
      },
      evidence_refs: uniqueSorted(obligation.evidence_refs),
    })
  }

  const frontierIds = new Set<string>()
  for (const frontier of contract.material_frontier) {
    if (frontierIds.has(frontier.frontier_id)) validationErrors.push(`duplicate frontier ${frontier.frontier_id}`)
    frontierIds.add(frontier.frontier_id)
    facts.push({
      fact_id: factIdentity('frontier', contract, frontier.frontier_id),
      kind: 'frontier',
      obligation_id: null,
      frontier_id: frontier.frontier_id,
      materiality: frontier.materiality,
      meaning: {
        label: `Evidence frontier for ${frontier.scu_id}`,
        rationale: frontier.reason,
        scu_ids: [frontier.scu_id],
        disposition: frontier.disposition,
      },
      evidence_refs: frontier.source_ref ? [frontier.source_ref] : [],
    })
  }

  const normalizedFacts = [...facts].sort((a, b) => a.fact_id.localeCompare(b.fact_id))
  if (new Set(normalizedFacts.map((fact) => fact.fact_id)).size !== normalizedFacts.length) {
    validationErrors.push('duplicate fact identity')
  }
  const normalized = {
    register_version: 'inquiry-fact-register-v1' as const,
    contract_id: contract.contract_id,
    semantic_contract_hash: contract.semantic_contract_hash,
    facts: normalizedFacts,
    required_fact_ids: normalizedFacts.filter((fact) => fact.materiality === 'required').map((fact) => fact.fact_id),
    validation_errors: uniqueSorted(validationErrors),
  }
  return { ...normalized, register_hash: stableFingerprint(normalized) }
}

export function inquiryResponsePartContentHash(
  register: InquiryFactRegister,
  factIds: readonly string[],
  kind: InquiryResponseDeliveryPart['kind'],
  exclusionReason: string | null = null,
): string {
  const factsById = new Map(register.facts.map((fact) => [fact.fact_id, fact]))
  return stableFingerprint({
    kind,
    facts: uniqueSorted(factIds).map((factId) => factsById.get(factId) ?? { fact_id: factId, unresolved: true }),
    exclusion_reason: exclusionReason,
  })
}

export function buildResponseCoverageReceipt(args: {
  contract: InquiryContract
  fact_register: InquiryFactRegister
  delivery_parts: readonly InquiryResponseDeliveryPart[]
}): InquiryResponseCoverageReceipt {
  const { contract } = args
  const expectedRegister = buildInquiryFactRegister(contract)
  const suppliedRegister = args.fact_register
  const register = expectedRegister
  const factsById = new Map(register.facts.map((fact) => [fact.fact_id, fact]))
  const invalid: string[] = [...register.validation_errors]
  const { register_hash: suppliedHash, ...suppliedProjection } = suppliedRegister
  if (suppliedRegister.contract_id !== contract.contract_id
    || suppliedRegister.semantic_contract_hash !== contract.semantic_contract_hash
    || suppliedHash !== stableFingerprint(suppliedProjection)
    || suppliedHash !== expectedRegister.register_hash) {
    invalid.push('fact register does not match the complete contract-derived denominator')
  }
  const delivered = new Set<string>()
  const excluded = new Set<string>()
  const partIds = new Set<string>()
  let synthesisPresent = false

  for (const part of [...args.delivery_parts].sort((a, b) => a.part_id.localeCompare(b.part_id))) {
    if (partIds.has(part.part_id)) invalid.push(`duplicate delivery part ${part.part_id}`)
    partIds.add(part.part_id)
    if (!part.part_id.trim()) invalid.push('delivery part id is empty')
    if (!HASH_RE.test(part.content_hash)) invalid.push(`delivery part ${part.part_id} has invalid content hash`)
    const expectedPartHash = inquiryResponsePartContentHash(
      register,
      part.fact_ids,
      part.kind,
      part.exclusion_reason,
    )
    if (part.kind !== 'prose' && part.content_hash !== expectedPartHash) {
      invalid.push(`delivery part ${part.part_id} content does not match its fact claims`)
    }
    if (part.kind === 'prose' && part.fact_ids.length > 0) {
      invalid.push(`prose delivery part ${part.part_id} cannot self-attest semantic fact coverage`)
    }
    if (part.kind === 'prose' && HASH_RE.test(part.content_hash) && part.fact_ids.length === 0) {
      synthesisPresent = true
    }
    for (const factId of uniqueSorted(part.fact_ids)) {
      const fact = factsById.get(factId)
      if (!fact) {
        invalid.push(`unknown fact ${factId}`)
        continue
      }
      if (part.kind === 'permitted_exclusion') {
        if (fact.materiality === 'required') {
          invalid.push(`required fact ${factId} cannot be excluded`)
          continue
        }
        if (!part.exclusion_reason?.trim()) {
          invalid.push(`excluded fact ${factId} lacks a reason`)
          continue
        }
        excluded.add(factId)
      } else {
        delivered.add(factId)
      }
    }
  }

  for (const factId of delivered) {
    if (excluded.has(factId)) {
      invalid.push(`fact ${factId} is both delivered and excluded`)
      excluded.delete(factId)
    }
  }

  const allFactIds = register.facts.map((fact) => fact.fact_id)
  const requiredFactIds = register.required_fact_ids
  const missingFactIds = allFactIds.filter((factId) => !delivered.has(factId) && !excluded.has(factId))
  const missingRequiredFactIds = requiredFactIds.filter((factId) => !delivered.has(factId))
  const unresolvedObligationIds = contract.obligations
    .filter((obligation) => obligation.materiality === 'required'
      && !['served', 'empty', 'not_applicable'].includes(obligation.disposition))
    .map((obligation) => obligation.obligation_id)
    .sort()
  const frontierIds = contract.material_frontier
    .filter((frontier) => frontier.materiality === 'required'
      && (frontier.disposition === 'open' || frontier.disposition === 'capped'))
    .map((frontier) => frontier.frontier_id)
    .sort()
  const nextActionIds = contract.plan_items
    .filter((item) => item.state === 'ready')
    .map((item) => item.item_id)
    .sort()
  const blockedItemIds = contract.plan_items
    .filter((item) => item.state === 'blocked')
    .map((item) => item.item_id)
    .sort()
  const exhausted = contract.status === 'BLOCKED'
    || (contract.iteration >= contract.max_iterations
      && (unresolvedObligationIds.length > 0 || frontierIds.length > 0))
  const invalidDeliveryClaims = uniqueSorted(invalid)
  const canComplete = contract.status === 'COMPLETE'
    && synthesisPresent
    && invalidDeliveryClaims.length === 0
    && missingFactIds.length === 0
    && missingRequiredFactIds.length === 0
    && frontierIds.length === 0
  const status = canComplete ? 'COMPLETE' as const
    : exhausted ? 'BLOCKED' as const
      : 'INCOMPLETE_RESUMABLE' as const
  const normalized = {
    receipt_version: 'inquiry-response-coverage-v1' as const,
    contract_id: contract.contract_id,
    semantic_contract_hash: contract.semantic_contract_hash,
    fact_register_hash: register.register_hash,
    status,
    coverage: {
      synthesis_present: synthesisPresent,
      all_total: allFactIds.length,
      all_delivered: delivered.size,
      all_permitted_exclusions: excluded.size,
      required_total: requiredFactIds.length,
      required_delivered: requiredFactIds.filter((factId) => delivered.has(factId)).length,
    },
    delivered_fact_ids: uniqueSorted([...delivered]),
    permitted_exclusion_fact_ids: uniqueSorted([...excluded]),
    missing_fact_ids: missingFactIds,
    missing_required_fact_ids: missingRequiredFactIds,
    delivery_part_ids: uniqueSorted([...partIds]),
    invalid_delivery_claims: invalidDeliveryClaims,
    continuation: {
      iteration: contract.iteration,
      max_iterations: contract.max_iterations,
      exhausted,
      next_action_ids: nextActionIds,
      blocked_item_ids: blockedItemIds,
      unresolved_obligation_ids: unresolvedObligationIds,
      frontier_ids: frontierIds,
    },
    resume_required: !canComplete,
  }
  return { ...normalized, receipt_hash: stableFingerprint(normalized) }
}

/**
 * Deliver the complete bounded fact register as an explicit structured
 * findings part beside prose. This prevents prose compression from becoming
 * an unobservable omission while retaining the prose as the reader-facing
 * synthesis. An incomplete evidence contract remains incomplete here.
 */
export function buildStructuredResponseAccountability(
  contract: InquiryContract,
  options: { response_text?: string | null } = {},
): InquiryResponseAccountability {
  const factRegister = buildInquiryFactRegister(contract)
  const deliveryPart: InquiryResponseDeliveryPart = {
    part_id: `structured-findings:${factRegister.register_hash}`,
    kind: 'structured_findings',
    content_hash: inquiryResponsePartContentHash(
      factRegister,
      factRegister.facts.map((fact) => fact.fact_id),
      'structured_findings',
    ),
    fact_ids: factRegister.facts.map((fact) => fact.fact_id),
    exclusion_reason: null,
  }
  const responseText = options.response_text?.trim() ?? ''
  const prosePart: InquiryResponseDeliveryPart | null = responseText
    ? {
        part_id: `prose:${stableFingerprint(responseText)}`,
        kind: 'prose',
        content_hash: stableFingerprint(responseText),
        fact_ids: [],
        exclusion_reason: null,
      }
    : null
  const deliveryParts = prosePart ? [deliveryPart, prosePart] : [deliveryPart]
  return {
    accountability_version: 'inquiry-response-accountability-v1',
    fact_register: factRegister,
    delivery_parts: deliveryParts,
    response_coverage_receipt: buildResponseCoverageReceipt({
      contract,
      fact_register: factRegister,
      delivery_parts: deliveryParts,
    }),
  }
}
