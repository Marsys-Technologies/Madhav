---
lane: F-117
stream: S3_SATYA (spec) -> [L2 Bodha owner, TBD by conductor] (build)
stage: S (SPEC)
class: CL-09 earned signal (TIER3-EXPERIENCE)
author: SATYA-SPEC (sonnet)
status: DRAFT — awaiting VERIFIER review
---

# SPEC — bo_upaya resonance ranking: dead/flat composite inputs + undisclosed rank-relative labels

## 0. Lease note (read first — unchanged from DIAGNOSIS.md §0)

Every file this spec touches (`bo_upaya.py`, `bo_cgm_motifs.py`,
`query_remedies.ts`) is **L2 Bodha**, outside S3 SATYA's owned lease
(`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`, `muhurta.py`). This document is
Stage-S output only — S3 does not build against these files. It is written to be
directly executable by whichever stream the conductor routes L2 Bodha `bo_*`
writers + `L2_bodha/` retrieval layers to (a `PAR-F117-NEEDS-LEASE` marker is
posted per the parent task). Every file path, function name, and line number
below was read live from the worktree at spec time (2026-08-16) — the builder
does not need to have seen the diagnosis conversation to execute this.

**This spec supersedes DIAGNOSIS.md on one point:** the diagnosis (§3, C1) left
open whether `contradiction_factor=0` for all grahas was chart-specific
coincidence or an upstream bug, flagging it "outside the 45-minute diagnosis
window to fully rule out." This spec closes that gap — see §1 and §2a. It is a
**confirmed structural bug**, not chart-specific coincidence.

## 1. Root-cause statement

`resonance_score_v1()`'s weakness-composite formula (`formulas.py:257-294`) is
correct math operating on four differentiating input terms that
`bo_upaya._build_resonances_and_prescriptions()` (`bo_upaya.py:1062-1183`)
populates for each graha; three of those four terms collapse to zero or a flat
constant for every graha in every chart because of three independent upstream
defects — a graha-identifier format mismatch that silently drops 7 of 9 grahas'
dosha associations (`contradiction_factor`, confirmed structural, not
chart-specific), a genuinely dead/never-populated L1 column left at an honest
placeholder while a *different*, real, already-fetched per-graha CDLM value
sits unused two lines below it in the same function (`domain_burden`), and a
flat per-motif-*class* strength literal one file upstream that overrides a
real per-edge computed value already present on every row the caller reads
(`motif_burden`) — collapsing the visible ranking to be effectively
shadbala/bhava_bala-driven alone; independently, the Rahu/Ketu shadbala
fallback and the rank-relative `"critical"` label are each computed correctly
and by design, but neither discloses its true nature (missing-classical-data
fallback; chart-relative-thirds framing) in the narration a caller actually
reads, which is a separate, narration-fidelity-class defect, not a computation
bug.

**Chart-specific vs. structurally broken — the explicit determination requested:**
- **C1** (`contradiction_factor`): **structurally broken**, confirmed live
  against chart 482012f1 — see §2a. NOT chart-specific.
- **C2** (`domain_burden`): **structurally broken**, for every chart, by the
  writer's own comment — see §2b.
- **C3** (`motif_burden`): **structurally broken**, for every chart — the flat
  `0.4` this chart shows is not a chart-specific coincidence, it is the
  deterministic output of a flat per-*class* literal applied regardless of
  which grahas/edges are involved — see §2c.
- **C5** (Rahu/Ketu `sha=1.00`): **not a ranking bug** — see §2d for why the
  diagnosis's "inflates priority" framing does not survive a check of the
  clamping math, and what the real, narrower defect is.
- **C6** (`"critical"` label): **confirmed-as-designed** computation, confirmed
  narration gap — see §2e.

## 2. Files to change

### 2a. `contradiction_factor` — fix the graha-identifier mismatch (structural bug, all charts)

**File:** `platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py`,
function `_fetch_active_doshas_by_graha` (starts line 808), the graha-matching
loop at **lines 837-844**:

```python
for cr in crows:
    subj = str((cr[0] if isinstance(cr, (tuple, list)) else cr.get("fact_subject")) or "").upper()
    for graha in KNOWN_GRAHAS:
        if subj == graha.upper():
            label = dosha_name or dosha_id
            out.setdefault(graha, [])
            if label not in out[graha]:
                out[graha].append(label)
```

**What:** replace the raw `subj == graha.upper()` string compare with the
canonical L1-code → Title-case translator, `to_title()` from
`brahmagyan.graha_vocabulary` (already imported for exactly this purpose
elsewhere in the writers directory — see below):

```python
from brahmagyan.graha_vocabulary import to_title
...
for cr in crows:
    subj_raw = str((cr[0] if isinstance(cr, (tuple, list)) else cr.get("fact_subject")) or "")
    graha_name = to_title(subj_raw)
    if graha_name in KNOWN_GRAHAS:
        label = dosha_name or dosha_id
        out.setdefault(graha_name, [])
        if label not in out[graha_name]:
            out[graha_name].append(label)
```

**Why (mechanism, verified live, not inferred):** `chart_facts.fact_subject`
stores L1's 3-letter/mean-node codes (`SUN, MOON, MAR, MER, JUP, VEN, SAT,
RAH_MEAN, KET_MEAN`); `KNOWN_GRAHAS` (`bo_upaya.py:48-51`) is Title-case full
names (`"Sun","Moon","Mars",...`). `subj.upper() == graha.upper()` can only
ever match **Sun** and **Moon** (whose 3-letter codes happen to equal their
full uppercased names) — it structurally can never match Mars, Mercury,
Jupiter, Venus, Saturn, Rahu, or Ketu, on any chart, any build. Verified
against the canonical chart via direct SQL
(`chart_id=482012f1-710e-4a25-994a-93821f5871aa`, `ayanamsha_id=lahiri_chitrapaksha`):
this build's one real `fires=true` `dosha_label` row is Manglik
(`fact_id=2ed777c21b86b03d`), whose `constituent_facts_array` resolves to two
`chart_facts` rows **both with `fact_subject='MAR'`** —
```sql
SELECT fact_id, fact_subject, fact_category, fact_key FROM chart_facts
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND ayanamsha_id='lahiri_chitrapaksha'
  AND fact_id IN ('61ff5df8420a8b45','6a2dd6c96896f8dd');
-- → both rows: fact_subject='MAR', fact_category='graha_position'
```
i.e. Mars genuinely has an active, `fires=true` dosha on this chart — the
function's own logic is designed to find exactly this — yet `'MAR' !=
'MARS'`, so `dosha_by_graha['Mars']` never receives it. This is why the live
reproduction shows `contradiction_factor=0` for **every** graha: not because
this chart has zero active dosha-graha associations (the diagnosis's open
question), but because the lookup can structurally never succeed for 7 of 9
grahas.

**Precedent (this is not a novel fix pattern):** this is the *exact same
defect class*, in the *same directory*, already found and fixed once before —
`bo_bimba.py`'s `_fetch_graha_positions` had the identical bug
(`subject.title()` instead of the SSoT translator), fixed via `_SUBJECT_TO_GRAHA
= {code: to_title(code) for code in (...)}` (`bo_bimba.py:45-56`, comment:
"subject.title() only worked for SUN→Sun and MOON→Moon ... causing 7/9 graha
nodes to get position_in_chart_jsonb=null" — the *identical* 7/9 failure
signature), imported from `brahmagyan.graha_vocabulary.to_title`
(`bo_bimba.py:26`). `platform/python-sidecar/tests/l2/test_bo_bimba_position_mapping.py`
is the existing regression-guard for that fix and is a direct structural model
for this spec's exit test (§3). Use `to_title()` directly (not a
re-derived local dict) per the R17 doctrine stated in
`brahmagyan/graha_vocabulary.py`'s own docstring: "every other Python graha
map in the codebase is retired to an import of `norm_graha`/`to_title`, not
duplicated."

### 2b. `domain_burden` — wire the real, already-fetched per-graha CDLM value (structural, all charts)

**File:** `bo_upaya.py`, `_build_resonances_and_prescriptions`, the
`ResonanceInputs(...)` construction, **line 1175**:

```python
# current
cdlm_weakest_constituent_count=0.0,
```

**What:** replace the literal `0.0` with a value derived from
`graha_cdlm_cells` — **already fetched** at line 1103
(`graha_cdlm_cells = _fetch_graha_cdlm_cells(conn, chart_id, aya)`) and
**already used** two fields later in the *same* dict literal for
`associated_cdlm_cells_array` (line 1213) and `associated_cdlm_cell_count`
(line 1241):

```python
cdlm_weakest_constituent_count=min(len(graha_cdlm_cells.get(graha) or []) / <N>, 1.0),
```

**Why:** the comment currently at lines 1172-1174 ("no real per-graha CDLM
value exists yet to reference") is **stale**, not currently true. It describes
`bodha_cdlm_cells.weakest_constituent_graha_jsonb` specifically, which
**is** confirmed genuinely dead — `bo_sangati.py`'s own `_CDLM_INSERT`
(lines 56-92) writes a literal `NULL` for that column on every row, every
chart (verified by reading the INSERT statement directly, not the comment). But
a *different*, real, per-graha CDLM signal was landed after that comment was
written: `_fetch_graha_cdlm_cells` (`bo_upaya.py:565-605`, "CR-67 / SARVA-SIDDHI
W-3") computes, per graha, the list of `bodha_cdlm_cells` the graha is a
material (salience-dominant) constituent of, joined through
`shared_signal_ids_array` (a column `bo_sangati` **does** populate). This is
real, L1/L2-traceable, chart-varying data sitting unused for this one field.

**BUILD-STAGE DECISION, not spec-invented content (B.10):** the normalizing
divisor `<N>` is an open decision this spec does not fabricate. Before
implementing, Build must query the live distribution of
`associated_cdlm_cell_count` (already computed, line 1241) across a representative
build or two (e.g. `SELECT associated_cdlm_cell_count, count(*) FROM
bodha_rm_resonances GROUP BY 1`) and pick a divisor that produces a
non-degenerate 0..1 spread (do not invent an untested constant). If Build
judges the CR-67 "material constituent" semantic ("cells this graha
dominates by salience") is not close enough to the field's literal name
("weakest constituent count") to be an honest substitution, STOP and raise to
PRATINIDHI rather than deciding the semantic question unilaterally — the
alternative (leave `domain_burden` at the honest `0.0` until `bo_sangati` is
extended to populate `weakest_constituent_graha_jsonb` for real) is also a
legitimate, B.10-compliant outcome; this spec's position is that the CR-67
data is close enough and available now, but does not have the authority to
overrule PRATINIDHI on a semantic fit question.

### 2c. `motif_burden` — replace bo_cgm_motifs.py's flat per-class strength literals with the real per-edge `computed_strength` (structural, all charts) — the most consequential fix in this lane

**File:** `platform/python-sidecar/pipeline/orchestrator/writers/bo_cgm_motifs.py`

Three flat literals, all in functions that already receive `edge_by_from: dict[str,
list[dict]]` whose entries are fetched by a SELECT (line 772-773) that
**already includes `computed_strength`** — confirmed present on every edge row,
not fabricated for this spec:

- `_detect_mutual_reception` (starts line 239) — pair strength literal
  **`0.8`** at line 291.
- `_detect_mutual_aspects` (starts line 419) — pair strength literal **`0.6`**
  at line 461; triangle variant literal **`0.75`** at line 499.

**What:** for each motif, replace the literal with `min()` of the
`computed_strength` values of the constituent edges (same min-over-parts
philosophy already documented in this codebase for `bo_cgm_paths.path_strength`
and for `bo_upaya._fetch_cgm_motif_weakness`'s own docstring — "a chain/pattern
is only as strong as its weakest constituent", JL-013):
  - `_detect_mutual_reception`: currently tracks only `edge_id` per (from,to)
    pair in `disp_edges: dict[tuple[str,str], str]` (line 257) — extend to also
    capture `computed_strength` alongside `edge_id` when populating `disp_edges`
    (line 265), then use `min(strength_ab, strength_ba)` in place of `0.8`.
  - `_detect_mutual_aspects`: currently tracks only `edge_id` per direction in
    `asp: dict[str, dict[str, str]]` (line 437) — extend similarly, use
    `min(strength_ab, strength_ba)` in place of `0.6` for the pair motif, and
    `min()` across all three pair-edges in place of `0.75` for the triangle
    variant (lines ~470-499).
  - Guard: if `computed_strength` is `None` on a given edge (should not occur —
    `bo_karanajala.py` always writes it — but do not assume), coalesce to the
    current literal as a documented fallback so a missing value degrades
    honestly rather than crashing the build.

**Why — mechanism, verified upstream, not assumed:** these three literals are
the direct, confirmed cause of `motif_burden=0.4` identically for all 8
grahas in the live reproduction (per DIAGNOSIS.md §3's derivation:
`1.0 - MIN(motif_strength) = 1.0 - 0.6 = 0.4` when every graha's only
reachable motif membership is a `mutual_aspect`, since `mutual_reception` and
`stellium`/`parivartana_chain` are gated off for this chart per the
diagnosis). Crucially, a real, non-constant, salience-derived per-edge
`computed_strength` **already exists and is already fetched** — it is not
something this spec invents:
- `bo_karanajala.py:1225-1237` (the 'aspect'/'conjunction' edge emitter) calls
  `_edge_strength_v1(round(salience, 6), graha, list(domains), lookups)` — a
  real, per-instance MSR-salience-derived value, confirmed varying (not a
  class-level constant) — and writes it to `computed_strength` on every
  aspect edge.
- `bo_cgm_motifs.py:770-777`'s own edge fetch already selects
  `computed_strength` into every row of `all_edges`/`edge_by_from` — it is
  sitting unused in the exact dict the three detector functions already
  iterate.

**Known sub-nuance, flagged not resolved:** `_detect_mutual_reception`'s
underlying `dispositor` edges get `computed_strength` from
`_edge_strength_v1(0.6, graha, None, lookups)` (`bo_karanajala.py:639`) — the
*base salience input* here is itself a flat `0.6` (not per-instance-varying
the way aspect edges' real MSR salience is), though `_edge_strength_v1`'s
`graha`-keyed lookups may still introduce some per-graha variance. This is a
strict improvement over bo_cgm_motifs's current single global `0.8` (real
per-pair variance vs. none), but Build/VERIFIER should confirm post-fix
`mutual_reception` strength is not itself degenerate-flat before treating this
sub-fix as fully resolved — flag as a possible narrower follow-up if so,
separate from the aspect-edge fix which is unambiguously real per-instance
data.

### 2d. Rahu/Ketu `sha=1.00` — narration-fidelity fix, NOT a ranking-math bug

**File:** `bo_upaya.py`, `citation_human` construction, **line 1255**:
```python
"citation_human": f"Resonance: {graha} | sha={sha_norm:.2f} dosha_count={len(dosha_by_graha.get(graha, []))}",
```

**Determination (reframing the diagnosis's C5 claim):** the diagnosis
characterizes this as "ranking them on it inflates their priority." Reading
the actual formula shows this does not hold: `ResonanceInputs.shadbala_normalized
= min(sha_norm, 1.0)` (line 1154) clamps **any** graha with a real ratio ≥1.0
to the exact same `1.0` (zero shadbala-term weakness contribution) that
Rahu/Ketu's fallback produces — and this chart's own live data shows Sun
(1.69) and Saturn (1.57) both clamp to that identical `1.0` alongside
Rahu/Ketu. The fallback is not privileging the nodes over genuinely strong
classical grahas in the score math; it is the documented, honest,
B.10-compliant neutral-default design already explained in `_fetch_shadbala`'s
own docstring (lines 200-221) and in the inline comment at lines 1130-1136.
**No change to the resonance formula or its inputs is warranted for C5.**

The real, narrower, confirmed defect: `citation_human` prints the raw,
pre-clamp `sha_norm` (`1.00` for Rahu/Ketu) using the **identical** `sha=X.XX`
format used for grahas with genuine L1-measured ratios (e.g. `sha=0.84` for
Venus, `sha=1.69` for Sun), with nothing distinguishing "real fetched ratio"
from "structural no-classical-requirement fallback" — even though the writer
**already tracks this honestly** two fields away in the same object:
`inputs_complete`/`missing_inputs` (lines 1124-1139) correctly records
`"shadbala"` in `missing_inputs` for Rahu/Ketu, but that honesty never reaches
`citation_human`, the human-readable field a caller/native is most likely to
actually read. This is a CLAUDE.md §N.7 item 6 violation ("an honest null
beats an invented judgment... a favorable/neutral-sounding invention standing
in for 'I don't know'") — `sha=1.00` reads as an unremarkable, roughly-average
real measurement, not as "no classical requirement exists for this body."

**What:** extend `citation_human` to disclose the fallback using data already
computed (`missing_inputs`, no new computation):
```python
_sha_note = " [no classical shadbala requirement for nodes]" if "shadbala" in missing_inputs else ""
"citation_human": (
    f"Resonance: {graha} | sha={sha_norm:.2f}{_sha_note} "
    f"dosha_count={len(dosha_by_graha.get(graha, []))}"
),
```

### 2e. `"critical"` priority label — undisclosed rank-relative framing (serving layer, not a computation bug)

**File:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`,
`leadSentence` construction, **lines 450-459**, plus the `resonanceRanked`
mapping (lines 463-478) and `resonancesCompact` mapping (lines 481+).

**Determination:** `bo_upaya.py`'s `_priority_class()` (lines 1005-1034) is
**confirmed-as-designed**, not a bug — its own docstring (lines 1005-1025,
"MC-025a") explicitly documents the deliberate move from absolute thresholds
to chart-relative thirds, precisely because absolute thresholds produced
degenerate "everyone high"/"everyone low" results. **No change to
`_priority_class()` or its call site (`bo_upaya.py:1275`) is in scope.**

**What:** the served narration must disclose the rank-relative framing the
writer already documents internally but never surfaces to a caller. Add a
one-time disclosure string to the response object (not per-row — the
framing is a fixed fact about the labeling scheme, not something that varies
per graha), and append a short pointer from `leadSentence` when it cites a
`remedy_priority_class`:

```ts
// after computing topRow/leadSentence, once per response:
const priorityClassNote =
  "remedy_priority_class is rank-relative among this chart's own 9 grahas " +
  "(chart-relative thirds), not an absolute severity threshold — the same " +
  "score can be 'critical' in one chart and 'low' in another."
```
and reference it from the `leadSentence` template (both branches, lines
452-459) with a trailing pointer, e.g. `` ` (rank-relative — see remedy_priority_class_note)` ``,
and include `remedy_priority_class_note: priorityClassNote` once in the
returned object alongside `resonance_ranked`/`resonances`.

**Why:** this is exactly the CLAUDE.md §N.7 "what violates this principle"
example already named in the org's own doctrine text: "a grade/label that a
reader would reasonably interpret as absolute-severity is actually
rank-relative, with the relative framing undisclosed." `_priority_class`'s
docstring already states the correct framing in the codebase; this fix moves
that existing sentence from a code comment to the served response, it does
not invent new judgment.

## 3. One lane, two build phases (the split/combine decision)

**Decision: one spec, one lane (F-117), but Build lands it as two independent
commits — not two lanes.**

- **Phase 1 — formula-input wiring (§2a, §2b, §2c).** Changes
  `contradiction_factor`, `domain_burden`, `motif_burden` — inputs that feed
  directly into `resonance_score`, so this **can reshuffle
  `weakest_rank_in_chart`/`remedy_priority_class` for this and every other
  already-built chart** (DIAGNOSIS.md §5's own flag). This is a native-facing
  behavior change (which graha gets recommended first for remedy) and
  **requires PRATINIDHI/native sign-off before Stage B lands**, independent of
  the §0 lease question. It is also build-time-only: takes effect on the next
  `bo_upaya` rebuild, not immediately at serve time (§N.3 delete-then-insert).
- **Phase 2 — narration disclosure (§2d, §2e).** Changes only human-readable
  text (`citation_human` in the writer; `leadSentence`/`remedy_priority_class_note`
  in the TS serving layer). **Zero risk of reshuffling any graha's rank or
  priority class** — `sha_norm`'s numeric role in the formula is completely
  untouched by §2d; §2e touches no writer code at all. This phase can ship
  immediately once the lease is granted, independent of PRATINIDHI's Phase-1
  ranking-change ruling. §2d requires a rebuild (it is a writer-side stored
  field); §2e does not (pure TS serve-time string construction over
  already-served fields).

**Why one spec, not two lanes:** all six sub-claims (C1-C6) trace to the same
reproduction, the same served surface (`bodha_remedies_get`), and the same
root finding (F-117); §2d's fix directly reuses the `missing_inputs` tracking
introduced alongside the §2a/formula discussion, and §2e's fix directly cites
`_priority_class`'s docstring that a Phase-1 builder must also read/verify
unchanged — splitting into two lanes would duplicate the §0 lease-routing
overhead for no review benefit, since both phases route to the same "L2 Bodha
owner, TBD" queue. Landing them as two *commits* (not one) means Phase 2 is
never held hostage to Phase 1's PRATINIDHI gate, and a `git revert` of Phase 1
alone never has to touch Phase 2's files.

## 4. Exit tests (fail today, pass after — two files, split by language/layer)

### 4a. Python — Phase 1 + §2d (writer-side), new file:
`platform/python-sidecar/tests/l2/test_bo_upaya_resonance_input_wiring.py`

```python
"""
Exit test for F-117 (PARISESA S3-diagnosed, L2-Bodha-built): bo_upaya's
resonance_score_v1 inputs collapse to zero/flat-constant for
contradiction_factor, domain_burden, motif_burden, defeating the composite
formula's differentiation. See SPEC.md §2a-§2d for full mechanism.
"""
import pytest
from pipeline.orchestrator.writers.bo_upaya import (
    _fetch_active_doshas_by_graha, _build_resonances_and_prescriptions,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"

def test_active_doshas_by_graha_finds_mars_manglik(db_conn):
    """§2a — today: returns {} (7/9 grahas structurally unmatchable).
    After fix: Mars maps to a non-empty list containing the Manglik dosha."""
    result = _fetch_active_doshas_by_graha(db_conn, CHART_ID, AYA)
    assert "Mars" in result, (
        f"_fetch_active_doshas_by_graha returned {result!r} — Mars's live, "
        f"fires=true Manglik dosha (fact_id=2ed777c21b86b03d, constituent "
        f"facts fact_subject='MAR') was not matched. See SPEC.md §2a."
    )
    assert any("anglik" in d for d in result["Mars"])

def test_resonance_inputs_are_not_degenerate(db_conn):
    """§2b/§2c — today: domain_burden==0.0 and motif_burden==0.4 for every
    graha (verbatim live reproduction, DIAGNOSIS.md §1). After fix: both
    vary by graha for at least one pair of grahas with differing underlying
    CDLM-cell-membership / motif-edge computed_strength."""
    resonances, _ = _build_resonances_and_prescriptions(
        CHART_ID, AYA, build_id="test-build", conn=db_conn, now="2026-08-16T00:00:00Z"
    )
    domain_burdens = {r["_graha"]: r["domain_burden"] for r in resonances}
    motif_burdens  = {r["_graha"]: r["motif_burden"] for r in resonances}
    assert len(set(domain_burdens.values())) > 1, (
        f"domain_burden is constant across all grahas: {domain_burdens} — "
        f"still hardcoded per SPEC.md §2b"
    )
    assert len(set(motif_burdens.values())) > 1, (
        f"motif_burden is constant across all grahas: {motif_burdens} — "
        f"bo_cgm_motifs.py strength literals not yet wired per SPEC.md §2c"
    )

def test_citation_human_discloses_shadbala_fallback(db_conn):
    """§2d — today: Rahu/Ketu's citation_human reads 'sha=1.00' identically
    to a real measured ratio. After fix: it discloses the fallback."""
    resonances, _ = _build_resonances_and_prescriptions(
        CHART_ID, AYA, build_id="test-build", conn=db_conn, now="2026-08-16T00:00:00Z"
    )
    by_graha = {r["_graha"]: r["citation_human"] for r in resonances}
    for node in ("Rahu", "Ketu"):
        assert "no classical shadbala" in by_graha[node].lower(), (
            f"{node}'s citation_human ({by_graha[node]!r}) does not disclose "
            f"the shadbala fallback — SPEC.md §2d"
        )
```
Today: all three tests fail as annotated (verified live against the canonical
chart in §2a/§1; §2b/§2c's constant-value claims are the diagnosis's own
verbatim reproduction). After the fix: all three pass.

### 4b. TypeScript — Phase 2 / §2e (serving layer), new file:
`platform/src/lib/retrieval/registry/layers/L2_bodha/__tests__/query_remedies_priority_class_disclosure.test.ts`

```ts
// Exit test for F-117 §2e: remedy_priority_class ("critical"/"high"/...) is
// rank-relative-within-this-chart by design (bo_upaya._priority_class,
// MC-025a) but the served narration never discloses that framing.
test('bodha_remedies_get discloses remedy_priority_class is rank-relative', async () => {
  const res = await queryRemedies({ chart_id: CANONICAL_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha' })
  expect(res.remedy_priority_class_note).toBeDefined()
  expect(String(res.remedy_priority_class_note).toLowerCase()).toContain('rank-relative')
  expect(res.lead_sentence ?? res.leadSentence).toMatch(/rank-relative/i)
})
```
Today: fails — no `remedy_priority_class_note` field exists and
`leadSentence` never mentions rank-relative framing (verified by reading
`query_remedies.ts:450-478` directly — no such string is constructed
anywhere in the file). After the fix: passes.

## 5. Sibling sites covered

- **§2a (graha-identifier mismatch):** `grep -rn "graha\.upper()\|\.upper() ==
  graha" platform/python-sidecar/pipeline/orchestrator/writers/*.py` returns
  exactly one hit today — `bo_upaya.py:840`, the site this spec fixes. (A
  second visually-similar hit, `bo_laksana.py:1408`
  `graha.upper() in _LONG_TO_SHORT`, is a membership test against a
  short-code dict, not a direct code-vs-full-name equality compare — different
  shape, not a sibling of this defect, out of scope.) After this fix, zero raw
  `graha.upper()`-equality sites remain in the writers directory. The
  *pattern* (an ad-hoc per-file graha-code map instead of
  `brahmagyan.graha_vocabulary`) was already the subject of a prior campaign
  (ADHIṢṬHĀNA Lane A2, which fixed `bo_bimba.py`'s identical bug) — this
  finding is that campaign's one missed sibling, not a new class of defect.
- **§2b (`domain_burden`):** `_fetch_graha_cdlm_cells`/
  `cdlm_weakest_constituent_count` has exactly one call site
  (`bo_upaya.py:1175`) and one definition; no sibling writer constructs
  `ResonanceInputs`. No siblings to cover.
- **§2c (motif-class flat-strength literals):** all three sites
  (`_detect_mutual_reception` 0.8, `_detect_mutual_aspects` pair 0.6 and
  triangle 0.75) are covered — confirmed the full set via `grep -n
  '"strength":' bo_cgm_motifs.py`, which also shows `_detect_parivartana_chains`
  already computes a real `strength` variable (not a literal) — no fourth
  sibling literal exists.
- **§2d (`citation_human`):** one call site (`bo_upaya.py:1255`); no sibling
  writer builds a `sha=` citation string for `ResonanceInputs`-fed rows.
- **§2e (`leadSentence`):** `_priority_class`
  (`grep -rn "_priority_class\|priority_class(" platform/python-sidecar/`)
  has exactly one call site, confirmed by the diagnosis; `query_remedies.ts`
  is the only consumer of `remedy_priority_class` that builds prose narration
  from it (`grep -rn "remedy_priority_class" platform/src` — other hits are
  pass-through field selections in `resonanceRanked`/`resonancesCompact`,
  §2e's own edit already covers the object those come from).

## 6. Recurrence guard

- **§2a class (graha-code format mismatches):** recommend a new CI grep-guard
  (out of this spec's own scope to author — flag to conductor as a follow-up
  finding) asserting zero matches for the pattern
  `graha\.upper\(\)\s*==|==\s*graha\.upper\(\)` across
  `pipeline/orchestrator/writers/*.py`, mirroring the existing
  `check_fact_category_pinning.py` CI-guard pattern (§N.7 item 2) — this is
  now a *twice-confirmed* defect class (bo_bimba, bo_upaya) and meets the bar
  for a permanent lint per the same doctrine that produced
  `fact-category-pin-lint`.
- **§2b/§2c (silent zero/flat-constant composite inputs):** the exit test in
  §4a's `test_resonance_inputs_are_not_degenerate` is itself the recurrence
  guard — any future edit that re-hardcodes `domain_burden` or `motif_burden`
  fails this test immediately, the same way `bo_upaya.py:1281-1286`'s existing
  "DEGENERATE DISTRIBUTION" warning already guards `resonance_score` itself
  but (confirmed by reading it) only logs a warning, never fails a build —
  this spec's test is a hard CI assertion, not a log line.
- **§2d/§2e (undisclosed fallback/rank-relative framing):** the exit tests in
  §4a/§4b directly assert the disclosure text is present; any future edit that
  removes it fails immediately.

## 7. Dependencies and rollback

- **Depends on:** nothing outside this lane. No DB migration. No other lane's
  build must land first.
- **Requires before Stage B:** PRATINIDHI/native ruling on the Phase 1
  native-facing ranking-behavior-change risk (§3), independent of and in
  addition to the §0 lease grant. Phase 2 requires only the lease grant.
- **Chart rebuild required:** Phase 1 (§2a-§2c) and §2d change writer-stored
  fields — take effect only on the next `bo_upaya` rebuild for each chart
  (§N.3: delete-then-insert, rebuild REPLACES). §2e is TS serve-time only —
  effective immediately, no rebuild.
- **Rollback:** each phase is a separate commit (§3) — revert Phase 1's commit
  alone to restore the pre-fix (degenerate but stable) ranking behavior
  without touching Phase 2's narration-only fixes, or vice versa. No schema
  change in either phase; both are pure code + narration-text edits.
- **Blast radius (inherited from DIAGNOSIS.md §5, re-confirmed):**
  `bodha_remedies_get`, `bodha_rm_chart_summary`
  (`top_3_resonance_targets_jsonb`), and any Bodha chart-digest surface citing
  "weakest graha for remedy purposes" inherit whatever ranking shuffle Phase 1
  produces once rebuilt. None of the 27 CL-00 controls assert on
  `bodha_rm_resonances`' `domain_burden`/`motif_burden`/`remedy_priority_class`
  shape (unchanged from diagnosis's own check) — low CL-00 regression risk.

## 8. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Determination | Spec element |
|---|---|---|
| C1: `contradiction_factor=0` for all grahas | **Structurally broken**, all charts (diagnosis left this open; this spec resolves it) | §2a |
| C2: `domain_burden=0` for all grahas | Structurally broken, all charts (confirmed by diagnosis; this spec adds the fix path) | §2b |
| C3: `motif_burden=0.4` identically for all grahas | Structurally broken, all charts; single most consequential mechanism (per diagnosis) | §2c |
| C4: rank order is (near-)exactly inverse-shadbala | Direct downstream consequence of C1-C3 collapsing 3 of 4 differentiating terms — not independently fixed, resolves automatically once §2a-§2c land and are rebuilt | §2a + §2b + §2c (no separate element; §3 flags the resulting rank-shuffle risk) |
| C5: Rahu/Ketu `sha=1.00` "inflates priority" | **Not a ranking-math bug** (clamping treats it identically to Sun/Saturn's real ≥1.0 ratios) — reframed as an undisclosed-fallback narration gap | §2d |
| C6: `0.173`→`"critical"` undisclosed rank-relative framing | Confirmed-as-designed computation (`_priority_class`, MC-025a); confirmed real narration-fidelity gap | §2e |
| Split-vs-combine decision (explicitly requested) | One lane/spec, two independently-committable build phases | §3 |
