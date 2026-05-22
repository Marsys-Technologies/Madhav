/**
 * A-S12: CapabilityHint.integration.test.tsx
 * Renders CapabilityHint with each of the 5 manifests to verify
 * supported-vs-hidden behavior across all stacks.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CapabilityHint } from '../../../src/components/chat/CapabilityHint';
import { VALID_STACK_IDS } from '../../../src/lib/providers/dispatcher';
import type { StackId } from '../../../src/lib/providers/dispatcher';
import { isCapabilityAvailable } from '../../../src/lib/providers/dispatcher';
import type { ProviderCapabilities } from '../../../src/lib/providers/capabilities';

const CHILD_LABEL = 'test-child';

function renderHint(capability: keyof ProviderCapabilities, stack: StackId) {
  return render(
    <CapabilityHint capability={capability} activeStack={stack}>
      <button type="button">{CHILD_LABEL}</button>
    </CapabilityHint>,
  );
}

// ---------------------------------------------------------------------------
// webSearch: anthropic, google, openai support it; deepseek, nvidia do not
// ---------------------------------------------------------------------------

describe('CapabilityHint.integration — webSearch capability', () => {
  for (const stackId of VALID_STACK_IDS) {
    it(`${stackId}: ${isCapabilityAvailable('webSearch', stackId) ? 'shows child' : 'shows chip'}`, () => {
      const { unmount } = renderHint('webSearch', stackId as StackId);
      if (isCapabilityAvailable('webSearch', stackId)) {
        expect(screen.getByText(CHILD_LABEL)).toBeTruthy();
        expect(screen.queryByTestId('capability-hint-chip')).toBeNull();
      } else {
        expect(screen.queryByText(CHILD_LABEL)).toBeNull();
        expect(screen.getByTestId('capability-hint-chip')).toBeTruthy();
        const chip = screen.getByTestId('capability-hint-chip');
        expect(chip.getAttribute('data-stack')).toBe(stackId);
        expect(chip.getAttribute('data-capability')).toBe('webSearch');
      }
      unmount();
    });
  }
});

// ---------------------------------------------------------------------------
// extendedThinking: anthropic, google, deepseek support it; openai (polyfill), nvidia does not
// ---------------------------------------------------------------------------

describe('CapabilityHint.integration — extendedThinking capability', () => {
  for (const stackId of VALID_STACK_IDS) {
    it(`${stackId}: extendedThinking renders correctly`, () => {
      const { unmount } = renderHint('extendedThinking', stackId as StackId);
      if (isCapabilityAvailable('extendedThinking', stackId)) {
        expect(screen.getByText(CHILD_LABEL)).toBeTruthy();
      } else {
        expect(screen.queryByText(CHILD_LABEL)).toBeNull();
        expect(screen.getByTestId('capability-hint-chip')).toBeTruthy();
      }
      unmount();
    });
  }
});

// ---------------------------------------------------------------------------
// computerUse: anthropic + openai support it; google, deepseek, nvidia do not
// ---------------------------------------------------------------------------

describe('CapabilityHint.integration — computerUse capability', () => {
  for (const stackId of VALID_STACK_IDS) {
    it(`${stackId}: computerUse renders correctly`, () => {
      const { unmount } = renderHint('computerUse', stackId as StackId);
      if (isCapabilityAvailable('computerUse', stackId)) {
        expect(screen.getByText(CHILD_LABEL)).toBeTruthy();
      } else {
        expect(screen.queryByText(CHILD_LABEL)).toBeNull();
      }
      unmount();
    });
  }
});

// ---------------------------------------------------------------------------
// inputAudio: google supports it; all others do not
// ---------------------------------------------------------------------------

describe('CapabilityHint.integration — inputAudio capability', () => {
  it('google: shows child for inputAudio', () => {
    renderHint('inputAudio', 'google');
    expect(screen.getByText(CHILD_LABEL)).toBeTruthy();
  });

  it('anthropic: shows chip for inputAudio', () => {
    renderHint('inputAudio', 'anthropic');
    expect(screen.queryByText(CHILD_LABEL)).toBeNull();
    expect(screen.getByTestId('capability-hint-chip')).toBeTruthy();
  });
});
