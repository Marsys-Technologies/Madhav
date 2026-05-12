/**
 * reasoning_vocabulary.smoke.ts — Gate III AC.III.8
 *
 * Live Gemini call verifying that reasoning narration emitted through
 * ‹reasoning› markers contains NO banned internal tokens (MSR, FORENSIC,
 * CGM, UCN, CDLM, RM, LEL, pgvector, cosine, embedding, chunk_id,
 * vector_score, cgm_graph_walk, hybrid_rank, retrieval_ranker, structured_sql).
 *
 * Also verifies ≥1 reasoning step fires on a representative Jyotish query.
 *
 * Tagged .smoke.ts — excluded from default vitest run sweep.
 *
 * Run: npx vitest run tests/smoke/reasoning_vocabulary.smoke.ts --pool=forks
 */

import { describe, it, expect } from 'vitest'
import { generateText } from 'ai'
import { google } from '@ai-sdk/google'
import { REASONING_NARRATION_GATE, OUT_OF_DOMAIN_GATE } from '@/lib/prompts/templates/shared'
import { parseMarkers } from '@/lib/consume/marker_parser'
import { containsBannedToken } from '@/lib/jyotish/domain_labels'

const TITLE_MODEL = 'gemini-2.5-flash-lite'

const systemPrompt = `You are a Jyotish synthesis engine reading the birth chart of Abhisek Mohanty, born 1984-02-05 at 10:43 IST, Bhubaneswar, Odisha, India. The Sun is in Capricorn (10th house), Moon in Scorpio (8th house), Lagna in Aries.

${REASONING_NARRATION_GATE}

${OUT_OF_DOMAIN_GATE}

Emit at least 3 ‹reasoning› markers in your response to demonstrate the narration. Keep the overall response brief (4–6 sentences) to minimize API cost.`

describe('Gate III AC.III.8 — Reasoning Vocabulary (live)', { timeout: 60_000 }, () => {
  it('emits ≥1 reasoning step with no banned tokens on a Jyotish query', async () => {
    const { text } = await generateText({
      model: google(TITLE_MODEL),
      system: systemPrompt,
      prompt:
        'Interpret my current dasha-bukhti window in light of natal chart strength.',
      maxOutputTokens: 500,
    })

    const parsed = parseMarkers(text)

    // Must emit at least 1 reasoning step
    expect(
      parsed.reasoning.length,
      `Expected ≥1 reasoning step but got 0.\nFull response:\n${text}`,
    ).toBeGreaterThanOrEqual(1)

    // No reasoning step text may contain banned tokens
    const violations: string[] = []
    for (const step of parsed.reasoning) {
      const hit = containsBannedToken(step.text)
      if (hit) {
        violations.push(`Step "${step.text.slice(0, 60)}" contains banned token "${hit}"`)
      }
    }

    expect(
      violations,
      `Banned token leakage in reasoning steps:\n${violations.join('\n')}`,
    ).toHaveLength(0)

    // Reasoning should not appear raw in visible text
    expect(
      parsed.visibleText,
      'Visible text should not contain raw ‹reasoning› markers',
    ).not.toContain('‹reasoning›')
  })

  it('all reasoning step texts are ≤30 words (sanity check on narration length)', async () => {
    const { text } = await generateText({
      model: google(TITLE_MODEL),
      system: systemPrompt,
      prompt: 'What does my Saturn-Moon configuration indicate for my emotional life?',
      maxOutputTokens: 400,
    })

    const parsed = parseMarkers(text)

    const longSteps = parsed.reasoning.filter(
      r => r.text.split(/\s+/).length > 30,
    )
    expect(
      longSteps,
      `${longSteps.length} reasoning step(s) exceeded 30 words:\n${longSteps.map(s => `  "${s.text}"`).join('\n')}`,
    ).toHaveLength(0)
  })
})
