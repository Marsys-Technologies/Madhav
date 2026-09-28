# Step 6 evidence — '4.0' candidate build (plan §9)

Runbook step 6 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 2
(requires `PRODUCTION_TRANCHE_2_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** candidate build — ka_gochara writes '4.0' as `candidate` on the canonical chart; '3.0' untouched; authority stays '3.0'
- **Gate:** integrity contract green; row counts in manifest; storage measured; §12.9 fingerprint match recorded BEFORE the build
- **Reversal:** delete candidate under own scope (ledger rollback)
- **DSN target:** `127.0.0.1:5433/amjis` (production, cloud-sql-proxy)
- **Operator / principal:** `amjis_app`

## 2026-09-24 — NATIVE RULING recorded; step NOT RUN — HALTED at the §12.9 gate (E-018)

Ruling (verbatim): **"Approved on point number two. Go ahead to everything."**
(native, 2026-09-24 17:09 IST / 2026-09-24T11:39:01Z, via the main agent;
full text in ESCALATIONS.md). Scope (c): §7.C steps 6–10 authorized
notwithstanding the merge-state preconditions (P-1 / WP9 §5.2 / N-19 live on
this branch, PR #2731). Tranche-1-green achieved first (step 5 RESUMED GREEN,
see step05_evidence.md).

### §12.9 staleness gate — verified to exist; RED on production

- Gate tests: fresh disposable Postgres 16 containers recreated —
  `gochara-wp6-disposable` (55433) and `gochara-wp10-disposable` (55434) —
  `test_wp12_vedha_stamp_helpers.py` + `test_wp12_vedha_fingerprint.py`
  **40 passed, 0 skipped** (13 previously NOT_RUN for want of 55433 now run
  green). The §12.10b writer-honesty fix (`uncited_extension` read from the
  row's actual citation state, never a literal) is covered by these tests.
- Production gate state (`check_overlay_freshness`, read-only, as `amjis_app`):
  - chart `1c826d5a…`: house_vedha **stale** — 135 rows, 135 without a
    fingerprint, 0 mismatched; moorti **stale** — 72 rows, 72 without, 0
    mismatched; `gate_allows_overlays = False`
  - chart `482012f1…` (canonical): house_vedha **stale** — 132 rows, 132
    without, 0 mismatched; moorti **stale** — 71 rows, 71 without, 0
    mismatched; `gate_allows_overlays = False`
  - Diagnosis: all overlay rows predate migration 1082's stamp columns
    (applied earlier today under E-016), so every row carries a NULL
    `upstream_fingerprint`. The gate is working exactly as designed: a
    candidate must not be built on rows whose citation/fingerprint state is
    unverified.
- Prescribed remediation (step06's own refusal text): rebuild
  `ka_vedha_gochara` and `ka_moorti_nirnaya` for the chart with this branch's
  writers (which populate `upstream_fingerprint`, M-8 rows, and the §12.10b
  honesty fix). **Not performed this run** — see the halt reason below: with
  the build blocked independently, an isolated rewrite of live-served overlay
  rows would be a production change with no tranche outcome attached to it.

### HALT reason — the step-6 episode enumeration driver does not exist

`step06_candidate_build.py` consumes the candidate's episode set as
`--episodes-json` / `--coverage-json`: "at tranche time the kernel pipeline
enumerates them". No such enumerator exists on this branch or anywhere in the
sidecar: the only callers of `ledger.write_contacts` are tests and step06
itself; `ka_gochara/service.py::find_episodes` SERVES from the ledger and only
solves Moon episodes live (R7, never persisted); the gochara_kernel modules
(arcs/knots/contacts/episodes/coverage) are the solving library, with no
chart-level driver that resolves the chart's WP1 target set from L1 facts and
enumerates all bodies × relations × targets over the horizon. Writing that
driver is the core of the '4.0' writer itself — new engineering, not a
prepared tranche artifact, and §10 bars live-chart writes before the proof
matrix's gates have run for it ("no live chart before its gate"). Building it
ad hoc inside the tranche would be improvisation; per the standing order this
run stops instead.

### Independent downstream blocker (recorded, still in force)

E-012: the '4.0' **windows projection writer** (plan §2.2/§4.7 — ka_gochara
writing `kala_gochara_windows` rows for '4.0') does not exist. Step 7's
`windows_present` gate is RED by design without it and step 8 refuses to flip.
Even a completed step 6 could not reach the flip this run. The authority flip
therefore remains physically impossible until that writer is built and gated —
the native's authorization of steps 6–10 stands, but the artifacts the steps
operate on are missing.

### State summary

- Steps 6, 7, 8, 9, 10: **NOT RUN** (halted at step 6's precondition gate).
- Production unchanged by this step: no candidate manifest, no '4.0' contacts
  or coverage rows, generations **v1=38287 / 3.0=1830** untouched, authority
  rows both `'3.0'`, century `is_active=false`.
- Disposable DBs 55433/55434 torn down after the gate tests.
- Escalation: **E-018** (ESCALATIONS.md) — requests (i) a native decision on
  who builds the episode enumeration driver and the windows projection writer
  (E-012 owner question carried), (ii) whether the overlay fingerprint rebuild
  for the two authority charts should run now as its own reviewed change
  (branch writers are ready and gate-tested) so the §12.9 gate is green when
  step 6 is re-attempted.

## 2026-09-27 — Link 1 (E-018 ii) — §12.9 overlay fingerprint rebuild RUN

Per the native's E-018 ruling (2026-09-24, "Approved on point number two. Go
ahead to everything.") and review `GO-BOTH` on
`REVIEW_REQUEST_PRODUCTION_APPLICATION_SET.md` (item `39063a94`), the overlay
fingerprint rebuild ran in production for both authority charts via the
direct-runner `platform/python-sidecar/run_wp10_overlay_rebuild.py`
(writer + ContextSpec, orchestrator bypassed; writers never commit — one
explicit transaction per chart; pre/post `check_overlay_freshness` checkpointed;
exit 0 only if `gate_allows_overlays(post)`).

**Rollback anchor:** pre-run dump `.run/wp10_tranche2/pre_run_dump_20260927.dump`
(30,464,307 bytes, sha256
`392985ab6c86c9ab6a9d646853520878e051660f9bdf87d9116bbbd68f786b4a`), restore-drilled
and content-verified identical to production (see step02_evidence.md, 2026-09-27
section). Rollback of this link = restore the `kala_vedha_gochara` /
`kala_moorti_nirnaya` tables from that dump.

**Commands** (each: `cd platform/python-sidecar && PRODUCTION_TRANCHE_2_AUTHORIZED=true python3 run_wp10_overlay_rebuild.py --dsn <prod via own proxy 127.0.0.1:55440> --chart-id <uuid>`; full JSON reports in `.run/wp10_tranche2/link1_<chart>.json`):

| chart | pre (house_vedha / moorti) | vedha rows inserted | moorti rows inserted | post (house_vedha / moorti) | gate_allows_overlays |
|---|---|---|---|---|---|
| `482012f1-…871aa` (canonical) | stale 132 / stale 71 | 171 (127 house_vedha, 24 sarvatobhadra, 20 latta) | 74 (66 moorti-computed, 8/8 grahas) | **fresh 127 / fresh 74** (missing 0, mismatched 0) | **true** |
| `1c826d5a-…5f75a` (abhinandan) | stale 135 / stale 72 | 173 (132 house_vedha, 19 sarvatobhadra, 22 latta) | 74 (66 moorti-computed, 8/8 grahas) | **fresh 132 / fresh 74** (missing 0, mismatched 0) | **true** |

- Row-count drift vs the pre-run rows (177/178 vedha, 71/72 moorti) is the
  expected horizon effect: writers rebuild the day-grade horizon
  **2026-07-29 → 2027-11-01** (today−60d…+400d) with delete-then-insert per
  chart. Old-row values are preserved in the pre-run dump.
- New rows carry the current `sha256/canonical-json/v1` fingerprints:
  house_vedha `bg_transit_rules=b78cd26f…` (42 rules) + `bg_vedha_malefic_scale=6b4ee79a…` (5 rows); moorti `bg_transit_moorti=6d3c0d58…` (27 rows). `latta`/`sarvatobhadra` kinds carry no per-row detail fingerprint by design — the §12.9 freshness gate evaluates the `house_vedha` kind and moorti only; both are fresh with missing=0/mismatched=0.
- M-8 exceptions applied: chart 1 = 7 windows, chart 2 = 5 windows (Moon/Mercury
  excluded-obstructor cases; see JSON reports for the exact windows).
- §12.10b honesty fix active in the stamps; moorti notes carry
  `kernel_instant_graded=61`, `day_grade_misclassification_rate=0.4918` per chart.
- Production side effects beyond the two overlay tables: none (single
  transaction per chart covering only that chart's overlay rows; writers do not
  touch windows/authority/publication).
- **Operator / principal:** subagent (l3/gochara-autonomous-wp0-7, WP10 tranche 2).

**Verdict: Link 1 RUN and GREEN for both charts — `check_overlay_freshness` fresh, `gate_allows_overlays` true.**

## 2026-09-27 — Link 2 (E-018 candidate build) — HALTED at enumeration (kernel refine bracket loss)

After Link 1 went green for both charts (see the Link-1 section above), Link 2
was attempted in packet order. The very first producer step failed before any
write:

- **Command:** `step06_enumerate_episodes.py --dsn <prod via own proxy 127.0.0.1:55440> --chart-id 482012f1-710e-4a25-994a-93821f5871aa --episodes-out .run/wp10_tranche2/episodes_482012f1.json --coverage-out .run/wp10_tranche2/coverage_482012f1.json` (defaults: horizon 2020-01-01→2030-01-01, orb 5.0, refine on; `PRODUCTION_TRANCHE_2_AUTHORIZED=true`). Log: `.run/wp10_tranche2/step06_enum_482012f1.log`.
- **Result:** exit 1 — `ValueError: Sun: separation root at 30.0000° lost its bracket under direct Swiss (2462240.4338207245..2462504.0)` raised from `gochara_kernel/contacts.py::swiss_bisect` via `find_boundary_roots` ← `episodes.py::residence_spans` ← `step06_enumerate_episodes.py::enumerate_body`. The §12.9 overlay gate itself PASSED (enumeration started — Link 1 did its job); the failure is inside kernel root refinement, on the first body's residence-span enumeration.
- **Mechanism (chart-independent):** `find_boundary_roots` (contacts.py:246) refines each boundary root by calling `swiss_bisect(body, arc.start_jd, arc.end_jd, level, …)` over the **whole arc**. For the Sun a wrap-band arc spans up to a full year (~260–365 days, e.g. the failing arc 2029-04-14→2029-12-30); the pointwise wrapped separation `((lon − level + 180) % 360) − 180` crosses its ±180° branch cut inside any arc whose travel extends more than 180° past the level, so both arc endpoints evaluate with the same sign and the bracket is reported lost (the ±25% widen-once rescue cannot fix a branch-cut crossing). `swiss_bisect`'s own docstring assumes "a sub-day bracket". **Scope correction (PRAMĀṆIN, per ADK-0019):** the defect is not Sun-only — on a 2029 horizon Sun, Moon AND Venus fail, Mars/Mercury can fail in other years (any arc with >180° of travel past the level loses the bracket), and the same defect fires through `find_roots` for conjunction/drishti levels; the docstring's sub-day-bracket design assumption was wrong, not just the code. Consequence: with `refine=True`, sign-ingress enumeration over full arcs fails for any chart/horizon — this path was never exercised green: all branch-local tests call the kernel with `refine=False` on synthetic curves (`tests/l3/gochara/test_step06_enumeration.py`), and the packet's 363/363 evidence is disposable-DB test evidence only.
- **Not done, deliberately:** (i) `--no-refine` was NOT used — it would silently downgrade every persisted `t_exact` to spline-only precision, a precision-regime deviation the review packet does not disclose; (ii) no kernel patch was attempted — narrowing the Swiss bracket around the spline root (or bisecting on the unwrapped longitude with the arc's wrap band) is new engineering in the solving library, barred inside the tranche by the standing order. Both are ruled decisions for the native, not the executor.
- **Production state after the halt:** unchanged by Link 2 — no episodes/coverage payloads consumed, no `'4.0'` rows in publication/contacts/coverage/windows (verified: all still 0 rows / v1=38,287 / 3.0=1,830 / authority both `'3.0'`). Link 1's rebuilt overlay rows remain live and fresh.
- **Escalation requested:** a native ruling on (a) authorizing the enumeration with `--no-refine` (spline exacts, disclosed as such), or (b) commissioning a reviewed kernel fix for boundary-root refinement brackets (e.g. refine over a narrow window around `_bisect_arc`'s spline root, not the full arc) plus a regression test with `refine=True` on a real Sun curve, after which Link 2 can be re-attempted as written.

**Verdict: Link 2 HALTED at step-6 enumeration precondition — kernel refine defect, no production writes made, no gates bypassed.**

## 2026-09-27 — ADK-0019 path (b) kernel patch + disposable-DB rehearsal — GREEN (production re-run NOT attempted)

ADHIKARIN ruling ADK-0019 chose path (b): a narrow-window refinement patch in
the gochara kernel, with a mandatory regression test, a green full battery, and
a step06 disposable-DB rehearsal as preconditions for any production re-run of
Link 2 (which additionally awaits PRAMĀṆIN re-verification). This section
records the patch, its verification, and the rehearsal. **No production write
path was run.**

### Patch (kernel internals only — no flag, gate, shape, contract, or parameter change)

- `services/gochara_kernel/contacts.py`:
  - `swiss_bisect` docstring corrected: the wrapped-separation objective is
    continuous only while the bracket keeps <180° of travel from the level;
    whole-arc bracketing is invalid (the ADK-0019 defect), replacing the old
    false "sub-day bracket" design assumption.
  - New module constants `_REFINE_INITIAL_HALF_WINDOW_DAYS = 1.0`,
    `_REFINE_WINDOW_GROWTH = 4.0`, `_REFINE_MAX_TRAVEL_DEG = 90.0`, and a new
    `_refine_root(body, arc, spline_jd, level_wrapped_deg, ephe_path)` helper:
    the refinement bracket is a ±1-day window around the spline root, clamped
    inside the arc; on a lost bracket (spline/Swiss disagreement near a
    station) the window grows ×4 up to a cap derived from the arc's mean
    travel rate (≤90° of travel, comfortably short of the ±180° branch cut);
    if the capped or whole-arc window still does not bracket, `swiss_bisect`'s
    ValueError propagates as a real failure.
  - Both call sites — `find_roots` (conjunction/drishti) and
    `find_boundary_roots` (sign ingress) — now refine via `_refine_root`
    instead of bisecting the whole arc.
- `services/gochara_kernel/episodes.py` — **scope extension beyond ADK-0019's
  literal two call sites, disclosed for PRAMĀṆIN re-verification (escalate on
  dissent):** `residence_spans` wrapped a span end of exactly 360.0 to 0.0 and
  refused the legitimate Pisces whole-sign span `(330.0, 360.0)` that the
  driver's `_sign_span` emits for sign 12. Fix: after wrapping, restore
  `hi_w = 360.0` when the unwrapped end exceeds the start. Additive only
  (accepts a previously-refused valid span; no accepted input changes
  meaning), reversible, 5 lines.
- Regression tests in `tests/l3/gochara/test_wp3a_kernel.py`:
  - `test_adk0019_refine_real_long_arcs_2029` (requires_swieph): real
    Sun/Moon/Venus arc indexes over calendar 2029 (the PRAMĀṆIN failure year);
    every sign-ingress root refines under refine=True (Sun ≥11, Moon ≥140,
    Venus ≥11 roots), each refined instant within 0.1 d of the spline root and
    landing the body within 1″ of the level.
  - `test_adk0019_refine_find_roots_conjunction_2029` (requires_swieph): the
    shared `find_roots` path refines green on a real Sun conjunction target.
  - `test_pisces_whole_sign_span_not_refused`: synthetic regression for the
    episodes.py span-wrap fix.

### Battery

`cd platform/python-sidecar && WP6_LEDGER_DSN=postgresql://wp6:disposable@localhost:55435/wp6 ../../.venv/bin/python -m pytest tests/l3/gochara -q`
(disposable containers `gochara-wp6-disposable` on :55435 and
`gochara-wp6-remainder` on :55434): **366 passed, 0 skipped** (365 prior + 1
new Pisces-span test). Log: `.run/wp10_tranche2/battery_after_pisces_fix.log`.

### Rehearsal (step06 enumeration, disposable DB `wp10_rehearsal` on :55434, refine ON, candidate-1 flags `linear_no_box` + orb 5.0°)

The rehearsal DB was rebuilt from production content (schema + overlay tables
+ reference_signs + chart-scoped chart_facts: 143,299 rows chart 1 / 139,717
rows chart 2) so the §12.9 overlay gate passes on the post-Link-1 fresh rows.

| chart | command exit | resonance rows → targets | resolution (resolved/unavailable) | episodes emitted | excluded w/o exact | coverage partitions | refine | backends |
|---|---|---|---|---|---|---|---|---|
| `482012f1-…871aa` | 0 (~32 min) | 765 → 1140 | 493 / 647 | **1,353,278** | 1,452 | 48 | true | swieph ×8 (retflag 65602) |
| `1c826d5a-…5f75a` | 0 (~33 min) | 753 → 1131 | 493 / 638 | **1,353,288** | 1,098 | 48 | true | swieph ×8 (retflag 65602) |

- Logs: `.run/wp10_tranche2/rehearsal_enum_{482012f1,1c826d5a}.log`; payloads:
  `rehearsal_episodes_*.json`, `rehearsal_coverage_*.json` in the same dir.
- Upstream fingerprints match production exactly: `bg_transit_rules`
  b78cd26f…, `bg_vedha_malefic_scale` 6b4ee79a…, `bg_transit_moorti`
  6d3c0d58….
- **Unavailable-target disclosure:** the `unavailable` counts (647 / 638:
  `yoga_constituent` 595/586 + `lord` 52/52) reproduce **byte-identically when
  the same resolution is run against production** (read-only check via
  127.0.0.1:55440) — this is the honest pre-existing resolution state of the
  current resonance rows, not a stripped-rehearsal-DB artifact. (The map
  rows' own stored `target_resolution_state` says 'resolved'; live
  re-resolution against current L1 facts disagrees for those target types.
  Recorded, not "fixed" — disposition belongs to the native/PRAMĀṆIN.)

**Verdict: ADK-0019 preconditions met — patch landed, regression tests green, battery 366/366, step06 disposable rehearsal GREEN for both charts under candidate-1 flags with refine on. Link 2 production re-run NOT attempted: it awaits PRAMĀṆIN's re-verification (drift check) per the ruling.**

## 2026-09-28 — Link 2 production run — HALTED at step06_candidate_build (contact-id multiplicity collision)

After PRAMĀṆIN verified the ADK-0019 amended package (`f1ee17c81`) and the
native re-authorized tranche 2, Link 2 was attempted against production (own
proxy 127.0.0.1:55440, fresh `amjis-pipeline-db-url` creds per connection,
`PRODUCTION_TRANCHE_2_AUTHORIZED=true`).

**Pre-run state (verified immediately before):** zero `'4.0'` rows in
`kala_gochara_contacts` / `_coverage` / `_convention` / `_publication` /
`_windows`; windows `v1`=38,287 / `3.0`=1,830; authority untouched.

**Step 1 — enumeration, chart `482012f1-…871aa`: GREEN.** Command:
`step06_enumerate_episodes.py --dsn <prod via 55440> --chart-id 482012f1-… --episodes-out .run/wp10_tranche2/prod_episodes_482012f1.json --coverage-out .run/wp10_tranche2/prod_coverage_482012f1.json`.
Exit 0, 32.6 min. Report (`.run/wp10_tranche2/prod_enum_482012f1.log`):
**reproduces the disposable-DB rehearsal exactly** — 765 resonance rows → 1140
targets (493 resolved / 647 unavailable, matching the pre-existing production
resolution state documented in the rehearsal section), 1,353,278 episodes
emitted, 1,452 without-exact excluded, 48 coverage partitions, refine ON,
swieph ×8, fingerprints b78cd26f…/6b4ee79a…/6d3c0d58…. The ADK-0019 patch
performs exactly as rehearsed.

**Step 2 — candidate build, chart `482012f1-…871aa`: FAILED, exit 1.** Command:
`step06_candidate_build.py --dsn <prod via 55440> --chart-id 482012f1-… --episodes-json …/prod_episodes_482012f1.json --coverage-json …/prod_coverage_482012f1.json --delta-report .run/wp10_tranche2/prod_delta_report_482012f1.md --evidence`.
Log: `.run/wp10_tranche2/prod_build_482012f1.log`. The §12.9 freshness gate
PASSED (writes began); the failure is a `UniqueViolation` on
`kala_gochara_contacts_pkey` — duplicate `contact_id`
`sha256:ed53a48a…` inside the insert batch. The transaction rolled back in
full (single-transaction writer).

**Diagnosis (payload scan, no production state involved):** the enumeration
payload contains 1,353,278 episodes but only **138,837 unique contact ids** —
138,767 ids repeat (1,214,441 extra rows). Duplicates share one
`independence_group` (H-6: one physical contact reached via several map rows);
within a duplicate group the rows are byte-identical (46,422 groups) or differ
only in `classical_citation` (46,353) or `target_ref` (45,992) — i.e. the
enumerator emits per (map row × level), while the ledger's pinned WP1 §3.2
contact id identities per physical contact. Duplicate concentration:
kakshya_cell_crossing / nakshatra_ingress / sign_ingress on fast bodies
(Mercury 173k, Venus 147k, Sun 140k, Mars 80k extra rows). The contract
question — how multiplicity is represented (dedupe at enumeration vs ledger,
which citation/weight survives) — is a ruling-level decision, not an executor
one. This collision was invisible at test scale (synthetic fixtures, far fewer
rows); the disposable rehearsal stopped at enumeration and never inserted.

**Post-failure production state (verified):** `kala_gochara_contacts`=0,
`_coverage`=0, `_convention`=0, `_publication`=0, windows `v1`=38,287 /
`3.0`=1,830 — byte-identical to the pre-run state; rollback complete, no
partial writes. Chart 2 (`1c826d5a-…`) was NOT started (same wall awaits its
candidate build). Pre-run dump `.run/wp10_tranche2/pre_run_dump_20260927.dump`
retained.

**Escalation requested:** a native ruling on the multiplicity contract —
e.g. (a) enumeration dedupes to one episode per physical contact (pinned id)
with a disclosed citation/weight merge rule, or (b) the ledger stores
multiplicity explicitly. Until ruled, Link 2 remains HALTED after a green
step 1 for chart 1 only.

**Verdict: Link 2 HALTED at step06_candidate_build — enumeration green and
rehearsal-exact; candidate-ledger write impossible under the current pinned
contact-id contract at production multiplicity; production left untouched and
verified clean.**

## 2026-09-28 — ADK-0020 option (i) dedupe implemented + rehearsed — driver REFUSES on real data (ruling premise falsified; Link 2 stays HALTED)

ADK-0020 (commit `d58e8c171`) ruled option (i): dedupe at enumeration in
`step06_enumerate_episodes.py`, keyed by the pinned WP1 §3.2 contact_id;
survival = highest-weight map row, weight ties → lexicographically smallest
target_ref, deeper ties surfaced as map defects; a duplicate group carrying
divergent NON-NULL classical_citation values REFUSES the run (the ruling's
own escalation clause); dedupe counts disclosed (total / per relation / per
survival tier); dropped target_refs recoverable via a dropped-refs artifact
keyed by contact_id.

### Patch (enumeration driver only — ledger, ids, schema, flags, gates, M-1 orb untouched)

`step06_enumerate_episodes.py`:
- `ResolvedTarget` gains `weight` (the source map row's weight, carried for
  the survival rule); `_episode_to_dict` stamps it as `_map_weight`, stripped
  from survivors before the payload is written.
- New `DedupeRefusal` exception, `_contact_id_of` (the pinned §3.2 id exactly
  as the ledger computes it — verified equal to
  `ledger.convention_id_for(CONVENTION_VECTOR)` /
  `gk_convention.canonical_convention_id()` =
  `sha256:38218e65c6f918eaaa5cbb814235c624a65e888e6f838d5942fe0ea815c10296`,
  method_version `1.0.0`), and `dedupe_episodes()` implementing the ruled
  survival tiers, the divergent-citation refusal, the disclosure report
  (`episodes_before/after`, `rows_dropped`, `duplicate_groups`,
  `per_relation_dropped`, `per_survival_tier`, `deeper_tie_groups`,
  `groups_with_multiple_independence_groups`, `dropped_refs_contacts`), and
  the dropped-refs artifact `<episodes-out>.dropped_refs.json`
  (contact_id → {survivor_target_ref, dropped_target_refs, dropped_rows}).
- `main()` dedupes after enumeration, before payload write; refusal prints
  `REFUSED (ADK-0020): …` and exits **5** (documented in the module docstring).

### Tests

`tests/l3/gochara/test_step06_enumeration.py` (all pass):
- `test_dedupe_weight_order_wins` — higher weight survives; counts, per-tier
  and per-relation disclosure, dropped-refs artifact content verified.
- `test_dedupe_weight_tie_breaks_lexicographic` — equal weights → smallest
  target_ref.
- `test_dedupe_deeper_tie_surfaced_not_silent` — same weight AND same ref →
  deterministic survivor + `deeper_tie_groups` populated (map defect
  surfaced, never silent).
- `test_dedupe_none_weight_loses_to_any_number` — NULL weight sorts last.
- `test_dedupe_divergent_citations_refuse` — `pytest.raises(DedupeRefusal)`.
- `test_dedupe_identical_null_citations_do_not_refuse`.
- `test_dedupe_strips_map_weight_and_keeps_singletons` — `_map_weight`
  stripped, singletons untouched, output sorted.
- `test_dedupe_two_map_rows_one_physical_target` (mandatory e2e regression,
  disposable DB): two map rows (`marriage`/karaka/Venus @0.9,
  `career_advancement`/karaka/Venus @0.6) resolving to the SAME physical
  target → one emitted row per pinned contact_id (Counter check over the
  whole payload), dedupe count disclosed in the report, dropped-refs
  artifact records the Venus pair, and after `step06_candidate_build`
  consumes the payload the ledger holds exactly one row per contact_id
  (`GROUP BY contact_id HAVING count(*)>1` → empty) with the surviving
  Venus contacts present exactly once.

### Battery

`cd platform/python-sidecar && WP6_LEDGER_DSN=postgresql://wp6:disposable@localhost:55435/wp6 ../../.venv/bin/python -m pytest tests/l3/gochara -q`
(disposable pg16 containers `gochara-wp6-disposable` :55435,
`gochara-wp6-remainder` :55434): **374 passed, 0 failed, 0 skipped**
(incl. all 8 new dedupe tests; both pre-existing e2e tests still green with
the duplicate map row added to the shared seed).

### Rehearsal (disposable DB `wp10_rehearsal` on :55434, rebuilt from retained production dumps; candidate-1 flags: linear_no_box, orb 5.0°, refine ON)

| chart | enumeration exit | result |
|---|---|---|
| `482012f1-…871aa` (~32 min enumerate) | **5 (REFUSED)** | 46,353 duplicate groups carry divergent non-null citations |
| `1c826d5a-…5f75a` (~31 min enumerate) | **5 (REFUSED)** | 46,354 duplicate groups carry divergent non-null citations |

Logs: `.run/wp10_tranche2/adk0020_rehearsal_enum_{482012f1,1c826d5a}.stderr`.
No payload was written (refusal precedes the write); per the ruling the
candidate build was NOT attempted.

### The ruling's premise is falsified on real data — escalation

ADK-0020 states citations are null on every duplicate row (recount: 92,775
fully-identical + 45,992 target_ref-only groups, zero citation-divergent).
Against the retained production payload
`.run/wp10_tranche2/prod_episodes_482012f1.json` (1,353,278 episodes), an
independent re-scan keyed by the driver's own `_contact_id_of` finds
**138,767 duplicate groups** (matching the prior census exactly): 92,414
citation-identical-or-null and **46,353 with divergent NON-NULL
classical_citation values**. Sample group `sha256:3df8c585…`
(Sun/kakshya_cell_crossing/karaka/Mercury) carries citations from different
event classes ("BPHS ch.1 (lagna, temperament) — inherited from
chronic_onset…", "BPHS ch.2,11 (dhana-bhava)", "BPHS ch.10 (karma-bhava)…",
…). The driver therefore REFUSES exactly as the ruling mandates — no
citation-selection rule was invented (§N.7/§N.8). Consequence: **Link 2
cannot go green under ADK-0020 as written**; it remains HALTED pending an
amended ruling (e.g. citation follows the surviving weight-selected row, or
an explicit citation-merge rule). The weight/tie survival tiers are verified
by unit + e2e tests but were never exercised on real data — the refusal
fires first, by design. Production was NOT touched.

## ADK-0021 option (A) — citation-only divergence survives; Link 2 rehearsal GREEN

ADK-0021 (`00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md`) amends ADK-0020:
a duplicate group whose rows diverge ONLY in `classical_citation` SURVIVES —
the surviving weight-selected row's citation is kept as that row's
event-class provenance (not a synthesis of the group), with disclosure in
both the run report and the episodes payload evidence. Exit-5 refusal is
retained for divergence in ANY other field (residual field-divergence check
over every payload key except `target_ref`, `classical_citation`,
`_map_weight`; missing-vs-present counts as divergence). Dropped citations
are recoverable in `.dropped_refs.json` (each entry now carries
`survivor_citation` and sorted-unique `dropped_citations`). No new
contact-row field; no schema change. Implemented in
`step06_enumerate_episodes.py` (`_SURVIVAL_FIELDS`, residual check,
`groups_with_divergent_citations` report count, `citation_rule` string).

### Disclosure wording as shipped (substance-verbatim in report AND payload)

> ADK-0021 option (A): classical_citation follows the surviving weight-selected map row; it is that row's event-class provenance, not a synthesis of the duplicate group; {N} groups had divergent non-null citations; dropped citations are recoverable in .dropped_refs.json keyed by contact_id

N = 46,353 (chart 482012f1), 46,354 (chart 1c826d5a) — matching the
ADK-0020-era refusal counts exactly.

### Tests (driver unit + e2e, `tests/l3/gochara/test_step06_enumeration.py`)

- `test_dedupe_divergent_citations_survive_with_disclosure` (replaces the
  ADK-0020 refusal test) — survivor keeps its own citation, N=1 disclosure
  substrings present in report and artifact, dropped citations recorded.
- `test_dedupe_non_citation_divergence_refuses` — divergence in
  `orb_max_deg` → `DedupeRefusal` (exit-5 domain intact).
- `test_dedupe_deeper_tie_with_divergent_citations_surfaces_defect` —
  deeper tie + divergent citations → surfaced AND survives.
- `test_dedupe_two_map_rows_one_physical_target` (mandatory e2e) — gained
  assertion that `citation_rule` embeds the N count.

### Battery

`cd platform/python-sidecar && WP6_LEDGER_DSN=postgresql://wp6:disposable@localhost:55435/wp6 ../../.venv/bin/python -m pytest tests/l3/gochara -q`
(disposable pg16 containers): **376 passed, 0 failed, 0 skipped**.

### Rehearsal (disposable DB `wp10_rehearsal` on :55434, rebuilt from retained production dumps; candidate-1 flags: linear_no_box, orb 5.0°, refine ON)

| chart | enumeration | dedupe | divergent-citation groups | candidate build |
|---|---|---|---|---|
| `482012f1-…871aa` | exit **0** (~32 min) | 1,353,278 → 138,837; 138,767 dup groups; 1,214,441 dropped | **46,353** | exit **0**; contacts_written **138,837**; coverage 48; zero UniqueViolation |
| `1c826d5a-…5f75a` | exit **0** (~13 min) | 1,353,288 → 138,836; 138,766 dup groups; 1,214,452 dropped | **46,354** | exit **0**; contacts_written **138,836**; coverage 48; zero UniqueViolation |

Per-relation dropped (chart 1): kakshya 826,893 / nakshatra 257,382 /
sign_ingress 113,198 / drishti 9,462 / conjunction 6,801 / return 705.
Survival tiers: **all duplicate groups resolved at the `deeper_tie` tier**
(weight 0, lexicographic 0) — on this map, duplicate rows carry identical
weight AND identical target_ref across event classes, so only the
deeper-tie tier fires; the full 138,767/138,766-entry `deeper_tie_groups`
list is surfaced in each run report as mandated (report ~32 MB; observed
behavior, not a defect). Ledger cross-check: `kala_gochara_contacts` holds
exactly 138,837 / 138,836 generation-4.0 rows per chart, coverage 48 each.
Freshness fresh; vedha/moorti fingerprints b78cd26f…/6b4ee79a…/6d3c0d58…
both charts. Logs: `.run/wp10_tranche2/adk0021_rehearsal_{enum,build}_*.log`
(zero-length stderr throughout).

Retained-payload validation (`.run/wp10_tranche2/validate_adk0021_on_prod_payload.py`
against `prod_episodes_482012f1.json`): amended dedupe — no refusal,
138,837 survivors, 46,353 divergent-citation groups disclosed, multi-IG 0,
`_map_weight` stripped. Matches the rehearsal exactly.

### Verdict

Link 2 (enumeration + candidate build) is GREEN on both rehearsal charts
under ADK-0021 option (A). Production was NOT touched; the production
Link 2 re-run proceeds only after PRAMĀṆIN re-verifies naming this run.

## ADK-0022 — dissent-rule re-rule: citation null-and-disclose on citation-divergent groups; Link 2 rehearsal GREEN

ADK-0022 (`00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md`) amends ADK-0021 on
its operative point: PRAMĀṆIN's deeper_tie census (weight: 0,
weight_tie_lexicographic: 0, deeper_tie: 138,767 — every duplicate group)
falsified ADK-0021's premise that a weight RULE earned the surviving
citation; the actual selector was `json.dumps` lexicographic order — a
property of the encoding, not of provenance (§N.8 earned signal). Re-ruled:
on citation-DIVERGENT groups the surviving row's classical_citation is NULL
(null-and-disclose, §N.7); groups whose citations AGREE non-null keep that
citation; all-null groups stay null; every citation of a nulled group is
recoverable in `.dropped_refs.json` (survivor_citation null there too,
dropped_citations carries EVERY group citation). The deeper-tie selector is
unaffected for row survival (a row must survive; the pick is immaterial
once the citation is nulled). Exit-5 refusal for divergence in any other
field stands. No schema/contract/flag/gate change. Implemented in
`step06_enumerate_episodes.py` (`survivor["classical_citation"] = None` on
divergent groups; dropped-refs entries now also created for
same-target_ref divergent groups; amended `citation_rule`; new record-only
`weight_tier_note`).

### Disclosure wording as shipped (substance-verbatim in report AND payload)

> ADK-0022 (amending ADK-0021): classical_citation follows the surviving map row where the group's citations agree; on {N} citation-divergent groups no rule earns a single citation and the field is NULL — all group citations recoverable in .dropped_refs.json keyed by contact_id

N = 46,353 (chart 482012f1), 46,354 (chart 1c826d5a) — matching the
ADK-0021 counts exactly.

### Uniform weight 0 — record-only (ADK-0022 (3))

Every run report now carries `weight_tier_note` when all duplicate groups
resolve at deeper_tie: weight is uniform (0) across all 138,767/138,766
duplicate groups; the weight and weight_tie_lexicographic tiers never fired
on this data. Recorded as an observation; NO action — weight semantics
belong to WP8 (E-008); a never-firing tier is a disclosure item, not a
defect to repair in this lane.

### Tests (driver unit + e2e, `tests/l3/gochara/test_step06_enumeration.py`)

- `test_dedupe_divergent_citations_nulled_with_disclosure` (replaces the
  ADK-0021 survive test) — survivor's citation is NULL, N=1 disclosure
  substrings (new wording), dropped_refs entry carries survivor_citation
  null and BOTH group citations.
- `test_dedupe_agreeing_non_null_citations_keep_the_citation` (NEW) —
  identical non-null citations survive unambiguous: the survivor KEEPS the
  agreed citation; group not counted divergent.
- `test_dedupe_deeper_tie_with_divergent_citations_surfaces_defect` —
  updated: deeper_tie surfaced AND survivor citation NULL.
- `test_dedupe_non_citation_divergence_refuses` — exit-5 residual domain
  intact (unchanged).
- `test_dedupe_two_map_rows_one_physical_target` (mandatory e2e) — asserts
  the new citation_rule wording embeds N.

### Battery

`cd platform/python-sidecar && WP6_LEDGER_DSN=postgresql://wp6:disposable@localhost:55435/wp6 ../../.venv/bin/python -m pytest tests/l3/gochara -q`
(disposable pg16 containers `gochara-wp6-disposable` :55435,
`gochara-wp6-remainder` :55434, torn down after): **377 passed, 0 failed,
0 skipped**.

### Rehearsal (disposable DB `wp10_rehearsal` on :55434, rebuilt from retained production dumps; candidate-1 flags: linear_no_box, orb 5.0°, refine ON)

| chart | enumeration | dedupe | citation-divergent groups NULLED | candidate build |
|---|---|---|---|---|
| `482012f1-…871aa` | exit **0** (~32 min) | 1,353,278 → 138,837; 138,767 dup groups; 1,214,441 dropped | **46,353** | exit **0**; contacts_written **138,837**; coverage 48; zero UniqueViolation |
| `1c826d5a-…5f75a` | exit **0** (~13 min) | 1,353,288 → 138,836; 138,766 dup groups; 1,214,452 dropped | **46,354** | exit **0**; contacts_written **138,836**; coverage 48; zero UniqueViolation |

Payload citation census: chart 1 — null 138,697 / non-null 140 (the 140 =
the 70 citation-agreeing groups' survivors plus citation-carrying
singletons); chart 2 — null 138,696 / non-null 140. Per-relation dropped
(chart 1): kakshya 826,893 / nakshatra 257,382 / sign_ingress 113,198 /
drishti 9,462 / conjunction 6,801 / return 705. Survival tiers again
100% deeper_tie (138,767 / 138,766 groups surfaced; ~32 MB report;
mandated disclosure, not a defect). Ledger cross-check:
`kala_gochara_contacts` holds exactly 138,837 / 138,836 generation-4.0 rows
per chart, coverage 48 each. Freshness fresh; identical vedha/moorti
fingerprints on both charts. Logs:
`.run/wp10_tranche2/adk0022_rehearsal_{enum,build}_*.log` (zero-length
stderr throughout).

Retained-payload validation (`.run/wp10_tranche2/validate_adk0022_on_prod_payload.py`
against `prod_episodes_482012f1.json`): no refusal, 138,837 survivors,
46,353 divergent groups nulled + disclosed, survivor citations null
138,697 / non-null 140, multi-IG 0, `_map_weight` stripped, weight_tier_note
present. Matches the rehearsal exactly.

### Verdict

Link 2 (enumeration + candidate build) is GREEN on both rehearsal charts
under ADK-0022 null-and-disclose. Production was NOT touched; the
production Link 2 re-run proceeds only after PRAMĀṆIN re-verifies naming
this run.

## 2026-09-28T00:21:46Z — GREEN

```json
{
  "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
  "generation": "4.0",
  "convention_id": "sha256:38218e65c6f918eaaa5cbb814235c624a65e888e6f838d5942fe0ea815c10296",
  "manifest_id": "d54d899b-7923-4b0d-92c5-0ff499f4a0bf",
  "build_id": "wp10-step6-1790554869",
  "contacts_written": 138837,
  "coverage_rows_written": 48,
  "input_generation_vector": {
    "activity_shape": "linear_no_box",
    "moon_channel": "separate",
    "nodal_drishti": "removed",
    "sade_sati_mode": "testimony",
    "kakshya_bindu_interim": true,
    "overlay_stamps": true,
    "vedha_exceptions": "m8_rows",
    "orb_max_deg": 5.0,
    "orb_ruling": "M-1 fallback no-box \u00d7 5.0\u00b0 (unratified)",
    "delta_report": ".run/wp10_tranche2/link2_delta_report_482012f1.md",
    "vedha_upstream_freshness": "fresh",
    "moorti_upstream_freshness": "fresh",
    "vedha_upstream_fingerprint": {
      "algorithm": "sha256/canonical-json/v1",
      "bg_transit_rules": "b78cd26fe30a1911066d0e8aa80738595d39610d0467cf6cf03404967ba5db61",
      "n_transit_rules": 42,
      "bg_vedha_malefic_scale": "6b4ee79a218b27249b6c9c84d20a01c08d2d8ab236522958a99f4cf218e28466",
      "n_malefic_scale_rows": 5
    },
    "moorti_upstream_fingerprint": {
      "algorithm": "sha256/canonical-json/v1",
      "bg_transit_moorti": "6d3c0d58a3668145c7bd85a2c15197fcebcb1588511cfa62046bc01793f0ad89",
      "n_moorti_rows": 27
    }
  }
}
```

## 2026-09-28T00:57:36Z — GREEN

```json
{
  "chart_id": "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
  "generation": "4.0",
  "convention_id": "sha256:38218e65c6f918eaaa5cbb814235c624a65e888e6f838d5942fe0ea815c10296",
  "manifest_id": "4dc6c74c-4efa-4dc7-86ff-d31b1b038359",
  "build_id": "wp10-step6-1790557021",
  "contacts_written": 138836,
  "coverage_rows_written": 48,
  "input_generation_vector": {
    "activity_shape": "linear_no_box",
    "moon_channel": "separate",
    "nodal_drishti": "removed",
    "sade_sati_mode": "testimony",
    "kakshya_bindu_interim": true,
    "overlay_stamps": true,
    "vedha_exceptions": "m8_rows",
    "orb_max_deg": 5.0,
    "orb_ruling": "M-1 fallback no-box \u00d7 5.0\u00b0 (unratified)",
    "delta_report": ".run/wp10_tranche2/link2_delta_report_1c826d5a.md",
    "vedha_upstream_freshness": "fresh",
    "moorti_upstream_freshness": "fresh",
    "vedha_upstream_fingerprint": {
      "algorithm": "sha256/canonical-json/v1",
      "bg_transit_rules": "b78cd26fe30a1911066d0e8aa80738595d39610d0467cf6cf03404967ba5db61",
      "n_transit_rules": 42,
      "bg_vedha_malefic_scale": "6b4ee79a218b27249b6c9c84d20a01c08d2d8ab236522958a99f4cf218e28466",
      "n_malefic_scale_rows": 5
    },
    "moorti_upstream_fingerprint": {
      "algorithm": "sha256/canonical-json/v1",
      "bg_transit_moorti": "6d3c0d58a3668145c7bd85a2c15197fcebcb1588511cfa62046bc01793f0ad89",
      "n_moorti_rows": 27
    }
  }
}
```

## 2026-09-28 — Link 2 production re-run (ADK-0022, commit 91eb3b9f6) — RUN and GREEN, both charts

After PRAMĀṆIN verified the ADK-0022 package (`91eb3b9f6`), Link 2 was executed
against production under `PRODUCTION_TRANCHE_2_AUTHORIZED=true`: own
cloud-sql-proxy on 127.0.0.1:55440 (the stale prior-window listener was killed
and replaced), fresh `amjis-pipeline-db-url` credentials fetched from Secret
Manager immediately before each connection, the native's 5433 session never
touched. The pre-dedupe payload `prod_episodes_482012f1.json` was NOT reused;
both enumerations ran fresh.

**Pre-run gates (all PASS, read-only):** zero `'4.0'` rows in
`kala_gochara_contacts` / `_coverage` / `_convention` / `_publication` /
`_windows`; windows `v1`=38,287 (md5 7c92025246d9fc870471789b5ab58876) /
`3.0`=1,830 (md5 85578c77dde8b8bd13d8dcea71ab237a); authority `3.0` both
charts (md5 034c31bbfc285ce9808387884af36278); `kala_gochara_generation_guard`
+ windows triggers and `kala_gochara_convention_immutable` present; §12.9
`check_overlay_freshness` = house_vedha FRESH, moorti FRESH, both charts.
(Recorded in `.run/wp10_tranche2/link2_prerun_state_20260928.txt`.)

**Chart 1 `482012f1-…871aa`:**
- Enumeration (exit 0, 33.3 min; log `.run/wp10_tranche2/link2_enum_482012f1.log`):
  765 resonance rows → 1,140 targets (493 resolved / 647 unavailable),
  1,353,278 episodes → **138,837 contacts** (1,214,441 dropped over 138,767
  duplicate groups, 100% deeper_tie), **46,353 citation-divergent groups
  nulled** (ADK-0022), 1,452 without-exact excluded, 48 coverage partitions,
  refine ON, swieph ×8, fingerprints b78cd26f…/6b4ee79a…/6d3c0d58….
  Payload: 138,697 citation-NULL / 140 present; 138,767 `.dropped_refs.json`
  entries. Rehearsal-exact.
- Candidate build (exit 0, 43 s; log `.run/wp10_tranche2/link2_build_482012f1.log`):
  §12.9 gate FRESH (both overlays); convention `sha256:38218e65…10296`;
  manifest `d54d899b-7923-4b0d-92c5-0ff499f4a0bf`, status `candidate`
  (NOT published); **contacts_written 138,837; coverage 48**. No
  UniqueViolation — the ADK-0022 dedupe holds at production scale.

**Chart 2 `1c826d5a-…f75a`:**
- Enumeration (exit 0, 32.8 min; log `.run/wp10_tranche2/link2_enum_1c826d5a.log`):
  753 resonance rows → 1,131 targets (493 resolved / 638 unavailable),
  1,353,288 episodes → **138,836 contacts**, **46,354 citation-divergent
  groups nulled**, 1,098 without-exact excluded, 48 coverage partitions,
  same fingerprints. Payload: 138,696 citation-NULL / 140 present; 138,766
  `.dropped_refs.json` entries. Rehearsal-exact.
- Candidate build (exit 0, 40 s; log `.run/wp10_tranche2/link2_build_1c826d5a.log`):
  §12.9 gate FRESH; same convention id; manifest
  `4dc6c74c-4efa-4dc7-86ff-d31b1b038359`, status `candidate`;
  **contacts_written 138,836; coverage 48**.

**Post-run verification (read-only; `.run/wp10_tranche2/link2_final_state_20260928.txt`):**
- `'4.0'` contacts: 138,837 (482012f1) / 138,836 (1c826d5a); citation-NULL
  138,697 / 138,696 in the database (matches payloads exactly).
- `'4.0'` coverage: 48 / 48. Publications: both `candidate`, content_digest
  `sha256:unpublished-candidate` — **nothing published, no authority flip**
  (Link 3 remains separately conditioned).
- Content digests of new rows: contacts md5 0f38c343b158a849dd5df04d5c7935f3
  (482012f1) / 5fb0e780b39bc7318445bf433023f1aa (1c826d5a); coverage md5
  cd03f9dc0551789ec0c481142b042c3d / d25d3ad397aba77144e503dac8b253fe.
- Untouched: windows `v1`=38,287 (md5 unchanged 7c920252…) / `3.0`=1,830 (md5
  unchanged 85578c77…); zero `'4.0'` windows; authority `3.0` both charts;
  §12.9 overlays re-checked FRESH both charts post-run.
- Delta-report pointers recorded in both input generation vectors
  (`.run/wp10_tranche2/link2_delta_report_<chart>.md`); the §4.11 reports
  themselves belong to step06b, outside Link 2's scope.

**Verdict: Link 2 GREEN end-to-end on production — fresh ADK-0022
enumeration + candidate-scoped '4.0' build for both charts, all gates passed,
published generations byte-identical, authority still '3.0'.**
