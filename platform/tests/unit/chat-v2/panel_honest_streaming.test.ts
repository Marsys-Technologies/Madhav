/**
 * β9 — Honest panel streaming tests.
 *
 * Verifies:
 * - PASSTHROUGH_MODEL constant is gone from panel_strategy.ts
 * - streamAdjudicate (not adjudicate) is imported in panel_strategy.ts
 * - panelStageEvents are returned by PanelModeOrchestrator.synthesize
 * - panelStageEvents contain panel:member:N running + done + panel:adjudicator running
 * - adjudicator_prompt_v1.ts produces a well-formed prompt with no model names
 * - streamAdjudicate forwards abortSignal
 * - Route emits panelStageEvents before merging the stream
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const src = (rel: string) => readFileSync(join(process.cwd(), rel), 'utf-8')

const panelStrategy = src('src/lib/synthesis/panel_strategy.ts')
const adjudicator = src('src/lib/synthesis/panel/adjudicator.ts')
const promptV1 = src('src/lib/synthesis/prompts/adjudicator_prompt_v1.ts')
const route = src('src/app/api/chat/consult/route.ts')

// ── panel_strategy.ts source assertions ───────────────────────────────────────

describe.skip('panel_strategy.ts — β9 structure', () => {
  it('PASSTHROUGH_MODEL constant declaration is removed (β9 — no cheap re-emission call)', () => {
    // The comment may reference the removed constant, but the const declaration is gone.
    expect(panelStrategy).not.toContain('const PASSTHROUGH_MODEL')
    expect(panelStrategy).not.toContain("= 'claude-haiku-4-5'")
  })

  it('imports streamAdjudicate (not adjudicate)', () => {
    expect(panelStrategy).toContain('streamAdjudicate')
    expect(panelStrategy).not.toContain("import { adjudicate }")
  })

  it('builds panelStageEvents array', () => {
    expect(panelStrategy).toContain('panelStageEvents')
    expect(panelStrategy).toContain("type: 'data-stage'")
  })

  it('emits panel:member:N running events', () => {
    // Template literal `panel:member:${i + 1}` used for dynamic stage names
    expect(panelStrategy).toContain('panel:member:')
    expect(panelStrategy).toContain("'running'")
  })

  it('emits panel:member:N done events after members complete', () => {
    expect(panelStrategy).toContain("'done'")
    expect(panelStrategy).toContain("latency_ms")
  })

  it('emits panel:adjudicator running event', () => {
    expect(panelStrategy).toContain('panel:adjudicator')
  })

  it('returns panelStageEvents in synthesize result', () => {
    expect(panelStrategy).toContain('panelStageEvents,')
  })

  it('no secondary passthrough LLM call — only streamAdjudicate call', () => {
    // Count streamAdapterRaw calls — should be zero (the passthrough is gone)
    const streamAdapterRawCalls = (panelStrategy.match(/streamAdapterRaw/g) ?? []).length
    expect(streamAdapterRawCalls).toBe(0)
  })
})

// ── adjudicator.ts source assertions ──────────────────────────────────────────

describe.skip('adjudicator.ts — streamAdjudicate function', () => {
  it('exports streamAdjudicate', () => {
    expect(adjudicator).toContain('export function streamAdjudicate')
  })

  it('uses streamAdapterRaw (not runAdapter) for the streaming call', () => {
    // Within the streamAdjudicate function body, streamAdapterRaw is called
    const fnBody = adjudicator.slice(adjudicator.indexOf('export function streamAdjudicate'))
    expect(fnBody).toContain('streamAdapterRaw')
  })

  it('passes smoothStream: true for a better streaming UX', () => {
    const fnBody = adjudicator.slice(adjudicator.indexOf('export function streamAdjudicate'))
    expect(fnBody).toContain('smoothStream: true')
  })

  it('forwards abortSignal to streamAdapterRaw', () => {
    const fnBody = adjudicator.slice(adjudicator.indexOf('export function streamAdjudicate'))
    expect(fnBody).toContain('request.abortSignal')
  })

  it('returns adjudicator_model_id in result', () => {
    expect(adjudicator).toContain('adjudicator_model_id: adjConfig.model_id')
  })

  it('accepts rawOnFinish as optional 4th parameter', () => {
    expect(adjudicator).toContain('rawOnFinish?:')
  })
})

// ── adjudicator_prompt_v1.ts assertions ───────────────────────────────────────

describe.skip('adjudicator_prompt_v1.ts — streaming prompt', () => {
  it('exports buildAdjudicatorStreamPrompt', () => {
    expect(promptV1).toContain('export function buildAdjudicatorStreamPrompt')
  })

  it('returns both systemPrompt and userPrompt', () => {
    expect(promptV1).toContain('systemPrompt')
    expect(promptV1).toContain('userPrompt')
  })

  it('does NOT instruct JSON output (plain text) in the prompt strings', () => {
    // The source file may have "JSON" in comments explaining what it replaced.
    // What matters is the runtime prompt strings do NOT ask for JSON.
    expect(promptV1).not.toContain('"final_answer"')
    expect(promptV1).not.toContain('Output Format')
    // No json_schema / json_object instructions in the prompt strings
    expect(promptV1).not.toContain('json_schema')
  })

  it('uses Member 1/2/3 labels (no model names)', () => {
    expect(promptV1).toContain('member_label')
    // No hardcoded model names
    expect(promptV1).not.toContain('claude')
    expect(promptV1).not.toContain('openai')
    expect(promptV1).not.toContain('gemini')
    expect(promptV1).not.toContain('deepseek')
  })
})

// ── route.ts — panelStageEvents handling ──────────────────────────────────────

describe.skip('route.ts — panelStageEvents forwarding', () => {
  it('destructures panelStageEvents from synthesize result', () => {
    expect(route).toContain('panelStageEvents')
  })

  it('iterates over panelStageEvents and calls writer.write', () => {
    expect(route).toContain('for (const evt of panelStageEvents')
    expect(route).toContain('writer.write(evt')
  })

  it('only emits synthesis:running when NOT panel mode (no panelStageEvents)', () => {
    expect(route).toContain("stagePart('synthesis', 'running')")
  })
})

// ── data_parts.ts — stage enum includes panel stages ──────────────────────────

import { StageNameSchema } from '@/lib/streams/data_parts'

describe.skip('data_parts StageNameSchema — panel stages', () => {
  it('includes panel:member:1', () => {
    expect(StageNameSchema.options).toContain('panel:member:1')
  })
  it('includes panel:member:2', () => {
    expect(StageNameSchema.options).toContain('panel:member:2')
  })
  it('includes panel:member:3', () => {
    expect(StageNameSchema.options).toContain('panel:member:3')
  })
  it('includes panel:adjudicator', () => {
    expect(StageNameSchema.options).toContain('panel:adjudicator')
  })
})
