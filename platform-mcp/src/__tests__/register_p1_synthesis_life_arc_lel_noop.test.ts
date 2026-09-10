import { readFileSync } from 'fs'
import { join } from 'path'
import { describe, it, expect } from 'vitest'

const SRC = readFileSync(
  join(__dirname, '../tools/register_p1_synthesis.ts'),
  'utf-8'
)

// Isolate just the kala_life_arc_get tool block
const blockStart = SRC.indexOf("'kala_life_arc_get'")
const blockEnd   = SRC.indexOf('server.tool(', blockStart + 1)
const block      = SRC.slice(blockStart, blockEnd === -1 ? undefined : blockEnd)

describe('F-26: kala_life_arc_get must not advertise include_lel_events (no-op)', () => {
  it('include_lel_events is absent from the tool block', () => {
    expect(block).not.toContain('include_lel_events')
  })

  it('description does not falsely claim LEL cross-links', () => {
    expect(SRC).not.toContain('cross-links to LEL events')
  })
})
