/**
 * A-S7: dispatcher.test.ts
 * Tests for the capability dispatcher: registry, routing, error handling.
 */

import { describe, it, expect } from 'vitest';
import {
  getAdapter,
  getManifest,
  getAllManifests,
  isCapabilityAvailable,
  getSwitchStackHint,
  CapabilityUnsupportedOnStackError,
  VALID_STACK_IDS,
  type StackId,
} from '../../src/lib/providers/dispatcher';
import { CapabilityUnsupportedError } from '../../src/lib/providers/adapter';
import { AnthropicAdapter } from '../../src/lib/providers/anthropic/adapter';
import { GoogleAdapter } from '../../src/lib/providers/google/adapter';
import { OpenAIAdapter } from '../../src/lib/providers/openai/adapter';
import { DeepSeekAdapter } from '../../src/lib/providers/deepseek/adapter';
import { NVIDIAAdapter } from '../../src/lib/providers/nvidia/adapter';

// ---------------------------------------------------------------------------
// VALID_STACK_IDS
// ---------------------------------------------------------------------------

describe('VALID_STACK_IDS', () => {
  it('contains all 5 providers', () => {
    expect(VALID_STACK_IDS).toHaveLength(5);
    expect(VALID_STACK_IDS).toContain('anthropic');
    expect(VALID_STACK_IDS).toContain('google');
    expect(VALID_STACK_IDS).toContain('openai');
    expect(VALID_STACK_IDS).toContain('deepseek');
    expect(VALID_STACK_IDS).toContain('nvidia');
  });
});

// ---------------------------------------------------------------------------
// getAdapter
// ---------------------------------------------------------------------------

describe('getAdapter', () => {
  it('returns AnthropicAdapter for anthropic', () => {
    expect(getAdapter('anthropic')).toBeInstanceOf(AnthropicAdapter);
  });

  it('returns GoogleAdapter for google', () => {
    expect(getAdapter('google')).toBeInstanceOf(GoogleAdapter);
  });

  it('returns OpenAIAdapter for openai', () => {
    expect(getAdapter('openai')).toBeInstanceOf(OpenAIAdapter);
  });

  it('returns DeepSeekAdapter for deepseek', () => {
    expect(getAdapter('deepseek')).toBeInstanceOf(DeepSeekAdapter);
  });

  it('returns NVIDIAAdapter for nvidia', () => {
    expect(getAdapter('nvidia')).toBeInstanceOf(NVIDIAAdapter);
  });

  it('throws RangeError for unknown stack ID', () => {
    expect(() => getAdapter('unknown' as StackId)).toThrow(RangeError);
  });

  it('error message includes stack ID for unknown stack', () => {
    let msg = '';
    try {
      getAdapter('xai' as StackId);
    } catch (e) {
      msg = (e as RangeError).message;
    }
    expect(msg).toContain('xai');
  });
});

// ---------------------------------------------------------------------------
// getManifest
// ---------------------------------------------------------------------------

describe('getManifest', () => {
  it('returns a valid manifest for each stack', () => {
    for (const stackId of VALID_STACK_IDS) {
      const manifest = getManifest(stackId);
      expect(manifest).toBeDefined();
      expect(typeof manifest.maxContextTokens).toBe('number');
    }
  });

  it('anthropic manifest has 1M context', () => {
    expect(getManifest('anthropic').maxContextTokens).toBe(1_000_000);
  });

  it('google manifest has 2M context', () => {
    expect(getManifest('google').maxContextTokens).toBe(2_000_000);
  });

  it('throws RangeError for unknown stack ID', () => {
    expect(() => getManifest('xai' as StackId)).toThrow(RangeError);
  });
});

// ---------------------------------------------------------------------------
// getAllManifests
// ---------------------------------------------------------------------------

describe('getAllManifests', () => {
  it('returns manifests for all 5 stacks', () => {
    const all = getAllManifests();
    expect(Object.keys(all)).toHaveLength(5);
    for (const stackId of VALID_STACK_IDS) {
      expect(all[stackId]).toBeDefined();
    }
  });
});

// ---------------------------------------------------------------------------
// isCapabilityAvailable
// ---------------------------------------------------------------------------

describe('isCapabilityAvailable', () => {
  it('anthropic supports webSearch (first_party)', () => {
    expect(isCapabilityAvailable('webSearch', 'anthropic')).toBe(true);
  });

  it('deepseek does NOT support webSearch (null)', () => {
    expect(isCapabilityAvailable('webSearch', 'deepseek')).toBe(false);
  });

  it('nvidia does NOT support extendedThinking (null)', () => {
    expect(isCapabilityAvailable('extendedThinking', 'nvidia')).toBe(false);
  });

  it('google supports extendedThinking (native_budget)', () => {
    expect(isCapabilityAvailable('extendedThinking', 'google')).toBe(true);
  });

  it('deepseek does NOT support inputImage (false)', () => {
    expect(isCapabilityAvailable('inputImage', 'deepseek')).toBe(false);
  });

  it('anthropic supports inputImage (true)', () => {
    expect(isCapabilityAvailable('inputImage', 'anthropic')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// getSwitchStackHint
// ---------------------------------------------------------------------------

describe('getSwitchStackHint', () => {
  it('returns null when capability is available on current stack', () => {
    expect(getSwitchStackHint('webSearch', 'anthropic')).toBeNull();
  });

  it('returns a suggested stack when capability not on current stack', () => {
    const hint = getSwitchStackHint('webSearch', 'deepseek');
    expect(hint).not.toBeNull();
    expect(hint?.suggestedStack).toBeDefined();
    // Should suggest a stack that has webSearch
    if (hint) {
      expect(isCapabilityAvailable('webSearch', hint.suggestedStack)).toBe(true);
    }
  });

  it('returns a suggested stack for extendedThinking when on nvidia', () => {
    const hint = getSwitchStackHint('extendedThinking', 'nvidia');
    expect(hint).not.toBeNull();
    // anthropic, google, deepseek all support some form of extended thinking
    if (hint) {
      expect(isCapabilityAvailable('extendedThinking', hint.suggestedStack)).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// CapabilityUnsupportedOnStackError
// ---------------------------------------------------------------------------

describe('CapabilityUnsupportedOnStackError', () => {
  it('has correct name', () => {
    const inner = new CapabilityUnsupportedError('cache', 'anthropic');
    const outer = new CapabilityUnsupportedOnStackError('cache', 'anthropic', inner);
    expect(outer.name).toBe('CapabilityUnsupportedOnStackError');
  });

  it('exposes capability, stackId, originalError', () => {
    const inner = new CapabilityUnsupportedError('memory', 'deepseek');
    const outer = new CapabilityUnsupportedOnStackError('memory', 'deepseek', inner);
    expect(outer.capability).toBe('memory');
    expect(outer.stackId).toBe('deepseek');
    expect(outer.originalError).toBe(inner);
  });

  it('is an instance of Error', () => {
    const inner = new CapabilityUnsupportedError('computerUse', 'deepseek');
    const outer = new CapabilityUnsupportedOnStackError('computerUse', 'deepseek', inner);
    expect(outer).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// Adapter routing via getAdapter — smoke calls
// ---------------------------------------------------------------------------

describe('Adapter smoke routing', () => {
  it('routes chat to anthropic adapter and gets events', async () => {
    const adapter = getAdapter('anthropic');
    const events = [];
    for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'hi' }], model: 'claude-sonnet-4-6' })) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('routes chat to google adapter and gets events', async () => {
    const adapter = getAdapter('google');
    const events = [];
    for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'hi' }], model: 'gemini-2.5-pro' })) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('unsupported capability throws CapabilityUnsupportedError (not re-raised by getAdapter)', () => {
    const adapter = getAdapter('deepseek');
    expect(() => adapter.webSearch({ query: 'test' })).toThrow(CapabilityUnsupportedError);
  });
});
