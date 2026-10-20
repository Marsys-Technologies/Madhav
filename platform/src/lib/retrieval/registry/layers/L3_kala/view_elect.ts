import { makeView } from './view_common'
import { evaluateScopedCancellation, parseCancellationRequest, type PariharaEvaluator } from './parihara_cancellation'

const stage = makeView({
  name: 'elect',
  description: 'Stored election assertions, obstruction states and their contacts for an explicit event class and horizon; no calendar recomputation.',
  sources: ['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts'],
  required: ['event_class', 'date_from', 'date_to'],
})

/** KA-4b (ALGO 3.17 step 3): an explicit `scoped_cancellation` argument additionally reads the parihāra
 * evaluator for named doṣas: `cancelled` with its source locator for marriage, upanayana and general,
 * `cancellation_unassessed` for everything else, never "clear". Requests without it keep the stored-stage
 * response unchanged.
 * Argument: { undertaking, candidate: { start_utc, end_utc }, location: { lat, lon, tz_offset_minutes },
 * location_basis?, dosas_present: string[] } (see parseCancellationRequest).
 * (I) INTERPRETATION: the catalog descriptor (input_schema / semantic outputs) is left byte-identical here,
 * because the generated knowledge snapshot feeds the pinned acceptance artifacts (BEYOND_ACARYA_ACCEPTANCE_v*);
 * declaring the argument belongs to the catalog-advance PR that issues the next successor artifact. */
export function makeElectView(evaluate?: PariharaEvaluator): typeof stage {
  return {
    ...stage,
    async handler(args, context) {
      if (!Object.hasOwn(args, 'scoped_cancellation')) return stage.handler!(args, context)
      const request = parseCancellationRequest(args.scoped_cancellation)
      if (typeof request === 'string') {
        return { content: { view: 'elect', manifest_id: null, empty_reason: 'invalid_request', error: request }, is_error: true }
      }
      const base = await stage.handler!(args, context)
      if (base.is_error || typeof base.content !== 'object') return base
      const scoped_cancellation = await evaluateScopedCancellation(request, evaluate)
      return { ...base, content: { ...base.content, scoped_cancellation } }
    },
  }
}

export const electViewCapability = makeElectView()
