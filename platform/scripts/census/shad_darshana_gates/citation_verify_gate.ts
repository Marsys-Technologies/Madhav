#!/usr/bin/env tsx
/**
 * citation_verify_gate.ts — SAMPURTI L0a / G16 citation-resolving gate (Part 4).
 *
 * DESIGN AUTHORITY: SAMPURTI MASTER_PLAN_v1_0.md §G16-P4 — "Upgrade the census's CI gate so
 * it randomly samples N=5 rows whose disposition cites a commit SHA or file path and RESOLVES
 * the citation (git cat-file -e for SHAs; fs.existsSync for paths), failing if any citation
 * doesn't resolve."
 *
 * Earned-Signal principle (CLAUDE.md §N.8): a census row's `evidence` field is only as honest
 * as the citations it contains. A citation that references a SHA that does not exist, or a
 * file path that was renamed/deleted, is a false claim — as bad as the D-CLASS-3 NOT-STARTED
 * error this gate is designed to catch and prevent from regressing. This gate makes the claim
 * machine-verifiable at every CI run by sampling and resolving citations at gate time.
 *
 * Algorithm:
 *   1. Load SHAD_DARSHANA_ITEM_REGISTRY from completeness_census_seed.ts.
 *   2. Collect all rows that carry an `evidence` field containing at least one verifiable
 *      citation (SHA token or file path token).
 *   3. Randomly sample N=5 of them (seeded from current epoch / 1800000 for 30-min stability;
 *      override with CITATION_GATE_SEED env var for reproducible test runs).
 *   4. For each sampled row, parse all citations from its `evidence` string and resolve each:
 *        - SHA token: `git cat-file -e <sha>` in REPO_ROOT. Exit 0 = exists. Exit non-0 = FAIL.
 *        - File path token: `existsSync(path.join(REPO_ROOT, token))`. false = FAIL.
 *   5. Emit the result as a GateReport (exit 0 = all sampled citations resolve; exit 1 = any fail).
 *
 * SHA token detection: 7- to 40-hex-char token that appears in the evidence string.
 * File path token detection: a token starting with `platform/`, `platform-mcp/`, or other known
 * repo-root-relative path prefixes.
 *
 * Run (from `platform/`):
 *   npx tsx scripts/census/shad_darshana_gates/citation_verify_gate.ts
 *
 * Override the sample (comma-separated item ids, for test reproducibility):
 *   CITATION_GATE_FORCE_IDS=1,8,11,22,31 npx tsx ...
 *
 * PLAN/LIVE: this gate is pure static/git — no MCP calls needed. Always runnable. Exit 0 =
 * all sampled citations resolve; exit 1 = any FAIL.
 */
import { existsSync } from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { printGateReport, type GateResult } from './_report'
import { SHAD_DARSHANA_ITEM_REGISTRY } from './completeness_census_seed'

// --- Config ------------------------------------------------------------------

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..', '..')
const SAMPLE_SIZE = 5

// Regex for a verifiable SHA token: 7–40 lowercase hex characters
const SHA_RE = /\b([0-9a-f]{7,40})\b/g

// Path prefixes that indicate a repo-root-relative file citation
const PATH_PREFIXES = [
  'platform/',
  'platform-mcp/',
  '00_ARCHITECTURE/',
  'platform-mcp/src/',
  'platform/python-sidecar/',
  'platform/src/',
  'platform/scripts/',
]

// --- Citation parsing --------------------------------------------------------

export interface ParsedCitation {
  raw: string
  kind: 'sha' | 'path'
}

/**
 * Extract all verifiable citations from an evidence string.
 * Returns SHA tokens (hex 7-40 chars) and file-path tokens (recognizable by path prefix).
 */
export function parseCitations(evidence: string): ParsedCitation[] {
  const results: ParsedCitation[] = []

  // SHA tokens
  const shaMatches = [...evidence.matchAll(SHA_RE)]
  for (const m of shaMatches) {
    results.push({ raw: m[1], kind: 'sha' })
  }

  // File path tokens: split on whitespace/semicolons/parens and look for path-prefixed segments
  const segments = evidence.split(/[\s;()\n]+/)
  for (const seg of segments) {
    const trimmed = seg.trim().replace(/[,;)]+$/, '')
    if (PATH_PREFIXES.some((p) => trimmed.startsWith(p))) {
      results.push({ raw: trimmed, kind: 'path' })
    }
  }

  // Deduplicate by raw value
  const seen = new Set<string>()
  return results.filter((c) => {
    if (seen.has(c.raw)) return false
    seen.add(c.raw)
    return true
  })
}

// --- Citation resolution -----------------------------------------------------

export interface CitationResolution {
  citation: ParsedCitation
  resolved: boolean
  detail: string
}

/**
 * Resolve one citation: SHA via `git cat-file -e`; path via `existsSync`.
 */
export function resolveCitation(citation: ParsedCitation): CitationResolution {
  if (citation.kind === 'sha') {
    try {
      execFileSync('git', ['cat-file', '-e', citation.raw], {
        cwd: REPO_ROOT,
        stdio: 'pipe',
      })
      return { citation, resolved: true, detail: `git cat-file -e ${citation.raw}: object exists` }
    } catch {
      return { citation, resolved: false, detail: `git cat-file -e ${citation.raw}: object NOT FOUND in repo` }
    }
  } else {
    const abs = path.join(REPO_ROOT, citation.raw)
    const exists = existsSync(abs)
    return {
      citation,
      resolved: exists,
      detail: exists ? `existsSync(${citation.raw}): true` : `existsSync(${citation.raw}): false — path does not exist in repo`,
    }
  }
}

// --- Sampling ----------------------------------------------------------------

/**
 * Deterministic seeded shuffle (Fisher-Yates with LCG).
 * Not cryptographic — only used for reproducible test sampling.
 */
function seededSample<T>(arr: T[], n: number, seed: number): T[] {
  const copy = [...arr]
  let s = seed >>> 0
  function next(): number {
    s = Math.imul(s, 1664525) + 1013904223
    return (s >>> 0) / 0x100000000
  }
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(next() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy.slice(0, Math.min(n, copy.length))
}

// --- Gate main ---------------------------------------------------------------

function validate(): GateResult[] {
  const results: GateResult[] = []

  // Step 1: collect rows with at least one verifiable citation
  const citable = SHAD_DARSHANA_ITEM_REGISTRY.filter((item) => {
    if (!item.evidence) return false
    const parsed = parseCitations(item.evidence)
    return parsed.length > 0
  })

  results.push({
    id: 'citation-corpus-size',
    title: 'Census rows carrying at least one verifiable evidence citation',
    status: citable.length >= SAMPLE_SIZE ? 'PASS' : 'FAIL',
    detail: `citable_rows=${citable.length}, required_minimum=${SAMPLE_SIZE}`,
  })

  if (citable.length < SAMPLE_SIZE) {
    // Cannot sample — fail fast. The corpus-size check already reports FAIL.
    return results
  }

  // Step 2: select sample
  let sample: typeof citable
  const forceEnv = process.env.CITATION_GATE_FORCE_IDS
  if (forceEnv) {
    const ids = new Set(forceEnv.split(',').map((s) => s.trim()).filter(Boolean))
    sample = citable.filter((item) => ids.has(item.id))
    if (sample.length === 0) {
      results.push({
        id: 'citation-sample-forced',
        title: `Forced sample via CITATION_GATE_FORCE_IDS=${forceEnv}`,
        status: 'FAIL',
        detail: `None of the forced ids (${forceEnv}) matched citable rows. Valid citable ids: ${citable.map((i) => i.id).join(', ')}`,
      })
      return results
    }
  } else {
    // Seed from epoch / 1800000 (30-min window; override via CITATION_GATE_SEED)
    const seedEnv = process.env.CITATION_GATE_SEED
    const seed = seedEnv ? parseInt(seedEnv, 10) : Math.floor(Date.now() / 1_800_000)
    sample = seededSample(citable, SAMPLE_SIZE, seed)
  }

  results.push({
    id: 'citation-sample-selected',
    title: `Randomly sampled ${sample.length} rows for citation resolution`,
    status: 'PASS',
    detail: `sampled_ids=[${sample.map((i) => i.id).join(', ')}]`,
  })

  // Step 3: resolve citations for each sampled row
  let anyFail = false
  for (const item of sample) {
    const citations = parseCitations(item.evidence!)
    const resolutions = citations.map(resolveCitation)
    const failed = resolutions.filter((r) => !r.resolved)

    if (failed.length > 0) {
      anyFail = true
      for (const r of failed) {
        results.push({
          id: `citation-resolve-item${item.id}-${r.citation.kind}-${r.citation.raw.slice(0, 12)}`,
          title: `Item ${item.id} — UNRESOLVED ${r.citation.kind} citation: ${r.citation.raw.slice(0, 20)}`,
          status: 'FAIL',
          detail: r.detail,
        })
      }
      // Also record which citations DID resolve for completeness
      const ok = resolutions.filter((r) => r.resolved)
      if (ok.length > 0) {
        results.push({
          id: `citation-resolve-item${item.id}-ok`,
          title: `Item ${item.id} — ${ok.length} citation(s) resolved OK`,
          status: 'PASS',
          detail: ok.map((r) => r.detail).join(' | '),
        })
      }
    } else {
      results.push({
        id: `citation-resolve-item${item.id}`,
        title: `Item ${item.id} — all ${resolutions.length} citation(s) resolve`,
        status: 'PASS',
        detail: resolutions.map((r) => r.detail).join(' | '),
      })
    }
  }

  if (!anyFail) {
    results.push({
      id: 'citation-gate-verdict',
      title: `All ${sample.length} sampled rows: every citation resolved`,
      status: 'PASS',
      detail: `sampled_ids=[${sample.map((i) => i.id).join(', ')}] — zero unresolved citations`,
    })
  } else {
    results.push({
      id: 'citation-gate-verdict',
      title: 'CITATION GATE FAILED: unresolved citations found in sample',
      status: 'FAIL',
      detail: 'One or more `evidence` fields cite a commit SHA or file path that does not exist in the repo. Fix the evidence field or the missing artifact before merging.',
    })
  }

  return results
}

function main(): void {
  process.exit(printGateReport('citation_verify_gate', validate()))
}

if (process.argv[1] && /citation_verify_gate\.(ts|mts|cts|js|mjs|cjs)$/.test(process.argv[1])) {
  main()
}
