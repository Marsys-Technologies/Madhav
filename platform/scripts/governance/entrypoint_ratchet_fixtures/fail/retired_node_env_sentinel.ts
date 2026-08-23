// FAIL fixture — the RETIRED `process.env.NODE_ENV` sentinel is NOT a guard and must never be
// accepted as one (ruling D-9 / M0-T60 finding F-2). It asks whether we are in a test run, not
// whether this module is the entrypoint: in any shell with NODE_ENV unset — every ordinary
// developer and agent shell — an import runs the whole program. This is the exact form that
// nearly applied migrations to production.
// EXPECT-VIOLATIONS: 1
async function main(): Promise<void> {
  console.log('applies migrations')
}

if (process.env.NODE_ENV !== 'test') {
  main()
}
