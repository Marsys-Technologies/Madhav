/**
 * e1_registry_extractor.ts — the "declared" side of the W1 Lane L1b harvest pipeline
 * (W-25, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-2, extractor E1).
 *
 * Walks the ACTUAL, LIVE `getCatalog()` capability registry (the same registry both
 * the MCP channel and the chat channel import — no separate hand-maintained list) and
 * extracts every capability's declared concept surface: uri, type, layer, name,
 * description, scope, archetype, plus a best-effort static table hint (which real
 * Postgres table(s) its own descriptor block's SQL touches, via the same FROM/JOIN
 * regex scan `scripts/audit/capability_map/generate_capability_map.ts` (WP-1.6)
 * already uses and has empirically verified — reused here rather than re-invented).
 *
 * `table_hint` is HEURISTIC, not authoritative: a regex over source text, not a real
 * SQL parse. It is good enough to drive the cross-diff's "declared touches table T"
 * signal but should never be read as a guarantee. Capabilities with no FROM/JOIN in
 * their own descriptor block (e.g. capabilities that proxy to the Python sidecar, or
 * pure-computation tools) legitimately have an empty table_hint array — this is
 * reported honestly, not padded.
 *
 * Output: platform/src/generated/harvest/e1_declared.json
 *
 * Run:
 *   cd platform && npx tsx --conditions=react-server scripts/harvest/e1_registry_extractor.ts
 * (no DB required — pure static + in-process registry load, same as WP-1.6.)
 */
import { readFileSync, writeFileSync, readdirSync, statSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { getAllCapabilities } from '@/lib/retrieval/registry'
import '@/lib/retrieval/registry/catalog' // side-effect: registers every capability

const __dirname = dirname(fileURLToPath(import.meta.url))
const PLATFORM_ROOT = join(__dirname, '..', '..')
const REGISTRY_LAYERS_DIR = join(PLATFORM_ROOT, 'src/lib/retrieval/registry/layers')
const SYNTHESIS_DIR = join(PLATFORM_ROOT, 'src/lib/retrieval/synthesis')
const OUTPUT_PATH = join(PLATFORM_ROOT, 'src/generated/harvest/e1_declared.json')

// ── static table-hint scan (same method as WP-1.6 generate_capability_map.ts) ──

const NON_TABLE_TOKENS = new Set([
  'l', 'r', 't', 'c', 's', 'p', 'd', 'e', 'f', 'g', 'x', 'a', 'b',
  'select', 'lateral', 'unnest', 'json_array_elements', 'jsonb_array_elements',
  'generate_series', 'values',
  // English-prose residue caught inside non-SQL backtick template literals (error
  // messages / doc-comment strings that happen to say "from X" or "join Y" without
  // being SQL) — confirmed by manual inspection of every occurrence, not guessed;
  // see e.g. register_d8_assess_domain.ts's `activation_end >= from AND
  // activation_start <= to` error-string literal.
  'and', 'the', 'this', 'to',
])
const URI_RE = /uri:\s*'(marsys:\/\/[^']+)'/g
const TABLE_RE = /\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)/gi
/** Backtick template-literal spans — real SQL lives here; English prose in doc
 * comments/console.log strings does not. Restricting the FROM/JOIN scan to this
 * text eliminates the false-positive class WP-1.6's original scan didn't need to
 * handle (this harvest lane's source files carry heavier prose commentary with
 * "from"/"join" in ordinary sentences, e.g. "resolves data FROM get_yoga_dosha
 * handler" — plain English, not SQL). Confirmed empirically: this repo's registry
 * SQL is written exclusively as backtick template literals passed to query().
 */
const BACKTICK_RE = /`([^`]*)`/g

function tablesIn(segment: string): string[] {
  const out = new Set<string>()
  for (const btMatch of segment.matchAll(BACKTICK_RE)) {
    for (const m of btMatch[1]!.matchAll(TABLE_RE)) {
      const tbl = m[1]!.toLowerCase()
      if (!NON_TABLE_TOKENS.has(tbl)) out.add(tbl)
    }
  }
  return [...out].sort()
}

function walkTs(dir: string): string[] {
  const out: string[] = []
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) {
      if (name === '__tests__') continue
      out.push(...walkTs(full))
    } else if (name.endsWith('.ts') && !name.endsWith('.test.ts')) {
      out.push(full)
    }
  }
  return out
}

interface UriScan {
  file: string
  uri: string
  table_hint: string[]
}

function scanSources(dirs: string[]): UriScan[] {
  const scans: UriScan[] = []
  for (const dir of dirs) {
    const files = walkTs(dir)
    for (const file of files) {
      const src = readFileSync(file, 'utf8')
      const rel = file.replace(PLATFORM_ROOT + '/', '')
      const matches = [...src.matchAll(URI_RE)]
      if (matches.length === 0) continue
      if (matches.length === 1) {
        scans.push({ file: rel, uri: matches[0]![1]!, table_hint: tablesIn(src) })
        continue
      }
      for (let i = 0; i < matches.length; i++) {
        const start = i === 0 ? 0 : matches[i]!.index!
        const end = i + 1 < matches.length ? matches[i + 1]!.index! : src.length
        scans.push({
          file: rel,
          uri: matches[i]![1]!,
          table_hint: tablesIn(src.slice(start, end)),
        })
      }
    }
  }
  return scans
}

// ── main ─────────────────────────────────────────────────────────────────────

interface DeclaredConcept {
  uri: string
  type: string
  layer: string
  name: string
  scope: string
  archetype: string
  traversal_level: string
  tool_role: string
  description_len: number
  description_preview: string
  table_hint: string[]
  source_file: string | null
}

function main(): void {
  const caps = getAllCapabilities()
  console.log(`[E1] getCatalog() returned ${caps.length} live capabilities`)

  const scans = scanSources([REGISTRY_LAYERS_DIR, SYNTHESIS_DIR])
  const scanByUri = new Map<string, UriScan>()
  for (const s of scans) {
    // Last write wins is fine here — a URI legitimately appears once per file in
    // practice; if it appears in two scanned dirs, prefer the last (synthesis wins
    // over layers in our dirs array order below is irrelevant since we pass layers
    // first then synthesis, and a URI shouldn't be declared in both).
    scanByUri.set(s.uri, s)
  }

  const declared: DeclaredConcept[] = caps
    .map((c) => {
      const scan = scanByUri.get(c.uri)
      return {
        uri: c.uri,
        type: c.type,
        layer: c.layer,
        name: c.name,
        scope: c.scope,
        archetype: c.archetype,
        traversal_level: c.traversal_level,
        tool_role: c.tool_role,
        description_len: c.description.length,
        description_preview: c.description.slice(0, 160),
        table_hint: scan?.table_hint ?? [],
        source_file: scan?.file ?? null,
      }
    })
    .sort((a, b) => a.uri.localeCompare(b.uri))

  const byLayer: Record<string, number> = {}
  for (const d of declared) byLayer[d.layer] = (byLayer[d.layer] ?? 0) + 1

  const noTableHintCount = declared.filter((d) => d.table_hint.length === 0).length
  const distinctTablesHinted = new Set(declared.flatMap((d) => d.table_hint))

  const out = {
    extractor: 'E1 — registry-declared',
    generated_at: new Date().toISOString(),
    method:
      'getCatalog() live in-process load (registers every capability via the real ' +
      'import chain used by both MCP and chat channels) + best-effort static ' +
      'FROM/JOIN regex table_hint scan over registry/layers + synthesis source, ' +
      'same method as WP-1.6 generate_capability_map.ts.',
    summary: {
      total_declared_capabilities: declared.length,
      by_layer: byLayer,
      capabilities_with_no_table_hint: noTableHintCount,
      distinct_tables_hinted: distinctTablesHinted.size,
    },
    concepts: declared,
  }

  mkdirSync(dirname(OUTPUT_PATH), { recursive: true })
  writeFileSync(OUTPUT_PATH, JSON.stringify(out, null, 2) + '\n')
  console.log(`[E1] wrote ${declared.length} declared concepts -> ${OUTPUT_PATH}`)
  console.log(`[E1] by_layer:`, byLayer)
  console.log(
    `[E1] ${noTableHintCount}/${declared.length} capabilities have no static table_hint ` +
      `(sidecar-proxied / pure-computation / cross-file helper SQL not caught by the regex)`,
  )
}

main()
