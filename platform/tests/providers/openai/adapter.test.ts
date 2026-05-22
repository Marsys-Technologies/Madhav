import { describe, it, expect } from 'vitest';
import { OpenAIAdapter } from '../../../src/lib/providers/openai/adapter';
import { OPENAI_MANIFEST } from '../../../src/lib/providers/openai/manifest';
import { CapabilityUnsupportedError } from '../../../src/lib/providers/adapter';

describe('OPENAI_MANIFEST', () => {
  it('validates cleanly at import', () => {
    expect(OPENAI_MANIFEST).toBeDefined();
  });
  it('extendedThinking = polyfill_cot', () => {
    expect(OPENAI_MANIFEST.extendedThinking).toBe('polyfill_cot');
  });
  it('promptCaching = automatic', () => {
    expect(OPENAI_MANIFEST.promptCaching).toBe('automatic');
  });
  it('webSearch = preview_api', () => {
    expect(OPENAI_MANIFEST.webSearch).toBe('preview_api');
  });
  it('structuredOutputs = json_schema_strict', () => {
    expect(OPENAI_MANIFEST.structuredOutputs).toBe('json_schema_strict');
  });
  it('computerUse = cua_responses', () => {
    expect(OPENAI_MANIFEST.computerUse).toBe('cua_responses');
  });
  it('maxContextTokens = 200_000', () => {
    expect(OPENAI_MANIFEST.maxContextTokens).toBe(200_000);
  });
});

describe('OpenAIAdapter', () => {
  const adapter = new OpenAIAdapter();

  it('providerId = openai', () => {
    expect(adapter.providerId).toBe('openai');
  });

  it('getManifest() returns OPENAI_MANIFEST', () => {
    expect(adapter.getManifest()).toBe(OPENAI_MANIFEST);
  });

  it('chat() yields events', async () => {
    const events = [];
    for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'hi' }], model: 'gpt-4.1' })) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('multimodal() reports image + audio + pdf as supported', () => {
    const r = adapter.multimodal({ inputModalities: ['image', 'audio', 'pdf', 'video'] });
    expect(r.supportedInputModalities).toContain('image');
    expect(r.supportedInputModalities).toContain('audio');
    expect(r.supportedInputModalities).toContain('pdf');
    expect(r.unsupportedInputModalities).toContain('video');
  });

  it('thinking() returns ThinkingResponse with mode=polyfill_cot', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'polyfill_cot' });
    expect(result).toBeDefined();
    expect(result.mode).toBe('polyfill_cot');
  });
});
