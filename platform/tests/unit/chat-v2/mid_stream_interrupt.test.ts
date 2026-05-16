/**
 * β3 — Mid-stream interrupt unit tests.
 *
 * Verifies the cancel-and-replace contract: UI elements, interrupt state
 * management, toast, abort listener registration, and cancelled trace step.
 * Source-audit tests (readFileSync) match the established β1 pattern.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const composerSrc = readFileSync(
  resolve(__dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf8',
)

const routeSrc = readFileSync(
  resolve(__dirname, '../../../src/app/api/chat/consume/route.ts'),
  'utf8',
)

const typesSrc = readFileSync(
  resolve(__dirname, '../../../src/lib/trace/types.ts'),
  'utf8',
)

// ── UI structural checks ───────────────────────────────────────────────────────

describe('ConsumeChatV2 β3 interrupt-and-send UI', () => {
  it('renders v2-interrupt-send-btn when running', () => {
    expect(composerSrc).toContain('v2-interrupt-send-btn')
  })

  it('renders v2-interrupt-toast for the cancel notification', () => {
    expect(composerSrc).toContain('v2-interrupt-toast')
  })

  it('displays the canonical interrupt toast message', () => {
    expect(composerSrc).toContain('Cancelled — sending new query')
  })

  it('uses pendingResubmit ref to track interrupt state', () => {
    expect(composerSrc).toContain('pendingResubmit')
  })

  it('calls runtime.cancelRun() on interrupt', () => {
    expect(composerSrc).toContain('runtime.cancelRun()')
  })

  it('uses 300ms delay before resubmit', () => {
    expect(composerSrc).toContain('300')
    expect(composerSrc).toContain('requestSubmit')
  })

  it('uses aria-live="polite" on the interrupt toast for accessibility', () => {
    expect(composerSrc).toContain('aria-live="polite"')
  })
})

// ── Server abort handling checks ──────────────────────────────────────────────

describe('consume route β3 abort sentinel', () => {
  it('registers an abort event listener on request.signal', () => {
    expect(routeSrc).toContain("request.signal.addEventListener('abort'")
  })

  it('uses { once: true } to avoid double-firing', () => {
    expect(routeSrc).toContain('{ once: true }')
  })

  it('emits a cancelled step_name on abort', () => {
    expect(routeSrc).toContain("step_name: 'cancelled'")
  })

  it('emits status: cancelled on abort', () => {
    expect(routeSrc).toContain("status: 'cancelled'")
  })
})

// ── StepStatus type ───────────────────────────────────────────────────────────

describe('trace types β3 cancelled status', () => {
  it("includes 'cancelled' in StepStatus union", () => {
    expect(typesSrc).toContain("'cancelled'")
    expect(typesSrc).toMatch(/StepStatus.*cancelled|cancelled.*StepStatus/)
  })
})
