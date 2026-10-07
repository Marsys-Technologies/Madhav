import { execFileSync, spawnSync } from 'node:child_process'
import { describe, expect, it } from 'vitest'
import { ingestKPChunks, type KPChunk, type KPQueryClient } from '../bootstrap_classical_texts_kp'

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
      return { rowCount: 0, rows: [] }
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
    expect(corpus.queries.some(query => query.includes('INSERT INTO rag_chunks'))).toBe(false)
  })

  it('fails the write oracle when the served target is missing', async () => {
    const missingText: KPQueryClient = { query: async () => ({ rowCount: 0, rows: [] }) }
    await expect(ingestKPChunks(missingText, fixtureChunks, [{ vol: 5, paragraphs: 1, chunks: 1 }]))
      .rejects.toThrow('MISSING_SERVED_TEXT')
  })
})
