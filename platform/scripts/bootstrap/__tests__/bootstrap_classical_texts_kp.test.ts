import { execFileSync, spawnSync } from 'node:child_process'
import { randomUUID } from 'node:crypto'
import { Pool, type PoolClient } from 'pg'
import { describe, expect, it } from 'vitest'
import { ingestKPChunks, KP_CHUNK_INSERT_SQL, type KPChunk, type KPQueryClient } from '../bootstrap_classical_texts_kp'

const script = 'scripts/bootstrap/bootstrap_classical_texts_kp.ts'

class DisposableServedCorpus implements KPQueryClient {
  readonly queries: string[] = []
  private readonly rows = new Map<string, KPChunk>()

  async query(text: string, values: readonly unknown[] = []) {
    this.queries.push(text)
    if (text.includes("SELECT 1 FROM classical_texts WHERE text_id = 'kp_reader'")) {
      return { rowCount: 1, rows: [] }
    }
    if (text.includes('INSERT INTO classical_text_chunks')) {
      const [chunkId, verseRef, chapter, content, sourceCitation] = values as [string, string, number, string, string]
      if (!chunkId.startsWith('KP_VOL5.') && !chunkId.startsWith('KP_VOL6.')) {
        throw new Error(`wrong selected volume: ${chunkId}`)
      }
      if (!this.rows.has(chunkId)) {
        this.rows.set(chunkId, { chunkId, verseRef, chapter, content, sourceCitation })
        return { rowCount: 1, rows: [] }
      }
      if (text.includes('ON CONFLICT (chunk_id) DO NOTHING')) {
        return { rowCount: 0, rows: [] }
      }
      this.rows.set(chunkId, { chunkId, verseRef, chapter, content, sourceCitation })
      return { rowCount: 1, rows: [] }
    }
    if (text.includes("chunk_id LIKE 'KP_VOL%'")) {
      return { rowCount: 1, rows: [{ count: String(this.rows.size) }] }
    }
    if (text.includes('chunk_id LIKE $1')) {
      const prefix = String(values[0]).replace('%', '')
      return { rowCount: 1, rows: [{ count: String([...this.rows.keys()].filter(key => key.startsWith(prefix)).length) }] }
    }
    throw new Error(`unexpected query: ${text}`)
  }

  search(needle: string): KPChunk[] {
    return [...this.rows.values()].filter(row => row.content.includes(needle))
  }
}

const fixtureChunks: KPChunk[] = [
  { chunkId: 'KP_VOL5.0001', verseRef: 'KP_VOL5.1', chapter: 1, content: 'Transit governs the timing of events.', sourceCitation: 'fixture vol 5' },
  { chunkId: 'KP_VOL6.0001', verseRef: 'KP_VOL6.1', chapter: 1, content: 'Horary judgment begins from the ascendant.', sourceCitation: 'fixture vol 6' },
]

describe('KP Reader V/VI bootstrap', () => {
  it('parses the two locator-backed OCR volumes without a database or provider call', () => {
    const output = execFileSync('npx', ['tsx', script, '--dry-run', '--volumes', '5,6'], {
      cwd: process.cwd(),
      encoding: 'utf8',
    })

    expect(output).toContain('Vol 5')
    expect(output).toContain('Vol 6')
    expect(output).toContain('[DRY-RUN] Not writing to DB.')
  })

  it('rejects a volume outside the V/VI repair scope', () => {
    const result = spawnSync('npx', ['tsx', script, '--dry-run', '--volumes', '4,5'], {
      cwd: process.cwd(),
      encoding: 'utf8',
    })

    expect(result.status).not.toBe(0)
    expect(`${result.stdout}\n${result.stderr}`).toContain('OUT_OF_SCOPE_VOLUME')
  })

  it.each(['5junk,6', '5,6.9', '5,,6', '5,5', '4,5'])(
    'rejects malformed or out-of-scope selected volumes: %s',
    volumeArgument => {
      const result = spawnSync('npx', ['tsx', script, '--dry-run', '--volumes', volumeArgument], {
        cwd: process.cwd(),
        encoding: 'utf8',
      })

      expect(result.status).not.toBe(0)
      expect(`${result.stdout}\n${result.stderr}`).toMatch(/INVALID_VOLUMES|OUT_OF_SCOPE_VOLUME/)
    },
  )

  it('writes a disposable served corpus that searches both volumes and remains idempotent', async () => {
    const corpus = new DisposableServedCorpus()
    const stats = [{ vol: 5, paragraphs: 1, chunks: 1 }, { vol: 6, paragraphs: 1, chunks: 1 }]

    await expect(ingestKPChunks(corpus, fixtureChunks, stats)).resolves.toEqual({
      inserted: 2,
      total: 2,
      perVolume: { 5: 1, 6: 1 },
    })
    expect(corpus.search('Transit')).toHaveLength(1)
    expect(corpus.search('Horary')).toHaveLength(1)
    await expect(ingestKPChunks(corpus, fixtureChunks, stats)).resolves.toMatchObject({ inserted: 0, total: 2 })
    expect(corpus.search('Transit')[0]?.content).toBe('Transit governs the timing of events.')
    expect(KP_CHUNK_INSERT_SQL).toContain('INSERT INTO classical_text_chunks')
    expect(KP_CHUNK_INSERT_SQL).toContain('ON CONFLICT (chunk_id) DO NOTHING')
    expect(corpus.queries.some(query => query.includes('INSERT INTO rag_chunks'))).toBe(false)
  })

  it('fails the write oracle when the served target is missing', async () => {
    const missingText: KPQueryClient = { query: async () => ({ rowCount: 0, rows: [] }) }
    await expect(ingestKPChunks(missingText, fixtureChunks, [{ vol: 5, paragraphs: 1, chunks: 1 }]))
      .rejects.toThrow('MISSING_SERVED_TEXT')
  })

  it('uses disposable PostgreSQL to preserve duplicate content and search both served volumes', async () => {
    const databaseUrl = process.env.KP_TEST_DATABASE_URL
    if (!databaseUrl) {
      return
    }

    const pool = new Pool({ connectionString: databaseUrl })
    const client = await pool.connect()
    const schema = `kp_l0k_${randomUUID().replaceAll('-', '')}`
    try {
      await client.query(`CREATE SCHEMA ${schema}`)
      await client.query(`SET search_path TO ${schema}`)
      await createDisposableCorpusTables(client)
      await client.query("INSERT INTO classical_texts (text_id) VALUES ('kp_reader')")
      const stats = [{ vol: 5, paragraphs: 1, chunks: 1 }, { vol: 6, paragraphs: 1, chunks: 1 }]

      await expect(ingestKPChunks(client, fixtureChunks, stats)).resolves.toMatchObject({ inserted: 2, total: 2 })
      await expect(ingestKPChunks(client, fixtureChunks, stats)).resolves.toMatchObject({ inserted: 0, total: 2 })
      const preserved = await client.query("SELECT content_en FROM classical_text_chunks WHERE chunk_id = 'KP_VOL5.0001'")
      expect(preserved.rows).toEqual([{ content_en: 'Transit governs the timing of events.' }])
      const servedSearch = await client.query(
        "SELECT chunk_id FROM classical_text_chunks WHERE content_en ILIKE $1 ORDER BY chunk_id",
        ['%Transit%'],
      )
      expect(servedSearch.rows).toEqual([{ chunk_id: 'KP_VOL5.0001' }])
      const bothVolumes = await client.query(
        "SELECT DISTINCT split_part(chunk_id, '.', 1) AS volume FROM classical_text_chunks ORDER BY volume",
      )
      expect(bothVolumes.rows).toEqual([{ volume: 'KP_VOL5' }, { volume: 'KP_VOL6' }])
    } finally {
      await client.query('RESET search_path').catch(() => undefined)
      await client.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`).catch(() => undefined)
      client.release()
      await pool.end()
    }
  })
})

async function createDisposableCorpusTables(client: PoolClient): Promise<void> {
  await client.query('CREATE TABLE classical_texts (text_id text PRIMARY KEY)')
  await client.query(`CREATE TABLE classical_text_chunks (
    text_id text NOT NULL REFERENCES classical_texts(text_id),
    chunk_id text PRIMARY KEY,
    verse_ref text NOT NULL,
    chapter integer NOT NULL,
    verse_start integer NOT NULL,
    verse_end integer NOT NULL,
    content_en text NOT NULL,
    source_citation text NOT NULL
  )`)
}
