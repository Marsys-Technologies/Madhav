# Step 9 — Soak checklist + second-chart birth-epoch fixture (#2534 class)

Runbook: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9 step 9.
Sheet: A-3 (tranche 2, `PRODUCTION_TRANCHE_2_AUTHORIZED`).

## Soak checklist (production, after step 8)

- [ ] Soak window declared in the evidence header (start/end timestamps) before
      it begins; **minimum soak duration is 24 hours** — the declared window
      must span at least 24 h and the declared minimum is recorded in the
      header itself.

## Abort triggers (Link 3 native condition (a)) — IMMEDIATE reversal

If **any** of the following holds at any of the three integrity evaluations
(soak start, midpoint, end) **or at any time in between**, execute
`step08_flip.py --reverse` **immediately**, without waiting for the soak to
complete and without further authorization:

1. Any integrity conjunct (a)–(k) of `ka_gochara` `integrity_check_sql` is
   RED at any evaluation.
2. Cockpit count ≠ `count_sql` (any drift between display and relation).
3. Any guard-trigger refusal occurs that is **not** on the
   expected-protection list.
4. Either chart has a `'4.0'` window with `window_start` before its own
   birth date (#2534 class, production detector).
5. The §3 F-02 walkthroughs (ordinary quarter; marriage 2013) show episodes
   without contacts.

Reversal procedure: run `step08_flip.py --reverse`, **record** the reversal in
`evidence/step09_evidence.md` (trigger observed, timestamps, query
outputs/screenshots, reversal command + exit code, post-reversal authority
state, **post-reversal integrity evaluation** — conjuncts (a) and (f) must be
GREEN again once the orphan windows are gone), then **escalate** to the
native. Reversal under these triggers needs no further authorization; it is
pre-authorized by Link 3 condition (a).

What `--reverse` does now (K3-F2 / ADK-0024 §2), in one transaction:

1. Authority is re-pointed to `'3.0'` **first**.
2. `ledger.rollback()` marks the manifest `rolled_back` and deletes the
   generation's coverage + contacts.
3. `ledger.clear_windows_on_reversal()` scoped-deletes the reversed chart's
   `'4.0'` rows from `kala_gochara_windows` (the explicit
   `EXPLICIT_CLEAR_OPS['ka_gochara']` windows op). Guard: the cleanup
   **refuses** unless the manifest is `candidate`/`rolled_back` AND the
   generation is no longer the served authority — authority reversed first,
   windows cleanup second. `'v1'`/`'3.0'` rows are untouchable on this path.
   Without step 3 the orphan windows leave conjuncts (a)/(f) permanently RED
   (coverage gone; manifest no longer candidate/published).

**Burned label:** a `rolled_back` manifest refuses re-publication — a
re-attempt after ANY reversal builds under a **new** generation label
(`'4.1'`), never a rebuild under `'4.0'`.

**Half-flip rule:** flips are per-chart with no cross-chart atomicity. If
chart 1 flips and chart 2's flip fails (or its step-7 gate is RED), the two
charts serve different generations; a failed chart-2 flip does NOT
automatically roll back chart-1, and operators must not assume it does —
chart-1 reversal is a separate, deliberate `--reverse` decision under the
abort triggers above.

**Conjunct-(i) vacuity (record-only, routed to the native by ADK-0024 §4):**
migration 1091's conjunct (i) checks `active_sentences` elements for a
`contact_id` KEY; step06b stores bare contact-id strings, so the conjunct
passes VACUOUSLY for `'4.0'` rows. The step-8/step-9 evidence must NOTE this:
"integrity green" is not earned on sentence-reference integrity by an empty
check.
- [ ] Walkthroughs §3 F-02 re-run: ordinary quarter and marriage 2013 show
      episodes with contacts and coverage (step 8's gate, re-run under soak
      traffic).
- [ ] Integrity contract green throughout the soak (`ka_gochara`
      `integrity_check_sql` — conjuncts (a)–(k) — evaluated at soak start,
      midpoint, end; all three results recorded).
- [ ] Cockpit count equals `count_sql` throughout (no drift between display
      and relation).
- [ ] No guard-trigger refusals in the logs other than expected
      protection rejections.
- [ ] Kṣetra's next build reads '4.0' rows (K-1 pins edges by
      `(generation, id)`); Saṅgam consumes `find_episodes` (V-1/S-2).

## Second-chart fixture — birth-epoch defect class (#2534)

The century writer's known-RED defect (#2534): a hardcoded native birth epoch
used for ALL charts. The second chart (`1c826d5a`, Abhinandan) is built with
birth from `ctx.config['birth_params']` — never a shared constant.

Fixture assertion (synthetic rehearsal form, exercised in
`tests/l3/gochara/test_wp10_cutover.py`): a synthetic chart born 1985-03-02
produces **no window before its own birth** — the detector the proof matrix
(§10 Revision row) names for this defect class.

Production form: build `1c826d5a` per step 6 with the same flags; gate =
integrity green on both charts AND zero `'4.0'` windows with
`window_start < birth date` for either chart.

## Reversal

As step 8: authority re-pointed to '3.0' FIRST, manifest `rolled_back`, then
the reversed chart's `'4.0'` windows scoped-deleted by
`ledger.clear_windows_on_reversal()` (guard: refuses unless the manifest is
`candidate`/`rolled_back` AND the generation is no longer the served
authority; `'v1'`/`'3.0'` untouchable). The manifest label is burned — a
re-attempt builds under a NEW generation label. Record the post-reversal
integrity evaluation (conjuncts (a)/(f) GREEN again) in the evidence, and
note conjunct (i)'s vacuity for step06b's bare-string `active_sentences`
(gate not earned on an empty check). Flips are per-chart: a failed chart-2
flip does not roll back chart-1.

## Evidence

`evidence/step09_evidence.md` — soak window, the three integrity evaluations,
walkthrough outcomes, second-chart build report, and the birth-epoch assertion
result.
