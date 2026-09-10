// @vitest-environment node
//
// F-129 — synth_chart_brief_get's `top_discoveries` field used to alias
// `bodha_discoveries.surface_reading` (an internal surface/depth epistemic-pair
// diagnostic label written by bo_anveshana.py, never designed as public prose) directly
// to the served `statement` field, discarding the richer `hypothesis_text` /
// `depth_reading` / `why_an_acharya_misses_it` columns already present on the same row.
// This suite proves the defect is fixed (honest field names, no statement collapse) and
// guards against the pattern recurring anywhere else in this file.

import { readFileSync } from 'node:fs'
import { describe, it, expect, beforeAll } from 'vitest'

const SRC_URL = new URL('../tools/register_p1_synthesis.ts', import.meta.url)

describe('F-129 exit — top_discoveries query fields', () => {
  let src: string
  beforeAll(() => {
    src = readFileSync(SRC_URL, 'utf8')
  })

  it('does NOT alias surface_reading as statement', () => {
    expect(src).not.toMatch(/surface_reading\s+AS\s+statement/i)
  })

  it('selects hypothesis_text in the discResult query block', () => {
    // Anchor: the `const discLimit` block is F-129's query (not F-135's ranked_themes,
    // which is built from a different query/table entirely).
    const discBlock = src.match(/const discLimit[\s\S]{0,1000}LIMIT \$2[\s\S]{0,60}`, \[chart_id/)
    expect(discBlock).not.toBeNull()
    expect(discBlock![0]).toMatch(/hypothesis_text/)
  })

  it('selects depth_reading and why_an_acharya_misses_it alongside hypothesis_text', () => {
    const discBlock = src.match(/const discLimit[\s\S]{0,1000}LIMIT \$2[\s\S]{0,60}`, \[chart_id/)
    expect(discBlock).not.toBeNull()
    expect(discBlock![0]).toMatch(/depth_reading/)
    expect(discBlock![0]).toMatch(/why_an_acharya_misses_it/)
  })
})

describe('F-129 recurrence guard', () => {
  let src: string
  beforeAll(() => {
    src = readFileSync(SRC_URL, 'utf8')
  })

  it('no *_reading column is aliased AS statement anywhere in this file', () => {
    // Fails closed on any future query that repeats the same mislabeling pattern —
    // not just a check for this exact defect, but the whole defect class.
    expect(src).not.toMatch(/\b\w+_reading\s+AS\s+statement\b/i)
  })
})
