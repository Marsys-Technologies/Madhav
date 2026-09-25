---
artifact: L0_W_L0_1_PACKET_REPORT
version: 1.0
status: CURRENT
packet: W-L0-1 (Registry truth)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-25
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md
---

# W-L0-1 Packet Report — Registry truth

Per-packet report per the execution kickoff. Convention: change → detector before →
detector after → blocks. All production figures measured live on 2026-09-25 via
read-only queries; this session writes nothing to production.

## Item 1 — bg_prashna_rules NULL target_table made honest

**Change (code, uncommitted in worktree):**
- `platform/scripts/seed/asset_registry_seed.ts:626-650` — seed row now declares the
  five-table comma-set
  `bg_prashna_lagna_methods,bg_prashna_tajik_yogas,bg_prashna_significators,bg_prashna_fructification_rules,bg_prashna_special_techniques`
  and an expanded english_description covering all five partitions.
- Comma-set consumers patched to split on `,`: seed pre-flight, `generate_tci.ts`,
  `assetClearSpec.ts` (EXPLICIT_CLEAR_OPS now lists all five tables), `AtlasView.tsx`,
  `dag_edge_guard.py`.

**Migration (authored, reviewed, HELD — not applied):**
- `platform/migrations/1120_l0_bg_prashna_rules_target_table_honest.sql` — guarded
  DO-block (migration-1075 pattern): refuses unless the row still has NULL
  target_table + the original short description; pre-flights all five tables via
  `to_regclass`; sets target_table + description to seed parity; postflight verifies.
  VERIFY falsifier + manual DOWN included. migration-guard review: PASS (strings
  byte-identical to seed; guard logic sound; numbering verified against the union of
  all origin/* heads — head is 1091, nothing at 1092–1199).
- **HELD** per the kickoff blocker: `_migrations_applied` is unreconciled for
  1080–1095; application belongs to the consolidation session (madhav-65) after
  ledger reconciliation.

**Detector before:** live `asset_registry.bg_prashna_rules.target_table` = NULL;
description truncated to the short form.
**Detector after:** production unchanged by design (migration held) — live row still
NULL today (verified). Code-side detector: `scripts/__tests__/l0_registry_parity.test.ts`
12/12 green, asserting seed/clear/writer agreement on the five-table set.

## Item 2 — Stale writer comments corrected to 171

Measured truth: CLASS_ROWS 24 + SUBSYSTEM 12 + TRADITION 6 + VARGA 30 +
GRAHA_DOMAIN 99 = **171**. Live cross-check: `brahma_class_priors WHERE
prior_version='1.0'` = **171** (queried today). The registry figure of 171 is
correct; 177 (shared table) was NOT substituted.

**Changes:**
- `platform/scripts/seed/asset_registry_seed.ts:580-584` — was "164 signal-salience
  priors"; now 171 with the 24+12+6+30+99 breakdown.
- `platform/src/lib/jyotish/asset_names.ts:39` — subtitle "165-row" → "171-row".
- `platform/python-sidecar/brahmagyan/l0_class_priors.py:5` — docstring "17
  signal_type_class rows" → "24" (17 predated the B-3/B-4/V-5 appends; tuple count
  re-verified in source).

**Detector before:** three stale figures (164, 165, 17) in code comments.
**Detector after:** all three read 171/24; live count agrees (171).

## Item 3 — l0_resource_config_slice_v1.json dispositioned (C-5): REGISTER

**Disposition: REGISTER** — bound to the semantic release, not a 41st asset row,
not deleted.
- `brahmagyan/l0_resource_config_slice_v1.json` `semantic_release_digest` equals the
  release `content_sha256` (665096a7…); both carry id `l0.semantic.2026-09-13.1`.
- Three release-binding tests added to
  `scripts/__tests__/l0_registry_parity.test.ts` (describe
  "l0_resource_config_slice_v1.json — disposition: registered (C-5)"): id+digest
  binding, `delivery_state` === `release_status`, scope honesty (forbidden payload
  fields).

**Detector after:** vitest 12/12 green; pytest `tests/test_l0_resource_config_slice.py`
24/24 green (both re-run today after the final edit).

## Item 4 — Legacy reference_nakshatras dropped — BLOCKED (handover owed)

**Detector (today):** `to_regclass('reference_nakshatras')` present, 27 rows;
canonical `reference_nakshatra` present, 28 rows. Lord agreement 27/27 (verified
earlier this session).
**Block:** three live L1 readers must be repointed to the canonical table before the
drop; that is L1 code, outside this session's remit. See
`L0_W_L0_1_REFERENCE_NAKSHATRAS_L1_REPOINT_HANDOVER_v1_0.md`.
**Standing detector (already in place):** drop condition
`to_regclass('reference_nakshatras') IS NULL`; parity test asserts no bg_* seed row
names the legacy table. The drop migration itself belongs to the consolidation
session AFTER the L1 repoint — do not author it into the unreconciled ledger range.

## Item 5 — bg_vidhi_floors DRAFT re-verified against the writer source

**Detector (today):** `asset_registry.bg_vidhi_floors` catalog_status = DRAFT,
target_table = `vidhi_floor_items`; live `vidhi_intent_floors` = 14 rows, matching
the writer source (12 writer-tagged [MANDATORY] + 2 elective).
**Outcome:** DRAFT stays. No flip.

## Item 6 — "No bg_* table carries a chart/subject column" check actually run

**Detector (today, precise predicate):** zero hits across
`information_schema.columns` for `bg_%` tables on
`chart_id, subject_id, person_id, jatka_id, birth_id, subject_hash, chart_hash,
profile_id, user_id, chart_%, subject_%`.
(Note: `bg_sarvatobhadra_grid.native_confirmed` exists but is a boolean
"human-confirmed" governance flag, not a chart-subject reference — a broad
`%native%` predicate false-positives on it; the precise predicate above is the
honest check.)

## Item 7 — Swiss .se1 resolver re-verified in production

Three independent production evidence points:
1. **2026-09-04 build receipt:** `build_run_assets` for `bg_ephemeris` shows
   disposition='build', output_changed=true, no error. The writer
   (`writers/bg_ephemeris.py:92-103`) hard-fails unless `_resolve_ephe_path()`
   returns a path, `_require_swiss_file_backend` passes (SWIEPH retflag), and all
   three SHA-256 pins match — the gate runs before any short-circuit.
2. **2026-09-01 typed-probe receipt:**
   `nirmana_evidence.nirmana_elevation_campaign_events` (event_type='probe_accepted',
   entity_id='bg_ephemeris_engine') — all three .se1 at `/app/ephe`, digests equal
   to registry pins, `ephemeris_backend: swiss_ephemeris_file`, rahu_lon 49.033.
3. **Today:** live registry `health_probe` for bg_ephemeris_engine matches migration
   1075 exactly (degree anchor 49.033044, tolerance 10 arcsec, allowed backend =
   swiss_ephemeris_file only). Resolver `_resolve_ephe_path()`
   (`brahmagyan/l0_ephemeris.py:230-248`) unchanged: SWE_EPHE_PATH → /app/ephe →
   /tmp/se1 → None.

**Governance note (cited, not re-raised):** the deeper chronicle §11.18 finding
(process-global unowned ephe path; `panchang_engine/__init__.py` `set_ephe_path(None)`
×4; `l0_ephemeris.py` ×2) is already governed by
`MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_AMENDMENT_v1_0.md` (DP-SD-010, approved
2026-09-13), whose may_touch list names exactly those files and which is owned by
another execution stream. Not fixed here (L1/shared code, other owner).

## Open question for the strategy session

`kala_brief_tracker.py` ASSETS-list extension (whether the tracker should gain the
L0 asset set) — undecided; needs strategy coordination. Not executed.

## Packet status

W-L0-1 items 1–3, 5–7 closed on the code/detector side. Item 1's production effect
and item 4's drop are held for the consolidation session (ledger reconciliation;
L1 repoint respectively). No gate was weakened; no production write was made from
this session.
