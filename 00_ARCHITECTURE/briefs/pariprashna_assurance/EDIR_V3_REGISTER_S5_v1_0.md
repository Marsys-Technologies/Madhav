---
artifact: PARIPRASHNA_EDIR_V3_REGISTER_S5
version: 1.0
status: LIVING — this is S5's OWN append-only findings register. Only S5
  agents write here. No other stream, and no convergence/index session,
  edits this file's entries — cross-stream corrections go through the
  referral protocol (elevation §8.3) and land as a new entry in the
  REFERRING stream's own file, cross-referencing the id here.
date: 2026-08-29
authoritative_side: claude
role: >
  S5's shard of the EDIR V3 register, split out of the single shared
  `EDIR_V3_REGISTER_v1_0.md` on 2026-08-29 so that S5 appending findings
  can never again produce a git merge conflict against S1, S2, S3, S4, S6
  appending their own findings concurrently (see `EDIR_V3_REGISTER_v1_0.md`
  §4a for the full rationale and the other five streams' files). Governed by
  the same Register law and Entry schema as the index file — this file does
  not restate them; see `EDIR_V3_REGISTER_v1_0.md` "Register law" / "Entry
  schema" sections, which apply here verbatim.
parent: 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
stream: S5
id_convention: >
  New S5 findings are `S5-V3-E-nnn`, sequential, claimed by appending (never
  by editing a prior entry's number). No `S5-V3-E-*` id had been minted
  before this split. **The next S5 id to claim is `S5-V3-E-001`.** S5's own
  "S5 convergence note" (in the archive) states plainly which pre-split ids
  it contributed under the shared, un-prefixed `V3-E-nnn` namespace:
  `E-001`, `V3-E-017`..`V3-E-020`, `V3-E-022`. Those, plus S5's "S5
  convergence note" and "S5 LIVE-rung evidence log" sections, stay in the
  archive exactly as written and are not renumbered or copied here.
changelog:
  - "1.0 (2026-08-29): opened by the A5 per-stream split. No entries yet —
    S5's pre-split entries (E-001, V3-E-017..020, V3-E-022, plus the S5
    convergence note and LIVE-rung evidence log) stay in the archive; next
    id to claim is S5-V3-E-001."
---

# Paripraśna EDIR V3 — S5 register

Append new S5 findings below, oldest first, using the schema and law defined
in `EDIR_V3_REGISTER_v1_0.md`. Do not edit an existing entry's observed text
to soften it — corrections append as a new entry citing the one they
correct. Do not write to any other stream's file or to the shared index.

## Entries

_(none yet — this file was opened empty by the 2026-08-29 split; the next id
to claim is `S5-V3-E-001`)_
