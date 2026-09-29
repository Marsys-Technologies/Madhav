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
