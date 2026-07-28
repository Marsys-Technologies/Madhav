/**
 * SAMĪKṢĀ E2E — candidate → confirm → REAL ledger row — PB-3 lane L-2.
 *
 * The lane's headline acceptance criterion, exercised end-to-end for REAL:
 *   a fixture turn with a time-indexed claim
 *     → the REAL detector emits a structured candidate
 *     → it is persisted as a REAL PB-2 `prediction_candidate` message_part
 *       (via the shipped store `writeTurn`)
 *     → the REAL confirm flow copies the D-16 stamp (real `getLastTurnStamp`) and
 *       writes the L-1 ledger row (real L-1 `createLedgerRow`)
 *     → a REAL ledger row exists, `confirmed`, stamp COPIED, and its
 *       `message_part_id` RESOLVES back to the originating message_part.
 *
 * NOT a mock of the detector/DAL agreeing with itself (the PB-2 false-confidence-
 * gate lesson): every step runs against a REAL throwaway Postgres with migrations
 * 467 (message_parts) + 470 (ledger) actually applied. Gated on
 * SAMIKSHA_E2E_DATABASE_URL; skipped when absent (CI has no DB).
 *
 * Run locally:
 *   SAMIKSHA_E2E_DATABASE_URL=postgres://... \
 *     npx vitest run tests/pariprashna/samiksha/confirm_e2e.db.test.ts
 */

// Point the shared DB client at the throwaway DB BEFORE any query runs (the pool
// is created lazily on first query; this top-level assignment precedes all tests).
const E2E_URL = process.env.SAMIKSHA_E2E_DATABASE_URL
if (E2E_URL) process.env.DATABASE_URL = E2E_URL

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { randomUUID } from 'node:crypto'
import { query } from '@/lib/db/client'
import { writeTurn } from '@/lib/pariprashna/store/writer'
import { detectStructuredCandidatesSync } from '@/lib/pariprashna/samiksha/detector'
import { confirmCandidate, dismissCandidate } from '@/lib/pariprashna/samiksha/confirm'
import { getLedgerRow } from '@/lib/pariprashna/samiksha/reader'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'

const run = E2E_URL ? describe : describe.skip

const CHART = '482012f1-710e-4a25-994a-93821f5871aa' // canonical chart
const CONVERSATION_ID = randomUUID()
const MESSAGE_ID = randomUUID()

const STAMP: TurnProvenanceStamp = {
  build_id: 'bf2ea4ce-0000-0000-0000-000000000001',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-07-28',
  computed_at: '2026-07-28T10:43:00.000Z',
}

const TURN_TEXT =
  'Reading the tenth house and its lord: An occupational shift, self-initiated, is ' +
  'likely around mid-2027, most probably during the Saturn dasha, with roughly a 70% ' +
  'chance. This is a genuine, time-indexed claim the instrument stands behind.'

run('SAMĪKṢĀ candidate → confirm → ledger (real DB, real DAL)', () => {
  beforeAll(async () => {
    // Idempotent DDL — mirrors migration 467 (message_parts) + 470 (ledger) so the
    // test is self-contained against a bare Postgres.
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
      chart_id uuid NOT NULL, message_part_id uuid REFERENCES message_parts(id),
      claim_text text NOT NULL, domain text, "window" daterange, confidence numrange, direction text,
      technique_refs text[] NOT NULL DEFAULT '{}', grounding_fact_ids text[] NOT NULL DEFAULT '{}',
      created_from_channel text NOT NULL DEFAULT 'pariprashna',
      lifecycle_status text NOT NULL DEFAULT 'detected',
      build_id text, priors_version text, formula_versions jsonb, ranking_config jsonb,
      now_context_date date, stamp_copied_at timestamptz,
      outcome text, outcome_value numeric, outcome_note text, outcome_recorded_at timestamptz,
      confirmed_at timestamptz, dismissed_reason text,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now())`)

    // Clean any prior run artifacts.
    await query('DELETE FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1', [CHART])
    await query('DELETE FROM message_parts WHERE message_id = $1', [MESSAGE_ID])
    await query('DELETE FROM conversation_messages WHERE conversation_id = $1', [CONVERSATION_ID])
  })

  afterAll(async () => {
    if (!E2E_URL) return
    await query('DELETE FROM brahma_mimamsa_prediction_ledger WHERE chart_id = $1', [CHART])
    await query('DELETE FROM message_parts WHERE message_id = $1', [MESSAGE_ID])
    await query('DELETE FROM conversation_messages WHERE conversation_id = $1', [CONVERSATION_ID])
  })

  it('detects a structured candidate, persists it as a message_part, confirms it to a resolving ledger row', async () => {
    // 1) Persist the assistant turn (with the D-16 stamp in metadata_json) + the
    //    prediction_candidate part — via the REAL PB-2 store writer.
    const detected = detectStructuredCandidatesSync({
      text: TURN_TEXT,
      citations: [{ signal_id: 'SIG.DASHA.SAT', layer: 'L3' }],
      nowDate: '2026-07-28',
    })
    expect(detected.length).toBeGreaterThanOrEqual(1)
    const candidate = detected[0]
    expect(candidate.claim_text).toMatch(/occupational shift/)
    expect(candidate.domain).toBe('career')
    expect(candidate.window_start).toBe('2027-05-01')
    expect(candidate.window_end).toBe('2027-09-01')

    await writeTurn(
      {
        id: MESSAGE_ID,
        conversation_id: CONVERSATION_ID,
        role: 'assistant',
        schema_version: 1,
        model_id: 'claude-opus-4-8[1m]',
        provider: 'anthropic',
        metadata: { provenance_stamp: STAMP }, // getLastTurnStamp reads this back
      },
      [
        { seq: 0, kind: 'text', body: { text: TURN_TEXT }, model_visible: true },
        {
          seq: 1,
          kind: 'prediction_candidate',
          body: { claim: candidate.claim_text, window: candidate.horizon_text ?? undefined, confidence: candidate.score, source_flag_code: 'prediction_candidate' },
          model_visible: false,
        },
      ],
    )

    // Fetch the real message_part id the candidate first appeared on.
    const partRes = await query<{ id: string }>(
      `SELECT id FROM message_parts WHERE message_id = $1 AND kind = 'prediction_candidate'`,
      [MESSAGE_ID],
    )
    expect(partRes.rows.length).toBe(1)
    const messagePartId = partRes.rows[0].id

    // 2) Confirm — REAL confirm flow: real getLastTurnStamp copy + real L-1 DAL write.
    const row = await confirmCandidate({
      chart_id: CHART,
      conversation_id: CONVERSATION_ID,
      message_part_id: messagePartId,
      candidate,
      confidence: { low: 0.6, high: 0.8 }, // the slider-elicited numrange band
    })

    // 3) The ledger row is real, confirmed, stamp COPIED (not joined), claim mapped.
    expect(row.lifecycle_status).toBe('confirmed')
    expect(row.chart_id).toBe(CHART)
    expect(row.message_part_id).toBe(messagePartId)
    expect(row.claim_text).toMatch(/occupational shift/)
    expect(row.domain).toBe('career')
    expect(row.window).toBe('[2027-05-01,2027-09-01)')
    expect(row.confidence).toBe('[0.6,0.8)')
    expect(row.created_from_channel).toBe('pariprashna')
    // D-16(d): the five stamp fields are COPIED verbatim onto the row.
    expect(row.build_id).toBe(STAMP.build_id)
    expect(row.priors_version).toBe('priors_v7')
    expect(row.now_context_date).toBe('2026-07-28')
    expect(row.stamp_copied_at).not.toBeNull()
    expect(row.grounding_fact_ids).toEqual(['SIG.DASHA.SAT'])
    expect(row.technique_refs).toContain('vimshottari_dasha')

    // 4) message_part_id RESOLVES back to the originating part (the FK is real).
    const resolved = await query<{ id: string; kind: string; message_id: string }>(
      `SELECT mp.id, mp.kind, mp.message_id
         FROM brahma_mimamsa_prediction_ledger l
         JOIN message_parts mp ON mp.id = l.message_part_id
        WHERE l.id = $1`,
      [row.id],
    )
    expect(resolved.rows.length).toBe(1)
    expect(resolved.rows[0].kind).toBe('prediction_candidate')
    expect(resolved.rows[0].message_id).toBe(MESSAGE_ID)

    // And the row is genuinely readable back via L-1's reader.
    const readback = await getLedgerRow(row.id)
    expect(readback?.message_part_id).toBe(messagePartId)
  })

  it('confirm without a provenance stamp is REFUSED (no silent zero-stamp row)', async () => {
    const bareConversation = randomUUID()
    const [candidate] = detectStructuredCandidatesSync({ text: TURN_TEXT, nowDate: '2026-07-28' })
    await expect(
      confirmCandidate({
        chart_id: CHART,
        conversation_id: bareConversation, // no assistant turn / no stamp
        candidate,
        confidence: { low: 0.6, high: 0.8 },
      }),
    ).rejects.toThrow(/no provenance stamp/i)
  })

  it('dismiss-with-reason persists the dismissal reason via L-1 DAL', async () => {
    const [candidate] = detectStructuredCandidatesSync({ text: TURN_TEXT, nowDate: '2026-07-28' })
    const row = await dismissCandidate({
      chart_id: CHART,
      candidate,
      reason: 'not a prediction — a description of the technique, not a claim',
    })
    expect(row.lifecycle_status).toBe('dismissed')
    expect(row.dismissed_reason).toMatch(/not a prediction/)
    const readback = await getLedgerRow(row.id)
    expect(readback?.dismissed_reason).toMatch(/not a prediction/)
  })
})
