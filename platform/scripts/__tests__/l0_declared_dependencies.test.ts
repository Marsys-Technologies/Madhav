import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'

/**
 * W-L0-2 (L0 Brahmagyan elevation, strategy v2.1 §4.2 + §1.4 + §7.1) —
 * declared dependencies and declared use.
 *
 * The packet's closing condition: every code read of a bg_* (L0) table is
 * either (a) a registered depends_on edge on the consuming asset, or (b) a
 * documented serve-time read with a declared use type. The measured census
 * lives in the machine-readable register
 * platform/python-sidecar/brahmagyan/l0_declared_use_register_v1.json; this
 * test is the standing detector over it.
 *
 * Three independent checks:
 *
 *  (a) EDGE CHECK — every writer-side census entry has the producer asset in
 *      the consumer's seed depends_on. depends_on is migration-governed (the
 *      seed upsert's ON CONFLICT preserves live), so the seed literal is the
 *      code-side declaration; held migration 1122 syncs live.
 *
 *  (b) REGISTER INTEGRITY — every serve-time read declares a non-empty
 *      use_types subset of the §7.1 vocabulary, and every file the register
 *      names actually exists. A register that points at ghosts is not a
 *      census.
 *
 *  (c) STALENESS CROSS-CHECK — re-run the §1.1 reader grep over the scoped
 *      trees and require every (file, table) hit to be covered by the
 *      register for THAT table — as a writer-side edge, an excluded read
 *      with a stated reason, producer-internal machinery, a producer file,
 *      a serve-time read, or a write-only access note. A new reader added
 *      to the code without a declaration fails here. This is the detector
 *      the strategy's "grep re-run yields no undeclared writer-side reads"
 *      asks for, generalised so the register itself cannot silently rot.
 */

const REPO_ROOT = path.resolve(__dirname, '../../..')
const REGISTER_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/brahmagyan/l0_declared_use_register_v1.json'
)

interface WriterRead {
  consumer_asset: string
  table: string
  producer_asset: string
  evidence_files: string[]
  edge: 'pre_existing' | 'declared_this_packet'
}
interface ExcludedRead { consumer_asset: string | null; table: string; files: string[]; reason: string }
interface ProducerInternal { table: string; producer_asset: string; files: string[] }
interface ServeRead { table: string; producer_asset: string; file: string; access: string; use_types: string[] }
interface TableNote { table: string; producer_asset: string }
interface WriteOnly { table: string; file: string }
interface MentionOnly { table: string; file: string; note: string }
interface Register {
  use_type_vocabulary: string[]
  writer_side_reads: WriterRead[]
  excluded_reads: ExcludedRead[]
  producer_internal: ProducerInternal[]
  serve_time_reads: ServeRead[]
  tables_without_readers: TableNote[]
  writer_only_tables: TableNote[]
  write_only_access: WriteOnly[]
  mention_only: MentionOnly[]
  producer_files: Record<string, string[]>
}

const register = JSON.parse(readFileSync(REGISTER_PATH, 'utf8')) as Register

// ── coverage map: table → set of repo-relative files accounted for ──────────

const coverage = new Map<string, Set<string>>()
function cover(table: string, file: string) {
  if (!coverage.has(table)) coverage.set(table, new Set())
  coverage.get(table)!.add(file)
}

/** table → producer assets (a shared physical table can have several, e.g.
 *  brahma_class_priors is written by bg_class_priors AND bg_class_lifetime_counts). */
const producerOf = new Map<string, Set<string>>()
function noteProducer(table: string, producer: string) {
  if (!producerOf.has(table)) producerOf.set(table, new Set())
  producerOf.get(table)!.add(producer)
}

for (const r of register.writer_side_reads) {
  noteProducer(r.table, r.producer_asset)
  for (const f of r.evidence_files) cover(r.table, f)
}
for (const r of register.excluded_reads) {
  for (const f of r.files) cover(r.table, f)
}
for (const r of register.producer_internal) {
  noteProducer(r.table, r.producer_asset)
  for (const f of r.files) cover(r.table, f)
}
for (const r of register.serve_time_reads) {
  noteProducer(r.table, r.producer_asset)
  cover(r.table, r.file)
}
for (const r of register.tables_without_readers) noteProducer(r.table, r.producer_asset)
for (const r of register.writer_only_tables) noteProducer(r.table, r.producer_asset)
for (const r of register.write_only_access) cover(r.table, r.file)
for (const r of register.mention_only) cover(r.table, r.file)

for (const [table, producers] of producerOf) {
  for (const producer of producers) {
    for (const f of register.producer_files[producer] ?? []) cover(table, f)
  }
}

const L0_TABLES = [...coverage.keys()].sort()

// ── scoped reader-grep (strategy §1.1 scope) ────────────────────────────────

function* walk(dir: string, exts: string[]): Generator<string> {
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) {
      if (['node_modules', '__pycache__', '.venv', 'tests', '__tests__', 'generated', 'scripts', 'migrations'].includes(entry)) continue
      yield* walk(full, exts)
    } else if (exts.some(e => entry.endsWith(e)) && !entry.endsWith('.test.ts') && !entry.endsWith('.spec.ts') && !entry.startsWith('test_')) {
      yield full
    }
  }
}

const SCOPES: Array<{ dir: string; exts: string[] }> = [
  { dir: path.join(REPO_ROOT, 'platform/python-sidecar'), exts: ['.py'] },
  { dir: path.join(REPO_ROOT, 'platform/src'), exts: ['.ts'] },
  { dir: path.join(REPO_ROOT, 'platform-mcp/src'), exts: ['.ts'] },
]

interface Hit { file: string; table: string }
function readerGrep(): Hit[] {
  const hits: Hit[] = []
  const res = L0_TABLES.map(t => ({
    table: t,
    re: new RegExp(`\\b(?:FROM|JOIN|INTO|UPDATE)\\s+${t}\\b`, 'i'),
  }))
  for (const scope of SCOPES) {
    for (const abs of walk(scope.dir, scope.exts)) {
      const rel = path.relative(REPO_ROOT, abs)
      const src = readFileSync(abs, 'utf8')
      for (const { table, re } of res) {
        if (re.test(src)) hits.push({ file: rel, table })
      }
    }
  }
  return hits
}

// ─────────────────────────────────────────────────────────────────────────────

describe('L0 declared dependencies and use (W-L0-2)', () => {
  describe('(a) every writer-side read is a registered depends_on edge', () => {
    const byConsumer = new Map<string, string[]>()
    for (const a of ASSETS) byConsumer.set(a.asset_id, a.depends_on ?? [])

    it('consumer assets in the census exist in the seed', () => {
      const missing = register.writer_side_reads
        .map(r => r.consumer_asset)
        .filter(id => !byConsumer.has(id))
      expect([...new Set(missing)]).toEqual([])
    })

    it('producer asset is present in the consumer\'s seed depends_on', () => {
      const undeclared = register.writer_side_reads
        .filter(r => !(byConsumer.get(r.consumer_asset) ?? []).includes(r.producer_asset))
        .map(r => `${r.consumer_asset} -/-> ${r.producer_asset} (${r.table}, ${r.edge})`)
      expect(undeclared).toEqual([])
    })

    it('every edge marker is one of the two declared values', () => {
      const bad = register.writer_side_reads.filter(
        r => r.edge !== 'pre_existing' && r.edge !== 'declared_this_packet',
      )
      expect(bad.map(r => `${r.consumer_asset}/${r.table}`)).toEqual([])
    })
  })

  describe('(b) register integrity', () => {
    it('every serve-time read declares a non-empty use_types subset of the vocabulary', () => {
      const vocab = new Set(register.use_type_vocabulary)
      const bad = register.serve_time_reads.filter(
        r => r.use_types.length === 0 || r.use_types.some(u => !vocab.has(u)),
      )
      expect(bad.map(r => `${r.file} → ${r.table}`)).toEqual([])
    })

    it('every file named anywhere in the register exists', () => {
      const files = new Set<string>()
      for (const r of register.writer_side_reads) r.evidence_files.forEach(f => files.add(f))
      for (const r of register.excluded_reads) r.files.forEach(f => files.add(f))
      for (const r of register.producer_internal) r.files.forEach(f => files.add(f))
      for (const r of register.serve_time_reads) files.add(r.file)
      for (const r of register.write_only_access) files.add(r.file)
      for (const list of Object.values(register.producer_files)) list.forEach(f => files.add(f))
      const missing = [...files].filter(f => !existsSync(path.join(REPO_ROOT, f)))
      expect(missing).toEqual([])
    })

    it('every serve-time access class is declared', () => {
      const bad = register.serve_time_reads.filter(
        r => !['direct', 'indirect', 'transport'].includes(r.access),
      )
      expect(bad.map(r => `${r.file} → ${r.table}`)).toEqual([])
    })
  })

  describe('(c) staleness cross-check — the §1.1 reader grep re-run', () => {
    it('covers every L0 table the register knows about', () => {
      // Guard against a register edit dropping a table silently: the 41
      // physical relations of the census (incl. the retired legacy plural)
      // must all be present.
      expect(L0_TABLES.length).toBeGreaterThanOrEqual(40)
    })

    it('every (file, table) grep hit is covered by the register for that table', () => {
      const uncovered = readerGrep()
        .filter(h => !coverage.get(h.table)?.has(h.file))
        .map(h => `${h.file} reads ${h.table}`)
      expect(uncovered).toEqual([])
    })
  })
})
