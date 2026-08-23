// PASS fixture — idiom 4 of 5, a PRECOMPUTED boolean, and it is same-line as well
// (generate_vidhi_registry_mirror.ts:266 `if (isEntrypoint)`, governance/icr_pr_gate.ts:276
// `if (isMain)`). The guard expression is nowhere near the call site, which is why a detector
// that only reads the line above the call cannot see it.
// EXPECT-GUARD: isEntrypoint/isMain
import { fileURLToPath } from 'node:url'

const isEntrypoint = process.argv[1] === fileURLToPath(import.meta.url)

async function main(): Promise<void> {
  console.log('a codegen mirror')
}

if (isEntrypoint) main()
