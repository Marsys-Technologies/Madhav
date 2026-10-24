"""EQUIVALENCE_RECORD/1 oracles (PLAN_A10_1 §3.6; D-OWNER-TESTS-20261016): one oracle per distinct production claim, the claim and its source in
each docstring. Every fixture is synthetic (a miniature sidecar tree, invented digests): no personal datum, no database, no network.

EQ-1  a change to any result-bearing module moves E1, the solver and the checker included; a required module in no list refuses   (G-8; N.5/N.8)
EQ-2  a change to selection, a ruling, the convention/node model or either orb policy moves E2                                     (G-8; AM-13)
EQ-3  a change to one L0 row, one copied L1 fact or one dasha row moves E3a, by CONTENT and not by row id                          (SR-1401-VERIFIED)
EQ-4  a change to a Swiss file, the library, the probe, the architecture or the lock moves E4                                      (`ephemeris_identity`)
EQ-5  a change to a budget, a tolerance constant, the horizon, the policy or the class universe moves E5
EQ-6  a label-only change (commit, tree, image, run id) keeps the decision EQUAL and is stored in E6
EQ-7  the projection excludes only the named trial-scope fields; a trial scope in a century config refuses
EQ-8  the decision never rewrites provenance or a record
EQ-9  the record is canonical, indexes retained manifests, its digest follows the five category digests, and a tampered record refuses
EQ-10 the pinned input vector must be the one of the commit (implementation stage digests recomputed from the commit's bytes)
EQ-11 an unreadable source makes the category NULL and the decision never EQUAL (N.7.6), even null-against-null
EQ-12 only a qualifying amd64 run or the dispatch image has an E4 (P3/P6)
EQ-13 E3b is checked for COVERAGE of every trial E3a row, by content (P2)
EQ-14 the minimum action per difference is the §3.5 table, as data
EQ-15 the import-closure port equals the repository's own detector at HEAD, and the CLI writes/compares end to end
EQ-16 (SR-T24-AMD64-DOCKER) an emulated linux/amd64 container run: the arch is READ inside the container (an arch asserted from outside is refused), the emulation is
      recorded in provenance.platform_notes (a missing note is refused), and the note lives in E6 so it never makes a record DIFFER from the dispatch image's
"""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET = Path(os.environ.get("EQR_UNDER_TEST_DIR") or Path(__file__).resolve().parents[1])
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(FLEET))
import equivalence_record as eqr  # noqa: E402

SC = "platform/python-sidecar"
K = SC + "/services/gochara_kernel/"
TS = "2026-01-01T00:00:00Z"
LISTS = {
    "geometry": ["services.gochara_kernel.arcs", "services.gochara_kernel.ids", "services.gochara_kernel.convention",
                 "services.gochara_kernel.record_store"],
    "evaluation": ["services.gochara_kernel.evaluator", "services.gochara_kernel.dasha_read", "services.gochara_kernel.chart_context",
                   "pipeline.orchestrator.writers.ka_gochara_v5", "services.gochara_rules.score"],
    "window": ["services.gochara_kernel.result_policy", "services.gochara_kernel.window_sweep", "services.gochara_kernel.window_solver",
               "services.gochara_kernel.window_solver_check"],
}
CLASSES = [f"class_{i:02d}" for i in range(26)]
TRIAL_CLASSES = CLASSES[:12]


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def put(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def make_world(root):
    for pkg in ("services", "services/gochara_kernel", "services/gochara_rules", "pipeline", "pipeline/orchestrator", "pipeline/orchestrator/writers"):
        put(root, f"{SC}/{pkg}/__init__.py", "")
    put(root, K + "input_vector.py",
        '_K, _R = "services.gochara_kernel.", "services.gochara_rules."\nIMPLEMENTATION_MODULES = {\n'
        '    "geometry": tuple(_K + m for m in ("arcs", "ids", "convention", "record_store")),\n'
        '    "evaluation": tuple(_K + m for m in ("evaluator", "dasha_read", "chart_context")) + '
        '("pipeline.orchestrator.writers.ka_gochara_v5",) + tuple(_R + m for m in ("score",)),\n'
        '    "window": tuple(_K + m for m in ("result_policy", "window_sweep", "window_solver", "window_solver_check")),\n}\n')
    put(root, K + "arcs.py", "ARC = 1\n")
    put(root, K + "ids.py", "ID = 1\n")
    put(root, K + "convention.py", 'ORB_TABLE = {"conjunction": {"orb": 8.0}, "aspect": {"orb": 6.0}}\n')
    put(root, K + "record_store.py",
        'POINT_ORB_SOURCE = {"conjunction": "orb_conj_slow"}\n'
        'KALA_CONVENTION_VECTOR = {"zodiac": "sidereal", "node_model": "mean", "epoch_convention": "noon_ut_knot_abscissa"}\n')
    put(root, K + "evaluator.py", "from . import ids\nEVAL = 1\n")
    put(root, K + "dasha_read.py", "DASHA = 1\n")
    put(root, K + "dasha_settlement.json", '{"settled": []}\n')
    put(root, K + "chart_context.py", "CTX = 1\n")
    put(root, K + "result_policy.py",
        'POLICY_QUALIFICATION = "window_qualification/1"\nRESULT_POLICIES = ("all_null_candidate/1", POLICY_QUALIFICATION)\n'
        'QUALIFICATION_TABLE = {"policy": POLICY_QUALIFICATION, "rules": [{"n": 1, "then": f"unqualified under {POLICY_QUALIFICATION}"}]}\n')
    put(root, K + "window_sweep.py", "from . import arcs\nBISECT_SECONDS = 1.0\nMIN_EXCURSION_SECONDS = 60\n")
    put(root, K + "window_solver.py", "MAX_EVALS = 40_000\n")
    put(root, K + "window_solver_check.py", "TIE = 1e-9\nGREY = 2e-10\nLEAF_S = 0.5\nF4_ABS_SLACK = 1e-7\nISOLATION_S = 30\n")
    put(root, SC + "/services/gochara_rules/score.py", "SCORE = 1\n")
    put(root, SC + "/pipeline/orchestrator/writers/ka_gochara_v5.py",
        "from services.gochara_kernel import arcs, evaluator, window_sweep\nfrom services.gochara_rules import score\n")
    put(root, SC + "/requirements.txt", "pyswisseph==2.10.3.2\n")
    put(root, "platform/migrations/1240_gate.sql",
        "CREATE OR REPLACE FUNCTION public.ka_gochara_window_qualification_ok(q jsonb)\nRETURNS boolean LANGUAGE sql AS $$\n"
        "  SELECT q IS NULL OR jsonb_typeof(q) = 'object';\n$$;\nALTER TABLE t ADD COLUMN c int;\n")
    put(root, "platform/migrations/1300_other.sql", "SELECT 1;\n")


def edit(root, rel, old, new):
    p = Path(root) / rel
    s = p.read_text(encoding="utf-8")
    assert old in s, (rel, old)
    p.write_text(s.replace(old, new), encoding="utf-8")


def stage_digests(root):
    """The vector's `implementation` rule, restated here independently of the tool (input_vector._module_source_digest)."""
    out = {}
    for stage, names in LISTS.items():
        d = {}
        for m in names:
            p = Path(root) / SC / (m.replace(".", "/") + ".py")
            src = p.read_text(encoding="utf-8")
            if m == "services.gochara_kernel.dasha_read":
                src += "\0" + (p.with_name("dasha_settlement.json")).read_text(encoding="utf-8")
            d[m] = hashlib.sha256(src.encode()).hexdigest()
        out[stage] = hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    return out


E3A = {
    "l0_rows": {"bg_transit_rules": {"rahu_taurus": {"rung": "EX"}, "rahu_gemini": {"rung": "MT"}}},
    "l1_facts": {"fact_1": {"content": {"sign": "A"}, "provenance": "ga_x"}, "fact_2": {"content": {"sign": "B"}, "provenance": "ga_y"}},
    "dasha": {"population": {"d1": {"lord": "Ju", "end": "2030-01-01"}, "d2": {"lord": "Sa", "end": "2049-01-01"}}, "held_state": {"held": "d2"}},
    "av_declarations": {"av_1": {"declared": True}},
}


def e3_keys(e3a):
    keys = {}
    for a, rows in e3a["l0_rows"].items():
        keys.update({f"l0:{a}:{i}": v for i, v in rows.items()})
    keys.update({f"l1:{i}": v for i, v in e3a["l1_facts"].items()})
    keys.update({f"dasha:population:{i}": v for i, v in e3a["dasha"]["population"].items()})
    keys["dasha:held_state"] = e3a["dasha"]["held_state"]
    keys.update({f"av:{i}": v for i, v in e3a["av_declarations"].items()})
    return keys


def base_pinned(root):
    pop = e3_keys(E3A)
    pop.update({"l1:fact_extra": {"content": {"sign": "C"}, "provenance": "ga_z"}, "dasha:population:d3": {"lord": "Me"}})
    return {
        "schema": eqr.PINNED_SCHEMA,
        "input_vector": {
            "schema": eqr.VECTOR_SCHEMA, "stored_scope": "trial_slice", "result_policy": "window_qualification/1",
            "sky_convention": {"id": "sky/1", "content_digest": h("sky")}, "registry": {"digest": h("registry"), "census": [["P1", "1.3.0"]]},
            "node": {"model": "mean", "source": "swiss", "zodiac": "sidereal", "ayanamsha": "lahiri"},
            "ephemeris": {"backend": "swieph", "swe_version": "2.10.03", "library_sha256": h("lib"), "platform": "Linux-x86_64",
                          "files": {"sepl_18.se1": h("f1"), "semo_18.se1": h("f2")}, "probe_digest": h("probe")},
            "l0": {"bg_transit_rules": h("l0")}, "orb_policy": {"admission_digest": h("adm"), "activity": {"1.3.0": {"orb_deg": "1.0"}}},
            "rulings_digest": h("rulings"), "implementation": stage_digests(root),
            "scored_classes": TRIAL_CLASSES, "test_slice": {"classes": 4}, "horizon_basis": {"kind": "configured"},
            "near_miss_layer_version": 1, "qualification_table": h("qt"),
        },
        "rules": {"selection": {"selected_rule_version": "1.3.0", "profile": "final"},
                  "declared_accuracy": {"peak_instant_seconds": "1", "q13": "declared"}},
        "inputs": {"e3a": E3A, "e3b_population": pop},
        "century_config": {
            "stored_scope": "stored_non_moon", "horizon": {"start": "1998-01-01T00:00:00+00:00", "end": "2050-01-01T00:00:00+00:00"},
            "horizon_basis": "configured", "final_rules": "true", "result_policy": "window_qualification/1", "in_build_verify": "deferred",
            "budgets": {"per_window": "40000", "verifier": "600"}, "classes": CLASSES,
            "verification_plan": {"mode": "one_execution", "shard_plan_digest": None, "g6_sampling_rule": "3pct+top5", "seed_rule": "generation_id"},
        },
        "runtime": {"kind": "qualifying_run", "arch": "linux/amd64", "python": "3.13.7", "dependency_lock_digest": h("lock")},
        "trial_scope": {"horizon": {"start": "2020-01-01", "end": "2021-01-01"}},
        "provenance": {"branch": "kalayantra/od1-integration", "image_tag": "trial-1", "image_digest": "sha256:" + h("img-a"),
                       "ci_run_ids": ["1"], "dispatch_run_id": None, "manifest_ids": ["m1"], "overlay_hashes": {"o": h("ov")}},
    }


class Case:
    """A tree + its pinned inputs; `.record(dir)` writes the record and loads it back (as the comparison sees it)."""

    def __init__(self, tmp_path, name, src=None, mutate=None, tree_edits=()):
        self.root = tmp_path / name
        if src is None:
            make_world(self.root)
        else:
            import shutil
            shutil.copytree(src.root, self.root)
        for rel, old, new in tree_edits:
            edit(self.root, rel, old, new)
        self.pinned = base_pinned(self.root) if src is None or tree_edits else copy.deepcopy(src.pinned)
        if tree_edits:
            self.pinned = copy.deepcopy(src.pinned) if src else self.pinned
            self.pinned["input_vector"]["implementation"] = stage_digests(self.root)
        if mutate:
            mutate(self.pinned)
        self.path = tmp_path / f"{name}.record.json"

    def build(self, generated_at=TS):
        return eqr.build_record(eqr.DirTree(self.root), self.pinned, generated_at)

    def loaded(self):
        rec, mans = self.build()
        eqr.write_record(rec, mans, self.path)
        return eqr.load_record(self.path)


@pytest.fixture
def base(tmp_path):
    return Case(tmp_path, "base")


def variant(tmp_path, base, name, mutate=None, tree_edits=()):
    return Case(tmp_path, name, src=base, mutate=mutate, tree_edits=tree_edits)


def digest(case, cat):
    return case.build()[0]["categories"][cat]["digest"]


def decide(a, b):
    return eqr.decide(a.loaded(), b.loaded(), eqr.load_table())


def only_differs(tmp_path, base, cat, **kw):
    v = variant(tmp_path, base, "v", **kw)
    a, b = base.build()[0], v.build()[0]
    return [c for c in eqr.CATEGORIES if a["categories"][c]["digest"] != b["categories"][c]["digest"]]


# ── EQ-1 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rel", ["window_solver_check.py", "window_solver.py", "evaluator.py", "window_sweep.py", "arcs.py"])
def test_eq1_a_one_byte_change_to_a_result_bearing_module_moves_E1_including_the_solver_and_checker(tmp_path, base, rel):
    """G-8; root N.5/N.8: editing any listed module (the solver and the checker included) changes the E1 digest."""
    old = {"window_solver_check.py": "TIE = 1e-9", "window_solver.py": "40_000", "evaluator.py": "EVAL = 1", "window_sweep.py": "BISECT_SECONDS = 1.0",
           "arcs.py": "ARC = 1"}[rel]
    new = old[:-1] + ("8" if old[-1] != "8" else "7")
    v = variant(tmp_path, base, "v", tree_edits=[(K + rel, old, new)])
    assert digest(v, "E1") != digest(base, "E1")


def test_eq1_a_required_module_in_no_list_refuses(tmp_path, base):
    """T19: window_solver_check exists in the tree but in no IMPLEMENTATION_MODULES list — editing it would not move the vector — so no record."""
    v = variant(tmp_path, base, "v")
    edit(v.root, K + "input_vector.py", '"window_solver", "window_solver_check")', '"window_solver")')
    LISTS_BACKUP = copy.deepcopy(LISTS)
    try:
        LISTS["window"] = [m for m in LISTS["window"] if not m.endswith("window_solver_check")]
        v.pinned["input_vector"]["implementation"] = stage_digests(v.root)
        with pytest.raises(eqr.EqrRefusal, match="window_solver_check.*no IMPLEMENTATION_MODULES list"):
            v.build()
    finally:
        LISTS.clear()
        LISTS.update(LISTS_BACKUP)


def test_eq1_a_required_module_absent_from_the_tree_is_recorded_as_absent(tmp_path):
    """Main today has no window_solver: E1 says `absent`, so a head with the solver differs from one without."""
    c = Case(tmp_path, "c")
    for m in ("window_solver", "window_solver_check"):
        (c.root / K / f"{m}.py").unlink()
    edit(c.root, K + "input_vector.py", ', "window_solver", "window_solver_check")', ")")
    saved = copy.deepcopy(LISTS)
    try:
        LISTS["window"] = LISTS["window"][:2]
        c.pinned["input_vector"]["implementation"] = stage_digests(c.root)
        rec, _ = c.build()
    finally:
        LISTS.clear()
        LISTS.update(saved)
    assert rec["categories"]["E1"]["digest"]
    sub = c.loaded().manifest("E1.json")
    assert sub["required_modules"] == {"services.gochara_kernel.window_solver": "absent", "services.gochara_kernel.window_solver_check": "absent"}


def test_eq1_a_closure_module_in_no_list_refuses(tmp_path, base):
    """The writer's static import closure must be covered by the lists (tests/l3/gochara/test_a53_input_vector.py coverage test)."""
    v = variant(tmp_path, base, "v")
    put(v.root, K + "unlisted.py", "X = 1\n")
    edit(v.root, K + "evaluator.py", "from . import ids", "from . import ids, unlisted")
    v.pinned["input_vector"]["implementation"] = stage_digests(v.root)
    with pytest.raises(eqr.EqrRefusal, match="import closure but in no IMPLEMENTATION_MODULES list.*unlisted"):
        v.build()


def test_eq1_the_qualification_check_function_body_in_the_migrations_moves_E1(tmp_path, base):
    """E1 binds the non-Python resource the build consumes: the CHECK function body of 1240 (and any 1402/1403 successor)."""
    v = variant(tmp_path, base, "v")
    edit(v.root, "platform/migrations/1240_gate.sql", "jsonb_typeof(q) = 'object'", "jsonb_typeof(q) = 'array'")
    assert digest(v, "E1") != digest(base, "E1")
    w = variant(tmp_path, base, "w")
    put(w.root, "platform/migrations/1403_successor.sql", Path(base.root / "platform/migrations/1240_gate.sql").read_text().split("ALTER")[0])
    assert digest(w, "E1") != digest(base, "E1")
    x = variant(tmp_path, base, "x")
    edit(x.root, "platform/migrations/1240_gate.sql", "ALTER TABLE t ADD COLUMN c int;", "ALTER TABLE t ADD COLUMN d int;")
    assert digest(x, "E1") == digest(base, "E1")                           # outside the function body: not a result-bearing change


# ── EQ-2 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

E2_MUTATIONS = {
    "selection_1_2_0": lambda p: p["rules"]["selection"].update(selected_rule_version="1.2.0"),
    "profile": lambda p: p["rules"]["selection"].update(profile="trial"),
    "form_b_cell_registry": lambda p: p["input_vector"]["registry"].update(digest=h("registry-2")),
    "ruling_ref": lambda p: p["input_vector"].update(rulings_digest=h("rulings-2")),
    "node_model": lambda p: p["input_vector"]["node"].update(model="true"),
    "activity_orb": lambda p: p["input_vector"]["orb_policy"].update(activity={"1.3.0": {"orb_deg": "1.5"}}),
    "admission_orb": lambda p: p["input_vector"]["orb_policy"].update(admission_digest=h("adm-2")),
    "declared_accuracy": lambda p: p["rules"]["declared_accuracy"].update(peak_instant_seconds="2"),
    "result_policy": lambda p: p["input_vector"].update(result_policy="all_null_candidate/1"),
}


@pytest.mark.parametrize("name", sorted(E2_MUTATIONS))
def test_eq2_a_change_to_selection_ruling_convention_or_orb_policy_moves_E2(tmp_path, base, name):
    """G-8; AM-13: each named rule input moves E2 (and nothing else)."""
    assert only_differs(tmp_path, base, "E2", mutate=E2_MUTATIONS[name]) == ["E2"]


@pytest.mark.parametrize("rel,old,new", [(K + "convention.py", '"orb": 8.0', '"orb": 7.0'), (K + "record_store.py", '"node_model": "mean"', '"node_model": "true"'),
                                          (K + "record_store.py", "orb_conj_slow", "orb_conj_fast"),
                                          (K + "result_policy.py", '"n": 1', '"n": 2')])
def test_eq2_the_orb_tables_convention_and_qualification_table_are_read_from_the_commits_bytes(tmp_path, base, rel, old, new):
    """The admission orb table, the node model and the qualification table are module constants: a change moves E2 (E1 moves with the module)."""
    v = variant(tmp_path, base, "v", tree_edits=[(rel, old, new)])
    assert digest(v, "E2") != digest(base, "E2")


# ── EQ-3 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

E3_MUTATIONS = {
    "rahu_gemini_rung_row": lambda p: p["inputs"]["e3a"]["l0_rows"]["bg_transit_rules"]["rahu_gemini"].update(rung="DB"),
    "l1_fact": lambda p: p["inputs"]["e3a"]["l1_facts"]["fact_1"]["content"].update(sign="Z"),
    "l1_provenance": lambda p: p["inputs"]["e3a"]["l1_facts"]["fact_1"].update(provenance="ga_other"),
    "held_dasha_boundary": lambda p: p["inputs"]["e3a"]["dasha"]["held_state"].update(held="d1"),
    "dasha_row": lambda p: p["inputs"]["e3a"]["dasha"]["population"]["d1"].update(end="2031-01-01"),
    "av_declaration": lambda p: p["inputs"]["e3a"]["av_declarations"]["av_1"].update(declared=False),
    "l0_loader_digest": lambda p: p["input_vector"]["l0"].update(bg_transit_rules=h("l0-2")),
}


@pytest.mark.parametrize("name", sorted(E3_MUTATIONS))
def test_eq3_a_change_to_one_input_row_moves_E3a_by_content(tmp_path, base, name):
    """SR-1401-VERIFIED; G-8: row IDENTITIES alone do not bind an input — the same row id with different content must move E3."""
    assert only_differs(tmp_path, base, "E3", mutate=E3_MUTATIONS[name]) == ["E3"]


def test_eq3_a_row_in_the_century_snapshot_but_not_consumed_by_the_trial_is_not_E3a(tmp_path, base):
    """P2: E3b is bound, not compared — extra century rows leave E3 equal."""
    v = variant(tmp_path, base, "v", mutate=lambda p: p["inputs"]["e3b_population"].update({"l1:another": {"content": 1}}))
    assert digest(v, "E3") == digest(base, "E3")


# ── EQ-4 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

E4_MUTATIONS = {
    "swiss_file_digest": lambda p: p["input_vector"]["ephemeris"]["files"].update({"sepl_18.se1": h("f1-changed")}),
    "library_sha": lambda p: p["input_vector"]["ephemeris"].update(library_sha256=h("lib-2")),
    "swe_version": lambda p: p["input_vector"]["ephemeris"].update(swe_version="2.10.04"),
    "series_probe": lambda p: p["input_vector"]["ephemeris"].update(probe_digest=h("probe-2")),
    "vector_platform": lambda p: p["input_vector"]["ephemeris"].update(platform="Linux-aarch64"),
    "python": lambda p: p["runtime"].update(python="3.12.1"),
    "dependency_lock": lambda p: p["runtime"].update(dependency_lock_digest=h("lock-2")),
}


@pytest.mark.parametrize("name", sorted(E4_MUTATIONS))
def test_eq4_a_change_to_a_swiss_file_library_probe_platform_or_lock_moves_E4(tmp_path, base, name):
    """`ephemeris_identity` contract (input_vector.py): file digests, library sha, series probe and platform are the runtime identity."""
    assert only_differs(tmp_path, base, "E4", mutate=E4_MUTATIONS[name]) == ["E4"]


def test_eq4_the_dependency_requirements_file_moves_E4(tmp_path, base):
    v = variant(tmp_path, base, "v")
    put(v.root, SC + "/requirements.txt", "pyswisseph==2.10.3.3\n")
    assert digest(v, "E4") != digest(base, "E4")


# ── EQ-5 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

E5_MUTATIONS = {
    "class_universe": lambda p: p["century_config"].update(classes=CLASSES[:-1]),
    "horizon": lambda p: p["century_config"]["horizon"].update(end="2051-01-01T00:00:00+00:00"),
    "result_policy": lambda p: p["century_config"].update(result_policy="all_null_candidate/1"),
    "deferral": lambda p: p["century_config"].update(in_build_verify="in_build"),
    "budget": lambda p: p["century_config"]["budgets"].update(per_window="50000"),
    "verification_plan": lambda p: p["century_config"]["verification_plan"].update(mode="sharded"),
}


@pytest.mark.parametrize("name", sorted(E5_MUTATIONS))
def test_eq5_a_change_to_a_config_field_moves_E5(tmp_path, base, name):
    """A10.1 B1 E5: horizon, policy, deferral, budgets, class universe and verification plan are how the century is asked for."""
    assert only_differs(tmp_path, base, "E5", mutate=E5_MUTATIONS[name]) == ["E5"]


def test_eq5_a_tolerance_constant_moves_E5(tmp_path, base):
    """MAX_EVALS and TIE are read from the module constants of the commit (E5 `tolerances`)."""
    for rel, old, new in ((K + "window_solver.py", "40_000", "50_000"), (K + "window_solver_check.py", "TIE = 1e-9", "TIE = 2e-9")):
        v = variant(tmp_path, base, "v" + new, tree_edits=[(rel, old, new)])
        assert digest(v, "E5") != digest(base, "E5"), rel


def test_eq5_an_unresolved_or_contradictory_tolerance_makes_E5_null_not_a_default(tmp_path, base):
    v = variant(tmp_path, base, "v", tree_edits=[(K + "window_solver_check.py", "ISOLATION_S = 30\n", "")])
    rec = v.build()[0]["categories"]["E5"]
    assert rec["digest"] is None and any("ISOLATION_S" in r for r in rec["unreadable"])
    w = variant(tmp_path, base, "w", tree_edits=[(K + "window_sweep.py", "MIN_EXCURSION_SECONDS = 60", "MIN_EXCURSION_SECONDS = 60\nMAX_EVALS = 1")])
    assert w.build()[0]["categories"]["E5"]["digest"] is None


# ── EQ-6 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True, env=env).stdout.strip()


def git_commit_pair(tmp_path, src_root):
    """Two commits with an IDENTICAL tree and different shas (what a squash merge does to an integration head)."""
    repo = tmp_path / "repo"
    import shutil
    shutil.copytree(src_root, repo)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "integration head")
    a = git(repo, "rev-parse", "HEAD")
    git(repo, "commit", "-q", "--allow-empty", "-m", "squash-merged main head")
    return repo, a, git(repo, "rev-parse", "HEAD")


def test_eq6_a_label_only_change_keeps_the_decision_EQUAL_and_E6_stored(tmp_path, base):
    """A10 §3 / REVIEW_A10_GPT61 B1: commit SHA equality is neither required nor sufficient. Same bytes, two commits, two image digests, other run ids."""
    repo, a, b = git_commit_pair(tmp_path, base.root)
    assert a != b
    pa, pb = copy.deepcopy(base.pinned), copy.deepcopy(base.pinned)
    pb["provenance"].update(branch="main", image_tag="main-1", image_digest="sha256:" + h("img-b"), ci_run_ids=["9"], dispatch_run_id="77")
    ra, ma = eqr.build_record(eqr.GitTree(repo, a), pa, "2026-01-01T00:00:00Z")
    rb, mb = eqr.build_record(eqr.GitTree(repo, b), pb, "2026-02-02T00:00:00Z")
    eqr.write_record(ra, ma, tmp_path / "t.json")
    eqr.write_record(rb, mb, tmp_path / "m.json")
    d = eqr.decide(eqr.load_record(tmp_path / "t.json"), eqr.load_record(tmp_path / "m.json"), eqr.load_table())
    assert d["decision"] == "EQUAL" and ra["record_digest"] == rb["record_digest"] and ra["record_digest"]
    assert (ra["E6"]["commit"], rb["E6"]["commit"]) == (a, b) and ra["E6"]["tree"] == rb["E6"]["tree"]
    assert ra["E6"]["image_digest"] != rb["E6"]["image_digest"] and rb["E6"]["dispatch_run_id"] == "77"
    assert d["action"]["overall"] == "none"


def test_eq6_the_git_path_reads_the_same_bytes_as_the_directory_path(tmp_path, base):
    repo, a, _ = git_commit_pair(tmp_path, base.root)
    rg, _ = eqr.build_record(eqr.GitTree(repo, a), base.pinned, TS)
    rd, _ = base.build()
    assert rg["record_digest"] == rd["record_digest"] and rg["categories"] == rd["categories"]


# ── EQ-7 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq7_the_trial_scope_fields_are_excluded_by_name_and_only_those(tmp_path, base):
    """A10.1 §3.3 P1: a 12-class trial differs from the century only in its own stored_scope, test_slice, horizon, horizon_basis, class subset."""
    def other_trial(p):
        iv = p["input_vector"]
        iv.update(stored_scope="other_slice", test_slice={"classes": 9}, horizon_basis={"kind": "derived"}, scored_classes=CLASSES[:5])
        p["trial_scope"] = {"horizon": {"start": "2010-01-01", "end": "2011-01-01"}}
    v = variant(tmp_path, base, "v", mutate=other_trial)
    d = decide(base, v)
    assert d["decision"] == "EQUAL" and base.build()[0]["record_digest"] == v.build()[0]["record_digest"]
    assert base.build()[0]["projection"]["excluded_fields"] == list(eqr.PROJECTION_EXCLUDED)


def test_eq7_a_century_horizon_that_differs_from_the_dispatch_config_is_DIFFERS(tmp_path, base):
    """§3.3 P1: the comparison uses the CENTURY fields declared in the dispatch config; the century horizon is not excluded."""
    v = variant(tmp_path, base, "v", mutate=lambda p: p["century_config"]["horizon"].update(start="1999-01-01T00:00:00+00:00"))
    d = decide(base, v)
    assert d["decision"] == "DIFFERS" and d["per_category"]["E5"] == "differs" and d["action"]["overall"] == "correct_config"


def test_eq7_a_trial_scope_inside_a_century_config_refuses(tmp_path, base):
    """§3.3 P1 / input_vector.py ≈ l.490–509: a trial scope that leaks into a century config is a difference (the manifest is unsealable)."""
    for key, val in (("test_slice", {"classes": 4}), ("class_subset", CLASSES[:12])):
        v = variant(tmp_path, base, "v" + key, mutate=lambda p, key=key, val=val: p["century_config"].update({key: val}))
        with pytest.raises(eqr.EqrRefusal, match="trial-scope"):
            v.build()
    w = variant(tmp_path, base, "w", mutate=lambda p: p["century_config"].update(stored_scope="trial_slice"))
    with pytest.raises(eqr.EqrRefusal, match="stored_scope"):
        w.build()


def test_eq7_a_record_that_excludes_more_than_the_named_fields_is_refused(tmp_path, base):
    rec, mans = base.build()
    rec["projection"]["excluded_fields"] = rec["projection"]["excluded_fields"] + ["century.horizon"]
    eqr.write_record(rec, mans, base.path)
    with pytest.raises(eqr.EqrRefusal, match="nothing else may be excluded"):
        eqr.load_record(base.path)


def test_eq7_p5_the_classes_without_trial_evidence_are_disclosed(base):
    assert base.build()[0]["projection"]["no_trial_evidence_classes"] == CLASSES[12:]


# ── EQ-8 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq8_the_decision_stores_both_producing_commits_and_images_unchanged_and_never_rewrites_a_record(tmp_path, base):
    """§3.4: EQ_CHECK never relabels the producing commit or image and never rewrites an attestation."""
    repo, a, b = git_commit_pair(tmp_path, base.root)
    pb = copy.deepcopy(base.pinned)
    pb["provenance"].update(image_tag="main-1", image_digest="sha256:" + h("img-b"))
    ra, ma = eqr.build_record(eqr.GitTree(repo, a), base.pinned, TS)
    rb, mb = eqr.build_record(eqr.GitTree(repo, b), pb, TS)
    eqr.write_record(ra, ma, tmp_path / "t.json")
    eqr.write_record(rb, mb, tmp_path / "m.json")
    before = [(tmp_path / n).read_bytes() for n in ("t.json", "m.json")]
    manifests = {p.name: p.read_bytes() for p in (tmp_path / "t.json.manifests").iterdir()}
    d = eqr.decide(eqr.load_record(tmp_path / "t.json"), eqr.load_record(tmp_path / "m.json"), eqr.load_table())
    assert d["provenance"]["trial"] == ra["E6"] and d["provenance"]["main"] == rb["E6"]
    assert d["provenance"]["trial"]["image_digest"] == "sha256:" + h("img-a") and d["provenance"]["main"]["image_digest"] == "sha256:" + h("img-b")
    assert d["provenance"]["trial"]["commit"] == a and d["provenance"]["main"]["commit"] == b
    assert before == [(tmp_path / n).read_bytes() for n in ("t.json", "m.json")]
    assert manifests == {p.name: p.read_bytes() for p in (tmp_path / "t.json.manifests").iterdir()}
    assert (d["trial_record_sha"], d["main_record_sha"]) == tuple(hashlib.sha256(x).hexdigest() for x in before)


# ── EQ-9 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq9_the_record_is_canonical_indexes_its_manifests_and_its_digest_follows_the_five_category_digests(tmp_path, base):
    """§3.1: canonical JSON; each category digest = sha256(canonical subtree) retained as a manifest; record_digest = sha256 over E1..E5 in order."""
    rec, mans = base.build()
    eqr.write_record(rec, mans, base.path)
    raw = base.path.read_bytes()
    assert raw == json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ds = [rec["categories"][c]["digest"] for c in eqr.CATEGORIES]
    assert rec["record_digest"] == hashlib.sha256(json.dumps(ds, separators=(",", ":")).encode()).hexdigest()
    mdir = base.path.with_name(base.path.name + ".manifests")
    for c in eqr.CATEGORIES:
        body = (mdir / f"{c}.json").read_bytes()
        assert hashlib.sha256(body).hexdigest() == rec["categories"][c]["digest"] == rec["categories"][c]["manifest"]["sha256"]
    assert (mdir / "E3b.json").is_file() and rec["categories"]["E3"]["e3b"]["row_count"] == 10


def test_eq9_a_float_is_not_a_canonical_number(base):
    with pytest.raises(eqr.EqrRefusal, match="float"):
        eqr.canonical_json({"a": [1.5]})
    assert eqr.loads(b'{"a": 1.50, "b": 2}', "x") == {"a": "1.50", "b": 2}          # REAL values are their persisted decimal text
    with pytest.raises(eqr.EqrRefusal):
        eqr.loads(b'{"a": NaN}', "x")


def test_eq9_a_tampered_or_non_canonical_record_or_manifest_is_refused(tmp_path, base):
    rec, mans = base.build()
    eqr.write_record(rec, mans, base.path)
    good = json.loads(base.path.read_bytes())
    forged = copy.deepcopy(good)
    forged["categories"]["E2"]["digest"] = h("forged")
    base.path.write_bytes(eqr.record_bytes(forged))
    with pytest.raises(eqr.EqrRefusal, match="record_digest"):
        eqr.load_record(base.path)
    base.path.write_bytes(json.dumps(good, indent=1).encode())
    with pytest.raises(eqr.EqrRefusal, match="canonical form"):
        eqr.load_record(base.path)
    base.path.write_bytes(eqr.record_bytes(good))
    (base.path.with_name(base.path.name + ".manifests") / "E1.json").write_bytes(b"{}")
    with pytest.raises(eqr.EqrRefusal, match="manifest bytes"):
        eqr.load_record(base.path)


# ── EQ-10 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq10_a_pinned_vector_that_is_not_of_this_commit_refuses(tmp_path, base):
    """The vector's `implementation` digests (input_vector.py:`implementation_digests`) must equal the ones this commit's bytes give."""
    v = variant(tmp_path, base, "v")
    v.pinned["input_vector"]["implementation"]["window"] = h("some other head")
    with pytest.raises(eqr.EqrRefusal, match="not of this commit"):
        v.build()
    w = variant(tmp_path, base, "w", tree_edits=[(K + "arcs.py", "ARC = 1", "ARC = 2")])
    w.pinned["input_vector"]["implementation"] = base.pinned["input_vector"]["implementation"]      # the old head's vector against the new bytes
    with pytest.raises(eqr.EqrRefusal, match="not of this commit"):
        w.build()


def test_eq10_an_input_vector_with_unknown_or_missing_keys_refuses(tmp_path, base):
    for mut, msg in ((lambda p: p["input_vector"].update(surprise=1), "unknown"), (lambda p: p["input_vector"].pop("registry"), "missing")):
        v = variant(tmp_path, base, "v" + msg, mutate=mut)
        path = tmp_path / f"{msg}.json"
        path.write_text(json.dumps(v.pinned))
        with pytest.raises(eqr.EqrRefusal, match=msg):
            eqr.load_pinned(path)


def test_eq10b_scored_until_is_a_known_optional_input_vector_key_and_an_unknown_key_still_refuses(tmp_path, base):
    # scored_until: services/gochara_kernel/input_vector.py SCORED_UNTIL_KEY (D-FLIP F-10) - serialised by the generation, so the pinned vector may carry it.
    v = variant(tmp_path, base, "vsu", mutate=lambda p: p["input_vector"].update(scored_until="2050-01-01T00:00:00+00:00"))
    path = tmp_path / "su.json"
    path.write_text(json.dumps(v.pinned))
    assert eqr.load_pinned(path)["input_vector"]["scored_until"] == "2050-01-01T00:00:00+00:00"
    w = variant(tmp_path, base, "vsu2", mutate=lambda p: p["input_vector"].update(scored_until="2050-01-01T00:00:00+00:00", surprise=1))
    path2 = tmp_path / "su2.json"
    path2.write_text(json.dumps(w.pinned))
    with pytest.raises(eqr.EqrRefusal, match=r"unknown \['surprise'\]"):
        eqr.load_pinned(path2)


def test_eq10c_the_constant_reader_joins_a_literal_over_a_constant_list_and_still_refuses_anything_else():
    # result_policy.QUALIFICATION_TABLE rule 2 is `"... " + ", ".join(SOLVER_BLANK_REASONS) + "..."` (platform/python-sidecar/services/gochara_kernel/result_policy.py)
    env = eqr.ConstEnv('R = ("a", "b")\nT = "x: " + ", ".join(R) + "; y"\nBAD = ", ".join(open("f"))\nBAD2 = "".join([1, 2])\n', "m.py")
    assert env.get("T") == "x: a, b; y"
    for bad in ("BAD", "BAD2"):
        with pytest.raises(eqr.Unreadable):
            env.get(bad)


# ── EQ-11 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq11_an_unreadable_source_makes_the_category_null_and_the_decision_never_EQUAL(tmp_path, base):
    """N.7.6: a category whose source cannot be read is null (with the reason), the record is incomplete, and null-against-null is not equal."""
    def no_rules(p):
        del p["rules"]
    a, b = variant(tmp_path, base, "a", mutate=no_rules), variant(tmp_path, base, "b", mutate=no_rules)
    rec = a.build()[0]
    assert rec["categories"]["E2"]["digest"] is None and rec["complete"] is False and rec["record_digest"] is None
    assert any("rules.selection" in r for r in rec["categories"]["E2"]["unreadable"])
    d = decide(a, b)
    assert d["decision"] == "DIFFERS" and d["per_category"]["E2"] == "differs" and d["action"]["overall"] == "complete_record_and_recheck"
    assert d["detail"]["unreadable"]["E2"]["trial"]


# ── EQ-12 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq12_only_a_qualifying_amd64_run_or_the_dispatch_image_has_an_E4(tmp_path, base):
    """A10.1 §3.3 P3/P6: rolling diagnostics and arm64 corroboration are excluded; a different image digest with identical E4 is allowed."""
    roll = variant(tmp_path, base, "r", mutate=lambda p: p["runtime"].update(kind="rolling_diagnostic"))
    assert roll.build()[0]["categories"]["E4"]["digest"] is None
    arm = variant(tmp_path, base, "a", mutate=lambda p: p["runtime"].update(arch="linux/arm64"))
    assert arm.build()[0]["categories"]["E4"]["digest"] is None
    disp = variant(tmp_path, base, "d", mutate=lambda p: (p["runtime"].update(kind="dispatch_image"),
                                                           p["provenance"].update(image_digest="sha256:" + h("another image"))))
    assert disp.build()[0]["categories"]["E4"]["digest"] == base.build()[0]["categories"]["E4"]["digest"]
    assert decide(base, disp)["decision"] == "EQUAL"
    with pytest.raises(eqr.EqrRefusal, match="runtime.kind"):
        variant(tmp_path, base, "x", mutate=lambda p: p["runtime"].update(kind="whatever")).build()


# ── EQ-13 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq13_E3b_must_cover_every_trial_E3a_row_with_identical_content(tmp_path, base):
    """§3.3 P2 / §3.5 'E3b coverage': a century snapshot lacking a trial-consumed row, or carrying it differently, blocks dispatch."""
    ok = decide(base, variant(tmp_path, base, "ok"))
    assert ok["decision"] == "EQUAL" and ok["per_category"]["E3b_coverage"] == "ok"
    missing = variant(tmp_path, base, "m", mutate=lambda p: p["inputs"]["e3b_population"].pop("l0:bg_transit_rules:rahu_gemini"))
    d = decide(base, missing)
    assert d["decision"] == "DIFFERS" and d["per_category"]["E3b_coverage"] == "missing_rows" and d["detail"]["e3b_coverage_rows"] == ["l0:bg_transit_rules:rahu_gemini"]
    assert d["per_category"]["E3"] == "equal" and d["action"]["overall"] == "repair_snapshot_and_recheck"
    changed = variant(tmp_path, base, "c", mutate=lambda p: p["inputs"]["e3b_population"].update({"l1:fact_1": {"content": {"sign": "Q"}, "provenance": "ga_x"}}))
    assert decide(base, changed)["per_category"]["E3b_coverage"] == "missing_rows"
    none = variant(tmp_path, base, "n", mutate=lambda p: p["inputs"].pop("e3b_population"))
    assert decide(base, none)["per_category"]["E3b_coverage"] == "unreadable" and decide(base, none)["decision"] == "DIFFERS"


# ── EQ-14 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_eq14_the_requalification_table_is_data_with_a_row_for_every_line_of_plan_3_5():
    t = eqr.load_table()
    ids = {r["id"] for r in t["rows"]}
    assert {"E1.outside", "E1.inside", "E2", "E3a.l0", "E3a.other", "E3b.coverage", "E4.probe", "E4.other", "E5.budgets_or_tolerances", "E5.other",
            "E6.only"} <= ids
    rows = {r["id"]: r for r in t["rows"]}
    assert rows["E1.outside"]["action"] == "rerun_tr1_four_class_slice_amd64" and rows["E1.inside"]["action"] == "full_tr"
    assert rows["E2"]["action"] == "full_tr" and rows["E6.only"]["action"] == "none"
    assert "stop_and_tell_surrogate" in rows["E3a.l0"]["flags"] and rows["E4.other"]["action"] == "rerun_amd64_slice_on_dispatch_image"


ACTION_CASES = [
    ("e1_outside", dict(tree_edits=[(K + "arcs.py", "ARC = 1", "ARC = 2")]), "E1", "rerun_tr1_four_class_slice_amd64"),
    ("e1_inside_checker", dict(tree_edits=[(K + "window_solver_check.py", "LEAF_S = 0.5", "LEAF_S = 0.25")]), "E1", "full_tr"),
    ("e2", dict(mutate=E2_MUTATIONS["activity_orb"]), "E2", "full_tr"),
    ("e3_l0", dict(mutate=E3_MUTATIONS["rahu_gemini_rung_row"]), "E3", "full_tr"),
    ("e3_dasha", dict(mutate=E3_MUTATIONS["held_dasha_boundary"]), "E3", "full_tr"),
    ("e4_probe", dict(mutate=E4_MUTATIONS["series_probe"]), "E4", "full_tr"),
    ("e4_file", dict(mutate=E4_MUTATIONS["swiss_file_digest"]), "E4", "rerun_amd64_slice_on_dispatch_image"),
    ("e5_budget", dict(mutate=E5_MUTATIONS["budget"]), "E5", "full_tr"),
    ("e5_class", dict(mutate=E5_MUTATIONS["class_universe"]), "E5", "correct_config"),
]


@pytest.mark.parametrize("name,kw,cat,action", ACTION_CASES, ids=[c[0] for c in ACTION_CASES])
def test_eq14_the_minimum_action_for_a_difference_is_the_table_row_of_its_differing_parts(tmp_path, base, name, kw, cat, action):
    """PLAN_A10_1 §3.5: E1 outside the solver/checker/evaluator → TR1; inside → full TR; E2/E3a/E4-probe/E5-budgets → full TR; E4 file/arch/lock →
    amd64 slice on the dispatch image; E5 other → correct the config."""
    d = decide(base, variant(tmp_path, base, "v", **kw))
    assert d["decision"] == "DIFFERS" and d["per_category"][cat] == "differs"
    assert d["action"]["overall"] == action, d["action"]


def test_eq14_the_surrogate_flag_rides_an_L0_difference_only(tmp_path, base):
    assert "stop_and_tell_surrogate" in decide(base, variant(tmp_path, base, "a", mutate=E3_MUTATIONS["rahu_gemini_rung_row"]))["action"]["flags"]
    assert "stop_and_tell_surrogate" not in decide(base, variant(tmp_path, base, "b", mutate=E3_MUTATIONS["l1_fact"]))["action"]["flags"]


def test_eq14_the_action_comes_from_the_data_file_not_from_code(tmp_path, base):
    t = eqr.load_table()
    for r in t["rows"]:
        if r["id"] == "E2":
            r["action"] = "correct_config"
    d = eqr.decide(variant(tmp_path, base, "x").loaded(), variant(tmp_path, base, "y", mutate=E2_MUTATIONS["profile"]).loaded(), t)
    assert d["action"]["overall"] == "correct_config"


# ── EQ-15 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _repo_closure_by_the_repositorys_own_detector():
    """tests/l3/gochara/_import_closure.py UNCHANGED; only its module resolution (importlib.find_spec, which would import the heavy packages) is
    replaced by a filesystem lookup."""
    spec = importlib.util.spec_from_file_location("_ic_under_test", REPO / SC / "tests/l3/gochara/_import_closure.py")
    ic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ic)

    def fs_spec(name):
        base = REPO / SC / name.replace(".", "/")
        for cand in (base.with_suffix(".py"), base / "__init__.py"):
            if cand.is_file():
                return SimpleNamespace(origin=str(cand))
        return None
    ic._spec = fs_spec
    return ic.writer_closure()


def test_eq15_the_closure_port_equals_the_repositorys_own_detector_at_head_and_the_lists_cover_it():
    tree = eqr.DirTree(REPO)
    mine = eqr.writer_closure(tree)
    assert mine == _repo_closure_by_the_repositorys_own_detector() and len(mine) > 40
    lists = eqr._Consts(tree).get(eqr.INPUT_VECTOR_REL, "IMPLEMENTATION_MODULES")
    assert mine <= {m for v in lists.values() for m in v}
    assert all(eqr.module_path(tree, m) for v in lists.values() for m in v)


def test_eq15_the_cli_writes_the_record_and_compares_two_records_end_to_end(tmp_path, base):
    repo, a, b = git_commit_pair(tmp_path, base.root)
    pin = tmp_path / "pin.json"
    pin.write_text(json.dumps(base.pinned))
    tool = str(FLEET / "equivalence_record.py")
    outs = []
    for name, commit in (("t", a), ("m", b)):
        r = subprocess.run([sys.executable, tool, "record", "--repo", str(repo), "--commit", commit, "--pinned-inputs", str(pin), "--out",
                            str(tmp_path / f"{name}.json"), "--generated-at", TS], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        outs.append(json.loads(r.stdout))
    assert outs[0]["complete"] and outs[0]["record_digest"] == outs[1]["record_digest"]
    r = subprocess.run([sys.executable, tool, "compare", "--trial", str(tmp_path / "t.json"), "--main", str(tmp_path / "m.json"), "--out",
                        str(tmp_path / "decision.json")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    dec = json.loads((tmp_path / "decision.json").read_text())
    assert dec["schema"] == eqr.DECISION_SCHEMA and dec["decision"] == "EQUAL" and dec["provenance"]["trial"]["commit"] == a
    # a difference exits 3; an incomplete record exits 2; a refusal exits 1 and writes nothing
    bad = copy.deepcopy(base.pinned)
    bad["runtime"]["python"] = "3.9"
    pin.write_text(json.dumps(bad))
    assert subprocess.run([sys.executable, tool, "record", "--repo", str(repo), "--commit", b, "--pinned-inputs", str(pin), "--out",
                           str(tmp_path / "m2.json")], capture_output=True, text=True).returncode == 0
    assert subprocess.run([sys.executable, tool, "compare", "--trial", str(tmp_path / "t.json"), "--main", str(tmp_path / "m2.json")],
                          capture_output=True, text=True).returncode == 3
    del bad["rules"]
    pin.write_text(json.dumps(bad))
    assert subprocess.run([sys.executable, tool, "record", "--repo", str(repo), "--commit", b, "--pinned-inputs", str(pin), "--out",
                           str(tmp_path / "m3.json")], capture_output=True, text=True).returncode == 2
    refused = subprocess.run([sys.executable, tool, "record", "--repo", str(repo), "--commit", "0" * 40, "--pinned-inputs", str(pin), "--out",
                              str(tmp_path / "m4.json")], capture_output=True, text=True)
    assert refused.returncode == 1 and not (tmp_path / "m4.json").exists() and "REFUSED" in refused.stderr


# ── EQ-16 (SR-T24-AMD64-DOCKER) ───────────────────────────────────────────────────────────────────────────────────────────────────────────

PROBE = {"source": "in_container", "uname_machine": "x86_64", "platform_machine": "x86_64", "sys_platform": "linux", "nonce_sha256": h("n")}
NOTE = {"emulation": {"emulated": True, "layer": "rosetta", "ruling": "SR-T24-AMD64-DOCKER"}}


def emulated(p, probe=PROBE, note=NOTE):
    p["runtime"].update(emulated=True)
    if probe is not None:
        p["runtime"]["arch_probe"] = dict(probe)
    if note is not None:
        p["provenance"]["platform_notes"] = copy.deepcopy(note)


@pytest.mark.parametrize("probe", [None, {**PROBE, "source": "host"}, {**PROBE, "uname_machine": "arm64"}, {**PROBE, "sys_platform": "darwin"}])
def test_eq16_the_arch_of_an_emulated_run_is_read_inside_the_container_never_asserted_from_outside(tmp_path, base, probe):
    """SR-T24-AMD64-DOCKER ('arch must still read linux/amd64 from inside the container - uname -m == x86_64 - never asserted from outside'): a container run whose runtime
    names linux/amd64 without an in-container probe reading x86_64 on linux is REFUSED, not recorded."""
    v = variant(tmp_path, base, "v", mutate=lambda p: emulated(p, probe=probe))
    with pytest.raises(eqr.EqrRefusal, match="read inside the container"):
        v.build()


@pytest.mark.parametrize("note", [None, {"emulation": {"emulated": True, "layer": ""}}, {"emulation": {"emulated": False, "layer": "qemu"}}, {"other": 1}])
def test_eq16_an_emulated_run_without_its_emulation_note_is_refused(tmp_path, base, note):
    """SR-T24-AMD64-DOCKER ('with the emulation recorded in the EQUIVALENCE_RECORD platform notes'): `emulated: true` needs provenance.platform_notes.emulation
    {emulated: true, layer: rosetta|qemu|undetermined}; without it no record is written."""
    v = variant(tmp_path, base, "v", mutate=lambda p: emulated(p, note=note))
    with pytest.raises(eqr.EqrRefusal, match="platform_notes"):
        v.build()


def test_eq16_the_emulation_note_is_provenance_it_never_moves_E4_or_the_decision(tmp_path, base):
    """The dispatch image is compared with this run: E4..E5 digests are equal whether or not the run was emulated; the note is stored verbatim in E6 (provenance, never compared)."""
    em = variant(tmp_path, base, "em", mutate=emulated)
    assert digest(em, "E4") == digest(base, "E4")
    rec = em.build()[0]
    assert rec["E6"]["platform_notes"] == NOTE and rec["complete"] is True
    disp = variant(tmp_path, base, "d", mutate=lambda p: p["runtime"].update(kind="dispatch_image"))
    assert decide(em, disp)["decision"] == "EQUAL"
