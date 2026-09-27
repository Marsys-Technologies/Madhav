import 'server-only'
import { z } from 'zod'
import { AiConsoleError } from './errors'
import type {
  ProviderRuntimeFailure, ResolvedExecutionPlan, ResolvedRoleExecution, SafeRoutingSnapshot,
} from './execution/types'
import { createConnectionRuntimeBinding } from './providers'
import { loadRoutingResolution, markConnectionForRevalidation, type RoutingTarget } from './repository'
import {
  AI_ROLES, AiChoiceRefSchema, ConversationAiSelectionSchema, RoutingSnapshotSchema,
  type AiRole, type AiSource, type ResolvedRoleTarget,
} from './types'

const ResolverInputSchema = z.object({
  userId: z.string().min(1).regex(/\S/),
  source: z.enum(['pariprashna', 'consult', 'mcp', 'backend']),
  selection: ConversationAiSelectionSchema,
  conversationId: z.string().uuid().optional(),
  turnId: z.string().min(1).regex(/\S/),
}).strict()

function safeTarget(target: RoutingTarget): ResolvedRoleTarget {
  return target.kind === 'provider_model'
    ? Object.freeze({ kind: 'provider_model' as const, connectionId: target.connectionId,
      providerId: target.providerId, modelId: target.modelId })
    : Object.freeze({ kind: 'local_cli' as const, cliId: target.cliId, modelId: target.modelId })
}

function executionTarget(userId: string, role: AiRole, target: RoutingTarget): ResolvedRoleExecution {
  const execution = {
    role,
    adapterType: target.kind === 'provider_model' ? 'provider' as const : 'cli' as const,
    target: safeTarget(target),
  } as ResolvedRoleExecution
  if (target.kind === 'provider_model') {
    const connection = Object.freeze({ userId, connectionId: target.connectionId,
      providerId: target.providerId, credentialVersion: target.credentialVersion })
    const model = Object.freeze({ modelId: target.modelId, displayName: target.displayName,
      compatibleRoles: [...target.compatibleRoles], supportsTools: false, supportsStructuredOutput: false })
    Object.defineProperty(execution, 'createRuntimeBinding', {
      enumerable: false,
      configurable: false,
      writable: false,
      value: () => createConnectionRuntimeBinding(connection, model),
    })
    Object.defineProperty(execution, 'markRuntimeFailure', {
      enumerable: false,
      configurable: false,
      writable: false,
      value: (error: ProviderRuntimeFailure) =>
        markConnectionForRevalidation(userId, target.connectionId, target.credentialVersion, error),
    })
  }
  return Object.freeze(execution)
}

/** Resolve exactly once. This function never searches for or retries another choice. */
export async function resolveUserRouting(input: {
  userId: string
  source: 'pariprashna' | 'consult' | 'mcp' | 'backend'
  selection: z.infer<typeof ConversationAiSelectionSchema>
  conversationId?: string
  turnId: string
}): Promise<ResolvedExecutionPlan> {
  if (typeof input?.userId !== 'string' || input.userId.trim().length === 0) {
    throw new AiConsoleError('AI_PERMISSION_DENIED')
  }
  if (input.conversationId !== undefined && !z.string().uuid().safeParse(input.conversationId).success) {
    throw new AiConsoleError('AI_PERMISSION_DENIED')
  }
  const parsed = ResolverInputSchema.parse(input)
  const source: AiSource = parsed.source === 'consult' ? 'pariprashna' : parsed.source
  const resolution = await loadRoutingResolution(parsed.userId, parsed.selection, parsed.conversationId)
  const parsedSelection = ConversationAiSelectionSchema.parse(parsed.selection)
  const selection = parsedSelection.kind === 'default'
    ? Object.freeze({ kind: 'default' as const })
    : Object.freeze({ kind: 'explicit' as const, choice: Object.freeze({ ...parsedSelection.choice }) })
  const resolvedChoice = Object.freeze(AiChoiceRefSchema.parse(resolution.resolvedChoice))
  const roles = Object.freeze(Object.fromEntries(AI_ROLES.map(role => [
    role, executionTarget(parsed.userId, role, resolution.roles[role]),
  ])) as Record<AiRole, ResolvedRoleExecution>)
  const plan = {
    source,
    userId: parsed.userId,
    correlationId: parsed.turnId,
    conversationId: parsed.conversationId ?? null,
    selection,
    resolvedChoice,
    configurationVersion: resolution.configurationVersion,
    roles,
    resolvedAt: new Date().toISOString(),
  } as ResolvedExecutionPlan
  Object.defineProperty(plan, 'toJSON', {
    enumerable: false,
    configurable: false,
    writable: false,
    value: () => { throw new AiConsoleError('AI_EXECUTION_FAILED') },
  })
  return Object.freeze(plan)
}

/** The sole serializable projection. Runtime factories and credential versions are excluded. */
export function toSafeRoutingSnapshot(plan: ResolvedExecutionPlan): SafeRoutingSnapshot {
  return RoutingSnapshotSchema.parse({
    source: plan.source,
    userId: plan.userId,
    correlationId: plan.correlationId,
    conversationId: plan.conversationId,
    selection: plan.selection,
    resolvedChoice: plan.resolvedChoice,
    configurationVersion: plan.configurationVersion,
    roles: Object.fromEntries(AI_ROLES.map(role => [role, plan.roles[role].target])),
  })
}
