---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_TULANA_ELEVATION_BRIEF
version: "1.2"
status: PROPOSED_FOR_NATIVE_RULING      # v1.0 REWORK (22) → v1.1 ACCEPT_WITH_CORRECTIONS (15 resolved, 7 partial, 15 new) → v1.2 folds all 15
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_tulana", "IP-4 (kala_priority_get / kala_priority_ranking_get honesty — enumerated blast radius)", "NEW sidecar route routers/tulana.py + its registration in main.py (stage 3)", "probe-contract successor to migration 849 — coordinated Pūrṇa packet", "L3-U04 (Kalasutra/Tulana → AHEAD/NOW)"]
goal_objective: "Make ka_tulana the layer's comparison authority in fact: three named comparators (nearest, strongest, robust) instead of one composite; every producer mode admitted and partitioned by a declared comparability key instead of Mode C/D refused at the door; missing inputs dropped and declared rather than defaulted; independence inherited from the producer — and a served surface that either calls it through a route that exists and is mounted, or stops claiming to, at every site that makes the claim."
source_revision: "9feac52d7 (l3/kala-layer-briefs); every cited code path checked identical at bf70a3477 and again at 27b0146f3 (2026-09-24)"
accepted_upstream_contract: "Saṅgam brief v1.5 / plan v1.0 typed testimony — DEMANDED, and persisted on NO branch today: sangam/stage3's ka_sangam.py INSERT column list (:990-999) is byte-identical to HEAD; stage3 exposure.py:65-82 still spells comparability_class; the Saṅgam brief spells independence_groups (SANGAM_ELEVATION_BRIEF_v1_0.md:184). W2 service input validation landed via fa9857f00 (#2607), not 47131772b (Avadhi/Yojaka only)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agents, fresh context; reports at briefs/reviews/REVIEW_KA_TULANA_v1_0.md (REWORK) and _v1_1.md (ACCEPT_WITH_CORRECTIONS)"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_tulana/{ranker,writer}.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_tulana.py", "platform/python-sidecar/routers/tulana.py (NEW at stage 3 — no sidecar route exposes the kernel today)", "platform/python-sidecar/main.py (ONE app.include_router line for the new route, mounted with prefix '/tulana' and dependencies=[Depends(verify_api_key)], the pattern at :37-108)", "platform/python-sidecar/tests/l3/test_ka_tulana.py, tests/l3/test_w2_first_frontier_service_contracts.py (tulana rows), tests/test_service_probes.py, tests/test_nirmana_probe_route.py, tests/test_migration_849_tulana_health_probe.py (retire/mark-historical + author its successor)", "pipeline/orchestrator/service_probes.py:655-846 (ka_tulana clause) + platform/python-sidecar/scripts/nirmana_probe_contracts.json + one NEW migration re-pinning asset_registry.health_probe (successor to 849) — coordinated Pūrṇa packet"]
interface_packet_targets_not_may_touch: ["IP-4 (Pūrṇa-owned; L3 owns only the sentinel test): platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:10,518-535,672-730; platform-mcp/src/tools/kala_views/priority.ts:8-10,329-331; register_p1_aliases.ts:1017,1022-1024; authority_basis_census_seed.ts:147-151; producer_editorial_review.ts:384-387; service_manifest.json:664-668; L3_kala/index.ts:27; the 7 regenerated files under platform/src/generated/projections/, capability_knowledge.snapshot.json, harvest/e1_declared.json and platform-mcp/src/generated/mcp_surface_profiles.generated.ts"]
must_not_touch: ["kala_convergence / ka_sangam (producer; Saṅgam packet)", "kala_activation / ka_kalasutra (the table the wrapper reads today; Kalasutra brief)", "platform-mcp/src/tools/kala_views/**", "register_d7_channel.ts (Saṅgam amendment-9 blast radius; coordinated)", "asset_registry_seed.ts:2438 depends_on edges (registry packet, own owner — §10.3)", ".github/workflows/deploy.yml", "applied migrations (849 is applied and sha-pinned; it is superseded by a new migration, never edited)", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY for the pure comparators (stage 3, DB-free, synthetic inputs); CONSUMER_INTEGRATED when a served surface calls the mounted route with real WindowInputs and the L3 sentinel passes; data-bound acceptance W7 — gated on Saṅgam persisting the DEMANDED columns"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; no t3 freeze event today (a superseded t2 tally — audit/_work/F2.md:126 [A] — is inadmissible)"
wave: "W2 pure / W7 data-bound"
shape: single asset, pure service
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted here are marked [R]; Lane D
  §14, T1 Spine item 9, Lane E §3.4 / §0.1 / §1 Q-K05/K14, Saṅgam amendment 9 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.2 (2026-09-24): v1.1 re-review dispositions (15 findings) — N-01 main.py added to may_touch (a router module is inert until mounted); N-02 §8 reordered so the 849-successor packet lands before or atomically with the confidence_* retirement, because legacy_composite cannot produce the pinned 0.795 without confidence_label, and the writer self-test that runs on EVERY build consumes it too; N-03 the Delivery sentinel re-specified — decisive_factor is reproducible by the wrapper in SQL, so the detector becomes call-evidence + a kernel-only receipt + the F28 ablation, and 'MCP census' is dropped as evidence; N-04 two may_touch paths corrected (scripts/ under python-sidecar; tests/l3/); N-05 the partition key's three columns declared DEMANDED (they exist on no branch), the same/newer split defined, and the comparable_with DEMAND/OFFER overload resolved by renaming the pairwise verdict; N-06 F24 verdict tiers added as their own column with the input-boundary axis kept separate and per-row commands; N-07 the 849 test cannot 'flip' — retire/mark-historical + successor; N-08 the writer self-test added to the must-flip list; N-09 the IP-4 blast radius corrected to 7 projection files + snapshot + e1_declared.json + the .ts profile, with capability_estate_census.json moved to the probe packet; N-10/N-11 line numbers; N-12 'Execution Brief §7 Delivery sentinel'; N-13 'no freeze row'; N-14 the producer's own RRV-03 ordering key named beside strongest's; N-15 source_revision phrasing."
  - "1.1 (2026-09-24): v1.0 REWORK dispositions (22 findings) — see §12."
  - "1.0 (2026-09-24): first issue."
---

# `ka_tulana` elevation brief — comparison under a named criterion

## §0 — The recommendation, in one paragraph

`ka_tulana` is a built, tested comparison kernel — `rank_windows`, `compare` with a named decisive
factor, `attention_map` (`ranker.py:268,307,390` [V]) — that **no production surface calls with
chart-derived inputs**: its two live paths are the writer self-test
(`services/ka_tulana/writer.py:25-62`, run on every orchestrator build, raising at `:119` [R]) and
the deployed health probe (`routers/nirmana_probe.py:24,111` → `service_probes.py:797,844` [R]),
both on fixed fixtures. The surface that says it wraps it, `kala_priority_get`, is inline SQL ranking
L2 `computed_salience` × an orb term NULL on 99.6% of rows, joined to `kala_activation` for a date
filter (`call_service_wrappers.ts:672-730` [R]); `service_manifest.json:664-668` says so in as many
words (*"Direct Postgres query … NOT a sidecar HTTP call"* [R]), and **no sidecar route exposes the
kernel** (grep over `routers/*.py`: only the fixed-fixture probe [R]). The kernel itself is one
composite (40/25/20/15) over four axes not on one scale, with a proximity term flooring every past
window at 0.05 (`:207-208`), an invented rarity of 0.5 (`:192-194`), a `confidence_label` that
**defaults to `'speculative'`** at the dataclass (`:135` [R]) → 0.2 — and, decisively, it **refuses
every Mode C or D window at the door** (`if window.mode not in {"A","B"}: raise ValueError`,
`:61-62`, via `_validate_window_set` `:288` [R]) while `kala_convergence.mode` has held `'C'` since
migration 360 dropped the CHECK (`360_kala_convergence_mode_c.sql:12` [R]) and Saṅgam emits `'C'`/`'D'`
(`engine.py:2115,2134,2201` [R]) — so a correct adapter over the real producer would be rejected for
the whole top-750. Recommendation: **`ENRICH_CORRECT` + `INTEGRATE` (split: honesty now, wrap
later)** — three **named comparators** (Q7); **all modes admitted** and partitioned by a declared
comparability key with cross-partition pairs reported `incomparable`; drop-and-declare missing
inputs; `independence_group` from the producer (SC-4) replacing the retiring `confidence_*` axis; the
`WindowInput` adapter by `window_ref` (synthetic until Saṅgam persists the columns); a **new, mounted**
sidecar route; the composite retired through a **successor migration to 849** (which sha-pins it,
and whose fixture `legacy_composite` must keep satisfying until then); and the IP-4 honesty fix
landed at every site that makes the claim. No table, no rows. Decisions: Q7, the split, the unread
edges (§10).

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
| Lane D §14 / T1 Spine 9 | NOT-FOUND consumer; wrapper reads `kala_activation`; no `kala_tulana` table | confirmed [R] |
| Lane E §3.4 / §0.1 | wrapper SQL; `orb_strength` NULL on 669,964/672,551; composite computed nowhere in production; the top-750 is **all Mode C** (`:96-97`) | all confirmed [V]/[R]; the Mode-C fact is what makes `:61-62` the load-bearing defect (§3) |
| Saṅgam amendments item 9 (`:32`) | remove `confidence_score`/`confidence_label`; readers include `ka_tulana/writer.py`, `ranker.py` | this brief migrates Tulana off both (§4.4) — **after** the probe packet (§8, N-02) |
| **Saṅgam plan RRV-03** (`SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md:193,:442`) [R] | the producer's own within-class ordering key is **`activity DESC, contact instant ASC`**, with independence carried as data and never pooled into the key | named beside `strongest`'s key in §10.4 (N-14) — the native decides with both in view |
| Migration **849** (`849_…tulana_health_probe.sql:78-104`) [R] | writes `asset_registry.health_probe` with `forensic_expected_composite_a: 0.795`, `_b: 0.4234`, `forensic_expected_decisive_factor: "proximity_factor"`; `routers/nirmana_probe.py:63-69,106-107` rejects any request whose `probe_contract_sha256` ≠ sha256(JCS(health_probe)); mirrored in `platform/python-sidecar/scripts/nirmana_probe_contracts.json`; `service_probes.py:804-811,847-848` assert those numbers | **the composite is pinned by an applied, sha-checked contract**, and 0.795 = 0.40·0.8 + 0.25·0.5 + **0.20·1.0** + 0.15·1.0 — its third term is `confidence_label` (N-02) |
| Migration **933** (`933_…selftest_shape_contracts.sql:135-151`) [R] | `ka_tulana`'s `integrity_check_sql` is **shape-only** (`selftest_detail` non-empty object); it does not pin the detail's keys | the writer self-test may be rewritten without a further migration (N-08) |
| Elevation plan Q7 (`:193`); Blueprint v5.0 §3.5 row 4 (`:320`), §9 Q7 (`:671`), §12.2 IP-4 (`:758`), §16.2 (`:902`) | three comparators; `criterion ∈ {nearest, strongest, robust}`; rename until the wrap is real | binds §4/§9 |
| `audit/_work/F2.md:126,140` [A] | a t2 `asset_frozen` tally for ka_tulana | inadmissible under t3; **no freeze row in `EVENTS.jsonl`** (one non-freeze row names the asset) [R] |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`asset_registry_seed.ts:2427-2441`: `storage_type: 'service'`, no table, `depends_on: ['ka_sangam',
'ka_vighnakara', 'ka_kala_darshana']` (`:2438`), `scope: 'per_chart'`, `asset_kind: 'service'`.
Cost: unmeasured (pure in-memory; the data-bound cost is the producer's).

### 2.2 The code [V]/[R]
- **Writer** `writers/ka_tulana.py:1-19` → `WriterResult(rows_inserted=0)`; self-test in
  `services/ka_tulana/writer.py:25-62`, which constructs two `WindowInput`s **with
  `confidence_label` and `rarity_years`**, calls the kernel at `:55`, asserts rank order at `:55-56`
  and raises at `:119` — **on every orchestrator build** (N-08).
- **Kernel** `services/ka_tulana/ranker.py`:
  - `WindowInput` (`:129-143`): **required** `window_id, mode, peak_date`; `confidence_label`
    defaults `'speculative'` (`:135`); `rarity_years: Optional = None` (`:136`) [R].
  - `_validate_window_set` (`:288`) → `if window.mode not in {"A","B"}: raise ValueError` (`:61-62`)
    [R]; pinned by `test_w2_first_frontier_service_contracts.py:161` (`"unknown mode"`; `:160` is the
    label case — N-11).
  - `I11_WEIGHTS = {convergence_score .40, rarity_years .25, confidence_score .20, proximity_factor
    .15}` (`:38-43`); `_CONFIDENCE_NUMERIC` (`:49`); unknown label rejected (`:80`).
  - `rarity_years is None → 0.5` (`:192-194`); `:222`'s `.get(…, 0.2)` is **unreachable** (`:80`
    raises first) — the 0.2 arrives through the `:135` default [R]; `_proximity_factor` (`:198-215`):
    past → 0.05 (`:207-208`); composite (`:222-229`); the rationale string **discloses**
    `(speculative, …)` and `~unknownyr cycle` (`:245`) while the composite uses 0.2/0.5 — the number
    is invented, the narration is honest about it [R].
  - `rank_windows` / `compare` / `attention_map` each default `reference_date` to `date.today()` at
    **`:287`, `:319`, `:402`** (`:281` is the docstring — N-10); `compare` (`:307-388`) with
    `decisive_factor` = argmax of **unweighted** deltas (`:328-334` [R]: a rarity Δ0.5 (weight .25 →
    .125) beats a convergence Δ0.4 (weight .40 → .16) in the composite yet `decisive_factor` names
    rarity); `:365-366` computes labels never used (dead code; the verdict's label is set at `:384`)
    [R]; `attention_map` (`:390-428`).
- **The served "wrapper"** `call_service_wrappers.ts:672-730` (JOIN/WHERE `:707-714`):
  `computed_salience * COALESCE(orb_strength, 1.0) * (dignity-neutral ? 0.3 : 1.0)` over
  `bodha_msr_signals JOIN kala_activation`; `orb_strength_available` emitted (`:703-706`); the 99.6%
  NULL figure is the comment at `:689` [A]. **No sidecar call**; **no sidecar route exists** for the
  kernel (`routers/*.py` grep → `nirmana_probe.py:24` only), and a router module is inert until
  mounted in `main.py` (`app.include_router(...)`, the pattern at `:37-108`) — N-01.

### 2.3 Consumers (grep, all file types, excluding `services/ka_tulana/` and tests) [R]
| consumer | reads | role |
|---|---|---|
| `services/ka_tulana/writer.py:25-62` (every orchestrator build) | kernel on fixtures, **with `confidence_label`** | probe |
| `routers/nirmana_probe.py:24,111` → `service_probes.py:655-846` (`:797,:844`) | kernel on fixtures; asserts 0.795 / 0.4234 / `proximity_factor` (`:804-811,847-848`) | probe (deployed, authenticated) |
| `kala_priority_get` / `kala_priority_ranking_get` | **claim** to wrap it — `call_service_wrappers.ts:10,524-535` (description `:525`), `priority.ts:8-10,329-331`, `register_p1_aliases.ts:1017,1022-1024`, `authority_basis_census_seed.ts:147-151`, `producer_editorial_review.ts:384-387`, `service_manifest.json:664-668`, `L3_kala/index.ts:27`, plus **7** generated files under `platform/src/generated/projections/`, `capability_knowledge.snapshot.json`, `harvest/e1_declared.json` and `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` [R] (N-09) | misnamed (the IP-4 blast radius) |
| `capability_estate_census.json` | carries the **probe-contract digest** (`generate_capability_estate_census.ts:728,870`), not the wrap claim | regenerates with the **probe packet**, not IP-4 (N-09) |

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
| `confidence_label` | `icc/13` bucketed; retiring | producer | `'speculative'` default → 0.2 invented; **and the 849 fixture's third term** |
| `proximity_factor` | prioritisation term | kernel | makes past windows incomparable under "strongest" |
| composite | `INTERPRETIVE_INFERENCE` | kernel; **sha-pinned by 849** | the unexplained scalar |
| `decisive_factor` | explanation | kernel | the *concept* is valuable; the *computation* (unweighted argmax) misreports |

### 2.5 Ladders
`PLAN_REVIEWED`; pure tests pass (W2). t3: no freeze row (`F2.md:126` t2 tally [A], inadmissible).

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Build a `WindowInput` from any real `kala_convergence` row for the canonical chart's top-750 (all Mode C) and call `rank_windows`: **`ValueError("unknown mode")`** at `:61-62` — the kernel cannot rank the producer's actual output. On the A/B fixtures it does accept, "is 2027 stronger than 2019?" (Q-K05) is decided 15% by *when it is asked* (past → 0.05) and `decisive_factor` names the largest unweighted delta, not the factor that moved the composite. Meanwhile "what matters most now?" is answered by L2 salience under an L3 name at ≥7 source sites plus regenerated projections |
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
   producing 0.795 / 0.4234 / `proximity_factor` on the 849 fixture — which means it keeps reading
   `confidence_label` — until the successor migration lands** (§5, §8; N-02).
3. **Missing inputs declared, not invented.** `rarity_years=None` → factor dropped, ordering
   renormalised, `factors_available` lists what was used. The `:135` `'speculative'` default is
   removed **in the same commit as the probe successor**, not before.
4. **Independence in, confidence out (SC-4, amendment 9).** `WindowInput` gains `independence_group`
   + the partition inputs and loses `confidence_*` — coordinated with Saṅgam behind the Execution
   Brief §7 Delivery sentinel (N-12), and **sequenced after** the 849 successor (§8).
5. **All modes admitted; partition key defined and DEMANDED (N-05).** `:61-62` is replaced by:
   every mode is accepted; the **partition key** is `(mode, ayanamsha_id, node_convention,
   kernel_version)`. Of those four, **only `mode` exists on `kala_convergence` today** — `ayanamsha_id`
   is a proposed Saṅgam column (`SANGAM_ELEVATION_BRIEF_v1_0.md:147,:208`), `kernel_version` is
   proposed by plan R-6 (`:193`, legacy rows `legacy_i16`), and `node_convention` is a column nowhere
   (binding B6 names the convention, not a field; it may instead be **derived from
   `kernel_version`**). All three are therefore **DEMANDED producer columns** (§7), and every proof
   row that consumes one is marked synthetic.
   **`comparable_with` is consumed, not re-emitted under the same name:** the producer's
   `comparable_with` (B2's relational enum) is an input; this kernel's pairwise verdict is emitted as
   the asset-local **`pair_comparability`**, so one binding name never carries two reference frames.
   The split within a partition: same `generation` → `same_convention_same_inputs`; differing
   `generation` → `same_convention_newer_inputs`; across partitions → `different_convention`, and
   `compare` returns `incomparable` exactly then. `rank` ranks within the reference partition and
   lists the rest under `coverage.exclusions` with reason `incomparable`.
6. **Ties, explanation (B2).** `compare` → `verdict ∈ {a, b, tie, incomparable}`; under `strongest`,
   `decisive_factor` = **the first differing key in the declared lexicographic order** (activity →
   independence count → t_start), `tie_on=[…]` when none differs — the unweighted argmax
   (`:328-334`) is retired with the composite; `epistemic_class='INTERPRETIVE_INFERENCE'`,
   `operator_role='relevance_navigation'` (`nearest`) / `'computation'` (`strongest`),
   `tier_basis='relative_uncalibrated'`.
7. **`WindowInput` adapter by `window_ref` (B3)** from `kala_convergence`: `t_start/t_end/t_peak`
   timestamptz (B1), `activity`, `valence`, `rarity_years` (until retired), `independence_group`,
   the partition inputs, `generation`, `mode`. **Spelling mapping declared:** `independence_groups`
   (Saṅgam brief) / `comparability_class` (stage3 `exposure.py:65-82`) → `independence_group` /
   `comparable_with` (binding). **None of these columns is persisted on any branch today.**
8. **Time discipline (SC-1).** `reference_instant` required, echoed; no `date.today()` (`:287,:319,
   :402`). It is an **asset-local input**, not a B1 field name (§7).
9. **Coverage (B5 shape).** `coverage = {requested_horizon, completed_horizon, resolution:
   'candidate_set', partitions_searched: [partition keys ranked], exclusions: [{window_ref, reason ∈
   {incomparable, missing_required_field, past_under_nearest}}], unsearched_regions: [],
   completion_detector: 'all_supplied_candidates_classified'}`; `candidates_supplied/ranked` are
   asset-local counters beside it.
10. **IP-4 — split.** *Honesty now*: the wrap claim is removed at every site in §2.3 (≥7 sources +
    the regenerated files enumerated there; the description at `call_service_wrappers.ts:525` sits
    inside the descriptor `:518-535`, not the SQL range) and the tool describes itself as
    `salience_by_date`. *Wrap later*: a **new** FastAPI route (`routers/tulana.py`) **mounted in
    `main.py`** exposes `rank/compare/attention_map`; `kala_priority_ranking_get` calls it with
    adapter-built `WindowInput`s and names `criterion` — gated on `kala_convergence` rows and the
    DEMANDED columns.
11. **Old vs new.** Positive: 2019 vs 2027 under `strongest` → activity/independence decide.
    Negative: a Mode C window → **ranked** in its partition (today: `ValueError`); Mode A vs C pair →
    `incomparable` (today: `ValueError`). Boundary: equal activity → `tie`, `tie_on=['activity']`.
    Missing: no `rarity_years` → dropped, declared. Duplicated: one `independence_group` → not two.
    **Ordinary period:** two Mode-C windows, equal activity, equal independence count, different
    `t_start` → `strongest` orders by `t_start` with `decisive_factor='t_start'`, `nearest` identical.
12. **Simpler baseline.** The I-11 composite (kernel) and the inline SQL (surface) — as they are.
13. **Ablation.** Under `strongest`, swap two windows' dates: today the composite flips; after, the
    verdict is invariant. For IP-4: remove the route call → the served ranking must change.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the `decisive_factor` **concept** and the per-factor delta report; `attention_map`;
  input validation for non-finite/duplicate (`:80`, `fa9857f00`); `legacy_composite` producing the
  849 fixture values — **including its `confidence_label` term** — until superseded.
- `ENRICH_CORRECT`: comparators; admitted modes + partition; declared missingness; ties;
  `reference_instant`; the lexicographic `decisive_factor`.
- `INTEGRATE`: the adapter; the new **mounted** route; IP-4 (both halves).
- `RETIRE_AFTER_MIGRATION`: the I-11 composite, `confidence_*` inputs, `:61-62`, `:365-366` (dead).
- **Probe contract (sequencing, N-02).** Migration 849 is applied and sha-pinned; retiring the
  composite requires, **in one packet**: a successor migration re-writing `asset_registry.health_probe`
  with the new fixture expectations; `platform/python-sidecar/scripts/nirmana_probe_contracts.json`
  updated; `service_probes.py:655-846` rewritten; the digest consumers and
  `capability_estate_census.json` regenerated; and
  `tests/test_migration_849_tulana_health_probe.py` **retired or marked historical** — it cannot
  "flip", because it reads the applied 849 file itself (`:47-49`), asserts
  `contract.keys() >= _TULANA_REQUIRED_FIELDS` (`:89`) and, under `@integration`, round-trips 849 to
  GREEN (`:123-129`) — with a successor test authored on the same two-layer convention (N-07).
  Until that packet lands, the probe asserts the legacy values and `legacy_composite` must satisfy
  them.
- **Tests that must flip:** `tests/l3/test_ka_tulana.py:212` (`_normalise_rarity(None) == 0.5`),
  `:114-133` (confidence semantics); `test_w2_first_frontier_service_contracts.py:160-161` (label +
  mode), `:184-200` (composite pins); `test_service_probes.py`, `test_nirmana_probe_route.py`; and
  **`services/ka_tulana/writer.py:25-62`**, the every-build self-test fixture, which consumes
  `confidence_label` and `rarity_years` — migration 933's contract is **shape-only** (`:135-151`), so
  rewriting it needs no further migration (N-08).
- **Fences**: reads `kala_convergence` only via the adapter; `kala_views/priority.ts` by packet;
  `register_d7_channel.ts` in amendment-9's radius; the `depends_on` edges are a **registry packet
  with its own owner** (§10.3).
- No table; one migration (the 849 successor).

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_tulana`, L3 pure service; engineered comparison over producers' testimony; placement correct; `ENRICH_CORRECT + INTEGRATE (split)` |
| B | three declared edges, none read (pure); adapter makes `ka_sangam` real; `ka_vighnakara`/`ka_kala_darshana` decided by §10.3; T5 leaf |
| C | invariants: `strongest` invariant to `reference_instant`; `nearest` monotone in `t_start`; `incomparable` iff `different_convention`; every producer mode accepted; dropped factor renormalises consistently; `legacy_composite` = 849 fixture values until superseded. Golden: 849 fixture; property: shuffle invariance |
| D | the producer's gap (0 rows; DEMANDED columns persisted nowhere) |
| E | no chart-input consumer; two fixture paths; ≥7 misnaming sites |
| F | `criterion`, `decisive_factor`, `pair_comparability`, `factors_available`, `coverage` machine-readable |
| G | negligible; justified no-change |
| H | pure; idempotent |
| I | files in `may_touch` (incl. the one `main.py` mount line); W2 pure / W7 data; two coordinated packets (amendment 9; probe successor) |
| J | this brief; §7 with commands; three reports; IP-4 sentinel |

---

## §7 — Proof matrix

Columns: **verdict tier** is F24's (`COMPUTATIONAL_CORRECTNESS` / `EXPLANATORY_DISCRIMINATIVE_VALUE`
/ `EMPIRICAL_OUTCOME_PERFORMANCE`); **inputs** is the separate data-boundedness axis — `[P]`
pure/synthetic, runnable today; `[D]` data-bound, gated on Saṅgam persisting the DEMANDED columns.

| proof | verdict tier | inputs | command / fixture | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | [P] | `pytest tests/l3/test_ka_tulana.py -k strongest_orders` — three synthetic Mode-A windows | activity → independence → t_start | shuffle-stable | order follows input order | `tests/l3/test_ka_tulana.py` |
| Negative | COMPUTATIONAL_CORRECTNESS | [P] | `pytest tests/l3/test_ka_tulana.py -k mode_c_ranked` — Mode C alone; Mode A vs C pair | **ranked** in partition; `incomparable` | never `ValueError` on a producer mode; never a cross-partition rank | `ValueError` (today) or a cross-partition rank | same |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | [P] | `-k independence_moves_rank` — `declared_current_count` 1→3 | moves up under `strongest`; others fixed | isolation | no movement / others move | same |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | [P] | `-k date_swap_invariant` — swap dates under `strongest` | identical verdict | proximity absent | flips (today) | same |
| Duplication | COMPUTATIONAL_CORRECTNESS | [P] | `-k attention_map_dedup` — two windows, one `independence_group` | counted once | dedup | counted twice | same |
| Context | COMPUTATIONAL_CORRECTNESS | [P] | `-k rarity_none_dropped` — `rarity_years=None` | dropped; `factors_available` = 3; **no 0.5** | declared | 0.5 appears (today `:212` asserts it) | same |
| Boundary | COMPUTATIONAL_CORRECTNESS | [P] | `-k reference_instant_inclusive` — `reference_instant` = a `t_start`; ordinary-period pair | included under `closed_open`; `tie`/`t_start`-decided | inclusivity; quiet result | wrong inclusion; a dramatic factor named | same |
| Delivery (IP-4) — **call evidence** | COMPUTATIONAL_CORRECTNESS | [P] | route test with `PYTHON_SIDECAR_URL` mocked: assert the sidecar received the `WindowInput` payload (the pattern the muhurat/transit wrappers are testable under) | the wrapper **called** the route | the surface uses the kernel | no request observed | capability/route test |
| Delivery (IP-4) — **kernel receipt** | COMPUTATIONAL_CORRECTNESS | [D] | envelope carries `kernel_receipt = {kernel_version, request_digest}` where `request_digest = sha256` over the canonicalised inputs **+ `kernel_version`**, computed only in `ranker.py` (a TS copy would be a §N.7-item-3 shadowing constant) | receipt present and matches a re-computation in the test | a value the wrapper cannot synthesise | absent or reproducible by the wrapper | route test |
| Delivery (IP-4) — **ablation** | EXPLANATORY_DISCRIMINATIVE_VALUE | [D] | remove the route call; re-run the same question | the served order changes | F28 | order unchanged (the surface never used it) | baseline record |
| Revision | COMPUTATIONAL_CORRECTNESS | [D] | producer emits a new `generation` | adapter re-reads; partition split reports `same_convention_newer_inputs` | no cache | stale | adapter test |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | [D] | frozen Q02/Q-K05 question | time-symmetric answer with a decisive key; baseline cannot | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable`: Tulana issues no claim of its own; evaluation belongs to the producer's windows | — | — | — | — |

Binding: **DEMANDS** B1 (`t_start/t_end/t_peak`), B2 (`comparable_with` as an **input**, R-6
`activity`), B3 (`window_ref`, `generation`), B4 (`independence_group`, `declared_current_count`),
**and the three partition columns `ayanamsha_id`, `kernel_version`, `node_convention` (or its
derivation from `kernel_version`)** — none persisted on any branch today. **OFFERS** B2
(`completeness_state`, `operator_role`, `tier_basis`), B5 (`coverage`, seven keys), B7 (the
kernel-receipt sentinel). **Asset-local (not binding vocabulary):** `criterion`, `verdict`,
`pair_comparability`, `tie_on`, `decisive_factor`, `factors_available`, `legacy_composite`,
`strength`, `candidates_supplied`, `candidates_ranked`, `reference_window_ref`, `reference_instant`,
`kernel_receipt`.

---

## §8 — Prioritization (sequencing is load-bearing — N-02)

(1) IP-4 honesty at every site (F28; enumerated) → (2) admit all modes + partition (the crash a real
wrap would hit; does not touch `confidence_*`) → (3) `strongest` time-symmetric + declared
missingness + lexicographic `decisive_factor` → (4) **the 849-successor probe packet** (successor
migration + contracts JSON + probe rewrite + digest/census regeneration + 849-test retirement) →
(5) `independence_group` in / `confidence_*` out and the `:135` default removed, **in or after the
same commit as (4)**, because until then `legacy_composite` and the every-build writer self-test both
need `confidence_label` → (6) new mounted route + adapter + wrap (waits on rows and columns) →
(7) `robust`. T5 leaf; W2 pure now, W7 data-bound.

---

## §9 — Disposition, target state, consumer walkthrough

`ENRICH_CORRECT` + `INTEGRATE` (split). Data-plane: `PRODUCER_READY` (pure) after the `[P]` rows;
`CONSUMER_INTEGRATED` when the mounted route is called from `main` with the call-evidence and
kernel-receipt sentinels — requires `kala_convergence` rows and the DEMANDED columns. Campaign:
`ANALYZED → ENRICHED`. Non-claims: `VALUE_EVALUATED` N; ordering engineered; no live ranking to
compare against; every `[D]` row is synthetic today.

**Walkthrough (experience 5, ordinary period).** The person asks in a quiet year: "which of my next
two windows matters more?" — two Mode-C windows, equal activity, one independence group each.
Served: `criterion='strongest'`, `verdict='tie'` on activity and independence, `decisive_factor=
't_start'`, `coverage.exclusions=[]`, `factors_available=['activity','independence','t_start']`. The
answer is "neither is stronger; the earlier one comes first" — no invented 0.5, no proximity
disguised as strength.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Q7 — three comparators; composite retired via the 849 successor** | yes |
| 2 | **IP-4 split: honesty at all sites now; wrap through a new, mounted route later** | yes — the wrap cannot land before a route, its `main.py` mount, rows and columns exist |
| 3 | `ka_vighnakara` / `ka_kala_darshana` edges: read via the adapter (valence/obstruction into `strongest`) or drop by registry packet (own owner, out of scope here) | **read**; if the adapter cannot, drop — never leave a declared edge unread |
| 4 | **`strongest`'s secondary keys — and how they sit beside the producer's own RRV-03 key.** Tulana proposes activity → independence count → `t_start`; the producer's declared within-class order (RRV-03) is `activity DESC, contact instant ASC`, with independence carried as data and **not** pooled into the key | adopt Tulana's for the *comparator* (it is a comparison, not the producer's projection order) and record the difference explicitly, so a reader never sees two orders without knowing why |

---

## §11 — Not verified here

1. The 99.6% NULL figure (`:689` comment) and `kala_convergence` = 0 rows [A]; no DB.
2. Whether `origin/sangam/stage3` moved past local `90435d96a`.
3. Non-Git callers (notebooks, cron, external MCP clients).
4. Test outcomes — read from source, not run.
5. The t2 `asset_frozen` row exists only as the `F2.md` tally.
6. **Whether the frozen writer-digest set (`platform/src/generated/nirmana-writer-digests.json`,
   consumed by `dispatch_frozen_rebuild.py:58` and `generate_capability_estate_census.ts:868-869`)
   hashes `services/ka_tulana/ranker.py`.** If it does, editing the kernel invalidates that digest
   and the census must regenerate — a blast-radius item to settle at source before stage 3; if it
   does not, no action. Stated, not asserted.

## §12 — Review dispositions

**v1.0 → v1.1 (22 findings).** 15 resolved, 7 partial — F-01 (§0, §2.2, §3, §4.5, §4.11, §7
Negative); F-02 (`may_touch` new route; §4.10 split; §10.2); F-03 (§1 849 row, §5 probe packet);
F-04 (§2.3, §4.10, `may_touch`); F-05 (§7 Delivery); F-06 (§4.9); F-07 (frontmatter, §4.7, §7 tiers);
F-08 (§1); F-09 (§0, §2.2); F-10 (§0, §2.3); F-11 (§2.2, §2.3); F-12 (§2.4, §4.6, §5); F-13 (§7);
F-14 (§4.11, §9); F-15 (§4.5); F-16–F-19 (citations); F-20 (§5); F-21 (§5, §10.3); F-22 (frontmatter).

**v1.1 → v1.2 (15 findings, all accepted).** N-01 (`may_touch` + §2.2 — `main.py` mount); N-02 (§1
849 row arithmetic, §2.3, §2.4, §4.2, §4.3, §5, §8 resequenced); N-03 (§7 three Delivery rows:
call-evidence, kernel receipt, ablation; "MCP census" dropped); N-04 (`may_touch`, §1, §5, §7 paths);
N-05 (§4.5 — three DEMANDED columns, the same/newer split, `pair_comparability`; §7 DEMANDS);
N-06 (§7 verdict-tier + inputs columns + per-row commands); N-07 (§5 — 849 test retired, successor
authored); N-08 (§2.2, §2.3, §5 — the every-build self-test; migration 933 is shape-only); N-09
(§2.3, `interface_packet_targets`, §4.10 — 7 projection files + snapshot + `e1_declared.json` + the
`.ts` profile; census moved to the probe packet); N-10 (`:287,:319,:402`); N-11 (`:160-161`,
`:184-200`); N-12 ("Execution Brief §7 Delivery sentinel"); N-13 (§1, §2.5 — "no freeze row");
N-14 (§1 RRV-03 row, §10.4); N-15 (`source_revision`). Also: `reference_instant` listed asset-local
(§7); the writer-digest question recorded as unverified (§11.6).
