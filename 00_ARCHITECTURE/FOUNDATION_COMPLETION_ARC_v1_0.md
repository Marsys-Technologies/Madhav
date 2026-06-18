---
artifact: FOUNDATION_COMPLETION_ARC_v1_0.md
canonical_id: FOUNDATION_COMPLETION_ARC
version: 1.0
status: CURRENT — native-ratified 2026-06-18
authored_by: Cowork (planning) 2026-06-18
authored_for: closing every L0+L1 completeness defect BEFORE L2 Bodha (bo_laksana) opens
grounded_in: L0_L1_STRATEGIC_DEEP_AUDIT_v1_0.md (live-DB + code-cited audit)
governing_decision: >
  Native ratified 2026-06-18: GATE L2 on all 5 BUILD-NOW defects + the 2 still-live ga_structural
  defects. Completeness is the #1 value; Bodha must not inherit gaps. ga_yoga resolution =
  investigate-first (decide fix-evaluator vs repoint-bo_samskara on evidence).
why_ordered: >
  These items have upstream→downstream dependencies. L0 source-catalogs (bg_yogas/bg_doshas/
  bg_medical_mappings/bg_rules) feed ga_structural's catalog path; ga_structural feeds bo_laksana/MSR.
  Building ga_structural fixes before the L0 catalogs are complete = rebuilding ga_structural twice.
  The order is L0-catalogs → ga_structural-rebuild → bo_laksana-wiring.
---

# Foundation Completion Arc v1.0 — close every completeness defect before L2

> **⚠️ SCOPE AMENDMENT 2026-06-18 (native):** ga_structural's RELATIONAL RE-ARCHITECTURE (does it need to INGEST
> the enriched/new L1 assets — enriched ga_sensitive, per-varga ga_strength, the parallel nakshatra chart, etc. —
> and derive their relational value) is PULLED OUT of this arc into its OWN dedicated track:
> `GA_STRUCTURAL_RELATIONAL_HUB` (investigation-first, then architecture). Reason: ga_structural was built against
> the OLD, smaller L1; the layer has since grown, and whether the relational hub must be re-architected to weave
> in the new relational value is the single highest-value pre-L2 decision — too important to bury in a wave.
> This arc retains only ga_structural's WRITER-INTERNAL DEFECT fixes (Wave 2: benefits_in / uncatalogued / orb)
> and the bo_laksana PROJECTION wiring (Wave 3). The ga_structural INGEST-completeness question is separate. The
> audit's "dual-capture working" claim (Q4.5) is UNVERIFIED against the enriched assets — do not trust it; the
> dedicated track re-establishes ground truth first.

## §0 — What this arc is + the prime principle

The pre-L2 deep audit (`L0_L1_STRATEGIC_DEEP_AUDIT_v1_0.md`) found NO data regressions but 5 BUILD-NOW
completeness defects + 2 still-live ga_structural defects. The native ruled: **close them ALL before bo_laksana
opens** — Bodha's signals can only be as complete as the L0+L1 base they project. This arc is the named sub-phase
that does that, in dependency order, each item computed-and-cited (the hard gate) and prod-verified via the
ENDPOINT (the standing rail — never DB-only; use `?chart_id=` not `?chartId=`).

**Inherited standards:** computed-and-cited HARD GATE (uncited → floor NULL+reason, never fabricate);
canonical-or-floor; L1 delete-then-insert idempotency; L0 ON-CONFLICT; FROZEN orchestrator contract (writer-
internal fixes only — NO contract change; HALT if one seems needed); surgical migrations ≥ next-free (main at
314 + #300 pending — confirm); ledger-reconcile; seed-consistency; endpoint-verify; only `482012f1`; FORENSIC 7/7.

**The reframe the audit produced (hold this):** ga_structural is RICHER than assumed — it computes **74,034
total rows** (the full asset), of which a LARGE SUBSET (the audit derived ~45-47k by summing the unprojected
categories — argala+virodha ~43,200 + lord matrices ~2,723 + 4 avasthas + functional-class + karaka-strength +
Jaimini/Tajik) is computed but NOT projected into bo_laksana/MSR. **DO NOT trust these derived numbers — they
are the audit agent's arithmetic, unverified against the live table.** The relational-elevation opportunity is
NOT "compute more in ga_structural"; it is "PROJECT what ga_structural already computes into bo_laksana/MSR"
(Wave 3). The computation gap is small; the projection gap is large. **Wave 3 MUST query the live per-category
count for 482012f1 and project against the ACTUAL rows — never against a number quoted in this doc or the
audit.** (Lesson of this whole campaign: reported numbers diverge from reality; verify at execution, every time.)

---

## WAVE 0 — ga_yoga investigation (read-only; decides the architecture; GATES the rest)

**Why first:** the yoga source-of-truth fork (fix ga_yoga evaluator vs repoint bo_samskara to ga_structural's
yoga_label) shapes Wave 1 (bg_yogas), Wave 2 (ga_structural rebuild), and Wave 3 (bo_laksana). Resolve before building.

**Investigate (read-only, code + prod):**
1. Read `ga_yoga_writer.py` lines 812–825 (the `return None` stubs) — list EVERY unimplemented relation type.
   How many of the 175 catalog yogas does the evaluator currently fail to evaluate?
2. Read ga_structural's yoga catalog path (`_load_yoga_catalog` + `_build_yoga_rows`). The 409 `yoga_label` rows
   it fires — query them: how many DISTINCT yogas, across how many ayanamshas? Do they carry the same
   constituent_facts + citations ga_yoga_firings would?
3. **Compare the two outputs head-to-head:** are ga_structural's 409 yoga_label rows a SUPERSET of what a
   completed ga_yoga evaluator would produce, a subset, or different? Is yoga_label richer (more yogas, real
   fact_ids, citations) or poorer (e.g. missing the per-ayanamsha firing detail ga_yoga produces)?
4. Check what `bo_samskara` is SPEC'd to read (its master plan + any stub code) — ga_yoga_firings specifically,
   or yoga firing data generically?

**Decide + recommend (the fork):**
- **Option A — fix the ga_yoga evaluator:** complete the `return None` stubs so ga_yoga_firings populates fully.
  Keeps the designed architecture (bo_samskara ← ga_yoga_firings). Choose if ga_yoga produces something
  yoga_label does NOT (e.g. richer per-ayanamsha firing semantics, or it's the canonical firing table).
- **Option B — repoint bo_samskara to yoga_label:** leave ga_yoga, point bo_samskara at ga_structural's 409
  yoga_label rows. Choose if yoga_label is a superset / richer and ga_yoga is redundant. Cleaner (one yoga
  source of truth = ga_structural's catalog path).
- **Option C — both:** ga_yoga becomes the per-chart firing detail, yoga_label the relational projection; bo_samskara
  reads whichever is canonical. Choose only if they're genuinely complementary, not redundant.

**Output Wave 0:** `GA_YOGA_SOURCE_OF_TRUTH_FINDING.md` — the head-to-head comparison + a recommended option
with evidence. **HALT for native sign-off on the fork before Wave 2 rebuilds ga_structural / Wave 3 wires
bo_samskara.** (Wave 1 L0 catalog work can proceed in parallel — it's upstream of both options.)

---

## WAVE 1 — L0 source-catalog completion (upstream; everything inherits from these)

Run these in parallel (independent of each other); all are L0 ON-CONFLICT, cited, endpoint-verified. They must
COMPLETE before Wave 2 (ga_structural rebuilds against them).

**1A — bg_rules bulk-mine (660 → 8,193 chunks).** The extraction infra that produced the 2,912 existing
sutravali_rules already exists — this is a BULK RE-RUN over the remaining 7,533 `classical_text_chunks`, not new
code. Run it; every extracted rule cited to its source chunk (computed-and-cited holds — these are deterministic
extractions over existing cited text, not generated content). Verify: bg_rules row count jumps from 2,912 toward
full-corpus coverage; set target_floor = achieved.
  - GUARD: if extraction quality on the un-mined chunks is lower (different chunk types), floor-and-flag the
    low-confidence extractions rather than dropping or fabricating. Confirm the extractor is deterministic, not
    an LLM generator (it must be, per the deterministic-first rule).

**1B — bg_medical_mappings (9 → ~150-200).** Add the missing tiers: planetary-combination medical rows + the
27×3 nakshatra-dosha grid + dignity-modified health indicators. Each cited to its classical source (BPHS Ch.18 /
Ashtanga Hridayam / the Ayurvedic-Jyotish texts). UPSTREAM FIX: ga_medical reads bg_medical_mappings, so this
auto-improves ga_medical on its next build (Wave 2). Build bg_medical_mappings FIRST.

**1C — bg_yogas (175 → 250) + bg_doshas (50 → fuller).** Add the missing classically-cited yoga definitions
(Jaimini yogas, Nabhasa variants, KP yogas) + dosha variants (Kuja/Grahan/Pitra/Naga), each with a
machine-evaluable `formation_rule_jsonb` + citation. CAPS ga_structural's catalog firing — so completing these
BEFORE Wave 2's ga_structural rebuild means the rebuild fires against the full catalog (no double-rebuild).
  - GATE: a yoga/dosha def is added ONLY if its formation rule is deterministically evaluable AND citable. An
    un-evaluable or uncited "yoga" is floored/skipped, not fabricated.

**1D — bg_remedies expansion (266 → fuller).** Add mantra prescriptions, yantra specs, dana schedules — cited.
LOWER PRIORITY within Wave 1: only bo_upaya (a later L2 asset) consumes it, so it can lag the others; but it
gates bo_upaya, so it must land before L2 reaches bo_upaya. Keep it in this arc.

**Wave 1 exit:** all four L0 catalogs at full computed-and-cited depth; floors = achieved; endpoint-green;
seed-patched. NOW ga_structural can rebuild against complete catalogs.

---

## WAVE 2 — ga_structural defect fixes (depend on Wave 1 catalogs complete)

Writer-internal fixes to `ga_writers/ga_structural_writer.py` (NO orchestrator contract change). Rebuild
ga_structural for 482012f1 AFTER Wave 1 so the catalog path fires against the complete bg_yogas/bg_doshas.

**2A — benefics_in composite stub (line 3833).** Replace `return False, "composite_distributional_unimplemented"`
with the real composite-distributional evaluation so Adhi Yoga + ~14 formations fire via the catalog path.
Verify those yogas now appear in yoga_label.

**2B — uncatalogued_configuration emission (prior finding Fix 4.2 — STILL UNSHIPPED).** After the catalog
evaluation loop, scan the structural-pattern inventory; when a real configuration matches NO catalog entry, emit
a typed `uncatalogued_configuration` fact referencing its constituent fact_ids. This is the GAP-DETECTION tool —
"a real pattern with no classical name." Verify: the category now has > 0 rows where appropriate; "absence
becomes presence."

**2C — orb-drop → low-strength (prior finding Fix 4.3 — STILL LIVE).** Replace `if orb > 10.0: continue` (lines
917-935 D1, 3245 varga) and the Tajik 30° drop with a low-`orb_tightness` emit (`orb_tightness = 1 - orb/180`).
Serve-time ranks; the asset never gates. Verify wide-orb pairs now emit rows.

**2D — fallback-path hygiene (LOW).** The 44 yoga_fires/10 dosha_fires legacy residuals: ensure the
delete-then-insert idempotency wipes them on rebuild; add a build-time WARNING if the catalog path ever falls
back to the YOGA_LIBRARY/DOSHA_LIBRARY hardcode (so the fallback is visible, not silent). Don't delete the
hardcode (it's the emergency fallback) — just make its use loud.

**Wave 2 exit:** ga_structural rebuilt against complete catalogs; benefics_in fires; uncatalogued + wide-orb rows
present; FORENSIC 7/7 holds; endpoint-green; ga_structural floor = new achieved count (migration + seed).

---

## WAVE 3 — the MSR wiring (the elevation; first L2/bo_laksana work; folds in Wave 0's decision)

This is technically bo_laksana (L2) work, but it IS the relational-elevation the native asked for, and it
depends on Waves 0–2. It's the seam where Foundation Completion hands into L2 Bodha.

**3A — Project the currently-UNPROJECTED ga_structural categories into MSR.** Add to bo_laksana's
`STRUCTURAL_SIGNAL_CATEGORIES` (`pipeline/orchestrator/writers/bo_laksana.py` lines 38-55) these categories that
ga_structural computes but bo_laksana does not currently read: `argala_natal_matrix`, `virodha_argala_natal_matrix`
(the intervention graph), `lord_in_house_per_varga`, `lord_aspects_lord_per_varga`,
`graha_avastha_baladi/deepta/jagrad/sayanadi` (the 4 missing avastha systems — only lajjitadi is projected today),
`graha_functional_class_per_ascendant` (yogakaraka/functional-malefic), `karakatva_strength_per_significance`,
`aspect_jaimini` (D1), `aspect_tajik`. Each needs a CATEGORY_DOMAIN_MAP entry too. NO ga_structural change — pure
projection. **FIRST STEP of 3A: query the live per-category row count for 482012f1 (`SELECT fact_category,
count(*) FROM chart_facts WHERE chart_id=:c AND fact_category IN (...) GROUP BY 1`) — confirm each category exists
and is non-empty BEFORE adding it to the signal list; project against the ACTUAL count, never a number from this
doc or the audit. Also CONFIRM the full set: re-derive which categories ga_structural emits vs which bo_laksana
already projects, by querying both — don't assume this list is exhaustive or that all 9 are still unprojected.**

**3B — Apply Wave 0's yoga decision** (fix-evaluator OR repoint-bo_samskara OR both) so the L2 yoga signal reads
the canonical, complete yoga source.

**Wave 3 exit:** bo_laksana projects the COMPLETE ga_structural relational surface; MSR signal richness reflects
the full intervention graph + avasthas + functional class + karaka strength + the resolved yoga source. This is
the elevated relational foundation L2 Bodha builds on.

---

## PARALLEL TRACK — non-gating hygiene (anytime; doesn't block the waves)

- **Autonomy writers (4):** add `@register` writers (or reclassify service/IMMUTABLE, or fold into parent) for
  bg_ephemeris, bg_dignity_reference, bg_transit_engine (→ bg_transit_rules), bg_nakshatra_medical (→
  bg_medical_mappings) so "Rebuild All" regenerates them. (bg_nakshatra_medical's fold-in pairs naturally with
  Wave 1B's bg_medical_mappings work.)
- **ga_pyjhora_engine:** investigate + reset the stuck error throughput (since 2026-06-12).
- **ga_transit_anchors:** add to asset_registry_seed.ts (registry has it, seed doesn't).
- **ga_prashna count_sql fix:** remove the leading `(` (seed_ts ~line 977) + migration → stops the false-red.
  (Prashna full activation stays DEFERRED post-L2 — zero L2 dependency.)

---

## §E — Sequencing summary + close

```
WAVE 0 (ga_yoga investigate, read-only) ──→ HALT for native fork sign-off
        │ (Wave 1 may run in parallel — it's upstream of both forks)
WAVE 1 (L0 catalogs: bg_rules ∥ bg_medical_mappings ∥ bg_yogas+bg_doshas ∥ bg_remedies) ──→ all complete
        ↓
WAVE 2 (ga_structural fixes: benefics_in + uncatalogued + orb + fallback-hygiene; rebuild) ──→ endpoint-green
        ↓
WAVE 3 (bo_laksana wiring: project 45k rows + apply yoga decision) ──→ elevated MSR foundation
        ║ PARALLEL TRACK (autonomy writers, pyjhora reset, seed, prashna count_sql) — anytime
        ↓
L0+L1 FOUNDATION COMPLETE ──→ L2 Bodha (bo_laksana) opens on a complete, elevated base
```

Each wave: computed-and-cited, endpoint-verified (the `chart_id=` rail), prod-ledger-reconciled, FORENSIC-clean,
no contract change. Validate-as-you-go (each item verified when it lands; the arc seals once at the end). When
all waves + the parallel track are done, re-run the autonomy audit + endpoint check to confirm the foundation is
complete and clean, then open L2 Bodha.

*End. Close every completeness defect in dependency order (L0 catalogs → ga_structural → bo_laksana projection),
resolve the yoga fork on evidence first, keep hygiene in parallel — so L2 Bodha is built on a complete, elevated,
non-dropping foundation. This is the foundation-completion the native required before Bodha.*
