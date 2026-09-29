import 'server-only'
import { AiConsoleError } from '../errors'
import type { ResolvedRoleExecution } from './types'
import { createCliRoleExecutor } from './cli-executor'
export { createProviderRoleExecutor } from './provider-executor'
export { createDefaultFallbackExecutor } from './fallback-executor'
import { createProviderRoleExecutor } from './provider-executor'

export function createRoleExecutor(execution: ResolvedRoleExecution) {
  if (execution.adapterType === 'provider') return createProviderRoleExecutor(execution)
  if (execution.adapterType === 'cli') return createCliRoleExecutor(execution)
  throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)
}
export type {
  NormalizedUsage, RoleExecutionEvent, RoleExecutionRequest, RoleExecutionResult, RoleExecutor,
  RoleToolCall, SafeProviderExecutorDescriptor, SafeCliExecutorDescriptor, SafeRoleExecutorDescriptor,
} from './provider-executor'
