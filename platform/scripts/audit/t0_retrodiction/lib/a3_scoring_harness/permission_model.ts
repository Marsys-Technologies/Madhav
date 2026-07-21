/**
 * permission_model.ts — D-4b permission-bridge lane (wave/D-4b/permission-bridge).
 *
 * Wires the 12 D-5 PERMISSION system-generators into `TemporalCurveModel`
 * (model_interface.ts), per BRIEF_D4B.md §1 B-1: "each D-5 system-generator
 * standalone ... run as if each were the SOLE timing signal, per DR-14's
 * 'per-system weights are LEARNED, never assumed' mandate". This is the
 * missing piece B1_BAKEOFF_STATUS_v1_0.md §3 found: "compute_permission()
 * ... returns one point-in-time (permission, detail) pair ... not a
 * curve(chart, event_class, [t1,t2]) series — no TemporalCurveModel
 * wrapper for any of the 12 exists anywhere."
 *
 * ONE adapter factory (`permissionSystemModel`), PARAMETERIZED by
 * `system_id` — not 12 copy-pasted files — calling the sidecar's new
 * `POST /api/compute/permission_curve` route (routers/permission_curve.py,
 * this same lane), which itself is a thin, read-only wrap of the
 * ALREADY-EXISTING `gochara_intensity.permission.compute_permission()`
 * (unmodified — see that route's own module docstring).
 *
 * ASYNC BRIDGE (why `bind()` exists): `TemporalCurveModel.curve()` is a
 * SYNCHRONOUS contract (model_interface.ts), but this model's data can only
 * be resolved over HTTP. `bind()` performs the one HTTP call for a given
 * `(chart, eventClass, range)` triple and caches the resulting points;
 * `curve()` then reads that cache synchronously. A `curve()` call for a
 * triple that was never bound throws `PermissionModelNotBoundError` — it
 * NEVER falls back to a fabricated/empty curve (B.10; mirrors
 * `NotImplementedModelError`'s "never a silent zero-curve" discipline).
 *
 * INTENSITY SEMANTICS: each point's `intensity` is that ONE system's own
 * `active` boolean from `compute_permission`'s per-system decomposition,
 * read as 1.0/0.0 — never re-weighted by `SYSTEM_WEIGHTS` here (that
 * blending is `compute_permission`'s own combined `permission` scalar,
 * which this model deliberately does NOT read, per BRIEF_D4B's own framing
 * that a standalone-system contender treats its system as the SOLE
 * signal). `proper_scoring.ts` treats every model's curve as an
 * UNNORMALIZED intensity function (see that module's own header) and
 * renormalizes internally before CRPS, so this binary scale composes
 * correctly with every other contender's own native scale without this
 * module inventing any cross-model rescaling.
 */
import type { ChartContext, EventClass, TemporalCurveModel } from './model_interface'
import type { CurvePoint } from '../curve'

// Live-verified against services/gochara_intensity/permission.py (8 chart_dashas
// systems + sade_sati + guru_shani_double_transit + av_threshold + planetary_return
// = 12) — see routers/permission_curve.py's own PERMISSION_SYSTEM_IDS, which asserts
// at import time that this exact set matches permission.py's live SYSTEM_WEIGHTS
// keys. Duplicated here (not imported cross-language) because this is the TS side of
// the bridge; a drift between the two lists would surface immediately as a 400 from
// the sidecar's own `unknown system_ids requested` validation (see
// `permissionSystemModel`'s error handling below), not silently.
export const PERMISSION_SYSTEM_IDS = [
  'vimshottari', 'yogini', 'ashtottari', 'chara_karaka', 'naisargika', 'mudda',
  'kalachakra', 'narayana',
  'sade_sati', 'guru_shani_double_transit', 'av_threshold', 'planetary_return',
] as const

export type PermissionSystemId = (typeof PERMISSION_SYSTEM_IDS)[number]

export class PermissionCurveFetchError extends Error {
  constructor(systemId: string, detail: string) {
    super(`permission system '${systemId}': sidecar /api/compute/permission_curve call failed — ${detail}`)
    this.name = 'PermissionCurveFetchError'
  }
}

export class PermissionModelNotBoundError extends Error {
  constructor(systemId: string) {
    super(`permission system '${systemId}': curve() called before bind() resolved this (chart, eventClass, range) — this model never fabricates a curve; the caller must 'await model.bind(chart, eventClass, range)' first.`)
    this.name = 'PermissionModelNotBoundError'
  }
}

export type PermissionModelOptions = {
  sidecarUrl?: string
  apiKey?: string
  stepDays?: number
  windowDays?: number
  ayanamshaId?: string
  /** Injectable for tests — defaults to the global `fetch` (Node 18+ has this natively). */
  fetchImpl?: typeof fetch
}

function resolveOpts(opts: PermissionModelOptions | undefined) {
  return {
    sidecarUrl: opts?.sidecarUrl ?? process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000',
    apiKey: opts?.apiKey ?? process.env.PYTHON_SIDECAR_API_KEY ?? '',
    stepDays: opts?.stepDays ?? 5,
    windowDays: opts?.windowDays ?? 15.0,
    ayanamshaId: opts?.ayanamshaId ?? 'lahiri_chitrapaksha',
    fetchImpl: opts?.fetchImpl ?? fetch,
  }
}

function bindKey(chart: ChartContext, eventClass: EventClass, range: [Date, Date]): string {
  return `${chart.chartId}|${eventClass}|${range[0].toISOString()}|${range[1].toISOString()}`
}

/**
 * The ONE adapter factory for all 12 PERMISSION standalone contenders —
 * `permissionSystemModel('vimshottari', opts)`,
 * `permissionSystemModel('sade_sati', opts)`, etc. `systemId` is validated
 * against `PERMISSION_SYSTEM_IDS` at call time (fails loudly on a typo,
 * never silently produces a model that will always 400).
 */
export function permissionSystemModel(systemId: PermissionSystemId, opts?: PermissionModelOptions): TemporalCurveModel {
  if (!PERMISSION_SYSTEM_IDS.includes(systemId)) {
    throw new Error(`permissionSystemModel: '${systemId}' is not one of the 12 live PERMISSION_SYSTEM_IDS: ${PERMISSION_SYSTEM_IDS.join(', ')}`)
  }
  const o = resolveOpts(opts)
  const cache = new Map<string, CurvePoint[]>()

  return {
    modelId: systemId,

    async bind(chart, eventClass, range) {
      const [t1, t2] = range
      let resp: Response
      try {
        resp = await o.fetchImpl(`${o.sidecarUrl}/api/compute/permission_curve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'x-api-key': o.apiKey },
          body: JSON.stringify({
            chart_id: chart.chartId,
            event_class: eventClass,
            t_start: t1.toISOString(),
            t_end: t2.toISOString(),
            step_days: o.stepDays,
            window_days: o.windowDays,
            ayanamsha_id: o.ayanamshaId,
            system_ids: [systemId],
          }),
        })
      } catch (err) {
        throw new PermissionCurveFetchError(systemId, `network error reaching sidecar at ${o.sidecarUrl} — ${err instanceof Error ? err.message : String(err)}`)
      }
      if (!resp.ok) {
        let detail = `HTTP ${resp.status}`
        try {
          const body = (await resp.json()) as { detail?: string }
          if (body?.detail) detail += `: ${body.detail}`
        } catch {
          // response body not JSON — keep the bare status
        }
        throw new PermissionCurveFetchError(systemId, detail)
      }
      const body = (await resp.json()) as {
        systems: Record<string, { t_datetime_ist: string; intensity: number }[]>
      }
      const points = body.systems?.[systemId]
      if (!points) {
        throw new PermissionCurveFetchError(systemId, `sidecar response missing systems['${systemId}'] entirely — response shape drifted from routers/permission_curve.py's documented contract`)
      }
      const curve: CurvePoint[] = points.map((p) => ({ date: new Date(p.t_datetime_ist), intensity: p.intensity }))
      cache.set(bindKey(chart, eventClass, range), curve)
    },

    curve(chart, eventClass, range) {
      const cached = cache.get(bindKey(chart, eventClass, range))
      if (!cached) throw new PermissionModelNotBoundError(systemId)
      return cached
    },
  }
}

/** All 12 PERMISSION standalone models at once, same `opts` applied to each — convenience for roster assembly (roster.ts). */
export function allPermissionSystemModels(opts?: PermissionModelOptions): TemporalCurveModel[] {
  return PERMISSION_SYSTEM_IDS.map((sid) => permissionSystemModel(sid, opts))
}
