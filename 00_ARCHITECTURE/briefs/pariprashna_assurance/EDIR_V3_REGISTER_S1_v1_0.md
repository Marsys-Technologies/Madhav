---
artifact: PARIPRASHNA_EDIR_V3_REGISTER_S1
version: 1.0
status: LIVING — this is S1's OWN append-only findings register. Only S1
  agents write here. No other stream, and no convergence/index session,
  edits this file's entries — cross-stream corrections go through the
  referral protocol (elevation §8.3) and land as a new entry in the
  REFERRING stream's own file, cross-referencing the id here.
date: 2026-08-29
authoritative_side: claude
role: >
  S1's shard of the EDIR V3 register, split out of the single shared
  `EDIR_V3_REGISTER_v1_0.md` on 2026-08-29 so that S1 appending findings
  can never again produce a git merge conflict against S2..S6 appending
  their own findings concurrently (see `EDIR_V3_REGISTER_v1_0.md` §4a for
  the full rationale and the other five streams' files). Governed by the
  same Register law and Entry schema as the index file — this file does not
  restate them; see `EDIR_V3_REGISTER_v1_0.md` "Register law" / "Entry
  schema" sections, which apply here verbatim.
parent: 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
stream: S1
id_convention: >
  New S1 findings are `S1-V3-E-nnn`, sequential, claimed by appending (never
  by editing a prior entry's number). S1 had already minted S1-V3-E-012,
  S1-V3-E-013, and S1-V3-E-014 before this split (2026-08-29 renumbering,
  recorded in the pre-split archive's "S5 convergence note" §"The
  ID-collision hazard"); those three entries and their full bodies stay in
  `EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md` (not copied here, to
  avoid a second copy drifting from the archived original) and are not
  reopened by this file. **The next S1 id to claim is `S1-V3-E-015`.**
pre_split_entries:
  - id: S1-V3-E-012
    title: History sidebar has no real cross-session/cross-load persistence
    location: EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md
  - id: S1-V3-E-013
    title: POST/GET /api/conversations had no chart_grants/ownership check (S1-F-001) — FIXED
    location: EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md
  - id: S1-V3-E-014
    title: Mobile referral triaged — history sidebar has no responsive/off-canvas behavior
    location: EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md
changelog:
  - "1.0 (2026-08-29): opened by the A5 per-stream split. No entries yet —
    S1's three pre-split entries stay in the archive; see pre_split_entries
    above and id_convention for the next id to claim (S1-V3-E-015)."
---

# Paripraśna EDIR V3 — S1 register

Append new S1 findings below, oldest first, using the schema and law defined
in `EDIR_V3_REGISTER_v1_0.md`. Do not edit an existing entry's observed text
to soften it — corrections append as a new entry citing the one they
correct. Do not write to any other stream's file or to the shared index.

## Entries

_(none yet — this file was opened empty by the 2026-08-29 split; the next id
to claim is `S1-V3-E-015`)_
