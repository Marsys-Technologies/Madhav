/**
 * Mechanically reproducible census of the capability and producer estate.
 *
 * This is deliberately an accounting artifact, not a semantic-capability
 * catalog. It keeps runtime descriptors, planner addressability, public
 * registrar resolution, producer assets, and reviewed output-digest coverage
 * as separate denominators. No generic SCU or semantic-output coverage is
 * inferred here.
 *
 * Usage:
 *   npm run codegen:capability-estate-census
 *   npm run codegen:capability-estate-census:check
 */
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { basename, dirname, join, relative, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

import { getCatalog } from '../src/lib/retrieval/registry/catalog'
import type { CapabilityDescriptor } from '../src/lib/retrieval/registry/types'
import {
  extractRegistrarCapabilityBindings,
} from './manifest/extract_registrar_capability_bridge'
import { resolveType } from './manifest/projection_builders'

const GENERATOR_VERSION = 'capability-estate-census/v1.2'
const DEFAULT_REPO_ROOT = resolve(__dirname, '..', '..')
const DEFAULT_OUTPUT_PATH = join(DEFAULT_REPO_ROOT, 'platform', 'src', 'generated', 'capability_estate_census.json')
const ASSET_ID_PATTERN = /'(?:bg|ga|bo|ka|ph|mi|lel)_[a-z0-9_]+'/g

type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue }
type CountMap = Record<string, number>

interface AssetDefShape {
  asset_id: string
  layer: string
  storage_type: string
  scope: string
  is_active: boolean
  catalog_status?: string
  target_table?: string | null
  count_sql?: string | null
  depends_on?: string[]
  asset_kind?: string
  english_description?: string
}

interface CurrentDigestSpec {
  asset_id: string
  spec_sha256: string
  spec: JsonValue
  migration_path: string
}

type ProducerContractDisposition =
  | 'relational_digest_current_source_intent'
  | 'relational_contract_blocked'
  | 'excluded_nondeterministic'
  | 'service_probe'
  | 'service_effect_contract'
  | 'user_authored_source_contract'

interface ProducerOutputContract {
  asset_id: string
  producer_kind: 'relational' | 'service' | 'user_authored_source'
  disposition: ProducerContractDisposition
  contract_ref: Readonly<Record<string, JsonValue>>
  implementation_refs: string[]
  tests: string[]
  known_gaps: string[]
}

interface DescriptorRouteContract {
  capability_uri: string
  descriptor_name: string
  descriptor_type: string
  planner_disposition: 'addressable' | 'excluded'
  planner_reason: string | null
  internal_route: 'handler' | 'loader'
  internal_route_evidence: string[]
  public_route_disposition: 'reviewed_exposed' | 'reviewed_not_exposed'
  public_tool_names: string[]
  public_routes: Array<{ tool_name: string; route_kind: 'exact_uri_binding' | 'parallel_same_name' }>
  public_route_evidence: string[]
  full_profile_enforcement: 'enforced'
  input_contract: JsonValue
  output_contract: JsonValue
  output_contract_state: 'declared' | 'descriptor_content_untyped'
  pagination: Readonly<Record<string, JsonValue>>
  empty_result_state: 'declared' | 'missing'
  empty_reason_declared: boolean
}

interface ProvenanceSource {
  id: string
  path: string
  sha256: string
  member_count?: number
  members?: Array<{ path: string; sha256: string }>
}

export interface CapabilityEstateCensus {
  schema_version: typeof GENERATOR_VERSION
  generated_at: string
  source_revision: string
  caveats: string[]
  denominators: {
    runtime_descriptors: {
      total: number
      tools: number
      resources: number
      prompts: number
      callable: number
      by_layer: CountMap
      by_scope: CountMap
      by_data_source: CountMap
      paginated_declared: number
      output_schema_declared: number
    }
    planner_addressable_descriptors: {
      total: number
      excluded: number
      policy: string
    }
    public_registrar_resolution: {
      descriptor_denominator: number
      verified: number
      resolved_including_ambiguous: number
      unresolved: number
      not_exposed: number
      ambiguous: number
      name_only_unverified: number
      literal_public_names: number
      unambiguous_uri_bindings: number
      method: string
    }
    producer_assets: {
      total: number
      active: number
      retired: number
      writer_identities: number
      non_writer_identities: number
      by_layer: CountMap
      by_storage_type: CountMap
      by_scope: CountMap
      by_catalog_status: CountMap
    }
    reviewed_output_digest_coverage: {
      asset_denominator: number
      active_asset_denominator: number
      assets_with_any_reviewed_spec: number
      assets_without_any_reviewed_spec: number
      active_assets_without_any_reviewed_spec: number
      current_source_intended_spec_rows: number
      current_source_intended_active_spec_rows: number
      basis: string
    }
    producer_output_contracts: {
      denominator: number
      by_disposition: CountMap
      unexplained: number
    }
    descriptor_route_contracts: {
      denominator: number
      by_public_route_disposition: CountMap
      non_exhaustible_paginated: number
      exhaustible_paginated: number
      descriptor_content_untyped: number
      full_profile_allowlist_enforced: true
    }
  }
  details: {
    planner_addressability: {
      excluded: Array<{ capability_uri: string; reason: string }>
    }
    public_registrar_resolution: {
      verified: Array<{ descriptor_name: string; capability_uri: string; public_tool_name: string }>
      unresolved_descriptor_names: string[]
      name_only_unverified: Array<{ descriptor_name: string; capability_uri: string; public_tool_name: string }>
      ambiguous: Array<{ descriptor_name: string; selected_public_tool_name: string; candidates: string[] }>
      known_extractor_limitations: string[]
    }
    producer_assets: {
      active_asset_ids: string[]
      retired_asset_ids: string[]
      writer_identity_ids: string[]
      non_writer_identity_ids: string[]
      generated_pin_non_writer_ids: string[]
      writer_ids_absent_from_asset_seed: string[]
      asset_ids_without_writer_digest_absent_from_generated_pins: string[]
    }
    reviewed_output_digest_coverage: {
      migration_files_scanned: string[]
      assets_with_any_reviewed_spec: string[]
      assets_without_any_reviewed_spec: string[]
      active_assets_without_any_reviewed_spec: string[]
      inserted_asset_tokens_absent_from_asset_seed: string[]
      current_source_intended_specs: CurrentDigestSpec[]
      current_source_intended_resolution_note: string
    }
    producer_output_contracts: ProducerOutputContract[]
    descriptor_route_contracts: DescriptorRouteContract[]
  }
  provenance: {
    method: string
    sources: ProvenanceSource[]
  }
  content_sha256: string
}

function normalizeForCanonicalJson(value: unknown): JsonValue {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return value
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('canonical JSON does not support non-finite numbers')
    return value
  }
  if (Array.isArray(value)) return value.map((item) => normalizeForCanonicalJson(item))
  if (typeof value === 'object') {
    const out: Record<string, JsonValue> = {}
    for (const key of Object.keys(value as Record<string, unknown>).sort()) {
      const child = (value as Record<string, unknown>)[key]
      if (child !== undefined) out[key] = normalizeForCanonicalJson(child)
    }
    return out
  }
  throw new Error(`canonical JSON does not support ${typeof value}`)
}

export function canonicalJson(value: unknown): string {
  return JSON.stringify(normalizeForCanonicalJson(value))
}

function sha256(value: string | Buffer): string {
  return createHash('sha256').update(value).digest('hex')
}

function producerContractIsExplained(repoRoot: string, contract: ProducerOutputContract): boolean {
  const hasRefs = contract.implementation_refs.length > 0
    && contract.tests.length > 0
    && contract.implementation_refs.every((ref) =>
      ref.startsWith('relation:') || ref.startsWith('asset_registry_count_sql:') || existsSync(join(repoRoot, ref)))
    && contract.tests.every((ref) => existsSync(join(repoRoot, ref)))
  if (!hasRefs || Object.keys(contract.contract_ref).length === 0) return false

  const ref = contract.contract_ref
  switch (contract.disposition) {
    case 'relational_digest_current_source_intent':
      return typeof ref.spec_sha256 === 'string'
        && /^[a-f0-9]{64}$/.test(ref.spec_sha256)
        && typeof ref.migration_path === 'string'
        && existsSync(join(repoRoot, ref.migration_path))
    case 'relational_contract_blocked':
      return typeof ref.blocker === 'string' && ref.blocker.length > 0 && contract.known_gaps.includes(ref.blocker)
    case 'excluded_nondeterministic':
      return typeof ref.retirement_migration === 'string'
        && existsSync(join(repoRoot, ref.retirement_migration))
        && typeof ref.negative_invariant === 'string'
    case 'service_probe':
    case 'service_effect_contract':
      return typeof ref.path === 'string'
        && existsSync(join(repoRoot, ref.path))
        && typeof ref.contract_sha256 === 'string'
        && /^[a-f0-9]{64}$/.test(ref.contract_sha256)
    case 'user_authored_source_contract':
      return typeof ref.relation === 'string'
        && typeof ref.scope_key === 'string'
        && typeof ref.contract === 'string'
    default:
      return false
  }
}

function hashFile(path: string): string {
  return sha256(readFileSync(path))
}

function countBy(values: readonly string[]): CountMap {
  const counts: CountMap = {}
  for (const value of values) counts[value] = (counts[value] ?? 0) + 1
  return Object.fromEntries(Object.entries(counts).sort(([a], [b]) => a.localeCompare(b)))
}

function sortedUnique(values: readonly string[]): string[] {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b))
}

function walkTypeScriptSources(dir: string): string[] {
  const files: string[] = []
  for (const entry of readdirSync(dir).sort()) {
    const path = join(dir, entry)
    const stat = statSync(path)
    if (stat.isDirectory()) {
      if (entry !== '__tests__') files.push(...walkTypeScriptSources(path))
    } else if (entry.endsWith('.ts') && !entry.includes('.test.')) {
      files.push(path)
    }
  }
  return files.sort((a, b) => a.localeCompare(b))
}

function sourceSet(
  repoRoot: string,
  id: string,
  displayPath: string,
  files: readonly string[],
): ProvenanceSource {
  const members = files.map((path) => ({
    path: relative(repoRoot, path),
    sha256: hashFile(path),
  })).sort((a, b) => a.path.localeCompare(b.path))
  return {
    id,
    path: displayPath,
    sha256: sha256(canonicalJson(members)),
    member_count: members.length,
    members,
  }
}

function isCallable(cap: CapabilityDescriptor): boolean {
  const loader = (cap as CapabilityDescriptor & { loader?: unknown }).loader
  return typeof cap.handler === 'function' || typeof loader === 'function'
}

function descriptorFingerprint(catalog: readonly CapabilityDescriptor[]): string {
  const projection = catalog.map((cap) => ({
    uri: cap.uri,
    type: resolveType(cap),
    name: cap.name,
    layer: cap.layer,
    scope: cap.scope,
    data_source: cap.data_source ?? null,
    projection_tags: cap.projection_tags ?? [],
    calibration_context_only: cap.calibration_context_only === true,
    input_schema: cap.input_schema ?? null,
    required_inputs: cap.required_inputs ?? [],
    output_schema: cap.output_schema ?? null,
    density_contract: cap.density_contract ?? null,
  })).sort((a, b) => a.uri.localeCompare(b.uri))
  return sha256(canonicalJson(projection))
}

function outputDigestMigrationFiles(repoRoot: string): string[] {
  const dirs = [
    join(repoRoot, 'platform', 'migrations'),
    join(repoRoot, 'platform', 'supabase', 'migrations'),
  ]
  return dirs
    .flatMap((dir) => readdirSync(dir)
      .filter((name) => name.endsWith('.sql'))
      .map((name) => join(dir, name)))
    .filter((path) => readFileSync(path, 'utf8').includes('asset_output_digest_specs'))
    .sort((a, b) => a.localeCompare(b))
}

function reviewedSpecAssetTokens(files: readonly string[]): string[] {
  const tokens: string[] = []
  for (const path of files) {
    const sql = readFileSync(path, 'utf8')
    const insertStatements = sql.match(/INSERT\s+INTO\s+(?:public\.)?asset_output_digest_specs\b[\s\S]*?;/gi) ?? []
    for (const statement of insertStatements) {
      for (const match of statement.match(ASSET_ID_PATTERN) ?? []) tokens.push(match.slice(1, -1))
    }
  }
  return sortedUnique(tokens)
}

function stripSqlComments(sql: string): string {
  let out = ''
  let i = 0
  let quote: "'" | '"' | null = null
  while (i < sql.length) {
    const char = sql[i]!
    const next = sql[i + 1]
    if (quote) {
      out += char
      if (char === quote) {
        if (quote === "'" && next === "'") {
          out += next
          i += 2
          continue
        }
        quote = null
      }
      i += 1
      continue
    }
    if (char === "'" || char === '"') {
      quote = char
      out += char
      i += 1
      continue
    }
    if (char === '-' && next === '-') {
      while (i < sql.length && sql[i] !== '\n') {
        out += ' '
        i += 1
      }
      continue
    }
    if (char === '/' && next === '*') {
      out += '  '
      i += 2
      while (i < sql.length && !(sql[i] === '*' && sql[i + 1] === '/')) {
        out += sql[i] === '\n' ? '\n' : ' '
        i += 1
      }
      if (i < sql.length) {
        out += '  '
        i += 2
      }
      continue
    }
    out += char
    i += 1
  }
  return out
}

function sqlString(value: string): string {
  return value.replaceAll("''", "'")
}

/**
 * Replays only the append/retire state machine for asset_output_digest_specs.
 * This is deliberately not a database-schema replay and makes no deployed-state
 * claim; it resolves the source-intended current row after lexically ordered
 * migrations from both governed trees.
 */
function currentSourceIntendedDigestSpecs(repoRoot: string, files: readonly string[]): CurrentDigestSpec[] {
  const current = new Map<string, CurrentDigestSpec>()
  const ordered = [...files].sort((a, b) => basename(a).localeCompare(basename(b)) || a.localeCompare(b))
  for (const path of ordered) {
    const sql = stripSqlComments(readFileSync(path, 'utf8'))
    const stringConstants = new Map<string, string>()
    const jsonConstants = new Map<string, JsonValue>()
    const constantPattern = /\b([a-z_][a-z0-9_]*)\s+constant\s+(text|jsonb)\s*:=\s*'((?:''|[^'])*)'(?:\s*::\s*jsonb)?\s*;/gi
    let constantMatch: RegExpExecArray | null
    while ((constantMatch = constantPattern.exec(sql))) {
      const name = constantMatch[1]!
      const value = sqlString(constantMatch[3]!)
      if (constantMatch[2]!.toLowerCase() === 'jsonb') jsonConstants.set(name, normalizeForCanonicalJson(JSON.parse(value)))
      else stringConstants.set(name, value)
    }

    const actions: Array<{ index: number; apply: () => void }> = []
    const insertPattern = /INSERT\s+INTO\s+(?:public\.)?asset_output_digest_specs\s*\(\s*asset_id\s*,\s*spec_sha256\s*,\s*spec\s*\)([\s\S]*?)(?:ON\s+CONFLICT|;)/gi
    let insertMatch: RegExpExecArray | null
    while ((insertMatch = insertPattern.exec(sql))) {
      const values = insertMatch[1]!
      const tuplePattern = /\(\s*'((?:''|[^'])+)'\s*,\s*(?:'([a-f0-9]{64})'|([a-z_][a-z0-9_]*))\s*,\s*(?:'((?:''|[^'])*)'\s*::\s*jsonb|([a-z_][a-z0-9_]*))\s*\)/gi
      let tupleMatch: RegExpExecArray | null
      while ((tupleMatch = tuplePattern.exec(values))) {
        const assetId = sqlString(tupleMatch[1]!)
        const specSha = tupleMatch[2] ?? stringConstants.get(tupleMatch[3] ?? '')
        const spec = tupleMatch[4] !== undefined
          ? normalizeForCanonicalJson(JSON.parse(sqlString(tupleMatch[4])))
          : jsonConstants.get(tupleMatch[5] ?? '')
        if (!specSha || !spec) throw new Error(`unable to resolve digest spec tuple for ${assetId} in ${relative(repoRoot, path)}`)
        const record = { asset_id: assetId, spec_sha256: specSha, spec, migration_path: relative(repoRoot, path) }
        actions.push({ index: insertMatch.index + tupleMatch.index, apply: () => current.set(assetId, record) })
      }
    }

    const updatePattern = /UPDATE\s+(?:public\.)?asset_output_digest_specs\s+SET\s+retired_at\s*=[\s\S]*?WHERE([\s\S]*?);/gi
    let updateMatch: RegExpExecArray | null
    while ((updateMatch = updatePattern.exec(sql))) {
      const where = updateMatch[1]!
      const ids = [
        ...(where.match(/asset_id\s*=\s*'((?:''|[^'])+)'/i)?.[1]
          ? [sqlString(where.match(/asset_id\s*=\s*'((?:''|[^'])+)'/i)![1]!)]
          : []),
        ...((where.match(/asset_id\s+IN\s*\(([^)]*)\)/i)?.[1] ?? '').match(/'((?:''|[^'])+)'/g) ?? []).map((value) => sqlString(value.slice(1, -1))),
      ]
      if (ids.length > 0) actions.push({ index: updateMatch.index, apply: () => ids.forEach((id) => current.delete(id)) })
    }
    actions.sort((a, b) => a.index - b.index).forEach((action) => action.apply())
  }
  return [...current.values()].sort((a, b) => a.asset_id.localeCompare(b.asset_id))
}

function descriptorSourceEvidence(
  repoRoot: string,
  registryFiles: readonly string[],
  capabilityUri: string,
  descriptorName: string,
): string[] {
  const escapedUri = capabilityUri.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const escapedName = descriptorName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const uriPattern = new RegExp(`[\\"']${escapedUri}[\\"']`)
  const namePattern = new RegExp(`\\bname\\s*:\\s*[\\"']${escapedName}[\\"']`)
  return registryFiles
    .filter((path) => {
      const source = readFileSync(path, 'utf8')
      return uriPattern.test(source) || namePattern.test(source)
    })
    .map((path) => relative(repoRoot, path))
    .sort()
}

function paginationForDescriptor(cap: CapabilityDescriptor): string {
  const schema = (cap.input_schema ?? {}) as Record<string, unknown>
  const properties = schema['type'] === 'object'
    && schema['properties']
    && typeof schema['properties'] === 'object'
    && !Array.isArray(schema['properties'])
    ? schema['properties'] as Record<string, unknown>
    : schema
  if ('cursor' in properties) return 'cursor'
  if ('offset' in properties) return 'offset'
  return 'bounded_without_position'
}

function readReviewedFullProfileToolNames(authorityPath: string): Set<string> {
  const source = readFileSync(authorityPath, 'utf8')
  const block = source.match(/REVIEWED_FULL_PROFILE_TOOL_NAMES\s*=\s*\[([\s\S]*?)\]\s*as const/)
  if (!block) throw new Error(`unable to parse reviewed full-profile authority: ${authorityPath}`)
  return new Set([...block[1]!.matchAll(/'([a-z0-9_]+)'/g)].map((match) => match[1]!))
}

function gitValue(repoRoot: string, args: string[]): string {
  return execFileSync('git', args, { cwd: repoRoot, encoding: 'utf8' }).trim()
}

function sourceCommit(repoRoot: string, sourcePaths: readonly string[]): { revision: string; generatedAt: string } {
  try {
    const relativePaths = sourcePaths.map((path) => relative(repoRoot, path))
    const revision = gitValue(repoRoot, ['log', '-1', '--format=%H', '--', ...relativePaths])
    const committedAt = gitValue(repoRoot, ['show', '-s', '--format=%cI', revision])
    return { revision, generatedAt: new Date(committedAt).toISOString() }
  } catch {
    // Content hashes still make archive builds reproducible when git metadata is absent.
    return { revision: 'unavailable', generatedAt: '1970-01-01T00:00:00.000Z' }
  }
}

async function loadAssetSeedWithoutRunningWriter(): Promise<AssetDefShape[]> {
  const priorNodeEnv = process.env.NODE_ENV
  process.env.NODE_ENV = 'test'
  try {
    const seed = await import('./seed/asset_registry_seed')
    return seed.ASSETS as AssetDefShape[]
  } finally {
    if (priorNodeEnv === undefined) delete process.env.NODE_ENV
    else process.env.NODE_ENV = priorNodeEnv
  }
}

export async function buildCapabilityEstateCensus(options: {
  generatedAt?: string
  repoRoot?: string
} = {}): Promise<CapabilityEstateCensus> {
  const repoRoot = resolve(options.repoRoot ?? DEFAULT_REPO_ROOT)
  const catalog = getCatalog()

  const plannerExcluded = catalog
    .filter((cap) => cap.calibration_context_only === true || !isCallable(cap))
    .map((cap) => ({
      capability_uri: cap.uri,
      reason: cap.calibration_context_only === true
        ? 'calibration_context_only'
        : 'no executable handler or loader',
    }))
    .sort((a, b) => a.capability_uri.localeCompare(b.capability_uri))

  const extractedRegistrar = extractRegistrarCapabilityBindings()

  const assets = await loadAssetSeedWithoutRunningWriter()
  const assetIds = sortedUnique(assets.map((asset) => asset.asset_id))
  if (assetIds.length !== assets.length) throw new Error('asset_registry_seed.ts contains duplicate asset_id values')
  const activeAssetIds = sortedUnique(assets.filter((asset) => asset.is_active).map((asset) => asset.asset_id))
  const retiredAssetIds = sortedUnique(assets.filter((asset) => !asset.is_active).map((asset) => asset.asset_id))

  const writerDigestPath = join(repoRoot, 'platform', 'src', 'generated', 'nirmana-writer-digests.json')
  const writerDigestInventory = JSON.parse(readFileSync(writerDigestPath, 'utf8')) as { writers: Record<string, string> }
  const writerIds = sortedUnique(Object.keys(writerDigestInventory.writers))
  const writerIdSet = new Set(writerIds)
  const assetIdSet = new Set(assetIds)
  const nonWriterIds = assetIds.filter((id) => !writerIdSet.has(id))
  const writerIdsAbsentFromAssets = writerIds.filter((id) => !assetIdSet.has(id))

  const pinsPath = join(repoRoot, 'platform', 'src', 'generated', 'nirmana-analysis-layer-pins.json')
  const pins = JSON.parse(readFileSync(pinsPath, 'utf8')) as {
    layers: Record<string, { non_writer_assets: string[] }>
  }
  const pinNonWriterIds = sortedUnique(Object.values(pins.layers).flatMap((layer) => layer.non_writer_assets))
  const pinNonWriterSet = new Set(pinNonWriterIds)

  const digestMigrationFiles = outputDigestMigrationFiles(repoRoot)
  const insertedSpecTokens = reviewedSpecAssetTokens(digestMigrationFiles)
  const reviewedAssetIds = insertedSpecTokens.filter((id) => assetIdSet.has(id))
  const reviewedAssetIdSet = new Set(reviewedAssetIds)
  const assetsWithoutReviewedSpec = assetIds.filter((id) => !reviewedAssetIdSet.has(id))
  const activeAssetsWithoutReviewedSpec = activeAssetIds.filter((id) => !reviewedAssetIdSet.has(id))
  const currentSourceSpecs = currentSourceIntendedDigestSpecs(repoRoot, digestMigrationFiles)
  const currentSourceSpecByAsset = new Map(currentSourceSpecs.map((spec) => [spec.asset_id, spec]))

  const registrarDir = join(repoRoot, 'platform-mcp', 'src', 'tools')
  const registrarFiles = walkTypeScriptSources(registrarDir)
  const registryDir = join(repoRoot, 'platform', 'src', 'lib', 'retrieval', 'registry')
  const registryFiles = walkTypeScriptSources(registryDir)
  const synthesisDir = join(repoRoot, 'platform', 'src', 'lib', 'retrieval', 'synthesis')
  const descriptorSourceFiles = [...registryFiles, ...walkTypeScriptSources(synthesisDir)]
    .sort((a, b) => a.localeCompare(b))
  const catalogSourcePath = join(repoRoot, 'platform', 'src', 'lib', 'retrieval', 'registry', 'catalog.ts')
  const assetSeedPath = join(repoRoot, 'platform', 'scripts', 'seed', 'asset_registry_seed.ts')
  const canonicalFacesPath = join(repoRoot, 'platform', 'src', 'lib', 'retrieval', 'registry', 'canonical_faces.json')
  const bridgeExtractorPath = join(repoRoot, 'platform', 'scripts', 'manifest', 'extract_registrar_capability_bridge.ts')
  const generatorPath = join(repoRoot, 'platform', 'scripts', 'generate_capability_estate_census.ts')
  const serviceProbePath = join(repoRoot, 'platform', 'python-sidecar', 'scripts', 'nirmana_probe_contracts.json')
  const serviceEffectPath = join(repoRoot, 'platform', 'python-sidecar', 'scripts', 'nirmana_service_effect_contracts.json')
  const fullRouteAuthorityPath = join(repoRoot, 'platform-mcp', 'src', 'lib', 'mcp_full_route_authority.ts')
  const reviewedFullToolNames = readReviewedFullProfileToolNames(fullRouteAuthorityPath)
  const serviceProbes = JSON.parse(readFileSync(serviceProbePath, 'utf8')) as Record<string, JsonValue>
  const serviceEffectsDocument = JSON.parse(readFileSync(serviceEffectPath, 'utf8')) as {
    schema_version: string
    contracts: Record<string, JsonValue>
  }

  const producerOutputContracts: ProducerOutputContract[] = assets
    .filter((asset) => asset.is_active)
    .map((asset): ProducerOutputContract => {
      const shared = {
        asset_id: asset.asset_id,
        implementation_refs: [] as string[],
        tests: [] as string[],
        known_gaps: ['deployed_current_state_not_read'],
      }
      if (asset.asset_id === 'ph_nimitta') {
        return {
          ...shared,
          producer_kind: 'relational',
          disposition: 'excluded_nondeterministic',
          contract_ref: {
            retirement_migration: 'platform/migrations/1016_nirmana_l4_ph_nimitta_digest_spec_retire.sql',
            negative_invariant: 'no current asset_output_digest_specs row',
          },
          implementation_refs: ['platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py'],
          tests: [
            'platform/python-sidecar/tests/test_ph_nimitta_base_rate.py',
            'platform/python-sidecar/tests/test_ph_nimitta_honest_defaults.py',
            'platform/python-sidecar/tests/test_ph_nimitta_spine.py',
            'platform/python-sidecar/tests/test_ph_nimitta_writer_date_coercion.py',
          ],
          known_gaps: [
            'posterior metadata collapses an unordered multi-row domain',
            'discovery selection uses a non-total top-100 ordering',
            'deployed_current_state_not_read',
          ],
        }
      }
      if (asset.asset_id === 'lel_events') {
        return {
          ...shared,
          producer_kind: 'user_authored_source',
          disposition: 'user_authored_source_contract',
          contract_ref: {
            relation: 'life_events',
            scope_key: 'chart_id',
            contract: 'schema, chart isolation, authorization, provenance, and prediction-generation no-leakage',
          },
          implementation_refs: [
            'platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts',
            'platform/src/lib/retrieval/registry/layers/L5_mimamsa/lel_intake_checklist.ts',
          ],
          tests: [
            'platform/src/lib/retrieval/registry/layers/L5_mimamsa/__tests__/lel_intake_checklist.test.ts',
            'platform/src/app/api/mcp/writes/__tests__/lel_event_record.test.ts',
          ],
          known_gaps: ['deployed_current_state_not_read'],
        }
      }
      if (asset.storage_type === 'service') {
        const probe = serviceProbes[asset.asset_id]
        if (probe) {
          return {
            ...shared,
            producer_kind: 'service',
            disposition: 'service_probe',
            contract_ref: {
              path: relative(repoRoot, serviceProbePath),
              contract_sha256: sha256(canonicalJson({ health_probe: probe })),
              probe_type: typeof probe === 'object' && probe && !Array.isArray(probe)
                ? (probe as Record<string, JsonValue>)['probe_type'] ?? null
                : null,
            },
            implementation_refs: ['platform/python-sidecar/pipeline/orchestrator/service_probes.py'],
            tests: [
              'platform/python-sidecar/tests/test_service_probes.py',
              'platform/python-sidecar/tests/test_nirmana_probe_route.py',
            ],
            known_gaps: ['deployed_current_state_not_read', 'release_smoke_not_estate_complete'],
          }
        }
        const effect = serviceEffectsDocument.contracts[asset.asset_id]
        if (!effect) throw new Error(`active service ${asset.asset_id} has no probe or effect contract`)
        return {
          ...shared,
          producer_kind: 'service',
          disposition: 'service_effect_contract',
          contract_ref: {
            path: relative(repoRoot, serviceEffectPath),
            contract_sha256: sha256(canonicalJson(effect)),
            authority_state: typeof effect === 'object' && effect && !Array.isArray(effect)
              ? (effect as Record<string, JsonValue>)['authority_state'] ?? null
              : null,
          },
          implementation_refs: typeof effect === 'object' && effect && !Array.isArray(effect)
            ? [String((effect as Record<string, JsonValue>)['implementation_ref'])]
            : [],
          tests: ['platform/python-sidecar/tests/test_purna_anvesana_service_effect_contracts.py'],
          known_gaps: asset.asset_id === 'mi_abhilekha'
            ? ['product_review_required_for_non_confirming_answer_semantics', 'disposable_fixture_execution_not_yet_run', 'deployed_current_state_not_read']
            : ['disposable_fixture_execution_not_yet_run', 'deployed_current_state_not_read'],
        }
      }
      const currentSpec = currentSourceSpecByAsset.get(asset.asset_id)
      if (currentSpec) {
        return {
          ...shared,
          producer_kind: 'relational',
          disposition: 'relational_digest_current_source_intent',
          contract_ref: {
            spec_sha256: currentSpec.spec_sha256,
            migration_path: currentSpec.migration_path,
            source_state: 'ordered_static_replay_not_database_replay',
          },
          implementation_refs: asset.target_table
            ? [`relation:${asset.target_table}`]
            : asset.count_sql
              ? [`asset_registry_count_sql:${asset.asset_id}`]
              : [],
          tests: ['platform/python-sidecar/pipeline/orchestrator/tests/test_output_digest.py'],
          known_gaps: ['disposable_schema_and_key_validation_not_yet_run', 'deployed_current_state_not_read'],
        }
      }
      const blockers: Record<string, string> = {
        ka_vighnakara: 'kala_obstruction lacks one stable non-null natural key across convergence and dasha anchors',
        ka_gochara_v3_century_materialize: 'digest v1 cannot hash stable parent hierarchy identity without hashing unstable parent_window_id',
      }
      const blocker = blockers[asset.asset_id]
      if (!blocker) throw new Error(`active relational producer ${asset.asset_id} has no current source-intended spec or named blocker`)
      return {
        ...shared,
        producer_kind: 'relational',
        disposition: 'relational_contract_blocked',
        contract_ref: { blocker },
        implementation_refs: asset.target_table
          ? [`relation:${asset.target_table}`]
          : asset.count_sql
            ? [`asset_registry_count_sql:${asset.asset_id}`]
            : [],
        tests: ['platform/scripts/__tests__/generate_capability_estate_census.test.ts'],
        known_gaps: [blocker, 'deployed_current_state_not_read'],
      }
    })
    .sort((a, b) => a.asset_id.localeCompare(b.asset_id))

  const exactBindingsByUri = new Map<string, Array<{ tool_name: string; source_file: string }>>()
  for (const binding of extractedRegistrar.bindings) {
    const currentBindings = exactBindingsByUri.get(binding.capability_uri) ?? []
    currentBindings.push({ tool_name: binding.tool_name, source_file: relative(repoRoot, binding.source_file) })
    exactBindingsByUri.set(binding.capability_uri, currentBindings)
  }
  const descriptorRouteContracts: DescriptorRouteContract[] = catalog.map((cap): DescriptorRouteContract => {
    const exactBindings = (exactBindingsByUri.get(cap.uri) ?? [])
      .filter((binding) => reviewedFullToolNames.has(binding.tool_name))
      .sort((a, b) => a.tool_name.localeCompare(b.tool_name) || a.source_file.localeCompare(b.source_file))
    const exactNames = sortedUnique(exactBindings.map((binding) => binding.tool_name))
    const parallelSameName = reviewedFullToolNames.has(cap.name) && !exactNames.includes(cap.name)
    const publicRoutes: DescriptorRouteContract['public_routes'] = [
      ...exactNames.map((tool_name) => ({ tool_name, route_kind: 'exact_uri_binding' as const })),
      ...(parallelSameName ? [{ tool_name: cap.name, route_kind: 'parallel_same_name' as const }] : []),
    ]
    const publicToolNames = sortedUnique(publicRoutes.map((route) => route.tool_name))
    const exclusion = plannerExcluded.find((entry) => entry.capability_uri === cap.uri)
    const loader = (cap as CapabilityDescriptor & { loader?: unknown }).loader
    const paginationVerified = cap.semantic_capabilities?.some((declaration) => declaration.primary_binding_details?.pagination_verified === true) ?? false
    const declaredPaginated = cap.density_contract?.paginated === true
    return {
      capability_uri: cap.uri,
      descriptor_name: cap.name,
      descriptor_type: resolveType(cap),
      planner_disposition: exclusion ? 'excluded' : 'addressable',
      planner_reason: exclusion?.reason ?? null,
      internal_route: typeof cap.handler === 'function' ? 'handler' : typeof loader === 'function' ? 'loader' : (() => { throw new Error(`${cap.uri} has no internal handler or loader`) })(),
      internal_route_evidence: descriptorSourceEvidence(repoRoot, descriptorSourceFiles, cap.uri, cap.name),
      public_route_disposition: publicRoutes.length > 0 ? 'reviewed_exposed' : 'reviewed_not_exposed',
      public_tool_names: publicToolNames,
      public_routes: publicRoutes,
      public_route_evidence: publicRoutes.length > 0
        ? sortedUnique([
          ...exactBindings.map((binding) => `${binding.source_file}:${binding.tool_name}`),
          `${relative(repoRoot, fullRouteAuthorityPath)}:reviewed_allowlist`,
        ])
        : [`${relative(repoRoot, fullRouteAuthorityPath)}:reviewed_not_exposed`],
      full_profile_enforcement: 'enforced',
      input_contract: normalizeForCanonicalJson(cap.input_schema ?? null),
      output_contract: normalizeForCanonicalJson(cap.output_schema ?? null),
      output_contract_state: cap.output_schema === undefined ? 'descriptor_content_untyped' : 'declared',
      pagination: declaredPaginated
        ? paginationVerified
          ? { disposition: 'exhaustible_reviewed', declared: paginationForDescriptor(cap) }
          : { disposition: 'non_exhaustible', declared: paginationForDescriptor(cap), blocker: 'response collection and exhaustion paths are not source-reviewed' }
        : { disposition: 'not_paginated' },
      empty_result_state: cap.density_contract?.empty_reason ? 'declared' : 'missing',
      empty_reason_declared: cap.density_contract?.empty_reason === true,
    }
  }).sort((a, b) => a.capability_uri.localeCompare(b.capability_uri))

  const sources: ProvenanceSource[] = [
    {
      id: 'live_runtime_catalog_projection',
      path: relative(repoRoot, catalogSourcePath),
      sha256: descriptorFingerprint(catalog),
    },
    { id: 'producer_asset_seed', path: relative(repoRoot, assetSeedPath), sha256: hashFile(assetSeedPath) },
    { id: 'writer_digest_inventory', path: relative(repoRoot, writerDigestPath), sha256: hashFile(writerDigestPath) },
    { id: 'analysis_layer_pins', path: relative(repoRoot, pinsPath), sha256: hashFile(pinsPath) },
    { id: 'service_probe_contracts', path: relative(repoRoot, serviceProbePath), sha256: hashFile(serviceProbePath) },
    { id: 'service_effect_contracts', path: relative(repoRoot, serviceEffectPath), sha256: hashFile(serviceEffectPath) },
    { id: 'reviewed_full_profile_route_authority', path: relative(repoRoot, fullRouteAuthorityPath), sha256: hashFile(fullRouteAuthorityPath) },
    { id: 'canonical_public_faces', path: relative(repoRoot, canonicalFacesPath), sha256: hashFile(canonicalFacesPath) },
    { id: 'census_generator', path: relative(repoRoot, generatorPath), sha256: hashFile(generatorPath) },
    { id: 'registrar_bridge_extractor', path: relative(repoRoot, bridgeExtractorPath), sha256: hashFile(bridgeExtractorPath) },
    sourceSet(repoRoot, 'runtime_registry_source_set', 'platform/src/lib/retrieval/{registry,synthesis}/**/*.ts (excluding tests)', descriptorSourceFiles),
    sourceSet(repoRoot, 'public_registrar_source_set', 'platform-mcp/src/tools/**/*.ts (excluding tests)', registrarFiles),
    sourceSet(
      repoRoot,
      'output_digest_migration_source_set',
      'platform/{migrations,supabase/migrations}/*.sql containing asset_output_digest_specs',
      digestMigrationFiles,
    ),
  ].sort((a, b) => a.id.localeCompare(b.id))
  const sourcePaths = sortedUnique([
    catalogSourcePath,
    assetSeedPath,
    writerDigestPath,
    pinsPath,
    canonicalFacesPath,
    generatorPath,
    bridgeExtractorPath,
    serviceProbePath,
    serviceEffectPath,
    fullRouteAuthorityPath,
    ...descriptorSourceFiles,
    ...registrarFiles,
    ...digestMigrationFiles,
  ])
  const sourceCommitMetadata = sourceCommit(repoRoot, sourcePaths)
  const generatedAt = options.generatedAt ?? sourceCommitMetadata.generatedAt

  const base = {
    schema_version: GENERATOR_VERSION,
    generated_at: generatedAt,
    source_revision: sourceCommitMetadata.revision,
    caveats: [
      'This artifact is an estate census only. It does not create SCUs or infer that a descriptor semantically covers a producer output.',
      'Descriptor exposure is joined to the authored, fail-closed full-profile allowlist. Exact URI bindings are source-evidenced; a same-name parallel route is enumerated separately and never substituted for exact URI proof.',
      'Current source-intended output-digest rows replay only the append/retire state machine across lexically ordered migration source. This is not a schema migration execution and is not deployed database proof.',
      'A reviewed output-digest specification establishes deterministic output hashing, not semantic value, population, planner reachability, or empirical validity.',
      'The full MCP profile is registration-gated by the reviewed route authority; its real registration set is exact-set tested independently.',
    ],
    denominators: {
      runtime_descriptors: {
        total: catalog.length,
        tools: catalog.filter((cap) => resolveType(cap) === 'tool').length,
        resources: catalog.filter((cap) => resolveType(cap) === 'resource').length,
        prompts: catalog.filter((cap) => resolveType(cap) === 'prompt').length,
        callable: catalog.filter(isCallable).length,
        by_layer: countBy(catalog.map((cap) => cap.layer)),
        by_scope: countBy(catalog.map((cap) => cap.scope)),
        by_data_source: countBy(catalog.map((cap) => cap.data_source ?? 'undeclared')),
        paginated_declared: catalog.filter((cap) => cap.density_contract?.paginated === true).length,
        output_schema_declared: catalog.filter((cap) => cap.output_schema !== undefined).length,
      },
      planner_addressable_descriptors: {
        total: catalog.length - plannerExcluded.length,
        excluded: plannerExcluded.length,
        policy: 'live descriptor has a callable handler/loader and calibration_context_only is not true; public dispatchability is reported separately',
      },
      public_registrar_resolution: {
        descriptor_denominator: catalog.length,
        verified: descriptorRouteContracts.filter((contract) => contract.public_route_disposition === 'reviewed_exposed').length,
        resolved_including_ambiguous: descriptorRouteContracts.filter((contract) => contract.public_route_disposition === 'reviewed_exposed').length,
        unresolved: 0,
        not_exposed: descriptorRouteContracts.filter((contract) => contract.public_route_disposition === 'reviewed_not_exposed').length,
        ambiguous: 0,
        name_only_unverified: 0,
        literal_public_names: reviewedFullToolNames.size,
        unambiguous_uri_bindings: descriptorRouteContracts.flatMap((contract) => contract.public_routes)
          .filter((route) => route.route_kind === 'exact_uri_binding').length,
        method: 'authored fail-closed full-profile route authority joined to source-evidenced URI bindings; absent dedicated descriptor routes are explicit reviewed_not_exposed dispositions',
      },
      producer_assets: {
        total: assets.length,
        active: activeAssetIds.length,
        retired: retiredAssetIds.length,
        writer_identities: writerIds.length,
        non_writer_identities: nonWriterIds.length,
        by_layer: countBy(assets.filter((asset) => asset.is_active).map((asset) => asset.layer)),
        by_storage_type: countBy(assets.filter((asset) => asset.is_active).map((asset) => asset.storage_type)),
        by_scope: countBy(assets.filter((asset) => asset.is_active).map((asset) => asset.scope)),
        by_catalog_status: countBy(assets.filter((asset) => asset.is_active).map((asset) => asset.catalog_status ?? 'undeclared')),
      },
      reviewed_output_digest_coverage: {
        asset_denominator: assetIds.length,
        active_asset_denominator: activeAssetIds.length,
        assets_with_any_reviewed_spec: reviewedAssetIds.length,
        assets_without_any_reviewed_spec: assetsWithoutReviewedSpec.length,
        active_assets_without_any_reviewed_spec: activeAssetsWithoutReviewedSpec.length,
        current_source_intended_spec_rows: currentSourceSpecs.length,
        current_source_intended_active_spec_rows: currentSourceSpecs.filter((spec) => activeAssetIds.includes(spec.asset_id)).length,
        basis: 'distinct static INSERT identities plus ordered append/retire source replay across both governed migration trees; no database was queried',
      },
      producer_output_contracts: {
        denominator: producerOutputContracts.length,
        by_disposition: countBy(producerOutputContracts.map((contract) => contract.disposition)),
        unexplained: producerOutputContracts.filter((contract) => !producerContractIsExplained(repoRoot, contract)).length,
      },
      descriptor_route_contracts: {
        denominator: descriptorRouteContracts.length,
        by_public_route_disposition: countBy(descriptorRouteContracts.map((contract) => contract.public_route_disposition)),
        non_exhaustible_paginated: descriptorRouteContracts.filter((contract) => contract.pagination['disposition'] === 'non_exhaustible').length,
        exhaustible_paginated: descriptorRouteContracts.filter((contract) => contract.pagination['disposition'] === 'exhaustible_reviewed').length,
        descriptor_content_untyped: descriptorRouteContracts.filter((contract) => contract.output_contract_state === 'descriptor_content_untyped').length,
        full_profile_allowlist_enforced: true as const,
      },
    },
    details: {
      planner_addressability: { excluded: plannerExcluded },
      public_registrar_resolution: {
        verified: descriptorRouteContracts
          .filter((contract) => contract.public_route_disposition === 'reviewed_exposed')
          .map((contract) => ({
            descriptor_name: contract.descriptor_name,
            capability_uri: contract.capability_uri,
            public_tool_name: contract.public_tool_names[0]!,
          })),
        unresolved_descriptor_names: [],
        name_only_unverified: [],
        ambiguous: [],
        known_extractor_limitations: [
          'Dynamic or table-driven registrations without a unique literal capability URI cannot be attributed 1:1 by source-text inspection.',
          'A reviewed public same-name route without unique URI source evidence is recorded as parallel_same_name, not promoted to exact_uri_binding.',
        ],
      },
      producer_assets: {
        active_asset_ids: activeAssetIds,
        retired_asset_ids: retiredAssetIds,
        writer_identity_ids: writerIds,
        non_writer_identity_ids: nonWriterIds,
        generated_pin_non_writer_ids: pinNonWriterIds,
        writer_ids_absent_from_asset_seed: writerIdsAbsentFromAssets,
        asset_ids_without_writer_digest_absent_from_generated_pins: nonWriterIds.filter((id) => !pinNonWriterSet.has(id)),
      },
      reviewed_output_digest_coverage: {
        migration_files_scanned: digestMigrationFiles.map((path) => relative(repoRoot, path)),
        assets_with_any_reviewed_spec: reviewedAssetIds,
        assets_without_any_reviewed_spec: assetsWithoutReviewedSpec,
        active_assets_without_any_reviewed_spec: activeAssetsWithoutReviewedSpec,
        inserted_asset_tokens_absent_from_asset_seed: insertedSpecTokens.filter((id) => !assetIdSet.has(id)),
        current_source_intended_specs: currentSourceSpecs,
        current_source_intended_resolution_note: 'Source-intended state only: ordered append/retire migration source replay. A disposable database replay is required for schema/key validation; an authorized live read is required for deployed-current truth.',
      },
      producer_output_contracts: producerOutputContracts,
      descriptor_route_contracts: descriptorRouteContracts,
    },
    provenance: {
      method: 'DB-free source census with recursively key-sorted canonical JSON and SHA-256 fingerprints',
      sources,
    },
  }
  return { ...base, content_sha256: sha256(canonicalJson(base)) }
}

export function renderCapabilityEstateCensus(census: CapabilityEstateCensus): string {
  return `${JSON.stringify(normalizeForCanonicalJson(census), null, 2)}\n`
}

async function main(): Promise<void> {
  const check = process.argv.includes('--check')
  const census = await buildCapabilityEstateCensus()
  const rendered = renderCapabilityEstateCensus(census)
  if (check) {
    if (!existsSync(DEFAULT_OUTPUT_PATH)) {
      console.error(`[capability-estate-census] drift: missing ${DEFAULT_OUTPUT_PATH}`)
      process.exitCode = 1
      return
    }
    const current = readFileSync(DEFAULT_OUTPUT_PATH, 'utf8')
    if (current !== rendered) {
      console.error(`[capability-estate-census] drift: regenerate ${DEFAULT_OUTPUT_PATH}`)
      process.exitCode = 1
      return
    }
    console.log(`[capability-estate-census] OK ${census.content_sha256}`)
    return
  }
  mkdirSync(dirname(DEFAULT_OUTPUT_PATH), { recursive: true })
  writeFileSync(DEFAULT_OUTPUT_PATH, rendered, 'utf8')
  console.log(`[capability-estate-census] wrote ${DEFAULT_OUTPUT_PATH}`)
  console.log(`[capability-estate-census] SHA-256 ${census.content_sha256}`)
}

const invokedPath = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : ''
if (invokedPath === import.meta.url) {
  main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : String(error))
    process.exitCode = 1
  })
}
