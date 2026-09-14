import type { CapabilityDescriptor } from '../types'
import {
  CAPABILITY_COMPATIBILITY_VERSION,
  CAPABILITY_KNOWLEDGE_SCHEMA_VERSION,
  type CapabilityKnowledgeCensus,
  type CapabilityKnowledgeSnapshot,
  type KnowledgeIntegrityFinding,
  type KnowledgeIntegrityReport,
  type PaginationSemantics,
  type SemanticConcept,
  type SemanticConceptBinding,
  type SemanticConceptType,
  type SemanticCapabilityBinding,
  type SemanticCapabilityDeclaration,
  type SemanticCapabilityEdge,
  type SemanticCapabilityUnit,
  type ProducerSemanticBinding,
} from './types'
import { canonicalize, deepFreeze, stableFingerprint } from './stable'
import { getDescriptorEditorialReview, getReviewedDescriptorNames } from './editorial_review'
import { getProducerSemanticReview } from './producer_editorial_review'
import estateCensus from '../../../../generated/capability_estate_census.json'

function slug(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')
}

function isDescriptorExecutable(cap: CapabilityDescriptor): boolean {
  const loader = (cap as CapabilityDescriptor & { loader?: unknown }).loader
  return typeof cap.handler === 'function' || typeof loader === 'function'
}

function exclusionReason(cap: CapabilityDescriptor): string | null {
  if (cap.calibration_context_only) return 'calibration_context_only descriptors are not planner-addressable'
  if (cap.mutation) return 'mutation-capable descriptors are not planner-addressable inquiry evidence'
  return null
}

function paginationFor(cap: CapabilityDescriptor): PaginationSemantics {
  if (!cap.density_contract?.paginated) return 'none'
  const parameters = normalizedInputParameters(cap)
  if (parameters.properties['cursor']) return 'cursor'
  if (parameters.properties['offset']) return 'offset'
  return 'bounded_unverified'
}

function normalizedInputParameters(cap: CapabilityDescriptor): {
  properties: Record<string, { type?: unknown; required?: unknown }>
  required: Set<string>
} {
  const schema = (cap.input_schema ?? {}) as Record<string, unknown>
  const jsonSchemaProperties = schema['type'] === 'object'
    && schema['properties']
    && typeof schema['properties'] === 'object'
    && !Array.isArray(schema['properties'])
    ? schema['properties'] as Record<string, { type?: unknown; required?: unknown }>
    : null
  const properties = jsonSchemaProperties ?? schema as Record<string, { type?: unknown; required?: unknown }>
  const schemaRequired = Array.isArray(schema['required'])
    ? schema['required'].filter((value): value is string => typeof value === 'string')
    : []
  return {
    properties,
    required: new Set([
      ...(cap.required_inputs ?? []),
      ...schemaRequired,
      ...Object.entries(properties).filter(([, value]) => value?.required === true).map(([key]) => key),
    ]),
  }
}

function contractFromSchema(cap: CapabilityDescriptor): Readonly<Record<string, string>> {
  const normalized = normalizedInputParameters(cap)
  return Object.fromEntries(Object.entries(normalized.properties).sort(([a], [b]) => a.localeCompare(b)).map(
    ([key, spec]) => [key, `${typeof spec?.type === 'string' ? spec.type : 'unknown'}${normalized.required.has(key) ? ':required' : ':optional'}`],
  ))
}

function kindFor(cap: CapabilityDescriptor): SemanticCapabilityDeclaration['kind'] {
  return cap.tool_role === 'synthesizer' ? 'synthesis_support'
    : cap.archetype === 'temporal' ? 'temporal'
    : cap.archetype === 'prose_citation' ? 'citation'
    : cap.archetype === 'cross_domain' ? 'contradiction'
    : cap.tool_role === 'graph' ? 'mechanism'
    : cap.traversal_level === 'L-DOMAIN' ? 'assessment'
    : 'datum'
}

function semanticOutputs(cap: CapabilityDescriptor, reviewedOutputs: readonly string[]): string[] {
  const schema = (cap.output_schema ?? {}) as Record<string, unknown>
  const properties = schema['properties'] && typeof schema['properties'] === 'object' && !Array.isArray(schema['properties'])
    ? Object.keys(schema['properties'] as Record<string, unknown>)
    : Object.keys(schema).filter((key) => !['$schema', 'type', 'required', 'additionalProperties', 'description'].includes(key))
  return [...new Set([...(properties.length > 0 ? properties : reviewedOutputs), ...(cap.emits_references ? ['evidence_references'] : [])])].sort()
}

function primaryBinding(
  cap: CapabilityDescriptor,
  details?: SemanticCapabilityDeclaration['primary_binding_details'],
): SemanticCapabilityBinding {
  const executable = isDescriptorExecutable(cap)
  return {
    binding_id: `registry:${cap.uri}`,
    kind: 'registry_capability',
    relation: 'primary',
    capability_uri: cap.uri,
    input_contract: contractFromSchema(cap),
    output_contract: cap.output_schema ? { structured_content: 'declared' } : { content: 'ToolResult.content' },
    pagination: paginationFor(cap),
    pagination_verified: null,
    executable,
    execution_channels: ['platform_internal'],
    route_evidence: `CapabilityDescriptor:${cap.uri}`,
    ...details,
    ...(executable ? {} : { unavailable_reason: 'CapabilityDescriptor has no executable handler or loader.' }),
  }
}

function deriveDeclaration(cap: CapabilityDescriptor): SemanticCapabilityDeclaration {
  const inputParameters = normalizedInputParameters(cap)
  const review = getDescriptorEditorialReview(cap.name)
  if (!review) throw new Error(`UNREVIEWED_DESCRIPTOR_SEMANTICS:${cap.name}`)
  const kind = cap.tool_role === 'synthesizer' ? 'synthesis_support' : review.kind ?? kindFor(cap)
  const sourceDescription = cap.description.trim().replace(/[.。]+$/, '')
  return {
    scu_id: `scu.catalog.${slug(cap.name)}`,
    version: 1,
    label: cap.display?.short_label ?? cap.name.replaceAll('_', ' '),
    description: `${sourceDescription}. Evidence use: ${review.evidence_use}.`,
    kind,
    domains: review.domains,
    concepts: [cap.name, ...review.concepts],
    intents: review.intents,
    horizons: review.horizons,
    scope: cap.scope === 'per_chart' ? 'chart' : 'global',
    inputs: Object.keys(inputParameters.properties).sort(),
    outputs: semanticOutputs(cap, review.outputs),
    primary_binding_uri: cap.uri,
    edges: (cap.drill_children ?? []).map((child) => ({
      relation: 'enables' as const,
      target_scu_id: `scu.catalog.${slug(child.split('/').at(-1) ?? child)}`,
      rationale: 'Derived from the executable descriptor drill_children contract.',
    })),
    provenance_requirements: cap.data_source === 'computed'
      ? ['chart_id_when_chart_scoped', 'computed_at', 'engine_version']
      : cap.data_source === 'hybrid'
        ? ['chart_id_when_chart_scoped', 'build_id', 'formula_or_writer_version', 'computed_at', 'engine_version']
        : ['chart_id_when_chart_scoped', 'build_id', 'formula_or_writer_version'],
    freshness_policy: cap.data_source === 'computed'
      ? 'Must carry computation time and engine version.'
      : cap.data_source === 'hybrid'
        ? 'Must resolve stored evidence against the active compatible chart build and carry computation time plus engine version for computed evidence.'
        : 'Must resolve against the active compatible chart build.',
    entitlement: 'native',
    safety_notes: cap.mutation
      ? ['Mutation-capable: execution requires explicit authorization and audit receipt.']
      : ['Read-only evidence surface; planner must not interpret returned chart facts.'],
    known_gaps: cap.calibration_context_only ? ['Calibration-context-only; excluded from planner addressability.'] : [],
    editorial: true,
  }
}

function conceptType(concept: string, cap: CapabilityDescriptor): SemanticConceptType {
  if (concept === cap.name) return 'capability'
  if (concept === cap.archetype) return 'retrieval_archetype'
  if (concept === cap.tool_role) return 'tool_role'
  if ((cap.projection_tags ?? [] as readonly string[]).includes(concept)) return 'projection'
  return 'domain_concept'
}

function editorialSourceRef(cap: CapabilityDescriptor, authored: boolean): string {
  if (authored) return `SemanticCapabilityDeclaration:${cap.uri}`
  const review = getDescriptorEditorialReview(cap.name)
  if (!review) throw new Error(`UNREVIEWED_DESCRIPTOR_SEMANTICS:${cap.name}`)
  return `platform/src/lib/retrieval/registry/knowledge/editorial_review.ts#${review.family_id}:${cap.name}`
}

function normalizeDeclaration(
  declaration: SemanticCapabilityDeclaration,
  source: CapabilityDescriptor,
): SemanticCapabilityUnit {
  const authored = source.semantic_capabilities?.includes(declaration) ?? false
  const sourceRef = editorialSourceRef(source, authored)
  const primary = source.uri === declaration.primary_binding_uri
    ? primaryBinding(source, declaration.primary_binding_details)
    : {
        binding_id: `registry:${declaration.primary_binding_uri}`,
        kind: 'registry_capability' as const,
        relation: 'primary' as const,
        capability_uri: declaration.primary_binding_uri,
        input_contract: {},
        output_contract: {},
        pagination: 'none' as const,
        pagination_verified: null,
        executable: false,
        execution_channels: [] as const,
        unavailable_reason: 'Primary binding descriptor was not the declaration host.',
      }
  const bindings = [primary, ...(declaration.additional_bindings ?? [])].sort((a, b) => a.binding_id.localeCompare(b.binding_id))
  const paginationGap = bindings.some((binding) => binding.pagination !== 'none' && !binding.pagination_verified)
    ? 'Pagination or bounded retrieval lacks a complete, source-reviewed exhaustion contract; the planner must retain a material frontier.'
    : null
  const knownGaps = [...new Set([...declaration.known_gaps, ...(paginationGap ? [paginationGap] : [])])]
  return {
    ...declaration,
    domains: [...new Set(declaration.domains)].sort(),
    concepts: [...new Set(declaration.concepts)].sort(),
    intents: [...new Set(declaration.intents)].sort(),
    horizons: [...new Set(declaration.horizons)].sort(),
    inputs: [...new Set(declaration.inputs)].sort(),
    outputs: [...new Set(declaration.outputs)].sort(),
    known_gaps: knownGaps,
    bindings,
    source_descriptor_uris: [source.uri],
    editorial: true,
    editorial_method: authored ? 'authored_declaration' : 'descriptor_metadata_review',
    editorial_sources: authored
      ? [{ source_ref: sourceRef, source_fields: ['semantic_capabilities', 'description', 'primary_binding_uri'] }]
      : [
          { source_ref: sourceRef, source_fields: ['family_id', 'domains', 'concepts', 'intents', 'outputs', 'horizons', 'evidence_use', 'member_name'] },
          {
            source_ref: `CapabilityDescriptor:${source.uri}`,
            source_fields: ['name', 'description', 'display', 'archetype', 'traversal_level', 'tool_role', 'scope', 'input_schema', 'required_inputs', 'output_schema', 'emits_references', 'projection_tags', 'drill_children', 'data_source', 'density_contract', 'mutation'],
          },
        ],
    concept_bindings: [...new Set(declaration.concepts)].sort().map((concept): SemanticConceptBinding => ({
      concept_id: concept,
      concept_type: conceptType(concept, source),
      source_ref: sourceRef,
    })),
    gap_dispositions: knownGaps.map((gap) => ({
      gap,
      status: /pag|route|total|ordering|contract|exhaust/i.test(gap) ? 'deferred_contract' as const : 'accepted_boundary' as const,
      rationale: /pag|route|total|ordering|contract|exhaust/i.test(gap)
        ? 'Retained as a named contract boundary until its evidence gate is separately closed.'
        : 'Retained as an explicit semantic or synthesis boundary; it is not silently treated as coverage.',
      source_ref: sourceRef,
    })),
    graph_disposition: {
      status: 'isolated_dispositioned',
      rationale: 'Graph disposition is finalized after authored and drill-child edges compile.',
      source_refs: [sourceRef],
    },
    producer_semantic_disposition: {
      status: 'not_applicable',
      asset_ids: [],
      rationale: 'Producer semantic disposition is finalized after the authored producer review compiles.',
      source_refs: [sourceRef],
    },
  }
}

interface ProducerCensusSource {
  readonly details: {
    readonly producer_assets: { readonly active_asset_ids: readonly string[] }
    readonly producer_output_contracts: readonly ({ readonly asset_id: string } & Readonly<Record<string, unknown>>)[]
  }
}

const DEFAULT_PRODUCER_CENSUS = estateCensus as ProducerCensusSource
const ACTIVE_PRODUCER_IDS = [...DEFAULT_PRODUCER_CENSUS.details.producer_assets.active_asset_ids].sort()

function producerSourceRef(assetId: string): string {
  return `platform/src/generated/capability_estate_census.json#details.producer_output_contracts:${assetId}`
}

function producerReviewRef(targetScuId: string, assetId: string): string {
  return `platform/src/lib/retrieval/registry/knowledge/producer_editorial_review.ts#${targetScuId}:${assetId}`
}

function compileProducerSemanticBindings(scus: readonly SemanticCapabilityUnit[], activeProducerIds: readonly string[]): readonly ProducerSemanticBinding[] {
  const scuIds = new Set(scus.map((scu) => scu.scu_id))
  const bindings = getProducerSemanticReview().flatMap((group) => group.asset_ids.map((asset_id): ProducerSemanticBinding => ({
    asset_id,
    target_scu_id: group.target_scu_id,
    relation: 'provides_evidence_for',
    rationale: group.rationale,
    source_refs: [producerSourceRef(asset_id), producerReviewRef(group.target_scu_id, asset_id)],
  }))).sort((a, b) => a.asset_id.localeCompare(b.asset_id))
  const counts = new Map<string, number>()
  for (const binding of bindings) counts.set(binding.asset_id, (counts.get(binding.asset_id) ?? 0) + 1)
  const missing = activeProducerIds.filter((assetId) => !counts.has(assetId))
  const duplicate = [...counts].filter(([, count]) => count !== 1).map(([assetId]) => assetId)
  const unknown = [...counts.keys()].filter((assetId) => !activeProducerIds.includes(assetId))
  const staleTargets = [...new Set(bindings.filter((binding) => !scuIds.has(binding.target_scu_id)).map((binding) => binding.target_scu_id))]
  if (missing.length > 0 || duplicate.length > 0 || unknown.length > 0 || staleTargets.length > 0) {
    throw new Error(`INVALID_PRODUCER_SEMANTIC_REVIEW:${JSON.stringify({ missing, duplicate, unknown, staleTargets })}`)
  }
  return bindings
}

function buildConceptUniverse(scus: readonly SemanticCapabilityUnit[]): readonly SemanticConcept[] {
  const concepts = new Map<string, { types: Set<SemanticConceptType>; sourceRefs: Set<string> }>()
  for (const binding of scus.flatMap((scu) => scu.concept_bindings)) {
    const entry = concepts.get(binding.concept_id) ?? { types: new Set<SemanticConceptType>(), sourceRefs: new Set<string>() }
    entry.types.add(binding.concept_type)
    entry.sourceRefs.add(binding.source_ref)
    concepts.set(binding.concept_id, entry)
  }
  return [...concepts.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([concept_id, entry]) => ({
    concept_id,
    types: [...entry.types].sort(),
    source_refs: [...entry.sourceRefs].sort(),
  }))
}

function graphMetrics(scus: readonly SemanticCapabilityUnit[], edges: readonly SemanticCapabilityEdge[]): {
  isolated: number
  components: number
} {
  const neighbors = new Map(scus.map((scu) => [scu.scu_id, new Set<string>()]))
  for (const edge of edges) {
    neighbors.get(edge.from_scu_id)?.add(edge.to_scu_id)
    neighbors.get(edge.to_scu_id)?.add(edge.from_scu_id)
  }
  let components = 0
  const visited = new Set<string>()
  for (const scu of scus) {
    if (visited.has(scu.scu_id)) continue
    components += 1
    const frontier = [scu.scu_id]
    while (frontier.length > 0) {
      const current = frontier.pop()!
      if (visited.has(current)) continue
      visited.add(current)
      for (const neighbor of neighbors.get(current) ?? []) if (!visited.has(neighbor)) frontier.push(neighbor)
    }
  }
  return {
    isolated: [...neighbors.values()].filter((items) => items.size === 0).length,
    components,
  }
}

function buildCensus(
  catalog: readonly CapabilityDescriptor[],
  scus: readonly SemanticCapabilityUnit[],
  edges: readonly SemanticCapabilityEdge[],
  conceptUniverse: readonly SemanticConcept[],
  producerSemanticBindings: readonly ProducerSemanticBinding[],
  activeProducerIds: readonly string[],
): CapabilityKnowledgeCensus {
  const exclusions = catalog.flatMap((cap) => {
    const reason = exclusionReason(cap)
    return reason ? [{ capability_uri: cap.uri, reason }] : []
  }).map((item) => ({
    capability_uri: item.capability_uri,
    reason: item.reason,
  })).sort((a, b) => a.capability_uri.localeCompare(b.capability_uri))
  const bindings = scus.flatMap((scu) => scu.bindings)
  const graph = graphMetrics(scus, edges)
  const boundConcepts = new Set(scus.flatMap((scu) => scu.concept_bindings.map((binding) => binding.concept_id)))
  const universeConcepts = new Set(conceptUniverse.map((concept) => concept.concept_id))
  return {
    runtime_descriptors: catalog.length,
    addressable_descriptors: catalog.length - exclusions.length,
    excluded_descriptors: exclusions.length,
    semantic_capabilities: scus.length,
    editorial_scus: scus.filter((scu) => scu.editorial).length,
    derived_scus: scus.filter((scu) => !scu.editorial).length,
    executable_bindings: bindings.filter((binding) => binding.executable).length,
    unavailable_bindings: bindings.filter((binding) => !binding.executable).length,
    publicly_named_bindings: bindings.filter((binding) => Boolean(binding.public_tool_name)).length,
    reviewed_pagination_bindings: bindings.filter((binding) => binding.pagination_verified).length,
    producer_output_claims: scus.flatMap((scu) => scu.producer_output_claims ?? []).length,
    reviewed_output_claims: scus.flatMap((scu) => scu.producer_output_claims ?? []).filter((claim) => claim.disposition === 'reviewed_output').length,
    typed_concepts: conceptUniverse.length,
    unbound_concepts: [...boundConcepts].filter((concept) => !universeConcepts.has(concept)).length,
    isolated_scus: graph.isolated,
    graph_components: graph.components,
    dispositioned_isolated_scus: scus.filter((scu) => scu.graph_disposition.status === 'isolated_dispositioned').length,
    unresolved_isolated_scus: scus.filter((scu) => {
      const incident = edges.some((edge) => edge.from_scu_id === scu.scu_id || edge.to_scu_id === scu.scu_id)
      return !incident && scu.graph_disposition.status !== 'isolated_dispositioned'
    }).length,
    producer_semantic_bindings: producerSemanticBindings.length,
    unbound_active_producers: activeProducerIds.filter((assetId) => !producerSemanticBindings.some((binding) => binding.asset_id === assetId)).length,
    undispositioned_producer_scus: scus.filter((scu) => !scu.producer_semantic_disposition).length,
    undispositioned_gaps: scus.reduce((total, scu) => total + scu.known_gaps.filter((gap) => !scu.gap_dispositions.some((item) => item.gap === gap)).length, 0),
    exclusions,
  }
}

export function compileCapabilityKnowledge(
  catalog: readonly CapabilityDescriptor[],
  generatedAt = new Date().toISOString(),
  producerCensus: ProducerCensusSource = DEFAULT_PRODUCER_CENSUS,
): CapabilityKnowledgeSnapshot {
  const activeProducerIds = [...producerCensus.details.producer_assets.active_asset_ids].sort()
  const activeProducerContracts = producerCensus.details.producer_output_contracts
    .filter((contract) => activeProducerIds.includes(contract.asset_id))
    .sort((a, b) => a.asset_id.localeCompare(b.asset_id))
  if (activeProducerContracts.length !== activeProducerIds.length
    || new Set(activeProducerContracts.map((contract) => contract.asset_id)).size !== activeProducerIds.length) {
    throw new Error('INVALID_PRODUCER_CONTRACT_SOURCE:active producer contracts must be exact and unique')
  }
  const addressable = catalog.filter((cap) => exclusionReason(cap) === null)
  const scusBase = addressable.flatMap((cap) => {
    const declarations = cap.semantic_capabilities?.length ? cap.semantic_capabilities : [deriveDeclaration(cap)]
    return declarations.map((declaration) => normalizeDeclaration(declaration, cap))
  }).sort((a, b) => a.scu_id.localeCompare(b.scu_id))

  const derivedIdToActual = new Map(addressable.map((cap) => [
    `scu.catalog.${slug(cap.name)}`,
    (cap.semantic_capabilities?.[0] ?? deriveDeclaration(cap)).scu_id,
  ]))
  const edges: SemanticCapabilityEdge[] = scusBase.flatMap((scu) => (scu.edges ?? []).map((edge) => ({
    from_scu_id: scu.scu_id,
    relation: edge.relation,
    to_scu_id: derivedIdToActual.get(edge.target_scu_id) ?? edge.target_scu_id,
    rationale: edge.rationale,
    edge_source: scu.editorial_method === 'authored_declaration' ? 'authored_declaration' as const : 'drill_child_contract' as const,
    source_ref: scu.editorial_method === 'authored_declaration'
      ? scu.editorial_sources[0]!.source_ref
      : `CapabilityDescriptor:${scu.source_descriptor_uris[0]}#drill_children`,
  }))).sort((a, b) => canonicalize(a).localeCompare(canonicalize(b)))
  const producerSemanticBindings = compileProducerSemanticBindings(scusBase, activeProducerIds)
  const scus = scusBase.map((scu): SemanticCapabilityUnit => {
    const incident = edges.filter((edge) => edge.from_scu_id === scu.scu_id || edge.to_scu_id === scu.scu_id)
    const producerBindings = producerSemanticBindings.filter((binding) => binding.target_scu_id === scu.scu_id)
    return {
      ...scu,
      edges: edges.filter((edge) => edge.from_scu_id === scu.scu_id).map((edge) => ({
        relation: edge.relation as Exclude<typeof edge.relation, 'primary'>,
        target_scu_id: edge.to_scu_id,
        rationale: edge.rationale,
      })),
      graph_disposition: incident.length > 0
        ? {
            status: 'connected',
            rationale: 'At least one authored declaration or descriptor drill-child contract names this relationship.',
            source_refs: incident.map((edge) => edge.source_ref!).filter(Boolean).sort(),
          }
        : {
            status: 'isolated_dispositioned',
            rationale: 'No authored declaration or descriptor drill-child contract names a semantic relationship; shared labels alone are not treated as edge evidence.',
            source_refs: scu.editorial_sources.map((source) => source.source_ref).sort(),
          },
      producer_semantic_disposition: producerBindings.length > 0
        ? {
            status: 'linked',
            asset_ids: producerBindings.map((binding) => binding.asset_id).sort(),
            rationale: 'One or more W1 producer outputs are editorially linked to this semantic capability.',
            source_refs: producerBindings.flatMap((binding) => binding.source_refs).sort(),
          }
        : {
            status: 'not_applicable',
            asset_ids: [],
            rationale: 'The exhaustive W1 producer review found no direct producer-output relationship for this semantic capability.',
            source_refs: scu.editorial_sources.map((source) => source.source_ref).sort(),
          },
    }
  })
  const conceptUniverse = buildConceptUniverse(scus)

  const sourceCatalogFingerprint = stableFingerprint(catalog.map((cap) => ({
    uri: cap.uri,
    name: cap.name,
    type: cap.type ?? (cap as CapabilityDescriptor & { primitive_type?: string }).primitive_type,
    layer: cap.layer,
    scope: cap.scope,
    input_schema: cap.input_schema,
    output_schema: cap.output_schema,
    density_contract: cap.density_contract,
    calibration_context_only: cap.calibration_context_only ?? false,
    description: cap.description,
    display: cap.display,
    archetype: cap.archetype,
    traversal_level: cap.traversal_level,
    tool_role: cap.tool_role,
    projection_tags: cap.projection_tags,
    drill_children: cap.drill_children,
    data_source: cap.data_source,
    emits_references: cap.emits_references,
    required_inputs: cap.required_inputs,
    mutation: cap.mutation ?? false,
    semantic_capabilities: cap.semantic_capabilities,
  })).sort((a, b) => a.uri.localeCompare(b.uri)))
  const semanticReviewFingerprint = stableFingerprint({
    descriptor_editorial_review: getReviewedDescriptorNames().map((name) => ({ name, review: getDescriptorEditorialReview(name) })),
    producer_editorial_review: getProducerSemanticReview(),
  })
  const producerContractFingerprint = stableFingerprint(activeProducerContracts)
  const census = buildCensus(catalog, scus, edges, conceptUniverse, producerSemanticBindings, activeProducerIds)
  const hashMaterial = {
    schema_version: CAPABILITY_KNOWLEDGE_SCHEMA_VERSION,
    compatibility_version: CAPABILITY_COMPATIBILITY_VERSION,
    source_catalog_fingerprint: sourceCatalogFingerprint,
    semantic_review_fingerprint: semanticReviewFingerprint,
    producer_contract_fingerprint: producerContractFingerprint,
    scus,
    edges,
    concept_universe: conceptUniverse,
    producer_semantic_bindings: producerSemanticBindings,
    census,
  }
  return deepFreeze({
    schema_version: CAPABILITY_KNOWLEDGE_SCHEMA_VERSION,
    compatibility_version: CAPABILITY_COMPATIBILITY_VERSION,
    generated_at: generatedAt,
    content_hash: stableFingerprint(hashMaterial),
    source_catalog_fingerprint: sourceCatalogFingerprint,
    semantic_review_fingerprint: semanticReviewFingerprint,
    producer_contract_fingerprint: producerContractFingerprint,
    scus,
    edges,
    concept_universe: conceptUniverse,
    producer_semantic_bindings: producerSemanticBindings,
    census,
  })
}

export function inspectCapabilityKnowledge(
  catalog: readonly CapabilityDescriptor[],
  snapshot: CapabilityKnowledgeSnapshot,
): KnowledgeIntegrityReport {
  const findings: KnowledgeIntegrityFinding[] = []
  const expectedSnapshot = compileCapabilityKnowledge(catalog, snapshot.generated_at)
  if (snapshot.source_catalog_fingerprint !== expectedSnapshot.source_catalog_fingerprint) {
    findings.push({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'source_catalog_fingerprint', detail: 'Snapshot catalog provenance does not match the current descriptor catalog.' })
  }
  if (snapshot.semantic_review_fingerprint !== expectedSnapshot.semantic_review_fingerprint) {
    findings.push({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'semantic_review_fingerprint', detail: 'Snapshot semantic-review provenance does not match the current authored reviews.' })
  }
  if (snapshot.producer_contract_fingerprint !== expectedSnapshot.producer_contract_fingerprint) {
    findings.push({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'producer_contract_fingerprint', detail: 'Snapshot producer provenance does not match the exact active W1 producer contract rows.' })
  }
  if (canonicalize(snapshot.scus) !== canonicalize(expectedSnapshot.scus)) {
    findings.push({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'semantic_capabilities', detail: 'Compiled SCUs differ from the current catalog and authored-review sources.' })
  }
  if (canonicalize(snapshot.edges) !== canonicalize(expectedSnapshot.edges)) {
    findings.push({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'semantic_edges', detail: 'Compiled semantic edges differ from authored declaration and drill-child sources.' })
  }
  if (canonicalize(snapshot.concept_universe) !== canonicalize(expectedSnapshot.concept_universe)) {
    findings.push({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'concept_universe', detail: 'Typed concept universe differs from the current source-linked SCU bindings.' })
  }
  if (canonicalize(snapshot.producer_semantic_bindings) !== canonicalize(expectedSnapshot.producer_semantic_bindings)) {
    findings.push({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'producer_semantic_bindings', detail: 'Producer semantic bindings differ from the authored W1-to-SCU review.' })
  }
  const descriptorByUri = new Map(catalog.map((cap) => [cap.uri, cap]))
  const conceptById = new Map(snapshot.concept_universe.map((concept) => [concept.concept_id, concept]))
  const expectedConceptById = new Map(expectedSnapshot.concept_universe.map((concept) => [concept.concept_id, concept]))
  const scuIds = new Set<string>()
  for (const scu of snapshot.scus) {
    if (scuIds.has(scu.scu_id)) findings.push({ code: 'DUPLICATE_SCU', severity: 'error', subject: scu.scu_id, detail: 'SCU id is not unique.' })
    scuIds.add(scu.scu_id)
    const primary = scu.bindings.filter((binding) => binding.relation === 'primary')
    const sourceUri = scu.source_descriptor_uris[0]
    const sourceDescriptor = sourceUri ? descriptorByUri.get(sourceUri) : undefined
    const sourceReview = sourceDescriptor ? getDescriptorEditorialReview(sourceDescriptor.name) : null
    const expectedEditorialRef = scu.editorial_method === 'authored_declaration'
      ? `SemanticCapabilityDeclaration:${sourceUri}`
      : sourceReview ? `platform/src/lib/retrieval/registry/knowledge/editorial_review.ts#${sourceReview.family_id}:${sourceDescriptor!.name}` : null
    const descriptorRef = `CapabilityDescriptor:${sourceUri}`
    const expectedEditorialFields = scu.editorial_method === 'authored_declaration'
      ? ['semantic_capabilities', 'description', 'primary_binding_uri']
      : ['family_id', 'domains', 'concepts', 'intents', 'outputs', 'horizons', 'evidence_use', 'member_name']
    const hasExpectedEditorialSource = Boolean(expectedEditorialRef && scu.editorial_sources.some((source) => source.source_ref === expectedEditorialRef
      && expectedEditorialFields.every((field) => source.source_fields.includes(field))))
    const hasExpectedDescriptorSource = scu.editorial_method === 'authored_declaration'
      || scu.editorial_sources.some((source) => source.source_ref === descriptorRef
        && ['description', 'display', 'scope', 'input_schema', 'required_inputs', 'output_schema', 'emits_references', 'data_source', 'mutation'].every((field) => source.source_fields.includes(field)))
    if (!scu.editorial || !sourceDescriptor || !hasExpectedEditorialSource || !hasExpectedDescriptorSource) {
      findings.push({ code: 'UNSOURCED_EDITORIAL_SCU', severity: 'error', subject: scu.scu_id, detail: 'Editorial SCU lacks an exact source reference and reviewed source-field list.' })
    }
    if (primary.length !== 1) findings.push({ code: 'MISSING_PRIMARY_BINDING', severity: 'error', subject: scu.scu_id, detail: `Expected exactly one primary binding; found ${primary.length}.` })
    for (const binding of scu.bindings) {
      const descriptor = binding.kind === 'registry_capability' ? descriptorByUri.get(binding.capability_uri) : undefined
      const descriptorExecutable = descriptor ? isDescriptorExecutable(descriptor) : false
      if (binding.kind === 'registry_capability' && !descriptor) {
        findings.push({ code: 'NON_EXECUTABLE_BINDING', severity: 'error', subject: binding.binding_id, detail: 'Binding URI is absent from the runtime catalog.' })
      } else if (binding.kind === 'registry_capability' && binding.executable !== descriptorExecutable) {
        findings.push({ code: 'NON_EXECUTABLE_BINDING', severity: 'error', subject: binding.binding_id, detail: 'Binding executable state disagrees with the handler-or-loader runtime surface.' })
      } else if (binding.kind === 'registry_capability' && !binding.executable) {
        findings.push({ code: 'NON_EXECUTABLE_BINDING', severity: 'warning', subject: binding.binding_id, detail: 'Descriptor remains discoverable knowledge but has no executable handler or loader.' })
      }
      if (descriptor?.density_contract?.paginated && binding.pagination === 'none') {
        findings.push({ code: 'BAD_PAGINATION_CONTRACT', severity: 'error', subject: binding.binding_id, detail: 'Paginated descriptor is presented as non-paginated.' })
      }
      if (scu.editorial && descriptor?.density_contract?.paginated && !binding.pagination_verified) {
        findings.push({ code: 'BAD_PAGINATION_CONTRACT', severity: 'warning', subject: binding.binding_id, detail: 'Editorial SCU uses a bounded route whose response/exhaustion contract is not yet source-reviewed.' })
      }
    }
    for (const claim of scu.producer_output_claims ?? []) {
      if (claim.disposition === 'reviewed_output' && !/^[a-f0-9]{64}$/.test(claim.output_digest_spec_sha256 ?? '')) {
        findings.push({ code: 'BAD_PRODUCER_OUTPUT_CLAIM', severity: 'error', subject: `${scu.scu_id}:${claim.asset_id}`, detail: 'A reviewed output claim must pin one exact SHA-256 output-digest specification.' })
      }
      if (claim.disposition !== 'reviewed_output' && claim.output_digest_spec_sha256 !== null) {
        findings.push({ code: 'BAD_PRODUCER_OUTPUT_CLAIM', severity: 'error', subject: `${scu.scu_id}:${claim.asset_id}`, detail: 'An unreviewed output claim cannot carry a reviewed specification hash.' })
      }
    }
    const boundConcepts = new Set(scu.concept_bindings.map((binding) => binding.concept_id))
    for (const concept of scu.concepts) {
      const binding = scu.concept_bindings.find((item) => item.concept_id === concept)
      const universe = conceptById.get(concept)
      if (!binding || !universe) {
        findings.push({ code: 'UNBOUND_CONCEPT', severity: 'error', subject: `${scu.scu_id}:${concept}`, detail: 'SCU concept lacks a typed source-linked universe binding.' })
      } else if (!universe.types.includes(binding.concept_type) || !universe.source_refs.includes(binding.source_ref)
        || !scu.editorial_sources.some((source) => source.source_ref === binding.source_ref)) {
        findings.push({ code: 'CONCEPT_BINDING_MISMATCH', severity: 'error', subject: `${scu.scu_id}:${concept}`, detail: 'Concept binding type/source disagrees with the concept universe or SCU editorial authority.' })
      }
    }
    for (const binding of scu.concept_bindings) if (!scu.concepts.includes(binding.concept_id)) {
      findings.push({ code: 'CONCEPT_BINDING_MISMATCH', severity: 'error', subject: `${scu.scu_id}:${binding.concept_id}`, detail: 'Concept binding is not declared by the SCU.' })
    }
    if (boundConcepts.size !== scu.concept_bindings.length) findings.push({ code: 'CONCEPT_BINDING_MISMATCH', severity: 'error', subject: scu.scu_id, detail: 'SCU contains duplicate concept bindings.' })
    for (const gap of scu.known_gaps) {
      const disposition = scu.gap_dispositions.find((item) => item.gap === gap)
      if (!disposition?.rationale || !disposition.source_ref) findings.push({ code: 'UNDISPOSITIONED_GAP', severity: 'error', subject: scu.scu_id, detail: `Known gap lacks an explicit disposition: ${gap}` })
    }
  }
  for (const edge of snapshot.edges) {
    if (!scuIds.has(edge.from_scu_id)) findings.push({ code: 'STALE_EDGE', severity: 'error', subject: edge.from_scu_id, detail: 'Edge origin does not exist.' })
    if (!scuIds.has(edge.to_scu_id)) findings.push({ code: 'STALE_EDGE', severity: 'error', subject: edge.from_scu_id, detail: `Target ${edge.to_scu_id} does not exist.` })
    const from = snapshot.scus.find((scu) => scu.scu_id === edge.from_scu_id)
    const expectedSource = from?.editorial_method === 'authored_declaration'
      ? from.editorial_sources[0]?.source_ref
      : from ? `CapabilityDescriptor:${from.source_descriptor_uris[0]}#drill_children` : null
    const exactSourceEdge = expectedSnapshot.edges.some((candidate) => canonicalize(candidate) === canonicalize(edge))
    if (edge.from_scu_id === edge.to_scu_id || !edge.edge_source || !edge.source_ref || edge.source_ref !== expectedSource || !exactSourceEdge) {
      findings.push({ code: 'INVALID_SEMANTIC_EDGE', severity: 'error', subject: edge.from_scu_id, detail: 'Edge is self-referential or lacks source-backed origin evidence.' })
    }
  }
  for (const conceptId of new Set([...conceptById.keys(), ...expectedConceptById.keys()])) {
    const actual = conceptById.get(conceptId)
    const expected = expectedConceptById.get(conceptId)
    if (!actual || !expected || canonicalize(actual) !== canonicalize(expected)) {
      findings.push({ code: expected ? 'CONCEPT_BINDING_MISMATCH' : 'UNBOUND_CONCEPT', severity: 'error', subject: conceptId, detail: 'Concept universe entry is missing, extra, or differs from the exact type/source aggregation.' })
    }
  }
  const validProducerBindings = new Map<string, ProducerSemanticBinding[]>()
  const authoredProducerBindings = new Map(getProducerSemanticReview().flatMap((group) => group.asset_ids.map((assetId) => [assetId, {
    target_scu_id: group.target_scu_id,
    rationale: group.rationale,
    source_refs: [producerSourceRef(assetId), producerReviewRef(group.target_scu_id, assetId)],
  }] as const)))
  for (const binding of snapshot.producer_semantic_bindings ?? []) {
    const authored = authoredProducerBindings.get(binding.asset_id)
    const knownAsset = ACTIVE_PRODUCER_IDS.includes(binding.asset_id)
    const validTarget = scuIds.has(binding.target_scu_id)
    const valid = knownAsset && validTarget && binding.relation === 'provides_evidence_for'
      && authored?.target_scu_id === binding.target_scu_id
      && authored.rationale === binding.rationale
      && canonicalize(binding.source_refs) === canonicalize(authored.source_refs)
    if (!valid) {
      findings.push({
        code: 'INVALID_PRODUCER_SEMANTIC_BINDING', severity: 'error', subject: binding.asset_id,
        detail: 'Producer semantic binding has an unknown asset, stale target, invalid relation, weak rationale, or incorrect W1 source reference.',
      })
    } else {
      const entries = validProducerBindings.get(binding.asset_id) ?? []
      entries.push(binding)
      validProducerBindings.set(binding.asset_id, entries)
    }
  }
  for (const assetId of ACTIVE_PRODUCER_IDS) {
    const count = validProducerBindings.get(assetId)?.length ?? 0
    if (count === 0) findings.push({ code: 'UNBOUND_ACTIVE_PRODUCER', severity: 'error', subject: assetId, detail: 'Active W1 producer has no valid source-backed semantic binding.' })
    if (count > 1) findings.push({ code: 'INVALID_PRODUCER_SEMANTIC_BINDING', severity: 'error', subject: assetId, detail: 'Active W1 producer appears in more than one semantic binding.' })
  }
  for (const scu of snapshot.scus) {
    const expectedDisposition = expectedSnapshot.scus.find((candidate) => candidate.scu_id === scu.scu_id)?.producer_semantic_disposition
    const valid = expectedDisposition
      && canonicalize(scu.producer_semantic_disposition) === canonicalize(expectedDisposition)
    if (!valid) findings.push({ code: 'INVALID_PRODUCER_SEMANTIC_DISPOSITION', severity: 'error', subject: scu.scu_id, detail: 'SCU producer disposition disagrees with the exhaustive producer binding set.' })
  }
  const graph = graphMetrics(snapshot.scus, snapshot.edges)
  for (const scu of snapshot.scus) {
    const incident = snapshot.edges.some((edge) => edge.from_scu_id === scu.scu_id || edge.to_scu_id === scu.scu_id)
    const expectedDisposition = expectedSnapshot.scus.find((candidate) => candidate.scu_id === scu.scu_id)?.graph_disposition
    const valid = incident
      ? scu.graph_disposition.status === 'connected' && scu.graph_disposition.source_refs.length > 0
      : scu.graph_disposition.status === 'isolated_dispositioned' && scu.graph_disposition.rationale.length > 0 && scu.graph_disposition.source_refs.length > 0
    if (!valid || !expectedDisposition || canonicalize(scu.graph_disposition) !== canonicalize(expectedDisposition)) findings.push({ code: incident ? 'INVALID_GRAPH_DISPOSITION' : 'ISOLATED_SCU', severity: 'error', subject: scu.scu_id, detail: 'Graph connectivity and exact source-backed disposition disagree.' })
  }
  if (graph.components < 1 && snapshot.scus.length > 0) findings.push({ code: 'DISCONNECTED_GRAPH', severity: 'error', subject: 'semantic_graph', detail: 'Semantic graph component accounting failed.' })
  const sourced = new Set(snapshot.scus.flatMap((scu) => scu.source_descriptor_uris))
  for (const cap of catalog.filter((item) => exclusionReason(item) === null)) {
    if (!sourced.has(cap.uri)) findings.push({ code: 'ORPHAN_DESCRIPTOR', severity: 'error', subject: cap.uri, detail: 'Addressable descriptor has no compiled SCU.' })
  }
  if (snapshot.compatibility_version !== CAPABILITY_COMPATIBILITY_VERSION) {
    findings.push({ code: 'COMPATIBILITY_MISMATCH', severity: 'error', subject: snapshot.compatibility_version, detail: `Expected ${CAPABILITY_COMPATIBILITY_VERSION}.` })
  }
  return deepFreeze({ passed: findings.every((finding) => finding.severity !== 'error'), findings, census: snapshot.census })
}
