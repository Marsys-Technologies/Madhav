/**
 * correction_live.smoke.ts — Gate III AC.III.9
 *
 * Live Gemini call to verify the FACTUAL_CORRECTION_GATE in the synthesis
 * prompt actually causes the model to emit ‹correction›...‹/correction›
 * markers when the user's query contains a factually-wrong chart claim.
 *
 * Abhisek's Sun is in Capricorn (10th house), per FORENSIC data.
 * The test query falsely asserts "Sun is in Aries" — a clear chart error.
 *
 * Tagged .smoke.ts — excluded from default vitest run sweep.
 *
 * Run: npx vitest run tests/smoke/correction_live.smoke.ts --pool=forks
 */

import { describe, it, expect } from 'vitest'
import { generateText } from 'ai'
import { google } from '@ai-sdk/google'
import { FACTUAL_CORRECTION_GATE, REASONING_NARRATION_GATE, OUT_OF_DOMAIN_GATE } from '@/lib/prompts/templates/shared'
import { parseMarkers } from '@/lib/consume/marker_parser'

const TITLE_MODEL = 'gemini-2.5-flash-lite'

const systemPrompt = `You are a Jyotish synthesis engine reading the birth chart of Abhisek Mohanty, born 1984-02-05 at 10:43 IST, Bhubaneswar, Odisha, India. The Sun is in Capricorn, in the 10th house (Shravana nakshatra, pada 4). The Lagna (Ascendant) is Aries.

${FACTUAL_CORRECTION_GATE}

${REASONING_NARRATION_GATE}

${OUT_OF_DOMAIN_GATE}

Keep your response brief (3–5 sentences) to minimize API cost during smoke testing.`

describe('Gate III AC.III.9 — Correction Doctrine (live)', { timeout: 60_000 }, () => {
  it('emits ‹correction› marker when user asserts Sun is in Aries (actual: Capricorn)', async () => {
    const { text } = await generateText({
      model: google(TITLE_MODEL),
      system: systemPrompt,
      prompt: 'Since my Sun is in Aries, what does that mean for my career?',
      maxOutputTokens: 400,
    })

    const parsed = parseMarkers(text)

    expect(
      parsed.correction,
      `Expected a correction event but got null.\nFull model response:\n${text}`,
    ).not.toBeNull()

    if (parsed.correction) {
      expect(
        parsed.correction.corrected_claim.toLowerCase(),
        `Corrected claim should mention Capricorn. Got: "${parsed.correction.corrected_claim}"`,
      ).toContain('capricorn')

      expect(
        parsed.correction.original_claim.trim(),
        'original_claim should be non-empty',
      ).toBeTruthy()
    }

    // Marker should be stripped from visible text
    expect(
      parsed.visibleText,
      'Visible text should not contain raw ‹correction› markers',
    ).not.toContain('‹correction›')
  })

  it('does NOT emit ‹correction› marker when query is factually correct', async () => {
    const { text } = await generateText({
      model: google(TITLE_MODEL),
      system: systemPrompt,
      prompt: 'My Sun is in Capricorn in the 10th house — what does that indicate for my career and public standing?',
      maxOutputTokens: 300,
    })

    const parsed = parseMarkers(text)

    expect(
      parsed.correction,
      `Got unexpected correction on a correct query.\nFull model response:\n${text}`,
    ).toBeNull()
  })
})
