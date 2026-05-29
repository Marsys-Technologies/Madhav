import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// __dirname = platform/src/scripts/manifest/__tests__ (5 levels below repo root)
const REPO_ROOT = resolve(__dirname, '../../../../..')

const FILES_TO_CHECK = [
  resolve(REPO_ROOT, '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md'),
  resolve(REPO_ROOT, '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md'),
  resolve(REPO_ROOT, '03_DOMAIN_REPORTS/REPORT_FINANCIAL_v2_1.md'),
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

// expose_to_chat and native_id are CAPABILITY_MANIFEST entry fields, not file frontmatter.
// These canonical artifacts use canonical_id as their required frontmatter key.
describe('frontmatter discipline (Stream E verification)', () => {
  for (const filePath of FILES_TO_CHECK) {
    it(`${filePath.split('/').pop()} has required frontmatter fields`, () => {
      const content = readFileSync(filePath, 'utf-8')
      const fm = extractFrontmatter(content)
      expect(fm).toHaveProperty('canonical_id')
    })
  }
})
