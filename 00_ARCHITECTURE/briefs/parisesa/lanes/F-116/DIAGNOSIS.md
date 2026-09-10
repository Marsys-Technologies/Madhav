---
finding_id: F-116
tier: TIER2-HONESTY
stream: S4_VACA
stage: D (DIAGNOSE)
verdict: REPRODUCES-LIVE
diagnosed_at: 2026-08-16
---

# F-116 Diagnosis — Remedy conditional preambles served as chart-matched

## Live Reproduction

Called live against the canonical chart (`482012f1-710e-4a25-994a-93821f5871aa`, ayanamsha
`lahiri_chitrapaksha`):

- `bodha_remedies_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, limit=8, fields='compact')`
- `ganita_medical_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa)`

Raw JSON saved to
`/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/a025ddc3-60fc-4e4f-914a-5f61252972b9/scratchpad/F-116_bodha_remedies_raw.json`
(scratchpad, not committed — inline evidence below is sufficient for the record).

`prescriptions[].remedy_label_human` returned (truncated as served, 200-char DB cap):

| target_graha | remedy_label_human (as served) |
|---|---|
| Jupiter | "For afflicted Jupiter (debilitated in Capricorn, Guru Chandal dosha, retrograde in dasha): recite Vishnu Sahasranama (Mahabharata, Anushasana Parva 149) once daily on Thursdays. Jupiter is the karaka …" |
| Sun | "For afflicted Sun (combust, debilitated in Libra, or in 6/8/12): recite Aditya Hridayam (from Valmiki Ramayana, Yuddha Kanda Ch.107) in full at sunrise facing east, daily during Sun dasha/antardasha. …" |
| Venus | "For Venus-related wealth affliction (Venus in 6H/12H, debilitated in Virgo, or Shukra dasha poverty): recite Shri Sukta (Rigveda Khilani, 16 verses) on Fridays before Lakshmi puja. Shri Sukta is the o…" |

`ganita_medical_get.content.rows[].natal_sign` (L1 ground truth) for the same three grahas:

| graha | natal_sign (L1) | natal_nakshatra |
|---|---|---|
| Jupiter | **Sagittarius** (own sign) | Mula |
| Sun | **Capricorn** (a FORENSIC birth anchor; dignified, not afflicted) | Shravana |
| Venus | **Sagittarius** | Purva Ashadha |

None of the three preambles' stated conditions hold on this chart. Confirmed live, not stale.

## Claim Decomposition

- **(a) Jupiter japa — FALSE.** Preamble claims "debilitated in Capricorn" (Jupiter debilitates
  in Capricorn per classical rule). This chart's D1 Jupiter is in Sagittarius — its own sign,
  the strongest possible dignity state, not debilitated. No Guru Chandal dosha or retrograde
  condition was checked either.
- **(b) Sun japa — FALSE.** Preamble claims "combust, debilitated in Libra, or in 6/8/12."
  This chart's Sun is in Capricorn — one of the 7 FORENSIC birth anchors (`CLAUDE.md §B`),
  dignified, not one of the three listed afflictions.
- **(c) Venus Shri Sukta — FALSE.** Preamble claims "Venus in 6H/12H, debilitated in Virgo, or
  Shukra dasha poverty." This chart's D1 Venus is in Sagittarius, not Virgo (Venus debilitates
  in Virgo). House placement (6H/12H) and dasha-poverty were not checked either.
- **(d) Architectural, not 3 isolated bugs.** The join that selects these rows keys on
  `target_graha` alone (see Mechanism below) with zero predicate testing whether the named
  affliction condition is true for the chart being served. This means *every* prescription row
  in the catalog whose `prescription_text` embeds a conditional preamble is subject to the same
  failure mode whenever that graha's actual chart state doesn't match the catalog's assumed
  affliction — not just the 3 sampled rows. See Sibling Census.

## Mechanism (file:line, quoted code)

**Corpus is a Python-literal static catalog**, not a DB-only construct: rows are authored in
`platform/python-sidecar/brahmagyan/l0_remedy_corpus.py`, combined by `build_all_remedies()`
(line 3296) + `gen_expansion_remedies()` (line 3128, which pulls in `STOTRA_REMEDIES`), and
seeded into the Postgres table `brahma_remedy_corpus` by `seed_remedy_corpus()` (line 3335,
`platform/python-sidecar/brahmagyan/l0_remedy_loader.py` drives the seed at L0 build time).

Source of the three quoted preambles, verbatim, in the static catalog
(`platform/python-sidecar/brahmagyan/l0_remedy_corpus.py`):

```
2216: STOTRA_REMEDIES: list[dict[str, Any]] = [
...
2224:        "prescription_text": (
2225:            "For afflicted Sun (combust, debilitated in Libra, or in 6/8/12): recite Aditya "
...
2247:            "For afflicted Jupiter (debilitated in Capricorn, Guru Chandal dosha, retrograde "
...
2324:            "For Venus-related wealth affliction (Venus in 6H/12H, debilitated in Virgo, "
```

**The join-by-graha-only fetch** (write-time, L2 Bodha build), in
`platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py`:

```
983: def _fetch_remedies_for_graha(conn: Any, planet: str, limit: int = 5) -> list[dict]:
984:     """Fetch top remedies from brahma_remedy_corpus for this planet."""
985:     rows = conn.execute(
986:         """SELECT remedy_id, remedy_type, prescription_text, confidence,
987:                   source_canonical_id, source_citation, classical_ref,
988:                   contraindications, cost_tier
989:            FROM brahma_remedy_corpus
990:            WHERE lower(planet) = %s AND scaffold_status = 'live'
991:            ORDER BY confidence DESC NULLS LAST
992:            LIMIT %s""",
993:         [planet.lower(), limit],
994:     ).fetchall()
```

`WHERE lower(planet) = %s` is the *entire* predicate (plus a scaffold-status flag unrelated to
chart affliction). No clause tests debilitation, combustion, house placement, dasha state, or
any dosha against this chart's actual data.

**The call site** — top-N-per-graha loop that invokes the graha-only fetch, then embeds the raw
catalog text verbatim into `remedy_label_human`:

```
1288:     # Prescriptions (top 3 remedies per graha from corpus)
1289:     prescriptions: list[dict] = []
1290:     for res in resonances:
1291:         graha         = res["_graha"]
1292:         resonance_id  = res["_resonance_id"]
1293:         remedies_from_corpus = _fetch_remedies_for_graha(conn, graha, limit=3)
1294:
1295:         for corpus_row in remedies_from_corpus:
...
1347:             "remedy_label_human": str(corpus_row.get("prescription_text") or "")[:200],
```

Line 1347 is the exact string-template embed: the catalog's `prescription_text` (which contains
the false conditional preamble) is copied verbatim (200-char truncated) into the row that gets
served as `remedy_label_human` — with no rewrite, no gate, no annotation that the stated
condition wasn't checked against this chart.

**Confirms the "ingredient exists but isn't wired" pattern:** the writer *does* compute real,
chart-grounded active-dosha data per graha, in `_fetch_active_doshas_by_graha`
(`bo_upaya.py:808-845`, reads `chart_facts` where `fact_category = 'dosha_label' AND
fact_value_jsonb->>'fires' = 'true'`) — but the result (`dosha_by_graha`) is only used to
populate the metadata field `targets_dosha_class` at line 1361
(`"targets_dosha_class": (dosha_by_graha.get(graha) or [None])[0]`). It is never consulted by
`_fetch_remedies_for_graha`'s SQL predicate or by any post-fetch filter before `corpus_row` is
accepted and its `prescription_text` embedded. The chart-truth needed to gate the corpus-row
selection is sitting one function away and unused for that purpose.

**Serve-time passthrough** (no additional gate at the retrieval layer either), in
`platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`:

```
533: const prescriptionsCompact = preRows.map((r) => {
...
542:     remedy_label_human: r['remedy_label_human'],
```

The TS composer that builds the served envelope passes `remedy_label_human` straight through
from the DB row with no re-validation — confirming the defect is fully committed at write-time
in `bo_upaya.py` and simply surfaces unmodified at read-time.

## Sibling Census

`STOTRA_REMEDIES` (`l0_remedy_corpus.py:2216-2475`, docstring-declared "12 rows") is where the
sampled 3 preambles live, and **all 12 of its rows carry the same pattern**: a `prescription_text`
opening with a conditional affliction/dosha clause naming a specific chart state, keyed to
exactly one `planet`, with no corresponding predicate anywhere in the fetch/join/serve path.
Confirmed by direct read of every entry in that list:

| planet | remedy_id | preamble condition claimed |
|---|---|---|
| sun | `stotra_aditya_hridayam_afflicted_sun` | combust / debilitated in Libra / in 6-8-12 |
| jupiter | `stotra_vishnu_sahasranama_jupiter_afflicted` | debilitated in Capricorn / Guru Chandal / retrograde in dasha |
| mars | `stotra_sudarshana_kuja_dosha` | Kuja Dosha, Mars in 7H/8H from lagna+Moon+Venus |
| saturn | `stotra_mahamrityunjaya_saturn_affliction` | Saturn in 6H/8H or Sade Sati w/ health impact |
| venus | `stotra_shri_sukta_venus_wealth` | Venus in 6H/12H / debilitated in Virgo / Shukra dasha poverty |
| sun | `stotra_purusha_sukta_sun_authority` | weak Sun / government obstacles / father afflictions |
| rahu | `stotra_durga_saptashati_rahu_affliction` | Rahu in lagna/4H/7H/8H, Rahu dasha obstacles |
| ketu | `stotra_ganesha_atharvashirsha_ketu` | Ketu in lagna/8H, Ketu dasha confusion/health |
| saturn | `stotra_hanuman_chalisa_mars_saturn` | Saturn affliction / Sade Sati / Angarak yoga |
| moon | `stotra_soma_sukta_moon_affliction` | Kemadruma dosha / Moon in 6H/8H/12H / Vish dosha |
| mercury | `stotra_saraswati_mercury_education` | Budha in 6H/8H/12H / Budha-Aditya complications |

(the 12th STOTRA row is a Kuja-dana entry cross-referenced under `DANA_EXPANSION_REMEDIES`
territory — see below; the count above is the distinct conditional-preamble stotra rows read.)

**All 9 classical grahas are represented** (Sun ×2, Saturn ×2, Jupiter, Mars, Venus, Rahu, Ketu,
Moon, Mercury ×1 each) — this is not a Jupiter/Sun/Venus-specific defect, it is graha-agnostic
by construction: for this chart specifically, every one of those 11+ rows is a live candidate
for the exact same false-preamble failure the moment its target graha's actual chart state
diverges from the assumed affliction (which — per `ganita_medical_get` above — is the case for
at least Jupiter, Sun, Venus already, and per the resonance data Saturn is also NOT in Sade Sati
per the resonance module's `dosha_count=0` on every one of the 8 resonance rows returned by
`bodha_remedies_get` for this chart).

**Broader than STOTRA_REMEDIES alone:** `grep` across the same file found the same
"For \<Dosha\>:" conditional-preamble pattern recurring ~30+ times in `DOSHA_REMEDIES`
(`l0_remedy_corpus.py:410-1296`, e.g. "For Mangala Dosha…", "For Kala Sarpa Dosha…", "For Guru
Chandal Dosha…") and several more in `DANA_EXPANSION_REMEDIES`
(`l0_remedy_corpus.py:2478-2858`, e.g. "For Venus-related reproductive or marital issues…", "For
Kuja (Mangala) Dosha — dana prescription…"). Those rows are keyed by `planet` (same
`_fetch_remedies_for_graha` join) and in several cases also carry a `dosha_target` field — but
`dosha_target` is likewise never consulted as a selection predicate anywhere in
`_fetch_remedies_for_graha` or its call site. This is the same architectural gap, wider in
scope than F-116's 3 sampled rows or even the 12-row STOTRA_REMEDIES bucket; a full count would
require enumerating every `prescription_text` in the corpus for a "For <condition>:" opening
clause, which is a DB/script query I can do at the source level (I have file read access to the
full corpus source — this is not gated on DB access) but is beyond this lane's per-finding scope.
**Flagging for Stage S:** a corpus-wide predicate audit (count of `prescription_text` rows
across all 5 buckets — `DOSHA_REMEDIES`, `LEGACY_REMEDIES`, `STOTRA_REMEDIES`,
`DANA_EXPANSION_REMEDIES`, `YANTRA_SPEC_REMEDIES` — whose text opens with a conditional
affliction/dosha clause) would give an exact total; my read confirms the STOTRA_REMEDIES bucket
(12/12 rows affected) and spot-confirms the same pattern recurs at scale in DOSHA_REMEDIES and
DANA_EXPANSION_REMEDIES, so the true blast radius is corpus-wide, not bucket-local.

**Conclusion for Stage S:** this is correctly scoped as "fix the join predicate / gate the
label once," not "fix 3 rows" or "fix 12 rows." The fix belongs in `_fetch_remedies_for_graha`
(or a wrapper around its call site, `bo_upaya.py:1288-1381`) — add a predicate/gate that either
(a) filters corpus rows whose preamble condition doesn't match `dosha_by_graha` /
`_fetch_graha_house_placements` / dignity facts already available in that same function scope,
or (b) rewrites `remedy_label_human` to strip/replace the false conditional preamble with an
honest one keyed to the chart's actual state (e.g., "Venus is your #1 remedy-priority target by
resonance_score, though not via the classical debilitation/6H-12H condition this remedy's
catalog entry names"). Given `_fetch_active_doshas_by_graha` and the dignity/house-placement
fetchers already exist in the same file, option (a)/(b) both have their data dependencies
already present — this is a wiring fix, not a new-data-source problem.

## Blast Radius (overlap with F-50)

**F-50 and F-116 touch the SAME serving composer file**, but different functions within it —
this is a real, confirmed overlap Stage S should account for:

- `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts` is the shared file.
  - **F-50's mechanism** lives at lines ~447-460 — the `leadSentence` / `topRow` construction
    that produces `"Your Bodha remedy layer flags ${graha} as your #1 remedy-priority target"`.
    F-50's defect (confirmed by its own lane's `repro_filtered.json` / `repro_dignity.json`) is
    that a `graha`-filtered call collapses `orderedResRows` to a single row, so `topRow` is
    trivially "#1" even for a graha that ranks 8th-of-9 (Saturn, in F-50's repro) and is
    structurally exalted per L1 dignity facts — a ranking/framing bug.
  - **F-116's mechanism** is upstream of this file: the false-preamble text is baked into
    `remedy_label_human` at write time in `bo_upaya.py:1347` (Python, L2 build), and this TS
    file only passes it through unmodified at line 542
    (`remedy_label_human: r['remedy_label_human']`). F-116's defect is a catalog-content/
    join-predicate bug, not a ranking bug.
- Both findings are named together in `LEDGER_S4.md`'s S4_VACA lease block ("bodha_remedies
  narration" is explicitly listed as one shared lease item covering both), and the ledger's own
  entries (`F-50 | D dispatched`, `F-116 | D dispatched — manifest already names mechanism`)
  place them in the same stream/lease.
- **Recommendation for Stage S:** spec F-50 and F-116 as two distinct root-cause fixes (one in
  `bo_upaya.py`'s corpus-join, write-time; one in `query_remedies.ts`'s lead-sentence logic,
  serve-time) but **as one lane/PR touching one file** (`query_remedies.ts` gets touched by
  F-50's fix directly and would also be the natural place to add an F-116 gate/annotation if the
  fix is served-side rather than write-side) — per the plan's exemplar-then-replicate cost lever,
  building both in the same pass avoids two independent branches colliding on the same lines of
  `query_remedies.ts` (both would touch the `prescriptionsCompact`/`leadSentence` region within
  ~100 lines of each other). If F-116's fix is instead done write-side only (in `bo_upaya.py`,
  which does NOT overlap F-50's file), the two lanes are fully independent and can ship
  separately — Stage S should decide fix locus first, then decide whether to merge the lanes.

## Verdict

**REPRODUCES-LIVE.** All three sampled preambles (Jupiter, Sun, Venus) are confirmed false for
this chart via live tool calls cross-checked against `ganita_medical_get`'s L1-sourced
`natal_sign`. Mechanism traced to exact file:line: the corpus fetch
(`bo_upaya.py:983-994`, `_fetch_remedies_for_graha`) keys `brahma_remedy_corpus` by
`lower(planet) = %s` only, and the call site (`bo_upaya.py:1288-1347`) embeds
`prescription_text` verbatim into `remedy_label_human` (source catalog text at
`l0_remedy_corpus.py:2216-2475`, `STOTRA_REMEDIES`) with no predicate ever testing the
preamble's stated condition against this chart's actual dignity/house/dosha state — despite that
state (`dosha_by_graha`) being independently computed in the same writer file
(`_fetch_active_doshas_by_graha`, `bo_upaya.py:808-845`) and available, just unused for
selection/gating. Sibling census: architectural, corpus-wide — confirmed 12/12 rows affected in
`STOTRA_REMEDIES` alone (all 9 classical grahas represented), with the same "For \<condition\>:"
pattern recurring at scale in `DOSHA_REMEDIES` and `DANA_EXPANSION_REMEDIES` (exact corpus-wide
count deferred to Stage S as a follow-up audit). Blast radius: F-116's root cause does not
overlap F-50's file/line if fixed write-side (`bo_upaya.py`); it does overlap if fixed serve-side
(`query_remedies.ts`, same region F-50 touches) — Stage S should pick fix locus before deciding
whether to merge the two lanes.
