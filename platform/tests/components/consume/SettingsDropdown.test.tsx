/**
 * SettingsDropdown.test.tsx — R11.G (AC.G2.4)
 *
 * Tests for the Settings gear-icon dropdown that replaces MultiProviderParityToggle.
 * Uses @testing-library/react + happy-dom environment.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';

// ---------------------------------------------------------------------------
// localStorage mock (set up once, cleared between tests)
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

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: false,
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

afterEach(() => {
  cleanup();
  localStorageMock.clear();
  vi.resetModules();
});

// ---------------------------------------------------------------------------
// §1 — PARITY_ENV_ENABLED = false (default in test env)
//       Component must return null.
// ---------------------------------------------------------------------------

describe('SettingsDropdown — env disabled (PARITY_ENV_ENABLED=false)', () => {
  it('renders nothing when PARITY_ENV_ENABLED is false', async () => {
    // Default test env: NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY is unset → false
    const { SettingsDropdown } = await import(
      '../../../src/components/consume/SettingsDropdown'
    );
    const { container } = render(<SettingsDropdown />);
    expect(container.firstChild).toBeNull();
  });

  it('gear button is not in DOM when env is false', async () => {
    const { SettingsDropdown } = await import(
      '../../../src/components/consume/SettingsDropdown'
    );
    render(<SettingsDropdown />);
    expect(screen.queryByTestId('settings-gear-button')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// §2 — PARITY_ENV_ENABLED = true (mocked)
//       All interactive behaviour.
// ---------------------------------------------------------------------------

describe('SettingsDropdown — env enabled (PARITY_ENV_ENABLED mocked to true)', () => {
  beforeEach(() => {
    vi.doMock('../../../src/lib/chat-v2/useMultiProviderParity', async (importOriginal) => {
      const original = await importOriginal<
        typeof import('../../../src/lib/chat-v2/useMultiProviderParity')
      >();
      return {
        ...original,
        PARITY_ENV_ENABLED: true,
      };
    });
  });

  async function renderDropdown() {
    // Import after mock is installed so the module picks up mocked PARITY_ENV_ENABLED
    const { SettingsDropdown } = await import(
      '../../../src/components/consume/SettingsDropdown'
    );
    return render(<SettingsDropdown />);
  }

  // AC.G2.4-a: gear icon renders
  it('renders gear button when PARITY_ENV_ENABLED is true', async () => {
    await renderDropdown();
    expect(screen.getByTestId('settings-gear-button')).toBeTruthy();
  });

  it('wrapping container has data-testid="settings-dropdown"', async () => {
    await renderDropdown();
    expect(screen.getByTestId('settings-dropdown')).toBeTruthy();
  });

  // AC.G2.4-b: menu opens on gear click
  it('click gear → menu opens (data-testid="settings-dropdown-menu" appears)', async () => {
    await renderDropdown();
    const gear = screen.getByTestId('settings-gear-button');

    expect(screen.queryByTestId('settings-dropdown-menu')).toBeNull();
    fireEvent.click(gear);
    expect(screen.getByTestId('settings-dropdown-menu')).toBeTruthy();
  });

  it('gear has aria-expanded=false before click, true after click', async () => {
    await renderDropdown();
    const gear = screen.getByTestId('settings-gear-button');

    expect(gear.getAttribute('aria-expanded')).toBe('false');
    fireEvent.click(gear);
    expect(gear.getAttribute('aria-expanded')).toBe('true');
  });

  // AC.G2.4-c: radio — Classic Marsys → localStorage = 'classic'
  // Seed localStorage with 'multi-provider' so the Classic radio is unchecked,
  // then click it — onChange fires and sets storage back to 'classic'.
  it('click "Classic Marsys" radio → localStorage["marsys.chatShellMode"] = "classic"', async () => {
    // Pre-seed storage so the hook initialises with 'multi-provider'
    localStorageMock.setItem('marsys.chatShellMode', 'multi-provider');
    await renderDropdown();
    fireEvent.click(screen.getByTestId('settings-gear-button'));

    const classicRadio = screen.getByTestId('chat-shell-classic');
    fireEvent.click(classicRadio);
    expect(localStorageMock.getItem('marsys.chatShellMode')).toBe('classic');
  });

  // AC.G2.4-d: radio — Claude-style → localStorage = 'multi-provider'
  it('click "Claude-style chat" radio → localStorage["marsys.chatShellMode"] = "multi-provider"', async () => {
    await renderDropdown();
    fireEvent.click(screen.getByTestId('settings-gear-button'));

    const claudeRadio = screen.getByTestId('chat-shell-claude-style');
    fireEvent.click(claudeRadio);
    expect(localStorageMock.getItem('marsys.chatShellMode')).toBe('multi-provider');
  });

  // AC.G2.4-e: click outside → menu closes
  it('click outside menu → menu closes', async () => {
    await renderDropdown();
    fireEvent.click(screen.getByTestId('settings-gear-button'));
    expect(screen.getByTestId('settings-dropdown-menu')).toBeTruthy();

    // Simulate mousedown outside the container (on document.body)
    fireEvent.mouseDown(document.body);
    expect(screen.queryByTestId('settings-dropdown-menu')).toBeNull();
  });

  // Bonus: menu labels are present
  it('menu contains "Classic Marsys" and "Claude-style chat" labels', async () => {
    await renderDropdown();
    fireEvent.click(screen.getByTestId('settings-gear-button'));

    expect(screen.getByText('Classic Marsys')).toBeTruthy();
    expect(screen.getByText('Claude-style chat')).toBeTruthy();
  });

  it('menu has "Chat experience" section heading', async () => {
    await renderDropdown();
    fireEvent.click(screen.getByTestId('settings-gear-button'));

    expect(screen.getByText('Chat experience')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// §3 — No-crash smoke (env=false path)
// ---------------------------------------------------------------------------

describe('SettingsDropdown — smoke (no env needed)', () => {
  it('renders without throwing when env is false', async () => {
    const { SettingsDropdown } = await import(
      '../../../src/components/consume/SettingsDropdown'
    );
    expect(() => render(<SettingsDropdown />)).not.toThrow();
  });
});
