/**
 * kala_views_registration_uniqueness.test.ts — ṢAḌ-DARŚANA W0.4 + G12e
 * (SHAD_DARSHANA_BRIEF_v2_0.md §2: "one canonical registration per tool, asserted by test").
 *
 * Scans platform-mcp/src/tools for `server.tool('kala_now_get'` / `server.tool('kala_ahead_get'`
 * / `server.tool('kala_dasha_sandhi_get'` call sites and asserts exactly one each — the
 * nine-facade campaign runs sibling lanes concurrently in separate worktrees that each register
 * their own view/capability tool name; this is the mechanical guard against two lanes
 * accidentally colliding on (or one lane accidentally duplicating) the same tool name, per §N.7
 * (a status claim needs a real detector, not "it hasn't broken yet").
 *
 * G12e (SAMPURTI L0c): also asserts that ALL nine kala_views tool names appear exactly once in
 * platform-mcp/src/tools — a catalog-completeness census that would have caught the W6-C1
 * "eight tools in docstring" drift (the W3-CAL dasha-sandhi lane added the ninth but the
 * docstrings were never updated). The census list is the authoritative enumeration; any
 * addition to kala_views/ must add an entry here before merging.
 *
 * Deliberately source-scans rather than importing+registering-on-a-mock-server: a duplicate
 * registration bug is just as likely to be "two DIFFERENT files both call server.tool with
 * this name" as "one file calls it twice" — only a source-wide scan catches the former.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const TOOLS_DIR = join(fileURLToPath(new URL('.', import.meta.url)), '..', 'tools')

function listTsFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) out.push(...listTsFiles(full))
    else if (entry.isFile() && entry.name.endsWith('.ts') && !entry.name.endsWith('.test.ts')) out.push(full)
  }
  return out
}

// Matches every `server.tool(<firstArg>,` call site, capturing <firstArg> as EITHER a
// quoted string literal OR a bare identifier (this codebase uses both conventions — some
// registrars inline the literal name, others bind it to a `const TOOL_NAME = '...'` first,
// per file — see now.ts/ahead.ts's own TOOL_NAME pattern vs. register_p1_aliases.ts's
// inline-literal calls).
const CALL_SITE_PATTERN = /server\.tool\(\s*(?:'([^']+)'|([A-Za-z_][A-Za-z0-9_]*))\s*,/g

/**
 * Resolves every `server.tool(...)` call site in `text` to the tool-name string it
 * registers — following one level of `const <ident> = '<literal>'` indirection when the
 * first argument is a bare identifier rather than an inline string literal. Returns the
 * resolved name for each call site (undefined entries are calls this scanner could not
 * resolve, e.g. a dynamically-computed name — none exist in this codebase today, but the
 * scanner stays honest about the limit rather than silently miscounting).
 */
function resolveCallSiteNames(text: string): (string | undefined)[] {
  const names: (string | undefined)[] = []
  for (const match of text.matchAll(CALL_SITE_PATTERN)) {
    const [, literal, ident] = match
    if (literal !== undefined) {
      names.push(literal)
      continue
    }
    if (ident !== undefined) {
      const constMatch = new RegExp(`const\\s+${ident}\\s*=\\s*'([^']+)'`).exec(text)
      names.push(constMatch?.[1])
    }
  }
  return names
}

function countRegistrations(toolName: string): number {
  let count = 0
  for (const file of listTsFiles(TOOLS_DIR)) {
    const text = readFileSync(file, 'utf8')
    count += resolveCallSiteNames(text).filter((n) => n === toolName).length
  }
  return count
}

describe('kala_now_get / kala_ahead_get — one canonical registration each', () => {
  it('kala_now_get: exactly one server.tool() call site in platform-mcp/src/tools', () => {
    expect(countRegistrations('kala_now_get')).toBe(1)
  })

  it('kala_ahead_get: exactly one server.tool() call site in platform-mcp/src/tools', () => {
    expect(countRegistrations('kala_ahead_get')).toBe(1)
  })
})

/**
 * G12e (SAMPURTI L0c) — Nine-tool catalog census for kala_views.
 *
 * Asserts that every kala_views tool name is registered EXACTLY ONCE in the tools directory.
 * This is the mechanical detector that would have caught the W6-C1 "eight tools" docstring
 * drift: the dasha_sandhi lane added the ninth tool but the count references were never
 * updated. The test here is the real detector; the docstring count is its consequence.
 *
 * WHY THIS CATCHES THE PRODUCTION-SERVES-8 HYPOTHESIS TOO: if `kala_dasha_sandhi_get` had
 * been left entirely unregistered (the "code gap" scenario), countRegistrations would return
 * 0 and this test would fail at CI — meaning any code gap in registration shows up here,
 * not just at live production probe time.
 *
 * The nine canonical kala_views tool names (authoritative enumeration):
 *   kala_now_get, kala_ahead_get, kala_upaya_get, kala_ritual_get, kala_priority_get,
 *   kala_explain_get, kala_elect_get, kala_story_get, kala_dasha_sandhi_get.
 */
describe('kala_views — nine-tool catalog census (G12e)', () => {
  const EXPECTED_KALA_TOOLS = [
    'kala_now_get',
    'kala_ahead_get',
    'kala_upaya_get',
    'kala_ritual_get',
    'kala_priority_get',
    'kala_explain_get',
    'kala_elect_get',
    'kala_story_get',
    'kala_dasha_sandhi_get',
  ] as const

  it('all nine kala_views tool names are registered exactly once in platform-mcp/src/tools', () => {
    for (const toolName of EXPECTED_KALA_TOOLS) {
      expect(
        countRegistrations(toolName),
        `${toolName}: expected exactly 1 server.tool() call site; got a different count — ` +
        `either the tool is unregistered (0) or duplicated (>1). ` +
        `Check platform-mcp/src/tools/kala_views/ and register_all.ts.`,
      ).toBe(1)
    }
  })

  it('kala_dasha_sandhi_get specifically: exactly one registration (G12e primary gate)', () => {
    // This assertion is the primary detector for the G12e hypothesis.
    // If production was serving 8 tools due to a code gap (missing registration), this returns 0.
    // If a duplicate registration crept in, this returns >1.
    // The expected value of 1 means the code is correctly wired; the live production check
    // at gate time (Wave-0 deploy) then closes the deploy-lag scenario.
    expect(countRegistrations('kala_dasha_sandhi_get')).toBe(1)
  })
})
