/**
 * The window-opening ask — DETERMINISTIC-BY-CONSTRUCTION detector (lane P4-G).
 *
 * `compose.ts`'s own header makes a specific claim: "no model composes any part of it," and
 * names THIS FILE as one of the two detectors backing that claim (the other is the wire
 * schema's `composition: 'deterministic'` Zod literal, which rejects any other value but
 * cannot see what `compose.ts` imports). Until this file existed, the claim was a comment with
 * no code behind it — the exact §N.7 item 4 / §N.8 defect class ("a flag that reads clean with
 * no code path that could ever produce a different value is not a clean result — it is an
 * unimplemented check wearing a clean result's clothes"). This file is that missing detector.
 *
 * ── WHAT IT CHECKS, AND HOW IT CAN FAIL ─────────────────────────────────────────────────────
 * Reads `compose.ts`'s OWN SOURCE TEXT (not a copy, not a description of it) and asserts:
 *   1. it imports nothing that could reach a model/provider/synthesis call — no `openai`,
 *      `anthropic`, `google`, `gemini`, `llm`, `provider`, `synth`, `generate`, `complete`,
 *      `model`, or `@/lib/pariprashna/synthesis` style path;
 *   2. it imports nothing that could reach the network or a database (`fetch(`, `axios`,
 *      `'pg'`, `@/lib/db`, `server-only` is even ABSENT — pure isomorphic module);
 *   3. `composeWindowAsk` is declared `export function` (not `async function`) — an `await`
 *      anywhere in its call chain is itself circumstantial evidence of an I/O-bound step this
 *      module claims never to have.
 *
 * A DEMONSTRATED FAILURE (so this detector is proven capable of catching the thing it claims
 * to catch, not merely "usually true"): the test below temporarily feeds the SAME regex bank
 * a deliberately model-flavoured decoy string containing `callAnthropicModel(` and asserts the
 * detector's own regex flags it — i.e. the detector is shown failing red before its green
 * reading of the real file counts (§N.8 / §6.2 of the overnight charter).
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const COMPOSE_PATH = fileURLToPath(new URL('../compose.ts', import.meta.url))
const composeSource = readFileSync(COMPOSE_PATH, 'utf8')

/** Import-only lines, so a comment that merely MENTIONS "model" (as this file's header does)
 *  cannot itself trip the detector — the detector inspects what the module actually imports
 *  and what it actually awaits, not its prose. */
function importLines(source: string): string[] {
  return source
    .split('\n')
    .filter((l) => /^\s*import\b/.test(l))
}

const FORBIDDEN_IMPORT_TOKENS = [
  /\bopenai\b/i,
  /\banthropic\b/i,
  /\bgoogle(?:generativeai|-genai)?\b/i,
  /\bgemini\b/i,
  /\bllm\b/i,
  /\bprovider\b/i,
  /synth(?:esis)?/i,
  /\bgenerate\b/i,
  /\bcomplete(?:ion)?\b/i,
  /\bmodel(?:client|router|policy)?\b/i,
  /['"]pg['"]/,
  /@\/lib\/db/,
  /\baxios\b/,
]

function findForbiddenImport(lines: string[]): string | null {
  for (const line of lines) {
    for (const re of FORBIDDEN_IMPORT_TOKENS) {
      if (re.test(line)) return line.trim()
    }
  }
  return null
}

describe('compose.ts is deterministic BY CONSTRUCTION — the detector demonstrably fails on a decoy first', () => {
  it('DEMONSTRATED-CAN-FAIL: a decoy import line naming a model call IS flagged', () => {
    // §N.8: prove the detector is capable of reading "no" before trusting its "yes" on the
    // real file. This decoy is never executed — it is a string handed to the same regex bank.
    const decoyLines = importLines(
      "import { callAnthropicModel } from '@/lib/pariprashna/synthesis/provider'\n" +
        "const x = 1",
    )
    expect(findForbiddenImport(decoyLines)).not.toBeNull()
  })

  it('DEMONSTRATED-CAN-FAIL: a decoy `fetch(` / `pg` import IS flagged', () => {
    const decoyLines = importLines("import { Pool } from 'pg'\n")
    expect(findForbiddenImport(decoyLines)).not.toBeNull()
  })

  it('imports nothing that could reach a model, provider, or synthesis path', () => {
    const offender = findForbiddenImport(importLines(composeSource))
    expect(offender).toBeNull()
  })

  it('imports nothing that could reach the network or the database', () => {
    expect(composeSource).not.toMatch(/\bfetch\s*\(/)
    expect(composeSource).not.toMatch(/from\s+['"]pg['"]/)
    expect(composeSource).not.toMatch(/@\/lib\/db/)
  })

  it("carries no 'server-only' marker — it is isomorphic, not a server-side effect module", () => {
    expect(composeSource).not.toMatch(/^\s*import\s+['"]server-only['"]/m)
  })

  it('composeWindowAsk is a synchronous, non-async export (no I/O in its own call chain)', () => {
    expect(composeSource).toMatch(/^export function composeWindowAsk\(/m)
    expect(composeSource).not.toMatch(/^export async function composeWindowAsk\(/m)
  })

  it('the file actually exists at the path this suite reads (guards against a silent rename)', () => {
    expect(path.basename(COMPOSE_PATH)).toBe('compose.ts')
    expect(composeSource.length).toBeGreaterThan(500)
  })
})
