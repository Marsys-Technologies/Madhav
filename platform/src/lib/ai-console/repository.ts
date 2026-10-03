import 'server-only'
import { isDeepStrictEqual, inspect, types as utilTypes } from 'node:util'
import type { PoolClient } from 'pg'
import { z } from 'zod'
import { query, withTransaction } from '@/lib/db/client'
import type { EncryptedCredential } from './crypto'
import { writeAiAudit } from './audit'
import { CLI_REGISTRY, validateCliModelId } from './cli/registry'
import { CLI_BUILTIN_MODEL_DB_ID } from './cli/types'
import { AiConsoleError, AiErrorCodeSchema, normalizeAiError } from './errors'
import { configurationKindMatchesRoles, type ConfigurationKind } from './configuration-kind'
import { cliEffortLevels, providerEffortLevels } from './effort'
import {
  AI_ROLES, CLI_IDS, AiChoiceRefSchema, AiRoleSchema, AiEffortSchema, CliIdSchema, ConversationAiSelectionSchema,
  ProviderIdSchema, RoleAssignmentsSchema, RoutingSnapshotSchema, SafeProviderConnectionSchema,
  type AiChoiceRef, type AiEffort, type AiRole, type RoleAssignments, type RoleTarget, type SafeProviderConnection,
} from './types'

type Client = Pick<PoolClient, 'query'>
type Row = Record<string, unknown>
const nameSchema = z.string().trim().min(1).max(120)
const uuidSchema = z.string().uuid()
const safeColumns = 'id,provider_id,name,anthropic_workspace_id,masked_suffix,validation_state,credential_validity'
const workspaceIdSchema = z.string().regex(/^wrkspc_[A-Za-z0-9]{20,64}$/).nullable()
const notFound = () => new AiConsoleError('AI_CHOICE_BROKEN')
const providerConnectionErrorSchema = z.enum([
  'AI_CONNECTION_INVALID', 'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE',
  'AI_PROVIDER_UNREACHABLE', 'AI_PERMISSION_DENIED', 'AI_BILLING_UNAVAILABLE',
  'AI_RATE_LIMITED', 'AI_EXECUTION_FAILED',
])
/**
 * One lock order for the entire owned graph: user advisory lock, then row locks.
 * Save/select/duplicate, validation, deletion, history and CLI authorization all
 * enter here before touching rows. Hash collisions only add serialization.
 * No external/model execution may wait inside this transaction.
 */
async function withUserTransaction<T>(userId: string, work: (client: PoolClient) => Promise<T>): Promise<T> {
  return withTransaction(async client => {
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('ai-console:user:' || $1::text, 0))", [userId])
    return work(client)
  })
}
async function assertAssignments(client: Client, userId: string, assignments: RoleAssignments) {
  const distinct = new Map<string, { target: RoleTarget; roles: AiRole[] }>()
  for (const role of AI_ROLES) {
    const target = assignments[role]
    const key = JSON.stringify([target.kind, target.kind === 'provider_model' ? target.connectionId : target.cliId,
      target.modelId, target.effort ?? null])
    const group = distinct.get(key) ?? { target, roles: [] }
    group.roles.push(role)
    distinct.set(key, group)
  }
  for (const key of [...distinct.keys()].sort()) {
    const group = distinct.get(key)!
    await assertTarget(client, userId, group.target, group.roles)
  }
}
function required<T>(rows: T[]): T { if (!rows.length) throw notFound(); return rows[0] }
function safeConnection(row: Row): SafeProviderConnection {
  return SafeProviderConnectionSchema.parse({ id: row.id, providerId: row.provider_id,
    name: row.name, ...(row.anthropic_workspace_id ? { workspaceId: row.anthropic_workspace_id } : {}),
    maskedSuffix: row.masked_suffix, validationState: row.validation_state,
    confirmedValid: row.credential_validity === 'valid' })
}
function credentialParams(e: EncryptedCredential) {
  return [e.ciphertext, e.nonce, e.authTag, e.wrappedDataKey, e.wrapNonce, e.wrapAuthTag, e.keyVersion, e.mask, e.fingerprint]
}
function choiceParams(choice: AiChoiceRef | { kind: 'default' }) {
  return [choice.kind, choice.kind === 'provider_model' ? choice.connectionId : null,
    choice.kind === 'provider_model' || choice.kind === 'local_cli' ? choice.modelId : null,
    choice.kind === 'custom_configuration' ? choice.configurationId : null,
    choice.kind === 'local_cli' ? choice.cliId : null]
}
function rowChoice(row: Row): AiChoiceRef {
  return AiChoiceRefSchema.parse(row.kind === 'provider_model'
    ? { kind: row.kind, connectionId: row.connection_id, modelId: row.model_id }
    : row.kind === 'local_cli' ? { kind: row.kind, cliId: row.cli_id, modelId: row.model_id }
      : { kind: row.kind, configurationId: row.configuration_id })
}
function rowRole(row: Row): RoleTarget {
  const choice = rowChoice(row)
  if (choice.kind === 'custom_configuration') throw notFound()
  return RoleAssignmentsSchema.shape.synthesizer.parse({ ...choice,
    ...(row.effort == null ? {} : { effort: row.effort }) })
}
function assertChoiceUuid(choice: AiChoiceRef): void {
  const id = choice.kind === 'provider_model' ? choice.connectionId
    : choice.kind === 'custom_configuration' ? choice.configurationId : undefined
  if (id !== undefined && !uuidSchema.safeParse(id).success) throw notFound()
}
async function ownedConnection(client: Client, userId: string, id: string) {
  if (!uuidSchema.safeParse(id).success) throw notFound()
  return required((await client.query(`SELECT ${safeColumns},credential_version FROM ai_provider_connections
    WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL FOR NO KEY UPDATE`, [userId, id])).rows)
}
async function invalidateCatalog(client: Client, userId: string, id: string) {
  await client.query(`UPDATE ai_connection_models SET available=false
    WHERE connection_id=$2 AND EXISTS(SELECT 1 FROM ai_provider_connections WHERE user_id=$1 AND id=$2)`, [userId, id])
}
async function clearModelProbeEvidence(client: Client, userId: string, id: string) {
  await client.query(`UPDATE ai_connection_models SET plain_tested_at=NULL,tested_credential_version=NULL,
    last_probe_at=NULL,last_probe_error_code=NULL,last_probe_input_tokens=NULL,last_probe_output_tokens=NULL
    WHERE connection_id=$2 AND EXISTS (SELECT 1 FROM ai_provider_connections WHERE user_id=$1 AND id=$2)`,
  [userId, id])
}
async function ownedConversation(client: Client, userId: string, conversationId: string) {
  if (!uuidSchema.safeParse(conversationId).success) throw new AiConsoleError('AI_PERMISSION_DENIED')
  const rows = (await client.query('SELECT id FROM conversations WHERE user_id=$1 AND id=$2 FOR NO KEY UPDATE', [userId, conversationId])).rows
  if (!rows.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
}

/** Validate exact current choices; never repair or substitute a missing target. */
async function assertTarget(client: Client, userId: string, target: RoleTarget, roles: readonly AiRole[]) {
  if (target.kind === 'provider_model') {
    const connection = await ownedConnection(client, userId, target.connectionId)
    const hasAuthority = connection.validation_state === 'validated'
      || (connection.validation_state === 'validating' && connection.credential_validity === 'valid')
    if (!hasAuthority) throw new AiConsoleError('AI_CONNECTION_INVALID')
    const model = required((await client.query(`SELECT m.compatible_roles,m.available,m.user_selected,m.supported_efforts,
      m.plain_tested_at,m.tested_credential_version,c.credential_version FROM ai_connection_models m
      JOIN ai_provider_connections c ON c.id=m.connection_id
      WHERE c.user_id=$1 AND c.id=$2 AND m.model_id=$3 AND m.available=true`, [userId, target.connectionId, target.modelId])).rows)
    if (model.user_selected !== true || model.plain_tested_at == null
      || Number(model.tested_credential_version) !== Number(model.credential_version)) {
      throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    }
    assertProviderEffort(target, connection, model)
    if (!roles.every(role => model.compatible_roles.includes(role))) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
  } else {
    if (!CLI_REGISTRY[target.cliId].execution) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    const model = (await client.query(`SELECT m.compatible_roles,m.supported_efforts,m.is_catalog_discovered,m.is_manual FROM ai_cli_grants g
      JOIN ai_cli_installations i ON i.cli_id=g.cli_id JOIN ai_cli_models m ON m.cli_id=g.cli_id
      WHERE g.user_id=$1 AND g.cli_id=$2 AND g.revoked_at IS NULL AND i.validation_state='reachable'
      AND m.available=true AND (($3::text IS NULL AND m.is_builtin_default) OR m.model_id=$3)
      FOR SHARE OF g,i,m`, [userId, target.cliId, target.modelId])).rows[0]
    if (!model) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
    assertCliEffort(target, model)
    if (!roles.every(role => model.compatible_roles.includes(role))) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
  }
}

function assertProviderEffort(target: RoleTarget, connection: Row, model: Row) {
  if (target.kind !== 'provider_model' || !target.effort) return
  const efforts = Array.isArray(model.supported_efforts)
    ? z.array(AiEffortSchema).max(16).parse(model.supported_efforts)
    : providerEffortLevels(ProviderIdSchema.parse(connection.provider_id), target.modelId)
  if (!efforts.includes(target.effort)) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
}

function assertCliEffort(target: RoleTarget, model: Row) {
  if (target.kind !== 'local_cli' || !target.effort) return
  const advertised = model.is_catalog_discovered === true
    ? z.array(AiEffortSchema).max(16).parse(model.supported_efforts ?? [])
    : model.is_manual === true ? [] : undefined
  if (!cliEffortLevels(target.cliId, target.modelId, advertised).includes(target.effort)) {
    throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
  }
}
async function assertChoice(client: Client, userId: string, choice: AiChoiceRef) {
  if (choice.kind !== 'custom_configuration') return assertTarget(client, userId, choice, AI_ROLES)
  required((await client.query(`SELECT id FROM ai_custom_configurations WHERE user_id=$1 AND id=$2
    AND deleted_at IS NULL FOR NO KEY UPDATE`, [userId, choice.configurationId])).rows)
  const rows = (await client.query(`SELECT role,kind,connection_id,model_id,cli_id,effort FROM ai_custom_configuration_roles
    WHERE user_id=$1 AND configuration_id=$2 ORDER BY role`, [userId, choice.configurationId])).rows
  const assignments = RoleAssignmentsSchema.parse(Object.fromEntries(rows.map(row => [row.role, rowRole(row)])))
  await assertAssignments(client, userId, assignments)
}

/** Explicit SQL projections also retain tombstones so broken references are explainable. */
export async function listAiConsoleState(userId: string) {
  const connections = await query(`SELECT ${safeColumns},credential_version,last_validated_at,last_checked_at,last_error_code,deleted_at,
    catalog_refreshed_at,catalog_attempted_at,catalog_error_code
    FROM ai_provider_connections WHERE user_id=$1 ORDER BY created_at,id`, [userId])
  const models = await query(`SELECT m.connection_id,m.model_id,m.display_name,m.compatible_roles,m.supports_tools,m.supports_structured_output,m.available,
    m.user_selected,m.plain_tested_at,m.tested_credential_version,m.last_probe_at,m.last_probe_error_code,
    m.last_probe_input_tokens,m.last_probe_output_tokens,m.supported_efforts,
    c.credential_version AS current_credential_version FROM ai_connection_models m
    JOIN ai_provider_connections c ON c.id=m.connection_id WHERE c.user_id=$1 ORDER BY m.connection_id,m.model_id`, [userId])
  const configurations = await query(`SELECT id,name,version,configuration_kind,owner_connection_id,owner_cli_id,deleted_at
    FROM ai_custom_configurations WHERE user_id=$1 ORDER BY created_at,id`, [userId])
  const roles = await query(`SELECT configuration_id,role,kind,connection_id,model_id,cli_id,effort FROM ai_custom_configuration_roles WHERE user_id=$1 ORDER BY configuration_id,role`, [userId])
  const defaults = await query('SELECT kind,connection_id,model_id,configuration_id,cli_id FROM ai_user_defaults WHERE user_id=$1', [userId])
  const clis = await query(`SELECT cli.cli_id,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.detected_product END AS detected_product,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.detected_version END AS detected_version,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.validation_state END AS validation_state,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.last_checked_at END AS last_checked_at,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.catalog_refreshed_at END AS catalog_refreshed_at,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.catalog_attempted_at END AS catalog_attempted_at,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.catalog_error_code END AS catalog_error_code,
    g.granted_at,g.revoked_at FROM unnest($2::text[]) WITH ORDINALITY AS cli(cli_id,ord)
    LEFT JOIN ai_cli_installations i ON i.cli_id=cli.cli_id
    LEFT JOIN ai_cli_grants g ON g.cli_id=cli.cli_id AND g.user_id=$1 ORDER BY cli.ord`, [userId, CLI_IDS])
  const cliModels = await query(`SELECT m.cli_id,m.model_id,m.display_name,m.compatible_roles,m.supports_tools,m.supports_structured_output,m.available,m.is_builtin_default,
    m.supported_efforts,m.default_effort,m.is_catalog_discovered,m.is_manual
    FROM ai_cli_models m JOIN ai_cli_grants g ON g.cli_id=m.cli_id WHERE g.user_id=$1 AND g.revoked_at IS NULL ORDER BY m.cli_id,m.model_id`, [userId])
  return { connections: connections.rows, models: models.rows, configurations: configurations.rows,
    roles: roles.rows, defaultChoice: defaults.rows[0] ? rowChoice(defaults.rows[0]) : null,
    clis: clis.rows, cliModels: cliModels.rows }
}

export interface RoutingProviderTarget {
  kind: 'provider_model'
  connectionId: string
  providerId: z.infer<typeof ProviderIdSchema>
  credentialVersion: number
  modelId: string
  effort?: AiEffort | null
  displayName: string
  compatibleRoles: AiRole[]
  supportsTools: boolean
  supportsStructuredOutput: boolean
}
export interface RoutingCliTarget {
  kind: 'local_cli'
  cliId: z.infer<typeof CliIdSchema>
  modelId: string | null
  effort?: AiEffort | null
  displayName: string
  compatibleRoles: AiRole[]
  supportsTools: boolean
  supportsStructuredOutput: boolean
}
export type RoutingTarget = RoutingProviderTarget | RoutingCliTarget
export interface RoutingResolution {
  resolvedChoice: AiChoiceRef
  configurationVersion: number | null
  roles: Record<AiRole, RoutingTarget>
}

export interface PreparedTurnRouting {
  selection: z.infer<typeof ConversationAiSelectionSchema>
  resolution: RoutingResolution
  safeSnapshot: z.infer<typeof RoutingSnapshotSchema>
  snapshotId: string
  fallback?: {
    resolution: RoutingResolution
    safeSnapshot: z.infer<typeof RoutingSnapshotSchema>
    snapshotId: string
  }
}

export interface PreparedMcpRouting extends PreparedTurnRouting {
  role: 'super_admin' | 'guest'
}

function firstIncompatibleRole(compatibleRoles: readonly AiRole[], roles: readonly AiRole[]): AiRole | undefined {
  return roles.find(role => !compatibleRoles.includes(role))
}

/** Exact target read for one resolution. It never decrypts, spawns, repairs, or searches alternatives. */
async function loadRoutingTarget(client: Client, userId: string, target: RoleTarget, roles: readonly AiRole[]): Promise<RoutingTarget> {
  if (target.kind === 'provider_model') {
    if (!uuidSchema.safeParse(target.connectionId).success) throw notFound()
    const connection = (await client.query(`SELECT c.id,c.provider_id,c.credential_version,c.credential_validity,c.validation_state,
      c.last_error_code,c.model_retest_required
      FROM ai_provider_connections c WHERE c.user_id=$1 AND c.id=$2 AND c.deleted_at IS NULL FOR SHARE`,
    [userId, target.connectionId])).rows[0]
    if (!connection) throw new AiConsoleError('AI_CHOICE_BROKEN')
    if (connection.validation_state === 'invalid' || connection.credential_validity === 'invalid') {
      throw new AiConsoleError('AI_CONNECTION_INVALID')
    }
    if (connection.validation_state === 'needs_attention') {
      const error = providerConnectionErrorSchema.safeParse(connection.last_error_code)
      if (!error.success) throw notFound()
      throw new AiConsoleError(error.data)
    }
    if (connection.validation_state === 'unreachable') {
      const error = providerConnectionErrorSchema.safeParse(connection.last_error_code)
      if (!error.success) throw notFound()
      throw new AiConsoleError(error.data)
    }
    const confirmedUsable = connection.credential_validity === 'valid'
      && (connection.validation_state === 'validated' || connection.validation_state === 'validating')
    if (!confirmedUsable) throw notFound()
    const model = (await client.query(`SELECT m.model_id,m.display_name,m.compatible_roles,m.supports_tools,m.supports_structured_output,
      m.available,m.plain_tested_at,m.tested_credential_version,m.supported_efforts
      FROM ai_connection_models m WHERE m.connection_id=$1 AND m.model_id=$2 FOR SHARE`,
    [target.connectionId, target.modelId])).rows[0]
    if (!model || model.available !== true) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    assertProviderEffort(target, connection, model)
    // Pre-probe saved choices are grandfathered. Any key or workspace edit
    // explicitly turns on exact-version model proof for this connection.
    if (connection.model_retest_required === true && (model.plain_tested_at == null
      || Number(model.tested_credential_version) !== Number(connection.credential_version))) {
      throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    }
    const compatibleRoles = z.array(AiRoleSchema).min(1).parse(model.compatible_roles)
    const incompatible = firstIncompatibleRole(compatibleRoles, roles)
    if (incompatible) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE', incompatible)
    return {
      kind: 'provider_model', connectionId: target.connectionId,
      providerId: ProviderIdSchema.parse(connection.provider_id),
      credentialVersion: z.coerce.number().int().positive().parse(connection.credential_version),
      modelId: target.modelId, ...(target.effort ? { effort: target.effort } : {}),
      displayName: z.string().min(1).parse(model.display_name), compatibleRoles,
      supportsTools: z.boolean().parse(model.supports_tools),
      supportsStructuredOutput: z.boolean().parse(model.supports_structured_output),
    }
  }

  if (!CLI_REGISTRY[target.cliId].execution) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const grant = (await client.query(`SELECT g.cli_id,g.revoked_at FROM ai_cli_grants g
    WHERE g.user_id=$1 AND g.cli_id=$2 FOR SHARE`, [userId, target.cliId])).rows[0]
  if (!grant || grant.revoked_at !== null) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
  const installation = (await client.query(`SELECT i.cli_id,i.validation_state FROM ai_cli_installations i
    WHERE i.cli_id=$1 FOR SHARE`, [target.cliId])).rows[0]
  if (!installation || installation.validation_state === 'not_installed') throw new AiConsoleError('AI_CLI_NOT_INSTALLED')
  if (installation.validation_state === 'auth_unavailable') throw new AiConsoleError('AI_CLI_AUTH_UNAVAILABLE')
  if (installation.validation_state !== 'reachable') throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const model = (await client.query(`SELECT m.model_id,m.display_name,m.compatible_roles,m.supports_tools,m.supports_structured_output,m.available,m.is_builtin_default,
    m.supported_efforts,m.is_catalog_discovered,m.is_manual
    FROM ai_cli_models m WHERE m.cli_id=$1
      AND (($2::text IS NULL AND m.is_builtin_default=true) OR m.model_id=$2) FOR SHARE`,
  [target.cliId, target.modelId])).rows[0]
  if (!model || model.available !== true) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
  assertCliEffort(target, model)
  const compatibleRoles = z.array(AiRoleSchema).min(1).parse(model.compatible_roles)
  const incompatible = firstIncompatibleRole(compatibleRoles, roles)
  if (incompatible) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE', incompatible)
  return { kind: 'local_cli', cliId: target.cliId, modelId: target.modelId,
    ...(target.effort ? { effort: target.effort } : {}),
    displayName: z.string().min(1).parse(model.display_name), compatibleRoles,
    supportsTools: z.boolean().parse(model.supports_tools),
    supportsStructuredOutput: z.boolean().parse(model.supports_structured_output) }
}

/**
 * Resolve one live default/explicit choice under the same user lock used by all
 * AI Console mutations. The returned graph contains only safe identity and
 * capability metadata; executable bindings are constructed outside the DB transaction.
 */
async function loadRoutingResolutionWithClient(
  client: Client,
  userId: string,
  selection: z.infer<typeof ConversationAiSelectionSchema>,
): Promise<RoutingResolution> {
    let resolvedChoice: AiChoiceRef
    if (selection.kind === 'default') {
      const row = (await client.query(`SELECT kind,connection_id,model_id,configuration_id,cli_id
        FROM ai_user_defaults WHERE user_id=$1 FOR SHARE`, [userId])).rows[0]
      if (!row) throw new AiConsoleError('AI_DEFAULT_REQUIRED')
      try { resolvedChoice = rowChoice(row) }
      catch { throw new AiConsoleError('AI_CHOICE_BROKEN') }
    } else {
      resolvedChoice = selection.choice
    }
    assertChoiceUuid(resolvedChoice)

    let assignments: RoleAssignments
    let configurationVersion: number | null = null
    if (resolvedChoice.kind === 'custom_configuration') {
      const configuration = (await client.query(`SELECT id,version FROM ai_custom_configurations
        WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL FOR SHARE`,
      [userId, resolvedChoice.configurationId])).rows[0]
      if (!configuration) throw new AiConsoleError('AI_CHOICE_BROKEN')
      const rows = (await client.query(`SELECT role,kind,connection_id,model_id,cli_id,effort
        FROM ai_custom_configuration_roles WHERE user_id=$1 AND configuration_id=$2 ORDER BY role FOR SHARE`,
      [userId, resolvedChoice.configurationId])).rows
      let rawAssignments: Record<string, RoleTarget>
      try { rawAssignments = Object.fromEntries(rows.map(row => [String(row.role), rowRole(row)])) }
      catch { throw new AiConsoleError('AI_CHOICE_BROKEN') }
      const parsed = RoleAssignmentsSchema.safeParse(rawAssignments)
      if (!parsed.success) throw new AiConsoleError('AI_CHOICE_BROKEN')
      assignments = parsed.data
      configurationVersion = z.coerce.number().int().positive().parse(configuration.version)
    } else {
      assignments = Object.fromEntries(AI_ROLES.map(role => [role, resolvedChoice])) as RoleAssignments
    }

    const grouped = new Map<string, { target: RoleTarget; roles: AiRole[] }>()
    for (const role of AI_ROLES) {
      const target = assignments[role]
      const key = JSON.stringify([target.kind, target.kind === 'provider_model' ? target.connectionId : target.cliId,
        target.modelId, target.effort ?? null])
      const current = grouped.get(key) ?? { target, roles: [] }
      current.roles.push(role)
      grouped.set(key, current)
    }
    const resolvedByKey = new Map<string, RoutingTarget>()
    for (const [key, group] of grouped) {
      resolvedByKey.set(key, await loadRoutingTarget(client, userId, group.target, group.roles))
    }
    const roles = Object.fromEntries(AI_ROLES.map(role => {
      const target = assignments[role]
      const key = JSON.stringify([target.kind, target.kind === 'provider_model' ? target.connectionId : target.cliId,
        target.modelId, target.effort ?? null])
      return [role, resolvedByKey.get(key)!]
    })) as Record<AiRole, RoutingTarget>
    return { resolvedChoice, configurationVersion, roles }
}

export async function loadRoutingResolution(userId: string, input: unknown, conversationId?: string): Promise<RoutingResolution> {
  if (typeof userId !== 'string' || userId.trim().length === 0) throw new AiConsoleError('AI_PERMISSION_DENIED')
  if (conversationId !== undefined && !uuidSchema.safeParse(conversationId).success) {
    throw new AiConsoleError('AI_PERMISSION_DENIED')
  }
  const parsedSelection = ConversationAiSelectionSchema.safeParse(input)
  if (!parsedSelection.success) throw notFound()
  const selection = parsedSelection.data
  if (selection.kind === 'explicit') assertChoiceUuid(selection.choice)
  return withUserTransaction(userId, async client => {
    const owner = (await client.query("SELECT id FROM profiles WHERE id=$1 AND status='active' FOR SHARE", [userId])).rows
    if (!owner.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
    if (conversationId !== undefined) await ownedConversation(client, userId, conversationId)
    return loadRoutingResolutionWithClient(client, userId, selection)
  })
}

export async function createConnection(userId: string, input: unknown, encrypted: EncryptedCredential) {
  const data = z.object({ providerId: ProviderIdSchema, name: nameSchema,
    workspaceId: workspaceIdSchema.optional() }).strict().parse(input)
  if (data.providerId !== 'anthropic' && data.workspaceId) throw new AiConsoleError('AI_EXECUTION_FAILED')
  return withUserTransaction(userId, async client => {
    const row = required((await client.query(`INSERT INTO ai_provider_connections
      (user_id,provider_id,name,credential_ciphertext,credential_nonce,credential_tag,wrapped_dek,wrap_nonce,wrap_tag,kek_version,masked_suffix,keyed_fingerprint,anthropic_workspace_id,model_retest_required)
      VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,true) RETURNING ${safeColumns}`,
    [userId, data.providerId, data.name, ...credentialParams(encrypted), data.workspaceId ?? null])).rows)
    await writeAiAudit(client, userId, { event: 'connection_created', connectionId: row.id })
    return safeConnection(row)
  })
}
/** Workspace edits revalidate the existing key without requiring its plaintext again. */
export async function updateConnectionWorkspace(userId: string, connectionId: string, workspaceId: string | null) {
  const parsed = workspaceIdSchema.parse(workspaceId)
  return withUserTransaction(userId, async client => {
    const row = required((await client.query(`UPDATE ai_provider_connections SET anthropic_workspace_id=$3,
      credential_version=credential_version+1,model_retest_required=true,
      credential_validity='unknown',validation_state='untested',
      last_validated_at=NULL,last_checked_at=NULL,last_error_code=NULL,updated_at=now()
      WHERE user_id=$1 AND id=$2 AND provider_id='anthropic' AND deleted_at IS NULL
      RETURNING ${safeColumns},credential_version`, [userId, connectionId, parsed])).rows)
    await invalidateCatalog(client, userId, connectionId)
    await clearModelProbeEvidence(client, userId, connectionId)
    await writeAiAudit(client, userId, { event: 'connection_updated', connectionId })
    return { connection: safeConnection(row), credentialVersion: Number(row.credential_version) }
  })
}
export async function renameConnection(userId: string, connectionId: string, name: string) {
  const parsed = nameSchema.parse(name)
  return withUserTransaction(userId, async client => {
    const row = required((await client.query(`UPDATE ai_provider_connections SET name=$3,updated_at=now()
      WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL RETURNING ${safeColumns}`, [userId, connectionId, parsed])).rows)
    await writeAiAudit(client, userId, { event: 'connection_renamed', connectionId })
    return safeConnection(row)
  })
}
export async function replaceConnectionCredential(userId: string, connectionId: string, encrypted: EncryptedCredential) {
  return withUserTransaction(userId, async client => {
    const row = required((await client.query(`UPDATE ai_provider_connections SET
      credential_ciphertext=$3,credential_nonce=$4,credential_tag=$5,wrapped_dek=$6,wrap_nonce=$7,wrap_tag=$8,
      kek_version=$9,masked_suffix=$10,keyed_fingerprint=$11,credential_version=credential_version+1,
      model_retest_required=true,
      credential_validity='unknown',validation_state='untested',last_validated_at=NULL,last_checked_at=NULL,last_error_code=NULL,updated_at=now()
      WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL RETURNING ${safeColumns},credential_version`,
    [userId, connectionId, ...credentialParams(encrypted)])).rows)
    await invalidateCatalog(client, userId, connectionId)
    await clearModelProbeEvidence(client, userId, connectionId)
    await writeAiAudit(client, userId, { event: 'connection_credential_replaced', connectionId })
    return { connection: safeConnection(row), credentialVersion: Number(row.credential_version) }
  })
}
const ValidationSchema = z.object({
  credentialVersion: z.number().int().positive(),
  state: z.enum(['validated', 'needs_attention', 'invalid', 'unreachable', 'validating']),
  errorCode: z.enum(['AI_CONNECTION_INVALID', 'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE', 'AI_PROVIDER_UNREACHABLE',
    'AI_PERMISSION_DENIED', 'AI_BILLING_UNAVAILABLE', 'AI_RATE_LIMITED', 'AI_EXECUTION_FAILED']).optional(),
  models: z.array(z.object({ modelId: z.string().min(1), displayName: z.string().min(1),
    compatibleRoles: z.array(AiRoleSchema).min(1), supportsTools: z.boolean(),
    supportsStructuredOutput: z.boolean(), supportedEfforts: z.array(AiEffortSchema).max(16).optional(),
    defaultEffort: AiEffortSchema.nullable().optional(),
  }).strict()).optional(),
}).strict().refine(v => v.state !== 'validated' || !!v.models?.length)
export async function storeConnectionValidation(userId: string, connectionId: string, input: unknown) {
  const result = ValidationSchema.parse(input)
  return withUserTransaction(userId, async client => {
    const row = await ownedConnection(client, userId, connectionId)
    if (Number(row.credential_version) !== result.credentialVersion) throw notFound()
    const validity = result.state === 'validated' ? 'valid' : result.state === 'invalid' ? 'invalid' : row.credential_validity
    await client.query(`UPDATE ai_provider_connections SET validation_state=$3,credential_validity=$4,last_checked_at=now(),
      last_validated_at=CASE WHEN $3='validated' THEN now() ELSE last_validated_at END,last_error_code=$5,updated_at=now()
      WHERE user_id=$1 AND id=$2 AND credential_version=$6`, [userId, connectionId, result.state, validity, result.errorCode ?? null, result.credentialVersion])
    if (result.models !== undefined || result.state === 'invalid') {
      await invalidateCatalog(client, userId, connectionId)
      if (result.state !== 'invalid') for (const model of result.models ?? []) {
        await client.query(`INSERT INTO ai_connection_models(connection_id,model_id,display_name,compatible_roles,supports_tools,supports_structured_output,available,supported_efforts)
          SELECT id,$3,$4,$5,$6,$7,true,$8 FROM ai_provider_connections WHERE user_id=$1 AND id=$2
          ON CONFLICT(connection_id,model_id) DO UPDATE SET display_name=excluded.display_name,
          compatible_roles=excluded.compatible_roles,supports_tools=excluded.supports_tools,
          supports_structured_output=excluded.supports_structured_output,available=true,last_seen_at=now(),
          supported_efforts=excluded.supported_efforts`,
        [userId, connectionId, model.modelId, model.displayName, model.compatibleRoles,
          model.supportsTools, model.supportsStructuredOutput, model.supportedEfforts ?? null])
      }
    }
    await writeAiAudit(client, userId, result.state === 'validated'
      ? { event: 'connection_validation_succeeded', connectionId }
      : result.state === 'invalid'
        ? { event: 'connection_validation_rejected', connectionId,
          errorCode: result.errorCode ?? 'AI_CONNECTION_INVALID' }
        : { event: 'connection_validated', connectionId })
  })
}

/** Claim metadata work under the existing owner lock; never hold a transaction during HTTP. */
export async function claimConnectionCatalogRefresh(userId: string, connectionId: string, force: boolean) {
  z.boolean().parse(force)
  return withUserTransaction(userId, async client => {
    const connection = await ownedConnection(client, userId, connectionId)
    if (connection.provider_id === 'kimi' || connection.credential_validity !== 'valid'
      || !['validated', 'validating'].includes(String(connection.validation_state))) {
      throw new AiConsoleError('AI_CONNECTION_INVALID')
    }
    const row = (await client.query(`UPDATE ai_provider_connections c SET
      catalog_refresh_epoch=catalog_refresh_epoch+1,catalog_refresh_in_progress=true,
      catalog_attempted_at=clock_timestamp()
      WHERE c.user_id=$1 AND c.id=$2 AND c.deleted_at IS NULL
      AND EXISTS (SELECT 1 FROM profiles p WHERE p.id=$1 AND p.status='active')
      AND (catalog_attempted_at IS NULL OR catalog_attempted_at < clock_timestamp()-interval '60 seconds')
      AND (NOT catalog_refresh_in_progress OR catalog_attempted_at < clock_timestamp()-interval '60 seconds')
      AND ($3::boolean OR catalog_refreshed_at IS NULL OR catalog_refreshed_at < clock_timestamp()-interval '15 minutes')
      RETURNING credential_version,provider_id,catalog_refresh_epoch::text AS epoch`,
    [userId, connectionId, force])).rows[0]
    return row ? { credentialVersion: z.coerce.number().int().positive().parse(row.credential_version),
      providerId: ProviderIdSchema.parse(row.provider_id), epoch: z.string().regex(/^\d+$/).parse(row.epoch) } : null
  })
}

/** Catalogue discovery does not create generation evidence or change any saved selection. */
export async function storeConnectionCatalogRefresh(userId: string, connectionId: string, input: unknown): Promise<boolean> {
  const data = z.object({ credentialVersion: z.number().int().positive(), epoch: z.string().regex(/^\d+$/),
    errorCode: AiErrorCodeSchema.optional(), models: ValidationSchema.shape.models,
  }).strict().refine(value => (value.models !== undefined) !== (value.errorCode !== undefined)).parse(input)
  return withUserTransaction(userId, async client => {
    const connection = await ownedConnection(client, userId, connectionId)
    if (Number(connection.credential_version) !== data.credentialVersion) return false
    const rejected = data.errorCode === 'AI_CONNECTION_INVALID'
    const updated = await client.query(`UPDATE ai_provider_connections c SET
      catalog_refresh_in_progress=false,catalog_error_code=$5,
      catalog_refreshed_at=CASE WHEN $6::boolean THEN clock_timestamp() ELSE catalog_refreshed_at END,
      credential_validity=CASE WHEN $7::boolean THEN 'invalid' ELSE credential_validity END,
      validation_state=CASE WHEN $7::boolean THEN 'invalid' ELSE validation_state END,
      last_error_code=CASE WHEN $7::boolean THEN $5 ELSE last_error_code END
      WHERE c.user_id=$1 AND c.id=$2 AND c.credential_version=$3 AND c.catalog_refresh_epoch=$4::bigint
      AND c.catalog_refresh_in_progress AND c.deleted_at IS NULL
      AND EXISTS (SELECT 1 FROM profiles p WHERE p.id=$1 AND p.status='active') RETURNING id`,
    [userId, connectionId, data.credentialVersion, data.epoch, data.errorCode ?? null, data.models !== undefined, rejected])
    if (!updated.rowCount) return false
    if (data.models !== undefined) {
      await invalidateCatalog(client, userId, connectionId)
      for (const model of data.models) {
        await client.query(`INSERT INTO ai_connection_models
          (connection_id,model_id,display_name,compatible_roles,supports_tools,supports_structured_output,available,supported_efforts)
          SELECT id,$3,$4,$5,$6,$7,true,$8 FROM ai_provider_connections WHERE user_id=$1 AND id=$2
          ON CONFLICT(connection_id,model_id) DO UPDATE SET display_name=excluded.display_name,
          compatible_roles=excluded.compatible_roles,supports_tools=excluded.supports_tools,
          supports_structured_output=excluded.supports_structured_output,available=true,
          supported_efforts=excluded.supported_efforts,last_seen_at=now()`,
        [userId, connectionId, model.modelId, model.displayName, model.compatibleRoles,
          model.supportsTools, model.supportsStructuredOutput, model.supportedEfforts ?? null])
      }
    }
    await writeAiAudit(client, userId, { event: 'connection_updated', connectionId })
    return true
  })
}

/** A catalog row is only a discovery claim. Individual confirmation is a separate, version-fenced write. */
export async function storeProviderModelProbe(userId: string, connectionId: string, modelId: string,
  credentialVersion: number, result: { ok: true; inputTokens: number | null; outputTokens: number | null }
    | { ok: false; errorCode: string }) {
  const safeModelId = z.string().min(1).max(512).parse(modelId)
  const safeVersion = z.number().int().positive().parse(credentialVersion)
  const safeError = result.ok ? null : AiErrorCodeSchema.parse(result.errorCode)
  const tokenSchema = z.number().int().nonnegative().nullable()
  const inputTokens = result.ok ? tokenSchema.parse(result.inputTokens) : null
  const outputTokens = result.ok ? tokenSchema.parse(result.outputTokens) : null
  return withUserTransaction(userId, async client => {
    const connection = await ownedConnection(client, userId, connectionId)
    if (Number(connection.credential_version) !== safeVersion) throw notFound()
    const updated = await client.query(`UPDATE ai_connection_models m SET
      last_probe_at=now(),last_probe_error_code=$5,
      last_probe_input_tokens=$6,last_probe_output_tokens=$7,
      plain_tested_at=CASE WHEN $5::text IS NULL THEN now() ELSE m.plain_tested_at END,
      tested_credential_version=CASE WHEN $5::text IS NULL THEN $4 ELSE m.tested_credential_version END,
      user_selected=CASE WHEN $5::text IS NULL THEN true ELSE m.user_selected END
      FROM ai_provider_connections c WHERE c.id=m.connection_id AND c.user_id=$1 AND c.id=$2
      AND c.deleted_at IS NULL AND c.credential_version=$4 AND m.model_id=$3 AND m.available=true
      RETURNING m.model_id`, [userId, connectionId, safeModelId, safeVersion, safeError, inputTokens, outputTokens])
    if (!updated.rowCount) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    await writeAiAudit(client, userId, { event: 'connection_updated', connectionId })
  })
}

export async function deselectProviderModel(userId: string, connectionId: string, modelId: string) {
  const safeModelId = z.string().min(1).max(512).parse(modelId)
  return withUserTransaction(userId, async client => {
    await ownedConnection(client, userId, connectionId)
    const updated = await client.query(`UPDATE ai_connection_models m SET user_selected=false
      FROM ai_provider_connections c WHERE c.id=m.connection_id AND c.user_id=$1 AND c.id=$2 AND m.model_id=$3
      RETURNING m.model_id`, [userId, connectionId, safeModelId])
    if (!updated.rowCount) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    await writeAiAudit(client, userId, { event: 'connection_updated', connectionId })
  })
}

/** Server-internal global scheduler boundary. last_checked_at is a recoverable lease. */
export async function claimStaleConnectionRevalidations(input: { staleBefore: Date; limit: number }) {
  const { staleBefore, limit } = z.object({ staleBefore: z.date().refine(v => v.getTime() <= Date.now()),
    limit: z.number().int().min(1).max(25) }).strict().parse(input)
  return withTransaction(async client => {
    const { rows } = await client.query(`WITH candidates AS (
      SELECT c.id FROM ai_provider_connections c JOIN profiles p ON p.id=c.user_id
      WHERE p.status='active' AND c.deleted_at IS NULL AND c.credential_validity<>'invalid'
      AND (c.last_checked_at IS NULL OR c.last_checked_at < $1)
      ORDER BY c.last_checked_at NULLS FIRST,c.id LIMIT $2 FOR UPDATE OF c SKIP LOCKED
    ) UPDATE ai_provider_connections c SET validation_state='validating',last_checked_at=now(),updated_at=now()
      FROM candidates WHERE c.id=candidates.id
      RETURNING c.user_id,c.id,c.provider_id,c.credential_version`, [staleBefore, limit])
    return rows.map(row => ({ userId: String(row.user_id), connectionId: String(row.id),
      providerId: ProviderIdSchema.parse(row.provider_id), credentialVersion: z.coerce.number().int().positive().parse(row.credential_version) }))
  })
}

/** Exact-version runtime failure marker; no catalog rewrite or credential substitution. */
export async function markConnectionForRevalidation(userId: string, connectionId: string, credentialVersion: number, normalizedError: unknown) {
  z.number().int().positive().parse(credentialVersion)
  const error = z.object({ code: z.enum(['AI_CONNECTION_INVALID', 'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE',
    'AI_PROVIDER_UNREACHABLE', 'AI_PERMISSION_DENIED', 'AI_BILLING_UNAVAILABLE', 'AI_RATE_LIMITED']),
  message: z.string(), retryable: z.boolean(), role: AiRoleSchema.optional() }).strict().parse(normalizedError)
  // Accept only canonical normalized public values, never provider-controlled messages.
  if (!isDeepStrictEqual(error, normalizeAiError(new AiConsoleError(error.code, error.role), { source: 'provider' }))) throw notFound()
  const state = error.code === 'AI_CONNECTION_INVALID' ? 'invalid'
    : error.code === 'AI_PROVIDER_UNREACHABLE' || error.code === 'AI_RATE_LIMITED' ? 'unreachable' : 'needs_attention'
  return withUserTransaction(userId, async client => {
    required((await client.query(`UPDATE ai_provider_connections c SET validation_state=$4,
      credential_validity=CASE WHEN $5='AI_CONNECTION_INVALID' THEN 'invalid' ELSE credential_validity END,
      last_error_code=$5,last_checked_at=now(),updated_at=now()
      WHERE c.user_id=$1 AND c.id=$2 AND c.credential_version=$3 AND c.deleted_at IS NULL
      AND EXISTS(SELECT 1 FROM profiles p WHERE p.id=c.user_id AND p.status='active') RETURNING c.id`,
    [userId, connectionId, credentialVersion, state, error.code])).rows)
    await writeAiAudit(client, userId, error.code === 'AI_CONNECTION_INVALID'
      ? { event: 'connection_validation_rejected', connectionId, errorCode: error.code }
      : { event: 'connection_validated', connectionId })
  })
}

const ConfigurationKindSchema = z.enum(['provider_preset', 'cli_preset', 'custom_api', 'custom_cli'])
const ConfigurationInput = z.object({ id: uuidSchema.optional(), expectedVersion: z.number().int().positive().optional(),
  name: nameSchema, roles: RoleAssignmentsSchema, configurationKind: ConfigurationKindSchema,
  ownerConnectionId: uuidSchema.nullable(), ownerCliId: CliIdSchema.nullable() }).strict()
  .refine(v => !v.id || !!v.expectedVersion)
  .refine(v => configurationKindMatchesRoles(v.configurationKind, v.roles, v.ownerConnectionId, v.ownerCliId))
function parseConfigurationInput(input: unknown) {
  const raw = z.object({ id: uuidSchema.optional(), expectedVersion: z.number().int().positive().optional(),
    name: nameSchema, roles: RoleAssignmentsSchema, configurationKind: ConfigurationKindSchema.optional(),
    ownerConnectionId: uuidSchema.nullable().optional(), ownerCliId: CliIdSchema.nullable().optional() }).strict().parse(input)
  const inferredKind: ConfigurationKind = raw.configurationKind ?? (AI_ROLES.every(role => raw.roles[role].kind === 'provider_model')
    ? 'custom_api' : 'custom_cli')
  return ConfigurationInput.parse({ ...raw, configurationKind: inferredKind,
    ownerConnectionId: raw.ownerConnectionId ?? null, ownerCliId: raw.ownerCliId ?? null })
}
async function persistConfiguration(client: Client, userId: string, data: z.infer<typeof ConfigurationInput>, duplicate = false) {
  await assertAssignments(client, userId, data.roles)
  const row = data.id ? required((await client.query(`UPDATE ai_custom_configurations SET name=$3,version=version+1
    WHERE user_id=$1 AND id=$2 AND version=$4 AND configuration_kind=$5
    AND owner_connection_id IS NOT DISTINCT FROM $6::uuid AND owner_cli_id IS NOT DISTINCT FROM $7::text
    AND deleted_at IS NULL RETURNING id,name,version`,
  [userId, data.id, data.name, data.expectedVersion, data.configurationKind,
    data.ownerConnectionId, data.ownerCliId])).rows)
    : required((await client.query(`INSERT INTO ai_custom_configurations
      (user_id,name,configuration_kind,owner_connection_id,owner_cli_id)
      VALUES($1,$2,$3,$4,$5) RETURNING id,name,version`, [userId, data.name, data.configurationKind,
      data.ownerConnectionId, data.ownerCliId])).rows)
  for (const role of AI_ROLES) {
    const target = data.roles[role]
    await client.query(`INSERT INTO ai_custom_configuration_roles(configuration_id,user_id,role,kind,connection_id,model_id,cli_id,effort)
      SELECT id,user_id,$3,$4,$5,$6,$7,$8 FROM ai_custom_configurations WHERE user_id=$1 AND id=$2
      ON CONFLICT(configuration_id,role) DO UPDATE SET kind=excluded.kind,connection_id=excluded.connection_id,
      model_id=excluded.model_id,cli_id=excluded.cli_id,effort=excluded.effort WHERE ai_custom_configuration_roles.user_id=$1`,
    [userId, row.id, role, target.kind, target.kind === 'provider_model' ? target.connectionId : null, target.modelId,
      target.kind === 'local_cli' ? target.cliId : null, target.effort ?? null])
  }
  await writeAiAudit(client, userId, { event: duplicate ? 'configuration_duplicated' : data.id ? 'configuration_updated' : 'configuration_created', configurationId: row.id, configurationVersion: Number(row.version) })
  return { id: row.id as string, name: row.name as string, version: Number(row.version), roles: data.roles,
    configurationKind: data.configurationKind, ownerConnectionId: data.ownerConnectionId, ownerCliId: data.ownerCliId }
}
export async function saveConfiguration(userId: string, input: unknown) {
  const data = parseConfigurationInput(input)
  return withUserTransaction(userId, client => persistConfiguration(client, userId, data))
}
export async function duplicateConfiguration(userId: string, configurationId: string, name: string) {
  const parsed = nameSchema.parse(name)
  return withUserTransaction(userId, async client => {
    required((await client.query('SELECT id FROM ai_custom_configurations WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL FOR NO KEY UPDATE', [userId, configurationId])).rows)
    const rows = (await client.query('SELECT role,kind,connection_id,model_id,cli_id,effort FROM ai_custom_configuration_roles WHERE user_id=$1 AND configuration_id=$2', [userId, configurationId])).rows
    return persistConfiguration(client, userId, parseConfigurationInput({ name: parsed,
      roles: RoleAssignmentsSchema.parse(Object.fromEntries(rows.map(row => [row.role, rowRole(row)]))) }), true)
  })
}
export async function setUserDefault(userId: string, input: unknown) {
  const choice = AiChoiceRefSchema.parse(input)
  return withUserTransaction(userId, async client => {
    await assertChoice(client, userId, choice)
    await client.query(`INSERT INTO ai_user_defaults(user_id,kind,connection_id,model_id,configuration_id,cli_id)
      VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT(user_id) DO UPDATE SET kind=excluded.kind,connection_id=excluded.connection_id,
      model_id=excluded.model_id,configuration_id=excluded.configuration_id,cli_id=excluded.cli_id,updated_at=now()
      WHERE ai_user_defaults.user_id=$1`, [userId, ...choiceParams(choice)])
    await writeAiAudit(client, userId, { event: 'default_selected',
      ...(choice.kind === 'provider_model' ? { connectionId: choice.connectionId } : choice.kind === 'custom_configuration' ? { configurationId: choice.configurationId } : { cliId: choice.cliId }) })
  })
}
export async function setConversationSelection(userId: string, conversationId: string, input: unknown) {
  const selection = ConversationAiSelectionSchema.parse(input)
  return withUserTransaction(userId, async client => {
    await ownedConversation(client, userId, conversationId)
    if (selection.kind === 'explicit') await assertChoice(client, userId, selection.choice)
    await client.query(`INSERT INTO ai_conversation_selections(conversation_id,user_id,kind,connection_id,model_id,configuration_id,cli_id)
      SELECT id,user_id,$3,$4,$5,$6,$7 FROM conversations WHERE user_id=$1 AND id=$2
      ON CONFLICT(conversation_id) DO UPDATE SET kind=excluded.kind,connection_id=excluded.connection_id,
      model_id=excluded.model_id,configuration_id=excluded.configuration_id,cli_id=excluded.cli_id,changed_at=now()
      WHERE ai_conversation_selections.user_id=$1`, [userId, conversationId, ...choiceParams(selection.kind === 'default' ? selection : selection.choice)])
    await writeAiAudit(client, userId, { event: 'conversation_selected' })
  })
}

export async function getConversationSelection(userId: string, conversationId: string) {
  return withUserTransaction(userId, async client => {
    await ownedConversation(client, userId, conversationId)
    const row = (await client.query(`SELECT kind,connection_id,model_id,configuration_id,cli_id
      FROM ai_conversation_selections WHERE user_id=$1 AND conversation_id=$2`, [userId, conversationId])).rows[0]
    return ConversationAiSelectionSchema.parse(!row || row.kind === 'default'
      ? { kind: 'default' } : { kind: 'explicit', choice: rowChoice(row) })
  })
}

/** Preview includes configurations and their transitive default/conversation dependents. */
export async function previewChoiceDependencies(userId: string, input: unknown) {
  const choice = AiChoiceRefSchema.parse(input)
  const [, connectionId, , configurationId, cliId] = choiceParams(choice)
  const configs = await query(`SELECT DISTINCT c.id,c.name FROM ai_custom_configurations c
    JOIN ai_custom_configuration_roles r ON r.configuration_id=c.id AND r.user_id=c.user_id
    WHERE c.user_id=$1 AND c.deleted_at IS NULL AND (c.id=$3 OR r.connection_id=$2 OR r.cli_id=$4)`, [userId, connectionId, configurationId, cliId])
  const ids = configs.rows.map(r => r.id)
  if (configurationId && !ids.includes(configurationId)) ids.push(configurationId)
  const defaults = await query(`SELECT kind,connection_id,model_id,configuration_id,cli_id FROM ai_user_defaults
    WHERE user_id=$1 AND (connection_id=$2 OR configuration_id=ANY($3::uuid[]) OR cli_id=$4)`, [userId, connectionId, ids, cliId])
  const conversations = await query(`SELECT c.id AS conversation_id FROM conversations c LEFT JOIN ai_conversation_selections s
    ON s.conversation_id=c.id AND s.user_id=c.user_id WHERE c.user_id=$1
    AND (s.connection_id=$2 OR s.configuration_id=ANY($3::uuid[]) OR s.cli_id=$4
      OR ((s.conversation_id IS NULL OR s.kind='default') AND $5::boolean))`,
  [userId, connectionId, ids, cliId, !!defaults.rows.length])
  return { configurations: configs.rows, defaultAffected: !!defaults.rows.length, conversations: conversations.rows }
}
export async function deleteConnection(userId: string, connectionId: string, confirmed: boolean) {
  if (confirmed !== true) throw new AiConsoleError('AI_PERMISSION_DENIED')
  return withUserTransaction(userId, async client => {
    required((await client.query(`UPDATE ai_provider_connections SET deleted_at=now(),updated_at=now()
      WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL RETURNING id`, [userId, connectionId])).rows)
    await invalidateCatalog(client, userId, connectionId)
    await writeAiAudit(client, userId, { event: 'connection_deleted', connectionId })
  })
}
export async function deleteConfiguration(userId: string, configurationId: string, confirmed: boolean) {
  if (confirmed !== true) throw new AiConsoleError('AI_PERMISSION_DENIED')
  return withUserTransaction(userId, async client => {
    const row = required((await client.query(`UPDATE ai_custom_configurations SET deleted_at=now(),version=version+1
      WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL RETURNING version`, [userId, configurationId])).rows)
    await writeAiAudit(client, userId, { event: 'configuration_deleted', configurationId, configurationVersion: Number(row.version) })
  })
}

/** Adapter-only: a version mismatch fails rather than silently switching credentials. */
export async function assertConnectionRequestAuthorized(input: { userId: string; connectionId: string; providerId: z.infer<typeof ProviderIdSchema>; credentialVersion: number }): Promise<void> {
  const parsed = z.object({ userId: z.string().min(1), connectionId: uuidSchema, providerId: ProviderIdSchema,
    credentialVersion: z.number().int().positive() }).strict().safeParse(input)
  if (!parsed.success) throw notFound()
  const target = parsed.data
  // A fresh read immediately before dispatch. No credential projection, row lock,
  // or open transaction spans the subsequent external provider request.
  required((await query(`SELECT c.id FROM ai_provider_connections c JOIN profiles p ON p.id=c.user_id
    WHERE c.user_id=$1 AND c.id=$2 AND c.provider_id=$3 AND c.credential_version=$4
    AND c.deleted_at IS NULL AND p.status='active'`,
  [target.userId, target.connectionId, target.providerId, target.credentialVersion])).rows)
}

/** Runtime-only: authorize the exact selected model as well as the pinned connection version. */
export async function assertRuntimeModelRequestAuthorized(input: { userId: string; connectionId: string;
  providerId: z.infer<typeof ProviderIdSchema>; credentialVersion: number; modelId: string }): Promise<void> {
  const parsed = z.object({ userId: z.string().min(1), connectionId: uuidSchema, providerId: ProviderIdSchema,
    credentialVersion: z.number().int().positive(), modelId: z.string().min(1).max(512) }).strict().safeParse(input)
  if (!parsed.success) throw notFound()
  const target = parsed.data
  required((await query(`SELECT c.id FROM ai_provider_connections c JOIN profiles p ON p.id=c.user_id
    JOIN ai_connection_models m ON m.connection_id=c.id AND m.model_id=$5
    WHERE c.user_id=$1 AND c.id=$2 AND c.provider_id=$3 AND c.credential_version=$4
    AND c.deleted_at IS NULL AND c.credential_validity='valid' AND p.status='active' AND m.available=true`,
  [target.userId, target.connectionId, target.providerId, target.credentialVersion, target.modelId])).rows)
}

function encryptedCredential(row: Row): EncryptedCredential {
  const record: EncryptedCredential = { ciphertext: row.credential_ciphertext as Buffer, nonce: row.credential_nonce as Buffer,
    authTag: row.credential_tag as Buffer, wrappedDataKey: row.wrapped_dek as Buffer, wrapNonce: row.wrap_nonce as Buffer,
    wrapAuthTag: row.wrap_tag as Buffer, keyVersion: String(row.kek_version), mask: String(row.masked_suffix),
    fingerprint: String(row.keyed_fingerprint), ...(row.anthropic_workspace_id ? { workspaceId: String(row.anthropic_workspace_id) } : {}) }
  Object.defineProperties(record, { toJSON: { value: () => '[REDACTED]' }, [inspect.custom]: { value: () => '[REDACTED]' } })
  return record
}

/** One-statement runtime authorization and encrypted credential projection for the exact model. */
export async function loadRuntimeModelCredential(input: { userId: string; connectionId: string;
  providerId: z.infer<typeof ProviderIdSchema>; credentialVersion: number; modelId: string }): Promise<EncryptedCredential> {
  const parsed = z.object({ userId: z.string().min(1), connectionId: uuidSchema, providerId: ProviderIdSchema,
    credentialVersion: z.number().int().positive(), modelId: z.string().min(1).max(512) }).strict().safeParse(input)
  if (!parsed.success) throw notFound()
  const target = parsed.data
  const row = required((await query(`SELECT c.credential_ciphertext,c.credential_nonce,c.credential_tag,c.wrapped_dek,
    c.wrap_nonce,c.wrap_tag,c.kek_version,c.masked_suffix,c.keyed_fingerprint,c.anthropic_workspace_id FROM ai_provider_connections c
    JOIN profiles p ON p.id=c.user_id JOIN ai_connection_models m ON m.connection_id=c.id AND m.model_id=$5
    WHERE c.user_id=$1 AND c.id=$2 AND c.provider_id=$3 AND c.credential_version=$4
    AND c.deleted_at IS NULL AND c.credential_validity='valid' AND p.status='active' AND m.available=true`,
  [target.userId, target.connectionId, target.providerId, target.credentialVersion, target.modelId])).rows)
  return encryptedCredential(row)
}

/** Adapter-only: a version mismatch fails rather than silently switching credentials. */
export async function loadConnectionCredential(userId: string, connectionId: string, credentialVersion: number): Promise<EncryptedCredential> {
  if (!uuidSchema.safeParse(connectionId).success || !z.number().int().positive().safeParse(credentialVersion).success) throw notFound()
  const row = required((await query(`SELECT c.credential_ciphertext,c.credential_nonce,c.credential_tag,c.wrapped_dek,
    c.wrap_nonce,c.wrap_tag,c.kek_version,c.masked_suffix,c.keyed_fingerprint,c.anthropic_workspace_id FROM ai_provider_connections c
    JOIN profiles p ON p.id=c.user_id WHERE c.user_id=$1 AND c.id=$2 AND c.credential_version=$3
    AND c.deleted_at IS NULL AND p.status='active'`, [userId, connectionId, credentialVersion])).rows)
  return encryptedCredential(row)
}

export interface CliInvocationHandle {
  readonly pid: number
  cancel(): void | Promise<void>
}

export interface CliValidationWrite {
  state: 'reachable' | 'not_installed' | 'auth_unavailable' | 'unreachable' | 'needs_attention'
  detectedProduct?: string
  detectedVersion?: string
  entrypointSha256?: string
  errorCode?: 'AI_CLI_NOT_INSTALLED' | 'AI_CLI_AUTH_UNAVAILABLE' | 'AI_CLI_UNREACHABLE'
    | 'AI_CLI_TIMEOUT' | 'AI_CLI_OUTPUT_LIMIT' | 'AI_EXECUTION_FAILED'
  models?: readonly {
    modelId: string
    displayName: string
    compatibleRoles: readonly AiRole[]
    supportsTools: boolean
    supportsStructuredOutput: boolean
    isBuiltinDefault: boolean
    supportedEfforts?: readonly string[]
    defaultEffort?: string | null
    isCatalogDiscovered?: boolean
  }[]
}

type CliStoredValidationState = 'untested' | 'validating' | CliValidationWrite['state']
type CliStoredErrorCode = NonNullable<CliValidationWrite['errorCode']>
export interface CliValidationAttempt {
  readonly cliId: z.infer<typeof CliIdSchema>
  /** PostgreSQL row-version token; never exposed by a route. */
  readonly epoch: string
  readonly previous: {
    readonly state: CliStoredValidationState
    readonly detectedProduct: string | null
    readonly detectedVersion: string | null
    readonly lastCheckedAt: Date | null
    readonly errorCode: CliStoredErrorCode | null
    readonly entrypointSha256?: string | null
  }
}

const cliStoredStateSchema = z.enum(['untested', 'validating', 'reachable', 'not_installed',
  'auth_unavailable', 'unreachable', 'needs_attention'])
const cliStoredErrorSchema = z.enum(['AI_CLI_NOT_INSTALLED', 'AI_CLI_AUTH_UNAVAILABLE', 'AI_CLI_UNREACHABLE',
  'AI_CLI_TIMEOUT', 'AI_CLI_OUTPUT_LIMIT', 'AI_EXECUTION_FAILED'])
const cliEpochSchema = z.string().regex(/^\d+$/)

export async function markCliValidationStarted(cliId: string): Promise<CliValidationAttempt> {
  const cli = CliIdSchema.parse(cliId)
  return withTransaction(async client => {
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('ai-console:cli:' || $1::text, 0))", [cli])
    await client.query(`INSERT INTO ai_cli_installations(cli_id) VALUES($1) ON CONFLICT(cli_id) DO NOTHING`, [cli])
    const previous = required((await client.query(`SELECT validation_state,detected_product,detected_version,
      last_checked_at,last_error_code,entrypoint_sha256 FROM ai_cli_installations WHERE cli_id=$1 FOR UPDATE`, [cli])).rows)
    const started = required((await client.query(`UPDATE ai_cli_installations SET
      validation_state=CASE WHEN validation_state='validating' THEN 'untested' ELSE validation_state END,
      detected_product=CASE WHEN validation_state='validating' THEN NULL ELSE detected_product END,
      detected_version=CASE WHEN validation_state='validating' THEN NULL ELSE detected_version END,
      last_checked_at=CASE WHEN validation_state='validating' THEN NULL ELSE last_checked_at END,
      last_error_code=CASE WHEN validation_state='validating' THEN NULL ELSE last_error_code END,
      updated_at=clock_timestamp() WHERE cli_id=$1 RETURNING xmin::text AS validation_epoch`, [cli])).rows)
    const previousState = cliStoredStateSchema.parse(previous.validation_state)
    // A cross-process predecessor can disappear while marked validating. Never
    // restore that non-terminal marker and strand the host; fail closed instead.
    const orphaned = previousState === 'validating'
    return {
      cliId: cli, epoch: cliEpochSchema.parse(started.validation_epoch),
      previous: {
        state: orphaned ? 'untested' : previousState,
        detectedProduct: orphaned || previous.detected_product == null ? null
          : z.string().min(1).max(120).parse(previous.detected_product),
        detectedVersion: orphaned || previous.detected_version == null ? null
          : z.string().min(1).max(80).parse(previous.detected_version),
        lastCheckedAt: orphaned || previous.last_checked_at == null ? null : z.coerce.date().parse(previous.last_checked_at),
        errorCode: orphaned || previous.last_error_code == null ? null : cliStoredErrorSchema.parse(previous.last_error_code),
        entrypointSha256: orphaned || previous.entrypoint_sha256 == null ? null
          : z.string().regex(/^[a-f0-9]{64}$/).parse(previous.entrypoint_sha256),
      },
    }
  })
}

/** Grant-gated preflight. It reveals no installation/auth state on denial. */
export async function assertCliValidationAuthorized(userId: string, cliId: string): Promise<void> {
  const cli = CliIdSchema.parse(cliId)
  const rows = await query(`SELECT g.cli_id FROM ai_cli_grants g JOIN profiles p ON p.id=g.user_id
    WHERE g.user_id=$1 AND g.cli_id=$2 AND g.revoked_at IS NULL AND p.status='active'`, [userId, cli])
  if (!rows.rows.length) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
}

/** Host-wide refresh lease shared by granted users and server instances. */
export async function claimCliCatalogRefresh(userId: string, cliId: string, force: boolean): Promise<string | null> {
  const cli = CliIdSchema.parse(cliId)
  z.boolean().parse(force)
  return withTransaction(async client => {
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('ai-console:cli:' || $1::text, 0))", [cli])
    const grant = await client.query(`SELECT g.cli_id FROM ai_cli_grants g JOIN profiles p ON p.id=g.user_id
      WHERE g.user_id=$1 AND g.cli_id=$2 AND g.revoked_at IS NULL AND p.status='active' FOR SHARE OF g,p`, [userId, cli])
    if (!grant.rows.length) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
    await client.query(`INSERT INTO ai_cli_installations(cli_id) VALUES($1) ON CONFLICT(cli_id) DO NOTHING`, [cli])
    const row = (await client.query(`UPDATE ai_cli_installations SET
      catalog_refresh_epoch=catalog_refresh_epoch+1,catalog_refresh_in_progress=true,catalog_attempted_at=clock_timestamp()
      WHERE cli_id=$1
      AND (catalog_attempted_at IS NULL OR catalog_attempted_at < clock_timestamp()-interval '60 seconds')
      AND (NOT catalog_refresh_in_progress OR catalog_attempted_at < clock_timestamp()-interval '180 seconds')
      AND ($2::boolean OR catalog_refreshed_at IS NULL OR catalog_refreshed_at < clock_timestamp()-interval '15 minutes')
      RETURNING catalog_refresh_epoch::text AS epoch`, [cli, force])).rows[0]
    return row ? z.string().regex(/^\d+$/).parse(row.epoch) : null
  })
}

export async function finishCliCatalogRefresh(cliId: string, epoch: string, errorCode?: string): Promise<boolean> {
  const cli = CliIdSchema.parse(cliId)
  const safeEpoch = z.string().regex(/^\d+$/).parse(epoch)
  const code = errorCode === undefined ? null : AiErrorCodeSchema.parse(errorCode)
  const result = await query(`UPDATE ai_cli_installations SET catalog_refresh_in_progress=false,catalog_error_code=$3
    WHERE cli_id=$1 AND catalog_refresh_epoch=$2::bigint AND catalog_refresh_in_progress`, [cli, safeEpoch, code])
  return (result.rowCount ?? 0) > 0
}

/** Global host state contains no user or authentication material. */
export async function storeCliValidation(cliId: string, input: CliValidationWrite, epoch: string): Promise<string | null> {
  const cli = CliIdSchema.parse(cliId)
  const expectedEpoch = cliEpochSchema.parse(epoch)
  const data = z.object({
    state: z.enum(['reachable', 'not_installed', 'auth_unavailable', 'unreachable', 'needs_attention']),
    detectedProduct: z.string().min(1).max(120).optional(),
    detectedVersion: z.string().min(1).max(80).optional(),
    entrypointSha256: z.string().regex(/^[a-f0-9]{64}$/).optional(),
    errorCode: z.enum(['AI_CLI_NOT_INSTALLED', 'AI_CLI_AUTH_UNAVAILABLE', 'AI_CLI_UNREACHABLE',
      'AI_CLI_TIMEOUT', 'AI_CLI_OUTPUT_LIMIT', 'AI_EXECUTION_FAILED']).optional(),
    models: z.array(z.object({ modelId: z.string().min(1).max(512), displayName: z.string().min(1).max(120),
      compatibleRoles: z.array(AiRoleSchema).min(1), supportsTools: z.boolean(), supportsStructuredOutput: z.boolean(),
      isBuiltinDefault: z.boolean(), supportedEfforts: z.array(AiEffortSchema).max(16).optional(),
      defaultEffort: AiEffortSchema.nullable().optional(), isCatalogDiscovered: z.boolean().optional(),
    }).strict()).optional(),
  }).strict().parse(input)
  return withTransaction(async client => {
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('ai-console:cli:' || $1::text, 0))", [cli])
    const updated = await client.query(`UPDATE ai_cli_installations SET detected_product=$2,detected_version=$3,
      validation_state=$4,last_checked_at=clock_timestamp(),last_error_code=$5,updated_at=clock_timestamp(),
      entrypoint_sha256=COALESCE($7,entrypoint_sha256),
      catalog_refreshed_at=CASE WHEN $8::boolean THEN clock_timestamp() ELSE catalog_refreshed_at END,
      catalog_attempted_at=clock_timestamp(),catalog_error_code=$5
      WHERE cli_id=$1 AND xmin::text=$6 RETURNING xmin::text AS validation_epoch`,
    [cli, data.detectedProduct ?? null, data.detectedVersion ?? null, data.state, data.errorCode ?? null,
      expectedEpoch, data.entrypointSha256 ?? null, data.models !== undefined])
    if (!updated.rows.length) return null
    if (data.models !== undefined) await client.query(`UPDATE ai_cli_models SET available=false,
      is_catalog_discovered=false,supported_efforts='{}',default_effort=NULL WHERE cli_id=$1`, [cli])
    for (const model of data.models ?? []) {
      await client.query(`INSERT INTO ai_cli_models
        (cli_id,model_id,display_name,is_builtin_default,available,compatible_roles,supports_tools,supports_structured_output,
         supported_efforts,default_effort,is_catalog_discovered)
        VALUES($1,$2,$3,$4,true,$5,$6,$7,$8,$9,$10)
        ON CONFLICT(cli_id,model_id) DO UPDATE SET display_name=excluded.display_name,
        is_builtin_default=excluded.is_builtin_default,available=true,compatible_roles=excluded.compatible_roles,
        supports_tools=excluded.supports_tools,supports_structured_output=excluded.supports_structured_output,last_seen_at=now(),
        supported_efforts=excluded.supported_efforts,default_effort=excluded.default_effort,is_catalog_discovered=excluded.is_catalog_discovered`,
      [cli, model.modelId, model.displayName, model.isBuiltinDefault, model.compatibleRoles,
        model.supportsTools, model.supportsStructuredOutput, model.supportedEfforts ?? [],
        model.defaultEffort ?? null, model.isCatalogDiscovered ?? false])
    }
    if (data.state === 'reachable' && data.detectedVersion && data.entrypointSha256) {
      await client.query(`UPDATE ai_cli_models SET available=true WHERE cli_id=$1 AND is_manual=true
        AND tested_version=$2 AND tested_entrypoint_sha256=$3`,
      [cli, data.detectedVersion, data.entrypointSha256])
    }
    return cliEpochSchema.parse(updated.rows[0].validation_epoch)
  })
}

export async function listConfirmedManualCliModels(cliId: string, version: string, entrypointSha256: string): Promise<string[]> {
  const cli = CliIdSchema.parse(cliId)
  const safeVersion = z.string().min(1).max(80).parse(version)
  const safeSha = z.string().regex(/^[a-f0-9]{64}$/).parse(entrypointSha256)
  const rows = await query(`SELECT model_id FROM ai_cli_models WHERE cli_id=$1 AND is_manual=true
    AND available=true AND tested_version=$2 AND tested_entrypoint_sha256=$3 ORDER BY model_id`,
  [cli, safeVersion, safeSha])
  return rows.rows.map(row => z.string().min(1).max(512).parse(row.model_id))
}

/** Host-global model addition is grant-gated and bound to the exact inspected binary/version. */
export async function storeManualCliModel(userId: string, cliId: string, modelId: string,
  version: string, entrypointSha256: string): Promise<void> {
  const cli = CliIdSchema.parse(cliId)
  if (cli !== 'codex' && cli !== 'claude_code') throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
  const model = validateCliModelId(modelId)
  if (!model || model === CLI_BUILTIN_MODEL_DB_ID) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
  const safeVersion = z.string().min(1).max(80).parse(version)
  const safeSha = z.string().regex(/^[a-f0-9]{64}$/).parse(entrypointSha256)
  await withTransaction(async client => {
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('ai-console:cli:' || $1::text, 0))", [cli])
    const authorized = await client.query(`SELECT i.cli_id FROM ai_cli_grants g
      JOIN ai_cli_installations i ON i.cli_id=g.cli_id JOIN profiles p ON p.id=g.user_id
      WHERE g.user_id=$1 AND g.cli_id=$2 AND g.revoked_at IS NULL AND p.status='active'
      AND i.validation_state='reachable' AND i.detected_version=$3 FOR SHARE OF g,i`,
    [userId, cli, safeVersion])
    if (!authorized.rowCount) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
    await client.query(`INSERT INTO ai_cli_models (cli_id,model_id,display_name,is_builtin_default,available,
      compatible_roles,supports_tools,supports_structured_output,is_manual,tested_entrypoint_sha256,tested_version)
      VALUES($1,$2,$2,false,true,$3,false,true,true,$4,$5)
      ON CONFLICT(cli_id,model_id) DO UPDATE SET available=true,is_manual=true,
      tested_entrypoint_sha256=excluded.tested_entrypoint_sha256,tested_version=excluded.tested_version,
      compatible_roles=excluded.compatible_roles,supports_structured_output=true,last_seen_at=now()`,
    [cli, model, [...CLI_REGISTRY[cli].compatibleRoles], safeSha, safeVersion])
    await writeAiAudit(client, userId, { event: 'cli_model_added', cliId: cli })
  })
}

/** Restore the prior visible state only if no newer host validation superseded this attempt. */
export async function restoreCliValidation(attempt: CliValidationAttempt): Promise<boolean> {
  const cli = CliIdSchema.parse(attempt.cliId)
  const epoch = cliEpochSchema.parse(attempt.epoch)
  const previous = {
    state: cliStoredStateSchema.parse(attempt.previous.state),
    detectedProduct: attempt.previous.detectedProduct == null ? null
      : z.string().min(1).max(120).parse(attempt.previous.detectedProduct),
    detectedVersion: attempt.previous.detectedVersion == null ? null
      : z.string().min(1).max(80).parse(attempt.previous.detectedVersion),
    lastCheckedAt: attempt.previous.lastCheckedAt == null ? null : z.coerce.date().parse(attempt.previous.lastCheckedAt),
    errorCode: attempt.previous.errorCode == null ? null : cliStoredErrorSchema.parse(attempt.previous.errorCode),
  }
  return withTransaction(async client => {
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('ai-console:cli:' || $1::text, 0))", [cli])
    const restored = await client.query(`UPDATE ai_cli_installations SET detected_product=$2,detected_version=$3,
      validation_state=$4,last_checked_at=$5,last_error_code=$6,updated_at=clock_timestamp()
      WHERE cli_id=$1 AND xmin::text=$7 RETURNING cli_id`,
    [cli, previous.detectedProduct, previous.detectedVersion, previous.state, previous.lastCheckedAt,
      previous.errorCode, epoch])
    return restored.rows.length === 1
  })
}

export async function listAdminCliGrants(actorId: string, userId: string) {
  const rows = await query(`SELECT cli.cli_id,g.granted_at,g.revoked_at,
    CASE WHEN i.validation_state='reachable' THEN 'reachable'
      WHEN i.validation_state IS NULL THEN 'unavailable' ELSE 'unavailable' END AS host_state
    FROM profiles actor CROSS JOIN profiles target
    CROSS JOIN unnest($3::text[]) WITH ORDINALITY AS cli(cli_id,ord)
    LEFT JOIN ai_cli_grants g ON g.user_id=target.id AND g.cli_id=cli.cli_id
    LEFT JOIN ai_cli_installations i ON i.cli_id=cli.cli_id
    WHERE actor.id=$1 AND actor.status='active' AND actor.role='super_admin' AND target.id=$2
    ORDER BY cli.ord`, [actorId, userId, CLI_IDS])
  if (rows.rows.length !== CLI_IDS.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
  return rows.rows
}

/**
 * Process creation/handle acquisition stays synchronous; never await model completion.
 * An optional asynchronous local-filesystem identity check may run after the
 * grant lock and immediately before process creation.
 * The handle stays outside the transaction so failure after spawn (including COMMIT)
 * cancels the started process exactly once. No callback or transaction retry occurs.
 */
export async function withCliInvocationAuthorization<T extends CliInvocationHandle>(userId: string, cliId: string, start: () => T,
  purpose: 'execution' | 'validation' = 'execution', beforeStart?: () => Promise<void>): Promise<T> {
  const cli = CliIdSchema.parse(cliId)
  if (!CLI_REGISTRY[cli].execution) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const safePurpose = z.enum(['execution', 'validation']).parse(purpose)
  if (typeof start !== 'function' || utilTypes.isAsyncFunction(start)) throw new AiConsoleError('AI_EXECUTION_FAILED')
  let started: T | undefined
  try {
    return await withUserTransaction(userId, async client => {
      const rows = (await client.query(`SELECT g.cli_id FROM ai_cli_grants g JOIN profiles p ON p.id=g.user_id
        JOIN ai_cli_installations i ON i.cli_id=g.cli_id WHERE g.user_id=$1 AND g.cli_id=$2
        AND g.revoked_at IS NULL AND p.status='active'
        ${safePurpose === 'execution' ? "AND i.validation_state='reachable'" : ''} FOR SHARE OF g,p,i`, [userId, cli])).rows
      if (!rows.length) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
      if (beforeStart) await beforeStart()
      const handle = start()
      // Retain any cancellable result before checking the rest of its contract.
      if (handle && typeof handle === 'object' && typeof handle.cancel === 'function') started = handle
      if (!started || 'then' in started || !Number.isSafeInteger(started.pid) || started.pid <= 0) {
        throw new AiConsoleError('AI_EXECUTION_FAILED')
      }
      return started
    })
  } catch (error) {
    try { await started?.cancel() } catch { /* Preserve the original authorization/commit error. */ }
    throw error
  }
}

/** Administrator-only grant persistence, with authorization and safe audit in one transaction. */
export async function setCliGrant(actorId: string, userId: string, cliId: string, granted: boolean): Promise<void> {
  const cli = CliIdSchema.parse(cliId)
  z.boolean().parse(granted)
  return withUserTransaction(userId, async client => {
    const actor = await client.query(`SELECT id FROM profiles WHERE id=$1 AND status='active' AND role='super_admin' FOR SHARE`, [actorId])
    if (!actor.rows.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
    const target = await client.query('SELECT id FROM profiles WHERE id=$1 FOR SHARE', [userId])
    if (!target.rows.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
    await client.query(`INSERT INTO ai_cli_installations(cli_id) VALUES($1) ON CONFLICT(cli_id) DO NOTHING`, [cli])
    if (granted) {
      const written = await client.query(`INSERT INTO ai_cli_grants(user_id,cli_id,granted_by)
        SELECT id,$2,$3 FROM profiles WHERE id=$1 AND status='active'
        ON CONFLICT(user_id,cli_id) DO UPDATE SET granted_by=excluded.granted_by,granted_at=now(),revoked_at=NULL
        WHERE ai_cli_grants.user_id=$1 RETURNING user_id`, [userId, cli, actorId])
      if (!written.rows.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
    } else {
      await client.query(`UPDATE ai_cli_grants SET revoked_at=clock_timestamp() WHERE user_id=$1 AND cli_id=$2 AND revoked_at IS NULL`, [userId, cli])
    }
    await client.query(`INSERT INTO admin_audit_log(actor_id,action,target_user_id,detail) VALUES($1,$2,$3,$4)`,
      [actorId, granted ? 'ai_cli_grant' : 'ai_cli_revoke', userId, { cliId: cli }])
  })
}

async function insertRoutingSnapshotWithClient(
  client: Client,
  snapshot: z.infer<typeof RoutingSnapshotSchema>,
): Promise<string> {
    if (snapshot.conversationId) await ownedConversation(client, snapshot.userId, snapshot.conversationId)
    const inserted = await client.query(`INSERT INTO ai_turn_routing_snapshots
      (user_id,correlation_id,source,conversation_id,selection,resolved_choice,configuration_version,roles)
      VALUES($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT(user_id,correlation_id) DO NOTHING RETURNING id`,
    [snapshot.userId, snapshot.correlationId, snapshot.source, snapshot.conversationId, snapshot.selection,
      snapshot.resolvedChoice, snapshot.configurationVersion, snapshot.roles])
    if (inserted.rows.length) return inserted.rows[0].id
    // Separate statement deliberately sees the winner after a concurrent ON CONFLICT wait.
    const row = required((await client.query(`SELECT id,source,conversation_id,selection,resolved_choice,configuration_version,roles
      FROM ai_turn_routing_snapshots WHERE user_id=$1 AND correlation_id=$2`, [snapshot.userId, snapshot.correlationId])).rows)
    const persisted = { source: row.source, conversationId: row.conversation_id, selection: row.selection,
      resolvedChoice: row.resolved_choice, configurationVersion: row.configuration_version === null ? null : Number(row.configuration_version), roles: row.roles }
    const expected = { source: snapshot.source, conversationId: snapshot.conversationId, selection: snapshot.selection,
      resolvedChoice: snapshot.resolvedChoice, configurationVersion: snapshot.configurationVersion, roles: snapshot.roles }
    if (!isDeepStrictEqual(persisted, expected)) throw notFound()
    return row.id
}

export async function insertRoutingSnapshot(input: unknown): Promise<string> {
  const snapshot = RoutingSnapshotSchema.parse(input)
  return withUserTransaction(snapshot.userId, client => insertRoutingSnapshotWithClient(client, snapshot))
}

const PrepareTurnRoutingSchema = z.object({
  userId: z.string().min(1).regex(/\S/),
  role: z.enum(['super_admin', 'guest']),
  chartId: z.string().uuid(),
  conversationId: z.string().uuid(),
  isFirstTurn: z.boolean(),
  turnId: z.string().min(1).regex(/\S/),
  source: z.enum(['pariprashna', 'consult']),
  selection: ConversationAiSelectionSchema,
}).strict()

/**
 * One serializable authority decision for a routed turn. The user advisory lock
 * covers chart/owner authority, first-turn initialization or stale-selection
 * comparison, exact target resolution, and the immutable snapshot. A concurrent
 * picker/default mutation therefore happens wholly before or after this decision.
 */
export async function prepareTurnRouting(input: unknown): Promise<PreparedTurnRouting> {
  const parsed = PrepareTurnRoutingSchema.parse(input)
  if (parsed.selection.kind === 'explicit') assertChoiceUuid(parsed.selection.choice)
  return withUserTransaction(parsed.userId, async client => {
    const owner = (await client.query("SELECT id FROM profiles WHERE id=$1 AND status='active' FOR SHARE", [parsed.userId])).rows
    if (!owner.length) throw new AiConsoleError('AI_PERMISSION_DENIED')

    const chart = (await client.query('SELECT owner_id FROM charts WHERE id=$1 FOR SHARE', [parsed.chartId])).rows[0]
    if (!chart) throw new AiConsoleError('AI_PERMISSION_DENIED')
    if (parsed.role !== 'super_admin' && chart.owner_id !== parsed.userId) {
      const grant = (await client.query(`SELECT permission FROM chart_grants
        WHERE chart_id=$1 AND principal_id=$2 AND permission='view' LIMIT 1 FOR SHARE`,
      [parsed.chartId, parsed.userId])).rows[0]
      if (!grant) throw new AiConsoleError('AI_PERMISSION_DENIED')
    }

    let authoritativeSelection: z.infer<typeof ConversationAiSelectionSchema>
    if (parsed.isFirstTurn) {
      const inserted = await client.query(`INSERT INTO conversations(id,chart_id,user_id,module,title)
        VALUES($1,$2,$3,'consume',NULL) ON CONFLICT(id) DO NOTHING RETURNING id`,
      [parsed.conversationId, parsed.chartId, parsed.userId])
      if (!inserted.rows.length) throw new AiConsoleError('AI_CHOICE_BROKEN')
      await client.query(`INSERT INTO ai_conversation_selections
        (conversation_id,user_id,kind,connection_id,model_id,configuration_id,cli_id)
        VALUES($1,$2,$3,$4,$5,$6,$7)`,
      [parsed.conversationId, parsed.userId, ...choiceParams(
        parsed.selection.kind === 'default' ? parsed.selection : parsed.selection.choice,
      )])
      await writeAiAudit(client, parsed.userId, { event: 'conversation_selected' })
      authoritativeSelection = parsed.selection
    } else {
      const conversation = (await client.query(`SELECT id,chart_id FROM conversations
        WHERE user_id=$1 AND id=$2 FOR NO KEY UPDATE`, [parsed.userId, parsed.conversationId])).rows[0]
      if (!conversation || conversation.chart_id !== parsed.chartId) throw new AiConsoleError('AI_PERMISSION_DENIED')
      const row = (await client.query(`SELECT kind,connection_id,model_id,configuration_id,cli_id
        FROM ai_conversation_selections WHERE user_id=$1 AND conversation_id=$2 FOR SHARE`,
      [parsed.userId, parsed.conversationId])).rows[0]
      authoritativeSelection = ConversationAiSelectionSchema.parse(!row || row.kind === 'default'
        ? { kind: 'default' } : { kind: 'explicit', choice: rowChoice(row) })
      if (!isDeepStrictEqual(authoritativeSelection, parsed.selection)) throw new AiConsoleError('AI_CHOICE_BROKEN')
    }

    const snapshot = (selection: z.infer<typeof ConversationAiSelectionSchema>, resolution: RoutingResolution,
      correlationId: string) => RoutingSnapshotSchema.parse({
        source: 'pariprashna',
        userId: parsed.userId,
        correlationId,
        conversationId: parsed.conversationId,
        selection,
        resolvedChoice: resolution.resolvedChoice,
        configurationVersion: resolution.configurationVersion,
        roles: Object.fromEntries(AI_ROLES.map(role => {
          const target = resolution.roles[role]
          return [role, target.kind === 'provider_model'
            ? { kind: target.kind, connectionId: target.connectionId, providerId: target.providerId,
              modelId: target.modelId, ...(target.effort ? { effort: target.effort } : {}) }
            : { kind: target.kind, cliId: target.cliId, modelId: target.modelId,
              ...(target.effort ? { effort: target.effort } : {}) }]
        })),
      })

    const resolution = await loadRoutingResolutionWithClient(client, parsed.userId, authoritativeSelection)
    const safeSnapshot = snapshot(authoritativeSelection, resolution, parsed.turnId)
    const snapshotId = await insertRoutingSnapshotWithClient(client, safeSnapshot)
    if (authoritativeSelection.kind === 'default') {
      return { selection: authoritativeSelection, resolution, safeSnapshot, snapshotId }
    }

    const defaultSelection = ConversationAiSelectionSchema.parse({ kind: 'default' })
    const fallbackResolution = await loadRoutingResolutionWithClient(client, parsed.userId, defaultSelection)
    const fallbackSafeSnapshot = snapshot(defaultSelection, fallbackResolution,
      `${parsed.turnId}:default-fallback`)
    if (isDeepStrictEqual(fallbackSafeSnapshot.roles, safeSnapshot.roles)) {
      return { selection: authoritativeSelection, resolution, safeSnapshot, snapshotId }
    }
    const fallbackSnapshotId = await insertRoutingSnapshotWithClient(client, fallbackSafeSnapshot)
    return { selection: authoritativeSelection, resolution, safeSnapshot, snapshotId,
      fallback: { resolution: fallbackResolution, safeSnapshot: fallbackSafeSnapshot,
        snapshotId: fallbackSnapshotId } }
  })
}

const McpPrincipalAuthorityFields = {
  userId: z.string().min(1).regex(/\S/),
  keyId: z.string().min(1).max(256),
  authKind: z.enum(['api_key', 'oauth']),
  chartId: z.string().uuid(),
}

function validateMcpPrincipalIdentity(
  value: { keyId: string; authKind: 'api_key' | 'oauth' },
  context: z.RefinementCtx,
): void {
  if (value.authKind === 'oauth' && !/^oauth_sha256:[0-9a-f]{64}$/.test(value.keyId)) {
    context.addIssue({ code: 'custom', path: ['keyId'], message: 'Invalid OAuth principal identity' })
  }
  if (value.authKind === 'api_key' && value.keyId.startsWith('oauth_sha256:')) {
    context.addIssue({ code: 'custom', path: ['keyId'], message: 'Invalid API-key principal identity' })
  }
}

const McpPrincipalAuthoritySchema = z.object(McpPrincipalAuthorityFields).strict()
  .superRefine(validateMcpPrincipalIdentity)

const PrepareMcpRoutingSchema = z.object({
  ...McpPrincipalAuthorityFields,
  correlationId: z.string().uuid(),
}).strict().superRefine(validateMcpPrincipalIdentity)

type McpPrincipalAuthority = z.infer<typeof McpPrincipalAuthoritySchema>

async function authorizeMcpPrincipalWithClient(
  client: Client,
  parsed: McpPrincipalAuthority,
): Promise<'super_admin' | 'guest'> {
  const credential = parsed.authKind === 'api_key'
    ? (await client.query(`SELECT key_id FROM mcp_api_keys
        WHERE key_id=$1 AND user_uid=$2 AND revoked_at IS NULL FOR SHARE`,
      [parsed.keyId, parsed.userId])).rows[0]
    : (await client.query(`SELECT access_token_hash FROM mcp_oauth_tokens
        WHERE access_token_hash=$1 AND uid=$2 AND expires_at>now() FOR SHARE`,
      [parsed.keyId.slice('oauth_sha256:'.length), parsed.userId])).rows[0]
  if (!credential) throw new AiConsoleError('AI_PERMISSION_DENIED')

  const profile = (await client.query(`SELECT id,role FROM profiles
    WHERE id=$1 AND status='active' FOR SHARE`, [parsed.userId])).rows[0]
  if (!profile) throw new AiConsoleError('AI_PERMISSION_DENIED')
  const role = profile.role === 'super_admin' ? 'super_admin' as const : 'guest' as const

  const chart = (await client.query('SELECT owner_id FROM charts WHERE id=$1 FOR SHARE', [parsed.chartId])).rows[0]
  if (!chart) throw new AiConsoleError('AI_PERMISSION_DENIED')
  if (role !== 'super_admin' && chart.owner_id !== parsed.userId) {
    const grant = (await client.query(`SELECT permission FROM chart_grants
      WHERE chart_id=$1 AND principal_id=$2 AND permission='view' LIMIT 1 FOR SHARE`,
    [parsed.chartId, parsed.userId])).rows[0]
    if (!grant) throw new AiConsoleError('AI_PERMISSION_DENIED')
  }
  return role
}

/** First managed-door gate. Snapshot preparation repeats this exact helper in its own transaction. */
export async function authorizeMcpPrincipal(input: unknown): Promise<{ role: 'super_admin' | 'guest' }> {
  const parsed = McpPrincipalAuthoritySchema.parse(input)
  return withUserTransaction(parsed.userId, async client => ({
    role: await authorizeMcpPrincipalWithClient(client, parsed),
  }))
}

async function loadPinnedMcpRouting(
  client: Client,
  userId: string,
  correlationId: string,
): Promise<Omit<PreparedMcpRouting, 'role'> | null> {
  const row = (await client.query(`SELECT id,source,conversation_id,selection,resolved_choice,configuration_version,roles
    FROM ai_turn_routing_snapshots WHERE user_id=$1 AND correlation_id=$2 FOR SHARE`,
  [userId, correlationId])).rows[0]
  if (!row) return null

  let safeSnapshot: z.infer<typeof RoutingSnapshotSchema>
  let snapshotId: string
  try {
    safeSnapshot = RoutingSnapshotSchema.parse({
      source: row.source,
      userId,
      correlationId,
      conversationId: row.conversation_id,
      selection: row.selection,
      resolvedChoice: row.resolved_choice,
      configurationVersion: row.configuration_version === null ? null : Number(row.configuration_version),
      roles: row.roles,
    })
    snapshotId = z.string().uuid().parse(row.id)
  } catch {
    throw new AiConsoleError('AI_CHOICE_BROKEN')
  }
  if (safeSnapshot.source !== 'mcp' || safeSnapshot.conversationId !== null) {
    throw new AiConsoleError('AI_CHOICE_BROKEN')
  }

  const grouped = new Map<string, { target: RoleTarget; roles: AiRole[] }>()
  for (const roleName of AI_ROLES) {
    const pinned = safeSnapshot.roles[roleName]
    const target: RoleTarget = pinned.kind === 'provider_model'
      ? { kind: pinned.kind, connectionId: pinned.connectionId, modelId: pinned.modelId,
        ...(pinned.effort ? { effort: pinned.effort } : {}) }
      : { kind: pinned.kind, cliId: pinned.cliId, modelId: pinned.modelId,
        ...(pinned.effort ? { effort: pinned.effort } : {}) }
    const key = JSON.stringify(target)
    const current = grouped.get(key) ?? { target, roles: [] }
    current.roles.push(roleName)
    grouped.set(key, current)
  }
  const resolvedByKey = new Map<string, RoutingTarget>()
  for (const [key, group] of grouped) {
    resolvedByKey.set(key, await loadRoutingTarget(client, userId, group.target, group.roles))
  }
  const roles = Object.fromEntries(AI_ROLES.map(roleName => {
    const pinned = safeSnapshot.roles[roleName]
    const target: RoleTarget = pinned.kind === 'provider_model'
      ? { kind: pinned.kind, connectionId: pinned.connectionId, modelId: pinned.modelId,
        ...(pinned.effort ? { effort: pinned.effort } : {}) }
      : { kind: pinned.kind, cliId: pinned.cliId, modelId: pinned.modelId,
        ...(pinned.effort ? { effort: pinned.effort } : {}) }
    const resolved = resolvedByKey.get(JSON.stringify(target))!
    const identityMatches = pinned.kind === 'provider_model' && resolved.kind === 'provider_model'
      ? pinned.connectionId === resolved.connectionId && pinned.providerId === resolved.providerId
        && pinned.modelId === resolved.modelId && (pinned.effort ?? null) === (resolved.effort ?? null)
      : pinned.kind === 'local_cli' && resolved.kind === 'local_cli'
        && pinned.cliId === resolved.cliId && pinned.modelId === resolved.modelId
        && (pinned.effort ?? null) === (resolved.effort ?? null)
    if (!identityMatches) throw new AiConsoleError('AI_CHOICE_BROKEN')
    return [roleName, resolved]
  })) as Record<AiRole, RoutingTarget>

  return {
    selection: safeSnapshot.selection,
    resolution: {
      resolvedChoice: safeSnapshot.resolvedChoice,
      configurationVersion: safeSnapshot.configurationVersion,
      roles,
    },
    safeSnapshot,
    snapshotId,
  }
}

/**
 * Re-verify the authenticated MCP credential mapping, active user, chart authority,
 * live Default, full four-role resolution and immutable snapshot under one user lock.
 * No executor or decrypted binding exists until this transaction commits.
 */
export async function prepareMcpRouting(input: unknown): Promise<PreparedMcpRouting> {
  const parsed = PrepareMcpRoutingSchema.parse(input)
  return withUserTransaction(parsed.userId, async client => {
    const role = await authorizeMcpPrincipalWithClient(client, parsed)

    const pinned = await loadPinnedMcpRouting(client, parsed.userId, parsed.correlationId)
    if (pinned) return { role, ...pinned }

    const selection = ConversationAiSelectionSchema.parse({ kind: 'default' })
    const resolution = await loadRoutingResolutionWithClient(client, parsed.userId, selection)
    const safeSnapshot = RoutingSnapshotSchema.parse({
      source: 'mcp',
      userId: parsed.userId,
      correlationId: parsed.correlationId,
      conversationId: null,
      selection,
      resolvedChoice: resolution.resolvedChoice,
      configurationVersion: resolution.configurationVersion,
      roles: Object.fromEntries(AI_ROLES.map(roleName => {
        const target = resolution.roles[roleName]
        return [roleName, target.kind === 'provider_model'
          ? { kind: target.kind, connectionId: target.connectionId, providerId: target.providerId,
            modelId: target.modelId, ...(target.effort ? { effort: target.effort } : {}) }
          : { kind: target.kind, cliId: target.cliId, modelId: target.modelId,
            ...(target.effort ? { effort: target.effort } : {}) }]
      })),
    })
    const snapshotId = await insertRoutingSnapshotWithClient(client, safeSnapshot)
    return { role, selection, resolution, safeSnapshot, snapshotId }
  })
}
const ReceiptSchema = z.object({ userId: z.string().min(1), snapshotId: z.string().uuid(), invocationId: z.string().uuid(), role: AiRoleSchema,
  phase: z.enum(['start', 'terminal']), status: z.enum(['started', 'succeeded', 'failed', 'cancelled']), errorCode: AiErrorCodeSchema.optional(),
}).strict().refine(r => r.phase === 'start' ? r.status === 'started' && !r.errorCode : r.status !== 'started' && (r.status !== 'succeeded' || !r.errorCode))
export async function insertRoleInvocationReceipt(input: unknown): Promise<void> {
  const receipt = ReceiptSchema.parse(input)
  return withUserTransaction(receipt.userId, async client => {
    const owner = (await client.query('SELECT id FROM ai_turn_routing_snapshots WHERE user_id=$1 AND id=$2', [receipt.userId, receipt.snapshotId])).rows
    if (!owner.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
    if (receipt.phase === 'terminal') {
      required((await client.query(`SELECT r.status FROM ai_turn_role_invocations r JOIN ai_turn_routing_snapshots s ON s.id=r.snapshot_id
        WHERE s.user_id=$1 AND s.id=$2 AND r.role=$3 AND r.invocation_id=$4 AND r.phase='start'`,
      [receipt.userId, receipt.snapshotId, receipt.role, receipt.invocationId])).rows)
    }
    const inserted = await client.query(`INSERT INTO ai_turn_role_invocations(snapshot_id,role,invocation_id,phase,status,error_code)
      SELECT id,$3,$4,$5,$6,$7 FROM ai_turn_routing_snapshots WHERE user_id=$1 AND id=$2
      ON CONFLICT(snapshot_id,role,invocation_id,phase) DO NOTHING RETURNING status`,
    [receipt.userId, receipt.snapshotId, receipt.role, receipt.invocationId, receipt.phase, receipt.status, receipt.errorCode ?? null])
    if (!inserted.rows.length) {
      const row = required((await client.query(`SELECT r.status,r.error_code FROM ai_turn_role_invocations r
        JOIN ai_turn_routing_snapshots s ON s.id=r.snapshot_id WHERE s.user_id=$1 AND s.id=$2
        AND r.role=$3 AND r.invocation_id=$4 AND r.phase=$5`,
      [receipt.userId, receipt.snapshotId, receipt.role, receipt.invocationId, receipt.phase])).rows)
      if (row.status !== receipt.status || row.error_code !== (receipt.errorCode ?? null)) throw notFound()
    }
  })
}
