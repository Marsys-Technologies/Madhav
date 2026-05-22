/**
 * A-S10: migration-adapter.test.ts
 * Tests for the MigrationAdapter and its delegation from all 5 provider adapters.
 */

import { describe, it, expect } from 'vitest';
import { MigrationAdapter, migrationAdapter } from '../../src/lib/providers/migration-adapter';
import { AnthropicAdapter } from '../../src/lib/providers/anthropic/adapter';
import { GoogleAdapter } from '../../src/lib/providers/google/adapter';
import { OpenAIAdapter } from '../../src/lib/providers/openai/adapter';
import { DeepSeekAdapter } from '../../src/lib/providers/deepseek/adapter';
import { NVIDIAAdapter } from '../../src/lib/providers/nvidia/adapter';
import type { ChatRequest, ChatEvent } from '../../src/lib/providers/types';

const MINIMAL_REQUEST: ChatRequest = {
  messages: [{ role: 'user', content: 'hi' }],
  model: 'test-model',
};

const EMPTY_REQUEST: ChatRequest = {
  messages: [],
  model: 'test-model',
};

// ---------------------------------------------------------------------------
// MigrationAdapter unit tests
// ---------------------------------------------------------------------------

describe('MigrationAdapter.stubChat', () => {
  const adapter = new MigrationAdapter();

  it('yields events for a valid request', async () => {
    const events: ChatEvent[] = [];
    for await (const e of adapter.stubChat(MINIMAL_REQUEST, 'anthropic')) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('emits text_delta event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of adapter.stubChat(MINIMAL_REQUEST, 'google')) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'text_delta')).toBe(true);
  });

  it('emits usage event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of adapter.stubChat(MINIMAL_REQUEST, 'openai')) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'usage')).toBe(true);
  });

  it('emits message_stop event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of adapter.stubChat(MINIMAL_REQUEST, 'deepseek')) {
      events.push(e);
    }
    const stop = events.find(e => e.type === 'message_stop');
    expect(stop).toBeDefined();
    if (stop && stop.type === 'message_stop') {
      expect(typeof stop.stopReason).toBe('string');
    }
  });

  it('emits error event for empty messages', async () => {
    const events: ChatEvent[] = [];
    for await (const e of adapter.stubChat(EMPTY_REQUEST, 'nvidia')) {
      events.push(e);
    }
    expect(events[0]?.type).toBe('error');
  });
});

describe('MigrationAdapter.bridge', () => {
  const adapter = new MigrationAdapter();

  it('delegates to providerChat generator and passes events through', async () => {
    async function* providerGen(req: ChatRequest): AsyncIterable<ChatEvent> {
      yield { type: 'text_delta', text: 'hello' };
      yield { type: 'message_stop', stopReason: 'end_turn' };
    }

    const events: ChatEvent[] = [];
    for await (const e of adapter.bridge(MINIMAL_REQUEST, 'anthropic', providerGen)) {
      events.push(e);
    }
    expect(events).toHaveLength(2);
    expect(events[0]).toEqual({ type: 'text_delta', text: 'hello' });
  });

  it('emits error for empty messages', async () => {
    async function* providerGen(_req: ChatRequest): AsyncIterable<ChatEvent> {
      yield { type: 'text_delta', text: 'never' };
    }

    const events: ChatEvent[] = [];
    for await (const e of adapter.bridge(EMPTY_REQUEST, 'google', providerGen)) {
      events.push(e);
    }
    expect(events[0]?.type).toBe('error');
  });
});

// ---------------------------------------------------------------------------
// Singleton export
// ---------------------------------------------------------------------------

describe('migrationAdapter singleton', () => {
  it('is an instance of MigrationAdapter', () => {
    expect(migrationAdapter).toBeInstanceOf(MigrationAdapter);
  });
});

// ---------------------------------------------------------------------------
// Per-provider adapter delegation (regression gate)
// ---------------------------------------------------------------------------

describe('AnthropicAdapter chat() delegation', () => {
  it('routes through migrationAdapter and yields events', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new AnthropicAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('sequence includes message_stop', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new AnthropicAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'message_stop')).toBe(true);
  });
});

describe('GoogleAdapter chat() delegation', () => {
  it('yields events', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new GoogleAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });
});

describe('OpenAIAdapter chat() delegation', () => {
  it('yields events', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new OpenAIAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });
});

describe('DeepSeekAdapter chat() delegation', () => {
  it('yields events (with migration adapter stub, no extractReasoningMiddleware yet)', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new DeepSeekAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });
});

describe('NVIDIAAdapter chat() delegation', () => {
  it('yields events (with migration adapter stub)', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new NVIDIAAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// All 5 adapters include MigrationAdapter reference
// ---------------------------------------------------------------------------

describe('All adapters reference MigrationAdapter (A-S10 delegation)', () => {
  it('anthropic delegates (emits usage event)', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new AnthropicAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'usage')).toBe(true);
  });

  it('google delegates (emits usage event)', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new GoogleAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'usage')).toBe(true);
  });

  it('openai delegates (emits usage event)', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new OpenAIAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'usage')).toBe(true);
  });

  it('deepseek delegates (emits usage event)', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new DeepSeekAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'usage')).toBe(true);
  });

  it('nvidia delegates (emits usage event)', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new NVIDIAAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.some(e => e.type === 'usage')).toBe(true);
  });
});
