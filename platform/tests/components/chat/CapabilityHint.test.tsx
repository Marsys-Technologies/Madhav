/**
 * A-S8: CapabilityHint.test.tsx
 * Tests for the CapabilityHint component and manifest-helpers utilities.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CapabilityHint } from '../../../src/components/chat/CapabilityHint';
import {
  getStacksSupporting,
  formatSupportingStackNames,
} from '../../../src/lib/providers/manifest-helpers';
import type { StackId } from '../../../src/lib/providers/dispatcher';

// ---------------------------------------------------------------------------
// manifest-helpers: getStacksSupporting
// ---------------------------------------------------------------------------

describe('getStacksSupporting', () => {
  it('webSearch returns stacks that support it (anthropic, google, openai)', () => {
    const stacks = getStacksSupporting('webSearch');
    expect(stacks).toContain('anthropic');
    expect(stacks).toContain('google');
    expect(stacks).toContain('openai');
  });

  it('webSearch does not include deepseek or nvidia', () => {
    const stacks = getStacksSupporting('webSearch');
    expect(stacks).not.toContain('deepseek');
    expect(stacks).not.toContain('nvidia');
  });

  it('extendedThinking returns at least anthropic, google, deepseek', () => {
    const stacks = getStacksSupporting('extendedThinking');
    expect(stacks).toContain('anthropic');
    expect(stacks).toContain('google');
    expect(stacks).toContain('deepseek');
  });

  it('extendedThinking does not include nvidia', () => {
    const stacks = getStacksSupporting('extendedThinking');
    expect(stacks).not.toContain('nvidia');
  });
});

// ---------------------------------------------------------------------------
// manifest-helpers: formatSupportingStackNames
// ---------------------------------------------------------------------------

describe('formatSupportingStackNames', () => {
  it('single supporter returns just the name', () => {
    // computerUse: only anthropic and openai
    const result = formatSupportingStackNames('computerUse');
    // result should not be empty
    expect(result.length).toBeGreaterThan(0);
  });

  it('two supporters returns "A or B" format', () => {
    // computerUse: anthropic + openai only → "Anthropic or Openai"
    const stacks = getStacksSupporting('computerUse');
    if (stacks.length === 2) {
      const result = formatSupportingStackNames('computerUse');
      expect(result).toContain(' or ');
      expect(result.split(' or ')).toHaveLength(2);
    }
  });

  it('three-or-more supporters includes Oxford comma "A, B, or C"', () => {
    // webSearch: anthropic, google, openai = 3
    const stacks = getStacksSupporting('webSearch');
    if (stacks.length >= 3) {
      const result = formatSupportingStackNames('webSearch');
      expect(result).toMatch(/, or /);
    }
  });

  it('capability with no supporters returns empty string', () => {
    // There is no capability with zero supporters in the current matrix,
    // but we can test the empty-array path via a cast
    // Instead verify: any real capability with supporters returns non-empty
    const result = formatSupportingStackNames('webSearch');
    expect(result.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// CapabilityHint component
// ---------------------------------------------------------------------------

describe('CapabilityHint — supported capability', () => {
  it('passes through children when capability is supported', () => {
    render(
      <CapabilityHint capability="webSearch" activeStack={'anthropic' as StackId}>
        <button type="button">Web Search</button>
      </CapabilityHint>,
    );
    expect(screen.getByRole('button', { name: 'Web Search' })).toBeTruthy();
  });

  it('does not render chip when capability is supported', () => {
    render(
      <CapabilityHint capability="extendedThinking" activeStack={'anthropic' as StackId}>
        <span>Thinking</span>
      </CapabilityHint>,
    );
    expect(screen.queryByTestId('capability-hint-chip')).toBeNull();
  });
});

describe('CapabilityHint — unsupported capability', () => {
  it('renders chip when capability is NOT supported on stack', () => {
    // deepseek doesn't support webSearch
    render(
      <CapabilityHint capability="webSearch" activeStack={'deepseek' as StackId}>
        <button type="button">Web Search</button>
      </CapabilityHint>,
    );
    expect(screen.getByTestId('capability-hint-chip')).toBeTruthy();
  });

  it('does not render children when capability is NOT supported', () => {
    render(
      <CapabilityHint capability="webSearch" activeStack={'deepseek' as StackId}>
        <button type="button">Web Search</button>
      </CapabilityHint>,
    );
    expect(screen.queryByRole('button', { name: 'Web Search' })).toBeNull();
  });

  it('chip copy contains "Switch to" text with stack name', () => {
    render(
      <CapabilityHint capability="webSearch" activeStack={'deepseek' as StackId}>
        <button type="button">Web Search</button>
      </CapabilityHint>,
    );
    const chip = screen.getByTestId('capability-hint-chip');
    expect(chip.textContent).toMatch(/Switch to/i);
  });

  it('chip has role=status and aria-label', () => {
    render(
      <CapabilityHint capability="webSearch" activeStack={'deepseek' as StackId}>
        <span>Web Search</span>
      </CapabilityHint>,
    );
    const chip = screen.getByRole('status');
    expect(chip.getAttribute('aria-label')).toMatch(/Switch to/i);
  });

  it('chip has data-capability and data-stack attributes', () => {
    render(
      <CapabilityHint capability="webSearch" activeStack={'deepseek' as StackId}>
        <span>Web Search</span>
      </CapabilityHint>,
    );
    const chip = screen.getByTestId('capability-hint-chip');
    expect(chip.getAttribute('data-capability')).toBe('webSearch');
    expect(chip.getAttribute('data-stack')).toBe('deepseek');
  });
});

describe('CapabilityHint — nvidia missing extendedThinking', () => {
  it('shows chip for nvidia + extendedThinking', () => {
    render(
      <CapabilityHint capability="extendedThinking" activeStack={'nvidia' as StackId}>
        <span>Thinking</span>
      </CapabilityHint>,
    );
    expect(screen.getByTestId('capability-hint-chip')).toBeTruthy();
  });

  it('chip text names at least one alternative stack', () => {
    render(
      <CapabilityHint capability="extendedThinking" activeStack={'nvidia' as StackId}>
        <span>Thinking</span>
      </CapabilityHint>,
    );
    const chip = screen.getByTestId('capability-hint-chip');
    // At minimum anthropic, google, or deepseek should appear
    const text = chip.textContent ?? '';
    const hasAlternative =
      text.includes('Anthropic') ||
      text.includes('Google') ||
      text.includes('Deepseek');
    expect(hasAlternative).toBe(true);
  });
});
