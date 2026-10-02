---
version: 1.1
status: CURRENT
lane: TI-l1-panchanga-moon-sign-001
branch: suvarna/land/TI-l1-panchanga-moon-sign-001
basis: origin/main 8cf05f507
changelog:
  - 1.0 — defect, fix, expected stored change (flip-detector hook entry), residual findings.
  - 1.1 — (exact database name pinned) real-PG suite wording (runs in CI, fails never skips), disposable-DB guard, SQL derivations of the same formula and the (uu2) consequence (R2b).
---

# chandra_bala_natal_baseline: birth Moon sign was derived from the nakshatra id

## Defect

`ga_panchanga_writer._emit_chandra_bala_baseline` computed the birth Moon sign as
`((birth_nak_id - 1) * 4) // 9 + 1`: the sign of the nakshatra's START. Purva Bhadrapada (id 25)
straddles Aquarius (pada 1-3) and Pisces (pada 4), so every ayanamsha got Aquarius. Stored
`ga_positions` fact `graha_position | MOON | sign` is Aquarius for krishnamurti, lahiri_chitrapaksha,
raman, true_chitra and Pisces for surya_siddhanta_classical (Moon in pada 4), so the 12
surya_siddhanta_classical rows were classified from the wrong sign (every Chandra Bala position
shifted by one) and contradicted the position fact. Same defect for any chart whose Moon is in the
later part of a sign-straddling nakshatra (Krittika, Mrigashira, Punarvasu, Uttara Phalguni,
Chitra, Vishakha, Uttara Ashadha, Dhanishtha, Purva Bhadrapada).

## Fix

The writer READS the per-ayanamsha Moon sign from the upstream `ga_positions` fact (chart_facts,
`fact_category='graha_position'`, `fact_subject='MOON'`, `fact_key='sign'`; one row per ayanamsha,
selected with `DISTINCT ON (ayanamsha_id) ... ORDER BY ayanamsha_id, computed_at DESC, build_id DESC`),
maps the English sign name through `brahmagyan.fact_identity_parser.SIGN_NAME_TO_NUM`, and RAISES when
the fact is absent or unrecognised (no default). `ga_positions` is a declared dependency of
`ga_panchanga`, so the facts exist at run time.

Why not `pi.*`: `panchanga_instant` runs under ONE ayanamsha (Lahiri) and its single result is
reused by all five per-ayanamsha passes, so `pi` cannot carry the surya_siddhanta Moon sign.

Also removed: the `NATIVE_MOON_NAK_ID` / `NATIVE_MOON_SIGN_ID` owner-chart constants and the
`else NATIVE_MOON_NAK_ID` fallback (`pi.nakshatra` is always populated by `panchanga_instant`; absence
now raises in both Tara Bala and Chandra Bala paths).

## HOOK entry (flip detector)

```
value change
table:              chart_facts
category:           chandra_bala_natal_baseline
ayanamsha:          surya_siddhanta_classical
chart:              482012f1-710e-4a25-994a-93821f5871aa (canonical)
expected_count:     12 rows with a value/citation change (fact_key=classification);
                    of these 9 change fact_value_text, 12 change citation_human
                    (birth Moon sign=Kumbha -> birth Moon sign=Meena)
expected_classification_changes: 9
other_ayanamshas:   krishnamurti, lahiri_chitrapaksha, raman, true_chitra: 0 rows change
                    (same sign, Aquarius -> 'Kumbha' text identical)
reason:             birth Moon sign now read from the ga_positions Moon sign fact
                    (Pisces for surya_siddhanta_classical) instead of derived from the nakshatra id (Aquarius).
to be confirmed by:  the rehearsal diff
```

New surya_siddhanta_classical classification (birth Moon in Pisces), subject -> value:
MEENA favorable, MESHA unfavorable, VRISHABHA favorable, MITHUNA unfavorable, KARKA unfavorable,
SIMHA favorable, KANYA favorable, TULA unfavorable, VRISHCHIKA neutral, DHANU favorable,
MAKARA favorable, KUMBHA unfavorable.

Rows whose classification changes (9): MEENA, MESHA, VRISHABHA, KARKA, KANYA, TULA, VRISHCHIKA,
MAKARA, KUMBHA. Unchanged value (3): MITHUNA, SIMHA, DHANU (citation text still changes).

Stored classification pattern read live (values only, reader role): the five ayanamshas were
byte-identical on the Aquarius pattern (DHANU favorable, KANYA unfavorable, KARKA favorable,
KUMBHA favorable, MAKARA unfavorable, MEENA unfavorable, MESHA favorable, MITHUNA unfavorable,
SIMHA favorable, TULA neutral, VRISHABHA unfavorable, VRISHCHIKA favorable), equal to the
synthetic Aquarius expectation in the new tests. Position facts read live: Moon sign Aquarius for
four ayanamshas, Pisces (pada 4) for surya_siddhanta_classical.

Served exposure of the stored rows on the canonical chart: dossier slice bundles
`career_482012f1.json` and `wealth_482012f1.json` (platform-mcp/src/resources/vidhi/dossier_slices/),
`concept_aliases.ts` (concept locate), source_query_availability probes, generic chart_facts reads.

## Verification

- New `tests/test_ga4_chandra_bala_birth_sign.py` (CI-run, DB-free, synthetic chart id and synthetic
  per-ayanamsha Moon signs): Pisces and Aquarius portions of Purva Bhadrapada; all 12 sign ids read
  as given; absent/unrecognised sign raises; Tara Bala has no fallback; end-to-end `build_ga_panchanga`
  with a fake connection asserts the emitted birth sign equals the position fact for all five
  ayanamshas (dict and tuple row shapes) and that nothing is inserted when one ayanamsha lacks the
  fact; structural guard that no `* 4) // 9` formula remains in `ga_writers/`.
- Mutation proof: sign hardwired to the nakshatra-derived value (11 failed), reader ignoring the
  fact (2 failed), default instead of raising (3 failed), nakshatra fallback restored (1 failed).
  Reverting the writer entirely fails the new tests (signature and values).
- Writer digest inventory: only `ga_panchanga` moves (`99ffa3fb...` -> `7cd8e0aa...`);
  `src/generated/nirmana-writer-digests.json` regenerated.
- E6 line pins moved with the line shift: `ga_panchanga_writer.py` citation sites 368 -> 359,
  534 -> 525, INSERT 1276 -> 1322 (asset_declarations.json and test_e6_1_declarations.py).

## Other nakshatra-to-sign derivations (grep of Python, SQL migrations and TypeScript)

Python: `* 4) // 9` appears nowhere else in `ga_writers/` or `brahmagyan/`; no other L1 writer maps a
nakshatra id to a sign. Longitude to nakshatra index (`lon // (360/27)`) in ga_sade_sati_writer.py,
ga_vargas_writer.py, ga_nakshatra_compute.py and ga_dashas_writer.py is the correct direction.
Owner-chart sign constants outside this lane (not touched): `services/ka_muhurta_seva/service.py:33`
`NATIVE_MOON_SIGN_ID = 11` and `brahmagyan/kala/l3_obstruction.py:51` `NATIVE_MOON_SIGN = "Aquarius"`.

SQL (the Python-only grep missed these; independent review R2b found the first, a wider grep for
`* 4) / 9`, `*4)/9`, `/ 2.25` forms over `platform/migrations`, `platform/supabase/migrations`,
`platform/src`, `platform-mcp/src`, `platform/scripts` and `platform/python-sidecar` lists every hit;
finding only, no edits): the same formula `( ((n.fact_value_num::int - 1) * 4) / 9 + 1 )`, applied to
`panchanga_nakshatra_moon.number`, appears in 33 migrations, each as a copy of the Chandra Bala
conjunct (uu2) inside a `ga_structural` integrity check: 790, 791, 792, 793, 794, 795, 796, 797, 798,
799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818,
819, 840, 841 and 904 (files named `<n>_nirmana_l1_ga_structural_integrity_*.sql` in the platform migrations directory; 904 is
`..._check_scope.sql`, the others `..._contract_<name>.sql`). Per R2b the live definition is
`asset_registry.integrity_check_sql` (not independently re-read here). There are 0 hits in
`platform/supabase/migrations`, `platform/src`, `platform-mcp/src` and `platform/scripts`; the only
other hit in the tree is this lane's own structural-guard test, which names the pattern in a regex.

Expected consequence (R2b finding): conjunct (uu2) re-derives the birth Moon sign from the nakshatra
number with that formula, so it would go FALSE for the 9 changed surya_siddhanta_classical rows once
ga_panchanga is rebuilt; (uu2) must be corrected in migration 1221 before the rebuild. Handled
separately from this lane (no edit here).

## Residual findings (recorded, no code changed)

`tara_bala_natal_baseline` is a pure function of the birth nakshatra id (correct as a function), but
the id comes from `pi.nakshatra`, which is the Lahiri-based `panchanga_instant`. Likewise the five
`panchanga_nakshatra_moon` row sets are all emitted from the same Lahiri `pi`. Both therefore use
the Lahiri nakshatra for all five ayanamshas. Harmless on the canonical chart (the stored Moon
nakshatra is Purva Bhadrapada for all five ayanamshas) but latent for any chart where an ayanamsha
puts the Moon in a different nakshatra than Lahiri. Not fixed in this lane.

Real-Postgres proof of the position-fact read (`tests/test_ga4_chandra_bala_birth_sign_pg.py`,
marked `integration`, so the generic sidecar job deselects it; it RUNS in the dedicated ci.yml step of the
DB-service job (`ga4_moon_sign_test`, no `-m` filter) and FAILS, never skips, under `GITHUB_ACTIONS=true`
when `GA4_MOON_SIGN_TEST_DATABASE_URL` is missing or the database is unreachable; it skips only on a
local run with the variable unset. Verified on a disposable PG 15 with production column types chart_id uuid, build_id uuid, computed_at timestamptz; synthetic rows only):
18 tests passed. Safety: the fixture TRUNCATEs `chart_facts`, so it refuses (`REFUSED`) any DSN that is
not loopback/unix-socket, any database not named EXACTLY `ga4_moon_sign_test` (a `<x>_test` pattern would
let a staging copy be wiped), and any existing `chart_facts` carrying columns beyond the test's own minimal
table; DB-free unit tests prove each refusal (including `pms_test`, `ga4_moon_sign_test_backup`,
`madhav_prod_test`, `postgres`, remote hosts) and mutants of each rule go red; on a real PG the refused
databases kept their rows. Five ayanamshas (Aquarius x4, Pisces for surya_siddhanta_classical) read exactly,
with decoys excluded (other graha, other key, other category, other chart, non-canonical ayanamsha);
dict-row and tuple-row connections agree. Two build generations of the same key: the LATEST
`computed_at` (the newest build) wins, because the newer build's fact supersedes the older one; an
equal-`computed_at` tie is broken by the higher `build_id`. Verified for every insertion order of 2 and
3 generations (all permutations), 25 repeats each, and under PYTHONHASHSEED 0/1/2/3/random in
subprocesses (identical output). A missing fact and an unrecognised stored sign ('Kumbha', 'aquarius',
'', 'Ophiuchus') both raise `RuntimeError` naming the ayanamsha. Mutations (each red, writer restored
to the committed bytes afterwards): drop the whole tie-break (7 failed), drop only `build_id DESC`
(1 failed: the equal-instant tie), drop the `fact_key` pin (2 failed), oldest-wins `computed_at ASC`
(9 failed).

Not verified here: a real-chart rebuild (production rebuild is not in scope); the hook counts rest on
the synthetic rehearsal plus the stored-row read.
