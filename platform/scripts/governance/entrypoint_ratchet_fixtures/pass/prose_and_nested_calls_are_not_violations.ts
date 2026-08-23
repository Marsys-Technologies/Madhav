// PASS fixture — the D-72 caution, which ADHIKĀRIN adopted as binding on this ratchet's design:
// "a grep for a defective form cannot tell code that has the defect from prose that documents
// it — and that false-positive rate RISES as more files get fixed." It proved itself inside
// ADHIKĀRIN's own reconciliation command: the 14th guard-bearing file was
// scripts/audit/A3_env_matrix.md, DOCUMENTATION, which defeated both a pattern filter and a
// `.ts:` path filter, because prose that documents code quotes source paths.
//
// Everything below is either a comment, a string, or a call inside a function body. NONE of it
// is a top-level executor and none of it may be reported.
//
// The defective form, documented rather than committed:
//     main().catch((err) => { console.error(err); process.exit(1) })
//
/* And in a block comment, indented, which is the form fixed migration guides use:
     if (true) {
       main()
     }
*/
async function main(): Promise<void> {
  // A recursive-looking call INSIDE a function body: reached only when something calls main().
  if (process.env.NEVER) await main()
}

export function runner(): void {
  main().catch(() => undefined)
}

export const HELP = 'usage: npx tsx thing.ts   # do not write main() at top level'
export const MULTILINE = `
  main()
  if (true) { main() }
`

export function describeSomething(): void {
  ;[1, 2].forEach(() => {
    main()
  })
}
