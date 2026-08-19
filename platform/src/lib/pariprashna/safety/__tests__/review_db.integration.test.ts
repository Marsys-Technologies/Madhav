/**
 * Lane G1-A — THE HS-3/HS-4 REVIEW LIFECYCLE, AGAINST A REAL MIGRATED POSTGRES.
 *
 * Hardening-round items C-5, C-6 and C-7, proven where a mock cannot prove them.
 *
 * Follows the convention `samiksha/__tests__/ledger_db.integration.test.ts`
 * established for exactly this reason (the PB-2 false-confidence-gate lesson):
 * a DAL tested only against an in-memory double proves the writer agrees with
 * itself, not that the DATABASE accepts what it writes or rejects what it must.
 * Every claim below is one the in-memory `fake_db.ts` structurally cannot make —
 * CHECK constraints and append-only triggers do not exist in a fake.
 *
 * Gated on `PARIPRASHNA_SAFETY_TEST_DATABASE_URL`; SKIPPED when unset, which is
 * the normal case in CI (no DB). Run locally against a throwaway Postgres with
 * migration 577 applied. The run history for this round is in the lane report.
 *
 * WHAT THIS PROVES THAT THE UNIT TESTS DO NOT:
 *   · C-5 — `interstitial_shown` with a NULL `subject_kind` is REJECTED. The
 *     old constraint evaluated to NULL (not FALSE) on that row and Postgres
 *     accepted it, and a null subject_kind is TODAY'S DEFAULT.
 *   · C-6 — a `seal_pending_signoff` decision with `review_id IS NULL` is
 *     REJECTED, so the untracked-sealed-reading bug cannot regress.
 *   · C-7 — the whole lifecycle (open → pass 1 → pass 2 → sign-off → released)
 *     runs END TO END through the real DAL against real tables, at least once,
 *     driven the way a human at the admin endpoint drives it.
 */

import { randomUUID } from 'node:crypto'

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'

import { persistNewReview, persistReviewTransition, loadReview, pendingReviews } from '../review_db'
import { openReview, recordAdversarialPass, signOff, withhold, isReleasable } from '../review_machine'
import type { SafetyDb, SafetyQueryable } from '../types'

const DB_URL = process.env.PARIPRASHNA_SAFETY_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

run('the HS-3/HS-4 review lifecycle against a real migrated Postgres', () => {
  let pool: Pool
  let db: SafetyDb

  /**
   * A FRESH chart id per run, and fresh ids for everything below it.
   *
   * There is no cleanup in this file and there cannot be: every table it writes
   * is APPEND-ONLY by trigger (PPR-26), so `DELETE` is blocked — including on
   * `pariprashna_safety_review_passes`, which is what a first draft of this file
   * tried to do in `afterAll` and got an `APPEND_ONLY_VIOLATION` for. That is
   * the schema working as designed, so the isolation strategy has to be
   * "never collide" rather than "clean up afterwards". Hence per-run ids: this
   * file is re-runnable against the same throwaway database indefinitely.
   */
  const CHART = randomUUID()
  const uuid = (): string => randomUUID()

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    db = {
      async query<T>(sql: string, params?: unknown[]) {
        const r = await pool.query(sql, params as unknown[])
        return { rows: r.rows as T[] }
      },
      async withTransaction<T>(fn: (tx: SafetyQueryable) => Promise<T>): Promise<T> {
        const client = await pool.connect()
        try {
          await client.query('BEGIN')
          const tx: SafetyQueryable = {
            async query<R>(sql: string, params?: unknown[]) {
              const r = await client.query(sql, params as unknown[])
              return { rows: r.rows as R[] }
            },
          }
          const out = await fn(tx)
          await client.query('COMMIT')
          return out
        } catch (err) {
          await client.query('ROLLBACK')
          throw err
        } finally {
          client.release()
        }
      },
    }
  })

  afterAll(async () => {
    // No row cleanup — see the `CHART` comment above. Closing the pool is all
    // there is to do.
    if (pool) await pool.end()
  })

  // ── C-7 ───────────────────────────────────────────────────────────────────
  it('C-7 — runs seal → two independent passes → sign-off → released, end to end', async () => {
    const reviewId = uuid()
    const opened = openReview({
      reviewId, chartId: CHART, turnId: uuid(),
      classes: ['hs4_mortality_window'], subjectKind: 'cohort', interstitial: false,
    })
    expect(await persistNewReview(db, opened), 'the review row did not persist').toBe(true)

    // It shows up in the queue a human would read.
    const queue = await pendingReviews(db)
    expect(queue.some((r) => r.review_id === reviewId)).toBe(true)

    let current = await loadReview(db, reviewId)
    expect(current).not.toBeNull()
    expect(current!.state).toBe('seal_pending')
    expect(isReleasable(current!)).toBe(false)

    // Pass 1 — the shape `POST {action:'record_pass'}` produces.
    const afterP1 = recordAdversarialPass(current!, {
      reviewerModelId: 'model-a', reviewerContextId: 'ctx-1',
      verdict: 'sustained', findings: ['grounding thin on the dasha claim'],
    })
    await persistReviewTransition(db, current!, afterP1, 'operator-uid')
    current = await loadReview(db, reviewId)
    expect(current!.state).toBe('adversarial_pass_1_recorded')
    expect(current!.passes).toHaveLength(1)
    expect(isReleasable(current!)).toBe(false)

    // Pass 2 — a DIFFERENT (model, context), as independence requires.
    const afterP2 = recordAdversarialPass(current!, {
      reviewerModelId: 'model-b', reviewerContextId: 'ctx-2',
      verdict: 'sustained_with_reservations', findings: ['calibration overstated'],
    })
    await persistReviewTransition(db, current!, afterP2, 'operator-uid')
    current = await loadReview(db, reviewId)
    expect(current!.state).toBe('adversarial_passes_complete')
    expect(current!.passes).toHaveLength(2)
    // Two passes are NOT a release — the controls are never collapsed.
    expect(isReleasable(current!)).toBe(false)

    // The SEPARATE act.
    const released = signOff(current!, { signedOffBy: 'native-uid' })
    await persistReviewTransition(db, current!, released, 'native-uid')
    current = await loadReview(db, reviewId)
    expect(current!.state).toBe('released')
    expect(current!.signed_off_by).toBe('native-uid')
    expect(current!.signed_off_at).not.toBeNull()
    expect(isReleasable(current!)).toBe(true)

    // And it has left the queue.
    expect((await pendingReviews(db)).some((r) => r.review_id === reviewId)).toBe(false)

    // The append-only event history recorded every hop: opened + 3 transitions.
    const { rows } = await pool.query(
      `SELECT from_state, to_state, actor FROM pariprashna_safety_review_events
        WHERE review_id = $1 ORDER BY event_id ASC`,
      [reviewId],
    )
    expect(rows.map((r) => r.to_state)).toEqual([
      'seal_pending', 'adversarial_pass_1_recorded', 'adversarial_passes_complete', 'released',
    ])
  })

  it('C-7 — the DB independence constraint rejects a duplicated (model, context)', async () => {
    // The state machine refuses this in memory. This proves the DATABASE does
    // too, so a caller bypassing the machine cannot record one pass twice.
    const reviewId = uuid()
    const opened = openReview({
      reviewId, chartId: CHART, turnId: uuid(),
      classes: ['hs3_health_crisis'], subjectKind: 'cohort', interstitial: false,
    })
    await persistNewReview(db, opened)
    const insertPass = (ordinal: number) =>
      pool.query(
        `INSERT INTO pariprashna_safety_review_passes
           (review_id, pass_ordinal, reviewer_model_id, reviewer_context_id, verdict)
         VALUES ($1,$2,'same-model','same-ctx','sustained')`,
        [reviewId, ordinal],
      )
    await insertPass(1)
    await expect(insertPass(2)).rejects.toThrow(/independence/i)
  })

  it('C-7 — the withhold path persists, with its reason', async () => {
    const reviewId = uuid()
    const opened = openReview({
      reviewId, chartId: CHART, turnId: uuid(),
      classes: ['hs3_mental_health'], subjectKind: 'cohort', interstitial: false,
    })
    await persistNewReview(db, opened)
    const before = (await loadReview(db, reviewId))!
    const held = withhold(before, 'reader withdrew the question')
    await persistReviewTransition(db, before, held, 'operator-uid')
    const after = (await loadReview(db, reviewId))!
    expect(after.state).toBe('withheld')
    expect(after.withheld_reason).toBe('reader withdrew the question')
    expect(isReleasable(after)).toBe(false)
  })

  it('C-7 — a stale transition is REFUSED rather than overwriting current state', async () => {
    // The compare-and-set in `persistReviewTransition`. Two concurrent sign-offs
    // cannot both land.
    const reviewId = uuid()
    const opened = openReview({
      reviewId, chartId: CHART, turnId: uuid(),
      classes: ['hs4_mortality_window'], subjectKind: 'cohort', interstitial: false,
    })
    await persistNewReview(db, opened)
    const before = (await loadReview(db, reviewId))!
    const p1 = recordAdversarialPass(before, {
      reviewerModelId: 'm1', reviewerContextId: 'c1', verdict: 'sustained', findings: [],
    })
    await persistReviewTransition(db, before, p1, 'operator-uid')

    // Replay the SAME transition from the now-stale `before` snapshot.
    await expect(persistReviewTransition(db, before, p1, 'operator-uid')).rejects.toThrow(
      /SAFETY_REVIEW_STALE_TRANSITION/,
    )
  })

  // ── C-5 ───────────────────────────────────────────────────────────────────
  it('C-5 — interstitial_shown with a NULL subject_kind is REJECTED by the DB', async () => {
    // The exact row the old constraint accepted, because `NULL = 'native_self'`
    // is NULL and Postgres accepts a CHECK that evaluates to NULL. And a null
    // subject_kind is the DEFAULT whenever consent enforcement is off.
    await expect(
      pool.query(
        `INSERT INTO pariprashna_safety_reviews (review_id, chart_id, turn_id, state, classes, subject_kind)
         VALUES ($1,$2,$3,'interstitial_shown',ARRAY['hs3_health_crisis'],NULL)`,
        [uuid(), CHART, uuid()],
      ),
    ).rejects.toThrow(/interstitial_is_native_self/)
  })

  it('C-5 — interstitial_shown for a COHORT subject is REJECTED (unchanged)', async () => {
    await expect(
      pool.query(
        `INSERT INTO pariprashna_safety_reviews (review_id, chart_id, turn_id, state, classes, subject_kind)
         VALUES ($1,$2,$3,'interstitial_shown',ARRAY['hs3_health_crisis'],'cohort')`,
        [uuid(), CHART, uuid()],
      ),
    ).rejects.toThrow(/interstitial_is_native_self/)
  })

  it('C-5 — interstitial_shown for a PROVEN native_self is ACCEPTED', async () => {
    // The floor: the constraint must still permit the case NCD-4 exists for.
    await expect(
      pool.query(
        `INSERT INTO pariprashna_safety_reviews (review_id, chart_id, turn_id, state, classes, subject_kind)
         VALUES ($1,$2,$3,'interstitial_shown',ARRAY['hs3_health_crisis'],'native_self')`,
        [uuid(), CHART, uuid()],
      ),
    ).resolves.toBeTruthy()
  })

  // ── C-6 ───────────────────────────────────────────────────────────────────
  //
  // Each decision insert uses its OWN chart_id at seq 1 with a NULL prev_hash.
  // Two reasons, both real constraints of this table rather than test taste:
  //   · `..._genesis_chk` requires seq = 1 ⇔ prev_hash IS NULL, so an arbitrary
  //     high seq fails on the WRONG constraint and would have made these tests
  //     pass for the wrong reason (they did, on the first run of this file);
  //   · `..._seq_uq` is UNIQUE (chart_id, seq), so a per-case chart keeps the
  //     cases independent of each other and of execution order.
  //
  // NOTE there is no cleanup for these rows: `pariprashna_safety_decisions` is
  // APPEND-ONLY by trigger — DELETE is blocked, by design (PPR-26). This file is
  // meant for a throwaway database, which the header says.
  const decisionInsert = (args: {
    chart: string
    action: string
    classes: string
    severity: string
    reviewId: string | null
    hash: string
  }): Promise<unknown> =>
    pool.query(
      `INSERT INTO pariprashna_safety_decisions
         (decision_id, chart_id, turn_id, seq, enforced, classes_detected, severity, action, review_id, prev_hash, entry_hash)
       VALUES (gen_random_uuid(),$1,gen_random_uuid(),1,true,${args.classes},$2,$3,$4,NULL,$5)`,
      [args.chart, args.severity, args.action, args.reviewId, args.hash],
    )

  it('C-6 — a sealed decision with NO review_id is REJECTED by the DB', async () => {
    await expect(
      decisionInsert({
        chart: uuid(), action: 'seal_pending_signoff',
        classes: `ARRAY['hs4_mortality_window']`, severity: 'review_required',
        reviewId: null, hash: 'a'.repeat(64),
      }),
    ).rejects.toThrow(/seal_requires_review/)
  })

  it('C-6 — an interstitial decision with NO review_id is REJECTED by the DB', async () => {
    await expect(
      decisionInsert({
        chart: uuid(), action: 'interstitial',
        classes: `ARRAY['hs3_health_crisis']`, severity: 'review_required',
        reviewId: null, hash: 'b'.repeat(64),
      }),
    ).rejects.toThrow(/seal_requires_review/)
  })

  it('C-6 — hard_stop with NO review_id is ACCEPTED (HS-2 opens none)', async () => {
    // The floor in the other direction: HS-2 composes no reading at all, so
    // requiring a review of it would be wrong.
    await expect(
      decisionInsert({
        chart: uuid(), action: 'hard_stop',
        classes: `ARRAY['hs2_suicide_adjacent']`, severity: 'hard_stop',
        reviewId: null, hash: 'c'.repeat(64),
      }),
    ).resolves.toBeTruthy()
  })

  it('C-6 — proceed with NO review_id is ACCEPTED (the overwhelmingly common row)', async () => {
    await expect(
      decisionInsert({
        chart: uuid(), action: 'proceed',
        classes: `ARRAY[]::text[]`, severity: 'none',
        reviewId: null, hash: 'd'.repeat(64),
      }),
    ).resolves.toBeTruthy()
  })

  it('C-6 — a sealed decision WITH a review_id is ACCEPTED', async () => {
    await expect(
      decisionInsert({
        chart: uuid(), action: 'seal_pending_signoff',
        classes: `ARRAY['hs4_mortality_window']`, severity: 'review_required',
        reviewId: uuid(), hash: 'e'.repeat(64),
      }),
    ).resolves.toBeTruthy()
  })
})
