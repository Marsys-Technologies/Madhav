/**
 * extract_registry_bridge_tools.ts — mechanical extraction of the live
 * ~25 hand-written `server.tool(...)` blocks in `platform-mcp/src/tools/
 * registry_bridge.ts`, for the R-1 projection-compiler comparison report
 * (plan §3 R-1 item 2b: "compare against the ~25 hand-written server.tool
 * blocks in registry_bridge.ts — report differences, don't replace").
 *
 * METHOD (mechanical, not hand-typed — same discipline as the W1 harvest
 * lane's `rescan_dark_tables_widened_surface.ts` / `scanImportSites()`):
 * reads the real source file as text and hand-parses each `server.tool(`
 * call site's first one or two string-literal arguments (name, and
 * description when present — see below) plus every `marsys://...` URI
 * literal referenced in that tool's body (up to the next `server.tool(` or
 * EOF), using a small quote-aware scanner (handles `\'`/`\"` escapes; the
 * real file mixes both single- and double-quote delimiters and one long
 * escaped-apostrophe description). This is NOT a TS/AST parse — a real
 * syntax change to the file (e.g. reordering args) could defeat it; the
 * PARITY TEST asserts a set of known tool names round-trip through this
 * extractor as a tripwire against silent breakage.
 *
 * REAL FINDING this extraction surfaces (not asserted, discovered): 7 of the
 * 25 `server.tool()` calls use the SDK's 3-arg overload — `server.tool(name,
 * schema, handler)` — with NO top-level description string at all (the
 * literal character immediately after the name is `{`, not a quote). Those
 * 7 entries get `description: null` here, not a fabricated/guessed string.
 *
 * Does not import `registry_bridge.ts` (it requires an `@modelcontextprotocol/
 * sdk` `McpServer` instance + a live `Principal` to execute) — this is a
 * source-text read only, cross-package (platform → platform-mcp), same class
 * of read the plan's own audit findings (GT-3, GT-40) are sourced from.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

export const REGISTRY_BRIDGE_PATH = join(
  __dirname,
  '..',
  '..',
  '..',
  'platform-mcp',
  'src',
  'tools',
  'registry_bridge.ts',
)

export interface ExtractedMcpToolBlock {
  tool_name: string
  /** null when the block uses the SDK's 3-arg (name, schema, handler) overload — no description literal. */
  description: string | null
  description_length: number
  /** Every distinct `marsys://...` URI literal referenced in this tool's body (registry capabilities it touches). */
  referenced_uris: string[]
  source_line: number
}

function lineNumberAt(text: string, index: number): number {
  let line = 1
  for (let i = 0; i < index; i++) if (text[i] === '\n') line++
  return line
}

/** Quote-aware scan of a string literal starting at `s[i]` (s[i] must be `'`, `"`, or `` ` ``). */
function scanStringLiteral(s: string, i: number): { content: string; end: number } {
  const quote = s[i]
  let j = i + 1
  let content = ''
  while (j < s.length && s[j] !== quote) {
    if (s[j] === '\\') {
      content += s[j] + (s[j + 1] ?? '')
      j += 2
    } else {
      content += s[j]
      j += 1
    }
  }
  return { content, end: j + 1 }
}

const URI_RE = /marsys:\/\/[^\s'"`)]+/g

/**
 * Extract all `server.tool(...)` blocks from the real registry_bridge.ts
 * source. Reads `sourceText` directly (caller-supplied) so this stays a pure,
 * testable function — the CLI/test call sites are responsible for the fs
 * read (see `REGISTRY_BRIDGE_PATH` above for the real file's location).
 */
export function extractRegistryBridgeTools(sourceText: string): ExtractedMcpToolBlock[] {
  const CALL_MARKER = 'server.tool('
  const positions: number[] = []
  let searchFrom = 0
  for (;;) {
    const idx = sourceText.indexOf(CALL_MARKER, searchFrom)
    if (idx === -1) break
    positions.push(idx)
    searchFrom = idx + CALL_MARKER.length
  }

  const blocks: ExtractedMcpToolBlock[] = []
  for (let b = 0; b < positions.length; b++) {
    const start = positions[b]!
    const blockEnd = b + 1 < positions.length ? positions[b + 1]! : sourceText.length
    let i = start + CALL_MARKER.length
    while (i < sourceText.length && /\s/.test(sourceText[i]!)) i++

    // Defensive: the name arg is always a plain string literal in the real file (verified
    // by construction of this extractor against the live source) — if a future edit
    // changes that shape, skip rather than silently fabricate a block.
    if (!"'\"`".includes(sourceText[i] ?? '')) continue
    const { content: toolName, end: afterName } = scanStringLiteral(sourceText, i)

    // Skip past `,` / whitespace to the next argument.
    let j = afterName
    while (j < blockEnd && /[,\s]/.test(sourceText[j]!)) j++

    let description: string | null = null
    if ("'\"`".includes(sourceText[j] ?? '')) {
      const { content } = scanStringLiteral(sourceText, j)
      description = content
    }
    // else: sourceText[j] === '{' — the 3-arg (name, schema, handler) overload, no description.

    const body = sourceText.slice(start, blockEnd)
    const referenced_uris = Array.from(new Set(Array.from(body.matchAll(URI_RE)).map((m) => m[0])))
      .sort()

    blocks.push({
      tool_name: toolName,
      description,
      description_length: description?.length ?? 0,
      referenced_uris,
      source_line: lineNumberAt(sourceText, start),
    })
  }
  return blocks
}

/** Convenience: read the real file and extract. Throws if the file is unreadable (never silently empty). */
export function extractRegistryBridgeToolsFromDisk(): ExtractedMcpToolBlock[] {
  const text = readFileSync(REGISTRY_BRIDGE_PATH, 'utf-8')
  return extractRegistryBridgeTools(text)
}
