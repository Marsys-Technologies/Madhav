/**
 * observability/index.ts — surface re-exports.
 *
 * Stream B / unit 4.observability.
 */

export {
  parseTraceparent,
  serializeTraceparent,
  startSpan,
  endSpan,
  fetchWithTrace,
  newTraceId,
  newSpanId,
  type TraceContext,
  type SpanRecord,
} from './trace'
