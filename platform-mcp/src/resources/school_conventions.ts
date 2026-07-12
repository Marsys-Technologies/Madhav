/**
 * school_conventions.ts — MCP resource: marsys://school-conventions
 *
 * Static reference: 4 Jyotish schools, what each is authoritative for,
 * output-form differences, known disagreements, classical anchors.
 * Uniform across all tiers. ~2.5k tokens.
 *
 * MCPT v3.1.0-S3
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const SCHOOL_CONVENTIONS_TEXT = `# MARSYS-JIS School Conventions
**MCP Resource: \`marsys://school-conventions\`**
*Static reference — uniform across all tiers. Rarely changes.*
*Authoritative schools: Parashara · Jaimini · KP · Tajaka*

---

## 1. Parashara (Primary School)

**What it is authoritative for:**
- Natal chart analysis (D1 Rasi chart, divisional charts D9/D10/D7/D4 etc.)
- Graha drishti (planetary aspects — 4th, 7th, 8th, 12th from planet by default; Mars 4/8/7+, Jupiter 5/9/7+, Saturn 3/10/7+)
- Yoga identification (Raj Yoga, Dhana Yoga, Parivartana Yoga, Neechabhanga, etc.)
- Vimshottari Dasha (120-year cycle: Ketu 7 → Venus 20 → Sun 6 → Moon 10 → Mars 7 → Rahu 18 → Jupiter 16 → Saturn 19 → Mercury 17)
- Bhava Chalit chart (shifted house cusps)
- Shadbala (planetary strength system — six factors)

**Classical anchors:**
- Brihat Parashara Hora Shastra (BPHS) — primary text
- Saravali (Kalyana Varma)
- Phaladeepika (Mantreswara)

**Output form:**
- House-lord significations (1st lord, 2nd lord, etc.)
- Yoga descriptions + strength
- Dasha–antardasha timeline

---

## 2. Jaimini

**What it is authoritative for:**
- Karakatva system (planet-based significations by degree order)
  - 7-karaka: AK (Atmakaraka), AmK (Amatyakaraka), BK (Bhatrikaraka), MK (Matrikaraka), PiK (Pitrikaraka), PK (Putrakaraka), GK (Gnatikaraka)
  - 8-karaka: adds DK (Darakaraka) — invoked for relationship + ancestral karma
- Chara Dasha (sign-based maha dasha system)
- Arudha Lagna (AL) and Pada positions
- Rashi aspects (all four kendra signs aspect each other; movable signs aspect fixed except adjacent; fixed signs aspect dual except adjacent; dual signs aspect movable except adjacent)

**Classical anchors:**
- Jaimini Sutram (attributed to Maharishi Jaimini)
- Jaimini Sutramritam (P.S. Sastri commentary)

**Output form:**
- Karaka planet names + degrees
- Chara Dasha sign periods
- Arudha chart positions

**Known disagreements with Parashara:**
- Dasha system: Jaimini Chara Dasha ≠ Parashara Vimshottari. Both are valid; they answer different questions.
- House significations: Jaimini uses Arudha Lagna as a secondary chart foundation.
- Aspects: Jaimini rashi aspects differ from Parashara graha drishti. Do NOT conflate them.

---

## 3. KP (Krishnamurti Paddhati)

**What it is authoritative for:**
- Sub-lord analysis (each sign divided into 249 subs proportional to Vimshottari years)
- Cuspal sub-lord (the sign/nakshatra/sub at each house cusp determines if the house "fructifies")
- Significators for houses 6/10/11 (primary lens for employment/career events)
- Precise event-timing within dasha periods

**Classical anchors:**
- KP Reader (K.S. Krishnamurti, 6 volumes)
- Stellar Astrology (K.S. Krishnamurti)

**Output form:**
- Sub-lord tables for each house cusp
- Significator lists per house
- Event timing: when running dasha lord = sub-lord significator

**Known disagreements:**
- Ayanamsha: KP uses Krishnamurti ayanamsha (~23°05′ for 1984); MARSYS uses Lahiri (23°37′). This shifts nakshatra positions slightly. KP-specific queries should use KP ayanamsha values from FORENSIC §KP if available.
- Node type: KP uses True Node; MARSYS primary uses Mean Node. KP rows in chart_facts (category: kp_cusp) use KP-specific positions.

---

## 4. Tajaka (Varshaphal / Annual Chart)

**What it is authoritative for:**
- Annual chart (Varshaphal): chart cast for the moment the Sun returns to its natal degree each year
- Muntha: a sensitive point that moves ~1 sign per year
- Tajaka yogas (Ithasala, Ishrafa, Nakta, Khallasara, etc.) — based on applying vs separating aspects
- Annual dasha systems (Mudda Dasha, Panchottari Dasha for annual chart)

**Classical anchors:**
- Tajaka Neelakanthi (Neelakantha)
- Brihat Tajaka (Balabhadra)

**Output form:**
- Annual chart positions for each Varshaphal year
- Tajaka yoga list for the annual chart
- Muntha sign + house

**Known disagreements:**
- Tajaka uses Sayana (tropical) positions for some calculations. FORENSIC §22 uses Nirayana (sidereal) for MARSYS consistency.
- Annual dasha systems vary across Tajaka texts; MARSYS uses Mudda Dasha as primary.
- KP and Tajaka data (chart_facts categories: kp_cusp, kp_planet, kp_significator, varshphal) are backfilled in phase v3.3 — queries before that phase return 0 rows.

---

## 5. School Convergence Index

When \`cross_school_lookup\` returns a \`convergence_score ≥ 0.75\`, the claim is considered high-confidence cross-school. Scores:

| Score | Interpretation |
|---|---|
| 1.00 | All 4 schools agree |
| 0.75 | 3 of 4 agree |
| 0.50 | 2 of 4 agree |
| 0.25 | 1 of 4 agrees |
| 0.00 | All schools silent or disagree |

For scores < 0.50: report each school's stance explicitly; do not synthesize as if consensus exists.

---

## 6. Tool Routing by School

| Question type | Primary tool | Secondary |
|---|---|---|
| Natal synthesis | \`holistic_bundle\` + \`query_signals\` | \`vector_search\` (UCN) |
| Jaimini karakas | \`query_chart_facts(category: "dasha_chara")\` | — (\`cross_school_lookup\` PARKED, F-WP17-1) |
| KP significators | \`query_chart_facts(category: "kp_significator")\` | \`query_chart_facts(category: "kp_cusp")\` |
| Tajaka annual | \`query_chart_facts(category: "varshphal")\` | \`query_chart_facts(category: "muntha")\` |
| Multi-school claim | \`multi_school_bundle\` (per-school evidence; \`cross_school_lookup\` PARKED, F-WP17-1) | — |

---

*End school conventions. v3.1.0-S3. Update when classical text indexing (v3.2) expands coverage.*
`

export function registerSchoolConventions(server: McpServer): void {
  server.resource(
    'school-conventions',
    new ResourceTemplate('marsys://school-conventions', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://school-conventions',
          mimeType: 'text/markdown',
          text: SCHOOL_CONVENTIONS_TEXT,
        },
      ],
    })
  )
}
