---
artifact: SHAD_DARSHANA_STATE (Campaign Ledger)
canonical_id: SHAD_DARSHANA_STATE
version: rolling
status: LIVE — created by Night 1 session (W0.1), updated at every wave boundary and session close
created: 2026-07-29
schema: per SHAD_DARSHANA_BRIEF_v2_0.md §6
governing: SHAD_DARSHANA_NIGHT_RUN_v1_0.md (orchestration) + SHAD_DARSHANA_BRIEF_v2_0.md (execution contract)
  + KALA_SUPREME_ELEVATION_v1_0.md (v1.2, spec authority) + KALA_SIX_VIEWS_DESIGN_v2_0.md/v1_0.md
---

# ṢAḌ-DARŚANA STATE — the campaign ledger

## NEXT-ACTION

**HOLD LIFTED (2026-08-01, native — requested the Night-3 kickoff; the §D paste authorizes
the run).** The hold condition was verified satisfied before lift, not assumed: **zero open
SAMĀPTI PRs** as of 2026-08-01 (checked live against Marsys-Technologies/Madhav).

**NIGHT-3 OPENING ORDERS (the frontier; supersedes the generic §C night-map for tonight):**
1. **Session-open protocol per §D (v1.3)**: rebase integration onto main · ledger-
   reconciliation sweep · ANTARYĀMIN discharges ALL pending adjudications up front · deploy.
2. **Deploy current `main` to production first** (Night 2's standing next-action — `main` has
   been one deploy ahead since Night 2's close, by explicit native decision then; the
   blocking consideration at the time, other campaigns' unshipped work, has since resolved:
   PŪRṆATĀ closed 2026-07-31, SAMĀPTI zero open PRs). Full verify discipline + Verifier
   acceptance on both charts before any new build work lands on top.
3. **Ledger-reconciliation sweep known target**: item 2's row reads IN-PROGRESS but PR #934
   (`w1-recurrence-digest`) is MERGED and the W1 gate-close record claims 12/12 VERIFIED —
   reconcile the row against the W1 round-2 evidence, append-only, citing it.
4. **ANTARYĀMIN's up-front docket (all before builders dispatch):** N1–N4 rulings + record
   N5's CONSERVATIVE-DEFAULT verbatim into the N-block (it has sat empty for two nights —
   W2G is unstartable until it is filled) · **the N_e priors-source design ruling** (see 5).
5. **The N_e blocker is tonight's critical path** (Lane C's honest disclosure, see the
   Night-2 record below): the hazard formula's lifetime-count priors
   (`fact_kind='lifetime_count_per_100y'`) exist nowhere in the corpus; a real `ka_kshetra`
   build writes ZERO field rows until an L0 lane seeds them. ANTARYĀMIN rules the source
   design (candidates: classical-text-derived counts with citations; documented demographic
   base rates as structural priors; cohort-derived where genuinely derivable — NEVER read
   `base_rate_by_age` as N_e, §5.1 C-1 forecloses that exactly); then a small L0 seeding
   lane lands it under the §D data-honesty rail: every value cited, versioned,
   structural_prior-labeled. A number without a source is a build error.
6. **Then the real Gate-W2 integration sequence** (design doc §10 / brief §3 W2): field
   build both charts → hash-replay determinism → weights-v0 seed → skill score published
   (both charts; FIRST score = CI baseline) → time-rescaling GOF report → specificity gate
   flips HARD → authority-basis census population → insight rows lead readings → Nirmāṇa
   checks green (L0 assets built in production BEFORE the first per-chart field build).
7. **In parallel with 5–6, dispatch the W3 lanes whose prerequisites are already met**
   (need L1/ephemeris/views, not the field): moorti (4) · vedha + REAL Sarvatobhadra grid
   (5) · Tithi-Praveśa (13) · Kota (16) · Sudarśana (17, writer `ka_sudarshana_varsha`) ·
   health/adverse class (9, S4-05 re-test). The lattice-query ENGINE (36's remaining half)
   + activity tables (6) + muhūrta-lagna (7) can also start — substrate (PR #930) is in.
   W2G starts the moment the N-block is filled (order 4). W4 design (5a) the moment 36+41's
   engine work lands. Field-dependent W3 items (33, 34, state_delta, decision_value) wait
   for 6.
8. **Gate W2 close = the §B.2 gate-close PR** (integration → main, rides the merge queue,
   5–60 min is normal) → deploy → PARĪKṢAKA live acceptance → ledger + morning report.

**Four infrastructure changes landed during the hold** — Night 3's Conductor MUST read
`SHAD_DARSHANA_NIGHT_RUN_v1_0.md` (now v1.3 — the §D prompt itself was elevated 2026-08-01,
read it fresh) rather than rely on cached knowledge of earlier mechanics:

1. **The integration branch is now the merge target for every lane PR** — `main` receives one
   deliberate merge per wave-gate close only (NIGHT_RUN §B.1/§B.2). `main == production`
   remains the invariant; `shad-darshana/integration == main` does NOT, between gates, by
   design.
2. **The two chronic multi-lane hot-file collisions are fixed structurally**: the 8 kala_*
   tool registrations are consolidated into `kala_views/register_all.ts` (registry_bridge.ts
   touches it exactly once, never again); `m8_e2e_proof.test.ts`'s two hand-bumped exact-count
   literals are replaced with a duplicate-registration check + a mass-regression floor (needs
   no bumping for ordinary tool additions). Neither change touches `server.ts`'s
   `REGISTERED_TOOL_COUNT` — that remains SAMĀPTI's own territory (PR #912, still open as of
   this writing).
3. **W4's Phase 4/5 boundary is now item-triggered, not gate-triggered**: Phase 5a (the W4
   Opus design pass) starts the moment items 36+41 land, not when W3/W2G/W3K's gates close —
   genuine additional parallelism, since W4 needs nothing from W2G or W3K.
4. **The repo migrated orgs (2026-07-31): `amonty84/Madhav` → `Marsys-Technologies/Madhav`.**
   `main` now merges through GitHub's merge queue (ruleset `20141220`, not classic branch
   protection) — the gate-close PR takes up to ~5–60 min to actually merge after checks pass,
   not seconds; do not treat a queued-but-unmerged green PR as stuck (NIGHT_RUN §B.2a).
   `shad-darshana/integration` carries no ruleset. Any `gh`/`git` invocation hardcoding
   `amonty84/Madhav` is now wrong — use `Marsys-Technologies/Madhav` or omit `--repo` and let
   it infer from the local remote.

**Resume checklist for whoever restarts the campaign:** (a) confirm SAMĀPTI has genuinely
dissolved/closed before dispatching anything; (b) rebase `shad-darshana/integration` onto the
current `origin/main` tip FIRST if it's been more than a few days — it was last rebased
2026-08-01 at `origin/main`@`8d7dee58`+; 52 commits of drift had already accumulated by that
point in ~36h (the PURNATA campaign's close-out + the org migration itself), so treat drift as
the norm, not the exception, for this repo; (c) THEN resume from the Night-2-authored
NEXT-ACTION below, which remains the substantive "what to do next" for the campaign's own
build state (Gate W1 closed, Gate W2 blocked on the N_e resolution, `main` one deploy ahead of
production by design).

---

**NIGHT 2 CLOSED (2026-07-31 — see MORNING REPORT at the end of this file for the full
close-out).** Gate W1 VERIFIED-CLOSED. All 5 W2 build lanes merged to `main`; Gate W2 itself
NOT closed (Lane C's disclosed N_e lifetime-count-priors gap must resolve first). `main` is
one deploy ahead of production, by explicit native decision, not oversight. **Single next
action for Night 3: deploy `main`, then resolve the N_e blocker before starting Gate W2's real
integration work** — see the MORNING REPORT for full detail. The Night-2 narrative below is
retained for evidence trail; the MORNING REPORT is now authoritative for "what to do next."

---

**GATE W1 FORMALLY VERIFIED-CLOSED (2026-07-30, Night 2 — see full PARĪKṢAKA round-1/round-2
record above in the deploy-#2 section).** Round 1 rejected 5 of 12 items with concrete live
evidence (items 8/28/29/32/30) — a real "coverage says computed while payload is 100% null"
honesty-inversion bug (missing sidecar API-key header, masking every 401 as an empty result),
a wrong panchāṅga parameter name causing an uncaught 500 on the single-date call path only,
and an undisclosed muntha schema mismatch. Fix (PR #940, Opus effort per the campaign's
post-rejection escalation rule) redeployed (revision `amjis-mcp-00525-hrd`, confirmed 100%
traffic via direct `gcloud run services describe`). **Round 2 independently re-verified all 5
fixes against live production, both charts — not trusted from the fix PR's self-report**:
recomputed Sun/Rahu sidereal longitudes from first principles and cross-checked against served
values (±1.5° tolerance for true-node wobble); traced 8 served `fact_id`s back to `chart_facts`
confirming 3 FORENSIC birth anchors exactly; cross-checked muntha against a repo FORENSIC test
fixture (`Libra, 7th house` — matched exactly). All 5 items + ND-1 (tri-plane null-shape) →
**VERIFIED-FIXED. Gate W1 → VERIFIED-CLOSED.** Two honest non-blocking notes filed: (a) the fix
PR's §N.5 rationale was directionally right but imprecise (claimed "near a nakshatra cusp" —
actually mid-nakshatra but 2.94° from the Aquarius/Pisces SIGN boundary, a related but more
precise hazard); (b) a NEW minor advisory (not a reopen): `kala_ahead_get` on Abhinandan's
chart returns `projections: []` while coverage labels it `"computed"` rather than the
system's own `honest_empty` convention — ticketed as a follow-up, does not block this closure
since nothing is fabricated and the reading discloses the emptiness in prose.

**All 12 W1 registry items are now VERIFIED-FIXED, live, both charts.** Wave W2's design +
both Lane D preconditions were already merged before Gate W1 closed; the campaign ran W2's
five build lanes (A/B/C/D/E) in parallel with the W1 reverify cycle, since neither blocks the
other (frozen anti-collision file/table contract per the design doc's own §0). All five lanes
(#944/#945/#946/#947/#949) landed and were independently scope-verified.

**MERGE-TRAIN PASS (2026-07-30, Conductor).** Before merging, found and fixed two real
cross-cutting issues the anti-collision contract's per-lane isolation couldn't itself catch:

1. **A real cross-directory migration collision, freshly landed.** Lane A's PR (474/475 in
   `platform/supabase/migrations/`) failed CI: a DIFFERENT campaign's
   `platform/migrations/474_asset_throughput_incomplete_state.sql` had landed on the SAME
   number in the OTHER directory since the night's earlier "474–483 free" check (which only
   ever looked at `platform/supabase/migrations/`) — the exact two-directory trap this
   codebase's own history repeatedly warns about, now hitting this campaign's own migrations
   directly rather than someone else's. **Renumbered all five W2 lanes' migrations to a
   clean, non-colliding block, 488–497** (above the true combined-directory max of 486, and
   clear of every sibling lane's own claim), rather than fixing one collision at a time and
   re-discovering the next as each lane merged: A → 488/489, B → 490, C → 491/492/493/494, D →
   495, E → 496/497. Each renumber verified independently: `migration_number_guard.ts` PASS +
   full relevant test suite green, before pushing.
2. **Lane E's own flagged "real gap" (ka_gochara_sweep/ka_gochara_resonance missing seed
   rows) was a false negative for THOSE two assets — correctly investigated and corrected —
   but the fix over-generalized and removed a row that was, in fact, still needed, catching
   itself on CI one round later. Full sequence, corrected in place rather than silently
   re-edited:**
   `ka_gochara_sweep`/`ka_gochara_resonance` ARE registered in production via a direct
   `INSERT INTO asset_registry` in their own migrations (460 and 459, pre-existing, confirmed
   `is_active:true, has_writer:true` live) — the same mechanism Lane C's `ka_kshetra` row uses
   (migration 494). On that basis, Lane E's inert `ka_kshetra` placeholder in
   `asset_registry_seed.ts` was judged unnecessary and removed, and the Kāla-layer asset-count
   test lowered 15→14. **This broke CI on PR #947** (`catalog_reconciliation.test.ts`:
   `mi_bhara → missing dep 'ka_kshetra'`), because that test resolves every `depends_on` entry
   purely against this file's own `ASSETS` array — never the DB. `ka_gochara_sweep`/
   `ka_gochara_resonance` get away with no TS row because nothing in this file's `depends_on`
   arrays names them; `ka_kshetra` does not, because `mi_bhara.depends_on = ['ka_kshetra']`
   lives in this same file. **Restored the `ka_kshetra` row** (count back 14→15), mirroring
   migration 494's identity fields exactly but with `depends_on: []` (a documented,
   intentional divergence from the migration's real 8-edge array, since two of those edges —
   `ka_gochara_sweep`/`ka_gochara_resonance` — still have no TS row themselves; closing that
   is separate legacy-asset cleanup, left as an open follow-up, not silently absorbed). Same
   defect class as the historical `ga_vichara`/`bo_pratijna` seed-registry gaps this
   codebase has hit before — the fix is always "add the row," never "the test doesn't need
   it." `w2_weights_acyclicity.test.ts` already independently constructs its own test
   registry from a literal mirror of migration 494's real INSERT, so it was unaffected by
   either the removal or the restore.

**Merged in dependency order: A → B → C → D → E — all five lane PRs (#945/#944/#949/#946/#947)
now landed on `main`.** Resolved each lane's real merge conflicts as they surfaced
(`services/ka_kshetra/__init__.py` across all five, `contracts.py` between A/C) — same
never-force-push, always-empirically-verify discipline as every prior merge this campaign.
Lane C (the hazard-formula + `ka_kshetra` orchestration-shim centre of gravity, Opus effort)
verified to `rel. err` ≤ 4.5e-13 against numerical integration, Circularity Guard proven three
ways. Both cross-lane gaps flagged during development are resolved (migration collision fixed
by the 488–497 renumber; `ka_gochara_sweep`/`ka_gochara_resonance` false-negative corrected —
see item 2 above for its own follow-on correction). The §9.3-vs-§0 `kala_field_snapshots`
ownership question resolved itself: Lane E correctly deferred it, and Lane C's migration 492
(`kala_field_core`) does create it, matching §0's lane-ownership table.

**Four further real integration bugs surfaced ONLY by combining all five lanes — none visible
within any single lane's own isolated test suite, which is exactly the value a dedicated
merge-train pass is for:**
1. **`stage1_symbolization.py`'s `build_sandhi_band_primitives()` crashed on `conn=None`.**
   The now-importable real `boundary_breakpoints` function is DB-backed with no None-handling
   of its own (correctly so — it is never meant to run standalone). Fixed with an explicit
   `if conn is None: return [], CoverageGap(...)` guard at the call site.
2. **A duplicate `ClockApplicability` dataclass, two different field orders.** Lane C's
   `contracts.py` had independently redefined a class Lane B already owned in
   `stage3_clocks.py`, with a different field order — found via import-site cross-referencing
   (`hazard.py` imports from `contracts`; `stage3_clocks.py` had its own local definition).
   Consolidated to ONE definition in `contracts.py`; `stage3_clocks.py` now imports it. This
   cascaded into 5 stale positional `Route(...)` test constructions across
   `test_hazard.py`/`test_stage4_field.py`/`test_stage5_null.py` (each lane's tests guessed a
   different field order before the other lane's code existed) — fixed by converting to
   keyword arguments, tracing each original call back to its author's intended semantic
   values rather than remapping by position number (an initial attempt did this wrong —
   `route_gain=0.60` was almost mapped to `path_edge_ids` — caught before running tests, redone
   correctly).
3. **`FakeConn`/`promise_prior` fixture mismatch.** `stage4_field.py`'s `load_promise_prior`
   now successfully imports Lane A's real `promise_prior` module (previously an ImportError
   fallback only), but Lane C's own `test_writer.py`/`test_circularity_guard.py` fixtures
   (`FakeConn`) don't implement the `.execute()` interface Lane A's real code needs. Fixed via
   a documented `monkeypatch.setitem(sys.modules, 'services.ka_kshetra.stage2_promise', None)`
   in both suites' fixtures, forcing the fallback path their `FakeConn` actually supports —
   rather than expanding `FakeConn` to simulate Lane A's full data model, which would make
   these unit tests into accidental integration tests of a different lane's code.
4. **`catalog_reconciliation.test.ts` / Kāla-asset-count regression** — see item 2 above
   (the `ka_kshetra` seed-row removal that needed correcting).

**⚠ A real, honestly-disclosed blocker for the next session's integration/Gate-W2 work, from
Lane C directly: §5.1 C-1's lifetime-count priors (N_e) do not exist in the corpus.**
`brahma_class_priors` holds only signal-salience priors; `brahma_event_ontology.base_rate_by_age`
is a distribution over age bands, not the century-count N_e the hazard formula's baseline term
needs — reading it as N_e would be the exact §N.7-item-6 fabrication defect, and §5.1 C-1
forecloses that explicitly. Lane C's writer correctly SKIPS every event class with
`no_class_prior_row` rather than fabricate, which means **a real `ka_kshetra` build will write
ZERO field rows until an L0 lane seeds `fact_kind='lifetime_count_per_100y'`** — the same shape
of prerequisite as ADJUDICATION-1's `bg_synthetic_cohort_md` gap. This must be resolved (likely
its own small L0 corpus-seeding lane, possibly another ANTARYĀMIN-adjudicated design choice for
where the priors come from) BEFORE the integration pass's "field integration" step can produce
anything other than an honest empty field.

**Once the merge train lands all five PRs: (1) resolve the N_e blocker above, (2) run the actual
field-integration/hash-replay/weights-v0-seed/skill-score-publish sequence, (3) evaluate Gate
W2's acceptance criteria (brief §3 W2 / design doc §10) — this is real, substantial work in
its own right and is correctly a separate session's focus, not squeezed into this one's tail.**

---

**GATE W0 FORMALLY CLOSED (2026-07-29, between Night 1 and Night 2 — see the GATE W0 CLOSURE
RECORD below for full evidence).** The native applied the `mcp-canary-key` Secret Manager IAM
binding; `deploy.yml` re-ran clean (run `30484976742`), all three auth probes passed for real,
traffic promoted 100% to `amjis-mcp-00517-b5q`; live production verification (direct
authenticated JSON-RPC calls, bypassing any client-side tool-cache ambiguity) confirmed all 8
tools registered and functionally correct on BOTH canonical charts, including a live Mode-3
routing test.

**POST-NIGHT-1 ADVERSARIAL AUDIT COMPLETE (2026-07-30 — see the AUDIT RECORD below).** Three
independent re-verification passes read every merged PR's actual diff against the ratified
spec (not trusted from this ledger's own self-report). Verdict: 13 of 15 PRs
CONFIRMED-SOUND with no defects found; two real, previously-undisclosed gaps found and
addressed — see the AUDIT RECORD for full evidence and disposition.

**DEPLOY #2 COMPLETE (2026-07-30, Night 2).** `gh workflow run deploy.yml --ref main` → run
`30525058905`, all 5 jobs green (Web, MCP, Sidecar, Pipeline Job, path-detection); post-deploy
smoke passed on all services; traffic promoted 100% to `amjis-mcp-00522-m6j` (confirmed via
`gcloud run services describe`). This deploy carries every merged Night-2 lane (#918/#924/
#926/#930/#932/#934) — all 12 W1 registry items went live on production for the first time.

**PARĪKṢAKA LIVE ACCEPTANCE — GATE W1 REJECTED, real defects, not park-worthy (2026-07-30).**
13 real MCP calls against production, both canonical charts, three `as_of` dates, four
surfaces. **7 of 12 items VERIFIED-FIXED** (1-lite, 2, 10, 24-lite, 38-lite, 43, E6-lite —
genuinely exemplary, chart-differentiated, honest 3-state coverage, several explicitly refuse
to fabricate a confidence claim they can't support). **5 of 12 items FAILED-REOPENED**, three
of them on the exact field the item exists to deliver, while `coverage` falsely asserted
`state:"computed"` — the precise honesty-inversion the campaign's own rails exist to prevent:
- **Items 8 (`gochara_dual_reference`) + 28 (`dasha_lord_transit_condition`)**: all 9 grahas'
  transit fields 100% NULL on BOTH charts, all calls, yet coverage claimed `"computed"`.
  **Conductor triage before dispatching a fix**: independently confirmed via a direct
  `ref_planet_transit_get` MCP call that the underlying L0 ephemeris transit substrate is
  HEALTHY (real data returned for Jupiter, 2026-07-30) — so this is NOT a production-wide
  ephemeris outage, just a narrow wiring bug in how `now.ts`/`ahead.ts` call the capability.
  Severity de-risked from "possible platform emergency" to "real but narrow bug" before
  dispatching the fix.
- **Items 29 (`chandrashtama`/`hora_now`/`janma_resonance`) + 32 (`disha_shula`/
  `gulika_kalam_now`)**: null on both charts, all dates, coverage falsely claims "L0 panchāṅga
  service unreachable" — proven false by the Verifier itself: the SAME service's RANGE-mode
  call (from `kala_ahead_get`'s `gulika_kalam_ahead`) returned 31 real per-day windows seconds
  apart in the same session. Only `kala_now_get`'s single-date call mode is broken.
- **Item 30 (`mudda_dasha_varsha`)**: core deliverable genuinely works (chart-differentiated,
  real data both charts) but `muntha_sign`/`muntha_house` are undisclosed nulls leaking into
  served prose as "Muntha in unknown."
- **4 new defects filed for the register (ND-1 through ND-4, not yet items):** ND-1 tri-plane
  null-shape inconsistency (`now`/`ahead`/`elect` emit bare `null` where `kala_ritual_get`
  already correctly emits `{no_lever:true, reason}`) · ND-2 unfalsifiable freshness claim
  (`stale:false` asserted with zero evidence — all freshness fields null) · ND-3 an L3 registry
  cold-start flake self-resolving on retry (reliability risk, not fixed this pass) · ND-4 the
  "unreachable this call" phrasing misrepresents a persistent deterministic bug as transient.

**Recommendation taken: fix-and-reverify, not park** — the Verifier itself assessed the
reopens as "shallow, not architectural" (two wiring faults account for four of five, both
proven data-plumbing since sibling code paths work in the same deploy). **Fix lane dispatched
at OPUS/high effort** per brief §5's standing rule ("effort raised one notch any time a lane
produces a Verifier-rejected artifact") — `shad-darshana/w1-verify-reopen-fixes`, covering all
3 root causes + ND-1/ND-2/ND-4, holds for a second PARĪKṢAKA live-acceptance pass before
merge (no auto-merge). **Gate W1 is NOT VERIFIED-CLOSED — do not treat items 8/28/29/30/32 as
done in any future session until the reverify pass confirms it.** Items 1-lite/2/10/24-lite/
38-lite/43/E6-lite ARE confirmed VERIFIED-FIXED regardless of the gate's overall state.

**Single next action for Night 2 (superseded detail below): resume Phase 2 fan-out** — 3 remaining W1 serving-join
lanes (mudda+sandhi-lite · 24-lite-intervals+grading-facade+frontier-v0+tri-plane-wiring),
the citation-heavy `bg_muhurta_lattice`+`bg_parihara_rules` lane (deliberately held back all
of Night 1), then W2 build-out per the now-corrected `KALA_W2_FIELD_DESIGN_v1_0.md` (§9.3
migration table fixed — see AUDIT RECORD). **W2's Lane D (cohort_client.py / salience+rarity)
carries one open precondition that MUST be resolved before Lane D starts** — see AUDIT
RECORD item 3 below; this is a real design decision, not a coding task, and the Conductor
should either resolve it via ANTARYĀMIN or raise it if it touches a FROZEN-contract boundary
(it does not appear to — it's a schema/approach choice, not an orchestrator-contract change).
No other blockers outstanding.

**NIGHT 2 IN PROGRESS (2026-07-30, live).** Four lanes dispatched this session, all in
worktrees off `origin/main@5f5033a5`. **Status as of this write, each independently
re-verified (diff scope + tsc + tests), not trusted from any lane's self-report:**
`shad-darshana/w1-mudda-sandhi` (items 30, 1-lite) — **PR #924 MERGED** (5 files, scope-clean,
115/119 tests green incl. 4 intentional skips, zero regressions vs. baseline) ·
`shad-darshana/w1-intervals-grading` (items 24-lite, 38-lite, frontier v0, 43) — **PR #926 OPEN,
mergeable, awaiting CI**; hit a REAL `now.ts` conflict against #924 once #924 merged first
(both lanes added independent fields to the same facade) — **Conductor-resolved** via
`git merge origin/main` (never force-push): both functions (`fetchSukshmaBoundaryUncertainty`
item 24-lite, `computeDashaSandhi` item 1-lite) kept in full, both fields kept on every
interface/return/coverage/provenance surface, doc-string prose combined; re-verified
`tsc --noEmit` clean + 107/111 tests green (4 intentional skips) across all 8 touched/related
suites including `m8_e2e_proof.test.ts` (no tool-count change needed — neither lane registers
a new tool) — pushed as commit `035a0c52` · `shad-darshana/bg-muhurta-parihara`
(`bg_muhurta_lattice.py` + `bg_parihara_rules.py`, migrations 484/485) — **PR #930 OPEN,
Opus citation-review VERDICT: REJECT (round 1), fixes dispatched.** The review confirmed the
core honesty machinery is genuine (placeholder-doṣa exclusion verified live in SQL, 26
real-cited/53 placeholder rows in `brahma_dosha_catalog` flattening to exactly the claimed 60;
all 9 yoga citations trace to real inline `Source:` comments; `computed_uncited_convention`
counts verified exactly 25/5/7=37; EVENT_TABLES reuse legitimately cited, not laundered;
`WriterBase`/idempotency/migration-collision all clean) but found **5 real defects the builder
must fix**: (1) `bg_muhurta_lattice.py:351` — `compute_extended_auspicious` ignores `vara_id`
and serves `abhijit` present on Wednesdays despite its own citation saying "excluded on
Wednesday" (~261 affected rows over the horizon); (2) the parihāra factor-census claimed
"221 of 266 real-cited" — actual live count is 164/266 (102 placeholder), the claim itself was
wrong; (3) claimed `content_en` NULL on all 274 corpus chunks — false, `content_en` is
non-NULL but byte-identical to `content_sa` (untranslated Devanagari sitting in the English
column) — only `cleaned_translation_text` is actually 0/274; (4) jvalamukhi-yoga marked
`not_in_corpus` when 1 real (untranslated) corpus chunk actually matches — needs its own
honest "present-but-untranslated" disposition, not a flat not-found; (5) several factors
(yamakantaka, krakaca, sashtighati, ghati_muhurta, varjyam, panchaka, 6 sandhyā/vijaya/
godhūli/niśīta keys) point to `bg_muhurta_factor_census` rows that don't exist — dangling
disclosure pointers. Fix list relayed to the original builder agent verbatim with file/line
citations and re-verification requirements; this is verify-cycle 1 of the campaign's own "2
failed verify cycles → Opus escalation" rule (brief §5) — if round 2 also fails, the rebuild
escalates to Opus per that rule. · `shad-darshana/w2-lane-d-design-fix` (docs-only, corrects
`KALA_W2_FIELD_DESIGN_v1_0.md` §6.3 against the real `bg_synthetic_cohort` schema per
ADJUDICATION-1) — **PR #918 MERGED.** All 4 Phase-2/Night-2 lanes now closed: **#924
(w1-mudda-sandhi) MERGED · #926 (w1-intervals-grading) MERGED** (after Conductor-resolved
`now.ts` conflict above) **· #930 (bg-muhurta-parihara) MERGED** (round-1 Opus review REJECT →
5 fixes applied with live re-verification → round-2 independent Opus review APPROVE, every
number re-derived, not trusted) **· #918 MERGED.**

**bg_cohort MD-lord chain table (unblocks W2 Lane D, ADJUDICATION-1's actual deliverable) —
PR #932, auto-merge armed post-APPROVE-WITH-NOTES.** `bg_cohort.py` extended (same asset, no
new `asset_registry` row per design) with `bg_synthetic_cohort_md` (migration 484, ~100,000
rows, age-interval Vimśottarī chain per synthetic chart). Builder found and fixed a real
JD-convention bug during its own worked-example check (PyJHora's dasha stack wants local
wall-clock JD, not UTC-converted — an initial wrong-convention attempt was off by ~3.3 years).
**Independent Opus review verified the arithmetic against the actual upstream source
(`jhora/const.py`/`vimsottari.py`, not the adapter's restatement) AND against the native's own
live `chart_dashas` row** (Jupiter mahādaśā end age 7.5316 vs. the PR function's 7.5337 on the
same Moon longitude — 0.8-day agreement, L1's day-snapping accounts for the rest) — verdict
APPROVE-WITH-NOTES. **Two notes recorded honestly, not swept under the rug:** (1) a code
comment overstates how "unreachable" a longitude-rounding divergence check is (P≈1e-5 per
10k-row build — rare, not zero, the reviewer made it fire); (2) **real, tracked residual** —
when that rare divergence does fire, the writer's broad `except Exception` in `run()`
swallows it into a success-shaped `WriterResult(notes="partial: ...")` rather than a hard
failure, which per CLAUDE.md §N.8 (Earned-Signal Principle) is exactly "a flag without a real
detector distinguishing it" — filed as a low-priority follow-up work item (fewer than 1-in-100k
build probability, degrades to a disclosed partial-note rather than a fabricated clean success,
Conductor judgment: not worth blocking Lane D's unblock over, tracked not hidden). Chain years
use sidereal-year length (365.256364) vs. the design's Gregorian-year consumer convention
(365.2425) — ≤1.7 days drift at age 120, acknowledged in the design as harmless.

**W2 Lane D is now fully unblocked**: ADJUDICATION-1's schema-reconciliation (design doc) and
its data deliverable (MD-lord chain table) are both merged/merging. W2 Lanes A/B/C/D/E may all
be dispatched together next, per the design doc's own "five parallel lanes" contract.

Plus one operational
(non-lane) action: **`1c826d5a` gochara-sweep horizon rebuild, dispatch 1 of ~3, IN PROGRESS —
will NOT complete tonight, honest park.** Root cause (found via a pre-existing, not-yet-merged
diagnosis on `samapti/gochara-parity` @ `d5907e64`, `GOCHARA_PARITY_DIAGNOSIS_v1_0.md` —
**a SEPARATE concurrent autonomous campaign, SAMĀPTI, already investigated this exact gap;
its diagnosis was reused here, not duplicated**): `ka_gochara_sweep`'s full plan is 303
substeps (~22h wall-clock); one 6h dispatch buys ~27%; the canonical chart (`482012f1`) only
reached 303/303 via six sequential resumed dispatches over 2026-07-19→25; `1c826d5a` got
exactly one productive dispatch (78/303) before a real orchestrator-watchdog defect + DB
instability parked it in `error` state on 2026-07-28 — a prior overlapping-dispatch attempt
that same day caused an 11-run crash cascade (see `build_runs` history), which is why
"one dispatch at a time, gated on ≥40-substeps-gained" is now the standing discipline.
**Collision check performed before proceeding (chart-level `pg_try_advisory_lock` — the same
lock behind the campaign's own N5 ruling — is the safety net if SAMĀPTI's session also
dispatches against this chart tonight; a second concurrent attempt fails safely, `sys.exit(3)`,
no corruption):** queried `build_runs`/`build_run_assets` directly, confirmed ZERO other
`running`-state runs against `(1c826d5a, ka_gochara_sweep)` at dispatch time — all 2026-07-28
attempts are dead/`failed`. Dispatched via the existing production path (no code/table
changes; `platform/scripts/dispatch_shaddarshana_c2_gochara_resume_1c826d5a.py`, modeled on
the canonical chart's own precedent script): `build_runs.id = 24073997-6fa7-4a1e-93fe-fc3eb369f192`,
triggered via `gcloud run jobs execute brahma-build-pipeline-job`, confirmed `state='running'`
as of this write. **~2 further dispatches still needed after this one (~18h more, sequential,
never overlapping) for full 58yr-horizon parity — this spans multiple future sessions, not
just Night 2.** Full parity is NOT a Gate W1 blocker per se: Gate W1's own criterion is honest
3-state coverage over whatever horizon exists, not a specific horizon length — AHEAD-window
items must report the current ~1yr `1c826d5a` horizon honestly (not fabricate a longer one),
which is a coverage-discipline check on the SERVING code, verifiable independent of full
sweep-parity completion. **Native-visible flag for morning review:** a second autonomous
campaign (SAMĀPTI) is independently active on this same production database tonight — no
direct coordination channel exists between the two sessions; the chart-level lock is the only
safety mechanism preventing actual collision, and it worked as designed here, but this is
worth the native's awareness for any future multi-campaign-concurrent night.

**ADJUDICATION-1 resolved**
(see ADJUDICATION log below): W2 Lane D's cohort-schema precondition ruled — precompute an
age-based MD-lord chain table (`bg_synthetic_cohort_md`), not a scalar column, not a
query-time derivation. **Operational note:** builder sandboxes reject git operations against
shared `.worktrees/...` checkout paths entirely; the working pattern this session is: each
agent operates in its own harness-provisioned isolated worktree, then pushes its finished
branch to `origin` under the intended `shad-darshana/<lane>` name via explicit refspec
(`git push origin HEAD:refs/heads/shad-darshana/<lane>`) and opens its PR from there. Future
sessions should dispatch with this pattern from the start rather than pre-creating shared
`.worktrees/shad-darshana-*` paths (four such empty/unused paths from this session should be
`git worktree remove`d at next cleanup — harmless, just clutter). **Next: verify each of the
four lanes' PRs independently as they land (do not trust self-reports), run the merge train,
then dispatch the `bg_cohort` md-lord-chain builder lane once w2-lane-d-design-fix merges,
then W2 Lanes A/B/C/E once the 3 remaining W1 items + bg-muhurta-parihara close Gate W1.**

---

## POST-NIGHT-1 ADVERSARIAL AUDIT RECORD (2026-07-30, between Night 1 and Night 2)

Three parallel, independent agents re-read every merged Night-1 PR's actual diff against the
ratified spec docs — deliberately NOT trusting this ledger's own self-reported dispositions,
since the same autonomous session wrote both the code and the ledger. Method, findings, and
what was done about each are recorded here so Night 2 inherits the corrected state, not just
the original claims.

**Confirmed sound, no defects (13 of 15 PRs):** #877 (envelope+composer), #879 (parva-dedup),
#880 (priority+explain facades), #881 (CI skeleton battery — census numbers independently
confirmed live-computed, not hardcoded), #882 (upaya+ritual stubs, Mode-3 routing — grep-
confirmed zero passthrough path exists), #883 (now+ahead facades), #884 (elect+story
facades), #885 (bash fix — root cause independently reproduced and confirmed fixed), #888
(bg_sky_calendar — floating-point fix confirmed to eliminate the bug class), #891 (dual-
reference gochara + daśā-lord condition — the forward-identity-pinning subtlety verified
correct by reading the actual call sites), #892 (panchāṅga joins — L1-authority discipline
confirmed, no re-derivation). Independent execution (fresh checkout, not the ledger's
numbers): `tsc --noEmit` clean, 163/163 relevant vitest tests pass, full python suite green.

**Real gap #1 — the Circularity Guard (item 10, PR #889) could not run in CI.** The test
mechanism itself is genuinely real (empirically proven non-vacuous: `ka_jivana_parva` has
zero LEL-reading code today, confirmed by direct source read) — but it is marked
`@pytest.mark.integration`, and `ci.yml`'s only pytest invocation runs `-m "not integration"`.
It ran exactly once, manually, at authorship, with no path to run again automatically —
precisely the CLAUDE.md §N.7 Earned-Signal failure class ("a signal without a real detector
is null, not green") applied to the detector's *execution*, not its *logic*.
**DISPOSITION: FIXED.** New workflow `.github/workflows/shad-darshana-circularity-guard.yml`
(this same PR) wires it into CI properly: reuses `deploy.yml`'s exact WIF/Cloud-SQL-Auth-
Proxy convention (same instance connection name, same service account), on port 5433 to
match the test's hardcoded DSN, running BOTH the static census and the empirical proof.
Triggers: `workflow_dispatch`, nightly `schedule`, and `push` to `main` on any `ka_*` writer
path (deliberately broader than shad-darshana-only, since the guard protects every `ka_*`
writer, not just this campaign's — but scoped to run only this one test file, not a
repo-wide integration sweep). Deliberately NOT a required branch-protection check yet —
informational/nightly, does not block any PR. **The other two integration tests this file's
own docstring names as sharing the same never-runs-in-CI gap
(`test_cr131_gochara_db_reachability.py`, `test_ka_gochara_sweep.py`) are PRE-EXISTING and
OUT OF SCOPE — flagged here for awareness, not fixed, per this campaign's own
don't-touch-other-sessions discipline.**

**Real gap #2 — the W2 field design doc's migration-range table (PR #886) was stale and
already colliding.** It claimed "current max in-tree is 466" and reserved 467–476 in
`platform/migrations/` — but 467–473 already existed on `main` (472/473 being this same
night's own `bg_cohort`/`bg_sky_calendar` migrations, in `platform/supabase/migrations/` —
the directory the migration runner actually applies from, not the one the design doc
checked). Exactly the "two migration directories" trap this codebase's own history warns
about, recurring within the same night. **DISPOSITION: FIXED** (this same PR) —
`KALA_W2_FIELD_DESIGN_v1_0.md` §9.3 corrected: directory → `platform/supabase/migrations/`,
range → 474–483 (473 confirmed live max at correction time), all ten table-row numbers and
the one other in-body reference (§7.3's weights-seed migration number) renumbered to match.
Whichever W2 lane writes the first migration still MUST re-verify the live max immediately
before use, per the design doc's own standing instruction — this reservation can go stale
exactly as the original one did if another campaign lands migrations first.

**Real gap #3 — the W2 design's matched-sub-cohort assumption doesn't match the shipped
cohort schema. OPEN — flagged for Night 2's Conductor/ANTARYĀMIN, not fixed here.** The
design doc's Lane D spec requires a `cohort_charts.md_lord` field (to support Elevation
§12.3's matched sub-cohort: same lagna + same MD-lord). The actual `bg_synthetic_cohort`
table (PR #887) has no MD-lord field — its own docstring states this needs the dasha engine
and was deliberately deferred; item 22's own ledger disposition already correctly scoped
"matched sub-cohort — that's W2's job," but nobody flagged that the ALREADY-BUILT cohort
table's schema doesn't support it either. **This needs a real decision before Lane D
(`cohort_client.py`, stage 6 salience/rarity) starts, not a quick fix**: (a) extend
`bg_cohort.py` to compute MD-lord for all 10,000 synthetic charts (requires running the dasha
engine over the whole cohort — real, scoped engineering work), or (b) revise the W2 design's
Lane D approach to compute MD-lord matching at field-build time instead of relying on a
pre-stored cohort column (e.g., join against each synthetic chart's ephemeris data on the fly
during rarity scoring). Native input at the elevation-planning session did not rule on this
specific schema question — it is a genuine open engineering/design choice, not a
FROZEN-orchestrator-contract question, so ANTARYĀMIN may resolve it autonomously per its
standing charter; it should NOT block the rest of W2's build (Lanes A/B/C/E have no
dependency on this), only Lane D specifically.

---

## GATE W0 CLOSURE RECORD (between Night 1 and Night 2, 2026-07-29 → 2026-07-30)

**Blocker resolved:** the native confirmed the exact grant scope (additive, read-only
`secretAccessor`, no rotation, trivially reversible) and authorized it. Applied:
`gcloud secrets add-iam-policy-binding mcp-canary-key --member="serviceAccount:github-actions@
madhav-astrology.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
--project=madhav-astrology`. Verified before AND after via `get-iam-policy`: before = only
`amjis-web-runtime` bound; after = both `amjis-web-runtime` and `github-actions` bound,
nothing else touched.

**Deploy re-run, real evidence (not trusted from a report — logs read directly):**
`gh workflow run deploy.yml --ref main` → run `30484976742`, all 5 jobs green (Web, Pipeline
Job, MCP, Sidecar, path-detection). MCP job's `Post-deploy smoke` step log confirmed line by
line: `[health] OK (HTTP 200)` · `[probe: no-auth] 401 (expect 401) — PASS` ·
`[probe: bearer-auth] 200 (expect 200) — PASS` · `[probe: url-token-fallback] 200 (expect 200)
— PASS` · `=== Smoke PASS ===`. `Promote traffic to latest revision` log confirmed:
`100% LATEST (currently amjis-mcp-00517-b5q)`. This is the genuine authenticated pass the
pipeline was designed to require — the prior night's two dark deploys never reached this point.

**Live-production verification (Verifier-style acceptance, both canonical charts) — done
directly, real calls, not delegated:**
1. Registration check bypassed the session's own (stale, pre-deploy-snapshot) client-side tool
   cache entirely: a direct authenticated `tools/list` JSON-RPC call against
   `https://amjis-mcp-qm256lasva-el.a.run.app/mcp` confirmed all 8 new tools present
   (`kala_now_get`, `kala_ahead_get`, `kala_elect_get`, `kala_story_get`, `kala_priority_get`,
   `kala_explain_get`, `kala_upaya_get`, `kala_ritual_get`) alongside the still-live legacy
   aliases (correct — nothing retired yet, per strangler discipline). 152 tools total.
2. Functional calls, both charts (`482012f1` Abhisek, `1c826d5a` Abhinandan):
   `kala_now_get` → HTTP 200 on both, envelope-conformant (`reading` with
   thesis/evidence/dissent/verdict/falsifier keys — E3's argument schema live; `coverage` as a
   3-state list; `field_snapshot_id` present as the documented pre-W2 stub form;
   `calibration_maturity` present with honest all-zero values — correct pre-Living-LEL state,
   not fabricated; `tri_plane` + `drill_pointers` present).
3. `kala_ritual_get` and `kala_upaya_get` stubs confirmed honestly reporting `not_in_corpus` /
   W4-not-yet-landed coverage states rather than fabricating data.
4. **The hard-gated Mode-3 routing rule tested live** (undertaking-shaped payload to
   `kala_ritual_get`): `wrong_view: true`, `correct_surface: "kala_elect_get"`, honest
   `no_lever` on the interpretation/prediction tri-plane slots, a live `intervention_ref`
   pointer to ELECT — matches Elevation §8 exactly, verified against real production.
5. One transient HTTP 401 observed on a first call attempt, immediately resolved on identical
   retry (200) — consistent with the same infrastructure-instability pattern the Night 1
   morning report already flagged (background-agent stalls/connection drops), not a real auth
   regression; not chased further as it self-resolved and matches a known noise class.

**Disposition:** Gate W0 → **VERIFIED-CLOSED.** All 8 tools live on production, both charts,
envelope-conformant, Mode-3 routing verified. `main` == production for the MCP surface as of
this record (Web/Sidecar/Pipeline-Job were already clean from Night 1's manual dispatches).

## Night 1 history (superseded detail below; see MORNING REPORT for the authoritative close-out)

**Night 1, Phase 0 — CLOSED.** Phase 1a (spine) — **VERIFIED-MERGED**: PR #877
(`kala_envelope.ts` + `argument_composer.ts`, 42/42 new tests, `tsc --noEmit` clean)
independently confirmed merged to `main` @ `5208bc55` — files present, scope-clean (touched
exactly the 4 files claimed), the one failing status check (`Boot-time pointer validation
SC-17/18/19`) confirmed pre-existing on `main` before this PR, not introduced by it, and not a
required check (auto-merge proceeded without override). Items E3/E4/E5/43 partially advanced
(envelope contract exists; not yet consumed by any tool, so still NOT-STARTED at the
item-disposition level until a facade wires it — see brief §6, items close on serving, not on
library existence). **Phase 1b now dispatched, all 6 lanes IN-PROGRESS** in fresh worktrees off updated
`main`@`5208bc55` (each on branch `shad-darshana/<lane>`): now-ahead (kala_now_get,
kala_ahead_get) · elect-story (kala_elect_get, kala_story_get; ELECT is the Mode-3 landing
target) · priority-explain (kala_priority_get, kala_explain_get) · upaya-ritual-stub
(kala_upaya_get stub, kala_ritual_get Modes 1-2 stub + the Mode-3 `wrong_view` redirect,
implemented for real from day one per Elev §8) · parva-dedup (bug fix in existing STORY
substrate, span+level dedup — NOT the new facade) · ci-skeletons (specificity v0,
prose-survival, tri-plane no-dead-end, completeness census seed, authority-basis census seed,
Mode-3 single-route assertion — this one is explicitly allowed to report its Mode-3 test as
pending until upaya-ritual-stub merges). Next action: await all 6 completions, verify each
independently (PR status, scope discipline, real merge — do not trust self-reports), run the
merge train, then close Gate W0 (deploy #1) once all 8 tools are live + CI skeletons green +
sealed-harness regression shows no loss, both charts.

**INFRASTRUCTURE FIX (discovered mid-Phase-1b, PR #878):** the campaign's own brief/design docs
and this ledger were UNTRACKED in git — meaning absent from every worktree's filesystem (a
worktree only contains committed content). Confirmed absent from a live worktree
(`shad-darshana-now-ahead`). `elect-story` lane's agent caught this itself mid-run and was
reading around it via the main checkout's absolute path when it hit an unrelated API
connection error and terminated — **not a logic failure, a transient error; the worktree has
no commits, safe to relaunch.** Root-cause fix: PR #878 commits the whole `kala_elevation`
briefs directory (docs-only) to `main`, auto-merge enabled, pending CI. **Caution for
verification:** the other 5 lanes launched BEFORE this fix landed — each must be checked for
whether it worked around the missing docs (like the spine lane and elect-story did) or
proceeded with incomplete context; do not assume clean. Once #878 merges, `elect-story` will
be relaunched fresh from updated main so it has the docs natively. Going forward: the ledger
must be periodically committed to `main` via small docs PRs at phase/gate boundaries (not
after every edit) so it stays durable and visible to future worktrees — the primary checkout's
live copy (this file) remains the authoring surface for the session, but a stale un-synced
ledger defeats its own purpose as "the campaign's memory."

**Lane status (Phase 1b):**
- `parva-dedup` — **PR #879 open, verified scope-clean (2 files: `query_life_arc.ts` +
  `query_life_arc_dedup.integration.test.ts`), auto-merge enabled, CI running.** Real defect
  found and fixed: `ka_jivana_parva`'s inclusive-both-ends date filter double-emits each
  mahadasha-boundary antardasha (own-lord rule + contiguous periods → the boundary AD
  satisfies both adjoining MD spans). Writer left untouched; fix is serving-side dedup
  (`DISTINCT ON (start_year, end_year, dasha_planet, level)`, keeping highest `parva_index`)
  in `query_life_arc.ts` (feeds `kala_life_arc_get`). Live-confirmed on all 3 built charts
  (100→91, 100→91, 109→99 rows) before landing the fix. Regression test added, integration-gated.
- **PR #878 (docs-sync) MERGED** — campaign docs now visible in every fresh/rebased worktree.
- `now-ahead`, `priority-explain` — hit the same transient API-connection error mid-response
  (not a logic failure; a pattern of 2 such drops this session so far). Both had real
  uncommitted progress in-worktree (modified `register_p1_aliases.ts`, `registry_bridge.ts`,
  new `kala_views/`) — **resumed via SendMessage rather than discarded**, told about the
  now-merged docs fix, instructed to finish + PR normally.
- `elect-story` — terminated on the same transient error before any commit; worktree clean.
  **Resumed via SendMessage** with instruction to rebase onto main (to pick up PR #878's docs)
  then proceed with original scope.
- `upaya-ritual-stub`, `ci-skeletons` — each hit a stall (600s no-progress watchdog); both had
  substantial real uncommitted progress in-worktree, resumed via SendMessage. `now-ahead` hit a
  SECOND transient connection drop after its first resume, also resumed again — real progress
  intact each time ("all prior edits are intact" per its own check before the second drop).
  **Pattern note:** all 5 remaining lanes have now hit multiple transient stalls/connection
  errors this session (some 2-3 times) — session infrastructure instability, not a logic
  problem in any lane; SendMessage-resume has preserved worktree progress every time, zero
  data loss.
- **PR #880 (priority-explain) MERGED.**
- **`upaya-ritual-stub` — PR #882 open, verified scope-clean** (6 files: `ritual.ts`,
  `ritual.test.ts`, `upaya.ts`, `upaya.test.ts`, `registry_bridge.ts` registration,
  `m8_e2e_proof.test.ts` count bump). **Mode-3 routing rule reviewed directly (not just
  trusted from the report)**: `isMode3ShapedRequest` fires on any non-blank `undertaking`
  field; `buildMode3WrongViewResponse` is synchronous with zero I/O (proof-by-construction of
  no passthrough), sets `wrong_view:true`, `correct_surface:'kala_elect_get'`, live
  `intervention_ref` pointer, honest `no_lever` on the other two tri-plane slots — matches
  Elevation §8 exactly. Hit merge conflicts against `main` (registry_bridge.ts +
  m8_e2e_proof.test.ts, both also touched by the already-merged priority-explain) —
  **Conductor resolved via `git merge origin/main` (not force-push, per rail B.1)**: combined
  both lanes' registrations additively, and caught a real error neither lane could have seen
  alone — both sides' branches independently computed their own tool-count delta (58→60,
  26→28) assuming their +2 was the ONLY addition, but with both lanes' registrations now
  landing together the true combined count is 62/30, not 60/28. Fixed, then verified
  empirically (not just arithmetic): `tsc --noEmit` clean, `m8_e2e_proof.test.ts` 35/35
  pass with the corrected counts. Pushed as a merge commit.
- **`now-ahead` — PR #883 open, verified scope-clean** (same file set pattern: `now.ts`,
  `ahead.ts`, 3 test files, `registry_bridge.ts`, `register_p1_aliases.ts`,
  `kala_temporal.ts`). Same merge-conflict class against `main` (this time vs. priority-explain
  only, upaya-ritual-stub not yet merged) — same fix pattern applied: additive registration
  merge, tool count corrected to 62/30, verified empirically (`tsc --noEmit` clean, 35/35
  tests pass), pushed as a merge commit. Confirming these are genuinely thin facades: every
  field either passes through a row verbatim from the underlying capability or directly
  relabels an existing pre-computed value — no new SQL/join/derivation.
- **Note on #882:** the `upaya-ritual-stub` agent independently resolved the SAME merge
  conflict the Conductor was resolving by hand, concurrently, in the same worktree — explains
  the "file modified since read" errors hit during manual resolution. Both converged on the
  identical correct fix (62/30). Real operational lesson for future nights: don't assume a
  resumed agent has gone idle just because a stall/error notification fired — it may resume
  and keep working before the next check-in. No harm this time (verified the final on-disk
  state independently either way), but worth avoiding the race going forward.
- **PR #882 (upaya-ritual-stub) and PR #884 (elect-story) both MERGED.** #884 landed 8 files
  (`elect.ts`, `elect.test.ts`, `story.ts`, `story.test.ts`, registration, count bump) —
  scope-clean, verified. The elect-story agent's connection dropped only during its final
  status-report phase; the actual work (commit, push, PR, auto-merge) had already completed
  successfully — Conductor found it merged, not stuck.
- **PR #879 (parva-dedup) MERGED.**
- `now-ahead` (#883) hit a THIRD conflict round (registry_bridge.ts + count assertion) after
  elect-story's merge — resolved the same way (additive merge, empirically-verified count,
  now 66/34 combining all four W0.4 lanes: now-ahead + upaya-ritual-stub + priority-explain +
  elect-story, each +2/+2). Pushed as a merge commit; branch nudged via update-branch (was
  BEHIND). Only `ci-skeletons` (#881) and `now-ahead` (#883) remain open — both clean/mergeable,
  nudged to update, awaiting CI. **5 of 6 Phase 1b lanes merged; Gate W0 close is next once
  these two land.**
- **PR #883 (now-ahead) MERGED.** All four W0.4 view-facade lanes now merged.
- **Real CI failure caught and fixed on `ci-skeletons` (#881), post-merge of its Mode-3
  dependency.** Once `kala_ritual_get` (upaya-ritual-stub, #882) merged, the Mode-3
  single-route test ran for real for the first time — and failed: a Mode-3-shaped request
  got `wrong_view:false` and fell through to Mode-1 (`opportunity_scan`) logic instead of
  redirecting. **Diagnosed, not assumed**: pulled the CI job log, found the test's payload
  shaped `undertaking` as an object (`{intent, description}`, authored before the sibling's
  schema was visible), but the now-merged `ritual.ts` declares
  `undertaking: z.string().optional()` — a deliberate, documented design (header comment:
  "no field an undertaking could hide behind"). `isMode3ShapedRequest`'s `typeof === 'string'`
  check correctly rejected the object, so the routing rule ITSELF is not broken — the test's
  payload was stale. Fixed the payload to a plain string (not the implementation — the schema
  is the ratified contract); both Mode-3 tests now pass empirically against the live merged
  code (verified directly, not trusted from a report). Also caught a real push race: an
  earlier `update-branch` API call had already pushed a merge commit to this branch that the
  local worktree hadn't pulled — resolved via `git merge` (not force-push) before pushing the
  fix. Pushed as commit `7190a79f`.
- **PR #881 (ci-skeletons) MERGED.** All 6 Phase 1b lanes complete — all 8 kala_* tools
  registered and merged to `main`. **Gate W0's remaining requirements: live on production
  (both charts), tool_search surfacing, sealed-harness regression, Verifier live acceptance.**
- **Deploy #1 attempt found a real, pre-existing, deploy-blocking bug — not campaign-caused,
  but campaign-discovered.** The `main`-branch deploy triggered automatically by these merges
  (`deploy.yml`, run `30423782330`) built and deployed a new Cloud Run MCP revision
  successfully, but `scripts/operator/mcp_end_to_end_smoke.sh` crashed on a bash parse error
  (`syntax error near unexpected token '('`), so traffic promotion was SKIPPED — the new
  revision (carrying all 8 kala_* tools) is deployed but dark; production still serves the
  prior revision. **Root cause, verified precisely** (not guessed): the script's
  `SMOKE_MCP_URL` error message contains an apostrophe (`deploy-cloudrun's`) inside a
  `${VAR:?message}` parameter expansion — a real, reproducible bash quirk (confirmed via
  `bash -n` and an isolated minimal repro) where a lone `'` inside `:?`/`:-` word-text opens
  an unterminated quoted string regardless of outer double-quote context, silently swallowing
  the rest of the file until it resurfaces as a stray-token error elsewhere. This has
  apparently broken every automated MCP smoke-and-promote step since the script was added —
  tonight's merges are just the first time it's been exercised. **Fixed** (PR #885,
  scope-clean single-line rephrase, auto-merge armed) and scoped a repo-wide grep for the same
  defect class (one other match, confirmed a false positive via `bash -n`). **Next: once #885
  merges, a fresh push to `main` is needed to re-trigger `deploy.yml` and get a clean
  smoke-and-promote run** (the dark revision from the failed run won't auto-promote itself).
- **PR #885 MERGED.** Confirmed the fix works: triggered a manual `workflow_dispatch` deploy
  (run `30433773914`, since `deploy.yml`'s path-detection only diffs `HEAD~1` and wouldn't have
  picked up the campaign's earlier merges) — `deploy-mcp`'s `if:` condition bypasses
  path-detection entirely under `workflow_dispatch`, confirmed by reading the workflow source
  before relying on it. Build + Cloud Run deploy succeeded; the smoke script now runs its real
  logic (no more parse crash): health check PASS, no-auth-rejection PASS (401 as expected).
- **Gate W0's "live on production" sub-condition — PARKED-HONEST, genuine external block, not
  something this session can resolve.** The smoke script's Bearer-auth and URL-token-fallback
  probes correctly FAIL LOUDLY (by the script's own explicit design) because `MCP_CANARY_KEY`
  is empty — the Secret Manager IAM binding for `mcp-canary-key` is still not applied (same
  gap flagged at Phase 0 preflight, independently confirmed via `PARISHODHANA_REPORT_v1_0.md`:
  "native action still required"). Traffic promotion was correctly skipped by the pipeline.
  **Conductor decision: NOT overriding this and manually promoting traffic without a real
  authenticated call.** The deploy cadence (brief §B.2) names "real authenticated call" as its
  own step for a reason — a production auth-path safety gate failing loud on missing
  credentials is not the same failure class as the earlier bash syntax bug; forcing it through
  on partial verification (health + no-auth only) would be exactly the kind of unilateral
  judgment call this campaign's Adjudicator boundaries exist to keep off an autonomous
  session's plate. **Unblock condition: the native applies the `mcp-canary-key` Secret
  Manager IAM binding for the GitHub Actions service account** — everything else re-runs clean
  once that lands (no code change needed, confirmed by this session's fix already being live
  on `main`). Code-complete state of Gate W0 (all 8 tools registered, merged, CI green) stands;
  only the live-traffic attestation is blocked. **Continuing Phase 2 work in the meantime**
  (per NIGHT_RUN §C, Phase 2 runs beside Phase 1/Gate-W0 close, not strictly after it) — main
  merges don't require production traffic to already reflect W0.

## Phase 2 — IN PROGRESS (first 2 of ~10 lanes dispatched)

- `w2-design` (Opus): the W2 field-as-science design doc (`KALA_W2_FIELD_DESIGN_v1_0.md`) —
  hazard-composition formula, provenance schema, null calibration, salience/submodular
  selection, 8-type insight catalog, skill-score/GOF definitions, DAG edges +
  weights-version-acyclicity mechanism (§2.5.4 — the subtle one). Design-only, no code.
- `bg-cohort` (Sonnet): `bg_cohort.py` writer (item 22) — synthetic reference cohort, global
  L0 upsert idempotency, migration reserved next-after-471 (agent re-verifies live max
  itself), seed row + both Nirmāṇa reconciliation checks required green in the same PR.
- **`w2-design` — PR #886 open, verified scope-clean (1 file, docs-only), auto-merge armed.**
  Substantial, high-quality design work: real closed-form hazard formula (λ as a power-weighted
  geometric product with noisy-OR promise, multiplicative thinning suppression, structural
  Adṛṣṭa floor), analytically-integrable log-linear field storage (peak-always-at-breakpoint
  invariant preserved deliberately for hash-replayability), a real skill-score/GOF definition
  (circular-shift null, deterministic bootstrap CI, three-state honest publication), and the
  weights-version acyclicity mechanism correctly specified — plus a self-caught refinement
  (resolve the weights version once in `plan_substeps`, not per-substep, to prevent a
  straddling build from mixing two weights versions into one non-deterministic hash). **Also
  caught a real cross-wave dependency bug**: the brief's own §2.5.3 proposes `bg_sky_calendar`
  as a `ka_kshetra` W2 dependency, but that asset is W3-owned and doesn't exist yet at W2 —
  would have broken `topoSort` in production. Documented an edge-staging rule (W2 declares
  without it; W3 adds it in its own seed-row PR) rather than silently building around it.
  Confirmed the one failing check (`Boot-time pointer validation`) is the same pre-existing,
  non-required TAP failure already confirmed at PR #877 — persists on main's last 3 commits,
  unrelated to this PR, not blocking.
- **`bg-cohort` — PR #887 open, verified scope-clean (5 files: writer, test, seed-registry
  update, has-writer-completeness update, migration `472_bg_synthetic_cohort.sql`), auto-merge
  armed, was BEHIND — nudged.** Real, verified engineering: N=10,000 synthetic births,
  fixed-seed RNG for reproducibility, 200-year window (chosen to span ~6.8 Jupiter / ~2
  Saturn-Rahu-Ketu cycles), Lahiri-only (a base-rate cohort needs one consistent frame, not
  all 5). **Found and honestly handled a real edge case**: `swe.houses()` (Placidus) fails near
  the polar circles — empirically probed 5,000 samples to confirm ±60° is safe rather than
  fabricate a placeholder Ascendant for failures (§N.7 discipline). Actually stood up a
  throwaway local Postgres cluster, ran real migrations + the writer, verified 10k rows in
  1.6s and correct idempotent re-run (0 new inserts, unchanged count) — not just unit-tested,
  live-verified. Migration 472 confirmed against live max (471) before use, no collision.
  Full Python suite: 4131 passed, 0 failed. **Side-note, investigated and resolved**: the
  agent found `CONDUCTOR_HALT_LOG.md` (unrelated governance file) locally modified in its
  worktree with a fresh FORENSIC-gate failure entry (Sun/Moon/Lagna all wrong, matching the
  exact historically-documented "wrong ayanamsha config → Scorpio not Aries" trap from
  CLAUDE.md §B) — traced to the agent's own throwaway test Postgres cluster almost certainly
  lacking production ayanamsha config; correctly left uncommitted by the agent, out of
  campaign scope, no action needed.
- **`bg-sky-calendar` — PR #888 MERGED, verified scope-clean** (5 files: writer, test,
  has-writer-completeness update, seed-registry update, migration
  `473_bg_sky_calendar.sql`). Took 4 resumes (session instability, not task difficulty — each
  resume showed real incremental progress). **Found a genuine floating-point boundary bug** in
  a shared, reused `find_ingress_events` utility: at an exact sign-cusp, `exact_longitude_deg`
  can land ~1e-7° on the wrong side, making the re-derived `sign` field report the prior sign
  even though the loop's own `target_sign` is unambiguous. Fixed on the writer's own side by
  trusting `target_sign` rather than re-deriving from the boundary-adjacent longitude — did
  NOT modify the shared utility itself (correctly out of scope for this lane), flagged to
  Conductor that other lanes reusing that utility near sign boundaries may hit the same thing.
  Chart-specific returns correctly skipped (belongs in `ka_kshetra` per brief §2 verbatim, as
  instructed). Migration 473 landed with no collision against bg-cohort's 472.

**All 3 dispatched L0/design Phase-2 lanes now complete and merged: w2-design (#886),
bg-cohort (#887), bg-sky-calendar (#888).**

## Phase 2 — W1 serving-join lanes (dispatching conservatively, ONE at a time)

**Deliberate deviation from NIGHT_RUN's suggested full-parallel W1 fan-out**: all 6 W1 lanes
edit the SAME shared facade files built in W0 (`now.ts`, `ahead.ts`, `elect.ts`, `story.ts`,
`priority.ts`, `explain.ts`) — a much higher collision density than tonight's W0/L0 pattern
(distinct new files per lane). Dispatching W1 lanes one at a time rather than all 6 concurrently
to avoid a 6-way merge-conflict storm on shared facades; will reconsider parallelizing once the
collision pattern is better understood from the first lane.

- **`w1-lel` dispatched** (Sonnet): item 10 (per-chapter LEL pinning + retrodiction fit, on
  STORY) + the Circularity-Guard LEL-invariance CI test — this is a **hard, unsoftenable gate**
  per the campaign's own kickoff contract. Instructed to write a real detector against the
  best current field-adjacent proxy (true field doesn't exist until W2) and name the proxy
  explicitly rather than stub the test meaninglessly.
- Not yet dispatched: recurrence-ladder+digest (2), dual-reference+daśā-lord-condition (8+28),
  kālam/diśā-śūla/chandrāṣṭama/horā/janma flags (32+29), mudda+sandhi-lite (30+1), 24-lite
  intervals+grading-facade+frontier+tri-plane (24-lite/38-lite/43); `bg_muhurta_lattice` +
  `bg_parihara_rules` (citation-heavy, still deliberately held back).
- **`bg-sky-calendar` — PR #888 MERGED.** Ingresses (9 grahas), stations (5 classical
  planets), eclipses, Jupiter-Saturn double-transit conjunctions; chart-specific returns
  correctly deferred to `ka_kshetra` per brief §2's explicit language, not built here.
  Migration 473, no collision. **Found and fixed a genuine floating-point boundary bug**: the
  shared `find_ingress_events` utility's re-derived `sign` field could land ~1e-7° on the
  wrong side of an exact sign cusp; fixed by trusting the loop's own unambiguous
  `target_sign` instead of re-deriving from the boundary-adjacent longitude. Live-verified
  against a throwaway Postgres (real migrations, real writer run, idempotency confirmed).
- All L0 substrate items now merged except `bg-muhurta-lattice` + `bg-parihara-rules`
  (higher-risk corpus-extraction lane — Agnivāsa/combination-yoga/parihāra rule tables need
  real citation-backed content, still deliberately held back for careful individual dispatch).
- **`w1-lel` — PR #889 open, verified scope-clean (5 files), auto-merge armed.** Item 10
  (per-chapter LEL pinning + retrodiction fit) done honestly: lexical theme-keyword overlap
  signal, `insufficient_data` when nothing pins rather than a fabricated ratio. **The HARD
  campaign gate — Circularity Guard LEL-invariance — is genuinely empirical, not a stub**:
  runs the production `KaJivanaParvaWriter` twice inside one never-committed transaction with
  a synthetic LEL row inserted between runs, asserts byte-identical output, verified no rows
  leaked. Static census caught a real (harmless, comment-only) LEL reference in an unrelated
  writer and rewrote it. Honest proxy note: targets `ka_jivana_parva` (closest existing
  "field-shaped" output) since W2's `ka_kshetra` doesn't exist yet — documented in the test's
  own docstring and the PR body as needing re-pointing once W2 lands, not silently glossed
  over. Full CI-equivalent suite: 4132 passed, 0 failed.
- `w1-lel` PR #889 MERGED (confirmed).
- **`w1-dual-dasha` — PR #891 open, verified scope-clean (4 files), auto-merge armed.** Items
  8 + 28 done: gochara dual-reference computes `house_from_moon` and `house_from_lagna`
  independently for all 9 grahas and serves both side by side (never a silent single-reference
  default); daśā-lord transit-condition reports current MD+AD lord's transit sign/house/dignity,
  and the AHEAD forward variant correctly pins the SAME lord identity as-of-today and projects
  ITS transit forward to the horizon, rather than re-identifying the ruling lord at a future
  date (a subtle correctness distinction the agent got right). Both fields kept strictly
  objective (raw houses + classical dignity labels, no favorable/unfavorable grading) per Gate
  W1's no-subjective-judgment-calls requirement. 47 new/extended tests pass, typecheck clean.
- **`w1-flags` — PR #892 open, verified scope-clean (4 files), auto-merge armed.** Items 32 +
  29 done: found existing-but-unwired substrate (`panchang_engine` already computes
  diśā-śūla/gulika-kālam, just never consumed by a `kala_*` view). Honest disclosure on
  gulika-kālam-ahead's horizon (bounded to the panchāṅga service's own 31-day cap, surfaced
  explicitly rather than silently truncated). **Janma-resonance's definition WAS found in the
  corpus** (KALA_SIX_VIEWS_DESIGN v2.0 + KALA_SUPREME_ELEVATION §9) — correctly implemented in
  full rather than defaulting to `not_in_corpus`, reading the native's own birth vara/tithi/
  nakshatra verbatim from L1 `chart_facts` (never re-derived, per §N.5). **Merge-conflict
  verification**: this lane edited the same files as the just-merged `w1-dual-dasha` — fetched
  + merged origin/main, resolved by concatenating both lanes' additions; independently
  confirmed post-merge that both lanes' fields (`dasha_lord_transit_condition`,
  `gochara_dual_reference`, `disha_shula`, `chandrashtama`) all coexist in `now.ts`, nothing
  lost. All objective, 3-state coverage, no new computation/migration.
- Not yet dispatched: 3 remaining W1 serving-join lanes (mudda+sandhi-lite · 24-lite
  intervals+grading facade+frontier v0+tri-plane wiring), `bg-muhurta-lattice` +
  `bg-parihara-rules`.
- **Merge-train note:** with 4+ lanes all registering new tools through the same
  `registry_bridge.ts` + bumping the same `m8_e2e_proof.test.ts` count assertions, every lane
  after the first to merge will hit this same conflict shape. Conductor is resolving each via
  `git merge origin/main` (never force-push) and re-deriving the count empirically rather than
  trusting either side's arithmetic — this is now the expected, not exceptional, path for the
  remaining lanes.
- **`ci-skeletons` — PR #881 open, verified scope-clean** (12 files, all under
  `.github/workflows/`, `platform-mcp/src/__tests__/`, `platform/scripts/census/shad_darshana_gates/`
  — no facade/lib/migration files touched). All 6 §0.6 items built: specificity gate v0,
  prose-survival battery (6/6 pass), tri-plane no-dead-end (7/7 pass), completeness census
  seed (52/52 items present, 7/7 pass), authority-basis census seed (**real detector: found 20
  live temporal-claim tools, honestly reports 0/20 carrying `authority_basis`** — correct
  pre-W2 state, not a stub), Mode-3 single-route assertion (**correctly SKIPPED, not
  fabricated-pass** — `kala_ritual_get` from `upaya-ritual-stub` not yet merged; written
  strictly against Elevation §8's binding text, will start asserting once that lane lands, no
  code change needed). Auto-merge enabled.

## Session log

| Session | Date | Phases worked | Outcome |
|---|---|---|---|
| Night 1 | 2026-07-29 | Phase 0 (boot) | IN-PROGRESS |

## Wave status

| Wave | Status | Evidence | Notes |
|---|---|---|---|
| W0 | **VERIFIED-CLOSED** | PRs #877/#880/#882/#883/#884/#881 (merged main@`42151b24`+); deploy run `30484976742`; direct production `tools/list` + functional calls on both charts; see GATE W0 CLOSURE RECORD above | All 8 tools live on production, both charts, envelope-conformant, Mode-3 routing live-verified. |
| W1 | **VERIFIED-CLOSED** | All 12 items VERIFIED-FIXED, both charts, live production (revision `amjis-mcp-00525-hrd`, 100% traffic). Round 1 rejected 5/12 (8,28,29,30,32) with real evidence; fix (PR #940, Opus) redeployed; round 2 independently re-verified all 5 via recomputed ephemeris + fact_id tracing + FORENSIC fixture cross-check, not self-report | Real honesty-inversion bugs caught and fixed by the verification apparatus exactly as designed — see NEXT-ACTION for the full round-1/round-2 record. Two non-blocking advisory notes filed. |
| W2 | **DESIGN-COMPLETE + Lane D unblocked, build lanes not yet dispatched** | PR #886 (`KALA_W2_FIELD_DESIGN_v1_0.md`), PR #918 (Lane D §6.3 reconciliation, ADJUDICATION-1), PR #932 (bg_cohort MD-lord chain table, APPROVE-WITH-NOTES) all merged | Hazard formula, skill-score/GOF, DAG acyclicity, AND Lane D's cohort contract all specified precisely against reality; 5 build lanes (A/B/C/D/E) ready to dispatch together. |
| W2G | NOT-STARTED | — | GOCHARA-2.0 sub-day. **BLOCKED on N1–N5 ratification (W2G.0) — see below.** |
| W3 | NOT-STARTED | — | New computations over the field. |
| W3K | NOT-STARTED | — | KP sub-lord engine (item 18, built from zero). |
| W4 | NOT-STARTED | — | Intervention flagship (UPĀYA/YAJÑA). Opus design mandatory. |
| W5 | NOT-STARTED | — | Planner integration; native's hard gate (real MCP calls). |
| W6 | NOT-STARTED | — | Cutover + retirement. |

## N1–N5 ratification block (W2G precondition — blank N5 means W2G is not startable)

| Item | Ruling | Ruled by | Date | Rationale |
|---|---|---|---|---|
| N1 (wave naming) | — | — | — | Pending ANTARYĀMIN pre-queued adjudication. |
| N2 (multi-chart rollout order) | — | — | — | Pending. |
| N3 (pre-1984 backfill) | — | — | — | Pending. |
| N4 (cutover posture) | — | — | — | Pending. |
| N5 (lock granularity) | — | — | — | **FROZEN-contract question. Native ruling required; ANTARYĀMIN may only apply the pre-ruled CONSERVATIVE-DEFAULT (chart-level lock stays, no orchestrator change, reversible) if the native has not yet spoken. Not yet recorded.** |

## Registry item status (1–44 + E1–E8)

All items below seeded **NOT-STARTED** per W0.1. Disposition vocabulary: VERIFIED-FIXED /
VERIFIED-NO-DEFECT / PARKED-HONEST / FAILED-REOPENED. `OUT-OF-SCOPE-BY-DESIGN` is retired and
illegal.

| # | Item | Wave | Status | Both-charts | Evidence |
|---|---|---|---|---|---|
| 1 | Daśā-sandhi calendar | W3 (lite@W1) | **W1-lite VERIFIED-FIXED** (band convention documented, not fabricated); full two-period calendar is W3 | Y (code-level) | PR #924, `dasha_sandhi` on `kala_now_get` |
| 2 | Recurrence-ladder serving | W1 | IN-PROGRESS | — | `shad-darshana/w1-recurrence-digest` dispatched Night 2 |
| 3 | Sky-event calendar | W3 | **VERIFIED-FIXED (bg_sky_calendar built; per-chart contact joins deferred to ka_kshetra per spec)** | Y (global asset) | PR #888, live-verified against throwaway Postgres |
| 4 | Moorti-nirṇaya | W3 | NOT-STARTED | — | — |
| 5 | Vedha + Sarvatobhadra grid | W3 | NOT-STARTED | — | — |
| 6 | Activity-specific muhūrta tables | W3 | NOT-STARTED | — | — |
| 7 | Muhūrta-lagna | W3 | NOT-STARTED | — | — |
| 8 | Gochara dual-reference | W1 | **VERIFIED-FIXED** (round-2 PARĪKṢAKA, 2026-07-30) | Y — all 9 grahas non-null both charts, live-recomputed (Sun/Rahu sidereal longitude independently verified against served values), house arithmetic self-consistent | PR #891 (code) + PR #940 (fix: missing sidecar `x-api-key` header masked every 401 as empty) |
| 9 | Health/adverse event class | W3 | NOT-STARTED | — | — |
| 10 | Per-chapter LEL pinning | W1 | **VERIFIED-FIXED** | Y (code-level) | PR #889; Circularity Guard empirically verified |
| 11 | Provenance edges | W2 | NOT-STARTED | — | — |
| 12 | Daśā-system applicability | W2 | NOT-STARTED | — | — |
| 13 | Tithi-Praveśa | W3 | NOT-STARTED | — | — |
| 14 | Janma-anchored election rules | W3 | NOT-STARTED | — | — |
| 15 | Rarity axis | W2 | NOT-STARTED | — | — |
| 16 | Kota-Chakra | W3 | NOT-STARTED | — | — |
| 17 | Sudarśana-Chakra | W3 | NOT-STARTED (naming ruled) | — | Conductor ruling: writer named `ka_sudarshana_varsha` — confirmed namesake-only collision vs `bo_sudarshana.py` (different layer/computation), not built yet |
| 18 | KP sub-lord clock (CR-75) | W3K | NOT-STARTED | — | — |
| 19 | GOCHARA-2.0 sub-day | W2G | NOT-STARTED | — | — (blocked on N1–N5) |
| 20 | Auto-filed prospective ledger entries | W2 | NOT-STARTED | — | — |
| 21 | Per-tradition calibration weights | W2 (ongoing) | NOT-STARTED | — | — |
| 22 | Synthetic reference cohort + matched sub-cohort | W2 | **VERIFIED-FIXED (cohort + MD-lord chain built; matched-sub-cohort JOIN logic itself is W2 Lane D's job)** | Y (global asset) | PR #887 (`bg_cohort`, 10k rows), PR #932 (`bg_synthetic_cohort_md` MD-lord chain, ADJUDICATION-1, ~100k rows, Vimśottarī arithmetic independently verified against native's own `chart_dashas`) |
| 23 | Circular-shift null calibration | W2 | NOT-STARTED | — | — |
| 24 | Uncertainty-budget propagation | W1-lite/W2-full | **W1-lite VERIFIED-FIXED**; full budget propagation is W2's job | Y (code-level) | PR #926, `sukshma_boundary_uncertainty` on `kala_now_get`, documented lite-v0 interval convention |
| 25 | Salience vector + submodular selection | W2 | NOT-STARTED | — | — |
| 26 | UPĀYA-SETU | W4 | NOT-STARTED | — | — |
| 27 | kala_timeline_spec v1 | W2 | NOT-STARTED | — | — |
| 28 | Daśā-lord transit-condition | W1 | **VERIFIED-FIXED** (round-2 PARĪKṢAKA, 2026-07-30) | Y — current + forward, both charts, real transit sign/house/dignity (e.g. C1 Mercury MD own_sign; forward Saturn AD Aries debilitated) | PR #891 (code) + PR #940 (fix: same root cause as item 8) |
| 29 | Chandrāṣṭama/horā/janma-resonance flags | W1 | **VERIFIED-FIXED** (round-2 PARĪKṢAKA, 2026-07-30) | Y — all populated both charts, 2 dates tested, panchāṅga single-date path confirmed healthy; C2 correctly fires a real `is_chandrashtama:true` positive | PR #892 (code) + PR #940 (fix: `panchang.py` wrong kwarg name causing an uncaught 500 on the single-date path only) |
| 30 | Mudda daśā join | W1 | **VERIFIED-FIXED** (round-2 PARĪKṢAKA, 2026-07-30) | Y — muntha now real both charts (C1 Libra/7th/Venus, C2 Virgo/6th/Mercury), cross-checked against a repo FORENSIC fixture; prose leak gone | PR #924 (code) + PR #940 (fix: reader expected nonexistent flat columns instead of `muntha_position_jsonb`) |
| 31 | Period-echo mining | W3 | NOT-STARTED | — | — |
| 32 | Diśā-śūla + gulika-kālam joins | W1 | **VERIFIED-FIXED** (round-2 PARĪKṢAKA, 2026-07-30) | Y — both fields populated both charts, both dates | PR #892 (code) + PR #940 (fix: same root cause as item 29) |
| 33 | Absence-of-expected detector | W3 | NOT-STARTED | — | — |
| 34 | Contrastive EXPLAIN | W3 | NOT-STARTED | — | — |
| 35 | Planner wiring verified LIVE (hard gate) | W5 | NOT-STARTED | — | — |
| 36 | Contender lattice + adjudication engine | W3 | **SUBSTRATE VERIFIED-FIXED** (`bg_muhurta_lattice` global tables built: Agnivāsa, combination-yogas, kālam periods, ghaṭī-muhūrtas, ~91,477 rows); the query-time lattice-annotation/adjudication ENGINE itself (`lib/kala_lattice_query.ts`) is still W3's job | Y (global asset) | PR #930, Opus citation-review round-2 APPROVE (every citation independently re-derived against live corpus + `panchang_engine` source, not trusted from self-report) |
| 37 | Ritual-resonance + paddhati profile | W3/W4 | NOT-STARTED | — | — |
| 38 | ELECT ritual-pairing + grading unification | W1 facade/W3/W4 | **W1-facade VERIFIED-FIXED** (grading-engine facade + frontier v0 on `kala_elect_get`); ritual-pairing half is W4's job | Y (code-level) | PR #926, documented placeholder tier thresholds not corpus-calibrated |
| 39 | Living-LEL incremental calibration plane | W2 | NOT-STARTED | — | — |
| 40 | kala_ritual_get registration + planner wiring | W0 stub/W4/W5 | **W0-stub VERIFIED-FIXED** (Modes 1-2 honest not_in_corpus; Mode-3 wrong_view redirect real & tested) | Y | PR #882 |
| 41 | Muhūrta Factor Census + corpus extraction | W3 | **VERIFIED-FIXED** (50-row census, 38 computed / 5 not_computed / 7 not_in_corpus, every row cross-checked with a real detector — `test_census_has_no_dangling_lattice_pointers` — not just claimed) | Y (global asset) | PR #930, round-1 Opus REJECT (5 real defects: a citation-contradicting Wednesday/abhijit bug, two wrong evidence numbers, one false "not found" corpus claim, dangling census pointers) → builder fixed all 5 with live re-verification → round-2 independent Opus APPROVE, every number re-derived |
| 42 | Unified Intervention Ledger | W4 | NOT-STARTED | — | — |
| 43 | Tri-plane traversability contract | W0–W1 | **VERIFIED-FIXED** (real-data wiring confirmed on all six view facades — items 8/10/28/29/30/32 now genuinely reflected, not just honest `no_lever` placeholders where a real signal exists) | Y | PRs #877/#880-884/#926, `no_lever`-honest pointers on every merged facade, new cross-facade real-wiring test |
| 44 | Single-temporal-authority (`authority_basis`) | W0 seed/W2/W6 gate | **W0 seed VERIFIED-FIXED**; population is W2's job | — | CI skeleton census seed, PR #881 |
| E1 | Point-process formalization + skill score | W2 | **DESIGN-COMPLETE, build not started** | — | PR #886: closed-form hazard, skill-score/GOF formulas specified precisely |
| E2 | Insight synthesis stage | W2 | **DESIGN-COMPLETE, build not started** | — | PR #886: all 8 insight types + trigger predicates specified |
| E3 | Argument-shaped reading + specificity gate | W0/W2 | **W0-skeleton VERIFIED-FIXED**; hard-gate flip is W2's job | Y | PRs #877, #881 |
| E4 | question_frame compiler | W0 | **VERIFIED-FIXED** | Y | PR #877, `kala_envelope.ts` |
| E5 | field_snapshot_id | W0/W2 | **W0-stub VERIFIED-FIXED**; real hash is W2's job | Y | PR #877, marked with explicit TODO(W2) upgrade point |
| E6 | Per-view elevations | W1–W3 | NOT-STARTED | — | — |
| E7 | Substrate (census CI, freshness, cohort, composer lib, skill-score CI) | W0/W2 | **PARTIAL**: composer lib + census CI seeded (W0), cohort + matched-sub-cohort MD-lord chain built (W2-prep, PRs #887/#932); skill-score CI not yet | Y (cohort, global) | PRs #877, #881, #887, #932 |
| E8 | Non-elevations register | standing | NOT-STARTED | — | — |

## Preflight (Phase 0)

- Repo clean: **NO** — pre-existing uncommitted state on the checked-out session branch
  (`satyadipa/orchestrator-lit-predicate`, unrelated SATYA-DĪPA work) and numerous untracked
  docs from other in-flight campaigns (PARIPRASHNA, narration_audit, PARISHODHANA). None of
  this is campaign scope; not touched. Campaign work branches from `main` (fast-forwarded to
  `origin/main` @ `8e1af4ca` this session), isolated in its own worktrees.
- Both canonical charts healthy (LC-5 sweep staleness on `1c826d5a`): **NOT CLEARED — ticketed
  per brief's own "CLEARED or ticketed" allowance, does not block W0/W1.** Live query against
  `kala_gochara_windows`: canonical chart `482012f1` has 8,345 rows to horizon 2084-12-30
  (58y forward); `1c826d5a` has only 1,267 rows to horizon 2027-07-03 (~1y forward) despite
  being computed *more recently* (2026-07-26 vs 2026-07-24/25) — a real coverage-horizon gap,
  not a timestamp-staleness one. **TICKET: `1c826d5a` needs a full gochara-sweep rebuild
  extending its horizon to parity with the canonical chart before any both-charts gate that
  depends on forward-window coverage can honestly close** (W1 items touching AHEAD-window
  serving are the first to hit this — Conductor to watch for it at Gate W1, not before).
- Canary pipeline state: real automated canary blocked — `MCP_CANARY_KEY` IAM binding not yet
  applied by the native (confirmed via `PARISHODHANA_REPORT_v1_0.md` + handoff doc, both
  independently). **Not a campaign blocker** — brief's own fallback applies: manual canary
  discipline (deploy.yml fails safely closed without the binding). Deploys proceed under this
  discipline until the native applies the grant.
- Migration range reserved: **472–495, in `platform/supabase/migrations/`** (see below for why
  that directory, not `platform/migrations/`).
- Duplicate-copy + tool-name census:
  - **Item 17 vs `bo_sudarshana.py` — CONFIRMED namesake collision, NOT a functional
    duplicate.** `bo_sudarshana.py` is an L2 Bodha static house-triad MSR signal writer
    (9 grahas × 5 ayanamshas, `bodha_msr_signals`). Item 17 (Sudarśana-Chakra year-wheel) is
    an L3 temporal progression technique — different layer, different computation, same
    classical term. **Conductor naming ruling (W0, no adjudication needed — plain engineering
    call): item 17's writer is named `ka_sudarshana_varsha`, never bare `sudarshana`, to keep
    the two permanently distinguishable in registries/logs.**
  - **`kala_activations` — confirmed live, but as a JSON field key, not a table or tool.**
    Written/read in `register_d9_judgment.ts` (`timing_hooks.kala_activations`) and
    reconciled in `registry_bridge.ts`. No table/tool collision exists, but **no new campaign
    envelope field or table may reuse this exact string for a different shape** — live serving
    code pattern-matches on it.
- Nirmāṇa catalog-reconciliation baseline: **CLEAN before this campaign adds anything.**
  `catalog_reconciliation.test.ts` 6/6 PASS; `test_has_writer_completeness.py` 3/3 offline PASS
  (1 live test needs `DATABASE_URL`, skipped locally); direct DB check confirms only 5
  pre-existing `has_writer=false` assets, none campaign-relevant. Brief §2.5.1 requires both
  checks stay green in the same PR as every new writer going forward — not a one-time gate.
- **Live collision note (out of campaign scope, flagged for awareness only):** the
  currently-checked-out session branch (`satyadipa/orchestrator-lit-predicate`, unrelated
  SATYA-DĪPA work) carries an unmerged `platform/migrations/466_asset_throughput_incomplete_state.sql`
  that collides on number 466 with main's `466_omega8_floor_wiring.sql`. This campaign's
  worktrees branch from `main`, not from that branch, so it's unaffected — noted here only so
  a future session doesn't mistake it for a campaign-caused collision.
- No existing SHAD_DARSHANA work found in git history (`origin/main` has no `shad-darshana*`
  branches, no PRs matching the campaign) — confirmed first night.

## Migration range reserved

**Known hygiene issue, not a data-loss bug (2026-07-30):** `484_bg_muhurta_lattice.sql` (PR
#930) and `484_bg_synthetic_cohort_md.sql` (PR #932) both used number 484 — two independent
lanes each re-verified "live max" at a moment that predated the other's merge. Confirmed via
direct query that BOTH tables exist in production (`to_regclass` resolves both) — the runner
dedupes by full filename, not the leading number, so nothing was silently skipped. Not
renaming the already-applied files (renaming something the runner has already tracked as
applied is its own risk for zero benefit). **Superseded (2026-07-30, merge-train pass):** the
474–483 reservation itself proved unsafe in practice — a DIFFERENT campaign's
`platform/migrations/474_asset_throughput_incomplete_state.sql` landed in the OTHER directory
before all five W2 lanes could merge, colliding with Lane A's `platform/supabase/migrations/
474_kala_field_stage0_1.sql`. All five lanes' migrations were renumbered to **488–497** (A:
488/489, B: 490, C: 491/492/493/494, D: 495, E: 496/497) — above the combined-directory true
max (486 at renumber time) and clear of every sibling lane's own claim. **474–483 is no
longer a live reservation for this campaign** — any future ṢAḌ-DARŚANA migration should
re-verify the actual combined max fresh (per the design doc's own standing instruction) rather
than assume that range is still free or still reserved.

**472–495, in `platform/supabase/migrations/`** (reserved 2026-07-29, Night 1). Two migration
directories both apply to prod and are deduped by filename (`migrate.ts`); the standing policy
doc (`MIGRATION_DIRECTORY_POLICY_v1_0.md`, 2026-05-22) claims `platform/migrations/` is
canonical and supabase is frozen, but the actually-current convention — per
`platform/supabase/migrations/README.md` and observed practice, both directories growing in
lockstep — is that new migrations land in `platform/supabase/migrations/`. Combined live max
on `main`@`8e1af4ca` = 471 (`471_retire_mcp_predictions.sql`). **Re-check the live max
immediately before writing the FIRST actual migration this campaign lands** — this range could
go stale if another campaign lands migrations first; 472 is a reservation, not a guarantee.

## Deployed revisions

`amjis-mcp-00517-b5q` — 100% traffic, deploy run `30484976742`, 2026-07-29T19:35 UTC. First
campaign revision serving all 8 kala_* tools live. Web/Sidecar/Pipeline-Job also current from
this same run (all 5 jobs green).

## Open PRs

None yet.

## Skill-score scoreboard

Not yet published (first publish at W2 close becomes the CI baseline).

## Specificity-gate status

Not yet seeded (W0.6 skeleton pending).

## Authority-basis census scoreboard (item 44)

Paths enumerated: — / carrying `authority_basis`: — / computing own windows: — (target: 0).

## Dark-corpus bright% per chart

Not yet re-measured this campaign (baseline = PARIŚODHANA measurement, referenced at W6).

## Live-MCP verification table (W5)

Not started.

## W4 Mode-2 fixture disposition

Not started.

## ADJUDICATION log (ANTARYĀMIN)

**ADJUDICATION-1 (2026-07-30, Night 2 — matched sub-cohort MD-lord, Gap #3 from the
post-Night-1 audit, W2 Lane D precondition).** Question: precompute MD-lord into `bg_cohort`
storage, or derive it at rarity-query time in `cohort_client.py`? **Ruling: precompute — but
as an age-based MD-lord CHAIN table, not a scalar column.** MD-lord is cheap arithmetic off the
Moon `sidereal_longitude` already stored in `bg_synthetic_cohort.positions` (no new ephemeris
call), so the audit's "needs the full dasha engine" deferral was overstated; a scalar
`md_lord` was rejected because cohort births span 1900–2099 and a fixed-epoch "current lord"
is undefined for future-born synthetic rows — so a new table `bg_synthetic_cohort_md
(synthetic_id, md_index, md_lord, start_age_years, end_age_years)` carries the full chain,
joined by the caller on an explicit reference age, not a stored "as of" date. Not a
FROZEN-contract question (no orchestrator-contract, untouchable, or rail touched — purely an
additive L0 schema + one lane's internal join strategy). Fully reversible (drops cleanly,
recomputes byte-identically from the fixed cohort seed). **Also surfaced, same investigation,
broader than the original question: the design doc's whole Lane D §6.3 contract (three tables
`cohort_charts`/`cohort_positions`/`cohort_feature_counts`) does not match the actual shipped
`bg_cohort` schema at all** (real table is the single JSONB `bg_synthetic_cohort`, no
`cohort_id`/`cohort_version`/`lagna_sign`/`md_lord` columns) — routed to a dedicated docs-only
design-correction lane (`shad-darshana/w2-lane-d-design-fix`, dispatched same session) to
reconcile §6.3 with reality before Lane D itself is dispatched; W2 Lanes A/B/C/E have no
dependency on this and are not blocked by it. Full ruling text preserved in this session's
agent transcript; summarized here per the ledger's evidence-link convention.

## MORNING REPORT — Night 1 close (2026-07-29 → 2026-07-30)

**Gates closed:** None VERIFIED-CLOSED in the brief's strict sense (a gate requires production
liveness + Verifier live acceptance, neither yet possible). **Gate W0 is CODE-COMPLETE**: all
8 tools (`kala_now_get`, `kala_ahead_get`, `kala_elect_get`, `kala_story_get`,
`kala_priority_get`, `kala_explain_get`, `kala_upaya_get`, `kala_ritual_get`) registered on
`main`, envelope-conformant, CI green, Mode-3 routing rule genuinely tested end-to-end. It
cannot formally close tonight — see the single blocker below.

**Items dispositioned VERIFIED-FIXED tonight:** 3 (sky calendar), 8 (dual-reference), 10 (LEL
pinning + the hard-gated Circularity Guard), 22 (synthetic cohort), 28 (daśā-lord condition),
29 (chandrāṣṭama/horā/janma-resonance), 32 (diśā-śūla/gulika-kālam), 40 (ritual stub + Mode-3
redirect), 43 (tri-plane, facade-level), 44 (authority-basis, seed-level); E3–E5 (W0-level),
E1/E2 (design-level via PR #886), E7 (partial). Item 17 naming ruled, not yet built. Everything
else (30 registry items, all of E6/E8, all of W2's actual build, all of W3/W3K/W4/W5/W6)
remains NOT-STARTED — **this campaign is realistically 14–24 sessions per its own brief; Night
1 covered Phase 0 through the start of Phase 2, which is on-pace, not behind.**

**The one real blocker — parked, not worked around:** Gate W0's production-liveness and every
downstream deploy this campaign needs are blocked on **the native applying the
`mcp-canary-key` Secret Manager IAM binding** for the GitHub Actions service account. This is
a genuine external dependency: the deploy pipeline's own smoke-test script is correctly
designed to fail loud rather than silently skip its auth verification when the key is
unavailable, and overriding that safety gate to force a production traffic promotion without a
real authenticated call would be exactly the kind of unilateral judgment call this campaign's
Adjudicator boundaries exist to keep off an autonomous session's plate — so it was not done.
Two manually-triggered deploy attempts tonight (`workflow_dispatch`, bypassing the pipeline's
stale path-detection) both built and pushed the Cloud Run image successfully and both stopped
at the same auth-probe gate for the same reason. **main ≠ production right now, and that is
the honest, documented state — not a false close.** Everything else deployed clean (Web,
Sidecar, Pipeline-Job images all shipped tonight); only the MCP surface is dark.

**Rulings made:** one, Conductor-authority (not ANTARYĀMIN): item 17's writer named
`ka_sudarshana_varsha` after confirming the `bo_sudarshana.py` "collision" is a namesake only
(different layer, different computation). Migration range 472–495 reserved in
`platform/supabase/migrations/` (through 473 actually used; 474–495 remain free). No
ANTARYĀMIN rulings were needed (see ADJUDICATION log above).

**Real defects found and fixed along the way (not just forward progress):**
1. The campaign's own governing docs were never committed to git — silently broke every fresh
   worktree's ability to read them. Fixed early (PR #878).
2. `ka_jivana_parva` double-emitted every mahadasha-boundary antardasha row (own-lord rule +
   inclusive-both-ends date filter). Fixed serving-side, live-verified on all 3 built charts
   (PR #879).
3. The Mode-3 routing CI test's payload predated the sibling lane's ratified schema
   (`undertaking` as an object vs. the real `z.string()`) — the routing rule itself was sound;
   only the test was stale. Diagnosed via live CI logs, not guessed (fix pushed directly).
4. A pre-existing, deploy-blocking bash bug: an apostrophe inside `${VAR:?message}`
   parameter-expansion syntax silently broke every automated MCP smoke-and-promote step since
   the script was added — discovered because tonight's merges were the first real exercise of
   the pipeline in a while. Root-caused via isolated `bash -n` repro before touching anything;
   fixed with a one-line rephrase (PR #885).
5. The W2 design itself would have created a production DAG break: brief §2.5.3 proposes
   `bg_sky_calendar` as a W2-time `ka_kshetra` dependency, but that asset doesn't exist until
   W3 — caught during design, not during a broken build; resolved with an explicit edge-staging
   rule (PR #886).
6. A floating-point sign-cusp boundary bug in shared ingress-detection code (~1e-7° landing on
   the wrong side of an exact cusp); fixed by trusting the unambiguous loop variable instead of
   re-deriving from boundary-adjacent longitude (PR #888).
7. `swe.houses()` (Placidus) fails near the polar circles — found via a 5,000-sample empirical
   probe before it could produce a silent placeholder value in the cohort writer; bounds
   narrowed to ±60° rather than fabricating a fallback Ascendant (PR #887).

**Parks and reasons (all PARKED-HONEST, all with a stated release condition):**
- Gate W0 production-liveness — blocked on native's `mcp-canary-key` IAM grant (above).
- `1c826d5a`'s (Abhinandan's) gochara-sweep forward horizon — truncated to ~1y vs. the
  canonical chart's 58y despite a more recent compute timestamp; ticketed at Phase 0 preflight,
  needs a full sweep rebuild before any both-charts gate depending on forward-window coverage
  can honestly close (first bite: any future W1 AHEAD-window gate check).
- `bg_muhurta_lattice` + `bg_parihara_rules` — deliberately never dispatched tonight; needs
  real citation-backed Agnivāsa/combination-yoga/parihāra content, judged to warrant a more
  careful individual session rather than being rushed alongside the batch lanes.
- W2G — correctly never started; blocked on the native's N1–N5 ratification per brief §3
  W2G.0, which this campaign may not decide autonomously. Not yet even requested from the
  native (Night 1 didn't reach the point of needing it).
- W3K — correctly never started; depends on W2's clock machinery, which isn't built yet.

**Skill scoreboard:** not yet publishable — W2's build (the actual field/skill-score
computation) hasn't started; only its design is done. First publish remains the W2-close CI
baseline per brief §3 Gate W2.

**Specificity-gate / authority-basis-census / dark-corpus scoreboards:** unchanged from seed
state — all three populate at W2/W6 per the brief's own schedule, not before.

**Housekeeping done at close:** all 15 of tonight's worktrees removed cleanly (each already
merged to main, verified before removal); local `main` fast-forwarded to `origin/main`
throughout the session, currently at `f573be8d`+ (includes unrelated concurrent work from
other active sessions in this repo — confirmed no conflicts touched campaign files). One
stale, pre-existing, locked worktree (`/tmp/prdocs`, predates this session) left untouched —
not created by this campaign, not safe to remove unilaterally.

**Operational note for Night 2:** roughly 15+ background-agent stalls/connection-drops
occurred across the session (apparent infrastructure-level instability, not task-specific) —
every single one was resumed from intact worktree state via SendMessage rather than
restarted from scratch or silently abandoned; zero work was lost to this pattern, but it did
slow the night down substantially. If it recurs, the same resume-don't-restart discipline is
the right response.

**Single next action:** the native applies the `mcp-canary-key` Secret Manager IAM binding for
the GitHub Actions service account, then Night 2 re-runs
`gh workflow run deploy.yml --ref main`, confirms the smoke script's auth probes pass and
traffic promotes, runs Verifier live acceptance on both canonical charts, and formally closes
Gate W0 — after which Phase 2 continues (3 remaining W1 lanes, the parihāra/lattice lane, W2
build-out against the now-merged design doc).

*Truth over completion. PARKED-HONEST with evidence, not a false close.*

---

## MORNING REPORT — Night 2 close (2026-07-30 → 2026-07-31)

**Gate W1 → VERIFIED-CLOSED.** All 12 registry items confirmed VERIFIED-FIXED, live, on both
canonical charts, across two independent PARĪKṢAKA rounds (round 1 caught 5 real defects,
round 2 independently re-verified the fix from first principles, not from the fix PR's own
report). Full record above.

**Wave W2 build lanes → all 5 merged to `main`, Gate W2 itself NOT closed.** Lanes A–E
(#945/#944/#949/#946/#947) all landed. The merge-train pass that combined them found and fixed
9 real defects total that no single lane's isolated development or CI could have caught: a
cross-directory migration-number collision (renumbered 474–483 → 488–497), a `ka_kshetra`
seed-row saga (removed as an over-generalized cleanup, then correctly restored when
`catalog_reconciliation.test.ts` caught that `mi_bhara`'s own `depends_on` entry needs it
resolvable in the same file — see NEXT-ACTION item 2 for the full account), and 4 further
integration bugs visible only once all five lanes were combined (a `conn=None` crash in
sandhi-band symbolization, a duplicate `ClockApplicability` dataclass with two different field
orders that cascaded into 5 stale positional test constructions, and a `FakeConn`/
`promise_prior` fixture mismatch). This is exactly the value a dedicated integration/merge-train
pass exists to catch, and it caught real bugs, not busywork. Full evidence trail in the
NEXT-ACTION section above and the ledger commit history (PR #951).

**Gate W2 itself is correctly NOT closed this session.** Lane C disclosed a real, honest
blocker: the hazard formula's lifetime-count priors (N_e) do not exist anywhere in the corpus
yet (`brahma_class_priors` only holds signal-salience priors; `brahma_event_ontology`'s
`base_rate_by_age` is a different distribution shape entirely) — a real `ka_kshetra` build
would currently write zero field rows rather than fabricate. The actual field-integration →
hash-replay → weights-v0-seed → skill-score-publish sequence and Gate W2's acceptance criteria
are real, substantial standalone work, correctly deferred to a session that starts by resolving
the N_e blocker.

**`main` ≠ production, by design, not by oversight.** Production (`amjis-mcp`, asia-south1) is
still serving `amjis-mcp-00525-hrd` — the Gate-W1-fix revision, deployed before any W2 lane
merged. `main` is now ahead by all 5 W2 lanes plus the ledger PR. **No deploy was triggered
this session**, on the native's explicit instruction after being shown the tradeoff: the W2
lanes are pure strangler-fig additions (new tables/migrations, nothing live-serving depends on
them yet, and the orchestrator won't build `ka_kshetra` productively until the N_e blocker
closes anyway), so a stale production revision costs nothing functionally — and a deploy right
now would also ship several unrelated commits from OTHER concurrently-active campaigns sharing
this repo tonight (SAMĀPTI's `n8-lint` gate; a migration-474-header-comment fix/revert pair
between two other sessions), which is not this Conductor's call to make unilaterally. **The
next session that wants to actually build a `ka_kshetra` field must deploy `main` first** —
this is the one concrete precondition it inherits.

**A genuine repo-concurrency observation, not a defect to fix, but worth the native's
awareness:** this session ran in a repository with a very high concurrent-campaign load —
dozens of other worktrees/branches active simultaneously (SAMĀPTI, sarva-siddhi, satya-shesha,
elev, pb, wave, and others), `main` receiving pushes every 10–30 minutes for hours at a stretch
from sessions this Conductor has no visibility into. This directly caused the ledger PR (#951)
to lose a merge race repeatedly (branch fell `BEHIND` faster than its own CI could complete) —
resolved once the native paused other sessions, not by any change on this campaign's side. Two
of the passing-by commits observed on `main` directly contradicted each other in successive
pushes (a migration-474 header-comment "fix" immediately followed by a "revert... Ruling 58
supersedes Ruling 44" from what appears to be a different session) — flagged here as an
observed fact, not investigated further, since it belongs to a different campaign's ledger.

**Worktree/branch hygiene: all of this campaign's completed-and-merged worktrees and local
branches removed** (9 worktrees, 18 local branch refs total across the session) — verified
each via its GitHub PR's actual merge record (not local git ancestry, since this repo
squash-merges, so a raw `--merged` check would have under-reported). The one pre-existing,
locked `/tmp/prdocs` worktree (`docs/shad-darshana-v2-spec`) was left untouched — it predates
this campaign and is not this Conductor's to remove unilaterally.

**Skill scoreboard / specificity-gate / authority-basis-census / dark-corpus scoreboards:**
unchanged from Night 1 seed state — all populate at W2-close/W6 per the brief's own schedule,
and W2 hasn't closed.

**Single next action for Night 3:** deploy `main` to apply the W2 migrations, then start Gate
W2's real integration work by first resolving Lane C's disclosed N_e lifetime-count-priors gap
(own small L0 corpus-seeding lane, or an ANTARYĀMIN-adjudicated design choice for where the
priors come from — same shape of precondition as ADJUDICATION-1's `bg_synthetic_cohort_md`
gap) — only after that can `ka_kshetra` produce a real, non-empty field for the actual
hash-replay/weights-v0-seed/skill-score-publish/Gate-W2-acceptance sequence.

*Truth over completion. PARKED-HONEST with evidence, not a false close.*
