/**
 * POST /api/clients/[id]/learning
 *
 * BA-P7B portal learning loop backend.
 * Single endpoint with `action` discriminant for all five learning loop surfaces:
 *   adjudicate    — Step 1: ask-card one-tap outcome for UNRESOLVED closed window
 *   lel_entry     — Step 2: append structured LEL entry to markdown + trigger resync
 *   schedule_followup — Step 3: auto-schedule prashna follow-up ask at fructification date
 *   cosign        — Step 4: native approve/revoke of calibration snapshot
 *   resonance     — Step 5 (QUARANTINED): resonance feedback, NO path to weights
 *
 * Auth: Firebase session; chart-level access guard (must be owner or super_admin).
 * No direct writes to L1–L4 tables. LEL markdown is never bypassed (Step 2).
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import * as fs from 'fs'
import * as path from 'path'

export const dynamic = 'force-dynamic'

// ── Auth guard ────────────────────────────────────────────────────────────────

async function guardChartAccess(chartId: string, uid: string): Promise<boolean> {
  const res = await query<{ id: string }>(
    `SELECT c.id FROM charts c
     LEFT JOIN chart_grants g ON g.chart_id = c.id AND g.principal_id = $2
     WHERE c.id = $1
       AND (c.owner_id = $2 OR c.client_id = $2
            OR g.principal_id IS NOT NULL
            OR EXISTS (SELECT 1 FROM profiles p WHERE p.id=$2 AND p.role='super_admin'))
     LIMIT 1`,
    [chartId, uid],
  )
  return res.rows.length > 0
}

// ── Step 1: adjudicate — one-tap verdict for UNRESOLVED closed window ─────────

async function handleAdjudicate(chartId: string, uid: string, body: unknown) {
  const { prediction_id, outcome } = body as {
    prediction_id: string
    outcome: 'happened' | 'partial' | 'didnt' | 'cant_say'
  }
  if (!prediction_id || !outcome) {
    return NextResponse.json({ error: 'prediction_id and outcome required' }, { status: 400 })
  }
  const valid = ['happened', 'partial', 'didnt', 'cant_say']
  if (!valid.includes(outcome)) {
    return NextResponse.json({ error: 'invalid outcome' }, { status: 400 })
  }

  // Map user tap → mi_pramana-readable verdict
  const verdictMap: Record<string, string> = {
    happened: 'CONFIRMED',
    partial: 'PARTIAL',
    didnt: 'REFUTED',
    cant_say: 'UNRESOLVED',
  }

  await query(
    `INSERT INTO mimamsa_adjudication_log
       (chart_id, prediction_id, outcome, verdict_mapped, adjudicator_uid, adjudicated_at)
     VALUES ($1, $2, $3, $4, $5, now())
     ON CONFLICT (chart_id, prediction_id) DO UPDATE SET
       outcome = EXCLUDED.outcome,
       verdict_mapped = EXCLUDED.verdict_mapped,
       adjudicator_uid = EXCLUDED.adjudicator_uid,
       adjudicated_at = now()`,
    [chartId, prediction_id, outcome, verdictMap[outcome], uid],
  )

  // Signal mi_abhilekha resync (async — portal does not wait)
  void triggerResync(chartId, prediction_id)

  return NextResponse.json({ ok: true, prediction_id, outcome, verdict_mapped: verdictMap[outcome] })
}

async function triggerResync(chartId: string, predictionId: string) {
  try {
    const sidecarUrl = (process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001').replace(/\/$/, '')
    await fetch(`${sidecarUrl}/mimamsa/abhilekha-resync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Api-Key': process.env['PYTHON_SIDECAR_API_KEY'] ?? '',
      },
      body: JSON.stringify({ chart_id: chartId, prediction_id: predictionId }),
    })
  } catch {
    // resync is best-effort; portal remains responsive
  }
}

// ── Step 2: lel_entry — structured LEL intake → markdown append + resync ─────

const LEL_MARKDOWN_PATH = path.resolve(
  process.cwd(),
  '..', '01_FACTS_LAYER', 'LIFE_EVENT_LOG_v1_2.md',
)

async function handleLelEntry(chartId: string, uid: string, body: unknown) {
  const { event_id, category, subcategory, magnitude, date, notes } = body as {
    event_id: string
    category: string
    subcategory?: string
    magnitude: string
    date: string
    notes?: string
  }
  if (!event_id || !category || !magnitude || !date) {
    return NextResponse.json({ error: 'event_id, category, magnitude, date required' }, { status: 400 })
  }
  const validMag = ['rupture', 'major', 'significant', 'moderate', 'minor', 'trivial']
  if (!validMag.includes(magnitude)) {
    return NextResponse.json({ error: 'invalid magnitude' }, { status: 400 })
  }

  // Build YAML block (governed append — preserves LEL as source-of-truth)
  const yamlBlock = [
    ``,
    `\`\`\`yaml`,
    `${event_id}:`,
    `  date: "${date}"`,
    `  category: "${category}"`,
    subcategory ? `  subcategory: "${subcategory}"` : null,
    `  magnitude: "${magnitude}"`,
    `  disclosure_timing: "prospective"`,
    notes ? `  notes: "${notes.replace(/"/g, "'")}"` : null,
    `  shaped_predictor: false`,
    `\`\`\``,
    ``,
  ].filter(Boolean).join('\n')

  try {
    if (!fs.existsSync(LEL_MARKDOWN_PATH)) {
      return NextResponse.json({ error: 'LEL markdown not found at expected path' }, { status: 500 })
    }
    fs.appendFileSync(LEL_MARKDOWN_PATH, yamlBlock, 'utf-8')
  } catch (err) {
    return NextResponse.json({ error: `LEL append failed: ${String(err)}` }, { status: 500 })
  }

  // Signal mi_jivanaghatana provenance resync (best-effort async)
  void triggerProvenanceResync(chartId)

  return NextResponse.json({
    ok: true,
    event_id,
    appended_to: 'LIFE_EVENT_LOG_v1_2.md',
    next: 'mi_jivanaghatana resync triggered',
  })
}

async function triggerProvenanceResync(chartId: string) {
  try {
    const sidecarUrl = (process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001').replace(/\/$/, '')
    await fetch(`${sidecarUrl}/mimamsa/provenance-resync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Api-Key': process.env['PYTHON_SIDECAR_API_KEY'] ?? '',
      },
      body: JSON.stringify({ chart_id: chartId }),
    })
  } catch {
    // best-effort
  }
}

// ── Step 3: schedule_followup — Loop B prashna follow-up ────────────────────

async function handleScheduleFollowup(chartId: string, body: unknown) {
  const { prediction_id, domain, composite_score, fructification_date, follow_up_prompt } = body as {
    prediction_id: string
    domain: string
    composite_score?: number
    fructification_date: string
    follow_up_prompt: string
  }
  if (!prediction_id || !domain || !fructification_date || !follow_up_prompt) {
    return NextResponse.json({ error: 'prediction_id, domain, fructification_date, follow_up_prompt required' }, { status: 400 })
  }

  await query(
    `INSERT INTO prashna_followup_schedule
       (chart_id, prediction_id, domain, composite_score, fructification_date, follow_up_prompt)
     VALUES ($1, $2, $3, $4, $5::date, $6)
     ON CONFLICT (chart_id, prediction_id) DO UPDATE SET
       composite_score = EXCLUDED.composite_score,
       fructification_date = EXCLUDED.fructification_date,
       follow_up_prompt = EXCLUDED.follow_up_prompt,
       status = 'scheduled'`,
    [chartId, prediction_id, domain, composite_score ?? null, fructification_date, follow_up_prompt],
  )

  return NextResponse.json({ ok: true, scheduled: { prediction_id, fructification_date } })
}

// ── Step 4: cosign — native approve/revoke of calibration snapshot ───────────

async function handleCosign(chartId: string, uid: string, body: unknown) {
  const { snapshot_id, cosign_action, judgment_ledger_ref, notes } = body as {
    snapshot_id: string
    cosign_action: 'approved' | 'revoked'
    judgment_ledger_ref?: string
    notes?: string
  }
  const action = cosign_action
  if (!snapshot_id || !['approved', 'revoked'].includes(action)) {
    return NextResponse.json({ error: 'snapshot_id and cosign_action (approved|revoked) required' }, { status: 400 })
  }

  await query(
    `INSERT INTO mimamsa_snapshot_cosign
       (snapshot_id, chart_id, action, cosigner_uid, judgment_ledger_ref, notes)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (snapshot_id, action) DO UPDATE SET
       cosigner_uid = EXCLUDED.cosigner_uid,
       cosigned_at = now(),
       notes = EXCLUDED.notes`,
    [snapshot_id, chartId, action, uid, judgment_ledger_ref ?? null, notes ?? null],
  )

  if (action === 'approved') {
    await query(
      `UPDATE mimamsa_calibration_snapshot
       SET two_key_complete = true, publication_status = 'live'
       WHERE snapshot_id = $1 AND chart_id = $2`,
      [snapshot_id, chartId],
    )
  } else {
    await query(
      `UPDATE mimamsa_calibration_snapshot
       SET publication_status = 'revoked'
       WHERE snapshot_id = $1 AND chart_id = $2`,
      [snapshot_id, chartId],
    )
  }

  return NextResponse.json({ ok: true, snapshot_id, action })
}

// ── Step 5: resonance — QUARANTINED feedback capture ─────────────────────────

async function handleResonance(chartId: string, uid: string, body: unknown) {
  const { signal_ref, domain, resonance, context_note, session_id } = body as {
    signal_ref: string
    domain?: string
    resonance: 'resonates' | 'doesnt_resonate' | 'neutral'
    context_note?: string
    session_id?: string
  }
  if (!signal_ref || !['resonates', 'doesnt_resonate', 'neutral'].includes(resonance)) {
    return NextResponse.json({ error: 'signal_ref and resonance required' }, { status: 400 })
  }

  // QUARANTINE: write ONLY to mimamsa_resonance_feedback — no join or FK to weight tables
  await query(
    `INSERT INTO mimamsa_resonance_feedback
       (chart_id, signal_ref, domain, resonance, context_note, session_id)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [chartId, signal_ref, domain ?? null, resonance, context_note ?? null, session_id ?? null],
  )

  return NextResponse.json({ ok: true, quarantine: 'CONFIRMED — no path to weights' })
}

// ── Router ────────────────────────────────────────────────────────────────────

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: chartId } = await params
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const hasAccess = await guardChartAccess(chartId, user.uid)
  if (!hasAccess) return NextResponse.json({ error: 'forbidden' }, { status: 403 })

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'invalid JSON' }, { status: 400 })
  }

  const action = (body as { action?: string }).action
  switch (action) {
    case 'adjudicate':      return handleAdjudicate(chartId, user.uid, body)
    case 'lel_entry':       return handleLelEntry(chartId, user.uid, body)
    case 'schedule_followup': return handleScheduleFollowup(chartId, body)
    case 'cosign':          return handleCosign(chartId, user.uid, body)
    case 'resonance':       return handleResonance(chartId, user.uid, body)
    default:
      return NextResponse.json({ error: `unknown action: ${action}` }, { status: 400 })
  }
}

// ── GET: open UNRESOLVED closed windows for ask-cards ────────────────────────

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: chartId } = await params
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const hasAccess = await guardChartAccess(chartId, user.uid)
  if (!hasAccess) return NextResponse.json({ error: 'forbidden' }, { status: 403 })

  // Fetch predictions whose window closed UNRESOLVED and not yet adjudicated
  const res = await query<{
    prediction_id: string
    domain: string
    summary: string
    window_end: string
    composite_verdict: string
  }>(
    `SELECT pa.prediction_id, pa.domain,
            pa.prediction_summary AS summary,
            pa.window_end::text,
            COALESCE(mc.composite_verdict, 'UNRESOLVED') AS composite_verdict
     FROM phala_anchors pa
     LEFT JOIN mimamsa_calibration mc ON mc.prediction_id = pa.prediction_id
                                      AND mc.chart_id = pa.chart_id
     LEFT JOIN mimamsa_adjudication_log al ON al.prediction_id = pa.prediction_id
                                           AND al.chart_id = pa.chart_id
     WHERE pa.chart_id = $1
       AND pa.window_end < CURRENT_DATE
       AND COALESCE(mc.composite_verdict, 'UNRESOLVED') = 'UNRESOLVED'
       AND al.prediction_id IS NULL
     ORDER BY pa.window_end DESC
     LIMIT 20`,
    [chartId],
  )

  // Fetch pending prashna follow-ups due today or earlier
  const followUps = await query<{
    prediction_id: string
    domain: string
    follow_up_prompt: string
    fructification_date: string
  }>(
    `SELECT prediction_id, domain, follow_up_prompt, fructification_date::text
     FROM prashna_followup_schedule
     WHERE chart_id = $1
       AND status = 'scheduled'
       AND fructification_date <= CURRENT_DATE
     ORDER BY fructification_date
     LIMIT 10`,
    [chartId],
  )

  // Fetch proposed (not yet co-signed) calibration snapshots
  const snapshots = await query<{
    snapshot_id: string
    formula_version: string
    publication_status: string
    created_at: string
    cells_jsonb: unknown
  }>(
    `SELECT snapshot_id, formula_version, publication_status,
            created_at::text, cells_jsonb
     FROM mimamsa_calibration_snapshot
     WHERE chart_id = $1
       AND two_key_complete = false
       AND publication_status = 'proposed'
     ORDER BY created_at DESC
     LIMIT 5`,
    [chartId],
  )

  return NextResponse.json({
    open_windows: res.rows,
    pending_followups: followUps.rows,
    pending_cosign: snapshots.rows,
  })
}
