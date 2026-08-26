import 'server-only'
import { createHash } from 'node:crypto'
import { z } from 'zod'
import {
  assertFreezableManifest,
  assertManifestMatchesRegistry,
  assertManifestMatchesRegistryIdentity,
  canonicalManifestDigest,
  canonicalRegistryContractDigest,
  CANONICAL_NIRMANA_CHART_ID,
  nirmanaExecutionContractForRegistryRow,
  NirmanaElevationManifestSchema,
  registryContractFingerprintInput,
  type NirmanaElevationManifest,
  type NirmanaRegistryContractRow,
} from './definitions'
import {
  NirmanaLegacyAliasSchema,
} from './label-contract'

const layerIds = {
  brahmagyan: 'L0',
  ganita: 'L1',
  bodha: 'L2',
  kala: 'L3',
  phala: 'L4',
  mimamsa: 'L5',
} as const
const registryLayerNames = {
  L0: 'brahmagyan',
  L1: 'ganita',
  L2: 'bodha',
  L3: 'kala',
  L4: 'phala',
  L5: 'mimamsa',
} as const
const layerRanks = { L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, L5: 5 } as const

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

function digest(value: unknown): string {
  return createHash('sha256').update(stableJson(value)).digest('hex')
}

const NirmanaBaselineLabelSchema = z.object({
  asset_id: z.string().min(1),
  sanskrit_name: z.string().min(1).nullable(),
  english_name: z.string().min(1).nullable(),
  description: z.string().min(1).nullable(),
  legacy_aliases: z.array(NirmanaLegacyAliasSchema),
  source_ref: z.string().min(1).max(512),
}).strict()

export type NirmanaBaselineLabel = z.infer<typeof NirmanaBaselineLabelSchema>

function canonicalCandidateLabelCatalogueDigest(labels: NirmanaBaselineLabel[]): string {
  const parsed = z.array(NirmanaBaselineLabelSchema).min(1).parse(labels)
  if (new Set(parsed.map((label) => label.asset_id)).size !== parsed.length) {
    throw new Error('Candidate label catalogue asset IDs must be unique.')
  }
  return digest([...parsed].sort((left, right) => left.asset_id.localeCompare(right.asset_id)))
}

export interface NirmanaBaselineCandidate {
  manifest: NirmanaElevationManifest
  manifest_sha256: string
  labels: NirmanaBaselineLabel[]
  catalogue_sha256: string
  registry_identity_sha256: string
  registry_contract_sha256: string
}

export type NirmanaMonitorStatusCode =
  | 'in_sync'
  | 'baseline_missing'
  | 'plan_adaptation_required'
  | 'evidence_refresh_required'
  | 'label_refresh_required'
  | 'release_attention'
  | 'source_unavailable'

export interface NirmanaMonitorStatus {
  status: NirmanaMonitorStatusCode
  affected_asset_ids: string[]
  current_definition_sha256: string | null
  candidate_definition_sha256: string
  registry_identity_sha256: string
  registry_contract_sha256: string
  candidate_catalogue_sha256: string
}

export interface NirmanaAcceptedDefinition {
  definition_status: 'frozen'
  manifest: NirmanaElevationManifest
  manifest_sha256: string
}

export interface NirmanaMonitorComparisonObservation {
  source_error_code?: string | null
  selected_catalogue_sha256?: string | null
  selected_catalogue_asset_ids?: string[]
  incomplete_label_asset_ids?: string[]
  release_in_sync?: boolean | null
}

function orderedRegistryRows(rows: NirmanaRegistryContractRow[]): NirmanaRegistryContractRow[] {
  return [...rows].sort((left, right) => {
    const layerOrder = layerRanks[layerIds[left.layer]] - layerRanks[layerIds[right.layer]]
    if (layerOrder !== 0) return layerOrder
    const sortOrder = left.sort_order - right.sort_order
    return sortOrder !== 0 ? sortOrder : left.asset_id.localeCompare(right.asset_id)
  })
}

function deriveWaveIndices(manifest: NirmanaElevationManifest): Map<string, number> {
  const byId = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  const memo = new Map<string, number>()
  const waveFor = (assetId: string): number => {
    const existing = memo.get(assetId)
    if (existing !== undefined) return existing
    const asset = byId.get(assetId)
    if (!asset) return 0
    const sameLayerDependencies = (asset.depends_on ?? [])
      .map((dependencyId) => byId.get(dependencyId))
      .filter((dependency): dependency is NonNullable<typeof dependency> => dependency?.layer === asset.layer)
    const wave = sameLayerDependencies.length === 0
      ? 0
      : Math.max(...sameLayerDependencies.map((dependency) => waveFor(dependency.asset_id))) + 1
    memo.set(assetId, wave)
    return wave
  }
  for (const asset of manifest.assets) waveFor(asset.asset_id)
  return memo
}

export function buildNirmanaBaselineCandidate(rows: NirmanaRegistryContractRow[]): NirmanaBaselineCandidate {
  const orderedRows = orderedRegistryRows(rows)
  const manifestWithoutWaves = NirmanaElevationManifestSchema.parse({
    chart_id: CANONICAL_NIRMANA_CHART_ID,
    assets: orderedRows.map((row) => {
      const dependsOn = [...(row.depends_on ?? [])].sort()
      const registryFingerprintInput = registryContractFingerprintInput({ ...row, depends_on: dependsOn })
      return {
        asset_id: row.asset_id,
        layer: layerIds[row.layer],
        depends_on: dependsOn,
        ...nirmanaExecutionContractForRegistryRow(row),
        registry_contract: registryFingerprintInput.registry_contract,
        registry_fingerprint_sha256: canonicalRegistryContractDigest(registryFingerprintInput),
      }
    }),
  })
  const waveIndices = deriveWaveIndices(manifestWithoutWaves)
  const manifest = NirmanaElevationManifestSchema.parse({
    ...manifestWithoutWaves,
    assets: manifestWithoutWaves.assets.map((asset) => ({
      ...asset,
      wave_index: waveIndices.get(asset.asset_id),
    })),
  })
  assertFreezableManifest(manifest)

  const labels = orderedRows.map((row) => NirmanaBaselineLabelSchema.parse({
    asset_id: row.asset_id,
    sanskrit_name: row.sanskrit_name ?? null,
    english_name: row.english_name ?? null,
    description: row.english_description ?? null,
    legacy_aliases: [],
    source_ref: `asset_registry:${row.asset_id}`,
  }))
  const identity = manifest.assets.map((asset) => ({
    asset_id: asset.asset_id,
    layer: asset.layer,
    depends_on: [...(asset.depends_on ?? [])].sort(),
  })).sort((left, right) => left.asset_id.localeCompare(right.asset_id))
  const contracts = manifest.assets.map((asset) => ({
    asset_id: asset.asset_id,
    registry_fingerprint_sha256: asset.registry_fingerprint_sha256,
  })).sort((left, right) => left.asset_id.localeCompare(right.asset_id))

  return {
    manifest,
    manifest_sha256: canonicalManifestDigest(manifest),
    labels,
    catalogue_sha256: canonicalCandidateLabelCatalogueDigest(labels),
    registry_identity_sha256: digest(identity),
    registry_contract_sha256: digest(contracts),
  }
}

function registryRowsFromCandidate(candidate: NirmanaBaselineCandidate): NirmanaRegistryContractRow[] {
  return candidate.manifest.assets.map((asset) => {
    if (!asset.registry_contract) throw new Error(`Candidate asset ${asset.asset_id} is missing its registry contract.`)
    return {
      asset_id: asset.asset_id,
      layer: registryLayerNames[asset.layer],
      depends_on: asset.depends_on ?? [],
      ...asset.registry_contract,
    }
  })
}

function affectedIdentityAssets(
  current: NirmanaElevationManifest,
  candidate: NirmanaElevationManifest,
): string[] {
  const identityById = (manifest: NirmanaElevationManifest) => new Map(manifest.assets.map((asset) => [
    asset.asset_id,
    stableJson({ layer: asset.layer, depends_on: [...(asset.depends_on ?? [])].sort() }),
  ]))
  const currentById = identityById(current)
  const candidateById = identityById(candidate)
  return [...new Set([...currentById.keys(), ...candidateById.keys()])]
    .filter((assetId) => currentById.get(assetId) !== candidateById.get(assetId))
    .sort()
}

function affectedContractAssets(
  current: NirmanaElevationManifest,
  candidate: NirmanaElevationManifest,
): string[] {
  const currentById = new Map(current.assets.map((asset) => [asset.asset_id, asset.registry_fingerprint_sha256]))
  return candidate.assets
    .filter((asset) => currentById.get(asset.asset_id) !== asset.registry_fingerprint_sha256)
    .map((asset) => asset.asset_id)
    .sort()
}

function statusResult(
  status: NirmanaMonitorStatusCode,
  candidate: NirmanaBaselineCandidate,
  currentDefinitionSha256: string | null,
  affectedAssetIds: string[] = [],
): NirmanaMonitorStatus {
  return {
    status,
    affected_asset_ids: [...new Set(affectedAssetIds)].sort(),
    current_definition_sha256: currentDefinitionSha256,
    candidate_definition_sha256: candidate.manifest_sha256,
    registry_identity_sha256: candidate.registry_identity_sha256,
    registry_contract_sha256: candidate.registry_contract_sha256,
    candidate_catalogue_sha256: candidate.catalogue_sha256,
  }
}

export function classifyNirmanaDivergence(input: {
  definition: NirmanaAcceptedDefinition | null
  candidate: NirmanaBaselineCandidate
  observation: NirmanaMonitorComparisonObservation | null
}): NirmanaMonitorStatus {
  const { candidate, definition, observation } = input
  if (observation?.source_error_code) {
    return statusResult('source_unavailable', candidate, definition?.manifest_sha256 ?? null)
  }
  if (!definition) return statusResult('baseline_missing', candidate, null)

  const currentManifest = NirmanaElevationManifestSchema.parse(definition.manifest)
  const currentDigest = canonicalManifestDigest(currentManifest)
  if (currentDigest !== definition.manifest_sha256) {
    throw new Error('Current frozen definition digest does not match its canonical manifest.')
  }
  const candidateRegistryRows = registryRowsFromCandidate(candidate)

  try {
    assertManifestMatchesRegistryIdentity(currentManifest, candidateRegistryRows)
  } catch {
    return statusResult(
      'plan_adaptation_required',
      candidate,
      currentDigest,
      affectedIdentityAssets(currentManifest, candidate.manifest),
    )
  }

  try {
    assertManifestMatchesRegistry(currentManifest, candidateRegistryRows)
  } catch {
    return statusResult(
      'evidence_refresh_required',
      candidate,
      currentDigest,
      affectedContractAssets(currentManifest, candidate.manifest),
    )
  }

  const candidateLabelAssetIds = candidate.labels.map((label) => label.asset_id)
  const selectedLabelAssetIds = observation?.selected_catalogue_asset_ids
  const labelCoverageDrift = selectedLabelAssetIds === undefined
    ? []
    : [...new Set([...candidateLabelAssetIds, ...selectedLabelAssetIds])]
      .filter((assetId) => candidateLabelAssetIds.includes(assetId) !== selectedLabelAssetIds.includes(assetId))
  const labelDigestDrift = observation?.selected_catalogue_sha256 !== undefined
    && observation.selected_catalogue_sha256 !== candidate.catalogue_sha256
  const incompleteLabelAssetIds = observation?.incomplete_label_asset_ids ?? []
  if (labelDigestDrift || labelCoverageDrift.length > 0 || incompleteLabelAssetIds.length > 0) {
    return statusResult(
      'label_refresh_required',
      candidate,
      currentDigest,
      [
        ...(labelDigestDrift ? [...candidateLabelAssetIds, ...(selectedLabelAssetIds ?? [])] : []),
        ...labelCoverageDrift,
        ...incompleteLabelAssetIds,
      ],
    )
  }

  if (observation?.release_in_sync !== undefined && observation.release_in_sync !== true) {
    return statusResult('release_attention', candidate, currentDigest)
  }

  return statusResult('in_sync', candidate, currentDigest)
}
