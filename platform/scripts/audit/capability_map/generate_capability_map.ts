/**
 * generate_capability_map.ts — WP-1.6 (P-12) capability-MAP generator.
 *
 * Transforms the ratified Concept×Retrievability matrix (Lane-1b seed,
 * 3,058 rows / ~2,589 unique concept families, per-channel) into a
 * machine-readable capability MAP keyed by concept family → serving route(s),
 * REGENERATED against POST-W1 reachability.
 *
 * WHY REGENERATE (not copy the seed): WP-1.2/1.3/1.3j/1.4/1.5/1.8 changed what is
 * actually served — new tools (WP-1.3a's 13 computed-but-unserved assets, WP-1.3j's
 * 5 bodha surfaces, dasha systems, chart_facts filters, msr_sql projection,
 * synthesis compose_large_n), fixed serving bugs, honest envelopes. The seed's
 * channel_retag is the PRE-W1 snapshot. This generator recomputes reachability
 * from the LIVE, integrated retrieval registry (the same catalog both the MCP
 * and chat channels import) so the map reflects what resolves NOW, and reports
 * the delta the W1 fixes produced.
 *
 * METHOD (deterministic + re-runnable):
 *   1. Load the live registry catalog → authoritative set of registered
 *      capability URIs + metadata (the ground truth for "reachable NOW").
 *   2. Statically scan the registry source files → per file, the URIs it
 *      registers and the DB tables it queries (FROM/JOIN). Associate URI↔table
 *      via source-file co-location. Keep only URIs that are LIVE in (1).
 *   3. Cross-reference the MCP capability bridge → which live URIs are exposed
 *      on the deployed MCP channel (deployed-mcp) vs surgical-registry only.
 *   4. For each matrix row (family × table): resolve post-W1 route(s) from the
 *      table→URI index; classify the post-W1 channel; diff vs the seed retag.
 *   5. Emit CONCEPT_CAPABILITY_MAP.json (per-family entries) + a summary with
 *      the reachability delta.
 *
 * The URI↔table association is table-granular (a tool that reads table T is a
 * candidate route for every concept stored in T); the SAMPLE verification
 * (verify_capability_map.integration.test.ts) empirically confirms specific
 * concept→route→arrival against the live DB, which resolves column-projection
 * questions the static association cannot.
 *
 * Run:
 *   cd platform && npx tsx --conditions=react-server \
 *     scripts/audit/capability_map/generate_capability_map.ts
 * (no DB required for generation — pure static + in-process registry load).
 */

import { readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { getAllCapabilities } from '@/lib/retrieval/registry'
import '@/lib/retrieval/registry/catalog' // side-effect: register every capability
import { getRegistryCapabilitiesForMcp } from '@/lib/retrieval/registry/mcp_capability_bridge'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = join(__dirname, '..', '..', '..', '..')
const PLATFORM_ROOT = join(REPO_ROOT, 'platform')
const MATRIX_PATH = join(
  REPO_ROOT,
  '00_ARCHITECTURE/llm_consumption_audit/state/CONCEPT_RETRIEVABILITY_MATRIX.jsonl'
)
const OUT_DIR = join(REPO_ROOT, '00_ARCHITECTURE/llm_consumption_audit/capability_map')
const OUT_MAP = join(OUT_DIR, 'CONCEPT_CAPABILITY_MAP.json')
const OUT_SUMMARY = join(OUT_DIR, 'CAPABILITY_MAP_SUMMARY.json')
const REGISTRY_LAYERS_DIR = join(PLATFORM_ROOT, 'src/lib/retrieval/registry/layers')

const MAP_VERSION = '1.0.0'

// ── seed matrix ────────────────────────────────────────────────────────────────

interface MatrixRow {
  family_key: string
  channel: string
  retrievability: string
  fidelity: string
  table_name: string
  channel_retag: string
}

function loadMatrix(): MatrixRow[] {
  const raw = readFileSync(MATRIX_PATH, 'utf8')
  return raw
    .split('\n')
    .filter((l) => l.trim().length > 0)
    .map((l) => JSON.parse(l) as MatrixRow)
}

// ── static scan: registry source → (uris, tables) per file ──────────────────────

/** SQL identifiers that are CTEs / aliases, not real tables — excluded. */
const NON_TABLE_TOKENS = new Set([
  'l', 'r', 't', 'c', 's', 'p', 'd', 'e', 'f', 'g', 'x', 'a', 'b',
  'select', 'lateral', 'unnest', 'json_array_elements', 'jsonb_array_elements',
  'generate_series', 'values',
])

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

const URI_RE = /uri:\s*'(marsys:\/\/[^']+)'/g
const TABLE_RE = /\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)/gi

/** One registered capability with the tables ITS descriptor block queries. */
interface UriScan {
  file: string
  uri: string
  tables: string[]
}

function tablesIn(segment: string): string[] {
  const out = new Set<string>()
  for (const m of segment.matchAll(TABLE_RE)) {
    const tbl = m[1]!.toLowerCase()
    if (!NON_TABLE_TOKENS.has(tbl)) out.add(tbl)
  }
  return [...out]
}

/**
 * Scan registry sources, associating each capability URI with ONLY the tables
 * its own descriptor block queries. Descriptors are laid out as
 * `uri: '...'` at the top, handler/SQL below, then the next `uri:`. We segment
 * the file at each `uri:` position so a multi-capability file (e.g. the 7-URI
 * L4 phala calibration file) attributes phala_muhurta to query_auspicious_windows,
 * phala_mitigation to query_remedy_program, etc. — not the file-level cross product.
 * Single-URI files use the whole file (shared consts may precede the uri).
 */
function scanRegistrySources(): UriScan[] {
  const files = walkTs(REGISTRY_LAYERS_DIR)
  const scans: UriScan[] = []
  for (const file of files) {
    const src = readFileSync(file, 'utf8')
    const rel = file.replace(PLATFORM_ROOT + '/', '')
    const matches = [...src.matchAll(URI_RE)]
    if (matches.length === 0) continue
    if (matches.length === 1) {
      scans.push({ file: rel, uri: matches[0]![1]!, tables: tablesIn(src) })
      continue
    }
    for (let i = 0; i < matches.length; i++) {
      const start = i === 0 ? 0 : matches[i]!.index! // first block absorbs pre-uri helpers
      const end = i + 1 < matches.length ? matches[i + 1]!.index! : src.length
      scans.push({ file: rel, uri: matches[i]![1]!, tables: tablesIn(src.slice(start, end)) })
    }
  }
  return scans
}

// ── build table → live-route index ──────────────────────────────────────────────

interface Route {
  uri: string
  name: string
  layer: string
  scope: string
  /** true iff exposed on the deployed MCP channel per the capability bridge. */
  deployed_mcp: boolean
  source_file: string
}

interface BuildResult {
  tableIndex: Map<string, Route[]>
  liveUriMeta: Map<string, { name: string; layer: string; scope: string }>
  deployedUris: Set<string>
}

function buildTableIndex(scans: UriScan[]): BuildResult {
  const liveCaps = getAllCapabilities()
  const liveUriMeta = new Map<string, { name: string; layer: string; scope: string }>()
  for (const c of liveCaps) {
    liveUriMeta.set(c.uri, { name: c.name, layer: c.layer, scope: c.scope })
  }
  const deployedUris = new Set<string>(Object.values(getRegistryCapabilitiesForMcp()))

  const tableIndex = new Map<string, Route[]>()
  const seen = new Set<string>() // dedupe (table|uri)
  for (const scan of scans) {
    const meta = liveUriMeta.get(scan.uri)
    if (!meta) continue // URI in source but NOT live in the registry → not reachable
    for (const table of scan.tables) {
      const key = `${table}|${scan.uri}`
      if (seen.has(key)) continue
      seen.add(key)
      const route: Route = {
        uri: scan.uri,
        name: meta.name,
        layer: meta.layer,
        scope: meta.scope,
        deployed_mcp: deployedUris.has(scan.uri),
        source_file: scan.file,
      }
      const arr = tableIndex.get(table) ?? []
      arr.push(route)
      tableIndex.set(table, arr)
    }
  }
  return { tableIndex, liveUriMeta, deployedUris }
}

// ── channel classification ────────────────────────────────────────────────────

type PostChannel =
  | 'reachable-deployed-mcp'
  | 'reachable-surgical'
  | 'served-only-by-down-pipeline'
  | 'truly-unreachable'

function classifyPost(routes: Route[], seedRetag: string): PostChannel {
  if (routes.length > 0) {
    return routes.some((r) => r.deployed_mcp) ? 'reachable-deployed-mcp' : 'reachable-surgical'
  }
  // No live route resolves this table. Preserve the seed's honest classification
  // (either truly-unreachable or served-only-by-down-pipeline) rather than
  // inventing reachability.
  if (seedRetag === 'truly-unreachable') return 'truly-unreachable'
  if (seedRetag === 'served-only-by-down-pipeline') return 'served-only-by-down-pipeline'
  // Seed said reachable but no route found now → down-pipeline (regression-safe,
  // honest: the concept exists in a served table but our static scan found no
  // direct primitive; flagged for the sample check / W4).
  return 'served-only-by-down-pipeline'
}

const CHANNEL_RANK: Record<PostChannel, number> = {
  'reachable-deployed-mcp': 3,
  'reachable-surgical': 2,
  'served-only-by-down-pipeline': 1,
  'truly-unreachable': 0,
}

// ── main ────────────────────────────────────────────────────────────────────────

interface ConceptRoute {
  table: string
  seed_channel: string
  post_w1_channel: PostChannel
  routes: Array<{ uri: string; tool: string; layer: string; scope: string; deployed_mcp: boolean }>
}

interface FamilyEntry {
  family_key: string
  reachable_post_w1: boolean
  best_channel: PostChannel
  reachable_pre_w1: boolean
  seed_best_channel: string
  moved: boolean
  concepts: ConceptRoute[]
}

const REACHABLE_CHANNELS = new Set(['reachable-deployed-mcp', 'reachable-surgical'])

function main(): void {
  const matrix = loadMatrix()
  const scans = scanRegistrySources()
  const { tableIndex, liveUriMeta, deployedUris } = buildTableIndex(scans)

  // group matrix rows by family
  const byFamily = new Map<string, MatrixRow[]>()
  for (const row of matrix) {
    const arr = byFamily.get(row.family_key) ?? []
    arr.push(row)
    byFamily.set(row.family_key, arr)
  }

  const families: FamilyEntry[] = []
  for (const [family_key, rows] of byFamily) {
    const concepts: ConceptRoute[] = []
    let bestPost: PostChannel = 'truly-unreachable'
    let bestSeedRank = 0
    for (const row of rows) {
      const routes = tableIndex.get(row.table_name) ?? []
      const post = classifyPost(routes, row.channel_retag)
      if (CHANNEL_RANK[post] > CHANNEL_RANK[bestPost]) bestPost = post
      const seedRank = seedRank2num(row.channel_retag)
      if (seedRank > bestSeedRank) bestSeedRank = seedRank
      concepts.push({
        table: row.table_name,
        seed_channel: row.channel_retag,
        post_w1_channel: post,
        routes: routes.map((r) => ({
          uri: r.uri,
          tool: r.name,
          layer: r.layer,
          scope: r.scope,
          deployed_mcp: r.deployed_mcp,
        })),
      })
    }
    const reachable_post_w1 = REACHABLE_CHANNELS.has(bestPost)
    const reachable_pre_w1 = bestSeedRank >= 2 // deployed-mcp or surgical
    families.push({
      family_key,
      reachable_post_w1,
      best_channel: bestPost,
      reachable_pre_w1,
      seed_best_channel: num2seed(bestSeedRank),
      moved: reachable_post_w1 && !reachable_pre_w1,
      concepts,
    })
  }

  families.sort((a, b) => a.family_key.localeCompare(b.family_key))

  // ── summary / delta ────────────────────────────────────────────────────────
  const totalFamilies = families.length
  const reachablePost = families.filter((f) => f.reachable_post_w1).length
  const reachablePre = families.filter((f) => f.reachable_pre_w1).length
  const moved = families.filter((f) => f.moved).length

  // per-row (family×table) tallies to mirror the seed's per-channel row counts
  const seedRowCounts: Record<string, number> = {}
  const postRowCounts: Record<string, number> = {}
  for (const row of matrix) {
    seedRowCounts[row.channel_retag] = (seedRowCounts[row.channel_retag] ?? 0) + 1
  }
  for (const f of families) {
    for (const c of f.concepts) {
      postRowCounts[c.post_w1_channel] = (postRowCounts[c.post_w1_channel] ?? 0) + 1
    }
  }

  const summary = {
    map_version: MAP_VERSION,
    generated_at: new Date().toISOString(),
    seed_matrix: MATRIX_PATH.replace(REPO_ROOT + '/', ''),
    method: 'live-registry + source-file table-scan; table-granular routes; sample verified against live DB',
    families: {
      total: totalFamilies,
      reachable_post_w1: reachablePost,
      reachable_pre_w1: reachablePre,
      newly_reachable_delta: moved,
      unreachable_post_w1: totalFamilies - reachablePost,
    },
    rows_per_channel_seed: seedRowCounts,
    rows_per_channel_post_w1: postRowCounts,
    live_registry: {
      total_capabilities: liveUriMeta.size,
      deployed_mcp_uris: deployedUris.size,
    },
    tables_with_routes: [...tableIndex.keys()].length,
    note:
      'newly_reachable_delta = families reachable via a live primitive route NOW ' +
      'that were served-only-by-down-pipeline or truly-unreachable in the pre-W1 seed. ' +
      'Routes are table-granular candidates; per-concept arrival is proven by the sample ' +
      'integration test against the live DB.',
  }

  writeFileSync(OUT_MAP, JSON.stringify({ map_version: MAP_VERSION, generated_at: summary.generated_at, families }, null, 2))
  writeFileSync(OUT_SUMMARY, JSON.stringify(summary, null, 2))

  // console report
  console.log('=== WP-1.6 capability map regenerated (POST-W1) ===')
  console.log(`families total:            ${totalFamilies}`)
  console.log(`reachable pre-W1 (seed):   ${reachablePre}`)
  console.log(`reachable post-W1:         ${reachablePost}`)
  console.log(`NEWLY reachable (delta):   ${moved}`)
  console.log(`unreachable post-W1:       ${totalFamilies - reachablePost}`)
  console.log('rows/channel seed:', seedRowCounts)
  console.log('rows/channel post:', postRowCounts)
  console.log(`live capabilities: ${liveUriMeta.size}  deployed-mcp uris: ${deployedUris.size}`)
  console.log(`wrote: ${OUT_MAP.replace(REPO_ROOT + '/', '')}`)
  console.log(`wrote: ${OUT_SUMMARY.replace(REPO_ROOT + '/', '')}`)
}

function seedRank2num(retag: string): number {
  switch (retag) {
    case 'reachable-deployed-mcp':
      return 3
    case 'reachable-surgical':
      return 2
    case 'served-only-by-down-pipeline':
      return 1
    default:
      return 0
  }
}
function num2seed(n: number): string {
  return ['truly-unreachable', 'served-only-by-down-pipeline', 'reachable-surgical', 'reachable-deployed-mcp'][n] ?? 'truly-unreachable'
}

main()
