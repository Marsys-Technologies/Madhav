# ga_structural — Phase-3 empty-category gate (diagnose + fix before L2) — paste into Claude Code

**Read CLAUDE.md §C first + memory `feedback-ga-structural-rebuild-locked-logic`.** The ga_structural v2.0
core rebuild is SEALED + PR-ready (build 5d11969e, 106,014 rows, 67 working categories, graph-theoretic
restored, L1-authority verified, FORENSIC 7/7). BUT the L1-authority follow-on audit found **2 Phase-3
blind-spot categories we DESIGNED IN are silently producing 0 rows** — they are NOT in the "69 non-zero"
count because they emit nothing. These were approved v2.0 scope. **HARD GATE: diagnose + fix (or consciously
cut) before L2 Bodha opens.** The "unknown cause" one must be ROOT-CAUSED — unknown-cause failures are not
acceptable as backlog.

## STANDING RAILS
no-threshold-drop; L1-authority §N.5 (refs in `fact_value_jsonb.constituent_fact_ids` resolving to real
fact_ids — the column `constituent_facts_array` does NOT exist; `_CF_INSERT_COLS` excludes it, so never rely on
the `_base_row(constituent_facts_array=...)` parameter); all-30-vargas where varga-meaningful; FROZEN
orchestrator contract (HALT if change seems needed); per-chart delete-then-insert; floor = ACHIEVED (recalibrate
after — the count will RISE when these populate); verify by per-category breakdown + acharya check; only 482012f1;
FORENSIC 7/7.

---

## CATEGORY 1 — `_build_nakshatra_relationship_rows` (nakshatra co-tenancy / tara / nakshatra-lord) — DOUBLE BUG

Designed in §0.5 of the logic doc (nakshatra co-tenancy + tara + nakshatra-lord relationships). Currently 0 rows.
Two confirmed bugs:
1. **Nakshatra key absent from `graha_nakshatra_join`** — the builder reads a nakshatra field that isn't present
   (or is named differently) in `graha_nakshatra_join`. INVESTIGATE the actual columns/fact_keys ga_nakshatra
   writes (the GAP-4 fix already found nakshatras must come from `graha_position` — confirm the SAME source
   convention here; the co-tenancy builder likely reads the wrong table/key the same way GAP-4 did).
2. **Broken constituent-ref path** — uses the silently-dropped `_base_row(constituent_facts_array=...)` param.
   Move refs into `fact_value_jsonb.constituent_fact_ids` (the fixed pattern), pointing at real
   `graha_nakshatra_join` / `graha_position` fact_ids.
FIX both, rebuild, confirm: co-tenancy rows fire (two grahas in the same nakshatra), tara_bala rows fire
(1–9 from Moon's nakshatra), nakshatra-lord rows fire — each with resolving fact_ids. D1 per ayanamsha
(nakshatra positions don't vary by varga). Acharya-check: a real co-tenancy pair for 482012f1, and Moon's own
tara = 1 (janma).

## CATEGORY 2 — `_build_bhava_chalit_divergence_rows` — UNKNOWN 0-ROW CAUSE (root-cause, do NOT backlog)

Designed in §0.5 (bhava-chalit vs rasi divergence flag). Currently 0 rows for an UNKNOWN reason. **Root-cause it
— an unknown silent-empty in the L2-critical hub is exactly the failure class we will not ship blind.**
Investigate in order: (a) does the source data exist? — confirm `bhava_chalit_house`/`bhava_chalit_sign` (or
whatever GA1/GA5 actually writes) is present in chart_facts for 482012f1; if the source category name is wrong,
that's the cause (same wrong-source-table pattern as GAP-4 + Category 1). (b) Is the builder even called by the
orchestrator/substep dispatch? (c) Does the divergence condition never fire (e.g. all grahas happen to have
chalit==rasi house, so the "emit only when diverges" guard suppresses everything)? — if (c), that's LEGITIMATE
(no divergence = correctly 0), and the fix is to DOCUMENT it as genuinely-zero-for-this-chart, not a bug.
Report which of (a)/(b)/(c) it is with evidence. If (a) or (b): fix + rebuild + confirm rows. If (c): document
as legitimately empty for 482012f1 (and confirm the builder WOULD fire on a chart with divergence).

---

## VERIFY + DISPOSITION
- Category 1: nakshatra co-tenancy/tara/lord rows now non-zero, fact_ids resolve, acharya-checked. Rebuild count
  rises; recalibrate floor.
- Category 2: root cause identified as (a)/(b)/(c) with evidence. Either populated (a/b) or documented
  legitimately-empty-for-this-chart (c).
- Update GA_STRUCTURAL_REBUILD_VERIFY (or a v2.1 addendum) so the per-category table reflects the now-populated
  categories — "all categories non-zero" must mean ALL designed categories, not just the ones that happened to
  emit.
- Confirm NO other designed Phase-3 category is silently empty (re-list §0.5's five designs — virupa_drishti
  2,850 ✓, significator_path 360 ✓, bhinnashtakavarga edges?, co-tenancy, chalit — verify each of the five is
  either populated or consciously-cut-with-reason).
- FROZEN contract untouched; floor = ACHIEVED.

**This is the Phase-3 completeness gate. The CORE rebuild (PR #301 ga_structural piece) is sealed and merges
independently. L2 Bodha opens only after this gate clears — every DESIGNED relationship type is either
populated or consciously documented as cut, with zero 'unknown empties' remaining.**
