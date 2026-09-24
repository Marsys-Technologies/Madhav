---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_TULANA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_TULANA_v1_0.md, 22 findings); v1.1 dispositions each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows + asset-local fields declared in §7
asset_or_interface_ids: ["ka_tulana", "IP-4 (kala_priority_get / kala_priority_ranking_get honesty — enumerated blast radius)", "new sidecar route (stage 3) exposing rank/compare/attention_map", "probe-contract re-pin (migration 849 successor) — coordinated Pūrṇa packet", "L3-U04 (Kalasutra/Tulana → AHEAD/NOW)"]
goal_objective: "Make ka_tulana the layer's comparison authority in fact: three named comparators (nearest, strongest, robust) instead of one composite; every mode admitted and partitioned by comparability instead of Mode C/D refused at the door; missing inputs dropped and declared rather than defaulted; independence inherited from the producer — and a served surface that either calls it through a route that exists or stops claiming to, across every site that makes the claim."
source_revision: "9feac52d7 (l3/kala-layer-briefs; every cited code file byte-identical to HEAD bf70a3477 per the reviewer's diff)"
accepted_upstream_contract: "Saṅgam brief v1.5 / plan v1.0 typed testimony — DEMANDED, and persisted on NO branch today: sangam/stage3's ka_sangam.py INSERT column list (:990-999) is byte-identical to HEAD; stage3 exposure.py:65-82 still spells comparability_class; the Saṅgam brief spells independence_groups (SANGAM_ELEVATION_BRIEF_v1_0.md:184). W2 service input validation landed via fa9857f00 (#2607), not 47131772b (which touches Avadhi/Yojaka only)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; v1.0 report at briefs/reviews/REVIEW_KA_TULANA_v1_0.md; re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_tulana/{ranker,writer}.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_tulana.py", "platform/python-sidecar/routers/tulana.py (NEW at stage 3 — no sidecar route exposes the kernel today)", "platform/python-sidecar/tests/test_ka_tulana.py, tests/l3/test_w2_first_frontier_service_contracts.py (tulana rows), tests/test_service_probes.py, tests/test_migration_849_*.py, tests/test_nirmana_probe_route.py (assertions that must flip — §5)", "pipeline/orchestrator/service_probes.py:655-846 (ka_tulana clause) + platform/scripts/nirmana_probe_contracts.json + one NEW migration re-pinning asset_registry.health_probe (successor to 849) — coordinated Pūrṇa packet", "interface packet only (IP-4, enumerated in §4.9): platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:10,518-535,672-730; platform-mcp/src/tools/kala_views/priority.ts:8-10,329-331; register_p1_aliases.ts:1017,1022-1024; authority_basis_census_seed.ts:147-151; producer_editorial_review.ts:384-387; service_manifest.json:664-668; L3_kala/index.ts:27; regenerated projections"]
must_not_touch: ["kala_convergence / ka_sangam (producer; Saṅgam packet)", "kala_activation / ka_kalasutra (the table the wrapper reads today; Kalasutra brief)", "platform-mcp/src/tools/kala_views/** except as an interface packet", "register_d7_channel.ts (Saṅgam amendment-9 blast radius; coordinated)", "asset_registry_seed.ts:2438 depends_on edges (registry packet, own owner — §10.3)", "applied migrations (849 is applied and sha-pinned; it is superseded by a new migration, never edited)", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the pure comparators (stage 3, DB-free, synthetic inputs); CONSUMER_INTEGRATED when a served surface calls the new route with real WindowInputs and the L3 sentinel passes; data-bound acceptance W7 — gated on Saṅgam persisting the DEMANDED columns"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; no t3 event today (a superseded t2 freeze — audit/_work/F2.md:126 [A] — is inadmissible)"
wave: "W2 pure / W7 data-bound"
shape: single asset, pure service
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted here are marked [R] with
  the reviewer's file:line; Lane D §14, T1 Spine item 9, Lane E §3.4 / §0.1 / §1 Q-K05/K14, Saṅgam
  amendment 9 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions — F-01 rank_windows refuses Mode C/D (ranker.py:61-62) while kala_convergence holds C/D: the defect is exclusion, not flattening; F-02 no sidecar route exists — a NEW route is stage-3 code, INTEGRATE split into honesty-now/wrap-later; F-03 migration 849 sha-pins the composite (0.795/0.4234/proximity_factor): retiring it needs a successor migration + contracts re-pin, legacy_composite must keep the fixture values meanwhile; F-04 the description claim lives at ≥7 sites + generated projections — enumerated; F-05 Delivery sentinel made kernel-only; F-06 coverage in B5 shape; F-07 DEMANDED columns persisted on no branch, spelling mapping declared, every data-bound proof marked synthetic; F-08 fa9857f00; F-09 :222 unreachable, :135 default, rationale discloses; F-10 two live fixture paths; F-11 WindowInput required fields; F-12 decisive_factor concept preserved, computation replaced; F-13 Evaluation row + command/evidence columns; F-14 ordinary-period fixture + walkthrough; F-15 partition key defined; F-16–F-22 citation fixes; asset-local fields declared."
  - "1.0 (2026-09-24): first issue."
---

# `ka_tulana` elevation brief — comparison under a named criterion

## §0 — The recommendation, in one paragraph

`ka_tulana` is a built, tested comparison kernel — `rank_windows`, `compare` with a named decisive
factor, `attention_map` (`ranker.py:268,307,390` [V]) — that **no production surface calls with
chart-derived inputs**: its two live paths are the writer self-test (`services/ka_tulana/writer.py:55`
[R]) and the deployed health probe (`routers/nirmana_probe.py:24,111` → `service_probes.py:797,844`
[R]), both on fixed fixtures. The surface that says it wraps it, `kala_priority_get`, is inline SQL
ranking L2 `computed_salience` × an orb term NULL on 99.6% of rows, joined to `kala_activation`
for a date filter (`call_service_wrappers.ts:672-730` [R]); `service_manifest.json:664-668` says so
in as many words (*"Direct Postgres query … NOT a sidecar HTTP call"* [R]), and **no sidecar route
exposes the kernel** (grep over `routers/*.py`: only the fixed-fixture probe [R]). The kernel
itself, when it runs, is one composite (40/25/20/15) over four axes not on one scale, with a
proximity term flooring every past window at 0.05 (`:207-208`), an invented rarity of 0.5
(`:192-194`), a `confidence_label` that **defaults to `'speculative'`** at the dataclass (`:135`
[R]) → 0.2 — and, decisively, it **refuses every Mode C or D window at the door**
(`if window.mode not in {"A","B"}: raise ValueError`, `:61-62`, via `_validate_window_set` `:288`
[R]) while `kala_convergence.mode` has held `'C'` since migration 360 dropped the CHECK
(`360_kala_convergence_mode_c.sql:12` [R]) and Saṅgam emits `'C'`/`'D'` (`engine.py:2115,2134,2201`
[R]) — so a correct adapter over the real producer would be rejected for the whole top-750.
Recommendation: **`ENRICH_CORRECT` + `INTEGRATE` (split: honesty now, wrap later)** — three
**named comparators** (Q7): `nearest`, `strongest`, `robust`; **all modes admitted** and partitioned
by a declared comparability key with cross-partition pairs reported `incomparable`; drop-and-declare
missing inputs; `independence_group` from the producer (SC-4) replacing the retiring `confidence_*`
axis; the `WindowInput` adapter by `window_ref` (synthetic until Saṅgam persists the columns); a
**new** sidecar route; the composite retired through a **successor migration to 849** (which
sha-pins it); and the IP-4 honesty fix landed at every site that makes the claim. No table, no rows.
Decisions for the native: Q7, the split, the unread edges (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:157) | *"Comparison service and factor breakdown. P/I/Q: compare named outcomes/criteria, nearest/strongest/robust separately; self-test not consumer-value proof. DP08/17."* | the three-comparator obligation is already stated |
| Strategy §6.1 **L3-A04** (`:274`) | *"Preserve useful ranking kernel; add matched mechanism/context, nearest versus stronger/robust candidates, trade-offs, ties and incomparable states. Prove both pure behavior and accepted-window use."* | unchanged |
| Strategy **L3-Q02** (`:63`), **L3-Q05** (`:66`), §3 (`:97`) | *nearest, strongest under a named criterion, robust across declared variants and merely present remain distinct*; *no universal ranking* | the value frame |
| Strategy **L3-U04** (`:444`) | *"a stronger historical-only ladder cannot suppress a weaker future recurrence"* | binds §4.2 |
| Product §7.1 (`:270`) | *"'Strongest' is not an unexplained scalar"* | §3 |
| W0 register #19 (`:38,:648-654`) | `service ranking/compare/attention payloads`; rejects non-finite, duplicate or unqualified inputs | `:80` rejects unknown labels [V]; landed via `fa9857f00` (#2607) [R] — **not** `47131772b` |
| Lane D §14 / T1 Spine 9 | NOT-FOUND consumer; wrapper reads `kala_activation`; no `kala_tulana` table | confirmed [R]: callers outside `services/ka_tulana/` and tests = the probe, the writer shim, prose/registry references |
| Lane E §3.4 / §0.1 | wrapper SQL; `orb_strength` NULL on 669,964/672,551; composite computed nowhere in production; the top-750 is **all Mode C** (`:96-97`) | all confirmed [V]/[R]; the Mode-C fact is what makes `:61-62` the load-bearing defect (§3) |
| Saṅgam amendments item 9 (`:32`) | remove `confidence_score`/`confidence_label`; readers include `ka_tulana/writer.py`, `ranker.py` | this brief migrates Tulana off both (§4.4) |
| Migration **849** (`849_…tulana_health_probe.sql:78-104`) [R] | writes `asset_registry.health_probe` with `forensic_expected_composite_a: 0.795`, `_b: 0.4234`, `forensic_expected_decisive_factor: "proximity_factor"`; `routers/nirmana_probe.py:63-69,106-107` rejects any request whose `probe_contract_sha256` ≠ sha256(JCS(health_probe)); mirrored in `scripts/nirmana_probe_contracts.json`; `service_probes.py:804-811,847-848` assert those numbers | **the composite is pinned by an applied, sha-checked contract** — retiring it is a migration + contracts + probe packet, not "no migration" (§5) |
| Elevation plan Q7 (`:193`); Blueprint v5.0 §3.5 row 4 (`:320`), §9 Q7 (`:671`), §12.2 IP-4 (`:758`), §16.2 (`:902`) | three comparators; `criterion ∈ {nearest, strongest, robust}`; rename until the wrap is real | binds §4/§9 |
| `audit/_work/F2.md:126,140` [A] | a t2 `asset_frozen` tally for ka_tulana | inadmissible under t3; no `EVENTS.jsonl` row [R] |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V seed]
`asset_registry_seed.ts:2427-2441`: `storage_type: 'service'`, no table, `depends_on:
['ka_sangam', 'ka_vighnakara', 'ka_kala_darshana']` (`:2438`), `scope: 'per_chart'`, `asset_kind:
'service'`. Cost: unmeasured (pure in-memory; the data-bound cost is the producer's).

### 2.2 The code [V]/[R]
- **Writer** `writers/ka_tulana.py:1-19` → `WriterResult(rows_inserted=0)`; self-test in
  `services/ka_tulana/writer.py` (`:25-62`, raise `:119`; calls the kernel at `:55` on fixtures).
- **Kernel** `services/ka_tulana/ranker.py`:
  - `WindowInput` (`:129-143`): **required** `window_id, mode, peak_date`; `confidence_label`
    defaults `'speculative'` (`:135`); `rarity_years: Optional = None` (`:136`) [R].
  - `_validate_window_set` (`:288`) → `if window.mode not in {"A","B"}: raise ValueError`
    (`:61-62`) [R]; pinned by `test_w2_first_frontier_service_contracts.py:161` (`"unknown mode"`).
  - `I11_WEIGHTS = {convergence_score .40, rarity_years .25, confidence_score .20,
    proximity_factor .15}` (`:38-43`); `_CONFIDENCE_NUMERIC` (`:49`); unknown label rejected (`:80`).
  - `rarity_years is None → 0.5` (`:192-194`); `:222`'s `.get(…, 0.2)` is **unreachable** (`:80`
    raises first) — the 0.2 arrives through the `:135` default [R]; `_proximity_factor`
    (`:198-215`): past → 0.05 (`:207-208`); composite (`:222-229`); the rationale string
    **discloses** `(speculative, …)` and `~unknownyr cycle` (`:245`) while the composite uses
    0.2/0.5 — the number is invented, the narration is honest about it [R].
  - `rank_windows(..., reference_date=None)` *"Defaults to date.today()"* (`:268-281`);
    `compare` (`:307-388`) with `decisive_factor` = argmax of **unweighted** deltas (`:328-334`
    [R]: a rarity Δ0.5 (weight .25 → .125) beats a convergence Δ0.4 (weight .40 → .16) in the
    composite yet `decisive_factor` names rarity); `:365-366` computes labels never used (dead
    code; the verdict's label is set at `:384`) [R]; `attention_map` (`:390-428`).
- **The served "wrapper"** `call_service_wrappers.ts:672-730` (JOIN/WHERE `:707-714`):
  `computed_salience * COALESCE(orb_strength, 1.0) * (dignity-neutral ? 0.3 : 1.0)` over
  `bodha_msr_signals JOIN kala_activation`; `orb_strength_available` emitted (`:703-706`); the
  99.6% NULL figure is the comment at `:689` [A]. **No sidecar call**; **no sidecar route exists**
  for the kernel (`routers/*.py` grep → `nirmana_probe.py:24` only) [R].

### 2.3 Consumers (grep, all file types, excluding `services/ka_tulana/` and tests) [R]
| consumer | reads | role |
|---|---|---|
| `services/ka_tulana/writer.py:55` (every orchestrator build) | kernel on fixtures | probe |
| `routers/nirmana_probe.py:24,111` → `service_probes.py:655-846` (`:797,:844`) | kernel on fixtures; asserts 0.795 / 0.4234 / `proximity_factor` (`:804-811,847-848`) | probe (deployed, authenticated) |
| `kala_priority_get` / `kala_priority_ranking_get` | **claim** to wrap it — `call_service_wrappers.ts:10,524-535` (description `:525`), `priority.ts:8-10,329-331`, `register_p1_aliases.ts:1017,1022-1024`, `authority_basis_census_seed.ts:147-151`, `producer_editorial_review.ts:384-387`, `service_manifest.json:664-668`, `L3_kala/index.ts:27`, plus 5 generated projection files, `capability_knowledge.snapshot.json`, `capability_estate_census.json`, `mcp_surface_profiles.generated.ts` [R] | misnamed (the IP-4 blast radius) |

**Live-path statement.** No live path carries chart-derived inputs to the kernel; two live paths
exercise it on fixed fixtures. The misnamed surface is live. `WindowInput` *accepts* `rarity_years`
and `confidence_label`; `kala_activation` (migration `246_l3_ka_kalasutra.sql:3-33` [R]) carries
neither, so a wrap over it would run on the `:135`/`:192` defaults; `kala_convergence` carries them
but is 0 rows for the canonical chart [A] and is Mode C — refused (§3).

### 2.4 Epistemic class
| quantity | class | authority | note |
|---|---|---|---|
| `convergence_score` | engineered inference (Saṅgam) | `kala_convergence` | A/B ≤ 0.3805, C ≥ 0.70 [A: Lane E §0.1] — not one scale |
| `mode` | producer partition | `kala_convergence` (A/B/C/D) | the kernel admits A/B only |
| `rarity_years` | computed, unaudited, being retired | producer | 0.5 default invented |
| `confidence_label` | `icc/13` bucketed; retiring | producer | `'speculative'` default → 0.2 invented |
| `proximity_factor` | prioritisation term | kernel | makes past windows incomparable under "strongest" |
| composite | `INTERPRETIVE_INFERENCE` | kernel; **sha-pinned by 849** | the unexplained scalar |
| `decisive_factor` | explanation | kernel | the *concept* is valuable; the *computation* (unweighted argmax) misreports |

### 2.5 Ladders
`PLAN_REVIEWED`; pure tests pass (W2). t3: no event (`F2.md:126` t2 tally [A], inadmissible).

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Build a `WindowInput` from any real `kala_convergence` row for the canonical chart's top-750 (all Mode C) and call `rank_windows`: **`ValueError("unknown mode")`** at `:61-62` — the kernel cannot rank the producer's actual output. On the A/B fixtures it does accept, "is 2027 stronger than 2019?" (Q-K05) is decided 15% by *when it is asked* (past → 0.05) and `decisive_factor` names the largest unweighted delta, not the factor that moved the composite. Meanwhile "what matters most now?" is answered by L2 salience under an L3 name at ≥7 sites that say the surface wraps `ka_tulana` |
| Evidence | `ranker.py:61-62,288,135,192-194,207-208,222-229,328-334`; migration `360:12`; `engine.py:2115,2134,2201`; `call_service_wrappers.ts:525,672-730`; `service_manifest.json:664-668` — [V]/[R] |
| Expected contract | L3-Q02 / L3-A04 (*ties and incomparable states* — not refusal); Product §7.1; L3-U04; L3-Q05 (*non-comparable scales*); §N.7 item 6; Strategy §3; F28 |
| Defect class | **excluded at the door** (the producer's modes are refused) + **unserved** (no route, no consumer) + **wrong authority** (≥7 sites claim it) + **flattened** + **invented neutrality** + **wrong context** (`date.today()`) + **misreporting explanation** (unweighted argmax) |
| Impact | Q-K05 unanswerable; Q-K14 unserved; Q02's nearest-vs-stronger answered by nobody; a wrap built tomorrow over the real producer would crash |
| Non-claim | the kernel's ordering is engineered, not classical; no live incidence (no caller); the 99.6% and the 0-row figures are [A]; test outcomes are read, not run |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q02; Q05's comparability half; Q-K05, Q-K14. Not Q01/Q03/Q08.
2. **Three comparators, no composite (Q7).** `rank(windows, criterion, reference_instant)`:
   - `nearest` — future windows only (U04), ordered by `t_start` from `reference_instant`;
     `strength` beside, never mixed;
   - `strongest` — time-symmetric, proximity excluded; ordered by the producer's `activity` (R-6),
     then `declared_current_count` of `independence_group`, then `t_start` (once `rarity_years`
     retires) — **within one partition** (item 5);
   - `robust` — survives every declared variant; `completeness_state='unavailable'` until the
     producer supplies variants (Q09 upstream).
   `criterion` on every result; the I-11 composite survives as `legacy_composite` **and must keep
   producing 0.795 / 0.4234 / `proximity_factor` on the 849 fixture until the successor migration
   lands** (§5).
3. **Missing inputs declared, not invented.** `rarity_years=None` → factor dropped, ordering
   renormalised, `factors_available` lists what was used; the `:135` default is removed
   (`confidence_label` becomes required-or-absent, then retired under item 4).
4. **Independence in, confidence out (SC-4, amendment 9).** `WindowInput` gains
   `independence_group` + `comparable_with` and loses `confidence_*` — coordinated with Saṅgam
   behind the §6.2 sentinel (`ranker.py:49,80,135,222,384` read the label today).
5. **All modes admitted; partition key defined (F-15).** `:61-62` is replaced by: every mode is
   accepted; the **partition key** is `(mode, ayanamsha_id, node_convention, kernel_version)` from
   the producer row; `comparable_with` is computed **relative to the reference window** (the first
   candidate or the caller's `reference_window_ref`) under B2's relational enum — `self` for the
   same window, `same_convention_same_inputs` / `same_convention_newer_inputs` within one partition,
   `different_convention` across partitions; `compare` returns `incomparable` iff
   `comparable_with='different_convention'`; `rank` ranks within the reference partition and lists
   the rest under `coverage.exclusions` with reason `incomparable`.
6. **Ties, explanation (B2).** `compare` → `verdict ∈ {a, b, tie, incomparable}`; under
   `strongest`, `decisive_factor` = **the first differing key in the declared lexicographic order**
   (activity → independence count → t_start), `tie_on=[…]` when none differs — the unweighted
   argmax (`:328-334`) is retired with the composite; `epistemic_class='INTERPRETIVE_INFERENCE'`,
   `operator_role='relevance_navigation'` (`nearest`) / `'computation'` (`strongest`),
   `tier_basis='relative_uncalibrated'`.
7. **`WindowInput` adapter by `window_ref` (B3)** from `kala_convergence`: `t_start/t_end/t_peak`
   timestamptz (B1), `activity`, `valence`, `rarity_years` (until retired), `independence_group`,
   `comparable_with` inputs, `generation`, `mode`. **Spelling mapping declared (F-07):**
   `independence_groups` (Saṅgam brief) / `comparability_class` (stage3 `exposure.py:65-82`) →
   `independence_group` / `comparable_with` (binding). **None of these columns is persisted on any
   branch today** — every §7 row that consumes one runs on synthetic inputs until Saṅgam's merge
   gate lands them.
8. **Time discipline (SC-1).** `reference_instant` required, echoed; no `date.today()` (`:281`).
9. **Coverage (B5 shape).** `coverage = {requested_horizon, completed_horizon, resolution:
   'candidate_set', partitions_searched: [partition keys ranked], exclusions: [{window_ref, reason ∈
   {incomparable, missing_required_field, past_under_nearest}}], unsearched_regions: [], 
   completion_detector: 'all_supplied_candidates_classified'}`; `candidates_supplied/ranked` are
   asset-local counters beside it, not substitutes.
10. **IP-4 — split (F-02/F-04).** *Honesty now*: the wrap claim is removed at every site in §2.3
    (≥7 sources + regenerated projections; `may_touch` lists them; the description at
    `call_service_wrappers.ts:525` is inside the descriptor `:518-535`, not the SQL range) and the
    tool describes itself as `salience_by_date`. *Wrap later*: a **new** FastAPI route
    (`routers/tulana.py`) exposes `rank/compare/attention_map`; `kala_priority_ranking_get` calls it
    with adapter-built `WindowInput`s and names `criterion` — gated on `kala_convergence` rows and
    the DEMANDED columns.
11. **Old vs new.** Positive: 2019 vs 2027 under `strongest` → activity/independence decide.
    Negative: a Mode C window → **ranked** in its partition (today: `ValueError`); Mode A vs C pair →
    `incomparable` (today: `ValueError`). Boundary: equal activity → `tie`, `tie_on=['activity']`.
    Missing: no `rarity_years` → dropped, declared. Duplicated: one `independence_group` → not two.
    **Ordinary period (F-14):** two Mode-C windows, equal activity, equal independence count,
    different `t_start` → `strongest` orders by `t_start` with `decisive_factor='t_start'`, `nearest`
    identical — a quiet, non-dramatic result the walkthrough (§9) shows the consumer.
12. **Simpler baseline.** The I-11 composite (kernel) and the inline SQL (surface) — as they are.
13. **Ablation.** Under `strongest`, swap two windows' dates: today the composite flips; after, the
    verdict is invariant. For IP-4: remove the route call → the served ranking must change.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the `decisive_factor` **concept** and the per-factor delta report; `attention_map`;
  input validation for non-finite/duplicate (`:80`, `fa9857f00`); `legacy_composite` producing the
  849 fixture values until superseded.
- `ENRICH_CORRECT`: comparators; admitted modes + partition; declared missingness; ties;
  `reference_instant`; the lexicographic `decisive_factor`.
- `INTEGRATE`: the adapter; the new route; IP-4 (both halves).
- `RETIRE_AFTER_MIGRATION`: the I-11 composite, `confidence_*` inputs, `:61-62`, `:365-366` (dead).
- **Probe contract (F-03).** Migration 849 is applied and sha-pinned; retiring the composite
  requires: a **successor migration** re-writing `asset_registry.health_probe` with the new
  fixture expectations; `nirmana_probe_contracts.json` updated; `service_probes.py:655-846`
  rewritten; and the digest consumers re-pinned — one coordinated Pūrṇa packet. Until it lands,
  the probe asserts the legacy values and `legacy_composite` must satisfy them.
- **Tests that must flip (F-20):** `test_ka_tulana.py:212` (`_normalise_rarity(None) == 0.5`),
  `:114-133` (confidence semantics); `test_w2_first_frontier_service_contracts.py:160,184-200`
  (`"unknown mode"`); `test_service_probes.py`, `test_migration_849_*.py`,
  `test_nirmana_probe_route.py` (probe pins).
- **Fences**: reads `kala_convergence` only via the adapter; `kala_views/priority.ts` by packet;
  `register_d7_channel.ts` in amendment-9's radius; the `depends_on` edges are a **registry packet
  with its own owner** (out of scope here — §10.3).
- No table; one migration (the 849 successor) — **not** "no migration".

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_tulana`, L3 pure service; engineered comparison over producers' testimony; placement correct; `ENRICH_CORRECT + INTEGRATE (split)` |
| B | three declared edges, none read (pure); adapter makes `ka_sangam` real; `ka_vighnakara`/`ka_kala_darshana` decided by §10.3; T5 leaf |
| C | invariants: `strongest` invariant to `reference_instant`; `nearest` monotone in `t_start`; `incomparable` iff `different_convention`; every producer mode accepted; dropped factor renormalises consistently; `legacy_composite` = 849 fixture values. Golden: 849 fixture; property: shuffle invariance |
| D | the producer's gap (0 rows; DEMANDED columns persisted nowhere) |
| E | no chart-input consumer; two fixture paths; ≥7 misnaming sites |
| F | `criterion`, `decisive_factor`, `incomparable`, `factors_available`, `coverage` machine-readable |
| G | negligible; justified no-change |
| H | pure; idempotent |
| I | files in `may_touch`; W2 pure / W7 data; two coordinated packets (amendment 9; probe re-pin) |
| J | this brief; §7 with commands; both reports; IP-4 sentinel |

---

## §7 — Proof matrix (tier: `[P]` pure-synthetic today, `[D]` data-bound, gated on Saṅgam)

| proof | tier | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|
| Positive | P | `pytest tests/test_ka_tulana.py -k strongest_orders` — three synthetic Mode-A windows | activity → independence → t_start | shuffle-stable | order follows input order | `tests/test_ka_tulana.py` |
| Negative | P | Mode C window alone; Mode A vs C pair | **ranked** in partition; `incomparable` | never `ValueError` on a producer mode; never ranked across partitions | `ValueError` raised (today) or a cross-partition rank | same |
| Relevant influence | P | `declared_current_count` 1→3 on one window | moves up under `strongest`; others fixed | isolation | no movement / others move | same |
| Irrelevant control | P | swap dates under `strongest` | identical verdict | proximity absent | flips (today) | same |
| Duplication | P | two windows, one `independence_group` | `attention_map` counts one | dedup | counts two | same |
| Context | P | `rarity_years=None` | dropped; `factors_available` = 3; **no 0.5** | declared | 0.5 appears (today: `:212` asserts it) | same |
| Boundary | P | `reference_instant` = a `t_start` exactly; ordinary-period pair | included under `closed_open`; `tie`/`t_start`-decided | inclusivity; quiet result | wrong inclusion; a dramatic factor named | same |
| Delivery (IP-4) | D | fixture where window X is **last** under `legacy_composite` and **first** under `strongest`; served via the new route | `kala_priority_ranking_get` envelope shows X first with `decisive_factor` = the lexicographic key — a value the TS wrapper cannot produce without the kernel | kernel-only sentinel (B7) | X not first / `decisive_factor` absent | route test + MCP census |
| Revision | D | producer emits new `generation` | adapter re-reads | no cache | stale | adapter test |
| Value | D | frozen Q02/Q-K05 question | time-symmetric answer with a decisive key; baseline cannot | — | no distinction | baseline record |
| Evaluation | — | `not_applicable`: Tulana issues no claim of its own; evaluation belongs to the producer's windows | — | — | — | — |

Binding: **DEMANDS** B1 (`t_start/t_end/t_peak`), B2 (`comparable_with` inputs, R-6 `activity`),
B3 (`window_ref`, `generation`), B4 (`independence_group`, `declared_current_count`) — persisted
on **no branch today**; **OFFERS** B2 (`completeness_state`, `operator_role`, `tier_basis`,
`comparable_with` as computed), B5 (`coverage` in the seven-key shape), B7 (kernel-only sentinel).
**Asset-local fields (not binding vocabulary):** `criterion`, `verdict`, `tie_on`,
`decisive_factor`, `factors_available`, `legacy_composite`, `strength`, `candidates_supplied`,
`candidates_ranked`, `reference_window_ref`.

---

## §8 — Prioritization

(1) IP-4 honesty at every site (F28; enumerated) → (2) admit all modes + partition (the crash a
real wrap would hit) → (3) `strongest` time-symmetric + declared missingness + lexicographic
`decisive_factor` → (4) `independence_group` in / `confidence_*` out (Saṅgam-coordinated) → (5)
the 849-successor probe packet → (6) new route + adapter + wrap (waits on rows and columns) → (7)
`robust`. T5 leaf; W2 pure now, W7 data-bound.

---

## §9 — Disposition, target state, consumer walkthrough

`ENRICH_CORRECT` + `INTEGRATE` (split). Data-plane: `PRODUCER_READY` (pure) after the `[P]` rows;
`CONSUMER_INTEGRATED` when the new route is called from `main` with the kernel-only sentinel —
requires `kala_convergence` rows and the DEMANDED columns. Campaign: `ANALYZED → ENRICHED`.
Non-claims: `VALUE_EVALUATED` N; ordering engineered; no live ranking to compare against; every
`[D]` row is synthetic today.

**Walkthrough (experience 5, ordinary period).** The person asks in a quiet year: "which of my
next two windows matters more?" — two Mode-C windows, equal activity, one independence group each.
Served: `criterion='strongest'`, `verdict='tie'` on activity and independence, `decisive_factor=
't_start'`, `coverage.exclusions=[]`, `factors_available=['activity','independence','t_start']`.
The answer is "neither is stronger; the earlier one comes first" — no invented 0.5, no proximity
disguised as strength.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Q7 — three comparators; composite retired via the 849 successor** | yes |
| 2 | **IP-4 split: honesty at all sites now; wrap through a new route later** | yes — the wrap cannot land before a route, rows and columns exist |
| 3 | `ka_vighnakara` / `ka_kala_darshana` edges: read via the adapter (valence/obstruction into `strongest`) or drop by registry packet (own owner, out of this brief's scope) | **read**; if the adapter cannot, drop — never leave a declared edge unread |
| 4 | `strongest` secondary keys once `rarity_years` retires | activity → independence count → `t_start`; engineered, `relative_uncalibrated` |

---

## §11 — Not verified here

1. The 99.6% NULL figure (`:689` comment) and `kala_convergence` = 0 rows [A]; no DB.
2. Whether `origin/sangam/stage3` moved past local `90435d96a`.
3. Non-Git callers (notebooks, cron, external MCP clients).
4. Test outcomes — read from source, not run.
5. The t2 `asset_frozen` row exists only as the `F2.md` tally.

## §12 — Review dispositions (v1.0 → v1.1)

F-01 accepted (§0, §2.2, §3, §4.5, §4.11, §7 Negative); F-02 accepted (`may_touch` new route; §4.10
split; §10.2); F-03 accepted (§1 849 row, §5 probe packet, `must_not_touch`); F-04 accepted (§2.3,
§4.10, `may_touch`); F-05 accepted (§7 Delivery); F-06 accepted (§4.9); F-07 accepted (frontmatter,
§4.7, §7 tiers); F-08 accepted (§1); F-09 accepted (§0, §2.2); F-10 accepted (§0, §2.3); F-11
accepted (§2.2, §2.3); F-12 accepted (§2.4, §4.6, §5); F-13 accepted (§7 columns + Evaluation);
F-14 accepted (§4.11, §9); F-15 accepted (§4.5); F-16–F-19 accepted (citations); F-20 accepted (§5);
F-21 accepted (§5, §10.3, `must_not_touch`); F-22 accepted (frontmatter); asset-local fields listed (§7).
