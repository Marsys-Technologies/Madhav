/**
 * D2 Query Router — Public API
 * ==============================
 * Re-exports the public surface for the D2 retrieval router.
 *
 * Consumers (the grounding spine D3, eval harness D8):
 *   import { route, RouteResult, RouteClass } from '@/lib/retrieval/router'
 */

// ── Public types ──────────────────────────────────────────────────────────────
export type {
  RouteClass,
  RouteResult,
  RouteTrajectory,
  RouteBudget,
  PlannedToolCall,
  RoutingHints,
} from './types'

// ── Main route function ───────────────────────────────────────────────────────
export { route, routeAndExecutePrimary } from './router'
export type { RouteInput } from './router'

// ── Classifier (exported for testing + D8 introspection) ─────────────────────
export { classifyQuery, isModelFallbackEligible } from './classifier'

// ── Tool selector (exported for testing) ─────────────────────────────────────
export { selectTools, getBudget, buildTerminationPolicy } from './tool_selector'
