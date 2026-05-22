/**
 * A-S12: adapter-contract.test.ts
 * Verifies every adapter implements the full CapabilityAdapter interface.
 * All 13 methods + providerId property must exist and be callable.
 */

import { describe, it, expect } from 'vitest';
import { AnthropicAdapter } from '../../src/lib/providers/anthropic/adapter';
import { GoogleAdapter } from '../../src/lib/providers/google/adapter';
import { OpenAIAdapter } from '../../src/lib/providers/openai/adapter';
import { DeepSeekAdapter } from '../../src/lib/providers/deepseek/adapter';
import { NVIDIAAdapter } from '../../src/lib/providers/nvidia/adapter';
import type { CapabilityAdapter } from '../../src/lib/providers/adapter';

const CONTRACT_METHODS: (keyof CapabilityAdapter)[] = [
  'chat',
  'thinking',
  'cache',
  'tools',
  'webSearch',
  'webFetch',
  'codeExecution',
  'memory',
  'multimodal',
  'imageGeneration',
  'computerUse',
  'structuredOutputs',
  'getManifest',
];

const ADAPTERS: Array<{ name: string; adapter: CapabilityAdapter }> = [
  { name: 'AnthropicAdapter', adapter: new AnthropicAdapter() },
  { name: 'GoogleAdapter', adapter: new GoogleAdapter() },
  { name: 'OpenAIAdapter', adapter: new OpenAIAdapter() },
  { name: 'DeepSeekAdapter', adapter: new DeepSeekAdapter() },
  { name: 'NVIDIAAdapter', adapter: new NVIDIAAdapter() },
];

for (const { name, adapter } of ADAPTERS) {
  describe(`${name} — interface contract`, () => {
    it('has readonly providerId string', () => {
      expect(typeof adapter.providerId).toBe('string');
      expect(adapter.providerId.length).toBeGreaterThan(0);
    });

    for (const method of CONTRACT_METHODS) {
      it(`has method: ${method}`, () => {
        expect(typeof adapter[method]).toBe('function');
      });
    }

    it('has exactly 13 interface methods + providerId', () => {
      const actualMethods = CONTRACT_METHODS.filter(m => typeof adapter[m] === 'function');
      expect(actualMethods).toHaveLength(13);
    });
  });
}
