---
artifact: PARIPRASHNA_EDIR_V3_REGISTER_S4
version: 1.0
status: LIVING — this is S4's OWN append-only findings register. Only S4
  agents write here. No other stream, and no convergence/index session,
  edits this file's entries — cross-stream corrections go through the
  referral protocol (elevation §8.3) and land as a new entry in the
  REFERRING stream's own file, cross-referencing the id here.
date: 2026-08-29
authoritative_side: claude
role: >
  S4's shard of the EDIR V3 register, split out of the single shared
  `EDIR_V3_REGISTER_v1_0.md` on 2026-08-29 so that S4 appending findings
  can never again produce a git merge conflict against S1, S2, S3, S5, S6
  appending their own findings concurrently (see `EDIR_V3_REGISTER_v1_0.md`
  §4a for the full rationale and the other five streams' files). Governed by
  the same Register law and Entry schema as the index file — this file does
  not restate them; see `EDIR_V3_REGISTER_v1_0.md` "Register law" / "Entry
  schema" sections, which apply here verbatim.
parent: 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
stream: S4
id_convention: >
  New S4 findings are `S4-V3-E-nnn`, sequential, claimed by appending (never
  by editing a prior entry's number). `S4-V3-E-016` was already used
  PRE-SPLIT as S4's own document-local numbering for a finding the archive
  itself flags as a "numeric collision" with the separately-numbered,
  unrelated `V3-E-016` (register_leak_lint id-leakage, a different bug that
  happens to share "016") — disclosed there, not merged. To avoid re-minting
  that number, **the next S4 id to claim is `S4-V3-E-017`.** S4 was also the
  fix-owning stream for several pre-split findings filed under the shared,
  un-prefixed `V3-E-nnn` namespace (e.g. V3-E-021, V3-E-014 — see each
  entry's own "filed to stream S4" line in the archive). This file does not
  hand-attribute a full list — grep the archive for `filed to stream
  \*\*S4\*\*` or `stream \*\*S4\*\*` to find them.
changelog:
  - "1.0 (2026-08-29): opened by the A5 per-stream split. No entries yet —
    S4's pre-split entries stay in the archive under the shared V3-E-nnn
    namespace, findable there by grep (see id_convention); next id to claim
    is S4-V3-E-017 (S4-V3-E-016 already reserved by a pre-split document-
    local number)."
---

# Paripraśna EDIR V3 — S4 register

Append new S4 findings below, oldest first, using the schema and law defined
in `EDIR_V3_REGISTER_v1_0.md`. Do not edit an existing entry's observed text
to soften it — corrections append as a new entry citing the one they
correct. Do not write to any other stream's file or to the shared index.

## Entries

_(none yet — this file was opened empty by the 2026-08-29 split; the next id
to claim is `S4-V3-E-017`)_
