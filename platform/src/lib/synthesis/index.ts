// Legacy synthesis trio (single_model_strategy / panel_strategy / orchestrator)
// deleted by Stream A unit 3.legacy_delete 2026-05-28. The adapter dispatch
// pipeline (platform/src/lib/providers/) is the only synthesis path now.
// Types are retained here as the audit consumer + performance ingestion still
// reference SynthesisAuditEvent / SynthesisRequest / SynthesisResult for their
// event-shape contracts.
export type {
  SynthesisRequest,
  SynthesisResult,
  SynthesisMetadata,
  SynthesisAuditEvent,
  SynthesisOrchestrator,
} from './types'
