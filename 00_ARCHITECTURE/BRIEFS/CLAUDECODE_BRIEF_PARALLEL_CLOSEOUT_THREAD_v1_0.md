# Parallel Close-Out Thread — everything EXCEPT ga_structural's own waves (paste into Antigravity)

**Context:** Runs IN PARALLEL with the separate `GA_STRUCTURAL_RELATIONAL_HUB` track (which the native handles).
This thread closes the Foundation Completion arc's Wave 1 (L0 catalogs) + the hygiene track. It does NOT touch
ga_structural's defect-fixes (arc Wave 2), the ga_yoga fork (Wave 0), or the bo_laksana projection wiring (Wave
3) — those wait for the native's ga_structural decision. Source plan: `FOUNDATION_COMPLETION_ARC_v1_0.md`.

**HARD BOUNDARY (must not cross):** do NOT modify, rebuild, or re-scope `ga_structural` or `bo_laksana` in this
thread. You MAY build the L0 catalogs that ga_structural later consumes (bg_yogas/bg_doshas) — but do NOT
trigger a ga_structural rebuild against them; that rebuild belongs to the ga_structural track. (Native accepts a
later second ga_structural rebuild as the cost of parallelizing.)

**Standards (every item):** computed-and-cited HARD GATE (uncited → floor NULL+reason, NEVER fabricate);
canonical-or-floor; deterministic-first (Python/extraction, never generative LLM for content); L0 ON-CONFLICT /
L1 delete-then-insert idempotency; FROZEN orchestrator contract (writer fixes only — HALT if a contract change
seems needed); surgical migrations ≥ next-free (confirm main's max + #300 pending); ledger-reconcile;
seed-consistency; **endpoint-verify via `?chart_id=` not `?chartId=`** (the standing rail — never DB-only);
floors = ACHIEVED count (never fabricate to a target; the audit's quoted counts are TO-VERIFY pointers, not
targets); only `482012f1`; FORENSIC 7/7 holds.

---

## PART A — L0 CATALOG COMPLETION (Wave 1; run items in parallel — independent of each other)

**A1 — bg_rules bulk-mine (the big completeness win).** Current ≈ 2,912 rules from 660 of 8,193
`classical_text_chunks` (8.1%). The extraction pipeline that produced them ALREADY EXISTS — this is a BULK RE-RUN
over the remaining ~7,533 chunks, NOT new code. Confirm the extractor is DETERMINISTIC (rule-extraction over
cited text), NOT a generative LLM (deterministic-first rule). Run it; every rule cited to its source chunk_id.
- ⭐ RECOMMENDED FIRST STEP (pin the number): the per-chart delta is dominated by this asset and is currently a
  wide guess. Before the full run, SAMPLE a few hundred of the un-mined chunks, measure actual rules-per-chunk
  yield (it may differ from the 660 already done if chunk types differ), and report a tightened projection. Then
  run the full mine.
- GUARD: lower-confidence extractions on different chunk types → floor-and-flag, never drop or fabricate.
- Verify: bg_rules count via endpoint; set target_floor = achieved; seed-patch.

**A2 — bg_medical_mappings expansion (9 → classical depth).** Add the missing tiers: planetary-combination
medical rows + the 27×3 nakshatra-dosha grid + dignity-modified health indicators. Each cited (BPHS Ch.18 /
Ashtanga Hridayam / Ayurvedic-Jyotish texts). The target "~150-200" is an ESTIMATE — build what is genuinely
computable+citable, set floor = achieved (don't pad to 200). DOWNSTREAM NOTE: ga_medical reads bg_medical_mappings;
its auto-improvement on next build is fine to trigger (ga_medical is NOT ga_structural — not boundary-blocked).

**A3 — bg_yogas (175 → ~250) + bg_doshas (50 → fuller).** Add missing classically-cited definitions (Jaimini
yogas, Nabhasa variants, KP yogas; Kuja/Grahan/Pitra/Naga dosha variants), each with a machine-evaluable
`formation_rule_jsonb` + citation. GATE: add a def ONLY if its formation rule is deterministically evaluable AND
citable — un-evaluable/uncited → skip, never fabricate. **DO NOT rebuild ga_structural against the expanded
catalog** (that's the ga_structural track). Just complete the L0 catalogs; set floors = achieved.

**A4 — bg_remedies expansion (266 → fuller).** Add mantra prescriptions, yantra specs, dana schedules — cited.
Scope is loosely bounded ("thousands in tradition"); build the deterministically-citable set, floor = achieved.
Lower priority within Part A (only bo_upaya consumes it, later) — fine to land last.

---

## PART B — HYGIENE TRACK (autonomy gaps + cosmetic fixes; forks resolved to defaults below)

The 4 autonomy-writer gaps + 3 small fixes. **Fork resolutions are RECOMMENDED DEFAULTS — native may override
any in review; note your reasoning if a default looks wrong on closer inspection.**

**B1 — bg_transit_engine (DEFER-001) → DEFAULT: FOLD into bg_transit_rules.** It has no standalone relational
meaning (it's the transit engine's 9 motion-parameter rows, a side-effect of bg_transit_rules). Add a second
`@register('bg_transit_engine')` decorator/sub-step to `bg_transit_rules.py` so a direct rebuild regenerates it,
OR (cleaner) remove bg_transit_engine as a standalone asset_registry entry and manage it inside bg_transit_rules.
Pick the fold that keeps one source of truth; document which.

**B2 — bg_nakshatra_medical (DEFER-002) → DEFAULT: FOLD into bg_medical_mappings.** Same pattern — it's a
side-effect of bg_medical_mappings. Add `@register('bg_nakshatra_medical')` to `bg_medical_mappings.py` (pairs
naturally with A2's expansion work — do them together), OR remove as standalone. One source of truth.

**B3 — bg_ephemeris → DEFAULT: write a real `bg_ephemeris.py` WriterBase writer** wrapping the legacy bootstrap
logic, so "Rebuild All" regenerates it via the orchestrator (don't leave it on the legacy `brahma_pipeline.py`
path). Alternative if the bootstrap is genuinely un-wrappable: reclassify `asset_type='service'`. Prefer the real
writer (ephemeris IS rebuildable data, not a probe service).

**B4 — bg_dignity_reference → DEFAULT: write a `bg_dignity_reference.py` writer** that re-seeds the 5 dignity
sub-tables (151 rows) from canonical SQL under the contract (ON-CONFLICT), so it's orchestrator-reproducible.
Alternative: mark `catalog_status='IMMUTABLE'` so the orchestrator intentionally skips it. Prefer the real writer
(consistency: every data asset should be rebuildable).

**B5 — ga_pyjhora_engine stuck error (since 2026-06-12).** Investigate the service-probe failure; once the
service is confirmed healthy, reset/clear the `asset_throughput` error row so the cockpit stops showing it
broken. If the service is genuinely down, report the root cause (don't just clear the flag on a broken service).

**B6 — ga_transit_anchors missing from seed.** It's in asset_registry (via migration) with a working writer but
absent from `asset_registry_seed.ts`. Add it to the seed so a from-scratch re-seed includes it.

**B7 — ga_prashna count_sql fix (the false-red).** In `asset_registry_seed.ts` (~line 977) the count_sql has a
stray leading `(`: `(SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1) AS count`. Fix to
`SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = $1` + a targeted migration to the live asset_registry
row. (Prashna FULL activation stays deferred post-L2 — out of scope here; just stop the false-red.) Verify via
the endpoint that ga_prashna shows lit/0-rows-valid, not error.

---

## EXECUTION + VERIFY

- Run Part A items in parallel (independent); Part B in parallel with A (independent). Each item: its own surgical
  migration(s), ledger-reconciled, seed-patched, endpoint-verified, CI green, merge-verified PR. Batch related
  items into sensible PRs (e.g. B1+A2+B2 medical/transit fold-ins; A3 yogas+doshas; A1 bg_rules standalone).
- After all: run the autonomy audit again — confirm the 4 autonomy gaps are CLOSED (Rebuild-All regenerates them),
  ga_pyjhora is healthy, ga_prashna is no-longer-red, the L0 catalogs are at their new floors. Hit the stats
  ENDPOINT (`?chart_id=482012f1`): every asset lit / non-null / no-error / not-stale, zero regressions.
- Report back: per-item PR + the endpoint JSON + the tightened bg_rules projection (A1 sampling result) + which
  fork default you took for B1-B4 and why.

**BOUNDARY REMINDER:** if any item appears to require touching ga_structural or bo_laksana, STOP and flag it for
the ga_structural track — do not cross the boundary. The ga_structural re-architecture + its defect-fixes + the
yoga fork + the MSR wiring are all handled in the separate track, not here.
