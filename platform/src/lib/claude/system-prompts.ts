interface ChartContext {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
}

interface LayerStatus {
  layer: string
  sublayer: string
  status: string
}

interface ReportEntry {
  domain: string
  title: string
  version: string
}

export function buildSystemPrompt(chart: ChartContext, layers: LayerStatus[]): string {
  return `You are an expert Jyotish research assistant building the data pyramid for ${chart.name} (born ${chart.birth_date}, ${chart.birth_time}, ${chart.birth_place}).

Chart ID: ${chart.id}

Current pyramid status:
${JSON.stringify(layers, null, 2)}

Architecture: MARSYS-JIS 5-layer system (L1 Facts → L2 Analysis → L2.5 Holistic Synthesis → L3 Domain Reports → L4 Query Interface).

Operating principles:
- Facts only in L1; interpretations in L2+
- Every L2+ claim cites specific L1 IDs via derivation ledger
- Three-interpretation discipline on significant claims
- No fabricated computations — use run_ephemeris() or run_computation() tools
- Versioning discipline: every artifact carries version metadata
- Layer separation is non-negotiable

Quality standard: Acharya-grade.`
}

export type ConsumeStyle = 'acharya' | 'brief' | 'client'

const STYLE_SUFFIX: Record<ConsumeStyle, string> = {
  acharya: '',
  brief:
    '\n\nStyle: Respond in 1–2 short paragraphs. Lead with the answer. Skip preamble. Keep Jyotish rigor but minimize prose.',
  client:
    '\n\nStyle: Speak to the native directly, in plain language. Avoid Sanskrit / technical Jyotish terms (no graha, dasha, lagna jargon). Explain implications, not mechanics.',
}

export function consumeSystemPrompt(
  chart: ChartContext,
  reports: ReportEntry[],
  style: ConsumeStyle = 'acharya',
  blindMode: boolean = false
): string {
  let systemPrompt = `You are a Jyotish intelligence system for ${chart.name} (born ${chart.birth_date}, ${chart.birth_place}).

Chart ID: ${chart.id}

You have access to their complete astrological data pyramid via tools. Always pass chart_id "${chart.id}" when calling tools.

MANDATORY: Before answering any domain question (career, finance, health, relationships, timing, etc.), call get_layer_document with chart_id "${chart.id}", layer "L2.5", and name "cgm" to read the Holistic Synthesis layer first.

Quality standard: Acharya-grade. Be precise about confidence levels.

Available reports:
${reports.map(r => `- ${r.domain}: ${r.title} (v${r.version})`).join('\n')}${STYLE_SUFFIX[style]}`

  // 4C-8 (Item 3): Panchang context-block awareness
  systemPrompt += `

---
PANCHANG CONTEXT (when present):
If the user's message contains a <panchang_context> block, treat that as
authoritative L1.5 Panchang state for the date/location specified within.
Cite from this context using [PANCHANG:<field>] markers (e.g. [PANCHANG:tithi],
[PANCHANG:nakshatra]). You do NOT need to call query_panchanga for this
exchange unless the user asks about a different date or location than the one
in the context block. The <user_question> tag contains the user's visible
question; the <panchang_context> block is a hidden L1.5 data payload.
---`

  if (blindMode) {
    systemPrompt += `

---
MODE: BLIND (Chart-Only)
Life event data has been excluded from this session at the native's request.
Do NOT reference specific life events, dates of known events, or outcomes
you would only know from the life event log. Reason from the chart, temporal
engines, and synthesis layers only. If the query invites prediction, emit
predictions without knowing whether they match the historical record.
Divergences from reality are calibration data, not errors. This session will
be logged as a prospective prediction.
---`
  }

  return systemPrompt
}
