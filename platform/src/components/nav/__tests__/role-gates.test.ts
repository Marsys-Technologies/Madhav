import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { visibleNavItems } from '../role-gates'

describe('AI Console shared navigation descriptor', () => {
  it('is hidden by default and while the public flag is off', () => {
    expect(visibleNavItems('super_admin').some(item => item.key === 'ai-console')).toBe(false)
    expect(visibleNavItems('guest', { aiConsoleByok: false }).some(item => item.key === 'ai-console')).toBe(false)
  })

  it('produces the exact super-admin and guest order when enabled', () => {
    expect(visibleNavItems('super_admin', { aiConsoleByok: true }).map(item => item.label)).toEqual([
      'Jātakas', 'Panchang', 'Cockpit', 'AI Console', 'AIOps', 'Audit', 'Performance', 'Admin',
    ])
    expect(visibleNavItems('guest', { aiConsoleByok: true }).map(item => item.label)).toEqual([
      'Jātakas', 'Panchang', 'AI Console',
    ])
  })

  it('is the shared source consumed by both rail and mobile navigation', () => {
    for (const file of ['AppShellRail.tsx', 'MobileNavSheet.tsx']) {
      const source = readFileSync(resolve(process.cwd(), `src/components/shared/${file}`), 'utf8')
      expect(source).toContain('visibleNavItems')
      expect(source).not.toMatch(/const NAV_ITEMS\s*=/)
      expect(source).toContain("NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'")
    }
  })
})
