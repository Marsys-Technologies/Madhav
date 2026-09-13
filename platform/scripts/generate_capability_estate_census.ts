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
import { dirname, join, relative, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

import { getCatalog } from '../src/lib/retrieval/registry/catalog'
import type { CapabilityDescriptor } from '../src/lib/retrieval/registry/types'
import {
  buildCapabilityPublicNameBridge,
  extractRegistrarCapabilityBindings,
} from './manifest/extract_registrar_capability_bridge'
import { resolveType } from './manifest/projection_builders'

const GENERATOR_VERSION = 'capability-estate-census/v1'
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
      ambiguous: number
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
      current_spec_rows: 'not_mechanically_resolved'
      basis: string
    }
  }
  details: {
    planner_addressability: {
      excluded: Array<{ capability_uri: string; reason: string }>
    }
    public_registrar_resolution: {
      verified: Array<{ descriptor_name: string; capability_uri: string; public_tool_name: string }>
      unresolved_descriptor_names: string[]
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
      current_spec_resolution_note: string
    }
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
  const dir = join(repoRoot, 'platform', 'supabase', 'migrations')
  return readdirSync(dir)
    .filter((name) => name.endsWith('.sql'))
    .map((name) => join(dir, name))
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
  const descriptorByName = new Map(catalog.map((cap) => [cap.name, cap]))

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
  const publicBridge = buildCapabilityPublicNameBridge(catalog)
  const publicResolved = [...publicBridge.resolved.entries()].map(([descriptorName, publicToolName]) => ({
    descriptor_name: descriptorName,
    capability_uri: descriptorByName.get(descriptorName)?.uri ?? '',
    public_tool_name: publicToolName,
  })).sort((a, b) => a.descriptor_name.localeCompare(b.descriptor_name))
  const publicAmbiguous = [...publicBridge.ambiguous.entries()].map(([descriptorName, candidates]) => ({
    descriptor_name: descriptorName,
    selected_public_tool_name: publicBridge.resolved.get(descriptorName) ?? '',
    candidates: [...candidates].sort(),
  })).sort((a, b) => a.descriptor_name.localeCompare(b.descriptor_name))
  const ambiguousDescriptorNames = new Set(publicAmbiguous.map((entry) => entry.descriptor_name))
  const publicVerified = publicResolved.filter((entry) => !ambiguousDescriptorNames.has(entry.descriptor_name))

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

  const registrarDir = join(repoRoot, 'platform-mcp', 'src', 'tools')
  const registrarFiles = walkTypeScriptSources(registrarDir)
  const registryDir = join(repoRoot, 'platform', 'src', 'lib', 'retrieval', 'registry')
  const registryFiles = walkTypeScriptSources(registryDir)
  const catalogSourcePath = join(repoRoot, 'platform', 'src', 'lib', 'retrieval', 'registry', 'catalog.ts')
  const assetSeedPath = join(repoRoot, 'platform', 'scripts', 'seed', 'asset_registry_seed.ts')
  const canonicalFacesPath = join(repoRoot, 'platform', 'src', 'lib', 'retrieval', 'registry', 'canonical_faces.json')
  const bridgeExtractorPath = join(repoRoot, 'platform', 'scripts', 'manifest', 'extract_registrar_capability_bridge.ts')
  const generatorPath = join(repoRoot, 'platform', 'scripts', 'generate_capability_estate_census.ts')

  const sources: ProvenanceSource[] = [
    {
      id: 'live_runtime_catalog_projection',
      path: relative(repoRoot, catalogSourcePath),
      sha256: descriptorFingerprint(catalog),
    },
    { id: 'producer_asset_seed', path: relative(repoRoot, assetSeedPath), sha256: hashFile(assetSeedPath) },
    { id: 'writer_digest_inventory', path: relative(repoRoot, writerDigestPath), sha256: hashFile(writerDigestPath) },
    { id: 'analysis_layer_pins', path: relative(repoRoot, pinsPath), sha256: hashFile(pinsPath) },
    { id: 'canonical_public_faces', path: relative(repoRoot, canonicalFacesPath), sha256: hashFile(canonicalFacesPath) },
    { id: 'census_generator', path: relative(repoRoot, generatorPath), sha256: hashFile(generatorPath) },
    { id: 'registrar_bridge_extractor', path: relative(repoRoot, bridgeExtractorPath), sha256: hashFile(bridgeExtractorPath) },
    sourceSet(repoRoot, 'runtime_registry_source_set', 'platform/src/lib/retrieval/registry/**/*.ts (excluding tests)', registryFiles),
    sourceSet(repoRoot, 'public_registrar_source_set', 'platform-mcp/src/tools/**/*.ts (excluding tests)', registrarFiles),
    sourceSet(repoRoot, 'output_digest_migration_source_set', 'platform/supabase/migrations/* containing asset_output_digest_specs', digestMigrationFiles),
  ].sort((a, b) => a.id.localeCompare(b.id))
  const sourcePaths = sortedUnique([
    catalogSourcePath,
    assetSeedPath,
    writerDigestPath,
    pinsPath,
    canonicalFacesPath,
    generatorPath,
    bridgeExtractorPath,
    ...registryFiles,
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
      'Public registrar resolution is a source-text audit using the existing extractor. Its documented parser limitations can produce false unresolved results; verified means mechanically evidenced, unresolved does not necessarily mean absent at runtime.',
      'Reviewed output-digest coverage counts assets named by static INSERT statements. Procedural retire/replace migrations and deployed database state are not replayed, so the unique current spec row per asset is not mechanically resolved here.',
      'A reviewed output-digest specification establishes deterministic output hashing, not semantic value, population, planner reachability, or empirical validity.',
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
        verified: publicVerified.length,
        resolved_including_ambiguous: publicResolved.length,
        unresolved: publicBridge.unresolved.length,
        ambiguous: publicAmbiguous.length,
        literal_public_names: extractedRegistrar.liveDirectNames.size,
        unambiguous_uri_bindings: extractedRegistrar.bindings.length,
        method: 'existing extract_registrar_capability_bridge.ts source-text scanner over non-test platform-mcp/src/tools TypeScript files',
      },
      producer_assets: {
        total: assets.length,
        active: activeAssetIds.length,
        retired: retiredAssetIds.length,
        writer_identities: writerIds.length,
        non_writer_identities: nonWriterIds.length,
        by_layer: countBy(assets.map((asset) => asset.layer)),
        by_storage_type: countBy(assets.map((asset) => asset.storage_type)),
        by_scope: countBy(assets.map((asset) => asset.scope)),
        by_catalog_status: countBy(assets.map((asset) => asset.catalog_status ?? 'undeclared')),
      },
      reviewed_output_digest_coverage: {
        asset_denominator: assetIds.length,
        active_asset_denominator: activeAssetIds.length,
        assets_with_any_reviewed_spec: reviewedAssetIds.length,
        assets_without_any_reviewed_spec: assetsWithoutReviewedSpec.length,
        active_assets_without_any_reviewed_spec: activeAssetsWithoutReviewedSpec.length,
        current_spec_rows: 'not_mechanically_resolved' as const,
        basis: 'distinct asset IDs found in static INSERT statements targeting asset_output_digest_specs, intersected with the producer asset seed',
      },
    },
    details: {
      planner_addressability: { excluded: plannerExcluded },
      public_registrar_resolution: {
        verified: publicVerified,
        unresolved_descriptor_names: [...publicBridge.unresolved].sort(),
        ambiguous: publicAmbiguous,
        known_extractor_limitations: [
          'regAlias/globalAlias parsing examines a bounded sequence of string literals, so concatenated descriptions can hide an otherwise real URI binding.',
          'Dynamic or table-driven registrations without a unique literal capability URI cannot be attributed 1:1 by source-text inspection.',
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
        current_spec_resolution_note: 'not_mechanically_resolved: determining each deployed current row requires ordered migration replay or a live read of asset_output_digest_specs WHERE retired_at IS NULL; this static census does neither',
      },
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
