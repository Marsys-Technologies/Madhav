/**
 * Spike endpoint for α0 assistant-ui fit verification.
 * Streams a hand-authored ~6k-token fixture containing code blocks, KaTeX math,
 * inline citations, reasoning, and stage data parts.
 *
 * This route is dev-only (no production traffic; master flag gates the real consume route).
 * Auth is enforced at the page level (layout.tsx in the dev route group).
 */
import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { NextRequest } from 'next/server'

/** Synthetic reasoning tokens (~300 tokens) */
const REASONING = `I need to carefully analyze this query about Rahu in the 7th house. Let me think through the classical texts first.

Parashara Hora Shastra (BPHS) Chapter 24, shlokas 14-16 discuss Rahu's placement in the 7th bhava. The key effects include:
1. Karmic intensity in the partnership domain
2. Attraction to foreign or unconventional partners
3. Possible delays in conventional marriage timeline

Now let me cross-reference with Jaimini Sutras. The 7th karaka (significator) perspective adds another layer...

Looking at the native's chart: Rahu is at approximately 23°14' Gemini (tropical) / 29°02' Taurus (sidereal Lahiri). This places it in the dual sign Gemini, amplifying the intellectual and communicative qualities of partnerships.

The Vimshottari dasha system puts Rahu MD from 2009-2027, which is the current operational period. This makes the 7th house Rahu ESPECIALLY active right now.

Cross-referencing with MSR signals: R.127 (Rahu 7H confirmed), R.089 (Venus as 7L in 4H), R.203 (Rahu MD active 2009-2027). The convergence across three MSR signals gives this a high-confidence rating.

Let me now compose the synthesis response incorporating these layers...`

/** Synthetic answer text (~1500 tokens with code blocks, math, and citations) */
const ANSWER_PARTS = [
  `## Rahu in the 7th House — Multi-Layer Synthesis

Based on the L1 chart data (FORENSIC §3.2.1) and the L2.5 synthesis corpus, Rahu's placement in the 7th bhava represents one of the highest-signal areas in this native's chart. This analysis integrates Classical Jyotish, Jaimini, and Krishnamurti layers.

---

### Primary Classical Signature

Per **Parashara Hora Shastra (BPHS) Chapter 24, shlokas 14–16**, Rahu in the 7th produces:

1. **Karmic partnerships** — The native is drawn toward relationships that carry a sense of fate or inevitability. Partners may be from markedly different backgrounds, cultures, or philosophies. [^1]

2. **Unconventional timing** — Marriage may occur outside the expected social timeline: either significantly earlier or later than peer norms, or under unusual circumstances. [^2]

3. **Foreign or cross-cultural connections** — Rahu in angular houses (1, 4, 7, 10) amplifies the cross-cultural signature. The 7th specifically ties this to *long-term* partnerships rather than casual encounters. [^3]

---

### Mathematical Position Verification

`,
  `The native's Rahu position (Swiss Ephemeris, from FORENSIC §2.1):

| System | Longitude | Nakshatra | Pada |
|---|---|---|---|
| Tropical | 23°14' Gemini | Punarvasu | 3 |
| Sidereal (Lahiri) | 29°02' Taurus | Mrigashira | 4 |

The **nodal axis** spans the 1st–7th axis, creating a karmic polarity between self-expression (1H) and partnership (7H). The mean nodal motion formula:

$$\\Delta_{\\text{nodal}} = -0.0529°/\\text{day (retrograde)}$$

Full nodal cycle:

$$T_{\\text{cycle}} = \\frac{360°}{0.0529°/\\text{day}} \\approx 6793 \\text{ days} \\approx 18.6 \\text{ years}$$

This means the Rahu–Ketu axis completes one cycle approximately every 18.6 years, which aligns with the **Saros cycle** observed in eclipse patterns — a non-coincidental correlation per Krishnamurti Paddhati's emphasis on astronomical resonance.

---

### Swiss Ephemeris Verification Code

`,
  `\`\`\`python
import swisseph as swe
from datetime import datetime

def verify_rahu_position(birth_year: int, birth_month: int, birth_day: int,
                          birth_hour_ut: float) -> dict[str, float]:
    """
    Compute Rahu's true node and mean node positions for verification.
    Returns both tropical and sidereal (Lahiri) longitudes.
    """
    jd = swe.julday(birth_year, birth_month, birth_day, birth_hour_ut)

    # True Node (Rahu)
    true_node_result = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SPEED)
    rahu_tropical = true_node_result[0][0]  # longitude in degrees

    # Mean Node for comparison
    mean_node_result = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SPEED)
    rahu_mean = mean_node_result[0][0]

    # Lahiri ayanamsa correction
    ayanamsa = swe.get_ayanamsa_ut(jd)  # ~24.12° for 1984
    rahu_sidereal = (rahu_tropical - ayanamsa) % 360

    return {
        "tropical_lon": rahu_tropical,
        "sidereal_lahiri_lon": rahu_sidereal,
        "mean_node_tropical": rahu_mean,
        "ayanamsa": ayanamsa,
        "speed_deg_day": true_node_result[0][3]  # typically ~-0.0529°/day
    }

# Native's birth data
result = verify_rahu_position(1984, 2, 5, 5.217)  # 10:43 IST = 05:13 UT
print(f"Rahu (true node) tropical:  {result['tropical_lon']:.4f}°")
print(f"Rahu sidereal (Lahiri):     {result['sidereal_lahiri_lon']:.4f}°")
print(f"Ayanamsa (1984-02-05):      {result['ayanamsa']:.4f}°")
\`\`\`

---

### MSR Signal Convergence

The Multi-Signal Repository surfaces three corroborating signals: [^1] [^4]

`,
  `| Signal | Description | Confidence | Layer |
|---|---|---|---|
| **MSR.R.127** | Rahu in 7H (Swiss Ephemeris confirmed; 23°14' Gemini tropical) | 0.97 | L1 FORENSIC |
| **MSR.R.089** | Venus (7L for Scorpio lagna) in 4H — 7L deposited in angular house | 0.88 | L2.5 synthesis |
| **MSR.R.203** | Rahu Mahadasha active 2009–2027 (18-year Vimshottari period) | 0.99 | L1 temporal |

The convergence of these three signals raises the synthesis confidence to **0.91** (weighted mean per CDLM §5.1 methodology). [^4]

---

### Dasha Context (Current Period)

Rahu Mahadasha began in **2009** and extends to **2027**. During this 18-year period, ALL natal promises indicated by Rahu's placement are operationalized. Practically, this means:

- Partnership themes have been (and continue to be) **the central experiential axis** for this native.
- The Rahu-7H signature is not a background indicator — it is **currently in full activation**.
- Sub-period (antardasha) lords modify the expression: current Rahu–Jupiter period (if applicable) amplifies wisdom, teaching, and long-distance partnership themes.

The Vimshottari period calculation:

$$\\text{Mahadasha years} \\times \\frac{\\text{elapsed longitude}}{\\text{total nakshatra arc}} = \\text{years elapsed}$$

For Rahu MD (18 years), with Rahu at 29°02' Taurus sidereal:
- Mrigashira nakshatra (Mars-ruled, 23°20'–6°40' in two halves) → pada 4 in Taurus
- Elapsed fraction at birth ≈ 0.73 of the Rahu nakshatra arc remaining in previous MD

---

### Cross-Domain Linkage (UCN §2.4, CDLM §5.1)

The Rahu-7H signal links to three other domains via the Cross-Domain Linkage Matrix: [^3]

1. **Career domain** — 7H is also the house of "open enemies" and negotiation. Rahu here amplifies non-conventional professional partnerships, consulting relationships, and cross-cultural business.

2. **Health domain** — Via 7H rulership of the lower back and kidneys in Jyotish body-mapping; Rahu's affliction potential (moderated by Jupiter's aspect in this chart) warrants attention.

3. **Psychological domain** — Shadow-self projection onto partners is a classical Rahu-7H psychological pattern. Recognition of this dynamic is the primary remedial direction.

---

### Synthesis Verdict

Rahu in the 7th bhava is the **single highest-confidence karma-indicator** in this native's chart for the current epoch (Rahu MD 2009–2027). The classical, mathematical, and temporal layers all converge on an **acharya-grade conclusion**: partnerships for this native carry exceptional karmic weight, are likely to manifest in unconventional form, and are currently in maximum activation.

---

**References:**

[^1]: FORENSIC §3.2.1; MSR.R.127; BPHS Chapter 24, shlokas 14–16
[^2]: UCN §2.4, cross-domain linkage CL.47 (partnership timing)
[^3]: CDLM §5.1, convergence cluster CC.12; UCN §2.4 CL.23
[^4]: MSR.R.203; FORENSIC §5.1 (Vimshottari timeline); CDLM §5.2`
]

/** Spike fixture stage events */
const STAGE_EVENTS = [
  { type: 'data', value: { type: 'stage', stage: 'classify', status: 'done', ms: 87 } },
  { type: 'data', value: { type: 'stage', stage: 'compose_bundle', status: 'done', ms: 312 } },
  { type: 'data', value: { type: 'stage', stage: 'plan_per_tool', status: 'done', ms: 156 } },
  { type: 'data', value: { type: 'stage', stage: 'tool_fetch', status: 'done', ms: 892 } },
  { type: 'data', value: { type: 'stage', stage: 'synthesis', status: 'done', ms: 4200 } },
]

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  const _messages = body.messages ?? []

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const reasoningId = 'reasoning-1'
      const textId = 'text-1'

      // Emit reasoning tokens
      writer.write({ type: 'reasoning-start', id: reasoningId })
      const reasoningChunks = REASONING.match(/.{1,80}/g) ?? []
      for (const chunk of reasoningChunks) {
        writer.write({ type: 'reasoning-delta', id: reasoningId, delta: chunk })
        await sleep(8)
      }
      writer.write({ type: 'reasoning-end', id: reasoningId })

      // Emit answer text in parts (simulating streaming)
      writer.write({ type: 'text-start', id: textId })
      for (const part of ANSWER_PARTS) {
        const chunks = part.match(/.{1,120}/g) ?? []
        for (const chunk of chunks) {
          writer.write({ type: 'text-delta', id: textId, delta: chunk })
          await sleep(4)
        }
      }
      writer.write({ type: 'text-end', id: textId })

      // Emit metadata (cost + stage events)
      writer.write({
        type: 'message-metadata',
        messageMetadata: {
          model: 'claude-3-7-sonnet-20250219',
          input_tokens: 4821,
          output_tokens: 1536,
          reasoning_tokens: 312,
          dollars: 0.0287,
          latency_ms: 5647,
          stage_events: STAGE_EVENTS.map((e) => e.value),
        },
      })
    },
  })

  return createUIMessageStreamResponse({ stream })
}
