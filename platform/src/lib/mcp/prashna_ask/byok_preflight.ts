import 'server-only'

import { AiConsoleError } from '@/lib/ai-console/errors'
import { createRoleExecutor, type RoleExecutor } from '@/lib/ai-console/execution'
import { trackRoleExecutor } from '@/lib/ai-console/execution/tracked-executor'
import { buildResolvedExecutionPlan } from '@/lib/ai-console/routing'
import { authorizeMcpPrincipal, prepareMcpRouting } from '@/lib/ai-console/repository'
import { admitByokTurn } from '@/lib/limits/byok_admission'
import type { SafeRoutingSnapshot, ResolvedExecutionPlan } from '@/lib/ai-console/execution/types'

export interface PreparedMcpByokRuntime {
  readonly role: 'super_admin' | 'guest'
  readonly plan: ResolvedExecutionPlan
  readonly safeSnapshot: SafeRoutingSnapshot
  readonly snapshotId: string
  readonly executors: Readonly<{
    planner: RoleExecutor
    deep_planner: RoleExecutor
    worker: RoleExecutor
  }>
  readonly releaseAdmission: () => void
}

export async function authorizeMcpByokPrincipal(input: {
  userId: string
  keyId: string
  authKind: 'api_key' | 'oauth'
  chartId: string
}): Promise<{ role: 'super_admin' | 'guest' }> {
  return authorizeMcpPrincipal(input)
}

export async function prepareMcpByokRuntime(input: {
  userId: string
  keyId: string
  authKind: 'api_key' | 'oauth'
  chartId: string
  correlationId: string
  questionChars: number
}): Promise<PreparedMcpByokRuntime> {
  const prepared = await prepareMcpRouting({
    userId: input.userId,
    keyId: input.keyId,
    authKind: input.authKind,
    chartId: input.chartId,
    correlationId: input.correlationId,
  })
  const plan = buildResolvedExecutionPlan({
    source: 'mcp',
    userId: input.userId,
    selection: prepared.selection,
    turnId: input.correlationId,
  }, prepared.resolution)
  const admission = admitByokTurn({ userId: input.userId, questionChars: input.questionChars })
  if (!admission.allowed) throw new AiConsoleError(admission.code)
  try {
    const make = (role: 'planner' | 'deep_planner' | 'worker') => trackRoleExecutor(
      createRoleExecutor(plan.roles[role]),
      { userId: input.userId, snapshotId: prepared.snapshotId,
        observation: { snapshot: prepared.safeSnapshot } },
    )
    return Object.freeze({
      role: prepared.role,
      plan,
      safeSnapshot: prepared.safeSnapshot,
      snapshotId: prepared.snapshotId,
      executors: Object.freeze({
        planner: make('planner'),
        deep_planner: make('deep_planner'),
        worker: make('worker'),
      }),
      releaseAdmission: admission.release,
    })
  } catch (error) {
    admission.release()
    throw error
  }
}
