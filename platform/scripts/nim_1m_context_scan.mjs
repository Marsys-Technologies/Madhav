/**
 * nim_1m_context_scan.mjs
 *
 * Finds every NIM free-tier model with ≥1M context window, confirms it is
 * actively responding, and ranks by parameter size (descending).
 *
 * Phase 1 — Fetch full catalog (141 models), pull per-model metadata to get
 *            context_length. Filter: context_length >= 1_000_000.
 * Phase 2 — Live-test every qualifying model (30s timeout).
 * Phase 3 — Print ranked table sorted by param count (descending), active only.
 *
 * Usage:  node scripts/nim_1m_context_scan.mjs
 */

import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
let apiKey = ''
try {
  for (const line of readFileSync(resolve(__dirname, '../.env.local'), 'utf8').split('\n')) {
    const m = line.match(/^NVIDIA_NIM_API_KEY\s*=\s*(.+)$/)
    if (m) { apiKey = m[1].trim(); break }
  }
} catch {}
if (!apiKey) { console.error('NVIDIA_NIM_API_KEY not found'); process.exit(1) }

const BASE    = 'https://integrate.api.nvidia.com/v1'
const HDR     = { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` }
const TIMEOUT = 30_000

console.log(`Key: ${apiKey.slice(0, 12)}…  |  Time: ${new Date().toISOString()}\n`)

// ── helpers ──────────────────────────────────────────────────────────────────
async function getJSON(url, timeoutMs = 10_000) {
  const ac = new AbortController()
  const t  = setTimeout(() => ac.abort(), timeoutMs)
  try {
    const r = await fetch(url, { headers: HDR, signal: ac.signal })
    clearTimeout(t)
    if (!r.ok) return null
    return r.json()
  } catch { clearTimeout(t); return null }
}

async function testModel(id) {
  const ac = new AbortController()
  const t  = setTimeout(() => ac.abort(), TIMEOUT)
  const t0 = Date.now()
  try {
    const r = await fetch(`${BASE}/chat/completions`, {
      method: 'POST', signal: ac.signal, headers: HDR,
      body: JSON.stringify({
        model: id,
        messages: [{ role: 'user', content: 'Reply with only the number 2.' }],
        max_tokens: 8,
        stream: false,
      }),
    })
    clearTimeout(t)
    const ms = Date.now() - t0
    if (r.ok) {
      const d = await r.json().catch(() => ({}))
      const c = d?.choices?.[0]?.message?.content?.trim().slice(0, 40) ?? '?'
      return { live: true, ms, reply: c }
    }
    return { live: false, ms, reply: `HTTP ${r.status}` }
  } catch {
    clearTimeout(t)
    return { live: false, ms: Date.now() - t0, reply: `Timeout/Error` }
  }
}

// ── extract parameter count from model ID string ──────────────────────────────
// Parses things like "70b", "253b", "405b", "120b-a12b" (active params), "397b-a17b"
function parseParams(id) {
  // For MoE: prefer total params over active-param suffix
  const totalMatch = id.match(/[_\-\/](\d+(?:\.\d+)?)b(?:[_\-]a\d)/i)
  if (totalMatch) return parseFloat(totalMatch[1])
  const simpleMatch = id.match(/[_\-\/](\d+(?:\.\d+)?)b/i)
  if (simpleMatch) return parseFloat(simpleMatch[1])
  return 0
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 1 — Catalog + context window metadata
// ═══════════════════════════════════════════════════════════════════════════
console.log('═══ Phase 1: Fetching catalog + context windows ═══\n')

const catalogData = await getJSON(`${BASE}/models`, 15_000)
if (!catalogData) { console.error('Failed to fetch catalog'); process.exit(1) }

const allModels = catalogData.data ?? []
console.log(`Catalog size: ${allModels.length} models`)

// For each model, context_window may be in the top-level catalog entry or need
// a per-model /v1/models/{id} call. Try the catalog entry first.
const candidates = []

for (const m of allModels) {
  // Skip embedding / image / safety / retrieval models
  const skip = ['embed', 'safety', 'guard', 'retriev', 'reward', 'video', 'vision',
                'vl-', 'vlm', 'coder', '-parse', 'translate', 'image', 'clip', 'pii',
                'ising', 'deplot', 'kosmos', 'recurrent', 'codellama', 'starcoder',
                'codestral', 'devstral', 'neva', 'vila']
  if (skip.some(s => m.id.toLowerCase().includes(s))) continue

  // context_window may be stored as context_window, max_context, context_length, or n_ctx
  let ctx = m.context_window ?? m.max_context ?? m.context_length ?? m.n_ctx

  if (!ctx || ctx < 1_000_000) {
    // Try fetching per-model metadata
    const safe = encodeURIComponent(m.id)
    const meta  = await getJSON(`${BASE}/models/${safe}`, 6_000)
    ctx = meta?.context_window ?? meta?.max_context ?? meta?.context_length ?? meta?.n_ctx
  }

  if (ctx && ctx >= 1_000_000) {
    candidates.push({ id: m.id, context: ctx, params: parseParams(m.id) })
    console.log(`  ✓ ${m.id.padEnd(55)} ctx=${(ctx/1_000_000).toFixed(1)}M  params≈${parseParams(m.id)||'?'}B`)
  }
}

// If context metadata is sparse (NIM often omits it), fall back to known-1M list
// built from official model cards + DeepSeek/NVIDIA documentation.
const KNOWN_1M = [
  // DeepSeek V4 confirmed 1M context
  { id: 'deepseek-ai/deepseek-v4-pro',           context: 1_000_000, params: 671  },
  { id: 'deepseek-ai/deepseek-v4-flash',         context: 1_000_000, params: 671  },
  // DeepSeek V3.x confirmed 1M context (V3 extended in late 2025)
  { id: 'deepseek-ai/deepseek-v3.2',             context: 1_000_000, params: 685  },
  { id: 'deepseek-ai/deepseek-v3.1-terminus',    context: 1_000_000, params: 685  },
  // Nemotron 3 Super — Mamba hybrid, 1M practical (confirmed in our registry)
  { id: 'nvidia/nemotron-3-super-120b-a12b',     context: 1_000_000, params: 120  },
  // Nemotron nano — NVIDIA advertises 1M for the nano-omni variants
  { id: 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning', context: 1_000_000, params: 30 },
]

// Merge: add KNOWN_1M entries that are in the catalog and not already found
const catalogIds = new Set(allModels.map(m => m.id))
const alreadyFound = new Set(candidates.map(c => c.id))

for (const k of KNOWN_1M) {
  if (catalogIds.has(k.id) && !alreadyFound.has(k.id)) {
    console.log(`  + ${k.id.padEnd(55)} ctx=${(k.context/1_000_000).toFixed(1)}M  params≈${k.params}B  (from model card)`)
    candidates.push(k)
  }
}

// Dedup (same model can appear twice in catalog)
const seen = new Set()
const uniqueCandidates = candidates.filter(c => {
  if (seen.has(c.id)) return false
  seen.add(c.id); return true
})

console.log(`\nTotal ≥1M-context candidates: ${uniqueCandidates.length}\n`)

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 2 — Live test every candidate (30s timeout)
// ═══════════════════════════════════════════════════════════════════════════
console.log('═══ Phase 2: Live testing all candidates (30s timeout each) ═══\n')

const results = []
for (const c of uniqueCandidates) {
  process.stdout.write(`  Testing ${c.id.padEnd(55)} ... `)
  const r = await testModel(c.id)
  const status = r.live ? `✅  ${r.ms}ms  "${r.reply}"` : `❌  ${r.reply}`
  console.log(status)
  if (r.live) results.push({ ...c, ms: r.ms, reply: r.reply })
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 3 — Ranked output (parameter size descending, active only)
// ═══════════════════════════════════════════════════════════════════════════
console.log('\n═══ Phase 3: Active 1M-context NIM models — ranked by parameter size ═══\n')

results.sort((a, b) => (b.params || 0) - (a.params || 0))

if (results.length === 0) {
  console.log('No active 1M-context models found on this run.')
} else {
  console.log(`${'RANK'} ${'MODEL ID'.padEnd(55)} ${'CTX'.padEnd(6)} ${'PARAMS'.padEnd(10)} ${'LATENCY'.padEnd(10)} REPLY`)
  console.log('─'.repeat(110))
  results.slice(0, 10).forEach((m, i) => {
    const ctx    = m.context >= 2_000_000 ? '2M' : '1M'
    const params = m.params ? `${m.params}B` : '?'
    console.log(`  #${i+1}  ${m.id.padEnd(55)} ${ctx.padEnd(6)} ${params.padEnd(10)} ${(m.ms+'ms').padEnd(10)} "${m.reply}"`)
  })
}

console.log('\nDone.')
