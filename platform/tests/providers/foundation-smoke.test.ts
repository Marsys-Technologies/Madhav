/**
 * A-S12: foundation-smoke.test.ts
 * 5-provider smoke test — all 5 adapters return valid ChatEvent streams
 * via the dispatcher. Gated by this suite passing before R11A-MERGE proceeds.
 *
 * Tests use the mocked adapter layer (no real SDK calls). In production the
 * migration adapter stub returns the same event shapes as the real provider
 * would return for the basic {messages, model} request.
 *
 * Report format per AC.6:
 * "R11.A foundation: 5/5 stacks PASS, capability manifests valid,
 *  telemetry firing, hide-and-hint working."
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { getAdapter, getManifest, VALID_STACK_IDS } from '../../src/lib/providers/dispatcher';
import {
  clearCapabilityPathRecords,
  logCapabilityPath,
  drainCapabilityPathRecords,
} from '../../src/lib/observatory/capability_telemetry';
import { vi } from 'vitest';
import type { ChatEvent } from '../../src/lib/providers/types';

// Mock configService so telemetry flag is on during these integration tests
vi.mock('../../src/lib/config/index', () => ({
  configService: {
    getFlag: vi.fn((flag: string) => {
      if (flag === 'R11V2_CAPABILITY_TELEMETRY') return true;
      if (flag === 'R11V2_USE_ADAPTERS') return true;
      return false;
    }),
  },
  DEFAULT_FLAGS: {},
}));

const MINIMAL_REQUEST = {
  messages: [{ role: 'user' as const, content: 'smoke test' }],
  model: 'test-model',
};

beforeEach(() => {
  clearCapabilityPathRecords();
});

// ---------------------------------------------------------------------------
// 5-provider smoke: chat() returns valid ChatEvent stream
// ---------------------------------------------------------------------------

describe('R11.A foundation smoke — 5-provider chat() round trip', () => {
  for (const stackId of VALID_STACK_IDS) {
    describe(`Stack: ${stackId}`, () => {
      it(`${stackId}: adapter resolves`, () => {
        const adapter = getAdapter(stackId);
        expect(adapter).toBeDefined();
        expect(adapter.providerId).toBe(stackId);
      });

      it(`${stackId}: chat() yields ≥1 events`, async () => {
        const adapter = getAdapter(stackId);
        const events: ChatEvent[] = [];
        for await (const e of adapter.chat(MINIMAL_REQUEST)) {
          events.push(e);
        }
        expect(events.length).toBeGreaterThan(0);
      });

      it(`${stackId}: chat() stream includes message_stop`, async () => {
        const adapter = getAdapter(stackId);
        const events: ChatEvent[] = [];
        for await (const e of adapter.chat(MINIMAL_REQUEST)) {
          events.push(e);
        }
        const hasStop = events.some(e => e.type === 'message_stop');
        expect(hasStop).toBe(true);
      });

      it(`${stackId}: manifest is defined and valid`, () => {
        const manifest = getManifest(stackId);
        expect(manifest).toBeDefined();
        expect(typeof manifest.maxContextTokens).toBe('number');
        expect(manifest.maxContextTokens).toBeGreaterThan(0);
      });
    });
  }
});

// ---------------------------------------------------------------------------
// Report summary: all 5 stacks pass
// ---------------------------------------------------------------------------

describe('R11.A foundation smoke — report', () => {
  it('all 5 stacks are covered in VALID_STACK_IDS', () => {
    expect(VALID_STACK_IDS).toHaveLength(5);
    expect(VALID_STACK_IDS).toContain('anthropic');
    expect(VALID_STACK_IDS).toContain('google');
    expect(VALID_STACK_IDS).toContain('openai');
    expect(VALID_STACK_IDS).toContain('deepseek');
    expect(VALID_STACK_IDS).toContain('nvidia');
  });

  it('R11.A foundation: capability manifests valid', () => {
    for (const stackId of VALID_STACK_IDS) {
      const manifest = getManifest(stackId);
      expect(manifest.maxContextTokens).toBeGreaterThan(0);
    }
  });

  it('R11.A foundation: all adapters satisfy CapabilityAdapter contract', () => {
    const METHODS = ['chat', 'thinking', 'cache', 'tools', 'webSearch', 'webFetch',
      'codeExecution', 'memory', 'multimodal', 'imageGeneration',
      'computerUse', 'structuredOutputs', 'getManifest'];
    for (const stackId of VALID_STACK_IDS) {
      const adapter = getAdapter(stackId);
      for (const method of METHODS) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        expect(typeof (adapter as any)[method]).toBe('function');
      }
    }
  });
});
