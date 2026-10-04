import type { AiEffort, CliId, ProviderId } from './types'

const LEVELS: readonly AiEffort[] = Object.freeze(['low', 'medium', 'high'])
const NONE: readonly AiEffort[] = Object.freeze([])

function openAiReasoningModel(modelId: string): boolean {
  return /^(?:gpt-[56](?:[.-]|$)|o[1-9](?:[.-]|$))/i.test(modelId)
}

function claudeEffortModel(modelId: string): boolean {
  return /^claude-(?:fable|mythos)-5(?:[.-]|$)|^claude-opus-(?:4-[5-9]|5)(?:[.-]|$)|^claude-sonnet-(?:4-[6-9]|5)(?:[.-]|$)/i.test(modelId)
}

function geminiEffortModel(modelId: string): boolean {
  return /^gemini-2\.5-(?:pro|flash(?:-lite)?)(?:[.-]|$)/i.test(modelId)
    || /^gemini-3\.(?:1-pro(?:-preview)?|[5-8]-flash(?:-lite)?)(?:[.-]|$)/i.test(modelId)
    || /^gemini-3-flash-preview(?:[.-]|$)/i.test(modelId)
}

/** Conservative allowlist: catalog presence alone does not establish effort support. */
export function providerEffortLevels(providerId: ProviderId, modelId: string): readonly AiEffort[] {
  if (providerId === 'openai') return openAiReasoningModel(modelId) ? LEVELS : NONE
  if (providerId === 'anthropic') return claudeEffortModel(modelId) ? LEVELS : NONE
  if (providerId === 'google') return geminiEffortModel(modelId) ? LEVELS : NONE
  if (providerId === 'openrouter') {
    const match = /^(openai|anthropic|google)\/(.+)$/.exec(modelId)
    if (!match) return NONE
    if (match[1] === 'openai') return openAiReasoningModel(match[2]) ? LEVELS : NONE
    if (match[1] === 'anthropic') return claudeEffortModel(match[2]) ? LEVELS : NONE
    return geminiEffortModel(match[2]) ? LEVELS : NONE
  }
  return NONE
}

export function cliEffortLevels(cliId: CliId, modelId: string | null,
  advertised?: readonly AiEffort[]): readonly AiEffort[] {
  if (!modelId) return NONE // the built-in default has no known model-specific capability
  if (advertised !== undefined) return advertised
  if (cliId === 'codex') return openAiReasoningModel(modelId) ? LEVELS : NONE
  if (cliId === 'claude_code') return claudeEffortModel(modelId) ? LEVELS : NONE
  // Antigravity model variants encode thinking level in the selected model ID;
  // Kimi ACP has no effort control. Keep both at model default here.
  return NONE
}
