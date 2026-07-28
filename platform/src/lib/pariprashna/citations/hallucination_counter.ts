/**
 * pariprashna/citations/hallucination_counter.ts — PB-1 lane S-3.
 *
 * In-memory, per-model counter of UNRESOLVABLE citation sentinels (a sentinel
 * that was well-formed but pointed at a reference with no matching source — the
 * model cited something it did not have grounding for).
 *
 * Persistence is explicitly a LATER wave's job (per the S-3 brief). This wave
 * only needs a process-lifetime tally keyed by model_id so the stream route and
 * tests can assert "model X hallucinated N citations this run."
 */

export interface HallucinationCounter {
  /** Record one unresolvable sentinel for a model; returns the new total. */
  increment(modelId: string): number
  /** Read the current total for a model. */
  get(modelId: string): number
  /** Snapshot of all model → count pairs. */
  snapshot(): Record<string, number>
  /** Reset (test hygiene). */
  reset(modelId?: string): void
}

/** Factory for an isolated counter instance (preferred — no cross-test bleed). */
export function createHallucinationCounter(): HallucinationCounter {
  const counts = new Map<string, number>()
  return {
    increment(modelId: string): number {
      const next = (counts.get(modelId) ?? 0) + 1
      counts.set(modelId, next)
      return next
    },
    get(modelId: string): number {
      return counts.get(modelId) ?? 0
    },
    snapshot(): Record<string, number> {
      return Object.fromEntries(counts)
    },
    reset(modelId?: string): void {
      if (modelId === undefined) counts.clear()
      else counts.delete(modelId)
    },
  }
}

/**
 * Process-wide default counter. The stream route can share this across requests
 * for a coarse per-model tally; tests should prefer createHallucinationCounter()
 * for isolation.
 */
export const globalHallucinationCounter: HallucinationCounter = createHallucinationCounter()
