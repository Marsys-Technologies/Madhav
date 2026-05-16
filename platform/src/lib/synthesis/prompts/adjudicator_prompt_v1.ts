/**
 * β9 — Streaming adjudicator prompt builder.
 *
 * Unlike the JSON-outputting adjudicator_v1.md template used by the
 * non-streaming adjudicate() path, this prompt instructs the model to
 * produce plain markdown prose. The output streams directly to the user.
 *
 * Anonymization contract: member labels are "Member 1/2/3" — no model or
 * provider names are injected. This mirrors the existing adjudicator_v1.md
 * anonymization discipline.
 */

import type { AnonymizedMemberOutput } from '../panel/types'
import type { SynthesisRequest } from '../types'

export interface AdjudicatorStreamPrompt {
  systemPrompt: string
  userPrompt: string
}

export function buildAdjudicatorStreamPrompt(
  anonymized: AnonymizedMemberOutput[],
  request: SynthesisRequest,
): AdjudicatorStreamPrompt {
  const membersBlock = anonymized
    .map(m => `## ${m.member_label}\n\n${m.answer}`)
    .join('\n\n---\n\n')

  const systemPrompt = [
    'You are an independent panel adjudicator for a Jyotish astrological instrument.',
    'Three analysts have each independently answered the same question about a birth chart.',
    'Your role is to synthesize their answers — not to pick a winner.',
    '',
    'Guidelines:',
    '- Write a unified final answer in markdown prose.',
    '- Incorporate all material the members agree on.',
    '- Explicitly acknowledge points where they differed; treat divergence as a first-class output.',
    '- Do NOT say "Member 2 was correct" or pick one member\'s answer over another.',
    '- Where members disagree, present the competing views with appropriate epistemic weight.',
    `- Style: ${request.style} | Audience tier: ${request.audience_tier}`,
  ].join('\n')

  const userPrompt = [
    `**Query class:** ${request.query_plan.query_class}`,
    '',
    '## Original Question',
    '',
    request.query,
    '',
    '---',
    '',
    '## Panel Answers',
    '',
    membersBlock,
    '',
    '---',
    '',
    'Synthesize a final answer in markdown. Begin directly with the answer — no preamble.',
  ].join('\n')

  return { systemPrompt, userPrompt }
}
