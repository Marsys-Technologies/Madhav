---
canonical_id: F62_MOOLATRIKONA_REBUILD_PACKET
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-62
authored: 2026-08-21
authored_by: PARIŚEṢA-V4 repair lane (GA-2/GA-3 authority)
execution_status: NOT EXECUTED — awaiting properly-scoped GA-3 execution
---

# F-62 — moolatrikona dignity tier: code repair landed, DATA REBUILD PENDING

## §1 — What this document is, and what it is not

This is the **rebuild specification** for F-62. It is deliberately **not a rebuild
execution**. No production data was written by the lane that authored it.

The reason is CLAUDE.md §N.3: `ga_structural` is an **L1, chart-scoped,
delete-then-insert** writer, not an L0 global-reference upsert. Re-running it
DESTROYS and REPLACES the existing `chart_facts` rows for a chart. That is
protected-data execution and belongs to a GA-3 packet run under its own scope
declaration — not to a code-repair lane. (The chart-`482012f1` GA-3 batch earlier
in this campaign found real process-integrity gaps when that separation was
rushed; this packet exists so the same pattern is not repeated.)

## §2 — The finding, and its two distinct layers

`chart_facts.graha_dignity_per_varga` / `fact_key='dignity_state'` never emits
`'moolatrikona'` anywhere in the native chart's data — confirmed chart-wide,
every varga, every graha:

```sql
SELECT fact_value_text, count(*) FROM chart_facts
 WHERE fact_category='graha_dignity_per_varga' AND fact_key='dignity_state'
 GROUP BY 1;
-- neutral 2888 | own 419 | exalted 317 | debilitated 291 | moolatrikona 0
```

This collapses a classically-distinct tier into plain `'own'`. It is not
cosmetic: Saptavargaja / Sthāna Bala scores moolatrikona at **45** shashtiamsa
and own at **30** (BPHS Ch.27), so every graha whose natal degree falls in its
own moolatrikona band is systematically under-scored.

The finding has **two layers, and they have different dispositions**:

| Layer | State | Disposition |
|---|---|---|
| **Write path** — the classifier and the writers that call it | ALREADY FIXED IN CODE (PR #1296, `ekv(b-01) F-72`) | No further code change needed |
| **Read path** — downstream consumers of the emitted value | WAS STILL BROKEN | Fixed by this packet's PR |
| **Data** — the already-computed `chart_facts` rows | STILL WRONG | **This rebuild. Not executed.** |

### §2.1 — Write path (already correct, verified not assumed)

`brahmagyan/dignity_oracle.py::classify_dignity` implements the degree-gated
tier, sourced from `brahmagyan/l0_dignity_reference.py::DIGNITY_REFERENCE` —
this codebase's own single-source classical reference, cited **BPHS Ch.3**, and
seeded to the `bg_dignity_reference` table by migration 250. No degree range in
the repair was invented; all were read from that module.

Both writers on the path already call it:

- `ga_writers/ga_structural_writer.py:4827` — `classify_dignity(g_name, sign, degree)`,
  the writer of `graha_dignity_per_varga`.
- `ga_writers/ga_vargas_writer.py:1747` — the Saptavargaja branch, which
  **already** scores moolatrikona at 45.0 and own at 30.0, already gates the
  tier on the real natal degree via the oracle, and already restricts it to
  `varga_n == 1`.

F-62's brief flagged the Sthāna Bala point mapping as a possible SECOND defect.
**It is not one.** That was verified rather than assumed, and is now pinned by
`test_saptavargaja_scores_moolatrikona_at_45_and_own_at_30`.

### §2.2 — Read path (the defect this PR repairs)

The instant the oracle became able to EMIT `'moolatrikona'`, four downstream
consumers could not SPELL it — three keyed on `"mooltrikona"` (no `a`), one
enumerated only a four-value scale. The result was **worse than the original
collapse**: a moolatrikona graha missed every lookup and took a *neutral*
default, scoring BELOW the plain `'own'` it used to score.

| Consumer | Pre-fix behaviour | Fixed to |
|---|---|---|
| `bodha_writers/formulas.py::DIGNITY_SCORE` | 0.50 neutral default (vs own 0.85) | 0.95 |
| `bo_laksana.py::_DIGNITY_SCORE` | 0.50 neutral default | 0.95 |
| `bo_laksana.py::_DIGNITY_STRENGTH_TIER` | tier 0 = neutral (vs own 2) | 2 |
| `bo_laksana.py::_BENEFIC_VALUE_SUBSTRINGS` | matched no benefic substring | benefic |
| `ga_vichara_writer.py::dignity_direction` | `None` — abstained from the vote | `positive` |

`brahmagyan/dignity_oracle.py::DIGNITY_STATES` is now the single declared
emittable vocabulary, and `tests/test_f62_moolatrikona_downstream_vocabulary.py`
is the detector that fails when a consumer cannot cover it (CLAUDE.md §N.8 — a
signal with no detector behind it is not a signal). All six defects were
mutation-tested: each fix, reverted individually, kills at least one test.

## §3 — Rebuild scope

### §3.1 — Blast radius, measured

Measured read-only against production, joining each D1 dignity row against the
graha's own `degree_in_sign` fact and the L0 moolatrikona bands. **Exactly three
rows flip in D1, all on the canonical chart:**

| chart_id | ayanamsha | subject | current | degree | correct |
|---|---|---|---|---|---|
| `482012f1-…` | `lahiri_chitrapaksha` | `D1_JUP` | `own` | 9.7875 | `moolatrikona` |
| `482012f1-…` | `krishnamurti` | `D1_JUP` | `own` | 9.8843 | `moolatrikona` |
| `482012f1-…` | `true_chitra` | `D1_JUP` | `own` | 9.8030 | `moolatrikona` |

Note what the other two ayanamshas show, because it is the single most useful
domain fact in this packet: under `raman` Jupiter sits at **11.2338°** and under
`surya_siddhanta_classical` at **12.7495°** — both **past** the 10° boundary, so
`own` is the CORRECT answer for those two. The moolatrikona/own boundary for this
native's Jupiter is genuinely **ayanamsha-dependent**. Any verification that
asserts "D1_JUP should be moolatrikona" flatly, across all five, is wrong. The
per-ayanamsha expectations are encoded in
`test_jupiter_d1_dignity_per_ayanamsha`.

The D1 count is small; the D2–D60 count is **not yet measured** and is gated on
§5's open question below.

### §3.2 — Assets to rebuild, in dependency order

From `asset_registry.depends_on`, live:

```
ga_vargas  →  ga_condition, ga_strength  →  ga_structural  →  ga_vichara  →  bo_laksana  →  bo_bimba
```

then the remainder of the L2→L5 chain that consumes bodha output
(`bo_*` → `ka_*` → `ph_*` → `mi_*`).

`ga_structural` is the row-of-record writer for `graha_dignity_per_varga`;
`ga_vichara`, `bo_laksana` and `bo_bimba` all read `dignity_state` and carry the
read-path fixes, so they must be rebuilt AFTER the code lands, not before.

`bg_dignity_reference` (L0) does **not** need re-running: its data is unchanged,
and it is an L0 global-reference upsert (§N.3) with nothing to correct.

### §3.3 — Idempotency classification (why this is not self-serve)

| Writer | Layer | §N.3 class | Safe for a code lane to run? |
|---|---|---|---|
| `bg_dignity_reference` | L0 | global-reference upsert | Yes — but not needed |
| `ga_vargas`, `ga_structural`, `ga_vichara`, `ga_condition`, `ga_strength` | L1 | per-chart **delete-then-insert** | **NO — protected data** |
| `bo_laksana`, `bo_bimba`, all L2+ | L2+ | per-chart **delete-then-insert** | **NO — protected data** |

Every writer in the rebuild path except the unneeded L0 one is chart-scoped
delete-then-insert. **Do not execute from a code-repair lane.**

## §4 — Verification the GA-3 execution should run

Post-rebuild, all three must hold:

1. The reproducer inverts — `SELECT DISTINCT fact_value_text FROM chart_facts
   WHERE fact_category='graha_dignity_per_varga' AND fact_value_text ILIKE
   '%moola%'` returns rows where it returned zero.
2. `D1_JUP` reads `moolatrikona` under `lahiri_chitrapaksha` / `krishnamurti` /
   `true_chitra` **and still reads `own` under `raman` /
   `surya_siddhanta_classical`** (§3.1 — a rebuild that makes all five
   moolatrikona has over-fired).
3. No graha whose D1 degree is OUTSIDE its band flipped to `moolatrikona`, and
   the `exalted` / `debilitated` counts are unchanged (the tier splits `own`; it
   must not consume any other tier).

## §5 — Open questions, disclosed rather than decided

Neither is decided by this repair. Both are flagged so a ruling changes a
documented position, not silent behaviour.

**§5a — Moolatrikona is unreachable for Moon and Mercury.** For both, the
exaltation sign IS the moolatrikona sign (Taurus, Virgo), and `classify_dignity`
checks exaltation by SIGN ONLY, before the degree-gated moolatrikona check — so
they return `exalted` throughout and never reach the tier. The L0 reference shows
the tension is real and intentional on the data side: Moon's band starts at 4°,
immediately after its 3° exaltation degree; Mercury's at 16°, immediately after
its 15°. **The ranges were authored not to overlap.** Whether exaltation should
therefore itself be degree-gated is a genuine classical question — the mainstream
Parāśarī reading treats exaltation as a whole-sign state with the exaltation
degree as the deep/paramocca point used for Uccha Bala — and it is reserved for a
PRATINIDHI ruling, not settled inside a vocabulary repair. Current behaviour is
pinned by `test_known_gap_exaltation_sign_shadows_moolatrikona`.

**§5b — Should the moolatrikona degree gate apply in vargas above D1?**
`ga_structural_writer` applies the oracle to EVERY varga, passing the divisional
`degree_in_sign`, so after rebuild `moolatrikona` will begin appearing in
D2–D60 rows derived from divisional degrees. Its sibling `ga_vargas_writer`
explicitly does the opposite, guarding its moolatrikona branch on `varga_n == 1`
with the stated reason that *"vargas >1 have no meaningful 'degree within amsa'
for a re-derived MT check."* Both behaviours are currently merged and they
disagree. Exalted / debilitated / own are sign-based and translate to a varga
cleanly; moolatrikona is the ONLY degree-based tier, so it is the odd one out.
This packet does **not** change `ga_structural` — that would be deciding the
question unilaterally — but the GA-3 execution should expect D2+ moolatrikona
rows and should not treat them as a rebuild defect, and the question should be
ruled on before the D2–D60 blast radius is treated as correct.

**§5c — A dormant second Sthāna Bala implementation.**
`brahmagyan/ganita/l1_strength.py` carries its own local `PLANET_DIGNITY` table
(governance-allowlisted) whose moolatrikona rule is **sign-only, with no degree
gate**, and which scores moolatrikona at **37.5**, not the classical 45. It has
**no callers anywhere in the repository** — `ganita_strength_get` serves from
`chart_facts`, not from this module — so it is dormant, and it was deliberately
left untouched: activating a divergent duplicate is a larger risk than the
dormant inconsistency. Flagged for disposition, not repaired here.
