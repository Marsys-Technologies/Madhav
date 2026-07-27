---
artifact: SHODHANA_SHESHA_BRIEF (Fast-Follow: reopened items + close-out hygiene)
canonical_id: SHODHANA_SHESHA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-07-27
author: Fable (Cowork planning session), from SHODHANA_REPORT_v1_0.md §5/§8 + the native's review
parent: 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_BRIEF_v1_0.md
  (its §5 rails apply verbatim except where §2 below explicitly narrows or grants)
source_documents:
  - briefs/shodhana/SHODHANA_REPORT_v1_0.md  (the close report — §5 is the work order)
  - LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md (status ADDRESSED-v1; annotate again at close)
mode: >
  FULLY AUTONOMOUS · ONE Conductor (Sonnet) + two parallel builders (Sonnet; Opus only after 2
  failed verify cycles) + ONE Opus Verifier that never writes code · no human gates (Dvārapāla
  duty folds into the Conductor for a campaign this size — any would-be gate gets a documented
  conservative decision) · wall-clock cap 3h · PR + auto-merge only · explicit deploy · truth
  over completion.
authorization_grant: >
  BY LAUNCHING THIS BRIEF the native explicitly authorizes W2's scoped orchestrator run of the
  ga_sensitive_degree writer substep against PRODUCTION data for the two canonical charts
  (482012f1-710e-4a25-994a-93821f5871aa, 1c826d5a) ONLY. This grant does NOT extend to a Bodha
  (L2) rebuild — the ŚODHANA §3 Decision-2 PARK and its three release conditions stand
  unchanged.
---

# ŚODHANA-ŚEṢA — the remainder (MC-015 · MC-029 · close-out hygiene)

## §0 — Mission

Close the two FAILED-REOPENED items with their precisely-specified fixes, re-verify MC-001's
incidentally-resolved state on live evidence, reconcile the disposition tally, codify the
incident's lesson as a standing rail, and widen the strict-schema gate now that the
conflict-avoidance reason is gone. Everything here is narrow; nothing is exploratory. If a work
item turns out wider than specified, PARK-HONEST with evidence rather than expanding scope.

## §1 — Work items

### W1 · MC-015 — discoveries dedup does not manifest live (Builder B1, Sonnet)
Report evidence (§5): PR #803 changed `query_discoveries.ts` (+133 lines), raw counts dropped,
but live `bodha_discoveries_get(domain=wealth, chart 482012f1)` still serves the same finding
(aspect_parashari house 1/4/9) repeated across 4–5 ayanāṃśas with NO `discovery_families`
collapse. The sibling fix in the SAME PR (`kala_projections_get` → `projection_families`) works
live — so the pattern is proven; this is a scoped bug in one function.
**Method — diagnosis before code:** (1) reproduce live; (2) trace the actual code path — prime
suspects, in order: the deployed handler never calls the new collapse function (wiring/registration
miss), the collapse keys on a field that differs across these rows (e.g. keying on `signal_ids`
or `discovery_id` instead of `meaningfulness_basis`×`discovery_class`), or a domain-filter branch
bypasses the collapse; (3) compare line-by-line against the working `projection_families`
implementation; (4) fix, add a live-shape regression test (families present, agreement score,
member refs), PR.
**Acceptance (Verifier, live post-deploy):** `domain=wealth` returns collapsed
`discovery_families` — the house-1/4/9 motif appears ONCE with a cross-ayanāṃśa agreement score
and member refs; total distinct families for wealth ≤ a handful (register measured ~2 motifs in
53 rows); `projection_families` still works (no regression).

### W2 · MC-029 — materialize the Yogi/Avayogi asset + reconcile the old category (Builder B2, Sonnet)
Report evidence (§5): computation verified exact (Yogi point 352.351181° → Revatī → **Mercury**;
Avayogi 179.017847° → Chitrā → **Mars**), serving code sound, but **zero live rows** under
`sensitive_point_yogi` for either canonical chart — the writer substep never ran against
production. A pre-existing GA5 writer serves a partial, disagreeing `esoteric_point_yogi`
category.
**Method:** (1) Confirm the substep wiring (T6's writer registered in the orchestrator's
ga_sensitive_degree substep roster — if not registered, that IS the bug; register it). (2) Under
the frontmatter grant, trigger the SCOPED orchestrator run of the `ga_sensitive_degree` writer
substep for the two canonical charts only — verify first (grep + dry-run if available) that this
substep touches neither `kala_gochara_windows` nor `build_substep_progress`-protected state
beyond its own normal progress rows; delete-then-insert idempotency per §N.3. (3) Two-pass
verify the written rows. (4) Reconcile the legacy category: retire `esoteric_point_yogi`/
`esoteric_point_avayogi` (preferred — mark superseded_by_aggregate or remove from serving) OR
prove it now agrees exactly; two disagreeing sources may not both serve. (5) All 5 ayanāṃśas,
both charts.
**Acceptance (Verifier, live):** `ganita_sensitive_degrees_get` serves `sensitive_point_yogi`
rows for BOTH charts; 482012f1/Lahiri shows Yogi=Mercury (Revatī) + Avayogi=Mars (Chitrā) +
Duplicate-Yogi/Sahayogi populated, matching independent recomputation from live Sun/Moon
longitudes; legacy esoteric category no longer serves as a second disagreeing source; T5's
`reading_checklist` yogi/avayogi box flips from absent to served on a wealth judgment call.

### W3 · Close-out hygiene (Conductor, interleaved — no dedicated builder)
1. **Tally reconciliation.** The report's §0 dispositions sum to 41 (27+3+9+2) over 42 items
   (34 MC + 8 WL). Produce the per-item table (all 42 rows, one disposition each), find the
   unaccounted/double-counted item, append the corrected tally to the report (append-only
   changelog entry, never rewrite §0).
2. **MC-001 re-verification on live evidence.** (a) Re-measure 482012f1 orphan rate (report
   claims 0% post-external-rebuild) AND measure 1c826d5a independently (Dvārapāla condition —
   never assumed). (b) Verify T2's freshness stamp reports `fresh: true` for 482012f1 and its
   honest value for 1c826d5a. (c) **Provenance of the external rebuild:** the report records a
   2026-07-27 rebuild of 482012f1 that NO SHODHANA agent triggered and the disabled autonomous
   path cannot explain. Check orchestrator run logs / build records / PV-session artifacts for
   the trigger; the likeliest candidates are the concurrent PŪRṆA-VIRĀMA session or the native
   themselves. Document the finding (or the honest dead-end) in the report — an unexplained
   production write against the canonical chart must not stay unexplained. (d) Note the rebuild's
   PARTIAL scope (no yogi substep — W2 closes that; `ka_kalasutra`/`kala_bhavishya` not rebuilt —
   assess whether their staleness is material or label-only, per the EL-24 stale-semantics work).
3. **Integration-gate rail (the incident's lesson, codified).** Append to the standing campaign
   rails (wherever ŚODHANA's rails live for reuse — briefs/shodhana/ or the campaign-governance
   doc): (a) any campaign merging >1 serving-path PR must, before ANY traffic shift, build the
   deploy-candidate from merged `main` and verify it with REAL authenticated calls (the "hit it
   and check logs" discipline that caught #812), then canary, then cut; (b) any portal-wide
   registration-time gate/monkeypatch requires an integration test against the REAL SDK, not a
   mock (the #812 regression test is the template). One PR, docs-only.
4. **Strict-schema exclusion set widening (report §8.1).** `STRICT_SCHEMA_GATE_EXCLUDED_TOOL_
   NAMES` still excludes T1/T5/T7/T8's tools; the merge-conflict reason is gone. Widen coverage
   to those tools, run the T3 envelope battery + the #812 real-SDK regression test, ship in W1's
   or W3.3's PR (small). If any newly-covered tool legitimately needs loose params, document the
   exception inline rather than silently retaining it.

**Explicitly OUT of scope** (deferred, listed so the Conductor doesn't absorb them):
`mimamsa_lel_query` non-functional params (report §8.2 — new investigation), the
`verbosity:'summary'` guaranteed-fits form for MC-004/006 (report §8.5 — real feature work),
the DAG-doc reconciliation + Bodha-rebuild authorization (§3 conditions — native-gated),
the sealed-harness baseline disambiguation (report §7 — governance question). Note in the
close report that these remain open.

## §2 — Rails

Parent brief §5 rails apply verbatim (untouchables · PR+auto-merge only · explicit deploy ·
preserve-list checks · no fabrication), with these deltas:
- **GRANTED:** the W2 scoped ga_sensitive_degree writer run (frontmatter grant, two charts only).
- **STILL PARKED:** Bodha (L2) rebuild — all three Decision-2 conditions stand.
- **PV:** PŪRṆA-VIRĀMA may still be live. Same locks: never touch root `CLAUDECODE_BRIEF.md`;
  check for PV branches before cutting worktrees; W3.2(c)'s provenance hunt READS PV artifacts
  but never modifies them.
- **Deploy discipline:** this campaign eats its own W3.3 dogfood — merged-main candidate, real
  authenticated verification, canary, cutover, in that order, even for these small PRs.

## §3 — Verification & close

Nothing is DONE until the Opus Verifier accepts against live production post-deploy. Four
dispositions, no "passed with caveats." Close artifacts: `SHODHANA_SHESHA_REPORT_v1_0.md`
(short — per-item dispositions, the tally-corrected table, the rebuild-provenance finding, the
rails PR link), register annotated (MC-015/MC-029 → their final state; ADDRESSED-v1 → 
ADDRESSED-v1.1), worktrees/branches cleaned, production == `main` HEAD confirmed.

## §D — Kickoff prompt (single paste)

```
You are the CONDUCTOR of ŚODHANA-ŚEṢA (fast-follow), FULLY AUTONOMOUS. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_SHESHA_BRIEF_v1_0.md — this
    brief; its §1 work items are the entire scope and its §2 rails bind you;
(2) briefs/shodhana/SHODHANA_REPORT_v1_0.md §5, §3 (Decision 2 + post-close finding), §8, §10;
(3) the parent SHODHANA_BRIEF_v1_0.md §5 rails.
The native's launch of this prompt constitutes the brief's frontmatter authorization: the SCOPED
ga_sensitive_degree writer run for the two canonical charts is GRANTED; the Bodha L2 rebuild
remains PARKED. Dispatch two parallel Sonnet builders in isolated worktrees (.worktrees/
shodhana-shesha-w1, -w2) for W1 (MC-015 diagnosis-first) and W2 (MC-029 materialization +
legacy-category reconciliation); run W3's four hygiene items yourself between dispatches. Opus
step-up only after 2 failed verify cycles. ONE Opus Verifier that never writes code accepts
every item against LIVE production post-deploy — four dispositions, no "passed with caveats".
PR + auto-merge only; deploy amjis-mcp explicitly using the merged-main → real-authenticated-
verify → canary → cutover discipline; PŪRṆA-VIRĀMA artifacts are read-only; never touch root
CLAUDECODE_BRIEF.md. Untouchables: kala_gochara_windows data, build_substep_progress, the
sealed evaluator harness. Wall-clock cap 3h. Close with SHODHANA_SHESHA_REPORT_v1_0.md, the
corrected 42-row disposition table, the external-rebuild provenance finding, register annotated
ADDRESSED-v1.1, worktrees cleaned, production == main. Truth over completion. Begin.
```
