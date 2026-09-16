import { readFileSync } from 'node:fs'
import path from 'node:path'

const CAPABILITY_KNOWLEDGE_SNAPSHOT = 'platform/src/generated/capability_knowledge.snapshot.json'
const EPOCH = '1970-01-01T00:00:00.000Z'

function normalizedTimestamp(value: unknown): string {
  if (typeof value !== 'string' || value.trim() === '') throw new Error('generated_at must be a non-empty ISO timestamp')
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) throw new Error('generated_at must be a valid ISO timestamp')
  return parsed.toISOString()
}

/**
 * Keep non-authoritative display metadata pinned to the reviewed artifact.
 *
 * GitHub's merge queue may materialize a PR as either a merge commit or a
 * single-parent squash commit, so no VCS timestamp is stable across the source
 * and queue trees. Semantic freshness is enforced by the rendered artifact,
 * content_hash, and source fingerprints; generated_at is intentionally read
 * from the committed snapshot (or supplied explicitly when refreshing it).
 */
export function resolveCapabilityKnowledgeGeneratedAt(
  repoRoot: string,
  explicitGeneratedAt?: string,
): string {
  if (explicitGeneratedAt !== undefined) return normalizedTimestamp(explicitGeneratedAt)
  try {
    const snapshot = JSON.parse(readFileSync(path.join(repoRoot, CAPABILITY_KNOWLEDGE_SNAPSHOT), 'utf8')) as {
      generated_at?: unknown
    }
    return normalizedTimestamp(snapshot.generated_at)
  } catch {
    return EPOCH
  }
}
