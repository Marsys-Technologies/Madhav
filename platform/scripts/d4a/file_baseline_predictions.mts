/**
 * file_baseline_predictions.mts — D-4a Lane A-4: file the initial live prospective-ledger
 * entries against chart 482012f1.
 *
 * NOTE on why this script uses a plain `pg` client instead of importing
 * `fileProspectivePrediction` from platform/src/lib/lel/prospective_ledger.ts directly:
 * a live import probe during this lane's work found that ANY module in the
 * `src/lib/db` -> `src/lib/lel` chain (even `db/client.ts` alone, with zero
 * D-4a-authored code involved) throws `ERR_REQUIRE_CYCLE_MODULE` when executed via
 * plain `node --conditions=react-server --import tsx/esm` outside the Next.js
 * bundler — a Node 24 require(esm)-interop quirk with this repo's 'pg' + path-alias
 * setup, pre-existing and unrelated to this lane's changes (confirmed: importing
 * `src/lib/db/client.ts` alone, untouched by this lane, reproduces the identical
 * error). `npx tsc --noEmit`, `eslint`, and the vitest suite (which runs under a
 * different module loader, jsdom/vitest's own Vite-based transform) all pass clean
 * against the real module — see prospective_ledger.test.ts. This script therefore
 * talks to Postgres directly, issuing THE SAME SQL fileProspectivePrediction issues
 * (verified by diff against prospective_ledger.ts's INSERT statement), so it is a
 * faithful exercise of the schema/constraints, not a bypass of them — and the DB-level
 * trigger (migration 458 §3) enforces claim_shape correctness regardless of which
 * path writes the row.
 *
 * Run with: node --import tsx/esm scripts/d4a/file_baseline_predictions.mts
 * (DATABASE_URL must be set — see ../../.env.rag)
 */
import { Pool } from 'pg'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

interface Entry {
  claim: string
  event_class: string
  claim_shape: 'point' | 'interval' | 'chain'
  observation_window: string | null // Postgres daterange literal
  milestone_set: unknown[] | null
  model: string
  formula_version: string
  confidence: number
  falsifier: string
  generator_class: 'anchor_engine' | 'reading_synthesis' | 'engine' | 'native_intuition'
  filed_by: string
  source_citation: string
}

const ENTRIES: Entry[] = [
  // 1. Sat-Jup pratyantar wealth window (named baseline-arc prediction #1)
  {
    claim:
      'Saturn-Jupiter pratyantar dasha convergence (2027-04-09 -> 2027-08-18) elevates wealth-domain ' +
      'gain likelihood for the native.',
    event_class: 'major_gain',
    claim_shape: 'interval',
    observation_window: '[2027-04-09,2027-08-18]',
    milestone_set: null,
    model: 'dasha_lord_confluence_v1 (Saturn-Jupiter pratyantar convergence, wealth-domain reading synthesis)',
    formula_version: 'wealth-baseline-arc-v1',
    confidence: 0.55,
    falsifier:
      'No major_gain-class LEL event (externally verifiable per major_gain.evidence_requirements: bank ' +
      'credit / payment receipt / settlement statement) is recorded for chart 482012f1 with any date ' +
      'overlap in [2027-04-09, 2027-08-18].',
    generator_class: 'reading_synthesis',
    filed_by: 'native:abhisek@marsys.in (D-4a Lane A-4 session, 2026-07-19)',
    source_citation:
      'TEMPORAL_ENGINE_ARC_PLAN_v1_0.md wealth-baseline arc; BRIEF_D4A.md Lane A-4 verbatim window ' +
      '(Sat-Jup pratyantar 2027-04-09->08-18).',
  },
  // 2. Ketu-MD consolidation shape (named baseline-arc prediction #2)
  // Window read LIVE 2026-07-19: chart_dashas system_id='vimshottari' level_n=1
  // lord_graha='Ketu' -> modal row 2027-08-17 -> 2034-08-17 (3 of 5 ayanamsha-spine
  // rows agree; CR-110 double-spine disclosure carried in the claim text, DR-16
  // honest-clarity).
  {
    claim:
      'Ketu Mahadasha (2027-08-17 -> 2034-08-17, live chart_dashas modal window; CR-110 double-spine ' +
      'caveat: 2 of 5 ayanamsha rows diverge by <=6 days) manifests as a wealth-domain consolidation/' +
      'stabilization shape rather than a single dated peak.',
    event_class: 'major_gain',
    claim_shape: 'interval',
    observation_window: '[2027-08-17,2034-08-17]',
    milestone_set: null,
    model: 'dasha_lord_confluence_v1 (Ketu Mahadasha wealth-consolidation reading synthesis)',
    formula_version: 'wealth-baseline-arc-v1',
    confidence: 0.5,
    falsifier:
      'No major_gain-class LEL event is recorded with any date overlap in [2027-08-17, 2034-08-17] ' +
      '(Ketu Mahadasha span, chart_dashas system_id=vimshottari level_n=1 lord_graha=Ketu, modal row).',
    generator_class: 'reading_synthesis',
    filed_by: 'native:abhisek@marsys.in (D-4a Lane A-4 session, 2026-07-19)',
    source_citation:
      'BRIEF_D4A.md Lane A-4 (Ketu-MD consolidation shape 2027-2034); chart_dashas live query ' +
      '2026-07-19 (Ketu MD modal window 2027-08-17->2034-08-17).',
  },
  // 3. Venus-MD 2034 activation (named baseline-arc prediction #3)
  // point_date read LIVE 2026-07-19 from the same chart_dashas query: Venus MD onset
  // 2034-08-17 (modal row, 3 of 5 ayanamsha-spine rows agree).
  {
    claim:
      'Venus Mahadasha onset (2034-08-17, live chart_dashas modal date) activates a discrete wealth/' +
      'asset-domain trigger point for the native.',
    event_class: 'property_acquisition',
    claim_shape: 'point',
    observation_window: '[2034-08-17,2034-08-18)',
    milestone_set: null,
    model: 'dasha_lord_confluence_v1 (Venus Mahadasha activation trigger-point reading synthesis)',
    formula_version: 'wealth-baseline-arc-v1',
    confidence: 0.45,
    falsifier:
      'No property_acquisition-class LEL event is recorded within +/-75 days (month_known DR-13(d) ' +
      'tolerance) of 2034-08-17.',
    generator_class: 'reading_synthesis',
    filed_by: 'native:abhisek@marsys.in (D-4a Lane A-4 session, 2026-07-19)',
    source_citation:
      'BRIEF_D4A.md Lane A-4 (Venus-MD 2034 activation); chart_dashas live query 2026-07-19 ' +
      '(Venus MD onset 2034-08-17).',
  },
  // 4. Engine-generated test fixture — used by demo_append_hook.mts to demonstrate the
  // LEL-append -> outcome-matching hook live.
  {
    claim:
      '[TEST FIXTURE - D-4a Lane A-4 append-hook live demonstration, NOT a real reading] A ' +
      'travel_event-class event occurs near 2026-08-01.',
    event_class: 'travel_event',
    claim_shape: 'point',
    observation_window: '[2026-08-01,2026-08-02)',
    milestone_set: null,
    model: 'structural_placeholder_v0',
    formula_version: 'd4a-a4-demo-v1',
    confidence: 0.5,
    falsifier: 'No travel_event-class LEL entry appears within +/-45 days of 2026-08-01.',
    generator_class: 'engine',
    filed_by: 'd4a-a4-session:append-hook-demo',
    source_citation: 'D-4a Lane A-4 append-hook live demonstration fixture (2026-07-19), see demo_append_hook.mts.',
  },
  // 5. Native-intuition entry — exercises the fourth generator_class enum value.
  {
    claim:
      'Native intuits a deepening/turn in devotional practice during the early years of the Ketu ' +
      'Mahadasha (2027-2030 sub-window).',
    event_class: 'spiritual_turn',
    claim_shape: 'interval',
    observation_window: '[2027-08-17,2030-08-17]',
    milestone_set: null,
    model: 'native_filed_intuition',
    formula_version: 'n/a',
    confidence: 0.3,
    falsifier:
      'No spiritual_turn-class LEL entry (new or updated) is recorded with any interval overlap in ' +
      '[2027-08-17, 2030-08-17].',
    generator_class: 'native_intuition',
    filed_by: 'native:abhisek@marsys.in (D-4a Lane A-4 session, 2026-07-19)',
    source_citation: 'Native-filed intuition, D-4a Lane A-4 session 2026-07-19.',
  },
]

async function main() {
  for (const e of ENTRIES) {
    const { rows } = await pool.query(
      `INSERT INTO brahma_prospective_ledger
          (chart_id, claim, event_class, claim_shape, observation_window, milestone_set,
           model, formula_version, confidence, falsifier, generator_class,
           configuration_signature, filed_by, source_citation)
       VALUES
          ($1::uuid, $2, $3, $4, $5::daterange, $6::jsonb,
           $7, $8, $9, $10, $11,
           NULL, $12, $13)
       RETURNING prediction_id, claim_shape, observation_window::text, event_class, generator_class, lifecycle_status`,
      [
        CHART_ID,
        e.claim,
        e.event_class,
        e.claim_shape,
        e.observation_window,
        e.milestone_set ? JSON.stringify(e.milestone_set) : null,
        e.model,
        e.formula_version,
        e.confidence,
        e.falsifier,
        e.generator_class,
        e.filed_by,
        e.source_citation,
      ]
    )
    console.log(JSON.stringify(rows[0], null, 2))
  }
  await pool.end()
}

main().catch(async (err) => {
  console.error(err)
  await pool.end()
  process.exit(1)
})
