/**
 * migration-adapter.test.ts
 * Tests for MigrationAdapter.bridge() and per-provider adapter chat() calls.
 * Note: stubChat() was removed in R11 dispatch wiring — all 5 adapters now use
 * real SDK calls. In the test environment (no API keys), real adapters yield
 * error events. Tests verify events.length > 0 (at least an error event emitted).
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
// Per-provider adapter error resilience (no API key in test env)
// All 5 adapters must catch SDK/auth errors and yield { type: 'error' }
// rather than throwing unhandled exceptions.
// ---------------------------------------------------------------------------

describe('All adapters yield events (error resilience without API keys)', () => {
  it('AnthropicAdapter.chat() yields at least one event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new AnthropicAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('GoogleAdapter.chat() yields at least one event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new GoogleAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('OpenAIAdapter.chat() yields at least one event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new OpenAIAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('DeepSeekAdapter.chat() yields at least one event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new DeepSeekAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('NVIDIAAdapter.chat() yields at least one event', async () => {
    const events: ChatEvent[] = [];
    for await (const e of new NVIDIAAdapter().chat(MINIMAL_REQUEST)) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });
});
