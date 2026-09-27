import 'server-only'
import { isDeepStrictEqual, inspect, types as utilTypes } from 'node:util'
import type { PoolClient } from 'pg'
import { z } from 'zod'
import { query, withTransaction } from '@/lib/db/client'
import type { EncryptedCredential } from './crypto'
import { writeAiAudit } from './audit'
import { AiConsoleError, AiErrorCodeSchema, normalizeAiError } from './errors'
import {
  AI_ROLES, AiChoiceRefSchema, AiRoleSchema, CliIdSchema, ConversationAiSelectionSchema,
  ProviderIdSchema, RoleAssignmentsSchema, RoutingSnapshotSchema, SafeProviderConnectionSchema,
  type AiChoiceRef, type AiRole, type RoleAssignments, type RoleTarget, type SafeProviderConnection,
} from './types'

type Client = Pick<PoolClient, 'query'>
type Row = Record<string, unknown>
const nameSchema = z.string().trim().min(1).max(120)
const safeColumns = 'id,provider_id,name,masked_suffix,validation_state'
const notFound = () => new AiConsoleError('AI_CHOICE_BROKEN')
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
    const key = JSON.stringify([target.kind, target.kind === 'provider_model' ? target.connectionId : target.cliId, target.modelId])
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
    name: row.name, maskedSuffix: row.masked_suffix, validationState: row.validation_state })
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
async function ownedConnection(client: Client, userId: string, id: string) {
  return required((await client.query(`SELECT ${safeColumns},credential_version,credential_validity FROM ai_provider_connections
    WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL FOR NO KEY UPDATE`, [userId, id])).rows)
}
async function invalidateCatalog(client: Client, userId: string, id: string) {
  await client.query(`UPDATE ai_connection_models SET available=false
    WHERE connection_id=$2 AND EXISTS(SELECT 1 FROM ai_provider_connections WHERE user_id=$1 AND id=$2)`, [userId, id])
}
async function ownedConversation(client: Client, userId: string, conversationId: string) {
  const rows = (await client.query('SELECT id FROM conversations WHERE user_id=$1 AND id=$2 FOR NO KEY UPDATE', [userId, conversationId])).rows
  if (!rows.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
}

/** Validate exact current choices; never repair or substitute a missing target. */
async function assertTarget(client: Client, userId: string, target: RoleTarget, roles: readonly AiRole[]) {
  if (target.kind === 'provider_model') {
    const connection = await ownedConnection(client, userId, target.connectionId)
    if (connection.validation_state !== 'validated') throw new AiConsoleError('AI_CONNECTION_INVALID')
    const model = required((await client.query(`SELECT m.compatible_roles,m.available FROM ai_connection_models m
      JOIN ai_provider_connections c ON c.id=m.connection_id
      WHERE c.user_id=$1 AND c.id=$2 AND m.model_id=$3 AND m.available=true`, [userId, target.connectionId, target.modelId])).rows)
    if (!roles.every(role => model.compatible_roles.includes(role))) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
  } else {
    const model = (await client.query(`SELECT m.compatible_roles FROM ai_cli_grants g
      JOIN ai_cli_installations i ON i.cli_id=g.cli_id JOIN ai_cli_models m ON m.cli_id=g.cli_id
      WHERE g.user_id=$1 AND g.cli_id=$2 AND g.revoked_at IS NULL AND i.validation_state='reachable'
      AND m.available=true AND (($3::text IS NULL AND m.is_builtin_default) OR m.model_id=$3)
      FOR SHARE OF g,i,m`, [userId, target.cliId, target.modelId])).rows[0]
    if (!model) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
    if (!roles.every(role => model.compatible_roles.includes(role))) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
  }
}
async function assertChoice(client: Client, userId: string, choice: AiChoiceRef) {
  if (choice.kind !== 'custom_configuration') return assertTarget(client, userId, choice, AI_ROLES)
  required((await client.query(`SELECT id FROM ai_custom_configurations WHERE user_id=$1 AND id=$2
    AND deleted_at IS NULL FOR NO KEY UPDATE`, [userId, choice.configurationId])).rows)
  const rows = (await client.query(`SELECT role,kind,connection_id,model_id,cli_id FROM ai_custom_configuration_roles
    WHERE user_id=$1 AND configuration_id=$2 ORDER BY role`, [userId, choice.configurationId])).rows
  const assignments = RoleAssignmentsSchema.parse(Object.fromEntries(rows.map(row => [row.role, rowChoice(row)])))
  await assertAssignments(client, userId, assignments)
}

/** Explicit SQL projections also retain tombstones so broken references are explainable. */
export async function listAiConsoleState(userId: string) {
  const connections = await query(`SELECT ${safeColumns},credential_version,last_validated_at,last_checked_at,last_error_code,deleted_at
    FROM ai_provider_connections WHERE user_id=$1 ORDER BY created_at,id`, [userId])
  const models = await query(`SELECT m.connection_id,m.model_id,m.display_name,m.compatible_roles,m.available FROM ai_connection_models m
    JOIN ai_provider_connections c ON c.id=m.connection_id WHERE c.user_id=$1 ORDER BY m.connection_id,m.model_id`, [userId])
  const configurations = await query(`SELECT id,name,version,deleted_at FROM ai_custom_configurations WHERE user_id=$1 ORDER BY created_at,id`, [userId])
  const roles = await query(`SELECT configuration_id,role,kind,connection_id,model_id,cli_id FROM ai_custom_configuration_roles WHERE user_id=$1 ORDER BY configuration_id,role`, [userId])
  const defaults = await query('SELECT kind,connection_id,model_id,configuration_id,cli_id FROM ai_user_defaults WHERE user_id=$1', [userId])
  const clis = await query(`SELECT i.cli_id,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.detected_product END AS detected_product,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.detected_version END AS detected_version,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.validation_state END AS validation_state,
    CASE WHEN g.revoked_at IS NULL AND g.user_id IS NOT NULL THEN i.last_checked_at END AS last_checked_at,
    g.granted_at,g.revoked_at FROM ai_cli_installations i LEFT JOIN ai_cli_grants g ON g.cli_id=i.cli_id AND g.user_id=$1 ORDER BY i.cli_id`, [userId])
  const cliModels = await query(`SELECT m.cli_id,m.model_id,m.display_name,m.compatible_roles,m.available,m.is_builtin_default
    FROM ai_cli_models m JOIN ai_cli_grants g ON g.cli_id=m.cli_id WHERE g.user_id=$1 AND g.revoked_at IS NULL ORDER BY m.cli_id,m.model_id`, [userId])
  return { connections: connections.rows, models: models.rows, configurations: configurations.rows,
    roles: roles.rows, defaultChoice: defaults.rows[0] ? rowChoice(defaults.rows[0]) : null,
    clis: clis.rows, cliModels: cliModels.rows }
}

export async function createConnection(userId: string, input: unknown, encrypted: EncryptedCredential) {
  const data = z.object({ providerId: ProviderIdSchema, name: nameSchema }).strict().parse(input)
  return withUserTransaction(userId, async client => {
    const row = required((await client.query(`INSERT INTO ai_provider_connections
      (user_id,provider_id,name,credential_ciphertext,credential_nonce,credential_tag,wrapped_dek,wrap_nonce,wrap_tag,kek_version,masked_suffix,keyed_fingerprint)
      VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING ${safeColumns}`,
    [userId, data.providerId, data.name, ...credentialParams(encrypted)])).rows)
    await writeAiAudit(client, userId, { event: 'connection_created', connectionId: row.id })
    return safeConnection(row)
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
      credential_validity='unknown',validation_state='untested',last_validated_at=NULL,last_checked_at=NULL,last_error_code=NULL,updated_at=now()
      WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL RETURNING ${safeColumns},credential_version`,
    [userId, connectionId, ...credentialParams(encrypted)])).rows)
    await invalidateCatalog(client, userId, connectionId)
    await writeAiAudit(client, userId, { event: 'connection_credential_replaced', connectionId })
    return { connection: safeConnection(row), credentialVersion: Number(row.credential_version) }
  })
}
const ValidationSchema = z.object({
  credentialVersion: z.number().int().positive(),
  state: z.enum(['validated', 'needs_attention', 'invalid', 'unreachable', 'validating']),
  errorCode: z.enum(['AI_CONNECTION_INVALID', 'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE', 'AI_PROVIDER_UNREACHABLE',
    'AI_PERMISSION_DENIED', 'AI_BILLING_UNAVAILABLE', 'AI_RATE_LIMITED', 'AI_EXECUTION_FAILED']).optional(),
  models: z.array(z.object({ modelId: z.string().min(1), displayName: z.string().min(1), compatibleRoles: z.array(AiRoleSchema).min(1) }).strict()).optional(),
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
        await client.query(`INSERT INTO ai_connection_models(connection_id,model_id,display_name,compatible_roles,available)
          SELECT id,$3,$4,$5,true FROM ai_provider_connections WHERE user_id=$1 AND id=$2
          ON CONFLICT(connection_id,model_id) DO UPDATE SET display_name=excluded.display_name,
          compatible_roles=excluded.compatible_roles,available=true,last_seen_at=now()`,
        [userId, connectionId, model.modelId, model.displayName, model.compatibleRoles])
      }
    }
    await writeAiAudit(client, userId, { event: 'connection_validated', connectionId })
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
    await writeAiAudit(client, userId, { event: 'connection_validated', connectionId })
  })
}

const ConfigurationInput = z.object({ id: z.string().uuid().optional(), expectedVersion: z.number().int().positive().optional(),
  name: nameSchema, roles: RoleAssignmentsSchema }).strict().refine(v => !v.id || !!v.expectedVersion)
async function persistConfiguration(client: Client, userId: string, data: z.infer<typeof ConfigurationInput>, duplicate = false) {
  await assertAssignments(client, userId, data.roles)
  const row = data.id ? required((await client.query(`UPDATE ai_custom_configurations SET name=$3,version=version+1
    WHERE user_id=$1 AND id=$2 AND version=$4 AND deleted_at IS NULL RETURNING id,name,version`,
  [userId, data.id, data.name, data.expectedVersion])).rows)
    : required((await client.query('INSERT INTO ai_custom_configurations(user_id,name) VALUES($1,$2) RETURNING id,name,version', [userId, data.name])).rows)
  for (const role of AI_ROLES) {
    const target = data.roles[role]
    await client.query(`INSERT INTO ai_custom_configuration_roles(configuration_id,user_id,role,kind,connection_id,model_id,cli_id)
      SELECT id,user_id,$3,$4,$5,$6,$7 FROM ai_custom_configurations WHERE user_id=$1 AND id=$2
      ON CONFLICT(configuration_id,role) DO UPDATE SET kind=excluded.kind,connection_id=excluded.connection_id,
      model_id=excluded.model_id,cli_id=excluded.cli_id WHERE ai_custom_configuration_roles.user_id=$1`,
    [userId, row.id, role, target.kind, target.kind === 'provider_model' ? target.connectionId : null, target.modelId,
      target.kind === 'local_cli' ? target.cliId : null])
  }
  await writeAiAudit(client, userId, { event: duplicate ? 'configuration_duplicated' : data.id ? 'configuration_updated' : 'configuration_created', configurationId: row.id, configurationVersion: Number(row.version) })
  return { id: row.id as string, name: row.name as string, version: Number(row.version), roles: data.roles }
}
export async function saveConfiguration(userId: string, input: unknown) {
  const data = ConfigurationInput.parse(input)
  return withUserTransaction(userId, client => persistConfiguration(client, userId, data))
}
export async function duplicateConfiguration(userId: string, configurationId: string, name: string) {
  const parsed = nameSchema.parse(name)
  return withUserTransaction(userId, async client => {
    required((await client.query('SELECT id FROM ai_custom_configurations WHERE user_id=$1 AND id=$2 AND deleted_at IS NULL FOR NO KEY UPDATE', [userId, configurationId])).rows)
    const rows = (await client.query('SELECT role,kind,connection_id,model_id,cli_id FROM ai_custom_configuration_roles WHERE user_id=$1 AND configuration_id=$2', [userId, configurationId])).rows
    return persistConfiguration(client, userId, { name: parsed, roles: RoleAssignmentsSchema.parse(Object.fromEntries(rows.map(row => [row.role, rowChoice(row)]))) }, true)
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
export async function loadConnectionCredential(userId: string, connectionId: string, credentialVersion: number): Promise<EncryptedCredential> {
  const row = required((await query(`SELECT c.credential_ciphertext,c.credential_nonce,c.credential_tag,c.wrapped_dek,
    c.wrap_nonce,c.wrap_tag,c.kek_version,c.masked_suffix,c.keyed_fingerprint FROM ai_provider_connections c
    JOIN profiles p ON p.id=c.user_id WHERE c.user_id=$1 AND c.id=$2 AND c.credential_version=$3
    AND c.deleted_at IS NULL AND p.status='active'`, [userId, connectionId, credentialVersion])).rows)
  const record: EncryptedCredential = { ciphertext: row.credential_ciphertext, nonce: row.credential_nonce,
    authTag: row.credential_tag, wrappedDataKey: row.wrapped_dek, wrapNonce: row.wrap_nonce,
    wrapAuthTag: row.wrap_tag, keyVersion: row.kek_version, mask: row.masked_suffix, fingerprint: row.keyed_fingerprint }
  Object.defineProperties(record, { toJSON: { value: () => '[REDACTED]' }, [inspect.custom]: { value: () => '[REDACTED]' } })
  return record
}

export interface CliInvocationHandle {
  readonly pid: number
  cancel(): void | Promise<void>
}

/**
 * Synchronous process creation/handle acquisition only; never await model completion.
 * The handle stays outside the transaction so failure after spawn (including COMMIT)
 * cancels the started process exactly once. No callback or transaction retry occurs.
 */
export async function withCliInvocationAuthorization<T extends CliInvocationHandle>(userId: string, cliId: string, start: () => T): Promise<T> {
  const cli = CliIdSchema.parse(cliId)
  if (typeof start !== 'function' || utilTypes.isAsyncFunction(start)) throw new AiConsoleError('AI_EXECUTION_FAILED')
  let started: T | undefined
  try {
    return await withUserTransaction(userId, async client => {
      const rows = (await client.query(`SELECT g.cli_id FROM ai_cli_grants g JOIN profiles p ON p.id=g.user_id
        JOIN ai_cli_installations i ON i.cli_id=g.cli_id WHERE g.user_id=$1 AND g.cli_id=$2
        AND g.revoked_at IS NULL AND p.status='active' AND i.validation_state='reachable' FOR SHARE OF g,p,i`, [userId, cli])).rows
      if (!rows.length) throw new AiConsoleError('AI_CLI_NOT_GRANTED')
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

export async function insertRoutingSnapshot(input: unknown): Promise<string> {
  const snapshot = RoutingSnapshotSchema.parse(input)
  return withUserTransaction(snapshot.userId, async client => {
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
  })
}
const ReceiptSchema = z.object({ userId: z.string().min(1), snapshotId: z.string().uuid(), role: AiRoleSchema,
  phase: z.enum(['start', 'terminal']), status: z.enum(['started', 'succeeded', 'failed', 'cancelled']), errorCode: AiErrorCodeSchema.optional(),
}).strict().refine(r => r.phase === 'start' ? r.status === 'started' && !r.errorCode : r.status !== 'started' && (r.status !== 'succeeded' || !r.errorCode))
export async function insertRoleInvocationReceipt(input: unknown): Promise<void> {
  const receipt = ReceiptSchema.parse(input)
  return withUserTransaction(receipt.userId, async client => {
    const owner = (await client.query('SELECT id FROM ai_turn_routing_snapshots WHERE user_id=$1 AND id=$2', [receipt.userId, receipt.snapshotId])).rows
    if (!owner.length) throw new AiConsoleError('AI_PERMISSION_DENIED')
    if (receipt.phase === 'terminal') {
      required((await client.query(`SELECT r.status FROM ai_turn_role_invocations r JOIN ai_turn_routing_snapshots s ON s.id=r.snapshot_id
        WHERE s.user_id=$1 AND s.id=$2 AND r.role=$3 AND r.phase='start'`, [receipt.userId, receipt.snapshotId, receipt.role])).rows)
    }
    const inserted = await client.query(`INSERT INTO ai_turn_role_invocations(snapshot_id,role,phase,status,error_code)
      SELECT id,$3,$4,$5,$6 FROM ai_turn_routing_snapshots WHERE user_id=$1 AND id=$2
      ON CONFLICT(snapshot_id,role,phase) DO NOTHING RETURNING status`,
    [receipt.userId, receipt.snapshotId, receipt.role, receipt.phase, receipt.status, receipt.errorCode ?? null])
    if (!inserted.rows.length) {
      const row = required((await client.query(`SELECT r.status,r.error_code FROM ai_turn_role_invocations r
        JOIN ai_turn_routing_snapshots s ON s.id=r.snapshot_id WHERE s.user_id=$1 AND s.id=$2 AND r.role=$3 AND r.phase=$4`,
      [receipt.userId, receipt.snapshotId, receipt.role, receipt.phase])).rows)
      if (row.status !== receipt.status || row.error_code !== (receipt.errorCode ?? null)) throw notFound()
    }
  })
}
