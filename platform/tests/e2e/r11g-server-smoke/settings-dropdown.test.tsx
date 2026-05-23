/**
 * settings-dropdown.test.tsx — G-S5 server-side integration smoke
 *
 * happy-dom render test for SettingsDropdown:
 *   - Click gear → menu opens (data-testid="settings-dropdown-menu" visible)
 *   - Click "Claude-style chat" radio → localStorage['marsys.chatShellMode'] = 'multi-provider'
 *   - Click "Classic Marsys" radio → localStorage = 'classic'
 *   - Click outside menu → menu closes
 *
 * PARITY_ENV_ENABLED is mocked to true so the component renders.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'

// ---------------------------------------------------------------------------
// localStorage mock
// ---------------------------------------------------------------------------

const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, val: string) => { store[key] = val },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
  }
})()

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: false,
  configurable: true,
})

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

afterEach(() => {
  cleanup()
  localStorageMock.clear()
  vi.resetModules()
})

// ---------------------------------------------------------------------------
// Helper: render with PARITY_ENV_ENABLED = true
// ---------------------------------------------------------------------------

async function renderWithEnvEnabled() {
  vi.doMock('../../../src/lib/chat-v2/useMultiProviderParity', async (importOriginal) => {
    const original = await importOriginal<
      typeof import('../../../src/lib/chat-v2/useMultiProviderParity')
    >()
    return {
      ...original,
      PARITY_ENV_ENABLED: true,
    }
  })
  const { SettingsDropdown } = await import('../../../src/components/consume/SettingsDropdown')
  return render(<SettingsDropdown />)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('settings-dropdown smoke — G-S5', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // --- 1. Click gear → menu opens ---
  it('click gear → data-testid="settings-dropdown-menu" becomes visible', async () => {
    await renderWithEnvEnabled()

    const gear = screen.getByTestId('settings-gear-button')
    expect(screen.queryByTestId('settings-dropdown-menu')).toBeNull()

    fireEvent.click(gear)

    expect(screen.getByTestId('settings-dropdown-menu')).toBeTruthy()
  })

  // --- 2. Click "Claude-style chat" radio → localStorage = 'multi-provider' ---
  it('click "Claude-style chat" radio → localStorage["marsys.chatShellMode"] = "multi-provider"', async () => {
    await renderWithEnvEnabled()

    fireEvent.click(screen.getByTestId('settings-gear-button'))

    const claudeRadio = screen.getByTestId('chat-shell-claude-style')
    fireEvent.click(claudeRadio)

    expect(localStorageMock.getItem('marsys.chatShellMode')).toBe('multi-provider')
  })

  // --- 3. Click "Classic Marsys" radio → localStorage = 'classic' ---
  it('click "Classic Marsys" radio → localStorage["marsys.chatShellMode"] = "classic"', async () => {
    // Pre-seed localStorage as multi-provider
    localStorageMock.setItem('marsys.chatShellMode', 'multi-provider')

    await renderWithEnvEnabled()

    fireEvent.click(screen.getByTestId('settings-gear-button'))

    const classicRadio = screen.getByTestId('chat-shell-classic')
    fireEvent.click(classicRadio)

    expect(localStorageMock.getItem('marsys.chatShellMode')).toBe('classic')
  })

  // --- 4. Click outside menu → menu closes ---
  it('click outside menu → menu closes (settings-dropdown-menu no longer visible)', async () => {
    await renderWithEnvEnabled()

    fireEvent.click(screen.getByTestId('settings-gear-button'))
    expect(screen.getByTestId('settings-dropdown-menu')).toBeTruthy()

    // Simulate mousedown outside the component (on document.body)
    fireEvent.mouseDown(document.body)

    expect(screen.queryByTestId('settings-dropdown-menu')).toBeNull()
  })

  // --- Bonus: aria-expanded attribute tracks open state ---
  it('gear aria-expanded=false initially, true after click, false after outside click', async () => {
    await renderWithEnvEnabled()

    const gear = screen.getByTestId('settings-gear-button')
    expect(gear.getAttribute('aria-expanded')).toBe('false')

    fireEvent.click(gear)
    expect(gear.getAttribute('aria-expanded')).toBe('true')

    fireEvent.mouseDown(document.body)
    expect(gear.getAttribute('aria-expanded')).toBe('false')
  })

  // --- Bonus: menu contains both radio options ---
  it('menu shows "Classic Marsys" and "Claude-style chat" options', async () => {
    await renderWithEnvEnabled()

    fireEvent.click(screen.getByTestId('settings-gear-button'))

    expect(screen.getByTestId('chat-shell-classic')).toBeTruthy()
    expect(screen.getByTestId('chat-shell-claude-style')).toBeTruthy()
    expect(screen.getByText('Classic Marsys')).toBeTruthy()
    expect(screen.getByText('Claude-style chat')).toBeTruthy()
  })

  // --- PARITY_ENV_ENABLED = false path: component renders null ---
  // Covered by: tests/components/consume/SettingsDropdown.test.tsx §1
  // Omitted from smoke suite because the module-level PARITY_ENV_ENABLED constant
  // cannot be reliably toggled to false within the same test file that already
  // mocks it to true via vi.doMock (vitest module isolation limitation).
  // The component-level test file handles this with isolated module resets.
  it('gear button is present when PARITY_ENV_ENABLED is mocked to true', async () => {
    await renderWithEnvEnabled()
    expect(screen.getByTestId('settings-gear-button')).toBeTruthy()
    expect(screen.getByTestId('settings-dropdown')).toBeTruthy()
  })
})
