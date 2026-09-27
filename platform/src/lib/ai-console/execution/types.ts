import 'server-only'
import type { RuntimeModelBinding } from '../providers/types'
import type { PublicAiError } from '../errors'
import type {
  AiChoiceRef, AiRole, AiSource, ConversationAiSelection, ResolvedRoleTarget, RoutingSnapshot,
} from '../types'

export type SafeRoutingSnapshot = RoutingSnapshot
export type ProviderRuntimeFailure = Omit<PublicAiError, 'code'> & { code:
  | 'AI_CONNECTION_INVALID'
  | 'AI_MODEL_UNAVAILABLE'
  | 'AI_ROLE_INCOMPATIBLE'
  | 'AI_PROVIDER_UNREACHABLE'
  | 'AI_PERMISSION_DENIED'
  | 'AI_BILLING_UNAVAILABLE'
  | 'AI_RATE_LIMITED'
}

export interface ResolvedRoleExecution {
  readonly role: AiRole
  readonly adapterType: 'provider' | 'cli'
  readonly target: ResolvedRoleTarget
  /** Present only for provider-backed roles; deliberately non-enumerable. */
  readonly createRuntimeBinding?: () => Promise<RuntimeModelBinding>
  /** Exact-version runtime health update; deliberately non-enumerable. */
  readonly markRuntimeFailure?: (error: ProviderRuntimeFailure) => Promise<void>
}

export interface ResolvedExecutionPlan {
  readonly source: AiSource
  readonly userId: string
  readonly correlationId: string
  readonly conversationId: string | null
  readonly selection: ConversationAiSelection
  readonly resolvedChoice: AiChoiceRef
  readonly configurationVersion: number | null
  readonly roles: Readonly<Record<AiRole, ResolvedRoleExecution>>
  /** Request-local observation timestamp. It is not part of the persisted schema. */
  readonly resolvedAt: string
}
