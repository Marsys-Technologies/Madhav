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
- Sub-lord analysis. The zodiac carries **249** sub-lord divisions: each of the 27 nakshatras is divided into 9 subs proportional to Vimshottari years (243 segments), and the 12 rashi boundaries cut 6 of those in two — 243 + 6 = 249. Stored as the L0 reference table \`bg_kp_sublord_division\`, in SIDEREAL longitude with no ayanamsha key (the sidereal division is ayanamsha-invariant).
- Cuspal sub-lord (the sign/nakshatra/sub at each house cusp determines if the house "fructifies")
- Significators for houses 6/10/11 (primary lens for employment/career events)
- Precise event-timing within dasha periods

**Classical anchors:**
- KP Reader (K.S. Krishnamurti, 6 volumes)
- Stellar Astrology (K.S. Krishnamurti)
- **Corpus status: NOT INGESTED.** No KP source text is present in \`classical_text_chunks\`. KP-specific conventions in this instrument are verified against a committed fixture (\`05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md\` §2/§6), NOT against ingested text. Do not claim a corpus citation for a KP convention.

**Output form:**
- Sub-lord tables for each house cusp
- Significator lists per house
- Event timing: when running dasha lord = sub-lord significator

**Where the data actually lives** (\`chart_facts.fact_category\`, corrected 2026-08-02 — the four names this resource previously listed, \`kp_cusp\` / \`kp_planet\` / \`kp_significator\` / \`varshphal\`, have **0 rows in production** and never existed as categories):

| fact_category | grain | emitted by |
|---|---|---|
| \`graha_kp_lords\` | per graha + Lagna: star / sub / sub-sub / prana lord | \`ga_nakshatra\` |
| \`cusp_kp_lords\` | per cusp (CUSP_01..12): the same 4-level chain | \`ga_nakshatra\` |
| \`kp_house_significators\` | per house (HOUSE_01..12): the 4-limbed ladder + owner + ranking | \`ga_nakshatra\` |
| \`kp_planet_significations\` | per graha: houses signified at each level, both house frames | \`ga_nakshatra\` |
| \`kp_cuspal_significators\` | per cusp: the cusp's own [sign_lord, star_lord, sub_lord] chain | \`ga_sensitive\` |
| \`kp_ruling_planets_natal\` | 5 natal ruling-planet roles (fixed at birth, NOT query-moment) | \`ga_sensitive\` |
| \`bhava_cusps\` | 12 houses x {sripati, placidus} x {start, madhya, end} | \`ga_positions\` |

**The 4-limbed significator ladder** (\`kp_house_significators\`), strongest first — this is KP's own judgment rule and has no Parashari analogue:
1. \`level_a_star_of_occupants\` — planets tenanting the STAR of an occupant of the house
2. \`level_b_occupants\` — the occupants
3. \`level_c_star_of_owner\` — planets tenanting the star of the house's OWNER
4. \`level_d_owner\` — the owner
\`ranked_significators\` is the deduped union in that order. An empty limb reports the literal \`none\`. KP's nodal agency rule (Rahu/Ketu acting for conjoined/aspecting planets) is NOT applied — each node carries an explicit \`nodal_agency_not_applied\` disclosure row.

**Known disagreements:**
- Ayanamsha: KP uses the Krishnamurti ayanamsha (~23°05′ for 1984); the project's primary elsewhere is Lahiri (23°37′). This is served as DATA, not reconciled: all 5 ayanamshas including \`krishnamurti\` are stored per chart, and \`ganita_kp_cusps_get\` already DEFAULTS to \`ayanamsha_id='krishnamurti'\`.
- House system: KP is cuspal (Placidus); the project's primary frame is whole-sign. Both are stored — \`bhava_cusps\` holds Placidus AND Sripati, and \`kp_planet_significations\` carries \`kp_cuspal_house\`, \`whole_sign_house\` and an explicit \`house_system_divergence\` flag per graha. A planet can be 9th cuspally and 10th whole-sign; neither value overwrites the other.
- Node type: KP uses True Node; the project's primary uses Mean Node.
- KP is NOT an independent timing generator. \`chart_dashas.system_id='vimshottari_kp'\` sub-periods are proportional subdivisions of the SAME Vimshottari windows already counted once — which is why the transit-permission plurality count deliberately excludes them. KP's independence is a judgment-method independence, not a clock.

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
- Tajaka rows live under \`chart_facts\` categories prefixed \`tajik_%\`, not \`varshphal\` — that name has 0 rows in production and is not a real category. For the KP categories see the table in §3 above; the "backfilled in phase v3.3" note was stale and is removed — KP and Tajaka rows are live on both canonical charts across all 5 ayanamshas.

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
| KP cusps / sub-lords | \`ganita_kp_cusps_get\` (dedicated serving face; defaults to \`ayanamsha_id='krishnamurti'\`) | \`ganita_chart_facts_get(category: "cusp_kp_lords")\` |
| KP significators | \`ganita_chart_facts_get(category: "kp_house_significators")\` | \`ganita_chart_facts_get(category: "kp_planet_significations")\` |
| Tajaka annual | \`ganita_tajaka_get\` | \`ganita_chart_facts_get\` on a \`tajik_*\` category |
| Multi-school claim | \`multi_school_bundle\` (per-school evidence; \`cross_school_lookup\` PARKED, F-WP17-1) | — |

---

*End school conventions. v3.1.1-S3 (2026-08-02, ṢAḌ-DARŚANA W3K Lane 1 §3 housekeeping: §3's KP fact_category names corrected — the four previously documented (\`kp_cusp\`, \`kp_planet\`, \`kp_significator\`, \`varshphal\`) have 0 rows in production and never existed, so an LLM consumer reading this resource was being told to query categories that do not exist; §3 gains the 249-division derivation, the 4-limbed significator ladder, the corpus NOT-INGESTED disclosure, and the ayanamsha/house-system divergences as served data; §6's routing table re-pointed at the real live tools. The retired planner-facing names \`kp_query\` / \`query_kp_ruling_planets\` are deliberately NOT re-instated — that question was raised by W3K_SUBSTRATE_INVENTORY §3 but is UNRULED in the Night-3 and Night-5 adjudications, so the conservative path is taken and the phantom-dropped disposition stands. Update when classical text indexing expands coverage.)*
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
