/**
 * fix_item3_spiritual_arc_correction.mts — D-4a Lane A-1 bug fix: ingest the item #3
 * ("Father's spiritual dialogues") correction that was wrongly skipped as "quarantined
 * pending native confirmation."
 *
 * BUG: BRIEF_D4A.md's own frontmatter already stated `item-#3-quarantine RESOLVED`, and
 * NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md's item #3 row is marked
 * `RESOLVED (native, 2026-07-19)`, not quarantined. The conductor incorrectly briefed the
 * original Lane A-1 pass to skip it. This script performs the append-only correction that
 * should have landed in that pass, following the identical pattern Lane A-1 used for its other
 * four corrections (item #2 congenital stammering, item #10 Mahadev/Shiva onset, item #7
 * sleep-disorder day-lock, item #13 relationship-end date):
 *
 *   - the ORIGINAL row (event_id d5db1b9a-b8c5-5b90-9641-c9ae9b1c2035, ~1997-2001 dialogues) is
 *     retained UNMODIFIED — append-only discipline, never delete/overwrite;
 *   - a NEW row is appended with event_id suffix `-corr-2001-initiation`, shape='interval'
 *     (spiritual_turn is canonically interval-shaped per EVENT_CLASS_ONTOLOGY_v1_0.md §3;
 *     validated below via validateClaimShape's logic), date_confidence='year_only',
 *     interval [2001-01-01 -> present (today, "till date" per native)],
 *     date_tightened_by_source='native_questionnaire_2026-07-19';
 *   - this new row is the ARC ROOT (milestone-1 / initiation) — chain_parent_event_id/
 *     milestone_label left NULL on the root itself, matching the item #1 (headaches) root-row
 *     precedent (event_id 64c475da-...), where the root also carries NULL chain fields and only
 *     its DEPENDENT milestones carry chain_parent_event_id + milestone_label;
 *   - the four later-milestone rows in the SAME arc that already exist live (item #6 Shani
 *     sadhana, item #10's CORRECTED Mahadev row, item #14 practice intensification, item #15
 *     mandala) get chain_parent_event_id + milestone_label added — an UPDATE of previously-NULL
 *     linkage columns only, not a rewrite of any substantive field (description/date/shape),
 *     mirroring the exact treatment item #5's peak_phase row (123eee97-...) already received in
 *     the original Lane A-1 pass.
 *
 * Uses a plain `pg` client rather than importing the app's db/client.ts — same
 * ERR_REQUIRE_CYCLE_MODULE avoidance rationale documented in
 * scripts/d4a/file_baseline_predictions.mts.
 *
 * Run with: node --import tsx/esm scripts/d4a/fix_item3_spiritual_arc_correction.mts
 * (DATABASE_URL must be set — see ../../.env.rag)
 */
import { Pool } from 'pg'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SOURCE = 'native_questionnaire_2026-07-19'
const SOURCE_CITATION = 'NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md (native-dictated, 2026-07-19)'
const SOURCE_SECTION = 'NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md (D-4a Lane A-1 correction backfill, 2026-07-19)'
const BUILD_ID = 'lel_v2_ingestion-D-4a-A-1'

const ORIGINAL_EVENT_ID = 'd5db1b9a-b8c5-5b90-9641-c9ae9b1c2035'
const NEW_EVENT_ID = `${ORIGINAL_EVENT_ID}-corr-2001-initiation`

// Later milestones in the same open-ended spiritual-journey arc, per item #3's correction text.
const CHAIN_MEMBERS: Array<{ event_id: string; milestone_label: string }> = [
  { event_id: '62f0460d-0cf1-5eab-bedc-47ecfcb04657', milestone_label: 'shani_sadhana_initiation' }, // item #6
  { event_id: '56a1222d-8c88-5445-b2a2-1fd89d470719-corr-2021-04', milestone_label: 'mahadev_adoption' }, // item #10 (corrected row)
  { event_id: '63e90113-eb35-5be4-9bce-1da7eda7d82d', milestone_label: 'practice_intensification' }, // item #14
  { event_id: '275b0c18-a159-5560-95f7-2a6cfbec58c4', milestone_label: 'mandala_formalization' }, // item #15
]

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

async function main() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')

    // 1. Confirm the original row exists and has not been touched.
    const orig = await client.query(
      `SELECT event_id, event_date, description FROM life_events WHERE chart_id = $1 AND event_id = $2`,
      [CHART_ID, ORIGINAL_EVENT_ID]
    )
    if (orig.rowCount !== 1) {
      throw new Error(`Original item #3 row ${ORIGINAL_EVENT_ID} not found live — aborting.`)
    }

    // 2. Guard against re-running (idempotency for this one-off script).
    const existing = await client.query(
      `SELECT 1 FROM life_events WHERE chart_id = $1 AND event_id = $2`,
      [CHART_ID, NEW_EVENT_ID]
    )
    if ((existing.rowCount ?? 0) > 0) {
      console.log(`Correction row ${NEW_EVENT_ID} already exists — skipping insert.`)
    } else {
      const description =
        "CORRECTION (native, 2026-07-19): 1997 is not correct. The late-night spiritual dialogues " +
        "with father did not begin ~1997 as originally recorded -- they began in 2001. That was the " +
        "INITIATION of the native's spiritual journey: \"the seeds were planted, and till date I am " +
        "on that journey.\" This row is milestone-1 (initiation) of an open-ended lifelong " +
        "spiritual-journey arc [2001 -> present], of which the following are LATER milestones in the " +
        "SAME arc (chain-linked via chain_parent_event_id): Shani sadhana initiation (~2002, event_id " +
        "62f0460d-0cf1-5eab-bedc-47ecfcb04657); Mahadev/Shiva adoption (2021-04/05, corrected event_id " +
        "56a1222d-8c88-5445-b2a2-1fd89d470719-corr-2021-04); practice intensification (~2024, event_id " +
        "63e90113-eb35-5be4-9bce-1da7eda7d82d); yantra mandala formalization (~2025-06, event_id " +
        "275b0c18-a159-5560-95f7-2a6cfbec58c4). Original row at event_id " +
        "d5db1b9a-b8c5-5b90-9641-c9ae9b1c2035 (recording the dialogues as ~1997-2001) is retained " +
        "unmodified per append-only discipline."

      const provenance = {
        native_quote:
          '1997 is not correct. The late-night discussions with my father started in 2001. That was ' +
          'the INITIATION of my spiritual journey — the seeds were planted, and till date I am on ' +
          'that journey.',
        correction_type: 'onset_date_correction_plus_chain_root',
        correction_source: 'NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md item #3',
        corrects_event_id: ORIGINAL_EVENT_ID,
        original_event_date: '1998-06-30',
        original_estimate_text: '~1997-2001',
        chain_role: 'root/milestone-1',
        chain_members: CHAIN_MEMBERS.map((m) => m.event_id),
      }

      const chartState = { dasha_ad: 'Venus', dasha_md: 'Saturn', key_transits: [] as unknown[] }

      await client.query(
        `INSERT INTO life_events
            (chart_id, event_id, event_date, event_type, description,
             domain, outcome_observed, source_citation, recorded_at,
             category, source_section, build_id, chart_state, provenance,
             shape, date_confidence, interval_start, interval_end,
             chain_parent_event_id, milestone_label,
             date_tightened_at, date_tightened_by_source,
             pool_consent, contributed_to_pool_at)
         VALUES
            ($1::uuid, $2, $3::date, $4, $5,
             $6, $7, $8, now(),
             $9, $10, $11, $12::jsonb, $13::jsonb,
             $14, $15, $16::date, $17::date,
             $18, $19,
             now(), $20,
             $21, $22)`,
        [
          CHART_ID,
          NEW_EVENT_ID,
          '2001-01-01',
          'spiritual',
          description,
          'spiritual/transmission',
          true,
          SOURCE_CITATION,
          'spiritual',
          SOURCE_SECTION,
          BUILD_ID,
          JSON.stringify(chartState),
          JSON.stringify(provenance),
          'interval',
          'year_only',
          '2001-01-01',
          '2026-07-19',
          null,
          null,
          SOURCE,
          false,
          null,
        ]
      )
      console.log(`Inserted correction row ${NEW_EVENT_ID}.`)
    }

    // 3. Chain-link the four later milestones that exist live (linkage-only UPDATE — no
    //    substantive field touched — mirroring item #5's peak_phase precedent).
    for (const member of CHAIN_MEMBERS) {
      const found = await client.query(
        `SELECT event_id, chain_parent_event_id, milestone_label FROM life_events
          WHERE chart_id = $1 AND event_id = $2`,
        [CHART_ID, member.event_id]
      )
      if (found.rowCount !== 1) {
        console.log(`  MILESTONE NOT FOUND LIVE: ${member.event_id} (${member.milestone_label}) — skipped.`)
        continue
      }
      const row = found.rows[0]
      if (row.chain_parent_event_id) {
        console.log(
          `  ${member.event_id} already chain-linked to ${row.chain_parent_event_id} — leaving untouched.`
        )
        continue
      }
      await client.query(
        `UPDATE life_events SET chain_parent_event_id = $1, milestone_label = $2
          WHERE chart_id = $3 AND event_id = $4`,
        [NEW_EVENT_ID, member.milestone_label, CHART_ID, member.event_id]
      )
      console.log(`  Chain-linked ${member.event_id} -> ${NEW_EVENT_ID} (${member.milestone_label}).`)
    }

    await client.query('COMMIT')
    console.log('Item #3 correction committed.')
  } catch (err) {
    await client.query('ROLLBACK')
    throw err
  } finally {
    client.release()
    await pool.end()
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
