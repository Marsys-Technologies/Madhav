// Human-readable display labels for the AIOps Control Panel UI.
// Source-of-truth identifiers (CallType, ModelStack, Provider, etc.) stay in
// their canonical snake_case / lowercase forms in the database, API payloads,
// and registry. Everything the operator *sees* on screen goes through this map.

import type { CallType, ModelStack, Provider } from '@/lib/models/registry'
import type { AiopsAction } from '@/lib/db/schema/aiops'

export const CALL_TYPE_DISPLAY: Record<CallType, string> = {
  synthesis:        'Synthesis',
  planner_deep:     'Deep Planner',
  planner_fast:     'Fast Planner',
  context_assembly: 'Context Assembly',
  worker:           'Worker',
  eval_judge:       'Eval Judge',
  eval_generator:   'Eval Generator',
  smoke_synth:      'Smoke Synthesis',
  checkpoint_4_5:   'Checkpoint 4.5',
  checkpoint_5_5:   'Checkpoint 5.5',
  checkpoint_8_5:   'Checkpoint 8.5',
}

export const STACK_DISPLAY: Record<ModelStack, string> = {
  nim:       'NIM',
  anthropic: 'Anthropic',
  gemini:    'Gemini',
  gpt:       'GPT',
  deepseek:  'DeepSeek',
  marsys:    'MARSYS',
}

export const PROVIDER_DISPLAY: Record<Provider, string> = {
  nvidia:    'Nvidia',
  google:    'Google',
  openai:    'OpenAI',
  anthropic: 'Anthropic',
  deepseek:  'DeepSeek',
}

export type ParamName = 'max_output_tokens' | 'temperature' | 'thinkingBudget' | 'timeout_ms'

export const PARAM_DISPLAY: Record<ParamName, string> = {
  max_output_tokens: 'Max output tokens',
  temperature:       'Temperature',
  thinkingBudget:    'Thinking budget',
  timeout_ms:        'Timeout (ms)',
}

// Loosely typed because the API in practice emits a few action names that
// pre-date the AiopsAction union (e.g. 'set_active_stack' from the stack
// endpoint). The fallback in displayOf() returns the raw key for anything
// not listed here, so adding entries is purely additive.
export const ACTION_DISPLAY: Record<string, string> = {
  set_stack:        'Stack changed',
  set_active_stack: 'Stack changed',
  set_routing:      'Routing changed',
  set_param:        'Parameter changed',
  reset_param:      'Parameter reset',
  reset_routing:    'Routing reset',
  probe:            'Probe',
  revert:           'Reverted',
} satisfies Record<AiopsAction | 'set_active_stack', string>

export const ROLE_DISPLAY: Record<'primary' | 'fallback', string> = {
  primary:  'Primary',
  fallback: 'Fallback',
}

/** Safe lookup — falls back to the raw key if a value isn't in the map. */
export function displayOf<K extends string>(map: Record<K, string>, key: string): string {
  return (map as Record<string, string | undefined>)[key] ?? key
}
