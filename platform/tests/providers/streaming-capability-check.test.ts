/**
 * C-S0: streaming-capability-check.test.ts
 *
 * R11.CDE stream-2 entry-point. Verifies all 5 provider manifests correctly
 * declare their streaming-relevant capabilities per CAPABILITY_MATRIX §9.
 *
 * Streaming-relevant fields:
 *   - smoothStreaming        — always true via Marsys server adapter
 *   - extendedThinking       — thinking variant used by this provider
 *   - interleavedThinkingTool — whether thinking + tool use can interleave
 *   - adaptiveToolLoop       — stop-reason signal for agentic loops
 */

import { describe, it, expect } from 'vitest';
import { ANTHROPIC_MANIFEST } from '../../src/lib/providers/anthropic/manifest';
import { GOOGLE_MANIFEST } from '../../src/lib/providers/google/manifest';
import { OPENAI_MANIFEST } from '../../src/lib/providers/openai/manifest';
import { DEEPSEEK_MANIFEST } from '../../src/lib/providers/deepseek/manifest';
import { NVIDIA_MANIFEST } from '../../src/lib/providers/nvidia/manifest';
import { getAllManifests } from '../../src/lib/providers/dispatcher';

// ---------------------------------------------------------------------------
// smoothStreaming — must be true for all providers (Marsys adapter layer)
// ---------------------------------------------------------------------------

describe('C-S0: smoothStreaming — all 5 providers', () => {
  it('ANTHROPIC_MANIFEST.smoothStreaming is true', () => {
    expect(ANTHROPIC_MANIFEST.smoothStreaming).toBe(true);
  });

  it('GOOGLE_MANIFEST.smoothStreaming is true', () => {
    expect(GOOGLE_MANIFEST.smoothStreaming).toBe(true);
  });

  it('OPENAI_MANIFEST.smoothStreaming is true', () => {
    expect(OPENAI_MANIFEST.smoothStreaming).toBe(true);
  });

  it('DEEPSEEK_MANIFEST.smoothStreaming is true', () => {
    expect(DEEPSEEK_MANIFEST.smoothStreaming).toBe(true);
  });

  it('NVIDIA_MANIFEST.smoothStreaming is true', () => {
    expect(NVIDIA_MANIFEST.smoothStreaming).toBe(true);
  });

  it('all providers in getAllManifests() have smoothStreaming=true', () => {
    const all = getAllManifests();
    for (const [provider, manifest] of Object.entries(all)) {
      expect(manifest.smoothStreaming, `${provider}.smoothStreaming`).toBe(true);
    }
  });
});

// ---------------------------------------------------------------------------
// extendedThinking — per-provider variant assertions
// ---------------------------------------------------------------------------

describe('C-S0: extendedThinking — per-provider variants', () => {
  it('Anthropic uses native_effort (Opus/Sonnet 4.6+ effort-based)', () => {
    expect(ANTHROPIC_MANIFEST.extendedThinking).toBe('native_effort');
  });

  it('Google uses native_budget (Gemini 2.5 thinkingBudget integer)', () => {
    expect(GOOGLE_MANIFEST.extendedThinking).toBe('native_budget');
  });

  it('OpenAI uses polyfill_cot (chain-of-thought system prompt nudge)', () => {
    expect(OPENAI_MANIFEST.extendedThinking).toBe('polyfill_cot');
  });

  it('DeepSeek uses inline_blocks (<think>…</think> via extractReasoningMiddleware)', () => {
    expect(DEEPSEEK_MANIFEST.extendedThinking).toBe('inline_blocks');
  });

  it('NVIDIA has null extendedThinking (not enabled in Marsys NIM config)', () => {
    expect(NVIDIA_MANIFEST.extendedThinking).toBeNull();
  });

  it('native thinking providers (anthropic + google) are the only two', () => {
    const all = getAllManifests();
    const nativeProviders = Object.entries(all)
      .filter(([, m]) => m.extendedThinking === 'native_effort' || m.extendedThinking === 'native_budget')
      .map(([id]) => id)
      .sort();
    expect(nativeProviders).toEqual(['anthropic', 'google']);
  });
});

// ---------------------------------------------------------------------------
// interleavedThinkingTool — only Anthropic + Google
// ---------------------------------------------------------------------------

describe('C-S0: interleavedThinkingTool — only native-thinking providers', () => {
  it('ANTHROPIC_MANIFEST.interleavedThinkingTool is true', () => {
    expect(ANTHROPIC_MANIFEST.interleavedThinkingTool).toBe(true);
  });

  it('GOOGLE_MANIFEST.interleavedThinkingTool is true', () => {
    expect(GOOGLE_MANIFEST.interleavedThinkingTool).toBe(true);
  });

  it('OPENAI_MANIFEST.interleavedThinkingTool is false (polyfill_cot, no native)', () => {
    expect(OPENAI_MANIFEST.interleavedThinkingTool).toBe(false);
  });

  it('DEEPSEEK_MANIFEST.interleavedThinkingTool is false (inline blocks, no interleave)', () => {
    expect(DEEPSEEK_MANIFEST.interleavedThinkingTool).toBe(false);
  });

  it('NVIDIA_MANIFEST.interleavedThinkingTool is false (no thinking support)', () => {
    expect(NVIDIA_MANIFEST.interleavedThinkingTool).toBe(false);
  });

  it('all providers with extendedThinking=null have interleavedThinkingTool=false', () => {
    const all = getAllManifests();
    for (const [provider, manifest] of Object.entries(all)) {
      if (manifest.extendedThinking === null) {
        expect(
          manifest.interleavedThinkingTool,
          `${provider}: null thinking → no interleave`
        ).toBe(false);
      }
    }
  });
});

// ---------------------------------------------------------------------------
// adaptiveToolLoop — stop-reason signals per provider
// ---------------------------------------------------------------------------

describe('C-S0: adaptiveToolLoop — stop-reason signals', () => {
  it('Anthropic uses stop_reason (stop_reason === "tool_use")', () => {
    expect(ANTHROPIC_MANIFEST.adaptiveToolLoop).toBe('stop_reason');
  });

  it('Google uses finish_reason_function_calls', () => {
    expect(GOOGLE_MANIFEST.adaptiveToolLoop).toBe('finish_reason_function_calls');
  });

  it('OpenAI uses finish_reason_tool_calls (OpenAI-compat)', () => {
    expect(OPENAI_MANIFEST.adaptiveToolLoop).toBe('finish_reason_tool_calls');
  });

  it('DeepSeek uses finish_reason_tool_calls (OpenAI-compat)', () => {
    expect(DEEPSEEK_MANIFEST.adaptiveToolLoop).toBe('finish_reason_tool_calls');
  });

  it('NVIDIA uses finish_reason_tool_calls (OpenAI-compat baseline)', () => {
    expect(NVIDIA_MANIFEST.adaptiveToolLoop).toBe('finish_reason_tool_calls');
  });

  it('no provider has null adaptiveToolLoop (all support tool loops)', () => {
    const all = getAllManifests();
    for (const [provider, manifest] of Object.entries(all)) {
      expect(manifest.adaptiveToolLoop, `${provider}.adaptiveToolLoop`).not.toBeNull();
    }
  });
});

// ---------------------------------------------------------------------------
// Cross-check: interleavedThinkingTool=true implies native thinking variant
// ---------------------------------------------------------------------------

describe('C-S0: invariant — interleavedThinkingTool=true ⟹ native thinking', () => {
  it('any provider with interleavedThinkingTool=true has a native thinking variant', () => {
    const all = getAllManifests();
    for (const [provider, manifest] of Object.entries(all)) {
      if (manifest.interleavedThinkingTool) {
        expect(
          manifest.extendedThinking,
          `${provider}: interleaved implies native thinking`
        ).toMatch(/^native_/);
      }
    }
  });
});
