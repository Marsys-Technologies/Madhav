---
artifact: PARIPRASHNA_EDIR_V3_REGISTER_S3
version: 1.0
status: LIVING — this is S3's OWN append-only findings register. Only S3
  agents write here. No other stream, and no convergence/index session,
  edits this file's entries — cross-stream corrections go through the
  referral protocol (elevation §8.3) and land as a new entry in the
  REFERRING stream's own file, cross-referencing the id here.
date: 2026-08-29
authoritative_side: claude
role: >
  S3's shard of the EDIR V3 register, split out of the single shared
  `EDIR_V3_REGISTER_v1_0.md` on 2026-08-29 so that S3 appending findings
  can never again produce a git merge conflict against S1, S2, S4, S5, S6
  appending their own findings concurrently (see `EDIR_V3_REGISTER_v1_0.md`
  §4a for the full rationale and the other five streams' files). Governed by
  the same Register law and Entry schema as the index file — this file does
  not restate them; see `EDIR_V3_REGISTER_v1_0.md` "Register law" / "Entry
  schema" sections, which apply here verbatim.
parent: 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
stream: S3
id_convention: >
  New S3 findings are `S3-V3-E-nnn`, sequential, claimed by appending (never
  by editing a prior entry's number). `S3-V3-E-001` was already used
  PRE-SPLIT as an inline cross-reference tag (not a standalone heading/entry
  in the register) attached to an existing V3-E-016-family finding — see the
  archive around its `reproduction_recorded` mention. To avoid re-minting
  that tag for a different finding, **the next S3 id to claim is
  `S3-V3-E-002`.** S3 authored and/or owned several pre-split findings under
  the shared, un-prefixed `V3-E-nnn` namespace (its own citation/grounding
  quality-corpus territory: V3-E-012 "S3 corpus territory", V3-E-016,
  V3-E-032 [note: two distinct headings pre-split share this exact number —
  a genuine unresolved id collision, left as found, not repaired by this
  split], V3-E-033 "S3 quality-corpus scoring harness"). This file does not
  hand-attribute a full list beyond what is explicitly lens-tagged
  `S3 corpus territory` in the archive — grep it for that phrase or for
  `stream \*\*S3\*\*` to find the rest.
changelog:
  - "1.0 (2026-08-29): opened by the A5 per-stream split. No entries yet —
    S3's pre-split entries stay in the archive under the shared V3-E-nnn
    namespace, findable there by grep (see id_convention); next id to claim
    is S3-V3-E-002 (S3-V3-E-001 already reserved by a pre-split inline tag)."
---

# Paripraśna EDIR V3 — S3 register

Append new S3 findings below, oldest first, using the schema and law defined
in `EDIR_V3_REGISTER_v1_0.md`. Do not edit an existing entry's observed text
to soften it — corrections append as a new entry citing the one they
correct. Do not write to any other stream's file or to the shared index.

**Known pre-existing defect in this territory (inherited, not S3's to fix
alone):** the archive carries an unresolved duplicate heading — two
different findings both titled `V3-E-032` (see
`EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md`). This split does not
repair it (repairing another stream's/session's prior text is out of scope
for a structural split); if S3 owns disambiguating it, file the resolution
here as a new `S3-V3-E-nnn` entry cross-referencing both archived headings
by line content, not by editing the archive.

## Entries

_(none yet — this file was opened empty by the 2026-08-29 split; the next id
to claim is `S3-V3-E-002`)_
