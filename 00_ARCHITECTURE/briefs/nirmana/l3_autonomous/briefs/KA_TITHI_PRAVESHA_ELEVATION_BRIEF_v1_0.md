---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_TITHI_PRAVESHA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_TITHI_PRAVESHA_v1_0.md, 25 findings); v1.1 disposes each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_tithi_pravesha", "SC-1 (tz-aware instants — on the row AND on the serving path, which strips the offset)", "D-M second L0 lane (source adjudication — which must adjudicate the w27b registry's contrary citation string too)", "SC-6 voice (annual frame)", "Gochara w27b: a registered candidate whose modifier schedule is the operand class Q2 bars before M-4"]
goal_objective: "Make ka_tithi_pravesha's stored return instants say what they are: the cast is computed at the CORRECT absolute instant (local jd + Place(tz), the FORENSIC-verified L1 pattern), so the lagna, graha positions and audit are right — it is only window_start/window_end that are handed naive to a timestamptz column and therefore ASSERT an instant 5.5 h late. Fix the assertion without disturbing the cast; stamp the method unsourced-with-receipt until the L0 lane adjudicates it; type the rows as one root's annual testimony; and decide the integrator use as a concurrence voice rather than a λ-product modifier."
source_revision: "9feac52d7 (l3/kala-layer-briefs); `git diff --stat 9feac52d7 e82dd34a3` on services/ka_tithi_pravesha/, query_tithi_pravesha.ts and kala_views/now.ts is empty"
accepted_upstream_contract: "L1 chart_facts MOON longitude_sidereal by fact_id (§N.5); birth_params via ctx.config (§N.2) — VERIFIED naive local wall-clock (pipeline/orchestrator/birth_params.py:96-106) with the offset travelling separately as tz_offset_hours (:97-101,:109, required by _REQUIRED :33), so raw[:19] discards nothing on any orchestrator-built input; the writer's prepare-before-DELETE block landed in fa9857f00 (#2607), not 47131772b"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_TITHI_PRAVESHA_v1_0.md (REWORK); re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_tithi_pravesha/{writer,logic}.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_tithi_pravesha.py", "platform/python-sidecar/tests/l3/test_ka_tithi_pravesha_writer.py, tests/l3/test_w2_first_frontier_writer_preservation.py (the assertions that must flip — §5)", "one additive migration on kala_tithi_pravesha (qualification columns)", "platform/src/generated/nirmana-writer-digests.json (REGENERATED, not hand-edited — consumed by dispatch_frozen_rebuild.py:29,58,113; the writer's code digest changes)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_tithi_pravesha.ts:70 (`as_of` default), :83-90 (to_char STRIPS the offset — the serving half of the defect) and :90 (a bare date cast at session tz) — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/now.ts:613-660 — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["chart_facts / ga_* (L1)", "pyjhora_adapter / panchang_engine (shared engines)", "classical_text_chunks (L0 corpus — the source adjudication is the L0 lane's, D-M)", "services/gochara_v3/** (w27b is Gochara-owned)", "platform-mcp/src/tools/kala_views/**", "platform/supabase/migrations/531_kala_tithi_pravesha.sql, platform/migrations/670_* (applied)", "applied migrations 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; a t0 freeze exists and is inadmissible under t3"
wave: "W2"
shape: single asset, rows (chart × ayanāṃśa × praveśa year)
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R] (including
  a trace of the timezone convention down to PyJHora's own `jd_utc = jd - place.timezone/24`);
  context §4 (5.5 h measured in production), Lane D §13, T1, elevation plan Q2, D-M [A]; no database
  query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions (25 findings) — F-01 the impact was mis-stated: the cast IS computed at the correct absolute instant (the writer passes the naive wall clock together with tz_offset_hours, the same local-jd + Place(tz) pattern the FORENSIC-verified L1 path uses; PyJHora then does jd_utc = jd − tz/24), so pravesha_lagna, graha_positions_jsonb, ephemeris_audit_jsonb and natal_moon_longitude_deg are CORRECT — only window_start/window_end assert an instant 5.5 h late; the rebuild's equivalence contract is now the exact inverse of what v1.0 claimed; F-02 and F-03 two proof rows would fail a CORRECT implementation (a tz relabel does not move the nearest return; 23:55 IST is the same UTC day) — both replaced; F-04 the Delivery sentinel was a constant default; F-05 a registered candidate consumer (w27b_tithi_pravesha) was omitted, and its yaml asserts a classical citation the writer's own constant denies; F-06 Q09 overclaimed (one hardcoded convention); F-07 coverage not in the B5 shape; F-08 the Positive fixture was not the production input shape; F-09–F-25 the ~3° figure, the commit, the duplication detector, the missing baseline, the JSONB-order control, the eleventh row and two columns, B4's shape, the template's §2.1/§2.5/§2.6, the SERVING half of the tz defect, the migration number, the in-scope 'lahiri' literal, 'can' vs 'does', the unreceipted absence claim, the unresolvable Gochara citation, migration 670's existing conjuncts and its blind spot, the tests that must flip, and the writer-digest regeneration."
  - "1.0 (2026-09-24): first issue."
---

# `ka_tithi_pravesha` elevation brief — an annual clock whose instants must be instants

## §0 — The recommendation, in one paragraph

`ka_tithi_pravesha` casts the lunar-return annual chart: it roots the transiting Moon's return to
the natal sidereal longitude (read by `fact_id` from L1, never restated, `:72-77`) nearest each
solar anniversary and verifies the result two ways (`writer.py:201-211` [V]) — numerically the most
careful row-producer in the frontier. The reviewer corrected my account of what is broken, and the
correction inverts the repair's equivalence contract. **The cast is right.** `_moon_longitude`
builds `jd` from the naive wall clock and passes `tz=float(bp["tz_offset_hours"])` (`:130-146`), and
`_annual_chart` passes `birth_params` with the naive `instant.isoformat()` (`:149-156`) — the
identical local-jd + `Place(tz)` pattern the FORENSIC-verified L1 path uses
(`pyjhora_adapter/compute.py:30-33,:58-66`), which PyJHora resolves as
`jd_utc = jd − place.timezone/24` (`drik.py:1773`) [R]. So `pravesha_lagna_*`,
`graha_positions_jsonb`, `ephemeris_audit_jsonb` and `natal_moon_longitude_deg` are **computed at
the correct absolute instant**, and the writer's own test confirms the year-1 return lands within
600 s of the birth instant (`test_ka_tithi_pravesha_writer.py:189-196` [R]). What is wrong is
narrower and still real: the naive `instant` is handed to a **`timestamptz`** column (`:81-98`; DDL
`531:49-50`), so **`window_start`/`window_end` assert a moment 5.5 h late** (context §4 [A]) while
everything computed from it is right. A downstream that **re-casts** from the served instant would
be wrong — that is the live hazard, and it is compounded on the serving path, where
`query_tithi_pravesha.ts:83-90` renders the timestamp with `to_char(… 'YYYY-MM-DD"T"HH24:MI:SS')`,
**stripping the offset** [R]. Second: the method is stamped with an **unreceipted absence claim** —
`CLASSICAL_SOURCE_CITATION = "not_in_corpus: …"` (`:60-70`) asserts the corpus lacks the technique,
and no `count(*)` receipt exists for that claim (nor for my own v1.0 assertion that none was ever
run). Recommendation: **`ENRICH_CORRECT` + `QUALIFY_LIMIT`** — attach `tz_offset_hours` to the wall
clock and store UTC, with an equivalence contract that **pins the cast byte-identical** and moves
only the two bounds; fix the serving render too; `source_qualification='unsourced'` with a real
receipt, upgradeable only by the D-M lane — which must also adjudicate the contrary citation string
a Gochara registry already asserts; per-row `completeness_state`; one declared root; and the
integrator use decided as a **concurrence voice**, not the λ-product modifier a registered candidate
currently proposes. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (`REGISTER:146`) | annual praveśa frame | — |
| Strategy §6.1 **L3-A09** (`:279`) | the asset's row | unchanged |
| Strategy §3 *Clock interval* (`:91`); **L3-Q09 (`:70`)** | annual/return adapters; Q09's proof is *"Recompute declared variants; match the same propositions and boundary changes"* | **Q09 cannot be served** — one hardcoded convention (F-06) |
| **`birth_params.py:33,:96-106,:109`** [R] | `datetime_iso` = `datetime.combine(birth_date, birth_time).isoformat()` — **naive, never carries an offset**; the offset is `tz_offset_hours`, required by `_REQUIRED` | `raw[:19]` **discards nothing** on any orchestrator input; the primary repair is "attach the offset", not "stop discarding it" (F-08) |
| **`pyjhora_adapter/compute.py:30-33,:58-66`; PyJHora `drik.py:1773`** [R] | strips tzinfo, uses `tz_offset_hours`, `jd_utc = jd − place.timezone/24` | the cast is at the **correct** absolute instant (F-01) |
| **Migration 670 (`:1413-1515`)** [R] | already enforces: (a) tiling + root-find consistency, (b) the verification status re-derived, (c) the two convergence booleans as restatements, (d) the L1 root-find target, (e) one natal anchor, (f) a real cast (≥ N grahas), (g) the lagna label restates `reference_signs` and its degree lies in the sign, (h) contiguity, (i) a 338–393 d band | a strong contract — **and (b) re-derives from the same naive-computed audit, so it cannot detect the tz assertion error**: it is the only live detector and it is blind here |
| **`w27b_tithi_pravesha`** (`gochara_v3/mechanisms/w27_annual_stack.py:74,:306-372`; `mechanisms/registry/w27b_tithi_pravesha.yaml`; `mechanism_register.yaml:215-223`; `grammar_v3_registry.yaml:212-214`) [R] | a **registered candidate** (`admission_state: candidate`) whose `data_source` names `ClassContext.tithi_pravesha_rows (from kala_tithi_pravesha…)`, whose `modifier_schedule` is `favourable 1.25 / adverse 0.80`, and whose **`citation_status: cited`** names *"Kṛṣṇa Miśra / Tājaka tradition … Sudarśana Cakra Paddhati"* | three things at once (F-05): nothing populates `tithi_pravesha_rows` (`context.py:114` has no such field) so it is **not live**; its modifier schedule is exactly the λ-product operand class blueprint **Q2 bars before an M-4 audit**; and its citation string **contradicts** this writer's `not_in_corpus` constant — a repository disagreement the D-M lane must adjudicate, not only the writer's absence claim |
| `KALA_DELEGATED_DECISIONS` D-M (`:411-417`) | a second L0 lane pass | the upgrade path for the stamp |
| Elevation plan Q2 (`:188`); Gochara N-8 (blueprint `:323,:325,:975`) | three assets consumed by nothing; the retired edge | the Q2 decision this brief settles as a voice (§10.3) |
| Lane D §13 (`LANE_D_ASSET_REGISTER.md:655-676`); T1 (`:305`) [A] | 120 rows, `lit`, single build 2026-09-07 | [A] |
| Migration 531 (`:44-72`) | DDL: `window_start/window_end TIMESTAMPTZ`, the natural key, CHECK on `verification_pass_status`, `computed_at` (`:63`) | `computed_at` is the only knowledge-time field |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration and latent value [V]
`asset_registry_seed.ts:2530-2544`: `target_table` `:2537`, `depends_on` `:2544`, `scope:
'per_chart'`. **Latent-value classes (template §2.1):** (a) *served and correct* — the cast
(`pravesha_lagna_*`, `graha_positions_jsonb`, `ephemeris_audit_jsonb`), the two-pass verification;
(b) *served and mis-asserted* — `window_start`/`window_end` (right value, wrong declared zone) and
their offset-stripped render; (c) *computed, unserved* — the verification status is available per row
but not typed as an F06 state; (d) *absent* — a source adjudication.
**Knowledge time (template §2.6):** the windows are event-time instants; `computed_at` (`531:63`)
is knowledge time.

### 2.2 The code [V]/[R]
- Constants `:60-70`: `FORMULA_VERSION`, `CANONICAL_AYANAMSHA`, **`ENGINE_AYANAMSHA = "lahiri"`**
  (`:62` — an SC-10-class bare literal that is **inside `may_touch`**, F-19),
  `CLASSICAL_SOURCE_CITATION = "not_in_corpus: …"`.
- `_FETCH_NATAL_MOON_SQL` (`:72-77`): by `fact_id` at the canonical ayanāṃśa — §N.5 correct.
- `_birth_dt_and_params_from_config` (`:116-127`): `datetime.fromisoformat(raw[:19])` (`:125`) —
  **naive by construction on orchestrator input** (F-08).
- `_moon_longitude` (`:130-146`): `jd` from the naive wall clock **plus** `tz=float(bp[
  "tz_offset_hours"])` (`:141`); `_annual_chart` (`:149-156`) passes `birth_params` with
  `instant.isoformat()` — the correct-instant pattern (F-01).
- `_compute_one_year` (`:181-231`): `lunar_return` (`logic.py:121-142`, never raises `:139`);
  two-pass verification (`:201-211`, `LUNAR_RETURN_TOL_DEG = 0.01`, `logic.py:73`); **naive
  `window_start`/`window_end` at `:215-216`**.
- Write: `_DELETE_SQL` `:79`; INSERT `:81-98` with `ON CONFLICT … DO NOTHING` `:97`; honest no-op
  `:249-253`; `run` `:240-303`.
- `DEFAULT_MAX_PRAVESHA_YEAR = 120` (`logic.py:81`); `pravesha_anniversary` (`:102-109`).
- **Verification status**: the writer **can** emit `divergent_flagged` (`:206-211`; DDL CHECK
  `531:60`); whether any production row **does** is unverified (F-20).

### 2.3 Consumers [V]/[R]
| consumer | reads | role |
|---|---|---|
| `query_tithi_pravesha.ts:83-94` | the table; **`to_char(window_start,'YYYY-MM-DD"T"HH24:MI:SS')` — the offset is stripped** (`:84-85`); `as_of` default `new Date()` (`:70`); a bare date cast `$4::timestamptz` at session tz (`:90`) | served — **the serving half of the defect** (F-17) |
| `now.ts:613-660`; coverage `:2040-2049` | named fields | served |
| **`gochara_v3/mechanisms/w27_annual_stack.py:306-372`** | `ClassContext.tithi_pravesha_rows` — **nothing populates it** (`context.py:114`), `engine.py` has no w27 reference; expected keys (`event_class`, `tone`, `varsha_start_iso`) match **no** `kala_tithi_pravesha` column | **registered candidate, unwired** (F-05) |
| no `ph_*` / `mi_*` / `ka_*` writer reads the table | — | — |

**Live-path statement.** Served on two surfaces; no integrator; one registered-but-unwired
candidate whose proposed use is a λ-product modifier.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `natal_moon_longitude_deg` | `COMPUTED_FACT_CONFIGURATION` (referenced) | L1 by `fact_id` | correct |
| the return instant (value) | computed fact **at the correct absolute instant** | this writer + PyJHora | the *value* is right; the *declared zone* is not |
| `window_start/window_end` (assertion) | the same instant **asserted 5.5 h late** | this writer → `timestamptz` | the defect, and the only thing the repair moves |
| `pravesha_lagna_*`, `graha_positions_jsonb`, `ephemeris_audit_jsonb` | computed facts | the cast | **unchanged by the repair** — the equivalence contract |
| `verification_pass_status` | earned status (two-pass) | this writer | **can** read `divergent_flagged`; typed as F06 by §4.4 |
| method | **unsourced with an unreceipted absence claim** | this writer's constant — contradicted by `w27b_tithi_pravesha.yaml`'s `citation_status: cited` | D-M adjudicates both |

### 2.5 Ladders
`PLAN_REVIEWED`; 120 rows, `lit` [A]. t3: a t0 freeze, inadmissible.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Read any row's `window_start`: the column is `timestamptz`, the value was inserted naive, and production measures it **5.5 h late** (context §4). The **cast at that row is nevertheless correct** — lagna, grahas and audit were computed at the true instant. So the row is internally inconsistent in one direction only: a consumer that *displays* the moment is 5.5 h off, and a consumer that *re-casts* from it gets a chart ~3° of lunar motion away from the one stored beside it. The served path compounds it: `to_char` renders the timestamp **without its offset**, so in a UTC session today's mislabeled rows print the *correct-looking* IST digits — and after the fix they will print UTC digits 5.5 h earlier, which a consumer comparing to local wall-clock will read as the regression |
| Evidence | `writer.py:125,:130-146,:149-156,:215-216,:81-98`; `531:49-50`; `compute.py:30-33,:58-66`; `drik.py:1773`; `test_ka_tithi_pravesha_writer.py:189-196`; `query_tithi_pravesha.ts:83-90`; context §4 [A] — [V]/[R] |
| Expected contract | Binding B1 (`t_start/t_end` as tz-aware instants, `time_basis='event_instant'`, `claim_grain='instant_grain'`) **and its tz-source rule on the serving path**; §N.7 item 1 (a stored value restates what was computed); DP03 |
| Defect class | **mis-asserted context** (a correct instant declared in the wrong zone) + **serving-render loss** (the offset stripped) + **unqualified method with an unreceipted absence claim** + **an unwired registered candidate proposing a barred operand class** |
| Impact | a served praveśa moment is 5.5 h wrong; any re-cast from it is ~3° of lunar motion out; migration 670's (b) re-derives from the same naive audit and is structurally blind to it, so nothing detects the error today |
| Non-claim | **no claim that the cast is wrong** — it is not; no claim that any consumer re-casts today (none does); the 5.5 h is context §4's production measurement, not re-measured here; the builder session's `TimeZone` setting is unverified (no `SET TIME ZONE` appears in the orchestrator) |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q06; Q05 **partial and conditional** on §10.3 (today nothing consumes the
   voice). **Q09 cannot be served** — the writer pins one convention (`CANONICAL_AYANAMSHA` `:61`;
   `ENGINE_AYANAMSHA='lahiri'` `:62`) and computes no variant, while Q09's proof requires recomputing
   declared variants (F-06). A second-ayanāṃśa partition would be a separate delta.
2. **Instants (B1) — attach, don't un-discard (F-08).** The production input is naive
   (`datetime_iso`) with the offset alongside (`tz_offset_hours`); the repair **attaches** that fixed
   offset to the wall clock and converts to UTC before the INSERT. An ISO string that *does* carry an
   offset is a second, secondary fixture. `t_start/t_end` (aliasing `window_start/window_end` for one
   generation), `inclusivity='closed_open'`, `time_basis='event_instant'`,
   `claim_grain='instant_grain'`.
3. **The equivalence contract — the inverse of v1.0's (F-01).** After the repair:
   `pravesha_lagna_*`, `graha_positions_jsonb`, `ephemeris_audit_jsonb` and
   `natal_moon_longitude_deg` are **byte-identical**; `window_start`/`window_end` move by exactly
   `−tz_offset_hours`; **nothing else changes**. That is the rebuild's acceptance test, and it is
   also why the rebuild is safe: no chart's reading changes, only its stated moment.
4. **The serving render (F-17).** The interface packet must serve the offset —
   `to_char(… 'YYYY-MM-DD"T"HH24:MI:SSOF')` or `AT TIME ZONE` with the declared zone — name the
   `as_of` default (`:70`) and the bare-date cast (`:90`), and the Delivery detector must compare
   **instants**, not rendered strings.
5. **Verification as an F06 state (B2).** `verification_pass_status` → `completeness_state`:
   `applied` on a clean two-pass, `contradictory_unresolved` on `divergent_flagged`, `unavailable`
   where the root-find did not converge; `reason`, `owner`, `evidence_ref`, `next_eligible_action`
   beside it.
6. **Source qualification with a receipt (F-21).** `source_qualification='unsourced'` **with the
   `count(*)` result that establishes it** — the constant asserts an absence and no receipt exists
   for it (nor for my own v1.0 claim that no predicate was ever run; that claim is withdrawn as
   unreceipted). The D-M lane adjudicates, **and must also adjudicate
   `w27b_tithi_pravesha.yaml`'s contrary `citation_status: cited` / "Kṛṣṇa Miśra / Tājaka … Sudarśana
   Cakra Paddhati"** — two repository records disagree about the same technique's sources (F-05).
7. **One declared root (B4, F-15).** `independence_group = [{group_id, family:'tithi_pravesha',
   roots:[natal_moon_fact_id], members:['pravesha_year'], basis:'declared_lineage'}]`,
   `declared_current_count=1` — the natal Moon is shared with every nakṣatra daśā **and with
   `ka_sudarshana_varsha`'s own `roots[]`**, so a consumer of both must not count two.
8. **Coverage (B5 shape, F-07).** `{requested_horizon: [year 1, year 120], completed_horizon,
   resolution: 'pravesha_year', partitions_searched: [ayanāṃśa], exclusions: [{year, reason}] for
   non-converged years, unsearched_regions: [], completion_detector: 'contiguous_year_run'}`;
   blueprint §12.1's Clock-interval names `clocks_consulted`/`clocks_unavailable` for the served
   projection.
9. **B3 (not offered, stated).** Rows are addressed by the natural key; no cross-asset citation
   exists until the voice does — `window_ref` is declined with that reason rather than faked.
10. **`ENGINE_AYANAMSHA` (F-19).** The bare `'lahiri'` at `:62` is **in scope**; either it resolves
    through the one alias map or the brief states why the literal stays. Recommended: resolve it, and
    record that the engine's own vocabulary is the constraint.
11. **Old vs new.** Positive (**production shape**): naive `datetime_iso` + `tz_offset_hours` → rows
    whose windows are UTC and whose cast is byte-identical to today's. Positive (secondary): an ISO
    string carrying an offset. Negative: `tz_offset_hours` absent → the orchestrator cannot produce
    it (`_REQUIRED:33`), so this stays a **unit-level** guard, not a production path. Boundary: a
    return at **03:00 IST** (= 21:30 UTC the previous day) → the UTC date and the served local date
    differ and both are correct under their declared zones (v1.0's 23:55 IST example was wrong —
    23:55 IST is 18:25 UTC the *same* day, F-03). Missing: a non-converged year → `unavailable` with
    a reason, not a silent gap.
12. **Simpler baseline.** Today's rows.
13. **Ablation.** Re-evaluate the Moon at each stored instant **read as UTC**: today it is ~3° from
    natal (5.5 h × ≈0.549°/h — the mean rate from `logic.py:67`'s 13.176°/day; the true-rate range is
    2.7–3.5°, F-09); after, within `LUNAR_RETURN_TOL_DEG`. That single check distinguishes the fix
    from plumbing, and **migration 670's (b) cannot perform it** because it re-derives from the same
    naive-computed audit.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the root-find kernel and its two-pass verification; the L1 `fact_id` read; the
  prepare-before-DELETE block (`fa9857f00`, **not** `47131772b` — F-10); `logic.py`'s
  never-raises contract; **and, above all, the cast itself** (§4.3).
- `ENRICH_CORRECT`: UTC instants on the row and the offset on the served render.
- `QUALIFY_LIMIT`: `source_qualification='unsourced'` with a receipt; F06 states; one root.
- **Tests that must flip (F-23):** `test_ka_tithi_pravesha_writer.py:117` (the naive-equality pin),
  `:196` and `:205` (aware − naive raises `TypeError`), and
  `test_w2_first_frontier_writer_preservation.py:289`.
- **Migration**: one additive migration (qualification columns). Number: the next free slot verified
  at execution against `origin/main` (in-tree max is 1072) — not asserted (F-18).
- **Writer-digest regeneration (F-23):** the code digest at
  `platform/src/generated/nirmana-writer-digests.json:100` is consumed by
  `dispatch_frozen_rebuild.py:29,58,113`; changing the writer changes it, so the file is
  **regenerated** as part of the packet (it is in `may_touch` for that purpose only).
- Fences: L1, the shared engines, the L0 corpus and Gochara untouched; the two served files are
  interface-packet targets.
- Rollback: the additive columns are nullable; the instant fix is the rebuild's own contract (§4.3).

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 rows; a numerical root-find over an L1-referenced target; `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | L1 `chart_facts` + `birth_params`; shared engines; fan-out: two served surfaces, one unwired candidate |
| C | invariants: 670 (a)–(i); **the cast is byte-identical across the repair**; the Moon at each stored UTC instant is within tolerance of natal; `t_end(N) = t_start(N+1)`; one root |
| D | the source adjudication (D-M), including the contrary w27b citation |
| E | served ×2; integrator ×0; one registered candidate proposing a barred operand class |
| F | `completeness_state`, `independence_group`, coverage, and an offset-bearing instant |
| G | 120 root-finds per chart; the writer's own docstring says ~3.4 ms/row; unmeasured end-to-end |
| H | idempotent; prepare-before-DELETE |
| I | files in `may_touch`; one additive migration; the digest regenerated |
| J | this brief; §7; the review; the ablation's output |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | command / fixture | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive (production shape) | COMPUTATIONAL_CORRECTNESS | I | naive `datetime_iso` + `tz_offset_hours` (the only shape the orchestrator builds) | windows in UTC; **cast columns byte-identical to today's** | §4.3 equivalence | any cast column changes | writer test |
| Positive (secondary) | COMPUTATIONAL_CORRECTNESS | U | an ISO string carrying an offset | same result | offset honoured | the offset is dropped | unit test |
| Negative | COMPUTATIONAL_CORRECTNESS | U | `tz_offset_hours` absent | a typed refusal — **a unit-level guard; `_REQUIRED:33` means the orchestrator cannot produce this** | honest absence | a naive instant is stored | unit test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I | perturb the **natal Moon longitude** by +13.176° in the fixture | `t_start` moves ≈1 day; the cast follows | the root-find depends on its target | unchanged | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | relabel the birth offset (+05:30 → +00:00) **under a correct implementation**; and permute cosmetic `birth_params` fields (`place_name`, `subject_label`) | the **nearest return and the cast are unchanged** (the anniversary moves, the return does not, barring a measure-zero knife-edge); every computed column identical | zone-relabel invariance | the return moves (which is today's naive behaviour) | writer test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | persisted row | `independence_group[0].roots == [natal_moon_fact_id]`, equal to the `chart_facts` id — **the served double-count test exists only once SC-6/IP-5 lands** | B4 shape | a per-fact count > 1 | integrity conjunct |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | a return at **03:00 IST** (= 21:30 UTC the previous day) | the UTC date and the served local date differ; both correct under their declared zones | tz-aware | one date is asserted as both | writer + route test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel: a per-row value the wrapper cannot synthesise — `completeness_state='unavailable'` seeded on one non-converging year, **or** `independence_group[0].roots[0]` = the real `moon_fact_id` | reaches `kala_now_get`'s `tithi_pravesha` object and the saved reading; **instants compared as instants, not rendered strings** | per-row propagation | absent; or a string comparison passes a wrong instant | MCP test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | bump `formula_version` | rows replaced; no accretion | §N.3 | accretion | writer test |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | I | **the ablation**: re-evaluate the Moon at each stored instant read as UTC | today ~3° from natal; after, within `LUNAR_RETURN_TOL_DEG` | the fix, not plumbing | no change | ablation record |
| Evaluation | — | — | `not_applicable` — no governed outcome set exists for an annual frame | — | — | — | — |

Binding: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`), B2
(`completeness_state` + F06 companions, `epistemic_class`, `source_qualification`,
`corpus_verifiable`, `comparable_with='different_convention'`, `operator_role='computation'`), B4
(`independence_group` in the array shape, `declared_current_count`), B5 (`coverage`, seven keys).
**B3: not offered** — rows are addressed by the natural key and no cross-asset citation exists until
the voice does (stated, not faked). **DEMANDS** the D-M adjudication.

---

## §8 — Prioritization

(1) the instant fix **with its equivalence contract** (the assertion, not the cast) → (2) the
serving render's offset → (3) the F06 states → (4) the receipted `unsourced` stamp and the D-M
adjudication (including the contrary w27b citation) → (5) one declared root + coverage →
(6) `ENGINE_AYANAMSHA` through the alias map → (7) the Q2 voice decision. W2.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY`; `DATA_ACCEPTED` requires the
120-row rebuild under the corrected instants (the §4.3 equivalence contract is its acceptance test);
`CONSUMER_INTEGRATED` when the annual voice reaches a composite surface. Campaign: `ANALYZED →
ENRICHED`. Non-claims: the cast is not wrong; nothing re-casts today; the 5.5 h is context §4's
measurement; the frozen-question fixture is pending the baseline freeze (`KALA_BASELINE_v1_0.md`
does not exist, F-12).

**Walkthrough (experience 4, ordinary year).** "What is this year's praveśa chart?" → one row: the
return instant **with its offset**, the same lagna and grahas as today (unchanged),
`completeness_state='applied'`, `source_qualification='unsourced'` with its receipt,
`independence_group` naming the natal Moon. For the reader nothing about the chart changes — only
the moment stops being 5.5 h wrong, and the source claim stops being unreceipted.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **The instant fix and its equivalence contract** (cast byte-identical; windows move by −`tz_offset_hours`), plus the serving render's offset | yes — and the rebuild is gated on the equivalence test |
| 2 | **The D-M lane adjudicates BOTH the writer's `not_in_corpus` constant AND `w27b_tithi_pravesha.yaml`'s contrary `citation_status: cited`** | yes — two repository records disagree |
| 3 | **Q2 for this asset: admit the annual frame as a concurrence VOICE (SC-6), not as a λ-product modifier** — noting w27b's registered `1.25/0.80` schedule is exactly the operand class Q2 bars before M-4 | voice; w27b's schedule is superseded by the voice or held under M-4 (Gochara's call) |
| 4 | `ENGINE_AYANAMSHA`'s bare `'lahiri'`: resolve through the alias map, or state why it stays | resolve |
| 5 | The rebuild: 120 rows, one chart at a time, gated on the equivalence test | yes |

---

## §11 — Not verified here

1. The 5.5 h production figure, the 120-row count, `asset_throughput = lit`, whether any row is
   `divergent_flagged`, and the builder connection's session `TimeZone` (no `SET TIME ZONE` appears
   in `pipeline/orchestrator/*.py`) — no DB.
2. Whether `classical_text_chunks` carries lunar-return / varṣa-praveśa doctrine — and **my v1.0
   claim that no predicate was ever run is itself withdrawn as unreceipted** (F-21).
3. Whether the "ingestion work item" the writer's docstring says is filed (`:31-35`) exists — no
   tracker record found.
4. End-to-end timing (`KALA_COST_PROFILE_v1_0.md` does not exist).
5. The measure-zero knife-edge in the Irrelevant-control row (a return equidistant between two
   anniversaries under a relabel) — not computed.
6. The corpus figure: `MADHAV_PRODUCT_DEFINITION_v2_0_PROPOSAL.md:277,368` says **16** texts /
   10,651 chunks; v1.0 said 15 — the discrepancy is recorded, not resolved (F-25).
7. No database query; no test run.

## §12 — Review dispositions (v1.0 → v1.1)

F-01 accepted — the impact restated and the equivalence contract inverted (§0, §2.4, §3, §4.3, §7
Positive); F-02 accepted (§7 Relevant-influence now perturbs the natal Moon; the tz relabel is the
irrelevant control); F-03 accepted (§4.11, §7 Boundary — 03:00 IST); F-04 accepted (§7 Delivery —
a per-row sentinel); F-05 accepted (§1 new row, §2.3, §4.6, §10.2–3 — w27b as a registered candidate
with a contrary citation and a barred operand class); F-06 accepted (§4.1 — Q09 cannot be served);
F-07 accepted (§4.8 — B5 shape); F-08 accepted (§1, §2.2, §4.2, §7 Positive/Negative — the
production input shape); F-09 accepted (≈3°, range 2.7–3.5°); F-10 accepted (`fa9857f00`); F-11
accepted (§7 Duplication — the row-level invariant, with the served test gated); F-12 accepted (§9);
F-13 accepted (§7 Irrelevant control — cosmetic fields, not JSONB key order); F-14 accepted (§7 —
eleven rows incl. Evaluation, plus command and evidence-path columns); F-15 accepted (§4.7 — B4
shape); F-16 accepted (§2.1 latent-value classes and knowledge-time pin; §9 walkthrough); F-17
accepted (§0, §2.3, §3, §4.4, §7 Delivery — the serving half); F-18 accepted (§5 — number verified
at execution); F-19 accepted (§2.2, §4.10, §10.4 — the literal is in scope); F-20 accepted (§2.2 —
"can"); F-21 accepted (§4.6, §11.2 — the absence claim and my own claim about it are both
unreceipted); F-22 accepted (§2.3 cites `context.py:114` and the grep, not the Gochara plan); F-23
accepted (§1 — 670's conjuncts and its blind spot; §5 — the tests that must flip and the digest
regeneration); F-24 accepted ("commit"); F-25 accepted (ranges re-pinned; the 15-vs-16 corpus
discrepancy recorded in §11.6).
