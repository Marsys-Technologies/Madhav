---
artifact: PURNA_OWNER_SURROGATE_LEDGER_CONTINUATION
version: 1.0
status: LIVE
date: 2026-09-29
campaign_id: madhav-purna-anvesana
charter: 00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_OWNER_SURROGATE_CHARTER_v1_0.md
note: >
  Continuation of charter §7. The charter lives in purna_anvesana/, which the shared
  .claude/settings.json (L3 session posture, PR #2718) denies for edits from this session after
  OSR-008 was recorded. Entries from OSR-009 onward are appended here; fold them back into the
  charter §7 when that deny is lifted. No authority or boundary is changed by this file.
---

# Owner-surrogate ledger — continuation

Format: `OSR-NNN | timestamp | question | evidence | decision | acceptance condition | residual`

- `OSR-009 | 2026-09-29 | OSR-001 near-miss domain decision (Addendum §6/§11.2) | source audit of ga_yoga_writer.py / l0_yogas.py / bo_laksana.py / register_d9_judgment.ts; PR #2705 has no near-miss code; two worktree-only tests salvaged (SHA-256 445b044d…, 31d2a8d0…) | Ratified NMB-v1 (packet NEAR_MISS_DOMAIN_PACKET_v1_0.md): six dhana candidates (dhana_yoga_house_lords near_miss-capable via the dusthana gate; five single-leg dhana yogas present/absent/indeterminate only), tolerance none, D1 whole-sign lagna frame per ayanamsha, states near_miss/absent/present/indeterminate; produced by bo_laksana as fact_kind=absence class yoga_formation_band, no migration; consumer serves near_miss only, never not_computed; lakshmi_yoga, chandra_mangala, mahapurusha and unsourced rows excluded; PR #2705 not merged | Red-then-green producer/consumer tests, independent Parashari domain review plus code review, reader-isolation test, merged and deployed before the OSR-004 rebuild | bo_laksana rebuild implied (folded into the single OSR-004 rebuild); domain review may narrow near_miss`
- `OSR-010 | 2026-09-29 | Conductor environment constraint: shared .claude/settings.json denies edits to purna_anvesana/**, platform/migrations 1000–1070 and 1120+, the main-checkout path, and worktrees under it | deny list read from .claude/settings.json (L3 PR #2718); two isolation-worktree subagents failed for that reason; charter §7 write denied after OSR-008 | Not circumvented. Campaign records continue in purna_acceptance/; PR work is done in this checkout on ordinary branches; migrations are limited to numbers the rules allow (1071–1119) and are requested from migration-guard against the runner's ordering; settings are never edited | Records reachable from the campaign brief; no denied path written; no rule weakened | If migration ordering or the records folder cannot work under the deny, record one terminal external dependency ("shared session-posture deny") with automatic resume when the rule is lifted`
- `OSR-011 | 2026-09-29 | OSR-007 implementation review: security-reviewer verdict DO-NOT-SHIP as written (HIGH-1 fresh-DB ordering, MED-1 codex tool exposure, MED-2 deploy-blocking guard, LOW audit/URL); migration-guard SAFE-WITH-CONDITIONS (1119 sits at the end of the L3 reserved window 1070–1119 and needs a recorded release) | reviewer reports; runner orders by numeric prefix and applies any unapplied file; production has the AI Console tables (1124 applied), probe profile active, claude_code installation reachable with a structured-output planner model row; the bridge runs claude_code tool-less | Ship the smaller grant: claude_code only (codex dropped), whole body guarded on the tables existing (NOTICE-only no-op elsewhere), post-condition downgraded to NOTICE for extra grants, admin_audit_log row added, set_default.ts locked to the production origin with redirect refused; number 1119 is a recorded owner-surrogate release of one number from the L3 window (logged on the coordination ledger) | Scratch-Postgres proof of fresh-DB / absent-probe / first / repeat / revoked / extra-grant cases; contract tests green; re-review not required for the narrowed scope, security-reviewer conditions 1–4 addressed | Codex remains available only via an admin grant; capacity (bridge caps 2 per CLI) measured during the golden inquiry`
