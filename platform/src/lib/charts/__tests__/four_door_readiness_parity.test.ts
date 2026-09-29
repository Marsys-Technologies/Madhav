/**
 * Readiness-gated door parity — static source guard (Jātaka Phase-A2).
 *
 * Legacy consult, MCP `prashna_ask` and super-admin `chat/build` each call the
 * ONE shared `checkReadingReadiness` (readingGate.ts) and must
 * propagate its `code`/`message`/`retryable` fields verbatim — never a
 * hardcoded retry value, never a locally-recomputed message. Each door's own
 * behavioral refusal is proved by its dedicated test file
 * (consult's readiness-gate.test.ts, prashna_ask's own route.test.ts,
 * chat/build's integrity.test.ts) and readingGate.test.ts proves the retry
 * contract itself; this file is the cheap, source-level cross-check that all
 * readiness-gated doors keep calling that one function the same way,
 * following the codebase's own convention for this kind of check (e.g.
 * mi_bhavisya's delete-scope regex test, dashboard.test.tsx's SQL regex).
 */
import { readFileSync } from 'fs'
import { join } from 'path'
import { describe, expect, it } from 'vitest'

const ROOT = join(__dirname, '../../../..')

function source(relPath: string): string {
  return readFileSync(join(ROOT, relPath), 'utf8')
}

const DOORS: Array<{ label: string; path: string }> = [
  { label: 'legacy consult', path: 'src/app/api/chat/consult/route.ts' },
  { label: 'MCP prashna_ask', path: 'src/app/api/mcp/prashna_ask/route.ts' },
  { label: 'super-admin chat/build', path: 'src/app/api/chat/build/route.ts' },
]

describe('every readiness-gated door calls the one shared readiness gate', () => {
  it.each(DOORS.map((d) => [d.label, d.path] as const))('%s imports checkReadingReadiness from readingGate.ts', (_label, path) => {
    const src = source(path)
    expect(src).toMatch(/import\s*\{[^}]*checkReadingReadiness[^}]*\}\s*from\s*['"]@\/lib\/charts\/readingGate['"]/)
    expect(src).toMatch(/checkReadingReadiness\(/)
  })
})

describe('the readiness-gated doors propagate readingGate verbatim', () => {
  // MCP prashna_ask prefixes its message with readingGate.code (so a durable
  // job store that keeps only the message still carries it) rather than
  // passing it unmodified — asserted separately below.
  it.each([
    ['legacy consult', 'src/app/api/chat/consult/route.ts'],
    ['super-admin chat/build', 'src/app/api/chat/build/route.ts'],
  ] as const)('%s never hardcodes retry — it reads readingGate.retryable', (_label, path) => {
    const src = source(path)
    expect(src).toMatch(/readingGate\.code/)
    expect(src).toMatch(/readingGate\.message/)
    expect(src).toMatch(/readingGate\.retryable/)
    // No literal `retry: true` / `retry: false` sitting beside a readingGate check
    // (a hardcoded flag is exactly the defect this guard exists to catch).
    expect(src).not.toMatch(/readingGate\.ok[\s\S]{0,400}retry:\s*(true|false)\s*[,}]/)
  })

  it('Paripraśna deliberately accepts partial charts instead of invoking the whole-chart gate', () => {
    const src = source('src/lib/pariprashna/pipeline/safety_gate.ts')
    expect(src).not.toMatch(/checkReadingReadiness/)
    expect(src).not.toMatch(/CHART_RECOMPUTE_REQUIRED/)
  })

  it('MCP prashna_ask reads readingGate.code/message/retryable into its envelope (message code-prefixed, not hardcoded)', () => {
    const src = source('src/app/api/mcp/prashna_ask/route.ts')
    expect(src).toMatch(/readingGate\.code/)
    expect(src).toMatch(/readingGate\.message/)
    expect(src).toMatch(/readingGate\.retryable/)
  })
})
