---
artifact: SANGAM_ELEVATION_BRIEF
canonical_id: SANGAM_ELEVATION_BRIEF
version: "1.0"
status: PROPOSAL_FOR_NATIVE_RULING
date: 2026-09-22
asset: ka_sangam (Saṅgam — convergence)
target_table: kala_convergence
packet_shape: MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §6.4
reconciles:
  - 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md  # kernel retained; campaign plan ref superseded
governed_by:
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md
  - 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md
  - 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md
evidence_base:
  - 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/readiness/_work/LANE_C_HARD_ASSETS.md  # F7–F11, §C
  - code re-verified in this session (file:line cited inline)
does_not_authorize: any code, migration, seed, build dispatch or campaign evidence event.
independent_reviewer: UNASSIGNED — see §14
---

# ka_sangam — elevation packet

**The claim of this brief in one sentence.** Saṅgam's defect is not in its scoring function —
that survived review — it is at its **output boundary**: one table with one natural key carries
four different grains of evidence, and every consequence the readiness lane measured (mode
starvation, 13× duplication, an anti-correlated confidence label, an uninherited independence
count) follows from that single fact. The elevation is therefore an **output-contract** change
first and a scoring change second.

The June brief (`CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md`) named the right kernel — the rigor
stratum, the independence discount, the generator→narrow→ephemeris-last spine. That kernel is
retained here. What it could not know is what four modes in one table would do to it downstream.

---

## §0 — Position, honestly stated

| | |
|---|---|
| Acceptance state today | **below `PLAN_REVIEWED`** for the canonical chart. `kala_convergence` holds **0 rows** for `482012f1`; the 20,497 live rows are two other charts. |
| Freeze status | `ka_sangam` is among the 12 of 23 identities with **no surviving `build_runs.plan_manifest`**, across 522 build runs. The campaign's integrity mechanism has never run on the layer's chokepoint. |
| Downstream exposure | Seven assets depend on it. Five `ka_*` writers select `convergence_score`; **zero** select `independent_current_count`. |
| What this brief is | A proposal. Every ruling in §13 is the native's. Where doctrine is required and absent, this brief records a requirement rather than inventing one. |

---

## §1 — The finding that reframes the asset: four grains, one key

This is the brief's substantive contribution, and everything downstream of §1 depends on it.

### 1.1 The four modes do not describe the same kind of object

| Mode | What one row actually is | Natural grain | Predicate-bound? |
|---|---|---|---|
| **A** | a dated contact inside a daśā-eligible interval | (signal, contact instant) | yes — genuinely |
| **B** | a dated contact anywhere in the horizon, daśā checked not gated | (signal, contact instant) | yes — genuinely |
| **C** | a multi-year **sign-residence state** for a subsystem | (subsystem, residence period) | weakly — routed by predicate class |
| **D** | a SAV≥28 **sign-ingress window** for one of three scan planets | (chart, scan planet, sign ingress) | **no — predicate-agnostic** |

Mode D's own code comment says so: *"Mode D is sign-level and predicate-agnostic"*
(`ka_sangam.py:721-726`). Yet the call passes `predicate=pred_dict` and then stamps
`w['primary_domain'] = primary_domain` from that predicate (`:728-737`). A computation that does
not depend on a signal is given that signal's identity **and its domain**.

### 1.2 The declared natural key ratifies the grain error

Migration 981 declares the key as `(chart_id, horizon_tier, mode, peak_date, signal_id)` and
live-verifies **0 duplicate-key groups across all 20,497 rows**. That verification is true and it
is uninformative: because `signal_id` is in the key, the 14,352 Mode D rows that collapse to
**1,104 distinct `(peak_date, window_start, window_end, score)` tuples** are each a *legal,
distinct key*. The key does not detect the duplication; it licenses it.

**Proposal.** A key that includes a field the computation does not depend on is not a natural key.
Mode D's natural key is `(chart_id, horizon_tier, scan_planet, sign, ingress_peak_date)`.

### 1.3 The expected-volume contract encodes the defect as truth

Migration 866 sets the canonical chart's `expected_volume_formula` to
`EXACT: 25 × 478 (Mode D, fully derived) + 2918 (Modes A/B/C)` = **14,868**, matching
`target_floor` and `count_sql` exactly, and states the 25 is "25 of this chart's 60 lifetime
substeps [that] have a non-SUBSYSTEM predicate … each producing exactly 478 windows."

That sentence *is* F8, written as a specification. The 25× multiplier exists only because the
guard `if pred_dicts and pred_dict is pred_dicts[0]` (`:726`) is vacuous on the lifetime path,
which passes `pred_dicts=[pred]` — a one-element list (`:591`).

**Consequence, and it is large:** repairing the guard reduces the canonical chart's Mode D
contribution from 11,950 to 478, and its total from **14,868 to ≈3,396 — a 77% drop**. Under §N.4
(*floors aspirational, never fabricate rows to hit a number*) that is the correct outcome and
`target_floor` must be reset to the achieved count. But three Nirmāṇa-ratified artifacts encode
the pre-repair number and must be re-issued in the same change: **866** (expected volume), **980**
(output digest spec), **981** (natural-key partition). Repairing the guard without re-issuing them
turns a correct fix into a freshness/digest failure.

*This is the concrete form of the coordination obligation: not "tell Nirmāṇa," but "these three
migrations are part of the same atomic change."*

### 1.4 The cascade binds sky facts to signals they do not depend on

Migration 403 makes `kala_convergence.signal_id` `REFERENCES bodha_msr_signals ON DELETE CASCADE`
(one of five `kala_*` tables). Combined with §1.1: **deleting one L2 signal deletes SAV-bindhu
sign-ingress windows that were never about that signal.** The predicate-agnostic rows are the most
reusable astronomical content in the table and the most arbitrarily destructible.

Generation binding (native decision 1) fixes the destructive event for predicate-bound rows. For
Mode D it is not sufficient and not really the right instrument: those rows should not be
signal-keyed at all. **If decision 1 goes the other way** (no L3 generations), the Mode D regrain
becomes *more* important, not less — it is the only thing that removes predicate-agnostic sky
geometry from the cascade's reach.

### 1.5 F7 is a symptom; cross-grain ranking is the cause

The top 500 and top 750 by `convergence_score` are 100% Mode C. The usual reading is "a LIMIT is
acting as a mode filter." True, but the deeper statement is: **`convergence_score` is a
within-grain quantity being used as a cross-grain ranking key.** A multi-year sign residence and a
same-day exact aspect are scored on one 0–1 scale that was never argued to be shared. `ORDER BY
convergence_score` across modes is therefore not a ranking at all — it is an artifact of which
grain the function happens to favour.

This is exactly F08's prohibition in the foundation contract (no averaging across incompatible
schools) and L3-Q05's *"non-comparable scales."* It also means **partitioning the top-N is the
immediate repair, and making the score cross-grain comparable is a separate question that may have
no answer.** They are not alternatives (agreeing with LANE C, S-C).

---

## §2 — Reconciling the June kernel

The June brief is reconciled, not re-authored. Its `parent_plan` pointer
(`L3_KALA_CAMPAIGN_PLAN_v1_0.md`) is superseded; its thinking is not.

| June item | Disposition now | Basis |
|---|---|---|
| **I-16 convergence function** (multiplicative necessary × saturating supporting) | **PRESERVE, re-scope.** Implemented and ratified (`engine.py:696-729`). Re-scoped from "the score" to "a **within-grain** score" that must carry an explicit comparability declaration. | §1.5 |
| **I-17 continuous orb-strength** | PRESERVE unchanged. | — |
| **I-18 window profile (peak + shoulder)** | PRESERVE. `peak_date` NULL on 0 of 20,497 rows. Note `ka_kalasutra`'s docstring "~99% NULL-date case" is stale phrasing on a load-bearing file. | LANE C §C.4 |
| **I-19 rarity** (measured base rate) | **PRESERVE, UNAUDITED.** `rarity_years` exists as a column; this pass did not verify it is a measured base rate rather than a formula. Named in §14, not asserted either way. | this session |
| **I-21 confidence** | **REPLACE OR NULL.** `confidence_score = min(1, ICC/13)` (`ka_sangam.py:965`) where one of 13 currents is `'transit': mode in ('A','B')` (`:908`) — a tautology — and C13 school consensus is structurally unreachable pre-U4 (`:989`), so the denominator contains a term that can never fire. Observed ICC ≤ 6, so the score is capped at 0.46 by construction. §N.8: a signal whose detector cannot make it read false is null, not green. | F10 |
| **I-22 independence discount** | **PRESERVE THE IDEA; RENAME AND INHERIT THE FIELD.** The concept is the single most valuable thing in the June brief. The implementation (`engine.py:850-889`) is a hand-weighted coupling table — which L3-U02 explicitly calls *bookkeeping, not demonstrated statistical independence*. | §3.3, S-A |
| **Efficiency spine** (generator→narrow→ephemeris-LAST) | PRESERVE. It is the live design and the P4 candidate. **Constraint adopted verbatim from Gochara v0.3 R2:** a new kernel must not edit or import `transit_search.py` (shared with Kshetra, the Gochara family and frozen L0 `bg_sky_calendar`). | S-I |
| **Hard internal gate** (prove one signal end-to-end before products fan out) | **PRESERVE, and it is now more necessary**, not less: canonical chart has 0 rows and the freeze has never fired. | §0 |
| **"Extend `kala_convergence`, do not replace"** | PRESERVE, with §1.3's condition: extension is now a coordinated re-issue of migrations 866/980/981. | §1.3 |
| Campaign-plan refs (§5.x, I-N, wave K4) | **SUPERSEDED as addresses.** Content retained above; do not cite the old plan as authority. | context §11 |

Two of the older discussion prompt's premises are **withdrawn** on measured evidence (F9, and
confirmed independently this session): the flat `ORDER BY dignity_score … LIMIT 200` at `:247`
exists only as a comment describing a superseded query — the live path is a per-`signature_class`
`ROW_NUMBER()` plus a quota selector (`:166-221, :274-305`) that guarantees each populated class a
floor; and `engine.py:1102`'s `[:1]` selects the **C12 tājika `domain_lord` only**, while the daśā
query at `:1113` uses the full `constituent_lords` set. The daśā prior is **not** built on a single
lord. The brief inherits the smaller, true claim.

---

## §3 — The output contract (the core deliverable)

### 3.1 What a consumer must receive to reconcile honestly

Under the native's ratified model — *assets need not agree; each reading carries its
qualification; the LLM reconciles at the end, in context* — the reconciling step is only possible
if each row declares what kind of evidence it is and whether it may be compared or combined. That
is not a new vocabulary; it is F04/F06/F12 plus Strategy §3's *Temporal testimony* object.

**Proposed minimum envelope on every served convergence row:**

| Element | Bind to | Why reconciliation fails without it |
|---|---|---|
| `mode` **and its grain** | Strategy §3 *Temporal testimony* → method/family | Without grain, a multi-year residence and a one-day aspect are one list. |
| `comparability_class` | F08 / L3-Q05 *non-comparable scales* | Declares whether this score may be ranked against another row's. The LLM must not have to infer it. Precedent in-layer: `ka_taranga` stamps `tier_basis='relative_uncalibrated'` on every row. |
| `independence_group` + count | L3-U02 | *"Zero supporting evidence cannot become one independent witness; another representation of the same origin adds no independent support."* Three agreeing rows are meaningless until the reader knows whether they are three witnesses or one echo. |
| `evidence_roots` (exact) | §N.5, Strategy §3 | L1 `fact_id`s referenced, never restated. |
| `completeness_state` | F06 six states | Today a caller cannot distinguish *no window* from *search failed* from *filtered below threshold* (S-12: modes that raise are logged at `warning` and skipped, `:654,690,716,738`; sub-0.45-orb events are `continue`d, `engine.py:1171,1400`). No null/zero/empty fallback may collapse these. |
| `coverage` object | Strategy §3 *Search coverage*; L3-Q08 | Requested vs completed horizon, exclusions, caps applied. *"A top-K cutoff cannot establish that no window exists."* |
| `domains` (plural) | L3-U02, B.11 | See 3.4. |
| ayanāṃśa identity | Strategy §6.1 L3-A15 (named gap) | See 3.5. |
| material uncertainty | Strategy §3 | — |

**The sentinel obligation is ours** (Execution Brief §7): a field that is computed, stored and then
trimmed before synthesis is worth nothing. F11 is the live instance — `confidence_label_relative`
+ `tier_basis` are computed, stored, and omitted by `query_convergence_windows.ts:118-129`, which
serves the degenerate absolute label instead.

### 3.2 Mode stratification — the rule

> **No ranked or truncated projection of `kala_convergence` may rank across grains.**
> Every top-N is partitioned by `mode` (and, where the consumer is domain-scoped, by domain),
> with a declared per-partition floor.

The in-repo precedent is already correct and should be copied rather than invented:
`ph_nimitta.py:337-348` uses `ROW_NUMBER() OVER (PARTITION BY domain …)` with
`_MAX_CONVERGENCE_PER_DOMAIN = 50` before its `LIMIT 500`. It is the best-behaved consumer in the
set for exactly this reason.

Sites that must change (consumer-owned, listed as effects in §9, not as edits this brief
authorizes): `ka_kala_darshana.py:26-32` (`LIMIT 750`), `ka_vighnakara.py:177-183` (`LIMIT 500`),
`mi_adhilepa.py:294-309` (**unordered** `LIMIT 500` feeding a calibration multiplier — the worst of
the set because it is silent *and* it feeds calibration), `ph_nimitta.py:710-715` (`LIMIT 1`
ordered only by date distance; ties arbitrary), `ka_jivana_parva.py:120-125` (`LATERAL … LIMIT 1`,
no `ORDER BY`).

### 3.3 Inherited independence

Measured this session, non-test, tree-wide:

- **Five** `ka_*` writers select `convergence_score`: `ka_jivana_parva`, `ka_kala_darshana`,
  `ka_kalasutra`, `ka_taranga`, `ka_vighnakara`.
- **Zero** `ka_*` writers select `independent_current_count`. Its only non-test consumers are
  **L4 `ph_nimitta.py:159,329`** and the serving capability `query_convergence_windows.ts:123`.

*(The session prompt said four inheriting assets; the measured number is five. Recorded as measured
rather than silently reconciled — `ka_bhavishya_lekha` references the table but not the score, so
the count depends on whether `ka_kalasutra`'s max-score-per-signal reduction counts as inheritance.
Either reading leaves the asymmetry intact.)*

**Proposal.** `independence_group` and its count are **part of the row envelope**, not an optional
column: any projection that carries `convergence_score` must carry the independence qualification
with it, and a projection that drops it is a contract violation detectable by the sentinel test.
A score without its independence qualifier is the force-fitting VA §10.2 names as
*duplicate-evidence counting*.

**And the field must stop claiming more than it measures.** Whatever S-A rules, the current name
asserts demonstrated independence that nothing demonstrates.

### 3.4 Domains — plural, at the source

`domains_affected_array` is fetched in full (`ka_sangam.py:343`) then reduced to `da[0] if da else
None` (`:353`). Downstream, `ka_tulana`'s own input model already declares `domains: list[str]`
(`ranker.py:138`) and is fed one; `ka_taranga.py:112` then drops every NULL-domain row —
**1,656 of 17,957 (9.2%)** on the measured chart — silently.

Cross-domain convergence ("this window is simultaneously a career and a relationship window") is
the Cross-Domain Linkage claim B.11 rests on, and first-domain-only makes it structurally
unrepresentable. The strategy forbids one-domain flattening.

### 3.5 Ayanāṃśa identity

`engine.py:1097` reads `predicate.get('ayanamsha_id') or 'lahiri'` — a default-on-missing — the
value drives the daśā query, and `kala_convergence` **has no ayanāṃśa column at all**. So a row
computed under a defaulted bare `'lahiri'` is indistinguishable from one computed under an explicit
convention, and `chart_facts` elsewhere stores `'lahiri_chitrapaksha'`, not `'lahiri'` — a
distinction `ka_sangam.py:993-995` already documents as a prior bug. The default is unrecoverable
from the data. This is Strategy §6.1 L3-A15's named gap, confirmed at schema level.

---

## §4 — Field-level dossier (Strategy §3)

Gap classes: *missing · computed-but-discarded · persisted-but-unused · flattened · unqualified ·
stale · unserved.*

| Field | Producer | Gap class | Receiving operator (F12) | Falsifying test |
|---|---|---|---|---|
| `convergence_score` | `engine.py:696-729` | **unqualified** (no comparability declaration) | computes / evaluates | Rank a Mode C row and a Mode A row; if the order is defensible under a stated criterion, the scale is shared. Today no criterion exists. |
| `confidence_score` | `ka_sangam.py:965` | **unqualified — unearned (§N.8)** | none admissible | Construct inputs that should make it read low; if no input can, it is null. The tautological `'transit'` term and the unreachable C13 term both fail this. |
| `confidence_label` | `engine.py:789-849` | **degenerate** | none admissible | Show one Mode A/B row not labelled `speculative`. Measured: 0 of 2,735. |
| `confidence_label_relative` + `tier_basis` | `engine.py:789-849` | **unserved** (computed, stored, trimmed) | expresses uncertainty | The §7 sentinel test: does it reach the allowed consumer and the saved result? Today: no. |
| `independent_current_count` | `engine.py:850-889` | **persisted-but-unused by L3** + **unqualified** (name claims more than the detector shows) | expresses uncertainty | Delete one "independent" current and one "coupled" current from an ICC-5 row; if the score moves identically, the coupling table is decorative. |
| `domain` | `ka_sangam.py:353` | **flattened** | interprets / navigates | Count rows whose `domain` would change if `domains_affected_array[1]` were used. If large, first-domain-only is a coin flip, not a simplification. (One query; not run here.) |
| `mode` | writer | **present, unqualified as grain** | gates applicability | §3.2 — can a projection rank across it? |
| ayanāṃśa | `engine.py:1097` | **missing** (+ default-on-missing) | gates applicability | Two builds under different ayanāṃśas must produce distinguishable rows. Today they do not. |
| coverage / silence | — | **missing** | expresses uncertainty | A caller must distinguish *no window* / *search failed* / *filtered*. Today it cannot (S-12). |
| `constituent_factors` (jsonb) | writer | **healthy** — rich and it does survive to the retrieval projection (`query_convergence_windows.ts:125`) | interprets | — |
| `signal_id` on Mode D rows | `:728-737` | **mis-keyed** (§1.1) | — | Does the computation read the predicate? Mode D: no. |
| `dignity_score` NULL → `0.5` | `ka_sangam.py:348,360` | **unqualified default inside a selection key** | gates eligibility | A signal with no measured dignity currently outranks any signal measured below 0.5. |

---

## §5 — Preserve / change / reuse

**Preserve unchanged.** The I-16 scoring function and its ratified form; continuous orb-strength;
window profile; the `_current_stance` honest-empty distinction (`engine.py:731-760`) — the right
shape of honesty about an unfinished thing; the SAVEPOINT discipline on the three soft dependencies
(`:997-1034, :1055-1079, :1098-1126`), which is the codebase's correct example of the pattern;
the CR-87 fail-loud birth-location resolver (`:813-862`); the CR-102 house-from-Moon frame fix;
the cross-attempt resume ledger (`:408-446`) and its byte-identical resumed builds; the D-3
FIX-PSEL per-class quota selector and its content-derived `md5` tiebreak.

**Change.** The Mode D guard and Mode D's grain/key (§1.1–1.3). The output envelope (§3.1).
Cross-grain ranking at every consumer (§3.2). `confidence_score`/`confidence_label` (§4).
The independence field's name and inheritance (§3.3). Domain plurality (§3.4). Ayanāṃśa identity
(§3.5). The `dignity_score` NULL→0.5 default in the selection key.

**Reuse.** `ph_nimitta`'s partition pattern rather than a new one. `ka_taranga`'s `tier_basis`
stamp as the comparability precedent. `ganita_yogas_get`'s `judgment_flags` pattern for cap
disclosure (§N.6 item 1) — it has precedent in this codebase and should win on consistency over a
new `coverage` object shape (agreeing with S-B).

**Explicitly not value** (adopted from LANE C §C.7): raising `_MAX_PREDICATES`; adding a fifth
mode; extending the lifetime horizon. All three add rows to a table whose top-750 is already
100% one grain and 70% duplicates.

---

## §6 — Method qualification

**Qualified today.** Mode A's daśā-eligibility-then-contact structure is the orthodox core
(*daśā gives the period, gochara gives the moment*); the soft-prior departure is deliberate and
documented. Mode D's SAV≥28 gating is orthodox aṣṭakavarga transit gating. Mode B is honestly
flagged as a discovery mode with no classical analogue.

**Not qualified, and requiring the native's doctrine rather than code:**

1. **What makes two witnesses independent** (S-A). Until ruled, no convergence count in this
   system means what it says — and five assets inherit it.
2. **Whether a sign-residence state and an exact aspect belong on one scale at all** (§1.5). If
   they do not, `convergence_score` is permanently within-grain and the comparability flag is not
   a nicety but the contract.
3. **What Mode C and Mode D each mean as qualified methods**, distinctly (S-D). Mode D at ICC=1,
   sign-level, predicate-agnostic may be a *modifier* on other modes' windows rather than a
   window-producing mode.

**Two one-query questions that this brief cannot close and should not guess** (S-G, S-H):
whether L1 computes daśā level 4 — which decides whether `max_level=3` (`engine.py:1124`) is
*forced* and should be documented as forced, or *lossy*; and whether `chart_dashas` uses closed or
half-open period boundaries — which `engine.py:1138`'s closed-closed test must match. A mismatch in
either direction is worse than a consistent choice.

---

## §7 — Input generations, output keys, and the Nirmāṇa coordination obligation

**Input generations — the packet cannot pin one today.** Strategy §4 requires binding *"one
compatible transitive dependency vector … no implicit fall-through to mutable `public` rows."*
Measured 2026-09-22: `l1_data_plane_generation_heads` = **0**, `l2_…` = **0**, and no L3 head table
exists. Saṅgam's actual reads (`kala_activation_predicates`, `bodha_msr_signals`, `chart_facts`,
`public.charts`, `chart_dashas`, plus three SAVEPOINT-guarded soft dependencies) therefore all
resolve against mutable `public` rows that L2's active campaign changes underneath a running build.

This packet's declared input vector is consequently **unpinnable as of this date**, and that is a
statement about the layer, not about this asset. It is also why the determinism gate cannot yet be
defined for Saṅgam: "build twice, diff" is meaningless without a pinned vector. The packet is
written to bind to published L1/L2 generations the moment decision 1 rules; §7's closing paragraph
states the position under both rulings.

**Proposed keys.**

| Rows | Proposed natural key | Change from live |
|---|---|---|
| Modes A / B | `(chart_id, horizon_tier, mode, signal_id, peak_date)` | unchanged |
| Mode C | `(chart_id, horizon_tier, mode, subsystem, period_start)` | subsystem replaces signal as the identifying participant |
| Mode D | `(chart_id, horizon_tier, mode, scan_planet, sign, ingress_peak_date)` | **signal_id leaves the key** |
| all | `+ ayanamsha_id` if S-E is ruled yes | new |

**Atomic coordination set.** Any of the above changes `ka_sangam`'s output identity and therefore
requires, in the same change: **866** (expected-volume formula and `target_floor`, which falls
14,868 → ≈3,396 on the Mode D repair alone), **980** (`asset_output_digest_specs` — key_columns and
value_columns both move), **981** (`natural_key_partition` text). Migration **403**'s cascade
applies to `signal_id`; removing it from Mode D's key is also the instrument that takes
predicate-agnostic geometry out of the cascade's reach (§1.4).

**Under generation binding (decision 1 = yes):** rows bind to a published L2 generation rather than
a live surrogate `signal_id`; the destructive event stops for predicate-bound rows and the 79
dangling predicate references become impossible. **Under decision 1 = no:** the Mode D regrain
carries more weight, `bodha_signal_identity`'s determinism continues to mitigate re-attachment but
not deletion, and the brief's honest position is that Modes A/B/C remain destructible by an L2
rebuild and must be treated as rebuildable projections — which requires the deterministic-rebuild
guarantee the context document flags as not yet true layer-wide (`date.today()`, naive-into-
`timestamptz`).

---

## §8 — Source and data checks

1. `ka_sangam` writes zero rows outside `kala_convergence`; it is the confirmed sole live writer of
   that table (migration 980's four-check investigation; re-confirmed this session).
2. Every constituent fact resolves to an L1 `fact_id`; no L1 computed value is restated (§N.5).
3. `signal_id` non-NULL on every predicate-bound row (live: 0/20,497 NULL); Mode D rows carry no
   signal identity after the regrain.
4. No row's `domain` is a silent reduction of a multi-domain array.
5. No served projection ranks across grains (§3.2) — assert in CI, not by review.
6. The sentinel test (Execution Brief §7) passes for `confidence_label_relative`/`tier_basis` or
   they are retired.
7. One dispatch whose `plan_manifest` is captured and verified, before any elevation (S-J).

---

## §9 — Consumer effects

| Consumer | Effect of this packet |
|---|---|
| `ka_kala_darshana` | **Begins to see daśā×transit convergences at all.** Today 0 of its 750 rows are Mode A/B. Every temporal view in L3 is currently built on sign-ingress windows exclusively. |
| `ka_vighnakara` | Same, at `LIMIT 500`. Every downstream obstruction judgment is currently built on one grain. |
| `ka_taranga` | Stops silently dropping 9.2% of rows once `domains` is plural; gains comparability declaration. |
| `ka_kalasutra` | Unaffected in purpose; its "~99% NULL-date" docstring should be corrected (stale, load-bearing). |
| `ka_jivana_parva` | Requires a total `ORDER BY` on its `LATERAL … LIMIT 1` (§N.7 item 2). |
| `ka_tulana` | Receives real multi-domain input its model already declares; its `confidence_label='speculative'` dataclass default (`ranker.py:135`) must become *unknown*, not the lowest tier. |
| `ph_nimitta` (L4) | Already partitions correctly; inherits the renamed independence field. Its `LIMIT 1` tie-break needs a total order. |
| `mi_adhilepa` (L5) | Its unordered `LIMIT 500` feeding a calibration multiplier must gain a total order and a partition, or calibration is applied to heap order. |
| `query_convergence_windows` (serving) | Projection gains the relative tier + `tier_basis`, independence group, coverage and grain. Owned by **Pūrṇa** — raised as an **L3-U04/U11 interface packet with a test**, not edited here (context §5). |

Row-count effect to state plainly for every consumer: the canonical chart's expected row count
**falls by ~77%** on the Mode D repair, and that is the correct direction. Any consumer whose
output is materially unchanged by the repair was reading duplicates.

---

## §10 — Benchmark target

P4 is the candidate: *reuse geometric search results across compatible predicates/modes, then apply
distinct semantic scoring and eligibility*, with the strategy's own qualification — **mode identity
and full applicable predicate coverage must survive; savings fund broader coverage; reduced caps
cannot pass as equivalent.**

Constraint (S-I, adopted verbatim from Gochara v0.3 R2 rather than re-litigated): the new kernel
must **not** edit or import `transit_search.py`. Shared with Kshetra, the Gochara family and frozen
L0 `bg_sky_calendar`; any change there is a cross-stream invalidation, not an in-stream edit.

Measure per the §5 benchmark contract on the disposable harness; do not use
`asset_registry.estimated_seconds` (463 s) as a baseline. Cite `KALA_COST_PROFILE_v1_0.md` when it
lands rather than guessing here. Cost is dominated by per-predicate Swiss `find_aspect_events` over
a 100-year horizon × up to 60 lifetime predicates.

**A free saving falls out of §1.3:** the Mode D repair removes 24 of 25 redundant century ingress
scans on the canonical chart before any P4 work begins.

---

## §11 — History and rollback

- **Nothing in `kala_convergence` is protected history.** It is a rebuildable projection — but
  rebuild-freely is only safe if rebuild is deterministic, which is not yet established layer-wide.
- The canonical chart holds **0 rows**; there is nothing to roll back to, and the first build is
  therefore also the first freeze (S-J).
- **The cascade has already fired** on this chart. Design for generation binding; §7 states the
  position under both rulings.
- Rollback contract: per-substep self-scoped delete-then-insert is already correct
  (`:576-579`) and must be preserved through any key change — a key change alters what "self-scoped"
  means and the delete predicate must move with it.
- Re-issue of 866/980/981 is part of the rollback unit, not a follow-up.

---

## §12 — Acceptance and the distinction this asset would earn

**Questions served:** L3-Q02 (nearest vs best-supported eligible window) primarily; L3-Q01 and
L3-Q07 as a contributor. **Partially:** L3-Q05 — it holds the material to show *why* methods
disagree but currently flattens it. **Cannot today:** L3-Q08 (*is no window a real negative?*) —
there is no coverage object, so absence is unbounded and indistinguishable from failure.

**VALUE_EVALUATED is N for all sixteen consumer questions examined layer-wide.** This brief does
not claim otherwise. The distinction this asset would earn, stated so it can be falsified:
*a consumer can tell a five-witness dated convergence from a one-witness sign residence, and can
tell either from a search that did not run.*

**Ablations** (adopted; none run here):
1. Rebuild `ka_kala_darshana` on the current top-750 and on a mode-partitioned top-750; compare.
   If materially identical, Mode C was carrying the signal and A/B add nothing — itself a finding.
2. Delete one current at a time from an ICC-5 row. If "independent" and "coupled" currents move the
   score identically, the coupling table is decorative.
3. Count rows whose `domain` changes if `domains_affected_array[1]` is used. One query.
4. Deduplicate Mode D and re-run every consumer. If nothing changes, Mode D's contribution is 1,104
   windows and every row-count statement about this asset is overstated by an order of magnitude.

---

## §13 — Decisions for the native

Carried from LANE C §C.8 where unchanged; **S-K and S-L are new in this brief.**

| # | Decision | This brief's recommendation |
|---|---|---|
| **S-K** *(new)* | **Do the four modes share one table, one key and one score?** | Keep one table; **four grains with four natural keys**; score declared within-grain. This is the root; S-C, S-D and much of S-A follow from it. |
| **S-L** *(new)* | **Is the Mode D repair's 77% row-count drop accepted, with 866/980/981 re-issued atomically?** | Yes. §N.4: reset the floor to the achieved count; never fabricate rows to hold a number. |
| S-A | What is an independent witness? | Rule (a) now — rename the field so it stops claiming independence — and hold (c), empirical decorrelation, as the real answer pending L5 outcome data. **Doing nothing is choosing (a) without saying so, while keeping the false name.** |
| S-B | How does a caller learn a cap bound? | `judgment_flags`-style disclosure; it has in-repo precedent. |
| S-C | Partition top-N, or make the score comparable? | Partition now; treat comparability as separate and possibly unanswerable. |
| S-D | Does Mode D survive, and how? | Keep as a **modifier** or as a mode excluded from ranked projections; not as a signal-keyed window producer. |
| S-E | Ayanāṃśa in the natural key? | Yes — the default at `engine.py:1097` is otherwise permanently unrecoverable. Cost: row multiplication and every consumer's dedup assumption. |
| S-F | Multi-domain representation | `domains text[]` on the row, or a child table. Not "keep `domain`, add `domains_all`" — that keeps the flattening alive. |
| S-G | `max_level=3` — semantic or accident? | One query against `chart_dashas`. Document as forced, or fix as lossy. |
| S-H | Closed-closed daśā interval test? | Check L1's own boundary rule first; a mismatch either way is worse than a consistent choice. |
| S-I | P4 shared geometry | Adopt Gochara v0.3 R2 verbatim: do not edit or import `transit_search.py`. |
| S-J | The unexercised freeze | One captured, verified `plan_manifest` dispatch before any elevation. |

---

## §14 — What this brief does not establish

1. **`rarity_years` was not audited.** Whether it is a measured base rate (I-19's intent) or a
   formula is **not verified** in this pass. It is not asserted either way.
2. **No live database query was run in this session.** Every live figure is cited from LANE C's
   read-only measurements or from migration 866's own derivation; code claims were independently
   re-verified at the cited file:line.
3. **The five-vs-four inheriting-consumer count** is recorded as measured, not reconciled (§3.3).
4. **COULD NOT VERIFY, inherited and not closed here:** whether L1 computes daśā level 4 (S-G);
   whether `chart_dashas` boundaries are closed or half-open (S-H).
5. **Not traced, scope stated:** `mi_kula`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`,
   `taranga_kernel`, `ka_temporal/date_resolver` reads of `kala_convergence`; `kala_temporal.ts`.
6. **Every method question remains the native's**, at acharya standard — what a convergence is,
   what an independent witness is, and whether a sign residence and an exact aspect belong on one
   scale at all.
7. **Independent reviewer: UNASSIGNED.** Strategy §6.4 requires one per packet. This brief's §1 is
   a new argument and should be broken by someone who did not write it — specifically §1.3's
   arithmetic (25 × 478 = 11,950; 11,950 + 2,918 = 14,868; post-repair ≈ 3,396) and §1.1's claim
   that Mode D is genuinely predicate-agnostic.

---

*Produced read-only. No row written, no migration authored or edited, no build dispatched, no
campaign evidence event emitted, no guard weakened, no credential echoed. This brief proposes;
the native rules.*

## Changelog

- **1.0** (2026-09-22) — First issue. Reconciles `CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md`'s kernel
  (retained: I-16/I-17/I-18, the independence-discount idea, the ephemeris-last spine, the
  spine-first hard gate) against the readiness lane's F7–F11 and the ratified context. New in this
  issue: §1's four-grains/one-key analysis and its three consequences — the natural key licenses
  the duplication rather than detecting it; migration 866 encodes the duplication as the exact
  expected-volume contract (repair drops the canonical floor 14,868 → ≈3,396); and migration 403's
  cascade binds predicate-agnostic sky geometry to signals it does not depend on. Two premises of
  the older discussion prompt withdrawn on evidence (the flat `LIMIT 200`; the `[:1]` daśā claim).
