import { isDeepStrictEqual } from 'node:util'
import { z } from 'zod'

const RoleSchema = z.enum(['synthesizer', 'planner', 'deep_planner', 'worker'])
const ProviderTargetSchema = z.object({
  kind: z.literal('provider_model'), providerId: z.string().min(1), connectionId: z.string().min(1), modelId: z.string().min(1),
}).strict()
const CliTargetSchema = z.object({
  kind: z.literal('local_cli'), cliId: z.string().min(1), modelId: z.string().nullable(),
}).strict()
const TargetSchema = z.discriminatedUnion('kind', [ProviderTargetSchema, CliTargetSchema])
const ChoiceSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('provider_model'), connectionId: z.string().min(1), modelId: z.string().min(1) }).strict(),
  z.object({ kind: z.literal('custom_configuration'), configurationId: z.string().min(1) }).strict(),
  z.object({ kind: z.literal('local_cli'), cliId: z.string().min(1), modelId: z.string().nullable() }).strict(),
])
const SelectionSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('default') }).strict(),
  z.object({ kind: z.literal('explicit'), choice: ChoiceSchema }).strict(),
])
const RolesSchema = z.object({
  synthesizer: TargetSchema, planner: TargetSchema, deep_planner: TargetSchema, worker: TargetSchema,
}).strict()
const EvidenceSchema = z.object({
  userId: z.string().min(1), correlationId: z.string().min(1), selection: SelectionSchema,
  resolvedChoice: ChoiceSchema, roles: RolesSchema,
  invocations: z.array(z.object({ role: RoleSchema, status: z.literal('succeeded') }).strict()).min(2),
  observatory: z.array(z.object({
    role: RoleSchema, providerId: z.string().min(1), modelId: z.string().nullable(),
    fallbackUsed: z.literal(false), status: z.literal('success'),
  }).strict()).min(2),
}).strict()

export type SafeRoleTarget = z.infer<typeof TargetSchema>
export type SafeRoleMap = z.infer<typeof RolesSchema>
export type SafeSelection = z.infer<typeof SelectionSchema>

function sseData(text: string): unknown[] {
  const values: unknown[] = []
  for (const line of text.split('\n')) {
    if (!line.startsWith('data: ')) continue
    try { values.push(JSON.parse(line.slice(6))) } catch { throw new Error('AIC_E2E_TERMINAL_EVENT_INVALID') }
  }
  return values
}

export function parsePariprashnaTerminal(text: string): string {
  const events = sseData(text) as Array<Record<string, unknown>>
  const indexes = (type: string) => events.flatMap((event, index) => event.type === type ? [index] : [])
  const opens = indexes('turn.open')
  const contents = events.flatMap((event, index) => ['block.delta', 'block.commit'].includes(String(event.type)) ? [index] : [])
  const commits = indexes('turn.commit')
  const persistedEvents = indexes('turn.persisted')
  const closes = indexes('turn.close')
  const opened = events[opens[0]]
  const committed = events[commits[0]]
  const persisted = events[persistedEvents.at(-1) ?? -1]
  const terminal = events[closes[0]]
  if (opens.length !== 1 || commits.length !== 1 || closes.length !== 1 || contents.length === 0
    || persistedEvents.length === 0 || opens[0] !== 0 || !(opens[0] < contents[0] && contents.at(-1)! < commits[0]
      && commits[0] < persistedEvents[0] && persistedEvents.at(-1)! < closes[0])
    || !opened || !terminal || terminal.status !== 'ok' || typeof opened.turn_id !== 'string'
    || terminal.turn_id !== opened.turn_id || events.at(-1) !== terminal
    || !committed || committed.status !== 'ok' || committed.turn_id !== opened.turn_id
    || !persisted || persisted.status !== 'durable' || persisted.turn_id !== opened.turn_id
    || persistedEvents.some(index => events[index].turn_id !== opened.turn_id)
    || events.some(event => event.type === 'error')) throw new Error('AIC_E2E_TURN_NOT_SUCCESSFUL')
  return opened.turn_id
}

export function parseConsultTerminal(text: string): true {
  const events = sseData(text) as Array<Record<string, unknown>>
  const finishes = events.filter(event => event.type === 'finish')
  if (finishes.length !== 1 || finishes[0].finishReason !== 'stop' || events.at(-1) !== finishes[0]
    || events.some(event => event.type === 'error')) {
    throw new Error('AIC_E2E_TERMINAL_EVENT_MISSING')
  }
  return true
}

export function assertSafeRoutingEvidence(
  input: unknown,
  expected: { readonly userId: string; readonly correlationId: string; readonly selection: SafeSelection;
    readonly resolvedChoice: z.infer<typeof ChoiceSchema>; readonly roles: SafeRoleMap },
): true {
  const parsed = EvidenceSchema.safeParse(input)
  if (!parsed.success) throw new Error('AIC_E2E_ROUTING_EVIDENCE_INVALID')
  const evidence = parsed.data
  if (evidence.userId !== expected.userId || evidence.correlationId !== expected.correlationId
    || !isDeepStrictEqual(evidence.selection, expected.selection)
    || !isDeepStrictEqual(evidence.resolvedChoice, expected.resolvedChoice)
    || !isDeepStrictEqual(evidence.roles, expected.roles)) {
    throw new Error('AIC_E2E_ROUTING_EVIDENCE_INVALID')
  }
  const invokedRoles = new Set(evidence.invocations.map(row => row.role))
  if (!invokedRoles.has('planner') || !invokedRoles.has('synthesizer')
    || invokedRoles.size !== evidence.invocations.length || evidence.observatory.length !== invokedRoles.size) {
    throw new Error('AIC_E2E_ROUTING_EVIDENCE_INVALID')
  }
  for (const row of evidence.observatory) {
    const target = expected.roles[row.role]
    const providerId =
      target.kind === 'local_cli'
        ? 'cli'
        : target.providerId === 'google'
          ? 'gemini'
          : target.providerId
    if (row.providerId !== providerId || row.modelId !== target.modelId || row.fallbackUsed !== false) {
      throw new Error('AIC_E2E_ROUTING_EVIDENCE_INVALID')
    }
  }
  const observedRoles = new Set(evidence.observatory.map(row => row.role))
  if (observedRoles.size !== evidence.observatory.length || observedRoles.size !== invokedRoles.size
    || [...invokedRoles].some(role => !observedRoles.has(role))) {
    throw new Error('AIC_E2E_ROUTING_EVIDENCE_INVALID')
  }
  return true
}
