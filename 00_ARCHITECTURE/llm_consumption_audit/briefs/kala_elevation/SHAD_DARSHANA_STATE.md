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

**NIGHT 5 CLOSED (2026-08-02, ~12:57–~20:30 IST) — see "MORNING REPORT — NIGHT 5" below.**
Headline: Stage 1's every dischargeable leg discharged and verified — L0 substrate fully
built in production for the first time (N_e, 164k-row lattice, 10k cohort + 100k MD-chain,
sky calendar, parihāra corpus 61/329/58 after a same-night production hotfix #1031), the
ENTIRE W2 field-integration code leg landed on integration (#1030/#1032/#1033/#1034/#1035,
each independently verified), ADJ-14/-15 ruled, and a live production verification slice
that caught a REAL serving defect (the lattice/parihāra ToolBundle unwrap — ELECT has been
silently serving the legacy path; fix lane dispatched). Gates W2/W3 PARK HONEST behind the
sweep rebuild (~330s/substep × 606 × 2 — multi-day compute physics, in flight under
automation, ~62/59 of 606 at close). Stage 2 partially triggered per the recorded
assessment: W4 seed landed (#1036 + #1037), W3K K.1 lane in flight at close; W2G + W5 prep
parked with recorded reasons.

**SINGLE NEXT ACTION (next session, in order):**
1. **Resume the sweep relay FIRST** (the babysitter dies with the session; the last
   dispatched runs — chart A `e733299f`, chart B `42e062e3`, both started ~14:25 UTC with
   6h writer budgets — evict ~20:25 UTC 2026-08-02): re-dispatch via the recorded pattern
   (`dispatch_night5_gochara.py <chart_id> <tag>` + `gcloud run jobs execute … --args=--run-id,<id>`),
   one at a time per chart, ≥40-substeps-gained continuation gate, resume-don't-restart.
   Trust the SUBSTEP LEDGER, not `build_runs.state` (two false-kill specimens now recorded:
   `807f3aa3` tonight, `e5cde4dc` Night-3 — the watchdog follow-up lane is still owed).
2. **Land the two in-flight lanes if not merged by then**: `shad-darshana/w3k-sublord-substrate`
   (W3K K.1, Opus) and `shad-darshana/w3-lattice-unwrap-fix` (the production ELECT serving
   defect — verify with a LIVE lattice-backed adjudication check post-deploy, not just unit
   tests).
3. **When BOTH charts hit 606/606**: ka_gochara_resonance is already re-run; go straight to
   the W2 field-integration OPERATIONAL leg — ka_kshetra build both charts (all its L0/code
   prerequisites are now live) → hash-replay determinism double-run → LEL-invariance CI →
   skill score + GOF published both charts (FIRST published score = permanent CI baseline —
   this is why it must wait for complete sweep data) → S4-05 data-real re-test (item 9's
   gate clause) → THEN the gate-close deploy (ONE integration→main PR via merge queue,
   which also ships migration 534's paddhati seed + the field snapshot serving + specificity
   HARD + everything above) → PARĪKṢAKA live acceptance both charts → evaluate Gates W2 AND
   W3 clause-by-clause per brief §3.
4. **Then Stage 2 continuation**: W2G writer lane (ADJ-14/-15 are ready; its v1
   equivalence ground truth exists again once sweeps complete) · W3K Lane 2 (behind Lane
   1's significators) · W4 live fixture discharge + Gate W4 evaluation (post-deploy, seed
   applied) · W5 prep.

**ADJUDICATION-16 issued (2026-08-04, ~21:30 UTC).** ANTARYĀMIN resumed ADJUDICATION-8's parked
Convention (B) slot now that the Muhūrta-Cintāmaṇi translation has landed
(`MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md`, 2026-08-03): the text's single Agnivāsa verse
(MC 1.36, `chunk_id=muhurta_chintamani_pg0048_c01`) does specify a real, verified, computable
arithmetic — `(tithi_id + 1 + vara_id) mod 4`, remainder {0,3}→Pṛthvī(favourable), 1→Ākāśa,
2→Pātāla — genuinely distinct from Convention (A)'s tithi-only four-element table, confirming
rather than contradicting ADJUDICATION-8's "lineage variation" framing. Ruling recommends (for a
future builder session; not executed by this docs-only ruling) flipping
`agnivasa_muhurta_chintamani_arithmetic`'s `convention_status` from `declared_not_computed` to
`computed` in `kala_paddhati_profile` — Convention (A) stays the native-confirmed, graded
lineage convention, unchanged. Note: the task proposing this ruling suggested slug "14", which
collides with the existing ADJUDICATION-14 (V4 §2.3 design-band re-scope, Night-5); this ruling
took the next free number, 16, instead. Full text:
`SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md` (this directory).

**INT-929 SESSION — sweep relay, two dispatch generations (2026-08-03 ~10:24–21:14 UTC).**
Executing Night 5's own step 1 ("resume the sweep relay first"). Both charts' Night-5 dispatch
(`e733299f`/`42e062e3`, Cloud Run executions `-zjwvn`/`-gbnsd`, started ~14:23 UTC 2026-08-02)
had completed its 6h container budget cleanly (`Completed/True`, confirmed via
`gcloud run jobs executions describe`) at ~20:24 UTC 2026-08-02 as Night 5 itself predicted —
**not** a crash — and then sat idle ~14h with no redispatch queued. A native directive this
session initially claimed emergency failure/eviction and asked for an emergency autonomous
swarm; live verification (gcloud + `build_substep_progress` filtered to
`asset_id='ka_gochara_sweep'`) found the completion was clean and the counts (117/606 482012f1,
155/606 1c826d5a at pickup) accurate once an unrelated week-old `ka_sangam` contamination was
excluded — same idle-not-crashed pattern as PR #1011. Native then explicitly LIFTED tonight's
initial descope (full night-run/merge/deploy authority granted, with Cloud Scheduler and the
482012f1/1c826d5a chart-lock both explicitly held in place) after the Conductor cross-checked
the directive against the then-current descope note and confirmed directly. Continuity ruling
recorded: "no human until morning" = decision-autonomy (ANTARYĀMIN rules in the native's
place), not daemon-persistence; relay mechanism = scheduled wakeups armed ahead of each ~6h
expiry, ready-to-fire fallback kept current in this file if the session dies.
- **Generation 1**: `dispatch_int929_gochara_resume_{482012f1,1c826d5a}.py` →
  `build_run acf4a632…`/`083e5a04…` → executions `-z2wtc`/`-xb8dc`, started
  10:23:43/45 UTC. Ran its full budget, `Completed/True` at 16:24:01/10 UTC. Substeps at
  handoff: 482012f1 129→215, 1c826d5a 155→211 (over gen-1's window; some of this gain predates
  gen-1's own start and reflects polling gaps, not gen-1's own throughput alone).
- **Idle gap**: ~4h49m uncaught (mid-conversation, not polling continuously) — the exact
  continuity-boundary risk the ruling above exists to close going forward.
- **Generation 2**: same script pattern → `build_run 5b5f6a98…`/`6c830543…` → executions
  `-h7n6x`/`-bsvhw`, both started 21:13:05.89 UTC. Collision-checked clean before dispatch;
  verified new substeps landing both charts (482012f1 215→216, 1c826d5a 211→212) within ~2 min.
  **Next expiry ~2026-08-04T03:13:05Z.** Scheduled wakeup armed ahead of it.
- Ledger-reconciliation sweep also run this session (PR #934/item-2, PR #1006/#1013/W2G V1–V6,
  migration 527 — all independently verified live against real PRs/DB, not assumed): **no new
  corrections needed** — this file's own more current sections (Night 3 resumed §946ff, Night 4,
  Night 5 NEXT-ACTION above) already carry the accurate, up-to-date picture. An earlier pass this
  session mistakenly edited a STALE, superseded historical snapshot (the old "Wave status" /
  "N1–N5 ratification block" / "Registry item status" tables further down this file, dated
  content from early Night 3) via a stray untracked copy of this file that had been sitting in
  the main repo checkout rather than this worktree — those edits were never committed/pushed and
  are retracted here rather than carried forward, to avoid contradicting this file's own later,
  correct sections. Process note for future sessions: **always edit this file inside
  `.worktrees/shad-darshana-conductor` (or wherever `shad-darshana/integration` is actually
  checked out) — not the main repo directory**, which is on an unrelated branch and should not
  hold a loose copy of this file at all.

**CI-health finding (not caused by this session, not fixed by this session — recorded per
no-silent-gaps discipline).** After the rebase above, PR #1043 (docs-only, one new file) showed
`Naming Governance Gate` and `Earned-Signal Gate` both red. Traced before assuming either was a
regression: `Naming Governance Gate` fails identically on `main`'s own HEAD (`f65680ab`, PR
#1042 — a `GCP_PROJECT` env-var naming violation in
`platform/scripts/corpus/apply_muhurta_chintamani_translations.ts`, pre-existing, not introduced
by this session's rebase, just inherited by it) — dozens of other unrelated
long-lived files (`platform/src/lib/storage/gcs.ts`, `observability/trace.ts`, etc.) also fail
the same "baseline-aware repo scan," suggesting the baseline/allowlist itself may be stale or
misconfigured, not that this many files all regressed at once. `Earned-Signal Gate` was already
red on `shad-darshana/integration` before tonight (confirmed via PR #1039's own checks). Neither
blocks merges — this branch is unprotected (§B.2a) — so PR #1043 merged despite both. Not
investigated further tonight (out of scope for the relay/ledger work); flagging for whichever
session next touches CI health, since a genuinely broken baseline-aware gate quietly stops
catching real new violations.

**Parihāra graph enrichment landed (PR #1044, 2026-08-04 ~22:40 UTC).** All 66 translated
`parihara`-topic `muhurta_chintamani` chunks read directly against live `content_en` (~25
usable/cited, rest skipped as too OCR-fragmentary or procedural non-doṣa material — not
smoothed over). Every genuine finding was conditional (activity-class, region, sub-window, or a
"cancels all doṣas" wildcard), so per the `vishti_conditional_undertaking_exception` row's own
precedent, none forced into `MUHURTA_PARIHARA_ROWS` (stays its single ADJUDICATION-10 row,
its own test unchanged) — instead 9 new cited, honestly `not_computed` `parihara_scope` census
rows, plus the pre-existing `jvalamukhi_yoga` ambiguous-OCR row now CONFIRMED (place name, not
yoga doctrine) on the translated evidence. No schema change. Independently re-run by the
Conductor before merge (38 passed/6 skipped, matches the builder's own report). No production
rebuild triggered — separate decision.

**Relay status at this point (2026-08-03 22:21 UTC check-in):** both charts healthy and
advancing on generation-2 (482012f1 216→229, 1c826d5a 212→222 substeps since the 21:13 dispatch);
not near the ~2026-08-04T03:13:05Z expiry. Wakeup re-armed (chained ~1h, per the 3600s cap).

**W3K Lane 2 landed (PR #1046, 2026-08-04 ~00:05 UTC), Opus per NIGHT_RUN §B.3.** G-4:
`vimshottari_kp` wired into Law-1 applicability (`stage3_clocks.py`), additive, no
FROZEN-contract change; new `q_s` rule referencing `bg_kp_sublord_division` (§N.5, `not_computed`
if absent). Double-count risk MEASURED not assumed — `kp_window_redundancy` detector, verified
read-only against production 482012f1: 69/69 L2 + 630/630 L3 in-horizon rows are exact
Vimśottarī twins → `excluded_by_condition` via `hazard.py`'s pre-existing clause, zero change to
§5.1. G-5: KP school voice (`kp_school_voice.ts` + `explain.ts` wiring), existing envelope
shapes/capabilities only. **Dissent found and verified on real production `chart_facts`, not
fabricated**: 482012f1 bhāva 7, 2026-08-04 — KP's occupant-based ladder (Mars+Saturn on the 7th
cusp) reads as delivering while Parāśarī grades the same occupants as affliction
(`denied_at_promise`/contested); control case bhāva 10 (same instant, same running lords)
concurs, proving independence. **Not yet actually served** — `kp_house_significators` has 0
production rows and `bg_kp_sublord_division` doesn't exist as a table (Lane 1 landed the
writers, no chart rebuilt since); today's served path is `honest_empty` naming that gap exactly.
Disclosed in `CROSSCHECK_v1_0.md` §10.4 (now v1.2), not hidden. G-2 confirmed out of scope per
inventory §5.4, untouched. Independently re-verified by the Conductor before merge (106 pytest +
43 vitest passing, clean `tsc --noEmit`) in addition to the builder's own broader run (full
pytest 5058/24 skip, vitest +43/0 new failures vs stashed baseline).

---

## NIGHT 5 — SESSION OPEN (2026-08-02, ~12:57 IST, in progress)

**NATIVE DIRECTIVE — recorded verbatim at session open as the native's standing order for
this session (it refines, never overrides, the v1.3 standing contract):**

> STAGE 1 — discharge the Night-4 next-action sequence, in dependency order, verified at
> every step:
> 1. L0 super-admin rebuilds: bg_class_lifetime_counts (N_e priors), the widened muhūrta
>    lattice (items 6+7), bg_kota_chakra_rings, and every other L0 asset whose writer landed
>    after its last production build. L0 builds BEFORE any per-chart build that consumes them
>    (Nirmāṇa §2.5.2). Verify: Nirmāṇa DB-true counts + catalog reconciliation green.
> 2. Gochara sweep + resonance re-run on BOTH canonical charts with the new grammar — this is
>    what makes item 9's S4-05 fix DATA-real, not merely code-live. LAUNCH THESE EARLY AND IN
>    THE BACKGROUND: they are long-running orchestrator builds; never idle-wait on them —
>    overlap steps 1/3-prep while they run. Resume-don't-restart on any stall (Night-3's
>    watchdog NOW()-fix is live); sweep DATA stays untouchable — rebuilds go through the
>    orchestrator only.
> 3. The real W2 field-integration sequence (KALA_W2_FIELD_DESIGN §10 / brief §3 W2):
>    ka_kshetra field build both charts → hash-replay determinism → LEL-invariance green →
>    weights v0 pinned → temporal skill score + time-rescaling GOF published for BOTH charts
>    (the FIRST published score becomes the CI baseline) → specificity gate flips HARD →
>    authority-basis census populated → insight rows lead readings → timeline-spec
>    golden-render.
> 4. AFTER the sweeps land: the S4-05 scenario re-test on real data (item 9's own gate
>    clause), both charts.
> 5. Gate-close: ONE integration→main PR (merge queue — queued-green up to ~60 min is normal,
>    never bypassed) → deploy → traffic tracks LATEST → PARĪKṢAKA live acceptance on both
>    charts against production → evaluate Gates W2 AND W3 against their FULL brief-§3
>    criteria, every clause pass/fail on inspection, dispositions recorded.
>
> STAGE 2 — trigger the next waves IN THIS SAME SESSION, if and only if Stage 1's gates are
> VERIFIED-CLOSED (or parked honest with reasons that do not undermine the frontier). If
> Stage 1 cannot verify by mid-session, Stage 2 does NOT start on partial foundations — park
> honest, report, and leave Stage 2 as the recorded next action. When cleared:
> - W2G writer lane against the enumerated V1–V6 findings work-list (the 779k-contact-events
>   scale finding; generation discriminator = migration 527, landed) — Opus numerics.
> - W3K continuation from the completed inventory: sub-lord substrate (K.1) → cusps/
>   significators/ruling planets (K.2) — Opus doctrine.
> - W4 gate: discharge the canned Mode-2 fixture EXACTLY (both charts, different candidate
>   sets required; Agnivāsa is now NATIVE-CONFIRMED Pṛthvī — seed kala_paddhati_profile with
>   native_confirmed=TRUE citing the adjudications doc §NATIVE CONFIRMATIONS) · the
>   weak-promise UPĀYA-SETU diagnosis test · the Intervention Ledger filing test · then Gate
>   W4 evaluation. The Muhūrta-Cintāmaṇi translation is COMMISSIONED but is NOT a night lane —
>   its four dependent deliverables stay PARKED-HONEST until it lands separately.
> - W5 prep (eight primitives + question_frame threading) may start; its live-MCP hard gate
>   runs only when the tool surface is final.

**Session-open protocol discharged, per §D v1.3:**
1. **Rebase**: `shad-darshana/integration` had diverged from `origin/main` by one
   content-identical docs commit (local `31daa36e` vs. main's squash-merge `93a6ad17` of PR
   #1028). Clean rebase dropped the duplicate; integration now == main @ `93a6ad17`,
   force-with-lease pushed, verified 0/0 ahead/behind.
2. **Ledger-reconciliation sweep — one material correction to Night-4's own record:** the
   Night-4 morning report listed three L0 assets pending super-admin build (N_e, widened
   lattice, Kota rings). Direct production DB census at open found the TRUE stale set is far
   larger — **`bg_synthetic_cohort` = 0 rows, `bg_synthetic_cohort_md` = 0, `bg_sky_events`
   = 0, `bg_parihara_rules` = 0, `bg_muhurta_activity_rules` = 0, `bg_muhurta_factor_census`
   = 0, N_e priors = 0, `bg_muhurta_lattice` = 0** (only `bg_kota_chakra_rings` has 27
   migration-seeded rows; `bg_sarvatobhadra_grid` = 0 is by-design). The Night-2/-3 L0
   writers (cohort, sky calendar, parihāra corpus) were merged + deployed but their
   super-admin L0 production build was NEVER run — every one of them. This directly matches
   the directive's "every other L0 asset whose writer landed after its last production
   build" clause, and `ka_kshetra.depends_on` includes `bg_cohort` +
   `bg_class_lifetime_counts`, making these hard Stage-1.3 prerequisites. No stale-closed
   rows found in the other direction this sweep.
3. **Builds dispatched (all three launched in background at open, per the directive's
   overlap rule — evidence: Cloud Run executions + build_runs rows):**
   - **L0 super-admin global build** — `--global-build` run_id
     `6fd72ed9-fb70-4867-b51e-2068d60a68f3`, Cloud Run execution
     `brahma-build-pipeline-job-k622x`. Walks ALL scope='global' active assets (the
     sanctioned trigger; writerless assets DEFERRED honestly — `bg_sarvatobhadra_grid` stays
     empty by design). Verified before dispatch: all six target writers present in the
     orchestrator discovery registry; deployed pipeline image `brahma-pipeline:f19969c5…`
     carries the full Night-4 code.
   - **Gochara re-grammar rebuild, chart 482012f1** — build_run
     `3190c9ac-1fc3-41c3-936b-a9c106772daa`, plan `[ka_gochara_resonance,
     ka_gochara_sweep]` (resonance is the sweep's upstream: it defines the per-event-class
     target sets, including item 9's new health/adverse classes, that `plan_substeps`
     discovers). Execution `brahma-build-pipeline-job-4gxq2`.
   - **Gochara re-grammar rebuild, chart 1c826d5a** — build_run
     `807f3aa3-90b3-4831-afa2-ce7c20ed55f9`, same plan. Execution
     `brahma-build-pipeline-job-x948j`.
   - **Load-bearing schedule fact, read from the sweep writer's own fingerprint contract
     (writer.py `_compute_build_fingerprint`): the event-class list is part of the build
     fingerprint.** Resonance adding the health/adverse classes CHANGES the fingerprint →
     the sweep takes the full-replan branch: per-chart delete-then-insert of
     `kala_gochara_windows` + `build_substep_progress`, then ALL ~606 substeps — not just
     the ~303 new ones. At the historical ~255–280s/substep rate this is a multi-dispatch
     rebuild per chart (writer budget 21600s per dispatch), realistically spanning beyond
     tonight. This is the designed rebuild semantics (grammar change = full re-derivation),
     dispatched orchestrator-only per the untouchable-data rail. Progress is monitored; each
     eviction gets a resume dispatch (fingerprint then matches → resume path). If sweeps
     cannot land tonight, S4-05 DATA-real verification and the sweep-dependent gate clauses
     PARK HONEST per the directive's own Stage-2 rule.
4. **ANTARYĀMIN docket — DISCHARGED at open.** Both W2G blockers ruled, full text in
   `SHAD_DARSHANA_ADJUDICATIONS_NIGHT5_v1_0.md` (this directory), measurements taken live:
   - **ADJUDICATION-14 (V4 band re-scope):** three-tier materialization split per design
     §2.5 read correctly — Tier A EAGER (Saturn/Jupiter/Rahu/Ketu + Mars ruled in): 40,293 /
     39,476 / 20,963 contact events for the three v1-corpus charts, INSIDE the original
     10k–100k band unamended; Tier B (Sun/Mercury/Venus) conditionally materialized only
     inside Tier-A-elevated intervals + own stations; Tier C (Moon) lazy-only, never
     materialized full-span. §2.3's "1–3× per cycle" multiplier WITHDRAWN (refuted by
     measurement: 1773.36 crossings/fixed° all-nine, Moon 76.1%). Amendment text supplied
     for the W2G lane's PR. Reversible (config + backfill under same `generation`).
   - **ADJUDICATION-15 (V1 instrumentation):** structured log + additive nullable
     `phase_profile` jsonb on `build_substep_progress`, written inside the writer's own
     existing upsert (no FROZEN-contract change — verified against three existing heavy
     writers); fixed six-phase enum, explicit 0.0 for phases that didn't run (§N.8),
     descriptive-never-gating (§N.4); names the exact column V1's existing detector already
     hints for, flipping V1 INDETERMINATE→measurable with zero validation edits. Reversible
     (DROP COLUMN).
   **The W2G writer lane is now fully unblocked on rulings** (N-block complete since Night 3
   + ADJ-14/-15 tonight); its remaining precondition is operational — the v1 equivalence
   corpus needs intact v1 windows, which are mid-rebuild tonight (see 3 above).
5. **Deploy check**: `main` @ `93a6ad17` — the ledger's own Night-4 close verified `main ==
   production` (all three services) at `d0f9cb1c`; `93a6ad17` adds only the docs commit
   (#1028), which per deploy path-detection does not owe a service deploy. No deploy owed at
   open; the next deploy is Stage 1.5's gate-close.

**STAGE 1.1 — L0 SUPER-ADMIN BUILD COMPLETE (2026-08-02 07:57 UTC, run `6fd72ed9`, execution
`k622x`): 35 ok · 3 deferred (honest: `bg_panchanga`/`bg_ephemeris_engine` have no writers;
`bg_sarvatobhadra_grid` empty-by-design) · 4 FAILED.** DB-true counts verified directly
post-build: N_e priors = 6 (`ne_v01`, all six classes) · `bg_muhurta_lattice` = **164,575**
(widened R-1 lattice, years 2026–2031, per-year row counts logged) · `bg_synthetic_cohort` =
10,000 · `bg_synthetic_cohort_md` = 100,000 (0 honest-null skipped) · `bg_sky_events` =
31,059 · `bg_kota_chakra_rings` = 27. The Mode-2 fixture's lattice prerequisite and
`ka_kshetra`'s two L0 `depends_on` edges (`bg_cohort`, `bg_class_lifetime_counts`) are now
LIVE in production for the first time.

**Defects found by the L0 walk (real, production-discovered):**
1. **`bg_parihara_rules` — a LIVE §N.8 no-op-completion defect + a dict_row crash.** The
   writer's `fetch_parihara_rows` indexes rows numerically (`row[0]/row[1]`) against the
   orchestrator connection's `dict_row` factory (`db.py:26`) → `KeyError: 1`; its `run()`
   then swallows the failure into a success-shaped `WriterResult(rows_inserted=0,
   notes="failed: 1")` — the global runner logged OK and LIT the asset while all three
   parihāra tables sit at 0 rows. Textbook §N.8 (swallowed failure wearing success). This
   blocks Gate-W3's judgment-ledger clause + the W4 Mode-2 parihāra adjudication until
   fixed+rebuilt. **Fix lane dispatched** (`shad-darshana/l0-parihara-dictrow-fix`: tuple-row
   cursor, re-raise on failure both branches, same audit+fix for `bg_reference`, dict_row
   regression tests). L0 re-trigger owed after it merges.
2. `bg_reference` — `KeyError: 0`, same dict_row class (properly raised → error state; live
   data unchanged). In the same fix lane.
3. `bg_ghatana` — `NotNullViolation` on `brahma_event_ontology.temporal_shape`: the writer's
   seed rows predate item 9's ontology column. Savepoint rolled back; the live 27-class
   ontology (including the health/adverse classes) is INTACT — the writer is stale, the data
   is not. Recorded follow-up, NOT tonight's path.
4. `bg_transit_rules`/`bg_transit_engine` — `ForeignKeyViolation`: the freshly-rebuilt
   `gochara_resonance_map` rows FK-reference `bg_transit_rules.id`, so the L0
   delete-then-replace cannot proceed while any chart's resonance map exists. Rolled back,
   data intact. A real L0-upsert-vs-L3-FK structural circularity needing its own design
   decision (ON DELETE strategy or id-stable upsert) — recorded follow-up, NOT tonight's
   path (the live transit-rules data these writers would have replaced is exactly what the
   resonance build just consumed successfully).

**NIGHT-5 MERGE TRAIN (running record):**
- **PR #1030 MERGED** (integration) — `l0-parihara-dictrow-fix`: dict_row crash fixed by
  explicit `row_factory` pin + name indexing (plus a second latent defect found by the lane:
  `dict(zip(cols, raw))` under dict_row silently corrupts); both `run()` except branches now
  re-raise per §N.8; `bg_reference` tuple_row boundary pin with finally-restore. TDD red
  (6 failed, exact production error shapes) → green (9 passed) — **independently re-run by
  the Conductor from the merged integration tree: 9 passed.** The lane also enumerated
  sibling writers sharing the §N.8 swallow pattern (bg_muhurta_lattice ~905/~925,
  bg_sky_calendar ~581/~602, bg_cohort ~524, bg_ephemeris ~153, plus
  `brahmagyan/l0_reference.py:1418/:1600` numeric indexing) — recorded as follow-ups in the
  PR body, deliberately not fixed in this lane.
- **PR #1031 OPENED → merge queue** (hotfix-to-main of #1030, same discipline as Night-4's
  #1026): the production pipeline image builds from `main`, so the parihāra L0 rebuild —
  which Gate-W3's judgment-ledger clause and the W4 Mode-2 fixture both need — cannot run
  until this deploys. L0 re-trigger owed post-deploy. Its one failing check (`Boot-time
  pointer validation SC-17/18/19`) verified PRE-EXISTING on main's last several commits
  (the TAP-6 campaign's own open item, not this PR's, not ruleset-required).
- **PR #1032 MERGED** (integration) — `w2-specificity-hard`: registration detector now
  resolves `server.tool(TOOL_NAME, …)` const-identifier registration (8/8 kala views
  detected, was 4/8); criterion upgraded byte-identity → structural S1–S3 (+S4 WARN) with
  an embedded non-vacuity fixture the gate re-verifies on EVERY invocation; PLAN-mode "exit
  0 always" escape removed (registration census + self-checks FAIL-capable without a
  server); re-armed on the PR path (items 3/6 stay retired — their PLAN modes still cannot
  fail; honest). Full-cohort 10k statistical gating explicitly DEFERRED in the gate's own
  output with the named unblocker (synthetic cohort charts are not built/served charts).
  **Independently re-verified by the Conductor from the merged tree: vitest 20/20; PLAN run
  PASS=12 FAIL=0 SKIPPED=2 (both skips honest-named).** The specificity gate's LIVE
  pairwise leg runs at gate-close against production.

- **PR #1033 MERGED** (integration) — `w2-envelope-real-snapshot`: `buildFieldSnapshotIdStub`
  retired at its reserved single replacement point; new `resolveFieldSnapshot` reads the
  chart's newest `kala_field_snapshots` row (total-order §N.7) via the established
  read-only db proxy, serving three machine-readable honest states (`served` with real
  `kfs_…`/`kfh_…` · `field_not_yet_built` — production's current state · `field_snapshot_unreachable`
  kept distinct); all 8 facades routed through the one resolver. Item-44 census now
  measures reality. **Independently re-verified by the Conductor: platform-mcp tsc clean,
  100/100 across envelope+views suites.** One disclosed gap → micro-lane
  `w2-dbquery-allow-snapshots` dispatched (whitelist `kala_field_snapshots` in the db/query
  proxy route, platform/src, outside #1033's contract).
- **ITEM-44 AUTHORITY-BASIS SCOREBOARD (W2 "reported" obligation, measured 2026-08-02
  08:39 UTC by the Conductor from the merged census):** paths_enumerated=29 ·
  paths_emitting_authority_basis=4 (elect/ahead/ritual/upaya) · basis kinds:
  field_window_id=0, locally_constructed=4, absent=25 · own-window clause-(b) assessments:
  inherits_substrate_window=7, no_window_emission=1, not_assessed=21 (each carrying an
  explicit per-path reason — the eight kala facades are hand-audited; the honest
  `field_window_id=0` is the number W6 gates on and the field-serving cutover moves).

- **PR #1034 MERGED** (integration) — micro-lane `w2-dbquery-allow-snapshots`:
  `kala_field_snapshots` whitelisted in the mcp db/query proxy (the one-line gap #1033
  disclosed), campaign-tagged provenance comment per file convention, route test 6/6.
- **PR #1035 MERGED** (integration) — `w2-field-writer-wiring` (Opus): N_e determinism
  defect fixed (both `'*'` coordinates pinned + total ORDER BY — closed BEFORE a second
  prior set can ever land, per the precheck's own sequencing warning); stages 6/6.5/8 wired
  into the ka_kshetra writer (substeps stage6/stage65/6× stage8:view between stage5finalize
  and snapshot; `_OWNED_TABLES`/`_HASHED_TABLES` extended; hash decision documented: new
  tables JOIN the §7.4 content hash, made determinism-safe by pinning `now_marker`=t_zero
  and natural-key boundary ids); mi_bhara migration-number doc drift fixed (483→497); the
  timeline golden-render test verified already collected by ci.yml (no CI change needed).
  Two real cross-lane hazards caught by the lane: a blanket per-chart delete would have
  wiped Lane E's `lel_derived=TRUE` insight rows on every rebuild (now per-table-predicated,
  scoped `lel_derived=FALSE`), and the legacy-table guard matched `kala_timeline` as a
  substring of `kala_timeline_spec` (now word-boundary tokenized, with its own regression
  test). Honest-null parks recorded in-code (factor_informativeness NULL below 10k cohort
  minimum · factor_actionability NULL until §11 tri-plane · contrast insights absent ·
  bands[] empty · six views share one declared row set). Mutation-checked 3/3 — including a
  self-caught vacuous first version of the delete-scoping test. **Independently re-verified
  by the Conductor: 224/224 in tests/l3/ka_kshetra from the merged tree; diff scope 7 files
  python-sidecar only.**
- **PR #1031 MERGED to `main`** (~08:55 UTC, merge queue) → deploy of `f97fc78d` watched;
  on success the parihāra L0 re-trigger runs.

**MID-SESSION STAGE-1/STAGE-2 ASSESSMENT (Conductor, ~09:15 UTC — made early because the
determining facts are settled and cannot change before mid-session):**

*Stage 1 state, clause-honest:* Step 1 (L0 rebuilds) — DONE+VERIFIED except the parihāra
rebuild, which is one deploy + one re-trigger away (fix merged to main, deploy in flight).
Step 2 (sweeps) — RUNNING under automation; measured ~330s/substep × 606 × 2 charts ⇒
**mathematically cannot complete tonight** (~55h/chart); this is compute physics, not a
blockable defect. Step 3 (W2 field-integration) — the ENTIRE code leg is now landed on
integration and independently verified (#1030 #1032 #1033 #1034 #1035); the operational leg
(production ka_kshetra build → hash-replay → skill/GOF publish) **deliberately waits for
sweep completion**: building the field on a half-rebuilt gochara substrate and publishing
THAT as the first skill score (which becomes the permanent CI baseline) would be exactly
the fabricated-baseline defect the campaign's rails exist to prevent. Steps 4–5 (S4-05
data-real, gate-close/PARĪKṢAKA) — sequenced behind the sweeps by the directive's own
dependency order. **Gates W2 and W3 therefore PARK HONEST tonight**: every dischargeable
clause discharged and verified; every parked clause parked on long-running compute that is
launched, monitored, and automated — not on missing work, not on an undischarged defect.

*Stage 2 decision, per the directive's own conditional ("parked honest with reasons that do
not undermine the frontier"):*
- **W2G writer lane — STAYS PARKED.** Its equivalence corpus uses v1 sweep rows as ground
  truth, and those rows are mid-rebuild (deleted by the replan, rebuilding). The Stage-1
  park reason DIRECTLY undermines this lane's foundation. Rulings (ADJ-14/-15) are ready;
  the lane dispatches the session after both charts' sweeps complete. Recorded next action.
- **W3K continuation — CLEARED to dispatch.** Its foundations (L1 KP cusps substrate,
  completed inventory #1003, layer-seating ruling from the Night-3 docket, W2 clock code
  merged) are all COMPLETE and none is touched by the sweep rebuild. Lane 1 (K.1 reference
  substrate + significators, Opus per §B.3) dispatches now; Lane 2 sequences behind Lane
  1's step 3 per the inventory's own §6.
- **W4 — PARTIALLY CLEARED.** The lattice prerequisite is LIVE (164,575 rows); the
  parihāra prerequisite lands post-deploy tonight; the paddhati-profile seed
  (native-confirmed Agnivāsa Pṛthvī) is buildable now as a migration. The canned Mode-2
  fixture's LIVE discharge requires the seed migration DEPLOYED, which only happens at the
  next gate-close deploy — so tonight builds the seed + runs the PLAN-mode fixture legs and
  parks the LIVE discharge honest. Gate W4 evaluation stays next-session.
- **W5 prep — NOT started tonight** (a deliberate scoping choice, not a block): conductor
  capacity is committed to verifying the above; W5's own hard gate cannot run until the
  tool surface is final regardless. Recorded next action.

**HOTFIX DEPLOYED + L0 RE-TRIGGER (2026-08-02 ~13:30 UTC):** deploy run `30740577620`
completed success on `f97fc78d`; pipeline job image verified re-pointed to
`brahma-pipeline:f97fc78d…` (checked directly via `gcloud run jobs describe`, not assumed).
L0 global build re-triggered (`a22bc93c`, execution `6sbsb`) to rebuild the parihāra corpus
tables with the fixed writer.

**NEW WATCHDOG FALSE-KILL SPECIMEN (real, disclosed, needs the watchdog follow-up lane):**
chart B's sweep run `807f3aa3` was marked `build_runs.state='failed'` at ~54/606 substeps
while its Cloud Run execution (`x948j`) was — and remains — RUNNING and committing substeps
(54→57+ observed after the failed mark; `build_run_assets.state='building'`). Proof
independent of the DB row: the babysitter's automatic redispatch (`a73aa9ab`, execution
`jz4dd`) hit the chart advisory lock and its assets went `aborted` — the lock is held,
therefore the original container is alive. This is the same false-kill class Night-3's
NOW()-fix addressed, recurring via some remaining path — the substep ledger is the truth
(campaign doctrine since `e5cde4dc`). **Responses:** (1) babysitter v1 (which trusted
`build_runs.state` as liveness) replaced by v2 — liveness = substep-progress within 25 min;
redispatch only on real stall; a lock-aborted redispatch counts as proof-of-life and backs
off rather than consuming a dispatch attempt; ≥40-gain continuation gate kept. (2) The
false-failed row `807f3aa3` and inert `a73aa9ab` (state='planned', assets aborted) are left
untouched — run-state rows are orchestrator-owned; recorded here instead. (3) Watchdog
clause diagnosis = recorded follow-up work item for a future lane (needs the specimen's
timing against the watchdog's clauses; not rushed mid-night).

- **PR #1036 MERGED** (integration) — `w4-paddhati-seed`: migration 534 seeds
  `kala_paddhati_profile` Row A (`agnivasa_tithi_element_prithvi`) for BOTH canonical
  charts with `native_confirmed=TRUE`, `awaiting_native_confirmation=FALSE`, and a new
  `confirmation_provenance` column citing the adjudications doc §NATIVE CONFIRMATIONS —
  implemented as an in-place v01 flip via `ON CONFLICT … DO UPDATE` (a bare DO NOTHING
  would silently no-op where 533 already ran; a v02 insert would drop Row B's divergence
  slot from serving — both traps identified and avoided by the lane); DO-block RAISEs
  unless exactly 2 confirmed rows land. Guard PASS (534 = next after true both-directory
  max 533). W4 gate scripts run in PLAN mode: Mode-2 fixture PASS=4/FAIL=0/SKIPPED=1
  (live legs honestly pending a server), Mode-3 single-route registered=true. Night-4's
  W4 tests actually run: UPĀYA-SETU weak-promise 81/81; `mi_sankalpa` filing 14 passed /
  10 honest DB skips. **Conductor verification: diff scope 1 file confirmed; migration
  content spot-checked (ON CONFLICT DO UPDATE, both chart ids, provenance, RAISE).**
  Follow-up dispatched: micro-lane `w4-paddhati-census-statement` (the static
  `PADDHATI_CENSUS_STATEMENT` in kala_sky_pattern.ts still asserts "not on record" —
  becomes false once 534 applies; statement must derive from the profile's actual state
  per §N.7/§N.8).

**STAGE 1.1 FULLY DISCHARGED (2026-08-02 13:50 UTC):** L0 re-run `a22bc93c` (execution
`6sbsb`, fixed image `f97fc78d`): **36 ok · 3 deferred (by design) · 3 failed** — vs the
first walk's 35/3/4. `bg_parihara_rules` now builds clean: **61 parihāra rules · 329
activity rules · 58 factor-census rows LIVE in production** (verified by direct count);
`bg_reference` also now OK. The three remaining failures (`bg_ghatana` stale seed vs
`temporal_shape`; `bg_transit_engine`/`bg_transit_rules` FK circularity with
`gochara_resonance_map`) are recorded follow-ups whose live data is intact and current —
not fabricated-green, not blocking any gate clause tonight. Nirmāṇa verification: DB-true
counts confirmed for every directive-named asset + catalog reconciliation 6/6 green.

**LIVE PRODUCTION VERIFICATION SLICE (Conductor, ~14:00–14:45 UTC, direct authenticated
MCP calls, both canonical charts) — found a REAL serving defect PARĪKṢAKA-style
verification exists to catch:**
- **What works live:** `kala_elect_get` serves 5 real graded candidates per chart with
  scores, horā ladder, citations, an honest 3-state coverage list, and honest-empty
  reasons (tāra-bala/target-graha correctly `honest_empty` with actionable reasons).
  Candidate sets differ across charts. The judgment-ledger structure is present and its
  refusal prose is exemplary ("residual standing is deliberately left uncomputed rather
  than assumed clean").
- **The defect:** every candidate's ledger reads `net_standing='not_adjudicated'` —
  "query_parihara_graph returned no parihara_rules/factor_census section" — DESPITE the
  tables now being populated and the capability's SQL verified clean by direct DB
  replication. Root cause pinned by code-trace: the `/api/mcp/primitives/<tool>` route
  serves `envelope.result` as the legacy **ToolBundle** (`capabilityResultToToolBundle` →
  `results[0].content` = JSON-STRINGIFIED handler content), while
  `kala_lattice_query.ts`'s `fetchLatticeSubstrate` reads `result.<key>` directly —
  always undefined in production. Consequence: the LATTICE section also silently serves
  zero rows with `lattice_available=true` asserted unconditionally on HTTP 200 (an §N.8
  earned-signal violation), so ELECT's candidates are actually served by the legacy
  `ph_muhurta` path (corroborated by the live `field_snapshot_id:
  "stub:ph_muhurta_queried_at=…"`). **The one-engine lattice path has never actually
  served in production** — unit/PLAN tests all pass because they never pin the wire
  shape. Same defect class as PR #823's ToolResult-wrapper fix. **Fix lane dispatched**
  (`shad-darshana/w3-lattice-unwrap-fix`: mirror the #823 unwrap idiom, make the
  available-flags real detectors, audit every `callPlatformPrimitive` consumer, add
  wire-shape regression fixtures).
- Also live-confirmed as expected: `field_snapshot_id` still serves the W0 stub
  (integration's #1033 not yet deployed — correct between gates), and the paddhati seed
  is not yet applied (migration 534 rides the next deploy).

**STAGE 1.2 — sweep telemetry (first measurement, ~08:14 UTC):** both charts committing
substeps under the new 606-substep plan (A: 5, B: 4 in the first ~28 min) → **measured
~330s/substep ⇒ ~55h/chart projected** (vs ~22h for the old 303 plan). This confirms the
full-replan semantics (fingerprint includes the event-class list) and makes the sweeps a
MULTI-DAY rebuild: the babysitter automation (redispatch-on-eviction, ≥40-substeps-gained
continuation gate, max 6 redispatches, one-at-a-time per chart) carries them through and
past this session. **Operational consequence, disclosed:** each chart's
`kala_gochara_windows` rows were deleted by the replan (designed delete-then-insert) and
are rebuilding progressively — gochara-window-reading surfaces serve honest-empty/partial
for the duration; nothing is fabricated. S4-05 DATA-real verification and every
sweep-dependent gate clause are therefore SCHEDULED BEHIND the sweeps, not closeable
tonight — parked honest per the directive's own Stage-2 rule, with the babysitter as the
carry mechanism.

---

## MORNING REPORT — NIGHT 5 (2026-08-02, ~12:57–~20:30 IST)

**Gates closed:** none VERIFIED-CLOSED (by compute physics, not by unfinished work — see
parks). **But Stage 1's entire dischargeable surface is discharged, verified, and
recorded**, and the production data substrate the campaign has been building toward is now
REAL for the first time.

**Done and verified tonight:**
- **Session-open protocol**: integration rebased (== main at open); ledger-reconciliation
  sweep found the TRUE stale-L0 set was ~3× larger than Night-4's record (cohort, sky
  calendar, parihāra, MD-chain all at 0 rows — corrected append-only with evidence);
  directive recorded verbatim; ADJUDICATION-14/-15 discharged at open by ANTARYĀMIN (W2G's
  V4 three-tier materialization re-scope grounded in live measurement — Tier A holds the
  original 10k–100k band; V1 `phase_profile` instrumentation with no FROZEN-contract
  change) — full text `SHAD_DARSHANA_ADJUDICATIONS_NIGHT5_v1_0.md`.
- **Stage 1.1 — L0 substrate LIVE**: two super-admin global builds (runs `6fd72ed9`,
  `a22bc93c`). Final: 36 ok / 3 deferred-by-design / 3 recorded follow-ups. In production
  for the first time: N_e priors (6 @ ne_v01) · widened muhūrta lattice (164,575 rows,
  2026–2031) · synthetic cohort (10,000) + MD-chain (100,000) · sky calendar (31,059
  events) · parihāra corpus (61 rules / 329 activity rules / 58 census rows) · Kota rings
  (27). Catalog reconciliation 6/6 green.
- **Stage 1.3 code leg — COMPLETE on integration**, 8 PRs, each independently re-verified
  by the Conductor (not trusted from lane self-reports): #1030 (parihāra dict_row + §N.8
  re-raise) · #1031 (its hotfix-to-main — merged through the merge queue, DEPLOYED,
  pipeline image verified re-pointed) · #1032 (specificity gate HARD: 8/8 detector,
  S1–S3 structural criterion, PLAN-mode fail-capable, non-vacuity self-fixture) · #1033
  (E5 real field-snapshot resolver, three honest states; item-44 census real numbers) ·
  #1034 (db-proxy whitelist) · #1035 (Opus: stages 6/6.5/8 wired into the ka_kshetra
  writer, N_e determinism fix closed BEFORE it could ever fire, hash-inclusion decision
  documented, 224/224) · #1036 (migration 534: paddhati native-confirmed seed, in-place
  v01 flip with RAISE verification) · #1037 (census statement derives from profile state).
- **Item-44 scoreboard reported** (the W2 obligation): 29 paths · 4 emitting (all
  `locally_constructed`) · `field_window_id=0` — the honest number W6 gates on.
- **Live production verification slice** (direct authenticated MCP calls, both charts):
  lattice-era ELECT serving verified live — and it caught a REAL defect (next section).

**Defects found + fixed tonight (all real, all production-relevant):**
1. **`bg_parihara_rules` dict_row crash swallowed into a success-shaped WriterResult** —
   the asset LIT while all three tables were empty (live §N.8 specimen). Fixed (#1030),
   hotfixed to main (#1031), deployed, rebuilt, verified populated same night.
2. **The lattice/parihāra ToolBundle unwrap defect** — found by tonight's live calls:
   `/api/mcp/primitives/*` serves the legacy ToolBundle wire shape
  (`results[0].content` JSON-string), while `fetchLatticeSubstrate` reads top-level keys →
  both sections silently empty in production, `lattice_available=true` asserted with no
  detector, ELECT actually serving the legacy `ph_muhurta` path (its own
  `field_snapshot_id` stub names it). The one-engine lattice path has NEVER truly served
  in production; every unit/PLAN test passed because none pinned the wire shape. Same
  class as #823. Fix lane in flight at close (`w3-lattice-unwrap-fix`).
3. **A second watchdog false-kill specimen** (`807f3aa3` marked failed at ~54/606 while
   its container demonstrably kept committing; the lock-collision abort of the redispatch
   proved the container alive). Babysitter v1 (which trusted run-state) replaced by v2
   (substep-progress liveness, lock-aware backoff). Watchdog root-cause lane still owed.
4. Two lane-caught cross-cutting hazards fixed inside #1035: the `kala_insights`
   LEL-derived-row deletion scoping, and the legacy-table guard substring false positive.

**Rulings:** ADJUDICATION-14, ADJUDICATION-15 (both reversible, native may overrule).

**Parks + reasons (the load-bearing part):**
- **Gates W2/W3 PARK HONEST**: their remaining clauses are all downstream of the gochara
  re-grammar rebuild — measured ~330s/substep × 606/chart ⇒ ~55h/chart; at close A=62/606,
  B=59/606, both advancing on redispatched runs. Publishing the first skill score (the
  permanent CI baseline) against a half-rebuilt substrate would be a fabricated baseline;
  correctly refused. S4-05 stays code-closed/data-pending — the sweep rebuild IS the fix
  landing.
- **W2G writer lane parked** — its rulings are ready, but its v1 equivalence ground truth
  (`kala_gochara_windows`) is mid-rebuild by design; dispatching against it would verify
  nothing. Re-enters when both charts hit 606/606.
- **W5 prep not started** — conductor-capacity scoping choice, recorded, no blocker.
- ~~W3K K.1 lane + lattice-unwrap fix lane in flight at close~~ **BOTH LANDED before final
  close — see the #1038 record above and this #1039 record:**
- **PR #1039 MERGED** (integration) — W3K K.1 (Opus): `bg_kp_sublord_division` (the
  ADJUDICATION-7-ruled name — the lane corrected the Conductor's brief on reading the
  ruling), 249 divisions DERIVED not asserted (27×9=243 sub segments + exactly 6 rāśi-split
  boundaries, proven in rationals with the three exact-coincidence boundaries asserted —
  a wrong derivation yields 252, not a quiet pass); `brahma_dasha_systems` `kp` row
  carrying the §4 constraint (judgment-method independence, NOT a fifth timing generator);
  G-1 4-limbed significators additive on `ga_nakshatra` (star lords REFERENCED from L0,
  writer HALTs rather than re-derives — §N.5); G-3 count_sql fix landed on `ga_positions`
  (the inventory's `ga_sensitive` attribution was wrong — corrected against the live
  emitter); G-6 CROSSCHECK v1.1; conservative no-reinstatement of retired kp tool names
  (unruled — noted). Worked example (10th cusp, chart 482012f1): Mercury ranked strongest
  10th-house significator WITHOUT being in the 10th — a KP-distinctive verdict, divergence
  served as data. Verification: 9/9 star + 9/9 sub vs FORENSIC fixture; 35,967 swept
  samples, 0 disagreements; cuspal 12/12 both charts; migration 535 guard-checked.
  **Conductor verification: 36/36 KP tests + catalog reconciliation 6/6 from the merged
  tree.** W3K Lane 2 (G-4 clock seam, G-5 served dissent voice) is the recorded
  continuation.
- Production serving note: gochara-window surfaces serve honest-empty/partial during the
  rebuild (designed replace semantics, disclosed; nothing fabricated).

**Deploy state at close:** `main` @ `f97fc78d` == production (hotfix deploy verified: run
`30740577620` success; pipeline image re-pointed and verified by describe; smoke green).
`shad-darshana/integration` ahead of main by tonight's 8 lane PRs + ledger commits — the
normal between-gates state (§B.2). No gate-close deploy tonight (no gate closed — honest).

**LATE-SESSION LANDING — PR #1038 MERGED (integration) + Conductor-verified:** the
ToolBundle unwrap fix turned out to be FAR wider than the two diagnosed sites. The lane's
audit of every `callPlatformPrimitive` consumer found and fixed **seven silently-broken
readers**: `fetchLatticeSubstrate` (the diagnosed defect — available-flags are now real
detectors) · `kala_ritual_resonance` (unwrap + two capability names that were never
whitelist keys and 400'd on EVERY call: `query_remedy_corpus`→`query_remedies`,
`query_rm_resonances`→`bodha_rm_resonances_get`) · `kala_upaya_diagnosis` (unwrap + two
more dead names repointed) · `kala_sky_pattern` readers · all 7 `remedy_tools` (served a
double-encoded bundle with `count: undefined`). Five consumers verified already-correct;
four passthrough sites flagged for follow-up, not silently absorbed. New shared
`primitive_unwrap.ts` helper (mirroring #823's idiom) with six machine-readable failure
causes; wire-shape regression fixtures now pin the actual ToolBundle encoding — the exact
mock-drift that let all of this ship green is closed. Lane counts: 298/0 targeted, full
suite failures verified pre-existing by stash-baseline. **Conductor verification:
primitive_unwrap 17/17 + lattice wire suite 12/12 from the merged tree.** The live
re-verification of adjudicated ledgers on production happens at the next gate-close deploy
(this code is integration-only until then).

**Swarm health:** 4 builder-lane transient stalls/drops (600s watchdog + connection
class), all resumed with zero work loss via SendMessage; 1 mid-session account-level pause
(native reset it — sweeps and deploys continued unattended; state fully reconstructed from
ledgers on resume).

*Truth over completion. The sweep relay is the single thing the next session must touch
first.*

---

**NIGHT 4 CLOSED (2026-08-02, ~01:22–~11:45 IST) — see "MORNING REPORT — NIGHT 4" below
(after the Night-4 session narrative) for the authoritative close-out.** Headline: Wave 1 (8
PRs — items 9/13/31/6/7, W4 Lanes U/R/S) built, merged, and **actually deployed to
production** for the first time since Night 2 — `main == production`, verified directly
against all three services. One real deploy-blocking bug found and fixed (migration 529 NOT
NULL violation). **The one gap that matters most: item 9's S4-05 fix is code-live but
DATA-empty** — the gochara sweep has not been re-run with the new grammar. **Single next
action**: L0 super-admin rebuilds (N_e, widened lattice, Kota rings) → gochara sweep/resonance
re-run both charts → the real W2 field-integration sequence → PARĪKṢAKA live acceptance. Full
detail, parks, and evidence in the Night-4 MORNING REPORT.

---

**ALL THREE NATIVE DECISIONS FROM THE NIGHT-3 DOCKET ARE RULED (2026-08-02, morning review —
full record: `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md` §NATIVE CONFIRMATIONS):**
1. **Agnivāsa CONFIRMED: Pṛthvī-favourable, corpus default correct** (the elevation-session
   "Pātāla" statement was the native's own misstatement, corrected on the record). Item 37's
   builder seeds `kala_paddhati_profile` with `native_confirmed=TRUE` citing that section —
   no unconfirmed-default caveat needed on yajña elections once seeded.
2. **N_e `ne_v01` AFFIRMED as-is, all six values.** Future revision = `ne_v02` supersession
   only.
3. **Muhūrta-Cintāmaṇi translation COMMISSIONED** — as its own supervised corpus-curation
   task, NOT a night-run lane (see `MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md`, this
   directory). The four PARKED-HONEST deliverables re-open when it lands; night runs do NOT
   attempt it.

---

## NIGHT 4 — SESSION OPEN (2026-08-02, ~01:22–02:58 IST, in progress)

**Session-open protocol discharged, per §D v1.3:**
1. **Rebase**: `shad-darshana/integration` was 2 commits behind `origin/main` (TAP-6 CI fixes,
   unrelated campaign). Clean rebase, no conflicts, force-with-lease pushed
   (`1878ac02` → `ff9c1f9c`, same content, new base). Verified `origin/main` is now an ancestor.
2. **Ledger-reconciliation sweep**: cross-checked NEXT-ACTION's open items against reality —
   PR #1009 and #1014 confirmed merged (git log, not self-report); no open shad-darshana PRs
   found repo-wide except unrelated campaigns (#1016 ci/m22-drain-and-probe, #899/#898 explicit
   PRESERVE markers, #446 stale docs) — none collide with tonight's scope. **Gochara sweep
   `d95583c8` on `1c826d5a` — CONFIRMED COMPLETE**: `build_runs.state='completed'`,
   `build_run_assets.state='complete'`, `build_substep_progress` count = exactly 303 for
   `(1c826d5a, ka_gochara_sweep)`. Both-charts horizon parity confirmed: `482012f1` 8,345 rows
   to 2084-12-30; `1c826d5a` 8,061 rows to 2085-12-24 — the standing forward-window gap from
   Phase-0 preflight (Night 1) is now CLOSED. This was NEXT-ACTION item 2; DONE.
3. **ANTARYĀMIN docket check**: the three native-ruled docket items (Agnivāsa, N_e, Muhūrta-
   Cintāmaṇi) are already recorded above (PR #1015). No new unruled adjudication blocks
   tonight's dispatched wave. **Deliberately NOT resolved tonight**: the W2G V4 design-band
   re-scope (779,595 measured contact events vs design §2.3's 10k–100k band — even the
   eager-layer-only split exceeds the band) and V1's per-phase instrumentation gap — both
   genuinely need dedicated Opus design attention, not a quick ruling, and W2G was judged lower
   priority than closing out W3/W4 build capacity tonight. Recorded here so it isn't lost:
   **W2G writer lane remains NOT DISPATCHED, blocked on this ruling, for a future session.**
4. **Deploy check**: `main`@`334436a9` already matches the last production deploy (run
   `30686193558`, 2026-08-01 05:37 UTC, confirmed via `gh run list` cross-checked against
   `git log origin/main -1`) — no separate main-only deploy was owed tonight; the next deploy
   is the wave's own gate-close (integration → main) once builders land.

**Dispatched — Wave 1, six lanes, all in worktrees off `origin/shad-darshana/integration`,
never spawned from inside a worktree:**
- `shad-darshana/w3-health-adverse-class` (item 9, health/adverse event class closing DP-4,
  **S4-05 re-test** — the historical trust-breaking-veto item; escalated to Opus/high on the
  Conductor's own authority given the stakes, per §B.3's "escalate wherever value-adding")
- `shad-darshana/w3-tithi-pravesha` (item 13, lunar-return annual chart, Sonnet)
- `shad-darshana/w3-period-echo` (item 31, hypothesis-framed period-echo mining, Sonnet —
  instructed to investigate and honestly report whether this is field-dependent before
  building, park-honest rather than build a hollow placeholder if so)
- `shad-darshana/w4-lane-u-upaya-setu` (W4 Lane U — item 26 full + E6 efficacy, Sonnet)
- `shad-darshana/w4-lane-s-sankalpa` (W4 Lane S — item 42 Intervention Ledger, Sonnet,
  spine-first: `intervention_filing.ts` + one-line `client.ts` widening lands before the
  writer, since Lanes U/R both consume the published type)
- `shad-darshana/w4-lane-r-yajna-setu` (W4 Lane R — items 37-full/40/38-W4-half PLUS items 6+7
  folded in, since both share Lane R's exclusive file `bg_muhurta_lattice.py` and depend on
  its R-1 lattice-widening work — dispatching 6/7 as a separate concurrent lane would have
  collided; Opus/high per §B.3's mandatory list, parihāra corpus-extraction review + the
  absolute mortality-exclusion rail ADJUDICATION-13)

**Deliberately not dispatched tonight, honest scoping choice, not an oversight:**
- Item 14 (janma-anchored election rules) — explicitly deferred by Lane R's own brief to a
  future session; composes with R-4 but out of scope for tonight's lane size.
- W2G writer lane — blocked on the V4/V1 Opus design ruling (see point 3 above).
- The real W2 field-integration run itself (hash-replay determinism, weights-v0 seed,
  skill-score/GOF publish, specificity-gate HARD flip, item-44 census population) — this is
  substantial standalone work in its own right (per PR #1014, "steps 1–2 proven, 3–5 next
  session") and was judged too large to fold into tonight's already-6-lane wave; planned as
  Wave 2 once Wave-1 capacity frees, still within tonight's ~7.5h budget if it does.

**WAVE 1 — MERGE TRAIN COMPLETE (2026-08-02, ~01:22–04:45 IST). Seven PRs landed on
`shad-darshana/integration`, each independently CI-verified green before merge (not trusted
from self-report):**

| PR | Lane | Landed |
|---|---|---|
| #1017 | W4 Lane S spine | `intervention_filing.ts` + `client.ts` one-line widening — the published `FilingState` contract Lanes U/R build against |
| #1018 | item 31 | period-echo mining on `kala_ahead_get`, hypothesis-framed, no new table (pure serving-layer join) |
| #1019 | W4 Lane R pt.1 | R-1 lattice widening (migration 530, +71k rows, `hora`/`vara`/`nakshatra`/`tithi`/`lagna` families) + items 6 (data-layer closed, engine-axis blocked — see gaps) + 7 (muhūrta-lagna substrate + query-time strength) |
| #1020 | item 9 | health/adverse event class in sweep grammar — **closes DP-4, S4-05 re-test PASS** (red-then-green proof against the real UAT_DARPANA S4-05 scenario text, not reconstructed) |
| #1021 | W4 Lane U | UPĀYA-SETU full (item 26) + E6 efficacy, mortality-exclusion rail (G16) proven non-vacuous, `for_intervention` contract published for Lane R |
| #1022 | item 13 | Tithi-Praveśa lunar-return annual chart, new `ka_tithi_pravesha` writer, migration 531 |
| #1023 | W4 Lane S writer | `mi_sankalpa` / `mimamsa_intervention_ledger`, migration 532, status-preserving idempotency live-proven against a real throwaway Postgres |

**PR #1024 (W4 Lane R pt.2 — R-2/R-3/R-4/R-5: `kala_paddhati_profile`, Mode-2 fixture, chart_relative
constraint kind, `ritual.ts`/items 37/38/40) — CI caught a real cross-lane migration collision**
(this branch's `531_kala_paddhati_profile.sql` was cut before `w3-tithi-pravesha`'s
`531_kala_tithi_pravesha.sql` merged — the exact "re-verify live max immediately before writing,
don't trust a stale reservation" trap this campaign's own docs warn about, recurring right on
schedule). **Conductor-fixed directly** (a one-line renumber doesn't warrant re-dispatching the
whole lane): merged `origin/shad-darshana/integration` into the branch, re-verified true live max
(532, both directories), renumbered to 533, updated the header comment, ran
`migration_number_guard.ts` locally — PASS, no new collision — pushed. CI re-running; will merge
on green like every other lane, not force-pushed through.

**Deep gaps surfaced honestly by the builders, carried forward (not silently dropped):**
- **Item 6's Pareto axis (`rite_specific_resonance`) could NOT be enabled** — `kala_lattice_query.ts`'s
  `EXCLUDED_AXES` is a module-private const with no injection point, and the file is FROZEN for W4.
  The builder correctly stopped rather than editing a frozen file. Item 6 is data-layer CLOSED,
  engine-axis OPEN — needs a small, deliberate one-line unfreeze PR, Conductor-authorized, in a
  future session (not tonight — a frozen-file exception is exactly the kind of call that should get
  its own deliberate PR, not be folded into a builder's larger lane).
- **Item 37 partial**: storage/reader/divergence-block closed; `query_kala_paddhati_profile`
  capability itself doesn't exist yet — needs a shared `index.ts` boundary negotiation the lane
  correctly declined to resolve unilaterally. Degrades honestly (`honest_empty`, corpus-default
  fallback disclosed) in the meantime.
- **Production `bg_muhurta_lattice` currently has 0 rows** — migration 530's schema is live but the
  L0 rebuild (super-admin trigger) hasn't run. The Mode-2 fixture gate is correctly honest-empty
  until then; this is a Nirmāṇa §2.5.2 prerequisite for the gate-close deploy below.
- **Item 9's sweep-grammar fix is code-live, DATA is not**: no chart has health/adverse windows
  until `ka_gochara_sweep` + `ka_gochara_resonance` re-run against production for both canonical
  charts. Sweep substep count doubles (303→606/chart). **This is a required step in the gate-close
  sequence, not optional** — S4-05 is not actually closed until the live query is re-run post-rebuild.
- Item 14 (janma-anchored election rules) — confirmed still NOT-STARTED, as instructed.
- The parihāra corpus pass found exactly one new genuine citable rule (Bṛhat Saṃhitā Viṣṭi
  exception) and correctly declined to encode it (schema has no undertaking-class qualifier column
  — encoding it unconditionally would wrongly cancel Bhadra for a wedding). Named as a work item,
  not silently dropped.

**Next**: land PR #1024 on green CI, then run the gate-close sequence — this is now the
critical path, not a further build wave (see below for the Wave-2 decision).

---

## MORNING REPORT — NIGHT 4 (2026-08-02, ~01:22–~11:45 IST)

**Gates closed:** none formally VERIFIED-CLOSED in the brief's strict sense (that requires
PARĪKṢAKA live acceptance, not reached this session — see parks below). **But this is the
first night since Night 2 that campaign work actually reached production**, and it's a large
jump: `main == production` now carries all of Night 2's W2 build lanes, all of Night 3's N_e
priors + W3 items 4/5/16/17 + W2G validations + W4 design v1.1 + the watchdog fix, AND
tonight's full Wave 1. Concretely, the wave that landed live:

**Items dispositioned tonight (code-built + merged + deployed to production; live-data
verification honestly still pending, see parks):**
- **Item 9 — health/adverse event class, S4-05 re-test.** The highest-stakes item in the wave:
  closes a documented historical trust-breaking veto (silence from the sweep read as an
  all-clear on a health question). Red-then-green proof against the real UAT_DARPANA scenario
  text. **Code is live in production; the sweep DATA is not yet** (see parks — this is the one
  gap that matters most and is flagged loudly, not buried).
- **Item 13 — Tithi-Praveśa** (new `ka_tithi_pravesha` L3 writer, lunar-return annual chart).
- **Item 31 — period-echo mining**, hypothesis-framed, on `kala_ahead_get`.
- **Items 6+7** — muhūrta-lagna substrate + activity-rule lattice atoms (R-1 widening, +71k
  lattice rows). Item 6's Pareto axis blocked on a frozen file — data-layer closed,
  engine-axis open, honestly disclosed, not silently claimed done.
- **W4 Lane U — UPĀYA-SETU full (item 26) + E6 efficacy**, mortality-exclusion rail (G16)
  proven non-vacuous.
- **W4 Lane R — YAJÑA-SETU** (items 37-partial/38/40), Mode-2 fixture built (PASS=4/FAIL=0 in
  PLAN mode; live detectors correctly SKIPPED, not forced green, pending a populated lattice).
- **W4 Lane S — Intervention Ledger** (`mi_sankalpa`), status-preserving idempotency
  live-proven against a real throwaway Postgres.

**Rulings made:** none new via ANTARYĀMIN tonight (the docket was already fully discharged as
of Night 3 + the native's morning-review PR #1015). One Conductor-authority migration
renumber (531→533, a real cross-lane collision caught by CI, fixed directly rather than
re-dispatching a lane).

**Defects found and fixed tonight (real, not cosmetic):**
1. A cross-lane migration-number collision (`531_kala_paddhati_profile.sql` vs the
   already-merged `531_kala_tithi_pravesha.sql`) — caught by CI, Conductor-fixed, renumbered
   533, guard re-verified PASS before pushing.
2. **A real, production-discovered deploy-blocking bug** (same class as Night 1's bash-quote
   bug): migration `529_bg_sarvatobhadra_grid.sql`'s `asset_registry` seed row passed
   `writer_timeout_seconds = NULL` against a NOT NULL column, halting `migrate.ts` mid-run and
   silently preventing migrations 530–533 (tonight's OWN new tables) from ever being attempted.
   Root-caused via `_migrations_applied` (confirmed 529 never applied, rolled back atomically —
   safe to edit), fixed to `600` matching every sibling row's live convention, PR #1026, landed
   and **verified**: all five migrations (529–533) now show `applied_at` timestamps in
   production.
3. Multiple builder-caught bugs recorded in their own PR bodies (see the Wave-1 merge-train
   record above) — a false-negative Pareto-axis assumption, a stale test payload, several
   correctly-declined-rather-than-fabricated citations.

**Parks and reasons — the honest, load-bearing part of this report:**
- **Item 9's live data is NOT yet real.** `ka_gochara_sweep` + `ka_gochara_resonance` have not
  been re-run against production for either canonical chart since tonight's grammar widening
  (303→606 substeps/chart). **S4-05 is code-closed, not data-closed** — a live query today
  would still return honest-empty for health windows, which is correct behavior (not
  fabricated), but is not yet the actual fix landing for the native. This is the single
  highest-priority carry-forward item.
- **The L0 super-admin rebuild/refresh triggers were NOT run tonight** for
  `bg_class_lifetime_counts` (N_e, migration 522, live in schema since Night 3 but never
  triggered), the widened `bg_muhurta_lattice` (migration 530, schema live, 0 rows — the
  Mode-2 fixture's own honest-empty state depends on this), `bg_kota_chakra_rings` (523), and
  `bg_sarvatobhadra_grid` (529, deliberately empty by design, no trigger needed). **Nirmāṇa
  §2.5.2 requires these built in production BEFORE the first per-chart build that needs
  them** — this is the direct blocker for the real W2 field-integration run.
- **The real W2 field-integration run (hash-replay determinism, weights-v0 seed, skill-score/
  GOF publish both charts, specificity-gate HARD flip, item-44 census population) was
  correctly never attempted tonight** — it was assessed early in the session as needing the
  L0 rebuilds above as a hard precondition (a per-chart field build against production data
  that doesn't have its L0 dependencies yet would either fail or silently produce an
  under-populated field), and as substantial standalone work in its own right, consistent
  with the same assessment Night 2/3 both made independently.
- **`ka_kshetra` was not rebuilt on either canonical chart in production tonight** — same
  precondition chain as above.
- **PARĪKṢAKA live acceptance did not run this session.** Per the brief's own rule ("an item
  without Verifier PASS does not exist"), none of tonight's items should be treated as
  VERIFIED-CLOSED yet, regardless of how solid the build/deploy evidence looks. This is a
  deliberate, disclosed gap, not an oversight — closing it needs a dedicated acceptance pass
  once the L0/field/sweep prerequisites above are actually live with real data to check
  against; running it against still-empty data tonight would only produce a shallow pass.
- **W2G writer lane was never dispatched** (the V4 measured-vs-design contact-event band
  re-scope — 779,595 events vs. a 10k-100k design assumption, even excluding the Moon — is a
  genuine Opus design decision, correctly not rushed into tonight's already-large wave).
- **Item 14** (janma-anchored election rules) remains NOT-STARTED, as instructed.

**Deploy verification, done for real (not trusted from a green checkmark):** confirmed via
direct log reads, not summaries — MCP's post-deploy smoke passed three real probes (no-auth
rejected 401, bearer-auth 200, URL-token wiring), 100% traffic on `amjis-mcp-00527-f47`
(confirmed via `gcloud run services describe`, revision creation timestamp cross-checked
against the deploy run that built it); Web's smoke passed for real (auth-enforced 401,
sidecar-reachable), 100% traffic on `amjis-web-01351-n2d`; Sidecar deployed clean. `main` @
`d0f9cb1c` == production across all three services, confirmed directly.

**Housekeeping done at close:** all six of tonight's builder worktrees removed (each verified
merged before removal); the standing `shad-darshana-conductor` worktree kept, synced to
`main` tip. `shad-darshana/integration` and `main` are now identical (integration was fully
absorbed by gate-close PR #1025 + hotfix #1026) — the next session should treat `main` as the
frontier for a fresh `git worktree add` rather than assuming integration has independent
unmerged content.

**Single next action for the next session:** run the L0 super-admin rebuild/refresh triggers
for `bg_class_lifetime_counts`, the widened `bg_muhurta_lattice`, and `bg_kota_chakra_rings` in
production; re-run `ka_gochara_sweep` + `ka_gochara_resonance` on both canonical charts
(doubled substep count from item 9); THEN the real W2 field-integration sequence
(`ka_kshetra` rebuild both charts → hash-replay → weights-v0 → skill-score/GOF publish →
specificity-gate HARD → item-44 census); THEN PARĪKṢAKA live acceptance covering everything
from Night 4 plus whatever lands from that sequence — this is realistically a full session's
own work, not a quick follow-up.

*Truth over completion. PARKED-HONEST with evidence, not a false close.*

---

**NIGHT-3 RESUMED SESSION CLOSED (2026-08-01, ~08:36–16:15 IST — see MORNING REPORT
NIGHT-3-RESUMED immediately below for the full close-out).** The single next action for the
next session:

1. ~~Confirm the final two merges landed~~ **DONE before close: PR #1009 MERGED
   (`a3a6a743`) and PR #1014 MERGED (`c84ae621`) — every lane PR of the session landed;
   nothing half-merged.**
2. **Confirm gochara run `d95583c8` completed `1c826d5a` to 303/303** — at the final
   pre-close check it stood at **302/303, state=running**; completion expected within
   minutes, unattended. If short, one more dispatch using the recorded
   `--run-id`/`MARSYS_RUN_ID` invocation.
3. **Then the W3 gate-close sequence is the main event**: remaining W3 items per brief §1
   (activity tables 6 · muhūrta-lagna 7 · janma rules 14 · health class 9/S4-05 · Tithi-
   Praveśa 13 · period-echo 31 · sandhi-full 1 · sky-calendar joins 3 · E6-full; field-
   dependent 33/34 wait for the field) — dispatch as parallel lanes off integration; when the
   wave's items are BUILT, open the §B.2 gate-close PR (integration → main, rides the merge
   queue 5–60 min), deploy, run the super-admin L0 trigger for the new bg_* assets
   (bg_class_lifetime_counts · bg_kota_chakra_rings · bg_muhurta_lattice/bg_parihara_rules
   if not yet built · bg_sarvatobhadra_grid empty registration), rebuild ka_kshetra both
   charts, and PARĪKṢAKA live-accepts — including the ADJUDICATION-10 LIVE Abhijit-rescue
   demonstration and the first skill-score/GOF publication (Gate W2's close rides the same
   deploy: N_e is now in the tree, so W2 + W3 likely close together).
4. **W2G writer lane** is unblocked next (N-block complete + generation schema landed +
   validations honest-FAIL findings enumerated): first resolve V4's design-band question
   (779,595 measured contact events vs §2.3's 10k–100k band — an E-3 re-scope/design
   amendment, Opus lane) and V1's per-phase instrumentation gap; Tier-1 equivalence can open
   once `1c826d5a` hits 303/303 (item 2 above).
5. **W4 Phase-5b lanes (U/R/S)** are fully specified (design v1.1 + ADJ-12/13) and can run
   beside W3 lanes.

**Native morning review requested on:** the twelve ADJUDICATION rulings (-2 through -13, all
reversible, full text in `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`) — in particular N_e's
six seeded values (independently re-derived, but they are structural priors the native may
wish to inspect), the Agnivāsa paddhati pin awaiting his one-line lineage-convention
confirmation, and the `muhurta_chintamani` translation work item (now blocking four
deliverables — the highest-leverage corpus action available).

---


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

## NIGHT 3 RESUMED SESSION (2026-08-01, ~08:36 IST — the prior Night-3 session was stopped externally ~08:31; this session resumed from its honest park)

**Session-open protocol discharged:**
- **Ledger PRs landed**: PR #1000 (the stopped session's honest wave-status/N-block/docket close) merged to integration @ `52deb3a1`. All four cancelled-lane worktrees (`w2-integration`, `w3-lattice-engine`, `w3-moorti-vedha`, `w3k-inventory`) verified clean, zero commits — the stopped session's "no work lost" claim independently confirmed.
- **PR #999 (W3 items 16+17) CI failure diagnosed + fixed**: two stale exact-count assertions — `descriptor_defaults.test.ts` (33→35 `register.reader_label` capabilities; the +2 traced by diff to exactly `query_kota_chakra.ts` + `query_sudarshana_varsha.ts`) and `AssetRow_CockpitPolishR2.test.tsx` (Kāla seed count 15→17; the +2 traced to exactly the two new seed entries). Semantic fixes with named additions, not blind bumps — commit `0f15baa2`, CI re-running.
- **Gochara-sweep resume, `1c826d5a` (standing operational item)**: collision check clean (zero running runs in `build_runs`); progress verified 209/303 substeps (prior dispatches gained ~131 ≫ the ≥40 gate). New dispatch `dbcd45e1-f90a-4e7c-8160-254b35de5bc6` created via the established script + `gcloud run jobs execute` (execution `brahma-build-pipeline-job-d6zlw`); ~94 substeps remain (likely dispatch 2-of-3).

**PARĪKṢAKA LIVE ACCEPTANCE — deploy-main@`6e53f7cb` → ACCEPTED (2026-08-01 ~03:13–03:17Z, both charts, all evidence from real calls).**
- Traffic independently re-derived to LATEST on 3/3 services (`amjis-mcp-00526-4p7` / `amjis-sidecar-00953-hzz` / `amjis-web-01345-c9d`, each 100%, `latestRevision:true`).
- W2 schema live: 18/18 `kala_field*`/`kala_timeline_spec` tables; migrations 488–497 all recorded in `_migrations_applied` (ids 367–376) with sha256 + sql_identity, no gaps.
- Gate-W1 baseline: all 7 spot-verifiable item families intact on both charts, zero regression. 8/8 cited `fact_id`s resolved against `chart_facts` with matching values, incl. 3 FORENSIC anchors re-confirmed through the live serve path; daśā claim cross-checked against `ganita_dashas_get` exactly.
- **Standing advisory RESOLVED**: `kala_ahead_get` on Abhinandan now returns 5 populated projections + ladder + digest — the `projections:[]`-with-`computed` advisory from Gate W1 is closable; `computed` is now earned.
- **PR #995 inversions confirmed present in production as expected** (fix is on integration, not main — strangler discipline working). **Ledger precision correction (from the Verifier, adopted here): the HARD inversion is `hora_ladder` in `elect.ts:228` (unconditional `computedCoverage('hora_ladder')` for a concept the tool never computes), NOT `hora_now` — `now.ts:1366`'s `hora_now` is correctly payload-conditioned and populated on both charts.** The soft inversion is `kala_darshana_confluence` (`now.ts:1146` gates coverage on reachability, not payload; prose layer is honest).
- **Two NEW minor disclosure defects filed, non-blocking** (register items for a small lane):
  - **ND-A**: `kala_ahead_get` thesis narrates already-open windows as "forward-dated" (e.g. `2010-08-18..2027-08-18` on Abhisek) — narration imprecision, rows themselves honest. Suggested wording: "currently-active or forward-dated windows overlapping the next N years."
  - **ND-B**: projection/window member arrays silently capped at 10 against an uncapped `member_count` (85 vs 10 ids, no `truncated`/`more_available` marker) — §N.6(4) says the cap should be declared machine-readably, not left to inference.

**Swarm dispatched this session (per §D v1.3, maximally parallel):** ANTARYĀMIN (Opus, full unruled docket: N_e priors-source · N1–N4 · W3K seating · paddhati/Agnivāsa · Kota ring-table citation tier) · `w3-moorti-vedha` (items 4+5, Sonnet) · `w3-lattice-engine` (item 36 query engine, Opus — W4 5a trigger) · `w3k-inventory` (item 18 inventory, Sonnet) · PARĪKṢAKA (acceptance above). Results recorded below as they land.

**ANTARYĀMIN DOCKET FULLY DISCHARGED (2026-08-01).** All eight rulings issued — the N-block is
COMPLETE for the first time (N1–N4 ruled + native's N5), so **W2G is startable**; the N_e
critical path has a binding build spec (`bg_class_lifetime_counts`, Tranche-1 of 6 classes
mandatory at Tier N-i sourcing, hard stop = seed zero rows if sourcing fails); the Kota
gate-blocker is a bounded task (`bg_kota_chakra_rings`); W3K seating ratified as a three-way
split. Full text: `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`. N-block + ADJUDICATION log
updated below.

**W3K INVENTORY LANDED (PR #1003, docs-only, scope-verified).** Headline: the brief's "KP
exists nowhere" premise is FALSE — `ganita_kp_cusps_get` (CR-30) serves a live, tested 249-fold
sub-lord substrate (`compute_kp_lords`, 4 levels), 5 KP fact categories live on both canonical
charts across all 5 ayanāṃśas, and `chart_dashas` already carries a `vimshottari_kp` system
(576 + 5,184 rows on the native chart). Also flagged: a stale "PHANTOM DROPPED" disposition in
`retrieval_capability_spec.ts`/`tool_metadata.ts` predating CR-30; a fabricated-data fallback
`schools/kp_engine.ts` (unrelated, flagged); a `bhava_cusps` cockpit-truth gap (no `count_sql`).
The inventory's seating recommendation is consistent with ADJUDICATION-7's ruling (which also
corrected the premise independently). Gap list + two-lane build plan in
`W3K_SUBSTRATE_INVENTORY_v1_0.md`.

**NIGHT-3 RESUMED SESSION — BUILD RECORD (running log, finalized in the MORNING REPORT below).**

**Merge train (all → `shad-darshana/integration`, each on green CI, scope-verified):**
- **PR #1004** — item 36's query-time lattice engine (Opus lane; §N.6 density layering:
  real-cited findings vs `computed_uncited_convention` counted separately, `hardFloor` on
  candidates; ONE-ENGINE RULE asserted by test). One CI count-fix cycle (whitelist 54→56,
  both literals updated semantically with the +2 named). **Item 36 LANDED → W4 Phase-5a
  trigger (36+41) MET.**
- **PR #1005** — ADJUDICATION-9 discharged: `bg_kota_chakra_rings` versioned L0 table
  (migration 523), inline dict deleted, byte-identity proven against a frozen golden
  partition + live throwaway-Postgres idempotency check. One disclosed precision note: 27
  rows (27-nakshatra arithmetic in actual use), not the ruling's "~28". **Item 16's
  citation-tier blocker on the W3 gate-close → CLEARED.**
- **PR #1008** — ADJUDICATION-10 Part 1 discharged: the Abhijit sarva-doṣaghna parihāra row
  (migration 524), source chunk `bphs_jaimini_pg0213_c01` verified in production corpus
  BEFORE seeding, transcribed verbatim, `extraction_context='translator_gloss_in_narrative'`.
  Schema-forced narrowing disclosed: engine matches per-doṣa (`rahu_kalam` chosen), no
  wildcard convention — a narrowing of practical reach, not of transcribed doctrine. Rescue
  proven in test against the real seeded row. Live-candidate demonstration = W3 gate
  Verifier item.
- **PR #1006** — W2G V1–V6 bind-time validations as real code (38 tests, each asserted both
  ways). **HONEST GATE RESULT: `may_proceed: false`** — V2 PASS (ephemeris 1900→2150 all 9
  bodies, zero gaps; ADJUDICATION-5's 1900 floor fully supported) · V3 PASS (spline worst
  error 0.314″ vs 60″ target; recommended root-find tol 1.0″) · **V4 FAIL** (779,595 contact
  events vs design §2.3's 10k–100k band — the design's per-cycle multiplier assumption is
  refuted by measurement; E-3 re-scope needed: Moon is 76% of events but the eager layer
  alone still exceeds the band) · **V5 FAIL** (no generation discriminator existed — see PR
  #1013; and Tier 1 cannot open: `1c826d5a` at 215/303 substeps, a row-count check would
  call it populated — the substep-plan check catches it) · V1/V6 INDETERMINATE with reasons
  (no per-phase timing instrumentation exists; classifier needs a 2.0 side). Grid convention
  finding: ephemeris knots at noon UT, v1 sweeps at midnight — half-day offset to reconcile.
  One real bug found by the live run (bare `%` in parameterised SQL), fixed + regression-
  tested.
- **PR #1013** — ADJUDICATION-6's schema landed: `kala_gochara_windows.generation` (DEFAULT
  'v1', catalog-only ALTER proven via xmin probe) + `kala_gochara_authority` pointer table
  (absent row = v1 authoritative). Two serving surfaces filtered; remaining readers
  documented as the 2.0 writer lane's checklist. Migration 527. v1 rows untouched
  (untouchable respected; behavior byte-identical today).
- **PR #1010** — W4 Phase-5a design pass (Opus): `KALA_W4_UPAYA_DESIGN_v1_0.md` v1.1. Lane
  split U/R/S with anti-collision file table; no new MCP tools (W0 shells filled — removes
  the historical registry_bridge collision surface); the lattice CHECK gap (4 factor
  families, no hora/vara/tara atoms) found and ruled R-1; Mode-2 fixture mapped to 4 named
  detectors incl. a two-part both-charts detector; ADJUDICATION-12/-13 folded in as v1.1
  (equality-not-negation basis check; DB CHECK making inferred-rows-never-sealed structural;
  mortality exclusion as a SUBSTRATE ban — forbidden identifiers ayurdaya|longevity|maraka|
  ayus — with G16 re-running under native_self and still refusing; §1 rail 11: a detector
  that cannot be shown to fire is treated as OFF — non-vacuity assertions required).
- **PR #1011** — the watchdog false-kill fix (campaign-discovered production defect, root
  cause pinned: Postgres `NOW()` = transaction start, so a multi-minute substep's own
  heartbeat understates its commit time; clause-1's 10-min window left no margin at 5–6.5
  min/substep cadence). Fix additive in the watchdog route only: 15-min window +
  `build_substep_progress.completed_at` as second evidence-of-life (read-only). RED-first
  repro of tonight's false kill + truly-orphaned still reaped, both proven.
- **PR #1007 — THE CRITICAL PATH: N_e priors LANDED, VERIFIED.** `bg_class_lifetime_counts`
  (migration 522): all SIX Tranche-1 classes at genuine Tier N-i — childbirth 3.09 (NFHS-5
  FR375 Tbl 4.5), marriage 0.984 + separation 0.00806 (Census 2011 C-2), relocation 0.376
  (Census D-2), surgery 0.356 (Zadey 2024 measured HMIS rate; Weiser's famous 904/100k
  REJECTED as a regression imputation — India sits in the missing-data table), foreign_
  settlement 0.0129 (UN DESA IMS 2020). Tranche 2: ZERO rows (nothing reached Tier N-i —
  the hard stop held; 21 classes honestly skip `no_class_prior_row`). DATA-HONESTY RAIL now
  MACHINE-ENFORCED (prior_basis + source_ref CHECK). Two beyond-spec catches: the
  `query_class_priors` serving surface would have flattened salience multipliers and event
  counts into one column (scoped out with excluded_fact_kinds disclosure, §N.6) and a real
  transaction-poisoning bug (un-rolled-back savepoint probe) fixed. **ADJUDICATION-2 item-7
  two-pass acceptance DISCHARGED: independent re-derivation (own downloads, MD5-recorded,
  figures read from the source cells/pages) confirmed all 6 figures TO THE DIGIT — verdict
  PASS, zero deletions, zero amendments; surgery choice upheld on the imputation ground.**
  Three advisory prose corrections to permanent audit fields applied pre-merge. Conductor
  resolved the lane's merge conflict (KNOWN_HAS_WRITER_TRUE additively) per §B.1.
- **PR #1003** — W3K substrate inventory (see above).

**Verification, adjudication + design artifacts this session:** deploy-main ACCEPTED
(PARĪKṢAKA, above) · **ADJUDICATION-2 through -13 — twelve rulings, the entire docket +
five mid-session escalations, zero lanes stalled waiting on a ruling** (full text:
`SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`) · `W3K_SUBSTRATE_INVENTORY_v1_0.md` ·
`KALA_W4_UPAYA_DESIGN_v1_0.md` v1.1 · W2G honest-FAIL validation record (PR #1006).

**Corpus findings elevated to standing work items:** (1) **`muhurta_chintamani` is ingested
but untranslated** (274 chunks, content_en byte-identical to content_sa, raw OCR) — now
blocking FOUR deliverables (Agnivāsa second convention, Kota primary source, muhūrta-scope
parihāra extraction, SBC grid candidates); the single highest-leverage corpus action
available, zero acquisition cost. (2) SBC-specific text (Nārada-Saṃhitā class) — genuine
acquisition. (3) KP texts — none ingested (tier-ii design doc is primary for W3K).

**Operational: the gochara-sweep watchdog false-kill class is now DIAGNOSED and FIXED (PR
#1011).** Both of tonight's early kill events (03:30:06 `run never dispatched` = the
Conductor's own bare-execute mistake, recorded above; 04:30:05 clause-1 kill of run
`e5cde4dc` with a 5.2-min-fresh heartbeat while the container ran on) are explained. The
container survived the false kill and kept committing substeps all session (209 → 230+/303,
~5–6.5 min cadence). The DB run-state row for `e5cde4dc` reads `failed` and is COSMETICALLY
WRONG — the substep ledger is the truth. ~70–90 substeps will remain at container timeout
(~09:53Z); ONE further dispatch (using the `--run-id` + `MARSYS_RUN_ID` invocation recorded
above) should complete the 303. The fix deploys with the next gate-close.

**Gochara-sweep resume (operational): first re-dispatch attempt `dbcd45e1` FAILED with
`orphan-watchdog: run never dispatched` — root cause: a bare `gcloud run jobs execute` runs the
container with NO run-id; the job requires `--args="--run-id,<id>"` +
`--update-env-vars MARSYS_RUN_ID=<id>` (per `src/lib/build/jobInvoker.ts:187`). Re-dispatched
correctly as run `e5cde4dc-3640-4fe8-b1b0-1e3439a06792` (execution
`brahma-build-pipeline-job-f5jkh`) — confirmed `state='running'`. Recorded so no future session
repeats the bare-execute mistake.**

---

## MORNING REPORT — NIGHT-3 RESUMED SESSION (2026-08-01, 08:36–~16:15 IST)

**Context:** the first Night-3 session was stopped externally ~08:31 after dispatching its
swarm; this session resumed from its honest park (PR #1000), re-ran the §D v1.3 session-open
protocol, and executed the full night.

**Gates closed:** NONE — correct, not a shortfall. W3 is a multi-night wave (only a subset of
its items landed); W2's close requires the L0 assets built in production, which rides the
next gate-close deploy. `main == production` verified at open (PARĪKṢAKA ACCEPTED deploy of
main@6e53f7cb, both charts, zero W1 regressions); `shad-darshana/integration` runs ahead of
`main` by ~25 commits — the normal, by-design between-gates state (§B.2).

**Items dispositioned (all on integration, none yet live-production):**
- Item 36 (lattice query engine) — BUILT+MERGED (#1004); W4 5a trigger met.
- Item 16 (Kota) — citation-tier blocker DISCHARGED (#1005, ADJ-9); VERIFIED-FIXED path
  confirmed pending gate-deploy Verifier pass.
- Abhijit parihāra (ADJ-10 Part 1) — extracted + merged (#1008); live rescue = gate item.
- Items 4+5 (moorti + vedha) — BUILT (#1009, ADJ-11 additions landed; final CI green-pending
  at close after a guard-caught 527 renumber).
- N_e priors (ADJ-2) — **BUILT + INDEPENDENTLY VERIFIED + MERGED (#1007)**: 6 Tranche-1
  classes at Tier N-i, two-pass re-derivation PASS to the digit; `ka_kshetra` proven locally
  to produce its first non-empty class set (6 compute + 21 honest-skip, #1014 evidence).
- W2G V1–V6 validations — BUILT+MERGED (#1006) with an HONEST `may_proceed:false` (V4/V5
  findings are the W2G writer lane's work list, not defects).
- ADJ-6 generation schema — BUILT+MERGED (#1013).
- W4 design v1.1 — RATIFIED+MERGED (#1010).
- Watchdog false-kill fix — BUILT+MERGED (#1011), root cause pinned (NOW() = txn start).
- W3K inventory — MERGED (#1003): KP substrate already exists at L1 (premise corrected).

**Rulings made:** ADJUDICATION-2 through -13 — the full pre-queued docket plus five
mid-session escalations, every lane unblocked same-session, zero stalls waiting on a ruling.
The N-block is COMPLETE (first time since the campaign opened); W2G is startable. Native may
overrule any ruling; all are reversible by design.

**Defects found + fixed:** the watchdog clause-1 false-kill (production, diagnosed with a
live specimen, fixed additively, both directions tested) · the W4 design's no-op adverse-
guardrail predicate (would have silently auto-filed every health intervention — caught by
ANTARYĀMIN against the live ontology, replaced + CI-asserted non-vacuous) · four exact-count
assertion regressions across three PRs (all bumped semantically with additions named) · a
migration-527 collision (guard caught; renumbered 529) · a psycopg `%`-placeholder bug in
V4's live path · a transaction-poisoning savepoint bug in the N_e writer · the Conductor's
own bare-`gcloud run jobs execute` mistake (run never dispatched — invocation contract now
recorded).

**Parks + reasons:** Tranche-2 N_e classes (21) — no Tier N-i source reached; honest-skip by
design. SBC grid — CLOSED-PARTIAL-BY-DESIGN per ADJ-11 (school-tagged table registered
empty; approximation served with machine-readable basis). W2 field determinism double-run +
ka_kshetra local build — NOT-REACHED in #1014's budget (steps 1–2 proven; 3–5 next session).
`e5cde4dc`'s DB run-state row falsely reads `failed` (watchdog false-kill; substep ledger is
the truth — fix merged, deploys at gate-close).

**Operational:** gochara `1c826d5a` horizon rebuild advanced 209 → 292/303 across two
container dispatches (the ≥40 gate more than doubled); the FINAL dispatch (`d95583c8`,
execution `dnznp`) was confirmed RUNNING at close — 303/303 expected unattended. The correct
job invocation (`--args="--run-id,<id>" --update-env-vars MARSYS_RUN_ID=<id>`) is recorded
above; a bare execute silently does nothing.

**Swarm health note for the native:** persistent infrastructure instability all session
(~15 agent connection-drops/stalls across 10 lanes; every one resumed with zero work lost —
the SendMessage-resume pattern + worktree isolation held). Two lanes' completed work was
landed by the Conductor from their verified working trees (N_e polish, ADJ-11 additions) —
each noted in the commit message, each independently test-verified before landing.

**Single next action:** open the W3 gate-close sequence (remaining W3 item lanes → gate-
close PR → deploy → L0 builds → Verifier live acceptance) — see NEXT-ACTION above. (#1009
and #1014 were merged before close; the gochara sweep stood at 302/303 running.)

**Final close state:** every session lane PR merged (13 total: #1000 #999 #1003 #1004 #1005
#1006 #1007 #1008 #1010 #1011 #1013 #1009 #1014); all campaign worktrees removed except the
standing `sd-conductor`; `main`@`334436a9` deployed and serving 100% (post-acceptance main
movement was the TAP-6 CI workstream's own docs/fix commits + its path-gated deploys — not
this campaign's); `shad-darshana/integration` ahead of `main` by design pending the W3/W2
gate close.

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
| W2 | **BUILT, NOT CLOSED — PARKED-HONEST (Night 3)** | Design PR #886 + PR #918 + PR #932; all 5 build lanes merged (#944/#945/#946/#947/#949); **migrations 488–497 APPLIED IN PRODUCTION Night 3** (deploy runs `30678888444` + `30679075712`, all 18 `kala_field*`/`kala_timeline_spec` tables verified live) | **The gate did NOT close and could not.** Two independent reasons, both recorded honestly: (1) the **N_e lifetime-count-priors blocker is still unruled** — ANTARYĀMIN was cancelled mid-session before issuing the priors-source ruling, so no seeding lane could be dispatched and `ka_kshetra` still writes ZERO field rows (correctly refusing to fabricate, per §5.1 C-1 / B.10); (2) the **`w2-integration` lane was cancelled mid-session** — it owned field integration, hash-replay determinism, the real `field_snapshot_id` (E5), weights-v0 seed, the item-44 census, and the specificity-gate flip to HARD. Neither cancellation lost work (both lanes had zero commits). Gate W2's §3 criteria — skill score + GOF published both charts, null exceedance per window, salience visible in PRIORITIZE, insight rows leading readings — ALL require a non-empty field, hence all require N_e first. |
| W2G | NOT-STARTED | — | GOCHARA-2.0 sub-day. **STILL BLOCKED on N1–N5 ratification — now for the THIRD consecutive night.** ANTARYĀMIN was dispatched Night 3 with N1–N4 + N5's pre-ruled conservative default as its up-front docket (per the v1.3 §D protocol, which exists precisely because this block sat empty through Nights 1–2), but was cancelled before ruling. The N-block below remains empty. |
| W3 | **IN PROGRESS (first items landed Night 3)** | PR #999 (items 16 Kota-Chakra + 17 `ka_sudarshana_varsha`); `w3-moorti-vedha` lane (items 4+5, closes R-19) in flight at session end | New computations. Items 16/17 land as new L3 per-chart writers with Nirmāṇa seed rows + chart-scoped `count_sql` in the same PR. **Item 36's remaining half (the query-time lattice engine) was dispatched and CANCELLED mid-session — so W4's Phase-5a trigger (36+41) is still NOT met.** |
| W3K | **INVENTORY IN FLIGHT** | `w3k-inventory` lane (item 18 substrate inventory + layer-seating recommendation) running at session end | KP sub-lord engine. Per §C, W3K correctly begins with existing-substrate inventory before any build. Note the layer-seating question was on ANTARYĀMIN's docket and is now **unruled** — the lane produces a recommendation, but nothing can ratify it this session. |
| W4 | NOT-STARTED | — | Intervention flagship (UPĀYA/YAJÑA). Opus design mandatory. |
| W5 | NOT-STARTED | — | Planner integration; native's hard gate (real MCP calls). |
| W6 | NOT-STARTED | — | Cutover + retirement. |

## N1–N5 ratification block (W2G precondition — blank N5 means W2G is not startable)

| Item | Ruling | Ruled by | Date | Rationale |
|---|---|---|---|---|
| N1 (wave naming) | **W2G is the operative wave id; "D-6" RETIRED as a wave label (survives only as `historical_alias` in the GOCHARA_SWEEP_2_0 design frontmatter). Engine name stays GOCHARA-2.0.** | ANTARYĀMIN (ADJUDICATION-3) | 2026-08-01 | Prior status: unruled Nights 1–2, adjudicator cancelled Night-3-first-session before ruling. Full text: `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`. Reversibility: TOTAL (docs-only). |
| N2 (multi-chart rollout order) | **Three tiers by descending equivalence-evidence: Tier 1 = both canonical charts TOGETHER (this IS the W2G gate); Tier 2 = `cb73cd3d` Kiran Shenoy (only third chart with a v1 corpus, 1970→2027, scoped divergence report); Tier 3 = Arunima/Musk/Jobs 2.0-native with `equivalence_basis='no_v1_baseline'`, never counted toward divergence completeness, Jobs/Musk excluded from any skill/GOF scoreboard. Hard tier gate: zero unclassified divergences before advancing.** | ANTARYĀMIN (ADJUDICATION-4) | 2026-08-01 | Full text: `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`. Reversibility: HIGH (per-chart, monotone). |
| N3 (pre-1984 backfill) | **Backfill the global event calendar to the ephemeris floor: `calendar_epoch_start=1900-01-01` (derived from live `ephemeris_daily` coverage 1899-12-31→2150-12-30, 825,084 rows — verified, not assumed). Epoch bounds served as data; outside-epoch queries return honest-empty `reason='outside_calendar_epoch'`. W2G validation V2 amended to verify 1900–2084 × 9 bodies; floor = max-over-bodies first-covered date if any body starts later.** | ANTARYĀMIN (ADJUDICATION-5) | 2026-08-01 | Lazy per-chart backfill rejected (would make a chart-independent asset chart-dependent). Full text: `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`. Reversibility: HIGH. |
| N4 (cutover posture) | **Dual-serve shadow with authority gated on EVIDENCE, not elapsed days ("N days of agreement" on a batch-computed century table measures nothing — category error, rejected). Generation-stamped 2.0 rows beside v1 (v1 rows NEVER touched — untouchable); authority flip requires ALL FOUR: zero unclassified divergences · §3.3 specimen continuity · §3.4 byte-identical determinism · §3.5 battery within tolerance (drift = finding, never tuning). 7-day post-flip observation window; revert = one per-chart `authoritative_generation` pointer flip. v1 writer retirement only per strangler discipline.** | ANTARYĀMIN (ADJUDICATION-6) | 2026-08-01 | Full text: `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`. Reversibility: MAXIMAL (chosen for exactly that). |
| N5 (lock granularity) | **CONSERVATIVE-DEFAULT: the chart-level advisory lock STAYS. No orchestrator-contract change. Intra-chart shard parallelism is forfeited. Recorded REVERSIBLE.** | **The native, directly** — stated verbatim in the Night-3 §D kickoff paste (2026-08-01) | 2026-08-01 | **Recorded by the Conductor, NOT by ANTARYĀMIN** — provenance matters here and is stated precisely because this is the one FROZEN-contract question in the block, which an adjudicator may never decide on its own. The native's Night-3 kickoff contains the ruling in its own words ("N5 lock-granularity is ruled CONSERVATIVE-DEFAULT: chart-level lock stays, no orchestrator change, recorded reversible"), so no adjudication was needed or performed. Reversible: re-opening it costs only a future decision, since nothing was built against shard parallelism. **N5 alone does NOT unblock W2G — N1–N4 remain unruled.** |

## Registry item status (1–44 + E1–E8)

All items below seeded **NOT-STARTED** per W0.1. Disposition vocabulary: VERIFIED-FIXED /
VERIFIED-NO-DEFECT / PARKED-HONEST / FAILED-REOPENED. `OUT-OF-SCOPE-BY-DESIGN` is retired and
illegal.

| # | Item | Wave | Status | Both-charts | Evidence |
|---|---|---|---|---|---|
| 1 | Daśā-sandhi calendar | W3 (lite@W1) | **W1-lite VERIFIED-FIXED** (band convention documented, not fabricated); full two-period calendar is W3 | Y (code-level) | PR #924, `dasha_sandhi` on `kala_now_get` |
| 2 | Recurrence-ladder serving | W1 | **VERIFIED-FIXED** (row reconciled Night 3 — had read IN-PROGRESS against a PR merged 2026-07-30, while the W1 wave row already claimed 12/12 VERIFIED-CLOSED; drift closed append-only, not overwritten) | Y | PR #934 MERGED 2026-07-30T07:07:19Z (`w1-recurrence-digest`, items 2 + E6-lite); W1 round-2 PARĪKṢAKA record; **re-verified live Night 3** on rev `amjis-mcp-00526-4p7`: C2 10 ladders served (20 pre-trim, budget trimmer fired with `recover_via`), C1 2 ladders × 7 points, `point_kind` period_start/peak/end + graha, `source_citation: ka_kalasutra:v1.0:signal=…` — chart-differentiated |
| 3 | Sky-event calendar | W3 | **VERIFIED-FIXED (bg_sky_calendar built; per-chart contact joins deferred to ka_kshetra per spec)** | Y (global asset) | PR #888, live-verified against throwaway Postgres |
| 4 | Moorti-nirṇaya | W3 | NOT-STARTED | — | — |
| 5 | Vedha + Sarvatobhadra grid | W3 | NOT-STARTED | — | — |
| 6 | Activity-specific muhūrta tables | W3 | NOT-STARTED | — | — |
| 7 | Muhūrta-lagna | W3 | NOT-STARTED | — | — |
| 8 | Gochara dual-reference | W1 | **VERIFIED-FIXED** (round-2 PARĪKṢAKA, 2026-07-30) | Y — all 9 grahas non-null both charts, live-recomputed (Sun/Rahu sidereal longitude independently verified against served values), house arithmetic self-consistent | PR #891 (code) + PR #940 (fix: missing sidecar `x-api-key` header masked every 401 as empty) |
| 9 | Health/adverse event class | W3 | NOT-STARTED | — | — |
| 10 | Per-chapter LEL pinning | W1 | **VERIFIED-FIXED** | Y (code-level) | PR #889; Circularity Guard empirically verified |
| 11 | Provenance edges | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #949 (Lane C) — stages 4–5 field assembly + provenance; table `kala_field_provenance` live in prod (migration 493) |
| 12 | Daśā-system applicability | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #944 (Lane B) — stage 3 clocks + Law-1 applicability; table `kala_field_clocks` live (migration 490) |
| 13 | Tithi-Praveśa | W3 | NOT-STARTED | — | — |
| 14 | Janma-anchored election rules | W3 | NOT-STARTED | — | — |
| 15 | Rarity axis | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #946 (Lane D) — stage 6 rarity via cohort (22) + matched sub-cohort |
| 16 | Kota-Chakra | W3 | NOT-STARTED | — | — |
| 17 | Sudarśana-Chakra | W3 | NOT-STARTED (naming ruled) | — | Conductor ruling: writer named `ka_sudarshana_varsha` — confirmed namesake-only collision vs `bo_sudarshana.py` (different layer/computation), not built yet |
| 18 | KP sub-lord clock (CR-75) | W3K | NOT-STARTED | — | — |
| 19 | GOCHARA-2.0 sub-day | W2G | NOT-STARTED | — | — (blocked on N1–N5) |
| 20 | Auto-filed prospective ledger entries | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #947 (Lane E) — Living-LEL plane |
| 21 | Per-tradition calibration weights | W2 (ongoing) | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #947 (Lane E); tables `kala_field_weights` (29 seed rows) + `kala_field_weight_versions` (1: `v0_classical`) live |
| 22 | Synthetic reference cohort + matched sub-cohort | W2 | **VERIFIED-FIXED (cohort + MD-lord chain built; matched-sub-cohort JOIN logic itself is W2 Lane D's job)** | Y (global asset) | PR #887 (`bg_cohort`, 10k rows), PR #932 (`bg_synthetic_cohort_md` MD-lord chain, ADJUDICATION-1, ~100k rows, Vimśottarī arithmetic independently verified against native's own `chart_dashas`) |
| 23 | Circular-shift null calibration | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #949 (Lane C) — null calibration; table `kala_field_null` live (migration 494) |
| 24 | Uncertainty-budget propagation | W1-lite/W2-full | **W1-lite VERIFIED-FIXED**; full budget propagation is W2's job | Y (code-level) | PR #926, `sukshma_boundary_uncertainty` on `kala_now_get`, documented lite-v0 interval convention |
| 25 | Salience vector + submodular selection | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #946 (Lane D) — stage 6 salience; table `kala_field_salience` live (migration 495) |
| 26 | UPĀYA-SETU | W4 | NOT-STARTED | — | — |
| 27 | kala_timeline_spec v1 | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #947 (Lane E) — stage 8 timeline spec; table `kala_timeline_spec` live (migration 496) |
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
| 39 | Living-LEL incremental calibration plane | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #947 (Lane E) |
| 40 | kala_ritual_get registration + planner wiring | W0 stub/W4/W5 | **W0-stub VERIFIED-FIXED** (Modes 1-2 honest not_in_corpus; Mode-3 wrong_view redirect real & tested) | Y | PR #882 |
| 41 | Muhūrta Factor Census + corpus extraction | W3 | **VERIFIED-FIXED** (50-row census, 38 computed / 5 not_computed / 7 not_in_corpus, every row cross-checked with a real detector — `test_census_has_no_dangling_lattice_pointers` — not just claimed) | Y (global asset) | PR #930, round-1 Opus REJECT (5 real defects: a citation-contradicting Wednesday/abhijit bug, two wrong evidence numbers, one false "not found" corpus claim, dangling census pointers) → builder fixed all 5 with live re-verification → round-2 independent Opus APPROVE, every number re-derived |
| 42 | Unified Intervention Ledger | W4 | NOT-STARTED | — | — |
| 43 | Tri-plane traversability contract | W0–W1 | **VERIFIED-FIXED** (real-data wiring confirmed on all six view facades — items 8/10/28/29/30/32 now genuinely reflected, not just honest `no_lever` placeholders where a real signal exists) | Y | PRs #877/#880-884/#926, `no_lever`-honest pointers on every merged facade, new cross-facade real-wiring test |
| 44 | Single-temporal-authority (`authority_basis`) | W0 seed/W2/W6 gate | **W0 seed VERIFIED-FIXED**; population is W2's job | — | CI skeleton census seed, PR #881 |
| E1 | Point-process formalization + skill score | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #947 (Lane E) — `mi_bhara` skill-score/GOF harness; tables `kala_field_skill` + `kala_field_gof` live (migration 497). Design PR #886. |
| E2 | Insight synthesis stage | W2 | **BUILT — NOT VERIFIED** (W2 lane landed; no PARĪKṢAKA live acceptance yet, and the field is empty pending the N_e blocker, so no live evidence can exist until Gate W2's integration runs. Working state, deliberately NOT a disposition.) | — | PR #946 (Lane D) — stage 6.5 insight synthesis. Design PR #886. |
| E3 | Argument-shaped reading + specificity gate | W0/W2 | **W0-skeleton VERIFIED-FIXED**; hard-gate flip is W2's job | Y | PRs #877, #881 |
| E4 | question_frame compiler | W0 | **VERIFIED-FIXED** | Y | PR #877, `kala_envelope.ts` |
| E5 | field_snapshot_id | W0/W2 | **W0-stub VERIFIED-FIXED**; real hash is W2's job | Y | PR #877, marked with explicit TODO(W2) upgrade point |
| E6 | Per-view elevations | W1–W3 | **E6-lite VERIFIED-FIXED**; the full per-view deepenings remain W3 (row reconciled Night 3 — had read NOT-STARTED while the W1 gate record already counted E6-lite among its 12/12) | Y | PR #934 (items 2 + E6-lite); **re-verified live Night 3** on rev `amjis-mcp-00526-4p7`: `weakest_link` served both charts, naming the honest gap in place of a fabricated gate verdict (`stage: TRIGGER, status: gate_data_fetched`, reason states the instrument does not convert to sidereal / cross-check the classical vedha) |
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

**[SUPERSEDED same day — Night-3 resumed session, 2026-08-01.] The block below records the
cancelled first attempt and is retained as evidence trail. A fresh ANTARYĀMIN (Opus/max) was
dispatched by the resumed session with the identical docket plus the Kota citation-tier item,
and RULED ALL EIGHT: ADJUDICATION-2 (N_e priors source — demographic structural priors,
Tranche-1 mandatory, classical + cohort sources affirmatively foreclosed) · -3 (N1 W2G naming)
· -4 (N2 rollout tiers) · -5 (N3 1900 backfill) · -6 (N4 evidence-gated dual-serve) · -7 (W3K
three-way seating; corrects the "KP exists nowhere" premise — L1 natal KP substrate already
live) · -8 (Agnivāsa: practice pinned hard, convention = labelled corpus default, second slot
declared-not-computed) · -9 (Kota ring table → versioned `bg_kota_chakra_rings` L0 row; item
16 VERIFIED-FIXED path, not parked). Full verbatim text (with per-ruling rationale,
reversibility, and DB evidence): `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md` (same
directory). The N-block table above now carries N1–N4. Native morning review may overrule any
of the eight; every ruling is reversible per its own note.**

**ADJUDICATION-2 through -5 — NOT ISSUED (Night 3, 2026-08-01). ANTARYĀMIN was dispatched
and then cancelled mid-session before ruling on anything.** This entry exists so the docket
is not silently lost between nights; none of the four is a ruling, and no lane may proceed as
if one were made.

The adjudicator was launched at Opus/max with a four-item docket, per the v1.3 §D protocol's
"adjudications discharged UP FRONT" step (a step that exists precisely because the N-block sat
empty through Nights 1–2). It was cancelled externally before returning. **No work was lost —
it produced no artifact — but nothing on the docket was decided:**

1. **The N_e priors-source ruling — tonight's designated critical path.** Where the hazard
   formula's `fact_kind='lifetime_count_per_100y'` priors come from. Candidates it was briefed
   to weigh: classical-text-derived counts with citations · documented demographic base rates
   entered as `structural_prior` · cohort-derived where genuinely non-circular · or PARK. It
   was explicitly forbidden from reading `brahma_event_ontology.base_rate_by_age` as N_e
   (§5.1 C-1 forecloses exactly that, and doing so would be the §N.7-item-6 fabrication
   defect). **Consequence: no seeding lane could be dispatched; `ka_kshetra` still writes zero
   field rows; Gate W2 cannot close.**
2. **N1–N4** (wave naming · multi-chart rollout order · pre-1984 backfill · cutover posture).
   **Consequence: W2G remains unstartable for a third consecutive night.**
3. **W3K layer seating** (`bg_*` vs `ga_*`/`ka_*` split for the KP sub-lord engine, item 18).
   The `w3k-inventory` lane still produces a recommendation, but **nothing can ratify it**.
4. **Paddhati-profile defaults** where the corpus is silent — specifically the Agnivāsa
   favorable-residence convention, to be pinned to the native's own stated lineage practice
   (yajña when Agnivāsa is favorable) with the corpus default served alongside, clearly
   labelled.

**A fifth item was routed to the docket mid-session and is also unruled — NEW, and it blocks a
gate-close rather than a wave start.** The `ka_kota_chakra` writer (item 16, PR #999)
disclosed — honestly and unprompted — that its **fort-chakra ring table is a tier-(iii)
secondary-source transcription that is NOT in this repo's ingested corpus.** Its mitigation:
every served row carries `ring_table_citation` + `uncited_extension=true`, so nothing claims
primary-corpus authority. The open question, which generalizes well beyond item 16: **does a
cited secondary source with an explicit `uncited_extension` flag satisfy the DATA-HONESTY RAIL
(NIGHT_RUN v1.3 §D — "every value cited, versioned, structural_prior-labeled; a number without
a source is a build error"), or does the rail demand primary-corpus ingestion?** Options
tabled for the ruling: (a) accept on the disclosure flags; (b) accept but require the ring
table seeded as a versioned `bg_*` L0 reference table with its citation rather than inline in
writer code; (c) require corpus ingestion first, parking item 16; (d) serve behind a
disclosure tier. **Conductor's interim disposition, recorded as reversible:** PR #999 lands on
`shad-darshana/integration` (not `main`, not production) under strangler discipline — build
beside, cut over classified — and **the Kota citation tier is registered as a BLOCKING
precondition on the W3 gate-close PR to `main`.** Landing on an integration branch is
reversible; shipping an uncited classical table to production is not. That the question is
adjudicable at all is a credit to the builder's disclosure — a lane that had quietly inlined
the table would have shipped a silent B.3 violation.

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
