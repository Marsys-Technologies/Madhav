/**
 * sanskrit_annotation.smoke.ts — Gate III AC.III.11
 *
 * Live Gemini call verifying the SANSKRIT_ANNOTATION_GATE in the synthesis
 * prompt causes the model to emit ‹sanskrit term=… def=… translit=…›
 * markers for Sanskrit/Jyotish technical terms.
 *
 * Tagged .smoke.ts — excluded from default vitest run sweep.
 *
 * Run: npx vitest run tests/smoke/sanskrit_annotation.smoke.ts --pool=forks
 */

import { describe, it, expect } from 'vitest'
import { generateText } from 'ai'
import { google } from '@ai-sdk/google'
import {
  SANSKRIT_ANNOTATION_GATE,
  REASONING_NARRATION_GATE,
} from '@/lib/prompts/templates/shared'
import { parseMarkers } from '@/lib/consume/marker_parser'

const TITLE_MODEL = 'gemini-2.5-flash-lite'

const systemPrompt = `You are a Jyotish synthesis engine reading the birth chart of Abhisek Mohanty, born 1984-02-05 at 10:43 IST, Bhubaneswar, Odisha, India. The native is in Mercury Mahadasha (ends 2027-08-21), with Lagna in Aries, Sun in Capricorn.

${SANSKRIT_ANNOTATION_GATE}

${REASONING_NARRATION_GATE}

Use Jyotish terminology naturally in your response — this query is designed to elicit Sanskrit terms. Keep the response to 4–6 sentences.`

const SANSKRIT_RICH_QUERIES = [
  'Explain my Vimshottari Mahadasha and what the Antardasha periods mean for me.',
  'What is my Atmakaraka and how should I read it in the context of my spiritual development?',
  'Interpret my Navamsa chart and what it says about marriage and dharmic partnerships.',
]

describe('Gate III AC.III.11 — Sanskrit Annotation (live)', { timeout: 120_000 }, () => {
  for (const query of SANSKRIT_RICH_QUERIES) {
    it(`emits ≥1 Sanskrit annotation for: "${query.slice(0, 50)}…"`, async () => {
      const { text } = await generateText({
        model: google(TITLE_MODEL),
        system: systemPrompt,
        prompt: query,
        maxOutputTokens: 400,
      })

      const parsed = parseMarkers(text)

      expect(
        parsed.sanskrit.length,
        `Expected ≥1 Sanskrit annotation but got 0.\nFull response:\n${text}`,
      ).toBeGreaterThanOrEqual(1)

      // Every annotated term must have non-empty term and definition
      for (const term of parsed.sanskrit) {
        expect(
          term.term.trim(),
          `Sanskrit entry has empty term. Entry: ${JSON.stringify(term)}`,
        ).toBeTruthy()

        expect(
          term.definition.trim(),
          `Sanskrit entry for "${term.term}" has empty definition`,
        ).toBeTruthy()
      }

      // Visible text should not contain raw ‹sanskrit marker tags
      expect(
        parsed.visibleText,
        'Visible text should not contain raw ‹sanskrit markers',
      ).not.toContain('‹sanskrit')

      // Display text (the term itself) should flow naturally in visible text
      for (const term of parsed.sanskrit) {
        expect(
          parsed.visibleText,
          `Visible text should contain the display text for term "${term.term}"`,
        ).toContain(term.term)
      }
    })
  }
})
