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
4. **Scope guard, added per §5b's correction**: `SELECT count(*) FROM
   chart_facts WHERE fact_category='graha_dignity_per_varga' AND
   fact_value_text ILIKE '%moola%' AND varga_n != 1` returns **zero**. Any
   non-zero result means `ga_structural_writer` fabricated a D2+ moolatrikona
   row from the replicated-D1-degree bug described in §5b and the execution
   must be treated as failed, not as "the tier is now working."

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

**§5b — CORRECTED (GA-5 review found this section's original claim factually
wrong; do not act on the version below the correction line if you are reading
an older copy of this document).**

Original claim (WRONG, do not act on it): "`ga_structural_writer` applies the
oracle to EVERY varga, passing the divisional `degree_in_sign`... expect D2+
moolatrikona rows and should not treat them as a rebuild defect."

**Corrected, live-verified**: `ga_structural_writer._load_varga_positions`
reads `chart_divisionals.varga_position` / `degree_in_sign` — and that column
is **the D1 natal degree replicated verbatim across all 29 vargas** (Jupiter/
lahiri/canonical reads `9.832504` for D1, D2, D3 … D2700 alike; only
`sign_number` genuinely varies per varga). There is **no real per-varga degree
anywhere in this database.** Passing this replicated D1 degree into the
degree-gated moolatrikona check for a D2+ row is therefore not "a legitimate
varga-level check that happens to reuse D1's number" — it is gating a
classification on a value that has no relationship to the graha's actual
position within that varga's sign at all.

**Consequently: a GA-3 execution against the current `ga_structural_writer`
would fabricate approximately 68 D2+ moolatrikona rows repo-wide (13 on the
canonical chart)** — each one a real §N.7 item 6 / B.10 violation (a computed
value invented from data that cannot support it), not a legitimate rebuild
result. **This packet's §3.1 blast-radius count (3 rows) is correct only for
D1.** Do NOT execute a GA-3 rebuild against `ga_structural_writer` for any
varga above D1 under this packet. The D1-only blast radius (§3.1's 3 rows) is
still valid and may proceed on its own merits; D2+ requires either (a) a real
per-varga degree source being added to `chart_divisionals` first (a separate,
larger finding), or (b) `ga_structural_writer` adopting `ga_vargas_writer`'s
existing `varga_n == 1` guard (the question of WHICH of the two disagreeing
writers is right is still a native ruling, not decided here) — before any
D2+ moolatrikona classification can be trusted.

`ga_vargas_writer` itself is not fully consistent either and needs its own
note: `_compute_dignity` applies the moolatrikona check in every varga
(multiple call sites), while only `_build_saptavargaja_rows` guards to
`varga_n == 1` — the two paths within this one writer disagree with each
other, a narrower version of the same open question. Separately,
`ga_vargas_writer.py`'s `_compute_dignity(graha, varga_sign)` call (no degree
argument) defaults to `0.0`, which trivially satisfies bottom-of-range checks
and labels every karaka in its own moolatrikona SIGN as `'Moolatrikona'`
regardless of real degree — a second, pre-existing MT-emitting surface this
packet did not originally account for, persisted to `karaka_per_varga`/
`dignity`. Exalted / debilitated / own are sign-based and translate to a varga
cleanly; moolatrikona is the ONLY degree-based tier, so it remains the odd one
out regardless of which writer's convention eventually wins.

**§5c — A dormant second Sthāna Bala implementation.**
`brahmagyan/ganita/l1_strength.py` carries its own local `PLANET_DIGNITY` table
(governance-allowlisted) whose moolatrikona rule is **sign-only, with no degree
gate**, and which scores moolatrikona at **37.5**, not the classical 45. It has
**no callers anywhere in the repository** — `ganita_strength_get` serves from
`chart_facts`, not from this module — so it is dormant, and it was deliberately
left untouched: activating a divergent duplicate is a larger risk than the
dormant inconsistency. Flagged for disposition, not repaired here.
