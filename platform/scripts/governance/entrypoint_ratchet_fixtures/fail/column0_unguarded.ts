// FAIL fixture — the plain M0-T60 defect: `main()` at column 0 with no guard, so importing
// this module runs the program. This is the form 76 files in the tree carried on 2026-08-23.
// EXPECT-VIOLATIONS: 1
async function main(): Promise<void> {
  console.log('would connect to the database and write')
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
