/**
 * Integration tests for B.9 — citation prompt v2 wired (audit finding O5).
 *
 * O5: consumeSystemPromptV2 and the SIG.MSR.NNN citation appendix were never
 * imported into single_model_strategy.ts. The model had no instruction to use
 * the SIG.MSR.NNN citation format, so the V2 renderer's regex could not match.
 * Fix: CITATION_APPENDIX exported from synthesis_prompt_v2.ts and appended to
 * renderedPrompt in the strategy when CHAT_V2_ENABLED is true.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const strategySrc = readFileSync(
  join(__dirname, '../../../src/lib/synthesis/single_model_strategy.ts'),
  'utf-8',
)

const v2PromptSrc = readFileSync(
  join(__dirname, '../../../src/lib/synthesis/prompts/synthesis_prompt_v2.ts'),
  'utf-8',
)

describe('B.9 — citation prompt v2 wired (O5)', () => {
  it('CITATION_APPENDIX is exported from synthesis_prompt_v2.ts', () => {
    expect(v2PromptSrc).toContain('export const CITATION_APPENDIX')
  })

  it('single_model_strategy imports CITATION_APPENDIX from synthesis_prompt_v2', () => {
    expect(strategySrc).toContain("from './prompts/synthesis_prompt_v2'")
    expect(strategySrc).toContain('CITATION_APPENDIX')
  })

  it('strategy appends CITATION_APPENDIX when CHAT_V2_ENABLED flag is true', () => {
    // Must be guarded by getFlag('CHAT_V2_ENABLED')
    expect(strategySrc).toContain("getFlag('CHAT_V2_ENABLED')")
    // Must append the appendix to renderedPrompt
    const v2Block = strategySrc.slice(
      strategySrc.indexOf("getFlag('CHAT_V2_ENABLED')"),
      strategySrc.indexOf("getFlag('CHAT_V2_ENABLED')") + 200,
    )
    expect(v2Block).toContain('CITATION_APPENDIX')
    expect(v2Block).toContain('renderedPrompt')
  })
})
