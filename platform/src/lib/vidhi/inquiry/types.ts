import type { ExecutionChannel } from '../../retrieval/registry/knowledge/types'

export const INQUIRY_CONTRACT_VERSION = '1.1.0' as const

/**
 * Channel-neutral scope carried by an Inquiry Contract. Both the Portal
 * planner and the Vidhi MCP planner have stricter local scope types; the
 * lifecycle only needs their shared semantic fields.
 */
export interface InquiryScopeTuple {
  readonly intent: string
  readonly domains: readonly string[]
  readonly width: string
  readonly depth: string
  readonly horizon: string
  readonly intervention: boolean | string
  readonly entitlement: string
}

export type InquiryStatus = 'INCOMPLETE' | 'COMPLETE' | 'BLOCKED'
export type ObligationDisposition = 'pending' | 'served' | 'empty' | 'dark' | 'failed' | 'not_applicable'

export interface InquiryObligation {
  readonly obligation_id: string
  readonly label: string
  readonly source: 'deterministic_floor' | 'ai_decomposition' | 'omission_rule' | 'adaptive_frontier'
  readonly materiality: 'required' | 'supporting'
  readonly scu_ids: readonly string[]
  readonly rationale: string
  readonly disposition: ObligationDisposition
  readonly evidence_refs: readonly string[]
  readonly gap_reason: string | null
}

export interface InquiryPlanItem {
  readonly item_id: string
  readonly obligation_ids: readonly string[]
  readonly scu_id: string
  readonly binding_id: string | null
  readonly args: Readonly<Record<string, unknown>>
  readonly depends_on: readonly string[]
  readonly state: 'ready' | 'blocked' | 'observed'
  readonly blocked_reason: string | null
  readonly observation: {
    readonly disposition: Exclude<ObligationDisposition, 'pending' | 'not_applicable'>
    readonly evidence_refs: readonly string[]
    readonly gap_reason: string | null
  } | null
}

export interface MaterialFrontierItem {
  readonly frontier_id: string
  readonly discovered_from: string
  readonly scu_id: string
  readonly materiality: 'required' | 'supporting'
  readonly reason: string
  readonly disposition: 'open' | 'absorbed' | 'capped' | 'not_applicable'
}

export interface OmissionFinding {
  readonly rule_id: string
  readonly severity: 'material' | 'advisory'
  readonly missing_scu_id: string
  readonly rationale: string
}

/** AI is allowed to decompose/associate; deterministic validation owns authority. */
export interface AiInquiryProposal {
  readonly question_facets: readonly { label: string; terms: readonly string[]; materiality: 'required' | 'supporting' }[]
  readonly uncommon_adjacencies: readonly { from_scu_id: string; to_scu_id: string; rationale: string }[]
  readonly hypotheses: readonly string[]
}

export interface InquiryContract {
  readonly contract_version: typeof INQUIRY_CONTRACT_VERSION
  readonly compiler_version: string
  readonly contract_id: string
  readonly semantic_contract_hash: string
  readonly execution_plan_hash: string
  readonly chart_id: string
  readonly execution_channel: ExecutionChannel
  readonly question: string
  readonly scope_tuple: InquiryScopeTuple
  readonly capability_compatibility_version: string
  readonly capability_content_hash: string
  readonly chart_availability_version: string | null
  readonly chart_build_id: string | null
  readonly obligations: readonly InquiryObligation[]
  readonly plan_items: readonly InquiryPlanItem[]
  readonly material_frontier: readonly MaterialFrontierItem[]
  readonly omission_findings: readonly OmissionFinding[]
  readonly ai_hypotheses: readonly string[]
  readonly status: InquiryStatus
  readonly status_reasons: readonly string[]
  readonly iteration: number
  readonly max_iterations: number
}

export interface InquiryObservation {
  readonly item_id: string
  readonly disposition: Exclude<ObligationDisposition, 'pending' | 'not_applicable'>
  readonly evidence_refs: readonly string[]
  readonly gap_reason?: string
  readonly discovered_frontier?: readonly {
    scu_id: string
    materiality: 'required' | 'supporting'
    reason: string
  }[]
}

export interface InquiryValidationResult {
  readonly valid: boolean
  readonly errors: readonly string[]
}

export interface InquiryClosureReceipt {
  readonly receipt_version: 'inquiry-closure-v1'
  readonly contract_id: string
  readonly semantic_contract_hash: string
  readonly execution_plan_hash: string
  readonly capability_content_hash: string
  readonly chart_availability_version: string | null
  readonly chart_build_id: string | null
  readonly status: InquiryStatus
  readonly status_reasons: readonly string[]
  readonly obligation_coverage: readonly {
    obligation_id: string
    materiality: 'required' | 'supporting'
    disposition: ObligationDisposition
    evidence_refs: readonly string[]
    gap_reason: string | null
  }[]
  readonly residual_frontier: readonly MaterialFrontierItem[]
  readonly receipt_hash: string
}
