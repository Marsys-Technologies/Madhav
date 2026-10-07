import { execFileSync, spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const script = 'scripts/bootstrap/bootstrap_classical_texts_kp.ts'

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

  it('targets only the served corpus and keeps repeated ingestion idempotent', () => {
    const source = readFileSync(join(process.cwd(), script), 'utf8')

    expect(source).toContain('INSERT INTO classical_text_chunks')
    expect(source).toContain("text_id = 'kp_reader'")
    expect(source).toContain('ON CONFLICT (chunk_id) DO NOTHING')
    expect(source).not.toContain('INSERT INTO rag_chunks')
  })
})
