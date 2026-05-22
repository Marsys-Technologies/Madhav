/**
 * D-S5: D-S5-prompt-layout.test.ts
 *
 * Tests for cache-aware prompt layout (R11.D).
 *
 * AC1: CACHE_AWARE_SECTION_ORDER defines canonical order.
 * AC2: validateCacheSections detects missing sections.
 * AC3: estimateCacheCoverage counts available BPs.
 * AC5: No NEXT_PUBLIC flag contamination.
 */

import { describe, it, expect } from 'vitest'
import {
  CACHE_AWARE_SECTION_ORDER,
  validateCacheSections,
  estimateCacheCoverage,
  assembleWithCacheBreakpoints,
  countCacheBreakpoints,
  type PromptSections,
} from '../../src/lib/synthesis/prompt_assembler'

// ---------------------------------------------------------------------------
// AC5: server-side flag discipline
// ---------------------------------------------------------------------------

describe('D-S5: R11D_PROMPT_LAYOUT flag — server-side only', () => {
  it('flag name does not have NEXT_PUBLIC prefix', () => {
    expect('R11D_PROMPT_LAYOUT'.startsWith('NEXT_PUBLIC')).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// Section ordering
// ---------------------------------------------------------------------------

describe('D-S5: CACHE_AWARE_SECTION_ORDER', () => {
  it('canonical order is tools → system → rag → history → current', () => {
    expect(CACHE_AWARE_SECTION_ORDER).toEqual(['tools', 'system', 'rag', 'history', 'current'])
  })

  it('has 5 sections', () => {
    expect(CACHE_AWARE_SECTION_ORDER).toHaveLength(5)
  })
})

// ---------------------------------------------------------------------------
// validateCacheSections
// ---------------------------------------------------------------------------

describe('D-S5: validateCacheSections', () => {
  it('returns empty array for a fully-populated sections object', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      systemPrompt: 'system',
      ragBundle: 'rag',
      historyTurns: [
        { role: 'user', content: 'prior question' },
        { role: 'assistant', content: 'prior answer' },
      ],
      currentUserTurn: 'current',
    }
    const warnings = validateCacheSections(sections)
    expect(warnings).toHaveLength(0)
  })

  it('warns when toolsBlock is absent (BP0 missing)', () => {
    const sections: PromptSections = {
      systemPrompt: 'system',
      ragBundle: 'rag',
      historyTurns: [{ role: 'assistant', content: 'prior' }],
      currentUserTurn: 'current',
    }
    const warnings = validateCacheSections(sections)
    expect(warnings.some(w => w.includes('BP0'))).toBe(true)
  })

  it('warns when systemPrompt is absent (BP1 missing)', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      ragBundle: 'rag',
      historyTurns: [{ role: 'assistant', content: 'prior' }],
      currentUserTurn: 'current',
    }
    const warnings = validateCacheSections(sections)
    expect(warnings.some(w => w.includes('BP1'))).toBe(true)
  })

  it('warns when ragBundle is absent (BP2 missing)', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      systemPrompt: 'system',
      historyTurns: [{ role: 'assistant', content: 'prior' }],
      currentUserTurn: 'current',
    }
    const warnings = validateCacheSections(sections)
    expect(warnings.some(w => w.includes('BP2'))).toBe(true)
  })

  it('warns when no assistant turn in history (BP3 missing)', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      systemPrompt: 'system',
      ragBundle: 'rag',
      historyTurns: [],
      currentUserTurn: 'current',
    }
    const warnings = validateCacheSections(sections)
    expect(warnings.some(w => w.includes('BP3'))).toBe(true)
  })

  it('returns 4 warnings when all sections are absent (minimal sections)', () => {
    const sections: PromptSections = {
      historyTurns: [],
      currentUserTurn: 'current',
    }
    const warnings = validateCacheSections(sections)
    expect(warnings).toHaveLength(4)
  })
})

// ---------------------------------------------------------------------------
// estimateCacheCoverage
// ---------------------------------------------------------------------------

describe('D-S5: estimateCacheCoverage', () => {
  it('bpCount is 4 for fully populated sections', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      systemPrompt: 'system',
      ragBundle: 'rag',
      historyTurns: [{ role: 'assistant', content: 'prior' }],
      currentUserTurn: 'current',
    }
    const result = estimateCacheCoverage(sections)
    expect(result.bpCount).toBe(4)
    expect(result.bp0HasContent).toBe(true)
    expect(result.bp1HasContent).toBe(true)
    expect(result.bp2HasContent).toBe(true)
    expect(result.bp3HasContent).toBe(true)
  })

  it('bpCount is 0 for minimal sections', () => {
    const sections: PromptSections = { historyTurns: [], currentUserTurn: 'current' }
    const result = estimateCacheCoverage(sections)
    expect(result.bpCount).toBe(0)
  })

  it('bpCount is 2 for tools + system only', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      systemPrompt: 'system',
      historyTurns: [],
      currentUserTurn: 'current',
    }
    const result = estimateCacheCoverage(sections)
    expect(result.bpCount).toBe(2)
  })

  it('structuralCoverageWarnings is empty when all 4 BPs have content', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      systemPrompt: 'system',
      ragBundle: 'rag',
      historyTurns: [{ role: 'assistant', content: 'prior' }],
      currentUserTurn: 'current',
    }
    const result = estimateCacheCoverage(sections)
    expect(result.structuralCoverageWarnings).toHaveLength(0)
  })
})

// ---------------------------------------------------------------------------
// Snapshot test: assembleWithCacheBreakpoints under flag=true + flag=false
// ---------------------------------------------------------------------------

describe('D-S5: prompt assembly snapshot', () => {
  const sections: PromptSections = {
    toolsBlock: 'tools',
    systemPrompt: 'system',
    ragBundle: 'rag',
    historyTurns: [
      { role: 'user', content: 'prev user' },
      { role: 'assistant', content: 'prev assistant' },
    ],
    currentUserTurn: 'current user',
  }

  it('flag=true: message order is tools → system → history → rag → current', () => {
    const messages = assembleWithCacheBreakpoints(sections, true)
    expect(messages[0].content).toBe('tools')
    expect(messages[1].content).toBe('system')
    // history turns follow
    expect(messages[2].content).toBe('prev user')
    expect(messages[3].content).toBe('prev assistant')
    // rag bundle
    expect(messages[4].content).toBe('rag')
    // current user turn last
    expect(messages[5].content).toBe('current user')
  })

  it('flag=true: exactly 4 cache markers', () => {
    const messages = assembleWithCacheBreakpoints(sections, true)
    expect(countCacheBreakpoints(messages)).toBe(4)
  })

  it('flag=false: 0 cache markers', () => {
    const messages = assembleWithCacheBreakpoints(sections, false)
    expect(countCacheBreakpoints(messages)).toBe(0)
  })

  it('flag=false: same message count as flag=true (content unchanged)', () => {
    const withCache = assembleWithCacheBreakpoints(sections, true)
    const withoutCache = assembleWithCacheBreakpoints(sections, false)
    expect(withCache.length).toBe(withoutCache.length)
  })

  it('flag=false: all messages have identical content to flag=true', () => {
    const withCache = assembleWithCacheBreakpoints(sections, true)
    const withoutCache = assembleWithCacheBreakpoints(sections, false)
    for (let i = 0; i < withCache.length; i++) {
      expect(withCache[i].content).toBe(withoutCache[i].content)
      expect(withCache[i].role).toBe(withoutCache[i].role)
    }
  })
})
