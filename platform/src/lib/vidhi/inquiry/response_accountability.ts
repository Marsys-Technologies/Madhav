import { canonicalize, stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import type {
  InquiryContract,
  InquiryFactRegister,
  InquiryRegisteredFact,
  InquiryResponseAccountability,
  InquiryResponseCoverageReceipt,
  InquiryResponseDeliveryPart,
} from './types'
import { inquiryAuthorizationHashes, validateInquiryContract } from './compiler'
import { indexInquiryEvidenceBindings } from './managed_bridge'
import { extractInquirySemanticFindings } from './pagination'

const HASH_RE = /^sha256:[a-f0-9]{64}$/
// `[[F7]]` or the Portal citation family `⟦cite: F7⟧` / `[[cite: F7]]` (case/spacing tolerant).
const CITATION_MARKER_RE = /(?:\[\[|\u27E6)\s*(?:cite\s*:\s*)?(F[0-9]+)\s*(?:\]\]|\u27E7)/gi
const UNKNOWN_CITATION_PREFIX = 'unknown-citation:'

/**
 * Short, stable citation handles for the register's findings (`F1`…`Fn` in fact-id order).
 * They depend only on the register, so the evidence shown to synthesis, the prose citations,
 * and the coverage receipt all resolve the same handle to the same finding (RC-6.3).
 */
export function inquiryFindingCitationHandles(register: InquiryFactRegister): ReadonlyMap<string, string> {
  return new Map(register.facts
    .filter((fact) => fact.kind === 'finding')
    .map((fact, index) => [fact.fact_id, `F${index + 1}`]))
}

/** The marker a synthesis cites a finding with, e.g. `[[F7]]`. */
export function inquiryCitationMarker(handle: string): string {
  return `[[${handle}]]`
}

/** The row field that carries a finding's citation handle in evidence shown to synthesis. */
export const INQUIRY_CITATION_FIELD = '_cite'

/**
 * Annotate evidence payloads with register citation handles, for display to a synthesis model.
 * Each semantic row that is a register finding gains `_cite: "Fn"`; the canonical payloads (and
 * therefore every evidence hash) are untouched — the returned payloads are copies for display.
 * The handles come from the same register the coverage receipt rebuilds, so a cited handle can
 * only ever resolve to the finding the model was shown.
 */
export function annotateInquiryEvidenceForSynthesis(
  contract: InquiryContract,
  evidencePayloads: readonly unknown[],
  knowledgeSnapshot?: CapabilityKnowledgeSnapshot,
): { register: InquiryFactRegister; handles: ReadonlyMap<string, string>; payloads: unknown[] } {
  const register = buildInquiryFactRegister(contract, evidencePayloads, knowledgeSnapshot)
  const handles = inquiryFindingCitationHandles(register)
  const bindings = knowledgeSnapshot ? indexInquiryEvidenceBindings(knowledgeSnapshot, contract, evidencePayloads) : {}
  const payloads = evidencePayloads.map((payload) => {
    const copy: unknown = payload === undefined ? undefined : JSON.parse(JSON.stringify(payload))
    const binding = bindings[stableFingerprint(payload)]
    const extraction = extractInquirySemanticFindings(binding, copy)
    const toolName = copy && typeof copy === 'object' ? (copy as { tool_name?: unknown }).tool_name : undefined
    const sourceCoordinate = binding?.binding_id ?? (typeof toolName === 'string' ? `opaque-tool:${toolName}` : 'opaque-unbound')
    extraction.rows.forEach((row, index) => {
      if (!row || typeof row !== 'object' || Array.isArray(row)) return
      const content = normalizedFindingContent(row, extraction.mode)
      const coordinate = `${sourceCoordinate}:${extraction.result_collection_path ?? 'opaque'}:${stableFingerprint(content)}`
      const handle = handles.get(factIdentity('finding', contract, coordinate))
      // The extracted collection is the copy's own array, so this annotates the display copy in place.
      if (handle) (extraction.rows as unknown[])[index] = { [INQUIRY_CITATION_FIELD]: handle, ...(row as Record<string, unknown>) }
    })
    return copy
  })
  return { register, handles, payloads }
}

/** Handles that actually appear in text shown to a synthesis model (after any budget trim). */
export function visibleInquiryCitationHandles(shownEvidenceText: string): string[] {
  return uniqueSorted([...shownEvidenceText.matchAll(/"_cite":\s*"(F[0-9]+)"/g)].map((match) => match[1]!))
}

function citedHandles(text: string): string[] {
  return uniqueSorted([...text.matchAll(CITATION_MARKER_RE)].map((match) => match[1]!.toUpperCase()))
}

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
function normalizedFindingContent(
  value: unknown,
  mode: ReturnType<typeof extractInquirySemanticFindings>['mode'],
): string {
  if (mode === 'opaque_adapter_items'
    && typeof value === 'object' && value !== null && 'content' in value
    && typeof (value as { content?: unknown }).content === 'string') {
    return (value as { content: string }).content.trim()
  }
  return canonicalize(value) ?? String(value)
}

export function buildInquiryFactRegister(
  contract: InquiryContract,
  evidencePayloads: readonly unknown[] = [],
  knowledgeSnapshot?: CapabilityKnowledgeSnapshot,
): InquiryFactRegister {
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
      obligation_ids: [obligation.obligation_id],
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
      normalized_content: null,
    })
  }

  const frontierIds = new Set<string>()
  for (const frontier of contract.material_frontier) {
    if (frontierIds.has(frontier.frontier_id)) validationErrors.push(`duplicate frontier ${frontier.frontier_id}`)
    frontierIds.add(frontier.frontier_id)
    facts.push({
      fact_id: factIdentity('frontier', contract, frontier.frontier_id),
      kind: 'frontier',
      obligation_ids: [],
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
      normalized_content: null,
    })
  }

  const payloadByHash = new Map(evidencePayloads.map((payload) => [stableFingerprint(payload), payload]))
  const snapshotMatchesContract = !knowledgeSnapshot
    || (knowledgeSnapshot.content_hash === contract.capability_content_hash
      && knowledgeSnapshot.compatibility_version === contract.capability_compatibility_version)
  if (!snapshotMatchesContract) {
    validationErrors.push('knowledge snapshot does not match the inquiry contract capability identity')
  }
  const evidenceBindings = knowledgeSnapshot && snapshotMatchesContract
    ? indexInquiryEvidenceBindings(knowledgeSnapshot, contract, evidencePayloads)
    : {}
  const obligationsByPayload = new Map<string, InquiryContract['obligations'][number][]>()
  const evidenceRefsByPayload = new Map<string, string[]>()
  for (const obligation of contract.obligations) {
    for (const evidenceRef of uniqueSorted(obligation.evidence_refs)) {
      const payloadHash = evidenceHashFromRef(evidenceRef)
      if (!payloadHash) continue
      obligationsByPayload.set(payloadHash, [...(obligationsByPayload.get(payloadHash) ?? []), obligation])
      evidenceRefsByPayload.set(payloadHash, [...(evidenceRefsByPayload.get(payloadHash) ?? []), evidenceRef])
    }
  }

  const findingsBySemanticCoordinate = new Map<string, {
    content: string
    row_hash: string
    mode: ReturnType<typeof extractInquirySemanticFindings>['mode']
    result_collection_path: string | null
    obligations: Map<string, InquiryContract['obligations'][number]>
    evidence_refs: Set<string>
  }>()
  for (const payloadHash of [...obligationsByPayload.keys()].sort()) {
    const payload = payloadByHash.get(payloadHash)
    if (payload === undefined) continue
    const obligations = obligationsByPayload.get(payloadHash) ?? []
    const binding = evidenceBindings[payloadHash]
    const extraction = extractInquirySemanticFindings(binding, payload)
    if (extraction.mode === 'reviewed_collection_missing') {
      validationErrors.push(`reviewed result collection ${extraction.result_collection_path} is absent from evidence ${payloadHash}`)
    }
    const toolName = payload && typeof payload === 'object'
      ? (payload as { tool_name?: unknown }).tool_name
      : undefined
    const sourceCoordinate = binding?.binding_id
      ?? (typeof toolName === 'string' ? `opaque-tool:${toolName}` : 'opaque-unbound')
    extraction.rows.map((row) => normalizedFindingContent(row, extraction.mode)).forEach((content) => {
      const rowHash = stableFingerprint(content)
      const semanticCoordinate = `${sourceCoordinate}:${extraction.result_collection_path ?? 'opaque'}:${rowHash}`
      const accumulated = findingsBySemanticCoordinate.get(semanticCoordinate) ?? {
        content,
        row_hash: rowHash,
        mode: extraction.mode,
        result_collection_path: extraction.result_collection_path,
        obligations: new Map(),
        evidence_refs: new Set<string>(),
      }
      obligations.forEach((obligation) => accumulated.obligations.set(obligation.obligation_id, obligation))
      evidenceRefsByPayload.get(payloadHash)?.forEach((ref) => accumulated.evidence_refs.add(ref))
      findingsBySemanticCoordinate.set(semanticCoordinate, accumulated)
    })
  }

  for (const [semanticCoordinate, finding] of [...findingsBySemanticCoordinate.entries()].sort(([a], [b]) => a.localeCompare(b))) {
    const obligations = [...finding.obligations.values()].sort((a, b) => a.obligation_id.localeCompare(b.obligation_id))
    const obligationIds = obligations.map((obligation) => obligation.obligation_id)
    const payloadHashes = uniqueSorted([...finding.evidence_refs].flatMap((ref) => evidenceHashFromRef(ref) ?? []))
    facts.push({
      fact_id: factIdentity('finding', contract, semanticCoordinate),
      kind: 'finding',
      obligation_ids: obligationIds,
      obligation_id: obligationIds.length === 1 ? obligationIds[0]! : null,
      frontier_id: null,
      materiality: obligations.some((obligation) => obligation.materiality === 'required') ? 'required' : 'supporting',
      meaning: {
        label: `Evidence finding for ${obligations.map((obligation) => obligation.label).sort().join(' / ')}`,
        rationale: finding.mode === 'opaque_adapter_items'
          ? `Opaque adapter item from canonical evidence payloads ${payloadHashes.join(', ')}; no independently reviewed result collection path was available.`
          : `Semantic row at reviewed collection ${finding.result_collection_path} in canonical evidence payloads ${payloadHashes.join(', ')}.`,
        scu_ids: uniqueSorted(obligations.flatMap((obligation) => obligation.scu_ids)),
        disposition: obligations.some((obligation) => obligation.disposition === 'served') ? 'served' : obligations[0]?.disposition ?? 'pending',
      },
      evidence_refs: [...uniqueSorted([...finding.evidence_refs]), `result:${finding.row_hash}`],
      normalized_content: finding.content,
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
  evidencePayloadHashes: readonly string[] = [],
  content: string | null = null,
): string {
  const factsById = new Map(register.facts.map((fact) => [fact.fact_id, fact]))
  return stableFingerprint({
    kind,
    facts: uniqueSorted(factIds).map((factId) => factsById.get(factId) ?? { fact_id: factId, unresolved: true }),
    evidence_payload_hashes: uniqueSorted(evidencePayloadHashes),
    content,
    exclusion_reason: exclusionReason,
  })
}

function evidenceHashFromRef(ref: string): string | null {
  const match = ref.match(/sha256:[a-f0-9]{64}$/)
  return match?.[0] ?? null
}

function isCompilerFrontier(item: InquiryContract['material_frontier'][number]): boolean {
  return item.discovered_from === 'independent_omission_challenger'
    || item.reason.startsWith('graph_')
    || item.reason.startsWith('challenger_')
    || item.reason.startsWith('search_hit_')
    || item.reason.startsWith('ai_adjacency_')
}

export function buildResponseCoverageReceipt(args: {
  contract: InquiryContract
  fact_register: InquiryFactRegister
  delivery_parts: readonly InquiryResponseDeliveryPart[]
  evidence_payloads?: readonly unknown[]
  knowledge_snapshot?: CapabilityKnowledgeSnapshot
  response_text?: string | null
}): InquiryResponseCoverageReceipt {
  const { contract } = args
  const expectedRegister = buildInquiryFactRegister(contract, args.evidence_payloads, args.knowledge_snapshot)
  const suppliedRegister = args.fact_register
  const register = expectedRegister
  const factsById = new Map(register.facts.map((fact) => [fact.fact_id, fact]))
  const citationHandles = inquiryFindingCitationHandles(register)
  const invalid: string[] = [...register.validation_errors, ...validateInquiryContract(contract).errors]
  // Compiler frontiers are immutable authorization inputs even after execution
  // absorbs them. Runtime-discovered frontiers are excluded by the compiler's
  // own authorization projection.
  const authorization = inquiryAuthorizationHashes({
    ...contract,
    material_frontier: contract.material_frontier.map((item) => isCompilerFrontier(item)
      ? { ...item, disposition: 'open' as const }
      : item),
  })
  if (authorization.semantic_contract_hash !== contract.semantic_contract_hash
    || authorization.execution_plan_hash !== contract.execution_plan_hash
    || authorization.contract_id !== contract.contract_id) {
    invalid.push('inquiry contract authorization hashes do not match immutable contract content')
  }
  const { register_hash: suppliedHash, ...suppliedProjection } = suppliedRegister
  if (suppliedRegister.contract_id !== contract.contract_id
    || suppliedRegister.semantic_contract_hash !== contract.semantic_contract_hash
    || suppliedHash !== stableFingerprint(suppliedProjection)
    || suppliedHash !== expectedRegister.register_hash) {
    invalid.push('fact register does not match the complete contract-derived denominator')
  }
  const delivered = new Set<string>()
  const excluded = new Set<string>()
  const interpretationMapped = new Set<string>()
  const partIds = new Set<string>()
  let synthesisPresent = false
  const canonicalResponseText = args.response_text ?? ''
  const actualEvidenceHashes = new Set((args.evidence_payloads ?? []).map((payload) => stableFingerprint(payload)))

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
      part.evidence_payload_hashes,
      part.content,
    )
    if (part.kind !== 'prose' && part.content_hash !== expectedPartHash) {
      invalid.push(`delivery part ${part.part_id} content does not match its fact claims`)
    }
    if (part.evidence_payload_hashes.some((hash) => !actualEvidenceHashes.has(hash))) {
      invalid.push(`delivery part ${part.part_id} cites evidence payload not present in canonical response parts`)
    }
    if (part.kind === 'prose') {
      if (!canonicalResponseText.trim() || part.content_hash !== stableFingerprint(canonicalResponseText)) {
        invalid.push(`prose delivery part ${part.part_id} does not match canonical response text`)
      } else {
        synthesisPresent = true
      }
      if (part.evidence_payload_hashes.length > 0) {
        invalid.push(`prose delivery part ${part.part_id} cannot directly carry retrieval payloads`)
      }
      if (part.fact_ids.length > 0 || part.content !== null) {
        invalid.push(`prose delivery part ${part.part_id} cannot self-attest fact or interpretation coverage`)
      }
    }
    if (part.kind === 'finding_interpretation' || part.kind === 'conjoint_interpretation') {
      if (!part.content?.trim() || !canonicalResponseText.includes(part.content)
        || part.content_hash !== expectedPartHash) {
        invalid.push(`finding interpretation ${part.part_id} is not an exact canonical response span`)
      }
      if (part.kind === 'finding_interpretation' && part.fact_ids.length !== 1) {
        invalid.push(`finding interpretation ${part.part_id} must map exactly one finding`)
      }
      if (part.kind === 'conjoint_interpretation' && part.fact_ids.length < 2) {
        invalid.push(`conjoint interpretation ${part.part_id} must map at least two findings`)
      }
    }
    for (const factId of uniqueSorted(part.fact_ids)) {
      const fact = factsById.get(factId)
      if (!fact) {
        invalid.push(factId.startsWith(UNKNOWN_CITATION_PREFIX)
          ? `unknown citation marker ${factId.slice(UNKNOWN_CITATION_PREFIX.length)}`
          : `unknown fact ${factId}`)
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
      } else if (part.kind === 'prose') {
        continue
      } else if (part.kind === 'finding_interpretation' || part.kind === 'conjoint_interpretation') {
        // A finding is interpreted by an exact response span that either restates its canonical
        // content or cites its register handle; a paraphrase without its marker maps nothing.
        const handle = citationHandles.get(factId)
        const cited = handle !== undefined && citedHandles(part.content ?? '').includes(handle)
        if (fact.kind !== 'finding' || !fact.normalized_content
          || !(part.content?.includes(fact.normalized_content) || cited)) {
          invalid.push(`finding interpretation ${part.part_id} does not contain mapped finding ${factId}`)
          continue
        }
        interpretationMapped.add(factId)
      } else {
        const expectedEvidenceHashes = fact.evidence_refs
          .map(evidenceHashFromRef)
          .filter((hash): hash is string => hash !== null)
        if (fact.kind === 'obligation'
          && (fact.meaning.disposition === 'served' || fact.meaning.disposition === 'empty')
          && (expectedEvidenceHashes.length !== fact.evidence_refs.length
            || expectedEvidenceHashes.some((hash) => !part.evidence_payload_hashes.includes(hash)))) {
          invalid.push(`fact ${factId} is not bound to every canonical evidence payload`)
          continue
        }
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
  const interpretationUnmappedFactIds = register.facts
    .filter((fact) => fact.kind === 'finding'
      && delivered.has(fact.fact_id) && !excluded.has(fact.fact_id)
      && !interpretationMapped.has(fact.fact_id))
    .map((fact) => fact.fact_id)
  const unresolvedObligationIds = contract.obligations
    .filter((obligation) => !['served', 'empty', 'not_applicable'].includes(obligation.disposition))
    .map((obligation) => obligation.obligation_id)
    .sort()
  const frontierIds = contract.material_frontier
    .filter((frontier) => frontier.disposition === 'open' || frontier.disposition === 'capped')
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
  const cappedFrontier = contract.material_frontier.some((frontier) => frontier.disposition === 'capped')
  const exhausted = contract.status === 'BLOCKED' || cappedFrontier
    || (contract.iteration >= contract.max_iterations
      && (unresolvedObligationIds.length > 0 || frontierIds.length > 0
        || nextActionIds.length > 0 || blockedItemIds.length > 0))
  const invalidDeliveryClaims = uniqueSorted(invalid)
  const canComplete = contract.status === 'COMPLETE'
    && synthesisPresent
    && invalidDeliveryClaims.length === 0
    && missingFactIds.length === 0
    && missingRequiredFactIds.length === 0
    && interpretationUnmappedFactIds.length === 0
    && unresolvedObligationIds.length === 0
    && frontierIds.length === 0
    && nextActionIds.length === 0
    && blockedItemIds.length === 0
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
      interpretation_mapped: interpretationMapped.size,
    },
    delivered_fact_ids: uniqueSorted([...delivered]),
    permitted_exclusion_fact_ids: uniqueSorted([...excluded]),
    missing_fact_ids: missingFactIds,
    missing_required_fact_ids: missingRequiredFactIds,
    interpretation_unmapped_fact_ids: interpretationUnmappedFactIds,
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
 * Interpretations evidenced by citation markers: each paragraph (an exact span of the
 * response) that cites register handles interprets exactly the findings it cites. A marker
 * naming no registered finding is carried forward so the coverage receipt fails closed on it.
 */
function citedInterpretations(
  register: InquiryFactRegister,
  responseText: string,
): { text: string; fact_ids: readonly string[] }[] {
  const factByHandle = new Map([...inquiryFindingCitationHandles(register)].map(([factId, handle]) => [handle, factId]))
  return responseText.split(/\n{2,}/)
    .filter((span) => span.trim().length > 0)
    .map((span) => ({
      text: span,
      fact_ids: citedHandles(span).map((handle) => factByHandle.get(handle) ?? `${UNKNOWN_CITATION_PREFIX}${handle}`),
    }))
    .filter((item) => item.fact_ids.length > 0)
}

/**
 * Deliver the complete bounded fact register as an explicit structured
 * findings part beside prose. This prevents prose compression from becoming
 * an unobservable omission while retaining the prose as the reader-facing
 * synthesis. An incomplete evidence contract remains incomplete here.
 */
export function buildStructuredResponseAccountability(
  contract: InquiryContract,
  options: {
    response_text?: string | null
    evidence_payloads?: readonly unknown[]
    knowledge_snapshot?: CapabilityKnowledgeSnapshot
    conjoint_interpretations?: readonly { text: string; fact_ids: readonly string[] }[]
    /**
     * Findings the synthesis model was actually shown (handles surviving any budget trim).
     * When supplied, a SUPPORTING finding the model never saw is a permitted exclusion with a
     * visible reason instead of a silent omission; a REQUIRED one stays delivered but
     * uninterpreted, so the reading remains honestly incomplete.
     */
    synthesis_visible_handles?: readonly string[]
  } = {},
): InquiryResponseAccountability {
  const factRegister = buildInquiryFactRegister(contract, options.evidence_payloads, options.knowledge_snapshot)
  const visibleHandles = options.synthesis_visible_handles ? new Set(options.synthesis_visible_handles) : null
  const handlesByFact = inquiryFindingCitationHandles(factRegister)
  const budgetExcludedFactIds = visibleHandles
    ? factRegister.facts
      .filter((fact) => fact.kind === 'finding' && fact.materiality === 'supporting'
        && !visibleHandles.has(handlesByFact.get(fact.fact_id) ?? ''))
      .map((fact) => fact.fact_id)
    : []
  const evidencePayloads = options.evidence_payloads ?? []
  const actualEvidenceHashes = uniqueSorted(evidencePayloads.map((payload) => stableFingerprint(payload)))
  const deliveredFactIds = factRegister.facts
    .filter((fact) => {
      if (budgetExcludedFactIds.includes(fact.fact_id)) return false
      if (fact.kind === 'frontier') return true
      if (fact.kind === 'finding') return true
      if (fact.meaning.disposition === 'not_applicable') return true
      if (fact.meaning.disposition !== 'served' && fact.meaning.disposition !== 'empty') return false
      const hashes = fact.evidence_refs.filter((ref) => ref.startsWith('retrieval:')).map(evidenceHashFromRef)
      return hashes.length === fact.evidence_refs.length
        && hashes.every((hash) => hash !== null && actualEvidenceHashes.includes(hash))
    })
    .map((fact) => fact.fact_id)
  const deliveredEvidenceHashes = uniqueSorted(factRegister.facts
    .filter((fact) => deliveredFactIds.includes(fact.fact_id))
    .flatMap((fact) => fact.evidence_refs.filter((ref) => ref.startsWith('retrieval:')).map(evidenceHashFromRef))
    .filter((hash): hash is string => hash !== null))
  const deliveryPart: InquiryResponseDeliveryPart = {
    part_id: `structured-findings:${factRegister.register_hash}`,
    kind: 'structured_findings',
    content_hash: inquiryResponsePartContentHash(
      factRegister,
      deliveredFactIds,
      'structured_findings',
      null,
      deliveredEvidenceHashes,
      null,
    ),
    fact_ids: deliveredFactIds,
    evidence_payload_hashes: deliveredEvidenceHashes,
    content: null,
    exclusion_reason: null,
  }
  const responseText = options.response_text ?? ''
  const prosePart: InquiryResponseDeliveryPart | null = responseText.trim()
    ? {
        part_id: `prose:${stableFingerprint(responseText)}`,
        kind: 'prose',
        content_hash: stableFingerprint(responseText),
        content: null,
        fact_ids: [],
        evidence_payload_hashes: [],
        exclusion_reason: null,
      }
    : null
  const findingFacts = factRegister.facts.filter((fact) => fact.kind === 'finding' && fact.normalized_content)
  const inferredInterpretations = findingFacts.length > 0
    && findingFacts.every((fact) => responseText.includes(fact.normalized_content!))
    ? [{ text: responseText, fact_ids: findingFacts.map((fact) => fact.fact_id) }]
    : citedInterpretations(factRegister, responseText)
  const conjointParts: InquiryResponseDeliveryPart[] = (options.conjoint_interpretations ?? inferredInterpretations).map((item, index) => {
    const kind = item.fact_ids.length === 1 ? 'finding_interpretation' as const : 'conjoint_interpretation' as const
    return {
      part_id: `${kind.replace('_', '-')}:${index + 1}:${stableFingerprint(item.text)}`,
      kind,
      content_hash: inquiryResponsePartContentHash(factRegister, item.fact_ids, kind, null, [], item.text),
      content: item.text,
      fact_ids: uniqueSorted(item.fact_ids),
      evidence_payload_hashes: [],
      exclusion_reason: null,
    }
  })
  const exclusionReason = 'synthesis_budget_excluded: the synthesis evidence budget omitted this supporting finding'
  const exclusionParts: InquiryResponseDeliveryPart[] = budgetExcludedFactIds.length
    ? [{
        part_id: `permitted-exclusion:${stableFingerprint(budgetExcludedFactIds)}`,
        kind: 'permitted_exclusion',
        content_hash: inquiryResponsePartContentHash(factRegister, budgetExcludedFactIds, 'permitted_exclusion', exclusionReason, [], null),
        content: null,
        fact_ids: uniqueSorted(budgetExcludedFactIds),
        evidence_payload_hashes: [],
        exclusion_reason: exclusionReason,
      }]
    : []
  const deliveryParts = [deliveryPart, ...(prosePart ? [prosePart] : []), ...conjointParts, ...exclusionParts]
  return {
    accountability_version: 'inquiry-response-accountability-v1',
    fact_register: factRegister,
    delivery_parts: deliveryParts,
    response_coverage_receipt: buildResponseCoverageReceipt({
      contract,
      fact_register: factRegister,
      delivery_parts: deliveryParts,
      evidence_payloads: evidencePayloads,
      knowledge_snapshot: options.knowledge_snapshot,
      response_text: responseText,
    }),
  }
}
