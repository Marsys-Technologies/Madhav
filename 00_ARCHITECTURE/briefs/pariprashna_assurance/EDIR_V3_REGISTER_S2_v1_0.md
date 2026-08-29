---
artifact: PARIPRASHNA_EDIR_V3_REGISTER_S2
version: 1.0
status: LIVING — this is S2's OWN append-only findings register. Only S2
  agents write here. No other stream, and no convergence/index session,
  edits this file's entries — cross-stream corrections go through the
  referral protocol (elevation §8.3) and land as a new entry in the
  REFERRING stream's own file, cross-referencing the id here.
date: 2026-08-29
authoritative_side: claude
role: >
  S2's shard of the EDIR V3 register, split out of the single shared
  `EDIR_V3_REGISTER_v1_0.md` on 2026-08-29 so that S2 appending findings
  can never again produce a git merge conflict against S1, S3, S4, S5, S6
  appending their own findings concurrently (see `EDIR_V3_REGISTER_v1_0.md`
  §4a for the full rationale and the other five streams' files). Governed by
  the same Register law and Entry schema as the index file — this file does
  not restate them; see `EDIR_V3_REGISTER_v1_0.md` "Register law" / "Entry
  schema" sections, which apply here verbatim.
parent: 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
stream: S2
id_convention: >
  New S2 findings are `S2-V3-E-nnn`, sequential, claimed by appending (never
  by editing a prior entry's number). No `S2-V3-E-*` id had been minted
  before this split. **The next S2 id to claim is `S2-V3-E-001`.** Note: S2
  authored and/or was the fix-owning stream for several findings pre-split
  under the shared, un-prefixed `V3-E-nnn` namespace (e.g. V3-E-030 fixed by
  S2; V3-E-021/V3-E-014/V3-E-015 authored during S2-territory investigation
  but filed to S4 as the root-cause-owning stream — "authored by" and "filed
  to" are not always the same stream in the pre-split text, so this file
  does not attempt to hand-attribute a specific list; grep the archive for
  `stream \*\*S2\*\*` / `filed to stream \*\*S2\*\*` to find them). Those
  entries stay in the archive exactly as written and are not renumbered or
  copied here.
changelog:
  - "1.0 (2026-08-29): opened by the A5 per-stream split. No entries yet —
    S2's pre-split entries stay in the archive under the shared V3-E-nnn
    namespace, findable there by grep (see id_convention); next id to claim
    is S2-V3-E-001."
---

# Paripraśna EDIR V3 — S2 register

Append new S2 findings below, oldest first, using the schema and law defined
in `EDIR_V3_REGISTER_v1_0.md`. Do not edit an existing entry's observed text
to soften it — corrections append as a new entry citing the one they
correct. Do not write to any other stream's file or to the shared index.

## Entries

_(none yet — this file was opened empty by the 2026-08-29 split; the next id
to claim is `S2-V3-E-001`)_
