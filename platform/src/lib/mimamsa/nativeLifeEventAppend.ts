import 'server-only'
import * as fs from 'fs'
import * as path from 'path'

export type NativeLifeEventAppendResult =
  | { status: 200; body: { ok: true; event_id: string; appended_to: string; next: string } }
  | { status: 400 | 403 | 500; body: { error: string } }

// The existing fixed file is native-only; never substitute this target for another chart.
const LEL_MARKDOWN_PATH = path.resolve(
  process.cwd(),
  '..', '01_FACTS_LAYER', 'LIFE_EVENT_LOG_v1_2.md',
)

/** Caller must first establish authentication, chart admission and write permission. */
export function appendNativeLifeEvent(chartId: string, body: unknown): NativeLifeEventAppendResult {
  if (chartId !== '482012f1-710e-4a25-994a-93821f5871aa') {
    return { status: 403, body: { error: 'Life event intake is available only for the native chart.' } }
  }

  const { event_id, category, subcategory, magnitude, date, notes } = body as {
    event_id: string
    category: string
    subcategory?: string
    magnitude: string
    date: string
    notes?: string
  }
  if (!event_id || !category || !magnitude || !date) {
    return { status: 400, body: { error: 'event_id, category, magnitude, date required' } }
  }
  const validMag = ['rupture', 'major', 'significant', 'moderate', 'minor', 'trivial']
  if (!validMag.includes(magnitude)) {
    return { status: 400, body: { error: 'invalid magnitude' } }
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
      return { status: 500, body: { error: 'LEL markdown not found at expected path' } }
    }
    fs.appendFileSync(LEL_MARKDOWN_PATH, yamlBlock, 'utf-8')
  } catch (err) {
    return { status: 500, body: { error: `LEL append failed: ${String(err)}` } }
  }

  // Signal mi_jivanaghatana provenance resync (best-effort async)
  void triggerProvenanceResync(chartId)

  return { status: 200, body: {
    ok: true,
    event_id,
    appended_to: 'LIFE_EVENT_LOG_v1_2.md',
    next: 'Life event appended; provenance resync completion is unconfirmed.',
  } }
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

