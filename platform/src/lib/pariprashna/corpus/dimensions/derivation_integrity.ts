/**
 * pariprashna/corpus/dimensions/derivation_integrity.ts — lane P2-N (G3-F).
 *
 * Grounded directly in G3-A's `AcharyaReadingReceipt` (merged, PR #1363):
 * `derivation_chains` (per committed block, which `SIG.*` refs that block's
 * OWN text cites) and `facts_consumed` (the turn's full by-reference fact
 * list). CLAUDE.md §N.5: an L2+ signal never restates a fact — it references
 * it, and the reference MUST resolve. This dimension operationalizes that at
 * the receipt level: every ref a block cites must also appear in the turn's
 * own `facts_consumed` ledger. A ref that doesn't resolve is exactly the
 * "structurally finds nothing" silent-empty defect class `assemble.ts`'s own
 * docblock names for `buildDerivationChains` — this dimension is the
 * regression check for that defect class recurring.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const DERIVATION_INTEGRITY_DIMENSION = 'derivation_integrity' as const

export function scoreDerivationIntegrity(obs: TurnObservation): DimensionResult {
  const { receipt } = obs
  if (!receipt) {
    return {
      dimension: DERIVATION_INTEGRITY_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no AcharyaReadingReceipt was supplied for this observation',
      findings: [],
    }
  }

  const factRefs = new Set(receipt.facts_consumed.map((f) => f.ref))
  const findings: string[] = []
  let citedTotal = 0
  let resolvedTotal = 0

  for (const block of receipt.derivation_chains) {
    for (const ref of block.fact_refs) {
      citedTotal += 1
      if (factRefs.has(ref)) {
        resolvedTotal += 1
      } else {
        findings.push(
          `block ${block.block_id} cites ${ref}, which does not appear in facts_consumed (unresolved reference)`,
        )
      }
    }
  }

  if (citedTotal === 0) {
    // Vacuously true: nothing was cited, so nothing failed to resolve. Still
    // worth flagging if facts_consumed is non-empty while no block cites
    // anything — the exact silent-empty shape assemble.ts's docblock warns
    // about (citationRewriteEnabled path scanning already-rewritten text).
    if (receipt.facts_consumed.length > 0) {
      findings.push(
        `facts_consumed has ${receipt.facts_consumed.length} entries but no derivation_chains block cites any of them`,
      )
      return {
        dimension: DERIVATION_INTEGRITY_DIMENSION,
        status: 'scored',
        score: 0,
        reason: null,
        findings,
      }
    }
    return { dimension: DERIVATION_INTEGRITY_DIMENSION, status: 'scored', score: 1, reason: null, findings: [] }
  }

  return {
    dimension: DERIVATION_INTEGRITY_DIMENSION,
    status: 'scored',
    score: resolvedTotal / citedTotal,
    reason: null,
    findings,
  }
}
