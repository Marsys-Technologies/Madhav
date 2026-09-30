export const AI_ROLES = ['synthesizer', 'planner', 'deep_planner', 'worker'] as const
export type AiRole = (typeof AI_ROLES)[number]
export type ProviderId = 'openai' | 'anthropic' | 'google' | 'xai' | 'deepseek' | 'kimi' | 'openrouter'
export type CliId = 'codex' | 'claude_code' | 'gemini_antigravity' | 'kimi_code'

export type ProviderChoice = { kind: 'provider_model'; connectionId: string; modelId: string }
export type ConfigurationChoice = { kind: 'custom_configuration'; configurationId: string }
export type CliChoice = { kind: 'local_cli'; cliId: CliId; modelId: string | null }
export type AiChoice = ProviderChoice | ConfigurationChoice | CliChoice
export type RoleTarget = ProviderChoice | CliChoice
export type ConfigurationKind = 'provider_preset' | 'cli_preset' | 'custom_api' | 'custom_cli' | 'legacy_mixed'

export interface ProviderConnectionDto {
  id: string
  providerId: ProviderId
  name: string
  maskedSuffix: string
  validationState: 'untested' | 'validating' | 'validated' | 'needs_attention' | 'invalid' | 'unreachable'
  confirmedValid: boolean
  lastValidatedAt: string | null
  lastCheckedAt: string | null
  lastErrorCode: string | null
  deletedAt: string | null
}

export interface ProviderModelDto {
  connectionId: string
  modelId: string
  displayName: string
  compatibleRoles: AiRole[]
  supportsTools: boolean
  supportsStructuredOutput: boolean
  available: boolean
  userSelected?: boolean
  plainTestedAt?: string | null
  lastProbeAt?: string | null
  lastProbeErrorCode?: string | null
  lastProbeInputTokens?: number | null
  lastProbeOutputTokens?: number | null
}

export interface ConfigurationDto {
  id: string
  name: string
  version: number
  roles: Record<AiRole, RoleTarget>
  configurationKind: ConfigurationKind
  ownerConnectionId: string | null
  ownerCliId: CliId | null
  deletedAt: string | null
}

export interface AiConsoleStateDto {
  connections: ProviderConnectionDto[]
  models: ProviderModelDto[]
  configurations: ConfigurationDto[]
  defaultChoice: AiChoice | null
  validationDisclosure: string
}

export interface CliModelDto {
  modelId: string | null
  displayName: string
  compatibleRoles: AiRole[]
  supportsTools: boolean
  supportsStructuredOutput: boolean
  isBuiltinDefault: boolean
}

export type CliCardDto =
  | { cliId: CliId; productName: string; state: 'not_granted' }
  | {
      cliId: CliId
      productName: string
      state: 'untested' | 'validating' | 'reachable' | 'not_installed' | 'auth_unavailable' | 'unreachable' | 'needs_attention'
      detectedProduct: string | null
      detectedVersion: string | null
      lastCheckedAt: string | null
      models: CliModelDto[]
    }

export interface CliStateDto { clis: CliCardDto[] }

export interface ConsoleMutation {
  (url: string, init: RequestInit, successMessage: string): Promise<unknown>
}

export const ROLE_LABELS: Record<AiRole, string> = {
  synthesizer: 'Synthesizer',
  planner: 'Planner',
  deep_planner: 'Deep Planner',
  worker: 'Worker',
}

export const PROVIDER_LABELS: Record<ProviderId, string> = {
  openai: 'OpenAI', anthropic: 'Anthropic', google: 'Google Gemini', xai: 'xAI',
  deepseek: 'DeepSeek', kimi: 'Kimi / Moonshot', openrouter: 'OpenRouter',
}

export function choicesEqual(left: AiChoice | null, right: AiChoice): boolean {
  if (!left || left.kind !== right.kind) return false
  if (left.kind === 'provider_model' && right.kind === 'provider_model') {
    return left.connectionId === right.connectionId && left.modelId === right.modelId
  }
  if (left.kind === 'custom_configuration' && right.kind === 'custom_configuration') {
    return left.configurationId === right.configurationId
  }
  return left.kind === 'local_cli' && right.kind === 'local_cli'
    && left.cliId === right.cliId && left.modelId === right.modelId
}

export function supportsEveryRole(roles: readonly AiRole[]): boolean {
  return AI_ROLES.every(role => roles.includes(role))
}

/**
 * A revalidation may retain the last confirmed catalog under AIC-R017. A
 * first validation (or a replacement credential) has no server confirmation
 * and must remain unavailable until the server confirms it.
 */
export function hasCurrentProviderConfirmation(connection: ProviderConnectionDto): boolean {
  return connection.confirmedValid
    && (connection.validationState === 'validated' || connection.validationState === 'validating')
}

export function formatCheckedAt(value: string | null): string {
  if (!value) return 'Not checked yet'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? 'Check time unavailable' : parsed.toLocaleString()
}
