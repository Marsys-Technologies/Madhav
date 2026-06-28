/**
 * D6 Synergy Layer — Public API
 * ==============================
 * Exports the whole-corpus synergy orchestrator and types.
 * Both MCP and chat channels import from here.
 */

export { runWholeChartRead } from './orchestrator'
export type { SynergyContext } from './orchestrator'
export type {
  WholeChartReadResult,
  UcdDigest,
  DomainReadingResult,
  SignalRankResult,
  GraphTraversalResult,
  ContradictionResult,
  TemporalEnrichmentResult,
  QualityScorecardResult,
  SynergyQueryClass,
  WholeChartReadMeta,
} from './types'
