/**
 * r218_planner_p_need_report.ts — R218 (NIKASHA_CHANGE_REGISTER_v2_0.md, D5 rev. 2.1). CLI report.
 *
 * Thin wrapper around `platform/src/lib/retrieval/registry/knowledge/r218_p_need_check.ts`
 * (`evaluateAllPNeeds`) — loads the real, live `capability_knowledge.snapshot.json` and Lane B's
 * committed, READ-ONLY `producer_provenance.derived.json`, and prints the per-P-need report.
 *
 * Usage:
 *   npx tsx --conditions=react-server platform/scripts/governance/r218_planner_p_need_report.ts
 *
 * Writes nothing; prints a JSON report to stdout.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { evaluateAllPNeeds, type ProducerProvenance } from '../../src/lib/retrieval/registry/knowledge/r218_p_need_check'
import type { CapabilityKnowledgeSnapshot } from '../../src/lib/retrieval/registry/knowledge/types'

const REPO_ROOT = join(__dirname, '..', '..', '..')
const SNAPSHOT_PATH = join(REPO_ROOT, 'platform/src/generated/capability_knowledge.snapshot.json')
const PROVENANCE_PATH = join(
  REPO_ROOT,
  '00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/producer_provenance.derived.json',
)

function main() {
  const snapshot = JSON.parse(readFileSync(SNAPSHOT_PATH, 'utf-8')) as CapabilityKnowledgeSnapshot
  const provenance = JSON.parse(readFileSync(PROVENANCE_PATH, 'utf-8')) as ProducerProvenance
  const report = evaluateAllPNeeds(snapshot, provenance)
  console.log(JSON.stringify(report, null, 2))
}

main()
