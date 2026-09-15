/** Reproducible compiler for the planner-facing capability knowledge snapshot. */
import { readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { getCatalog } from '../src/lib/retrieval/registry/catalog'
import { compileCapabilityKnowledge, inspectCapabilityKnowledge } from '../src/lib/retrieval/registry/knowledge'
import { resolveCapabilityKnowledgeGeneratedAt } from './lib/capability_knowledge_provenance'

const check = process.argv.includes('--check')
const outputPath = path.resolve(process.cwd(), 'src/generated/capability_knowledge.snapshot.json')
const generatedAt = resolveCapabilityKnowledgeGeneratedAt(path.resolve(process.cwd(), '..'))

const catalog = getCatalog()
const snapshot = compileCapabilityKnowledge(catalog, generatedAt)
const report = inspectCapabilityKnowledge(catalog, snapshot)
if (!report.passed) throw new Error(`Capability knowledge integrity failed: ${JSON.stringify(report.findings)}`)
const rendered = `${JSON.stringify(snapshot, null, 2)}\n`

if (check) {
  const existing = readFileSync(outputPath, 'utf8')
  if (existing !== rendered) throw new Error('capability_knowledge.snapshot.json is stale; run npm run codegen:capability-knowledge')
  console.log(`capability knowledge snapshot current: ${snapshot.content_hash}; ${snapshot.census.semantic_capabilities} SCUs`)
} else {
  writeFileSync(outputPath, rendered)
  console.log(`wrote ${outputPath}: ${snapshot.content_hash}; ${snapshot.census.semantic_capabilities} SCUs`)
}
