import 'server-only'

import { isDeepStrictEqual } from 'node:util'
import { z } from 'zod'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { authorizeChartAccess, type DbLike } from '@/lib/auth/authorizeChartAccess'
import { query } from '@/lib/db/client'
import { getConversation, insertConversationWithId } from '@/lib/conversations'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { createRoleExecutor } from '@/lib/ai-console/execution'
import { trackRoleExecutor } from '@/lib/ai-console/execution/tracked-executor'
import { resolveUserRouting, toSafeRoutingSnapshot } from '@/lib/ai-console/routing'
import { getConversationSelection, insertRoutingSnapshot, setConversationSelection } from '@/lib/ai-console/repository'
import { AI_ROLES, ConversationAiSelectionSchema, type ConversationAiSelection } from '@/lib/ai-console/types'
import { admitByokTurn } from '@/lib/limits/byok_admission'
import type { ByokTurnRuntime } from './turn_runtime'

const UuidSchema = z.string().uuid()

export async function authenticateByokUser() {
  const auth = await getServerUserWithProfile()
  if (!auth) throw new AiConsoleError('AI_PERMISSION_DENIED')
  if (auth.profile.status !== 'active') throw new AiConsoleError('AI_PERMISSION_DENIED')
  return auth
}

async function authorizeOwnerAndChart(input: {
  userId: string
  role: 'super_admin' | 'guest'
  chartId: string
  conversationId?: string
}) {
  UuidSchema.parse(input.chartId)
  const permission = await authorizeChartAccess({
    principal: { uid: input.userId, role: input.role },
    chartId: input.chartId,
    db: { query: (sql: string, params?: unknown[]) => query(sql, params).then(result => ({ rows: result.rows })) } as DbLike,
  })
  if (permission === 'deny') throw new AiConsoleError('AI_PERMISSION_DENIED')
  if (!input.conversationId) return
  UuidSchema.parse(input.conversationId)
  const existing = await getConversation({
    id: input.conversationId,
    userId: input.userId,
    isSuperAdmin: input.role === 'super_admin',
  })
  if (!existing || existing.chart_id !== input.chartId) throw new AiConsoleError('AI_PERMISSION_DENIED')
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
  await authorizeOwnerAndChart({
    userId: input.userId,
    role: input.role,
    chartId: input.chartId,
    ...(input.isFirstTurn ? {} : { conversationId: input.conversationId }),
  })

  let authoritativeSelection: ConversationAiSelection
  if (input.isFirstTurn) {
    await insertConversationWithId({
      id: input.conversationId,
      chartId: input.chartId,
      userId: input.userId,
      module: 'consume',
    })
    await setConversationSelection(input.userId, input.conversationId, selection)
    authoritativeSelection = selection
  } else {
    authoritativeSelection = await getConversationSelection(input.userId, input.conversationId)
    if (!isDeepStrictEqual(authoritativeSelection, selection)) throw new AiConsoleError('AI_CHOICE_BROKEN')
  }

  const plan = await resolveUserRouting({
    source: input.source ?? 'pariprashna',
    userId: input.userId,
    selection: authoritativeSelection,
    conversationId: input.conversationId,
    turnId: input.turnId,
  })
  const safeSnapshot = toSafeRoutingSnapshot(plan)
  const snapshotId = await insertRoutingSnapshot(safeSnapshot)
  const admission = admitByokTurn({ userId: input.userId, questionChars: input.questionChars })
  if (!admission.allowed) throw new AiConsoleError(admission.code)

  try {
    const executors = Object.freeze(Object.fromEntries(AI_ROLES.map(role => {
      const executor = createRoleExecutor(plan.roles[role])
      return [role, trackRoleExecutor(executor, { userId: input.userId, snapshotId })]
    })) as ByokTurnRuntime['executors'])
    const synth = safeSnapshot.roles.synthesizer
    const displayModelId = synth.modelId ?? ('cliId' in synth ? `${synth.cliId}:built-in-default` : 'selected-model')
    return Object.freeze({
      kind: 'byok' as const,
      selection: authoritativeSelection,
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
