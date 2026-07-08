/**
 * generate_registry_shims.ts — R5 W0b-codegen keystone script #2
 * ==================================================================
 * Design mandate: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §19 (single-source
 * contract generation) + brief §6.2 (STRANGLER — migrate one instrument at a time, behind
 * a parity gate; "no single PR regenerates the estate").
 *
 * WHAT THIS GENERATES: for each PILOT instrument listed in `registry_manifest.ts`, a Zod
 * input-validation schema (+ a name/URI map) derived from that instrument's registry
 * CapabilityDescriptor (`input_schema` + `required_inputs` + `uri`) — the same descriptor
 * object that today only drives the platform-side dispatcher. platform-mcp's hand-written
 * shims (e.g. `src/tools/register_p1_ganita.ts`) currently re-type each tool's zod schema
 * BY HAND, independently of the descriptor. This script closes that gap for the pilot set.
 *
 * WHY STATIC AST PARSING, NOT IMPORT/EXECUTION (critical §19 distinction from
 * generate_envelope.ts, whose source has zero imports): CapabilityDescriptor modules
 * (`platform/src/lib/retrieval/registry/layers/**`) import `@/lib/db/client` and other
 * platform-only runtime deps (DB pool, path-mapped `@/` aliases). platform-mcp is a
 * separate deployable process/package with its own node_modules and a plain NodeNext
 * tsconfig — it CANNOT resolve `@/lib/db/client` at build or run time, and must NEVER try
 * to `import()` or `require()` these files. Instead this script parses the descriptor
 * file's SOURCE TEXT with the TypeScript compiler API and evaluates only the literal
 * (string/number/boolean/array/object literal) AST nodes of the `input_schema` /
 * `required_inputs` / `uri` / `name` properties — no module resolution, no execution,
 * no side effects. If a descriptor's schema is expressed in a form this literal-evaluator
 * doesn't understand (e.g. a computed property, a spread, a non-literal default), the
 * script HALTS loudly for that field rather than silently guessing.
 *
 * STRANGLER SCOPE (brief §6.2): only the PILOT set from `registry_manifest.ts` is
 * generated. The generated shim lands ALONGSIDE the existing handwritten shim in
 * `register_p1_ganita.ts` — it does NOT replace it, does NOT get wired into the live
 * server.tool() registration, and the handwritten shim is not deleted. Promotion of a
 * generated shim to be the LIVE registration is a separate, later, single-instrument PR
 * gated on its own parity run (unlike the envelope module, which had zero live callers of
 * the old path once the import was repointed — this is a genuine narrower migration).
 *
 * PARITY NOTE: the current handwritten MCP-facing shims for these 3 pilots expose only
 * {chart_id, ayanamsha_id, limit, offset} — a deliberately narrowed facade of the full
 * registry descriptor (which for get_tajik also has categories/include_varsha/year_min/
 * year_max). This script generates the FULL descriptor-derived schema (the honest
 * single-source artifact); the parity-gate test therefore compares behavior on the
 * INTERSECTING field set the live shim actually accepts today, not the full descriptor
 * surface. Widening the live MCP shim to the full descriptor surface is a future-wave
 * product decision, not a codegen-correctness question — flagged, not resolved, here.
 *
 * USAGE: tsx scripts/generate_registry_shims.ts [--check]
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import ts from 'typescript'
import { REGISTRY_MANIFEST, type RegistryManifestEntry } from './registry_manifest.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUTPUT_PATH = path.resolve(__dirname, '../src/generated/registry_shims.ts')
const GENERATOR_REL_PATH = 'platform-mcp/scripts/generate_registry_shims.ts'

// ── Minimal literal-only AST evaluator ────────────────────────────────────────

type JsonLiteral = string | number | boolean | null | JsonLiteral[] | { [k: string]: JsonLiteral }

function evalLiteral(node: ts.Node, sf: ts.SourceFile, ctxLabel: string): JsonLiteral {
  if (ts.isStringLiteralLike(node)) return node.text
  if (ts.isNumericLiteral(node)) return Number(node.text)
  if (node.kind === ts.SyntaxKind.TrueKeyword) return true
  if (node.kind === ts.SyntaxKind.FalseKeyword) return false
  if (node.kind === ts.SyntaxKind.NullKeyword) return null
  if (ts.isArrayLiteralExpression(node)) {
    return node.elements.map(el => evalLiteral(el, sf, ctxLabel))
  }
  if (ts.isObjectLiteralExpression(node)) {
    const out: Record<string, JsonLiteral> = {}
    for (const prop of node.properties) {
      if (!ts.isPropertyAssignment(prop)) {
        throw new Error(`[generate_registry_shims] HALT (${ctxLabel}): non-literal object member ` +
          `(${ts.SyntaxKind[prop.kind]}) at ${prop.getText(sf)} — this generator only understands ` +
          `plain literal PropertyAssignments. Raise with the native before hand-patching around this.`)
      }
      const key = ts.isIdentifier(prop.name) || ts.isStringLiteralLike(prop.name)
        ? prop.name.text
        : (() => { throw new Error(`[generate_registry_shims] HALT (${ctxLabel}): computed property key ` +
            `not supported: ${prop.name.getText(sf)}`) })()
      out[key] = evalLiteral(prop.initializer, sf, `${ctxLabel}.${key}`)
    }
    return out
  }
  throw new Error(
    `[generate_registry_shims] HALT (${ctxLabel}): AST node kind ${ts.SyntaxKind[node.kind]} ` +
    `("${node.getText(sf).slice(0, 80)}") is not a literal this generator can statically evaluate. ` +
    `Descriptor input_schema/required_inputs must be plain literals for codegen — raise with the ` +
    `native if a pilot instrument's descriptor needs a computed/dynamic schema field.`,
  )
}

interface ParsedDescriptor {
  uri: string
  name: string
  inputSchema: Record<string, JsonLiteral>
  requiredInputs: string[]
}

function findExportedConstObjectLiteral(sf: ts.SourceFile, exportName: string): ts.ObjectLiteralExpression {
  let found: ts.ObjectLiteralExpression | undefined
  sf.forEachChild(node => {
    if (found) return
    if (!ts.isVariableStatement(node)) return
    const isExported = node.modifiers?.some(m => m.kind === ts.SyntaxKind.ExportKeyword) ?? false
    if (!isExported) return
    for (const decl of node.declarationList.declarations) {
      if (ts.isIdentifier(decl.name) && decl.name.text === exportName && decl.initializer &&
          ts.isObjectLiteralExpression(decl.initializer)) {
        found = decl.initializer
      }
    }
  })
  if (!found) {
    throw new Error(`[generate_registry_shims] HALT: could not find "export const ${exportName} = {...}" ` +
      `as a top-level object literal in the descriptor source.`)
  }
  return found
}

function parseDescriptor(entry: RegistryManifestEntry): ParsedDescriptor {
  const descriptorAbsPath = path.resolve(__dirname, entry.descriptorPath)
  const sourceText = readFileSync(descriptorAbsPath, 'utf8')
  const sf = ts.createSourceFile(descriptorAbsPath, sourceText, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS)
  const objLit = findExportedConstObjectLiteral(sf, entry.exportName)

  const props: Record<string, ts.Expression> = {}
  for (const prop of objLit.properties) {
    if (ts.isPropertyAssignment(prop) && ts.isIdentifier(prop.name)) {
      props[prop.name.text] = prop.initializer
    }
    // Non-literal members (e.g. `async handler(...) {...}` is a MethodDeclaration, not a
    // PropertyAssignment) are intentionally skipped here — we only need uri/name/input_schema/
    // required_inputs, never the handler body (which is exactly the platform-only-import code
    // this generator must never execute or resolve).
  }

  const uriExpr = props['uri']
  const nameExpr = props['name']
  const inputSchemaExpr = props['input_schema']
  const requiredInputsExpr = props['required_inputs']
  if (!uriExpr || !nameExpr || !inputSchemaExpr || !requiredInputsExpr) {
    throw new Error(`[generate_registry_shims] HALT: descriptor ${entry.exportName} is missing one of ` +
      `uri/name/input_schema/required_inputs as a direct literal property.`)
  }

  const uri = evalLiteral(uriExpr, sf, `${entry.exportName}.uri`) as string
  const name = evalLiteral(nameExpr, sf, `${entry.exportName}.name`) as string
  const inputSchema = evalLiteral(inputSchemaExpr, sf, `${entry.exportName}.input_schema`) as Record<string, JsonLiteral>
  const requiredInputs = evalLiteral(requiredInputsExpr, sf, `${entry.exportName}.required_inputs`) as string[]

  if (uri !== entry.uri) {
    throw new Error(`[generate_registry_shims] HALT: sanity check failed for ${entry.mcpToolName} — ` +
      `manifest uri "${entry.uri}" != parsed descriptor uri "${uri}".`)
  }

  return { uri, name, inputSchema, requiredInputs }
}

// ── ParameterSchema (JSON-Schema-like) → zod expression text ─────────────────

function paramSchemaToZodExpr(key: string, schema: Record<string, JsonLiteral>, required: boolean): string {
  const type = schema['type'] as string
  const description = schema['description'] as string | undefined
  const hasDefault = Object.prototype.hasOwnProperty.call(schema, 'default')
  const defaultVal = schema['default']

  let base: string
  switch (type) {
    case 'string':
      // Convention (matches every handwritten shim in register_p1_ganita.ts): the chart_id
      // field is always a UUID. This is the one type-inference step beyond a literal
      // JSON-Schema→zod mapping; flagged here rather than silently assumed elsewhere.
      base = key === 'chart_id' ? 'z.string().uuid()' : 'z.string()'
      break
    case 'number':
      base = 'z.number()'
      break
    case 'boolean':
      base = 'z.boolean()'
      break
    case 'array': {
      const items = schema['items'] as Record<string, JsonLiteral> | undefined
      const itemType = items?.['type'] === 'number' ? 'z.number()'
        : items?.['type'] === 'boolean' ? 'z.boolean()'
        : 'z.string()'
      base = `z.array(${itemType})`
      break
    }
    case 'object':
      base = 'z.record(z.unknown())'
      break
    default:
      throw new Error(`[generate_registry_shims] HALT: unsupported ParameterSchema type "${type}" for field "${key}".`)
  }

  if (description) base += `.describe(${JSON.stringify(description)})`
  if (!required) base += '.optional()'
  if (hasDefault) base += `.default(${JSON.stringify(defaultVal)})`
  return base
}

function buildShimModuleSource(entries: Array<{ manifest: RegistryManifestEntry; descriptor: ParsedDescriptor }>): string {
  const sourceRefs = entries.map(e => `\`${e.manifest.descriptorPath.replace('../../', 'platform/src/lib/retrieval/registry/')}\``)
  void sourceRefs

  const schemaBlocks = entries.map(({ manifest, descriptor }) => {
    const fields = Object.entries(descriptor.inputSchema).map(([key, schema]) => {
      const required = descriptor.requiredInputs.includes(key)
      const zodExpr = paramSchemaToZodExpr(key, schema as Record<string, JsonLiteral>, required)
      return `  ${key}: ${zodExpr},`
    }).join('\n')

    const constName = `${toCamel(manifest.mcpToolName)}GeneratedInputSchema`
    return `/** Generated from ${manifest.descriptorPath} (export ${manifest.exportName}), uri=${descriptor.uri}. */\n` +
      `export const ${constName} = {\n${fields}\n} as const\n`
  }).join('\n')

  const nameMapEntries = entries.map(({ manifest, descriptor }) =>
    `  ${JSON.stringify(manifest.mcpToolName)}: ${JSON.stringify(descriptor.uri)},`).join('\n')

  return `/**
 * registry_shims.ts — GENERATED, DO NOT HAND-EDIT.
 * ===================================================
 * Generated by \`${GENERATOR_REL_PATH}\` from the registry CapabilityDescriptor modules
 * named in \`registry_manifest.ts\` (STRANGLER pilot set — design §19 + brief §6.2). Each
 * schema below is derived from that instrument's \`input_schema\` + \`required_inputs\`,
 * parsed statically (TypeScript AST, no import/execution — see the generator's docstring
 * for why). Run \`npm run codegen:registry-shims\` to regenerate; run with --check in CI.
 *
 * LANDED ALONGSIDE, NOT WIRED IN (brief §6.2 strangler discipline): these schemas are NOT
 * imported by \`register_p1_ganita.ts\`'s live server.tool() registrations. The existing
 * handwritten schemas (ganitaStrengthGetInputSchema / ganitaSadeSatiGetInputSchema /
 * ganitaTajakaGetInputSchema, exported from that file) remain the live contract. The
 * parity-gate test (\`src/__tests__/r5_codegen_parity.test.ts\`) is what proves these
 * generated schemas already agree with the live ones on the intersecting field set —
 * promotion to "live" is a separate, later, single-instrument decision.
 */
import { z } from 'zod'

${schemaBlocks}
/** mcpToolName → capability URI, for reference / future promotion wiring. */
export const REGISTRY_SHIM_NAME_MAP: Record<string, string> = {
${nameMapEntries}
}
`
}

function toCamel(mcpToolName: string): string {
  return mcpToolName.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase())
}

function main(): void {
  const checkMode = process.argv.includes('--check')
  const parsed = REGISTRY_MANIFEST.map(manifest => ({ manifest, descriptor: parseDescriptor(manifest) }))
  const generated = buildShimModuleSource(parsed)

  if (checkMode) {
    if (!existsSync(OUTPUT_PATH)) {
      console.error(`[generate_registry_shims --check] FAIL: ${OUTPUT_PATH} does not exist.`)
      process.exit(1)
    }
    const existing = readFileSync(OUTPUT_PATH, 'utf8')
    if (existing !== generated) {
      console.error(`[generate_registry_shims --check] FAIL: generated/registry_shims.ts is STALE. ` +
        `Run \`npm run codegen:registry-shims\` and commit the result.`)
      process.exit(1)
    }
    console.log('[generate_registry_shims --check] OK: generated/registry_shims.ts is up to date.')
    return
  }

  writeFileSync(OUTPUT_PATH, generated, 'utf8')
  console.log(`[generate_registry_shims] wrote ${OUTPUT_PATH} (${parsed.length} pilot instruments)`)
}

// keep the hash helper available even though not currently emitted into the banner
// (parity with generate_envelope.ts's pattern; the URI sanity check above is this
// script's drift guard instead of a content hash, since 3 separate source files feed
// one output).
void createHash

main()
