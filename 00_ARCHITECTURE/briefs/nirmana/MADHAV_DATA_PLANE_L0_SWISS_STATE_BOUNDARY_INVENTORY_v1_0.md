---
artifact: MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_INVENTORY
version: "1.0"
status: IMPLEMENTED_VALIDATED_PENDING_INDEPENDENT_CHALLENGE
decision: DP-SD-010
accepted_source_revision: 552fa76d21406fcbb7f534afbd9600330f3a6276
strategy_content_revision: d61469b6d96b956782548d36fb23f9e813e1ae98
approval_pin_revision: b1a0f17eb65494f21a00fd2b22d6264da76c3c38
scope_addendum_decision: DP-SD-011
scope_addendum_accepted_source_revision: b8e342049f0ac90e794bc3f547468a785a98d108
scope_addendum_strategy_content_revision: a112b64a61c60ff44369ba64eee73a3445a48461
scope_addendum_approval_pin_revision: add798f6ce37893f8c7ef3e771f30e15b0fb24f2
generated_on: 2026-09-13
---

# L0 Swiss-state boundary inventory

## Result

The non-test Python sidecar tree has **70 detector-owned direct or wrapper
Swiss-state operation owners**, **76 decorated serialized entry points**, and
four exact explicit-scope owners. The union is 80 boundary owners. Every live
state-dependent operation found by the source-tree detector is classified;
`UNRESOLVED = 0`.

All decorators and explicit scopes resolve to
`panchang_engine.swiss_state.SWISS_STATE_LOCK`. The tree contains one shipped
`RLock()` construction. `panchang_engine.__init__` is a compatibility re-export,
not another lock. This inventory does not claim deployment or production use.

## Detection contract

`platform/python-sidecar/tests/test_swiss_state_boundary.py` parses every
non-test `*.py` under the sidecar. It resolves direct `swisseph` imports,
renamed module imports, imported function aliases, PyJHora `drik` aliases,
PyJHora chart/strength calls, adapter setter aliases, canonical decorators and
canonical explicit scopes. The expected owner set is
exact, so an added, removed or moved operation fails until this artifact and
the detector are deliberately reconciled.

Negative fixtures prove that each of these is rejected:

- an unguarded literal `swe.set_sid_mode` plus `swe.calc_ut` sequence;
- a renamed `swisseph as ephemeris` sequence;
- `from swisseph import ... as ...` setter/calculation aliases;
- an unguarded PyJHora `drik.set_ayanamsa_mode` sequence; and
- a separate `RLock`, including one with a misleading Swiss-like name.

## Direct and wrapper operation owners

Every row below is `SERIALIZED`. “Decorator” means the complete function holds
the canonical re-entrant boundary. “Scope” means only the setter and dependent
calculation are inside `swiss_state_scope()` or the compatibility lock; DB and
unrelated work remain outside.

| File | Exact function owner(s) | Evidence |
|---|---|---|
| `brahma/l1/ganita/divisionals_writer.py` | `compute_vargas_for_native` | decorator |
| `brahmagyan/ganita/engine.py` | `compute_positions` | decorator |
| `brahmagyan/ganita/graha_sthana_writer.py` | `_compute_graha_sthana` | decorator |
| `brahmagyan/ganita/l1_engine_check.py` | `run_engine_smoke` | decorator |
| `brahmagyan/ganita/l1_positions.py` | `compute_positions_all_bodies` | decorator |
| `brahmagyan/l0_ephemeris.py` | `_compute_positions_for_date`, `derive_sidereal`, `query_ayanamsha_delta` | decorator |
| `brahmagyan/l0_ephemeris.py` | `build_ephemeris` | narrow scope; DB build is outside |
| `ga_writers/ga_dashas_writer.py` | `_get_moon_position`, `_mudda_solar_return_jd`, `compute_mudda_system` | decorator |
| `ga_writers/ga_dashas_writer.py` | `build_system` | narrow fallback scope; DB reads/writes are outside |
| `ga_writers/ga_sade_sati_writer.py` | `_detect_saturn_sign_changes`, `_detect_saturn_retrogrades` | decorator |
| `ga_writers/ga_sade_sati_writer.py` | `_lookup_tara_bala_for_saturn_at` | narrow computation scope; DB lookup is outside |
| `ga_writers/ga_strength_writer.py` | `_derive_ashtakavarga_shodhana_grids`, `_derive_bhava_bala` | decorator; each spans ayanamsha selection through final dependent result copy |
| `ga_writers/ga_vargas_writer.py` | `_compute_varga_positions` | decorator |
| `panchang_engine/__init__.py` | `compute_panchang`, `panchanga_instant` | decorator; path and Lahiri selection through final result |
| `panchang_engine/angas.py` | `_get_sun_moon_lon`, `compute_nakshatra` | decorator |
| `panchang_engine/ayanamsha.py` | `set_ayanamsha`, `get_ayanamsha_value` | decorator |
| `panchang_engine/lagna.py` | `_get_ayanamsha`, `compute_lagna` | decorator |
| `panchang_engine/planets.py` | `compute_planet_state`, `compute_all_grahas` | decorator |
| `panchang_engine/rich_topics.py` | `compute_sun_moon_dynamics` | decorator |
| `panchang_engine/timings.py` | `compute_sunrise_sunset`, `compute_moonrise_moonset`, `compute_day_events` | decorator |
| `panchang_engine/upagrahas.py` | `_ayanamsha`, `compute_upagrahas`, `compute_outer_planets` | decorator |
| `pipeline/orchestrator/service_probes.py` | `_probe_ephemeris_engine` | decorator |
| `pipeline/orchestrator/writers/bg_cohort.py` | `_require_pinned_ephemeris_runtime`, `compute_synthetic_positions` | decorator |
| `pipeline/orchestrator/writers/bg_sky_calendar.py` | `_require_swiss_file_backend`, `scan_eclipses`, `_scan_solar_eclipses`, `_scan_lunar_eclipses` | decorator |
| `pipeline/orchestrator/writers/ka_vighnakara.py` | `_get_sidereal_lon` | decorator |
| `pipeline/transit_search.py` | `_get_planet_pos` | decorator; mode/path are explicit cache dimensions |
| `pyjhora_adapter/compute.py` | `compute_chart` | decorator |
| `pyjhora_adapter/dashas.py` | `compute_dashas` | decorator |
| `pyjhora_adapter/houses.py` | `compute_ascendant`, `compute_midheaven`, `compute_bhava_chalit` | decorator |
| `pyjhora_adapter/panchanga.py` | `compute_panchanga` | decorator |
| `pyjhora_adapter/positions.py` | `_set_ayanamsha`, `compute_positions` | decorator |
| `pyjhora_adapter/sensitive_points.py` | `compute_sensitive_points` | decorator |
| `pyjhora_adapter/special_lagnas.py` | `compute_special_lagnas` | decorator |
| `pyjhora_adapter/strength.py` | `_set_ayanamsha` | decorator |
| `pyjhora_adapter/vargas.py` | `compute_vargas` | decorator |
| `routers/ephemeris.py` | `_calculate_sidereal_positions` | existing compatibility lock scope |
| `routers/pyhora.py` | `compute_natal`, `smoke_test` | async decorator; neither body suspends during computation |
| `services/gochara_v3/engine.py` | `_evaluate_single_from_context` | decorator |
| `services/gochara_v3/mechanisms/w30_nodal_drishti.py` | `compute` | decorator |
| `services/ka_kshetra/stage0_kinematics.py` | `_sidereal_offset_series` | decorator |
| `services/ka_kshetra/stage3_clocks.py` | `moon_velocity_dps_at_jd` | decorator |
| `services/ka_sangam/engine.py` | `_c_tara_bala_for_jd` | decorator |
| `services/w2g_validations/v3_spline_accuracy.py` | `_swe_longitude` | decorator |

## Transitive state-dependent boundaries

These 14 functions enclose multiple state-dependent helper calls or PyJHora
calculations and therefore hold one coherent boundary. The hardened detector
now also recognizes the four adapter-strength calculation owners directly.
They are all `SERIALIZED`:

- `panchang_engine/angas.py`: `compute_tithi`, `compute_yoga`,
  `compute_karana_pair`;
- `pipeline/orchestrator/writers/bg_muhurta_lattice.py`:
  `compute_day_factors`, `_ascendant_sign_id_at`, `compute_lagna_spans`;
- `pipeline/orchestrator/writers/bg_sky_calendar.py`: `scan_ingresses`,
  `scan_stations`, `scan_double_transits`; and
- `pyjhora_adapter/strength.py`: `compute_shadbala`, `compute_uchcha_bala`,
  `compute_vimsopaka`, `compute_ashtakavarga_shodhana`, `compute_strength`.

All other live callers reach one of the serialized owners above. They are
classified `SERIALIZED_AT_CALLEE`; no caller needs its own boundary merely to
perform state-independent preparation or result shaping.

## Other classifications

| Classification | Exact surface | Evidence |
|---|---|---|
| `PROCESS_ISOLATED_EXISTING` | `pyjhora_adapter/_isolation.py::per_ayanamsha` and `_worker` | unchanged existing five-process fan-out; not introduced, changed or relied on by DP-SD-010 |
| `NOT_STATE_DEPENDENT` | all direct `swe.julday` (68 occurrences), `swe.revjul` (12) and `swe.jdut1_to_utc` (3) calls in shipped source | calendar/JD conversion does not read sidereal mode or ephemeris path; excluded by detector method set |
| `NOT_STATE_DEPENDENT` | pure longitude normalization, sign/nakshatra mapping, interpolation, event ordering and result shaping | no Swiss/PyJHora state read; unchanged algorithms |
| `TEST_ONLY` | tests and injected negative fixtures | excluded from shipped-source inventory by path |
| `UNRESOLVED` | none | exact source-tree detector result: zero |

## Exact narrowed implementation manifest

The implementation touches only these amendment-authorized surfaces:

- canonical boundary and Panchang engine: `panchang_engine/swiss_state.py`,
  `panchang_engine/__init__.py`, `angas.py`, `ayanamsha.py`, `lagna.py`,
  `planets.py`, `rich_topics.py`, `timings.py`, `upagrahas.py`;
- L0/Gaṇita writers and adapters: `brahmagyan/l0_ephemeris.py`,
  `brahmagyan/ganita/{engine,graha_sthana_writer,l1_engine_check,l1_positions}.py`,
  `brahma/l1/ganita/divisionals_writer.py`,
  `ga_writers/{ga_dashas_writer,ga_sade_sati_writer,ga_strength_writer,
  ga_vargas_writer}.py`;
- pipeline: `pipeline/transit_search.py`,
  `pipeline/orchestrator/service_probes.py`, and writers
  `{bg_cohort,bg_muhurta_lattice,bg_sky_calendar,ka_vighnakara}.py`;
- PyJHora adapters: `{compute,dashas,houses,panchanga,positions,
  sensitive_points,special_lagnas,strength,vargas}.py`;
- routes/services: `routers/pyhora.py`, `services/gochara_v3/engine.py`,
  `services/gochara_v3/mechanisms/w30_nodal_drishti.py`,
  `services/ka_kshetra/{stage0_kinematics,stage3_clocks}.py`,
  `services/ka_sangam/engine.py`,
  `services/w2g_validations/v3_spline_accuracy.py`; and
- proof: `tests/test_swiss_state_boundary.py`.

No file outside the DP-SD-010 amendment plus DP-SD-011 addendum `may_touch`
union is affected. No process-manager, worker-count, deployment, schema,
identity, rights or output-semantic surface is changed.
