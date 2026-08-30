import 'server-only'
import { createHash } from 'node:crypto'
import { getNirmanaCampaignControlWriterPool } from './campaign-control-writer'
import { getNirmanaEvidenceVerifierWriterPool } from './verifier-writer'
import { loadNirmanaReleaseStatus } from './release'

export const NIRMANA_CONDUCTOR_AUDIENCE = 'https://amjis-web-938361928218.asia-south1.run.app'
export const NIRMANA_CONDUCTOR_PRINCIPAL = 'amjis-nirmana-conductor@madhav-astrology.iam.gserviceaccount.com'
export const NIRMANA_VERIFIER_PRINCIPAL = 'amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com'
export const NIRMANA_CONDUCTOR_SCOPE = 'T0,F0,L0'

const requiredReadinessChecks = [
  'policy_is_enabled_and_l0_only',
  'distinct_conductor_and_verifier_identities',
  'durable_lease_and_monotonic_fence',
  'append_only_idempotent_action_receipts',
  'stage_transition_writes',
  'foundation_receipts',
  'asset_analysis_and_verdict_receipts',
  'implementation_and_build_authorization',
  'rebuild_probe_producer_and_nonbuild_receipts',
  'independent_integrity_and_freeze_receipts',
  'protected_merge_deploy_and_migration_verification',
  'production_build_natural_observation_and_heartbeat_recovery',
] as const

type ReadinessCheckName = typeof requiredReadinessChecks[number]
export type NirmanaReadinessCheck = { name: ReadinessCheckName; passed: boolean; detail: string }

export type NirmanaConductorLease = { lease_id: string; fence: number; expires_at: string }

export type NirmanaReadinessResult = {
  verdict: 'pass' | 'fail'
  checks: NirmanaReadinessCheck[]
  expires_at: string
}

type NirmanaReadinessBinding = {
  policy_revision: string
  definition_revision: string
  definition_manifest_sha256: string
  main_sha: string
  deployed_sha: string
  cloud_run_revision: string
  migration_set_sha256: string
  source_observation_id: string
  lease_id: string
  fence: number
}

interface PolicyRow {
  status: 'enabled' | 'revoked'
  max_layer: string
  expires_at: string
  allowed_actions: string[]
}

interface StoredLease extends NirmanaConductorLease {
  principal_email: string
  released_at: string | null
  revoked_at: string | null
}

/**
 * A single campaign-wide advisory lock serializes stale-owner recovery.  The
 * monotonically increasing fence is returned to every later action and is not
 * inferred from wall-clock time; an expired owner therefore cannot resume.
 */
export async function acquireNirmanaConductorLease(principal: string): Promise<NirmanaConductorLease> {
  if (principal !== NIRMANA_CONDUCTOR_PRINCIPAL) throw new Error('Only the dedicated Nirmana conductor may acquire the campaign lease.')
  const pool = await getNirmanaCampaignControlWriterPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SELECT pg_advisory_xact_lock(hashtextextended('nirmana-elevation:conductor', 0))`)
    const policy = await client.query<PolicyRow>(
      `SELECT status, max_layer, expires_at, allowed_actions
         FROM nirmana_evidence.nirmana_elevation_conductor_policies
        WHERE campaign_id = 'nirmana-elevation' FOR SHARE`,
    )
    const configured = policy.rows[0]
    if (!configured || configured.status !== 'enabled' || configured.max_layer !== 'L0'
      || Date.parse(configured.expires_at) <= Date.now()) throw new Error('Nirmana conductor policy is unavailable, revoked, expired, or exceeds L0.')

    const previous = await client.query<StoredLease>(
      `SELECT lease_id::text, fence, expires_at, principal_email, released_at, revoked_at
         FROM nirmana_evidence.nirmana_elevation_conductor_leases
        WHERE campaign_id = 'nirmana-elevation'
        ORDER BY fence DESC LIMIT 1 FOR UPDATE`,
    )
    const last = previous.rows[0]
    const now = Date.now()
    if (last && !last.released_at && !last.revoked_at && Date.parse(last.expires_at) > now) {
      if (last.principal_email !== principal) throw new Error('A distinct live Nirmana conductor lease holds the fence.')
      const renewed = await client.query<NirmanaConductorLease>(
        `UPDATE nirmana_evidence.nirmana_elevation_conductor_leases
            SET expires_at = clock_timestamp() + INTERVAL '15 minutes'
          WHERE lease_id = $1::uuid AND fence = $2
        RETURNING lease_id::text, fence, expires_at`,
        [last.lease_id, last.fence],
      )
      if (!renewed.rows[0]) throw new Error('Nirmana conductor lease renewal lost its fence.')
      await client.query('COMMIT')
      return renewed.rows[0]
    }
    if (last && !last.released_at && !last.revoked_at) {
      await client.query(
        `UPDATE nirmana_evidence.nirmana_elevation_conductor_leases
            SET released_at = clock_timestamp()
          WHERE lease_id = $1::uuid AND fence = $2 AND expires_at <= clock_timestamp()`,
        [last.lease_id, last.fence],
      )
    }
    const acquired = await client.query<NirmanaConductorLease>(
      `INSERT INTO nirmana_evidence.nirmana_elevation_conductor_leases
         (campaign_id, principal_email, fence, scope, expires_at)
       VALUES ('nirmana-elevation', $1, $2, $3, clock_timestamp() + INTERVAL '15 minutes')
       RETURNING lease_id::text, fence, expires_at`,
      [principal, (last?.fence ?? 0) + 1, NIRMANA_CONDUCTOR_SCOPE],
    )
    if (!acquired.rows[0]) throw new Error('Nirmana conductor lease acquisition did not return a fence.')
    await client.query('COMMIT')
    return acquired.rows[0]
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

/**
 * This is intentionally a verifier report, not an authority grant. The
 * controller consumes only a durable, unexpired PASS receipt from this report;
 * a missing or incomplete check remains a hard stop before F0 or L0 writes.
 */
export async function verifyNirmanaUnattendedReadiness(): Promise<NirmanaReadinessResult> {
  const pool = await getNirmanaEvidenceVerifierWriterPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN TRANSACTION READ ONLY')
    const policy = await client.query<PolicyRow>(
      `SELECT status, max_layer, expires_at, allowed_actions
         FROM nirmana_evidence.nirmana_elevation_conductor_policies
        WHERE campaign_id = 'nirmana-elevation'`,
    )
    const capability = await client.query<{ lease_table: string | null; receipt_table: string | null; readiness_table: string | null }>(
      `SELECT to_regclass('nirmana_evidence.nirmana_elevation_conductor_leases')::text AS lease_table,
              to_regclass('nirmana_evidence.nirmana_elevation_conductor_receipts')::text AS receipt_table,
              to_regclass('nirmana_evidence.nirmana_elevation_conductor_readiness_receipts')::text AS readiness_table`,
    )
    await client.query('COMMIT')
    const configured = policy.rows[0]
    const now = Date.now()
    const policyValid = configured?.status === 'enabled'
      && configured.max_layer === 'L0'
      && Date.parse(configured.expires_at) > now
    const durableControl = capability.rows[0]?.lease_table !== null
      && capability.rows[0]?.receipt_table !== null
      && capability.rows[0]?.readiness_table !== null
    const checks: NirmanaReadinessCheck[] = [
      { name: 'policy_is_enabled_and_l0_only', passed: policyValid, detail: policyValid ? 'enabled L0-only policy is current' : 'policy is absent, revoked, expired, or exceeds L0' },
      { name: 'distinct_conductor_and_verifier_identities', passed: true, detail: 'route accepts two fixed, distinct OIDC subjects' },
      { name: 'durable_lease_and_monotonic_fence', passed: durableControl, detail: durableControl ? 'lease schema is present' : 'lease schema is unavailable' },
      { name: 'append_only_idempotent_action_receipts', passed: durableControl, detail: durableControl ? 'receipt schema is present' : 'receipt schema is unavailable' },
      // The remaining actions must be exercised by their independently
      // authenticated production adapters. This initial verifier refuses to
      // convert a static code-path assertion into overnight authority.
      ...requiredReadinessChecks.slice(4).map((name): NirmanaReadinessCheck => ({
        name,
        passed: false,
        detail: 'production adapter has not yet produced an independent readiness proof',
      })),
    ]
    return {
      verdict: checks.every((check) => check.passed) ? 'pass' : 'fail',
      checks,
      expires_at: new Date(now + 30 * 60 * 1000).toISOString(),
    }
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    return {
      verdict: 'fail',
      checks: requiredReadinessChecks.map((name) => ({ name, passed: false, detail: 'control-plane readiness query failed closed' })),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    }
  } finally {
    client.release()
  }
}

export async function recordNirmanaUnattendedReadiness(
  verifierPrincipal: string,
  result: NirmanaReadinessResult,
): Promise<'recorded'> {
  if (verifierPrincipal !== NIRMANA_VERIFIER_PRINCIPAL) throw new Error('Only the fixed independent Nirmana verifier may record readiness.')
  const pool = await getNirmanaEvidenceVerifierWriterPool()
  const canonicalChecks = JSON.stringify(result.checks)
  const client = await pool.connect()
  try {
    const [policy, definition, observation, lease, migrations, release] = await Promise.all([
      client.query<{ policy_revision: string }>(`SELECT policy_revision FROM nirmana_evidence.nirmana_elevation_conductor_policies WHERE campaign_id = 'nirmana-elevation'`),
      client.query<{ definition_revision: string; manifest_sha256: string }>(`SELECT definition_revision, manifest_sha256 FROM nirmana_evidence.nirmana_elevation_campaign_definitions WHERE campaign_id = 'nirmana-elevation' AND definition_status = 'frozen' AND superseded_at IS NULL`),
      client.query<{ id: string }>(`SELECT id::text FROM public.nirmana_elevation_monitor_observations WHERE freshness_state = 'fresh' AND source_state = 'available' ORDER BY observed_at DESC LIMIT 1`),
      client.query<{ lease_id: string; fence: number }>(`SELECT lease_id::text, fence FROM nirmana_evidence.nirmana_elevation_conductor_leases WHERE campaign_id = 'nirmana-elevation' AND released_at IS NULL AND revoked_at IS NULL AND expires_at >= transaction_timestamp() ORDER BY fence DESC LIMIT 1`),
      client.query<{ filename: string; sha256: string }>(`SELECT filename, sha256 FROM public._migrations_applied ORDER BY filename`),
      loadNirmanaReleaseStatus(),
    ])
    const binding: NirmanaReadinessBinding = {
      policy_revision: policy.rows[0]?.policy_revision ?? '',
      definition_revision: definition.rows[0]?.definition_revision ?? '',
      definition_manifest_sha256: definition.rows[0]?.manifest_sha256 ?? '',
      main_sha: release.release.main_sha ?? '', deployed_sha: release.release.deployed_sha ?? '',
      cloud_run_revision: release.release.deployed_revision ?? '',
      migration_set_sha256: createHash('sha256').update(JSON.stringify(migrations.rows)).digest('hex'),
      source_observation_id: observation.rows[0]?.id ?? '', lease_id: lease.rows[0]?.lease_id ?? '', fence: lease.rows[0]?.fence ?? 0,
    }
    if (!binding.policy_revision || !binding.definition_revision || !binding.definition_manifest_sha256 || !binding.main_sha || !binding.deployed_sha
      || !binding.cloud_run_revision || !binding.source_observation_id || !binding.lease_id || binding.fence <= 0) {
      throw new Error('Readiness provenance is incomplete; no readiness receipt may be written.')
    }
    await client.query(
      `INSERT INTO nirmana_evidence.nirmana_elevation_conductor_readiness_receipts
         (campaign_id, verifier_principal_email, policy_revision, definition_revision, definition_manifest_sha256,
          main_sha, deployed_sha, cloud_run_revision, migration_set_sha256, source_observation_id, lease_id, fence, verdict, checks, expires_at)
       VALUES ('nirmana-elevation', $1, $2, $3, $4, $5, $6, $7, $8, $9::uuid, $10::uuid, $11, $12, $13::jsonb, $14::timestamptz)`,
      [verifierPrincipal, binding.policy_revision, binding.definition_revision, binding.definition_manifest_sha256,
        binding.main_sha, binding.deployed_sha, binding.cloud_run_revision, binding.migration_set_sha256,
        binding.source_observation_id, binding.lease_id, binding.fence, result.verdict, canonicalChecks, result.expires_at],
    )
    return 'recorded'
  } finally {
    client.release()
  }
}

export async function evaluateNirmanaConductor(principal: string): Promise<{
  state: 'readiness_required' | 'no_action'
  lease: NirmanaConductorLease
  readiness_receipt_id?: string
}> {
  if (principal !== NIRMANA_CONDUCTOR_PRINCIPAL) throw new Error('Only the fixed Nirmana conductor may evaluate campaign actions.')
  const lease = await acquireNirmanaConductorLease(principal)
  const pool = await getNirmanaCampaignControlWriterPool()
  const client = await pool.connect()
  try {
    const readiness = await client.query<{ readiness_receipt_id: string }>(
      `SELECT receipt.readiness_receipt_id::text
         FROM nirmana_evidence.nirmana_elevation_conductor_readiness_receipts AS receipt
         JOIN nirmana_evidence.nirmana_elevation_conductor_policies AS policy
           ON policy.campaign_id = receipt.campaign_id
          AND policy.policy_revision = receipt.policy_revision
          AND policy.status = 'enabled'
          AND policy.max_layer = 'L0'
          AND policy.expires_at >= transaction_timestamp()
         JOIN nirmana_evidence.nirmana_elevation_campaign_definitions AS definition
           ON definition.campaign_id = receipt.campaign_id
          AND definition.definition_revision = receipt.definition_revision
          AND definition.manifest_sha256 = receipt.definition_manifest_sha256
          AND definition.definition_status = 'frozen'
          AND definition.superseded_at IS NULL
         JOIN nirmana_evidence.nirmana_elevation_conductor_leases AS readiness_lease
           ON readiness_lease.lease_id = receipt.lease_id
          AND readiness_lease.fence = receipt.fence
          AND readiness_lease.released_at IS NULL
          AND readiness_lease.revoked_at IS NULL
          AND readiness_lease.expires_at >= transaction_timestamp()
         JOIN public.nirmana_elevation_monitor_observations AS observation
           ON observation.id = receipt.source_observation_id
          AND observation.current_definition_sha256 = receipt.definition_manifest_sha256
          AND observation.source_state = 'available'
          AND observation.freshness_state = 'fresh'
          AND observation.freshness_deadline_at >= transaction_timestamp()
          AND observation.release_state = 'in_sync'
          AND observation.runtime_liveness = 'quiet'
        WHERE receipt.campaign_id = 'nirmana-elevation'
          AND receipt.verdict = 'pass'
          AND receipt.expires_at >= transaction_timestamp()
        ORDER BY checked_at DESC
        LIMIT 1`,
    )
    if (!readiness.rows[0]) return { state: 'readiness_required', lease }

    // No asset or F0 action is inferred from a mere green readiness receipt.
    // The future dispatcher must first bind a fresh tracker observation, a
    // current lease/fence, and an exact allowlisted action into an append-only
    // receipt. Returning no_action is safer than manufacturing progress.
    return { state: 'no_action', lease, readiness_receipt_id: readiness.rows[0].readiness_receipt_id }
  } finally {
    client.release()
  }
}

export function canonicalNirmanaConductorRequestDigest(input: unknown): string {
  return createHash('sha256').update(JSON.stringify(input)).digest('hex')
}
