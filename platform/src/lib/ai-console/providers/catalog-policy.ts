import 'server-only'
import type { ProviderId } from '../types'
import { object, tokenCount, type DiscoveredModel } from './types'

const MODEL_ID = /^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,199}$/
const UNSUPPORTED = /embedding|rerank|moderation|whisper|tts|audio|realtime|image|vision-exp|video|computer-use|deep-research|multi-agent|instruct|codex|(^|\/)auto$|openrouter\/(auto|free)|:online|:nitro|:floor/i
// Positive protocol evidence, not availability. Unknown/specialized suffixes do
// not inherit a family's capabilities. Sources and limitations: Task 5 report.
const DOCUMENTED_CAPABILITIES: Partial<Record<ProviderId, RegExp>> = {
  openai: /^(?:gpt-4\.1(?:-mini|-nano)?(?:-2025-04-14)?|gpt-4o(?:-2024-08-06|-2024-11-20)?|gpt-4o-mini(?:-2024-07-18)?)$/,
  anthropic: /^claude-(?:haiku-4-5|sonnet-4-[56]|opus-4-[56])(?:-\d{8})?$/,
  google: /^gemini-2\.5-(?:pro|flash|flash-lite)$/,
  xai: /^grok-4(?:-0709)?$/,
}
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
  let tools = DOCUMENTED_CAPABILITIES[provider]?.test(id) ?? false
  let structured = tools
  if (Array.isArray(parameters)) {
    tools = parameters.includes('tools')
    // response_format alone may mean only json_object, not schema conformance.
    structured = parameters.includes('structured_outputs')
  }
  if (typeof capabilities.tools === 'boolean') tools = capabilities.tools
  if (typeof object(capabilities.tools).supported === 'boolean') tools = object(capabilities.tools).supported === true
  if (typeof capabilities.structured_outputs === 'boolean') structured = capabilities.structured_outputs
  if (typeof object(capabilities.structured_outputs).supported === 'boolean') structured = object(capabilities.structured_outputs).supported === true
  // Native function calling is explicitly unsupported for the search preview.
  if (provider === 'openai' && /^gpt-4o(?:-mini)?-search-preview(?:-\d{4}-\d{2}-\d{2})?$/.test(id)) tools = false
  // Shared Chat SDK cannot round-trip reasoning_content/reasoning_details.
  // Kimi/DeepSeek default-thinking models are synthesis-only under this adapter.
  if (provider === 'kimi' || provider === 'deepseek') { tools = false; structured = false }
  if (provider === 'openrouter') {
    tools = false
    structured = structured && Array.isArray(parameters) && parameters.includes('structured_outputs')
  }
  const label = row.display_name ?? row.displayName ?? row.name
  const displayName = typeof label === 'string' && !label.includes(secret) && label.length <= 160
    && /^[\p{L}\p{N} ._:/()+\-]+$/u.test(label) ? label : id
  const context = tokenCount(row.context_length ?? row.context_window ?? row.inputTokenLimit ?? row.max_input_tokens)
  const outputLimit = tokenCount(row.max_output_tokens ?? row.outputTokenLimit ?? row.max_tokens ?? object(row.top_provider).max_completion_tokens)
  return { modelId: id, displayName, compatibleRoles: ['synthesizer', ...(structured ? ['planner' as const, 'deep_planner' as const, 'worker' as const] : [])],
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
