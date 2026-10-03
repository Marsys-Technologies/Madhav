import 'server-only'
import { z } from 'zod'
import { AI_ROLES, AiRoleSchema, CliIdSchema, type AiRole, type CliId } from '../types'

export const CLI_VALIDATION_STATES = [
  'untested', 'validating', 'reachable', 'not_installed', 'auth_unavailable', 'unreachable', 'needs_attention',
] as const
export const CliValidationStateSchema = z.enum(CLI_VALIDATION_STATES)
export type CliValidationState = z.infer<typeof CliValidationStateSchema>

export interface CliModelCatalogEntry {
  readonly modelId: string | null
  readonly displayName: string
  readonly compatibleRoles: readonly AiRole[]
  readonly supportsTools: boolean
  readonly supportsStructuredOutput: boolean
  readonly isBuiltinDefault: boolean
  readonly supportedEfforts?: readonly string[]
  readonly defaultEffort?: string | null
  readonly isCatalogDiscovered?: boolean
}

export interface SafeCliCard {
  readonly cliId: CliId
  readonly productName: string
  readonly state: 'not_granted' | CliValidationState
  readonly detectedProduct?: string
  readonly detectedVersion?: string
  readonly lastCheckedAt?: string
  readonly models?: readonly CliModelCatalogEntry[]
}

export const CLI_BUILTIN_MODEL_DB_ID = '__madhav_builtin_default__'
export const ALL_CLI_ROLES = Object.freeze([...AI_ROLES]) as readonly AiRole[]

export const CliModelCatalogEntrySchema = z.object({
  modelId: z.string().min(1).max(512).nullable(),
  displayName: z.string().min(1).max(120),
  compatibleRoles: z.array(AiRoleSchema).length(4),
  supportsTools: z.boolean(),
  supportsStructuredOutput: z.boolean(),
  isBuiltinDefault: z.boolean(),
  supportedEfforts: z.array(z.string().regex(/^[a-z][a-z0-9_]{0,31}$/)).max(16).optional(),
  defaultEffort: z.string().regex(/^[a-z][a-z0-9_]{0,31}$/).nullable().optional(),
  isCatalogDiscovered: z.boolean().optional(),
}).strict()

export const CliRouteIdSchema = CliIdSchema
