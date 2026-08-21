/**
 * generate_signal_glossary_mirror.ts — Python→TS codegen for the signal-register glossary
 * =========================================================================================
 * Design mandate: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §19 ("SINGLE-SOURCE
 * CONTRACT GENERATION" — a contract is declared ONCE; every other process-boundary copy is
 * GENERATED, never hand-mirrored). Same discipline as `generate_vidhi_registry_mirror.ts`
 * and `platform-mcp/scripts/generate_envelope.ts`, applied across the Python/TypeScript
 * boundary rather than the platform/platform-mcp one.
 *
 * PROBLEM THIS CLOSES (F-131): `platform/python-sidecar/brahmagyan/signal_register_glossary.py`
 * carries the acharya-grade fact_category→label mapping AND the internal-abstention marker
 * pattern list, but the surface that needs them most — `kala_priority_ranking_get`, a
 * TypeScript capability handler — cannot import a Python module. Hand-copying the tables into
 * TS would create exactly the drift hazard §19 exists to forbid. So the TS side is GENERATED
 * from the Python module and pinned to its sha256.
 *
 * HOW: the Python module is DATA-ONLY (three module-level literals, `from __future__ import
 * annotations` its only import), so this generator asks the Python interpreter itself for the
 * values (`python3 -c "import json; ..."`) rather than re-implementing a Python literal parser
 * in TS. The interpreter is the authority on what the module means — a hand-rolled parser
 * would be a second, drift-prone interpretation of the same file (the precise failure mode
 * §19 forbids). Codegen-time only: the generated file is committed, so neither the vitest
 * suite nor the Next.js build ever needs python3.
 *
 * DRIFT DETECTION WITHOUT PYTHON: the emitted module exports `SOURCE_SHA256`, the sha256 of
 * the canonical .py at generation time. `signal_glossary.parity.test.ts` re-hashes the .py and
 * asserts equality — so a Python-side edit that is not regenerated fails CI on a machine with
 * no Python at all. Same "content hash of the canonical source" mechanism
 * `generate_vidhi_registry_mirror.ts` uses.
 *
 * USAGE:
 *   npm run codegen:signal-glossary          # regenerate
 *   npm run codegen:signal-glossary:check    # exit 1 if the committed file is stale
 */
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import * as fs from 'node:fs'
import * as path from 'node:path'

const REPO_ROOT = path.resolve(__dirname, '..', '..')
const PY_SOURCE = path.join(
  REPO_ROOT, 'platform', 'python-sidecar', 'brahmagyan', 'signal_register_glossary.py',
)
const TS_TARGET = path.join(
  REPO_ROOT, 'platform', 'src', 'lib', 'retrieval', 'signal_glossary.generated.ts',
)

interface GlossaryPayload {
  FACT_CATEGORY_DISPLAY_LABEL: Record<string, string>
  SIGNAL_TYPE_GLOSSARY: Record<string, string>
  INTERNAL_MARKER_PATTERNS: string[]
}

/** Ask the Python interpreter for the module's three literals, as JSON. */
function readPythonGlossary(): GlossaryPayload {
  const sidecar = path.join(REPO_ROOT, 'platform', 'python-sidecar')
  const script = [
    'import json, sys',
    `sys.path.insert(0, ${JSON.stringify(sidecar)})`,
    'from brahmagyan import signal_register_glossary as g',
    'json.dump({',
    '  "FACT_CATEGORY_DISPLAY_LABEL": g.FACT_CATEGORY_DISPLAY_LABEL,',
    '  "SIGNAL_TYPE_GLOSSARY": g.SIGNAL_TYPE_GLOSSARY,',
    '  "INTERNAL_MARKER_PATTERNS": g.INTERNAL_MARKER_PATTERNS,',
    '}, sys.stdout)',
  ].join('\n')
  const out = execFileSync('python3', ['-c', script], { encoding: 'utf8' })
  const parsed = JSON.parse(out) as GlossaryPayload
  // HALT loudly rather than emit a hollow mirror (§N.8: a signal with no detector behind it
  // is null, not green — an empty table here would silently disable every downstream label).
  for (const key of ['FACT_CATEGORY_DISPLAY_LABEL', 'SIGNAL_TYPE_GLOSSARY'] as const) {
    if (Object.keys(parsed[key]).length === 0) {
      throw new Error(`${key} came back empty from ${PY_SOURCE} — refusing to emit a hollow mirror.`)
    }
  }
  if (parsed.INTERNAL_MARKER_PATTERNS.length === 0) {
    throw new Error(`INTERNAL_MARKER_PATTERNS came back empty from ${PY_SOURCE} — refusing to emit.`)
  }
  return parsed
}

function renderRecord(name: string, doc: string, value: Record<string, string>): string {
  const body = Object.entries(value)
    .map(([k, v]) => `  ${JSON.stringify(k)}: ${JSON.stringify(v)},`)
    .join('\n')
  return `${doc}\nexport const ${name}: Readonly<Record<string, string>> = Object.freeze({\n${body}\n})\n`
}

function renderList(name: string, doc: string, value: string[]): string {
  const body = value.map(v => `  ${JSON.stringify(v)},`).join('\n')
  return `${doc}\nexport const ${name}: readonly string[] = Object.freeze([\n${body}\n])\n`
}

export function generate(): string {
  const py = fs.readFileSync(PY_SOURCE, 'utf8')
  const sha = createHash('sha256').update(py, 'utf8').digest('hex')
  const data = readPythonGlossary()

  return [
    '/**',
    ' * signal_glossary.generated.ts — DO NOT HAND-EDIT.',
    ' * ============================================================================',
    ' * GENERATED from platform/python-sidecar/brahmagyan/signal_register_glossary.py',
    ' * by platform/scripts/generate_signal_glossary_mirror.ts (`npm run codegen:signal-glossary`).',
    ' *',
    ' * The Python module is the single source of truth for these tables. Edit it, then',
    ' * regenerate. `signal_glossary.parity.test.ts` re-hashes the .py and fails if this',
    ' * file is stale, so hand edits (or an un-regenerated Python edit) are caught in CI.',
    ' *',
    ' * Behaviour built ON these tables lives in the hand-written sibling',
    ' * `signal_glossary.ts` — this file is data only.',
    ' */',
    '',
    '/** sha256 of the canonical Python source at generation time (drift detector). */',
    `export const SOURCE_SHA256 = ${JSON.stringify(sha)}`,
    '',
    '/** Relative path of the canonical source, for error messages and the parity test. */',
    "export const SOURCE_PATH = 'platform/python-sidecar/brahmagyan/signal_register_glossary.py'",
    '',
    renderRecord(
      'FACT_CATEGORY_DISPLAY_LABEL',
      '/** raw `fact_category` (snake_case, as written to chart_facts) → acharya-grade display label. */',
      data.FACT_CATEGORY_DISPLAY_LABEL,
    ),
    renderRecord(
      'SIGNAL_TYPE_GLOSSARY',
      '/** Leaked headline token (space-separated form) → display label. Includes the two\n *  computation-abstention marker glosses. */',
      data.SIGNAL_TYPE_GLOSSARY,
    ),
    renderList(
      'INTERNAL_MARKER_PATTERNS',
      [
        '/** Substrings identifying rows that are NOT astrological findings — internal',
        ' *  floor/abstention markers written when no verifiable classical formula exists',
        ' *  (§B.10 / §N.4), plus catalog-only rows awaiting cross-verification.',
        ' *  Order is load-bearing: first match wins in `classifySignalMarker`. */',
      ].join('\n'),
      data.INTERNAL_MARKER_PATTERNS,
    ),
  ].join('\n')
}

function main(): void {
  const next = generate()
  const check = process.argv.includes('--check')
  const existing = fs.existsSync(TS_TARGET) ? fs.readFileSync(TS_TARGET, 'utf8') : null

  if (check) {
    if (existing !== next) {
      console.error(
        `[signal-glossary-mirror] STALE: ${path.relative(REPO_ROOT, TS_TARGET)} does not match ` +
        `${path.relative(REPO_ROOT, PY_SOURCE)}. Run: npm run codegen:signal-glossary`,
      )
      process.exit(1)
    }
    console.log('[signal-glossary-mirror] OK — generated mirror is current.')
    return
  }

  fs.writeFileSync(TS_TARGET, next, 'utf8')
  console.log(`[signal-glossary-mirror] wrote ${path.relative(REPO_ROOT, TS_TARGET)}`)
}

if (require.main === module) main()
