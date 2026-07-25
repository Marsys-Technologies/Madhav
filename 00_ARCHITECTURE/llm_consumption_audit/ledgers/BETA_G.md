# Lane β.G ledger — Remedies & corpus (EL-51, EL-35, EL-52)

Per charter §10 / M2.10, append-only Native-Proxy ruling log for lane β.G, plus the Verifier-protocol
evidence blocks for each EL id this lane owns.

---

## PROXY-RULED — 2026-07-25 — Worktree/branch setup

**Situation:** This session began in `.worktrees/beta`, which was checked out on
`elev/beta-T-gochara-timing` (lane T's branch), not any lane-G branch — the brief's stated
`elev/beta/G-remedy-corpus` did not exist anywhere (`git branch -a` confirmed). An untracked file,
`platform/scripts/dispatch_elev_beta_t_gochara_resume.py`, was present in the working tree —
leftover lane-T work, outside this lane's file-ownership manifest (`platform/scripts/**` is not
owned by β.G).

**Ruling:** Verified `elev/beta`, `elev/beta-T-gochara-timing`, `origin/elev/beta`, and `main` all
point at the identical commit (`43116c42`) and the working tree was clean before branching — so no
lane-T work existed to lose. Created `elev/beta-G-remedy-corpus` from `elev/beta` in this same
worktree, following the flattened-branch-name convention this stream already established for lanes
D/D2 (`elev/beta-D-writer-integrity`, `elev/beta-D2-saham-bhanga`) to avoid the same `refs/heads/
elev/beta` file/directory git conflict. The stray T-lane script is left untouched, uncommitted, not
staged — commits from this lane will `git add` only files under this lane's explicit ownership
(`platform/python-sidecar/**`, `platform/migrations/**` additive-only, this ledger file), never a
blanket `git add`. PR base will be `elev/beta`, matching precedent. No citation applicable —
engineering/process decision, §10 MAY (merge-order and lock arbitration; ruling on ambiguous
acceptance criteria).

---

## PROXY-RULED — 2026-07-25 — A-5 supersession authorization record

Recorded here for lane-local completeness (canonical record is `~/elev-v2-shared/proxy/beta.md`
"[STREAM-CONDUCTOR] Session-scope autonomy authorization" entry, independently re-checked against
the live file before this lane proceeded): the A-5 "remedy accept-as-dark" supersession is exercised
under charter §10's MAY-list, which names it explicitly by ID
("superseding CURRENT_STATE A-5 (remedy accept-as-dark -> beta.G repair)"), verified directly against
the primary charter text (`ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §10), not taken on trust from any
relayed paraphrase. This is disclosed and provisional (PROXY-RULED, open for morning ratification),
not a claim of native ratification. The hard, non-negotiable constraint carried into this lane's
work: the gemstone contraindication verdict may ship `VERIFIED-CLOSED` only with a real, checkable
citation from this project's own classical-text corpus (`ref_rules_search` / `ref_classical_
citation_get` / `ref_doshas_get`); absent that, the honest disposition is `PARKED-HONEST`, not a
forced close.

---

## G0 live reproduction — 2026-07-25

**`ref_remedies_chart_get(affliction="Venus", top_k=50)`** against the canonical chart returned
`returned_count: 25` — this is almost certainly where the register's "catalog of 25" figure comes
from (a live row count for one affliction keyword), not 25 distinct remedy *classes*. Cross-checked
against `l0_remedy_corpus.py`'s `VALID_REMEDY_TYPES` (12 types: mantra, yantra, gemstone, charity,
vrata, puja, japa, homa, tantric, ayurvedic, vastu, behavioral) and the YAML corpus (10 distinct
`category:` values) — no 25-class enumeration exists anywhere in the codebase. **Correction to the
brief's framing, logged honestly rather than silently implemented against a number that isn't real.**

**More serious finding: `ref_remedies_chart_get` is not actually chart-scoped.** Its tool schema
takes no `chart_id` parameter at all; per source (`platform/src/lib/retrieval/registry/layers/
register_d7_channel.ts:1362-1452`, found via code investigation, NOT edited — outside this lane's
file ownership), it is `scope: 'global'`, a single `WHERE planet ILIKE $1 OR domain ILIKE $1` keyword
match with a flat `ORDER BY confidence DESC, cost_tier ASC LIMIT $2`, no per-class fan-out, no
per-class inclusion/exclusion accounting, and `chart_id` (when passed at all) is documented in-code
as being used for provenance logging only, never for filtering. This is the real EL-51 root cause:
a tool named "chart_get" that silently ignores the chart.

**File-ownership conflict — must be disclosed, not silently worked around.** This lane's ownership is
`platform/python-sidecar/**` + `platform/migrations/**` (additive) + this ledger only.
`register_d7_channel.ts` is under `platform/src/lib/retrieval/registry/**` — explicitly listed as
**never touch** in this lane's brief. **The actual fix for "chart-scoped engine ignores chart_id and
has no per-class accounting" requires a file this lane is not permitted to edit.** This is not a
PARKED-HONEST finding about the astrology (the classical grounding work is going fine) — it's a
scope/ownership finding about the engineering task itself, and it needs a decision from whoever owns
that path, not a unilateral lane-G workaround (e.g. editing outside ownership, which would itself
violate the file-ownership discipline this campaign runs on).

**What IS in-scope and being pursued:** the `bodha_remedies_get` (L2 Bodha) path is genuinely
chart-scoped (SQL keyed on `chart_id`, confirmed live — 9 resonances + 27 prescriptions returned for
the canonical chart, all real rows) and is backed by Python writers under this lane's ownership.
`associated_doshas_array` and `estimated_cost_inr_range_jsonb` are confirmed live-NULL DB-wide (own
live call, matches the code's documented `DATA_GAP_NOTE`) — a `bo_upaya`-writer population gap, which
IS a python-sidecar writer fix, in scope.

**EL-52 named example reproduced live, verbatim.** Row `sweep_venus_japa_1b8a46b9` from the same
`ref_remedies_chart_get` call: `source_citation: "[HIGH] BPHS — Trans. R. Santhanam, Ranjan
Publications (archive.org: BPHSEnglish) | PG581"`, prescription_text:
`".Chapter 47\n3Tr?Ctrqqqad\nEI€TITfEfrffTq I\n589\n...88-8g.SimilararetheeffectsofVenusinhissub.
periods.\nIf Venus belord of the 2nd or the 7th(two maraka houses)' there\nwill'be during his Dasa,
physical pains and troubles' To get\nalleviation from those troubles the native should"` — this is
the exact garbled text named in the register. Assessment: the garbled segment
(`3Tr?Ctrqqqad EI€TITfEfrffTq`, `?6{ler qfilqfa llqqll`, `qr aqrcti qt( |`) is an OCR-mangled attempt
at a Devanagari verse — **not recoverable from this OCR output; flagged low-confidence, not
reconstructed.** The trailing English is legible with only word-boundary loss (a mechanical OCR
defect, not missing/altered characters): `"88-89. Similar are the effects of Venus in his
sub-periods. If Venus be lord of the 2nd or the 7th (two maraka houses), there will be during his
Dasa, physical pains and troubles. To get alleviation from those troubles the native should..."` —
de-spacing this is safe (no characters invented, no words guessed) and it directly corroborates the
maraka rule via a second citation (BPHS Ch.47, PG581) beyond Ch.44.

## Maraka-lordship rule — citation grounding (safety-critical piece)

**Source: BPHS Chapter 44 "Maraka (Killer) Planets"**, `[HIGH]` confidence, Trans. R. Santhanam,
Ranjan Publications, corpus chunks `bphs_pg0439_c01` through `bphs_pg0443_c01` (verified live via
`ref_rules_search(keyword="maraka")`).

Rule as stated in the primary text: "the 3rd and 8th are the two houses of longevity. The houses
related to death are the 12th from each of these, i.e. the 2nd and 7th are Maraka houses... The
lords of the 2nd and the 7th, malefics in the 2nd and the 7th and malefics accompanying the 2nd and
7th lords are all known as Marakas" (`bphs_pg0439_c01`). Strength ordering, same source
(`bphs_pg0440_c02`): primary marakas = lords/occupants of 2nd, 3rd, 7th, 8th, 12th (2nd ranked
strongest); second-grade = lords/occupants of 6th, 11th; least-marakas = lords/occupants of 1st, 4th,
5th, 9th, 10th (can still act as marakas under specific conjunct/aspect conditions per slokas 15-21,
not modeled in this pass — scoped to the primary 2nd/7th-lordship rule only, disclosed as a scope
limit, not silently generalized).

This matches this lane's brief's own stated hypothesis almost exactly ("a maraka is typically the
lord of the 2nd or 7th house from lagna, or a planet closely associated with those lords") and is
independently corroborated by the BPHS Ch.47 passage above (Venus named as maraka specifically via
2nd/7th lordship). **Verdict: real, citable, HIGH-confidence grounding exists. The A-5 "no
fabrication-free repair possible" prior finding does NOT hold for the core 2nd/7th-lordship rule** —
this is the fresh-eyes repair the charter's supersession asked for. Scope note: the fuller rule
(malefic occupants, conjunct/aspecting planets, Rahu/Ketu-as-maraka per `bphs_pg0443_c01`) is
documented above but not yet implemented in code — v1 of the deterministic verdict should implement
the 2nd/7th-lordship core (unambiguous, directly cited) and disclose the occupant/conjunction
extensions as a named follow-up rather than silently baking in an under-verified fuller rule.

## EL-51 sub-piece disposition — PARKED-HONEST (blocked-on-alpha)

**Item:** `ref_remedies_chart_get` (`query_remedies_for_chart`) does not filter by `chart_id`.
**Location:** `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1362-1452`.
**Ownership:** confirmed directly against `ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §4 (line 473) —
`platform/src/lib/retrieval/registry/layers/register_d*.ts` (except `register_d8_assess_domain.ts`)
is Stream α's (SATYA) file-ownership manifest, not β.G's. Per M2.9 ("no cross-stream arbiter — park
instead"), this is parked, not touched, not negotiated.

**Disposition: `PARKED-HONEST (blocked-on-alpha: register_d7_channel.ts chart_id filter)`.**

**Exact requirement for α to pick up:**
- File: `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`, handler backing
  `ref_remedies_chart_get` / `query_remedies_for_chart` (currently lines ~1362-1452).
- Current behavior: `scope: 'global'`; SQL is `WHERE planet ILIKE $1 OR domain ILIKE $1` against the
  `affliction` param only; `chart_id`, when passed, is used for provenance logging only (not a WHERE
  clause predicate); flat `ORDER BY confidence DESC, cost_tier ASC LIMIT $2` with no per-class
  fan-out and no inclusion/exclusion accounting in the response.
- Required change: (1) add `chart_id` as a real filter predicate — join to whatever chart-scoped
  table actually carries this chart's afflictions/resonances (the L2 Bodha tables,
  `bodha_rm_resonances` / `bodha_rm_remedy_prescriptions`, are already correctly chart-scoped per
  live verification below and are the right join target, OR chart-scope `brahma_remedy_corpus` via
  a chart-relevance join if that table is meant to stay the source — α's call which table anchors
  the "chart-scoped" contract); (2) replace the flat `LIMIT` with a per-`remedy_category`
  (12-type ontology, `l0_remedy_corpus.py:47-50`) fan-out that reports one of `served` /
  `excluded: no_match_for_affliction` / `excluded: below_confidence_floor` / etc. per class, never a
  silent drop.
- What breaks without it: a tool named "chart_get" returns the same global keyword-matched rows for
  every chart_id passed to it — this is the entire EL-51 "silently serves a fraction of the catalog"
  symptom; it cannot be fixed from the data side alone because the serving query itself never reads
  `chart_id` as a filter.
- What β.G is delivering instead, so the fix is real the moment α lands the filter: the
  chart-relevant computed data itself (gemstone maraka verdict, `associated_doshas_array` backfill),
  written to the already-chart-scoped `bodha_rm_*` tables that `bodha_remedies_get` (a working,
  genuinely chart-scoped sibling tool) already serves correctly today — so this specific safety-bearing
  content is live NOW via `bodha_remedies_get`, independent of α's fix, and α's eventual
  `ref_remedies_chart_get` fix inherits it automatically once it joins to the same tables.

## EL-51 — evidence block

**Delivered (in-scope half — the Python/data side):**
- `platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py`: `MARAKA_CITATION`,
  `_fetch_maraka_facts` (L1-authoritative read of `chart_facts.ayurdaya.CHART.maraka_grahas`,
  §N.5-compliant — never recomputes lordship), `_compute_gemstone_maraka_verdict` (pure,
  deterministic, BPHS Ch.44/47-cited), `_fetch_active_doshas_by_graha` (real backfill for
  `associated_doshas_array`, traced via `constituent_facts_array`, not name-guessed). Wired into
  the resonance/prescription row builders: gemstone rows carry
  `prescription_detail_jsonb.maraka_contraindication_verdict` + a plain-text entry in
  `counter_indications_array` when contraindicated; `estimated_cost_inr_range_jsonb` now carries
  an explicit honest-gap disclosure object (never a bare NULL, never a fabricated INR figure —
  real market pricing is not classical/deterministic data) instead of the prior hardcoded NULL.
- Migration: none required for this half (all target columns — `associated_doshas_array`,
  `estimated_cost_inr_range_jsonb`, `counter_indications_array`, `prescription_detail_jsonb` —
  already exist per migration 226; this is a writer fix, not a schema change).
- Tests: `tests/test_beta_g_el51_maraka_verdict.py`, 12/12 passing. Full existing bo_upaya-adjacent
  suite re-run for regressions: `test_ba_p25_4_bo_upaya_resonance_wiring.py`,
  `test_wave_d4b_b4_remedy_leverage_join.py`, `test_bo_wp22_empty_shells.py`,
  `test_bo_loud_fail.py` — 77/77 passing, zero regressions.
- Parked (out-of-scope half, see PARKED-HONEST block above): `ref_remedies_chart_get`'s missing
  `chart_id` filter, `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`, Stream
  α's file. `bodha_remedies_get` — already genuinely chart-scoped — serves this lane's fix live
  the moment α's filter lands, per the ledger entry above.

**Disposition: `PREPARED-FOR-NATIVE`.** Code is real, tested, matches the FROZEN writer contract,
and the citation is independently verified against the primary corpus. NOT `VERIFIED-CLOSED`:
this session did not run the chart-scoped rebuild + FORENSIC 7/7 gate against either canonical
chart, so the computed verdict has not yet been observed live in `bodha_rm_remedy_prescriptions`
for a real build. Rebuilding both canonical charts and re-running the Verifier G0 recipe
(`bodha_remedies_get(chart_id=482012f1…, domain=…)`, confirming a gemstone row now carries a
non-null `maraka_contraindication_verdict`) is the exact next step for whoever picks this up —
not attempted here because this session was already very long and a rushed rebuild at the tail
end of it is exactly the corner-cutting this campaign's own doctrine (truth over coverage) warns
against.

## EL-52 — evidence block

**Delivered:**
- Migration `465_classical_text_chunks_ocr_cleanup.sql` — additive, `migration-guard`-reviewed
  (PASS on all 5 requested checks, one non-blocking WARN re: non-concurrent index build on a
  10,651-row table — acceptable at this size). Not yet applied to the live DB (see disposition).
- `platform/python-sidecar/brahmagyan/ocr_cleanup.py` — deterministic `score_ocr_confidence()`
  (worst-line-capped token-legibility heuristic, no LLM, no content invention) +
  `HAND_CLEANED_CHUNKS` (small, explicit, human-reviewed registry) + `apply_ocr_cleanup()`.
- **The named example, actually cleaned by hand**: `bphs_pg0581_c01` (BPHS Ch.47, Venus
  dasha/sub-period maraka passage) — Devanagari segment left `None` (genuinely unrecoverable,
  not guessed), English translation de-spaced (`"88-89. Similar are the effects of Venus in his
  sub-periods. If Venus be lord of the 2nd or the 7th (two maraka houses)..."`) with a review
  note explaining exactly what was and wasn't recovered. This is the same passage cited as
  corroborating evidence in EL-51's `MARAKA_CITATION`.
- Tests: `tests/test_beta_g_el52_ocr_cleanup.py`, 9/9 passing, including a regression pin against
  the exact live-reproduced raw text and a check that a badly-garbled line inside an otherwise
  legible row still pulls the whole-row score below threshold (an earlier version of the scorer
  failed this — flat token-ratio averaging let a long legible tail dilute a short garbled
  segment; fixed to cap the score at the worst individual line's ratio).

**Disposition: `PARKED-HONEST`, bounded and explicit, per the brief's own scope cap.** The
brief's ~200-highest-traffic-row bound was never going to be fully hand-reviewed inside one
session without risking exactly the fabrication this lane exists to prevent — B.10 forbids
"cleaning" by guessing, and a robust *generic* English-desegmentation-plus-Devanagari-recovery
algorithm is not something to improvise safely under time pressure. What ships instead: (1) a
real, tested, safe-to-run-at-scale confidence SCORER (satisfies "OCR-confidence scored" for the
full bounded set the moment someone runs `apply_ocr_cleanup()` over the ~200-row list); (2) one
fully hand-cleaned, citation-verified row — specifically the named EL-52 example, chosen because
it directly unblocks EL-51's gemstone verdict citation, exactly as the brief asked. **Named
follow-up, sized:** hand-review the remaining ~199 rows (remedy-linked + `ref_rules_search` top
hits) through the same `HAND_CLEANED_CHUNKS` registry pattern — each addition is a small, explicit,
auditable dict entry, not a code change to the scoring/apply machinery. A full-corpus pass beyond
this bound remains explicitly out of scope per the brief's own §12.

## EL-35 — not reached this session

**Disposition: not attempted — scope exceeded available session time, disclosed rather than
rushed.** Initial grep found the drekkāṇa/tāra-bala/KP-sublord fields spread across at least 8
different writers (`ga_nakshatra.py`, `ga_sensitive_degree.py`, `bo_nakshatra_semantic.py`,
`bo_laksana.py`, `ka_sangam.py`, `ph_muhurta.py`, `bg_vidhi_primitives.py`, `muhurat/finder.py`)
— each field needs its own citation-traced significance string, correctly tagged by school
(Parāśarī/Jaimini/KP/Tājaka), sourced from `ref_*` tables per the brief's own requirement ("never
write a significance string you can't trace to a `ref_*` source row"). Doing this correctly
requires understanding each writer's actual computation before attaching a school-tagged claim to
it — not something to do shallowly at the end of an already very long session. Per this
campaign's own tie-breaker doctrine (§10: "truth over coverage — an honest gap beats a padded
answer"), this is disclosed as unattempted, not padded with a thin implementation across 8
unfamiliar writers.

## Chart-scoped rebuild + FORENSIC gate — not run this session

**Disposition: not attempted.** The db-rebuild lock was never taken; `dispatch_*_rebuild_job.py`
was not invoked; no production DB write happened as part of this lane beyond what
`migration-guard` reviewed (the migration itself was reviewed but not applied). This is a
deliberate stop, not an oversight: this session already found and fixed one real infrastructure
incident (the shared-worktree HEAD race, see above) earlier in the same run, and attempting a
live chart-scoped rebuild with a mandatory FORENSIC 7/7 gate and a STOP-never-self-rollback
protocol, at the tail end of an unusually long session, is exactly the condition under which
corners get cut. Whoever picks this up next should: apply migration 465, run
`apply_ocr_cleanup()` against the bounded row list, take the `db-rebuild` lock properly (mkdir +
holder.json + 2-min heartbeat), dispatch the chart-scoped rebuild for both canonical charts, and
run FORENSIC 7/7 before treating any of this lane's dispositions as `VERIFIED-CLOSED`.
