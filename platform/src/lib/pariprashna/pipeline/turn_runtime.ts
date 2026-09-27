import 'server-only'

import type { ResolvedExecutionPlan } from '@/lib/ai-console/execution/types'
import type { RoleExecutor } from '@/lib/ai-console/execution'
import type { AiRole, ConversationAiSelection } from '@/lib/ai-console/types'
import type { SafeRoutingSnapshot } from '@/lib/ai-console/execution/types'

export interface LegacyTurnRuntime {
  readonly kind: 'legacy'
}

export interface ByokTurnRuntime {
  readonly kind: 'byok'
  readonly selection: ConversationAiSelection
  readonly plan: ResolvedExecutionPlan
  readonly safeSnapshot: SafeRoutingSnapshot
  readonly snapshotId: string
  readonly executors: Readonly<Record<AiRole, RoleExecutor>>
  readonly displayModelId: string
  readonly releaseAdmission: () => void
}

export type TurnRuntime = LegacyTurnRuntime | ByokTurnRuntime

export const LEGACY_TURN_RUNTIME: LegacyTurnRuntime = Object.freeze({ kind: 'legacy' })
