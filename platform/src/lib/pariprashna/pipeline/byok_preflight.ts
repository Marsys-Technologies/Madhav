import 'server-only'

import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { createDefaultFallbackExecutor, createRoleExecutor } from '@/lib/ai-console/execution'
import { trackRoleExecutor } from '@/lib/ai-console/execution/tracked-executor'
import { buildResolvedExecutionPlan } from '@/lib/ai-console/routing'
import { prepareTurnRouting } from '@/lib/ai-console/repository'
import { AI_ROLES, ConversationAiSelectionSchema } from '@/lib/ai-console/types'
import { admitByokTurn } from '@/lib/limits/byok_admission'
import type { ByokTurnRuntime } from './turn_runtime'

export async function authenticateByokUser() {
  const auth = await getServerUserWithProfile()
  if (!auth) throw new AiConsoleError('AI_PERMISSION_DENIED')
  if (auth.profile.status !== 'active') throw new AiConsoleError('AI_PERMISSION_DENIED')
  return auth
}

/**
 * The complete flag-on authority boundary. No executor exists until ownership,
 * persisted selection, one resolution, snapshot commit and one admission pass.
 */
export async function prepareByokTurn(input: {
  userId: string
  role: 'super_admin' | 'guest'
  chartId: string
  conversationId: string
  isFirstTurn: boolean
  turnId: string
  requestedSelection: unknown
  questionChars: number
  source?: 'pariprashna' | 'consult'
}): Promise<ByokTurnRuntime> {
  const selection = ConversationAiSelectionSchema.parse(input.requestedSelection)
  const prepared = await prepareTurnRouting({
    userId: input.userId,
    role: input.role,
    chartId: input.chartId,
    conversationId: input.conversationId,
    isFirstTurn: input.isFirstTurn,
    turnId: input.turnId,
    source: input.source ?? 'pariprashna',
    selection,
  })
  const plan = buildResolvedExecutionPlan({
    source: input.source ?? 'pariprashna',
    userId: input.userId,
    selection: prepared.selection,
    conversationId: input.conversationId,
    turnId: input.turnId,
  }, prepared.resolution)
  const fallbackPlan = prepared.fallback ? buildResolvedExecutionPlan({
    source: input.source ?? 'pariprashna',
    userId: input.userId,
    selection: { kind: 'default' },
    conversationId: input.conversationId,
    turnId: prepared.fallback.safeSnapshot.correlationId,
  }, prepared.fallback.resolution) : undefined
  const { safeSnapshot, snapshotId } = prepared
  const admission = admitByokTurn({ userId: input.userId, questionChars: input.questionChars })
  if (!admission.allowed) throw new AiConsoleError(admission.code)

  try {
    const selectedExecutors = Object.freeze(Object.fromEntries(AI_ROLES.map(role => {
      const executor = createRoleExecutor(plan.roles[role])
      return [role, trackRoleExecutor(executor, { userId: input.userId, snapshotId,
        observation: { snapshot: safeSnapshot } })]
    })) as ByokTurnRuntime['executors'])
    const fallbackExecutors = fallbackPlan && prepared.fallback
      ? Object.freeze(Object.fromEntries(AI_ROLES.map(role => {
          const executor = createRoleExecutor(fallbackPlan.roles[role])
          return [role, trackRoleExecutor(executor, { userId: input.userId,
            snapshotId: prepared.fallback!.snapshotId,
            observation: { snapshot: prepared.fallback!.safeSnapshot,
              fallback: { fromCorrelationId: input.turnId } } })]
        })) as ByokTurnRuntime['executors'])
      : undefined
    const executors = fallbackExecutors
      ? Object.freeze(Object.fromEntries(AI_ROLES.map(role => [role,
          createDefaultFallbackExecutor(selectedExecutors[role], fallbackExecutors[role]),
        ])) as ByokTurnRuntime['executors'])
      : selectedExecutors
    const synth = safeSnapshot.roles.synthesizer
    const displayModelId = synth.modelId ?? ('cliId' in synth ? `${synth.cliId}:built-in-default` : 'selected-model')
    return Object.freeze({
      kind: 'byok' as const,
      selection: prepared.selection,
      plan,
      safeSnapshot,
      snapshotId,
      executors,
      displayModelId,
      releaseAdmission: admission.release,
    })
  } catch (error) {
    admission.release()
    throw error
  }
}
