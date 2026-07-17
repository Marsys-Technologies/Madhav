/**
 * description_payload_audit.test.ts — D-2 Lane V-3, CR-44 (ledger row 23).
 *
 * Runs the description-vs-payload auditor over the live MCP tool source and asserts ZERO
 * UNEXPLAINED description⇄payload divergences. Explained divergences are whitelisted with a written
 * reason (the DONE criterion's "explicit flags allowed"). This test is the in-scope CI enforcement
 * surface (Lane V-3 may_touch excludes ci.yml/tap-ci.yml — the platform `npm test` gate runs this).
 */
import { describe, it, expect } from 'vitest'
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { auditDescriptionPayload, extractClaimedFields, extractToolBlocks } from './description_payload_audit.js'

// repoRoot: vitest runs with cwd = platform/. The tools live one level up in platform-mcp/.
const REPO_ROOT = path.resolve(process.cwd(), '..')
const TOOLS_DIR = path.resolve(process.cwd(), '../platform-mcp/src/tools')

// Explained divergences: {tool, claimed_field} the description legitimately names but the handler
// doesn't textually emit (produced by a shared envelope/delegate, or a documented facet name).
// Each MUST carry a reason. An empty list means the estate is clean.
const EXPLAINED = new Set<string>([
  // (populated below once the first run reveals genuine shared-wrapper cases)
])

describe('extractClaimedFields', () => {
  it('extracts backticked payload field names', () => {
    expect(extractClaimedFields('Returns a `verdict_summary` and `trim_report`.')).toEqual(
      expect.arrayContaining(['verdict_summary', 'trim_report']),
    )
  })
  it('extracts fields following "returns/section" keywords', () => {
    const c = extractClaimedFields('returns a separate divisional_facts section per varga')
    expect(c).toContain('divisional_facts')
  })
  it('ignores bare common words and single-token noise', () => {
    expect(extractClaimedFields('Returns the full chart data now.')).toEqual([])
  })
})

describe('CR-44 description-vs-payload audit', () => {
  it('has zero UNEXPLAINED description⇄payload divergences across the MCP tool estate', () => {
    const divergences = auditDescriptionPayload(TOOLS_DIR, REPO_ROOT)
    const unexplained = divergences.filter((d) => !EXPLAINED.has(`${d.tool}::${d.claimed_field}`))
    if (unexplained.length > 0) {
      // eslint-disable-next-line no-console
      console.error('CR-44 UNEXPLAINED divergences:\n' + unexplained.map(
        (d) => `  ${d.tool}: description claims \`${d.claimed_field}\` but the handler never emits it (${d.file})`,
      ).join('\n'))
    }
    expect(unexplained).toEqual([])
  })

  it('actually scans a non-trivial number of tools and extracts real claims (anti-vacuous)', () => {
    // Guard against a vacuous green: prove the auditor sees many tools and extracts real field-claims.
    const walk = (d: string): string[] => {
      const out: string[] = []
      for (const e of readdirSync(d)) {
        if (e === '__tests__') continue
        const f = path.join(d, e)
        const s = statSync(f)
        if (s.isDirectory()) out.push(...walk(f))
        else if (e.endsWith('.ts') && !e.endsWith('.test.ts')) out.push(f)
      }
      return out
    }
    let tools = 0, claims = 0
    for (const f of walk(TOOLS_DIR)) {
      const src = readFileSync(f, 'utf-8')
      if (!src.includes('server.tool(')) continue
      for (const b of extractToolBlocks(src)) {
        tools++
        claims += extractClaimedFields(b.description).length
      }
    }
    // Coverage scope: the auditor sees inline `server.tool('name','desc',…)` blocks. Many aliases
    // register through regAlias/globalAlias wrappers whose description is a generic template — their
    // inline field-claims are not audited here (a documented limitation, same class as R-18's
    // ...rest blind spot). Still, 30+ direct blocks with real backticked/multi-token field-claims
    // are scanned — a genuinely non-vacuous run, not a green over zero input.
    expect(tools).toBeGreaterThan(30)
    expect(claims).toBeGreaterThan(8)
  })
})
