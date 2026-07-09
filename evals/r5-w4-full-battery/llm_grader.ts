/**
 * llm_grader.ts — real product-policy LLM rubric grading for the R5.1 C4 acceptance battery.
 *
 * Implements the brief's C4 requirement: "rubric grading via the product-policy LLM path
 * (Gemini primary / DeepSeek fallback)". Prior to this file, battery_runner.ts only had a
 * STRUCTURAL PROXY (regex keyword-presence scaled onto /15) explicitly labeled NOT_LLM_GRADED —
 * see the harness's original header comment. This module replaces that proxy with a genuine
 * LLM-as-judge call per rubric-bearing item, grading the raw MCP tool-response text against the
 * item's stated "must contain" properties (the same `checks` the harness already derives from
 * R5_ANSWER_BATTERY_v1_0.md's per-item deterministic-assertion/rubric prose), using Gemini
 * 2.5-flash as primary grader and DeepSeek (deepseek-chat) as fallback if Gemini errors or
 * rate-limits on a given item.
 *
 * Per the governing brief: "Claude/Anthropic models are BANNED from grading/scoring rubric items
 * themselves" — this file NEVER computes a score itself; it only orchestrates calls to Gemini/
 * DeepSeek and parses their returned score. If both providers fail for an item, the result is
 * honestly NOT_LLM_GRADED — never a fabricated pass.
 *
 * Keys are read from process.env only (GOOGLE_GENERATIVE_AI_API_KEY, DEEPSEEK_API_KEY) — never
 * hardcoded, never logged.
 */

export interface LLMCheck {
  label: string
  met: boolean // the harness's own regex-based structural hint — advisory only, the grader must independently judge from the raw text
}

export interface RubricResult {
  applicable: boolean
  floor: number | null
  structuralProxyScore: number | null // retained field name for JSON-shape compatibility with prior runs; now holds the REAL LLM score when graded
  status:
    | 'NOT_APPLICABLE'
    | 'NOT_LLM_GRADED'
    | 'STRUCTURAL_PROXY_MET' // legacy value, unused by this module but kept in the type union for shape compatibility
    | 'STRUCTURAL_PROXY_BELOW_FLOOR'
    | 'LLM_GRADED_MET'
    | 'LLM_GRADED_BELOW_FLOOR'
  note: string
  grader?: 'gemini' | 'deepseek' | 'none'
  grader_model?: string
  tokens_in?: number
  tokens_out?: number
  grading_latency_ms?: number
}

const GEMINI_KEY = process.env['GOOGLE_GENERATIVE_AI_API_KEY'] ?? ''
const DEEPSEEK_KEY = process.env['DEEPSEEK_API_KEY'] ?? ''
const GEMINI_MODEL = 'gemini-2.5-flash'
const DEEPSEEK_MODEL = 'deepseek-chat'

interface GraderCallResult {
  ok: boolean
  text: string | null
  tokensIn?: number
  tokensOut?: number
  error?: string
}

async function callGemini(prompt: string): Promise<GraderCallResult> {
  if (!GEMINI_KEY) return { ok: false, text: null, error: 'GOOGLE_GENERATIVE_AI_API_KEY not set' }
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_KEY}`
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0, responseMimeType: 'application/json', maxOutputTokens: 1024 },
      }),
      signal: AbortSignal.timeout(45_000),
    })
    if (!res.ok) {
      const errText = await res.text().catch(() => '')
      return { ok: false, text: null, error: `gemini HTTP ${res.status}: ${errText.slice(0, 300)}` }
    }
    const j = (await res.json()) as any
    const text = j?.candidates?.[0]?.content?.parts?.[0]?.text ?? null
    const tokensIn = j?.usageMetadata?.promptTokenCount
    const tokensOut = j?.usageMetadata?.candidatesTokenCount
    if (!text) return { ok: false, text: null, error: `gemini: no text in response (finishReason=${j?.candidates?.[0]?.finishReason ?? 'unknown'})` }
    return { ok: true, text, tokensIn, tokensOut }
  } catch (e) {
    return { ok: false, text: null, error: e instanceof Error ? e.message : String(e) }
  }
}

async function callDeepSeek(prompt: string): Promise<GraderCallResult> {
  if (!DEEPSEEK_KEY) return { ok: false, text: null, error: 'DEEPSEEK_API_KEY not set' }
  try {
    const res = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${DEEPSEEK_KEY}` },
      body: JSON.stringify({
        model: DEEPSEEK_MODEL,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0,
        max_tokens: 1024,
        response_format: { type: 'json_object' },
      }),
      signal: AbortSignal.timeout(45_000),
    })
    if (!res.ok) {
      const errText = await res.text().catch(() => '')
      return { ok: false, text: null, error: `deepseek HTTP ${res.status}: ${errText.slice(0, 300)}` }
    }
    const j = (await res.json()) as any
    const text = j?.choices?.[0]?.message?.content ?? null
    const tokensIn = j?.usage?.prompt_tokens
    const tokensOut = j?.usage?.completion_tokens
    if (!text) return { ok: false, text: null, error: 'deepseek: no content in response' }
    return { ok: true, text, tokensIn, tokensOut }
  } catch (e) {
    return { ok: false, text: null, error: e instanceof Error ? e.message : String(e) }
  }
}

function buildPrompt(floor: number, checks: LLMCheck[], rawText: string, capNote: string): string {
  const checklist = checks.map((c) => `- ${c.label} (harness's own regex keyword-presence hint: ${c.met ? 'present' : 'absent'} — verify independently from the actual text, do not trust this hint blindly)`).join('\n')
  const truncated = rawText.length > 8000 ? rawText.slice(0, 8000) + '\n...[truncated for grading — response continues]' : rawText
  return `You are the product-policy rubric grader for the MARSYS-JIS Jyotish instrument's R5 Answer Battery (canonical_id R5_ANSWER_BATTERY, FROZEN law). You are grading ONE item's raw MCP tool-response JSON/text against a synthesis-quality rubric out of 15 points (the "G10-QT"-style rubric convention used throughout this program). This is NOT a chart-astrology judgment call — you are judging whether the RESPONSE, as a piece of communication, demonstrates the specific named properties below with genuine substance (not just keyword presence).

RUBRIC FLOOR for this item: ${floor}/15 (item PASSES the rubric only if your score >= floor).

NAMED PROPERTIES THIS ITEM MUST DEMONSTRATE (score holistically across these; do not just count keyword hits — judge whether each property is substantively satisfied):
${checklist}

ADDITIONAL GRADING CONTEXT / KNOWN LIMITATIONS OF THIS PROXY CHECK (read carefully — factor into your score honestly, do not ignore):
${capNote}

RAW MCP TOOL RESPONSE BEING GRADED (this is what an MCP client actually received — grade THIS, not what you imagine a hypothetical better answer would say):
"""
${truncated}
"""

Score 0-15. Deduct points for: missing named properties, superficial/keyword-only treatment without real reasoning, generic astrology boilerplate, fabricated-sounding claims without grounding, alarmist or overconfident language on sensitive topics, and any internal contradiction. Award full marks only for genuine acharya-grade synthesis quality across ALL named properties.

Respond with ONLY a JSON object, no markdown fences, no other text:
{"score": <integer 0-15>, "rationale": "<2-4 sentences citing SPECIFIC evidence from the response text for your score>"}`
}

function parseGraderJson(text: string): { score: number; rationale: string } | null {
  // strip markdown fences if the model added them despite instructions
  const cleaned = text.replace(/^```(json)?\s*/i, '').replace(/```\s*$/, '').trim()
  try {
    const j = JSON.parse(cleaned)
    const score = Number(j.score)
    if (!Number.isFinite(score) || score < 0 || score > 15) return null
    return { score, rationale: String(j.rationale ?? '') }
  } catch {
    // last-resort: pull a bare integer out of the text
    const m = cleaned.match(/"score"\s*:\s*(\d+(\.\d+)?)/)
    if (m) return { score: Number(m[1]), rationale: cleaned.slice(0, 400) }
    return null
  }
}

/**
 * Real LLM rubric grade. Gemini primary, DeepSeek fallback on any Gemini failure
 * (network error, non-200, empty/unparseable response). If both fail, returns
 * NOT_LLM_GRADED honestly — never a fabricated score.
 */
export async function llmRubric(floor: number, checks: LLMCheck[], rawText: string, capNote: string): Promise<RubricResult> {
  const prompt = buildPrompt(floor, checks, rawText, capNote)
  const t0 = performance.now()

  let call = await callGemini(prompt)
  let grader: 'gemini' | 'deepseek' | 'none' = 'gemini'
  let model = GEMINI_MODEL
  if (!call.ok) {
    const geminiError = call.error
    call = await callDeepSeek(prompt)
    grader = 'deepseek'
    model = DEEPSEEK_MODEL
    if (!call.ok) {
      return {
        applicable: true,
        floor,
        structuralProxyScore: null,
        status: 'NOT_LLM_GRADED',
        note: `Both graders failed for this item. Gemini: ${geminiError}. DeepSeek: ${call.error}.`,
        grader: 'none',
        grading_latency_ms: Math.round(performance.now() - t0),
      }
    }
  }

  const parsed = call.text ? parseGraderJson(call.text) : null
  if (!parsed) {
    return {
      applicable: true,
      floor,
      structuralProxyScore: null,
      status: 'NOT_LLM_GRADED',
      note: `${grader} responded but output was unparseable as the required JSON shape: ${(call.text ?? '').slice(0, 300)}`,
      grader,
      grader_model: model,
      grading_latency_ms: Math.round(performance.now() - t0),
    }
  }

  const status: RubricResult['status'] = parsed.score >= floor ? 'LLM_GRADED_MET' : 'LLM_GRADED_BELOW_FLOOR'
  return {
    applicable: true,
    floor,
    structuralProxyScore: parsed.score,
    status,
    note: `[${grader}/${model}] ${parsed.rationale}`,
    grader,
    grader_model: model,
    tokens_in: call.tokensIn,
    tokens_out: call.tokensOut,
    grading_latency_ms: Math.round(performance.now() - t0),
  }
}
