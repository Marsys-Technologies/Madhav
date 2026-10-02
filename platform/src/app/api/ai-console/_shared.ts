import 'server-only'
import { NextResponse } from 'next/server'
import { z } from 'zod'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { getFlag } from '@/lib/config'
import { checkRpm } from '@/lib/mcp/rate_limiter_core'
import { AiConsoleError, AiErrorCodeSchema, normalizeAiError, type AiErrorCode } from '@/lib/ai-console/errors'
import { listAiConsoleState, previewChoiceDependencies } from '@/lib/ai-console/repository'
import {
  AiChoiceRefSchema, AiRoleSchema, CliIdSchema, CustomConfigurationChoiceSchema, LocalCliChoiceSchema,
  ProviderModelChoiceSchema, ProviderModelSchema, RoleAssignmentsSchema,
  RoleTargetSchema, SafeProviderConnectionSchema, type SafeProviderConnection,
} from '@/lib/ai-console/types'
import type { ValidationResult } from '@/lib/ai-console/validation'
import { CLI_REGISTRY } from '@/lib/ai-console/cli/registry'
import { configurationKindMatchesRoles } from '@/lib/ai-console/configuration-kind'

export const VALIDATION_DISCLOSURE = 'Testing this connection makes a tiny generation request and may incur a tiny provider charge.'
export const NameSchema = z.string().trim().min(1).max(120)
export const IdSchema = z.string().uuid()
// Persistence IDs are UUIDs even though the shared routing identity contract is more general.
const ProviderInputSchema = ProviderModelChoiceSchema.extend({ connectionId: IdSchema })
const RoleInputSchema = z.discriminatedUnion('kind', [ProviderInputSchema, LocalCliChoiceSchema])
export const ChoiceInputSchema = z.discriminatedUnion('kind', [ProviderInputSchema, LocalCliChoiceSchema,
  CustomConfigurationChoiceSchema.extend({ configurationId: IdSchema })])
export const AssignmentsInputSchema = RoleAssignmentsSchema.extend({ synthesizer: RoleInputSchema,
  planner: RoleInputSchema, deep_planner: RoleInputSchema, worker: RoleInputSchema })
const ConfigurationKindInputSchema = z.enum(['provider_preset', 'cli_preset', 'custom_api', 'custom_cli'])
export const ConfigurationScopeInputSchema = z.object({
  configurationKind: ConfigurationKindInputSchema.optional(),
  ownerConnectionId: IdSchema.nullable().optional(),
  ownerCliId: CliIdSchema.nullable().optional(),
})
export function validConfigurationScope(input: { roles: z.infer<typeof AssignmentsInputSchema>;
  configurationKind?: z.infer<typeof ConfigurationKindInputSchema>;
  ownerConnectionId?: string | null; ownerCliId?: z.infer<typeof CliIdSchema> | null }) {
  const kind = input.configurationKind ?? (Object.values(input.roles).every(role => role.kind === 'provider_model')
    ? 'custom_api' : 'custom_cli')
  return configurationKindMatchesRoles(kind, input.roles, input.ownerConnectionId ?? null, input.ownerCliId ?? null)
}
// Provider formats vary; reject only impossible input, never infer validity from syntax.
export const CredentialSchema = z.string().min(1).max(4096).regex(/^[\x21-\x7e]+$/)
export const ChargeSchema = z.object({ acknowledgeCharge: z.literal(true) }).strict()
export const DeleteSchema = z.object({ confirm: z.boolean().optional() }).strict()
export type IdContext = { params: Promise<{ id: string }> }
export type CliContext = { params: Promise<{ cliId: string }> }
type Row = Record<string, unknown>
type ConsoleState = Awaited<ReturnType<typeof listAiConsoleState>>

class RequestError extends Error {
  constructor(readonly status: number, readonly publicCode: string, readonly retryAfter?: number) { super(publicCode) }
}

const MUTATION_RPM_LIMIT = 30
const VALIDATION_RPM_LIMIT = 3
const MAX_BODY_BYTES = 16 * 1024
// Both checkRpm and this admission set are process-local: restart resets them;
// multi-instance deployment requires shared coordination for a global guarantee.
const validationFlights = new Set<string>()

function checkRate(key: string, limit: number) {
  const result = checkRpm(key, limit)
  if (!result.allowed) throw new RequestError(429, 'rate_limited', result.retry_after_seconds ?? 60)
}

export function checkAiConsoleMutationRate(userId: string, scope = 'mutation') {
  checkRate(`ai-console:${scope}:${userId}`, MUTATION_RPM_LIMIT)
}

/** Synchronous alias reservation; does not consume an additional validation RPM token. */
export function reserveValidationFlight(userId: string, target: string): () => void {
  const key = JSON.stringify([userId, target])
  if (validationFlights.has(key)) throw new RequestError(429, 'rate_limited', 30)
  validationFlights.add(key)
  let released = false
  return () => {
    if (released) return
    released = true
    validationFlights.delete(key)
  }
}

/** Covers the entire mutation plus probe, so rejection cannot leave a changed key. */
export async function withValidationAdmission<T>(userId: string, target: string, work: () => Promise<T>): Promise<T> {
  const release = reserveValidationFlight(userId, target)
  try {
    checkRate(`ai-console:validation:${userId}`, VALIDATION_RPM_LIMIT)
    return await work()
  } finally { release() }
}

/** CLI installation state is host-global, so users share one process-local flight per CLI. */
export async function withCliValidationAdmission<T>(userId: string, cliId: string,
  work: () => Promise<T>): Promise<T> {
  const release = reserveValidationFlight('host-cli', cliId)
  try {
    checkRate(`ai-console:validation:${userId}`, VALIDATION_RPM_LIMIT)
    return await work()
  } finally { release() }
}

export function json(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: { 'Cache-Control': 'no-store' } })
}

const ERROR_STATUS: Record<AiErrorCode, number> = {
  AI_DEFAULT_REQUIRED: 409, AI_CHOICE_BROKEN: 409, AI_CONNECTION_INVALID: 422,
  AI_MODEL_UNAVAILABLE: 422, AI_ROLE_INCOMPATIBLE: 422, AI_CLI_NOT_GRANTED: 403,
  AI_CLI_UNREACHABLE: 503, AI_PROVIDER_UNREACHABLE: 503, AI_PERMISSION_DENIED: 403,
  AI_BILLING_UNAVAILABLE: 402, AI_RATE_LIMITED: 429, AI_CLI_NOT_INSTALLED: 503,
  AI_CLI_AUTH_UNAVAILABLE: 503, AI_CLI_TIMEOUT: 504, AI_CLI_OUTPUT_LIMIT: 422,
  AI_EXECUTION_FAILED: 500,
}

/** All handlers, including failures in authentication, share this non-logging boundary. */
export async function withAiConsole(work: (userId: string) => Promise<NextResponse>, mutation = false) {
  try {
    if (!getFlag('AI_CONSOLE_BYOK')) return json({ error: 'not_found' }, 404)
    const auth = await getServerUserWithProfile()
    if (!auth) return json({ error: 'unauthorized' }, 401)
    if (auth.profile.status !== 'active') return json({ error: 'account_inactive' }, 403)
    if (mutation) checkAiConsoleMutationRate(auth.user.uid)
    return await work(auth.user.uid)
  } catch (error) {
    if (error instanceof RequestError) {
      const response = json({ error: error.publicCode }, error.status)
      if (error.retryAfter !== undefined) response.headers.set('Retry-After', String(Math.max(1, Math.ceil(error.retryAfter))))
      return response
    }
    if (error instanceof AiConsoleError) {
      const safe = normalizeAiError(error, { source: 'provider' })
      return json({ error: safe }, ERROR_STATUS[safe.code])
    }
    // Database constraint details can contain submitted secrets. Read only the SQLSTATE.
    if (typeof error === 'object' && error !== null && 'code' in error && error.code === '23505') {
      return json({ error: 'name_conflict', message: 'Choose a different name.' }, 409)
    }
    return json({ error: normalizeAiError(new AiConsoleError('AI_EXECUTION_FAILED'), { source: 'provider' }) }, 500)
  }
}

export function requestErrorResponse(error: unknown): NextResponse | null {
  if (!(error instanceof RequestError)) return null
  const response = json({ error: error.publicCode }, error.status)
  if (error.retryAfter !== undefined) response.headers.set('Retry-After', String(Math.max(1, Math.ceil(error.retryAfter))))
  return response
}

export function withAiConsoleMutation(work: (userId: string) => Promise<NextResponse>) {
  return withAiConsole(work, true)
}

/** Count raw bytes (including whitespace), never trusting a declared length alone. */
async function readBoundedText(request: Request): Promise<string> {
  const declared = request.headers.get('content-length')
  let expected: number | undefined
  if (declared !== null) {
    expected = Number(declared)
    // A syntactically valid huge integer is oversize even beyond JS's safe range.
    const valid = /^\d+$/.test(declared)
    if (!valid || expected > MAX_BODY_BYTES) {
      await request.body?.cancel().catch(() => {})
      throw new RequestError(valid ? 413 : 400, valid ? 'request_too_large' : 'invalid_request')
    }
  }
  const reader = request.body?.getReader()
  if (!reader) {
    if (expected !== undefined && expected !== 0) throw new RequestError(400, 'invalid_request')
    return ''
  }
  try {
    const bytes = new Uint8Array(MAX_BODY_BYTES)
    let size = 0
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      if (value.byteLength > MAX_BODY_BYTES - size) throw new RequestError(413, 'request_too_large')
      bytes.set(value, size)
      size += value.byteLength
    }
    if (expected !== undefined && expected !== size) throw new RequestError(400, 'invalid_request')
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes.subarray(0, size))
  } catch (error) {
    await reader.cancel().catch(() => {})
    if (error instanceof RequestError) throw error
    throw new RequestError(400, 'invalid_request')
  } finally { reader.releaseLock() }
}

/** Zod issues can contain user-supplied values/field names; never serialize them. */
export async function readBody<T>(request: Request, schema: z.ZodType<T>, allowEmpty = false): Promise<T> {
  let value: unknown
  try {
    const text = await readBoundedText(request)
    value = allowEmpty && text.length === 0 ? {} : JSON.parse(text)
  } catch (error) {
    if (error instanceof RequestError) throw error
    throw new RequestError(400, 'invalid_request')
  }
  const parsed = schema.safeParse(value)
  if (!parsed.success) throw new RequestError(400, 'invalid_request')
  return parsed.data
}

export async function readId(context: IdContext) {
  const parsed = IdSchema.safeParse((await context.params).id)
  if (!parsed.success) throw new RequestError(400, 'invalid_request')
  return parsed.data
}
export async function readCliId(context: CliContext) {
  const parsed = CliIdSchema.safeParse((await context.params).cliId)
  if (!parsed.success) throw new RequestError(400, 'invalid_request')
  return parsed.data
}

const date = (value: unknown) => {
  if (value == null) return null
  if (value instanceof Date) return value.toISOString()
  const raw = z.string().min(1).parse(value)
  const alreadyIso = z.string().datetime({ offset: true }).safeParse(raw)
  if (alreadyIso.success) return alreadyIso.data
  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) throw new RequestError(500, 'invalid_timestamp')
  return parsed.toISOString()
}
const text = (value: unknown) => z.string().min(1).parse(value)
const nullableText = (value: unknown) => value == null ? null : text(value)

export function projectConnection(connection: SafeProviderConnection) {
  return SafeProviderConnectionSchema.parse({ id: connection.id, providerId: connection.providerId,
    name: connection.name, ...(connection.workspaceId ? { workspaceId: connection.workspaceId } : {}),
    maskedSuffix: connection.maskedSuffix, validationState: connection.validationState,
    confirmedValid: connection.confirmedValid })
}
function projectConnectionRow(row: Row) {
  return { ...projectConnection({ id: row.id, providerId: row.provider_id, name: row.name,
    ...(row.anthropic_workspace_id ? { workspaceId: row.anthropic_workspace_id } : {}),
    maskedSuffix: row.masked_suffix, validationState: row.validation_state,
    confirmedValid: row.credential_validity === 'valid' } as SafeProviderConnection),
  lastValidatedAt: date(row.last_validated_at), lastCheckedAt: date(row.last_checked_at),
  lastErrorCode: row.last_error_code == null ? null : AiErrorCodeSchema.parse(row.last_error_code), deletedAt: date(row.deleted_at) }
}

function projectRole(row: Row) {
  return RoleTargetSchema.parse(row.kind === 'provider_model'
    ? { kind: row.kind, connectionId: row.connection_id, modelId: row.model_id,
      ...(row.effort == null ? {} : { effort: row.effort }) }
    : { kind: row.kind, cliId: row.cli_id, modelId: row.model_id,
      ...(row.effort == null ? {} : { effort: row.effort }) })
}
export function projectConfiguration(input: { id: unknown; name: unknown; version: unknown; roles: unknown;
  configurationKind: unknown; ownerConnectionId: unknown; ownerCliId: unknown }) {
  return { id: IdSchema.parse(input.id), name: NameSchema.parse(input.name),
    version: z.coerce.number().int().positive().parse(input.version), roles: RoleAssignmentsSchema.parse(input.roles),
    configurationKind: z.enum(['provider_preset', 'cli_preset', 'custom_api', 'custom_cli', 'legacy_mixed']).parse(input.configurationKind),
    ownerConnectionId: input.ownerConnectionId == null ? null : IdSchema.parse(input.ownerConnectionId),
    ownerCliId: input.ownerCliId == null ? null : CliIdSchema.parse(input.ownerCliId) }
}

/** Explicit fields at every level; never return repository rows or spread a credential. */
export function projectState(state: ConsoleState) {
  return {
    connections: state.connections.map(projectConnectionRow),
    models: state.models.map(row => ProviderModelSchema.parse({ connectionId: row.connection_id,
      modelId: row.model_id, displayName: row.display_name, compatibleRoles: row.compatible_roles,
      supportsTools: row.supports_tools, supportsStructuredOutput: row.supports_structured_output,
      available: row.available, userSelected: row.user_selected === true,
      plainTestedAt: row.tested_credential_version != null
        && Number(row.tested_credential_version) === Number(row.current_credential_version)
        ? date(row.plain_tested_at) : null,
      lastProbeAt: date(row.last_probe_at), lastProbeErrorCode: row.last_probe_error_code == null
        ? null : AiErrorCodeSchema.parse(row.last_probe_error_code),
      lastProbeInputTokens: row.last_probe_input_tokens == null ? null
        : z.coerce.number().int().nonnegative().parse(row.last_probe_input_tokens),
      lastProbeOutputTokens: row.last_probe_output_tokens == null ? null
        : z.coerce.number().int().nonnegative().parse(row.last_probe_output_tokens) })),
    configurations: state.configurations.map(row => ({ ...projectConfiguration({ id: row.id, name: row.name, version: row.version,
      configurationKind: row.configuration_kind, ownerConnectionId: row.owner_connection_id, ownerCliId: row.owner_cli_id,
      roles: Object.fromEntries(state.roles.filter(role => role.configuration_id === row.id).map(role => [AiRoleSchema.parse(role.role), projectRole(role)])) }),
    deletedAt: date(row.deleted_at) })),
    defaultChoice: state.defaultChoice === null ? null : AiChoiceRefSchema.parse(state.defaultChoice),
    clis: state.clis.map(row => {
      const granted = row.granted_at != null && row.revoked_at == null
      return { cliId: CliIdSchema.parse(row.cli_id), granted,
        detectedProduct: granted ? nullableText(row.detected_product) : null,
        detectedVersion: granted ? nullableText(row.detected_version) : null,
        validationState: granted ? nullableText(row.validation_state) : null,
        lastCheckedAt: granted ? date(row.last_checked_at) : null }
    }),
    cliModels: state.cliModels.filter(model => CLI_REGISTRY[CliIdSchema.parse(model.cli_id)].execution
      && state.clis.some(cli => cli.cli_id === model.cli_id && cli.granted_at != null
        && cli.revoked_at == null && cli.validation_state === 'reachable'))
      .map(row => ({ cliId: CliIdSchema.parse(row.cli_id), modelId: row.is_builtin_default ? null : text(row.model_id), displayName: text(row.display_name),
        compatibleRoles: z.array(AiRoleSchema).min(1).parse(row.compatible_roles), available: z.boolean().parse(row.available),
        supportsTools: z.boolean().parse(row.supports_tools),
        supportsStructuredOutput: z.boolean().parse(row.supports_structured_output),
        isBuiltinDefault: z.boolean().parse(row.is_builtin_default) })),
    validationDisclosure: VALIDATION_DISCLOSURE,
  }
}

export function projectCliCards(state: ConsoleState) {
  return state.clis.map(row => {
    const cliId = CliIdSchema.parse(row.cli_id)
    const productName = CLI_REGISTRY[cliId].productName
    const executable = CLI_REGISTRY[cliId].execution !== undefined
    const granted = row.granted_at != null && row.revoked_at == null
    if (!granted) return { cliId, productName, state: 'not_granted' as const }
    const validationState = z.enum(['untested', 'validating', 'reachable', 'not_installed', 'auth_unavailable',
      'unreachable', 'needs_attention']).parse(row.validation_state ?? 'untested')
    const models = executable && validationState === 'reachable'
      ? state.cliModels.filter(model => model.cli_id === cliId && model.available === true).map(model => ({
      modelId: model.is_builtin_default ? null : text(model.model_id), displayName: text(model.display_name),
      compatibleRoles: z.array(AiRoleSchema).min(1).parse(model.compatible_roles),
      supportsTools: z.boolean().parse(model.supports_tools),
      supportsStructuredOutput: z.boolean().parse(model.supports_structured_output),
      isBuiltinDefault: z.boolean().parse(model.is_builtin_default),
      })) : []
    return { cliId, productName, state: executable ? validationState : 'needs_attention' as const,
      detectedProduct: nullableText(row.detected_product),
      detectedVersion: nullableText(row.detected_version), lastCheckedAt: date(row.last_checked_at), models }
  })
}

export async function ownedConnection(userId: string, id: string) {
  const state = await listAiConsoleState(userId)
  const row = state.connections.find(row => row.id === id && !row.deleted_at)
  if (!row) throw new RequestError(404, 'not_found')
  return { connection: projectConnectionRow(row), credentialVersion: z.coerce.number().int().positive().parse(row.credential_version) }
}
export async function ownedConfiguration(userId: string, id: string) {
  const state = projectState(await listAiConsoleState(userId))
  const configuration = state.configurations.find(row => row.id === id && !row.deletedAt)
  if (!configuration) throw new RequestError(404, 'not_found')
  return configuration
}

export function projectValidation(result: ValidationResult) {
  const error = result.error ? normalizeAiError(new AiConsoleError(AiErrorCodeSchema.parse(result.error.code), result.error.role), { source: 'provider' }) : undefined
  return { state: z.enum(['validated', 'needs_attention', 'invalid', 'unreachable']).parse(result.state),
    modelCount: z.number().int().nonnegative().parse(result.modelCount), ...(error ? { error } : {}) }
}

export async function dependencyPreview(userId: string, kind: 'connection' | 'configuration', id: string) {
  const choice = kind === 'connection'
    // Dependency discovery is connection-wide; this model label is never resolved or stored.
    ? { kind: 'provider_model', connectionId: id, modelId: '*' }
    : { kind: 'custom_configuration', configurationId: id }
  const dependencies = await previewChoiceDependencies(userId, choice)
  return { configurations: dependencies.configurations.map(row => ({ id: IdSchema.parse(row.id), name: NameSchema.parse(row.name) })),
    defaultAffected: z.boolean().parse(dependencies.defaultAffected),
    conversations: dependencies.conversations.map(row => ({ conversationId: IdSchema.parse(row.conversation_id) })) }
}
