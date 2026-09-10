/**
 * Paripraśna semantic block classifier — lane P2-A (PPR-07, FD-1).
 *
 * SERVER-SIDE, COMMIT-TIME classification: the server holds the FULL block
 * text at commit, so this runs exactly once, on a finished string — never a
 * mid-stream segmentation heuristic that has to guess at an incomplete tail.
 * That is the design point the roadmap names explicitly: "deterministic,
 * testable; NOT mid-stream segmentation."
 *
 * Every rule below is a structural/markdown-convention match on the block's
 * OWN text — no LLM call, no fabrication (CLAUDE.md §N.4 "deterministic-
 * first"), and each rule is intentionally narrow so it does not fire on
 * ordinary prose that merely contains a superficially similar character (a
 * stray `|`, a `>` mid-sentence, the word "silent" in an unrelated sentence).
 * See `__tests__/block_classifier.test.ts` for a real, distinguishing
 * positive/negative pair per kind.
 *
 * Isomorphic (no `server-only`, no DB, no Node-only API) so it is directly
 * unit-testable and could, in principle, be shared with a future client-side
 * preview — though today it only runs server-side, in
 * `pipeline/reading_parts.ts`'s `commitBlock()`.
 */

export type WireBlockKind = 'paragraph' | 'heading' | 'table' | 'verse' | 'gap_ribbon'
export type WireReadingRole = 'verdict' | 'elaboration' | 'verse' | 'caveat'

export interface BlockTable {
  headers: string[]
  rows: string[][]
}

/**
 * A markdown table found EMBEDDED inside a larger paragraph block (DD-22,
 * approach (c) — "annotate rather than split"). `start`/`end` are exact
 * character offsets into the block's own raw `text` (never a normalized or
 * trimmed copy), so `text.slice(0, spans[0].start)`, `text.slice(spans[0].start,
 * spans[0].end)`, `text.slice(spans[0].end, ...)`, etc. concatenate back to
 * `text` byte-for-byte — the renderer's reconstruction, not this module's,
 * but only possible because the offsets are exact.
 */
export interface BlockTableSpan {
  start: number
  end: number
  table: BlockTable
}

export interface BlockClassification {
  kind: WireBlockKind
  /** Only set when `kind === 'paragraph'`. */
  role?: WireReadingRole
  /** Reader-facing text when it differs from the raw committed text (verse
   *  with `>` stripped, heading with `#`s stripped). Undefined ⇒ the raw
   *  text is already reader-ready as-is. */
  content?: string
  /** Only set when `kind === 'table'` — the WHOLE block is one table (the
   *  original, stronger detector: header + separator + data rows occupy the
   *  entire committed text). */
  table?: BlockTable
  /** Only set when `kind === 'paragraph'` AND the block's text contains one
   *  or more embedded tables that do NOT occupy the whole block (DD-22).
   *  `kind` stays `'paragraph'` — this is metadata alongside it, not a
   *  reclassification; `committedBlocks`' cardinality is unchanged (one
   *  block per role-shift, same as before this field existed). */
  tableSpans?: BlockTableSpan[]
  /** Only set when `kind === 'gap_ribbon'`. */
  gapText?: string
}

// ---------------------------------------------------------------------------
// Kind detectors
// ---------------------------------------------------------------------------

/** A GFM-style separator row: `---`, `:--`, `--:`, `:-:`, one or more cells,
 *  optionally piped at the edges. Requires at least 2 dashes per cell so a
 *  bare `-` (a list-item marker, not a table separator) never matches. */
const TABLE_SEPARATOR_ROW = /^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$/

function splitTableRow(line: string): string[] {
  let l = line.trim()
  if (l.startsWith('|')) l = l.slice(1)
  if (l.endsWith('|')) l = l.slice(0, -1)
  return l.split('|').map((cell) => cell.trim())
}

/**
 * Parses a GFM markdown table: a header row containing `|`, immediately
 * followed by a valid separator row, then one or more data rows. Returns
 * `null` (not a table) for anything short of that — in particular, ordinary
 * prose that happens to contain a `|` character does NOT match, because it
 * has no following separator row.
 */
function parseMarkdownTable(text: string): BlockTable | null {
  const lines = text
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.length > 0)
  if (lines.length < 2) return null
  const [headerLine, sepLine, ...rest] = lines
  if (!headerLine.includes('|')) return null
  if (!TABLE_SEPARATOR_ROW.test(sepLine)) return null

  const headers = splitTableRow(headerLine)
  const rows = rest.map(splitTableRow).filter((r) => r.some((cell) => cell.length > 0))
  if (headers.length === 0 || rows.length === 0) return null
  return { headers, rows }
}

/**
 * Scan a block's RAW (untrimmed) text for GFM markdown table(s) that do NOT
 * occupy the whole block — a header line containing `|`, immediately
 * followed by a valid separator row, then one or more data rows, with prose
 * before and/or after. Unlike `parseMarkdownTable`, which requires line 0 to
 * be the header and fails on any leading prose, this scans every line as a
 * candidate header. Only called from the `paragraph` fallback path below —
 * a block whose ENTIRE text is a table is caught by `parseMarkdownTable`
 * first and never reaches this function, so no double-classification.
 *
 * Offsets are computed from the ORIGINAL, unmodified `text` — never a
 * trimmed or normalized copy — so callers can slice `text` at these exact
 * boundaries and reconstruct it byte-for-byte (DD-22 acceptance criterion
 * 1). Returns `[]` when no embedded table is found.
 */
export function detectTableSpans(text: string): BlockTableSpan[] {
  const rawLines = text.split('\n')
  const lineStarts: number[] = []
  let offset = 0
  for (const line of rawLines) {
    lineStarts.push(offset)
    offset += line.length + 1 // +1 accounts for the '\n' this split() consumed
  }

  const spans: BlockTableSpan[] = []
  let i = 0
  while (i < rawLines.length - 1) {
    const headerLine = rawLines[i].trim()
    const sepLine = rawLines[i + 1].trim()
    if (headerLine.includes('|') && TABLE_SEPARATOR_ROW.test(sepLine)) {
      let j = i + 2
      const dataLines: string[] = []
      while (j < rawLines.length && rawLines[j].trim().includes('|')) {
        dataLines.push(rawLines[j])
        j++
      }
      const headers = splitTableRow(headerLine)
      const rows = dataLines.map(splitTableRow).filter((r) => r.some((cell) => cell.length > 0))
      if (headers.length > 0 && rows.length > 0) {
        const lastLineIdx = j - 1
        spans.push({
          start: lineStarts[i],
          end: lineStarts[lastLineIdx] + rawLines[lastLineIdx].length,
          table: { headers, rows },
        })
        i = j
        continue
      }
    }
    i++
  }
  return spans
}

/** True iff every non-empty line of the block is a markdown blockquote line
 *  (starts with `>`) — the convention a classical verse quote is committed
 *  under. A block that merely contains a `>` mid-sentence does not match. */
function isBlockquote(text: string): boolean {
  const lines = text
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.length > 0)
  return lines.length > 0 && lines.every((l) => l.startsWith('>'))
}

function stripBlockquote(text: string): string {
  return text
    .split('\n')
    .map((l) => l.trim().replace(/^>\s?/, ''))
    .join('\n')
    .trim()
}

/** The honest-gap phrasing convention (matches the ribbon's own fixed header
 *  "The chart is silent here" / the honest-gap fixture's body phrasing). */
const GAP_RIBBON_PATTERN = /\bthe chart is silent\b/i

/** A single-line ATX markdown heading (`#` through `######`) that is the
 *  WHOLE block — a `#` appearing mid-paragraph (a hashtag, a literal pound
 *  sign) does not match because the block carries more than that one line,
 *  or the line has content before the `#`. */
const HEADING_LINE = /^(#{1,6})\s+(\S.*)$/

function matchHeading(text: string): string | null {
  const lines = text
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.length > 0)
  if (lines.length !== 1) return null
  const m = HEADING_LINE.exec(lines[0])
  return m ? m[2].trim() : null
}

/**
 * Classify a committed block's KIND from its own text. Order matters: table
 * and blockquote structure are checked before the looser phrase/line checks,
 * so a table row that happens to contain the word "silent" is still a table.
 */
export function classifyBlockKind(text: string): BlockClassification {
  const table = parseMarkdownTable(text)
  if (table) return { kind: 'table', table }

  if (isBlockquote(text)) {
    const content = stripBlockquote(text)
    if (content.length > 0) return { kind: 'verse', content }
  }

  if (GAP_RIBBON_PATTERN.test(text)) {
    return { kind: 'gap_ribbon', gapText: text.trim() }
  }

  const headingText = matchHeading(text)
  if (headingText !== null) {
    return { kind: 'heading', content: headingText }
  }

  // DD-22, approach (c): a table embedded in an otherwise-prose block does
  // not reclassify the block — it stays 'paragraph', with the embedded
  // table(s) carried as metadata for the renderer to draw inline.
  const tableSpans = detectTableSpans(text)
  if (tableSpans.length > 0) return { kind: 'paragraph', tableSpans }

  return { kind: 'paragraph' }
}

// ---------------------------------------------------------------------------
// Role detector (paragraph blocks only)
// ---------------------------------------------------------------------------

/** Lexical caveat lead-ins — checked BEFORE the structural (first-in-pass)
 *  signal, since a sentence that explicitly hedges is a caveat regardless of
 *  its position. */
const CAVEAT_LEAD_IN =
  /^(however|but\b|that said|it(?:'|’)s worth noting|note that|a caveat|outside (?:that|this)|on the other hand)\b/i

/**
 * Classify a paragraph block's READING ROLE. Structural signal (is this the
 * first prose block committed in its pass?) combined with a lexical caveat
 * check the structural signal cannot express — a caveat can arrive as the
 * FIRST prose of a pass (e.g. a single-paragraph turn that opens with a
 * hedge) and must still read as `caveat`, not `verdict`.
 */
export function classifyRole(text: string, opts: { isFirstProseInPass: boolean }): WireReadingRole {
  if (CAVEAT_LEAD_IN.test(text.trim())) return 'caveat'
  return opts.isFirstProseInPass ? 'verdict' : 'elaboration'
}

// ---------------------------------------------------------------------------
// Combined entry point
// ---------------------------------------------------------------------------

/**
 * Full commit-time classification: kind first, then (only for `paragraph`
 * blocks) a reading role. Non-paragraph kinds never carry a role — `verse`,
 * `table`, `gap_ribbon` and `heading` blocks are not rendered through
 * `ParagraphBlock`, the only consumer of `role`.
 */
export function classifyCommittedBlock(
  text: string,
  opts: { isFirstProseInPass: boolean },
): BlockClassification {
  const base = classifyBlockKind(text)
  if (base.kind !== 'paragraph') return base
  return { ...base, role: classifyRole(text, opts) }
}
