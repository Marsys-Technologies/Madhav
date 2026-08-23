# DD-1 battery — banked red-proof evidence

**Closes MATERIAL-6** from `P3_P4_COMPLETENESS_AUDIT_2026-08-23.md`.

## Why this directory exists

`platform/.gitignore:21` ignores `/scripts/pariprashna/dd1_battery/out/`, which is where the
battery writes its receipt. So the DD-1 claim *"13/13 can-fail proven"* survived only in one
local worktree and, by the audit's own standard, rested on an agent's summary rather than on
evidence. These files are the evidence, at a path that is actually tracked.

The gitignore entry is left alone deliberately — routine local run artifacts *should* stay
untracked. What was missing was a curated, committed copy of the proof, not a policy change.

## What is actually proven here — 7 of 13, not 13

Read this number carefully, because it is smaller than the claim it replaces.

| red-proof key | check | `red_fired` | `green_clean` |
|---|---|---|---|
| `m4_ttft` | M4 | true | true |
| `m5_id_leak` | M5 | true | true |
| `m6_wire_late_define` | M6-wire | true | true |
| `reg_voice_lint` | REG | true | true |
| `plain_register` | PLAIN | true | true |
| `cite_integrity` | CITE | true | true |
| `edge_fixture_suite` | EDGE | true | true |

**Seven.** The remaining six checks live in the browser lane, whose red-proofs need a live
surface; this run executed `--red-proof --no-live --no-browser` and therefore did not produce
them. Nothing here should be read as evidence for those six.

Both halves matter and both are recorded per key: `red_fired` (the detector fired on a corpus
broken for exactly that rule) **and** `green_clean` (the same detector stayed quiet on the clean
counterpart). A detector that fires on everything is as useless as one that fires on nothing.

## Provenance

- Generated `2026-08-23T03:55:36Z`, from `main` at `0253f5e8e`.
- `detector_hash`: `fca9bd30a53bb1bce254160e19615c5125ab6d65deae7c185ce9c8b9ee631f8e`
- Command: `npx tsx scripts/pariprashna/dd1_battery/index.ts --red-proof --no-live --no-browser`
- The battery's own gate re-ran the repo selftest during this run (`pariprashna:selftest`, exit 0).

## How this receipt expires, by design

`red_proof.ts` binds the receipt to the bytes of its detector sources. Edit any detector and the
hash stops matching, the banked proof goes stale, and **every PASS it was gating degrades to
`NOT_IMPLEMENTED` until the proof is re-run.** That is the intended behaviour, not a bug: it is
what stops an edited-and-neutered detector from minting greens off an old receipt.

To refresh after touching a detector, re-run the command above and replace both files.
