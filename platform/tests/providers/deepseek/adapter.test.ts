import { describe, it, expect } from 'vitest';
import { DeepSeekAdapter } from '../../../src/lib/providers/deepseek/adapter';
import { DEEPSEEK_MANIFEST } from '../../../src/lib/providers/deepseek/manifest';
import { CapabilityUnsupportedError } from '../../../src/lib/providers/adapter';

describe('DEEPSEEK_MANIFEST', () => {
  it('validates cleanly at import', () => {
    expect(DEEPSEEK_MANIFEST).toBeDefined();
  });
  it('extendedThinking = inline_blocks', () => {
    expect(DEEPSEEK_MANIFEST.extendedThinking).toBe('inline_blocks');
  });
  it('promptCaching = implicit', () => {
    expect(DEEPSEEK_MANIFEST.promptCaching).toBe('implicit');
  });
  it('webSearch = null', () => {
    expect(DEEPSEEK_MANIFEST.webSearch).toBeNull();
  });
  it('inputImage = false', () => {
    expect(DEEPSEEK_MANIFEST.inputImage).toBe(false);
  });
  it('maxContextTokens = 128_000', () => {
    expect(DEEPSEEK_MANIFEST.maxContextTokens).toBe(128_000);
  });
});

describe('DeepSeekAdapter', () => {
  const adapter = new DeepSeekAdapter();

  it('providerId = deepseek', () => {
    expect(adapter.providerId).toBe('deepseek');
  });

  it('getManifest() returns DEEPSEEK_MANIFEST', () => {
    expect(adapter.getManifest()).toBe(DEEPSEEK_MANIFEST);
  });

  it('chat() yields events', async () => {
    const events = [];
    for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'hi' }], model: 'deepseek-v3' })) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('multimodal() reports all modalities as unsupported (text-only)', () => {
    const r = adapter.multimodal({ inputModalities: ['image', 'audio', 'video', 'pdf'] });
    expect(r.supportedInputModalities).toHaveLength(0);
    expect(r.unsupportedInputModalities).toHaveLength(4);
  });

  it('thinking() returns ThinkingResponse with mode=inline_blocks', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'inline_blocks' });
    expect(result).toBeDefined();
    expect(result.mode).toBe('inline_blocks');
  });

  it('webSearch() throws CapabilityUnsupportedError', () => {
    expect(() => adapter.webSearch({ query: 'test' })).toThrow(CapabilityUnsupportedError);
  });
});
