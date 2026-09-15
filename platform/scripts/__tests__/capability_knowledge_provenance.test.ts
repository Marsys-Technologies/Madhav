import { execFileSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

import { resolveCapabilityKnowledgeGeneratedAt } from '../lib/capability_knowledge_provenance'

function git(repoRoot: string, args: string[], timestamp?: string): string {
  return execFileSync('git', args, {
    cwd: repoRoot,
    encoding: 'utf8',
    env: timestamp
      ? { ...process.env, GIT_AUTHOR_DATE: timestamp, GIT_COMMITTER_DATE: timestamp }
      : process.env,
  }).trim()
}

describe('capability knowledge provenance', () => {
  it('ignores a synthetic merge-group commit when binding generated_at', () => {
    const repoRoot = mkdtempSync(path.join(tmpdir(), 'capability-knowledge-provenance-'))
    const registryRoot = path.join(repoRoot, 'platform/src/lib/retrieval/registry')
    mkdirSync(registryRoot, { recursive: true })

    git(repoRoot, ['init', '-q', '-b', 'main'])
    git(repoRoot, ['config', 'user.email', 'test@example.com'])
    git(repoRoot, ['config', 'user.name', 'Test'])

    writeFileSync(path.join(registryRoot, 'catalog.ts'), 'export const catalog = 1\n')
    git(repoRoot, ['add', '.'])
    git(repoRoot, ['commit', '-q', '-m', 'base'], '2026-09-15T15:00:00Z')

    git(repoRoot, ['checkout', '-q', '-b', 'feature'])
    writeFileSync(path.join(registryRoot, 'catalog.ts'), 'export const catalog = 2\n')
    git(repoRoot, ['add', '.'])
    git(repoRoot, ['commit', '-q', '-m', 'semantic source'], '2026-09-15T15:40:50Z')

    git(repoRoot, ['checkout', '-q', 'main'])
    writeFileSync(path.join(repoRoot, 'unrelated.txt'), 'base advances\n')
    git(repoRoot, ['add', '.'])
    git(repoRoot, ['commit', '-q', '-m', 'advance base'], '2026-09-15T15:50:00Z')

    git(repoRoot, ['merge', '--no-ff', '--no-commit', 'feature'])
    // Model a queue-created merge tree that Git considers to affect the source
    // path. Its time must not replace the reviewed semantic source commit time.
    writeFileSync(path.join(registryRoot, 'catalog.ts'), 'export const catalog = 2\n// merge group\n')
    git(repoRoot, ['add', '.'])
    git(repoRoot, ['commit', '-q', '-m', 'synthetic merge group'], '2026-09-15T16:00:00Z')

    expect(resolveCapabilityKnowledgeGeneratedAt(repoRoot))
      .toBe('2026-09-15T15:40:50.000Z')
  })

  it('falls back to the epoch without Git provenance', () => {
    const archiveRoot = mkdtempSync(path.join(tmpdir(), 'capability-knowledge-archive-'))
    expect(resolveCapabilityKnowledgeGeneratedAt(archiveRoot))
      .toBe('1970-01-01T00:00:00.000Z')
  })
})
