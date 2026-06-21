---
artifact: CLAUDECODE_BRIEF_G52_KILL_AND_BRIEF_PURGE_v1_0.md
canonical_id: G52_KILL_AND_BRIEF_PURGE_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
native_decisions_2026_06_16:
  - "G52 / signal_type_registry is ELIMINATED EVERYWHERE — native removed it from the Bodha conversation too. Not a label-catalog, not a prereq: GONE. Drop the table, scrub every spec/doc/code reference."
  - "Brief purge = AGGRESSIVE: archive ALL non-CURRENT/non-ACTIVE briefs (incl. AUTHORED/READY/PENDING/DRAFT/COMPLETE + the 85 citation-blocked). Keep ONLY live CURRENT/ACTIVE briefs + the live Bodha/cockpit set."
  - "Citation handling = ARCHIVE ANYWAY + FIX THE REFERRERS — update or remove every reference so no dangling links remain."
data_plane: ALWAYS prod via Cloud SQL proxy (port 5433) — for the G52 table drop only
safety: >
  A live L2 Bodha conversation shares this repo. This brief MUST NOT touch any LIVE/CURRENT Bodha
  artifact's CONTENT (only scrub G52 mentions). Reverse-citation discipline still applies — but the
  native's directive is to FIX referrers, not leave briefs in place. Branch + PR; never direct-to-main.
verified_current_state: >
  main HEAD bddb1931. Active BRIEFS/ = 308 files; 63 already in 99_ARCHIVE/BRIEFS_RETIRED/. G52 still
  CREATEd by migration 226, described in A10_MSR_SPEC, mentioned across ~14 architecture docs; the
  code references in bo_laksana.py are CORRECT "G52 retired" comments (those just need the comment
  kept accurate, not the concept revived).
---

# G52 Total Kill + Aggressive Brief Purge — Brief v1.0

## §0 — Two independent workstreams; run as two PRs
**WS-A: G52 elimination** (code + DB + specs). **WS-B: aggressive brief archive** (docs only).
Independent — separate branches, separate PRs. Both gated on the live Bodha conversation being at a
checkpoint (shared repo). Reverse-citation grep before every delete. Neither touches `bo_*`/`bodha_*`
writer LOGIC, prod chart data, or any CURRENT/ACTIVE brief's content.

---

# WS-A — Eliminate G52 / signal_type_registry EVERYWHERE
Native directive: G52 does not exist anywhere. It is not a label-catalog, not a prerequisite. Gone.
The architecture (enumeration in ga_structural, projection in Bodha, labels from brahma_yoga_catalog)
has zero need for it. The native has already removed it from the Bodha conversation.

### A1 — Drop the table (DB + migration)
- Migration 226 (`226_bodha_spec_tables.sql`) still `CREATE TABLE signal_type_registry` (~L17) + 2
  indexes (~L33-34). The table is EMPTY (nothing writes/queries it — verified: bo_laksana.py only
  references it in a "G52 retired" comment).
- Author a NEW surgical migration (FRESH number — check the supabase/migrations sequence; 237+ likely
  free, verify against both migration dirs per [[reference-two-migration-directories]]):
  `NNN_drop_signal_type_registry.sql` → `DROP TABLE IF EXISTS signal_type_registry CASCADE;`
- Do NOT edit migration 226 in place (it's applied history) — the new migration supersedes it. But DO
  add a one-line comment to 226 noting "signal_type_registry dropped by migration NNN — G52 eliminated."
- Apply to prod (proxy up). Confirm `to_regclass('signal_type_registry')` returns NULL afterward.
- **Reverse-citation gate first:** grep all live code (platform/src, python-sidecar, scripts) for any
  SELECT/INSERT/JOIN on signal_type_registry. Expected: ZERO (only the bo_laksana comment). If any
  live query exists, STOP and report — do not drop a table something reads.

### A2 — Scrub the spec (A10) + the asset_registry seed
- `00_ARCHITECTURE/A10_MSR_SPEC_v1_0.md` — remove every clause treating G52/signal_type_registry as a
  dependency, prerequisite, or "P0.2 seed 500-700 predicates" task (the agent found refs at ~L24, 30,
  44, 79, 262, 396, 411). Replace with the projection model: bo_laksana projects ga_structural
  enumeration; signal_type_id is derived (fact_category-based), NOT looked up in a registry. Bump A10
  version + changelog noting "G52 fully removed per native 2026-06-16."
- `platform/scripts/seed/asset_registry_seed.ts` — the `bg_signal_type_registry (G52) RETIRED` comment
  (~L695): confirm there is NO active asset ROW for it (just the comment). If a dormant row exists,
  remove it. Keep a one-line "G52 eliminated 2026-06-16" note or remove entirely — native's call is
  "gone," so prefer removal of the row; the comment can stay as a tombstone breadcrumb.

### A3 — Scrub the architecture docs (keep "retired" tombstones accurate, remove "prereq" language)
For each doc that still frames G52 as needed, change it to "G52 eliminated" (NOT "G52 is a label
catalog"): `L2_BODHA_BUILD_CAMPAIGN_v1_0.md §3.4` (the "new global prerequisite" section — rewrite to
"G52 ELIMINATED — no registry, projection model only"), `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md §8.3`,
`BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md §5.6` (currently flags it as an open decision — change to
"RESOLVED: G52 eliminated 2026-06-16"), `L2_BODHA_PHASE0_GAP_REPORT`, `L2_BODHA_PHASE0_ALIGNMENT_ROADMAP`,
`L2_BODHA_ASSET_TABLE_BRIEF_MAP`, `MARSYS_CONSOLIDATED_RUNWAY`. The historical-record docs
(`L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION`, `L0_L1_SENSEMAKING_AUDIT`, `MARSYS_DATA_INTEGRITY_DEEP_AUDIT`,
`GA_STRUCTURAL_COMPLETENESS_FINDING`, `LEGACY_GOVERNANCE_TEARDOWN_AUDIT`) may KEEP their G52 mentions
as accurate history (they describe the decision to drop it) — do not rewrite history, just ensure none
says "G52 is still needed."
- The CONDUCTOR/build_orchestrator/streams/KICKOFF_STREAM_B.md ref is legacy — archive with WS-B.

### A4 — bo_laksana.py + live Bodha briefs (comments only — DO NOT touch logic)
- `bo_laksana.py:11` comment "NO predicate registry (G52 retired)" is CORRECT — leave it (it documents
  the right model). Same for the live Bodha briefs (BODHA_B1, BODHA_B1_FULL_PROJECTION, etc.) — they
  already say G52 is retired; confirm none lists it as a build step. **Do NOT change any Bodha writer
  logic** — the live Bodha conversation owns that code.

### A5 — Acceptance [verify-against: prod + grep]
- [ ] `signal_type_registry` table dropped from prod (to_regclass → NULL); new migration committed.
- [ ] `grep -rn signal_type_registry platform/ 00_ARCHITECTURE/ --include=*.sql --include=*.ts --include=*.py` (excluding node_modules + 99_ARCHIVE) returns ONLY: the new drop-migration, the 226 supersede-comment, and accurate "retired/eliminated" tombstone comments. ZERO "create", "prereq", "depends_on", "seed 500-700" framing.
- [ ] A10 spec + the Bodha campaign/handoff docs say "G52 ELIMINATED", not "open decision" or "prerequisite".
- [ ] No Bodha writer LOGIC changed; tests green.

---

# WS-B — Aggressive brief archive (308 → keep only CURRENT/ACTIVE)
Native directive: archive ALL non-CURRENT/ACTIVE briefs. Fix every referrer so no dangling links.

### B1 — Build the keep-list FIRST (the safety anchor)
KEEP in `00_ARCHITECTURE/BRIEFS/` ONLY briefs whose frontmatter `status` is exactly **CURRENT** or
**ACTIVE** (incl. ACTIVE-AUTONOMOUS / ACTIVE — executable), PLUS the live workstream set regardless of
status label:
- The live Bodha briefs: `CLAUDECODE_BRIEF_BODHA_*` (B1, B1_FULL_PROJECTION, P0E_SEED_CORRECTION,
  L1E_GA_STRUCTURAL_ENRICHMENT) — KEEP (the Bodha conversation is using these).
- The current cockpit/Nirmāṇa briefs that haven't merged yet, the WAVE3_4 brief, GA8 enumeration briefs
  still cited by current work.
- This brief itself + the two open-PR briefs + LEGACY_GOVERNANCE_TEARDOWN_AUDIT.
- When in doubt about a Bodha-related brief, KEEP it and flag for native — do NOT archive anything the
  live Bodha conversation might be reading.

Everything else (COMPLETE, CLOSED, BUILD_COMPLETE, CODE_COMPLETE, SUPERSEDED, AUTHORED, READY*,
PENDING, DRAFT, NOT_STARTED, NO_STATUS, prompt, the 85 citation-blocked, all dead-model) → ARCHIVE.
Estimate ~250 archived, ~50 kept.

### B2 — Archive with referrer-fixing (the native's chosen path)
For each brief to archive:
1. `git mv 00_ARCHITECTURE/BRIEFS/<brief>.md 99_ARCHIVE/BRIEFS_RETIRED/<brief>.md` (preserve history).
2. **Find every referrer:** `grep -rln "<brief-filename>" . --include=*.md --include=*.ts --include=*.py --include=*.yml | grep -v 99_ARCHIVE | grep -v node_modules`.
3. For each referrer: if the referrer is ITSELF being archived in this pass, no action (both move). If
   the referrer is a KEPT/live file (CLAUDE.md, a current doc, a live brief), UPDATE the reference —
   repoint the path to `99_ARCHIVE/BRIEFS_RETIRED/<brief>.md`, OR if the reference is a dead mention
   (the referring section is itself obsolete), remove the dead line. Never leave a path that resolves
   to nothing.
4. Special care: CLAUDE.md §C/§D and CAPABILITY_MANIFEST.json — if any archived brief is referenced
   there, repoint or remove the entry + note it in the changelog. Do NOT break the §C reading list.

### B3 — Extend the index
- Append every newly-archived brief to `99_ARCHIVE/BRIEFS_RETIRED/BRIEFS_INDEX.md` (the index from the
  prior teardown) with: filename, prior status, one-line what-it-was, and (if known) its replacement.
- Group by family (PHASE_4C, MCP/MCPT, TOOLING_REMEDIATION, WS-waves, GATE, M2, BHISMA, L0FR, PARITY,
  etc.) so the archive is navigable, not a 250-file dump.

### B4 — Acceptance
- [ ] `00_ARCHITECTURE/BRIEFS/` contains ONLY CURRENT/ACTIVE + the named live Bodha/cockpit set (~50 files); confirm count.
- [ ] Every live Bodha brief is STILL present (spot-check BODHA_B1_FULL_PROJECTION exists).
- [ ] ZERO dangling references: `grep -rln` for any archived brief filename across live (non-99_ARCHIVE) files returns nothing, OR only repointed 99_ARCHIVE/ paths.
- [ ] CLAUDE.md §C reading list still resolves (no archived brief left as a live §C pointer).
- [ ] BRIEFS_INDEX.md lists all ~250+ archived briefs, grouped by family.
- [ ] `git mv` used throughout (history preserved); tests + tsc still green (briefs are docs — should be no code impact; confirm no .ts/.py imported a brief path).

---

## §FINAL — run order + rails
1. WS-A (G52) on `chore/g52-eliminate` → PR. 2. WS-B (briefs) on `chore/brief-purge-aggressive` → PR.
Both: branch → reverse-citation grep → change → tests/tsc green → PR (native merges). 
DO NOT: touch live Bodha writer logic, archive any CURRENT/ACTIVE or live-Bodha brief, leave a dangling
reference, drop signal_type_registry without the zero-live-query confirmation, force-push, or touch main directly.
The native has confirmed G52 is removed from the Bodha conversation, so WS-A will not collide with it —
but still run when Bodha is at a checkpoint to avoid main churn.

---
*End of G52_KILL_AND_BRIEF_PURGE v1.0. WS-A: eliminate G52/signal_type_registry everywhere — drop the
(empty) table via a fresh migration, scrub A10 + Bodha campaign/handoff docs from "prereq" to
"eliminated", keep accurate "retired" tombstone comments, touch NO Bodha logic. WS-B: aggressively
archive ALL ~250 non-CURRENT/ACTIVE briefs to 99_ARCHIVE/BRIEFS_RETIRED/ + FIX every referrer (no
dangling links) + extend BRIEFS_INDEX, keeping only the ~50 live CURRENT/ACTIVE + Bodha/cockpit briefs.
Two PRs, reverse-citation-gated, gated on a Bodha checkpoint.*
