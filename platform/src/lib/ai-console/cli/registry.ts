import 'server-only'
import { z } from 'zod'
import { AiConsoleError } from '../errors'
import { CLI_IDS, type AiRole, type CliId } from '../types'
import { ALL_CLI_ROLES } from './types'

export type CliOutputFormat = 'codex_jsonl' | 'claude_json'

export interface CliExecutionDefinition {
  readonly args: readonly string[]
  readonly modelFlag: readonly string[]
  readonly structuredSchemaFlag?: readonly string[]
  readonly outputFormat: CliOutputFormat
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
}

const fixed = <T extends string>(...values: T[]): readonly T[] => Object.freeze(values)

export const CLI_REGISTRY: Readonly<Record<CliId, CliDefinition>> = Object.freeze({
  codex: Object.freeze({
    id: 'codex', productName: 'Codex CLI', candidates: fixed('/opt/homebrew/bin/codex'),
    allowedRealpathPrefixes: fixed('/opt/homebrew/Caskroom/codex/'), versionArgs: fixed('--version'),
    supportedVersion: '0.155.1', compatibleRoles: fixed<AiRole>(), supportsTools: false,
    supportsStructuredOutput: false,
  }),
  claude_code: Object.freeze({
    id: 'claude_code', productName: 'Claude Code', candidates: fixed('/usr/local/bin/claude'),
    allowedRealpathPrefixes: fixed('/usr/local/lib/node_modules/@anthropic-ai/claude-code/'), versionArgs: fixed('--version'),
    authStatusArgs: fixed('auth', 'status'), supportedVersion: '2.1.56', compatibleRoles: ALL_CLI_ROLES,
    supportsTools: false, supportsStructuredOutput: true,
    interpreter: Object.freeze({ candidate: '/usr/local/bin/node',
      allowedRealpathPrefixes: fixed('/usr/local/bin/') }),
    execution: Object.freeze({
      args: fixed('-p', '--input-format', 'text', '--output-format', 'json', '--no-session-persistence',
        '--disable-slash-commands', '--tools', '', '--setting-sources', '', '--mcp-config', '{}',
        '--strict-mcp-config', '--permission-mode', 'dontAsk'),
      modelFlag: fixed('--model'), structuredSchemaFlag: fixed('--json-schema'), outputFormat: 'claude_json',
    }),
  }),
  gemini_antigravity: Object.freeze({
    id: 'gemini_antigravity', productName: 'Gemini / Antigravity', candidates: fixed<string>(),
    allowedRealpathPrefixes: fixed<string>(), versionArgs: fixed('--version'), supportedVersion: '',
    compatibleRoles: fixed<AiRole>(), supportsTools: false,
    supportsStructuredOutput: false,
  }),
  kimi_code: Object.freeze({
    id: 'kimi_code', productName: 'Kimi Code', candidates: fixed<string>(), allowedRealpathPrefixes: fixed<string>(),
    versionArgs: fixed('--version'), supportedVersion: '', compatibleRoles: fixed<AiRole>(), supportsTools: false,
    supportsStructuredOutput: false,
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
  if (model !== null) additions.push(...definition.execution.modelFlag, model)
  if (options.schemaPath !== undefined) {
    if (!definition.execution.structuredSchemaFlag) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
    additions.push(...definition.execution.structuredSchemaFlag, options.schemaPath)
  }
  const stdinMarker = definition.id === 'codex' ? args.lastIndexOf('-') : -1
  if (stdinMarker >= 0) args.splice(stdinMarker, 0, ...additions); else args.push(...additions)
  return args
}
