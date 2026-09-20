import { stableFingerprint } from '../../src/lib/retrieval/registry/knowledge/stable'
import type { AcceptanceCaseInput, AcceptanceSuite } from './acceptance_cases'

export type AcceptanceDoor = 'portal' | 'managed_mcp' | 'raw_mcp'
export type CollectionTerminal = 'complete' | 'incomplete' | 'blocked' | 'transport_error'
export const PURNA_COLLECTION_ARTIFACT_VERSION = 'purna-collected-cases/v3' as const
export const PURNA_ACCOUNTABLE_ANSWERS_VERSION = 'purna-accountable-answers/v1' as const
const SHA256_FINGERPRINT = /^sha256:[a-f0-9]{64}$/

/**
 * A protected changed-path release may intentionally retain an unchanged MCP
 * service revision while promoting a web-only repair.  Bind each door to the
 * revision actually selected for it; `expected_revision` remains the source
 * release identity for the whole collection.
 */
export interface DoorExpectedRevisions {
  readonly portal: string
  readonly managed_mcp: string
  readonly raw_mcp: string
}

export interface AcceptanceCase {
  readonly id: string
  readonly question: string
  readonly scope_tuple: Record<string, unknown>
  readonly requiredDimensions: readonly string[]
  readonly expected: 'supported_complete' | 'honest_insufficient'
}

/** A redacted reference only; raw evidence stays in the configured restricted directory. */
export interface CollectedCase {
  readonly caseId: string
  readonly door: AcceptanceDoor
  readonly inquiryId: string | null
  readonly expectedRevision: string
  readonly observedRevision: string | null
  /** Chart identity returned by the served channel, never just the requested id. */
  readonly observedChartId: string | null
  readonly snapshotHash: string | null
  readonly chartBuildId: string | null
  readonly answer: string
  /** Typed server envelope retained for independent answer assessment. */
  readonly responseAccountability: unknown | null
  readonly receiptRefs: readonly string[]
  readonly materialFactIds: readonly string[]
  readonly deliveredFactIds: readonly string[]
  readonly unresolvedObligationIds: readonly string[]
  readonly networkCallCount: number
  readonly source: 'candidate' | 'live' | 'fixture'
  readonly terminal: CollectionTerminal
  readonly diagnostic: string | null
}

export interface DoorClient { collect(input: AcceptanceCase): Promise<CollectedCase> }

export interface CollectionManifest {
  readonly suite: AcceptanceSuite
  readonly environment: 'candidate' | 'live'
  readonly expected_revision: string
  readonly expected_door_revisions: DoorExpectedRevisions
  readonly authorization_approval_id: string
  /** Non-secret target identity, carried into the collection hash. */
  readonly target: {
    readonly chart_id: string
    readonly portal_url: string
    readonly mcp_url: string
  }
  readonly case_inputs: readonly AcceptanceCaseInput[]
}

export interface CollectionArtifact {
  readonly schema_version: typeof PURNA_COLLECTION_ARTIFACT_VERSION
  readonly manifest: CollectionManifest
  readonly manifest_hash: string
  readonly rows: readonly CollectedCase[]
  readonly collection_hash: string
}

export interface CollectionProvenance {
  readonly collection_artifact: string
  readonly collection_hash: string
  readonly collection_manifest_hash: string
  readonly suite: AcceptanceSuite
  readonly door: AcceptanceDoor
  readonly environment: 'candidate' | 'live'
  readonly expected_revision: string
  readonly authorization_approval_id: string
  readonly accountable_answers_hash: string
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[]): boolean {
  return Object.keys(value).length === expected.length && Object.keys(value).every((key) => expected.includes(key))
}

function stringArray(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function validDoorExpectedRevisions(value: unknown): value is DoorExpectedRevisions {
  return record(value)
    && exactKeys(value, ['portal', 'managed_mcp', 'raw_mcp'])
    && ['portal', 'managed_mcp', 'raw_mcp'].every((door) => typeof value[door] === 'string' && value[door].length > 0)
}

function validCaseInput(value: unknown): value is AcceptanceCaseInput {
  return record(value)
    && exactKeys(value, ['case_id', 'kind', 'question', 'scope_tuple', 'deterministic_gates', 'required_dimensions', 'expected'])
    && typeof value.case_id === 'string' && value.case_id.length > 0
    && (value.kind === 'beyond_acarya' || value.kind === 'product')
    && (value.question === null || typeof value.question === 'string')
    && (value.scope_tuple === null || record(value.scope_tuple))
    && stringArray(value.deterministic_gates)
    && value.deterministic_gates.length > 0
    && stringArray(value.required_dimensions)
    && (value.expected === null || value.expected === 'supported_complete' || value.expected === 'honest_insufficient')
}

function validCollectedCase(value: unknown): value is CollectedCase {
  if (!record(value) || !exactKeys(value, [
    'caseId', 'door', 'inquiryId', 'expectedRevision', 'observedRevision', 'observedChartId', 'snapshotHash', 'chartBuildId',
    'answer', 'responseAccountability', 'receiptRefs', 'materialFactIds', 'deliveredFactIds',
    'unresolvedObligationIds', 'networkCallCount', 'source', 'terminal', 'diagnostic',
  ])) return false
  return typeof value.caseId === 'string' && value.caseId.length > 0
    && (value.door === 'portal' || value.door === 'managed_mcp' || value.door === 'raw_mcp')
    && (value.inquiryId === null || typeof value.inquiryId === 'string')
    && typeof value.expectedRevision === 'string' && value.expectedRevision.length > 0
    && (value.observedRevision === null || typeof value.observedRevision === 'string')
    && (value.observedChartId === null || typeof value.observedChartId === 'string')
    && (value.snapshotHash === null || typeof value.snapshotHash === 'string')
    && (value.chartBuildId === null || typeof value.chartBuildId === 'string')
    && typeof value.answer === 'string'
    && (value.responseAccountability === null || record(value.responseAccountability))
    && stringArray(value.receiptRefs)
    && stringArray(value.materialFactIds)
    && stringArray(value.deliveredFactIds)
    && stringArray(value.unresolvedObligationIds)
    && Number.isSafeInteger(value.networkCallCount) && (value.networkCallCount as number) >= 0
    && (value.source === 'candidate' || value.source === 'live')
    && ['complete', 'incomplete', 'blocked', 'transport_error'].includes(String(value.terminal))
    && (value.diagnostic === null || typeof value.diagnostic === 'string')
}

function manifestProjection(manifest: CollectionManifest): CollectionManifest {
  return {
    suite: manifest.suite,
    environment: manifest.environment,
    expected_revision: manifest.expected_revision,
    expected_door_revisions: manifest.expected_door_revisions,
    authorization_approval_id: manifest.authorization_approval_id,
    target: manifest.target,
    case_inputs: manifest.case_inputs,
  }
}

function isSafeHttpsUrl(value: unknown): value is string {
  if (typeof value !== 'string' || value.length === 0) return false
  try {
    const url = new URL(value)
    return url.protocol === 'https:' && !url.username && !url.password && !url.search && !url.hash
  } catch { return false }
}

function validTarget(value: unknown): value is CollectionManifest['target'] {
  return record(value)
    && exactKeys(value, ['chart_id', 'portal_url', 'mcp_url'])
    && typeof value.chart_id === 'string' && value.chart_id.length > 0
    && isSafeHttpsUrl(value.portal_url)
    && isSafeHttpsUrl(value.mcp_url)
}

export function createCollectionArtifact(args: {
  readonly suite: AcceptanceSuite
  readonly environment: 'candidate' | 'live'
  readonly expectedRevision: string
  readonly expectedDoorRevisions?: DoorExpectedRevisions
  readonly authorizationApprovalId: string
  readonly target: CollectionManifest['target']
  readonly caseInputs: readonly AcceptanceCaseInput[]
  readonly rows: readonly CollectedCase[]
}): CollectionArtifact {
  const manifest = manifestProjection({
    suite: args.suite,
    environment: args.environment,
    expected_revision: args.expectedRevision,
    expected_door_revisions: args.expectedDoorRevisions ?? {
      portal: args.expectedRevision,
      managed_mcp: args.expectedRevision,
      raw_mcp: args.expectedRevision,
    },
    authorization_approval_id: args.authorizationApprovalId,
    target: args.target,
    case_inputs: args.caseInputs,
  })
  const manifest_hash = stableFingerprint(manifest)
  const projection = {
    schema_version: PURNA_COLLECTION_ARTIFACT_VERSION,
    manifest,
    manifest_hash,
    rows: args.rows,
  }
  return validateCollectionArtifact({ ...projection, collection_hash: stableFingerprint(projection) })
}

export function validateCollectionArtifact(value: unknown): CollectionArtifact {
  if (!record(value) || !exactKeys(value, ['schema_version', 'manifest', 'manifest_hash', 'rows', 'collection_hash'])
    || value.schema_version !== PURNA_COLLECTION_ARTIFACT_VERSION
    || !record(value.manifest)
    || !exactKeys(value.manifest, ['suite', 'environment', 'expected_revision', 'expected_door_revisions', 'authorization_approval_id', 'target', 'case_inputs'])
    || (value.manifest.suite !== 'beyond_acarya' && value.manifest.suite !== 'product')
    || (value.manifest.environment !== 'candidate' && value.manifest.environment !== 'live')
    || typeof value.manifest.expected_revision !== 'string' || value.manifest.expected_revision.length === 0
    || !validDoorExpectedRevisions(value.manifest.expected_door_revisions)
    || typeof value.manifest.authorization_approval_id !== 'string' || value.manifest.authorization_approval_id.length === 0
    || !validTarget(value.manifest.target)
    || !Array.isArray(value.manifest.case_inputs) || !value.manifest.case_inputs.every(validCaseInput)
    || !Array.isArray(value.rows) || !value.rows.every(validCollectedCase)
    || typeof value.manifest_hash !== 'string' || !SHA256_FINGERPRINT.test(value.manifest_hash)
    || typeof value.collection_hash !== 'string' || !SHA256_FINGERPRINT.test(value.collection_hash)) {
    throw new Error('PURNA_COLLECTION_ARTIFACT_INVALID')
  }
  const artifact = value as unknown as CollectionArtifact
  const caseIds = artifact.manifest.case_inputs.map((input) => input.case_id)
  const expectedRows = new Set(caseIds.flatMap((caseId) => [
    `${caseId}\u0000portal`, `${caseId}\u0000managed_mcp`, `${caseId}\u0000raw_mcp`,
  ]))
  const actualRows = artifact.rows.map((row) => `${row.caseId}\u0000${row.door}`)
  const projection = {
    schema_version: PURNA_COLLECTION_ARTIFACT_VERSION,
    manifest: manifestProjection(artifact.manifest),
    manifest_hash: artifact.manifest_hash,
    rows: artifact.rows,
  }
  if (caseIds.length === 0 || new Set(caseIds).size !== caseIds.length
    || actualRows.length !== expectedRows.size || new Set(actualRows).size !== actualRows.length
    || actualRows.some((key) => !expectedRows.has(key))
    || artifact.rows.some((row) => row.expectedRevision !== artifact.manifest.expected_door_revisions[row.door]
      || row.source !== artifact.manifest.environment
      || row.observedChartId !== artifact.manifest.target.chart_id)
    || artifact.manifest_hash !== stableFingerprint(manifestProjection(artifact.manifest))
    || artifact.collection_hash !== stableFingerprint(projection)) {
    throw new Error('PURNA_COLLECTION_ARTIFACT_INVALID')
  }
  return artifact
}

export function isLiveEvidence(row: CollectedCase, expectedChartId?: string): boolean {
  return row.source !== 'fixture'
    && row.networkCallCount > 0
    // A genuinely served, revision-bound honest insufficiency remains live
    // evidence. The acceptance protocol, not collection transport, decides
    // whether its bounded outcome satisfies the particular case.
    && row.terminal !== 'transport_error'
    && row.observedRevision === row.expectedRevision
    && (expectedChartId === undefined || row.observedChartId === expectedChartId)
    && row.receiptRefs.length > 0
}

export function assertLiveEvidence(row: CollectedCase, expectedChartId?: string): void {
  if (!isLiveEvidence(row, expectedChartId)) throw new Error('PURNA_COLLECTION_NOT_LIVE_EVIDENCE')
}
