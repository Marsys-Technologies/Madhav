import type { ExecutionChannel } from '../../retrieval/registry/knowledge/types'

export const INQUIRY_CONTRACT_VERSION = '1.2.0' as const

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

export interface InquiryScopeNormalizationReceipt {
  readonly normalization_version: 'inquiry-scope-normalization-v1'
  readonly applied_rules: readonly string[]
  readonly normalized_scope_hash: string
}

export type InquiryStatus = 'INCOMPLETE' | 'COMPLETE' | 'BLOCKED'
export type ObligationDisposition = 'pending' | 'served' | 'empty' | 'dark' | 'failed' | 'not_applicable'

export interface InquiryObligation {
  readonly obligation_id: string
  readonly label: string
  readonly source: 'deterministic_floor' | 'ai_decomposition' | 'graph_traversal' | 'omission_challenger' | 'omission_rule' | 'adaptive_frontier'
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
  /** Immutable compiler-time arguments; runtime pagination may advance args. */
  readonly authorization_args?: Readonly<Record<string, unknown>>
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
  readonly source_ref?: string
}

export interface OmissionFinding {
  readonly rule_id: string
  readonly severity: 'material' | 'advisory'
  readonly missing_scu_id: string
  readonly rationale: string
  readonly source: 'rule' | 'graph'
  readonly relation: string | null
  readonly source_ref: string
}

export interface GraphTraversalStep {
  readonly from_scu_id: string
  readonly relation: string
  readonly to_scu_id: string
  readonly hop: number
  readonly materiality: 'required' | 'supporting'
  readonly edge_source: string
  readonly source_ref: string
}

export interface GraphTraversalFrontier extends GraphTraversalStep {
  readonly reason: 'graph_hop_budget_exhausted' | 'graph_node_budget_exhausted'
}

export interface GraphTraversalReceipt {
  readonly traversal_version: 'inquiry-graph-traversal-v1'
  readonly seed_scu_ids: readonly string[]
  readonly selected_scu_ids: readonly string[]
  readonly steps: readonly GraphTraversalStep[]
  readonly frontier: readonly GraphTraversalFrontier[]
  readonly max_hops: number
  readonly max_nodes: number
  readonly truncated: boolean
  readonly traversal_hash: string
}

export interface OmissionChallengeReceipt {
  readonly challenge_version: 'inquiry-omission-challenger-v1'
  readonly selected_scu_ids: readonly string[]
  readonly findings: readonly OmissionFinding[]
  readonly challenge_hash: string
}

export interface InquiryPlanningBudget {
  readonly max_search_hits: number
  readonly max_graph_hops: number
  readonly max_graph_nodes: number
  readonly max_challenger_additions: number
}

export interface InquiryPlanningBudgetReceipt extends InquiryPlanningBudget {
  readonly floor_nodes_selected: number
  readonly search_hits_considered: number
  readonly ai_adjacency_nodes_selected: number
  readonly graph_seed_nodes: number
  readonly graph_nodes_selected: number
  readonly graph_expansion_nodes_selected: number
  readonly graph_edges_followed: number
  readonly challenger_findings: number
  readonly challenger_additions: number
  readonly frontier_items: number
  readonly truncated: boolean
  readonly budget_hash: string
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
  readonly scope_normalization?: InquiryScopeNormalizationReceipt
  readonly graph_traversal?: GraphTraversalReceipt
  readonly omission_challenge?: OmissionChallengeReceipt
  readonly planning_budget?: InquiryPlanningBudgetReceipt
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
  readonly scope_normalization?: InquiryScopeNormalizationReceipt
  readonly graph_traversal_hash?: string
  readonly omission_challenge_hash?: string
  readonly planning_budget?: InquiryPlanningBudgetReceipt
}

export interface InquiryRegisteredFact {
  readonly fact_id: string
  readonly kind: 'obligation' | 'frontier'
  readonly obligation_id: string | null
  readonly frontier_id: string | null
  readonly materiality: 'required' | 'supporting'
  readonly meaning: {
    readonly label: string
    readonly rationale: string
    readonly scu_ids: readonly string[]
    readonly disposition: ObligationDisposition | MaterialFrontierItem['disposition']
  }
  readonly evidence_refs: readonly string[]
}

export interface InquiryFactRegister {
  readonly register_version: 'inquiry-fact-register-v1'
  readonly contract_id: string
  readonly semantic_contract_hash: string
  readonly facts: readonly InquiryRegisteredFact[]
  readonly required_fact_ids: readonly string[]
  readonly validation_errors: readonly string[]
  readonly register_hash: string
}

export interface InquiryResponseDeliveryPart {
  readonly part_id: string
  readonly kind: 'prose' | 'structured_findings' | 'permitted_exclusion'
  readonly content_hash: string
  readonly fact_ids: readonly string[]
  /** Hashes of the canonical retrieval payloads that substantiate these claims. */
  readonly evidence_payload_hashes: readonly string[]
  readonly exclusion_reason: string | null
}

export interface InquiryContinuationReceipt {
  readonly iteration: number
  readonly max_iterations: number
  readonly exhausted: boolean
  readonly next_action_ids: readonly string[]
  readonly blocked_item_ids: readonly string[]
  readonly unresolved_obligation_ids: readonly string[]
  readonly frontier_ids: readonly string[]
}

export interface InquiryResponseCoverageReceipt {
  readonly receipt_version: 'inquiry-response-coverage-v1'
  readonly contract_id: string
  readonly semantic_contract_hash: string
  readonly fact_register_hash: string
  readonly status: 'COMPLETE' | 'INCOMPLETE_RESUMABLE' | 'BLOCKED'
  readonly coverage: {
    readonly synthesis_present: boolean
    readonly all_total: number
    readonly all_delivered: number
    readonly all_permitted_exclusions: number
    readonly required_total: number
    readonly required_delivered: number
    readonly interpretation_mapped: number
  }
  readonly delivered_fact_ids: readonly string[]
  readonly permitted_exclusion_fact_ids: readonly string[]
  readonly missing_fact_ids: readonly string[]
  readonly missing_required_fact_ids: readonly string[]
  readonly interpretation_unmapped_fact_ids: readonly string[]
  readonly delivery_part_ids: readonly string[]
  readonly invalid_delivery_claims: readonly string[]
  readonly continuation: InquiryContinuationReceipt
  readonly resume_required: boolean
  readonly receipt_hash: string
}

export interface InquiryResponseAccountability {
  readonly accountability_version: 'inquiry-response-accountability-v1'
  readonly fact_register: InquiryFactRegister
  readonly delivery_parts: readonly InquiryResponseDeliveryPart[]
  readonly response_coverage_receipt: InquiryResponseCoverageReceipt
}
