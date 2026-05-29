/**
 * β3 — Mid-stream abort tests.
 *
 * R6.5 (2026-05-18): v2-interrupt-send-btn + handleInterruptSend removed per
 * F.3 forensic L3 fix. UI describe block deleted accordingly. Server-side
 * abort handling (route.ts) and StepStatus type tests retained unchanged.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const routeSrc = readFileSync(
  resolve(__dirname, '../../../src/app/api/chat/consult/route.ts'),
  'utf8',
)

const typesSrc = readFileSync(
  resolve(__dirname, '../../../src/lib/trace/types.ts'),
  'utf8',
)

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
