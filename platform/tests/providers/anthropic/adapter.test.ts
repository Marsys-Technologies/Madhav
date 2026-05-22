/**
 * A-S2: anthropic/adapter.test.ts
 * Tests for AnthropicAdapter skeleton + ANTHROPIC_MANIFEST.
 */

import { describe, it, expect } from 'vitest';
import { AnthropicAdapter } from '../../../src/lib/providers/anthropic/adapter';
import { ANTHROPIC_MANIFEST } from '../../../src/lib/providers/anthropic/manifest';
import { CapabilityUnsupportedError } from '../../../src/lib/providers/adapter';
import { validateManifest } from '../../../src/lib/providers/manifest-validator';

// ---------------------------------------------------------------------------
// Manifest tests
// ---------------------------------------------------------------------------

describe('ANTHROPIC_MANIFEST', () => {
  it('passes validateManifest at module load', () => {
    // The fact that the import succeeded means validateManifest ran without throwing.
    expect(ANTHROPIC_MANIFEST).toBeDefined();
  });

  it('has extendedThinking = native_effort', () => {
    expect(ANTHROPIC_MANIFEST.extendedThinking).toBe('native_effort');
  });

  it('has promptCaching = explicit_4bp', () => {
    expect(ANTHROPIC_MANIFEST.promptCaching).toBe('explicit_4bp');
  });

  it('has adaptiveToolLoop = stop_reason', () => {
    expect(ANTHROPIC_MANIFEST.adaptiveToolLoop).toBe('stop_reason');
  });

  it('has interleavedThinkingTool = true', () => {
    expect(ANTHROPIC_MANIFEST.interleavedThinkingTool).toBe(true);
  });

  it('has webSearch = first_party', () => {
    expect(ANTHROPIC_MANIFEST.webSearch).toBe('first_party');
  });

  it('has webFetch = first_party', () => {
    expect(ANTHROPIC_MANIFEST.webFetch).toBe('first_party');
  });

  it('has codeExecution = first_party', () => {
    expect(ANTHROPIC_MANIFEST.codeExecution).toBe('first_party');
  });

  it('has nativeMemory = memory_tool', () => {
    expect(ANTHROPIC_MANIFEST.nativeMemory).toBe('memory_tool');
  });

  it('has inputImage = true', () => {
    expect(ANTHROPIC_MANIFEST.inputImage).toBe(true);
  });

  it('has inputAudio = false', () => {
    expect(ANTHROPIC_MANIFEST.inputAudio).toBe(false);
  });

  it('has computerUse = computer_use_api', () => {
    expect(ANTHROPIC_MANIFEST.computerUse).toBe('computer_use_api');
  });

  it('has structuredOutputs = tool_force', () => {
    expect(ANTHROPIC_MANIFEST.structuredOutputs).toBe('tool_force');
  });

  it('has maxContextTokens = 1_000_000', () => {
    expect(ANTHROPIC_MANIFEST.maxContextTokens).toBe(1_000_000);
  });

  it('re-validates cleanly (double validation is safe)', () => {
    expect(() => validateManifest(ANTHROPIC_MANIFEST)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Adapter tests
// ---------------------------------------------------------------------------

describe('AnthropicAdapter', () => {
  const adapter = new AnthropicAdapter();

  it('has providerId = anthropic', () => {
    expect(adapter.providerId).toBe('anthropic');
  });

  it('getManifest() returns ANTHROPIC_MANIFEST', () => {
    expect(adapter.getManifest()).toBe(ANTHROPIC_MANIFEST);
  });

  describe('chat()', () => {
    it('yields events for a minimal request', async () => {
      const events = [];
      for await (const event of adapter.chat({
        messages: [{ role: 'user', content: 'Hello' }],
        model: 'claude-sonnet-4-6',
      })) {
        events.push(event);
      }
      expect(events.length).toBeGreaterThan(0);
    });

    it('yields error event for empty messages', async () => {
      const events = [];
      for await (const event of adapter.chat({ messages: [], model: 'claude-sonnet-4-6' })) {
        events.push(event);
      }
      expect(events[0].type).toBe('error');
    });
  });

  describe('capability method responses', () => {
    it('thinking() returns ThinkingResponse with mode=native_effort', () => {
      const result = adapter.thinking({ extendedThinkingMode: 'native_effort' });
      expect(result).toBeDefined();
      expect(result.mode).toBe('native_effort');
    });

    it('cache() returns CacheResponse with mode=explicit_4bp', () => {
      const result = adapter.cache({ cacheMode: 'explicit_4bp' });
      expect(result).toBeDefined();
      expect(result.mode).toBe('explicit_4bp');
    });

    it('tools() returns ToolsResponse with mode=stop_reason', () => {
      const result = adapter.tools({ toolLoopMode: 'stop_reason', tools: [], maxIterations: 8 });
      expect(result).toBeDefined();
      expect(result.mode).toBe('stop_reason');
    });
  });

  describe('unsupported capabilities throw CapabilityUnsupportedError', () => {
    it('webSearch()', () => {
      expect(() => adapter.webSearch({ query: 'test' })).toThrow(CapabilityUnsupportedError);
    });

    it('webFetch()', () => {
      expect(() => adapter.webFetch({ url: 'https://example.com' })).toThrow(
        CapabilityUnsupportedError,
      );
    });

    it('codeExecution()', () => {
      expect(() => adapter.codeExecution({ code: 'print("hi")' })).toThrow(
        CapabilityUnsupportedError,
      );
    });

    it('memory()', () => {
      expect(() => adapter.memory({ operation: 'read' })).toThrow(CapabilityUnsupportedError);
    });

    it('imageGeneration()', () => {
      expect(() => adapter.imageGeneration({ prompt: 'a cat' })).toThrow(
        CapabilityUnsupportedError,
      );
    });

    it('computerUse()', async () => {
      await expect(adapter.computerUse({ task: 'click submit' }).next()).rejects.toThrow(
        CapabilityUnsupportedError,
      );
    });

    it('structuredOutputs()', () => {
      expect(() => adapter.structuredOutputs({ schema: { type: 'object' } })).toThrow(
        CapabilityUnsupportedError,
      );
    });
  });

  describe('multimodal() — synchronous routing', () => {
    it('reports image as supported', () => {
      const result = adapter.multimodal({ inputModalities: ['image'] });
      expect(result.supportedInputModalities).toContain('image');
      expect(result.unsupportedInputModalities).toHaveLength(0);
    });

    it('reports audio as unsupported', () => {
      const result = adapter.multimodal({ inputModalities: ['audio'] });
      expect(result.unsupportedInputModalities).toContain('audio');
      expect(result.supportedInputModalities).toHaveLength(0);
    });

    it('reports pdf as supported', () => {
      const result = adapter.multimodal({ inputModalities: ['pdf'] });
      expect(result.supportedInputModalities).toContain('pdf');
    });

    it('reports video as unsupported', () => {
      const result = adapter.multimodal({ inputModalities: ['video'] });
      expect(result.unsupportedInputModalities).toContain('video');
    });

    it('has no output modalities (Anthropic API)', () => {
      const result = adapter.multimodal({ inputModalities: [], outputModalities: ['voice'] });
      expect(result.supportedOutputModalities).toHaveLength(0);
    });
  });
});
