# Review request — Gochara family elevation plan v0.2

You are the independent reviewer. Your job is to break this plan before we build on it. Agreement is
not useful; a finding I missed is.

## Ground rules
- **Read-only.** No production code changes, no builds or dispatches, no migrations, no database
  writes, no PRs, no edits to the plan itself. The ONE file you may write is your review (below).
- The native's priorities, in order: **(1) quality of what the asset delivers, (2) build
  efficiency, (3) the surrounding ecosystem matters as much as the asset.** Judge everything
  against that order.
- Do not trust my summary. Open the cited source and the raw evidence. Treat every `[I]` and `[U]`
  tag in the plan as unproven.
- If you have the `layer-value-elevation` skill available, this is a Madhav L3 (Kāla) application
  of it.

## Where things are
Worktree `/Users/Dev/madhav-l3/integration` · branch `codex/madhav-l3-claude-code` · revision
`5d8252dbe`. **The plan and evidence files are untracked — read them from disk, not from git.**
Python with Swiss Ephemeris: `/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python`

## Read in this order
1. **The plan** — `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v0_2.md`
   (ignore `…PROPOSAL_v0_1.md`; it is superseded).
2. **The evidence** — same folder, `evidence_gochara/OUTPUT_2026-09-20.txt`, then re-run whichever of
   `E1`–`E7` you doubt. They are read-only, need no database, and run from anywhere:
   `<python above> <path>/E1_w2g_frame_defect.py`
3. **What the plan must fit** —
   - `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md` §1.2, §3.10, §7, §12.2
   - `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §3, §4, §5 (P3/P4), §6.1 rows L3-A05/A13/A14/H01, §6.3, §7 (U01–U11)
   - `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md` §3 (authority matrix), §6, §7
   - `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §1 (D1–D10), §3 (hubs), §4 (streams/rules), §5 (Q1, Q2, Q3, Q8)
   - `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/STATE.md` and `discussion_prompts/PROMPT_1_GOCHARA_FAMILY.md`
   - root `CLAUDE.md` §N.3–§N.8
   - history: `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/GOCHARA_SWEEP_2_0_DESIGN_v1_0.md`,
     `…/gochara_elevation/GOCHARA_UTKARSHA_CLOSE_REPORT_v1_1.md`,
     `…/kala_elevation/SHAD_DARSHANA_ADJUDICATIONS_NIGHT5_v1_0.md` (ADJUDICATION-14)
4. **The source the findings rest on** (all under `platform/python-sidecar/` unless noted) —
   - `services/gochara_v3/engine.py` :418, :469, :821, :1063, :1157 · `interval_solver.py` :116, :202 · `threshold.py` :393 · `resolution_hierarchy.py` · `mechanism_register.yaml` (MR-19 header)
   - `pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py` :360, :482-487, :1940 · `writers/ka_gochara.py` :120
   - `services/w2g/{arcs,crossings,solver,materialize,db_source,tiers}.py` — esp. `materialize.py:156-195`, `db_source.py:35,80`
   - `services/gochara_intensity/enrichment.py:124-150` · `brahmagyan/l0_ephemeris.py:16,52,168`
   - `services/ka_kshetra/stage0_kinematics.py` :18-20, :329, :437-470, :607
   - `pipeline/transit_search.py` :96, :131, :301-372 · `services/gochara_grammar/primitives.py` :247, :664-724
   - `services/ka_vedha_gochara/writer.py:86-87` · `services/ka_moorti_nirnaya/logic.py:1-60` · `services/ka_graha_sancara/engine.py:1-25`
   - `services/ka_gochara_resonance/writer.py:1-120`
   - `platform/scripts/seed/asset_registry_seed.ts:2117-2230`
   - `platform/migrations/588_remove_asset_build_protection.sql`, `platform/migrations/568_parishkara_mr45_hierarchy_natkey.sql`, `platform/supabase/migrations/{527,540,556}_*.sql`
   - `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` :566-590, :640 · `platform/src/lib/retrieval/registry/layers/reading_checklist.ts:1040-1075`

## What I need from you
**A. Findings.** For each of F1–F17 and the PoC: `CONFIRMED` / `REFUTED` / `PARTLY` / `UNVERIFIABLE`,
with your own evidence (file:line or command output). Priority targets:
 - **F3** — find the ayanāṃśa conversion I missed in the W2G path, or confirm there is none.
 - **F2 + PoC** — is any λ_v3 term *not* piecewise-constant in t? Is "exact on 7 of 8 primitives" right?
 - **F14 / F15** — are activity saturation and the kakshya fixture-approximation real on the *served*
   path, or artefacts of the 2-target, `conn=None` fixture I had to use?
 - **F13** — and explain the recorded ≥2-era-window case (career_setback, MR-44/45), which I cannot.
 - **F17** — is migration 588 applied in production?

**B. If you have read access to the live database** (I did not): per-class resonance target counts
for chart `482012f1-710e-4a25-994a-93821f5871aa`; rows by generation in `kala_gochara_windows` and
`kala_gochara_windows_v2`; contents of `kala_gochara_authority`; whether the 540/566 triggers exist;
any recorded wall-clock for a complete `ka_gochara_v3_century_materialize` build. Aggregates only.

**C. Recommendations R1–R10 (§8).** For each: `AGREE` / `AMEND` / `REJECT`, why, and your alternative.
Push hardest on:
 - **R4** — is contact-interval activity the highest-value repair? Is taking the Moon out of the
   activity term defensible, or does it discard a legitimate classical signal? Am I smuggling in
   doctrine anywhere?
 - **R1** — does consolidating into one successor hide a legitimate variant some consumer needs?
 - **R2** — new module vs. enriching `ka_graha_sancara`: which is right for the digest/hub rules?
 - **R6** — is a generation-keyed guard a fair reading of the native's 2026-08-23 instruction?

**D. The design (§7).** Does cutting at stations and wraps on the *sidereal* series bracket every
root — true-node prograde excursions, targets within minutes of a station, ayanāṃśa drift? Is 0.314″
longitude accuracy enough, or does some consumer need latitude/distance? Is one table + a new
generation + `kala_gochara_authority` a sound cutover?

**E. The ecosystem (§9).** Which reader or writer of `kala_gochara_windows`, `kala_gochara_windows_v2`,
`gochara_resonance_map` or `bg_gochara_arcs` did I miss? Which campaign rule does this plan break? Is
Stream C the right single owner?

**F. The implementation plan (§10–§11).** Is WP1+WP2+WP3 the right first slice? Wrong dependencies?
A packet that cannot pass its own exit gate? A failure mode missing from §11? What would you cut,
and what would you add?

**G. Verdict.** `PROCEED` / `PROCEED WITH AMENDMENTS` / `DO NOT PROCEED` on the first slice, your top
five risks ranked, and anything I stated more confidently than the evidence allows.

## Where to put it
Write your review to
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md`
with frontmatter (`artifact`, `version`, `status`, `reviewed_revision`, `reviewer`, `date`). Use the
finding and recommendation ids above so your review can be merged back line by line. Where you
disagree, say what would change your mind.
