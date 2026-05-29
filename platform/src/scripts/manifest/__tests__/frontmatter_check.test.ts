import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'

const FILES_TO_CHECK = [
  '/Users/Dev/Vibe-Coding/Apps/Madhav/01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  '/Users/Dev/Vibe-Coding/Apps/Madhav/025_HOLISTIC_SYNTHESIS/MSR_v5_0.md',
  '/Users/Dev/Vibe-Coding/Apps/Madhav/03_DOMAIN_REPORTS/REPORT_FINANCIAL_v2_1.md',
]

function extractFrontmatter(content: string): Record<string, unknown> {
  const match = content.match(/^---\n([\s\S]+?)\n---/)
  if (!match) return {}
  const fm: Record<string, unknown> = {}
  for (const line of match[1].split('\n')) {
    const kv = line.match(/^(\w+):\s*(.+)/)
    if (kv) fm[kv[1]] = kv[2].replace(/^["']|["']$/g, '')
  }
  return fm
}

describe('frontmatter discipline (Stream E verification)', () => {
  for (const filePath of FILES_TO_CHECK) {
    it(`${filePath.split('/').pop()} has required frontmatter fields`, () => {
      const content = readFileSync(filePath, 'utf-8')
      const fm = extractFrontmatter(content)
      expect(fm).toHaveProperty('expose_to_chat')
      expect(fm).toHaveProperty('native_id')
    })
  }
})
