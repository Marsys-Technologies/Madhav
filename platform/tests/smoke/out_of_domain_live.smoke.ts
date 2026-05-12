/**
 * out_of_domain_live.smoke.ts — Gate III AC.III.10
 *
 * Live Gemini call to verify the OUT_OF_DOMAIN_GATE in the synthesis prompt
 * causes the model to emit ‹out_of_domain› markers for non-Jyotish queries
 * and NOT for Jyotish queries.
 *
 * Tagged .smoke.ts — excluded from default vitest run sweep.
 *
 * Run: npx vitest run tests/smoke/out_of_domain_live.smoke.ts --pool=forks
 */

import { describe, it, expect } from 'vitest'
import { generateText } from 'ai'
import { google } from '@ai-sdk/google'
import {
  OUT_OF_DOMAIN_GATE,
  REASONING_NARRATION_GATE,
  FACTUAL_CORRECTION_GATE,
} from '@/lib/prompts/templates/shared'
import { parseMarkers } from '@/lib/consume/marker_parser'

const TITLE_MODEL = 'gemini-2.5-flash-lite'

const systemPrompt = `You are a Jyotish synthesis engine reading the birth chart of Abhisek Mohanty, born 1984-02-05 at 10:43 IST, Bhubaneswar, Odisha, India.

${OUT_OF_DOMAIN_GATE}

${FACTUAL_CORRECTION_GATE}

${REASONING_NARRATION_GATE}

Keep your response brief (2–4 sentences) to minimize API cost during smoke testing.`

const NON_JYOTISH_QUERIES = [
  "What's the weather in Bangalore tomorrow?",
  'Summarize this PDF for me.',
  'Write me a Python script to sort a list.',
  "What's the best restaurant near MG Road?",
]

const JYOTISH_QUERIES = [
  'What does my current Mahadasha indicate for my life right now?',
  'Explain my Atmakaraka and what it means for my spiritual path.',
  'How do I interpret Saturn and Moon in my natal chart?',
  'Predict the key themes for the next 6 months based on my chart.',
]

describe('Gate III AC.III.10 — Out-of-Domain (live)', { timeout: 120_000 }, () => {
  it('emits ‹out_of_domain› for 4/4 non-Jyotish queries', async () => {
    const results: Array<{ query: string; fired: boolean; response: string }> = []

    for (const query of NON_JYOTISH_QUERIES) {
      const { text } = await generateText({
        model: google(TITLE_MODEL),
        system: systemPrompt,
        prompt: query,
        maxOutputTokens: 200,
      })
      const parsed = parseMarkers(text)
      results.push({ query, fired: parsed.outOfDomain !== null, response: text })
    }

    const failures = results.filter(r => !r.fired)
    expect(
      failures.length,
      `Expected 0 failures but got ${failures.length}:\n${failures.map(f => `  "${f.query}"\n  Response: ${f.response.slice(0, 120)}`).join('\n')}`,
    ).toBe(0)
  })

  it('does NOT emit ‹out_of_domain› for 4/4 Jyotish queries', async () => {
    const results: Array<{ query: string; fired: boolean; response: string }> = []

    for (const query of JYOTISH_QUERIES) {
      const { text } = await generateText({
        model: google(TITLE_MODEL),
        system: systemPrompt,
        prompt: query,
        maxOutputTokens: 250,
      })
      const parsed = parseMarkers(text)
      results.push({ query, fired: parsed.outOfDomain !== null, response: text })
    }

    const falsePositives = results.filter(r => r.fired)
    expect(
      falsePositives.length,
      `Got unexpected out_of_domain for ${falsePositives.length} Jyotish queries:\n${falsePositives.map(f => `  "${f.query}"\n  Response: ${f.response.slice(0, 120)}`).join('\n')}`,
    ).toBe(0)
  })
})
