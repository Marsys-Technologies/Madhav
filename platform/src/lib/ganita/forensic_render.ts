/**
 * ganita/forensic_render.ts — FORENSIC v8.0-style Markdown renderer
 *
 * Renders a GanitaFactStore into a Markdown document that covers all domains
 * present in FORENSIC v8.0 §0–§27 (chart_facts via forensic_render;
 * md archived at 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md). The render is
 * deterministic, section-ordered, and suitable for LLM context injection.
 *
 * Coverage requirement: every §N section in FORENSIC v8.0 has a corresponding
 * render block. Sections with no data emit a "— (no data) —" placeholder so
 * the structure is always complete.
 *
 * [BRAHMA-GA-1-8]
 */

import type {
  GanitaFactStore,
  MetadataSection,
  PlanetPlacementRow,
  HouseRow,
  DivisionalChartRow,
  DashaRow,
  StrengthRow,
  SensitivePointRow,
  PanchangaRow,
  YogaRow,
  AspectRow,
  ChartFactRow,
} from './types'

// ─── Render options ───────────────────────────────────────────────────────────

export interface ForensicRenderOptions {
  /** Include raw row counts in section footers (default: false) */
  include_row_counts?: boolean
  /** Include ayanamsha / build provenance header (default: true) */
  include_header?: boolean
  /** Render sections as collapsible HTML <details> (default: false) */
  collapsible?: boolean
  /** Maximum number of rows per section (0 = unlimited, default: 0) */
  max_rows_per_section?: number
}

// ─── Utility helpers ──────────────────────────────────────────────────────────

function hr(): string {
  return '\n---\n'
}

function h2(title: string): string {
  return `\n## ${title}\n`
}

function h3(title: string): string {
  return `\n### ${title}\n`
}

function h4(title: string): string {
  return `\n#### ${title}\n`
}

function tableRow(cells: (string | number | null | undefined)[]): string {
  return `| ${cells.map(c => (c === null || c === undefined) ? '—' : String(c)).join(' | ')} |`
}

function tableHeader(headers: string[]): string {
  const row = tableRow(headers)
  const sep = `| ${headers.map(() => '---').join(' | ')} |`
  return `${row}\n${sep}`
}

function noData(label?: string): string {
  return `\n_${label ?? 'No data available for this section.'}_\n`
}

function bool(v: boolean | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return v ? 'Yes' : 'No'
}

function num(v: number | null | undefined, decimals = 2): string {
  if (v === null || v === undefined) return '—'
  return v.toFixed(decimals)
}

// ─── Section renderers ────────────────────────────────────────────────────────

function renderDocumentIndex(): string {
  return `
## §0 — DOCUMENT INDEX AND USAGE

This document is a machine-rendered projection of the Gaṇita Fact Store onto the
FORENSIC v8.0 section structure. All values are sourced from the \`chart_facts\`
database table. Sections with no data emit "no data" placeholders.

| § | Section | Content Type |
| --- | --- | --- |
| 0 | Document Index | Index |
| 1 | Core Identity / Metadata | FACT |
| 2 | D1 Rashi Chart | FACT |
| 3 | Divisional Charts (D2–D60) | FACT |
| 4 | KP System | FACT + DERIVED |
| 5 | Dasha Systems | FACT |
| 6 | Strength Metrics (Shadbala) | FACT |
| 7 | Ashtakavarga | FACT + DERIVED |
| 8 | Saturn Kakshya Zones | DERIVED |
| 9 | Avastha Diagnostics | DERIVED |
| 10 | Chara Karakas | DERIVED |
| 11 | Sensitive Points | DERIVED |
| 12 | Special Lagnas and Sahams | DERIVED |
| 13 | Arudhas | DERIVED |
| 14 | Stellar Matrix (Navatara) | DERIVED |
| 15 | Panchanga DNA | FACT |
| 16 | Aspects (Graha Drishti) | FACT |
| 17 | Chalit Kinetic Shifts | DERIVED |
| 18 | Chandra Chart | DERIVED |
| 19 | Kota Chakra | DERIVED |
| 20 | Deity Assignments | DERIVED |
| 21 | Sade Sati Cycles | FACT |
| 22 | Varshphal | FACT |
| 23 | Cross-Reference Matrices | DERIVED indexes |
| 24 | Longevity Indicators | FACT |
| 25 | Additional Dasha Systems | FACT |
| 26 | Yogas Register | DERIVED |
| 27 | Document Completeness Ledger | DERIVED |
`
}

function renderMetadata(meta: MetadataSection): string {
  const lines = [
    h2('§1 — CORE IDENTITY (FACTS)'),
    h3('§1.1 Birth Metadata'),
    tableHeader(['ID', 'Field', 'Value']),
    tableRow(['`MET.BIRTH.DATE`', 'Birth Date', meta.birth_date]),
    tableRow(['`MET.BIRTH.TIME`', 'Birth Time', meta.birth_time]),
    tableRow(['`MET.BIRTH.PLACE`', 'Birth Place', meta.birth_place]),
    tableRow(['`MET.BIRTH.LAT`', 'Latitude', meta.latitude]),
    tableRow(['`MET.BIRTH.LON`', 'Longitude', meta.longitude]),
    tableRow(['`MET.BIRTH.TZ`', 'Timezone', meta.timezone]),
    tableRow(['`MET.AYAN.NAME`', 'Ayanamsa', meta.ayanamsha]),
    tableRow(['`MET.AYAN.VAL`', 'Ayanamsa Value', meta.ayanamsha_value]),
    tableRow(['`MET.HOUSE.SYSTEM`', 'House System', meta.house_system]),
    h3('§1.2 Core Mirror'),
    tableHeader(['ID', 'Field', 'Value']),
    tableRow(['`MET.LAGNA.SIGN`', 'Lagna Sign', meta.lagna_sign]),
    tableRow(['`MET.LAGNA.DEG`', 'Lagna Degree', meta.lagna_degree]),
    tableRow(['`MET.LAGNA.NAK`', 'Lagna Nakshatra', meta.lagna_nakshatra]),
    tableRow(['`MET.LAGNA.PADA`', 'Lagna Pada', meta.lagna_pada]),
  ]
  return lines.join('\n')
}

function renderPlanets(planets: PlanetPlacementRow[]): string {
  if (planets.length === 0) {
    return h2('§2 — D1 RASHI CHART (FACTS)') + noData('No planet placement data')
  }
  const lines = [
    h2('§2 — D1 RASHI CHART (FACTS)'),
    h3('§2.1 D1 Planet Positions'),
    tableHeader(['ID', 'Planet', 'Sign', 'Degree', 'Nakshatra', 'Pada', 'Rashi House', 'Chalit House', 'Dignity', 'Retro']),
  ]
  for (const p of planets) {
    lines.push(tableRow([
      `\`PLN.${p.planet.toUpperCase()}\``,
      p.planet,
      p.sign,
      p.degree_dms ?? num(p.degree_decimal),
      p.nakshatra,
      p.nakshatra_pada,
      p.house_rashi,
      p.house_chalit,
      p.dignity,
      bool(p.retrograde),
    ]))
  }
  lines.push(h3('§2.2 D1 Sign Occupancy (Bhava View)'))
  lines.push(tableHeader(['Planet', 'Sign', 'Rashi House', 'Chalit House', 'Combusted']))
  for (const p of planets) {
    lines.push(tableRow([p.planet, p.sign, p.house_rashi, p.house_chalit, bool(p.combusted)]))
  }
  return lines.join('\n')
}

function renderDivisionals(divisionals: DivisionalChartRow[]): string {
  if (divisionals.length === 0) {
    return h2('§3 — DIVISIONAL CHARTS (FACTS)') + noData('No divisional chart data')
  }
  const byVarga: Record<string, DivisionalChartRow[]> = {}
  for (const d of divisionals) {
    if (!byVarga[d.varga]) byVarga[d.varga] = []
    byVarga[d.varga].push(d)
  }
  const lines = [h2('§3 — DIVISIONAL CHARTS (FACTS)')]
  const vargaOrder = ['D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60']
  const allVargas = [...new Set([...vargaOrder, ...Object.keys(byVarga)])]
  for (const varga of allVargas) {
    const rows = byVarga[varga]
    if (!rows || rows.length === 0) continue
    lines.push(h3(`§3.x ${varga} — Divisional Chart`))
    lines.push(tableHeader(['Planet', 'Sign', 'House', 'Lord']))
    for (const r of rows) {
      lines.push(tableRow([r.planet, r.sign, r.house, r.lord]))
    }
  }
  return lines.join('\n')
}

function renderKP(rows: ChartFactRow[]): string {
  if (rows.length === 0) {
    return h2('§4 — KP SYSTEM (FACTS + DERIVED)') + noData('No KP data')
  }
  const lines = [
    h2('§4 — KP SYSTEM (FACTS + DERIVED)'),
    h3('§4.1 KP Cusp Sub-Lords'),
    tableHeader(['Cusp', 'Sign', 'Sub-Lord', 'Star Lord', 'Value']),
  ]
  const cusp = rows.filter(r => r.fact_id.startsWith('KP.CUSP') || r.category === 'kp')
  for (const r of cusp) {
    lines.push(tableRow([
      r.fact_id,
      r.fact_subject ?? '—',
      r.value_text ?? '—',
      r.value_json?.['star_lord'] as string ?? '—',
      r.value_number ?? '—',
    ]))
  }
  return lines.join('\n')
}

function renderDashas(dashas: DashaRow[]): string {
  if (dashas.length === 0) {
    return h2('§5 — DASHA SYSTEMS (FACTS)') + noData('No dasha data')
  }
  const lines = [h2('§5 — DASHA SYSTEMS (FACTS)')]
  const bySystem: Record<string, DashaRow[]> = {}
  for (const d of dashas) {
    if (!bySystem[d.system]) bySystem[d.system] = []
    bySystem[d.system].push(d)
  }

  for (const [system, sdashas] of Object.entries(bySystem)) {
    lines.push(h3(`§5.x ${system.charAt(0).toUpperCase() + system.slice(1)} Dasha`))
    lines.push(tableHeader(['Level', 'Lord', 'Start Date', 'End Date', 'Duration (days)']))
    for (const d of sdashas) {
      lines.push(tableRow([d.level, d.lord, d.start_date, d.end_date, d.duration_days]))
    }
  }
  return lines.join('\n')
}

function renderStrengths(strengths: StrengthRow[]): string {
  if (strengths.length === 0) {
    return h2('§6 — STRENGTH METRICS (FACTS)') + noData('No strength data')
  }
  const shadbala = strengths.filter(s => s.system === 'shadbala')
  const vimsopaka = strengths.filter(s => s.system === 'vimsopaka')
  const bhavaBala = strengths.filter(s => s.system === 'bhava_bala')
  const lines = [h2('§6 — STRENGTH METRICS (FACTS)')]

  if (shadbala.length > 0) {
    lines.push(h3('§6.1 Shadbala'))
    lines.push(tableHeader(['Planet', 'Category', 'Value', 'Unit']))
    for (const s of shadbala) {
      lines.push(tableRow([s.planet, s.category, num(s.value), s.unit]))
    }
  }
  if (vimsopaka.length > 0) {
    lines.push(h3('§6.2 Vimsopaka Bala'))
    lines.push(tableHeader(['Planet', 'Category', 'Value', 'Unit']))
    for (const s of vimsopaka) {
      lines.push(tableRow([s.planet, s.category, num(s.value), s.unit]))
    }
  }
  if (bhavaBala.length > 0) {
    lines.push(h3('§6.3 Bhava Bala (JH)'))
    lines.push(tableHeader(['Planet/House', 'Category', 'Value', 'Unit']))
    for (const s of bhavaBala) {
      lines.push(tableRow([s.planet, s.category, num(s.value), s.unit]))
    }
  }
  return lines.join('\n')
}

function renderAshtakavarga(strengths: StrengthRow[], rawRows: ChartFactRow[]): string {
  const avRows = strengths.filter(s => s.system === 'ashtakavarga')
  const rawAv = rawRows
  if (avRows.length === 0 && rawAv.length === 0) {
    return h2('§7 — ASHTAKAVARGA (FACTS + DERIVED)') + noData('No ashtakavarga data')
  }
  const lines = [
    h2('§7 — ASHTAKAVARGA (FACTS + DERIVED)'),
    h3('§7.1 Sarvashtakavarga Bindus'),
    tableHeader(['Planet / Sign', 'Category', 'Value (Bindus)', 'Unit']),
  ]
  for (const s of avRows) {
    lines.push(tableRow([s.planet, s.category, num(s.value, 0), s.unit]))
  }
  return lines.join('\n')
}

function renderCategorySection(
  sectionTitle: string,
  rows: ChartFactRow[],
  sectionNum: string,
): string {
  if (rows.length === 0) {
    return h2(`${sectionNum} — ${sectionTitle}`) + noData()
  }
  const lines = [
    h2(`${sectionNum} — ${sectionTitle}`),
    tableHeader(['ID', 'Subject', 'Category', 'Value', 'JSON']),
  ]
  for (const r of rows) {
    const jsonStr = r.value_json ? JSON.stringify(r.value_json).slice(0, 60) : '—'
    lines.push(tableRow([r.fact_id, r.fact_subject, r.category, r.value_text ?? num(r.value_number), jsonStr]))
  }
  return lines.join('\n')
}

function renderSensitivePoints(points: SensitivePointRow[]): string {
  if (points.length === 0) {
    return h2('§11–§13 — SENSITIVE POINTS (DERIVED)') + noData('No sensitive point data')
  }
  const upagrahas = points.filter(p => p.type === 'upagraha')
  const specialLagnas = points.filter(p => p.type === 'special_lagna')
  const sahams = points.filter(p => p.type === 'saham')
  const arudhas = points.filter(p => p.type === 'arudha')
  const karakas = points.filter(p => p.type === 'karaka')
  const lines = []

  if (upagrahas.length > 0) {
    lines.push(h2('§11 — UPAGRAHAS (DERIVED)'))
    lines.push(tableHeader(['Name', 'Type', 'Sign', 'House', 'Degree']))
    for (const p of upagrahas) {
      lines.push(tableRow([p.name, p.type, p.sign, p.house, p.degree]))
    }
  }
  if (specialLagnas.length > 0) {
    lines.push(h2('§12.1 — SPECIAL LAGNAS (DERIVED)'))
    lines.push(tableHeader(['Name', 'Sign', 'House', 'Degree', 'Lord']))
    for (const p of specialLagnas) {
      lines.push(tableRow([p.name, p.sign, p.house, p.degree, p.lord]))
    }
  }
  if (sahams.length > 0) {
    lines.push(h2('§12.2 — SAHAMS (DERIVED)'))
    lines.push(tableHeader(['Saham Name', 'Sign', 'House', 'Degree', 'Lord']))
    for (const p of sahams) {
      lines.push(tableRow([p.name, p.sign, p.house, p.degree, p.lord]))
    }
  }
  if (arudhas.length > 0) {
    lines.push(h2('§13 — ARUDHAS (DERIVED)'))
    lines.push(tableHeader(['Arudha', 'Sign', 'House', 'Lord']))
    for (const p of arudhas) {
      lines.push(tableRow([p.name, p.sign, p.house, p.lord]))
    }
  }
  if (karakas.length > 0) {
    lines.push(h2('§10 — CHARA KARAKAS (DERIVED)'))
    lines.push(tableHeader(['Karaka Role', 'Planet', 'Sign', 'House']))
    for (const p of karakas) {
      lines.push(tableRow([p.name, p.sign, p.house, p.lord]))
    }
  }
  return lines.join('\n')
}

function renderPanchanga(panchanga: PanchangaRow[]): string {
  if (panchanga.length === 0) {
    return h2('§15 — PANCHANGA DNA (FACTS)') + noData('No panchanga data')
  }
  const lines = [
    h2('§15 — PANCHANGA DNA (FACTS)'),
    h3('§15.1 Birth Panchanga Elements'),
    tableHeader(['Component', 'Value', 'Lord', 'Pada', 'Start (ISO)', 'End (ISO)']),
  ]
  for (const p of panchanga) {
    lines.push(tableRow([p.component, p.value, p.lord, p.pada, p.start_iso, p.end_iso]))
  }
  return lines.join('\n')
}

function renderAspects(aspects: AspectRow[]): string {
  if (aspects.length === 0) {
    return h2('§16 — ASPECTS (GRAHA DRISHTI) (FACTS)') + noData('No aspect data')
  }
  const lines = [
    h2('§16 — ASPECTS (GRAHA DRISHTI) (FACTS)'),
    h3('§16.1 Planetary Aspects'),
    tableHeader(['Aspector', 'Aspected Body', 'Aspect Type', 'Orb (°)', 'Strength']),
  ]
  for (const a of aspects) {
    lines.push(tableRow([a.aspector, a.aspected_body, a.aspect_type, num(a.orb_degrees), a.strength]))
  }
  return lines.join('\n')
}

function renderYogas(yogas: YogaRow[]): string {
  if (yogas.length === 0) {
    return h2('§26 — YOGAS REGISTER (DERIVED)') + noData('No yoga data')
  }
  const lines = [
    h2('§26 — YOGAS REGISTER (DERIVED)'),
    h3('§26.1 D1 Yoga Summary'),
    tableHeader(['Yoga Name', 'Type', 'Planets Involved', 'Houses', 'Strength', 'Source Rule']),
  ]
  for (const y of yogas) {
    lines.push(tableRow([
      y.yoga_name,
      y.type,
      y.planets_involved.join(', '),
      y.houses_involved.join(', '),
      y.strength,
      y.source_rule,
    ]))
  }
  return lines.join('\n')
}

function renderSadeSati(rows: ChartFactRow[]): string {
  if (rows.length === 0) {
    return h2('§21 — SADE SATI CYCLES (FACTS)') + noData('No Sade Sati data')
  }
  const lines = [
    h2('§21 — SADE SATI CYCLES (FACTS)'),
    tableHeader(['ID', 'Subject', 'Value', 'JSON Data']),
  ]
  for (const r of rows) {
    const jsonStr = r.value_json ? JSON.stringify(r.value_json).slice(0, 80) : '—'
    lines.push(tableRow([r.fact_id, r.fact_subject, r.value_text ?? num(r.value_number), jsonStr]))
  }
  return lines.join('\n')
}

function renderVarshphal(rows: ChartFactRow[]): string {
  if (rows.length === 0) {
    return h2('§22 — VARSHPHAL (FACTS)') + noData('No Varshphal data')
  }
  const lines = [
    h2('§22 — VARSHPHAL (FACTS)'),
    tableHeader(['ID', 'Subject', 'Category', 'Value', 'JSON Data']),
  ]
  for (const r of rows) {
    const jsonStr = r.value_json ? JSON.stringify(r.value_json).slice(0, 80) : '—'
    lines.push(tableRow([r.fact_id, r.fact_subject, r.category, r.value_text ?? num(r.value_number), jsonStr]))
  }
  return lines.join('\n')
}

function renderHouses(houses: HouseRow[]): string {
  // rendered inline with §2 above — but also produce standalone for §2.2 + Chalit
  if (houses.length === 0) return ''
  const lines = [
    h3('§2.3 Bhava / Chalit Cusp Ledger'),
    tableHeader(['House', 'Sign', 'Cusp Degree', 'Cusp Nakshatra', 'Lord', 'KP Sub-Lord', 'Planets (Rashi)', 'Planets (Chalit)']),
  ]
  for (const h of houses) {
    lines.push(tableRow([
      h.house,
      h.sign,
      h.cusp_degree,
      h.cusp_nakshatra,
      h.cusp_lord,
      h.sub_lord,
      h.planets_rashi.join(', ') || '(none)',
      h.planets_chalit.join(', ') || '(none)',
    ]))
  }
  return lines.join('\n')
}

function renderCompletenessLedger(store: GanitaFactStore): string {
  const lines = [
    h2('§27 — DOCUMENT COMPLETENESS LEDGER (DERIVED)'),
    h3('§27.1 Coverage Summary'),
    tableHeader(['Domain', 'Status']),
  ]
  const allDomains = [
    'metadata', 'planet', 'house', 'divisional',
    'dasha_vimshottari', 'shadbala', 'ashtakavarga',
    'upagraha', 'saham', 'special_lagna', 'arudha',
    'karaka', 'yoga', 'aspect', 'panchanga', 'sade_sati',
    'varshphal', 'kp',
  ]
  for (const d of allDomains) {
    const present = store.domains_present.includes(d)
    lines.push(tableRow([d, present ? 'PRESENT' : 'ABSENT']))
  }
  lines.push(h3('§27.2 Coverage Score'))
  lines.push(`\nCoverage score: **${(store.coverage_score * 100).toFixed(1)}%** (${store.domains_present.length}/${store.domains_present.length + store.domains_missing.length} domains present)\n`)
  if (store.domains_missing.length > 0) {
    lines.push(h3('§27.3 Missing Domains'))
    lines.push(`Missing: ${store.domains_missing.join(', ')}`)
  }
  return lines.join('\n')
}

// ─── Stub section renderers (placeholder coverage for §8–§10, §14, §17–§20, §23–§25) ─

function renderStubSection(sectionNum: string, title: string, reason: string): string {
  return h2(`${sectionNum} — ${title}`) + `\n_${reason}_\n`
}

// ─── Main: render_forensic_document ──────────────────────────────────────────

/**
 * render_forensic_document — Renders the full GanitaFactStore as a Markdown
 * document in the style of FORENSIC v8.0 (chart_facts via forensic_render;
 * md archived at 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md).
 *
 * The render covers all §0–§27 sections from FORENSIC v8.0. Sections without
 * data emit placeholder lines to maintain structural completeness.
 */
export function render_forensic_document(
  store: GanitaFactStore,
  opts: ForensicRenderOptions = {},
): string {
  const { include_header = true } = opts

  const parts: string[] = []

  // ── Document header ──────────────────────────────────────────────────────
  if (include_header) {
    parts.push(`---
artifact: FORENSIC_ASTROLOGICAL_DATA_rendered
rendered_from: ganita.facts_store
chart_id: ${store.chart_id ?? 'unknown'}
ayanamsha_id: ${store.ayanamsha_id}
build_id: ${store.build_id}
generated_at: ${store.generated_at}
coverage_score: ${(store.coverage_score * 100).toFixed(1)}%
---

# FORENSIC ASTROLOGICAL DATA — RENDERED FROM FACT STORE
## Gaṇita L1 Facts Layer — Machine Rendered Projection
`)
  }

  // ── §0 — Document Index ──────────────────────────────────────────────────
  parts.push(renderDocumentIndex())
  parts.push(hr())

  // ── §1 — Core Identity / Metadata ────────────────────────────────────────
  parts.push(renderMetadata(store.metadata))
  parts.push(hr())

  // ── §2 — D1 Rashi Chart ───────────────────────────────────────────────────
  parts.push(renderPlanets(store.planets))
  // §2.3 house cusp ledger appended inline
  if (store.houses.length > 0) {
    parts.push(renderHouses(store.houses))
  }
  parts.push(hr())

  // ── §3 — Divisional Charts ────────────────────────────────────────────────
  parts.push(renderDivisionals(store.divisionals))
  parts.push(hr())

  // ── §4 — KP System ───────────────────────────────────────────────────────
  const kpRows = store.rows_by_category['kp'] ?? []
  parts.push(renderKP(kpRows))
  parts.push(hr())

  // ── §5 — Dasha Systems ────────────────────────────────────────────────────
  parts.push(renderDashas(store.dashas))
  parts.push(hr())

  // ── §6 — Shadbala ─────────────────────────────────────────────────────────
  parts.push(renderStrengths(store.strengths))
  parts.push(hr())

  // ── §7 — Ashtakavarga ────────────────────────────────────────────────────
  const avRows = store.rows_by_category['ashtakavarga'] ?? []
  parts.push(renderAshtakavarga(store.strengths, avRows))
  parts.push(hr())

  // ── §8 — Saturn Kakshya Zones ────────────────────────────────────────────
  const kakshyaRows = store.rows_by_category['kakshya'] ?? store.rows_by_category['saturn_kakshya'] ?? []
  if (kakshyaRows.length > 0) {
    parts.push(renderCategorySection('SATURN KAKSHYA ZONES (DERIVED)', kakshyaRows, '§8'))
  } else {
    parts.push(renderStubSection('§8', 'SATURN KAKSHYA ZONES (DERIVED)', 'Data derived from §7 Ashtakavarga — see rows_by_category[kakshya]'))
  }
  parts.push(hr())

  // ── §9 — Avastha Diagnostics ─────────────────────────────────────────────
  const avasthaRows = store.rows_by_category['avastha'] ?? []
  if (avasthaRows.length > 0) {
    parts.push(renderCategorySection('AVASTHA DIAGNOSTICS (DERIVED)', avasthaRows, '§9'))
  } else {
    parts.push(renderStubSection('§9', 'AVASTHA DIAGNOSTICS (DERIVED)', 'Planet state diagnostics — see rows_by_category[avastha]'))
  }
  parts.push(hr())

  // ── §10–§13 — Sensitive Points ────────────────────────────────────────────
  parts.push(renderSensitivePoints(store.sensitive_points))
  parts.push(hr())

  // ── §14 — Stellar Matrix (Navatara) ──────────────────────────────────────
  const navataraRows = store.rows_by_category['navatara'] ?? store.rows_by_category['stellar_matrix'] ?? []
  if (navataraRows.length > 0) {
    parts.push(renderCategorySection('STELLAR MATRIX / NAVATARA (DERIVED)', navataraRows, '§14'))
  } else {
    parts.push(renderStubSection('§14', 'STELLAR MATRIX / NAVATARA (DERIVED)', 'Nakshatra-relative star matrix — see rows_by_category[navatara]'))
  }
  parts.push(hr())

  // ── §15 — Panchanga DNA ───────────────────────────────────────────────────
  parts.push(renderPanchanga(store.panchanga))
  parts.push(hr())

  // ── §16 — Aspects ─────────────────────────────────────────────────────────
  parts.push(renderAspects(store.aspects))
  parts.push(hr())

  // ── §17 — Chalit Kinetic Shifts ───────────────────────────────────────────
  const chalitRows = store.rows_by_category['chalit_kinetic'] ?? store.rows_by_category['chalit'] ?? []
  if (chalitRows.length > 0) {
    parts.push(renderCategorySection('CHALIT KINETIC SHIFTS (DERIVED)', chalitRows, '§17'))
  } else {
    parts.push(renderStubSection('§17', 'CHALIT KINETIC SHIFTS (DERIVED)', 'Planet moves between Rashi and Chalit houses — see rows_by_category[chalit_kinetic]'))
  }
  parts.push(hr())

  // ── §18 — Chandra Chart ───────────────────────────────────────────────────
  const chandraRows = store.rows_by_category['chandra_chart'] ?? []
  if (chandraRows.length > 0) {
    parts.push(renderCategorySection('CHANDRA CHART (DERIVED)', chandraRows, '§18'))
  } else {
    parts.push(renderStubSection('§18', 'CHANDRA CHART (DERIVED)', 'Moon-sign chart overlay — see rows_by_category[chandra_chart]'))
  }
  parts.push(hr())

  // ── §19 — Kota Chakra ─────────────────────────────────────────────────────
  const kotaRows = store.rows_by_category['kota_chakra'] ?? []
  if (kotaRows.length > 0) {
    parts.push(renderCategorySection('KOTA CHAKRA (DERIVED)', kotaRows, '§19'))
  } else {
    parts.push(renderStubSection('§19', 'KOTA CHAKRA (DERIVED)', 'Fort wheel protective dignity — see rows_by_category[kota_chakra]'))
  }
  parts.push(hr())

  // ── §20 — Deity Assignments ───────────────────────────────────────────────
  const deityRows = store.rows_by_category['deity'] ?? []
  if (deityRows.length > 0) {
    parts.push(renderCategorySection('DEITY ASSIGNMENTS (DERIVED)', deityRows, '§20'))
  } else {
    parts.push(renderStubSection('§20', 'DEITY ASSIGNMENTS (DERIVED)', 'Ishta Devata and Dharma Devata — see rows_by_category[deity]'))
  }
  parts.push(hr())

  // ── §21 — Sade Sati Cycles ────────────────────────────────────────────────
  parts.push(renderSadeSati(store.sade_sati))
  parts.push(hr())

  // ── §22 — Varshphal ───────────────────────────────────────────────────────
  parts.push(renderVarshphal(store.varshphal))
  parts.push(hr())

  // ── §23 — Cross-Reference Matrices ───────────────────────────────────────
  const xrefRows = store.rows_by_category['cross_reference'] ?? []
  if (xrefRows.length > 0) {
    parts.push(renderCategorySection('CROSS-REFERENCE MATRICES (DERIVED)', xrefRows, '§23'))
  } else {
    parts.push(renderStubSection('§23', 'CROSS-REFERENCE MATRICES (DERIVED)', 'Derived index linking planets to houses across systems — see rows_by_category[cross_reference]'))
  }
  parts.push(hr())

  // ── §24 — Longevity Indicators ────────────────────────────────────────────
  const longevityRows = store.rows_by_category['longevity'] ?? []
  if (longevityRows.length > 0) {
    parts.push(renderCategorySection('LONGEVITY INDICATORS (FACTS)', longevityRows, '§24'))
  } else {
    parts.push(renderStubSection('§24', 'LONGEVITY INDICATORS (FACTS)', 'Kalachakra longevity + Ayurdaya — see rows_by_category[longevity]'))
  }
  parts.push(hr())

  // ── §25 — Additional Dasha Systems ───────────────────────────────────────
  const additionalDashaRows = [
    ...(store.rows_by_category['dasha_yogini'] ?? []),
    ...(store.rows_by_category['dasha_kalachakra'] ?? []),
    ...(store.rows_by_category['dasha_balance'] ?? []),
  ]
  if (additionalDashaRows.length > 0) {
    parts.push(renderCategorySection('ADDITIONAL DASHA SYSTEMS — JH (FACTS)', additionalDashaRows, '§25'))
  } else {
    parts.push(renderStubSection('§25', 'ADDITIONAL DASHA SYSTEMS — JH (FACTS)', 'Yogini, Kalachakra, and balance dashas — see rows_by_category[dasha_yogini/kalachakra]'))
  }
  parts.push(hr())

  // ── §26 — Yogas Register ─────────────────────────────────────────────────
  parts.push(renderYogas(store.yogas))
  parts.push(hr())

  // ── §27 — Completeness Ledger ─────────────────────────────────────────────
  parts.push(renderCompletenessLedger(store))

  return parts.join('')
}

// ─── Coverage checker ─────────────────────────────────────────────────────────

/**
 * FORENSIC v8.0 section list — every section that must be present in the render.
 * Used by the coverage test to assert render completeness.
 */
export const FORENSIC_V8_RENDER_SECTIONS = [
  '§0',  // Document index
  '§1',  // Core identity
  '§2',  // D1 Rashi
  '§3',  // Divisionals
  '§4',  // KP
  '§5',  // Dashas
  '§6',  // Strengths
  '§7',  // Ashtakavarga
  '§8',  // Kakshya
  '§9',  // Avastha
  '§10', // Chara Karakas (within §10–§13)
  '§11', // Sensitive points
  '§12', // Special Lagnas + Sahams
  '§13', // Arudhas
  '§14', // Navatara
  '§15', // Panchanga
  '§16', // Aspects
  '§17', // Chalit kinetic
  '§18', // Chandra chart
  '§19', // Kota Chakra
  '§20', // Deity
  '§21', // Sade Sati
  '§22', // Varshphal
  '§23', // Cross-reference
  '§24', // Longevity
  '§25', // Additional dashas
  '§26', // Yogas
  '§27', // Completeness ledger
] as const

export type ForensicSection = (typeof FORENSIC_V8_RENDER_SECTIONS)[number]

/**
 * check_render_coverage — asserts that a rendered document contains all §N
 * section markers from FORENSIC v8.0. Returns the list of missing sections.
 */
export function check_render_coverage(rendered: string): {
  coverage_ratio: number
  present: string[]
  missing: string[]
} {
  const present: string[] = []
  const missing: string[] = []
  for (const section of FORENSIC_V8_RENDER_SECTIONS) {
    // §10 appears inside "§10–§13" compound heading or standalone
    const pattern = new RegExp(`${section.replace('§', '§')}[\\s\\-—–]`)
    if (pattern.test(rendered) || rendered.includes(`## ${section}`) || rendered.includes(`#### ${section}`)) {
      present.push(section)
    } else {
      missing.push(section)
    }
  }
  return {
    coverage_ratio: present.length / FORENSIC_V8_RENDER_SECTIONS.length,
    present,
    missing,
  }
}
