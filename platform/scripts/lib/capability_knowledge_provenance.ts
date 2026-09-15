import { execFileSync } from 'node:child_process'

const CAPABILITY_KNOWLEDGE_SOURCE = 'platform/src/lib/retrieval/registry'

/**
 * Bind the generated snapshot timestamp to the reviewed semantic source
 * revision rather than wall-clock time. Merge commits are excluded because
 * GitHub's merge queue creates an ephemeral merge-group commit whose timestamp
 * changes without changing the reviewed source. Source archives without Git
 * metadata use the epoch.
 */
export function resolveCapabilityKnowledgeGeneratedAt(repoRoot: string): string {
  try {
    const committedAt = execFileSync(
      'git',
      ['log', '--no-merges', '-1', '--format=%cI', '--', CAPABILITY_KNOWLEDGE_SOURCE],
      { cwd: repoRoot, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] },
    ).trim()
    return new Date(committedAt).toISOString()
  } catch {
    return '1970-01-01T00:00:00.000Z'
  }
}
