/**
 * description_payload_audit.ts — D-2 Lane V-3, CR-44 (BIND_D-2.md §F1.7 ledger row 23).
 *
 * Extends D-1.6's R-18 param-honesty harness PATTERN (platform/scripts/audit/tap/
 * r18_param_noop_audit.ts) from param-filtering to description-vs-payload: a tool's description
 * must not PROMISE a returned field/section the handler never emits. R-18 asks "is every declared
 * INPUT param honored?"; CR-44 asks "is every payload field the description NAMES actually produced?"
 *
 * METHOD (honestly stated, same class as R-18): a STATIC regex/brace pass over the MCP tool source
 * — no DB, no connector. For each `server.tool('name', '<description>', {schema}, handler)` it
 * extracts snake_case field names the description CLAIMS to return (backticked identifiers, and
 * identifiers following "returns/carries/section/field") and checks each appears as a whole word in
 * the handler body. A claimed field with zero handler occurrence is a presumptive description⇄payload
 * divergence. LIMITATION: like R-18 it cannot see fields produced by a shared wrapper (envelope/
 * dualOutput) or a delegate in another file — so a divergence flag is strong evidence, a PASS is
 * necessary-not-sufficient. Explained divergences are whitelisted with a written reason (the
 * "explicit flags allowed" clause of the DONE criterion).
 *
 * This module is the pure auditor; description_payload_audit.test.ts drives it under the platform
 * test gate and asserts zero UNEXPLAINED divergences. (CI-workflow wiring — ci.yml/tap-ci.yml — is
 * outside Lane V-3's may_touch; the test gate is the in-scope enforcement surface.)
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'

export type DescPayloadDivergence = { tool: string; file: string; claimed_field: string }

export type ExplainedDivergence = { tool: string; claimed_field: string; reason: string }

// Common English words that pass the snake_case-ish / following-keyword filters but are NOT payload
// field claims. Kept tight — over-broadening this hides real divergences.
const STOPWORDS = new Set([
  'the', 'a', 'an', 'this', 'that', 'each', 'all', 'one', 'same', 'full', 'default', 'true', 'false',
  'per', 'and', 'or', 'to', 'for', 'with', 'via', 'not', 'only', 'e_g', 'i_e', 'etc', 'chart_id',
  'response_format', 'it', 'its', 'their', 'them', 'you', 'your', 'is', 'are', 'be', 'as', 'in', 'on',
  'of', 'by', 'when', 'if', 'so', 'but', 'more', 'less', 'over', 'under', 'than', 'then', 'now',
])

/** Extract candidate payload-field CLAIMS from a description string. */
export function extractClaimedFields(description: string): string[] {
  const claims = new Set<string>()
  // (1) backticked identifiers: `verdict_summary`, `divisional_facts`
  for (const m of description.matchAll(/`([a-z][a-z0-9_]*)`/g)) claims.add(m[1])
  // (2) identifiers following a returns/carries/section/field keyword
  const kw = /\b(?:returns?|carr(?:y|ies|ying)|section|field|block|includes?|reports?)\b[^.`]{0,40}?\b([a-z][a-z0-9_]*_[a-z0-9_]+)\b/g
  for (const m of description.matchAll(kw)) claims.add(m[1])
  // keep only multi-token snake_case (a payload field is almost never a bare common word)
  return [...claims].filter((c) => c.includes('_') && !STOPWORDS.has(c))
}

function findMatchingClose(src: string, openIdx: number, openCh: string, closeCh: string): number {
  let depth = 1, i = openIdx
  while (i < src.length && depth > 0) { i++; if (src[i] === openCh) depth++; else if (src[i] === closeCh) depth-- }
  return i
}

type ToolBlock = { toolName: string; description: string; handlerBody: string }

export function extractToolBlocks(src: string): ToolBlock[] {
  const blocks: ToolBlock[] = []
  const toolCallRe = /server\.tool\(\s*\n?\s*'([a-zA-Z0-9_]+)'\s*,/g
  let m: RegExpExecArray | null
  while ((m = toolCallRe.exec(src)) !== null) {
    const toolName = m[1]
    const callStart = m.index + m[0].lastIndexOf('(', m[0].indexOf(toolName)) // '(' of server.tool(
    const openParen = src.indexOf('(', m.index)
    const callEnd = findMatchingClose(src, openParen, '(', ')')
    if (callEnd >= src.length) continue
    const callBody = src.slice(openParen + 1, callEnd)
    // description = concatenation of the string literal(s) that form the 2nd argument.
    // Grab the run of single-quoted string chunks (possibly '+'-joined) right after the name.
    const afterName = callBody.slice(callBody.indexOf(toolName) + toolName.length)
    // strip leading `',` then collect quoted chunks until the first `{` (schema) or `async`/param
    const descRegion = afterName.slice(afterName.indexOf(',') + 1)
    const cut = Math.min(
      ...['{', 'async', '=>'].map((s) => { const i = descRegion.indexOf(s); return i === -1 ? Infinity : i }),
    )
    const descChunk = Number.isFinite(cut) ? descRegion.slice(0, cut) : descRegion
    const description = [...descChunk.matchAll(/'((?:[^'\\]|\\.)*)'/g)].map((x) => x[1]).join(' ')
    blocks.push({ toolName, description, handlerBody: callBody })
  }
  return blocks
}

function listToolFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    if (entry === '__tests__') continue
    const full = path.join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) out.push(...listToolFiles(full))
    else if (entry.endsWith('.ts') && !entry.endsWith('.test.ts')) out.push(full)
  }
  return out
}

/**
 * Run the description-vs-payload audit over a tools directory.
 * @returns every divergence where a description-claimed field is absent from the handler body.
 */
export function auditDescriptionPayload(toolsDir: string, repoRoot: string): DescPayloadDivergence[] {
  const divergences: DescPayloadDivergence[] = []
  for (const file of listToolFiles(toolsDir)) {
    const src = readFileSync(file, 'utf-8')
    if (!src.includes('server.tool(')) continue
    for (const block of extractToolBlocks(src)) {
      const claimed = extractClaimedFields(block.description)
      for (const field of claimed) {
        // whole-word occurrence anywhere in the handler body (it's set into the returned payload,
        // read from the upstream payload, or named in a trim/section config).
        if (!new RegExp(`\\b${field}\\b`).test(block.handlerBody)) {
          divergences.push({ tool: block.toolName, file: path.relative(repoRoot, file), claimed_field: field })
        }
      }
    }
  }
  return divergences
}
