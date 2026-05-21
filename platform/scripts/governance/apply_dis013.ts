// apply_dis013.ts — one-shot script to apply DIS.013 (MSR.377 signal_name correction)
// ICR-S5 (2026-05-21)
//
// Run: npx tsx scripts/governance/apply_dis013.ts
// Dry-run: npx tsx scripts/governance/apply_dis013.ts --dry-run

import { atomicApply } from '../../src/lib/icr/atomic_apply'
import * as path from 'path'

const dryRun = process.argv.includes('--dry-run')
const repoRoot = path.join(__dirname, '../../..')
const proposedPath = path.join(repoRoot, 'PROPOSED/DIS.013_MSR_377_proposed.yaml')

console.log(`apply_dis013: ${dryRun ? 'DRY RUN' : 'LIVE APPLY'}`)
console.log(`  proposed: ${proposedPath}`)
console.log(`  repoRoot: ${repoRoot}`)

const result = atomicApply(proposedPath, repoRoot, dryRun)
console.log(JSON.stringify(result, null, 2))

if (!result.ok) {
  console.error('APPLY FAILED')
  process.exit(1)
}

console.log(dryRun ? 'DRY RUN PASSED — no files written' : 'APPLY SUCCEEDED')
