/**
 * SAMĪKṢĀ turn-commit capture — PB-3.1 **G1** live-entry-point E2E.
 *
 * The exact production sequence `/api/pariprashna`'s `writeMessages` closure now performs,
 * driven through the REAL shipped functions in the REAL order, against a REAL Postgres:
 *
 *   the REAL Stage-1 detector (`detectPredictionCandidates`) on real assistant prose
 *     → the REAL store writer (`writeTurn`) persists the `prediction_candidate` parts
 *     → the REAL capture (`captureDetectedCandidates`) writes `detected` ledger rows
 *     → the REAL review-surface read (`getReviewData`) returns them in `awaiting`
 *        with a resolving deep-link anchor
 *     → the REAL review-tab confirm (`confirmDetectedCandidate`) advances
 *        detected → confirmed → open, with the D-16 stamp COPIED
 *     → the REAL daily job's own selector sees the row as `open`
 *
 * That chain is the whole of what `REPORT_PB-3.md` recorded as FAIL ("ledger = 0 rows on every
 * chart... detection runs; nothing carries its output forward"). Nothing here is mocked: no
 * fake DAL, no hand-inserted row, no test double asserting a function was called. The one thing
 * this file CANNOT prove is A1 itself — that the DEPLOYED route runs this chain on production.
 * That proof is a live reading against the deployed app, psql-verified; see the PR body.
 *
 * Gated on SAMIKSHA_E2E_DATABASE_URL (CI has no DB until PB-3.1 G3 wires one — lane A5).
 *
 * Run locally:
 *   SAMIKSHA_E2E_DATABASE_URL=postgres://... \
 *     npx vitest run tests/pariprashna/samiksha/capture_turn_commit.db.test.ts
 */

// Point the shared DB client at the throwaway DB BEFORE any query runs (the pool is created
// lazily on first query; this top-level assignment precedes all tests).
const E2E_URL = process.env.SAMIKSHA_E2E_DATABASE_URL
if (E2E_URL) process.env.DATABASE_URL = E2E_URL

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { randomUUID } from 'node:crypto'
import { query } from '@/lib/db/client'
import { writeTurn } from '@/lib/pariprashna/store/writer'
import {
  textPartFromBlock,
  predictionCandidatePartFromDetection,
} from '@/lib/pariprashna/store/route_writer_adapter'
import type { MessagePartInput } from '@/lib/pariprashna/store/schema'
import { CANONICAL_SCHEMA_VERSION } from '@/lib/pariprashna/store/schema'
import { detectPredictionCandidates } from '@/lib/ppl/prediction_detector'
import { captureDetectedCandidates } from '@/lib/pariprashna/samiksha/capture'
import { getReviewData } from '@/lib/pariprashna/samiksha/review'
import { confirmDetectedCandidate } from '@/lib/pariprashna/samiksha/reviewConfirm'
import { runDailyJob } from '@/lib/pariprashna/samiksha/daily_job'
import { InMemoryDigestJournal } from '@/lib/pariprashna/samiksha/digest_journal'
import { RecordingTransport } from '@/lib/pariprashna/samiksha/digest'
import type { LedgerStamp } from '@/lib/pariprashna/samiksha/schema'

const run = E2E_URL ? describe : describe.skip

/**
 * An ISOLATED synthetic chart scope, not the canonical chart. `confirm_e2e.db.test.ts` uses the
 * canonical id and clears ALL of that chart's ledger rows in its own beforeAll/afterAll; vitest
 * runs test FILES in parallel, so sharing the id makes the two files race and fail each other
 * intermittently. (That pre-existing isolation hazard is invisible today only because both files
 * are env-gated and permanently skipped in CI — PB-3.1 G3 / lane A5. Reported as a residual.)
 */
const CHART = '11111111-2222-3333-4444-5555555540c1'
const CONVERSATION_ID = randomUUID()
const MESSAGE_ID = randomUUID()
const NOW_DATE = '2026-07-30'

/** The D-16 stamp the review-tab confirm copies (resolved live by the real caller). */
const STAMP: LedgerStamp = {
  build_id: 'bf2ea4ce-0000-0000-0000-000000000001',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: NOW_DATE,
}

/**
 * Real assistant prose of the kind the instrument actually produces. Deliberately contains
 * TWO claims that clear the route's live `score >= 0.5` filter (so pairing is exercised on more
 * than one row) plus a historical sentence that carries a year but no prediction verb — the
 * detector scores that one 0.45, so it must be filtered out and never reach the ledger.
 */
const TURN_TEXT = [
  'Reading the tenth house and its lord together with the running dasha:',
  'An occupational shift, self-initiated rather than imposed, is likely around mid-2027,',
  'most probably during the Saturn antardasha.',
  'A relocation of the household is likely in the next 18 months.',
  'He was born in Bhubaneswar in 1984, which is context rather than prediction.',
].join(' ')

async function ensureSchema() {
  // Idempotent DDL mirroring migration 467 (message_parts) + 470 (ledger) so the test is
  // self-contained against a bare Postgres. When the real migrations are already applied
  // (the preferred local setup), every statement here is a no-op.
  await query(`CREATE TABLE IF NOT EXISTS conversation_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    conversation_id uuid NOT NULL, parent_message_id uuid, role text NOT NULL,
    parts_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL)`)
  await query(`ALTER TABLE conversation_messages
    ADD COLUMN IF NOT EXISTS schema_version int,
    ADD COLUMN IF NOT EXISTS model_id text, ADD COLUMN IF NOT EXISTS provider text`)
  await query(`CREATE TABLE IF NOT EXISTS message_parts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id uuid NOT NULL REFERENCES conversation_messages(id),
    seq int NOT NULL,
    kind text NOT NULL CHECK (kind IN ('text','reasoning','tool_call','tool_result','citation','prediction_candidate','attachment')),
    body jsonb NOT NULL, model_visible boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now())`)
  await query(`CREATE UNIQUE INDEX IF NOT EXISTS idx_message_parts_message_seq ON message_parts(message_id, seq)`)
  await query(`CREATE TABLE IF NOT EXISTS brahma_mimamsa_prediction_ledger (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    -- ON DELETE SET NULL per migration 474: a turn rewrite must drop the anchor, never the claim.
    chart_id uuid NOT NULL, message_part_id uuid REFERENCES message_parts(id) ON DELETE SET NULL,
    claim_text text NOT NULL, domain text, "window" daterange, confidence numrange, direction text,
    technique_refs text[] NOT NULL DEFAULT '{}', grounding_fact_ids text[] NOT NULL DEFAULT '{}',
    created_from_channel text NOT NULL DEFAULT 'pariprashna',
    lifecycle_status text NOT NULL DEFAULT 'detected'
      CHECK (lifecycle_status IN ('detected','confirmed','open','window_closed','outcome_recorded',
                                  'dismissed','lapsed','unverifiable','lapsed_unconfirmed')),
    build_id text, priors_version text, formula_versions jsonb, ranking_config jsonb,
    now_context_date date, stamp_copied_at timestamptz,
    outcome text, outcome_value numeric, outcome_note text, outcome_recorded_at timestamptz,
    confirmed_at timestamptz, dismissed_reason text,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT bmpl_unverifiable_has_no_value
      CHECK (outcome IS DISTINCT FROM 'unverifiable' OR outcome_value IS NULL))`)
}

async function cleanup() {
  await query('DELETE FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1', [CHART])
  await query('DELETE FROM message_parts WHERE message_id = $1', [MESSAGE_ID])
  await query('DELETE FROM conversation_messages WHERE conversation_id = $1', [CONVERSATION_ID])
}

/** Replays the route's own part-assembly + capture, verbatim in shape. */
async function commitTurnAsRouteDoes() {
  const candidates = detectPredictionCandidates(TURN_TEXT).filter((c) => c.score >= 0.5)

  const parts: MessagePartInput[] = []
  let seq = 0
  parts.push(textPartFromBlock({ block_id: 'b1', text: TURN_TEXT }, seq++))
  for (const c of candidates) {
    parts.push(predictionCandidatePartFromDetection({ text: c.text, score: c.score, horizon: c.horizon }, seq++))
  }

  await writeTurn(
    {
      id: MESSAGE_ID,
      conversation_id: CONVERSATION_ID,
      role: 'assistant',
      schema_version: CANONICAL_SCHEMA_VERSION,
      model_id: 'claude-sonnet-5',
      provider: 'anthropic',
      metadata: {},
    },
    parts,
  )

  return {
    candidates,
    capture: await captureDetectedCandidates({
      chartId: CHART,
      messageId: MESSAGE_ID,
      candidates,
      citations: [{ signal_id: 'SIG.MSR.101', layer: 'L2.5' }],
      nowDate: NOW_DATE,
    }),
  }
}

run('PB-3.1 G1 — a committed turn writes `detected` rows and the loop runs from there', () => {
  beforeAll(async () => {
    await ensureSchema()
    await query(
      `INSERT INTO conversation_messages (id, conversation_id, role, metadata_json)
       VALUES ($1, $2, 'user', '{}'::jsonb) ON CONFLICT (id) DO NOTHING`,
      [randomUUID(), CONVERSATION_ID],
    )
    await cleanup()
  })

  afterAll(async () => {
    if (!E2E_URL) return
    await cleanup()
  })

  it('the real detector + real writeTurn + real capture produce `detected` rows with resolving FKs', async () => {
    const { candidates, capture } = await commitTurnAsRouteDoes()

    // The prose really does yield two time-indexed candidates and drops the historical one.
    expect(candidates.length).toBe(2)
    expect(capture.unpaired).toBe(0)
    expect(capture.skippedExisting).toBe(0)
    expect(capture.created.length).toBe(2)

    for (const row of capture.created) {
      expect(row.lifecycle_status).toBe('detected')
      // W-1: born with NO stamp and NO confidence band — the human supplies both at confirm.
      expect(row.confirmed_at).toBeNull()
      expect(row.stamp_copied_at).toBeNull()
      expect(row.confidence).toBeNull()
      expect(row.created_from_channel).toBe('pariprashna')
      expect(row.grounding_fact_ids).toContain('SIG.MSR.101')

      // The FK resolves back to a real `prediction_candidate` part of THIS turn.
      const { rows } = await query<{ kind: string; message_id: string }>(
        'SELECT kind, message_id FROM message_parts WHERE id = $1',
        [row.message_part_id],
      )
      expect(rows[0]?.kind).toBe('prediction_candidate')
      expect(rows[0]?.message_id).toBe(MESSAGE_ID)
    }

    // The deterministic enrichment resolved the mid-2027 window from the prose.
    const shift = capture.created.find((r) => /occupational shift/.test(r.claim_text))
    expect(shift).toBeDefined()
    expect(shift!.domain).toBe('career')
    expect(shift!.window).toBe('[2027-05-01,2027-09-01)')
  })

  it('the capture is re-entrant — running it again on the same committed turn writes no duplicates', async () => {
    // The reachable re-entrancy case: the turn's parts are already committed and unchanged, and
    // the capture runs a second time (an onFinish retry). It must find every part already
    // ledgered and write nothing.
    const before = await query<{ n: string }>(
      'SELECT count(*)::text AS n FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1',
      [CHART],
    )

    const again = await captureDetectedCandidates({
      chartId: CHART,
      messageId: MESSAGE_ID,
      candidates: detectPredictionCandidates(TURN_TEXT).filter((c) => c.score >= 0.5),
      citations: [{ signal_id: 'SIG.MSR.101', layer: 'L2.5' }],
      nowDate: NOW_DATE,
    })

    const after = await query<{ n: string }>(
      'SELECT count(*)::text AS n FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1',
      [CHART],
    )

    expect(again.created.length).toBe(0)
    expect(again.skippedExisting).toBe(2)
    expect(again.unpaired).toBe(0)
    expect(after.rows[0].n).toBe(before.rows[0].n)
  })

  it('a turn REWRITE cannot cost the reader their turn, nor delete a captured claim (migration 474)', async () => {
    // Before migration 474 this exact sequence raised
    //   'update or delete on table "message_parts" violates foreign key constraint ...'
    // from writeTurn's DELETE-then-INSERT, aborting the whole turn write. With ON DELETE SET
    // NULL the rewrite succeeds and the human-owned claim survives with its anchor dropped —
    // the documented, renderable null-anchor state, not a lost prediction.
    const idsBefore = await query<{ id: string; claim_text: string }>(
      'SELECT id, claim_text FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1 ORDER BY id',
      [CHART],
    )
    expect(idsBefore.rows.length).toBe(2)

    await expect(commitTurnAsRouteDoes()).resolves.toBeDefined()

    const idsAfter = await query<{ id: string; message_part_id: string | null }>(
      'SELECT id, message_part_id FROM brahma_mimamsa_prediction_ledger WHERE id = ANY($1::uuid[]) ORDER BY id',
      [idsBefore.rows.map((r) => r.id)],
    )
    // Every original claim still exists...
    expect(idsAfter.rows.length).toBe(2)
    // ...with its anchor nulled rather than the row destroyed.
    expect(idsAfter.rows.every((r) => r.message_part_id === null)).toBe(true)

    // Clean the rows the rewrite's re-capture produced, so the later cases see a known state.
    await query(
      'DELETE FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1 AND message_part_id IS NULL',
      [CHART],
    )
  })

  it('the rows render in the review tab’s Awaiting section with a resolving turn anchor', async () => {
    const review = await getReviewData(CHART)

    expect(review.awaiting.length).toBe(2)
    expect(review.coverage.awaitingCount).toBe(2)
    // `AwaitingSection` shows the ProbabilitySlider only when the row has no band yet.
    expect(review.awaiting.every((r) => r.confidence === null)).toBe(true)
    // The deep-link anchor the Awaiting row's "view source turn" link needs.
    for (const r of review.awaiting) {
      expect(review.turnAnchors[r.message_part_id!]).toMatchObject({
        chartId: CHART,
        conversationId: CONVERSATION_ID,
      })
    }
  })

  it('a human confirm advances detected → confirmed → open, stamp copied, and the daily job then sees it', async () => {
    const review = await getReviewData(CHART)
    const target = review.awaiting.find((r) => /occupational shift/.test(r.claim_text))!

    const opened = await confirmDetectedCandidate({ rowId: target.id, probability: 0.7, stamp: STAMP })

    expect(opened.lifecycle_status).toBe('open')
    // The shipped `probabilityToBand(0.7)` is plain float arithmetic (0.7 - 0.05), so the
    // numrange literal carries the IEEE-754 residue verbatim. Asserted as-is rather than
    // rounded — the band the DB really holds is the band the Brier score will really use.
    expect(opened.confidence).toBe('[0.6499999999999999,0.75)')
    expect(opened.confirmed_at).not.toBeNull()
    expect(opened.stamp_copied_at).not.toBeNull()
    expect(opened.priors_version).toBe('priors_v7')
    expect(opened.now_context_date).toBe(NOW_DATE)

    // The L-4 daily job — the loop's EXIT half, previously starved because nothing was ever
    // `open` — now has a real row to act on. Run the REAL job, not a re-implemented predicate.
    const duringWindow = await runDailyJob({
      asOf: NOW_DATE,
      chartId: CHART,
      journal: new InMemoryDigestJournal(),
      transport: new RecordingTransport(),
    })
    expect(duringWindow.closed_row_ids).not.toContain(opened.id) // window still running

    const afterWindow = await runDailyJob({
      asOf: '2027-10-01',
      chartId: CHART,
      journal: new InMemoryDigestJournal(),
      transport: new RecordingTransport(),
    })
    expect(afterWindow.closed_row_ids).toContain(opened.id)

    // And it lands in the Resolve section, where a human records the outcome.
    const afterClose = await getReviewData(CHART)
    expect(afterClose.resolvable.map((r) => r.id)).toContain(opened.id)
  })
})
