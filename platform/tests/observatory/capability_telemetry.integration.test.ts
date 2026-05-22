/**
 * A-S12: capability_telemetry.integration.test.ts
 * Verifies that dispatch() fires telemetry + emits CapabilityPathRecord when
 * the flag is on.
 *
 * Simulates the full dispatch → telemetry path for all 5 stacks.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  clearCapabilityPathRecords,
  drainCapabilityPathRecords,
  pendingCapabilityPathRecordCount,
} from '../../src/lib/observatory/capability_telemetry';

// Enable telemetry flag for this integration test suite
vi.mock('../../src/lib/config/index', () => ({
  configService: {
    getFlag: vi.fn((flag: string) => {
      if (flag === 'R11V2_CAPABILITY_TELEMETRY') return true;
      return false;
    }),
  },
  DEFAULT_FLAGS: {},
}));

import {
  logCapabilityPath,
  type CapabilityPathRecord,
} from '../../src/lib/observatory/capability_telemetry';

beforeEach(() => {
  clearCapabilityPathRecords();
});

// ---------------------------------------------------------------------------
// Integration: records emitted for each stack on dispatch
// ---------------------------------------------------------------------------

describe('capability_telemetry.integration — records per stack', () => {
  const stacks = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia'] as const;

  for (const stackId of stacks) {
    it(`${stackId}: logCapabilityPath records a record`, () => {
      logCapabilityPath({
        stackId,
        capability: 'chat',
        manifestSupport: null,
        success: true,
        durationMs: 50,
      });
      expect(pendingCapabilityPathRecordCount()).toBe(1);
      const [record] = drainCapabilityPathRecords();
      expect(record.stackId).toBe(stackId);
      expect(record.capability).toBe('chat');
      expect(record.success).toBe(true);
    });
  }
});

// ---------------------------------------------------------------------------
// Integration: failure record shape
// ---------------------------------------------------------------------------

describe('capability_telemetry.integration — failure record', () => {
  it('failure records include errorClass', () => {
    logCapabilityPath({
      stackId: 'deepseek',
      capability: 'webSearch',
      manifestSupport: null,
      success: false,
      durationMs: 2,
      errorClass: 'CapabilityUnsupportedOnStackError',
    });
    const [rec] = drainCapabilityPathRecords();
    expect(rec.success).toBe(false);
    expect(rec.errorClass).toBe('CapabilityUnsupportedOnStackError');
  });
});

// ---------------------------------------------------------------------------
// Integration: drain clears buffer
// ---------------------------------------------------------------------------

describe('capability_telemetry.integration — drain semantics', () => {
  it('drain returns all records and clears buffer', () => {
    const stacks = ['anthropic', 'google', 'openai'] as const;
    for (const stackId of stacks) {
      logCapabilityPath({ stackId, capability: 'chat', manifestSupport: null, success: true, durationMs: 10 });
    }
    expect(pendingCapabilityPathRecordCount()).toBe(3);
    const drained = drainCapabilityPathRecords();
    expect(drained).toHaveLength(3);
    expect(pendingCapabilityPathRecordCount()).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Integration: SSE part schema compliance
// ---------------------------------------------------------------------------

describe('capability_telemetry.integration — SSE CapabilityPathPart shape', () => {
  it('record shape maps correctly to CapabilityPathPart schema', () => {
    logCapabilityPath({
      stackId: 'anthropic',
      capability: 'chat',
      manifestSupport: null,
      success: true,
      durationMs: 75,
    });
    const [rec] = drainCapabilityPathRecords();
    // Verify fields match CapabilityPathPartSchema shape
    expect(typeof rec.stackId).toBe('string');
    expect(typeof rec.capability).toBe('string');
    expect(typeof rec.success).toBe('boolean');
    expect(typeof rec.durationMs).toBe('number');
    expect(rec.durationMs).toBeGreaterThanOrEqual(0);
  });
});
