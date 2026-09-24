---
artifact: KALA_BRIEF_INDEPENDENT_REVIEW
canonical_id: REVIEW_KA_GRAHA_SANCARA
version: "1.1"
status: ISSUED
date: 2026-09-24
brief_under_review: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_GRAHA_SANCARA_ELEVATION_BRIEF_v1_0.md (frontmatter version 1.1)
reviewed_at: "worktree /Users/Dev/madhav-l3/layer-briefs, branch l3/kala-layer-briefs, HEAD 27b0146f3; 9feac52d7 and 4d8c6aa9b are both ancestors; every cited code file is byte-identical across 9feac52d7 → 4d8c6aa9b → HEAD (git diff --stat empty on all nine)"
reviewer: "Fable 5.1 review agent, fresh context, read-only; one pure in-process swisseph computation run (Moshier on this host — retflag 65860 has the MOSEPH bit; no DB, no network, no repository write except this file)"
method: "REVIEWER_PROMPT_TEMPLATE_v1_0.md followed; RE-REVIEW of v1.0's 20 findings at source (the brief's §12 disposition claims were not trusted); then a fresh pass for defects the rewrite introduced"
predecessor: REVIEW_KA_GRAHA_SANCARA_v1_0.md (REWORK, 20 findings)
---

# Independent re-review — `KA_GRAHA_SANCARA_ELEVATION_BRIEF` v1.1

## 1. Verdict

**ACCEPT_WITH_CORRECTIONS.** The three load-bearing premises v1.0 got wrong (00:00-UT live
path, TRUE node on both engine paths, constants-only fan-out) now read as the code reads, and the
reference is correctly flipped to the served `bg_ephemeris_engine` surface; but the rewrite
re-asks as an "L0 question" a fact and remedy already written down in-tree (N1), leaves a third
convention divergence between the two implementations unnamed while mis-mapping the field that
carries it (N2), and specifies one proof-matrix row against an envelope that does not exist under
its own design (N3) — corrections, not a rework of premises.

## 2. Findings (new in v1.1)

| id | sev | brief's claim (section) | found at source | proposed correction |
|---|---|---|---|---|
| N1 | MAJOR | §10.4 "**L0 question:** `l0_ephemeris.py:77/287` computes `swe_id 11` (TRUE) under a 'Mean North Node' comment — is the stored knot set intended TRUE … or MEAN?"; §4.4 "raised to L0 as a question"; §5 QUALIFY_LIMIT "PATH-A `node_convention='true'` until L0 answers"; §7 Duplication "Rāhu differs by ~1° until L0 answers"; §8 "(4) node frame with L0's answer" | The fact is already recorded and the remedy already specified in this tree. `L0_REPAIR_EXECUTION_PROMPT_v1_0.md:85-87` item 7: *"The table stores the **TRUE** node under a contract asserting mean, at a **noon-UT** epoch, and declares neither. Both must be declared on the row."* Item 6 (`:77-83`) gives the degree-level anchor (TRUE 50.049248°, MEAN 49.033044° at JD 2445735.717361). Saṅgam M-1 row `SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md:44`: *"disposition (b): true L0 knots retained, mean derived at read in the L0 service, the 1.016204° / 3658.3″ mean↔true gap declared per row"* (marked `[A]` author-layer; the mean ruling itself `[N]`). Binding B6 (`:79`): *"the degree-level anchor (L0 item 6) plus a per-call `retflag`/node-mode assertion"*. Nothing in tree treats the store's frame as undecided. The code at `l0_ephemeris.py:77` (`"swe_id": 11  # Mean North Node`) and `:289` (`swe.calc_ut(jd, 11, flags)`) is as the brief says (`:287` is off by two, see N10); `MEAN_NODE=10, TRUE_NODE=11` re-verified in-process. | Collapse §10.4 to a citation of item 7 + disposition (b): the store is TRUE, stays TRUE, and the row declares it. Then §4.4/§5/§7/§8 stop waiting on "L0's answer": PATH-A either derives mean at read from the knot's JD (the ruled mechanism; `derive_sidereal` already runs at read, so a `swe.calc_ut(jd, MEAN_NODE)` at the same noon JD is the same class of read-time derivation) with the gap declared, or asserts `node_convention='true'` honestly while that derivation is unbuilt. The mislabelled comment at `:77` remains a one-line L0 hygiene note, not a decision. |
| N2 | MAJOR | §4.5 mapping table "`frame ↔ ayanamsa_application`"; §2.4 "sidereal longitude (PATH-A) … `ayanamsa_application` declared" (no value given); §3 "Two answers, two frames" (time + node only); §7 Duplication "longitudes within the date-grain tolerance" | `ayanamsa_application` is defined at `SANGAM_RULING_SHEET_v1_0.md:465` as ∈ `{apparent_flg_sidereal (project convention, reproduces L1), mean_get_ayanamsa_ut}` — *how* the ayanāṃśa is applied, after "the 14.82″ nutation episode". The route's `frame` is the constant `"geocentric_sidereal"` (`routers/ephemeris.py:47`) — a coordinate frame, not an application method; the mapping is semantically wrong. And the two implementations **differ on this element**: PATH-A is `derive_sidereal` = `set_sid_mode() + get_ayanamsa_ut()` subtraction (`l0_ephemeris.py:168-172`) → `mean_get_ayanamsa_ut`; the route (and `compute_transits.py:83`) use `FLG_SIDEREAL` (`routers/ephemeris.py:147`) → `apparent_flg_sidereal`. That is a third convention divergence between PATH-A and the instant path (after time basis and node frame) that the brief does not name; at date-grain tolerance it is invisible, which is exactly why it must be declared rather than absorbed. | Add `ayanamsa_application` to §2.4 with its value per path (PATH-A `mean_get_ayanamsa_ut`; route/instant path `apparent_flg_sidereal`), to §3's "two frames", to the §7 Duplication row (declared, not tolerated), and to the transition-parity/golden-fixture contract. Fix the mapping: `frame` has no build-side counterpart; `ayanamsa_application` has no served-route counterpart today and must be **added** to `_service_context` (in `may_touch`) or declared absent. |
| N3 | MAJOR | §7 Delivery row "sentinel `claim_grain='date_grain'` on a PATH-A answer → reaches the served envelope → detector fails when absent" | Under the brief's own design the served envelope is `/api/compute/ephemeris_at_t` (`routers/ephemeris.py:280-291`), which never carries a PATH-A answer — the route computes at the instant and the engine delegates *to* it, not the reverse. PATH-A's only consumers are in-process `EphemerisResult` readers: L4 `brahmagyan/phala/muhurta.py:737` and the writer/probe self-tests. `EphemerisResult` (`engine.py:129-135`) has no `claim_grain` field. The row names a detector with no surface to observe; it cannot go red or green as written. | Re-specify Delivery against the envelope PATH-A actually reaches (`EphemerisResult`, gaining `time_basis`/`claim_grain` fields; observed at `muhurta.py:737`'s read), and add a separate Delivery row for the served route's `_service_context` (`input_precision`, `node_mode`, `ephemeris_backends_observed`) reaching the TS wrapper — which today drops `service_context` entirely (`call_service_wrappers.ts:250-258` forwards only `datetime_utc, ayanamsha_id, jd, positions, count`). That drop is the real delivery defect and the brief does not name it. |
| N4 | MINOR | §7 Irrelevant control "`is_retrograde` convention on nodes declared"; §2.4 `is_retrograde` (nodes) row; §5 PRESERVE `applying_or_separating` | Ketu's **speed sign** also differs: the route gives Ketu the *same* signed speed as Rāhu (`routers/ephemeris.py:163-168`, comment "same signed angular speed"; mean-node speed −0.05299°/d measured), while both engine paths **negate** it (`compute_transits.py:199` `-planets["Rahu"]["speed_deg_per_day"]`; L0 `l0_ephemeris.py:292` `speed = -rahu_result[0][3]`) — Ketu direct on the engine, retrograde on the route. `GrahaState.applying_or_separating` (`engine.py:84-126`) branches on `speed_dps` sign, so after delegation every Ketu applying/separating verdict flips unless the convention is pinned. | Add Ketu `speed_dps` sign to the parity contract and §2.4; state which convention `applying_or_separating` is preserved under. |
| N5 | MINOR | §4.3 "the engine's live path delegates to it (or both call one shared kernel …)"; §5 "The four overlay writers: unaffected" | The route's `NAKSHATRAS` spell `'Moola'`, `'Purva Phalguni'`, `'Uttara Bhadrapada'` (`routers/ephemeris.py:90-96`); the engine's spell `"Mula"`, `"PurvaPhalguni"`, `"UttaraBhadrapada"` (`engine.py:43-51`) — and the engine's tuple is what `ka_kota_chakra/writer.py:56`, `ka_moorti_nirnaya/writer.py:49`, `ka_vedha_gochara/writer.py:60` import. If the engine takes `PlanetPosition.nakshatra` from the kernel the names change under the writers; if it re-decomposes from longitude with its own tuple they do not. The brief does not say which. | State that the engine consumes only `(lon, speed, retflag)` from the kernel and keeps its own decomposition/constants; put the two spellings in the parity contract as a declared non-field. Also: the route rounds longitude to 4 dp and speed to 6 dp (`:126,:132`) before the envelope — the golden fixture's tolerance floor is that rounding, worth stating in §10.6. |
| N6 | MINOR | §2.4 route positions "the qualified computation"; §4.11 "The route as it is today (already qualified)"; §0 "the unqualified implementation certifies the qualified one" | Per call the route labels itself **`backend_qualification_state: "UNQUALIFIED_BACKEND"`** — a constant (`routers/ephemeris.py:54-58`) with `qualification_requires: "VERIFIED_REGISTRY_PROBE_RECEIPT"` and `registry_health_detector: pipeline.orchestrator.service_probes._probe_ephemeris_engine` (`:69-70`). That L0 probe (`service_probes.py:374-`) hashes the `.se1` corpus at `/app/ephe` and runs its own `calc_ut` at the forensic JD — it qualifies the process's Swiss corpus, not the route's code path. So: the route is *instrumented* (backend observed) and *corpus-qualified by receipt*; it is not "qualified" per call, and no probe exercises `_calculate_sidereal_positions` itself. Two gates exist: the L0 receipt (corpus) and the TS availability contract (`call_service_wrappers.ts:215-217`, the other engine's probe). | Say "instrumented and L0-receipt-qualified"; name both gates; the thesis sharpens to "no probe measures the served code path". |
| N7 | MINOR | §4.6 / §10.2 "`AYANAMSHA_MAP` … with `DEFAULT_AYANAMSHA` as the default" | No Python symbol `DEFAULT_AYANAMSHA` exists in L0. `brahmagyan/l0_ephemeris.py:121` `_DEFAULT_AYANAMSHA = "lahiri"` (legacy key), `:137` `_DEFAULT_READ_AYANAMSHA = "lahiri_chitrapaksha"` (private). The two importable `DEFAULT_AYANAMSHA` symbols in the sidecar are both the **legacy** `'lahiri'`: `pyjhora_adapter/_ayanamsha.py:42`, `panchang_engine/ayanamsha.py:15`. The canonical `'lahiri_chitrapaksha'` default lives in TS (`registry/constants.ts:2`) and in `routers/ephemeris.py:233` / `routers/jaimini.py:80`. Blueprint SC-10's "every default imports `DEFAULT_AYANAMSHA`" (`:289`) names the TS constant; a Python writer following the brief literally imports the wrong one. | Name the exact symbol (`l0_ephemeris._DEFAULT_READ_AYANAMSHA`, or a new public alias in L0 — which is `must_not_touch`, so say so) and its value. |
| N8 | MINOR | §1 "corrected in blueprint v5.1" (twice: L0 items row; §3.5 row 1) | No v5.1 exists: `KALA_ELEVATION_BLUEPRINT_v1_0.md:4` `version: "5.0"`; grep `5.1` in its changelog empty. On this base `:189`/`:287` still say "applied", `:383` "open and RED", `:317` still "engine import, comp". The brief asserts a correction in an artifact not on its stated revision. | "to be corrected in the blueprint's next version" or cite the commit that does it. Also refresh `source_revision` — "byte-identical to HEAD 4d8c6aa9b" is true but HEAD is now 27b0146f3 (re-verified identical). |
| N9 | MINOR | §4.2 / §10.5 binding amendment "`time_basis += 'midnight_ut_knot'` … only so the *retiring* path can be labelled honestly for one generation" | `KALA_SYNERGY_BINDING_v1_0.md:31` enum `{event_instant, noon_ut_knot, date_grain_midpoint}` — the member is absent, so the ask is real. But the binding has **no amendment procedure** (grep `amend` empty) and `KALA_SYNERGY_AMENDMENTS_v1_0.md` does not carry `time_basis` at all; and the need is avoidable: §5 says "rollback = the engine's delegation is one flag", i.e. the 00:00-UT path survives only as a rollback target that no caller is served from. Labelling a path nobody is served from is what B1's enum is not for. | Prefer: retire the delegate in the same commit as the delegation (no labelled generation, no enum change); if a rollback flag is kept, the flagged path is `unqualified` (F06) with `time_basis` null and a reason, not a new enum member. If the amendment is still wanted, route it to the binding's owner with the amendments artifact as its home. |
| N10 | NOTE | `[R]` line numbers copied from v1.0 | These resolve to the right *content* a few lines away: `l0_ephemeris.py:277` → `:278` (noon `julday(...,12.0)`; also `:164` in `_tropical_to_jd`); `:287` → `:289`; `:139-156` → `:140-158`; `compute_transits.py:77-79` → `:73-75` (`_sidereal_jd_ut`), `:79-80` → `:78-79`, `:187` → `:190`, `:216` → `:217`, `:197-198` → `:197-200`; `routers/ephemeris.py:48` → `:49`, `:128` → `:131`, `:250-258` → `:253-260`, `:264-268` → `:267-271`, `:140-173` → `:136-170`, `:176-197` → `:173-197`, `:45-46` → `:43-44`, `:211-213` → `:210-212`; `service_probes.py:582-583` → `:578-579`. | Correct in place; v1.0's numbers were off, the files did not change. |
| N11 | NOTE | §4.10 / §7 Boundary "2150-12-31 23:59 UTC → … PATH-A `unavailable(out_of_range)`" | `BG_EPHEMERIS_END = date(2150, 12, 31)` with `<=` (`engine.py:58,:416`); `q_date = dt.date()` in the instant's own tz (`:393`) → 2150-12-31 is **in range**; PATH-A would read, not refuse. The out-of-range boundary is 2151-01-01 00:00 UTC (and 1899-12-31 23:59 UTC below). | Fix the fixture instants. |
| N12 | NOTE | §4.3 "shared kernel extracted from `_calculate_sidereal_positions`"; §2.1 "two registered identities" | The kernel is L0-identified (`service_asset_id: "bg_ephemeris_engine"`, seed `asset_registry_seed.ts:465`, layer `brahmagyan`) yet lives in a FastAPI router module (`routers/ephemeris.py:1-7` imports fastapi/pydantic); `brahmagyan/` is `must_not_touch`. Delegating means `services/` (and, transitively, L4 `muhurta.py`) importing from `routers/` — an inverted dependency the brief does not name — or extracting an L0 kernel into a home the brief cannot touch. | Name the kernel's target module and owner; if it is L0's, it is a DEMAND on L0 like items 6–7, not an engine change. |
| N13 | NOTE | frontmatter `must_not_touch` | Guide `KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md:73-75` lists fixed entries `platform-mcp/src/tools/kala_views/**`, `.github/workflows/deploy.yml`, "applied migrations 1033–1070"; the brief carries "applied migrations" only. Context `:103` makes `kala_views` Pūrṇa's. | Add the two missing fixed entries. |
| N14 | NOTE | `may_touch` "(compute_transits.py …) its other consumers traced at stage 3"; §5 RETIRE_AFTER_MIGRATION "for this caller" | Traceable now: `platform/scripts/temporal/signal_activator.py:46` `from compute_transits import get_transit_states, parse_iso8601, SIGNS`; plus the CLI `main()` (`compute_transits.py:225-`). No sidecar/MCP/TS consumer. | Name them; "for this caller" stands. |
| N15 | NOTE | §4.12 / §7 Value "golden-value fixture at the served envelope" | Where the golden values come from is unstated. If pinned from the same kernel they detect mutation/regression only (fine, and consistent with §N.4 "no JH-parity oracle"); the FORENSIC instant is the one independent ground. Also §10.6's tolerance must be ≥ the route's 4-dp rounding (N5). | State provenance: kernel-pinned at the transition commit + FORENSIC anchor as the independent value; tolerance ≥ 0.5e-4°. |
| N16 | NOTE | §4.4 "Ripple: … `pyjhora_adapter/transits.py` and L4 `muhurta.py:737` are named as consumers whose values move" vs §5 "L4 … (PATH-A — unchanged unless L0's stored node changes)" | Both cannot hold; L4 reads PATH-A (`muhurta.py:737`, `db_conn=conn`, no `force_live`), which item 3 does not touch. Under N1's ruled mechanism (mean derived at read) L4's Rāhu/Ketu *would* move — by ~1°. | Make §4.4 and §5 agree, and say which mechanism moves L4. |
| N17 | NOTE | changelog "F19/F20 … `'mixed'` dropped"; §12 "F20 accepted (§2.1, §1)" | §1 only *notes* `'mixed'` is never produced (`engine.py:134`); no section proposes dropping or producing it. | Add the disposition to §4 or strike "dropped" from the changelog. |

## 3. Citations verified

| citation (as in brief) | resolved? | what is actually there |
|---|---|---|
| `engine.py:19-20` TRUE_NODE everywhere | yes | `:19-20` |
| `engine.py:43-51` NAKSHATRAS; `:58` END; `:61` ALL_GRAHAS | yes | as stated (`"Mula"`, `"PurvaPhalguni"` spellings — N5) |
| `engine.py:64` SUPPORTED_AYANAMSHAS | yes | `:64` |
| `engine.py:84` applying_or_separating | yes | `:84-126`; branches on `speed_dps` sign (N4) |
| `engine.py:134` `'mixed'` | yes | `:134` |
| `engine.py:143-168` cache; key `:151-152` | yes | `:143-168`, `:151-152` |
| `engine.py:173-279` PATH-A; `:220`; `:228,:248,:256`; `:253`; `:263` | yes | all as stated |
| `engine.py:284-339` live; `:306-310`; `:312-313` | yes | `:312` `q_date = query_dt.date()`, `:313` `get_transit_states(query_dt, q_date, …)` |
| `engine.py:346`; `:376-379`; `:381-391`; `:393`; `:396-407`; `:416`; `:425-427` | yes | as stated |
| `compute_transits.py:54,:63` TRUE_NODE | yes | `:54` comment, `:63` `swe.TRUE_NODE` |
| `compute_transits.py:77-79,:183` 00:00 UT jd | content yes, lines off | `_sidereal_jd_ut` `:73-75` (`julday(..., 0.0)` `:75`); `jd = _sidereal_jd_ut(query_date)` `:183` |
| `compute_transits.py:79-80` SIDM_LAHIRI | ~ | `:78-79` |
| `compute_transits.py:83` FLG_MOSEPH; `:84` retflag discarded | yes | `:83`, `:84` `pos, _ = swe.calc_ut(...)` |
| `compute_transits.py:158-161` signature | yes | `:158-164` `get_transit_states(birth_dt, query_date, ayanamsha='lahiri', *, natal_moon_sign=None)` |
| `compute_transits.py:187,:197-198` nodes not retrograde | ~ | `:190` (planets), `:197-200` (Ketu forced False); Ketu speed negated `:199` (N4) |
| `compute_transits.py:216` `"ephe_mode": "moshier"` | ~ | `:217` |
| `routers/ephemeris.py:5`; `:7` SWISS_STATE_LOCK | yes | `:5`, `:7`; lock held `:145` |
| `routers/ephemeris.py:11-12,45-46` identity | ~ | `:11-12`; `service_asset_id`/`registry_generation` `:43-44` |
| `routers/ephemeris.py:12-24` `_ephemeris_backend` | yes | tuple `:13-17`, fn `:20-24` |
| `routers/ephemeris.py:27-73` `_service_context`; `:48` node_mode; `:66` HTTP_422 | ~ | `:27-72`; `node_mode` `:49`; `:66`; `backend_qualification_state` constant `:54` (N6); `frame` `:47` (N2) |
| `routers/ephemeris.py:82` MEAN_NODE | yes | `:82` |
| `routers/ephemeris.py:128` retrograde | ~ | `:131`; rounding `:126,:132` |
| `routers/ephemeris.py:140-173` helper; `:154-156` retflag | ~ | `:136-170`; `:154-156` yes; Ketu same-signed speed `:163-168` |
| `routers/ephemeris.py:176-197` natal endpoint | ~ | `:173-197` |
| `routers/ephemeris.py:200,:244` engine not imported | yes | comment only; no import |
| `routers/ephemeris.py:211-213` "rather than a second swisseph integration" | ~ | `:210-212` |
| `routers/ephemeris.py:223-225`; `:226-232`; `:233`; `:241`; `:242-291` | yes | as stated |
| `routers/ephemeris.py:250-258` 422; `:264-268` naive rejected | ~ | `:253-260`; `:267-271` |
| `writers/ka_graha_sancara.py:94`; `:118-248`; `:172` | yes | raise `:94-97`; checks `:118-251`; `:172` "PATH-B gives Moon at 324.4787° sidereal" |
| `l0_ephemeris.py:77`; `:287` | `:77` yes; `:287` → `:289` | `:77` `"swe_id": 11 # Mean North Node`; `:289` `swe.calc_ut(jd, 11, flags)`; Ketu speed negated `:292` |
| `l0_ephemeris.py:91-119` map; `:118-119` `{}`; `:137`; `:139-156` | ~ | `:90-119`; `:119`; `:137`; `_resolve_read_ayanamsha` `:140-158`; `_DEFAULT_AYANAMSHA='lahiri'` `:121` (N7) |
| `l0_ephemeris.py:277` noon | ~ | `:278` (and `:164`) |
| `l0_ephemeris.py:168-172` derive_sidereal | (not cited; read for N2) | `set_sid_mode() + get_ayanamsa_ut()` |
| `ka_kota_chakra/writer.py:56`, `:96`; `ka_moorti_nirnaya/writer.py:49`, `:77`; `ka_sudarshana_varsha/writer.py:34`; `ka_vedha_gochara/writer.py:60`, `:106` | yes | constants-only imports; own `FROM ephemeris_daily` SQL |
| `service_probes.py:292`; `:342-347`; `:546-548`; `:582-583`; `:618` | ~ | `:292` def; `:342-347` yes; `:546-549`; `:578-579`; `:617-619` |
| `service_probes.py:374` `_probe_ephemeris_engine` | (read for N6) | corpus SHA-256 + own calc |
| `nirmana_probe.py:69,107` | yes | `:69` hexdigest; `:107` `compare_digest`; `_ASSET_PROBE_TYPES` `:20-27` |
| `nirmana_probe_contracts.json` | yes | `bg_ephemeris_engine.allowed_ephemeris_backends: ["swiss_ephemeris_file"]` `:23`; `ka_graha_sancara.forensic_ayanamsha: "lahiri"` `:34` |
| `call_service_wrappers.ts:170-262`; `:215-219`; `:227`; `:235-240` | yes | `:172-262`; contract `:215-217` (sha `2e71…`, 900 s); `:227`; `:235-239`; `service_context` not forwarded `:250-258` (N3) |
| `pyjhora_adapter/transits.py:82-86` | yes | `:82-87` `force_live=True`; no importer of the adapter found (non-test) |
| `brahmagyan/phala/muhurta.py:737` | yes | `get_ephemeris(window_start, ayanamsha="lahiri", db_conn=conn)` |
| tests: `tests/test_ka_graha_sancara.py`, `tests/l3/test_m3_graha_sancara_defects.py:71-74`, `tests/l3/test_ephemeris_at_t_sidecar_route.py:83-86`, `tests/test_ephemeris_ayanamsha.py` | yes | all exist; `:72-73` "exact birth instant … ~324.48°"; `:83-86` 422 test |
| `asset_registry_seed.ts:2230-2245` | yes | `:2230-2245`; `bg_ephemeris_engine` `:465-` (layer brahmagyan, "MEAN_NODE convention") |
| "highest migration 1072"; no node_mode/epoch migration | yes | `platform/supabase/migrations` tops at 1072 (`platform/migrations` at 1070); grep → only `624_…probe_contract.sql` |
| REGISTER:136; Strategy `:271`; Q01/Q03/Q09 (`:62,:64,:70`) | yes | Q09 "What changes with birth uncertainty or convention?" |
| STATE.md `:219-235` | yes | ★ finding |
| Blueprint `:30,:31,:40` G4 retracted; `:189`; `:287`; `:289`; `:317`; `:383`; `:899`; `:950`; `:465` | yes | as stated; version `5.0` (`:4`), no v5.1 (N8) |
| Synergy audit `:59` | yes | "Kṣetra reads mean via `ephemeris_daily`" |
| Chronicle §11.18 / w2g | yes | `KALA_ELEVATION_CHRONICLE_v1_0.md:505-533`; `w2g` in `ka_gochara.py`, `bg_gochara_arcs.py`, `services/w2g_validations/` |
| `panchang_engine/__init__.py:71,149,252,347` | yes | `set_ephe_path(None)` ×4 |
| `routers/jaimini.py:76-80`; `constants.ts:2` | yes | canonical five; `'lahiri_chitrapaksha'` |
| Binding `:31` time_basis; `:32` claim_grain; `:43` comparable_with; `:79` B6 | yes | `midnight_ut_knot` absent; no amendment clause (N9) |
| Foundation `:39` F12; `:65` COMPUTED_FACT_CONFIGURATION; F06 `:33`; F28 `:55`; DP01 `:84`; DP03 `:86`; DP07 `:90` | yes | as stated |
| `SANGAM_STAGE3_STATE.md:160` frame_vector | yes | `(ayanamsha_id, ephemeris_backend, epoch_convention, ayanamsa_application, node_convention, house_frame)` |
| `L0_REPAIR_EXECUTION_PROMPT_v1_0.md:77-87` items 6–7 | (not cited; read for N1) | store is TRUE; declare on row |
| swisseph figures | re-run | MEAN_NODE=10, TRUE_NODE=11; Moon 324.4787 / 327.0550 / 330.4060 (00:00 / 05:13 / 12:00 UT); true−mean 1.0213° at 05:13 UT; Δ 2.5763° |

## 4. What I could not verify, and why

- Production state (`service_health`, `.se1` on the host, whether PR #2727 / migrations 1075–1079 are applied there, live incidence) — no DB, no network. This host has no `.se1` (retflag MOSEPH); the figures are Moshier, degree-level.
- Whether `pyjhora_adapter.transits.compute_transits` has any caller — none found in sidecar/scripts/MCP/TS non-test scope by grep; not asserted unused.
- "Service payload frozen at `47131772b`" — unverified, as the brief itself says.
- Which node `ephemeris_daily` physically stores — inferred from `l0_ephemeris.py:77,:289` and now corroborated by `L0_REPAIR_EXECUTION_PROMPT_v1_0.md:85`; not queried.
- Whether Saṅgam disposition (b) (`[A]` author-layer) has been ratified by the native — the plan row marks the mean ruling `[N]` and the mechanism `[A]`; I report it as the in-tree remedy, not as a ruling.
- Per-call latency — not measured; not claimed.

## 5. Conformance to the binding

- **B1** `time_basis`: `noon_ut_knot` (PATH-A) in enum; the engine's live path is a 00:00-UT knot with no member — the brief now says so and proposes `midnight_ut_knot` (N9: avoidable; no amendment procedure exists). `claim_grain` `date_grain`/`instant_grain` in enum. `inclusivity` n/a stated. tz rule: the Asia/Kolkata default is now named and slated for removal (§4.7) — conformant as a plan.
- **B2** `epistemic_class='COMPUTED_FACT_CONFIGURATION'`, `operator_role='computation'`, `completeness_state` (`unavailable` now reserved for out-of-range / PATH-A read failure; 422 kept for caller error) — conformant. `comparable_with='different_convention'` across ayanāṃśas — stated. `tier_basis`, `independence_group` — n/a with reason, stated.
- **Fields named outside B1–B7**: the route's `node_mode`, `frame`, `ayanamsha_id`, `input_precision`, `ephemeris_backends_observed`, `backend_observation_state`, `backend_qualification_state`, `failure_contract` are adopted from code, with a declared mapping to Saṅgam's `node_convention` / `ayanamsa_application` / `epoch_convention` / `ephemeris_backend`. Two mapping rows are wrong or empty: `frame ↔ ayanamsa_application` (N2 — different meanings) and `epoch_convention` (build-side only — but the served route's `input_precision`/`instant_utc` is its epoch statement and should be mapped, not left "build-side only"). `ephemeris_backends_observed ↔ ephemeris_backend` is a set↔scalar mapping; say so.
- **B6** node longitude mean: the brief now states the delta honestly and asserts `'true'` on PATH-A until changed; N1 shows the "until" condition is already specified in tree.
- **B7**: the §7 Value row can go red under mutation (kernel `MEAN_NODE → TRUE_NODE` fails a pinned golden); Transition row can go red (disagreement); Delivery row cannot go either way as written (N3).

## 6. Disposition of the twenty v1.0 findings (verified at source, not from §12)

| v1.0 | status | verified how |
|---|---|---|
| F1 instant vs 00:00 UT | **RESOLVED** | §0/§2.2/§2.4/§3/§4.2-3/§4.9/§7 all say 00:00 UT; `engine.py:312-313` + `compute_transits.py:75,:183` re-read; figures re-run |
| F2 node frame is a computation delta | **RESOLVED** (N1 overlays the "until L0 answers" framing) | §4.4 computation delta with ripple; `'true'` asserted on PATH-A; §7 Duplication declares ~1°; §10.3 routed |
| F3 constants-only fan-out | **RESOLVED** | four import lines + three `FROM ephemeris_daily` SQL sites re-read; §2.3/§5 match |
| F4 rival backend vocabulary | **PARTIAL** | route names adopted, no `swieph`/`ephemeris_backend ∈` residue (grep empty); but the declared mapping is wrong for `frame ↔ ayanamsa_application` (N2) |
| F5 retflag discarded / compute_transits outside may_touch | **RESOLVED** | `may_touch` now lists it with `:83,:84,:216`; other consumer nameable now (N14) |
| F6 wrong reference | **RESOLVED** | §10.1 flipped to the `bg_ephemeris_engine` surface; `routers/ephemeris.py:43-44,:210-212` confirm identity |
| F7 migrations 1075–1079 "applied" | **RESOLVED** | frontmatter + §1 + §5 state the blocker; 1072 ceiling confirmed (`supabase/migrations`) |
| F8 422 replaced by `unavailable` | **RESOLVED** | §4.6 keeps 422; §7 Negative expects 422 / typed `ValueError`; `:253-260` and test `:83-86` unchanged |
| F9 Value row cannot go red | **RESOLVED** (N15 provenance note) | §4.12/§7 golden fixture + transition-only parity |
| F10 fourth vocabulary | **PARTIAL** | L0 `AYANAMSHA_MAP` adopted (§4.6); the default symbol named does not exist in Python and the ones that do are the legacy key (N7) |
| F11 date-keyed cache | **RESOLVED** | §4.8 instant key when computing at an instant; PATH-A key QUALIFY_LIMIT |
| F12 Asia/Kolkata default | **RESOLVED** | §2.2 names it; §4.7 removes it; `:381-391` re-read |
| F13 `is_retrograde` on nodes | **RESOLVED** (N4 adds Ketu speed sign) | §2.4 row + §7 Irrelevant control |
| F14 ranges/paths/may_touch | **PARTIAL** | test paths, seed path, may_touch widening fixed; ~17 line numbers still off by 1–4 (N10) |
| F15 "Synergy audit §2 / G4" | **RESOLVED** | §1 cites chronicle §11.18; G4 retraction cited to `:30,:31,:40` |
| F16 `estimated_seconds` | **RESOLVED** | grep of the brief empty |
| F17 §0 vs §2.3 consistency | **RESOLVED** | both now "live for no L3 writer" with the same caller list |
| F18 availability contract / probe digest | **RESOLVED** | `call_service_wrappers.ts:215-217` cited in §0/§1/§2.2/§4.9/§5; Pūrṇa packet named |
| F19 PATH-A `None` → vocabulary error | **RESOLVED** | §2.2 describes it; §4.6 `unavailable(reason='path_a_read_failed')` |
| F20 `service_asset_id` / `'mixed'` | **PARTIAL** | §2.1 states the two identities; `'mixed'` noted in §1 but "dropped" only in the changelog (N17) |
