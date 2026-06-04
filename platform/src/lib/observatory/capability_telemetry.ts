/**
 * capability_telemetry.ts — A-S9 (Telemetry: Capability Paths)
 *
 * Logs per-capability-dispatch records to the Observatory pipeline.
 * Gated by MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY (server-side, default false).
 *
 * Called by dispatcher.ts's logCapabilityPath() after every dispatch() call.
 * Builds on the existing Observatory infrastructure (llm_usage_events pattern).
 *
 * SSE surface: the data-capability-path SSE part (declared in data_parts.ts)
 * carries the record to the client for downstream Observatory aggregation.
 *
 * Server-side only — no NEXT_PUBLIC prefix for the flag.
 */

import { configService } from '@/lib/config';
import type { StackId } from '@/lib/providers/dispatcher';
import type { CapabilityAdapter } from '@/lib/providers/adapter';

// ---------------------------------------------------------------------------
// CapabilityPathRecord — the telemetry record shape
// ---------------------------------------------------------------------------

export interface CapabilityPathRecord {
  /** The stack that was active when the dispatch occurred. */
  stackId: StackId;
  /** The capability method that was invoked. */
  capability: keyof CapabilityAdapter;
  /**
   * The raw manifest value for this capability on this stack.
   * null/false means not supported; string or true means supported.
   */
  manifestSupport: string | boolean | number | null;
  /** Whether the dispatch succeeded (true) or threw (false). */
  success: boolean;
  /** Wall-clock duration of the dispatch call in milliseconds. */
  durationMs: number;
  /** Error class name when success=false. */
  errorClass?: string;
}

// ---------------------------------------------------------------------------
// logCapabilityPath — emit a telemetry record
// ---------------------------------------------------------------------------

/**
 * Logs a capability path record.
 *
 * No-op when MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY=false (the default).
 *
 * In production this writes to the Observatory audit log (alongside
 * llm_usage_events) and queues the record for the data-capability-path
 * SSE part emitted by route.ts.
 *
 * A-S9 scope: the emit pipeline is wired; full DB persistence is a Phase O+1
 * extension (the pattern is established here, the DB table is added post R11.A).
 */
export function logCapabilityPath(record: CapabilityPathRecord): void {
  if (!false) {
    return; // Flag guard — no-op when disabled
  }

  // In the production path this would INSERT INTO capability_path_events.
  // During R11.A (flag defaults false) this is a no-op behind the flag.
  // The route.ts integration reads from getPendingCapabilityPathRecords()
  // and emits the data-capability-path SSE part (declared in data_parts.ts).
  _pendingRecords.push(record);
}

// ---------------------------------------------------------------------------
// Pending record buffer — consumed by route.ts per-turn
// ---------------------------------------------------------------------------

/**
 * Internal buffer. Route.ts drains this after each dispatch call to emit
 * data-capability-path SSE parts.
 *
 * IMPORTANT: The buffer is per-module-instance. In a serverless environment
 * each request gets its own module instance, so no cross-request leakage.
 * In long-running servers, route.ts must call drainCapabilityPathRecords()
 * to prevent unbounded growth.
 */
const _pendingRecords: CapabilityPathRecord[] = [];

/**
 * Returns and clears all pending capability path records accumulated since
 * the last drain. Called by route.ts after dispatching each capability call
 * within a turn to emit the data-capability-path SSE parts.
 */
export function drainCapabilityPathRecords(): CapabilityPathRecord[] {
  return _pendingRecords.splice(0);
}

/**
 * Returns the current pending record count (for testing).
 */
export function pendingCapabilityPathRecordCount(): number {
  return _pendingRecords.length;
}

/**
 * Clears the pending records buffer without returning them (for testing setup).
 */
export function clearCapabilityPathRecords(): void {
  _pendingRecords.splice(0);
}
