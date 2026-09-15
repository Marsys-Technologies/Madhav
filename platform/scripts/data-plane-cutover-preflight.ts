/** Fail-closed release evidence gate for the one-shot DP-SD-018 cutover. */
import { execFileSync } from 'node:child_process'
import { Pool } from 'pg'
import { readDataPlaneOwnershipStatus } from './data-plane-ownership-status'

function requireValue(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required by the protected data-plane cutover environment.`)
  return value
}

export interface BackupRestoreReceipt {
  backupId: string
  restoreOperationId: string
  validationInstance: string
  sourceCommit: string
  leaseId: string
  approvedBy: string
  expiresAt: string
  repository: string
  workflowRunId: string
  environment: string
}

interface GitHubEnvironment {
  name?: string
  protection_rules?: Array<{
    type?: string
    prevent_self_review?: boolean
    reviewers?: unknown[]
  }>
  deployment_branch_policy?: { protected_branches?: boolean; custom_branch_policies?: boolean } | null
}
interface GitHubReview {
  state?: string
  environments?: Array<{ name?: string }>
  user?: { login?: string }
}
interface GitHubWorkflowRun { id?: number; head_sha?: string; repository?: { full_name?: string } }
interface CloudSqlInstanceIdentity { name?: string; connectionName?: string; state?: string }

export function parseBackupRestoreReceipt(value: string): BackupRestoreReceipt {
  let parsed: unknown
  try { parsed = JSON.parse(value) }
  catch { throw new Error('DATA_PLANE_BACKUP_RESTORE_ID must be an exact JSON receipt.') }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Backup/restore receipt must be an object.')
  const receipt = parsed as Record<string, unknown>
  const expectedKeys = [
    'approvedBy','backupId','environment','expiresAt','leaseId','repository',
    'restoreOperationId','sourceCommit','validationInstance','workflowRunId',
  ]
  if (Object.keys(receipt).sort().join(',') !== expectedKeys.join(',')
      || expectedKeys.some((key) => typeof receipt[key] !== 'string' || !(receipt[key] as string).trim())) {
    throw new Error('Backup/restore receipt fields are missing, empty, or unexpected.')
  }
  return receipt as unknown as BackupRestoreReceipt
}

export function assertBackupReceiptBinding(
  receipt: BackupRestoreReceipt,
  binding: {
    validationInstance: string; sourceCommit: string; leaseId: string; approvedBy: string
    repository: string; workflowRunId: string; environment: string
  },
  now = new Date(),
): void {
  if (!/^[A-Za-z0-9_-]+$/.test(receipt.backupId) || !/^[A-Za-z0-9_-]+$/.test(receipt.restoreOperationId)
      || !/^[a-z][a-z0-9-]{4,97}[a-z0-9]$/.test(receipt.validationInstance)
      || !/^[0-9a-f]{40}$/.test(receipt.sourceCommit) || !/^[0-9a-f-]{36}$/i.test(receipt.leaseId)
      || receipt.validationInstance === 'amjis-postgres'
      || receipt.validationInstance !== binding.validationInstance || receipt.sourceCommit !== binding.sourceCommit
      || receipt.leaseId !== binding.leaseId || receipt.approvedBy !== binding.approvedBy
      || receipt.repository !== binding.repository || receipt.workflowRunId !== binding.workflowRunId
      || receipt.environment !== binding.environment || !/^\d+$/.test(receipt.workflowRunId)) {
    throw new Error('Backup/restore receipt is not bound to this commit, lease, deployment review, and isolated instance.')
  }
  const expiry = Date.parse(receipt.expiresAt)
  if (!Number.isFinite(expiry) || expiry <= now.getTime() || expiry > now.getTime() + 48 * 60 * 60 * 1000) {
    throw new Error('Backup/restore receipt is expired or has an unsafe expiry horizon.')
  }
}

export function assertGitHubDeploymentReviewEvidence(
  environment: GitHubEnvironment,
  reviews: GitHubReview[],
  workflowRun: GitHubWorkflowRun,
  binding: {
    environment: string; actor: string; approvedBy: string
    repository: string; workflowRunId: string; sourceCommit: string
  },
): void {
  if (String(workflowRun.id ?? '') !== binding.workflowRunId
      || workflowRun.head_sha !== binding.sourceCommit
      || workflowRun.repository?.full_name !== binding.repository) {
    throw new Error('Authenticated GitHub workflow run does not match the receipt repository, run, and source commit.')
  }
  if (environment.name !== binding.environment) {
    throw new Error('Authenticated GitHub environment response does not match the cutover environment.')
  }
  const reviewerRule = (environment.protection_rules ?? [])
    .filter((rule) => rule.type === 'required_reviewers')
  if (reviewerRule.length !== 1 || reviewerRule[0]?.prevent_self_review !== true
      || (reviewerRule[0]?.reviewers ?? []).length < 1) {
    throw new Error('Cutover environment lacks exact required-reviewer and no-self-review protection.')
  }
  const branch = environment.deployment_branch_policy
  if (!branch || branch.protected_branches !== true || branch.custom_branch_policies !== false) {
    throw new Error('Cutover environment must permit only protected branches.')
  }
  const approvals = reviews.filter((review) => review.state === 'approved'
    && (review.environments ?? []).some((candidate) => candidate.name === binding.environment)
    && review.user?.login === binding.approvedBy)
  if (binding.approvedBy === binding.actor || approvals.length !== 1) {
    throw new Error('Receipt approver is not the one authenticated independent GitHub deployment reviewer.')
  }
}

export function assertValidationConnectorBinding(
  databaseUrl: string,
  binding: {
    instance: CloudSqlInstanceIdentity; validationInstance: string
    connectionName: string; proxyPort: string; project: string
  },
): void {
  const url = new URL(databaseUrl)
  const parts = binding.connectionName.split(':')
  if (binding.instance.name !== binding.validationInstance || binding.instance.state !== 'RUNNABLE'
      || binding.instance.connectionName !== binding.connectionName || parts.length !== 3
      || parts[0] !== binding.project || parts[2] !== binding.validationInstance
      || !/^\d{2,5}$/.test(binding.proxyPort) || Number(binding.proxyPort) > 65535
      || !['postgres:','postgresql:'].includes(url.protocol)
      || !['127.0.0.1','localhost'].includes(url.hostname) || url.port !== binding.proxyPort) {
    throw new Error('Validation database URL is not bound to the authenticated isolated Cloud SQL proxy identity.')
  }
}

function githubApi<T>(path: string): T {
  requireValue('GH_TOKEN')
  return JSON.parse(execFileSync('gh', ['api', path], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
  })) as T
}

export async function withDataPlaneCutoverLease<T>(action: () => Promise<T>): Promise<T> {
  const receipt = parseBackupRestoreReceipt(requireValue('DATA_PLANE_BACKUP_RESTORE_ID'))
  const lease = requireValue('DATA_PLANE_CUTOVER_LEASE')
  const actor = requireValue('GITHUB_ACTOR')
  const repository = requireValue('GITHUB_REPOSITORY')
  const workflowRunId = requireValue('GITHUB_RUN_ID')
  const environmentName = requireValue('DATA_PLANE_CUTOVER_ENVIRONMENT')
  const sourceCommit = requireValue('DEPLOY_SHA')
  const encodedEnvironment = encodeURIComponent(environmentName)
  const environment = githubApi<GitHubEnvironment>(`repos/${repository}/environments/${encodedEnvironment}`)
  const reviews = githubApi<GitHubReview[]>(`repos/${repository}/actions/runs/${workflowRunId}/approvals`)
  const workflowRun = githubApi<GitHubWorkflowRun>(`repos/${repository}/actions/runs/${workflowRunId}`)
  assertGitHubDeploymentReviewEvidence(environment, reviews, workflowRun, {
    environment: environmentName, actor, approvedBy: receipt.approvedBy,
    repository,workflowRunId,sourceCommit,
  })
  const approver = receipt.approvedBy
  const validationInstance = requireValue('DATA_PLANE_RESTORE_VALIDATION_INSTANCE')
  const validationDatabaseUrl = requireValue('DATA_PLANE_RESTORE_VALIDATION_DATABASE_URL')
  const validationConnectionName = requireValue('DATA_PLANE_RESTORE_VALIDATION_CONNECTION_NAME')
  const validationProxyPort = requireValue('DATA_PLANE_RESTORE_VALIDATION_PROXY_PORT')
  if (!/^[0-9a-f-]{36}$/i.test(lease)) throw new Error('DATA_PLANE_CUTOVER_LEASE must be an exact UUID lease receipt.')
  assertBackupReceiptBinding(receipt, {
    validationInstance,sourceCommit,leaseId: lease,approvedBy: approver,
    repository,workflowRunId,environment: environmentName,
  })
  const project = process.env.GCP_PROJECT ?? 'madhav-astrology'
  const backup = JSON.parse(execFileSync('gcloud', [
    'sql', 'backups', 'describe', receipt.backupId, '--instance', 'amjis-postgres',
    '--project', project, '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as { status?: string; id?: string | number; endTime?: string }
  const backupCompleted = Date.parse(backup.endTime ?? '')
  if (backup.status !== 'SUCCESSFUL' || String(backup.id) !== receipt.backupId
      || !Number.isFinite(backupCompleted) || backupCompleted > Date.now()
      || Date.now() - backupCompleted > 24 * 60 * 60 * 1000) {
    throw new Error('Named Cloud SQL backup evidence is absent, unsuccessful, or stale.')
  }
  const restore = JSON.parse(execFileSync('gcloud', [
    'sql', 'operations', 'describe', receipt.restoreOperationId,
    '--project', project, '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as {
    name?: string; status?: string; operationType?: string; targetId?: string; endTime?: string
    backupContext?: { backupId?: string | number }
  }
  const restoreCompleted = Date.parse(restore.endTime ?? '')
  if (restore.name !== receipt.restoreOperationId || restore.status !== 'DONE'
      || restore.targetId !== validationInstance || restore.targetId === 'amjis-postgres'
      || !/^RESTORE(?:_|$)/.test(restore.operationType ?? '')
      || String(restore.backupContext?.backupId ?? '') !== receipt.backupId
      || !Number.isFinite(restoreCompleted) || restoreCompleted < backupCompleted
      || restoreCompleted > Date.parse(receipt.expiresAt)) {
    throw new Error('Named restore does not prove the pinned backup on the isolated validation instance.')
  }
  const instance = JSON.parse(execFileSync('gcloud', [
    'sql', 'instances', 'describe', validationInstance, '--project', project, '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as CloudSqlInstanceIdentity
  assertValidationConnectorBinding(validationDatabaseUrl, {
    instance, validationInstance, connectionName: validationConnectionName,
    proxyPort: validationProxyPort, project,
  })
  if (await readDataPlaneOwnershipStatus(validationDatabaseUrl) !== 'unmarked') {
    throw new Error('Isolated restore does not attest the expected pre-cutover protected state.')
  }
  const validationPool = new Pool({ connectionString: validationDatabaseUrl, max: 1 })
  try {
    const validation = await validationPool.query<{ version: number; build_runs: string | null }>(`
      SELECT current_setting('server_version_num')::int version,
             to_regclass('public.build_runs')::text build_runs
    `)
    if ((validation.rows[0]?.version ?? 0) < 150000 || (validation.rows[0]?.version ?? 0) >= 160000
        || validation.rows[0]?.build_runs !== 'build_runs') {
      throw new Error('Isolated restore validation database has the wrong engine or schema identity.')
    }
  } finally {
    await validationPool.end()
  }
  const pool = new Pool({ connectionString: requireValue('PROD_DATABASE_URL'), max: 1 })
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    const lock = await client.query<{ locked: boolean }>(
      `SELECT pg_try_advisory_xact_lock(hashtextextended('DP-SD-018-PROTECTED-CUTOVER',0)) AS locked`,
    )
    if (!lock.rows[0]?.locked) throw new Error('Exclusive DP-SD-018 cutover lease is already held.')
    await client.query(`LOCK TABLE public.build_runs, public.build_run_assets
      IN SHARE ROW EXCLUSIVE MODE NOWAIT`)
    const active = await client.query<{ count: string }>(`
      SELECT count(*)::text AS count FROM public.build_runs
      WHERE state IN ('running','queued','dispatching')
    `)
    if (active.rows[0]?.count !== '0') throw new Error('Data-plane cutover requires build-run quiescence.')
    return await action()
  } finally {
    await client.query('ROLLBACK').catch(() => undefined)
    client.release()
    await pool.end()
  }
}

export async function assertDataPlaneCutoverPreflight(): Promise<void> {
  await withDataPlaneCutoverLease(async () => undefined)
}

if (require.main === module) assertDataPlaneCutoverPreflight().catch((error) => {
  console.error(error); process.exitCode = 1
})
