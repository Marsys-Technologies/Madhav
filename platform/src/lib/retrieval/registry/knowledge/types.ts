/** Planner-facing semantic-capability knowledge contract.
 *
 * SCUs describe what the system can KNOW or DO for planning.  They are not
 * retrieval tools and they are not stored assets.  Bindings connect an SCU to
 * one or more executable registry descriptors without collapsing either side.
 */

export const CAPABILITY_KNOWLEDGE_SCHEMA_VERSION = '1.0.0' as const
export const CAPABILITY_COMPATIBILITY_VERSION = 'planner-scu-v1' as const

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
    'pagination' | 'pagination_verified' | 'result_collection_verified' | 'pagination_contract' | 'execution_channels' | 'public_tool_name' | 'route_evidence'>
  readonly additional_bindings?: readonly SemanticCapabilityBinding[]
  readonly edges?: readonly SemanticCapabilityEdgeDeclaration[]
  readonly provenance_requirements: readonly string[]
  readonly freshness_policy: string
  readonly entitlement: 'native' | 'research' | 'public_disclosed'
  readonly safety_notes: readonly string[]
  readonly known_gaps: readonly string[]
  /** Links to producer outputs without claiming unreviewed output contracts exist. */
  readonly producer_output_claims?: readonly ProducerOutputClaim[]
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
}

export interface SemanticCapabilityEdge {
  readonly from_scu_id: string
  readonly relation: CapabilityRelation
  readonly to_scu_id: string
  readonly rationale: string
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
  readonly producer_output_claims: number
  readonly reviewed_output_claims: number
  readonly exclusions: readonly { capability_uri: string; reason: string }[]
}

export interface CapabilityKnowledgeSnapshot {
  readonly schema_version: typeof CAPABILITY_KNOWLEDGE_SCHEMA_VERSION
  readonly compatibility_version: typeof CAPABILITY_COMPATIBILITY_VERSION
  readonly generated_at: string
  readonly content_hash: string
  readonly source_catalog_fingerprint: string
  readonly scus: readonly SemanticCapabilityUnit[]
  readonly edges: readonly SemanticCapabilityEdge[]
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
    | 'ORPHAN_DESCRIPTOR'
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
