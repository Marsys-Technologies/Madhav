"""SR-GEOMETRY-PIN-ONCE (T20, with amend-1, amend-3 = SR-EPHE-PATH-ONCE-AMEND-1, amend-4): the geometry implementation digest is re-derived ONCE, recorded in the
EQUIVALENCE_RECORD changelog with every cause, and a further geometry change refuses.

DB-free. Every detector takes a path, so each planted reversion below is applied to a COPY of the real file and never to the repository.

Distinct production claims (one oracle each, one planted reversion each; doctrine = the cited ruling, CLAUDE.md §N.8 earned signal, B.10):
  P1  the golden's geometry literal, the changelog's `geometry_after` and the production `module_digests` of the real bytes are one value.
      Reversion: flip one hex character of the literal in a copy of test_mb_ordinary_golden.py.
  P2  a further geometry change refuses and NAMES the module (T20; amend-1 "any further geometry change refuses").
      Reversion: append a comment line to a copy of arcs.py.
  P3  every geometry module whose bytes differ from the I1 base is owned by an approved cause in the changelog; the changelog names all five causes (R2, DASH,
      NEARMISS, EPHE_ONCE = amend-3, F4_READ_CASTS = amend-4) and its 16 modules equal IMPLEMENTATION_MODULES['geometry'].
      Reversion: delete the DASH cause from a copy of the changelog.
  P4  the row-attribution verdict refuses an unattributed row, a doubly attributed row, a row owned by a cause that cannot reach its table, and a pin-consumer row that
      differs in a column that is not a digest/manifest column (N.8: a verdict computed by a detector that can read false).
      Reversion: make `unattributed` always empty in a copy of _geompin_attribution.py.
  P6  R2: the contact geometry keeps its 60 s floor and its named limit (SR-H2-1S scoped the 1 s floor to the P1 STATE providers).
      Reversion: `MIN_EXCURSION_SECONDS = 1` in a copy of contact_reconstruct.py.
  P7  SR-NEARMISS-BISECT: the near-miss verifier tolerance is still 600 s (only the builder bracket changed).
      Reversion: tol_seconds=600 -> 2 in a copy of near_miss_verifier.py.
  P8  SR-REASON-ONE-NAME did not enter a geometry module: record_store.py holds neither reason spelling as a literal and the one name is dasha_horizon_exhausted.
      Reversion: put the first spelling in as a literal in a copy of record_store.py.
  P9  SR-EPHE-PATH-ONCE-AMEND-1: the changelog carries the honest gap of the ephe-once byte-identity check (2 of 4 slice classes did not finish on the pre-fix side).
      Reversion: delete the `honest_gap` of the EPHE_ONCE cause in a copy of the changelog.
P5 (DASH blanks past the table end, T13), the R2 state-floor oracle, the band-edge oracles (P7 geometry) and the once-per-thread ephemeris-path oracle with its stale-memo
reversion are the lanes' own existing tests (test_a53_p1_support, test_od1_r2_state_boundaries, test_d1_near_miss_geometry, test_od1_ephe_path_once); the controlled
data attribution is job evidence whose detector is P4.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from services.gochara_kernel import dasha_read
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import input_vector_verifier as ivv

from . import _geompin_attribution as ga

HERE = Path(__file__).resolve().parent
SIDECAR = HERE.parents[2]
REPO = HERE.parents[4]
KERNEL_DIR = SIDECAR / "services" / "gochara_kernel"
GOLDEN = HERE / "test_mb_ordinary_golden.py"
CHANGELOG = REPO / "00_ARCHITECTURE" / "briefs" / "kalayantra" / "fleet" / "EQUIVALENCE_RECORD_CHANGELOG.json"
ENTRY_ID = "GEOM-PIN-ONCE"
CAUSES = {"R2", "DASH", "NEARMISS", "EPHE_ONCE", "F4_READ_CASTS"}
#: the one module two causes edit, each in its own disjoint hunk (ephe-once memo; f4-exact ::float8 read)
SHARED = {"near_miss_verifier": {"EPHE_ONCE", "F4_READ_CASTS"}}
#: the first spelling of the dasha-table-end reason; built from parts so this file never carries it (SR-REASON-ONE-NAME guard)
OLD_NAME = "dasha_table_ends" + "_before_support"
ONE_NAME = "dasha_horizon_exhausted"


def _entry(path: Path = CHANGELOG) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema"] == "ky.equivalence_changelog/1"
    (entry,) = [e for e in doc["entries"] if e["id"] == ENTRY_ID]
    return entry


def _geometry_tree_copy(tmp_path: Path) -> Path:
    """A root holding input_vector.py and the 16 geometry modules of the real tree (the layout `geometry_digests_of` reads)."""
    root = tmp_path / "tree"
    dest = root / "services" / "gochara_kernel"
    dest.mkdir(parents=True)
    shutil.copy2(KERNEL_DIR / "input_vector.py", dest / "input_vector.py")
    for name in ga.geometry_module_names(KERNEL_DIR / "input_vector.py"):
        shutil.copy2(KERNEL_DIR / (name.rsplit(".", 1)[1] + ".py"), dest / (name.rsplit(".", 1)[1] + ".py"))
    return root


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── P1 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _pin_values(golden: Path, entry_path: Path, tree_root: Path) -> dict:
    return {"golden literal": ga.golden_geometry_literal(golden), "changelog geometry_after": _entry(entry_path)["geometry_after"],
            "recipe over the real bytes": ga.geometry_digest_of(tree_root)}


def test_the_pin_the_golden_asserts_equals_the_production_digest_of_the_real_bytes(tmp_path):
    production = ivv.module_digests(iv.IMPLEMENTATION_MODULES)["geometry"]
    values = _pin_values(GOLDEN, CHANGELOG, SIDECAR)
    assert ga.geometry_digest_of(SIDECAR) == production, "the helper recipe drifted from the production module_digests"
    assert len(production) == 64
    for what, value in values.items():
        assert value == production, f"{what} != the production geometry digest of the real bytes"
    # the detector can read false: a flipped hex character in a copy of the golden is a different value
    flipped = GOLDEN.read_text(encoding="utf-8").replace(production, ("0" if production[0] != "0" else "1") + production[1:], 1)
    assert flipped != GOLDEN.read_text(encoding="utf-8")
    bad = tmp_path / "flipped_golden_copy.py"
    bad.write_text(flipped, encoding="utf-8")
    assert ga.golden_geometry_literal(bad) != production


# ── P2 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("module", ["arcs", "near_miss"])    # one no cause owns, one a cause owns: neither may change after the pin
def test_a_byte_added_to_a_geometry_module_refuses_naming_it(tmp_path, module):
    root = _geometry_tree_copy(tmp_path)
    entry = _entry()
    assert ga.refusals_for(root, entry) == [], "the untouched copy of the real tree must not refuse"
    target = root / "services" / "gochara_kernel" / f"{module}.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# a further geometry change\n", encoding="utf-8")
    refusals = ga.refusals_for(root, entry)
    assert len(refusals) == 1 and refusals[0].startswith("REFUSE: geometry module " + module + " "), refusals


# ── P3 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_every_changed_module_has_exactly_one_cause_and_the_changelog_names_all_causes(tmp_path):
    assert ga.ownership_problems(_entry(), [n.removeprefix(ga.KERNEL) for n in iv.IMPLEMENTATION_MODULES["geometry"]], CAUSES, SHARED) == []
    broken = copy.deepcopy(_entry())
    broken["causes"] = [c for c in broken["causes"] if c["id"] != "DASH"]
    problems = ga.ownership_problems(broken, [n.removeprefix(ga.KERNEL) for n in iv.IMPLEMENTATION_MODULES["geometry"]], CAUSES, SHARED)
    assert any("DASH" in p for p in problems) and any("record_store" in p for p in problems), problems


# ── P4 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

ALLOWED = {"snapshot": {"input_digest"}, "inventory": {"input_digest", "ledger_digest"}}
REACH = {"R2": {"records", "windows"}, "NEARMISS": {"near_miss"}, "DASH": {"records"}, "EPHE_ONCE": set(), "F4_READ_CASTS": set()}


def _verdict(rows, sets):
    return ga.attribute(rows, {c: sets.get(c, set()) for c in REACH}, ALLOWED, REACH)


def test_attribution_refuses_unattributed_double_and_non_digest_consumer_rows():
    nm = {("near_miss", ("n1", 0)), ("near_miss", ("n2", 0))}
    rows = [("near_miss", ("n1", 0), {"t_in"}), ("near_miss", ("n2", 0), {"t_out"}), ("snapshot", ("g",), {"input_digest"})]
    ok = _verdict(rows, {"NEARMISS": nm})
    assert ok["status"] == "ATTRIBUTED" and ok["pin_consumers"] == {"snapshot": 1} and len(ok["attributed"]["NEARMISS"]) == 2
    # a row nobody owns
    lost = _verdict(rows + [("records", ("r9",), {"severity"})], {"NEARMISS": nm})
    assert lost["status"] == "REFUSED" and [r[:2] for r in lost["unattributed"]] == [("records", ("r9",))]
    # a row two causes own
    both = _verdict(rows + [("records", ("r1",), {"severity"})], {"NEARMISS": nm, "R2": {("records", ("r1",))}, "DASH": {("records", ("r1",))}})
    assert both["status"] == "REFUSED" and both["double"] == [("records", ("r1",), ["R2", "DASH"])]
    # a cause that moved a table its code path cannot reach (the near-miss builder writing a record)
    reach = _verdict(rows + [("records", ("r2",), {"severity"})], {"NEARMISS": nm | {("records", ("r2",))}})
    assert reach["status"] == "REFUSED" and reach["out_of_reach"] == [("NEARMISS", "records", ("r2",))]
    # a consumer-table row that differs in a NON-digest column is a geometry row and needs a cause; an added/removed consumer row likewise
    sneaky = _verdict([("snapshot", ("g",), {"input_digest", "horizon"})], {})
    assert sneaky["status"] == "REFUSED" and sneaky["pin_consumers"] == {} and len(sneaky["unattributed"]) == 1
    removed = _verdict([("inventory", ("c",), {"*"})], {})
    assert removed["status"] == "REFUSED" and removed["pin_consumers"] == {}


# ── P6 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _contact_geometry_floor(path: Path) -> dict:
    cr = _load(path, "_geompin_contact_reconstruct_" + path.parent.name)
    import inspect
    return {"floor": cr.MIN_EXCURSION_SECONDS, "core_default": inspect.signature(cr._core).parameters["min_excursion_seconds"].default,
            "named_limit_says_60": "at least 60 s" in cr.NAMED_LIMIT and "shorter than 60 s" in cr.NAMED_LIMIT, "state_floor": cr.STATE_MIN_EXCURSION_SECONDS}


def test_contact_geometry_keeps_its_sixty_second_floor():
    got = _contact_geometry_floor(KERNEL_DIR / "contact_reconstruct.py")
    assert got["floor"] == 60 and got["core_default"] == 60, got
    assert got["named_limit_says_60"], got
    assert got["state_floor"] == 1.0, "the P1 STATE floor is the bisection resolution (SR-H2-1S)"


# ── P7 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _verifier_tolerance(path: Path) -> list[int]:
    """The `tol_seconds` constants passed to compare_sets inside verify_generation (AST)."""
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "verify_generation")
    return [kw.value.value for c in ast.walk(fn) if isinstance(c, ast.Call) and getattr(c.func, "id", None) == "compare_sets"
            for kw in c.keywords if kw.arg == "tol_seconds" and isinstance(kw.value, ast.Constant)]


def test_near_miss_verifier_tolerance_is_still_600_seconds():
    assert _verifier_tolerance(KERNEL_DIR / "near_miss_verifier.py") == [600]


# ── P8 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_reason_rename_is_outside_geometry():
    assert dasha_read.PERIOD_TABLE_ENDS_REASON == ONE_NAME
    assert ga.reason_literals(KERNEL_DIR / "record_store.py", (OLD_NAME, ONE_NAME)) == [], "record_store must import the reason by name, never spell it"
    assert "PERIOD_TABLE_ENDS_REASON" in (KERNEL_DIR / "record_store.py").read_text(encoding="utf-8")


def test_a_reason_literal_planted_in_a_geometry_module_is_seen(tmp_path):
    copy_ = tmp_path / "record_store.py"
    copy_.write_text((KERNEL_DIR / "record_store.py").read_text(encoding="utf-8") + f'\n_PLANTED = "{OLD_NAME}"\n', encoding="utf-8")
    assert ga.reason_literals(copy_, (OLD_NAME, ONE_NAME)) == [OLD_NAME]


# ── P9 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_ephe_once_honest_gap_is_recorded():
    (cause,) = [c for c in _entry()["causes"] if c["id"] == "EPHE_ONCE"]
    gap = cause.get("honest_gap", "")
    assert "2 of the 4 slice classes did not finish on the pre-fix side" in gap and "105,012" in gap


def test_the_entry_is_closed_and_chained_to_the_i1_base_pin():
    entry = _entry()
    assert entry["closed"] is True and entry["further_geometry_change"] == "REFUSE"
    assert entry["geometry_before"].startswith("a8cb08f0") and len(entry["geometry_before"]) == 64
    assert entry["geometry_after"] != entry["geometry_before"]
