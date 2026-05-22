'use client'

/**
 * MultiProviderParityToggle — A-S11 (Runtime User Toggle)
 *
 * Settings affordance that lets users opt into the Multi-Provider Parity
 * chat shell (R11 v2 arc).
 *
 * VISIBILITY: Hidden when NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY
 * is false (build-time default). Only visible when operator enables the env-var.
 *
 * STATE: Reads from and writes to localStorage via useChatShellMode().
 * Cross-tab sync is handled by the hook.
 *
 * Visual change: None yet — visual changes ship in R11.B. Clicking this toggle
 * only updates the user preference in localStorage. The hook is read by later
 * phases to switch rendering.
 *
 * Carry-forward from R11 v1 V-S0 design per SUPERSESSION_NOTE §2.
 */

import {
  useChatShellMode,
  PARITY_ENV_ENABLED,
} from '@/lib/chat-v2/useMultiProviderParity';

export function MultiProviderParityToggle() {
  const { mode, setMode } = useChatShellMode();

  // Hidden when env-var is false (default) — operator kill-switch
  if (!PARITY_ENV_ENABLED) {
    return null;
  }

  const isMultiProvider = mode === 'multi-provider';

  function handleToggle() {
    setMode(isMultiProvider ? 'classic' : 'multi-provider');
  }

  return (
    <div
      className="flex items-center gap-2"
      data-testid="multi-provider-parity-toggle"
    >
      <button
        type="button"
        role="switch"
        aria-checked={isMultiProvider}
        aria-label="Use Multi-Provider Parity interface"
        onClick={handleToggle}
        className={[
          'relative h-5 w-9 rounded-full transition-colors',
          'border border-current/20 focus:outline-none focus-visible:ring-2',
          'focus-visible:ring-brand-gold/40',
          isMultiProvider
            ? 'bg-brand-gold/80 text-brand-ink'
            : 'bg-muted text-muted-foreground',
        ].join(' ')}
        data-testid="multi-provider-parity-switch"
      >
        <span
          className={[
            'absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow',
            'transition-transform',
            isMultiProvider ? 'translate-x-4' : 'translate-x-0',
          ].join(' ')}
          aria-hidden="true"
        />
      </button>
      <span
        className="text-xs text-muted-foreground"
        data-testid="multi-provider-parity-label"
      >
        Multi-Provider Parity
        {isMultiProvider ? ' (on)' : ' (off)'}
      </span>
    </div>
  );
}
