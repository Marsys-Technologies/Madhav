---
artifact: VISUAL_CONTRACT_v2.md
status: LOCKED
arc_id: build_e2e_arc
authored_by: Cowork (native-approved 2026-05-31)
role: The native-approved visual contract Stream C implements. Match or exceed.
---

# Visual Contract v2 — what Stream C must implement

The native reviewed three rounds of mockups and locked v2. Stream C's job
is to implement what the v2 mockup specifies, matching it on first pass
and elevating further where natural (typography precision, animation
quality, microcopy).

## Theme tokens (non-negotiable)

| Token | Value | Where used |
|---|---|---|
| `--obsidian-bg` | `#08070a` | Page background, frame interior |
| `--obsidian-panel` | `#0a0908` to `#0c0b0e` | Inset panels, cards |
| `--obsidian-border` | `#1f1c17` to `#2a2620` | Hairline dividers, card borders |
| `--gold-primary` | `#d4a648` | Headings, primary CTA, lit nodes, accents |
| `--gold-light` | `#e8c878` to `#f8e6a8` | Subtle accents, running-node fills, hover |
| `--gold-deep` | `#5a3a1f` | Warning-tinted borders (Rebuild all) |
| `--text-primary` | `#e8e6df` | Body text |
| `--text-secondary` | `#888373` | Captions, secondary |
| `--text-tertiary` | `#5d5b54` | Micro-labels, hints |
| `--success` | `#9bd49a` | Complete status |
| `--danger` | `#e89a9a` | Failed status |

## Typography stack

- **Headings + Sanskrit names:** `'Cormorant Garamond', serif`, weight 500, often italic for Sanskrit
- **Body + UI labels:** `'Inter', sans-serif`, weights 400 and 500 only
- **Numeric telemetry + monospace:** `'JetBrains Mono', monospace`

Font sizes:
- Page-title Sanskrit headings: 32-36px serif italic
- Section Sanskrit headings: 22px serif italic
- Asset name (rows + graph): 15px serif (non-italic)
- Body: 13-14px sans
- Micro-labels: 10-11px sans, letter-spacing 0.08-0.1em, uppercase

## Sanskrit asset name map (must be in `lib/jyotish/asset_names.ts`)

```typescript
export const ASSET_NAMES = {
  // Adhara · L1 · Foundation
  pratyaksha:        { sanskrit: 'Pratyaksha',        english: 'Direct perception', subtitle: 'Forensic chart' },
  panchanga:         { sanskrit: 'Panchanga',         english: 'Five limbs',         subtitle: 'Daily almanac' },
  drishti_lakshana:  { sanskrit: 'Drishti Lakshana',  english: 'Sensitive points',   subtitle: 'ARMC, ASC, Vertex' },
  graha_sthana:      { sanskrit: 'Graha Sthana',      english: 'Planet positions',   subtitle: 'Across ayanamshas' },
  bhava_vibhaga:     { sanskrit: 'Bhava Vibhaga',     english: 'House divisions',    subtitle: 'Cusps + lords' },
  varga:             { sanskrit: 'Varga',             english: 'Divisional charts',  subtitle: 'D1 through D60' },
  dasha_krama:       { sanskrit: 'Dasha Krama',       english: 'Period sequence',    subtitle: 'Vimshottari + Yogini + Chara' },
  yoga_sambandha:    { sanskrit: 'Yoga Sambandha',    english: 'Yoga relationships', subtitle: 'Raja, Dhana, Pancha-Mahapurusha' },

  // Sambandha · L2.5 · Synthesis
  lakshana_kosha:    { sanskrit: 'Lakshana Kosha',    english: 'Treasury of indicators', subtitle: 'MSR · 573 signals' },
  karana_jala:       { sanskrit: 'Karana Jala',       english: 'Net of causes',          subtitle: 'CGM · conditional graph' },
  anubandha_mandala: { sanskrit: 'Anubandha Mandala', english: 'Matrix of linkages',     subtitle: 'CDLM · cross-domain' },
  upaya_kosha:       { sanskrit: 'Upaya Kosha',       english: 'Treasury of remedies',   subtitle: 'RM · 6 traditions' },
  sangam:            { sanskrit: 'Sangam',            english: 'Confluence',             subtitle: 'UCD · folded into Karana + Anubandha' },

  // Sutra · L3 · Meta-threads
  kala_yoga:         { sanskrit: 'Kala Yoga',         english: 'Time-synchronicity',     subtitle: 'A15 · convergence map' },
  bandha:            { sanskrit: 'Bandha',            english: 'Phase-locked anchors',   subtitle: 'A16 · M6 ground truth' },
  chakra_vichara:    { sanskrit: 'Chakra Vichara',    english: 'Chakra analysis',        subtitle: 'A17' },
  vedha_drishti:     { sanskrit: 'Vedha Drishti',     english: 'Vedha aspects',          subtitle: 'A18' },
  bhrigu_kshetra:    { sanskrit: 'Bhrigu Kshetra',    english: 'Bhrigu transit field',   subtitle: 'A19' },
  tajik_varsha:      { sanskrit: 'Tajik Varsha',      english: 'Annual revolution',      subtitle: 'A20' },
  sphurana:          { sanskrit: 'Sphurana',          english: 'Aspect ignition',        subtitle: 'A21 · exact aspects' },
  kala_smriti:       { sanskrit: 'Kala Smriti',       english: 'Per-varsha digest',      subtitle: 'A22' },

  // Vyavahara · L4 · Interface
  prashna:           { sanskrit: 'Prashna',           english: 'Inquiry',                subtitle: 'Consume chat' },
  yantra_mcp:        { sanskrit: 'Yantra',            english: 'MCP surface',            subtitle: 'Tool access' },
  marga:             { sanskrit: 'Marga',             english: 'API path',               subtitle: 'REST routes' },
} as const

export const LAYER_NAMES = {
  L1:    { sanskrit: 'Adhara',     english: 'Foundation' },
  L2_5:  { sanskrit: 'Sambandha',  english: 'Synthesis' },
  L3:    { sanskrit: 'Sutra',      english: 'Meta-threads' },
  L4:    { sanskrit: 'Vyavahara',  english: 'Interface' },
} as const
```

## Three pages — implementation contracts

### Page 1 — `/clients/new` — Naya Yantra

Layout (top to bottom):
1. Header bar: gold glyph (`॥`) + MARSYS wordmark serif + "Jyotish Instrument" micro-label + crumb "Charts · New" right-aligned + "Step 1 of 2" pill
2. Hero: 36px Cormorant italic "Naya Yantra" + 13px secondary description
3. Section: **Vyakti · Identity** — 3-column grid: Full name | Preferred name | Gender (140px)
4. Section: **Janma Sthana · Birth coordinates** — 3-column grid: Date (DD MM YYYY) | Time (HH MM local) | Time zone select. Below: full-width Birth place input with Places autocomplete confirmation line. Below that: collapsed "Manual override" accordion
5. Section: **Ganana · Compute** — 3-column grid of 6 ayanamsha cards (5 standard + 1 Custom slot), each with checkbox + name + subtitle
6. Footer: left-aligned microcopy "5 ayanamshas × 28 assets = 140 nodes" + right-aligned Cancel + Compute chart (gold) buttons

### Page 2 — `/clients/<id>/build` — Yantra Chitra

Layout (top to bottom):
1. Header bar: glyph + native name (Cormorant 18px) + DD MM YYYY · time · place micro-label · ayanamshas. Right side: 4 buttons in order Stop · Continue · Rebuild all (warning-tinted) · Build (gold primary)
2. **Sampurna gati overall progress bar**: section label italic Cormorant 14px + monospace count "47 / 140 nodes · 33.6% · ETA 11m 42s" right-aligned. 6px tall track, gold fill. Below: 5 per-ayanamsha sub-counts in monospace 9px
3. **Yantra Chitra force-graph panel** (#0a0908 inset card):
   - Header: "Yantra Chitra" Cormorant italic + "Live dependency graph · 28 assets · synced to data plane" caption
   - Right: legend pills (Complete N · Running N · Pending N) in monospace
   - SVG graph: 4 columns labeled Adhara · Sambandha · Sutra · Vyavahara at top + L1/L2.5/L3/L4 micro-labels. Dashed gutter dividers between columns. Nodes positioned by column, vertical spacing reflects asset count. Edges drawn with `marker-end` arrows in `#3a3328`; LIVE edges (currently transferring data) in `#d4a648` with `marker-end` lit arrow. Node states: complete = filled gold circle, running = outlined circle + SVG arc progress ring (renders the current percent), pending = outlined dim circle, failed = outlined red circle, skipped = dimmer outline + line-through. Vyavahara nodes rendered as rounded rects (terminal surfaces, not assets).
   - Telemetry strip below: QPS · WRITERS · QUEUE · SIDECAR · BUILD ID in monospace
4. **Per-layer asset tables**: each layer has a Sanskrit section heading (e.g. "Adhara · Foundation · L1 · 8 of 8 complete"). Rows are 5-column grid: row_num (2-digit monospace) | name + subtitle | progress bar | row count (monospace) | status pill or % readout
5. Footer hint: "Click any row to Rebuild just that asset · the cascade preview will show downstream nodes that get invalidated and recomputed"

### Page 3 — `/clients/<id>/consume` — Prashna

Layout:
1. Header bar: glyph + native name + "Chart built · 28 assets · 5 ayanamshas · last refreshed Nm ago" micro-label. Right: "Fully ready" pill + Trace button
2. Hero: 32px Cormorant italic "Prashna" + "Inquiry · ask the chart anything · every answer grounded in your data" + tier label right-aligned
3. Two-column layout (1fr 200px):
   - Left: User question in Cormorant italic 14px inside gold-left-bordered card · Assistant response in 14px sans with Sanskrit layer names threaded inline (Adhara / Sambandha / Sutra) in Cormorant italic gold, citations as superscript monospace `[N]`
   - Right rail: "Citations · N" header + numbered list with `[N]` + source table name in monospace
4. **Anuprashna · follow-up inquiries**: micro-label header + chip row (Cormorant placeholder feel)
5. Composer: message icon + input (italic Cormorant placeholder) + ⌘↵ kbd hint + Send button (gold)

## Animation expectations (Stream C target, ≥)

- Progress rings: visible CSS animation showing the arc filling smoothly as percent changes (`stroke-dashoffset` transition)
- New node accretion: 200-300ms fade-in + slight scale when the cockpit receives a `node_added` SSE event
- Active edge lighting: 800ms pulse on the lit edge stroke color when an `edge_added` event arrives
- Overall progress bar: smooth interpolation, not snap-on-update

## Acceptance — Stream C passes when

- A pixel-comparison against the v2 mockup shows the cockpit hero panel, asset tables, and form sections substantially matching
- Sanskrit names appear in cockpit, consume responses, and asset tables (no bare "MSR" / "CGM" without their Sanskrit name)
- Progress rings animate during a real build
- SSE events drive node accretion + edge lighting (depends on Stream B's R1 also landing)
- All theme tokens flow through `:root` CSS variables and are reused (no hardcoded hex outside the tokens file)

---

End of visual contract.
