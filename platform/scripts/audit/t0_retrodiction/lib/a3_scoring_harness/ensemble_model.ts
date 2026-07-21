/**
 * ensemble_model.ts — D-4b permission-bridge lane (wave/D-4b/permission-bridge).
 *
 * The hierarchical ENSEMBLE contender: "the confluence-weighted
 * superposition (DR-15(a): multi-modal density is a legitimate served
 * shape, not a contradiction)" (BRIEF_D4B.md §1 B-1). Deliberately SMALL —
 * per-system WEIGHT LEARNING is B-3's job ("per-system weights are
 * LEARNED, never assumed", the very reason B-1 scores the 12 standalone
 * generators separately in the first place), not this contender's. This
 * module superimposes whichever contenders are evaluable by summing their
 * OWN `curve()` output, unweighted, point-for-point — no invented
 * cross-model weighting scheme, no fabricated normalization.
 *
 * Why summing raw intensities is safe even though `pratyantar_lord`'s
 * scale (DEPTH_WEIGHT-summed, potentially >1) differs from a PERMISSION
 * standalone system's binary 0/1 scale: `proper_scoring.ts`'s own header
 * documents that every model's curve is treated as an UNNORMALIZED
 * intensity function, renormalized to a probability distribution
 * (`p_i = intensity_i / sum(intensity_j)`) before CRPS — so the ensemble's
 * summed curve is renormalized exactly the same way any single
 * contender's curve is, and no separate rescaling step is needed or
 * invented here.
 *
 * Grid alignment: every constituent model in this bridge (pratyantar_lord
 * via curve.ts's `buildCurve`, the 12 PERMISSION models via
 * permission_model.ts) is called with the IDENTICAL `[t1, t2]` range and
 * the same 5-day step convention, so their curves land on the same date
 * grid by construction. This is verified, not assumed: a length mismatch
 * throws `EnsembleGridMismatchError` rather than silently truncating or
 * padding either curve.
 */
import type { TemporalCurveModel } from './model_interface'
import type { CurvePoint } from '../curve'

export class EnsembleGridMismatchError extends Error {
  constructor(modelIdA: string, lenA: number, modelIdB: string, lenB: number) {
    super(`hierarchical_ensemble: constituent curves are not grid-aligned — '${modelIdA}' produced ${lenA} points, '${modelIdB}' produced ${lenB}, for the identical (chart, eventClass, range). Refusing to silently truncate/pad; every constituent model must share the same step_days convention over the same range.`)
    this.name = 'EnsembleGridMismatchError'
  }
}

/**
 * `contenders` should be whichever of the bridge's evaluable models
 * (pratyantar_lord + the 12 PERMISSION standalone models) the caller has
 * ALREADY bound (`await m.bind?.(chart, eventClass, range)`) for this
 * exact `(chart, eventClass, range)` triple — this factory's own `bind()`
 * does that binding for the caller as a convenience (chains to every
 * constituent's own `bind`, no-op for a constituent with none), so a
 * caller can treat `hierarchicalEnsembleModel(contenders)` exactly like
 * any other roster entry.
 */
export function hierarchicalEnsembleModel(contenders: TemporalCurveModel[]): TemporalCurveModel {
  if (contenders.length === 0) {
    throw new Error('hierarchicalEnsembleModel: contenders must be non-empty — an ensemble over zero models is not a legitimate superposition, it is a silent zero-curve (B.10).')
  }

  return {
    modelId: 'hierarchical_ensemble',

    async bind(chart, eventClass, range) {
      for (const m of contenders) {
        await m.bind?.(chart, eventClass, range)
      }
    },

    curve(chart, eventClass, range) {
      const curves = contenders.map((m) => ({ modelId: m.modelId, points: m.curve(chart, eventClass, range) }))
      const [first, ...rest] = curves
      for (const c of rest) {
        if (c.points.length !== first.points.length) {
          throw new EnsembleGridMismatchError(first.modelId, first.points.length, c.modelId, c.points.length)
        }
      }
      const out: CurvePoint[] = first.points.map((p, i) => ({
        date: p.date,
        intensity: curves.reduce((sum, c) => sum + c.points[i].intensity, 0),
      }))
      return out
    },
  }
}
