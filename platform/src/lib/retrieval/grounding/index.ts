/**
 * D3 Grounding Spine — Public API
 * =================================
 * The layer that resolves retrieved L2 signals back to L1 facts,
 * enforcing §N.5 authority and principle #3 (cite-don't-regenerate).
 *
 * Exports:
 *   Types   — GroundedResult, GroundedSignal, L1Fact, GroundingError, etc.
 *   Resolver — resolveSignals(), resolveMetric(), assertNoN5Violations()
 *   DbProxy — makeLiveDbProxy(), makeStubDbProxy() (for tests)
 *   Capability — D3_GROUNDING_CAPABILITIES (per-wave registration, Gate A)
 */

// Types
export type {
  SignalId,
  FactId,
  ChartId,
  AyanamshaId,
  L1Fact,
  GroundedSignal,
  GroundedResult,
  GroundingError,
  GroundingErrorCode,
  GroundingOperationResult,
  GovernedMetric,
  ResolvedMetric,
  MetricResolutionResult,
} from './types'
export { GOVERNED_METRICS } from './types'

// DB proxy (inject-able for testing)
export type { DbProxy, StubData } from './db_proxy'
export { makeLiveDbProxy, makeStubDbProxy } from './db_proxy'

// Core resolver functions
export { resolveSignals, resolveMetric, assertNoN5Violations } from './resolver'

// Capability registration (Gate A: per-wave, not the central index)
export {
  resolveSignalsCapability,
  resolveMetricCapability,
  D3_GROUNDING_CAPABILITIES,
} from './capability'
