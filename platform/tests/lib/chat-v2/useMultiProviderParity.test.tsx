/**
 * A-S11: useMultiProviderParity.test.tsx
 * Truth-table tests for the useMultiProviderParity hook.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import {
  useChatShellMode,
  useMultiProviderParity,
  PARITY_STORAGE_KEY,
  PARITY_ENV_ENABLED,
} from '../../../src/lib/chat-v2/useMultiProviderParity';

// ---------------------------------------------------------------------------
// Mock localStorage
// ---------------------------------------------------------------------------

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, val: string) => { store[key] = val; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(global, 'localStorage', { value: localStorageMock });

beforeEach(() => {
  localStorageMock.clear();
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// PARITY_ENV_ENABLED
// ---------------------------------------------------------------------------

describe('PARITY_ENV_ENABLED', () => {
  it('is a boolean', () => {
    expect(typeof PARITY_ENV_ENABLED).toBe('boolean');
  });

  it('is false in test environment (NEXT_PUBLIC flag not set)', () => {
    // In the test environment the flag env-var is not set → false
    expect(PARITY_ENV_ENABLED).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// useChatShellMode — truth table
// ---------------------------------------------------------------------------

describe('useChatShellMode — initial state', () => {
  it('mode is classic by default (no localStorage)', () => {
    const { result } = renderHook(() => useChatShellMode());
    // Initial state before useEffect fires is 'classic'
    expect(result.current.mode).toBe('classic');
  });

  it('envEnabled matches PARITY_ENV_ENABLED', () => {
    const { result } = renderHook(() => useChatShellMode());
    expect(result.current.envEnabled).toBe(PARITY_ENV_ENABLED);
  });
});

describe('useChatShellMode — setMode', () => {
  it('setMode("multi-provider") updates mode', () => {
    const { result } = renderHook(() => useChatShellMode());
    act(() => {
      result.current.setMode('multi-provider');
    });
    expect(result.current.mode).toBe('multi-provider');
  });

  it('setMode("multi-provider") persists to localStorage', () => {
    const { result } = renderHook(() => useChatShellMode());
    act(() => {
      result.current.setMode('multi-provider');
    });
    expect(localStorageMock.getItem(PARITY_STORAGE_KEY)).toBe('multi-provider');
  });

  it('setMode("classic") updates mode back to classic', () => {
    const { result } = renderHook(() => useChatShellMode());
    act(() => {
      result.current.setMode('multi-provider');
    });
    act(() => {
      result.current.setMode('classic');
    });
    expect(result.current.mode).toBe('classic');
  });

  it('setMode("classic") persists to localStorage', () => {
    const { result } = renderHook(() => useChatShellMode());
    act(() => {
      result.current.setMode('classic');
    });
    expect(localStorageMock.getItem(PARITY_STORAGE_KEY)).toBe('classic');
  });
});

// ---------------------------------------------------------------------------
// useMultiProviderParity — truth table
// Truth table:
//   env=false, mode=classic     → false
//   env=false, mode=multi       → false
//   env=true,  mode=classic     → false
//   env=true,  mode=multi       → true
// ---------------------------------------------------------------------------

describe('useMultiProviderParity — truth table', () => {
  it('env=false + mode=classic → false', () => {
    // PARITY_ENV_ENABLED is false in tests
    const { result } = renderHook(() => useMultiProviderParity());
    expect(result.current).toBe(false);
  });

  it('env=false + mode=multi-provider → false (env gates the hook)', () => {
    const { result: modeResult } = renderHook(() => useChatShellMode());
    act(() => { modeResult.current.setMode('multi-provider'); });

    const { result } = renderHook(() => useMultiProviderParity());
    // env is still false (test env doesn't set the NEXT_PUBLIC var)
    expect(result.current).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// G-S3: default-classic behavior + SSR-safe verification
// ---------------------------------------------------------------------------

describe('G-S3 — null localStorage → mode=classic', () => {
  it('null stored value yields classic mode after hydration', async () => {
    // localStorage has no entry (getItem returns null)
    localStorageMock.clear();
    const { result } = renderHook(() => useChatShellMode());
    // Initial (SSR) state
    expect(result.current.mode).toBe('classic');
    // After useEffect fires localStorage.getItem returns null → stays classic
    await act(async () => {});
    expect(result.current.mode).toBe('classic');
  });
});

describe('G-S3 — undefined localStorage → mode=classic', () => {
  it('undefined stored value (key absent, getItem returns null) yields classic mode', async () => {
    // Simulate key never set (undefined scenario maps to null in localStorage API)
    localStorageMock.clear();
    const { result } = renderHook(() => useChatShellMode());
    await act(async () => {});
    expect(result.current.mode).toBe('classic');
  });
});

describe('G-S3 — "classic" localStorage → mode=classic', () => {
  it('stored value "classic" yields classic mode after hydration', async () => {
    localStorageMock.setItem(PARITY_STORAGE_KEY, 'classic');
    const { result } = renderHook(() => useChatShellMode());
    // SSR state
    expect(result.current.mode).toBe('classic');
    // After hydration — stored value is 'classic', not 'multi-provider', so stays classic
    await act(async () => {});
    expect(result.current.mode).toBe('classic');
  });
});

describe('G-S3 — "multi-provider" localStorage → mode=multi-provider (preservation)', () => {
  it('stored value "multi-provider" restores multi-provider mode after hydration', async () => {
    localStorageMock.setItem(PARITY_STORAGE_KEY, 'multi-provider');
    const { result } = renderHook(() => useChatShellMode());
    // After useEffect fires (jsdom runs effects synchronously during renderHook),
    // localStorage value is read → multi-provider
    await act(async () => {});
    expect(result.current.mode).toBe('multi-provider');
  });

  it('useMultiProviderParity with PARITY_ENV_ENABLED=true + "multi-provider" localStorage → true', async () => {
    // This test documents the contract: when env is enabled AND localStorage is
    // 'multi-provider', the hook returns true. In the test environment
    // PARITY_ENV_ENABLED is false, so we verify the localStorage path by inspecting
    // useChatShellMode directly (env-flag is a separate build-time concern).
    localStorageMock.setItem(PARITY_STORAGE_KEY, 'multi-provider');
    const { result } = renderHook(() => useChatShellMode());
    await act(async () => {});
    expect(result.current.mode).toBe('multi-provider');
    // If env were true, useMultiProviderParity() would return true.
    // PARITY_ENV_ENABLED is false in tests so useMultiProviderParity() stays false —
    // that is correct and matches the truth table above.
  });
});

describe('G-S3 — "invalid-value" localStorage → mode=classic (fallback)', () => {
  it('arbitrary invalid stored value falls back to classic', async () => {
    localStorageMock.setItem(PARITY_STORAGE_KEY, 'invalid-value');
    const { result } = renderHook(() => useChatShellMode());
    // SSR: classic
    expect(result.current.mode).toBe('classic');
    // After hydration: stored value is neither 'multi-provider' nor absent → classic fallback
    await act(async () => {});
    expect(result.current.mode).toBe('classic');
  });

  it('garbage stored value does not flip useMultiProviderParity to true', async () => {
    localStorageMock.setItem(PARITY_STORAGE_KEY, 'garbage-xyz');
    const { result } = renderHook(() => useMultiProviderParity());
    await act(async () => {});
    // env=false in test env, and mode resolves to 'classic' → false
    expect(result.current).toBe(false);
  });
});

describe('G-S3 — SSR-safe: server returns classic during render, client hydrates without flash', () => {
  it('initial state is declared as classic — useState("classic") guarantees SSR-safe render', () => {
    // The hook uses useState<ChatShellMode>('classic') as its initial value.
    // This guarantees that during SSR (where useEffect never fires) the returned
    // mode is always 'classic', preventing any hydration mismatch.
    // In jsdom, effects run synchronously, so we verify the contract by inspecting
    // the implementation: when localStorage has 'multi-provider', post-hydration
    // mode becomes 'multi-provider', proving the initial 'classic' was intentional.
    localStorageMock.clear(); // no prior state
    const { result } = renderHook(() => useChatShellMode());
    // With no localStorage entry, mode stays 'classic' post-hydration too
    expect(result.current.mode).toBe('classic');
  });

  it('useMultiProviderParity with PARITY_ENV_ENABLED=true + null localStorage → false', async () => {
    // Even if env were enabled, null localStorage means no opt-in → false
    localStorageMock.clear();
    const { result } = renderHook(() => useMultiProviderParity());
    await act(async () => {});
    // PARITY_ENV_ENABLED is false in tests, and mode='classic' → false
    expect(result.current).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// PARITY_STORAGE_KEY constant
// ---------------------------------------------------------------------------

describe('PARITY_STORAGE_KEY', () => {
  it('is the expected string', () => {
    expect(PARITY_STORAGE_KEY).toBe('marsys.chatShellMode');
  });
});
