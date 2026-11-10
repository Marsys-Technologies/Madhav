/**
 * A-S8: useProviderManifest.test.ts
 * Tests for the useProviderManifest hook.
 */

import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useProviderManifest } from '../../../src/lib/chat-v2/useProviderManifest';
import { ANTHROPIC_MANIFEST } from '../../../src/lib/providers/anthropic/manifest';
import { googleProviderManifest } from '../../../src/lib/providers/google/manifest';
import { OPENAI_MANIFEST } from '../../../src/lib/providers/openai/manifest';
import { DEEPSEEK_MANIFEST } from '../../../src/lib/providers/deepseek/manifest';
import { NVIDIA_MANIFEST } from '../../../src/lib/providers/nvidia/manifest';

describe('useProviderManifest', () => {
  it('returns ANTHROPIC_MANIFEST for anthropic', () => {
    const { result } = renderHook(() => useProviderManifest('anthropic'));
    expect(result.current).toBe(ANTHROPIC_MANIFEST);
  });

  it('returns googleProviderManifest for google', () => {
    const { result } = renderHook(() => useProviderManifest('google'));
    expect(result.current).toBe(googleProviderManifest);
  });

  it('returns OPENAI_MANIFEST for openai', () => {
    const { result } = renderHook(() => useProviderManifest('openai'));
    expect(result.current).toBe(OPENAI_MANIFEST);
  });

  it('returns DEEPSEEK_MANIFEST for deepseek', () => {
    const { result } = renderHook(() => useProviderManifest('deepseek'));
    expect(result.current).toBe(DEEPSEEK_MANIFEST);
  });

  it('returns NVIDIA_MANIFEST for nvidia', () => {
    const { result } = renderHook(() => useProviderManifest('nvidia'));
    expect(result.current).toBe(NVIDIA_MANIFEST);
  });

  it('manifest has maxContextTokens as a number', () => {
    const { result } = renderHook(() => useProviderManifest('anthropic'));
    expect(typeof result.current.maxContextTokens).toBe('number');
  });

  it('returns stable reference when stackId unchanged (memoisation)', () => {
    const { result, rerender } = renderHook(() => useProviderManifest('google'));
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
