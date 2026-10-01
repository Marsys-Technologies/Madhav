export type MeteringChannel = 'web' | 'mcp' | 'api' | 'backend' | 'scheduled' | 'unknown'
export type MeteringPurpose = 'customer' | 'admin_test' | 'validation' | 'evaluation' | 'background' | 'legacy'
export type AttemptStatus = 'success' | 'error' | 'timeout' | 'cancelled' | 'incomplete'
export interface MeteringContext {
  userId: string
  conversationId: string | null
  turnId: string
  operationId: string
  parentOperationId?: string | null
  channel: MeteringChannel
  purpose: MeteringPurpose
  payer: 'user' | 'platform' | 'subscription' | 'unknown'
  provider: string
  model: string
  role: string
  connectionId?: string | null
  snapshotId?: string | null
  testRunId?: string | null
  requestedModel?: string | null
  aggregation: 'transport' | 'cli_aggregate' | 'legacy_aggregate'
}
export interface UsageEvidence {
  input: number | null
  uncachedInput: number | null
  cacheRead: number | null
  cacheWrite: number | null
  output: number | null
  textOutput: number | null
  reasoning: number | null
  source: 'provider_reported' | 'client_reported' | 'legacy_reported' | 'unavailable'
  raw: Record<string, unknown>
  issues: string[]
}
export interface AttemptStart extends MeteringContext {
  attemptId: string
  startedAt: string
}
export interface AttemptReceipt {
  attemptId: string
  finishedAt: string
  status: AttemptStatus
  usage: UsageEvidence
  providerRequestId: string | null
  finishReason: string | null
  firstTokenAt: string | null
  providerCostUsd: string | null
}
export const meteringEnabled = () => process.env.MARSYS_FLAG_AI_METERING_ENABLED === 'true'
