---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_TULANA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows in §7
asset_or_interface_ids: ["ka_tulana", "IP-4 (kala_priority_get / kala_priority_ranking_get honesty)", "L3-U04 (Kalasutra/Tulana → AHEAD/NOW)"]
goal_objective: "Make ka_tulana the layer's comparison authority in fact: three named comparators (nearest, strongest, robust) instead of one composite, incomparable pairs reported as such, missing inputs dropped and declared rather than defaulted, independence inherited from the producer — and a served surface that either calls it or stops claiming to."
source_revision: "9feac52d7 (l3/kala-layer-briefs; = origin/l3/kala-elevation-readiness tip 2026-09-24)"
accepted_upstream_contract: "Saṅgam brief v1.5 / plan v1.0 (typed testimony: independence group, comparability, R-6 four components) on sangam/stage3 — DEMANDED, not yet on main; W2 service payload shape frozen (47131772b: Tulana rejects non-finite, duplicate or unqualified inputs)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_TULANA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_tulana/{ranker,writer}.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_tulana.py", "platform/python-sidecar/tests/l3/test_ka_tulana*.py", "pipeline/orchestrator/service_probes.py (ka_tulana clause)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:660-720 (call_priority_ranking), platform-mcp/src/tools/kala_views/priority.ts"]
must_not_touch: ["kala_convergence / ka_sangam (producer; Saṅgam packet)", "kala_activation / ka_kalasutra (the table the wrapper reads today; Kalasutra brief)", "platform-mcp/src/tools/kala_views/** except as an interface packet", "platform/src/lib/retrieval/registry/layers/register_d7_channel.ts (Saṅgam amendment-9 blast radius; coordinated)", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the pure comparators (stage 3, DB-free); CONSUMER_INTEGRATED when a served surface calls the service with real WindowInputs and the L3 sentinel passes; data-bound acceptance W7"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; no t3 event today (a superseded t2 freeze is inadmissible)"
wave: "W2 pure / W7 data-bound"
shape: single asset, pure service
evidence_base: >
  Source read directly on 9feac52d7 [V]; Lane D §14, T1 Spine item 9, Lane E §3.4 and §1
  Q-K05/K14, Saṅgam amendment 9 (KALA_SYNERGY_AMENDMENTS §Saṅgam item 9) [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_tulana` elevation brief — comparison under a named criterion

## §0 — The recommendation, in one paragraph

`ka_tulana` is a built, tested, documented comparison kernel — `rank_windows`, `compare` with a
named decisive factor, `attention_map` (`ranker.py:268,307,390` [V]) — that **no production
surface calls** (only `service_probes.py:783-843` [V]). The surface that says it wraps it,
`kala_priority_get`, is inline SQL ranking L2 `computed_salience` × an orb term that is NULL on
99.6% of rows, joined to `kala_activation` for a date filter (`call_service_wrappers.ts:670-712`
[V]) — L3's contribution to "what matters most" is the WHERE clause. And the kernel itself, when it
runs, is one composite (40/25/20/15) over four axes that are not on one scale, with a proximity
term that floors every past window at 0.05 (`:207-208`), a rarity default of 0.5 and a confidence
default of 0.2 when the input is missing (`:192-194,:222`) — so "was 2019 stronger than 2027?"
cannot be asked (Q-K05), and a window with no rarity data outranks or trails on an invented
number. Recommendation: **`ENRICH_CORRECT` + `INTEGRATE`** — replace the composite with three
**named comparators** (Q7): `nearest` (time-asymmetric, proximity-led), `strongest`
(time-symmetric, proximity excluded), `robust` (survives declared variants; `unavailable` until
variants exist); report `incomparable` for pairs whose `comparable_with` differs (Mode A vs C);
drop-and-declare missing inputs instead of 0.5/0.2; take `independence_group` from the producer
(SC-4) in place of the `confidence_label` that Saṅgam is retiring (amendment 9); build the
`WindowInput` adapter from real `kala_convergence` columns by `window_ref`; and make
`kala_priority_get` either call the service or describe itself honestly (IP-4). No table, no rows.
Decision for the native: Q7, and the interim rename (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:157) | *"Comparison service and factor breakdown. P/I/Q: compare named outcomes/criteria, nearest/strongest/robust separately; self-test not consumer-value proof. DP08/17."* | the three-comparator obligation is stated there already |
| Strategy §6.1 **L3-A04** | *"Preserve useful ranking kernel; add matched mechanism/context, nearest versus stronger/robust candidates, trade-offs, ties and incomparable states. Prove both pure behavior and accepted-window use."* W2 pure / W7 data-bound | unchanged |
| Strategy §2 **L3-Q02** | *nearest, strongest under a named criterion, robust across declared variants and merely present remain distinct*; proof = *controlled ranking on matched candidates and coverage; preserve ties/incomparability* | the value frame |
| Strategy **L3-U04** | selection over the right complete candidate set; *"a stronger historical-only ladder cannot suppress a weaker future recurrence"*; calibration-only changes cannot change coverage labels | binds §4 item 5 |
| Product §7.1 | *"'Strongest' is not an unexplained scalar"* | §3 |
| W0 register #19 | `service ranking/compare/attention payloads`; W2: rejects non-finite, duplicate or unqualified inputs while retaining its fixed forensic result | `:80` rejects unknown `confidence_label` [V] |
| Lane D §14 / T1 Spine 9 | **NOT-FOUND** consumer; wrapper reads `kala_activation`, not any Tulana output; no `kala_tulana` table exists | confirmed [V]: the only `KaTulanaService|rank_windows|attention_map|CompareVerdict` reference outside `services/ka_tulana/` and tests is `service_probes.py` |
| Lane E §3.4 | the wrapper's SQL; `orb_strength` NULL on 669,964/672,551; the I-11 composite computed nowhere in production; proximity floor; invented defaults; a future `rank_windows` over `kala_activation` would get `rarity_norm=0.5`, `confidence=0.2` on every row while the rationale string reports them as measured | all confirmed at the cited lines on this base [V] (§2.2) |
| Saṅgam amendments (2026-09-24) item 9 | Saṅgam's brief mandates removing `confidence_score`/`confidence_label`; readers include `ka_tulana/writer.py`, `ka_tulana/ranker.py` — *"a coordinated change behind the §6.2 sentinel"* | this brief migrates Tulana off both fields (§4 item 4) |
| Elevation plan Q7 | names `tulana` | §10 |
| Blueprint v5.0 §3.5 row 4, §12.2 IP-4, §16.2 | three comparators; rename until the wrap is real | binds §4/§9 |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V seed]
`asset_registry_seed.ts:2432-2440`: `storage_type: 'service'`, no table, `depends_on:
['ka_sangam', 'ka_vighnakara', 'ka_kala_darshana']`, `scope: 'per_chart'`,
`estimated_seconds: null`, `asset_kind: 'service'`.

### 2.2 The code [V]
- **Writer** `writers/ka_tulana.py:1-19`: returns `WriterResult(rows_inserted=0)`; logic in
  `services/ka_tulana/writer.py` (self-test). Conformant.
- **Kernel** `services/ka_tulana/ranker.py`:
  - `I11_WEIGHTS = {convergence_score: 0.40, rarity_years: 0.25, confidence_score: 0.20,
    proximity_factor: 0.15}` (`:38-45`); `_CONFIDENCE_NUMERIC = {high:1.0, moderate:0.6,
    speculative:0.2}` (`:49`); unknown label rejected at input (`:80`).
  - `rarity_years is None → 0.5` (`:192-194`); `_proximity_factor` (`:198-215`): `days < 0 →
    0.05  # past window` (`:207-208`), >1 yr → 0.05 floor.
  - composite (`:222-229`); rationale string reports each factor incl. `proximity=… weight 15%`
    (`:247`).
  - `rank_windows(..., reference_date=None)` — *"Defaults to date.today()"* (`:268-281`);
    `compare(a, b)` → `CompareVerdict` (`:166,:307-389`) with per-factor deltas (`:332`) and a
    confidence-label comparison (`:365-366`); `attention_map(horizon_days)` (`:390-405`).
- **The served "wrapper"** `call_service_wrappers.ts:660-712`: `priority_score =
  m.computed_salience * COALESCE(a.orb_strength, 1.0) * (dignity-neutral ? 0.3 : 1.0)` over
  `bodha_msr_signals m JOIN kala_activation a` with a date-overlap WHERE; `orb_strength_available`
  emitted (good §N.6 practice); the comment records the 99.6% NULL measurement. No call to the
  sidecar, no `KaTulanaService`.

### 2.3 Consumers (grep on this base, tests excluded) [V]
| consumer | reads | role |
|---|---|---|
| `pipeline/orchestrator/service_probes.py:655-846` | `rank_windows()` / `compare()` on fixed `WindowInput`s (pure probe, *"no architecture question, unlike ka_dasha_kala"*, `:659-663`) | probe |
| `kala_priority_get` / `kala_priority_ranking_get` (`priority.ts`; `call_service_wrappers.ts`) | **claim** to wrap it (`priority.ts:330-331`, description `:525` [A: Lane E]); do not | misnamed |
| nobody else | — | — |

**Live-path statement.** No live path reaches the kernel. The misnamed surface is live and
user-reachable. `WindowInput` requires `rarity_years` and `confidence_label`, which `kala_activation`
(the wrapper's table) does not carry and `kala_convergence` (the declared producer) does — but
`kala_convergence` is 0 rows for the canonical chart, so even a correct wrap would rank nothing
today (starvation, blueprint §3.5 reading 1).

### 2.4 Epistemic class of the important quantities
| quantity | class | authority | note |
|---|---|---|---|
| `convergence_score` | engineered inference (Saṅgam) | `kala_convergence` | mode-dependent scale: A/B ≤ 0.3805, C ≥ 0.70 [A: Lane E §0.1] — **not one scale** |
| `rarity_years` | computed (never audited; Saṅgam retires it) | `kala_convergence` | 0.5 default is invented (§N.7 item 6) |
| `confidence_label` | = `icc/13` bucketed; anti-correlated with evidence count | Saṅgam, **being removed** | 0.2 default invented; the whole axis is a proxy for independence |
| `proximity_factor` | a prioritisation term, not a strength term | this kernel | makes past windows incomparable |
| the composite | `INTERPRETIVE_INFERENCE` | this kernel | *"'strongest' is not an unexplained scalar"* — it is one |
| `CompareVerdict.decisive_factor` | explanation | this kernel | the genuinely valuable part |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; pure kernel tests pass (W2). t3: a t2 `asset_frozen` exists and is inadmissible.
Cost: pure in-memory ranking; negligible; the data-bound cost is the producer's.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Ask "is my 2027 window stronger than 2019?" (Q-K05): `compare` scores 2019's proximity at 0.05 and 2027's at up to 1.0, a 15% weight decided by *when it is asked*, and its verdict names `proximity_factor` as decisive whenever the other three are close. Ask "what matters most now?" (`kala_priority_get`): the answer is L2's salience ordering under an L3 name; `ka_tulana` runs nowhere. Feed two Mode-C windows and one Mode-A window to `rank_windows`: they are ranked on `convergence_score` as if one scale |
| Evidence | `ranker.py:207-208, 222-229, 192-194, 49, 80, 281`; `call_service_wrappers.ts:670-712`; grep for callers [V] |
| Expected contract | L3-Q02 (*nearest, strongest, robust, merely present remain distinct; preserve ties/incomparability*); Product §7.1; L3-U04; F08/L3-Q05 (*non-comparable scales*); §N.7 item 6 (no invented neutral); Strategy §3 *Comparison/election* (*no universal ranking*); F28 (a surface that claims a component must have a path that would fail without it) |
| Defect class | **unserved** (kernel has no consumer) + **wrong authority** (a surface claims it) + **flattened** (four axes → one composite) + **invented neutrality** (0.5 / 0.2) + **wrong context** (`date.today()` reference) |
| Impact | Q-K05 unanswerable; Q-K14 (within-chart rarity) unserved though computed; Q02's *nearest vs stronger* is answered by nobody; the person is told "what matters most" by L2 with an L3 label |
| Non-claim | No claim that the kernel's *ordering* is astrologically right — it is engineered; no live incidence (no caller); the 99.6% NULL figure is the code comment's measurement [A] |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q02 (directly); Q05's comparability half; Lane E Q-K05, Q-K14. Cannot serve
   Q01/Q03/Q08 (no windows of its own).
2. **Three comparators, no composite (Q7).** `rank(windows, criterion, reference_instant)`:
   - `nearest` — future windows only (U04: history cannot suppress a future recurrence), ordered
     by `t_start` from `reference_instant`; `strength` reported beside, never mixed in;
   - `strongest` — **time-symmetric**: proximity excluded; ordered by the producer's `activity`
     (R-6) with `independence_group` cardinality and `rarity` as declared secondary keys, *within
     one `comparable_with` class*; pairs across classes → `incomparable`;
   - `robust` — a window that remains ranked under every declared variant (ayanāṃśa, node
     convention, `kernel_version`); `completeness_state='unavailable'` until the producer supplies
     variants (Q09 is upstream).
   `criterion` is a field on every result; the legacy I-11 composite survives one generation as
   `legacy_composite` with its rationale string labelled `legacy`.
3. **Missing inputs are declared, not invented.** `rarity_years=None` → the factor is **dropped
   and the ordering renormalised**, `factors_available` lists what was used (the codebase's own
   convention at `call_service_wrappers.ts:688-697`); never 0.5/0.2.
4. **Independence in, confidence out (SC-4, amendment 9).** `WindowInput` gains
   `independence_group` and `comparable_with` from the producer row and loses
   `confidence_label`/`confidence_score` — coordinated with Saṅgam's removal behind the §6.2
   sentinel, since `ranker.py:49,80,222,365` read the label today.
5. **Ties and incomparability (B2).** `compare` returns `verdict ∈ {a, b, tie, incomparable}` with
   `decisive_factor` (or `tie_on=[…]`), `comparable_with` of the pair, and `completeness_state`
   per factor; `epistemic_class='INTERPRETIVE_INFERENCE'`, `operator_role='relevance_navigation'`
   for `nearest`, `'computation'` for `strongest`, `tier_basis='relative_uncalibrated'`.
6. **`WindowInput` adapter from real columns.** Built from `kala_convergence` rows by
   `window_ref` (B3): `t_start/t_end/t_peak` as `timestamptz` (B1, from the producer's converted
   fields), `activity`, `valence`, `rarity_years` (until retired), `independence_group`,
   `comparable_with`, `generation`; never from `kala_activation` (which lacks the fields — the
   wrapper's current table).
7. **Time discipline (SC-1).** `reference_instant` is a required parameter, echoed on the result;
   no `date.today()` default (`:281`).
8. **Coverage (B5).** Every ranking carries `coverage = {candidates_supplied, candidates_ranked,
   excluded: [{window_ref, reason ∈ {incomparable, missing_required_field, past_under_nearest}}]}`.
9. **IP-4.** `kala_priority_get` / `kala_priority_ranking_get`: either call the sidecar's Tulana
   route with `WindowInput`s from `kala_convergence` and name the `criterion`, or their
   description and name change to what they are (`salience_by_date`). Interim: the description
   change is a one-line honesty fix that can land first.
10. **Old vs new.** Positive: 2019 vs 2027 under `strongest` → decided on activity/independence,
    proximity absent. Negative: Mode A vs Mode C → `incomparable`. Boundary: two windows with equal
    activity → `tie`, `tie_on=['activity']`. Missing: no `rarity_years` → dropped, declared.
    Duplicated: two windows from one `independence_group` → not "two strong windows".
11. **Simpler baseline.** The I-11 composite (for the kernel) and the inline SQL (for the surface).
12. **Ablation.** Under `strongest`, swap the two windows' dates (keeping everything else): today
    the composite flips (proximity); after, the verdict is invariant — that invariance is the
    distinction. For IP-4: remove the Tulana call → the served ranking must change (else the
    surface never used it).

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: `compare`'s decisive-factor explanation; `attention_map`; the input validation
  (`:80`, W2); the forensic fixture in `service_probes.py`.
- `ENRICH_CORRECT`: comparators; declared missingness; ties/incomparable; `reference_instant`.
- `INTEGRATE`: the `WindowInput` adapter by `window_ref`; IP-4.
- `RETIRE_AFTER_MIGRATION` (one generation): the I-11 composite and the `confidence_*` inputs —
  coordinated with Saṅgam amendment 9 (five readers + `register_d7_channel.ts` + the capability
  census).
- **Fences**: reads `kala_convergence` only through the adapter (Saṅgam-owned table; no writes);
  `kala_views/priority.ts` by interface packet; `register_d7_channel.ts` is in the amendment-9
  blast radius — one coordinated change.
- **Dependency honesty**: `depends_on` keeps `ka_sangam` (real, via adapter); `ka_vighnakara` and
  `ka_kala_darshana` are declared and **not read** by the kernel — either the adapter reads
  obstruction/effective-view fields from them (then keep) or the edges are dropped (registry
  packet). This brief recommends **keep and read**: `valence`/obstruction from Vighnakara is
  exactly what `strongest` needs to avoid ranking a strongly-opposed window first.
- No table, no migration; rollback = keep `legacy_composite` as the served value.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_tulana`, L3 pure service; epistemic: engineered comparison over producers' testimony; placement correct (Comparison/election object); `ENRICH_CORRECT + INTEGRATE` |
| B | declared three edges; reads none directly today (pure); the adapter makes `ka_sangam` real and decides the other two; no hidden read; T5 leaf |
| C | invariants: `strongest` invariant to `reference_instant`; `nearest` monotone in `t_start`; `incomparable` iff `comparable_with` differs; dropped factor renormalises to the same order as when all present with equal values. Golden: the forensic fixture; property: shuffle invariance |
| D | n/a; the data gap is the producer's (`kala_convergence` empty; `independence_group` not yet emitted) |
| E | no consumer (the defect); one misnamed surface; declared edges unread |
| F | `criterion`, `decisive_factor`, `incomparable`, `factors_available` machine-readable; the served surface names what it used |
| G | negligible; **justified no-change** |
| H | pure; idempotent; no timeout concern |
| I | files in `may_touch`; W2 pure / W7 data; coordinated with Saṅgam amendment 9 |
| J | this brief; §7; review; the IP-4 sentinel |

---

## §7 — Proof matrix

| proof | fixture | expected | invariant | detector fails when… |
|---|---|---|---|---|
| Positive | three synthetic windows, Mode A, `strongest` | ordered by activity → independence → rarity | order stable under shuffle | order changes with input order |
| Negative | Mode A vs Mode C pair | `incomparable` | never ranked together | a rank is emitted |
| Relevant influence | change one window's `independence_group` cardinality 1→3 | it moves up under `strongest` | others unchanged | no movement |
| Irrelevant control | swap the two windows' dates under `strongest` | identical verdict | proximity absent | verdict flips |
| Duplication | two windows sharing one `independence_group` | not counted as two independent strong windows in `attention_map` | dedup | counted twice |
| Context | `rarity_years=None` | factor dropped, `factors_available` lists three; **no 0.5** | declared | 0.5 appears |
| Boundary | `reference_instant` = a window's `t_start` exactly | `nearest` includes it under `closed_open` | inclusivity honoured | excluded/included wrongly |
| Delivery (IP-4) | sentinel `criterion='strongest'` from the service | reaches `kala_priority_ranking_get`'s envelope | survives | absent → the surface did not call the service |
| Revision | producer emits a new `generation` | adapter re-reads; no cache | fresh | stale |
| Value | frozen Q02/Q-K05 question | a time-symmetric answer with a decisive factor; the baseline cannot give one | — | no distinction |

Binding: **DEMANDS** B1 (`t_start/t_end/t_peak` timestamptz), B2 (`comparable_with`, R-6 fields),
B3 (`window_ref`, `generation`), B4 (`independence_group`) from the producer; **OFFERS** B2
(`completeness_state`, `operator_role`, `tier_basis`) and B5 (`coverage`) on its results.

---

## §8 — Prioritization

(1) IP-4 honesty (a surface claims a component it does not use — F28; one line) → (2) `strongest`
time-symmetric + declared missingness (correctness of the comparison) → (3) `independence_group`
in / `confidence_*` out (coordinated with Saṅgam) → (4) the adapter + wrap (integration; waits on
`kala_convergence` data and R-5 identity) → (5) `robust` (waits on variants). Leaf of the DAG
(T5); W2 pure now, W7 data-bound; no P-candidate.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `INTEGRATE` (service terminal rule: correctness, failure semantics and **a
product consumer** verified; no row-count proxy). Data-plane: `PRODUCER_READY` (pure) after §7;
`CONSUMER_INTEGRATED` when a served surface calls it at a `file:line` on `main` with the sentinel
— which requires `kala_convergence` to hold rows for the chart. Campaign: `ANALYZED` →
`ENRICHED`. Non-claims: `VALUE_EVALUATED` N until the baseline's Q02 case; the kernel's ordering
is engineered, not classical; no live ranking exists to compare against.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Q7 — the three comparators as the contract; the composite retired** | yes; `strongest` excludes proximity by definition |
| 2 | **IP-4 interim: rename/describe `kala_priority_get` honestly now, wrap later?** | yes — the description fix is one line and removes a false claim today |
| 3 | Drop or read the declared `ka_vighnakara` / `ka_kala_darshana` edges? | **read** (obstruction/valence into `strongest`); if the adapter cannot, drop them by registry packet — never leave a declared edge unread |
| 4 | What `strongest`'s secondary keys are once `rarity_years` is retired (Saṅgam) | activity → independence cardinality → `t_start`; recorded as engineered, `tier_basis='relative_uncalibrated'` |

---

## §11 — Not verified here

1. `priority.ts:330-331` and the `:525` description text — Lane E's citations [A], not re-opened
   (the wrapper SQL was [V]).
2. The 99.6% NULL figure — the code comment's own measurement [A].
3. Whether any non-`.py/.ts` caller (notebooks, scripts) uses the kernel — search scope stated.
4. No database query; `kala_convergence` emptiness is Lane E's 2026-09-22 measurement [A].
