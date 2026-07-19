/**
 * model_interface.ts — the model-agnostic `curve(chart, event_class,
 * [t1,t2])` contract (BRIEF_D4A.md Lane A-3, deliverable 5; DIS.028/DR-15(a)
 * "confluence ensembles are first-class model contenders, not resolved to a
 * single peak-logic").
 *
 * DR-10 (DIS.023) names three model contenders: `midpoint_triangle`
 * (deprecated default), `pratyantar_lord` (classical default), and
 * `transit_kernel` (supersedes both once it ships). Only `pratyantar_lord`
 * is servable today (T-0's existing `dasha_lord_confluence_v1` proxy from
 * curve.ts / mechanisms.ts — DR-10's interim approximation of it). This
 * module wraps that ONE real model behind the shared interface and stubs
 * the other two with an explicit `NotImplementedModelError` (never a silent
 * zero-curve) so Lane A-5 can register a real implementation later without
 * touching the harness contract (scoring_harness.ts consumes ONLY this
 * interface, never `buildCurve`/`DashaPeriod` directly).
 *
 * `ChartContext.substrate` is deliberately an opaque bag, not a fixed shape:
 * pratyantar-lord needs `{ periods: DashaPeriod[] }`; a future transit-kernel
 * model will need ephemeris/aspect data; a future midpoint-triangle model
 * will need natal + transit longitudes. The harness never reaches into
 * `substrate` itself — only the model implementation that declared it knows
 * what it needs. This is what makes deliverable 5 genuinely model-agnostic
 * rather than "one function signature, still coupled to dasha periods
 * underneath."
 */
import type { DashaPeriod, CurvePoint } from '../curve'
import { buildCurve } from '../curve'

export type EventClass = string // canonical event-class id, A-2 ontology (bo_*/ka_* event-class enumeration — this module does not assume a fixed list, it is handed whatever id the caller resolved)

export type ChartContext = {
  chartId: string
  ayanamsha?: string
  /** Opaque, model-specific substrate. Never read by the harness — only by the model that owns the shape it expects here. */
  substrate: Record<string, unknown>
}

export type ModelId = 'pratyantar_lord' | 'midpoint_triangle' | 'transit_kernel' | (string & {})

/**
 * The one contract every scoreable model exposes. `curve()` returns the
 * model's intensity function over `[t1, t2]`, discretized (STEP_DAYS
 * resolution is the model's own choice — the harness makes no assumption
 * about spacing beyond "sorted ascending by date").
 */
export type TemporalCurveModel = {
  readonly modelId: ModelId
  curve(chart: ChartContext, eventClass: EventClass, range: [Date, Date]): CurvePoint[]
}

export class NotImplementedModelError extends Error {
  constructor(modelId: string) {
    super(`${modelId}: not implemented — this is a registered contender per DR-10 but has no servable substrate yet. Lane A-5 (or a later lane) must supply a real curve() before this model can be scored; the harness will never silently substitute a zero/flat curve for a missing model.`)
    this.name = 'NotImplementedModelError'
  }
}

/**
 * The ONE real model servable today: DR-10's interim `dasha_lord_confluence_v1`
 * proxy (curve.ts's `buildCurve`), wrapped behind the shared interface.
 * `eventClassSignificators` maps an A-2 event-class id to the significator
 * weights that mechanism uses (mirrors mechanisms.ts's category->significator
 * map, but keyed by event_class rather than LEL free-text category — the
 * caller resolves that mapping and hands it in, this module does not invent
 * a canonical event-class list itself, per A-2 owning that enumeration).
 */
export function pratyantarLordModel(eventClassSignificators: Record<EventClass, Record<string, number>>): TemporalCurveModel {
  return {
    modelId: 'pratyantar_lord',
    curve(chart, eventClass, [t1, t2]) {
      const periods = chart.substrate.periods as DashaPeriod[] | undefined
      if (!periods) {
        throw new Error(`pratyantar_lord model: chart.substrate.periods missing for chart ${chart.chartId} — this model requires a DashaPeriod[] substrate.`)
      }
      const significators = eventClassSignificators[eventClass]
      if (!significators) {
        // Honest empty curve, not an error: an event class this significator map has no
        // entry for genuinely has zero modeled intensity under this model — matches
        // curve.ts's own "domain not in domains_affected_array -> excluded" convention.
        const out: CurvePoint[] = []
        let t = t1.getTime()
        while (t <= t2.getTime()) {
          out.push({ date: new Date(t), intensity: 0 })
          t += 5 * 86_400_000
        }
        return out
      }
      return buildCurve(periods, significators, t1, t2, 5)
    },
  }
}

/** DR-10 contender, not yet servable (no midpoint-triangle substrate wired into this harness). Stub — throws, never fabricates a curve. */
export function midpointTriangleModel(): TemporalCurveModel {
  return {
    modelId: 'midpoint_triangle',
    curve() {
      throw new NotImplementedModelError('midpoint_triangle')
    },
  }
}

/** DR-10 contender, not yet servable (transit kernel has not shipped — BRIEF_D4A §F1 A-5 note). Stub — throws, never fabricates a curve. */
export function transitKernelModel(): TemporalCurveModel {
  return {
    modelId: 'transit_kernel',
    curve() {
      throw new NotImplementedModelError('transit_kernel')
    },
  }
}
