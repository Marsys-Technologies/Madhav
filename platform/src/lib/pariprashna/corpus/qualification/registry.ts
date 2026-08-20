/**
 * pariprashna/corpus/qualification/registry.ts — lane P2-O (G3-G, PPR-32).
 *
 * A model→work-class qualification registry: an in-memory, pure-function
 * lookup table built from a set of `ModelQualificationResult`s (`gate.ts`).
 * Deliberately NOT a DB table — this lane's `must_not_touch` scope excludes
 * migration files, and no real qualification RUN has happened yet (see this
 * lane's own report): persisting an empty/synthetic table to the database
 * would misrepresent readiness the same way a fabricated `target_floor`
 * would (CLAUDE.md §N.4 "floors aspirational, not gates"). Building the
 * registry as a pure function of a result set keeps the mechanism real and
 * fully tested while being honest that the durable-store question is
 * unresolved — a disclosed residual for whichever lane wires this to a live
 * qualification run.
 */

import type { ModelQualificationResult } from './gate'
import type { WorkClass } from './work_classes'

export const QUALIFICATION_REGISTRY_VERSION = 1 as const

function registryKey(modelId: string, workClass: WorkClass): string {
  return `${modelId}::${workClass}`
}

export interface QualificationRegistry {
  readonly version: number
  readonly records: ReadonlyMap<string, ModelQualificationResult>
}

/** Builds a registry from a flat result set. Later results for the same (modelId, workClass) pair overwrite earlier ones — "most recent run wins", the same convention a live re-qualification run would need. */
export function buildQualificationRegistry(results: readonly ModelQualificationResult[]): QualificationRegistry {
  const records = new Map<string, ModelQualificationResult>()
  for (const result of results) {
    records.set(registryKey(result.modelId, result.workClass), result)
  }
  return { version: QUALIFICATION_REGISTRY_VERSION, records }
}

export function getQualificationRecord(
  registry: QualificationRegistry,
  modelId: string,
  workClass: WorkClass,
): ModelQualificationResult | undefined {
  return registry.records.get(registryKey(modelId, workClass))
}

/**
 * `false` for both "explicitly not qualified" and "never evaluated" — the
 * caller that needs to distinguish those two honestly should read
 * `getQualificationRecord` directly rather than this boolean convenience.
 */
export function isQualified(registry: QualificationRegistry, modelId: string, workClass: WorkClass): boolean {
  return getQualificationRecord(registry, modelId, workClass)?.qualified === true
}

export function qualifiedModelIds(registry: QualificationRegistry, workClass: WorkClass): readonly string[] {
  return [...registry.records.values()]
    .filter((r) => r.workClass === workClass && r.qualified)
    .map((r) => r.modelId)
}
