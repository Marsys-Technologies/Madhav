/**
 * useMultiProviderParity.ts — A-S11 (Runtime User Toggle)
 *
 * Provides the `useMultiProviderParity()` hook and `useChatShellMode()` hook
 * for the Multi-Provider Parity opt-in arc (R11 v2).
 *
 * The full parity surface is gated by TWO conditions, both must be true:
 *   1. Build-time: NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY === 'true'
 *      (operator kill-switch; deploy.yml --build-arg; default false)
 *   2. Runtime: localStorage['marsys.chatShellMode'] === 'multi-provider'
 *      (per-browser user preference; set by MultiProviderParityToggle)
 *
 * SSR safety: localStorage is only accessed in useEffect (client-side only).
 * During SSR, the hook returns false. No hydration mismatch.
 *
 * Cross-tab sync: listens to the 'storage' event on window so flipping in one
 * tab propagates to all other open tabs.
 *
 * Carry-forward from R11 v1 V-S0 design per SUPERSESSION_NOTE §2.
 */

'use client';

import { useEffect, useState } from 'react';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const PARITY_STORAGE_KEY = 'marsys.chatShellMode';
export type ChatShellMode = 'classic' | 'multi-provider';

/**
 * Build-time kill-switch. True only when the operator sets the env-var to 'true'.
 * Evaluated once at module load. Server renders see false (no window.env access).
 */
export const PARITY_ENV_ENABLED =
  typeof process !== 'undefined' &&
  process.env.NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY === 'true';

// ---------------------------------------------------------------------------
// useMultiProviderParity — primary hook
// ---------------------------------------------------------------------------

/**
 * Returns true iff:
 *   - NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY === 'true' AND
 *   - user has set localStorage['marsys.chatShellMode'] = 'multi-provider'
 *
 * Safe for server render (returns false until client hydration).
 */
export function useMultiProviderParity(): boolean {
  const { mode } = useChatShellMode();
  return PARITY_ENV_ENABLED && mode === 'multi-provider';
}

// ---------------------------------------------------------------------------
// useChatShellMode — full mode management
// ---------------------------------------------------------------------------

export interface ChatShellModeState {
  /** Current effective mode ('classic' or 'multi-provider'). */
  mode: ChatShellMode;
  /** Set the mode and persist to localStorage. */
  setMode: (m: ChatShellMode) => void;
  /** Whether the env-var kill-switch is on. */
  envEnabled: boolean;
}

/**
 * Returns the current chat shell mode, a setter, and the env-var state.
 *
 * SSR-safe: during server render `mode` is 'classic' (the default).
 * Client hydration reads localStorage and updates the state synchronously.
 */
export function useChatShellMode(): ChatShellModeState {
  // Start with 'classic' — safe for SSR / pre-hydration.
  const [mode, setModeState] = useState<ChatShellMode>('classic');

  useEffect(() => {
    // Read initial value from localStorage on mount
    const stored = localStorage.getItem(PARITY_STORAGE_KEY);
    if (stored === 'multi-provider') {
      setModeState('multi-provider');
    }

    // Cross-tab sync via storage event
    function onStorage(e: StorageEvent) {
      if (e.key !== PARITY_STORAGE_KEY) return;
      const newVal = e.newValue;
      setModeState(newVal === 'multi-provider' ? 'multi-provider' : 'classic');
    }

    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  function setMode(m: ChatShellMode) {
    setModeState(m);
    localStorage.setItem(PARITY_STORAGE_KEY, m);
  }

  return { mode, setMode, envEnabled: PARITY_ENV_ENABLED };
}
