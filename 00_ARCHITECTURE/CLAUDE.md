---
artifact: CLAUDE
version: 2.0
status: CURRENT
changelog:
  - v2.0 (2026-10-08): refreshed — v1.0 named PROJECT_ARCHITECTURE_v2_1 and "future" files that never shipped.
---

# 00_ARCHITECTURE — Instructions

Governance and planning documents. Root `CLAUDE.md` §C says which ones a task needs; do not pre-read this folder.

- Canonical paths/versions: `CAPABILITY_MANIFEST.json` (authoritative). Blueprint: `PROJECT_ARCHITECTURE_v2_2.md`.
- Live state: `CURRENT_STATE_v1_0.md` §2 top banners only (the file is ~1 MB).
- `SESSION_LOG.md` is append-only, written at a validated session close.
- Campaign briefs live under `briefs/<campaign>/`; finished artifacts are retained in place (archival policy), so an old file here is not necessarily current — check its `status` frontmatter.
- Any version change carries a changelog entry; architectural changes need the native's explicit approval.
