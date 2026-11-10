/**
 * nim_synthesis_candidates.mjs
 *
 * Tests every NIM catalog model that could serve as a 1M-context synthesis
 * model. 30s timeout per model (V4 Flash took 13.6s cold-start).
 *
 * Candidates from the Phase 1 catalog scan:
 *   deepseek-ai/deepseek-v4-flash          ✅ Phase 2 confirmed, 13.6s cold-start
 *   deepseek-ai/deepseek-v3.1-terminus     in catalog, untested
 *   deepseek-ai/deepseek-v3.2             in catalog, untested
 *   nvidia/llama-3.1-nemotron-ultra-253b-v1 back in catalog! (was 404 before)
 *   openai/gpt-oss-120b                    mysterious — in catalog, twice
 *   openai/gpt-oss-20b                     smaller variant
 *   moonshotai/kimi-k2.6                   updated Kimi K2 (newer than k2-instruct)
 *   moonshotai/kimi-k2-thinking            thinking mode variant
 *   mistralai/mistral-large-3-675b-instruct-2512  largest Mistral on NIM
 *   qwen/qwen3.5-397b-a17b                 massive Qwen (397B)
 *
 * Usage:  node scripts/nim_synthesis_candidates.mjs
 */

import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const envPath   = resolve(__dirname, '../.env.local')
let apiKey = ''
try {
  for (const line of readFileSync(envPath, 'utf8').split('\n')) {
    const m = line.match(/^NVIDIA_NIM_API_KEY\s*=\s*(.+)$/)
    if (m) { apiKey = m[1].trim(); break }
  }
} catch {}
if (!apiKey) { console.error('NVIDIA_NIM_API_KEY not found'); process.exit(1) }

const BASE = 'https://integrate.api.nvidia.com/v1'
console.log(`Key: ${apiKey.slice(0, 12)}…`)
console.log(`Time: ${new Date().toISOString()}`)
console.log('Timeout: 30s per model\n')

async function test(modelId) {
  const ac = new AbortController()
  const timer = setTimeout(() => ac.abort(), 30_000)
  const start = Date.now()
  try {
    const res = await fetch(`${BASE}/chat/completions`, {
      method: 'POST',
      signal: ac.signal,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: modelId,
        messages: [{ role: 'user', content: 'Reply with only the number: 1+1=' }],
        max_tokens: 10,
        stream: false,
      }),
    })
    clearTimeout(timer)
    const ms = Date.now() - start
    if (res.ok) {
      const data = await res.json().catch(() => ({}))
      const content = data?.choices?.[0]?.message?.content?.trim().slice(0, 50) ?? '?'
      // Try to get context window from response headers or model info
      return { ok: true, ms, result: `✅  ${ms}ms  "${content}"` }
    }
    const body = await res.text().catch(() => '').then(t => t.slice(0, 100).replace(/\n/g, ' '))
    const sym = res.status === 404 ? '❌' : res.status === 410 ? '☠️' : res.status === 429 ? '🔁' : '⚠️'
    return { ok: false, ms, result: `${sym}  HTTP ${res.status} in ${ms}ms  ${body}` }
  } catch {
    clearTimeout(timer)
    const ms = Date.now() - start
    return { ok: false, ms, result: `⏱   Timeout after ${ms}ms` }
  }
}

const CANDIDATES = [
  // ── DeepSeek ─────────────────────────────────────────────────────────────
  { id: 'deepseek-ai/deepseek-v4-flash',           note: 'V4 Flash — 1M ctx, confirmed 13.6s cold-start' },
  { id: 'deepseek-ai/deepseek-v4-pro',             note: 'V4 Pro  — in catalog, was 60s timeout' },
  { id: 'deepseek-ai/deepseek-v3.2',               note: 'V3.2    — new in catalog, context unknown' },
  { id: 'deepseek-ai/deepseek-v3.1-terminus',      note: 'V3.1-T  — in catalog, context unknown' },
  // ── NVIDIA Nemotron ───────────────────────────────────────────────────────
  { id: 'nvidia/llama-3.1-nemotron-ultra-253b-v1', note: 'Nemotron Ultra 253B — back in catalog!' },
  { id: 'nvidia/llama-3.3-nemotron-super-49b-v1',  note: 'Nemotron Super 49B — confirmed 714ms' },
  { id: 'nvidia/nemotron-3-super-120b-a12b',       note: 'Nemotron 3 120B — confirmed 356ms, 1M ctx' },
  // ── OpenAI OSS (mysterious) ───────────────────────────────────────────────
  { id: 'openai/gpt-oss-120b',                     note: 'GPT OSS 120B — in catalog twice' },
  { id: 'openai/gpt-oss-20b',                      note: 'GPT OSS 20B  — in catalog twice' },
  // ── Kimi K2 variants ─────────────────────────────────────────────────────
  { id: 'moonshotai/kimi-k2.6',                    note: 'Kimi K2.6 — newer than k2-instruct' },
  { id: 'moonshotai/kimi-k2-thinking',             note: 'Kimi K2 Thinking — CoT mode' },
  // ── Large open-weight models ──────────────────────────────────────────────
  { id: 'mistralai/mistral-large-3-675b-instruct-2512', note: 'Mistral Large 3 675B — largest Mistral' },
  { id: 'qwen/qwen3.5-397b-a17b',                  note: 'Qwen3.5 397B — massive MoE' },
  { id: 'meta/llama-3.1-405b-instruct',            note: 'Llama 3.1 405B — large Llama' },
]

const PAD_ID   = Math.max(...CANDIDATES.map(c => c.id.length)) + 2
const PAD_NOTE = 46

console.log(`${'MODEL ID'.padEnd(PAD_ID)} ${'NOTE'.padEnd(PAD_NOTE)} RESULT`)
console.log('─'.repeat(PAD_ID + PAD_NOTE + 50))

for (const c of CANDIDATES) {
  process.stdout.write(`${c.id.padEnd(PAD_ID)} ${c.note.padEnd(PAD_NOTE)} `)
  const r = await test(c.id, c.note)
  console.log(r.result)
}

console.log('\nDone.')
console.log('\nNote: ✅ models with long latency (>5s) are cold-starting — subsequent calls will be faster.')
console.log('For synthesis routing, any ✅ model with 1M context window qualifies.')
