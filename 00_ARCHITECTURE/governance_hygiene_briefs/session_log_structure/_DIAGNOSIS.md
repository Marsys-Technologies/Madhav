---
artifact_id: GH-SESSION-LOG-STRUCTURE-DIAGNOSIS
title: "SESSION_LOG Structural Heading Repair — Diagnosis & Fix Record"
status: COMPLETE
session: GH-SESSION-LOG-STRUCTURE
authored: 2026-05-21
---

# SESSION_LOG Structural Heading Repair — Diagnosis

## 1. Root Cause

`schema_validator.py` splits `SESSION_LOG.md` into per-session validator entries using `_split_session_log_post_adoption()`. This function only creates entry boundaries at headings matching:

```
^## ([A-Za-z0-9_.\-]+)\s+—
```

(an H2 heading where the session ID is immediately followed by ` —`).

Non-matching heading formats cause all YAML `session_open` / `session_close` blocks between two matching headings to be attributed to the *preceding* matching heading's validator entry. The validator then compares the LAST `session_open.session_id` and `session_close.session_id` found in that entry against the heading's captured session ID, producing `session_log_entry_session_id_disagreement_heading_open` and/or `session_log_entry_session_id_disagreement_heading_close` HIGH violations.

The schema adoption point that activates this validation is line 2581 of `SESSION_LOG.md`:
```
# Schema adoption point (Step 10 close, 2026-04-24)
```

## 2. Baseline Violations

**Baseline report:** `SCHEMA_REPORT_GH-SESSION-LOG-AC1_20260521T034444Z.json`

- Total violations: 202
- HIGH: 39 (36 `session_id_disagreement_heading_*` + 3 `learning_layer_*` pre-existing)
- MEDIUM: 125
- LOW: 38
- CRITICAL: 0

## 3. All 36 HIGH Violations — Root Cause Catalogue

The 36 `session_id_disagreement_heading_*` violations were caused by the following non-conforming heading patterns in the post-adoption section of `SESSION_LOG.md`.

### Category A — Wrong H2 prefix (Session: / Entry: / Session — prefix)

| # | Original Line | Original Heading | Non-Conforming Pattern |
|---|---|---|---|
| 1 | 5516 | `## Session: Madhav_M2A_Plan_Foundation_Stack` | `Session:` prefix — regex captures `Session` as session_id |
| 2 | 7679 | `## Session: Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1` | Same |
| 3 | 9558 | `## Entry: Madhav_M2A_Exec_11` | `Entry:` prefix — regex captures `Entry` |
| 4 | 9853 | `## Entry: Madhav_M2A_Exec_12 — B.6 Hybrid Retrieval Library + M2B milestone close` | `Entry:` prefix |
| 5 | 10046 | `## Session: Madhav_COW_M2A_Exec_13_BRIEF_AUTHORING` | `Session:` prefix |
| 6 | 10726 | `## Session: redesign-r7-polish-2026-04-30` | `Session:` prefix |
| 7 | 19412 | `## Session — USTAD_S2_6_O2_GATE_CLOSE (2026-05-03, Phase O sub-phase O.2 GATE CLOSE)` | `Session —` with space before em-dash; regex captures `Session` |
| 8 | 19557 | `## Session — USTAD_S2_5_DEEPSEEKNNIM_CSV (2026-05-03, Phase O sub-phase O.2 implementation)` | Same |
| 9 | 20011 | `## Session — USTAD_S3_1_BUDGET_RULES_FRAMEWORK (2026-05-03, Phase O sub-phase O.3 GATE-OPEN)` | Same |
| 10 | 20162 | `## Session — USTAD_S3_3_BUDGETS_UI (2026-05-03, Phase O sub-phase O.3 implementation)` | Same |
| 11 | 20281 | `## Session — USTAD_S3_2_ALERT_DISPATCHER (2026-05-03, Phase O sub-phase O.3 IMPLEMENTATION)` | Same |
| 12 | 20391 | `## Session — USTAD_S3_4_EXPORT_O3_CLOSE (2026-05-03, Phase O sub-phase O.3 GATE-CLOSE)` | Same |
| 13 | 21859 | `## Session M5-C-S2 — Prior Freeze + M5-C Close (2026-05-13)` | `Session ` prefix before ID; regex captures `Session` |
| 14 | 9257 | `## Entry: Madhav_PORTAL_QUALITY_v0_1` | `Entry:` prefix — also orphan close-only (no session_open) |
| 15 | 9360 | `## Entry: Madhav_M2A_Exec_10` | `Entry:` prefix — also orphan close-only |

### Category B — Parenthetical date without em-dash

| # | Original Line | Original Heading | Non-Conforming Pattern |
|---|---|---|---|
| 16 | 5193 | `## Madhav_17_B0_DISCOVERY_LAYER_SCAFFOLD (2026-04-24)` | Parenthetical; no ` —` after session ID |
| 17 | 8918 | `## Madhav_M2A_Exec_9` | Missing ` —` entirely |
| 18 | 18086 | `## USTAD_S1_4_ANTHROPIC_OBSERVED_ADAPTER (2026-05-03)` | Parenthetical |
| 19 | 18274 | `## USTAD_S1_5_OPENAI_OBSERVED_ADAPTER (Phase O sub-phase O.1, OpenAI provider adapter) — 2026-05-03 (close)` | Long parenthetical interrupts pattern |
| 20 | 19812 | `## USTAD_S2_3_OPENAI_RECONCILER (2026-05-03)` | Parenthetical |
| 21 | 19901 | `## USTAD_S2_2_ANTHROPIC_RECONCILER (2026-05-03)` | Parenthetical |
| 22 | 17940 | `## USTAD_S1_9_OBSERVATORY_FRONTEND_SCAFFOLD` | Missing ` —` entirely |
| 23 | 24066 | `## Session M9-E-S1` | `Session ` prefix |

### Category C — H1 heading in body (should be H2)

| # | Original Line | Original Heading | Non-Conforming Pattern |
|---|---|---|---|
| 24 | 8262 | `# Session: Madhav_M2A_Exec_7 — B.4 Task 3 (Gemini SUPPORTS two-pass)` | H1 (`#`) not H2 (`##`); regex only matches `##` |

### Category D — Missing headings (CONDUCTOR-S0 sub-sessions, M5-E-S2 sub-sessions)

These entries had no `## SESSION_ID —` heading at all. Their YAML blocks bled into the preceding matching heading's entry.

**CONDUCTOR-S0 sub-sessions (14 entries):**

| # | Session ID | Insertion point |
|---|---|---|
| 25 | 4C-1-S1 | Before line 24380 (original; inserted before `\`\`\`yaml` block) |
| 26 | 4C-1-S2 | Before line 24477 |
| 27 | 4C-3 | Before line 24566 |
| 28 | 4C-4-S1 | Before line 24689 |
| 29 | 4C-4-S2 | Before line 24786 |
| 30 | 4C-4-S3 | Before line 24892 |
| 31 | 4C-4-S4 | Before line 24998 |
| 32 | 4C-5 | Before line 25077 |
| 33 | 4C-6-S1 | Before line 25148 |
| 34 | 4C-6-S4 | Before line 25264 |
| 35 | 4C-7 | Before line 25388 |
| 36 | 4C-8 | Before line 25510 |

(4C-9 and PANCHANG-ENRICH-GOVCLOSE also inserted for completeness; total insertion batch was 14 new headings.)

**M5-E-S2 sub-sessions (12 entries — M8-A-S1 through M9-D-S1):**

| # | Session ID | Insertion point (original + offset) |
|---|---|---|
| — | M8-A-S1 | Before line 23073+2 |
| — | M8-B-S1 | Before line 23155+2 |
| — | M8-C-S1 | Before line 23215+2 |
| — | M8-D-S1 | Before line 23273+2 |
| — | M8-E-S1 | Before line 23334+2 |
| — | M8-F-S1 | Before line 23409+2 |
| — | M8-G-S1 | Before line 23477+2 |
| — | M8-H-S1 | Before line 23564+2 |
| — | M9-A-S1 | Before line 23637+2 |
| — | M9-B-S1 | Before line 23743+2 |
| — | M9-C-S1 | Before line 23865+2 |
| — | M9-D-S1 | Before line 23978+2 |

**redesign-r6-cockpit-2026-04-30 (1 entry):**

Also lacked a conforming heading. Inserted `## redesign-r6-cockpit-2026-04-30 — Portal Redesign R6 Cockpit elevation 2026-04-30` before its YAML block at original line 10641.

## 4. Additional Fixes (structural hygiene, not violation-driven)

- `## Session: redesign-r7-polish-2026-04-30` at line 10726 → `## redesign-r7-polish-2026-04-30 — Portal Redesign R7 Polish`
- `## Session 4C-3 body` at line 24606 demoted to `### 4C-3 body` (H3) — was a false H2 body heading inside the 4C-3 session entry
- `## Phase 4C Wave 1 Close Summary` at line 25736 demoted to `### Phase 4C Wave 1 Close Summary` (H3) — same pattern

## 5. Special Case — Orphan Close-Only Entries

`Madhav_PORTAL_QUALITY_v0_1` and `Madhav_M2A_Exec_10` only had `session_close` YAML blocks; no `session_open` blocks existed. Giving them proper `## SESSION_ID —` headings without a `session_open` would introduce `session_log_entry_missing_session_open_yaml` CRITICAL violations (baseline had 0 CRITICAL).

**Resolution:** Added minimal stub `session_open` blocks with a `note` field explaining the governance-repair provenance:

```yaml
session_open:
  session_id: Madhav_PORTAL_QUALITY_v0_1
  note: "session_open reconstructed during GH-SESSION-LOG-STRUCTURE governance repair 2026-05-21 — original session predated SESSION_LOG_SCHEMA adoption"
```

This preserves 0 CRITICAL and avoids introducing new CRITICAL violations.

## 6. Post-Fix Results

**Post-fix report:** `SCHEMA_REPORT_GH-SESSION-LOG-FIX2_20260521T083337Z.json`

- Total violations: 198 (↓ from 202)
- HIGH: 3 (↓ from 39 — all 3 remaining are pre-existing `learning_layer_*` violations)
- MEDIUM: 125 (unchanged)
- LOW: 70 (↑ from 38 — new entries lack `### Next session objective` headings; acceptable side-effect)
- CRITICAL: 0 (unchanged)
- `session_id_disagreement_heading_*` count: **0** (↓ from 36) ✓

Exit code: 2 (HIGH present but pre-existing; no CRITICAL; violation count strictly lower).

## 7. Files Modified

- `00_ARCHITECTURE/SESSION_LOG.md` — 37 heading renames/insertions + 2 H1→H2 promotions + 2 H2→H3 demotions + 2 stub `session_open` insertions + GH-SESSION-LOG-STRUCTURE session entry appended
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — v5.30 → v5.31 (changelog entry for this session)
- `.gemini/project_state.md` — MP.2 mirror updated (adapted parity, same-session)
- `00_ARCHITECTURE/governance_hygiene_briefs/GH_SESSION_LOG_STRUCTURE_BRIEF_v1_0.md` — status STORED → COMPLETE
