/**
 * DD-20 end-to-end proof: calls the REAL shipped generateInterpretationSets()
 * (default caller, real runAdapter, real gemini-2.5-flash) with a realistic
 * judgment, to prove the fix works through the actual code path — not a
 * standalone reimplementation.
 */
import { generateInterpretationSets } from '../../src/lib/pariprashna/interpretation/worker'
import type { SignificantJudgment } from '../../src/lib/pariprashna/interpretation/detect'

const REAL_PROSE_EXCERPT =
  'Based on the synthesis of your astrological chart, the current Vimshottari dasha period is ' +
  'Mercury Mahadasha and Saturn Antardasha. This sub-period began on December 12, 2024, and will ' +
  'end on August 21, 2027. This timing is exceptionally significant for career and authority, ' +
  'representing a peak window for consolidating the intellectual work of the entire 17-year ' +
  'Mercury Mahadasha into tangible, lasting, and public forms of authority. The convergence of ' +
  'these two planetary energies creates a powerful synergy for professional achievement.'

const judgments: SignificantJudgment[] = [
  {
    judgment_id: 'sig-domain_verdict-1',
    category: 'domain_verdict',
    block_id: 'blk-1-1',
    claim_text: REAL_PROSE_EXCERPT,
    detection_basis: "G2-A block role='verdict' (first prose block of its pass)",
  },
]

async function main() {
  console.log('[dd20-e2e] calling the REAL generateInterpretationSets() — default caller, real model...')
  const entries = await generateInterpretationSets(judgments)
  for (const e of entries) {
    console.log('[dd20-e2e] entry:', JSON.stringify({
      judgment_id: e.judgment_id,
      status: e.status,
      candidates_count: e.candidates?.length ?? 0,
      waiver_reason: e.waiver_reason,
    }, null, 2))
  }
  const genuinelyGenerated = entries.filter((e) => e.status === 'generated')
  console.log(`[dd20-e2e] ${genuinelyGenerated.length}/${entries.length} entries genuinely generated (not waived)`)
  if (genuinelyGenerated.length === 0) {
    console.log('[dd20-e2e] FAIL: still 100% waived through the real shipped code path.')
    process.exitCode = 1
  } else {
    console.log('[dd20-e2e] PASS: the fix works through the real shipped code path.')
  }
}

main().catch((err) => {
  console.error('[dd20-e2e] FAIL:', err)
  process.exitCode = 1
})
