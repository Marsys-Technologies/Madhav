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
// PARITY_STORAGE_KEY constant
// ---------------------------------------------------------------------------

describe('PARITY_STORAGE_KEY', () => {
  it('is the expected string', () => {
    expect(PARITY_STORAGE_KEY).toBe('marsys.chatShellMode');
  });
});
