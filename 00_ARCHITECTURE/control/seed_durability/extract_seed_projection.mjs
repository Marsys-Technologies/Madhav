/**
 * M0-T29 · seed-value extractor (READ-ONLY, no DB, no seed code path executed).
 *
 * Reads platform/scripts/seed/asset_registry_seed.ts AS TEXT (D-13: the module is
 * never imported — its main() runs INSERT … ON CONFLICT DO UPDATE against
 * asset_registry, and D-17 records that it also refuses dry-run requests).
 *
 * What it DOES do, and why that is not "running the seed":
 *   1. slices out the `export const ASSETS: AssetDef[] = [ … ]` array LITERAL only;
 *   2. statically proves that slice is INERT — after stripping comments and string /
 *      template literals, what remains contains no call expression, no identifier
 *      other than an object property key or a JS keyword literal, and no template
 *      substitution (`${`). The check's result is emitted in the output and the
 *      script refuses to evaluate if it fails;
 *   3. evaluates that proven-inert literal in a fresh process with no DB client and
 *      no module imports beyond node:fs;
 *   4. re-implements, in this file, the value-derivation main() performs between the
 *      ASSETS array and the bound parameters ($1..$25) — the `?? 'data'` defaults,
 *      the layerNames/layerIndices maps, the catalog_status default, the
 *      evalFileCount() mutation of mi_jivanaghatana.expected_volume_inputs.
 *
 * The one thing it CANNOT do here is main()'s pre-flight `to_regclass(target_table)`
 * mutation of is_active — that needs the DB. It is emitted as `is_active_seed_declared`
 * plus `target_table`, and the Python side resolves it read-only.
 *
 * Output: JSON on stdout. Nothing is written to any database by this file.
 */
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const REPO = resolve(HERE, '../../..')
const SEED = resolve(REPO, 'platform/scripts/seed/asset_registry_seed.ts')

const txt = readFileSync(SEED, 'utf8')

// ── 1. slice the array literal ──────────────────────────────────────────────
const startTok = 'export const ASSETS: AssetDef[] = ['
const startIdx = txt.indexOf(startTok)
if (startIdx < 0) throw new Error('ASSETS declaration not found')
const openIdx = startIdx + startTok.length - 1 // at '['

// bracket-match, skipping string/template/comment regions
function scanInert(src) {
  // returns { end, stripped } where stripped has all comments + literal bodies blanked
  let i = 0, depth = 0, end = -1
  const out = []
  while (i < src.length) {
    const ch = src[i], nx = src[i + 1]
    if (ch === '/' && nx === '/') { const j = src.indexOf('\n', i); const k = j < 0 ? src.length : j; out.push(' '.repeat(k - i)); i = k; continue }
    if (ch === '/' && nx === '*') { const j = src.indexOf('*/', i + 2); const k = j < 0 ? src.length : j + 2; out.push(' '.repeat(k - i)); i = k; continue }
    if (ch === "'" || ch === '"' || ch === '`') {
      const q = ch; let j = i + 1
      while (j < src.length) {
        if (src[j] === '\\') { j += 2; continue }
        if (src[j] === q) break
        j++
      }
      out.push('"' + ' '.repeat(Math.max(0, j - i - 1)) + '"')
      i = j + 1; continue
    }
    if (ch === '[' || ch === '{') depth++
    if (ch === ']' || ch === '}') { depth--; if (depth === 0 && ch === ']') { out.push(ch); end = i; break } }
    out.push(ch); i++
  }
  return { end, stripped: out.join('') }
}
const { end, stripped } = scanInert(txt.slice(openIdx))
if (end < 0) throw new Error('could not bracket-match the ASSETS array')
const literal = txt.slice(openIdx, openIdx + end + 1)

// ── 2. inertness proof ──────────────────────────────────────────────────────
const inert = { checks: {}, ok: false }
inert.checks.no_template_substitution = !literal.includes('${')
// strip the blanked-out string bodies' quote pairs, then look for call syntax
const skeleton = stripped.replace(/"\s*"/g, '""')
inert.checks.no_call_expression = !/[A-Za-z_$][A-Za-z0-9_$]*\s*\(/.test(skeleton)
// every identifier in the skeleton must be a property key (followed by ':') or a keyword literal
const KEYWORDS = new Set(['true', 'false', 'null', 'undefined'])
const badIdents = new Set()
for (const m of skeleton.matchAll(/[A-Za-z_$][A-Za-z0-9_$]*/g)) {
  const name = m[0]
  if (KEYWORDS.has(name)) continue
  const after = skeleton.slice(m.index + name.length).match(/^\s*/)[0].length
  if (skeleton[m.index + name.length + after] === ':') continue // property key
  badIdents.add(name)
}
inert.checks.no_free_identifiers = badIdents.size === 0
inert.checks.free_identifiers_found = [...badIdents]
inert.ok = inert.checks.no_template_substitution && inert.checks.no_call_expression && inert.checks.no_free_identifiers
if (!inert.ok) {
  process.stdout.write(JSON.stringify({ ok: false, inertness: inert }, null, 2))
  process.exit(3)
}

// ── 3. evaluate the proven-inert literal ────────────────────────────────────
// eslint-disable-next-line no-new-func
const ASSETS = new Function('return ' + literal)()

// ── 4. re-implement main()'s derivations (asset_registry_seed.ts:3255-3268,
//      :3200-3205) ─────────────────────────────────────────────────────────
const layerNames = { brahmagyan: 'Brahmagyan', ganita: 'Gaṇita', bodha: 'Bodha', kala: 'Kāla', phala: 'Phala', mimamsa: 'Mīmāṃsā' }
const layerIndices = { brahmagyan: 'L0', ganita: 'L1', bodha: 'L2', kala: 'L3', phala: 'L4', mimamsa: 'L5' }

// evalFileCount(:145) — replicated verbatim
function evalFileCount(path, marker) {
  const content = readFileSync(resolve(REPO, path), 'utf8')
  const re = new RegExp(`${marker}\\.[0-9]{4}\\.[0-9X]{2}\\.[0-9X]{2}\\.[0-9]+`, 'g')
  return new Set(content.match(re) ?? []).size
}
let lelCount = null, lelErr = null
try { lelCount = evalFileCount('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md', 'EVT') } catch (e) { lelErr = String(e.message) }

const rows = {}
for (const a of ASSETS) {
  const r = {
    layer: a.layer,
    sort_order: a.sort_order,
    sanskrit_name: a.sanskrit_name,
    english_name: a.english_name,
    english_description: a.english_description,
    storage_type: a.storage_type,
    target_table: a.target_table ?? null,
    count_sql: a.count_sql ?? null,
    size_sql: a.size_sql ?? null,
    target_floor: a.target_floor ?? null,
    expected_volume_formula: a.expected_volume_formula ?? null,
    expected_volume_inputs: a.expected_volume_inputs ?? null,
    volume_explanation: a.volume_explanation ?? null,
    depends_on: a.depends_on ?? null,
    scope: a.scope,
    asset_type: a.asset_type ?? 'data',
    layer_name: a.layer_name ?? layerNames[a.layer] ?? a.layer,
    layer_index: a.layer_index ?? layerIndices[a.layer] ?? null,
    provides_apis: a.provides_apis ?? null,
    health_probe: a.health_probe ?? null,
    catalog_status: a.catalog_status ?? (a.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT'),
    asset_kind: a.asset_kind ?? 'data',
    // INSERT-only, never in DO UPDATE SET:
    estimated_seconds: a.estimated_seconds ?? null,
    // is_active is pre-flight-mutated (:3228) and CASE-guarded (:3308); resolved downstream
    is_active_seed_declared: a.is_active,
  }
  // which of these came from an explicit key vs a derived default
  r.__declared = {}
  for (const k of ['asset_type', 'asset_kind', 'layer_name', 'layer_index', 'catalog_status'])
    r.__declared[k] = Object.prototype.hasOwnProperty.call(a, k)
  rows[a.asset_id] = r
}

// main():3205 mutates ONE asset's expected_volume_inputs before the upsert
if (rows['mi_jivanaghatana'] && lelCount !== null) {
  rows['mi_jivanaghatana'].expected_volume_inputs =
    { file_count: lelCount, source_file: '01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md' }
  rows['mi_jivanaghatana'].__lel_file_count_applied = lelCount
} else if (rows['mi_jivanaghatana']) {
  rows['mi_jivanaghatana'].expected_volume_inputs = '__UNKNOWN__'
  rows['mi_jivanaghatana'].__lel_error = lelErr
}

process.stdout.write(JSON.stringify({
  ok: true,
  seed_path: 'platform/scripts/seed/asset_registry_seed.ts',
  seed_bytes: txt.length,
  inertness: inert,
  assets_parsed: Object.keys(rows).length,
  lel_file_count: lelCount,
  lel_error: lelErr,
  rows,
}, null, 2))
