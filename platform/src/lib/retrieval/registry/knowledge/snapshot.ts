import snapshotJson from '@/generated/capability_knowledge.snapshot.json'
import { getCatalog } from '../catalog'
import { compileCapabilityKnowledge } from './compiler'
import { deepFreeze } from './stable'
import type { CapabilityKnowledgeSnapshot } from './types'

const PINNED_SNAPSHOT = deepFreeze(snapshotJson as unknown as CapabilityKnowledgeSnapshot)

/** The immutable build-time artifact used by every planner/inquiry door. */
export function getPinnedCapabilityKnowledgeSnapshot(): CapabilityKnowledgeSnapshot {
  return PINNED_SNAPSHOT
}

/** Fail closed if deployed handlers and the build-time authorization artifact drift. */
export function assertPinnedCapabilityKnowledgeCurrent(): CapabilityKnowledgeSnapshot {
  const live = compileCapabilityKnowledge(getCatalog(), PINNED_SNAPSHOT.generated_at)
  if (live.content_hash !== PINNED_SNAPSHOT.content_hash
    || live.source_catalog_fingerprint !== PINNED_SNAPSHOT.source_catalog_fingerprint) {
    throw new Error('CAPABILITY_KNOWLEDGE_STALE')
  }
  return PINNED_SNAPSHOT
}
