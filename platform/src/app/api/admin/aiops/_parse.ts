// Shared Zod schemas and request-parsing utilities for the AIOps API.

import { z } from 'zod'
import type { CallType, ModelStack } from '@/lib/models/registry'

export const VALID_STACKS: ModelStack[] = ['nim', 'anthropic', 'gemini', 'gpt', 'deepseek', 'marsys']
export const VALID_CALL_TYPES: CallType[] = [
  'synthesis', 'planner_deep', 'planner_fast', 'context_assembly', 'worker',
  'eval_judge', 'eval_generator', 'smoke_synth',
  'checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5',
]

export const stackSchema = z.enum(['nim', 'anthropic', 'gemini', 'gpt', 'deepseek', 'marsys'])
export const callTypeSchema = z.enum([
  'synthesis', 'planner_deep', 'planner_fast', 'context_assembly', 'worker',
  'eval_judge', 'eval_generator', 'smoke_synth',
  'checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5',
])

export const routingOverrideBodySchema = z.object({
  primary_model:  z.string().min(1),
  fallback_model: z.string().min(1),
})

export const paramOverrideBodySchema = z.object({
  param_name:  z.enum(['max_output_tokens', 'temperature', 'thinkingBudget', 'timeout_ms']),
  param_value: z.union([z.number(), z.boolean(), z.string()]),
})
