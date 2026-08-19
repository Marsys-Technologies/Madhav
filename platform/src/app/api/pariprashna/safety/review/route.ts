/**
 * /api/pariprashna/safety/review — THE HS-3/HS-4 REVIEW LIFECYCLE ENTRY POINT.
 *
 * Lane G1-A, hardening round item C-7.
 *
 * ── WHY THIS FILE EXISTS ─────────────────────────────────────────────────────
 * The first G1-A build shipped `review_machine.ts` (a genuine, well-tested pure
 * state machine) and `review_db.ts` (its persistence), and described the pair in
 * its commit message as "the three-step path as a real state machine". A
 * reviewer then checked the only question that matters about a state machine —
 * who drives it — and found the honest answer: NOBODY. `recordAdversarialPass`,
 * `signOff`, `withhold`, `persistReviewTransition`, `loadReview` and
 * `isReleasable` had zero callers outside their own modules and tests. No cron,
 * no admin route, no job. Every review that opened sat in `seal_pending`
 * forever, and there was no way — not a slow way, not a manual way, no way — for
 * a human to complete the two-pass + sign-off flow the lane's own documentation
 * described as built.
 *
 * That is the §N.8 defect class exactly: machinery that measures nothing because
 * nothing runs it, described as though it did. The lane had already applied the
 * honest-disclosure discipline to `notification.ts` ("NOT BUILT: delivery") and
 * `predictive_sampling.ts` ("§IS.8 is a governance cadence with no runtime
 * mechanism") and then failed to apply it to this one.
 *
 * This route is the fix, and it is the SMALLER of the two honest options: not a
 * disclosure that the lifecycle cannot run, but a real entry point so that it
 * can. It is deliberately bare — JSON in, JSON out, no UI — because a bare-bones
 * surface a human can actually drive is worth more than an admin console this
 * round has no mandate to design. What it is NOT is a claim that the review
 * WORKFLOW is productized: there is no queue view, no reviewer assignment, no
 * notification that a review is waiting. `review_machine.ts`'s header states
 * that residual in the same terms.
 *
 * ── WHAT DRIVES IT ───────────────────────────────────────────────────────────
 * A human, deliberately, with super-admin credentials. That is not a limitation
 * to be engineered away later — MP §3.5.C requires the sign-off to be an
 * "explicit native sign-off", a SEPARATE act informed by the two passes, and an
 * automated caller for this endpoint would collapse the two controls the whole
 * state machine exists to keep apart.
 *
 * ── AUTHORIZATION ────────────────────────────────────────────────────────────
 * `requireSuperAdmin()` — the same gate `/api/admin/*` uses. Releasing a sealed
 * health or mortality reading is the single most consequential act in this lane;
 * it gets the strictest role the app has.
 *
 * ── FLAG ─────────────────────────────────────────────────────────────────────
 * Gated on `PARIPRASHNA_SAFETY_GATE_ENABLED` like everything else in the lane.
 * With the flag OFF no review can exist to act on, so the endpoint answers 404:
 * this operation does not exist for this deploy.
 */

import { NextResponse } from 'next/server'

import { requireSuperAdmin } from '@/lib/auth/access-control'
import { res } from '@/lib/errors'

export const dynamic = 'force-dynamic'

type Action = 'record_pass' | 'sign_off' | 'withhold'

const ACTIONS: readonly Action[] = ['record_pass', 'sign_off', 'withhold'] as const

interface ReviewActionBody {
  review_id?: string
  action?: string
  /** record_pass only. */
  reviewer_model_id?: string
  reviewer_context_id?: string
  verdict?: string
  findings?: unknown
  /** withhold only. */
  reason?: string
}

const VERDICTS = ['refuted', 'sustained', 'sustained_with_reservations'] as const

/**
 * GET — read one review, or list the ones still awaiting a human.
 *
 * The list is the closest thing this lane has to a queue: `?pending=1` returns
 * the reviews in a non-terminal state, oldest first, so an operator can find the
 * work without knowing a `review_id` in advance. Without it, `?review_id=…`
 * returns one full record including its recorded passes.
 */
export async function GET(request: Request): Promise<Response> {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { isSafetyGateEnabled } = await import('@/lib/pariprashna/safety/flag')
  if (!isSafetyGateEnabled()) {
    return res.notFound('The Paripraśna safety review lifecycle is not enabled for this deploy.')
  }

  const url = new URL(request.url)
  const reviewId = url.searchParams.get('review_id')
  const { defaultSafetyDb } = await import('@/lib/pariprashna/safety/db')
  const db = defaultSafetyDb()

  try {
    if (reviewId) {
      const { loadReview } = await import('@/lib/pariprashna/safety/review_db')
      const review = await loadReview(db, reviewId)
      if (!review) return res.notFound('No such review.')
      const { isReleasable } = await import('@/lib/pariprashna/safety/review_machine')
      return NextResponse.json({ review, releasable: isReleasable(review) })
    }

    const { pendingReviews } = await import('@/lib/pariprashna/safety/review_db')
    return NextResponse.json({ pending: await pendingReviews(db) })
  } catch (err) {
    console.error('[pariprashna/safety/review] GET failed', err)
    return res.internal('Failed to load safety review.')
  }
}

/**
 * POST — drive one transition.
 *
 * Every legality question is answered by `review_machine.ts`, never here: this
 * handler loads the record, calls the pure transition, and persists what came
 * back. A transition this route refuses is a transition the MACHINE refused, so
 * the rules cannot drift between the HTTP surface and the unit tests that hold
 * them. A `SafetyReviewTransitionError` becomes a 409 with the machine's own
 * message — the caller learns exactly which rule stopped them (both passes not
 * in, a `refuted` verdict, a non-independent second pass), not a bare failure.
 */
export async function POST(request: Request): Promise<Response> {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth
  const actorId = auth.user.uid

  const { isSafetyGateEnabled } = await import('@/lib/pariprashna/safety/flag')
  if (!isSafetyGateEnabled()) {
    return res.notFound('The Paripraśna safety review lifecycle is not enabled for this deploy.')
  }

  let body: ReviewActionBody
  try {
    body = await request.json()
  } catch {
    return res.badRequest('Invalid JSON body')
  }

  const reviewId = body.review_id
  const action = body.action as Action | undefined
  if (!reviewId) return res.badRequest('review_id is required')
  if (!action || !ACTIONS.includes(action)) {
    return res.badRequest(`action must be one of: ${ACTIONS.join(', ')}`)
  }

  const { defaultSafetyDb } = await import('@/lib/pariprashna/safety/db')
  const { loadReview, persistReviewTransition } = await import('@/lib/pariprashna/safety/review_db')
  const { recordAdversarialPass, signOff, withhold, isReleasable, SafetyReviewTransitionError } =
    await import('@/lib/pariprashna/safety/review_machine')

  const db = defaultSafetyDb()
  const before = await loadReview(db, reviewId)
  if (!before) return res.notFound('No such review.')

  let after: typeof before
  try {
    if (action === 'record_pass') {
      const { reviewer_model_id, reviewer_context_id, verdict } = body
      if (!reviewer_model_id || !reviewer_context_id) {
        return res.badRequest('reviewer_model_id and reviewer_context_id are required')
      }
      if (!verdict || !(VERDICTS as readonly string[]).includes(verdict)) {
        return res.badRequest(`verdict must be one of: ${VERDICTS.join(', ')}`)
      }
      after = recordAdversarialPass(before, {
        reviewerModelId: reviewer_model_id,
        reviewerContextId: reviewer_context_id,
        verdict: verdict as (typeof VERDICTS)[number],
        // Findings are the substance of an adversarial pass, so they are
        // accepted as given and only shape-checked — never summarized or
        // rewritten by this route.
        findings: Array.isArray(body.findings) ? body.findings.map(String) : [],
      })
    } else if (action === 'sign_off') {
      // The signer is the AUTHENTICATED principal, never a body field. A
      // sign-off attributable to whoever the caller says they are is not a
      // sign-off (MP §3.5.C: "explicit native sign-off").
      after = signOff(before, { signedOffBy: actorId })
    } else {
      const reason = (body.reason ?? '').trim()
      if (!reason) return res.badRequest('reason is required to withhold a review')
      after = withhold(before, reason)
    }
  } catch (err) {
    if (err instanceof SafetyReviewTransitionError) {
      return NextResponse.json({ error: err.code, message: err.message }, { status: 409 })
    }
    console.error('[pariprashna/safety/review] transition failed', err)
    return res.internal('Failed to apply the review transition.')
  }

  try {
    // Compare-and-set on the PREVIOUS state inside `persistReviewTransition`:
    // two concurrent sign-offs cannot both land. A stale transition throws
    // rather than overwriting whatever is there now.
    await persistReviewTransition(db, before, after, actorId)
  } catch (err) {
    console.error('[pariprashna/safety/review] persist failed', err)
    return NextResponse.json(
      { error: 'SAFETY_REVIEW_PERSIST_FAILED', message: err instanceof Error ? err.message : String(err) },
      { status: 409 },
    )
  }

  return NextResponse.json({
    review: after,
    from_state: before.state,
    to_state: after.state,
    releasable: isReleasable(after),
    actor: actorId,
  })
}
