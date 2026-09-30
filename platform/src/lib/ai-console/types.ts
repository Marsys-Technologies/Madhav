/** Shared, strict data contracts only. Credentials and executable bindings stay server-only. */
import { z } from 'zod'

export const AI_ROLES = ['synthesizer', 'planner', 'deep_planner', 'worker'] as const
export const PROVIDER_IDS = ['openai', 'anthropic', 'google', 'xai', 'deepseek', 'kimi', 'openrouter'] as const
export const CLI_IDS = ['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'] as const

export const AiRoleSchema = z.enum(AI_ROLES)
export const ProviderIdSchema = z.enum(PROVIDER_IDS)
export const CliIdSchema = z.enum(CLI_IDS)
export type AiRole = z.infer<typeof AiRoleSchema>
export type ProviderId = z.infer<typeof ProviderIdSchema>
export type CliId = z.infer<typeof CliIdSchema>

const IdentifierSchema = z.string().min(1).regex(/\S/)
export const ProviderModelChoiceSchema = z.object({
  kind: z.literal('provider_model'),
  connectionId: IdentifierSchema,
  modelId: IdentifierSchema,
}).strict()
export const CustomConfigurationChoiceSchema = z.object({
  kind: z.literal('custom_configuration'),
  configurationId: IdentifierSchema,
}).strict()
export const LocalCliChoiceSchema = z.object({
  kind: z.literal('local_cli'),
  cliId: CliIdSchema,
  // null means the adapter's explicitly discovered built-in default model.
  modelId: IdentifierSchema.nullable(),
}).strict()

export const AiChoiceRefSchema = z.discriminatedUnion('kind', [
  ProviderModelChoiceSchema, CustomConfigurationChoiceSchema, LocalCliChoiceSchema,
])
export type AiChoiceRef = z.infer<typeof AiChoiceRefSchema>

export const ConversationAiSelectionSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('default') }).strict(),
  z.object({ kind: z.literal('explicit'), choice: AiChoiceRefSchema }).strict(),
])
export type ConversationAiSelection = z.infer<typeof ConversationAiSelectionSchema>

// Configurations cannot recursively reference another configuration.
export const RoleTargetSchema = z.discriminatedUnion('kind', [ProviderModelChoiceSchema, LocalCliChoiceSchema])
export type RoleTarget = z.infer<typeof RoleTargetSchema>
export const RoleAssignmentsSchema = z.object({
  synthesizer: RoleTargetSchema,
  planner: RoleTargetSchema,
  deep_planner: RoleTargetSchema,
  worker: RoleTargetSchema,
}).strict()
export type RoleAssignments = z.infer<typeof RoleAssignmentsSchema>

export const CONNECTION_VALIDATION_STATES = [
  'untested', 'validating', 'validated', 'needs_attention', 'invalid', 'unreachable',
] as const
export const ConnectionValidationStateSchema = z.enum(CONNECTION_VALIDATION_STATES)
export type ConnectionValidationState = z.infer<typeof ConnectionValidationStateSchema>

/** Explicit projections: never spread a persisted credential record into these objects. */
export const SafeProviderConnectionSchema = z.object({
  id: IdentifierSchema,
  providerId: ProviderIdSchema,
  workspaceId: z.string().regex(/^wrkspc_[A-Za-z0-9]{20,64}$/).optional(),
  name: IdentifierSchema,
  maskedSuffix: IdentifierSchema,
  validationState: ConnectionValidationStateSchema,
  confirmedValid: z.boolean(),
}).strict()
export type SafeProviderConnection = z.infer<typeof SafeProviderConnectionSchema>

export const ProviderModelSchema = z.object({
  connectionId: IdentifierSchema,
  modelId: IdentifierSchema,
  displayName: IdentifierSchema,
  compatibleRoles: z.array(AiRoleSchema).min(1),
  supportsTools: z.boolean(),
  supportsStructuredOutput: z.boolean(),
  available: z.boolean(),
  userSelected: z.boolean().optional(),
  plainTestedAt: z.string().nullable().optional(),
  lastProbeAt: z.string().nullable().optional(),
  lastProbeErrorCode: z.string().nullable().optional(),
  lastProbeInputTokens: z.number().int().nonnegative().nullable().optional(),
  lastProbeOutputTokens: z.number().int().nonnegative().nullable().optional(),
}).strict()
export type ProviderModel = z.infer<typeof ProviderModelSchema>

export const AiSourceSchema = z.enum(['pariprashna', 'mcp', 'backend'])
export type AiSource = z.infer<typeof AiSourceSchema>
export const ResolvedRoleTargetSchema = z.discriminatedUnion('kind', [
  ProviderModelChoiceSchema.extend({ providerId: ProviderIdSchema }).strict(),
  LocalCliChoiceSchema,
]).readonly()
export type ResolvedRoleTarget = z.infer<typeof ResolvedRoleTargetSchema>

// Freeze each nested object: Zod's readonly() alone freezes only its immediate result.
const SnapshotSelectionSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('default') }).strict(),
  z.object({ kind: z.literal('explicit'), choice: AiChoiceRefSchema.readonly() }).strict(),
]).readonly()
export const RoutingSnapshotSchema = z.object({
  source: AiSourceSchema,
  userId: IdentifierSchema,
  correlationId: IdentifierSchema,
  conversationId: IdentifierSchema.nullable(),
  selection: SnapshotSelectionSchema,
  resolvedChoice: AiChoiceRefSchema.readonly(),
  configurationVersion: z.number().int().positive().nullable(),
  roles: z.object({
    synthesizer: ResolvedRoleTargetSchema,
    planner: ResolvedRoleTargetSchema,
    deep_planner: ResolvedRoleTargetSchema,
    worker: ResolvedRoleTargetSchema,
  }).strict().readonly(),
}).strict().refine(
  snapshot => (snapshot.resolvedChoice.kind === 'custom_configuration') === (snapshot.configurationVersion !== null),
  { message: 'A configuration version is required only for a custom configuration.', path: ['configurationVersion'] },
).readonly()
export type RoutingSnapshot = z.infer<typeof RoutingSnapshotSchema>
