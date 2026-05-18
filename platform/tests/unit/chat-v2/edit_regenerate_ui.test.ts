/**
 * β1 — Edit & Regenerate UI integration tests.
 *
 * Verifies that ActionBarPrimitive.Edit, ActionBarPrimitive.Reload, and
 * BranchPickerPrimitive are referenced in ConsumeChatV2 (structural / import audit).
 * Full E2E rendering tests deferred to the E2E suite which requires a browser.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const componentPath = resolve(
  __dirname,
  '../../../src/components/consume/ConsumeChatV2.tsx',
)
const src = readFileSync(componentPath, 'utf8')

describe('ConsumeChatV2 β1 edit & regenerate wiring', () => {
  it('imports ActionBarPrimitive from @assistant-ui/react', () => {
    expect(src).toContain('ActionBarPrimitive')
    expect(src).toContain('@assistant-ui/react')
  })

  it('imports BranchPickerPrimitive from @assistant-ui/react', () => {
    expect(src).toContain('BranchPickerPrimitive')
  })

  it('renders ActionBarPrimitive.Edit for user messages', () => {
    expect(src).toContain('ActionBarPrimitive.Edit')
    expect(src).toContain('v2-edit-btn')
  })

  it('renders V2RegenerateButton with async-await reload (race-condition-free)', () => {
    expect(src).toContain('V2RegenerateButton')
    expect(src).toContain('v2-regenerate-btn')
    expect(src).toContain('messageRuntime.reload()')
  })

  it('renders ActionBarPrimitive.Copy for assistant messages', () => {
    expect(src).toContain('ActionBarPrimitive.Copy')
    expect(src).toContain('v2-copy-btn')
  })

  it('renders BranchPickerPrimitive.Root with hideWhenSingleBranch', () => {
    expect(src).toContain('BranchPickerPrimitive.Root')
    expect(src).toContain('hideWhenSingleBranch')
    expect(src).toContain('v2-branch-picker')
  })

  it('renders BranchPickerPrimitive.Previous and Next navigation', () => {
    expect(src).toContain('BranchPickerPrimitive.Previous')
    expect(src).toContain('BranchPickerPrimitive.Next')
    expect(src).toContain('v2-branch-prev')
    expect(src).toContain('v2-branch-next')
  })

  it('renders BranchPickerPrimitive.Number / Count for branch indicator', () => {
    expect(src).toContain('BranchPickerPrimitive.Number')
    expect(src).toContain('BranchPickerPrimitive.Count')
  })

  it('uses ActionBarPrimitive.Root with hideWhenRunning to suppress during streaming', () => {
    expect(src).toContain('hideWhenRunning')
  })

  it('uses ActionBarPrimitive.Root with autohide="not-last" to show only on last message', () => {
    expect(src).toContain('autohide="not-last"')
  })
})
