---
artifact: SHAD_DARSHANA_ADJUDICATION_16_FOLLOWUP_MULTI_CONVENTION_GAP
version: 1.0
status: OPEN — blocks ADJUDICATION-16 implementation pending a design ruling
campaign: ṢAḌ-DARŚANA
branch: shad-darshana/w2g-agnivasa-convention-b
predecessor: SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md (task-cited; see §0
  below — this file was not found in the repo at authoring time)
---

# ADJUDICATION-16 follow-up — the multi-convention resolution gap

## §0 — A precondition note before the gap itself

The task that produced this document instructed: "ruling file:
`00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_ADJUDICATION_16_AGNIVASA_CONVENTION_B_v1_0.md`
— read it in full first." That file does not exist anywhere in this repository: not in this
worktree, not in the main `Madhav` checkout, not in `git log --all --diff-filter=A` across every
branch (6,957 commits scanned). `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md` and
`..._NIGHT5_v1_0.md` — the two files that actually carry the numbered `ADJUDICATION-N` rulings —
stop at ADJUDICATION-15. No ADJUDICATION-16 ruling text is on record in this repo at all.

This is reported as a fact, not worked around. The task's own instructions supplied the extracted
rule content directly (`remainder = (tithi_id + 1 + vara_id) mod 4` → `{0,3}`=Pṛthvī, `1`=Ākāśa,
`2`=Pātāla) and the exact required migration field values, which is why the investigation below
was still worth doing — the MANDATORY CONTEXT items (migration 533, `kala_sky_pattern.ts`, the
Convention-A computation path) all exist and were read in full. But the provenance citation this
document would otherwise need to quote verbatim from ADJUDICATION-16 (its stated rationale,
reversibility, and any caveats it may have attached to Convention B) cannot be verified against a
source document, because there isn't one in this repo to check it against. Whoever holds the
canonical ADJUDICATION-16 text should reconcile this before any migration lands.

## §1 — What was investigated

Per the task's DECISION POINT, the governing question was: does `kala_sky_pattern.ts` /
`PaddhatiResolution` already have a defined, correct way to handle two simultaneously
`convention_status='computed'` + `constraint_role='hard'` rows in one `factor_family` (here,
`agnivasa`), or does it assume at most one?

**Files read in full:**
- `platform/supabase/migrations/533_kala_paddhati_profile.sql` (the seed migration; Row A
  computed, Row B `declared_not_computed`)
- `platform/supabase/migrations/534_kala_paddhati_native_confirmed.sql` (the only migration to
  touch this table since 533)
- `platform-mcp/src/lib/kala_sky_pattern.ts` (1,540 lines, in full)
- `platform-mcp/src/lib/kala_sky_pattern.test.ts` (the relevant `paddhati`/`operative`/
  `divergence` sections)
- `platform/python-sidecar/panchang_engine/shastra_tables.py` (`AGNI_VASA_TABLE`, lines
  1188–1193)
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py` (the Agnivāsa
  family's construction, header + implementation)

## §2 — Finding: the code assumes at most one computed convention per factor_family, and does not detect a second one

Three independent lines of evidence, each sufficient on its own:

### 2.1 — The `residence`/`agnivasa` grading branch never reads convention content from `kala_paddhati_profile`

`kala_sky_pattern.ts:1351–1403` (the `case 'residence':` branch of `compileConstraint`) is the
ONLY place in the codebase that consumes `paddhati.operative` for `factor_family='agnivasa'`
grading. What it actually does:

```ts
// kala_sky_pattern.ts:1374
const usingProfile = b.per === 'paddhati_profile' && paddhati.available && paddhati.operative.length > 0
const favourableElements = ['prithvi']
const wantFavourable = (b.state ?? 'favorable') === 'favorable'
const matched = rows.filter((r) => {
  const el = String((r.detail as { element?: unknown } | null)?.element ?? '').toLowerCase()
  const isFav = favourableElements.includes(el)
  return wantFavourable ? isFav : !isFav
})
```

`usingProfile` is a boolean gate on `paddhati.operative.length > 0` — it is **never** used to read
a `convention_id`, select between rule tables, or branch computation. `rows` (line 1365,
`rowsByFamily.get('agnivasa')`) comes from the muhūrta lattice's precomputed atoms — one row per
calendar day, built entirely by `bg_muhurta_lattice.py` from `AGNI_VASA_TABLE` (Convention A's
tithi-only arithmetic; `shastra_tables.py:1188–1193`). `favourableElements = ['prithvi']` is a
hardcoded, single-convention constant. The ONLY effect `paddhati.operative` has on this branch is
cosmetic: it flips the `reason` field between `null` (line 1390) and an explanatory string
(1391–1396) — the matched interval set is byte-identical either way.

Consequence: `kala_paddhati_profile` is architecturally incapable of steering grading here at all,
for ONE convention or TWO. Convention A's rule reaching a candidate happens because
`bg_muhurta_lattice.py` bakes it into the lattice at L0 build time (chart-independent, built once,
`bg_muhurta_lattice.py:65–75`); `kala_paddhati_profile` is chart-scoped and is consulted only for
disposition text. Flipping Convention B's row to `computed` would add a second entry to
`paddhati.operative`, but no code path reads that entry's `convention_id` or applies its
arithmetic — Convention B would be silently absent from grading while the disposition's `reason`
field (when `usingProfile` is true) claims resolution "against the paddhati profile," which
becomes actively misleading the moment two rows are present, since only Convention A's
precomputed atoms are ever actually matched.

### 2.2 — `PaddhatiResolution.divergence` is a hardcoded constant, not a computed comparison, and no test ever exercises its two non-trivial states

`kala_sky_pattern.ts:513–517` declares `divergence.state` as a closed three-value type
(`'none_computed' | 'diverges' | 'agrees'`, exported as `PADDHATI_DIVERGENCE_STATES`). But
`fetchPaddhatiProfile` (`kala_sky_pattern.ts:642–655`) never computes it — it is a literal:

```ts
// kala_sky_pattern.ts:646–651
divergence: {
  state: 'none_computed',
  reason:
    'one convention computable; agnivasa_muhurta_chintamani_arithmetic is ' +
    'declared_not_computed pending muhurta_chintamani translation',
},
```

This string is factually accurate today (one convention IS computable) and would become false the
instant a second `computed` row exists — but there is no code that re-derives it. `'diverges'` and
`'agrees'` are declared as legal states and asserted as a closed set in
`kala_sky_pattern.test.ts:126–128`, but no test — and no production code path — ever produces
either value. Grepping the test file's `operative:` fixtures (`kala_sky_pattern.test.ts:150, 170,
178, 184, 193`) confirms every single one passes an array of length 0 or 1; none test two rows in
one `factor_family`. This is the same defect class CLAUDE.md §N.8 (Earned-Signal Principle) names
directly: "a status... must be computed by a detector that measures the specific claim it
asserts; a signal without such a detector is null, not green." `divergence.state` has never had a
detector for its two non-`none_computed` states.

### 2.3 — The census-statement reader assumes single-match-wins, by construction

`paddhatiCensusStatement` (`kala_sky_pattern.ts:563–597`) resolves the confirmed convention via
`profile.operative.find((r) => r.factor_family === 'agnivasa' && r.native_confirmed === true)`
(line 575) — a first-match `.find()` over an array that today holds at most one qualifying row.
This is not immediately triggered by this task (Convention B is specified `native_confirmed=FALSE`
per the task's own required field values), but it is further evidence of the same underlying
assumption across every consumer of `paddhati.operative`: exactly one row per `factor_family` is
the design's working model, never explicitly stated but never contradicted by a test either.

## §3 — Why this meets the task's STOP condition

The task's DECISION POINT is unambiguous: if the code "was written assuming at most one computed
convention per factor_family, and introducing a second would either crash, silently ignore one, or
silently double-count in a way nobody designed," the correct action is to stop rather than invent a
resolution scheme unilaterally. §2.1–§2.3 above show the third of those three failure modes most
precisely: introducing Convention B as a second `computed`/`hard` row would neither crash nor
double-count — it would be **silently ignored** by the one code path that grades `agnivasa`
constraints (§2.1), while a separate honesty surface (`divergence`, §2.2) would begin asserting a
narration that is no longer true, with no detector to catch the drift. This is exactly the kind of
undesigned, rail-adjacent decision the task correctly flagged as off-limits for this session to
resolve unilaterally.

## §4 — What a design ruling needs to decide

For a future session (or the native/ANTARYĀMIN adjudication process) to unblock this:

1. **Does Convention B ever reach actual grading, or does it remain informational-only forever?**
   If informational-only, `constraint_role` for Convention B should arguably be `'informational'`
   or `'soft'`, not `'hard'` — a `'hard'` role on a row that structurally cannot participate in
   grading (§2.1) is itself a smaller version of the same honesty gap.
2. **If Convention B should reach grading:** does it REPLACE Convention A's atoms for candidates
   where the native's practice governs (recall migration 534: Convention A is native-CONFIRMED
   practice), does it run as a SECOND independent hard filter (candidate must satisfy BOTH
   conventions' favourable-element test, which for tithi-only vs. the mod-4 tithi+vara arithmetic
   could easily produce an EMPTY intersection on many calendar days), or is it served alongside as
   a labeled alternative for the caller to choose (`operative` becoming a set the caller filters by
   `convention_id`, with `constraint_role` and grading semantics moved from "the array's mere
   non-emptiness" to "the specific row the caller selected")?
3. **Where does the arithmetic actually run?** Today Convention A's rule is baked into
   `bg_muhurta_lattice.py` at L0 build time (chart-independent, one row per calendar day,
   `detail.tithi_id`/`detail.vara_id` already carried on every row per
   `bg_muhurta_lattice.py:509–510` — so Convention B's arithmetic COULD be computed from data
   already on the row without new substrate). Wiring Convention B in would require either (a) a
   second `bg_*` L0 writer emitting a second `factor_family` (e.g. `agnivasa_mc`) so both
   conventions' atoms exist side-by-side on the lattice, or (b) a query-time computation inside
   `kala_sky_pattern.ts`'s `residence` branch reading `detail.tithi_id`/`detail.vara_id` off the
   EXISTING `agnivasa` atoms and applying whichever convention `kala_paddhati_profile` says is
   operative for this chart. These are materially different builds and the choice is a design
   decision, not an implementation detail.
4. **What should `divergence.state` mean, concretely, once two conventions ARE both computed?**
   `'agrees'`/`'diverges'` per WHAT comparison — per calendar day? Per candidate window? And what
   should a caller do differently when told the two conventions diverge on a given date — is
   `constraint_role='hard'` on BOTH still correct (a candidate must satisfy both, i.e. only dates
   where Pṛthvī-per-A and Pṛthvī-per-B coincide survive), or does divergence itself become a
   caller-facing signal rather than a silent AND?
5. **Precedence, if any.** ADJUDICATION-8's own rail 3 (migration 533's header, restated in 534)
   is explicit that Convention A is native-CONFIRMED practice and Convention B is NOT — does that
   asymmetry mean A wins on disagreement, or does "confirmed" only describe provenance/attestation
   status and carry no grading precedence at all? The code today treats `native_confirmed` as
   purely a census-statement input (§2.3), never a grading input — a ruling should say explicitly
   whether that stays true once Convention B is live.

## §5 — What this session did NOT do

Per the task's explicit instruction for this branch of the decision tree: no new migration file
was written (the next available migration number, for whoever picks this up, is currently `537` —
the highest existing is `536_muhurta_chintamani_translation_provenance.sql`). No change was made
to `kala_sky_pattern.ts`, `bg_muhurta_lattice.py`, `shastra_tables.py`, or any test. No commit
beyond this document has been made on `shad-darshana/w2g-agnivasa-convention-b`.
