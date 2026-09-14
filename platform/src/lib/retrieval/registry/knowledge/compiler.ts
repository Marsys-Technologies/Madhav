import type { CapabilityDescriptor } from '../types'
import {
  CAPABILITY_COMPATIBILITY_VERSION,
  CAPABILITY_KNOWLEDGE_SCHEMA_VERSION,
  type CapabilityKnowledgeCensus,
  type CapabilityKnowledgeSnapshot,
  type KnowledgeIntegrityFinding,
  type KnowledgeIntegrityReport,
  type PaginationSemantics,
  type SemanticCapabilityBinding,
  type SemanticCapabilityDeclaration,
  type SemanticCapabilityEdge,
  type SemanticCapabilityUnit,
} from './types'
import { canonicalize, deepFreeze, stableFingerprint } from './stable'

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
  return {
    scu_id: `scu.catalog.${slug(cap.name)}`,
    version: 1,
    label: cap.display?.short_label ?? cap.name.replaceAll('_', ' '),
    description: cap.display?.one_line ?? cap.description,
    kind: cap.archetype === 'temporal' ? 'temporal'
      : cap.archetype === 'prose_citation' ? 'citation'
      : cap.archetype === 'cross_domain' ? 'contradiction'
      : cap.tool_role === 'synthesizer' ? 'synthesis_support'
      : cap.tool_role === 'graph' ? 'mechanism'
      : cap.traversal_level === 'L-DOMAIN' ? 'assessment'
      : 'datum',
    domains: cap.traversal_level === 'L-DOMAIN' ? [slug(cap.name).replace(/^assess_/, '')] : ['all'],
    concepts: Array.from(new Set([cap.name, cap.archetype, cap.tool_role, ...(cap.projection_tags ?? [])])).sort(),
    intents: [cap.traversal_level.toLowerCase(), cap.tool_role],
    horizons: cap.archetype === 'temporal' ? ['current', 'multi_year'] : ['natal'],
    scope: cap.scope === 'per_chart' ? 'chart' : 'global',
    inputs: Object.keys(inputParameters.properties).sort(),
    outputs: cap.output_schema ? ['structured_content'] : ['content'],
    primary_binding_uri: cap.uri,
    edges: (cap.drill_children ?? []).map((child) => ({
      relation: 'enables' as const,
      target_scu_id: `scu.catalog.${slug(child.split('/').at(-1) ?? child)}`,
      rationale: 'Derived from the executable descriptor drill_children contract.',
    })),
    provenance_requirements: cap.data_source === 'computed'
      ? ['chart_id_when_chart_scoped', 'computed_at', 'engine_version']
      : ['chart_id_when_chart_scoped', 'build_id', 'formula_or_writer_version'],
    freshness_policy: cap.data_source === 'computed'
      ? 'Must carry computation time and engine version.'
      : 'Must resolve against the active compatible chart build.',
    entitlement: 'native',
    safety_notes: cap.mutation
      ? ['Mutation-capable: execution requires explicit authorization and audit receipt.']
      : ['Read-only evidence surface; planner must not interpret returned chart facts.'],
    known_gaps: cap.calibration_context_only ? ['Calibration-context-only; excluded from planner addressability.'] : [],
    editorial: false,
  }
}

function normalizeDeclaration(
  declaration: SemanticCapabilityDeclaration,
  source: CapabilityDescriptor,
): SemanticCapabilityUnit {
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
  return {
    ...declaration,
    domains: [...new Set(declaration.domains)].sort(),
    concepts: [...new Set(declaration.concepts)].sort(),
    intents: [...new Set(declaration.intents)].sort(),
    horizons: [...new Set(declaration.horizons)].sort(),
    inputs: [...new Set(declaration.inputs)].sort(),
    outputs: [...new Set(declaration.outputs)].sort(),
    bindings: [primary, ...(declaration.additional_bindings ?? [])].sort((a, b) => a.binding_id.localeCompare(b.binding_id)),
    source_descriptor_uris: [source.uri],
  }
}

function buildCensus(
  catalog: readonly CapabilityDescriptor[],
  scus: readonly SemanticCapabilityUnit[],
): CapabilityKnowledgeCensus {
  const exclusions = catalog.flatMap((cap) => {
    const reason = exclusionReason(cap)
    return reason ? [{ capability_uri: cap.uri, reason }] : []
  }).map((item) => ({
    capability_uri: item.capability_uri,
    reason: item.reason,
  })).sort((a, b) => a.capability_uri.localeCompare(b.capability_uri))
  const bindings = scus.flatMap((scu) => scu.bindings)
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
    exclusions,
  }
}

export function compileCapabilityKnowledge(
  catalog: readonly CapabilityDescriptor[],
  generatedAt = new Date().toISOString(),
): CapabilityKnowledgeSnapshot {
  const addressable = catalog.filter((cap) => exclusionReason(cap) === null)
  const scus = addressable.flatMap((cap) => {
    const declarations = cap.semantic_capabilities?.length ? cap.semantic_capabilities : [deriveDeclaration(cap)]
    return declarations.map((declaration) => normalizeDeclaration(declaration, cap))
  }).sort((a, b) => a.scu_id.localeCompare(b.scu_id))

  const derivedIdToActual = new Map(addressable.map((cap) => [
    `scu.catalog.${slug(cap.name)}`,
    (cap.semantic_capabilities?.[0] ?? deriveDeclaration(cap)).scu_id,
  ]))
  const edges: SemanticCapabilityEdge[] = scus.flatMap((scu) => (scu.edges ?? []).map((edge) => ({
    from_scu_id: scu.scu_id,
    relation: edge.relation,
    to_scu_id: derivedIdToActual.get(edge.target_scu_id) ?? edge.target_scu_id,
    rationale: edge.rationale,
  }))).sort((a, b) => canonicalize(a).localeCompare(canonicalize(b)))

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
  })).sort((a, b) => a.uri.localeCompare(b.uri)))
  const census = buildCensus(catalog, scus)
  const hashMaterial = {
    schema_version: CAPABILITY_KNOWLEDGE_SCHEMA_VERSION,
    compatibility_version: CAPABILITY_COMPATIBILITY_VERSION,
    source_catalog_fingerprint: sourceCatalogFingerprint,
    scus,
    edges,
    census,
  }
  return deepFreeze({
    schema_version: CAPABILITY_KNOWLEDGE_SCHEMA_VERSION,
    compatibility_version: CAPABILITY_COMPATIBILITY_VERSION,
    generated_at: generatedAt,
    content_hash: stableFingerprint(hashMaterial),
    source_catalog_fingerprint: sourceCatalogFingerprint,
    scus,
    edges,
    census,
  })
}

export function inspectCapabilityKnowledge(
  catalog: readonly CapabilityDescriptor[],
  snapshot: CapabilityKnowledgeSnapshot,
): KnowledgeIntegrityReport {
  const findings: KnowledgeIntegrityFinding[] = []
  const descriptorByUri = new Map(catalog.map((cap) => [cap.uri, cap]))
  const scuIds = new Set<string>()
  for (const scu of snapshot.scus) {
    if (scuIds.has(scu.scu_id)) findings.push({ code: 'DUPLICATE_SCU', severity: 'error', subject: scu.scu_id, detail: 'SCU id is not unique.' })
    scuIds.add(scu.scu_id)
    const primary = scu.bindings.filter((binding) => binding.relation === 'primary')
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
  }
  for (const edge of snapshot.edges) {
    if (!scuIds.has(edge.to_scu_id)) findings.push({ code: 'STALE_EDGE', severity: 'error', subject: edge.from_scu_id, detail: `Target ${edge.to_scu_id} does not exist.` })
  }
  const sourced = new Set(snapshot.scus.flatMap((scu) => scu.source_descriptor_uris))
  for (const cap of catalog.filter((item) => exclusionReason(item) === null)) {
    if (!sourced.has(cap.uri)) findings.push({ code: 'ORPHAN_DESCRIPTOR', severity: 'error', subject: cap.uri, detail: 'Addressable descriptor has no compiled SCU.' })
  }
  if (snapshot.compatibility_version !== CAPABILITY_COMPATIBILITY_VERSION) {
    findings.push({ code: 'COMPATIBILITY_MISMATCH', severity: 'error', subject: snapshot.compatibility_version, detail: `Expected ${CAPABILITY_COMPATIBILITY_VERSION}.` })
  }
  return deepFreeze({ passed: findings.every((finding) => finding.severity !== 'error'), findings, census: snapshot.census })
}
