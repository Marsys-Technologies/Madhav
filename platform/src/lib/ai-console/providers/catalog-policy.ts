import 'server-only'
import type { ProviderId } from '../types'
import { object, tokenCount, type DiscoveredModel } from './types'

const MODEL_ID = /^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,199}$/
const UNSUPPORTED = /embedding|rerank|moderation|whisper|tts|audio|realtime|image|vision-exp|video|computer-use|deep-research|multi-agent|instruct|codex|(^|\/)auto$|openrouter\/(auto|free)|:online|:nitro|:floor/i
export function safeModelId(value: unknown): value is string {
  return typeof value === 'string' && MODEL_ID.test(value) && !value.includes('..')
}
/** Availability always comes from authenticated discovery; these are protocol family rules. */
export function compatibleModel(provider: ProviderId, input: unknown, secret: string): DiscoveredModel | null {
  const row = object(input)
  const id = provider === 'google' && typeof row.name === 'string' ? row.name.replace(/^models\//, '') : row.id
  if (!safeModelId(id) || id.includes(secret) || UNSUPPORTED.test(id)
    || row.retired === true || row.deprecated === true || ['retired', 'deprecated', 'disabled'].includes(String(row.status))
    || (typeof row.expiration_date === 'string' && Date.parse(row.expiration_date) <= Date.now())) return null
  const architecture = object(row.architecture)
  const output = row.output_modalities ?? architecture.output_modalities
  if (Array.isArray(output) && !output.some(m => String(m).toLowerCase() === 'text')) return null
  const methods = row.supportedGenerationMethods
  const family = provider === 'openai' ? /^(gpt-(4o|4\.1|5|6)(-|\.|$)|o[34](-|$))/.test(id) && !/-pro($|-)|gpt-4\.1-nano|o3-mini|o4-mini/.test(id)
    : provider === 'anthropic' ? /^claude-/.test(id) && !/^claude-(instant|2|3-)/.test(id)
      : provider === 'google' ? /^gemini-/.test(id) && Array.isArray(methods) && methods.includes('generateContent')
        : provider === 'xai' ? /^grok-/.test(id)
          : provider === 'deepseek' ? /^deepseek-/.test(id)
            : provider === 'kimi' ? /^(kimi-|moonshot-)/.test(id)
              : Array.isArray(output) && output.includes('text')
  if (!family) return null
  const parameters = row.supported_parameters
  const capabilities = object(row.capabilities)
  let tools = provider !== 'openrouter'
  let structured = provider !== 'openrouter'
  if (Array.isArray(parameters)) {
    tools = parameters.includes('tools')
    structured = parameters.includes('response_format') || parameters.includes('structured_outputs')
  }
  if (typeof capabilities.tools === 'boolean') tools = capabilities.tools
  if (typeof capabilities.structured_outputs === 'boolean') structured = capabilities.structured_outputs
  if (object(capabilities.structured_outputs).supported === false) structured = false
  const label = row.display_name ?? row.displayName ?? row.name
  const displayName = typeof label === 'string' && !label.includes(secret) && label.length <= 160
    && /^[\p{L}\p{N} ._:/()+\-]+$/u.test(label) ? label : id
  const context = tokenCount(row.context_length ?? row.context_window ?? row.inputTokenLimit ?? row.max_input_tokens)
  const outputLimit = tokenCount(row.max_output_tokens ?? row.outputTokenLimit ?? row.max_tokens ?? object(row.top_provider).max_completion_tokens)
  return { modelId: id, displayName, compatibleRoles: ['synthesizer', ...(structured ? ['planner' as const, 'deep_planner' as const] : []), ...(tools ? ['worker' as const] : [])],
    supportsTools: tools, supportsStructuredOutput: structured,
    ...(context && { contextWindow: context }), ...(outputLimit && { outputLimit }) }
}
export function filterCatalog(provider: ProviderId, rows: unknown[], secret: string): DiscoveredModel[] {
  const found = new Map<string, DiscoveredModel>()
  for (const row of rows) { const model = compatibleModel(provider, row, secret); if (model) found.set(model.modelId, model) }
  return [...found.values()].sort((a, b) => a.modelId.localeCompare(b.modelId))
}
export function chooseProbeModel(models: DiscoveredModel[]): DiscoveredModel | undefined {
  // Only validation chooses a cheap candidate; runtime choices never use this preference.
  return models.find(m => /mini|nano|haiku|flash|instant/.test(m.modelId)) ?? models[0]
}
