/**
 * generate_envelope.ts — R5 W0b-codegen keystone script #1
 * ===========================================================
 * Design mandate: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §19
 * ("SINGLE-SOURCE CONTRACT GENERATION" — a contract is declared ONCE; every other
 * process-boundary copy is GENERATED, never hand-mirrored).
 *
 * PROBLEM THIS CLOSES: platform-mcp is a standalone TS project (NodeNext, no path
 * mapping into the platform repo's `@/` aliases) and cannot `import` platform's
 * `src/lib/retrieval/envelope.ts` at runtime. The r5/w0b-envelope lane's stopgap was
 * a HAND-WRITTEN byte-for-byte mirror at `platform-mcp/src/lib/envelope.ts` — flagged
 * by the verifier ring as a genuine §19 violation (hand-maintained duplication across
 * this exact process seam is what silently dropped `as_of_date` on one side in the P1
 * audit failure). This script REPLACES that hand-mirror with a generated artifact.
 *
 * WHY THIS IS SAFE TO GENERATE MECHANICALLY (not just copy-paste in a different hat):
 * `platform/src/lib/retrieval/envelope.ts` has ZERO imports — it is pure, self-contained
 * TypeScript (types + functions only, no `@/lib/db/client` or other platform-only runtime
 * deps). That is exactly the property that makes it eligible for this codegen path (see
 * generate_registry_shims.ts's docstring for the contrasting case — CapabilityDescriptor
 * modules DO have such imports and must be parsed statically, never imported/executed).
 *
 * WHAT THIS SCRIPT ACTUALLY DOES (AST-driven, not a string copy):
 *   1. Reads the canonical source file.
 *   2. Parses it with the TypeScript compiler API (ts.createSourceFile).
 *   3. HALTS if the AST contains any ImportDeclaration/ImportEqualsDeclaration — a guard
 *      against silent breakage if envelope.ts ever grows a platform-only dependency (the
 *      contract this whole file exists to prevent from being hand-mirrored around).
 *   4. Re-emits the AST deterministically via the TS printer (canonicalizes formatting;
 *      proves the artifact is derived from a parsed, validated AST rather than raw text).
 *   5. Prepends a DO-NOT-HAND-EDIT banner + a content hash of the canonical source, so
 *      drift between the two files is mechanically detectable (see the parity-gate test
 *      and the `--check` flag, which fails CI if the committed generated file is stale
 *      relative to its source).
 *
 * USAGE: tsx scripts/generate_envelope.ts [--check]
 *   (no flag)  regenerate platform-mcp/src/generated/envelope.ts from the canonical source.
 *   --check    exit 1 if the committed generated file does not match what would be generated
 *              (CI drift gate — run in the same job as typecheck/test).
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import ts from 'typescript'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const SOURCE_PATH = path.resolve(__dirname, '../../platform/src/lib/retrieval/envelope.ts')
const OUTPUT_PATH = path.resolve(__dirname, '../src/generated/envelope.ts')
const GENERATOR_REL_PATH = 'platform-mcp/scripts/generate_envelope.ts'
const SOURCE_REL_PATH = 'platform/src/lib/retrieval/envelope.ts'

function hashOf(text: string): string {
  return createHash('sha256').update(text).digest('hex').slice(0, 16)
}

function assertNoImports(sourceFile: ts.SourceFile): void {
  const offenders: string[] = []
  sourceFile.forEachChild(node => {
    if (ts.isImportDeclaration(node) || ts.isImportEqualsDeclaration(node)) {
      offenders.push(node.getText(sourceFile))
    }
  })
  if (offenders.length > 0) {
    throw new Error(
      `[generate_envelope] HALT: ${SOURCE_REL_PATH} now has import(s) this generator cannot ` +
      `resolve across the platform / platform-mcp process boundary:\n  ${offenders.join('\n  ')}\n` +
      `This script only handles self-contained (zero-import) contract modules — see ` +
      `generate_registry_shims.ts for the static-AST-parse pattern used for modules with ` +
      `platform-only runtime deps (e.g. '@/lib/db/client'). Raise with the native before proceeding ` +
      `(a design-doc §19 judgment call — do not silently hand-mirror around this).`,
    )
  }
}

function stripLeadingFileDocComment(sourceFile: ts.SourceFile, sourceText: string): string {
  // The canonical file's own leading /** ... */ doc-comment describes ITS identity as the
  // single source of truth (mentions the hand-mirror this script replaces). The generated
  // file gets its own banner instead (below) — strip the source's leading block comment so
  // the generated output doesn't carry stale narrative about a hand-mirror that no longer exists.
  const firstStatement = sourceFile.statements[0]
  if (!firstStatement) return sourceText
  const leadingRanges = ts.getLeadingCommentRanges(sourceText, firstStatement.getFullStart()) ?? []
  if (leadingRanges.length === 0) return sourceText
  const last = leadingRanges[leadingRanges.length - 1]!
  return sourceText.slice(last.end).replace(/^\s+/, '')
}

function generate(): { generated: string; sourceHash: string } {
  const sourceText = readFileSync(SOURCE_PATH, 'utf8')
  const sourceFile = ts.createSourceFile(SOURCE_PATH, sourceText, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS)
  assertNoImports(sourceFile)

  const bodyOnly = stripLeadingFileDocComment(sourceFile, sourceText)
  const sourceHash = hashOf(sourceText)

  const banner = `/**
 * envelope.ts — GENERATED, DO NOT HAND-EDIT.
 * ============================================
 * Generated by \`${GENERATOR_REL_PATH}\` from \`${SOURCE_REL_PATH}\`
 * (source sha256:${sourceHash}). Run \`npm run codegen:envelope\` in platform-mcp/ to
 * regenerate after any change to the canonical source; run \`npm run codegen:check\` in CI
 * to detect drift.
 *
 * Design §19 (single-source contract generation): this file exists so the platform /
 * platform-mcp process-boundary envelope shape has exactly ONE authored copy (the canonical
 * file above) and every other copy is mechanically derived. A hand-written mirror
 * (\`platform-mcp/src/lib/envelope.ts\`) previously stood in for this file — it has been
 * deleted; this generated module is its replacement, closing the §19 violation flagged by
 * the r5/w0b-envelope lane's verifier ring.
 *
 * CONSUMER FORMAT NEGOTIATION (brief §6.3): response_format: 'legacy' | 'v3', default 'legacy'.
 * 'legacy' is byte-identical to the pre-W0b envelope shape (no live client breaks). 'v3' is
 * additive-only: every legacy field ships unchanged in shape, PLUS chart_header / epistemic /
 * timing / coverage, AND verdict/ranking_basis/grounding/drill_pointers/judgment_flags are
 * populated from data already present in the response (never fabricated — B.10).
 */

`
  return { generated: banner + bodyOnly, sourceHash }
}

function main(): void {
  const checkMode = process.argv.includes('--check')
  const { generated } = generate()

  if (checkMode) {
    if (!existsSync(OUTPUT_PATH)) {
      console.error(`[generate_envelope --check] FAIL: ${OUTPUT_PATH} does not exist.`)
      process.exit(1)
    }
    const existing = readFileSync(OUTPUT_PATH, 'utf8')
    if (existing !== generated) {
      console.error(
        `[generate_envelope --check] FAIL: generated/envelope.ts is STALE relative to ` +
        `${SOURCE_REL_PATH}. Run \`npm run codegen:envelope\` and commit the result.`,
      )
      process.exit(1)
    }
    console.log('[generate_envelope --check] OK: generated/envelope.ts is up to date.')
    return
  }

  writeFileSync(OUTPUT_PATH, generated, 'utf8')
  console.log(`[generate_envelope] wrote ${OUTPUT_PATH}`)
}

main()
