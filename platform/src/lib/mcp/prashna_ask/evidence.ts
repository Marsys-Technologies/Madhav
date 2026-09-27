import 'server-only'

import { AiConsoleError } from '@/lib/ai-console/errors'
import type { SafeRoutingSnapshot } from '@/lib/ai-console/execution/types'
import { MCP_BYOK_EVIDENCE_ENVELOPE_MAX_BYTES } from '@/lib/limits/byok_admission'

export const MCP_RAW_EVIDENCE_MAX_BYTES = 1024 * 1024
export const MCP_EVIDENCE_ENVELOPE_MAX_BYTES = MCP_BYOK_EVIDENCE_ENVELOPE_MAX_BYTES

type SafeRoleTarget = SafeRoutingSnapshot['roles']['planner']

export interface SafeMcpRoutingSummary {
  selection: SafeRoutingSnapshot['selection']
  resolvedChoice: SafeRoutingSnapshot['resolvedChoice']
  configurationVersion: number | null
  roles: {
    planner: SafeRoleTarget
    deep_planner: SafeRoleTarget
    worker: SafeRoleTarget
  }
}

export interface McpEvidenceEnvelopeV1 {
  schema_version: 'madhav.evidence.v1'
  synthesis: { mode: 'external'; performed_by_madhav: false }
  question: string
  plan: unknown
  results: unknown[]
  completeness: unknown
  judgment_flags: string[]
  response_accountability: unknown
  routing: SafeMcpRoutingSummary
  ok?: true
  trace_id?: string
  chart_id?: string
  outcome?: 'plan' | 'safety_withheld'
  safety_response?: string
  persistence?: unknown
  safety_decision?: unknown
  query_class?: unknown
  query_intent_summary?: unknown
  chart_header?: unknown
  planning_latency_ms?: number
  inquiry_contract?: unknown
  inquiry_closure_receipt?: unknown
  inquiry_door_parity?: unknown
}

export interface McpEvidenceMetadata {
  ok?: true
  trace_id?: string
  chart_id?: string
  outcome?: 'plan' | 'safety_withheld'
  safety_response?: string
  persistence?: unknown
  safety_decision?: unknown
  query_class?: unknown
  query_intent_summary?: unknown
  chart_header?: unknown
  planning_latency_ms?: number
  inquiry_contract?: unknown
  inquiry_closure_receipt?: unknown
  inquiry_door_parity?: unknown
}

export function safeMcpRoutingSummary(snapshot: SafeRoutingSnapshot): SafeMcpRoutingSummary {
  return {
    selection: snapshot.selection,
    resolvedChoice: snapshot.resolvedChoice,
    configurationVersion: snapshot.configurationVersion,
    roles: {
      planner: snapshot.roles.planner,
      deep_planner: snapshot.roles.deep_planner,
      worker: snapshot.roles.worker,
    },
  }
}

export function buildMcpEvidenceEnvelope(input: {
  question: string
  plan: unknown
  results: unknown[]
  completeness: unknown
  judgmentFlags: string[]
  responseAccountability: unknown
  snapshot: SafeRoutingSnapshot
  metadata?: McpEvidenceMetadata
}): McpEvidenceEnvelopeV1 {
  const metadata = input.metadata
  const envelope: McpEvidenceEnvelopeV1 = {
    schema_version: 'madhav.evidence.v1',
    synthesis: { mode: 'external', performed_by_madhav: false },
    question: input.question,
    plan: input.plan,
    results: input.results,
    completeness: input.completeness,
    judgment_flags: [...input.judgmentFlags],
    response_accountability: input.responseAccountability,
    routing: safeMcpRoutingSummary(input.snapshot),
    ...(metadata?.ok === undefined ? {} : { ok: metadata.ok }),
    ...(metadata?.trace_id === undefined ? {} : { trace_id: metadata.trace_id }),
    ...(metadata?.chart_id === undefined ? {} : { chart_id: metadata.chart_id }),
    ...(metadata?.outcome === undefined ? {} : { outcome: metadata.outcome }),
    ...(metadata?.safety_response === undefined ? {} : { safety_response: metadata.safety_response }),
    ...(metadata?.persistence === undefined ? {} : { persistence: metadata.persistence }),
    ...(metadata?.safety_decision === undefined ? {} : { safety_decision: metadata.safety_decision }),
    ...(metadata?.query_class === undefined ? {} : { query_class: metadata.query_class }),
    ...(metadata?.query_intent_summary === undefined ? {} : { query_intent_summary: metadata.query_intent_summary }),
    ...(metadata?.chart_header === undefined ? {} : { chart_header: metadata.chart_header }),
    ...(metadata?.planning_latency_ms === undefined ? {} : { planning_latency_ms: metadata.planning_latency_ms }),
    ...(metadata?.inquiry_contract === undefined ? {} : { inquiry_contract: metadata.inquiry_contract }),
    ...(metadata?.inquiry_closure_receipt === undefined ? {} : { inquiry_closure_receipt: metadata.inquiry_closure_receipt }),
    ...(metadata?.inquiry_door_parity === undefined ? {} : { inquiry_door_parity: metadata.inquiry_door_parity }),
  }
  const bytes = Buffer.byteLength(JSON.stringify(envelope), 'utf8')
  if (bytes > MCP_EVIDENCE_ENVELOPE_MAX_BYTES) {
    throw new AiConsoleError('AI_EXECUTION_FAILED')
  }
  return envelope
}

/** Dedicated external-synthesis budget, deliberately independent of model metadata. */
export function mcpEvidenceBudgetTokens(reserveTokens = 1_000): number {
  const approximateTokens = Math.floor(MCP_EVIDENCE_ENVELOPE_MAX_BYTES / 4)
  return Math.max(1, approximateTokens - reserveTokens)
}
