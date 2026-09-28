import 'server-only'
import { z } from 'zod'
import { AiConsoleError } from '../errors'
import { CLI_IDS, type AiRole, type CliId } from '../types'
import { ALL_CLI_ROLES } from './types'

export type CliOutputFormat = 'codex_jsonl' | 'claude_json' | 'antigravity_stream_json' | 'kimi_acp_json'
export type CliExecutionTransport = 'standard' | 'antigravity_stream_json' | 'kimi_acp'
export type CliModelCatalogFormat = 'antigravity_models' | 'kimi_provider_json'

export interface CliExecutionDefinition {
  readonly args: readonly string[]
  readonly modelFlag: readonly string[]
  readonly structuredSchemaFlag?: readonly string[]
  readonly outputFormat: CliOutputFormat
  readonly transport?: CliExecutionTransport
}

export interface CliModelCatalogDefinition {
  readonly args: readonly string[]
  readonly format: CliModelCatalogFormat
}

export interface CliInterpreterDefinition {
  readonly candidate: string
  readonly allowedRealpathPrefixes: readonly string[]
}

export interface CliDefinition {
  readonly id: CliId
  readonly productName: string
  readonly candidates: readonly string[]
  readonly allowedRealpathPrefixes: readonly string[]
  readonly versionArgs: readonly string[]
  readonly authStatusArgs?: readonly string[]
  readonly supportedVersion: string
  readonly compatibleRoles: readonly AiRole[]
  readonly supportsTools: false
  readonly supportsStructuredOutput: boolean
  readonly interpreter?: CliInterpreterDefinition
  readonly execution?: CliExecutionDefinition
  readonly modelCatalog?: CliModelCatalogDefinition
}

const fixed = <T extends string>(...values: T[]): readonly T[] => Object.freeze(values)

export const CLI_REGISTRY: Readonly<Record<CliId, CliDefinition>> = Object.freeze({
  codex: Object.freeze({
    id: 'codex', productName: 'Codex CLI', candidates: fixed('/opt/homebrew/bin/codex'),
    allowedRealpathPrefixes: fixed('/opt/homebrew/Caskroom/codex/'), versionArgs: fixed('--version'),
    authStatusArgs: fixed('login', 'status'), supportedVersion: '0.155.1', compatibleRoles: ALL_CLI_ROLES,
    supportsTools: false, supportsStructuredOutput: true,
    execution: Object.freeze({
      args: fixed('exec', '--sandbox', 'read-only', '--ephemeral', '--ignore-user-config', '--ignore-rules',
        '--skip-git-repo-check', '--color', 'never', '--json', '--cd', '__CWD__', '-'),
      modelFlag: fixed('--model'), structuredSchemaFlag: fixed('--output-schema'), outputFormat: 'codex_jsonl',
    }),
  }),
  claude_code: Object.freeze({
    id: 'claude_code', productName: 'Claude Code', candidates: fixed('/Users/Dev/.local/bin/claude'),
    allowedRealpathPrefixes: fixed('/Users/Dev/.local/share/claude/versions/'), versionArgs: fixed('--version'),
    authStatusArgs: fixed('auth', 'status'), supportedVersion: '2.1.239', compatibleRoles: ALL_CLI_ROLES,
    supportsTools: false, supportsStructuredOutput: true,
    execution: Object.freeze({
      args: fixed('-p', '--input-format', 'text', '--output-format', 'json', '--no-session-persistence',
        '--disable-slash-commands', '--tools', '', '--setting-sources', '', '--mcp-config', '{"mcpServers":{}}',
        '--strict-mcp-config', '--permission-mode', 'dontAsk'),
      modelFlag: fixed('--model'), structuredSchemaFlag: fixed('--json-schema'), outputFormat: 'claude_json',
    }),
  }),
  gemini_antigravity: Object.freeze({
    id: 'gemini_antigravity', productName: 'Gemini / Antigravity', candidates: fixed('/Users/Dev/.local/bin/agy'),
    allowedRealpathPrefixes: fixed('/Users/Dev/.local/bin/'), versionArgs: fixed('--version'),
    supportedVersion: '1.2.12', compatibleRoles: ALL_CLI_ROLES, supportsTools: false,
    supportsStructuredOutput: true,
    modelCatalog: Object.freeze({ args: fixed('models'), format: 'antigravity_models' }),
    execution: Object.freeze({
      args: fixed('--sandbox', '--disable-slash-commands', '--input-format', 'stream-json', '--output-format',
        'stream-json', '--print-timeout', '2m'),
      modelFlag: fixed('--model'), structuredSchemaFlag: fixed('--json-schema'),
      outputFormat: 'antigravity_stream_json', transport: 'antigravity_stream_json',
    }),
  }),
  kimi_code: Object.freeze({
    id: 'kimi_code', productName: 'Kimi Code', candidates: fixed('/Users/Dev/.kimi-code/bin/kimi'),
    allowedRealpathPrefixes: fixed('/Users/Dev/.kimi-code/bin/'), versionArgs: fixed('--version'),
    supportedVersion: '2.0.2', compatibleRoles: ALL_CLI_ROLES, supportsTools: false,
    supportsStructuredOutput: false,
    modelCatalog: Object.freeze({ args: fixed('provider', 'list', '--json'), format: 'kimi_provider_json' }),
    execution: Object.freeze({ args: fixed('acp'), modelFlag: fixed<string>(), outputFormat: 'kimi_acp_json',
      transport: 'kimi_acp' }),
  }),
})

if (Object.keys(CLI_REGISTRY).join(',') !== CLI_IDS.join(',')) throw new Error('CLI registry drift')

export function parseSupportedVersion(definition: CliDefinition, output: string): string | null {
  const escaped = definition.supportedVersion.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return escaped && new RegExp(`(?:^|\\s)${escaped}(?:\\s|$|\\))`).test(output.trim())
    ? definition.supportedVersion : null
}

const ModelIdSchema = z.string().min(1).max(512).refine(value => !value.startsWith('-')
  && !/[\u0000-\u001f\u007f]/.test(value), 'Unsafe model identifier')

export function validateCliModelId(modelId: string | null): string | null {
  if (modelId === null) return null
  const parsed = ModelIdSchema.safeParse(modelId)
  if (!parsed.success) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
  return parsed.data
}

export function buildExecutionArgs(definition: CliDefinition, modelId: string | null,
  options: { cwd?: string; schemaPath?: string } = {}): string[] {
  if (!definition.execution) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const model = validateCliModelId(modelId)
  const args = definition.execution.args.map(value => value === '__CWD__' ? options.cwd ?? '__CWD__' : value)
  const additions: string[] = []
  if (model !== null && definition.execution.modelFlag.length > 0) {
    additions.push(...definition.execution.modelFlag, model)
  }
  if (options.schemaPath !== undefined) {
    if (!definition.execution.structuredSchemaFlag) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
    additions.push(...definition.execution.structuredSchemaFlag, options.schemaPath)
  }
  const stdinMarker = definition.id === 'codex' ? args.lastIndexOf('-') : -1
  if (stdinMarker >= 0) args.splice(stdinMarker, 0, ...additions); else args.push(...additions)
  return args
}
