/**
 * kala_views_registration_uniqueness.test.ts — ṢAḌ-DARŚANA W0.4
 * (SHAD_DARSHANA_BRIEF_v2_0.md §2: "one canonical registration per tool, asserted by test").
 *
 * Scans platform-mcp/src/tools for `server.tool('kala_now_get'` / `server.tool('kala_ahead_get'`
 * call sites and asserts exactly one each — the eight-facade campaign runs six sibling lanes
 * concurrently in separate worktrees that each register their own view/capability tool name;
 * this is the mechanical guard against two lanes accidentally colliding on (or one lane
 * accidentally duplicating) the same tool name, per §N.7 (a status claim needs a real
 * detector, not "it hasn't broken yet").
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
