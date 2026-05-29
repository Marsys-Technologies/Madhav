/**
 * E.3 — Anthropic force-route param.
 *
 * Source-level assertions that route.ts reads ?provider= URL param
 * and MARSYS_FORCE_PROVIDER env override to select the synthesis stack
 * when the client sends no explicit stack field.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const routeSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/app/api/chat/consult/route.ts'),
  'utf8',
)

describe('E.3 — Anthropic force-route param', () => {
  it('reads ?provider= URL query param', () => {
    expect(routeSrc).toContain("searchParams.get('provider')")
  })

  it('reads MARSYS_FORCE_PROVIDER env var', () => {
    expect(routeSrc).toContain('MARSYS_FORCE_PROVIDER')
  })

  it('override only applies when client sends no explicit stack', () => {
    const block = routeSrc.slice(
      routeSrc.indexOf('providerOverride'),
      routeSrc.indexOf('providerOverride') + 400,
    )
    expect(block).toContain('!body.stack')
  })

  it('override is validated against VALID_STACKS before use', () => {
    const block = routeSrc.slice(
      routeSrc.indexOf('providerOverride'),
      routeSrc.indexOf('providerOverride') + 400,
    )
    expect(block).toContain('VALID_STACKS.includes(providerOverride')
  })

  it('falls back to DEFAULT_STACK_ID if override is invalid', () => {
    const block = routeSrc.slice(
      routeSrc.indexOf('providerOverride'),
      routeSrc.indexOf('providerOverride') + 600,
    )
    expect(block).toContain('DEFAULT_STACK_ID')
  })
})
