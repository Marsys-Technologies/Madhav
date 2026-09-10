/**
 * pariprashna/corpus/qualification/fallback.ts — lane P2-O (G3-G, PPR-32).
 *
 * Roadmap line 107's third clause: "fallback substitutes only equally-
 * qualified models or degrades VISIBLY with a flag + provenance record."
 *
 * `selectModelForWorkClass` is a PURE function over `models/registry.ts`'s
 * `MODELS` (read-only import, per this lane's scope — nothing in that file
 * is modified) and this lane's own `QualificationRegistry`. It answers one
 * question: "may `requestedModelId` serve `workClass`, and if not, what
 * happens?" — never silently returning the unqualified model as if nothing
 * were wrong.
 *
 * "Equally qualified" is read STRUCTURALLY from the registry's existing
 * three-tier family structure (`ModelTier`: premium/mid/worker,
 * `registry.ts`'s own docblock: "premium — flagship/deepest model...  mid —
 * balanced model...  worker — cheapest"): a same-tier model that the
 * qualification registry separately confirms IS qualified for this work
 * class is the substitute; a different-tier model is never silently
 * substituted even if qualified, because tier is this codebase's own
 * capability/cost signal and swapping it without disclosure would silently
 * change what the reader is actually getting (a worker-tier model standing
 * in for a premium request, or vice versa, at a different quality and cost
 * point than what was asked for).
 *
 * ── NOT WIRED INTO LIVE SELECTION (disclosed) ──────────────────────────────
 * This function is not called from `bindTurnParams`
 * (`pipeline/safety_gate.ts`) or anywhere else in the live request path.
 * `models/registry.ts` and `pipeline/safety_gate.ts` are both read-only for
 * this lane's scope, and — more fundamentally — no real qualification run
 * has happened yet (see this lane's own report: the registry this function
 * consumes has never been populated from a live corpus run against a real
 * model in this environment). Wiring a mechanism that always returns
 * "everyone is unqualified" into the live model-selection path would
 * either silently degrade every request or require a bypass flag that
 * defeats the point — neither is proportionate for a lane whose own
 * upstream data does not exist yet. This module is real, tested, and ready
 * to be called the moment a qualification registry backed by an actual
 * corpus run exists; connecting it to `bindTurnParams` is left as a
 * disclosed residual for that later lane.
 */

import { MODELS, getModelMeta, type ModelTier } from '@/lib/models/registry'
import { isQualified, type QualificationRegistry } from './registry'
import type { WorkClass } from './work_classes'

export const MODEL_SELECTION_MECHANISM_VERSION = 1 as const

export type ModelSelectionOutcome = 'requested_model_qualified' | 'substituted_same_tier' | 'degraded_unqualified' | 'degraded_unknown_model'

export interface ModelSelectionResult {
  /** The model id the caller should actually use. Equal to `requestedModelId` unless `outcome === 'substituted_same_tier'`. */
  selectedModelId: string
  requestedModelId: string
  workClass: WorkClass
  outcome: ModelSelectionOutcome
  /** `true` whenever the served model is not a confirmed-qualified match for the request — i.e. every outcome except `requested_model_qualified`. */
  degraded: boolean
  /** Reader/operator-visible flag. `null` only for `requested_model_qualified` — every degraded path carries one, never a silent substitution. */
  flag: string | null
  provenance: {
    mechanismVersion: number
    requestedModelTier: ModelTier | null
    selectedModelTier: ModelTier | null
    requestedModelQualified: boolean | null
    selectedModelQualified: boolean | null
    reason: string
  }
}

export function selectModelForWorkClass(args: {
  requestedModelId: string
  workClass: WorkClass
  registry: QualificationRegistry
}): ModelSelectionResult {
  const { requestedModelId, workClass, registry } = args
  const requestedMeta = getModelMeta(requestedModelId)

  if (!requestedMeta) {
    // An unknown model id cannot be reasoned about structurally at all — degrade
    // visibly rather than guessing at a tier or silently falling through to a
    // default (that would be exactly the "silent substitution" this mechanism
    // exists to prevent).
    return {
      selectedModelId: requestedModelId,
      requestedModelId,
      workClass,
      outcome: 'degraded_unknown_model',
      degraded: true,
      flag: `model_qualification_unknown_model:${workClass}`,
      provenance: {
        mechanismVersion: MODEL_SELECTION_MECHANISM_VERSION,
        requestedModelTier: null,
        selectedModelTier: null,
        requestedModelQualified: null,
        selectedModelQualified: null,
        reason: `"${requestedModelId}" is not a registered model — cannot evaluate tier or qualification.`,
      },
    }
  }

  const requestedQualified = isQualified(registry, requestedModelId, workClass)
  if (requestedQualified) {
    return {
      selectedModelId: requestedModelId,
      requestedModelId,
      workClass,
      outcome: 'requested_model_qualified',
      degraded: false,
      flag: null,
      provenance: {
        mechanismVersion: MODEL_SELECTION_MECHANISM_VERSION,
        requestedModelTier: requestedMeta.tier,
        selectedModelTier: requestedMeta.tier,
        requestedModelQualified: true,
        selectedModelQualified: true,
        reason: 'requested model is qualified for this work class',
      },
    }
  }

  // Look for a same-tier, synthesis-capable substitute the registry separately
  // confirms is qualified. Never cross tiers — see this module's docblock.
  const sameTierCandidates = MODELS.filter(
    (m) => m.id !== requestedMeta.id && m.tier === requestedMeta.tier && (m.role === 'synthesis' || m.role === 'both'),
  )
  const substitute = sameTierCandidates.find((m) => isQualified(registry, m.id, workClass))

  if (substitute) {
    return {
      selectedModelId: substitute.id,
      requestedModelId,
      workClass,
      outcome: 'substituted_same_tier',
      degraded: true,
      flag: `model_substituted_for_work_class:${workClass}:${requestedModelId}->${substitute.id}`,
      provenance: {
        mechanismVersion: MODEL_SELECTION_MECHANISM_VERSION,
        requestedModelTier: requestedMeta.tier,
        selectedModelTier: substitute.tier,
        requestedModelQualified: false,
        selectedModelQualified: true,
        reason: `requested model not qualified for ${workClass}; substituted same-tier (${requestedMeta.tier}) qualified model "${substitute.id}"`,
      },
    }
  }

  // No equally-qualified substitute exists. Serve the request but degrade
  // VISIBLY — never proceed as if the model were qualified.
  return {
    selectedModelId: requestedModelId,
    requestedModelId,
    workClass,
    outcome: 'degraded_unqualified',
    degraded: true,
    flag: `unqualified_model_serving_work_class:${workClass}:${requestedModelId}`,
    provenance: {
      mechanismVersion: MODEL_SELECTION_MECHANISM_VERSION,
      requestedModelTier: requestedMeta.tier,
      selectedModelTier: requestedMeta.tier,
      requestedModelQualified: false,
      selectedModelQualified: false,
      reason: `no same-tier (${requestedMeta.tier}) qualified substitute exists for ${workClass}; proceeding with unqualified requested model, flagged`,
    },
  }
}
