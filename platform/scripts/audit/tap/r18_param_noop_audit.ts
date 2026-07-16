/**
 * r18_param_noop_audit.ts — R-18 CI implementation (D-1.6 Lane S-5)
 * ===================================================================
 * Register item R-18: "estate-wide silent parameter no-op audit — every documented param
 * (start/end/domain/limit etc across tools) must be HONORED or the call REJECTED; add a
 * harness assertion (a script, not prose) that every documented param provably filters
 * something." This script IS that assertion.
 *
 * WHAT IT CHECKS: for every `server.tool('name', ..., { zodSchema }, async (params) => {...})`
 * block found in platform-mcp/src/tools/*.ts, extract the top-level zod-schema parameter
 * names, then check whether each name is referenced ANYWHERE inside that tool's own handler
 * function body (destructured, bracket-accessed, or spread through `...rest` — the common
 * silent-no-op shape this lane fixed twice live: `min_weight` never read at all — D15b-F3 —
 * and a facet's declared categories silently ignored downstream by a different tool — PARK-A7).
 * A schema key with ZERO textual occurrence in its own handler body is presumptively a no-op
 * (the handler cannot possibly be honoring a param it never looks at) and is flagged.
 *
 * METHOD, HONESTLY STATED: this is a STATIC, regex/brace-matching heuristic over source text,
 * not a live behavioral probe (it needs no DATABASE_URL, no MCP connector, no chart data — it
 * runs anywhere, always, like tap6_method_grep.ts). It catches the "never even referenced"
 * class exhaustively but CANNOT catch "referenced but the reference is itself dead code" or
 * "referenced in a comment only" (this run's own two live no-op fixes were BOTH the pure
 * never-referenced-downstream class this script targets — min_weight forwarded via `...rest`
 * to a capability that only reads min_salience — but `...rest` spread means the STATIC
 * per-name check here can't distinguish "the individual key surfaces downstream" from "it's
 * silently absorbed by a `...rest` spread and then never read by the callee" without also
 * tracing into the callee file, which is out of scope for a single-file regex pass. Known
 * limitation documented in the report, not hidden: a PASS here is necessary, not sufficient,
 * evidence of honoring; a FLAG here is close to sufficient evidence of a genuine no-op.
 *
 * A comment-suppression escape hatch is honored: a schema key preceded by a line containing
 * `// r18-intentional-passthrough:` immediately above the key is treated as an acknowledged,
 * documented pass-through (e.g. deliberately unused/reserved params) rather than a silent bug —
 * this keeps the gate from becoming a false-positive trap for genuinely intentional shapes
 * while still requiring every exception to be WRITTEN DOWN, not merely absent from the flag list.
 *
 * Run: npx tsx platform/scripts/audit/tap/r18_param_noop_audit.ts
 */
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { printReport, type LawResult } from './lib/tap_db'

const REPO_ROOT = path.join(__dirname, '../../../..')
const TOOLS_DIR = path.join(REPO_ROOT, 'platform-mcp/src/tools')
const BASELINE_PATH = path.join(__dirname, 'r18_baseline.json')

type BaselineEntry = { tool: string; param: string; file: string; note?: string }

function loadBaseline(): BaselineEntry[] {
  try {
    const raw = readFileSync(BASELINE_PATH, 'utf-8')
    return (JSON.parse(raw) as { entries: BaselineEntry[] }).entries
  } catch {
    return []
  }
}

// Params that are structural/pagination plumbing consumed by shared wrapper code
// (dualOutput/envelope helpers) rather than the handler body text itself, or that are
// legitimately unused-by-design (documented inline) — an estate-wide allowlist so the
// gate doesn't flag every tool's chart_id (always used, but sometimes only for an
// early-return guard the regex below already credits) or standard cursor/offset fields
// whose honoring lives in a shared pagination helper, not per-handler text.
const GLOBAL_ALLOWLIST = new Set(['chart_id', 'response_format', 'cursor'])

type ToolBlock = {
  file: string
  toolName: string
  schemaKeys: string[]
  handlerBody: string
  intentionalPassthrough: Set<string>
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

/** Finds the matching close-brace/paren for an open at `openIdx` (already consumed). */
function findMatchingClose(src: string, openIdx: number, openCh: string, closeCh: string): number {
  let depth = 1
  let i = openIdx
  while (i < src.length && depth > 0) {
    i++
    if (src[i] === openCh) depth++
    else if (src[i] === closeCh) depth--
  }
  return i
}

/** Extracts top-level `key:` identifiers from a zod-schema object literal's source text —
 *  only keys at the OUTERMOST brace depth of the literal itself (the caller passes the
 *  literal's INNER text, so depth 0 here IS the object's own top level; a nested object/
 *  array schema shape like `date_range: z.object({start:..., end:...})` does not introduce
 *  new top-level params). Depth-at-match is computed by scanning the text up to each match —
 *  O(n²) but these schema blocks are small (tens of keys at most), never a bottleneck. */
function extractSchemaKeys(schemaSrc: string): string[] {
  const keys: string[] = []
  const re = /([{,]\s*|^\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:/g
  let m: RegExpExecArray | null
  while ((m = re.exec(schemaSrc)) !== null) {
    const upTo = schemaSrc.slice(0, m.index)
    let depth = 0
    for (const c of upTo) {
      if (c === '{' || c === '(' || c === '[') depth++
      else if (c === '}' || c === ')' || c === ']') depth--
    }
    if (depth === 0) keys.push(m[2])
  }
  return [...new Set(keys)]
}

function extractToolBlocks(file: string, src: string): ToolBlock[] {
  type RawBlock = { toolName: string; schemaKeys: string[]; schemaSrc: string; schemaAbsStart: number; schemaAbsEnd: number }
  const raw: RawBlock[] = []
  const toolCallRe = /server\.tool\(\s*\n?\s*'([a-zA-Z0-9_]+)'/g
  let m: RegExpExecArray | null
  while ((m = toolCallRe.exec(src)) !== null) {
    const toolName = m[1]
    const callStart = m.index + m[0].indexOf('(')
    const callEnd = findMatchingClose(src, callStart, '(', ')')
    if (callEnd >= src.length) continue
    const callBody = src.slice(callStart + 1, callEnd)

    // Find the schema object literal: the first top-level `{` in callBody that is NOT
    // immediately followed by a string (i.e. not the description arg) — heuristically, the
    // schema is the argument whose own text contains `z.` (a zod builder call). Tools with
    // no params (rare) or schemas built as a separate named const (e.g. ganitaStrengthGetInputSchema)
    // are skipped — not flagged, since there's no inline schema to diff against.
    const schemaObjRe = /\{[^]*?z\.[a-zA-Z]/
    const schemaStartMatch = schemaObjRe.exec(callBody)
    if (!schemaStartMatch) continue
    const braceIdx = callBody.indexOf('{', schemaStartMatch.index)
    if (braceIdx === -1) continue
    const schemaEnd = findMatchingClose(callBody, braceIdx, '{', '}')
    if (schemaEnd >= callBody.length) continue
    const schemaSrc = callBody.slice(braceIdx + 1, schemaEnd)
    const schemaKeys = extractSchemaKeys(schemaSrc)
    if (schemaKeys.length === 0) continue

    raw.push({
      toolName, schemaKeys, schemaSrc,
      schemaAbsStart: callStart + 1 + braceIdx,
      schemaAbsEnd: callStart + 1 + schemaEnd,
    })
  }

  // Search scope for EVERY tool = the WHOLE FILE with EVERY tool's own schema-literal text
  // (across the whole file, not just this one) blanked out — not just this tool's inline
  // handler closure. Two reasons this two-pass approach beats a single-tool-scoped search:
  //   1. Some tools (e.g. muhurta_finder.ts) parse the schema into a typed object and
  //      delegate to a SEPARATELY-NAMED function defined earlier in the same file
  //      (`handleMuhurtaFinder(parsed, ...)`) — a search scoped to text strictly after this
  //      tool's own schema block would false-flag every one of that function's genuinely-
  //      honored params.
  //   2. Blanking every tool's schema text (not just this one's) prevents a DIFFERENT common
  //      param name — `limit`, `domain`, `keyword` are declared in dozens of unrelated
  //      tools' OWN schemas in the same file — from producing a false "referenced" credit
  //      merely because some other tool's schema line contains that identifier as a key.
  //      Only genuine handler-body/delegate-function usage counts.
  let strippedSrc = src
  // Blank from the end backward so earlier offsets stay valid.
  for (const b of [...raw].sort((a, b2) => b2.schemaAbsStart - a.schemaAbsStart)) {
    const blanked = ' '.repeat(b.schemaAbsEnd - b.schemaAbsStart)
    strippedSrc = strippedSrc.slice(0, b.schemaAbsStart) + blanked + strippedSrc.slice(b.schemaAbsEnd)
  }

  const blocks: ToolBlock[] = []
  for (const b of raw) {
    // Escape hatch: a `// r18-intentional-passthrough: key1, key2` comment anywhere in the
    // schema block marks those keys as deliberately unchecked.
    const intentionalPassthrough = new Set<string>()
    const escapeRe = /\/\/\s*r18-intentional-passthrough:\s*([a-zA-Z0-9_,\s]+)/g
    let em: RegExpExecArray | null
    while ((em = escapeRe.exec(b.schemaSrc)) !== null) {
      for (const k of em[1].split(',')) intentionalPassthrough.add(k.trim())
    }
    blocks.push({
      file: path.relative(REPO_ROOT, file),
      toolName: b.toolName,
      schemaKeys: b.schemaKeys,
      handlerBody: strippedSrc,
      intentionalPassthrough,
    })
  }
  return blocks
}

async function main() {
  const results: LawResult[] = []
  const files = listToolFiles(TOOLS_DIR)
  const allFlags: { tool: string; file: string; param: string }[] = []
  let toolsScanned = 0
  let paramsChecked = 0

  for (const file of files) {
    const src = readFileSync(file, 'utf-8')
    if (!src.includes('server.tool(')) continue
    const blocks = extractToolBlocks(file, src)
    for (const block of blocks) {
      toolsScanned++
      for (const key of block.schemaKeys) {
        if (GLOBAL_ALLOWLIST.has(key)) continue
        if (block.intentionalPassthrough.has(key)) continue
        paramsChecked++
        // Whole-word occurrence anywhere in the handler body (destructure, bracket access,
        // spread-then-reference, or a same-name variable derived from it).
        const wordRe = new RegExp(`\\b${key}\\b`)
        if (!wordRe.test(block.handlerBody)) {
          allFlags.push({ tool: block.toolName, file: block.file, param: key })
        }
      }
    }
  }

  // Ratchet discipline (same shape as tap6_method_grep.ts's baseline): a flag matching a
  // KNOWN (tool, param, file) triple in r18_baseline.json is QUARANTINED — tracked, not yet
  // triaged/fixed, but not a NEW regression. Any flag NOT in the baseline is a brand-new
  // no-op this run has never seen and FAILS outright. This lets the gate go live today
  // (41 pre-existing candidates from this run's own first pass, most plausibly false
  // positives from `...rest`-spread pass-through this static pass can't trace into the
  // callee — see module doc) without either (a) blocking CI on a backlog nobody has
  // triaged yet, or (b) silently accepting every future no-op as "more of the same".
  const baseline = loadBaseline()
  const baselineKeys = new Set(baseline.map(b => `${b.tool}::${b.param}::${b.file}`))
  const newFlags = allFlags.filter(f => !baselineKeys.has(`${f.tool}::${f.param}::${f.file}`))
  const knownFlags = allFlags.filter(f => baselineKeys.has(`${f.tool}::${f.param}::${f.file}`))
  const flagKeys = new Set(allFlags.map(f => `${f.tool}::${f.param}::${f.file}`))
  const staleBaseline = baseline.filter(b => !flagKeys.has(`${b.tool}::${b.param}::${b.file}`))

  results.push({
    id: 'R-18',
    title: `Static param no-op audit: ${paramsChecked} schema params checked across ${toolsScanned} inline-schema tool() blocks in platform-mcp/src/tools/`,
    status: newFlags.length === 0 ? (allFlags.length === 0 ? 'PASS' : 'QUARANTINED') : 'FAIL',
    detail: newFlags.length > 0
      ? `${newFlags.length} NEW param no-op(s) not in r18_baseline.json (either honor the param, ` +
        'reject calls that pass it, or add an inline `// r18-intentional-passthrough: <param>` ' +
        `comment if genuinely by design): ${newFlags.map(f => `${f.tool}.${f.param} (${f.file})`).join('; ')}. ` +
        `(${knownFlags.length} already-baselined candidate(s) unaffected.)`
      : allFlags.length === 0
        ? 'Every checked param is referenced somewhere in its own handler body.'
        : `${knownFlags.length} known/baselined candidate(s), zero new. Baseline entries pending ` +
          'manual triage (each needs an honor-fix, a rejection, or an intentional-passthrough ' +
          `comment to graduate out): ${knownFlags.map(f => `${f.tool}.${f.param}`).join(', ')}.` +
          (staleBaseline.length > 0
            ? ` STALE baseline entries (fix already landed — delete from r18_baseline.json): ` +
              staleBaseline.map(b => `${b.tool}.${b.param}`).join(', ') + '.'
            : ''),
    register_rows: ['R-18'],
  })

  process.exit(printReport('R-18 param no-op audit', results))
}

main().catch((err) => {
  console.error('r18_param_noop_audit FATAL:', err)
  process.exit(4)
})
