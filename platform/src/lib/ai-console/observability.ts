import 'server-only'

import { z } from 'zod'
import { AiErrorCodeSchema, type AiErrorCode } from './errors'
import type { NormalizedUsage, SafeRoleExecutorDescriptor } from './execution/provider-executor'
import type { SafeRoutingSnapshot } from './execution/types'
import { writeAiRoutingUsageEvent, writeMcpExternalSynthesisEvent } from '@/lib/db/monitoring-write'

const Identifier = z.string().min(1).max(512).regex(/\S/)
const NullableTokens = z.number().int().nonnegative().nullable()
const Provider = z.enum(['openai', 'anthropic', 'gemini', 'xai', 'deepseek', 'kimi', 'openrouter', 'cli'])

export const SafeAiRoutingParametersSchema = z.object({
  schema_version: z.literal('madhav.ai-routing.v1'),
  snapshot_id: z.string().uuid(),
  invocation_id: z.string().uuid(),
  correlation_id: Identifier,
  conversation_id: Identifier.nullable(),
  user_id: Identifier,
  source: z.enum(['pariprashna', 'mcp', 'backend']),
  role: z.enum(['synthesizer', 'planner', 'deep_planner', 'worker']),
  selection_mode: z.enum(['default', 'explicit']),
  resolved_choice_kind: z.enum(['provider_model', 'custom_configuration', 'local_cli']),
  configuration_id: z.string().uuid().nullable(),
  configuration_version: z.number().int().positive().nullable(),
  target_kind: z.enum(['provider_model', 'local_cli']),
  connection_id: z.string().uuid().nullable(),
  provider: Provider,
  model_id: Identifier.nullable(),
  cli_id: z.enum(['codex', 'claude_code', 'gemini_antigravity', 'kimi_code']).nullable(),
  built_in_default: z.boolean(),
  terminal_status: z.enum(['success', 'error', 'timeout', 'cancelled']),
  started_at: z.string().datetime(),
  finished_at: z.string().datetime(),
  latency_ms: z.number().int().nonnegative(),
  input_tokens: NullableTokens,
  output_tokens: NullableTokens,
  total_tokens: NullableTokens,
  retry_count: z.number().int().nonnegative().nullable(),
  error_code: AiErrorCodeSchema.nullable(),
  fallback_used: z.literal(false),
}).strict().superRefine((value, context) => {
  if (value.target_kind === 'provider_model') {
    if (!value.connection_id || value.cli_id || value.provider === 'cli' || !value.model_id || value.built_in_default) {
      context.addIssue({ code: 'custom', message: 'Provider routing identity is inconsistent.' })
    }
  } else if (value.connection_id || !value.cli_id || value.provider !== 'cli'
    || (value.model_id === null) !== value.built_in_default) {
    context.addIssue({ code: 'custom', message: 'CLI routing identity is inconsistent.' })
  }
  if ((value.resolved_choice_kind === 'custom_configuration') !== (value.configuration_id !== null)) {
    context.addIssue({ code: 'custom', message: 'Configuration identity is inconsistent.' })
  }
  if ((value.configuration_id === null) !== (value.configuration_version === null)) {
    context.addIssue({ code: 'custom', message: 'Configuration version is inconsistent.' })
  }
})

export type SafeAiRoutingParameters = z.infer<typeof SafeAiRoutingParametersSchema>

export interface RoleInvocationTerminalFacts {
  readonly invocationId: string
  readonly status: 'success' | 'error' | 'timeout' | 'cancelled'
  readonly startedAt: Date
  readonly finishedAt: Date
  readonly usage: NormalizedUsage | null
  readonly retryCount: number | null
  readonly errorCode: AiErrorCode | null
}

export interface RoleObservationContext {
  readonly snapshotId: string
  readonly snapshot: SafeRoutingSnapshot
  readonly write?: (event: SafeAiRoutingParameters) => Promise<void>
}

function observableProvider(provider: string): z.infer<typeof Provider> {
  return Provider.parse(provider === 'google' ? 'gemini' : provider)
}

export function projectRoleInvocationObservation(
  descriptor: SafeRoleExecutorDescriptor,
  context: RoleObservationContext,
  terminal: RoleInvocationTerminalFacts,
): SafeAiRoutingParameters {
  const snapshot = context.snapshot
  const roleTarget = snapshot.roles[descriptor.role]
  const configurationId = snapshot.resolvedChoice.kind === 'custom_configuration'
    ? snapshot.resolvedChoice.configurationId : null
  const isProvider = 'providerId' in descriptor
  const modelId = descriptor.modelId
  if (isProvider && (roleTarget.kind !== 'provider_model'
    || roleTarget.connectionId !== descriptor.connectionId
    || roleTarget.providerId !== descriptor.providerId || roleTarget.modelId !== modelId)) {
    throw new Error('Executor descriptor does not match the immutable routing snapshot.')
  }
  if (!isProvider && (roleTarget.kind !== 'local_cli'
    || roleTarget.cliId !== descriptor.cliId || roleTarget.modelId !== modelId)) {
    throw new Error('Executor descriptor does not match the immutable routing snapshot.')
  }
  const input = terminal.usage?.inputTokens ?? null
  const output = terminal.usage?.outputTokens ?? null
  const total = terminal.usage?.totalTokens ?? null
  return SafeAiRoutingParametersSchema.parse({
    schema_version: 'madhav.ai-routing.v1',
    snapshot_id: context.snapshotId,
    invocation_id: terminal.invocationId,
    correlation_id: snapshot.correlationId,
    conversation_id: snapshot.conversationId,
    user_id: snapshot.userId,
    source: snapshot.source,
    role: descriptor.role,
    selection_mode: snapshot.selection.kind,
    resolved_choice_kind: snapshot.resolvedChoice.kind,
    configuration_id: configurationId,
    configuration_version: snapshot.configurationVersion,
    target_kind: isProvider ? 'provider_model' : 'local_cli',
    connection_id: isProvider ? descriptor.connectionId : null,
    provider: isProvider ? observableProvider(descriptor.providerId) : 'cli',
    model_id: modelId,
    cli_id: isProvider ? null : descriptor.cliId,
    built_in_default: !isProvider && modelId === null,
    terminal_status: terminal.status,
    started_at: terminal.startedAt.toISOString(),
    finished_at: terminal.finishedAt.toISOString(),
    latency_ms: Math.max(0, terminal.finishedAt.getTime() - terminal.startedAt.getTime()),
    input_tokens: input,
    output_tokens: output,
    total_tokens: total,
    retry_count: terminal.retryCount,
    error_code: terminal.errorCode,
    fallback_used: false,
  })
}

export async function observeRoleInvocation(
  descriptor: SafeRoleExecutorDescriptor,
  context: RoleObservationContext,
  terminal: RoleInvocationTerminalFacts,
): Promise<void> {
  const event = projectRoleInvocationObservation(descriptor, context, terminal)
  await (context.write ?? writeAiRoutingUsageEvent)(event)
}

export const SafeMcpExternalSynthesisSchema = z.object({
  schema_version: z.literal('madhav.external-synthesis.v1'),
  correlation_id: z.string().uuid(),
  conversation_id: z.string().uuid().nullable(),
  user_id: Identifier,
  call_stage: z.literal('external_synthesis'),
  external_synthesis: z.literal(true),
  performed_by_madhav: z.literal(false),
  status: z.enum(['success', 'error', 'cancelled']),
  fallback_used: z.literal(false),
}).strict()
export type SafeMcpExternalSynthesis = z.infer<typeof SafeMcpExternalSynthesisSchema>

export async function observeMcpExternalSynthesis(
  snapshot: SafeRoutingSnapshot,
  status: SafeMcpExternalSynthesis['status'] = 'success',
): Promise<void> {
  if (snapshot.source !== 'mcp') return
  try {
    const event = SafeMcpExternalSynthesisSchema.parse({
      schema_version: 'madhav.external-synthesis.v1',
      correlation_id: snapshot.correlationId,
      conversation_id: snapshot.conversationId,
      user_id: snapshot.userId,
      call_stage: 'external_synthesis',
      external_synthesis: true,
      performed_by_madhav: false,
      status,
      fallback_used: false,
    })
    await writeMcpExternalSynthesisEvent(event)
  } catch {
    console.warn('[ai-console] Observatory external-synthesis observation failed')
  }
}
