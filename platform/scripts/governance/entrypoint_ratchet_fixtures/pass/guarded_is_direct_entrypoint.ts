// PASS fixture — idiom 1 of 5. The contract this campaign standardised on for any module whose
// hazard is RUNNING (A3.4 operator rule 5).
// EXPECT-GUARD: isDirectEntrypoint
import { isDirectEntrypoint } from '../../lib/entrypoint'

export { isDirectEntrypoint }

async function main(): Promise<void> {
  console.log('only ever on an explicit npx tsx')
}

if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main().catch((err) => {
    console.error(err)
    process.exit(1)
  })
}
