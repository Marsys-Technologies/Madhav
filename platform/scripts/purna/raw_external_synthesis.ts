/**
 * Conforming reference synthesis for the governed raw-MCP lifecycle.
 *
 * The server intentionally owns only authorization, retrieval, receipt, and
 * closure. This client owns its independent model call and refuses to certify
 * its prose without deriving the standard response-accountability register
 * from the exact payloads whose hashes the lifecycle committed.
 */
import { assertPinnedCapabilityKnowledgeCurrent } from '../../src/lib/retrieval/registry/knowledge'
import { stableFingerprint } from '../../src/lib/retrieval/registry/knowledge/stable'
import { fetchChartHeaderResolution } from '../../src/lib/retrieval/chart_header'
import { synthesizeReading, type SynthesisEvidenceItem } from '../../src/lib/pipeline/prashna_ask_synthesis'
import { buildStructuredResponseAccountability, type InquiryContract } from '../../src/lib/vidhi/inquiry'
import type { AcceptanceCase } from './collection_types'

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null
}

function evidenceForContract(contract: InquiryContract, payloads: readonly unknown[]): SynthesisEvidenceItem[] {
  const byHash = new Map(payloads.map((payload) => [stableFingerprint(payload), payload]))
  const usable: SynthesisEvidenceItem[] = []
  for (const item of contract.plan_items) {
    if (!item.binding_id?.startsWith('registry:')) continue
    const evidenceHashes = contract.obligations
      .filter((obligation) => item.obligation_ids.includes(obligation.obligation_id))
      .flatMap((obligation) => obligation.evidence_refs)
      .map((ref) => ref.match(/sha256:[a-f0-9]{64}$/)?.[0])
      .filter((hash): hash is string => Boolean(hash))
    const payload = evidenceHashes.map((hash) => byHash.get(hash)).find((candidate) => {
      const raw = record(candidate)
      return raw !== null && Array.isArray(raw.results)
    })
    const raw = record(payload)
    if (!raw || !Array.isArray(raw.results)) continue
    usable.push({ tool_name: item.binding_id.slice('registry:'.length), bundle: { results: raw.results } })
  }
  return usable
}

export async function synthesizeRawLifecycleEvidence(input: {
  readonly test: AcceptanceCase
  readonly inquiryId: string
  readonly contract: InquiryContract
  readonly evidencePayloads: readonly unknown[]
}) {
  const snapshot = assertPinnedCapabilityKnowledgeCurrent()
  if (snapshot.content_hash !== input.contract.capability_content_hash
    || snapshot.compatibility_version !== input.contract.capability_compatibility_version) {
    throw new Error('RAW_EXTERNAL_SYNTHESIS_SNAPSHOT_STALE')
  }
  const temporalAnchor = input.contract.plan_items
    .map((item) => item.argument_resolution?.temporal_anchor_date)
    .find((value): value is string => typeof value === 'string' && value.length > 0)
    ?? new Date().toISOString().slice(0, 10)
  const chartHeader = await fetchChartHeaderResolution(input.contract.chart_id, undefined, temporalAnchor)
    .catch(() => ({ header: null, flags: ['chart_header_unresolved'] as string[] }))
  const evidence = evidenceForContract(input.contract, input.evidencePayloads)
  const evidenceToolNames = new Set(evidence.map((item) => item.tool_name))
  const unresolvedTools = input.contract.plan_items
    .filter((item) => item.binding_id?.startsWith('registry:') && !evidenceToolNames.has(item.binding_id.slice('registry:'.length)))
    .map((item) => item.binding_id!.slice('registry:'.length))
  const synthesis = await synthesizeReading({
    chartId: input.contract.chart_id,
    question: input.contract.question,
    queryClass: input.contract.scope_tuple.intent,
    queryIntentSummary: `Governed raw-MCP inquiry ${input.inquiryId}`,
    evidence,
    unresolvedTools,
    emptyResultTools: [],
    strippedLeakedCapabilities: [],
    capTripped: null,
    nowContextDate: temporalAnchor,
    currentMahaAntar: chartHeader.header?.current_maha_antar ?? null,
    responseFormat: 'full',
    synthesisGuidance: null,
  })
  const responseAccountability = buildStructuredResponseAccountability(input.contract, {
    response_text: synthesis.reading,
    evidence_payloads: input.evidencePayloads,
    knowledge_snapshot: snapshot,
  })
  return { answer: synthesis.reading ?? '', responseAccountability }
}
