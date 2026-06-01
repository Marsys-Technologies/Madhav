---
artifact: CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md
brief_id: FORENSIC_RENDER_COVERAGE_AUDIT
version: 1.0
status: ACTIVE — read-only analysis (NO code changes, NO deploy, NO migration)
authored_at: 2026-06-01
authored_by: cowork-planner
implementation_surface: Claude Code in Google Antigravity IDE
mode: AUDIT — produce a report artifact only; halt for native decision. Do NOT fix anything in this run.
why: >
  Native provisioned the new forensic render to capture MORE data points per chart than legacy
  FORENSIC v8.0 (PyJHora computes a richer fact set than the old pyswisseph model). But the new
  per-ayanamsha render is ~56KB vs v8.0's ~98KB with roughly equal chunk count — suggesting it
  is THINNER, not richer. This must be verified at the data level before downstream systems
  consume the forensic corpus and re-duplicate effort on incomplete data.
cowork_prefinding (CONFIRM or REFUTE with data — do not trust):
  - "compute_chart() (pyjhora_adapter/compute.py) returns ONLY: ascendant/lagna, houses, grahas/planets, vargas, dashas, panchanga, sensitive_points, ayanamsha, reconciliation + metadata."
  - "It does NOT return: shadbala, ashtakavarga (BAV/SAV), bhava_bala, chara/natural karakas, yogas/doshas, aspect matrices (Parashari/Jaimini/Tajik), vimsopaka, avastha schemes, KP cuspal sub-lords, Tajik varshphal, sahams, midpoints, eclipses, choghadiya, hora, tara/chandra bala, special lagnas, arudhas."
  - "ForensicRenderer.render() catches per-section exceptions and emits a '_[Render error]_' / empty placeholder, so renderers with no input data produce near-empty sections (rich code, thin output)."
  - "_chart_output_adapter.py hardcodes panchanga lords/padas to None and points all 6 house-systems at the SAME house_list (fake 6-system comparison)."
  - "The depth data (shadbala, ashtakavarga, KP, Tajaka, etc.) ALREADY EXISTS in chart_facts via v3.3 backfills — but the render reads compute_chart output, not chart_facts."
hypothesis_to_settle: >
  The forensic render is gated by compute_chart() coverage (~6 of ~13 data domains), so it is
  THINNER than v8.0 and far thinner than the renderers' capability. Confirm/quantify; if true,
  surface the fix options (extend compute_chart vs renderers read chart_facts) for native decision.
may_touch:
  - 00_ARCHITECTURE/audits/FORENSIC_RENDER_COVERAGE_AUDIT_REPORT_v1_0.md   (CREATE — the report)
  - a scratch script under platform/python-sidecar/tests/_audit/ (gitignored) for data extraction
must_not_touch:
  - EVERYTHING else. No renderer, adapter, engine, migration, or writer change in this run.
hard_bans:
  - No code fixes. No deploy. No migration. No JH/v8.0 value oracle (v8.0 is the SECTION/DATA-POINT baseline, not a value check). No Anthropic models.
prime_directive: only computed facts.
---

# Forensic render coverage audit — is the new render richer than v8.0, per ayanamsha?

## 0 · The question (answer it with a number, per section)

For ONE ayanamsha (use `lahiri`), does the new `forensic_render` document contain MORE, EQUAL,
or FEWER actual data points than legacy `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`? And where it is
thinner, WHY (engine doesn't compute it / adapter drops it / renderer bug / data is in
chart_facts but unread)? Multiply nothing by 5 — compare a single ayanamsha to the single-
ayanamsha legacy.

## 1 · Pull the four data sources (read-only)

1. **New render (actual output).** From production (or a local build) read the
   `forensic_render` `content_md` for the native chart, `ayanamsha_id='lahiri'`:
   ```sql
   SELECT content_md, byte_size FROM chart_documents
    WHERE chart_id='362f9f17-95a5-490b-a5a7-027d3e0efda0'
      AND ayanamsha_id='lahiri' AND document_type='forensic_render'
    ORDER BY rendered_at DESC LIMIT 1;
   ```
   Save it. This is the ground truth of what was actually churned.
2. **Legacy baseline.** `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (§0–§27; 30 H2 +
   79 H3). Build its data-point inventory per section.
3. **Renderer capability (the plan).** The 13 `pipeline/render/*_renderer.py` docstrings +
   code enumerate the INTENDED data points. This is what the native provisioned.
4. **Engine output.** Run `pyjhora_adapter.compute_chart('lahiri', <native jd_ut>)` in a scratch
   script and dump the top-level keys + the shape of each. Also list what `chart_facts` holds
   for the native (categories from `data_coverage` / `SELECT DISTINCT category FROM chart_facts`).

## 2 · Build the coverage matrix (the core deliverable)

One row per forensic section/domain. Columns:

| Section / domain | v8.0 data points | New render: populated? | New render data points | Renderer capability | Fed by compute_chart? | Exists in chart_facts? | Verdict |
|---|---|---|---|---|---|---|---|

For "populated?" inspect the actual `content_md`: is the section a real table with values, or
empty / `_[Render error]_` / all-`N/A` / `None`? Count real data points (table rows × meaningful
columns, distinct values) — not prose. Mark each domain: RICHER / EQUAL / THINNER / EMPTY vs v8.0.

Cover at least: identity, planets (positions+dignity+nakshatra), houses (+6-system — verify it's
real or faked), upagrahas, vargas (how many of D1–D60 actually populated), dashas (how many of
the 32 systems actually have data vs empty), panchanga (which fields real vs None), sahams,
chara/natural karakas, special lagnas, arudhas, aspects (Parashari/Jaimini/Tajik), shadbala,
ashtakavarga (BAV/SAV), bhava bala, vimsopaka + avastha schemes, yogas/doshas, KP cuspal
sub-lords, Tajik varshphal, midpoints, eclipses, choghadiya, hora, tara/chandra bala, longevity.

## 3 · Root-cause every gap

For each THINNER/EMPTY domain, classify the cause:
- **Engine gap** — `compute_chart()` doesn't compute/return it.
- **Adapter gap** — engine has it but `_chart_output_adapter` drops/hardcodes-None it (e.g.
  panchanga lords/padas, the fake 6-house-system).
- **Renderer bug** — input present but renderer errors/empties.
- **Wrong source** — data exists in `chart_facts` (v3.3 depth backfills) but the render reads
  `compute_chart` only and never queries `chart_facts`.

Quantify: how many domains are EMPTY purely because the engine output omits them while the data
sits in `chart_facts` already computed.

## 4 · Totals + verdict

- Total real data points: legacy v8.0 vs new render (single ayanamsha). State the ratio.
- Section completeness: N of ~28 domains fully populated / partial / empty in the new render.
- Byte explanation: account for 56KB vs 98KB (facts-only density vs missing-section stubs —
  quantify how much of the gap is each).
- **Plan-alignment verdict:** is the new render capturing MORE / EQUAL / FEWER data points than
  (a) v8.0 and (b) the renderer-capability plan? One clear sentence.

## 5 · Fix options (surface, do NOT implement)

If thinner (expected), lay out the options for the native to choose — with a rough effort + risk
sketch for each, no recommendation-as-decision:
- **A. Extend `compute_chart()`** to emit the missing depth domains (shadbala, ashtakavarga, KP,
  Tajaka, karakas, yogas, aspects, …) so the existing renderers light up.
- **B. Re-point the depth renderers at `chart_facts`** (where v3.3 already computed this data)
  instead of `compute_chart`, via the adapter.
- **C. Hybrid** — core from compute_chart, depth from chart_facts.
- Note the downstream-rebuild cost: forensic docs → rag_chunks → embeddings all regenerate once
  the render is enriched, so the native wants this settled BEFORE the eval baseline and before
  any consumer indexes the current thin corpus.

## 6 · Output

Write `00_ARCHITECTURE/audits/FORENSIC_RENDER_COVERAGE_AUDIT_REPORT_v1_0.md`: the §2 matrix, §3
root-causes, §4 totals+verdict, §5 options. Lead with a 5-line TL;DR answering the §0 question.
Commit the report to a branch and open it for native review. **No other code changes. Halt.**

## 7 · Acceptance criteria

1. Real `content_md` for lahiri pulled and inspected section-by-section (not inferred from code).
2. compute_chart() output keys dumped empirically; chart_facts categories listed.
3. Coverage matrix complete for all ~28 domains with populated?/data-point counts/root-cause.
4. Totals + ratio + byte explanation + one-sentence plan-alignment verdict.
5. Fix options A/B/C with effort/risk + downstream-rebuild note.
6. Report committed; zero production/code changes; pre-finding confirmed or refuted with data.

## 8 · Kickoff prompt (paste verbatim into Antigravity Claude Code)

```
You are running a READ-ONLY data audit. Do NOT change any code, schema, renderer, adapter,
engine, or deploy anything. Produce a report only, then halt.

Setup:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav && git fetch origin
  git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavForensicAudit -b audit/forensic-render-coverage origin/main
  cd /Users/Dev/Vibe-Coding/Apps/MadhavForensicAudit

Execute 00_ARCHITECTURE/BRIEFS/CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md end-to-end.

The question: does the new forensic_render doc (one ayanamsha = lahiri) contain MORE, EQUAL, or
FEWER actual data points than legacy FORENSIC_ASTROLOGICAL_DATA_v8_0.md — and where thinner, WHY?
Compare a SINGLE ayanamsha to the single-ayanamsha legacy (do not multiply by 5).

Pull 4 sources: (1) the REAL forensic_render content_md from chart_documents (native, lahiri) —
inspect the actual text, do not infer from code; (2) legacy v8.0 doc; (3) the 13 render/*_renderer.py
capabilities; (4) compute_chart() output keys dumped empirically + chart_facts categories.

Pre-finding to CONFIRM or REFUTE with data: compute_chart() returns only ~6 domains
(positions/houses/vargas/dashas/panchanga/sensitive_points) and NOT the depth set
(shadbala/ashtakavarga/KP/Tajaka/karakas/yogas/aspects/vimsopaka/midpoints/eclipses), so those
renderers emit empty/placeholder sections — making the render THINNER than v8.0 despite richer
renderer code. The depth data already exists in chart_facts (v3.3) but the render doesn't read it.
The adapter also hardcodes panchanga lords/padas to None and fakes the 6-house-system comparison.

Build the per-section coverage matrix (§2), root-cause every gap (§3: engine/adapter/renderer/
wrong-source), give totals + ratio + byte explanation + a one-sentence plan-alignment verdict (§4),
and lay out fix options A/B/C with effort/risk + the downstream-rebuild cost (§5) — surface them,
do NOT implement.

Write the report to 00_ARCHITECTURE/audits/FORENSIC_RENDER_COVERAGE_AUDIT_REPORT_v1_0.md with a
5-line TL;DR on top. Commit to the audit branch, push, open for native review. Change nothing else.
Report the verdict + the matrix back in chat.
```

---

*End of CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md*
