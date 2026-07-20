/**
 * tools/reading_notes.ts — D-2 Lane V-3, ledger row 25 (CR-38/71/80).
 *
 * Per-chart verified reading-notes, served as a TOOL. CR-38/71/80 in
 * POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md are LOGGED reading-notes (verified chart knowledge,
 * NOT defects) with the standing disposition "Carry into every future 482012f1 reading." They lived
 * only in the register — invisible to any consuming LLM. This surfaces them so a reading agent
 * inherits the verified structure instead of re-deriving (and possibly mis-deriving) it.
 *
 * SCOPE NOTE: the brief names these "MCP resources" (row 25), but MCP resources live in
 * platform-mcp/src/resources/** which is Lane V-2's may_touch glob — outside V-3's. To stay in
 * scope (scope-warden), V-3 delivers the identical content through a tool in tools/** (V-3's glob).
 * The content + chart-keying are what the DONE criterion checks; a resource wrapper over this same
 * getter is a trivial V-2/integration follow-up if the resource FORM is required.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { budgetMcpContent } from '../lib/response_budget.js'

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// Verbatim from POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md rows CR-38 / CR-71 / CR-80.
export const READING_NOTES_482012F1 = `# Verified Reading-Notes — chart 482012f1 (Abhisek Mohanty)

*Source: POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md rows CR-38 / CR-71 / CR-80 — LOGGED reading-notes (verified chart knowledge, not defects). Disposition: carry into every future 482012f1 reading. These are STRUCTURE cues, not a substitute for the served signals/verdicts — always confirm against the live tools.*

## Dhana / wealth structure (CR-71)
- **Dhana Yoga:** 2L Venus (H9, Purva Ashadha, shadbala 4.64) conjunct 9L Jupiter (H9, own Sagittarius, Mula, 7.80). **Arudha Lagna also in H9**, on top of the yoga.
- **Śaśa Yoga (PMP):** Saturn exalted H7 Libra (10L+11L, 7.83).
- **Budha-Āditya:** Sun 22°11′ + Mercury 1°09′ H10 Capricorn, 21° apart — **non-combust → fires**. Mercury **vargottama** (Capricorn D1/D9).
- **Wealth-loss mechanism:** exalted Rahu (Rohiṇī) IN H2 + **8L Mars full aspect on H2 at strength 1.00** (fact 82cc6f52) + Mars–Saturn conjunct H7 (partners). Full **2/11 axis** tenanted (Rahu H2, Moon H11 at 29°46′).
- **Varga collapse (D9):** Venus **debilitated** (Virgo), Saturn **debilitated** (Aries), Jupiter → 12th; **both debilities carry NBRY grounds** (Sun in D9 lagna kendra; Mercury in D9 kendra).
- **D2:** Venus/Saturn/Mercury/Moon all H12, Chandra-hora; Sun (own)/Jupiter/Rahu in Leo H1, Sūrya-hora; Mars **debilitated** D2.
- **D11:** Venus **EXALTED** (Pisces), Saturn in H11.
- **Shadbala order:** Sun 8.47 > Saturn 7.83 > Jupiter 7.80 > Mercury 7.55 > Moon 5.65 > Mars 5.57 > **Venus 4.64** > Ketu 0.625 > Rahu 0.375.

## Dasha spine (CR-38, CR-71)
- Mercury MD (3L/6L, no dhana participation) 2010-08-18 → **2027-08-18/19**.
- **Ketu MD (H8, shadbala 0.625) 2027-08-18 → 2034-08-18.** Sub-windows: Ketu-Venus 2028-01-15→2029-03-16 (first preview); **Ketu-Rahu 2030-07-19→2031-08-06 (highest loss/fraud risk)**; Ketu-Jupiter 2031-08→2032-07 and Ketu-Saturn 2032-07→2033-08 (the two constructive windows).
- **VENUS MD 2034-08-18 → 2054-08-18 (20y)** — Venus-Venus to 2037-12-18 = the dhana dasha, activation of full financial potential. Venus is MD lord 2034–2054, so the 2034 activation is an NBRY maturing.

## Yogas / karakas / special lagnas (CR-80)
- **Kāla-Sarpa: D1 = NONE** (Rahu H2 / Ketu H8; Mars + Saturn in H7 break the hemming). Fires only in ~18 vargas (D2/D10 Rahu-H1, D6, D12, D16, D20, D24…).
- **Anapha Yoga genuinely fires** (Mercury in 12th-from-Moon) → **Kemadruma is FALSE.** Also firing: Śaśa (PMP), Vasi.
- **Chara karakas:** AK=Moon, AmK=Saturn, BK=Sun, MK=Venus, PiK=Mars, GK=Jupiter/Rahu, DK=Mercury; **Karakāṁśa = Gemini.**
- **Special lagnas:** Indu(Dhana) Scorpio H8 (exalted Ketu on it, lord Mars); Sree(Lakṣmī) Libra H7 (on exalted Saturn 11L, lord Venus 2L); Ghati Sagittarius H9 (on Jupiter+Venus dhana yoga); Hora Gemini/H2-axis; Bhava Pisces H12; Varnada Cancer; Vighati Libra H7.
- **Nakshatra-lord (Parāśari) chain:** Mars→Rāhu→Moon→Jupiter→Ketu→Mercury→Sun→Moon (cycle); everything funnels through Jupiter↔Ketu + Mercury→Sun→Moon-AK(H11). Rāhu in **Rohiṇī** (prosperity star, exalted, H2).
- **Other (CR-38):** Saraswati structure fires; KP cash-flow chain Mars(Swati)→Rahu(H2)→Moon(H11), Mercury(U.Ashadha)→Sun(H10); D9 lagna = Cancer; Saturn D9 Aries + NBRY grounds; Venus D9 Virgo + NBRY grounds.
`

/** Pure lookup — exported for testing. Returns notes markdown for a chart, or null if none logged. */
export function readingNotesFor(chartId: string): string | null {
  return chartId === CANONICAL_CHART_ID ? READING_NOTES_482012F1 : null
}

export function registerReadingNotesTool(server: McpServer): void {
  server.tool(
    'reading_notes_get',
    'Per-chart VERIFIED reading-notes (CR-38/71/80) — the standing chart-knowledge appendix a ' +
    'reading agent should inherit before a reading (structure cues: dhana/śaśa/budha-āditya yogas, ' +
    'the H2 wealth-loss mechanism, the dasha spine, karakas, special lagnas). NOT a substitute for ' +
    'the live served signals — always confirm against the tools. Returns an honest empty note for ' +
    'any chart with no logged notes.',
    { chart_id: z.string().uuid().describe('Chart UUID') },
    async ({ chart_id }) => {
      const notes = readingNotesFor(chart_id)
      const body = notes ?? `# Reading-Notes — ${chart_id}\n\n*No verified reading-notes are logged ` +
        `for this chart. Reading-notes accrue in POST_REMEDIATION_CONSUMPTION_REGISTER as a reading ` +
        `matures; none exist yet for ${chart_id}. Do not treat this absence as a chart defect.*`
      const budgeted = budgetMcpContent(
        { chart_id, has_notes: notes != null, reading_notes_markdown: body },
        'reading_notes_get',
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgeted) }],
      }
    }
  )
}
