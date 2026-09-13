"""DP-SD-010 process-wide Swiss Ephemeris state-boundary proof."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from time import sleep

import pytest

from panchang_engine import SWISS_STATE_LOCK as EXPORTED_LOCK
from panchang_engine.swiss_state import (
    SWISS_STATE_LOCK,
    serialized_swiss_state,
    swiss_state_scope,
)
from pipeline import transit_search


SIDEREAL_MODE_LAHIRI = 101
SIDEREAL_MODE_RAMAN = 202

SWE_STATE_METHODS = {
    "set_sid_mode",
    "set_ephe_path",
    "set_topo",
    "set_jpl_file",
    "get_ayanamsa_ut",
    "calc_ut",
    "houses",
    "houses_ex",
    "rise_trans",
    "rise_trans_true_hor",
    "pheno_ut",
    "nod_aps_ut",
    "fixstar_ut",
    "sol_eclipse_when_glob",
    "lun_eclipse_when",
    "lun_occult_when_glob",
}

PYJHORA_STATE_METHODS = {
    "set_ayanamsa_mode",
    "get_ayanamsa_value",
    "sidereal_longitude",
    "ascendant",
    "bhaava_madhya_swe",
    "bhaava_madhya_sripathi",
    "dhasavarga",
    "planets_in_retrograde",
    "nakshatra",
    "tithi",
    "yogam",
    "karana",
    "upagraha_longitude",
    "bhava_lagna",
    "hora_lagna",
    "ghati_lagna",
    "vighati_lagna",
    "indu_lagna",
    "sree_lagna",
    "pranapada_lagna",
    "bhrigu_bindhu_lagna",
    "kunda_lagna",
}

EXPECTED_OPERATION_OWNERS = {
    ("brahma/l1/ganita/divisionals_writer.py", "compute_vargas_for_native"),
    ("brahmagyan/ganita/engine.py", "compute_positions"),
    ("brahmagyan/ganita/graha_sthana_writer.py", "_compute_graha_sthana"),
    ("brahmagyan/ganita/l1_engine_check.py", "run_engine_smoke"),
    ("brahmagyan/ganita/l1_positions.py", "compute_positions_all_bodies"),
    ("brahmagyan/l0_ephemeris.py", "_compute_positions_for_date"),
    ("brahmagyan/l0_ephemeris.py", "build_ephemeris"),
    ("brahmagyan/l0_ephemeris.py", "derive_sidereal"),
    ("brahmagyan/l0_ephemeris.py", "query_ayanamsha_delta"),
    ("ga_writers/ga_dashas_writer.py", "_get_moon_position"),
    ("ga_writers/ga_dashas_writer.py", "_mudda_solar_return_jd"),
    ("ga_writers/ga_dashas_writer.py", "build_system"),
    ("ga_writers/ga_dashas_writer.py", "compute_mudda_system"),
    ("ga_writers/ga_sade_sati_writer.py", "_detect_saturn_retrogrades"),
    ("ga_writers/ga_sade_sati_writer.py", "_detect_saturn_sign_changes"),
    ("ga_writers/ga_sade_sati_writer.py", "_lookup_tara_bala_for_saturn_at"),
    ("ga_writers/ga_vargas_writer.py", "_compute_varga_positions"),
    ("panchang_engine/__init__.py", "compute_panchang"),
    ("panchang_engine/__init__.py", "panchanga_instant"),
    ("panchang_engine/angas.py", "_get_sun_moon_lon"),
    ("panchang_engine/angas.py", "compute_nakshatra"),
    ("panchang_engine/ayanamsha.py", "get_ayanamsha_value"),
    ("panchang_engine/ayanamsha.py", "set_ayanamsha"),
    ("panchang_engine/lagna.py", "_get_ayanamsha"),
    ("panchang_engine/lagna.py", "compute_lagna"),
    ("panchang_engine/planets.py", "compute_all_grahas"),
    ("panchang_engine/planets.py", "compute_planet_state"),
    ("panchang_engine/rich_topics.py", "compute_sun_moon_dynamics"),
    ("panchang_engine/timings.py", "compute_day_events"),
    ("panchang_engine/timings.py", "compute_moonrise_moonset"),
    ("panchang_engine/timings.py", "compute_sunrise_sunset"),
    ("panchang_engine/upagrahas.py", "_ayanamsha"),
    ("panchang_engine/upagrahas.py", "compute_outer_planets"),
    ("panchang_engine/upagrahas.py", "compute_upagrahas"),
    ("pipeline/orchestrator/service_probes.py", "_probe_ephemeris_engine"),
    (
        "pipeline/orchestrator/writers/bg_cohort.py",
        "_require_pinned_ephemeris_runtime",
    ),
    ("pipeline/orchestrator/writers/bg_cohort.py", "compute_synthetic_positions"),
    (
        "pipeline/orchestrator/writers/bg_sky_calendar.py",
        "_require_swiss_file_backend",
    ),
    ("pipeline/orchestrator/writers/bg_sky_calendar.py", "_scan_lunar_eclipses"),
    ("pipeline/orchestrator/writers/bg_sky_calendar.py", "_scan_solar_eclipses"),
    ("pipeline/orchestrator/writers/bg_sky_calendar.py", "scan_eclipses"),
    ("pipeline/orchestrator/writers/ka_vighnakara.py", "_get_sidereal_lon"),
    ("pipeline/transit_search.py", "_get_planet_pos"),
    ("pyjhora_adapter/compute.py", "compute_chart"),
    ("pyjhora_adapter/dashas.py", "compute_dashas"),
    ("pyjhora_adapter/houses.py", "compute_ascendant"),
    ("pyjhora_adapter/houses.py", "compute_bhava_chalit"),
    ("pyjhora_adapter/houses.py", "compute_midheaven"),
    ("pyjhora_adapter/panchanga.py", "compute_panchanga"),
    ("pyjhora_adapter/positions.py", "_set_ayanamsha"),
    ("pyjhora_adapter/positions.py", "compute_positions"),
    ("pyjhora_adapter/sensitive_points.py", "compute_sensitive_points"),
    ("pyjhora_adapter/special_lagnas.py", "compute_special_lagnas"),
    ("pyjhora_adapter/strength.py", "_set_ayanamsha"),
    ("pyjhora_adapter/vargas.py", "compute_vargas"),
    ("routers/ephemeris.py", "_calculate_sidereal_positions"),
    ("routers/pyhora.py", "compute_natal"),
    ("routers/pyhora.py", "smoke_test"),
    ("services/gochara_v3/engine.py", "_evaluate_single_from_context"),
    ("services/gochara_v3/mechanisms/w30_nodal_drishti.py", "compute"),
    ("services/ka_kshetra/stage0_kinematics.py", "_sidereal_offset_series"),
    ("services/ka_kshetra/stage3_clocks.py", "moon_velocity_dps_at_jd"),
    ("services/ka_sangam/engine.py", "_c_tara_bala_for_jd"),
    ("services/w2g_validations/v3_spline_accuracy.py", "_swe_longitude"),
}


def _receiver_label(node: ast.AST) -> str:
    return ast.unparse(node)


def _decorator_is_boundary(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        (isinstance(d, ast.Name) and d.id == "serialized_swiss_state")
        or (isinstance(d, ast.Attribute) and d.attr == "serialized_swiss_state")
        for d in node.decorator_list
    )


def _context_is_boundary(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Name)
        and node.id == "SWISS_STATE_LOCK"
    ) or (
        isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Name, ast.Attribute))
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "swiss_state_scope")
            or (isinstance(node.func, ast.Attribute) and node.func.attr == "swiss_state_scope")
        )
    )


def _scan_module(source: str, relative_path: str):
    tree = ast.parse(source)
    swiss_module_aliases = {"swe", "_swe", "swisseph"}
    swiss_callable_aliases: set[str] = set()
    pyjhora_module_aliases = {"drik", "_drik", "jh_drik"}
    pyjhora_callable_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name == "swisseph":
                    swiss_module_aliases.add(imported.asname or imported.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for imported in node.names:
                local_name = imported.asname or imported.name
                if module == "swisseph" and imported.name in SWE_STATE_METHODS:
                    swiss_callable_aliases.add(local_name)
                if "jhora" in module and imported.name == "drik":
                    pyjhora_module_aliases.add(local_name)
                if module.endswith("drik") and imported.name in PYJHORA_STATE_METHODS:
                    pyjhora_callable_aliases.add(local_name)

    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    owners: set[tuple[str, str]] = set()
    unresolved: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            receiver = _receiver_label(node.func.value)
            terminal = receiver.split(".")[-1]
            direct_swiss = method in SWE_STATE_METHODS and terminal in swiss_module_aliases
            pyjhora_wrapper = (
                method in PYJHORA_STATE_METHODS
                and terminal in pyjhora_module_aliases
            )
            operation = f"{receiver}.{method}"
        elif isinstance(node.func, ast.Name):
            direct_swiss = node.func.id in swiss_callable_aliases
            pyjhora_wrapper = node.func.id in pyjhora_callable_aliases
            operation = node.func.id
        else:
            continue
        if not direct_swiss and not pyjhora_wrapper:
            continue

        cursor: ast.AST = node
        function_stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        protected_owner: str | None = None
        inside_canonical_scope = False
        while cursor in parents:
            cursor = parents[cursor]
            if isinstance(cursor, ast.With):
                inside_canonical_scope = inside_canonical_scope or any(
                    _context_is_boundary(item.context_expr)
                    for item in cursor.items
                )
            if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_stack.append(cursor)
                if _decorator_is_boundary(cursor):
                    protected_owner = cursor.name
                    break

        nearest_name = function_stack[0].name if function_stack else "<module>"
        if inside_canonical_scope:
            protected_owner = nearest_name
        if relative_path == "pipeline/transit_search.py" and nearest_name == "_calc_ut_cached":
            # Private cached primitive has one call site: serialized
            # `_get_planet_pos`, which supplies mode/path cache dimensions.
            protected_owner = "_get_planet_pos"

        if protected_owner is None:
            unresolved.append((relative_path, node.lineno, operation))
        else:
            owners.add((relative_path, protected_owner))
    return owners, unresolved


def _scan_source_tree():
    source_root = Path(__file__).resolve().parents[1]
    owners: set[tuple[str, str]] = set()
    unresolved: list[tuple[str, int, str]] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root)
        if "tests" in relative.parts or path.name.startswith("test_"):
            continue
        found, missing = _scan_module(path.read_text(encoding="utf-8"), relative.as_posix())
        owners.update(found)
        unresolved.extend(missing)
    return owners, unresolved


def test_generated_inventory_is_exact_and_has_no_unresolved_live_owner():
    owners, unresolved = _scan_source_tree()
    assert unresolved == []
    assert owners == EXPECTED_OPERATION_OWNERS


@pytest.mark.parametrize(
    "source",
    [
        "def unsafe(swe):\n    swe.set_sid_mode(1)\n    return swe.calc_ut(1, 0, 0)\n",
        (
            "import swisseph as ephemeris\n"
            "def unsafe():\n"
            "    ephemeris.set_sid_mode(1)\n"
            "    return ephemeris.calc_ut(1, 0, 0)\n"
        ),
        (
            "from swisseph import set_sid_mode as select_mode, calc_ut as calculate\n"
            "def unsafe():\n"
            "    select_mode(1)\n"
            "    return calculate(1, 0, 0)\n"
        ),
        (
            "from jhora.panchanga import drik\n"
            "def unsafe():\n"
            "    drik.set_ayanamsa_mode('RAMAN')\n"
            "    return drik.sidereal_longitude(1, 0)\n"
        ),
    ],
)
def test_inventory_detector_rejects_injected_direct_and_wrapper_gaps(source):
    _owners, unresolved = _scan_module(source, "injected.py")
    assert unresolved


def test_deliberately_separate_lock_is_not_accepted_as_canonical_scope():
    source = (
        "from threading import RLock\n"
        "OTHER_LOCK = RLock()\n"
        "def unsafe(swe):\n"
        "    with OTHER_LOCK:\n"
        "        swe.set_sid_mode(1)\n"
        "        return swe.calc_ut(1, 0, 0)\n"
    )
    _owners, unresolved = _scan_module(source, "injected_separate_lock.py")
    assert unresolved

    misleading_name = source.replace("OTHER_LOCK", "OTHER_SWISS_STATE_LOCK")
    _owners, unresolved = _scan_module(misleading_name, "injected_named_lock.py")
    assert unresolved


def test_only_one_shipped_rlock_definition_and_compatibility_export():
    source_root = Path(__file__).resolve().parents[1]
    definitions = []
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root)
        if "tests" in relative.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "RLock()" in text:
            definitions.append(relative.as_posix())
    assert definitions == ["panchang_engine/swiss_state.py"]
    assert EXPORTED_LOCK is SWISS_STATE_LOCK
    assert transit_search._get_planet_pos.__swiss_state_lock__ is SWISS_STATE_LOCK


class _BlockingSwiss:
    SUN = 0
    SIDM_LAHIRI = SIDEREAL_MODE_LAHIRI
    FLG_SIDEREAL = 1
    FLG_SPEED = 2

    def __init__(self):
        self.mode = None
        self.path = None
        self.block_mode = None
        self.entered = Event()
        self.release = Event()
        self.calls: list[tuple[int | None, str | None]] = []

    def set_sid_mode(self, mode):
        self.mode = mode

    def set_ephe_path(self, path):
        self.path = path

    def calc_ut(self, _jd, _planet_id, _flags):
        selected = (self.mode, self.path)
        self.calls.append(selected)
        if self.mode == self.block_mode and not self.entered.is_set():
            self.entered.set()
            assert self.release.wait(timeout=2)
            assert (self.mode, self.path) == selected
        return ([float(self.mode or 0), 0.0, 0.0, -0.1], 0)


def _raman_operation(fake: _BlockingSwiss):
    with swiss_state_scope():
        fake.set_ephe_path("raman-path")
        fake.set_sid_mode(SIDEREAL_MODE_RAMAN)
        return fake.calc_ut(1.0, fake.SUN, fake.FLG_SIDEREAL)


@pytest.mark.parametrize("first", ["lahiri", "raman"])
def test_barrier_controlled_mode_and_path_interleave_is_serialized(first):
    fake = _BlockingSwiss()
    transit_search.clear_ephemeris_cache()
    fake.block_mode = SIDEREAL_MODE_LAHIRI if first == "lahiri" else SIDEREAL_MODE_RAMAN

    if first == "lahiri":
        first_fn = lambda: transit_search._get_planet_pos(fake, "Sun", 2451545.0)
        second_fn = lambda: _raman_operation(fake)
    else:
        first_fn = lambda: _raman_operation(fake)
        second_fn = lambda: transit_search._get_planet_pos(fake, "Sun", 2451545.0)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(first_fn)
        assert fake.entered.wait(timeout=1)
        second_future = pool.submit(second_fn)
        sleep(0.05)
        assert len(fake.calls) == 1, "conflicting calculation entered the critical section"
        fake.release.set()
        first_future.result(timeout=2)
        second_future.result(timeout=2)

    assert [mode for mode, _path in fake.calls] == (
        [SIDEREAL_MODE_LAHIRI, SIDEREAL_MODE_RAMAN]
        if first == "lahiri"
        else [SIDEREAL_MODE_RAMAN, SIDEREAL_MODE_LAHIRI]
    )


def test_reentrant_nested_entry_points_complete_without_deadlock():
    @serialized_swiss_state
    def inner():
        return "deterministic"

    @serialized_swiss_state
    def outer():
        return inner()

    with ThreadPoolExecutor(max_workers=1) as pool:
        assert pool.submit(outer).result(timeout=1) == "deterministic"


class _ContextSwiss:
    def __init__(self):
        self.mode = None
        self.path = None
        self.calls = 0

    def calc_ut(self, _jd, _planet_id, _flags):
        self.calls += 1
        value = float(self.mode or 0) + (10.0 if self.path == "path-a" else 20.0)
        return ([value, 0.0, 0.0, -0.1], 0)


def test_cache_key_carries_mode_and_ephemeris_path_context():
    fake = _ContextSwiss()
    transit_search.clear_ephemeris_cache()

    with swiss_state_scope():
        fake.mode, fake.path = SIDEREAL_MODE_LAHIRI, "path-a"
        first = transit_search._calc_ut_cached(fake, 1.0, 0, 3, fake.mode, fake.path)
        again = transit_search._calc_ut_cached(fake, 1.0, 0, 3, fake.mode, fake.path)
        fake.mode, fake.path = SIDEREAL_MODE_RAMAN, "path-b"
        second = transit_search._calc_ut_cached(fake, 1.0, 0, 3, fake.mode, fake.path)

    assert first == again
    assert first != second
    assert fake.calls == 2
