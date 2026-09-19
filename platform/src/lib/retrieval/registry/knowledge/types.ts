/** Planner-facing semantic-capability knowledge contract.
 *
 * SCUs describe what the system can KNOW or DO for planning.  They are not
 * retrieval tools and they are not stored assets.  Bindings connect an SCU to
 * one or more executable registry descriptors without collapsing either side.
 */

export const CAPABILITY_KNOWLEDGE_SCHEMA_VERSION = '2.3.0' as const
export const CAPABILITY_COMPATIBILITY_VERSION = 'planner-scu-v2' as const

export type SemanticCapabilityKind =
  | 'datum'
  | 'assessment'
  | 'mechanism'
  | 'temporal'
  | 'citation'
  | 'contradiction'
  | 'intervention'
  | 'synthesis_support'

export type CapabilityRelation =
  | 'primary'
  | 'requires'
  | 'provides'
  | 'enables'
  | 'related'
  | 'contradicts'

export type ExecutionBindingKind = 'registry_capability' | 'mcp_native'
export type PaginationSemantics = 'none' | 'cursor' | 'offset' | 'bounded_complete' | 'bounded_unverified'
export type ExecutionChannel = 'platform_internal' | 'mcp_full' | 'mcp_compact' | 'mcp_consult'

export type SemanticConceptType =
  | 'capability'
  | 'domain_concept'
  | 'retrieval_archetype'
  | 'tool_role'
  | 'projection'

export interface SemanticConceptBinding {
  readonly concept_id: string
  readonly concept_type: SemanticConceptType
  readonly source_ref: string
}

export interface SemanticConcept {
  readonly concept_id: string
  readonly types: readonly SemanticConceptType[]
  readonly source_refs: readonly string[]
}

export interface SemanticEditorialSource {
  readonly source_ref: string
  readonly source_fields: readonly string[]
}

export interface SemanticGapDisposition {
  readonly gap: string
  readonly status: 'accepted_boundary' | 'deferred_contract' | 'blocked_authority'
  readonly rationale: string
  readonly source_ref: string
}

export interface SemanticGraphDisposition {
  readonly status: 'connected' | 'isolated_dispositioned'
  readonly rationale: string
  readonly source_refs: readonly string[]
}

export interface ProducerSemanticBinding {
  readonly asset_id: string
  /** Planner-addressable semantic target, when the producer output is inquiry evidence. */
  readonly target_scu_id: string | null
  /** Exact registry target when the serving surface is deliberately planner-excluded. */
  readonly target_capability_uri: string | null
  /**
   * `directly_serves_output` is reserved for a capability whose result reads or
   * exposes the producer's governed output. The other relations are useful
   * semantic context, but never count as route coverage.
   */
  readonly relation: 'directly_serves_output' | 'consumes_output' | 'supports_same_semantic_domain'
  readonly rationale: string
  readonly source_refs: readonly string[]
}

export interface ProducerSemanticDisposition {
  readonly status: 'linked' | 'not_applicable'
  readonly asset_ids: readonly string[]
  readonly rationale: string
  readonly source_refs: readonly string[]
}

export interface PaginationContract {
  readonly request_position_path?: string
  readonly request_limit_path?: string
  readonly effective_maximum?: number
  readonly result_collection_path: string
  readonly total_path?: string
  readonly next_path?: string
  readonly more_available_path?: string
  readonly deterministic_order: readonly string[]
}

export interface PaginationReviewDisposition {
  readonly disposition: 'not_paginated' | 'exhaustible_reviewed' | 'non_exhaustible'
  readonly source_ref: string
  readonly blocker?: string
}

/**
 * A handler-specific proof that one finite temporal window was fully returned.
 *
 * This does not authorize cursor or offset continuation.  It merely lets the
 * inquiry lifecycle accept an exact, server-observed bounded window when its
 * receipt independently proves that no rows were trimmed.
 */
export interface BoundedWindowClosureContract {
  readonly receipt_path: string
  readonly closure_version: string
  readonly collection: string
  readonly maximum_top_k: number
  readonly source_ref: string
}

/**
 * Reviewed response-level closure for a non-paginated binding whose single
 * response can still be materially incomplete. Paths are relative to the
 * response content object; this contract does not define semantic result rows.
 */
export interface NonPaginatedClosureContract {
  readonly closure_version: string
  readonly checklist_path: string
  readonly material_trim_paths: readonly string[]
  readonly source_ref: string
}

/** Exact evidence a binding needs before it can be offered for execution. */
export interface ProducerOutputAvailabilityRequirement {
  readonly kind: 'producer_output'
  readonly asset_id: string
  readonly spec_sha256: string
  readonly scope: 'chart_build' | 'global'
  readonly source_ref: string
}

/**
 * A successful, authenticated service-health probe for an executable binding.
 *
 * `endpoint_identity` is the persisted trusted-provenance identity, rather than
 * an environment URL: the real runner URL contains deployment-specific host
 * details and must never be copied into the knowledge snapshot.  The runtime
 * evaluator requires that exact identity together with its server-reconstructed
 * source kind, so a similarly named asset or an anonymous health result cannot
 * satisfy this contract.
 */
export interface ServiceProbeAvailabilityRequirement {
  readonly kind: 'service_probe'
  readonly asset_id: string
  readonly probe_id: string
  readonly endpoint_identity: string
  /** SHA-256 of the exact registry-owned health-probe configuration. */
  readonly probe_contract_sha256: string
  /** Evidence older than this cannot represent current service readiness. */
  readonly max_age_seconds: number
  readonly source_ref: string
}

export interface SourceQueryAvailabilityRequirement {
  readonly kind: 'source_query'
  readonly contract_id: string
  /** Exact registry capability whose handler query this contract reviews. */
  readonly capability_uri: string
  /** Fingerprint of the exact registry-owned query, scope binding, and empty semantics. */
  readonly contract_sha256: string
  readonly scope: 'chart' | 'global'
  readonly source_ref: string
}

export interface DerivedAvailabilityRequirement {
  readonly kind: 'derived'
  /**
   * The child bindings are evaluated in the same availability scope as the
   * composite.  This prevents a chart-scoped composite from being promoted by
   * a merely global or differently-scoped adjacent route.
   */
  readonly scope: 'chart' | 'global'
  readonly required_binding_ids: readonly string[]
  readonly source_ref: string
}

export type AvailabilityRequirement =
  | ProducerOutputAvailabilityRequirement
  | ServiceProbeAvailabilityRequirement
  | SourceQueryAvailabilityRequirement
  | DerivedAvailabilityRequirement

/** Source-authored requirements for one known executable binding. */
export interface BindingAvailabilityContract {
  readonly binding_id: string
  readonly requirements: readonly AvailabilityRequirement[]
  readonly unavailable_reason?: string
}

/**
 * A reviewed decision not to offer an otherwise executable binding yet.
 *
 * This is deliberately separate from an empty availability contract: an empty
 * contract is malformed, whereas this records the concrete handler dependency
 * that lacks a receipt contract and keeps the binding fail-closed.
 */
export interface BindingAvailabilityDisposition {
  readonly binding_id: string
  readonly status: 'deliberately_dark'
  readonly reason: string
  /**
   * Exact mandatory executable legs that prevent a composite from becoming
   * available.  This is structured rather than inferred from prose so callers
   * can distinguish an intentionally dark route from a route with a complete
   * derived availability contract.
   */
  readonly missing_binding_ids?: readonly string[]
  readonly source_refs: readonly string[]
}

export interface SemanticCapabilityBinding {
  readonly binding_id: string
  readonly kind: ExecutionBindingKind
  readonly relation: 'primary' | 'provides'
  /** CapabilityDescriptor.uri for registry bindings; stable MCP-native URI otherwise. */
  readonly capability_uri: string
  readonly input_contract: Readonly<Record<string, string>>
  readonly output_contract: Readonly<Record<string, string>>
  readonly pagination: PaginationSemantics
  /** True only when response paths and exhaustion semantics were source-reviewed. */
  readonly pagination_verified?: boolean | null
  readonly pagination_review?: PaginationReviewDisposition
  /** Reviewed proof contract for one non-repeatable bounded temporal window. */
  readonly bounded_window_closure?: BoundedWindowClosureContract
  /** Reviewed completeness receipt for one non-paginated response. */
  readonly non_paginated_closure?: NonPaginatedClosureContract
  /** True when the semantic result collection path was reviewed, independently of exhaustion semantics. */
  readonly result_collection_verified?: boolean
  readonly pagination_contract?: PaginationContract
  readonly executable: boolean
  /** Where the route is actually callable; internal dispatch is not public MCP proof. */
  readonly execution_channels?: readonly ExecutionChannel[]
  readonly public_tool_name?: string
  readonly route_evidence?: string
  /** Honest reason when the binding is known but cannot currently execute. */
  readonly unavailable_reason?: string
}

export interface SemanticCapabilityEdgeDeclaration {
  readonly relation: Exclude<CapabilityRelation, 'primary'>
  readonly target_scu_id: string
  readonly rationale: string
}

export interface SemanticCapabilityDeclaration {
  readonly scu_id: string
  readonly version: number
  readonly label: string
  readonly description: string
  readonly kind: SemanticCapabilityKind
  readonly domains: readonly string[]
  readonly concepts: readonly string[]
  readonly intents: readonly string[]
  readonly horizons: readonly string[]
  readonly scope: 'chart' | 'global'
  readonly inputs: readonly string[]
  readonly outputs: readonly string[]
  readonly primary_binding_uri: string
  readonly primary_binding_details?: Pick<SemanticCapabilityBinding,
    'pagination' | 'pagination_verified' | 'result_collection_verified' | 'pagination_contract' | 'bounded_window_closure' | 'non_paginated_closure' | 'execution_channels' | 'public_tool_name' | 'route_evidence'>
  readonly additional_bindings?: readonly SemanticCapabilityBinding[]
  readonly edges?: readonly SemanticCapabilityEdgeDeclaration[]
  readonly provenance_requirements: readonly string[]
  readonly freshness_policy: string
  readonly entitlement: 'native' | 'research' | 'public_disclosed'
  readonly safety_notes: readonly string[]
  readonly known_gaps: readonly string[]
  /** Links to producer outputs without claiming unreviewed output contracts exist. */
  readonly producer_output_claims?: readonly ProducerOutputClaim[]
  /** Binding-specific evidence. Snapshots without this use reviewed SCU claims as a legacy fallback. */
  readonly availability_contracts?: readonly BindingAvailabilityContract[]
  /** Reviewed fail-closed decisions for executable bindings without an evidence contract. */
  readonly availability_dispositions?: readonly BindingAvailabilityDisposition[]
  /** false means the compiler conservatively derived this from a descriptor. */
  readonly editorial: boolean
}

export interface ProducerOutputClaim {
  readonly asset_id: string
  readonly component: string
  readonly output_digest_spec_sha256: string | null
  readonly disposition: 'reviewed_output' | 'route_evidence_only' | 'dark' | 'excluded'
  readonly evidence: string
  readonly gap_reason?: string
}

export interface SemanticCapabilityUnit extends SemanticCapabilityDeclaration {
  readonly bindings: readonly SemanticCapabilityBinding[]
  readonly source_descriptor_uris: readonly string[]
  readonly editorial_method: 'authored_declaration' | 'descriptor_metadata_review'
  readonly editorial_sources: readonly SemanticEditorialSource[]
  readonly concept_bindings: readonly SemanticConceptBinding[]
  readonly gap_dispositions: readonly SemanticGapDisposition[]
  readonly graph_disposition: SemanticGraphDisposition
  readonly producer_semantic_disposition: ProducerSemanticDisposition
}

export interface SemanticCapabilityEdge {
  readonly from_scu_id: string
  readonly relation: CapabilityRelation
  readonly to_scu_id: string
  readonly rationale: string
  readonly edge_source?: 'authored_declaration' | 'drill_child_contract'
  readonly source_ref?: string
}

export interface CapabilityKnowledgeCensus {
  readonly runtime_descriptors: number
  readonly addressable_descriptors: number
  readonly excluded_descriptors: number
  readonly semantic_capabilities: number
  readonly editorial_scus: number
  readonly derived_scus: number
  readonly executable_bindings: number
  readonly unavailable_bindings: number
  readonly publicly_named_bindings: number
  readonly reviewed_pagination_bindings: number
  readonly reviewed_pagination_dispositions: number
  readonly reviewed_paginated_descriptors: number
  readonly exhaustible_reviewed_descriptors: number
  readonly non_exhaustible_descriptors: number
  readonly reviewed_route_descriptors: number
  readonly reviewed_public_descriptors: number
  readonly reviewed_nonpublic_descriptors: number
  readonly producer_output_claims: number
  readonly reviewed_output_claims: number
  readonly typed_concepts: number
  readonly unbound_concepts: number
  readonly isolated_scus: number
  readonly graph_components: number
  readonly dispositioned_isolated_scus: number
  readonly unresolved_isolated_scus: number
  readonly producer_semantic_bindings: number
  readonly directly_served_producer_outputs: number
  readonly support_only_producer_bindings: number
  readonly unbound_active_producers: number
  readonly undispositioned_producer_scus: number
  readonly undispositioned_gaps: number
  readonly exclusions: readonly { capability_uri: string; reason: string }[]
}

export interface CapabilityKnowledgeSnapshot {
  readonly schema_version: typeof CAPABILITY_KNOWLEDGE_SCHEMA_VERSION
  readonly compatibility_version: typeof CAPABILITY_COMPATIBILITY_VERSION
  readonly generated_at: string
  readonly content_hash: string
  readonly source_catalog_fingerprint: string
  readonly semantic_review_fingerprint: string
  readonly producer_contract_fingerprint: string
  readonly scus: readonly SemanticCapabilityUnit[]
  readonly edges: readonly SemanticCapabilityEdge[]
  readonly concept_universe: readonly SemanticConcept[]
  readonly producer_semantic_bindings: readonly ProducerSemanticBinding[]
  readonly census: CapabilityKnowledgeCensus
}

export interface ChartCapabilityAvailability {
  readonly scu_id: string
  readonly state: 'available' | 'partial' | 'empty' | 'dark' | 'incompatible'
  readonly build_status: string | null
  readonly build_id: string | null
  readonly freshness: string | null
  readonly available_binding_ids: readonly string[]
  readonly gaps: readonly string[]
  readonly asset_receipts: readonly ChartAssetCapabilityReceipt[]
}

export interface ChartAssetCapabilityReceipt {
  readonly asset_id: string
  readonly build_id: string | null
  readonly writer_version: string | null
  readonly output_digest_spec_sha256: string | null
  readonly state: 'passed' | 'partial' | 'failed' | 'missing'
  readonly receipt_ref: string | null
}

/** Runtime/chart state remains separate from the immutable semantic snapshot. */
export interface ChartCapabilityOverlay {
  readonly chart_id: string
  readonly overlay_version: string
  readonly capability_compatibility_version: string
  readonly catalog_content_hash: string
  readonly build_id: string | null
  readonly code_revision: string | null
  readonly writer_inventory_hash: string | null
  readonly generated_at: string
  readonly availability: readonly ChartCapabilityAvailability[]
}

export interface KnowledgeIntegrityFinding {
  readonly code:
    | 'DUPLICATE_SCU'
    | 'MISSING_PRIMARY_BINDING'
    | 'STALE_EDGE'
    | 'NON_EXECUTABLE_BINDING'
    | 'BAD_PAGINATION_CONTRACT'
    | 'BAD_PRODUCER_OUTPUT_CLAIM'
    | 'BAD_BINDING_AVAILABILITY_CONTRACT'
    | 'BAD_BINDING_AVAILABILITY_DISPOSITION'
    | 'UNSUPPORTED_BINDING_AVAILABILITY_REQUIREMENT'
    | 'ORPHAN_DESCRIPTOR'
    | 'UNBOUND_CONCEPT'
    | 'ISOLATED_SCU'
    | 'DISCONNECTED_GRAPH'
    | 'UNDISPOSITIONED_GAP'
    | 'UNSOURCED_EDITORIAL_SCU'
    | 'CONCEPT_BINDING_MISMATCH'
    | 'INVALID_SEMANTIC_EDGE'
    | 'INVALID_GRAPH_DISPOSITION'
    | 'UNBOUND_ACTIVE_PRODUCER'
    | 'INVALID_PRODUCER_SEMANTIC_BINDING'
    | 'INVALID_PRODUCER_SEMANTIC_DISPOSITION'
    | 'CHANGE_SYNC_DRIFT'
    | 'COMPATIBILITY_MISMATCH'
  readonly severity: 'error' | 'warning'
  readonly subject: string
  readonly detail: string
}

export interface KnowledgeIntegrityReport {
  readonly passed: boolean
  readonly findings: readonly KnowledgeIntegrityFinding[]
  readonly census: CapabilityKnowledgeCensus
}
