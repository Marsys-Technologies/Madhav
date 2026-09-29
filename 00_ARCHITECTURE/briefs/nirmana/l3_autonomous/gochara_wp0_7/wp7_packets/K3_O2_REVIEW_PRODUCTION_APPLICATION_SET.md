# K3/O-2 Independent Review — Production Application Set (Gochara WP0-7, Link 3 authority flip)

- Reviewer designation: K3/O-2 (independent; no prior involvement in this lane)
- Date: 2026-09-28
- Branch: `l3/gochara-autonomous-wp0-7` @ `47d6905d5`
- Scope: whether Link 3 (cutover runbook steps 7–10: flip gates, authority flip
  '3.0' → '4.0' for charts `482012f1-710e-4a25-994a-93821f5871aa` and
  `1c826d5a-41cb-4450-b4dc-59d440e5f75a`, soak, disposition) should proceed.
- Method: read of the runbook scripts, the defect-fix code, migration 1091's
  re-pinned integrity contract, the ADHIKARIN register (ADK-0019..0023), and
  the conditioning evidence; direct reproduction of the key suspicion against
  the actual production-written payload (`.run/wp10_tranche2/link2_episodes_482012f1.json`,
  the file step06_candidate_build consumed for the production '4.0' build —
  138,837 rows, matching the verified production contact count). No production
  database access was needed; nothing outside this report was modified.

## VERDICT: BLOCK — two blocking findings

The flip must not proceed until both findings are dispositioned. Finding K3-F1
means the artefact Link 3 would serve — and the ADK-0023 §4 delta reports the
step-7 gate evidence rests on — were computed with 67.9% of the candidate's
contacts silently excluded from the activity function. Finding K3-F2 means the
designed rollback path lands the database in a permanently integrity-RED state.

---

## BLOCKING K3-F1 — step06b drops every kakshya contact: relation-vocabulary key mismatch in `RELATION_TO_PRIMITIVE`

**Files:**

- `platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py:146-155`
  (the map), `:923-926` (the lookup-and-skip), `:1022` (the only disclosure
  channel — a count in the stdout JSON report, retained nowhere in the
  Link 3 evidence package)
- `platform/python-sidecar/tests/l3/gochara/test_step06b_windows_projection.py:224-235`
  (`test_relation_to_primitive_vocabulary` pins the wrong key, so the battery
  locks the defect in instead of catching it)

**Defect.** `RELATION_TO_PRIMITIVE` keys are matched against the ledger's
`relation` string, but the kakshya key is written as `"kakshya_cell"`:

```python
RELATION_TO_PRIMITIVE = {
    "conjunction": "degree_contact",
    ...
    "kakshya_cell": "kakshya_cell_crossing",   # step06b:152 — key is wrong
    ...
}
```

The pinned WP1 §3.1 relation vocabulary — and the value actually stored in
`kala_gochara_contacts.relation` for generation '4.0' — is
`kakshya_cell_crossing` (WP1_CONTRACTS.md §3.1 line 299 and §7 line 650;
`gochara_kernel/contacts.py:41` `BOUNDARY_RELATIONS`; every production payload
row). `RELATION_TO_PRIMITIVE.get("kakshya_cell_crossing")` is therefore `None`,
and the main loop counts and skips:

```python
primitive = RELATION_TO_PRIMITIVE.get(c["relation"])
if primitive is None:
    unmapped_relation += 1
    continue        # step06b:923-926 — excluded from ALL class activity
```

**Reproduction (reviewer's own, no production access):**

```
RELATION_TO_PRIMITIVE keys: [..., 'kakshya_cell', ...]
payload relation -> mapped? {'kakshya_cell_crossing': False, others: True}
unmapped contact count: 94203 of 138837   (67.9%)
```

run against the real module and the real production-written payload
(`.run/wp10_tranche2/link2_episodes_482012f1.json`). Chart 2's payload is built
by the same code path and carries the same vocabulary; per the step06 evidence
its dedupe histogram is kakshya-dominated in the same way (826,893 kakshya rows
dropped at dedupe on chart 1 — kakshya is the largest relation family).

**Impact.** Every '4.0' window row step06b projects — the rows the flip would
serve, and the numbers in both `link2_delta_report_*.md` files — is computed
from an activity function over only ~32% of the contact ledger. The noisy-OR
activity, the component boundaries, the peaks, the per-class mean raw values,
and every Δ-vs-'3.0' cell in the delta reports are materially understated.
ADK-0023 (4) made these delta reports **Link 3 pre-flip evidence at the step-7
gate**; as generated they do not describe the candidate that was actually
built. The failure is invisible end-to-end: enumeration is green, the build is
green, the battery is green (the vocabulary test pins the wrong key), and the
only signal is a `contacts_unmapped_relation: 94203` field in a stdout JSON
report that was not retained in `.run/wp10_tranche2/` and is not mentioned in
`evidence/link3_conditioning_evidence.md` or the delta reports.

**Required before flip:** fix the key to `"kakshya_cell_crossing"` (and correct
the pinning test), re-run step06b on the disposable copy, regenerate both delta
reports, disclose the `contacts_unmapped_*` counts in the step-7 evidence, and
re-present the package — the current step-7 gate evidence does not survive this
correction. If the exclusion were somehow intended, that would be a
ruling-level contract change (WP1 §7 names `kakshya_cell_crossing` a served
relation), not something to leave as a silent map entry.

---

## BLOCKING K3-F2 — the reversal path leaves production permanently integrity-RED (orphan '4.0' windows)

**Files:**

- `platform/python-sidecar/scripts/kala_gochara_cutover/step08_flip.py:78-99`
  (`--reverse` = `ledger.rollback()` + authority UPDATE — nothing else)
- `platform/python-sidecar/services/gochara_kernel/ledger.py:578-608`
  (`rollback()` deletes **coverage and contacts only**; `kala_gochara_windows`
  is "deliberately not touched")
- `platform/migrations/1091_wp10_ka_gochara_registry_repin.sql` — the re-pinned
  `ka_gochara` `integrity_check_sql`, conjuncts (a) and (f)

**Defect.** After `step08_flip.py --reverse`:

1. '4.0' coverage and contacts are deleted; the manifest is `rolled_back`;
   authority reads '3.0'. Serving is safe.
2. But the '4.0' **window rows remain** (step06b's relation is not the ledger's
   to clear, and no step in the runbook deletes them).
3. Migration 1091's conjunct **(a)** then fails: every '4.0' window must be
   covered by a '4.0' coverage partition for the same chart — coverage is gone.
4. Conjunct **(f)** also fails: '4.0' windows may exist only behind a
   `candidate`/`published` manifest — the manifest is `rolled_back`.

So the designed, pre-authorized abort path (soak checklist triggers 1–5 →
"execute `step08_flip.py --reverse` immediately") lands the asset's own
integrity contract **RED, permanently**, with no documented cleanup: the
checklist's reversal section (`step09_soak_checklist.md:30-35`) names only the
flip script; `ledger.rollback`'s C-1 order explicitly excludes the windows
table; and no step00–step10 artifact deletes '4.0' windows on reversal. The
post-reversal state is then indistinguishable from corruption by the platform's
own detector — the same detector soak-trigger 1 watches — and any future '4.1'
attempt inherits the RED until someone hand-deletes the orphan rows. (The
generation guard in `step03_guard_n6a.sql` permits deleting '4.0' rows, so
cleanup is physically possible — it is simply nowhere in the reversal design,
and the step-7 gate-4 "rollback-through-adapters" rehearsal exercises a scratch
candidate on contacts/coverage only, so it cannot see this.)

**Required before flip:** extend the reversal (step08 `--reverse` or the
checklist's reversal procedure) to delete '4.0' windows for the chart in the
same transaction, and add a post-reversal integrity evaluation to the recorded
reversal evidence. Also rehearse `--reverse` end-to-end (flip → reverse on a
disposable copy with windows present) and record the post-reversal conjunct
state.

---

## Non-blocking observations

1. **Dedupe survival determinism is sound — verified by construction, not just
   claimed.** At the `deeper_tie` tier (100% of real groups) the surviving row's
   non-survival fields are required identical (residual refusal, exit 5),
   `target_ref` is equal by tier definition, and `classical_citation` is nulled
   (ADK-0022) — so the persisted row is invariant to the `json.dumps`
   tie-break pick. The null-and-disclose amendment converts the earlier
   arbitrary-citation survival into an honest null with full recoverability in
   `.dropped_refs.json`. No silent data-quality regression for ledger consumers;
   consumers of `classical_citation` see NULL on 46,353/46,354 groups, which is
   the ruled, disclosed behaviour.
2. **step06b natural-key dedupe (412d99d0c) is deterministic** (first in a
   fixed insert order: era→month→day, class-sorted; children re-pointed). Two
   nits: the skip is disclosed on stderr only, and the run report's
   `windows_by_tier` counts pre-dedupe rows while `windows_written` is
   post-dedupe — reconcile these in the report so the step-7 evidence shows the
   collapse count. (`step06b_windows_projection.py:640-672`, `:1026-1028`)
3. **Integrity conjunct (i) is structurally blind to step06b's row shape.**
   Conjunct (i) checks `active_sentences` elements with a `contact_id` KEY;
   step06b stores bare contact-id strings (`_window_row`,
   `step06b_windows_projection.py:488`), so `s ? 'contact_id'` never binds and
   the conjunct passes vacuously for '4.0' rows. The soak's "integrity green"
   therefore proves nothing about sentence-reference integrity. Either shape
   the rows to the conjunct or re-scope the conjunct; at minimum disclose the
   vacuity in the soak evidence.
4. **Half-flip state is unaddressed.** `step08_flip.py` is per-chart; if chart
   1 flips and chart 2's flip fails (or its step-7 gate is RED), the two
   charts serve different generations with no documented rule. The reversal is
   per-chart and pre-authorized, so recovery exists — write the rule down
   (flip order + what to do when the second chart cannot follow).
5. **`--reverse` burns the '4.0' label.** `rollback()` marks the manifest
   `rolled_back`, and `publish_candidate` refuses `rolled_back` — a re-attempt
   after any reversal must use a new generation label ('4.1') and will inherit
   K3-F2's orphan windows until that finding is fixed. This is by design per
   plan §4.7 but should be stated in the soak checklist's reversal section.
6. **Conditioning claim (b) verified against code:** step06b's
   `jd_of`/`date_of_jd` (`step06b_windows_projection.py:119,183-192`) and the
   '3.0' writer's `_jd_to_date`
   (`pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:1515-1524`)
   use the identical `int(jd − 2440588.0)` convention. The 9-instant numeric
   proof in `link3_conditioning_evidence.md` is consistent with the code.
7. **Era-slice honest-degradation (condition (c)) is real:** the facet, both
   disclosure strings, and the deliberate non-write of `era_slice_key`
   (migration 1091 conjunct (g)) are mutually consistent
   (`register_gochara_windows.ts:1630-1708`, `step06b:157-163`). The 5/5 vitest
   and clean `tsc` claims were not re-run by this reviewer but the code matches
   the description.
8. **step06b's stdout run report (with `contacts_unmapped_relation`,
   `skipped_dupes`, per-class reports) was not retained** for the
   delta-report runs — only the `--delta-report-out` files survive in
   `.run/wp10_tranche2/`. Retain the JSON; K3-F1 would have been visible there.

## What was checked and found supported

- Flip preconditions in `step08_flip.py:101-140` genuinely refuse a
  flip-over-void (manifest/candidate, coverage>0, contacts, windows>0) and the
  manifest is published via `ledger.publish()` (recomputed digest/row_counts),
  never hand-stamped. Guard posture (1091 conjuncts, generation guard,
  convention immutability) is real and current per the Link-2 post-run record.
- The soak checklist now carries pre-written abort triggers and a 24h minimum
  (condition (a)) — adequate in form; its reversal step is the part broken by
  K3-F2.
- The `_refine_root` patch (`contacts.py:159-201`) is branch-cut-safe by
  construction (≤90° travel cap; `swiss_bisect`'s internal ±25%-span widen adds
  at most ~45° more, still under 180°) and fails loudly rather than degrading.
- Rollback anchor: pre-run dump exists
  (`.run/wp10_tranche2/pre_run_dump_20260927.dump`, sha256 recorded in
  step06_evidence.md) — restore-drilled per step02 evidence (not re-drilled by
  this reviewer).

## What would unblock

1. K3-F1: fix the `RELATION_TO_PRIMITIVE` key + pinning test, rebuild the
   projection on the disposable copy, regenerate both delta reports, disclose
   unmapped counts, and re-present step-7 evidence.
2. K3-F2: make reversal delete '4.0' windows transactionally, add the
   post-reversal integrity evaluation to the checklist, and rehearse
   flip→reverse with windows present.
3. Observation 3 (conjunct (i) vacuity) dispositioned — fix or disclose.

— K3/O-2, 2026-09-28

---

# K3/O-2 RE-REVIEW (2026-09-28, HEAD `db03a2927`) — remediation of the BLOCK above + the E-020 fix chain

Scope of this pass: commits `419aca944` (K3-F1), `9ef81897c` (K3-F2),
`3c7bf6947` (E-020 date convention + conjunct-(d) skip), `1fc8fd2d7`
(migration 1150), `007853c2c`/`db03a2927` (wording + apply evidence), the
updated runbook/checklist text, and the retained run artifacts. The original
BLOCK section above stands as written; this section decides whether it lifts.

## RE-REVIEW VERDICT: NO BLOCKING FINDINGS — the block lifts

Both original findings are genuinely closed, the E-020 chain is a data fix
plus a detector correctness fix (not a relaxation), and nothing in the
remediation introduces a new hole that I would block on. Conditions and
observations below.

## K3-F1 — CLOSED, verified against code and data

- The key is now `"kakshya_cell_crossing"` and the pinning test
  (`test_step06b_windows_projection.py:229-245`) regression-asserts that all
  eight enumerator relations are map keys — the test now catches the defect
  class instead of locking it in.
- The stderr WARNING on non-zero `contacts_unmapped_*` and the retained run
  reports close the visibility hole that made the original defect silent.
- I re-ran my reproduction: `contacts_unmapped_relation = 0` in the retained
  run report (`.run/wp10_tranche2/link3_step06b_runreport_482012f1.json`;
  138,837 read, 4,415 written, 0 collapsed dupes), and the shift ledgers and
  zero-length stderr files exist as claimed.
- I independently verified the "amplitude-neutral" claim the commit message
  makes: all 94,203 kakshya contacts in the real payload are zero-width
  instants (`t_in == t_exact == t_out`), inert under
  `linear_no_box_decay` (every t satisfies `t<=t_in or t>=t_out`). The only
  non-zero-width boundary rows in the payload (two Venus sign_ingress rows)
  have `t_out == t_in < t_exact` and are likewise inert. The fix changes the
  breakpoint set, not λ values — the small window-count deltas (4,417→4,415 /
  3,955→3,947) are explained by the date shifts moving rows across dedupe
  keys, consistent with the evidence.

## K3-F2 — CLOSED, verified against code

- `ledger.clear_windows_on_reversal()` carries the triple guard (v1/'3.0'
  untouchable; manifest must be candidate/rolled_back; refuses while the
  generation is the served authority) and `step08_flip.py --reverse` now runs
  authority→'3.0' → rollback → windows cleanup in ONE transaction — a failure
  anywhere rolls the whole reversal back, so no half-reversed state.
- Post-reversal the integrity contract reads GREEN again by construction:
  zero '4.0' rows remain, so conjuncts (a)/(f) have nothing to bind; conjunct
  (k) is out of scope once authority is '3.0'. The test extension
  (`test_step08_flip_and_reverse` + `test_clear_windows_on_reversal_refusals`)
  covers the refusals, the cleanup, the post-reversal integrity GREEN, and
  the burned-label refusal (exit 8).
- The reversal drill (flip → reverse on the disposable production copy,
  4,417 windows deleted, v1/'3.0' untouched) and the updated checklist text
  (3-step reverse, burned-label, half-flip rule, conjunct-(i) vacuity note —
  `step09_soak_checklist.md:57-108`) close every sub-item of my original
  finding and observations 4–5.
- Disclosed residual (accepted, not blocking): a reversal after step 9 leaves
  Kṣetra's `(generation, id)` provenance edges dangling at deleted '4.0' rows.
  The docstring now states this. The native should be aware the earlier
  "rows still exist but are no longer served" framing is superseded — the
  rows are now deleted.

## E-020 chain — scrutinized, no new blocking risk

- **Date-convention fix** (`JD_UNIX_EPOCH = 2440587.5`, `date_of_jd` a true
  inverse of `jd_of` via `fromtimestamp(..., tz=UTC)`): correct. I reproduced
  the gate-(b) claim independently over the real payload (138,837 contacts ×
  3 instants = 416,511 conversions): shift distribution is exactly {0, +1},
  and every +1 shift falls in UTC hours 0–11 — matching the claimed
  00:00–11:59 UTC / 05:30–17:29 IST scope and the corrected disclosure
  wording. The contact-level figures in the evidence (0: 137,464 / +1:
  140,209 over both charts' t_exact) are consistent with my per-instant
  reproduction.
- **Conjunct-(d) outside-era skip**: the skip is bounded, counted
  (`peaks_refined_outside_era`: 2 / 5), and disclosed; era rows are unaffected,
  so no window coverage is lost — only month/day granularity rows for 7 peaks,
  each of which the adjacent component represents. Not a silent activity
  omission. The claim that the defect predates E-020 (convention-independent)
  is credible from the mechanism (±7-day refine argmax vs era clipping).
- **`legacy_semantics.py:1331,1342` second copy**: I checked the consumer
  question explicitly — the only production writer of hierarchies,
  `ka_gochara_v3_century_materialize.py:345`, imports
  `build_resolution_hierarchy` from `services.gochara_v3.resolution_hierarchy`,
  NOT from `legacy_semantics`; no non-test code consumes the changed copy
  (step06b merely mirrors it). No served-path behavior change. Non-blocking
  observation R1 below.
- **Migration 1150 is exactly a detector correctness fix.** I compared old vs
  new conjunct-(e) semantics: under a UTC session the two forms accept/reject
  identically (half-open horizon: `date(lower)` inside, `date(upper)` the
  tolerated boundary day under both; anything strictly outside RED under
  both). The new form only removes the session-TimeZone dependence
  (Asia/Kolkata false-positives) — nothing that was RED in a UTC session
  becomes GREEN. All other conjuncts byte-identical; the DO gate-probe pins
  that. Production apply evidence (ledger row id 885, triple match,
  dual-timezone GREEN, dry-run pending set unchanged) is internally
  consistent.

## Verification I ran myself (this pass)

- Payload census + module-level reproduction of the kakshya mapping
  (unmapped 94,203 → 0 after the fix; zero-width inertness proof).
- Old-vs-new date-convention shift histogram over all 416,511 chart-1
  contact instants (exactly {0,+1}, +1 confined to UTC hours 0–11).
- `pytest tests/l3/gochara/test_step06b_windows_projection.py -q` at HEAD:
  **12 passed, 4 skipped** (the 4 skips are the disposable-DB tests, DBs not
  running here). The DB-backed battery (381 passed claim) was not re-run by
  this reviewer — no disposable containers were up; I note this honestly.
- Old-vs-new conjunct-(e) equivalence reasoning (above); I did not query
  production — nothing in this pass required it.

## Non-blocking observations carried forward / new

1. (R1) `legacy_semantics.py` documents itself as a *faithful reproduction*
   of the served-path functions; the E-020 edit makes
   `build_resolution_hierarchy` intentionally diverge from
   `resolution_hierarchy.py`'s noon anchor with only an inline comment. No
   served-path consumer exists today, but a future consumer reading the
   module header's "reproduced faithfully" promise would inherit the
   corrected bucketing silently. Name the divergence in the module docstring.
2. Conjunct (i) remains vacuous for step06b's bare-string `active_sentences`
   — now disclosed in the soak checklist; a real fix (row shape or conjunct
   re-scope) belongs to a later lane. Carried, non-blocking.
3. The two non-zero-width Venus sign_ingress payload rows with
   `t_out == t_in < t_exact` (35 µs) look like an enumeration edge case
   (zero-width span with the exact 35 µs past the edge). Inert under M-1 and
   immaterial to the flip, but worth a ticket for the kernel lane.
4. Kṣetra dangling-edge consequence of the new reversal cleanup is disclosed
   but should be echoed into the K-1 packet notes so a post-soak reversal
   doesn't surprise that consumer.

## What would make me block again

Nothing outstanding. The flip may proceed through steps 7–10 under the stated
gates: step06b production write of the corrected projection, step-7 gates with
the regenerated delta reports attached, the per-chart flip with the 24h soak
and pre-authorized reversal (now integrity-clean), and the step-9 birth-epoch
gate on chart 2.

— K3/O-2, re-review 2026-09-28 (HEAD db03a2927)
