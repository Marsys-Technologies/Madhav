import { describe, it, expect } from 'vitest';
import { GoogleAdapter } from '../../../src/lib/providers/google/adapter';
import { googleProviderManifest } from '../../../src/lib/providers/google/manifest';
import { CapabilityUnsupportedError } from '../../../src/lib/providers/adapter';

describe('googleProviderManifest', () => {
  it('validates cleanly at import', () => {
    expect(googleProviderManifest).toBeDefined();
  });
  it('extendedThinking = native_budget', () => {
    expect(googleProviderManifest.extendedThinking).toBe('native_budget');
  });
  it('promptCaching = cached_content_api', () => {
    expect(googleProviderManifest.promptCaching).toBe('cached_content_api');
  });
  it('webSearch = grounding', () => {
    expect(googleProviderManifest.webSearch).toBe('grounding');
  });
  it('maxContextTokens = 2_000_000', () => {
    expect(googleProviderManifest.maxContextTokens).toBe(2_000_000);
  });
  it('inputAudio = true', () => {
    expect(googleProviderManifest.inputAudio).toBe(true);
  });
  it('inputVideo = true', () => {
    expect(googleProviderManifest.inputVideo).toBe(true);
  });
});

describe('GoogleAdapter', () => {
  const adapter = new GoogleAdapter();

  it('providerId = google', () => {
    expect(adapter.providerId).toBe('google');
  });

  it('getManifest() returns googleProviderManifest', () => {
    expect(adapter.getManifest()).toBe(googleProviderManifest);
  });

  it('chat() yields events', async () => {
    const events = [];
    for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'hi' }], model: 'gemini-2.5-pro' })) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('multimodal() reports all modalities supported', () => {
    const r = adapter.multimodal({ inputModalities: ['image', 'audio', 'video', 'pdf'] });
    expect(r.supportedInputModalities).toHaveLength(4);
    expect(r.unsupportedInputModalities).toHaveLength(0);
  });

  it('thinking() returns ThinkingResponse with mode=native_budget', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_budget' });
    expect(result).toBeDefined();
    expect(result.mode).toBe('native_budget');
  });

  it('computerUse() throws CapabilityUnsupportedError', async () => {
    const iter = adapter.computerUse({ task: 'test' })[Symbol.asyncIterator]();
    await expect(iter.next()).rejects.toThrow(CapabilityUnsupportedError);
  });
});
