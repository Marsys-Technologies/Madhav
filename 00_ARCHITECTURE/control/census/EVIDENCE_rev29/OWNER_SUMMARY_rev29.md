# Owner summary: certification census after the clean-up round (registry revision 29)

Written for: the owner (non-technical). This is the second measurement. The first (registry revision 28, 66 of 82) is in `../83316abb9-1791733139506-run2-cap600/OWNER_SUMMARY.md`; the two are kept apart and never mixed. Detail files are next to this one: `lists/CERTIFIED_LIST.md`, `lists/BLOCKERS_BY_CLASS.md`, `lists/FIX_LIST.md`, `strict/`.

## Bottom line
**76 of the 82 data assets are certified** on the agreed bar (named limits and disclosed gaps allowed): up from 66. On the stricter bar, where every check must pass or be formally "not applicable", **13 of 82** (up from 12).

**What "certified" means here:** the census's certified list on the agreed bar (N-268), for registry revision 29, measured on a copy of production taken on 12 Oct 2026 (backup 1791769727082) for the native's chart plus the shared reference data. It is **not** a set of formal per-check ledger records: you dropped that ceremony (decision N-152), and this round keeps to that. The measurement files are committed in the repository as a hash-verified baseline (pull request noted at the end).

## By layer (certified / total)
| Layer | Certified | Not certified |
|---|---|---|
| Reference data (L0) | 38 of 39 | bg_sky_calendar |
| Chart facts (L1) | 18 of 20 | ga_structural, ga_vichara |
| Synthesis (L2) | 20 of 23 | bo_laksana, bo_laksana_rerank, bo_samskara |

69 of the 76 sit at a *declared limit* (single derivation 45, unverified transcription of a classical text 20, unsourced by declaration 3, ratified judgement 4). They are stated openly, not hidden. Certified does not mean every check passed.

## What the clean-up round fixed
- bg_rules: the seven empty-result rules (and one dash-only rule) are gone (3,002 to 2,994), and its integrity check was re-sealed.
- bg_ontology: the one-row counting mismatch is gone (728 = 728).
- bg_concordance: re-sealed and rebuilt on the new rule set.
- Two assets that inherit their parent's baseline (bg_nakshatra_medical, bg_transit_engine) no longer fail the baseline check wrongly; bg_prashna_rules' serving check now reads. (The two no-writer services still fail it: see the information-only table.)
- Seven assets now have a build that exercised the current rules, after a rebuild of 47 assets.

## The 6 not certified, and what each needs (next round)
| Asset | What it needs |
|---|---|
| ga_structural | A small registry change (its registry row names no target table, so two checks cannot run) **and** the spelling mix cleaned up: planet codes (JUP), planet names (Jupiter) and sign names (Aquarius) sit together in the same columns. |
| bo_laksana | Declarations for the JSON fields that mix spellings (none declared yet). Its one other open cell is a connection timeout on the shared copy, which would clear on a repeat run but cannot lift it on its own. |
| bo_laksana_rerank | Declarations for about 9 JSON paths still open; part of them is the nakshatra spelling change. |
| bo_samskara | A writer change so the checker can follow its insert, which means re-embedding about 127,000 rows. |
| bg_sky_calendar | A real measured disagreement: 10 of 31,104 eclipse rows are over the declared 180-second tolerance. The tolerance can only be changed with the measured deviations in hand. |
| ga_vichara | **An owner decision.** The native chart has no row in the slice it is checked on (the post-pass wrote none), and one earlier error sits in its build-history window. This round it stays partial and no exception was added. |

## Also in the residual (small, named)
- **bg_ephemeris_engine and bg_panchanga baseline check:** needs the latest probe record id declared as their probe run in the declarations.
- **bo_samvada fingerprint:** its output fingerprint reads unknown (probable timing clash while its view is re-created each build). Certification is unaffected; the fix is a later registry or permissions change.

## Five failures that block nothing (information-only checks)
| Check | Why |
|---|---|
| Count floors: bg_parihara_rules (440 vs 449), ga_vichara (7,774 vs 8,249), ga_yoga (53 vs 63) | Stale floors, not lost data: 9 orphan rows were deliberately deleted; 750 duplicate rows were removed on 3 Oct; and for ga_yoga an August correction made two yogas (Chatra and Ardhachandra) stricter, so they correctly no longer fire for this chart. The floors are to be set to the achieved counts with these reasons, in the parked migration, at the next full rebuild round (changing them now would reopen build windows). |
| Baseline: bg_ephemeris_engine, bg_panchanga | These two have no writer, only probe runs. Their probe evidence was overwritten by newer probe records (only the latest survives), so the "not applicable" rule that follows the build-record check correctly does not apply. Fix: record the current probe run in their declarations. |

## Known gaps in the evidence (for you)
1. **No semantic fingerprints** exist for 37 of the certified assets, so a formal ledger could not have been written for them even if wanted.
2. **One check has no detector** (the per-witness comparison): every asset reads "not applicable" there, by ruling.
3. **No automated job runs the census hash verification** yet (the repository's documentation says one does). I ran it by hand on the committed files. SS will add it to the follow-ups.

## Lessons (standing operational rules)
1. **Build windows.** A build counts as "exercising the current code" only if it was created after the latest change to the asset's writer code **or** the latest migration or registry edit that names the asset (even in a comment). Rebuild only after the last such merge; shared helper files reopen windows for several assets at once.
2. **A changed writer needs its stored integrity check re-sealed in the same round,** and the sweep must follow dependencies (bg_concordance was missed once because only the wording was considered).
3. **The database's read-only account has its own 2-minute limit;** a census run must override it for its session, or long reads are silently cut.
4. **Tests must prove what was sent and who cancelled it,** not a clock margin; timing assertions failed on busy runners three times.
5. **Revision labels.** Counts on revision 28 (66) and revision 29 (76) are never mixed.

## What was not covered
Kāla (timing layers), Mimāṃsā and Phala are on hold and not part of these counts. The second and third charts are out of scope until all six layers succeed on the native's chart. bo_samvada is lit and certified, but its output fingerprint still reads unknown (a probable timing clash while its view is re-created each build); it is a later-round fix.
