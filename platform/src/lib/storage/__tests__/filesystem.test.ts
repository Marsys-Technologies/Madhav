import { describe, it, expect } from 'vitest'
import { filesystemAdapter } from '../filesystem'

describe('filesystemAdapter', () => {
  it('reads a known file', async () => {
    const content = await filesystemAdapter.readFile('package.json')
    expect(content).toContain('"name"')
  })

  it('fileExists returns true for known file', async () => {
    expect(await filesystemAdapter.fileExists('package.json')).toBe(true)
  })

  it('fileExists returns false for missing file', async () => {
    expect(await filesystemAdapter.fileExists('no_such_file_abc123.txt')).toBe(false)
  })

  it('blocks path traversal', async () => {
    await expect(filesystemAdapter.readFile('../../etc/passwd')).rejects.toThrow('Path traversal attempt blocked')
  })

  it('listFiles returns an array of strings', async () => {
    const files = await filesystemAdapter.listFiles('src/lib/storage')
    expect(Array.isArray(files)).toBe(true)
    expect(files.length).toBeGreaterThan(0)
  })

  it('listFiles filters by pattern', async () => {
    const files = await filesystemAdapter.listFiles('src/lib/storage', { pattern: '*.ts' })
    expect(files.every((f) => f.endsWith('.ts'))).toBe(true)
  })
})
