/**
 * A-S9: capability_telemetry.test.ts
 * Tests for the capability path telemetry module.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  logCapabilityPath,
  drainCapabilityPathRecords,
  pendingCapabilityPathRecordCount,
  clearCapabilityPathRecords,
  type CapabilityPathRecord,
} from '../../src/lib/observatory/capability_telemetry';

// ---------------------------------------------------------------------------
// Mock the configService so we can control the flag
// ---------------------------------------------------------------------------

vi.mock('../../src/lib/config/index', () => ({
  configService: {
    getFlag: vi.fn((flag: string) => {
      // Default: flag is OFF (matching the real default)
      if (flag === 'R11V2_CAPABILITY_TELEMETRY') return false;
      return false;
    }),
  },
}));

import { configService } from '../../src/lib/config/index';

// Helper to set the flag state
function setTelemetryFlag(enabled: boolean): void {
  vi.mocked(configService.getFlag).mockImplementation((flag: string) => {
    if (flag === 'R11V2_CAPABILITY_TELEMETRY') return enabled;
    return false;
  });
}

beforeEach(() => {
  clearCapabilityPathRecords();
  setTelemetryFlag(false); // Default: off
});

// ---------------------------------------------------------------------------
// Flag-off: no records written
// ---------------------------------------------------------------------------

describe('logCapabilityPath — flag OFF', () => {
  it('does not buffer any records when flag is false', () => {
    setTelemetryFlag(false);
    logCapabilityPath({
      stackId: 'anthropic',
      capability: 'chat',
      manifestSupport: null,
      success: true,
      durationMs: 100,
    });
    expect(pendingCapabilityPathRecordCount()).toBe(0);
  });

  it('drain returns empty array when flag is false', () => {
    setTelemetryFlag(false);
    logCapabilityPath({
      stackId: 'google',
      capability: 'webSearch',
      manifestSupport: 'grounding',
      success: true,
      durationMs: 50,
    });
    expect(drainCapabilityPathRecords()).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Flag-on: records written
// ---------------------------------------------------------------------------

describe('logCapabilityPath — flag ON', () => {
  it('buffers a record when flag is true', () => {
    setTelemetryFlag(true);
    logCapabilityPath({
      stackId: 'anthropic',
      capability: 'chat',
      manifestSupport: null,
      success: true,
      durationMs: 120,
    });
    expect(pendingCapabilityPathRecordCount()).toBe(1);
  });

  it('record matches the input shape', () => {
    setTelemetryFlag(true);
    const record: CapabilityPathRecord = {
      stackId: 'google',
      capability: 'webSearch',
      manifestSupport: 'grounding',
      success: true,
      durationMs: 88,
    };
    logCapabilityPath(record);
    const drained = drainCapabilityPathRecords();
    expect(drained).toHaveLength(1);
    expect(drained[0]).toMatchObject(record);
  });

  it('draining clears the buffer', () => {
    setTelemetryFlag(true);
    logCapabilityPath({
      stackId: 'openai',
      capability: 'webSearch',
      manifestSupport: 'preview_api',
      success: true,
      durationMs: 60,
    });
    drainCapabilityPathRecords();
    expect(pendingCapabilityPathRecordCount()).toBe(0);
  });

  it('multiple records accumulate before drain', () => {
    setTelemetryFlag(true);
    logCapabilityPath({ stackId: 'anthropic', capability: 'chat', manifestSupport: null, success: true, durationMs: 10 });
    logCapabilityPath({ stackId: 'google', capability: 'webSearch', manifestSupport: 'grounding', success: true, durationMs: 20 });
    logCapabilityPath({ stackId: 'deepseek', capability: 'chat', manifestSupport: null, success: false, durationMs: 5, errorClass: 'CapabilityUnsupportedError' });
    expect(pendingCapabilityPathRecordCount()).toBe(3);
    const records = drainCapabilityPathRecords();
    expect(records).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------
// Failure paths include errorClass
// ---------------------------------------------------------------------------

describe('logCapabilityPath — failure records', () => {
  it('accepts errorClass on failure records', () => {
    setTelemetryFlag(true);
    const record: CapabilityPathRecord = {
      stackId: 'deepseek',
      capability: 'webSearch',
      manifestSupport: null,
      success: false,
      durationMs: 3,
      errorClass: 'CapabilityUnsupportedOnStackError',
    };
    logCapabilityPath(record);
    const drained = drainCapabilityPathRecords();
    expect(drained[0].errorClass).toBe('CapabilityUnsupportedOnStackError');
    expect(drained[0].success).toBe(false);
  });

  it('success records do not require errorClass', () => {
    setTelemetryFlag(true);
    logCapabilityPath({
      stackId: 'anthropic',
      capability: 'chat',
      manifestSupport: null,
      success: true,
      durationMs: 200,
    });
    const drained = drainCapabilityPathRecords();
    expect(drained[0].errorClass).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// Record shape matches schema
// ---------------------------------------------------------------------------

describe('CapabilityPathRecord schema validation', () => {
  it('stackId is a string', () => {
    setTelemetryFlag(true);
    logCapabilityPath({ stackId: 'nvidia', capability: 'chat', manifestSupport: false, success: true, durationMs: 15 });
    const [rec] = drainCapabilityPathRecords();
    expect(typeof rec.stackId).toBe('string');
  });

  it('capability is a string', () => {
    setTelemetryFlag(true);
    logCapabilityPath({ stackId: 'openai', capability: 'structuredOutputs', manifestSupport: 'json_schema_strict', success: true, durationMs: 30 });
    const [rec] = drainCapabilityPathRecords();
    expect(typeof rec.capability).toBe('string');
  });

  it('durationMs is a non-negative number', () => {
    setTelemetryFlag(true);
    logCapabilityPath({ stackId: 'google', capability: 'chat', manifestSupport: null, success: true, durationMs: 0 });
    const [rec] = drainCapabilityPathRecords();
    expect(rec.durationMs).toBeGreaterThanOrEqual(0);
  });
});
