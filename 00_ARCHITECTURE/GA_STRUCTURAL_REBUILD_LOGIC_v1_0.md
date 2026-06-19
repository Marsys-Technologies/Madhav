---
artifact: GA_STRUCTURAL_REBUILD_LOGIC_v1_0
type: STEP_0_LOGIC_GATE
version: 1.0
status: REVISED_AWAITING_NATIVE_APPROVAL
authored_by: Claude Code 2026-06-19
governing_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_GA_STRUCTURAL_COMPLETENESS_REBUILD_v2_0.md
purpose: >
  STEP 0 gate document: proves the logic, citations, and per-file line numbers
  for the ga_structural completeness rebuild before any code changes.
  Native must approve this document before STEP 1 (code) begins.
may_proceed_to_step_1: false
---

# GA8 ga_structural — Rebuild Logic (STEP 0)

All findings reference the live file:
`platform/python-sidecar/ga_writers/ga_structural_writer.py` (5,348 lines)

---

## §0.1 — Aspect Re-derivation (BPHS Ch.7, Cited)

### The BPHS Ch.7 Rule

BPHS Ch.7 ("Aspects of Planets") states:

> All planets cast a full aspect on the **7th house** from their position.
> **Mars** additionally aspects the **4th and 8th** (full aspect).
> **Jupiter** additionally aspects the **5th and 9th** (full aspect).
> **Saturn** additionally aspects the **3rd** (¼ aspect) and **10th** (¾ aspect).

Rahu/Ketu: Per the majority Parashari authority (Sarvartha Chintamani, Phala Deepika
commentary), nodes aspect the **5th, 7th, and 9th** — same offsets as Jupiter. This is
a modal majority; some schools omit node special aspects. The writer's choice is
documented here and in code.

Saturn's 3rd aspect strength is 1/4 (25%), 7th is full (100%), 10th is 3/4 (75%) —
per Parashara's own grading in Ch.7.

### Canonical Table Verdict: CORRECT

`PARASHARI_ASPECTS` at **L414–428**:

```python
PARASHARI_ASPECTS: dict[str, dict[int, float]] = {
    "all":     {7: 1.0},
    "Saturn":  {3: 0.25, 7: 1.0, 10: 0.75},
    "Jupiter": {5: 1.0,  7: 1.0,  9: 1.0},
    "Mars":    {4: 1.0,  7: 1.0,  8: 1.0},
}
NODE_PARASHARI_ASPECTS: dict[int, float] = {5: 1.0, 7: 1.0, 9: 1.0}
```

Keys are **1-indexed house offsets**: offset 7 = 7th house from the aspecting graha.
This matches BPHS Ch.7 graha-by-graha:

| Graha   | BPHS Ch.7 Houses | Canonical Table Offsets | Match? |
|---------|-------------------|------------------------|--------|
| All     | 7th               | {7: 1.0}               | ✓      |
| Mars    | 4th, 7th, 8th     | {4:1.0, 7:1.0, 8:1.0}  | ✓      |
| Jupiter | 5th, 7th, 9th     | {5:1.0, 7:1.0, 9:1.0}  | ✓      |
| Saturn  | 3rd(¼), 7th, 10th | {3:0.25, 7:1.0, 10:0.75}| ✓     |
| Nodes   | 5th, 7th, 9th     | {5:1.0, 7:1.0, 9:1.0}  | ✓      |

**The canonical table is correct. No aspect redefinition needed.**

### Private Duplicate Tables — Architecture Problem

Two private helper functions in the file use a DIFFERENT offset convention
(0-indexed: `offset = (target_h - source_h) % 12 or 12`) and contain their own
aspect mappings. They produce the same correct results as the canonical table but
are SEPARATE code paths — a maintenance divergence risk.

**`_has_aspect` in `_build_sambandha_rows` (L4344–4355):**
```python
def _has_aspect(aspector: str, target_h: int) -> bool:
    h = g_house.get(aspector, 1)
    offset = (target_h - h) % 12 or 12        # 0-indexed: offset 6 = 7th house
    if aspector in ("Rahu", "Ketu"):
        return offset in {4, 6, 8}             # 5th/7th/9th — correct math
    if aspector == "Saturn":
        return offset in {2, 6, 9}             # 3rd/7th/10th — correct math
    if aspector == "Jupiter":
        return offset in {4, 6, 8}             # 5th/7th/9th — correct math
    if aspector == "Mars":
        return offset in {3, 6, 7}             # 4th/7th/8th — correct math
    return offset == 6                          # 7th — correct math
```

**`_lord_aspects_house` in `_build_bhava_web_rows` (L4576–4587):**  
Identical body to `_has_aspect` — complete duplication.

**Math check**: Converting 0-indexed offsets to 1-indexed:
- offset=6 → 7th house ✓ · offset=4 → 5th ✓ · offset=8 → 9th ✓
- offset=2 → 3rd ✓ · offset=9 → 10th ✓ · offset=3 → 4th ✓ · offset=7 → 8th ✓

Both private helpers are **mathematically correct but architecturally wrong**: they
duplicate logic that already lives in `PARASHARI_ASPECTS`. If the canonical table is
ever updated (e.g., Saturn 3rd strength changed from 0.25 to 0.375), the private
tables will silently diverge.

**Fix (STEP 1):** Write one canonical helper:
```python
def _graha_aspects_house(aspector: str, source_h: int, target_h: int) -> float:
    """Return aspect strength (0.0 = no aspect) from PARASHARI_ASPECTS."""
    offset_1indexed = ((target_h - source_h) % 12) or 12
    if aspector in ("Rahu", "Ketu"):
        return NODE_PARASHARI_ASPECTS.get(offset_1indexed, 0.0)
    table = PARASHARI_ASPECTS.get(aspector, PARASHARI_ASPECTS["all"])
    base = table.get(offset_1indexed, 0.0)
    # Also check "all" for planets with special aspects (they also cast 7th)
    if base == 0.0 and aspector in PARASHARI_ASPECTS:
        base = PARASHARI_ASPECTS["all"].get(offset_1indexed, 0.0)
    return base
```

Collapse both `_has_aspect` and `_lord_aspects_house` to call this helper.
After the fix: ONE aspect-offset source in the file. Grep confirms no other
private offset literal tables exist beyond these two.

### Combustion Bug — L2530–2532 (Two Bugs)

In `_build_special_state_rows`:
```python
sun_dist = abs(long_deg - sun_long)
if sun_dist > 180:
    sun_dist = 360 - sun_long   # BUG 1: should be 360 - sun_dist
is_combust = (sun_dist < 8.0 and g_name not in {"Sun", "Moon"})  # BUG 2: wrong orb
```

**Bug 1 (L2531):** `360 - sun_long` uses the Sun's longitude, not the computed arc.
Example: Sun at 300°, planet at 10°. `sun_dist = |10-300| = 290 > 180`, so correct arc
= 360-290 = 70°. But code computes 360-300 = 60° (wrong). Fix: `360 - sun_dist`.

**Bug 2 (L2532):** Hardcoded orb of 8° for all planets. `COMBUSTION_ORBS` at L163–168
defines per-planet classical orbs (Moon 12°, Mars 17°, Mercury 14°/12°R, Jupiter 11°,
Venus 10°/8°R, Saturn 15°) but is NOT consulted here.

**Canonical reference:** `_build_combustion_retrograde_relationship_rows` (L4233–4270)
is correct — uses `COMBUSTION_ORBS.get(name, 0.0)` and `diff = 360.0 - diff`.
Fix: unify `_build_special_state_rows` combustion check onto this same logic.

### Dead Jaimini Sign-Type Branching — L938–948

```python
if s1_type == "fixed":
    has_aspect = offset not in [1, 11]
elif s1_type == "movable":
    has_aspect = offset not in [1, 11]
else:  # common
    has_aspect = offset not in [1, 11]
```

All three branches are identical → dead code. The branching implies differentiation
that is not implemented. Fix documented in §0.2 below.

---

## §0.2 — Per-Varga Applicability Table (All 30 Vargas, No Exceptions)

`ALL_30_VARGAS` constant at L136 = 16 shodasha + 11 supplementary + 3 Nadi = 30 total.

### Degree availability in chart_divisionals — confirmed

`chart_divisionals` stores `degree_in_sign` (NUMERIC 0.0–30.0) for every graha per
varga. `_load_varga_positions` (L686–740) reads it as `degree` in the returned dict.
Full varga longitude for any graha:

```python
varga_longitude = (sign_num - 1) * 30.0 + degree   # degree = degree_in_sign
```

This value is computed by PyJHora's divisional algorithm — it is a real computed value,
not a projection from D1. It is available for every varga that GA6 has written to
`chart_divisionals`. Degree-based computation is therefore uniform across all vargas.

**Documented exception:** Vargas for which GA6 has no rows in `chart_divisionals` are
handled by the existing missing-varga guard at L3735–3741 (logs `VARGA_MISSING`, skips).
This is not a ga_structural gap — GA6 governs which vargas are computed. If a Nadi varga
(D108, D150, D2700) or a supplementary varga has no GA6 data, ga_structural skips it and
logs the warning. Nothing is silently dropped from the documented scope; the skip is
auditable in the build log.

### Current per-varga loop (already correct)

`_build_varga_aspect_rows` (L3713–3764) loops over ALL_30_VARGAS and calls:
- `_build_varga_relationship_rows` — conjunctions, parivartanas, dispositor chains,
  vargottama per varga ✓
- `_build_karaka_web_rows` — karaka inter-relationship web per varga ✓
- `_build_argala_rows` — 144-cell argala/virodha matrices per varga ✓

### D1-only builders that MUST be brought into the per-varga loop

Degree-based computation is used uniformly — same formula for D1 and every non-D1 varga.
Sign-occupancy is NOT the basis for any distance-based computation (conjunctions, yuddha,
combustion) after this rebuild.

| Builder function | Current scope | Target scope | Varga-space basis |
|---|---|---|---|
| `_build_aspect_rows` (Parashari, Tajik, conjunction_within_orb) | D1-only | All 30 vargas | Degree-based from varga longitude |
| `_build_sambandha_rows` (4-fold grade) | D1-only | All 30 vargas | Degree-based from varga longitude |
| `_build_bhava_web_rows` (bhava-significance-link) | D1-only | All 30 vargas | House-based from varga house assignments |
| `_build_net_argala_rows` | D1-only | All 30 vargas | Sign-occupancy (argala is sign-based by classical rule) |
| `_build_graph_theoretic_rows` (centrality/COG) | D1-only | All 30 vargas | Varga dispositor structure |
| `_build_nway_config_rows` (stelliums, clusters) | D1-only | All 30 vargas | Degree-based from varga longitude |
| `_build_graha_yuddha_rows` (planetary war) | D1-only | All 30 vargas | Degree-based from varga longitude ⚑ ASSUMPTION |
| `_build_combustion_retrograde_relationship_rows` | D1-only | All 30 vargas | Degree-based from varga longitude ⚑ ASSUMPTION |

**Pattern for all D1→all-30 expansion:** Each builder receives a `varga_state` dict
(already the pattern for `_build_varga_relationship_rows`) and operates on
`varga_longitude = (sign_num - 1) * 30.0 + degree` for each graha.

### ⚑ Modeling assumption: graha-yuddha and combustion in varga space

Graha-yuddha (planetary war) and combustion are **classically physical-sky phenomena**:
they refer to arc-distance between bodies in the observable ecliptic. A divisional chart
has no physical sky — `degree_in_sign` in D9 or D30 is a mathematical mapping produced
by an integer-division algorithm; there is no physical conjunction of celestial bodies
at those positions.

**Native decision (2026-06-19):** Despite this, RECOMPUTE both graha-yuddha and
combustion across all 30 vargas from varga-space longitudes. Rationale: the varga degrees
are real computed values (PyJHora DE441 ephemeris), the extension is deterministic and
auditable, and the all-30-varga completeness ruling supersedes classical limits.

This is an **explicit modeling assumption**, not a cited verse or settled tradition. It is
documented at three levels:
1. Here in this logic document (permanent audit record).
2. In the docstring of each expanded builder function (code-level).
3. In `value_jsonb` of every row emitted: `"varga_assumption": "physical_phenomenon_extended_to_mathematical_varga"`.

A reviewing acharya or L2 reader seeing this flag knows: "this combustion/yuddha detection
is structurally consistent but carries no classical authority for this varga."

**Combustion orb sub-assumption (unchanged from prior review):** Classical orbs
(Moon 12°, Mars 17°, Mercury 14°, Jupiter 11°, Venus 10°, Saturn 15°) are applied to
varga-space arc. Same assumption flag applies. Rahu/Ketu: orb=0 (unchanged — nodes are
mathematically combust-immune by definition in most schools).

### Jaimini dead-branching fix (per this section)

Jaimini rasi drishti per Jaimini Sutras (1.1.28): Fixed signs aspect movable and common;
movable signs aspect fixed and common; common signs aspect movable and fixed. In all three
cases, the sign immediately before (12th, offset=11) and the sign immediately after (2nd,
offset=1) of the SAME modality are excluded.

The current implementation of `offset not in [1, 11]` happens to approximate the majority
reading for fixed and movable signs (excluding immediate neighbors). For common signs, some
authorities say they aspect ALL others including immediate neighbors; others say same
exclusion. Since the dead-branching means all three share the same rule today, the fix is:

- **Fixed signs**: `offset not in [1, 11]` — keep (correct per majority)
- **Movable signs**: `offset not in [1, 11]` — keep (correct per majority)
- **Common signs**: `offset not in [1, 11]` — keep for consistency (majority view);
  document as a modeling assumption (some authorities give common signs full 11-sign scope)

This makes the branching meaningful: even though the bodies are currently identical, they
now carry explicit comments and could be differentiated if school-specific mode is added.

### Expected category × varga matrix (post-rebuild)

For verification after STEP 2, each category should appear for all vargas where applicable:

| Category | D1 | D2–D60 (16 shodasha) | Supplementary 11 | Nadi 3 | Notes |
|---|---|---|---|---|---|
| aspect_parashari_given/received | ✓ | ✓ | ✓ | ✓ | house-based, recompute per varga |
| conjunction_per_varga | ✓ | ✓ | ✓ | ✓ | same-sign for non-D1 |
| conjunction_within_orb | ✓ | ✓ | ✓ | ✓ | degree-based for D1, same-sign for others |
| aspect_tajik | ✓ | ✓ | ✓ | ✓ | recompute from varga longitudes |
| sambandha_grade | ✓ | ✓ | ✓ | ✓ | 4-fold per varga |
| parivartana_per_varga | ✓ | ✓ | ✓ | ✓ | already in loop |
| dispositor_chain_per_varga | ✓ | ✓ | ✓ | ✓ | already in loop |
| argala_natal_matrix | ✓ | ✓ | ✓ | ✓ | 144 cells, already in loop |
| virodha_argala_natal_matrix | ✓ | ✓ | ✓ | ✓ | 144 cells, already in loop |
| net_argala | ✓ | ✓ | ✓ | ✓ | expand to all vargas |
| bhava_significance_link | ✓ | ✓ | ✓ | ✓ | expand to all vargas |
| combustion_relationship | ✓ | ✓ | ✓ | ✓ | recompute, explicit assumption |
| graha_yuddha | ✓ | ✓ | ✓ | ✓ | recompute from varga longitudes |
| graph_theoretic (centrality etc.) | ✓ | ✓ | ✓ | ✓ | expand to all vargas |
| nway_config (stelliums etc.) | ✓ | ✓ | ✓ | ✓ | expand to all vargas |

Any category missing from a varga in the STEP 2 breakdown = bug.

---

## §0.3 — Drop/Inflation Ledger

### Drops to REMOVE (silent suppression of valid relationships)

| Location | Code | Verdict | Fix |
|---|---|---|---|
| L3387–3388 | `if orb > 10.0: continue` (conjunction in varga loop, D1 degree-based path) | REMOVE | Emit graded strength + `salience` in jsonb; no orb ceiling |
| L1042–1043 | Tajik: `else: continue` (orb > 30°) | REMOVE | Emit with `salience="low"` and strength=0.1 |

**Salience column spec:** Add a `salience` field to the `value_jsonb` (not a separate column):
`"salience": "high"` (orb ≤5°), `"medium"` (5–15°), `"low"` (15–30°). L2 thresholds at serve-time.

**On the dropped orb gate at L3387:** The `_build_varga_relationship_rows` function
distinguishes D1 (degree-based orb) from non-D1 (same-sign). After the rebuild, both
are degree-based, so the 10° ceiling at L3387 applies to the D1 path that BECOMES the
universal path. The fix is the same: remove the ceiling universally.

For non-D1 vargas (previously same-sign only, conjunction iff sign1==sign2):
- Two grahas in the same varga sign may have `degree_in_sign` values up to 29° apart.
- The rebuilt builder computes `orb = |varga_long1 - varga_long2|` (capped at 180°) and
  emits with graded salience. Cross-sign orbs ≤30° are also emitted (this CAN cross a
  sign boundary in varga space).
- Same-sign same-degree = orb 0° = full strength = physical conjunction equivalent.
- This supersedes the prior same-sign boolean treatment uniformly.

### Drops to KEEP (true non-relationships or definitional)

| Location | Code | Verdict | Reason |
|---|---|---|---|
| L929, L933 | `if s1_idx == s2_idx: continue` (Jaimini) | KEEP | Self-aspect is definitional non-relationship |
| L3429 | `if lord1 == g1: continue` (parivartana) | KEEP | A planet in its own sign is not parivartana |
| L3440 | `_seen_parivartana` dedup | KEEP | A↔B and B↔A are the same pair; emit once |
| L3364 | `for i, g1 in enumerate(ALL_GRAHAS): for g2 in ALL_GRAHAS[i+1:]` | KEEP | Upper triangle dedup; avoids Sun-Mars + Mars-Sun duplicate |

### Conjunction_within_orb (already correct in `_build_aspect_rows`)

The D1 outer conjunction builder at L963–997 already emits up to 30° with graded strength:
- ≤5°: strength=1.0 · ≤10°: 0.75 · ≤20°: 0.5 · ≤30°: 0.25
- No `continue` drop above 30° — correct, already fixed.

The per-varga conjunction builder inside `_build_varga_relationship_rows` is the one
with the remaining >10° gate (L3387). After the rebuild this builder uses
`varga_longitude = (sign_num-1)*30 + degree` for all vargas, and the ceiling is removed.

### Contradiction_pair — Redefinition

**Current implementation (L5159–5219):** Groups by `fact_subject`, checks if any row on
that subject is in `BENEFIC_SOURCE_CATS` (yoga_fires, argala_natal_matrix) AND any row is
in `MALEFIC_SOURCE_CATS` (dosha_fires, virodha_argala_natal_matrix). One contradiction row
per subject regardless of relationship type or varga.

**Problem:** A house can simultaneously receive yoga_fires from one category and
virodha_argala from a completely different category — these cross-type tensions are real but
are not the same "contradiction" as opposing valences on the SAME relationship type.
Over-counting inflates the total significantly.

**Correct redefinition:**
A contradiction pair is: same `fact_subject` + same varga + opposing valence on **the SAME
`fact_category` type**. Examples:
- `net_argala` for `HOUSE_5` with value>0 (argala wins) AND value<0 (virodha wins) across
  two different vargas → valid multi-varga contradiction
- `yoga_fires` for `SUN` firing in D1 AND `dosha_fires` for `SUN` firing in D1 →
  valid contradiction (same entity, same varga, opposing on yoga/dosha which are the
  same relationship-type family)
- `yoga_fires` for `HOUSE_5` AND `virodha_argala_natal_matrix` for `HOUSE_5` →
  NOT a contradiction pair; these are structurally different relationship types

**Implementation:** Group by `(fact_subject, fact_category_family, varga)` where
`fact_category_family` collapses `yoga_fires`/`yoga_label` → "yoga" and
`dosha_fires`/`dosha_label` → "dosha". Emit only when opposing valences appear within
the same family+varga combination.

**Expected outcome:** Count drops materially (≥50%). This is correct — the prior count was
inflated by cross-category pairings that are not genuine contradictions.

---

## §0.4 — Ingest-Gap Closure Plan (GAP 1–4)

### GAP-1: `_load_special_points` extends to full sensitive-point family

**Current state (L2940–3009):** Queries only 3 `fact_category` values:
- `upagraha_position` (keys: `sign`, `house`, `longitude`)
- `sensitive_point_gulika_mandi` (keys: `sign`, `house_d1`, `longitude_sidereal`)
- `sun_derived_upagraha` (keys: `sign`, `house_d1`, `longitude_sidereal`)

**Missing categories (GA5 output, all in chart_facts):**
- `special_lagna` — Arudha Lagna, Bhava Pada, Ghati Lagna, etc. (keys: `sign`, `house_d1`, `longitude_sidereal`)
- `arudha_pada` — ~285 rows per ayanamsha (keys: `sign`, `house_d1`, `longitude_sidereal`)
- `saham_position` — ~2,800 rows per ayanamsha (keys: `sign`, `house_d1`, `longitude_sidereal`)
- `esoteric_point_*` — wildcard match; use `LIKE 'esoteric_point_%'` (same keys)
- `saturn_derived_point` (keys: `sign`, `house_d1`, `longitude_sidereal`)
- `aprakasha_position` (keys: `sign`, `house_d1`, `longitude_sidereal`)

**Fix:** Extend the second query in `_load_special_points` to:
```sql
AND fact_category IN (
    'sensitive_point_gulika_mandi', 'sun_derived_upagraha',
    'special_lagna', 'arudha_pada', 'saham_position',
    'saturn_derived_point', 'aprakasha_position'
)
```
Plus a separate query using `LIKE 'esoteric_point_%'` for the wildcard family.

Each newly loaded sensitive point becomes a relationship participant in
`_build_special_point_relationship_rows`: it receives Parashari aspects from the 9
grahas, and any co-placed graha fires a conjunction row. Expected: thousands of
additional valid relationship rows (saham alone adds ~2,800 participants per ayanamsha).

### GAP-2: `_build_composite_strength_rows` — replace inline proxies

**Current proxies (L2129–2148):**
```python
bhava_bala_proxy = {h: (1.0 if h in {1,4,7,10} else 0.75 if h in {2,5,8,11} else 0.5) ...}
dignity_to_strength = {"exalted": 1.0, "own_sign": 0.75, "neutral": 0.5, ...}
shadbala_proxy = sthana * 5.0 + 1.0   # rough rupa estimate
```

**Fix:** Query `chart_facts` for the real values:
- Replace `bhava_bala_proxy[h]` with the `house_bhava_bala_total` fact_id for house `h`
  (GA3 output, fact_category=`house_bhava_bala_total`, fact_subject=`HOUSE_{h}`).
- Replace `dignity_to_strength` + `shadbala_proxy` computation with
  `graha_shadbala_total` fact_id for the graha (GA3 output,
  fact_category=`graha_shadbala_total`, fact_subject=graha_subject).
- Store the referenced fact_ids in `constituent_facts_array` so L2 can resolve them.

`constituent_facts_array` entries must be live fact_ids (verified by SELECT from
`chart_facts` using those ids) — zero proxy strings remain.

### GAP-3: `_build_karakatva_rows` — replace inline dignity/house proxy

**Current proxy (L2274–2280):**
```python
karaka_strength = {"exalted": 1.0, "own_sign": 0.875, ...}.get(dignity, 0.5)
house_strength = (1.0 if karaka_house in {1,4,7,10} else 0.75 if h in {5,9} else 0.5)
```

**Fix:** Reference `ashtakavarga_bindu_per_varga` or `graha_shadbala_total` from
chart_facts. The `composite_strength` for a significator's karaka should read the
actual GA3 strength value, not an inline approximation. Store fact_id in
`constituent_facts_array`.

Also add `ga_condition` to the writer's `depends_on` in the orchestrator writer
`platform/python-sidecar/pipeline/orchestrator/writers/ga_structural.py`
(currently missing — confirmed by grep returning no matches).

### GAP-4: `_build_nakshatra_dispositor_chain_rows` — reference, not recompute

**Current (L4419–4468):** Re-derives from `longitude → nakshatra → NAKSHATRA_LORDS`
in Python. This diverges from whatever GA4/ga_nakshatra wrote into `chart_facts`.

**Fix:** Read the canonical `nakshatra_dispositor_chain` rows that ga_nakshatra already
emitted (fact_category=`nakshatra_dispositor_chain`, fact_subject=graha_subject). Emit a
`nakshatra_dispositor_chain` row in ga_structural that REFERENCES the GA4 row's fact_id
in `constituent_facts_array` rather than recomputing. If the GA4 row is not found, log
WARNING and skip (do not recompute — that would violate L1-authority §N.5).

Add `ga_nakshatra` to `depends_on` in the orchestrator writer (currently absent).

### Root-cause note (sealing-discipline lesson)

These four gaps were documented in `FOUNDATION_COMPLETION_HANDOFF §3` as known and
deferred. The "ga_structural COMPLETE" seal was applied based on the maximal-depth half of
the spec (the Phase-2 depth additions: sambandha, bhava_web, graph-theoretic, etc.) while
the maximal-ingest half (full sensitive-point family, real strength references, nakshatra
chain reference) remained open.

**Lesson:** An asset must not be sealed on a partial scope. The seal implies the spec is
fully satisfied. Partial completion should be marked `PARTIAL_COMPLETE` with an explicit
open-items list, not `COMPLETE`. This pattern produced the current rebuild session.

---

## §0.5 — Phase-3 Blind-Spot Designs (All Across 30 Vargas, Same Rule)

### 1. Virupa-graded drishti (continuous graded aspect)

**Problem:** `_has_aspect` in sambandha/bhava_web is boolean. The PARASHARI_ASPECTS table
already encodes strength (Saturn 3rd = 0.25, 10th = 0.75; others = 1.0) but this
information is discarded in the private boolean helpers.

**Design:** New category `virupa_drishti` (distinct from `aspect_parashari_given`):
```
fact_category = virupa_drishti
fact_subject  = {GRAHA_SUBJECT}
fact_key      = house_{N}_offset_{offset}
value_num     = strength (0.0–1.0 per PARASHARI_ASPECTS)
value_jsonb   = {aspector, target_house, offset, strength, varga}
```
One row per (aspector, target_house, varga) with continuous strength. Emitted across all
30 vargas. BPHS Ch.7 citation per row. Boolean aspect rows remain for backward compat;
virupa rows add the graded signal.

### 2. Bhinnashtakavarga inter-graha contribution edges

**Sources:** GA3 already emits `ashtakavarga_kakshya` rows (fact_category=
`ashtakavarga_kakshya`, value_jsonb containing per-kakshya contributing grahas).

**Design:** New category `bav_intergraha_contribution`:
```
fact_category = bav_intergraha_contribution
fact_subject  = {contributing_graha}_to_sign_{sign_num}
fact_key      = sign_{sign_num}
value_num     = bindu_contribution (0 or 1 per kakshya, summed across kakshyas)
value_jsonb   = {contributor, sign, house, ashtakavarga_bindu_total, ayanamsha_id}
constituent_facts_array = [ashtakavarga_kakshya fact_id for this graha+sign]
```
Computed per varga (GA3 has per-varga BAV). Reads from chart_facts WHERE
fact_category='ashtakavarga_kakshya'. No recomputation.

### 3. Nakshatra co-tenancy + tara + nakshatra-lord relationships

**Source:** `graha_nakshatra_join` rows in chart_facts (GA4 output, currently UNREAD by
ga_structural). These contain each graha's nakshatra assignment.

**Co-tenancy design:** New category `nakshatra_co_tenancy`:
```
fact_subject = {nak_name}
fact_key     = co_tenant_{graha1}_{graha2}
value_jsonb  = {nakshatra, grahas: [g1, g2, ...], house_d1}
constituent_facts_array = [graha_nakshatra_join fact_ids for both grahas]
```
D1 only (nakshatra positions don't vary by varga within an ayanamsha).

**Tara design:** New category `tara_bala`:
```
fact_subject = {GRAHA_SUBJECT}
fact_key     = tara_count_from_moon
value_num    = tara integer (1–9), cyclically from Moon nakshatra
value_text   = tara_name (janma/sampat/vipat/kshema/pratyak/sadhaka/naidhana/mitra/atimitra)
constituent_facts_array = [graha_nakshatra_join for this graha, graha_nakshatra_join for Moon]
```
Structural fact. D1 per ayanamsha.

**Nakshatra-lord relationship design:** New category `nakshatra_lord_relationship`:
```
fact_subject = {GRAHA_SUBJECT}
fact_key     = nakshatra_lord
value_text   = lord_graha_name
value_jsonb  = {graha, nakshatra, lord, lord_house_d1, lord_sign}
constituent_facts_array = [graha_nakshatra_join fact_id]
```
One row per graha. D1 per ayanamsha.

### 4. Bhava-chalit vs rasi divergence flag

**Source:** `bhava_chalit_house` or `bhava_chalit_sign` from chart_facts (GA1/GA5 output).

**Design:** New category `bhava_chalit_rasi_divergence`:
```
fact_subject = {GRAHA_SUBJECT}
fact_key     = diverges_from_rasi
value_text   = "true" | "false"
value_jsonb  = {rasi_house, chalit_house, rasi_sign, chalit_sign, diverges}
constituent_facts_array = [bhava_chalit_house fact_id, graha position fact_id]
```
Only emit when `diverges = true` (no-op rows add noise). One row per graha per ayanamsha.
D1 only (bhava-chalit is a D1 concept).

### 5. Significator path-analysis (§2.5/§6 of original spec, currently unimplemented)

**Source:** Dispositor tree already built by `_build_dispositor_tree_rows` and
`_build_graph_theoretic_rows`. Final dispositor per graha is already emitted.

**Design:** New category `significator_path`:
```
fact_subject = {GRAHA_SUBJECT}_to_{TARGET_GRAHA_SUBJECT}
fact_key     = shortest_path_length
value_num    = number of hops (1 = direct lord, 0 = self, None/null = no path)
value_jsonb  = {
    from_graha, to_graha, path: [g1, g2, ..., gN],
    path_length: N, varga
}
```
Compute via BFS on the dispositor graph (each graha points to its sign lord). Emit for
all (graha, target_graha) pairs. Across all 30 vargas (graph structure varies per varga).
Classification:
- path_length 1 = direct disposal → "tightly_coupled"
- path_length 2–3 = intermediate → "mediated"
- path_length ≥4 or None = "remote" or "isolated"

No external computation required — dispositor graph is fully deterministic from varga
positions already loaded.

---

## Summary — Changes Required (Preview for STEP 1)

| Category | Issue | Fix type |
|---|---|---|
| `_has_aspect` + `_lord_aspects_house` | Duplicate private tables | Collapse to `_graha_aspects_house` canonical helper |
| `_build_special_state_rows` L2531 | `360 - sun_long` → wrong | Fix to `360 - sun_dist` |
| `_build_special_state_rows` L2532 | Hardcoded 8° orb | Replace with `COMBUSTION_ORBS[g_name]` |
| Jaimini dead branching L938–948 | All branches identical | Add explicit comments; differentiate if school mode added |
| D1-only builders | 8 builders not in varga loop | Extend `_build_varga_aspect_rows` orchestrator |
| D1 conjunction >10° drop L3387 | Silent suppression | Remove gate, add `salience` to jsonb |
| Tajik >30° drop L1042 | Silent suppression | Remove gate, emit `salience="low"` |
| contradiction_pair definition | Inflated cross-type counting | Redefine: same entity + same varga + same category-family |
| `_load_special_points` | 3 categories only | Extend to full 8+ sensitive-point family |
| Composite strength proxies L2129–2148 | Inline approximations | Reference real GA3 fact_ids |
| Karakatva proxies L2274–2280 | Inline approximations | Reference real GA3 fact_ids |
| `_build_nakshatra_dispositor_chain_rows` | Re-derives (diverges from GA4) | Reference GA4 fact_ids |
| `depends_on` missing `ga_condition`, `ga_nakshatra` | Writer has wrong deps | Add to orchestrator writer |
| Phase-3 blind spots (5 types) | Unimplemented | Implement per §0.5 designs |

---

*End of GA_STRUCTURAL_REBUILD_LOGIC_v1_0.md — AWAITING_NATIVE_APPROVAL before STEP 1.*
