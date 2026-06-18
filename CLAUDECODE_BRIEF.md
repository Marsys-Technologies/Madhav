---
artifact: CLAUDECODE_BRIEF_FOUNDATION_SESSION_1
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-06-18
session_type: claude_code_autonomous (documented-defaults; native reviews at end)
phase: pre-L2 foundation close-out + PROD verification
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
may_touch:
  - platform/migrations/**
  - platform/scripts/seed/asset_registry_seed.ts
  - platform/python-sidecar/brahmagyan/**            # l0_yogas.py, l0_doshas.py, l0 catalog content, bg_medical
  - platform/python-sidecar/**bg_rules**             # the extractor + its rebuild
  - platform/python-sidecar/**bg_ephemeris** , **bg_dignity_reference** , **bg_transit_rules** , **bg_medical_mappings**   # autonomy-writer verification
  - 00_ARCHITECTURE/**                               # verification reports + CURRENT_STATE + registers
must_not_touch:
  - platform/python-sidecar/ga_writers/ga_structural_writer.py          # SESSION 2 / ga_structural track ONLY
  - platform/python-sidecar/pipeline/orchestrator/writers/ga_structural.py
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py
  - any L2 bo_* asset
acceptance_criteria:
  - migrations 315–317 (+ any new) APPLIED to prod, ledger-reconciled
  - all §6 endpoint checks pass via /api/cockpit/stats?chart_id=482012f1 (NOT db, NOT a report claim)
  - bg_rules sampled THEN mined; floor = achieved; deterministic extractor confirmed
  - 4 autonomy writers confirmed REGENERABLE (behavioral, not "file exists")
  - bg_medical grid/combos verified present-or-built
  - FOUNDATION_SESSION_1_CLOSE.md written with endpoint JSON evidence
---

# CLAUDE CODE — Foundation Completion Session 1 (autonomous; documented defaults; review-at-end)

Read CLAUDE.md §C (mandatory session-open reads) FIRST. Then this brief governs the session. Run the items in
order, FULLY AUTONOMOUS using the DOCUMENTED DEFAULTS at the bottom; native reviews ONCE at the end. Source:
`00_ARCHITECTURE/FOUNDATION_COMPLETION_HANDOFF_v1_0.md` + `FOUNDATION_COMPLETION_ARC_v1_0.md`. **ga_structural's
re-architecture is SESSION 2 — do NOT touch it (see must_not_touch).**

**STANDING RAILS (non-negotiable):** computed-and-cited HARD GATE (uncited → floor NULL+reason, NEVER fabricate);
canonical-or-floor; deterministic-first (no generative LLM for content — HALT if the bg_rules extractor is
generative); L1-is-authority; FROZEN orchestrator contract (HALT if a change seems needed); surgical migrations
only, numbered above main's current max (parallel thread wrote 315/316/317 — confirm next-free + continue),
ledger-reconciled with correct SHA; seed-consistency; **VERIFY VIA THE ENDPOINT `/api/cockpit/stats?chart_id=
482012f1` — underscore param, NOT chartId — never DB-only, never a report's claim**; floors = ACHIEVED count
(every number in the handoff/audit is a TO-VERIFY pointer, NEVER a build target); only 482012f1; FORENSIC 7/7;
**branch-complete ≠ prod-true — VERIFY post-apply.**

---

## ITEM 1 — Apply + prod-verify the parallel close-out thread (migrations 315–317)

Parallel thread WROTE 315 (ga_prashna count_sql fix), 316 (bg_nakshatra_medical ADD COLUMN dosha), 317
(ga_pyjhora error reset) but did NOT apply them. Apply all three to PROD surgically, ledger-reconcile. Verify via
ENDPOINT: ga_prashna lit/0-valid (not red); ga_pyjhora GREEN after 317 + a probe (if still error → service is
genuinely down, root-cause it, don't just re-clear); bg_nakshatra_medical `dosha` column exists+populated. Confirm
CI green with the assert changes (YOGAS_CORE=144, doshas assert=79). Merge.

## ITEM 2 — Autonomy gaps: CONFIRM the 4 writers actually regenerate (behavioral, not "file added")

Parallel thread added writers (bg_transit_engine → folded into bg_transit_rules; bg_nakshatra_medical → folded
into bg_medical_mappings; bg_ephemeris → new; bg_dignity_reference → new). VERIFY each by triggering a Rebuild of
that asset_id via the orchestrator and confirming it REGENERATES (not DEFERS). The test is "does Rebuild-All now
cover all 39 assets," not "a file exists." Report any that still DEFER (+ fix).

## ITEM 3 — bg_rules: do the SKIPPED yield-sampling FIRST, then mine

Parallel thread skipped sampling, jumped to "run rebuild." bg_rules ≈ 90% of the foundation delta, currently an
unpinned ±30k guess. ORDER:
1. SAMPLE a few hundred un-mined `classical_text_chunks` (~7,533 unprocessed), run the EXISTING extractor, measure
   actual rules-per-chunk yield → report a tightened projection.
2. CONFIRM the extractor is DETERMINISTIC (rule-extraction over cited text), NOT generative. If generative → HALT
   + flag (violates deterministic-first; do not mine).
3. MINE all chunks (ON CONFLICT DO NOTHING), each rule cited to source chunk_id. bg_rules floor = ACHIEVED;
   seed-patch; endpoint-verify the new count.

## ITEM 4 — Catalog completeness (DEFAULT accept-as-built; EXCEPTION bg_medical grid/combos)

A3: bg_yogas 81→144, bg_doshas 50→79, bg_medical 9→21 — all BELOW the audit's soft estimates (~250/~80-120/~150-200).
- DEFAULT: accept bg_yogas + bg_doshas as-built (hard gate working; don't pad to a target). Spot-check 3-4 entries
  each for genuine formation_rule_jsonb + citation (not stubs); if clean, accept. Report.
- EXCEPTION — bg_medical_mappings (21 vs ~150-200, a large gap): the audit described a 27×3 nakshatra-dosha GRID +
  planetary-combination tier. CHECK whether bg_medical_mappings now CONTAINS the grid + combos or only the
  single-planet tier + a few additions. If the grid/combos are genuinely MISSING (deferred, not just "fewer than
  estimated"), BUILD them (deterministic + cited: BPHS Ch.18 / Ayurvedic-Jyotish). If present and 21 is the
  correct citable count, accept. Report which. (ga_medical reads bg_medical_mappings → rebuild ga_medical after if
  bg_medical changed — ga_medical is in scope, ga_structural is NOT.)

## ITEM 5 — bg_remedies (DEFAULT accept; log bo_upaya dependency)

+66 (→283) vs "thousands in tradition." DEFAULT: accept as-built (first pass; bo_upaya is downstream). LOG in
OPEN_ITEMS that bo_upaya remedy depth depends on a future bg_remedies expansion. No build this session.

## ITEM 6 — FINAL VERIFICATION (the seal) — ENDPOINT ONLY, paste the JSON

Hit `/api/cockpit/stats?chart_id=482012f1` and assert (paste JSON as evidence):
- Every L0+L1 asset lit / non-null / no-error / not-stale.
- ga_prashna lit-0-valid; ga_pyjhora GREEN.
- bg_rules at new mined floor; bg_yogas=144; bg_doshas=79; bg_medical at confirmed floor.
- 4 autonomy assets regenerable (Item 2).
- ZERO regressions vs the pre-session endpoint snapshot.
Then: update CURRENT_STATE; mark Session-1 items closed in OPEN_ITEMS_REGISTER + FOUNDATION_COMPLETION_HANDOFF;
write `00_ARCHITECTURE/FOUNDATION_SESSION_1_CLOSE.md` (endpoint JSON + bg_rules sampling result + bg_medical
verdict + autonomy-confirm result).

**Set this brief frontmatter `status: COMPLETE` when done.** Session 2 (ga_structural Option-C rebuild) opens
against the settled, prod-verified foundation — do NOT do Session-2 work here.

---

## DOCUMENTED DEFAULTS (applied autonomously, no halt)
- Catalogs: accept-as-built EXCEPT bg_medical grid/combos (Item 4 — build if genuinely missing).
- bg_rules extractor: proceed only if DETERMINISTIC; HALT if generative.
- Autonomy writers: parallel thread's fold-ins stand; VERIFY they regenerate, fix if they DEFER.
- Migrations continue from next free number above 317.
- OUT OF SCOPE → Session 2: ga_structural, bo_laksana, the yoga_label fork, the aspect_tajik fork, nakshatra_dispositor
  alignment, per-varga edge-weight ingest. Touch NONE of these.
- bg_remedies: accept + log; no build.
