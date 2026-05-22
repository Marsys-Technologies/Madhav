import { describe, it, expect } from 'vitest';
import { NVIDIAAdapter } from '../../../src/lib/providers/nvidia/adapter';
import { NVIDIA_MANIFEST } from '../../../src/lib/providers/nvidia/manifest';
import { CapabilityUnsupportedError } from '../../../src/lib/providers/adapter';

describe('NVIDIA_MANIFEST', () => {
  it('validates cleanly at import', () => {
    expect(NVIDIA_MANIFEST).toBeDefined();
  });
  it('extendedThinking = null', () => {
    expect(NVIDIA_MANIFEST.extendedThinking).toBeNull();
  });
  it('adaptiveToolLoop = finish_reason_tool_calls', () => {
    expect(NVIDIA_MANIFEST.adaptiveToolLoop).toBe('finish_reason_tool_calls');
  });
  it('inputImage = true (llama3.2-vision)', () => {
    expect(NVIDIA_MANIFEST.inputImage).toBe(true);
  });
  it('maxContextTokens = 131_072', () => {
    expect(NVIDIA_MANIFEST.maxContextTokens).toBe(131_072);
  });
});

describe('NVIDIAAdapter', () => {
  const adapter = new NVIDIAAdapter();

  it('providerId = nvidia', () => {
    expect(adapter.providerId).toBe('nvidia');
  });

  it('getManifest() returns NVIDIA_MANIFEST', () => {
    expect(adapter.getManifest()).toBe(NVIDIA_MANIFEST);
  });

  it('chat() yields events', async () => {
    const events = [];
    for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'hi' }], model: 'meta/llama-3.3-70b-instruct' })) {
      events.push(e);
    }
    expect(events.length).toBeGreaterThan(0);
  });

  it('multimodal() reports image as supported, others not', () => {
    const r = adapter.multimodal({ inputModalities: ['image', 'audio', 'video', 'pdf'] });
    expect(r.supportedInputModalities).toContain('image');
    expect(r.unsupportedInputModalities).toContain('audio');
    expect(r.unsupportedInputModalities).toContain('video');
    expect(r.unsupportedInputModalities).toContain('pdf');
  });

  it('thinking() throws CapabilityUnsupportedError', () => {
    expect(() => adapter.thinking({ extendedThinkingMode: null })).toThrow(CapabilityUnsupportedError);
  });
});
