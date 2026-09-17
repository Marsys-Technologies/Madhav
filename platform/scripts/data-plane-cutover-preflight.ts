/** Fail-closed release evidence gate for the one-shot DP-SD-018/DP-SD-020 cutover. */
import { execFileSync } from 'node:child_process'
import { Pool, type PoolConfig } from 'pg'
import { parse as parsePgConnectionString } from 'pg-connection-string'
import { readDataPlaneOwnershipStatus } from './data-plane-ownership-status'

function requireValue(name: string): string {
  const value = process.env[name]?.trim()
  if (!value) throw new Error(`${name} is required by the protected data-plane cutover environment.`)
  return value
}

export interface BackupRestoreReceipt {
  authorityDecision: string
  backupId: string
  executionMode: string
  restoreOperationId: string
  validationInstance: string
  sourceCommit: string
  leaseId: string
  expiresAt: string
  repository: string
  workflowRunId: string
  environment: string
}

/**
 * Short-lived Native authorization stored before an automatic deploy exists.
 * The workflow's authenticated runtime identity supplies the only two values
 * that cannot be known until that deploy has been created.
 */
export interface BackupRestoreAuthorization {
  authorityDecision: string
  backupId: string
  executionMode: string
  restoreOperationId: string
  validationInstance: string
  leaseId: string
  expiresAt: string
  repository: string
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
interface GitHubWorkflowRun { id?: number; head_sha?: string; repository?: { full_name?: string } }
interface CloudSqlInstanceIdentity { name?: string; connectionName?: string; state?: string }
interface CloudSqlRestoreAuditEntry {
  operation?: { id?: string; first?: boolean; last?: boolean; producer?: string }
  protoPayload?: {
    serviceName?: string; methodName?: string; resourceName?: string
    authorizationInfo?: Array<{ granted?: boolean; permission?: string; resource?: string }>
    request?: {
      project?: string; instance?: string
      body?: { restoreBackupContext?: { backupRunId?: string; instanceId?: string } }
    }
    response?: { name?: string; operationType?: string; targetId?: string }
    status?: { message?: string }
  }
}

export const DATA_PLANE_CUTOVER_AUTHORITY = 'DP-SD-020'
export const DATA_PLANE_CUTOVER_EXECUTION_MODE = 'native_authorized_automated_cutover'

export function parseBackupRestoreReceipt(value: string): BackupRestoreReceipt {
  let parsed: unknown
  try { parsed = JSON.parse(value) }
  catch { throw new Error('DATA_PLANE_BACKUP_RESTORE_ID must be an exact JSON receipt.') }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Backup/restore receipt must be an object.')
  const receipt = parsed as Record<string, unknown>
  const expectedKeys = [
    'authorityDecision','backupId','environment','executionMode','expiresAt','leaseId','repository',
    'restoreOperationId','sourceCommit','validationInstance','workflowRunId',
  ]
  if (Object.keys(receipt).sort().join(',') !== expectedKeys.join(',')
      || expectedKeys.some((key) => typeof receipt[key] !== 'string' || !(receipt[key] as string).trim())) {
    throw new Error('Backup/restore receipt fields are missing, empty, or unexpected.')
  }
  return receipt as unknown as BackupRestoreReceipt
}

export function parseBackupRestoreAuthorization(value: string): BackupRestoreAuthorization {
  let parsed: unknown
  try { parsed = JSON.parse(value) }
  catch { throw new Error('DATA_PLANE_CUTOVER_AUTHORIZATION must be an exact JSON authorization.') }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Backup/restore authorization must be an object.')
  const authorization = parsed as Record<string, unknown>
  const expectedKeys = [
    'authorityDecision','backupId','environment','executionMode','expiresAt','leaseId','repository',
    'restoreOperationId','validationInstance',
  ]
  if (Object.keys(authorization).sort().join(',') !== expectedKeys.join(',')
      || expectedKeys.some((key) => typeof authorization[key] !== 'string' || !(authorization[key] as string).trim())) {
    throw new Error('Backup/restore authorization fields are missing, empty, or unexpected.')
  }
  return authorization as unknown as BackupRestoreAuthorization
}

export function materializeRunBoundBackupRestoreReceipt(
  authorization: BackupRestoreAuthorization,
  binding: { sourceCommit: string; workflowRunId: string },
): BackupRestoreReceipt {
  return { ...authorization, ...binding }
}

export function assertBackupReceiptBinding(
  receipt: BackupRestoreReceipt,
  binding: {
    validationInstance: string; sourceCommit: string; leaseId: string
    authorityDecision: string; executionMode: string
    repository: string; workflowRunId: string; environment: string
  },
  now = new Date(),
): void {
  if (!/^[A-Za-z0-9_-]+$/.test(receipt.backupId) || !/^[A-Za-z0-9_-]+$/.test(receipt.restoreOperationId)
      || !/^[a-z][a-z0-9-]{4,97}[a-z0-9]$/.test(receipt.validationInstance)
      || !/^[0-9a-f]{40}$/.test(receipt.sourceCommit) || !/^[0-9a-f-]{36}$/i.test(receipt.leaseId)
      || receipt.validationInstance === 'amjis-postgres'
      || receipt.validationInstance !== binding.validationInstance || receipt.sourceCommit !== binding.sourceCommit
      || receipt.leaseId !== binding.leaseId || receipt.authorityDecision !== binding.authorityDecision
      || receipt.executionMode !== binding.executionMode
      || receipt.repository !== binding.repository || receipt.workflowRunId !== binding.workflowRunId
      || receipt.environment !== binding.environment || !/^\d+$/.test(receipt.workflowRunId)) {
    throw new Error('Backup/restore receipt is not bound to this commit, lease, DP-SD-020 authority, automated execution mode, and isolated instance.')
  }
  const expiry = Date.parse(receipt.expiresAt)
  if (!Number.isFinite(expiry) || expiry <= now.getTime() || expiry > now.getTime() + 48 * 60 * 60 * 1000) {
    throw new Error('Backup/restore receipt is expired or has an unsafe expiry horizon.')
  }
}

export function assertGitHubAutomatedCutoverEvidence(
  environment: GitHubEnvironment,
  workflowRun: GitHubWorkflowRun,
  binding: {
    environment: string; authorityDecision: string; executionMode: string
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
  if (reviewerRule.length !== 0) {
    throw new Error('DP-SD-020 automated cutover environment must not depend on a human required-reviewer rule.')
  }
  const branch = environment.deployment_branch_policy
  if (!branch || branch.protected_branches !== true || branch.custom_branch_policies !== false) {
    throw new Error('Cutover environment must permit only protected branches.')
  }
  if (binding.authorityDecision !== DATA_PLANE_CUTOVER_AUTHORITY
      || binding.executionMode !== DATA_PLANE_CUTOVER_EXECUTION_MODE) {
    throw new Error('Cutover receipt does not carry the exact Native-authorized DP-SD-020 automated execution binding.')
  }
}

export function assertValidationConnectorBinding(
  databaseUrl: string,
  binding: {
    instance: CloudSqlInstanceIdentity; validationInstance: string
    connectionName: string; proxyPort: string; project: string
  },
): Readonly<PoolConfig> {
  let parsed: ReturnType<typeof parsePgConnectionString>
  try {
    parsed = parsePgConnectionString(databaseUrl)
  } catch {
    throw new Error('Validation database URL is not a valid node-postgres connection string.')
  }
  const routingQueryNames = new Set([
    'address','connectionname','connectionstring','host','hostaddr','hostaddress','hostname',
    'path','port','server','servername','service','servicename','socket','socketpath',
    'unixsocket','unixsocketpath',
  ])
  // A verifier URL is a credential carrier, not a routing instruction.  A few
  // standard libpq spellings add a localhost authority or a port while retaining
  // the Unix-socket `host` parameter.  Those values are discarded below when we
  // construct the authenticated local-proxy PoolConfig; accepting them therefore
  // cannot redirect the connection.  Other routing aliases remain forbidden.
  const benignSocketCarrierMetadata = new Set(['sslmode', 'applicationname', 'port'])
  const parts = binding.connectionName.split(':')
  const expectedSocket = `/cloudsql/${binding.connectionName}`
  // The verifier secret predates the isolated restore and therefore names the
  // source Cloud SQL socket. It is a credential carrier only: this function
  // discards that route and always returns the authenticated local proxy route.
  const sourceSocket = `/cloudsql/${parts[0]}:${parts[1]}:amjis-postgres`
  let route: 'proxy' | 'socket-carrier'
  try {
    const url = new URL(databaseUrl)
    const routingOverride = [...url.searchParams.keys()].some((key) =>
      routingQueryNames.has(key.toLowerCase().replace(/[^a-z0-9]/g, '')))
    if (!['postgres:','postgresql:'].includes(url.protocol) || routingOverride
        || !['127.0.0.1','localhost'].includes(parsed.host ?? '')
        || parsed.port !== binding.proxyPort) {
      throw new Error('invalid direct proxy route')
    }
    route = 'proxy'
  } catch {
    const [prefix, query] = databaseUrl.split('?', 2)
    const queryParts = query?.split('&') ?? []
    let socketHost: string | undefined
    try {
      const emptyAuthorityCarrier = /^postgres(?:ql)?:\/\/[^/?#]+@\/[^?#]+$/i.test(prefix)
      const localAuthorityCarrier = /^postgres(?:ql)?:\/\/[^/?#]+@(?:localhost|127\.0\.0\.1)(?::\d+)?\/[^?#]+$/i.test(prefix)
      if (!emptyAuthorityCarrier && !localAuthorityCarrier) {
        throw new Error('invalid socket carrier')
      }
      const hostValues: string[] = []
      for (const part of queryParts) {
        const separator = part.indexOf('=')
        if (separator <= 0) throw new Error('invalid socket carrier')
        const key = decodeURIComponent(part.slice(0, separator))
        const value = decodeURIComponent(part.slice(separator + 1))
        const normalizedKey = key.toLowerCase().replace(/[^a-z0-9]/g, '')
        if (key === 'host') {
          hostValues.push(value)
        } else if (!benignSocketCarrierMetadata.has(normalizedKey)) {
          throw new Error('invalid socket carrier')
        }
      }
      if (hostValues.length !== 1) throw new Error('invalid socket carrier')
      // Only explicitly benign metadata is accepted; it is deliberately ignored
      // because the returned PoolConfig always uses the authenticated local proxy.
      socketHost = hostValues[0]
    } catch {
      throw new Error('Validation database URL is not bound to the authenticated isolated Cloud SQL proxy identity.')
    }
    if (![expectedSocket, sourceSocket].includes(socketHost ?? '')
        || parsed.host !== socketHost) {
      throw new Error('Validation database URL is not bound to the authenticated isolated Cloud SQL proxy identity.')
    }
    route = 'socket-carrier'
  }
  if (binding.instance.name !== binding.validationInstance || binding.instance.state !== 'RUNNABLE'
      || binding.instance.connectionName !== binding.connectionName || parts.length !== 3
      || parts[0] !== binding.project || parts[2] !== binding.validationInstance
      || !/^\d{2,5}$/.test(binding.proxyPort) || Number(binding.proxyPort) > 65535
      || !route) {
    throw new Error('Validation database URL is not bound to the authenticated isolated Cloud SQL proxy identity.')
  }
  return Object.freeze({
    host: '127.0.0.1',
    port: Number(binding.proxyPort),
    user: parsed.user,
    password: parsed.password,
    database: parsed.database ?? undefined,
    max: 1,
  })
}

/**
 * Routes the protected admin credential only to the already-authenticated
 * isolated validation proxy. Its original route is intentionally discarded.
 */
export function validationAdminProxyConfig(
  databaseUrl: string,
  binding: { proxyPort: string },
): Readonly<PoolConfig> {
  const diagnostic = inspectDataPlaneAdminCredential(databaseUrl, binding)
  if (!diagnostic.parseable) throw new Error('Data-plane admin credential is not a valid connection string.')
  if (!diagnostic.safeToRoute) {
    throw new Error(`Data-plane admin credential cannot be safely routed to the isolated validation proxy; missing or invalid components: ${diagnostic.invalidComponents.join(',')}.`)
  }
  const parsed = parsePgConnectionString(databaseUrl)
  return Object.freeze({
    host: '127.0.0.1', port: Number(binding.proxyPort), user: parsed.user,
    password: parsed.password, database: parsed.database, max: 1,
  })
}

/** Non-secret component diagnostic for the isolated administrator connector. */
export function inspectDataPlaneAdminCredential(
  databaseUrl: string,
  binding: { proxyPort: string },
): Readonly<{ parseable: boolean; safeToRoute: boolean; invalidComponents: readonly string[] }> {
  let parsed: ReturnType<typeof parsePgConnectionString>
  try {
    parsed = parsePgConnectionString(databaseUrl)
  } catch {
    return Object.freeze({ parseable: false, safeToRoute: false, invalidComponents: Object.freeze(['connection_string']) })
  }
  const invalidComponents = [
    !parsed.user && 'user',
    !parsed.password && 'password',
    !parsed.database && 'database',
    (!/^\d{2,5}$/.test(binding.proxyPort) || Number(binding.proxyPort) > 65535) && 'proxy_port',
  ].filter((component): component is string => Boolean(component))
  return Object.freeze({
    parseable: true,
    safeToRoute: invalidComponents.length === 0,
    invalidComponents: Object.freeze(invalidComponents),
  })
}

async function grantValidationVerifierBootstrapReadAccess(
  adminDatabaseUrl: string,
  binding: { proxyPort: string },
): Promise<void> {
  const pool = new Pool(validationAdminProxyConfig(adminDatabaseUrl, binding))
  try {
    // This is intentionally limited to the restored validation copy. The same
    // terminal ACLs are installed atomically on production by the subsequent
    // locked ownership preflight; the grant merely lets the verifier attest the
    // unmarked restored state before that transition.
    await pool.query('GRANT USAGE ON SCHEMA public TO data_plane_verifier')
    await pool.query('GRANT SELECT ON TABLE public._migrations_applied TO data_plane_verifier')
  } finally {
    await pool.end()
  }
}

export function assertRestoreAuditBinding(
  entries: CloudSqlRestoreAuditEntry[],
  binding: {
    project: string; operationId: string; backupId: string
    sourceInstance: string; validationInstance: string
  },
): void {
  const resourceName = `projects/${binding.project}/instances/${binding.validationInstance}`
  const request = entries.find((entry) => entry.operation?.id === binding.operationId
    && entry.operation.first === true
    && entry.operation.producer === 'cloudsql.googleapis.com')
  const completion = entries.find((entry) => entry.operation?.id === binding.operationId
    && entry.operation.last === true
    && entry.operation.producer === 'cloudsql.googleapis.com')
  const requestPayload = request?.protoPayload
  const restoreContext = requestPayload?.request?.body?.restoreBackupContext
  const authorized = requestPayload?.authorizationInfo?.some((authorization) =>
    authorization.granted === true
      && authorization.permission === 'cloudsql.instances.restoreBackup'
      && authorization.resource === resourceName)
  if (requestPayload?.serviceName !== 'cloudsql.googleapis.com'
      || requestPayload.methodName !== 'cloudsql.instances.restoreBackup'
      || requestPayload.resourceName !== resourceName
      || requestPayload.request?.project !== binding.project
      || requestPayload.request.instance !== binding.validationInstance
      || restoreContext?.backupRunId !== binding.backupId
      || restoreContext.instanceId !== binding.sourceInstance
      || requestPayload.response?.name !== binding.operationId
      || requestPayload.response.operationType !== 'RESTORE_VOLUME'
      || requestPayload.response.targetId !== binding.validationInstance
      || requestPayload.status?.message !== 'OK'
      || !authorized
      || completion?.protoPayload?.serviceName !== 'cloudsql.googleapis.com'
      || completion.protoPayload.methodName !== 'cloudsql.instances.restoreBackup'
      || completion.protoPayload.resourceName !== resourceName
      || completion.protoPayload.status?.message !== 'OK') {
    throw new Error('Cloud Audit evidence does not bind the exact backup restore request and successful completion.')
  }
}

function githubApi<T>(path: string): T {
  requireValue('GH_TOKEN')
  return JSON.parse(execFileSync('gh', ['api', path], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
  })) as T
}

export async function withDataPlaneCutoverLease<T>(action: () => Promise<T>): Promise<T> {
  const authorization = parseBackupRestoreAuthorization(requireValue('DATA_PLANE_CUTOVER_AUTHORIZATION'))
  const lease = requireValue('DATA_PLANE_CUTOVER_LEASE')
  const repository = requireValue('GITHUB_REPOSITORY')
  const workflowRunId = requireValue('GITHUB_RUN_ID')
  const environmentName = requireValue('DATA_PLANE_CUTOVER_ENVIRONMENT')
  const sourceCommit = requireValue('DEPLOY_SHA')
  const receipt = materializeRunBoundBackupRestoreReceipt(authorization, { sourceCommit, workflowRunId })
  const encodedEnvironment = encodeURIComponent(environmentName)
  const environment = githubApi<GitHubEnvironment>(`repos/${repository}/environments/${encodedEnvironment}`)
  const workflowRun = githubApi<GitHubWorkflowRun>(`repos/${repository}/actions/runs/${workflowRunId}`)
  assertGitHubAutomatedCutoverEvidence(environment, workflowRun, {
    environment: environmentName, authorityDecision: receipt.authorityDecision,
    executionMode: receipt.executionMode,
    repository,workflowRunId,sourceCommit,
  })
  const validationInstance = requireValue('DATA_PLANE_RESTORE_VALIDATION_INSTANCE')
  const validationDatabaseUrl = requireValue('DATA_PLANE_RESTORE_VALIDATION_DATABASE_URL')
  const validationConnectionName = requireValue('DATA_PLANE_RESTORE_VALIDATION_CONNECTION_NAME')
  const validationProxyPort = requireValue('DATA_PLANE_RESTORE_VALIDATION_PROXY_PORT')
  if (!/^[0-9a-f-]{36}$/i.test(lease)) throw new Error('DATA_PLANE_CUTOVER_LEASE must be an exact UUID lease receipt.')
  assertBackupReceiptBinding(receipt, {
    validationInstance,sourceCommit,leaseId: lease,
    authorityDecision: DATA_PLANE_CUTOVER_AUTHORITY,
    executionMode: DATA_PLANE_CUTOVER_EXECUTION_MODE,
    repository,workflowRunId,environment: environmentName,
  })
  const project = process.env.GOOGLE_CLOUD_PROJECT ?? 'madhav-astrology'
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
  }
  const restoreCompleted = Date.parse(restore.endTime ?? '')
  if (restore.name !== receipt.restoreOperationId || restore.status !== 'DONE'
      || restore.targetId !== validationInstance || restore.targetId === 'amjis-postgres'
      || !/^RESTORE(?:_|$)/.test(restore.operationType ?? '')
      || !Number.isFinite(restoreCompleted) || restoreCompleted < backupCompleted
      || restoreCompleted > Date.parse(receipt.expiresAt)) {
    throw new Error('Named restore does not prove the pinned backup on the isolated validation instance.')
  }
  const restoreAudit = JSON.parse(execFileSync('gcloud', [
    'logging', 'read',
    `operation.id="${receipt.restoreOperationId}" AND logName="projects/${project}/logs/cloudaudit.googleapis.com%2Factivity"`,
    '--project', project, '--limit=10', '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as CloudSqlRestoreAuditEntry[]
  assertRestoreAuditBinding(restoreAudit, {
    project, operationId: receipt.restoreOperationId, backupId: receipt.backupId,
    sourceInstance: 'amjis-postgres', validationInstance,
  })
  const instance = JSON.parse(execFileSync('gcloud', [
    'sql', 'instances', 'describe', validationInstance, '--project', project, '--format=json',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })) as CloudSqlInstanceIdentity
  const validationPoolConfig = assertValidationConnectorBinding(validationDatabaseUrl, {
    instance, validationInstance, connectionName: validationConnectionName,
    proxyPort: validationProxyPort, project,
  })
  await grantValidationVerifierBootstrapReadAccess(
    requireValue('DATA_PLANE_ADMIN_DATABASE_URL'), { proxyPort: validationProxyPort },
  )
  if (await readDataPlaneOwnershipStatus(validationPoolConfig) !== 'unmarked') {
    throw new Error('Isolated restore does not attest the expected pre-cutover protected state.')
  }
  const validationPool = new Pool(validationPoolConfig)
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
