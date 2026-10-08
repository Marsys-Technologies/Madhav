import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { ordinal } from '@/lib/format/ordinal'

const CASES: Array<[number, string]> = [
  [1, '1st'], [2, '2nd'], [3, '3rd'], [4, '4th'], [10, '10th'], [11, '11th'], [12, '12th'],
  [13, '13th'], [21, '21st'], [22, '22nd'], [23, '23rd'], [101, '101st'], [111, '111th'],
]

describe('ordinal', () => {
  it.each(CASES)('%i -> %s', (n, s) => expect(ordinal(n)).toBe(s))
  it('rejects non-integers', () => expect(() => ordinal(2.5)).toThrow(TypeError))
})

describe('platform-mcp copy parity', () => {
  it('has the same function body as the platform helper', () => {
    const body = (p: string) => readFileSync(resolve(__dirname, p), 'utf8').slice(readFileSync(resolve(__dirname, p), 'utf8').indexOf('export function ordinal'))
    expect(body('../../../platform-mcp/src/lib/ordinal.ts')).toBe(body('../../src/lib/format/ordinal.ts'))
  })
})

describe('serving strings no longer build "Nth" by hand', () => {
  const files = [
    'src/lib/retrieval/registry/layers/register_d10_pact.ts',
    'src/components/trace/QueryDNAPanel.tsx',
    '../platform-mcp/src/tools/registry_bridge.ts',
    '../platform-mcp/src/lib/kp_school_voice.ts',
  ]
  it.each(files)('%s has no hand-built ${n}th', (f) => {
    const src = readFileSync(resolve(__dirname, '../../', f), 'utf8')
    expect(src).not.toMatch(/\$\{[^}]*\}th\b/)
  })
})
