"""test_e5_7_fingerprint_declarations.py -- E5.7: `00_ARCHITECTURE/control/FINGERPRINT_DECLARATIONS.json` and its loader/validator
(`fingerprint_declarations.py`), tests-first and mutation-checked.

No production database, credential or network is touched. The mirror dump (`prod_schema.sql`, schema only) is read as TEXT when it is
present on the machine; the committed schema extract (derived from it) makes the same checks run in CI. PostgreSQL appears ONLY through the
repo's disposable fixture.

Layout
  1. the committed file          valid against the registry snapshot, the schema extract and the writer files; 40 assets, every one
                                 declared or listed undeclared with a reason; ONE fingerprint definition
  2. the mirror dump             every declared table is `CREATE TABLE public.<name>` in the dump; every excluded column is in that
                                 table's body; the committed extract equals one regenerated from the dump
  3. refusals                    one mutation per refusal (the validator must name it)
  4. conversion + composition    each declared table is a valid E5.5 declaration; the asset fingerprint composition
  5. real SQL                    on the disposable cluster: the asset fingerprint equals E5.5's `table_fingerprint`, ignores exactly the
                                 declared volatile columns, moves on a semantic change; undeclared assets are refused
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
REPO = GOV.parents[2]
sys.path.insert(0, str(GOV))
sys.path.insert(0, str(HERE))

import fingerprint_declarations as fd  # noqa: E402
import nikasha_stale_certs as nsc  # noqa: E402
import suvarna_rehearsal as sr  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

MIRROR_DUMP = pathlib.Path("/Users/Dev/suvarna-evidence/S_L1/rehearsal_final/seed/prod_schema.sql")
needs_dump = pytest.mark.skipif(not MIRROR_DUMP.is_file(), reason="the mirror recipe dump is not on this machine (the committed extract covers CI)")

DOC = json.loads(fd.DEFAULT_DECLARATIONS.read_text(encoding="utf-8"))
REG = fd.load_registry()
EXT = fd.load_schema_extract()


def problems(doc, *, registry=REG, schema=EXT, repo_root=REPO):
    return fd.validate(doc, registry=registry, schema=schema, repo_root=repo_root)


def codes(doc, **kw):
    return sorted({c for c, _p, _m in problems(doc, **kw)})


def mut(fn, doc=None):
    d = copy.deepcopy(DOC if doc is None else doc)
    fn(d)
    return d


def first_declared(pred=lambda a, d: True):
    for a, d in DOC["assets"].items():
        if d["status"] == "declared" and pred(a, d):
            return a
    raise AssertionError("no declared asset matches")


# ═════════════════════════ 1. the committed file ═════════════════════════

def test_the_committed_declarations_are_valid():
    assert problems(DOC) == []
    d = fd.load_declarations()
    assert d.sha256 == fd.sha256_file(fd.DEFAULT_DECLARATIONS) and len(d.sha256) == 64


def test_every_active_l0_asset_is_declared_or_listed_undeclared_exactly_once():
    assert len(REG) == 40 and set(DOC["assets"]) == set(REG)
    d = fd.load_declarations()
    assert sorted(d.declared_assets() + list(d.undeclared_assets())) == sorted(REG)
    assert len(d.declared_assets()) == 35 and len(d.undeclared_assets()) == 5          # 34 / 6 before bg_transit_rules was declared (SS ruling 2, shared writer group bg_transit_seed)
    # the comparison units: the declared assets that own tables + one unit per shared-table group; undeclared assets are never units
    assert d.expected_assets() == sorted(d.units()) and len(d.expected_assets()) == 32
    assert {u for u in d.units() if u.startswith("grp_")} == {"grp_bg_transit_seed", "grp_brahma_class_priors", "grp_brahma_ontology", "grp_classical_text_chunks"}
    assert not set(d.expected_assets()) & set(d.undeclared_assets())
    for a, u in d.undeclared_assets().items():
        assert u["reason_code"] in fd.UNDECLARED_CODES and len(u["reason"]) >= fd.MIN_UNDECLARED_REASON_CHARS, a


def test_the_known_undeclared_assets_and_their_reasons():
    un = fd.load_declarations().undeclared_assets()
    assert {a: u["reason_code"] for a, u in un.items()} == {
        "bg_compendium_index": "no_plain_natural_key", "bg_ephemeris_engine": "no_table", "bg_panchanga": "no_table",
        "bg_gochara_citation_resolution": "migration_owned_rows", "bg_sarvatobhadra_grid": "migration_owned_rows"}
    # SS decision 5: the stated reasons carry the probe counts (bg_transit_rules is declared since SS ruling 2: its probe count lives in its partial_ownership detail)
    assert "14 rows" in un["bg_gochara_citation_resolution"]["reason"]
    assert "count(*) = 0" in un["bg_sarvatobhadra_grid"]["reason"]


def test_partial_assets_name_the_tables_they_do_not_cover():
    p = fd.load_declarations().partial_assets()
    assert sorted(p) == ["bg_remedies", "bg_texts"]
    assert [n["name"] for n in p["bg_remedies"]] == ["remedy_review_queue"] and [n["name"] for n in p["bg_texts"]] == ["classical_texts"]


def test_the_three_shared_tables_are_declared_once_as_groups_with_all_their_members():
    d = fd.load_declarations()
    assert {g: sorted(v["members"]) for g, v in d.groups.items()} == {
        "brahma_ontology": ["bg_dasha_systems", "bg_doshas", "bg_ontology", "bg_yogas"],
        "brahma_class_priors": ["bg_class_lifetime_counts", "bg_class_priors"],
        "classical_text_chunks": ["bg_text_index", "bg_texts"],
        "bg_transit_seed": ["bg_transit_engine", "bg_transit_rules"]}
    assert d.members("grp_brahma_ontology") == ["bg_dasha_systems", "bg_doshas", "bg_ontology", "bg_yogas"]
    for g, v in d.groups.items():
        for m in v["members"]:
            assert g in DOC["assets"][m]["groups"]
    # no asset-owned table is also a group table, and group-only assets own none
    gt = {t["name"] for v in d.groups.values() for t in v["tables"]}
    assert not gt & {t["name"] for a in DOC["assets"].values() if a["status"] == "declared" for t in a["tables"]}
    assert all(DOC["assets"][a]["tables"] == [] for a in ("bg_ontology", "bg_class_priors", "bg_class_lifetime_counts", "bg_text_index", "bg_texts"))
    # the former partial assets are now full
    assert all(DOC["assets"][a]["coverage"] == "full" for a in ("bg_dasha_systems", "bg_doshas", "bg_yogas"))
    # the text group carries the embedding policy (the vector is not hashed)
    txt = d.groups["classical_text_chunks"]["tables"][0]
    assert txt["embedding"] == [{"column": "embedding", "source_columns": ["content_en", "content_sa"], "model_id": "text-multilingual-embedding-002"}]
    assert d.table_declaration("grp_classical_text_chunks", "classical_text_chunks")["embedding"][0]["column"] == "embedding"


def test_ss_decision_2_only_kill_switch_criteria_is_excluded_from_the_event_ontology():
    t = next(t for t in DOC["assets"]["bg_ghatana"]["tables"] if t["name"] == "brahma_event_ontology")
    assert {e["column"]: e["reason_code"] for e in t["exclude"]} == {"created_at": "wall_clock_timestamp", "kill_switch_criteria": "not_written_by_writer"}


def test_ss_decision_3_ephemeris_node_columns_are_compared_now_that_3015_is_on_main():
    """#3015 (bg_ephemeris writes node_mode and epoch_convention) is on main: the expected-difference record that covered the gap is retired (review of the
    split, 2026-10-05), so a rebuild that nulls those columns is a real mismatch, not an explained difference. The columns were never excluded."""
    d = fd.load_declarations()
    t = next(t for t in DOC["assets"]["bg_ephemeris"]["tables"] if t["name"] == "ephemeris_daily")
    assert {e["column"] for e in t["exclude"]} == {"id", "computed_at"}
    assert "expected_difference" not in t and d.expected_differences() == []
    assert d.table_declaration("bg_ephemeris", "ephemeris_daily")["volatile_columns"] == ["id", "computed_at"]      # node_mode and epoch_convention stay in the fingerprint
    assert "bg_gochara_arcs" not in fd.NOT_RUN_ALLOWED                                                              # the writer exists on main: the unit must run


def test_partly_writer_owned_tables_carry_the_closed_partial_ownership_field():
    d = fd.load_declarations()
    assert d.partial_ownership_units() == {"bg_formula_constants": ["brahma_formula_constants"], "bg_ghatana": ["brahma_event_ontology"], "grp_bg_transit_seed": ["bg_transit_rules"]}
    for a, t in (("bg_formula_constants", "brahma_formula_constants"), ("bg_ghatana", "brahma_event_ontology")):
        po = next(x for x in DOC["assets"][a]["tables"] if x["name"] == t)["partial_ownership"]
        assert set(po) == {"reason_code", "detail", "evidence"} and po["reason_code"] == "migration_owned_rows" and po["evidence"] and "whole table" in po["detail"]
    assert d.drill_coverage()["partial_ownership"] == d.partial_ownership_units() and d.drill_coverage()["scope"] == "declared_only"
    assert d.coverage_report()["partial_ownership"] == d.partial_ownership_units()
    # bg_transit_rules is declared since SS ruling 2 (group bg_transit_seed): its migration-owned rows are in the group table's partial_ownership detail
    grp = next(x for x in DOC["groups"]["bg_transit_seed"]["tables"] if x["name"] == "bg_transit_rules")
    assert DOC["assets"]["bg_transit_rules"]["status"] == "declared" and "double_transit" in grp["partial_ownership"]["detail"] and "Jupiter 5, Saturn 2" in grp["partial_ownership"]["detail"]


def test_ss_decision_5_bg_rules_is_declared_on_the_probe_evidence():
    a = DOC["assets"]["bg_rules"]
    t = a["tables"][0]
    assert a["status"] == "declared" and t["name"] == "sutravali_rules" and t["key"] == ["rule_id"]
    assert [e["column"] for e in t["exclude"]] == ["created_at"] and t["exclude"][0]["reason_code"] == "wall_clock_timestamp"
    assert t["ownership_evidence"][0].startswith("00_ARCHITECTURE/control/FINGERPRINT_OWNERSHIP_PROBES_2026-10-03.txt:")
    probe = (REPO / "00_ARCHITECTURE/control/FINGERPRINT_OWNERSHIP_PROBES_2026-10-03.txt").read_text()
    assert "python_regex_v2|3002" in probe and "double_transit|Jupiter|5" in probe and "double_transit|Saturn|2" in probe


def test_the_drill_coverage_block_says_what_the_verdict_covers():
    cov = fd.load_declarations().drill_coverage()
    assert cov["scope"] == "declared_only" and len(cov["units"]) == 32 and len(cov["declared"]) == 35
    assert sorted(cov["undeclared"]) == ["bg_compendium_index", "bg_ephemeris_engine", "bg_gochara_citation_resolution", "bg_panchanga",
                                         "bg_sarvatobhadra_grid"] and sorted(cov["partial"]) == ["bg_remedies", "bg_texts"]
    assert cov["non_deterministic"] == {"bg_cohort": ["platform_bound"], "bg_muhurta_lattice": ["rolling_horizon"],
                                        "bg_sky_calendar": ["rolling_horizon", "platform_bound"]}
    assert cov["declarations_sha256"] == fd.load_declarations().sha256 and sr.check_coverage(cov, cov["units"]) == cov
    assert cov["seeded"] == ["grp_classical_text_chunks"] and fd.load_declarations().coverage_report()["seeded"] == ["grp_classical_text_chunks"]
    assert {g: v["seeded"] for g, v in DOC["groups"].items()} == {"brahma_ontology": False, "brahma_class_priors": False, "classical_text_chunks": True, "bg_transit_seed": False}


def test_the_not_run_list_is_closed_decided_by_n_121_and_limited_to_declared_plain_units():
    assert fd.NOT_RUN_ALLOWED == {"bg_sky_calendar": {"reason": "NEEDS_LINUX_AMD64_RUNTIME", "decision": "N-121"},
                                  "bg_cohort": {"reason": "NEEDS_LINUX_AMD64_RUNTIME", "decision": "N-121"},
                                  "bg_muhurta_lattice": {"reason": "NEEDS_AS_OF_PIN", "decision": "N-121"}}
    assert "bg_gochara_arcs" not in fd.NOT_RUN_ALLOWED                    # #3015 is on main: the unit must run (the permission was retired in the split review)
    d = fd.load_declarations()
    assert d.not_run_allowed() == {"bg_cohort": "NEEDS_LINUX_AMD64_RUNTIME", "bg_muhurta_lattice": "NEEDS_AS_OF_PIN", "bg_sky_calendar": "NEEDS_LINUX_AMD64_RUNTIME"}
    assert set(d.not_run_allowed()) <= set(d.declared_assets()) and not set(d.not_run_allowed()) & set(d.drill_coverage()["groups"])
    assert d.drill_coverage()["not_run_allowed"] == d.not_run_allowed() and d.coverage_report()["not_run_allowed"] == d.not_run_allowed()
    assert d.drill_coverage()["scope"] == "declared_only" and sr.check_coverage(d.drill_coverage(), d.expected_assets())["not_run_allowed"] == d.not_run_allowed()
    # no decision text other than N-121 anywhere in the declarations or the module's constant
    assert "SS round" not in json.dumps(DOC) and "N-121" in json.dumps(DOC)


@pytest.mark.parametrize("old,new", [
    ('    "bg_cohort": {"reason": "NEEDS_LINUX_AMD64_RUNTIME", "decision": "N-121"},', '    "bg_cohort": {"reason": "NEEDS_LINUX_AMD64_RUNTIME", "decision": "N-121"},\n    "bg_ephemeris": {"reason": "NEEDS_X", "decision": "N-121"},'),
    ('        return {a: v["reason"] for a, v in sorted(NOT_RUN_ALLOWED.items()) if a in units}', '        return {a: v["reason"] for a, v in sorted(NOT_RUN_ALLOWED.items())}'),
    ('"not_run_allowed": self.not_run_allowed(),\n                "expected_differences"', '"not_run_allowed": {},\n                "expected_differences"'),
    ('"not_run_allowed": cov["not_run_allowed"], "expected_differences"', '"not_run_allowed": {}, "expected_differences"'),
], ids=["widen_the_list", "unit_filter", "coverage_block", "coverage_report"])
def test_not_run_list_source_mutants_are_caught(old, new):
    assert SRC_FD.count(old) == 1, f"the mutant target is absent or not unique: {old!r}"
    mod = load_module(SRC_FD.replace(old, new, 1), "fd_nr_mut_" + str(abs(hash(old)) % 10**8))
    real = mod.load_declarations()
    syn = mod.Declarations(doc=_syn_decls().doc, sha256="9" * 64)
    caught = (mod.NOT_RUN_ALLOWED != fd.NOT_RUN_ALLOWED or real.not_run_allowed() != fd.load_declarations().not_run_allowed() or syn.not_run_allowed() != {}
              or real.drill_coverage()["not_run_allowed"] != real.not_run_allowed() or real.coverage_report()["not_run_allowed"] != real.not_run_allowed())
    assert caught, f"SURVIVING MUTANT: {old!r}"


# ----- round 6: table fingerprints do not depend on the SQL row order or on any database collation -----

def _collation_sensitive_rows():
    """Keys whose order differs between byte order (C) and an en_US-like collation (punctuation ignored first): 'mi_pariksha...' vs 'mimamsa...'."""
    keys = ["mimamsa_a", "mi_pariksha_b", "mi_a", "MI_Z", "mimamsa_B", "mi_pariksha_a", "a_b", "ab", "a-c", "mi gunanaka", "Zeta", "alpha"]
    return [{"constant_id": k, "value_jsonb": {"k": k}, "class": "c", "version": i} for i, k in enumerate(keys)]


def _orders(rows):
    import random
    c_order = sorted(rows, key=lambda r: r["constant_id"].encode("utf-8"))
    en_like = sorted(rows, key=lambda r: (re.sub(r"[^a-z0-9]", "", r["constant_id"].lower()), r["constant_id"]))
    assert [r["constant_id"] for r in c_order] != [r["constant_id"] for r in en_like]       # the two collations really disagree on these keys
    out = [c_order, en_like, list(reversed(c_order))]
    rng = random.Random(121)
    for _ in range(20):
        x = list(rows)
        rng.shuffle(x)
        out.append(x)
    return out


def _order_independent(nsc_mod, decl) -> bool:
    fps = {nsc_mod.fingerprint_rows(o, decl) for o in _orders(_collation_sensitive_rows())}
    return len(fps) == 1


def test_table_fingerprints_are_independent_of_the_sql_row_order_and_the_collation():
    d = fd.load_declarations()
    decl = d.table_declaration("bg_formula_constants", "brahma_formula_constants")
    assert decl["natural_key"] == ["constant_id"]
    assert _order_independent(nsc, decl)
    # a changed row still moves the fingerprint (the sort is not hiding content)
    rows = _collation_sensitive_rows()
    changed = [dict(r) for r in rows]
    changed[3]["version"] = 99
    assert nsc.fingerprint_rows(changed, decl) != nsc.fingerprint_rows(rows, decl)
    # the reader issues no ORDER BY at all: the order is irrelevant by construction, and nothing there can depend on a collation
    sels = fd.reader_selects(d)
    assert len(sels) == 64 and all(x["sql"].startswith("SELECT ") and "ORDER BY" not in x["sql"].upper() and "COLLATE" not in x["sql"].upper() for x in sels)
    assert "ORDER BY" not in SRC_NSC.split("def build_select")[1].split("\ndef ")[0].upper()
    assert "keyed.sort()" in SRC_NSC                                          # the Python sort of the canonical key strings: byte/codepoint order


SRC_NSC = (GOV / "nikasha_stale_certs.py").read_text(encoding="utf-8")


def test_dropping_the_python_row_sort_is_caught_by_the_order_independence_test():
    mutated = SRC_NSC.replace("    keyed.sort()\n", "    pass\n", 1)
    assert mutated != SRC_NSC
    mod = types.ModuleType("nsc_nosort")
    mod.__file__ = str(GOV / "nikasha_stale_certs.py")
    sys.modules["nsc_nosort"] = mod
    exec(compile(mutated, "<nsc_nosort>", "exec"), mod.__dict__)         # noqa: S102 - the repo's own source with one mutation
    decl = fd.load_declarations().table_declaration("bg_formula_constants", "brahma_formula_constants")
    assert _order_independent(mod, decl) is False


# ----- round 8: the projection of a recorded expected difference (the fingerprint WITHOUT its columns) -----

def _eph_rows(node_mode, epoch, n=6, speed_bump=None):
    rows = []
    for i in range(n):
        rows.append({"id": i + 1, "ayanamsha_id": "tropical", "body": "Rahu" if i % 2 else "Sun", "date": f"2026-01-{i + 1:02d}", "longitude": 10.5 + i, "latitude": 0.1 * i,
                     "speed_dps": (1.0 + i) + (speed_bump if speed_bump and i == 2 else 0), "computed_at": f"2026-10-0{i + 1}T00:00:00+00:00",
                     "node_mode": node_mode, "epoch_convention": epoch, "source_citation": "pyswisseph"})
    return rows


def test_the_projection_declaration_ignores_exactly_the_recorded_columns(tmp_path):
    d = _decl_with_ed(tmp_path)
    full = d.table_declaration("bg_ephemeris", "ephemeris_daily")
    proj = d.projection_declaration("bg_ephemeris", "ephemeris_daily")
    assert proj["volatile_columns"] == full["volatile_columns"] + ["node_mode", "epoch_convention"] and proj["natural_key"] == full["natural_key"]
    assert full["volatile_columns"] == ["id", "computed_at"]                                      # the full declaration still fingerprints the two columns
    key = full["natural_key"]
    a, b = _eph_rows("true", "noon_ut"), _eph_rows(None, None)
    assert nsc.fingerprint_rows(a, full) != nsc.fingerprint_rows(b, full)                         # the recorded difference moves the full fingerprint
    assert nsc.fingerprint_rows(a, proj) == nsc.fingerprint_rows(b, proj)                         # and only that: the projection is equal
    other = _eph_rows(None, None, speed_bump=0.5)                                                  # something ELSE changed as well (speed_dps)
    assert nsc.fingerprint_rows(other, proj) != nsc.fingerprint_rows(a, proj)
    assert nsc.fingerprint_rows(_eph_rows(None, None, n=5), proj) != nsc.fingerprint_rows(b, proj)  # a missing row moves the projection too
    assert nsc.fingerprint_rows([], proj) == fd.empty_projection_fingerprint(d, "bg_ephemeris", "ephemeris_daily") != fd.empty_table_fingerprint(d, "bg_ephemeris", "ephemeris_daily")
    assert key and d.projection_tables() == {"bg_ephemeris": "ephemeris_daily"}
    with pytest.raises(fd.DeclarationError):
        d.projection_declaration("bg_nakshatra", "nakshatra")                                      # a table with no recorded difference has no projection


def test_a_unit_fingerprint_over_a_connection_reports_the_projection_from_the_same_rows(monkeypatch, tmp_path):
    d = _decl_with_ed(tmp_path)
    rows = _eph_rows("true", "noon_ut")
    fake = types.SimpleNamespace(load_rows=lambda conn, decl, chart, **kw: rows if decl["table"] == "ephemeris_daily" else [], fingerprint_rows=nsc.fingerprint_rows, validate_declaration=nsc.validate_declaration)
    monkeypatch.setattr(fd, "_e55", lambda: fake)                                                   # no database: the rows come from the stub, the hashing is E5.5's
    r = fd.unit_fingerprint(None, d, "bg_ephemeris")
    o = fd.unit_fingerprints(None, d, ["bg_ephemeris"])
    assert r["projections"]["ephemeris_daily"] == {"sha256": nsc.fingerprint_rows(rows, d.projection_declaration("bg_ephemeris", "ephemeris_daily")), "rows": 6}
    assert r["tables"]["ephemeris_daily"]["rows"] == 6 and r["projections"]["ephemeris_daily"]["sha256"] != r["tables"]["ephemeris_daily"]["sha256"]
    assert o["projections"] == {"bg_ephemeris": r["projections"]}
    assert fd.unit_fingerprints(None, d, ["bg_nakshatra"])["projections"] == {}                      # a unit with no recorded difference has none


# ----- round 9 (N-135): horizon_date_column, the horizon block and its computation in the reader's streaming pass -----

import datetime as _dt


def _cal_rows(n=6, start=1, jd0=0, tz=None):
    return [{"event_type": "x", "primary_body": "s", "secondary_body_key": "", "event_jd": float(jd0 + i), "id": i, "computed_at": "2026-10-01T00:00:00+00:00", "build_id": "b",
             "event_datetime_utc": _dt.datetime(2026, 1, start + i, 3, 0, 0, tzinfo=tz)} for i in range(n)]


def test_horizon_date_columns_are_declared_for_exactly_the_rolling_horizon_units_and_validated():
    d = fd.load_declarations()
    assert d.horizon_tables() == {"bg_muhurta_lattice": {"table": "bg_muhurta_lattice", "date_column": "start_utc"},
                                  "bg_sky_calendar": {"table": "bg_sky_calendar", "date_column": "event_datetime_utc"}}
    assert [u for u, v in d.units().items() if "rolling_horizon" in v["reproducibility"]] == list(d.horizon_tables())
    assert "horizon_date_column" in fd.TABLE_KEYS and "horizon_date_column" not in fd.TABLE_REQUIRED
    carriers = [a for a, v in DOC["assets"].items() if v["status"] == "declared" for t in v["tables"] if "horizon_date_column" in t]
    assert carriers == ["bg_muhurta_lattice", "bg_sky_calendar"]

    def run(edit):
        doc = copy.deepcopy(DOC)
        edit(doc)
        return [(p[0], p[2]) for p in fd.validate(doc, registry=REG, schema=EXT, repo_root=REPO)]
    sky = lambda doc: doc["assets"]["bg_sky_calendar"]["tables"][0]  # noqa: E731
    assert run(lambda doc: None) == []
    assert [c for c, _ in run(lambda doc: sky(doc).update(horizon_date_column="computed_at"))] == ["bad_horizon_column"]            # timestamptz
    assert [c for c, _ in run(lambda doc: sky(doc).update(horizon_date_column="event_jd"))] == ["bad_horizon_column"]               # not a date
    assert [c for c, _ in run(lambda doc: sky(doc).update(horizon_date_column="no_such_col"))] == ["bad_horizon_column"]
    assert [c for c, _ in run(lambda doc: sky(doc).update(horizon_date_column="Bad Col"))] == ["bad_horizon_column"]
    assert [c for c, _ in run(lambda doc: sky(doc).pop("horizon_date_column"))] == ["horizon_column_required"]
    assert "horizon_on_non_rolling" in [c for c, _ in run(lambda doc: doc["assets"]["bg_nakshatra"]["tables"][0].update(horizon_date_column="created_at"))]
    assert [c for c, _ in run(lambda doc: sky(doc).update(naive_utc_columns=[]))] == ["bad_horizon_column"] or "bad_horizon_column" in [c for c, _ in run(lambda doc: sky(doc).update(naive_utc_columns=[]))]


def _horizon_invariants(m) -> list[str]:
    """The behaviours of the horizon computation, checked against module `m` (the real one, or a mutant); a crash outside a single check is itself a failure."""
    try:
        return _horizon_invariants_inner(m)
    except Exception as exc:                                               # noqa: BLE001
        return [f"crashed: {type(exc).__name__}"]


def _horizon_invariants_inner(m) -> list[str]:
    bad: list[str] = []

    def check(name, cond):
        try:
            ok = bool(cond())
        except Exception:                                                  # noqa: BLE001 - a crash is a failed invariant
            ok = False
        if not ok:
            bad.append(name)
    decl = fd.load_declarations().table_declaration("bg_sky_calendar", "bg_sky_calendar")
    nsc_m = nsc
    prod = _cal_rows(6)
    pb = m.horizon_block(prod, decl, "event_datetime_utc")
    check("own_cutoff_is_max", lambda: pb["overlap_cutoff"] == pb["max_date"] == "2026-01-06T03:00:00.000000" and pb["min_date"] == "2026-01-01T03:00:00.000000")
    check("counts", lambda: pb["rows"] == 6 and pb["overlap_rows"] == 6)
    check("whole_overlap_equals_table_fingerprint", lambda: pb["overlap_sha256"] == nsc_m.fingerprint_rows(prod, decl))
    check("block_keys", lambda: tuple(pb) == m.HORIZON_BLOCK_KEYS)
    reh = _cal_rows(9)                                                     # the same 6 rows + 3 rows after the production horizon
    rb = m.horizon_block(reh, decl, "event_datetime_utc", pb["max_date"])
    check("overlap_cut_at_production_max", lambda: rb["overlap_cutoff"] == pb["max_date"] and rb["overlap_rows"] == 6 and rb["rows"] == 9 and rb["max_date"] == "2026-01-09T03:00:00.000000")
    check("overlap_equal_when_only_extras", lambda: rb["overlap_sha256"] == pb["overlap_sha256"])
    check("cutoff_is_inclusive", lambda: m.horizon_block(reh, decl, "event_datetime_utc", "2026-01-06T03:00:00.000000")["overlap_rows"] == 6
          and m.horizon_block(reh, decl, "event_datetime_utc", "2026-01-06T02:59:59.999999")["overlap_rows"] == 5)
    changed = _cal_rows(9)
    changed[2]["event_jd"] = 99.5                                           # a SHARED row differs (and the key differs): the overlap fingerprint moves
    check("overlap_moves_with_a_shared_row", lambda: m.horizon_block(changed, decl, "event_datetime_utc", pb["max_date"])["overlap_sha256"] != pb["overlap_sha256"])
    missing = _cal_rows(9)[:2] + _cal_rows(9)[3:]                           # a shared row is missing in the rehearsal
    check("overlap_rows_moves_with_a_missing_row", lambda: m.horizon_block(missing, decl, "event_datetime_utc", pb["max_date"])["overlap_rows"] == 5)
    check("extras_never_enter_the_overlap", lambda: m.horizon_block(reh + _cal_rows(2, start=20, jd0=50), decl, "event_datetime_utc", pb["max_date"])["overlap_sha256"] == pb["overlap_sha256"])
    check("null_cutoff_means_empty_overlap", lambda: m.horizon_block(reh, decl, "event_datetime_utc", None)["overlap_rows"] == 0
          and m.horizon_block(reh, decl, "event_datetime_utc", None)["overlap_cutoff"] is None
          and m.horizon_block(reh, decl, "event_datetime_utc", None)["overlap_sha256"] == nsc_m.fingerprint_rows([], decl))
    eb = m.horizon_block([], decl, "event_datetime_utc")
    check("empty_table", lambda: eb["rows"] == 0 and eb["min_date"] is None and eb["max_date"] is None and eb["overlap_cutoff"] is None and eb["overlap_rows"] == 0
          and eb["overlap_sha256"] == nsc_m.fingerprint_rows([], decl))
    check("bad_cutoff_refused", lambda: _raises(m.DeclarationError, lambda: m.horizon_block(reh, decl, "event_datetime_utc", "yesterday")))
    check("tz_aware_refused", lambda: _raises(m.DeclarationError, lambda: m.horizon_block(_cal_rows(2, tz=_dt.timezone.utc), decl, "event_datetime_utc")))
    check("null_date_refused", lambda: _raises(m.DeclarationError, lambda: m.horizon_block([{**_cal_rows(1)[0], "event_datetime_utc": None}], decl, "event_datetime_utc")))
    check("missing_column_refused", lambda: _raises(m.DeclarationError, lambda: m.horizon_block(_cal_rows(1), decl, "no_such_column")))
    check("string_dates_normalised", lambda: m.horizon_iso("2026-01-02T03:04:05") == "2026-01-02T03:04:05.000000" and m.horizon_iso("2026-01-02 03:04:05.5") == "2026-01-02T03:04:05.500000"
          and m.horizon_iso("2026-01-02") == "2026-01-02" and m.horizon_iso(_dt.date(2026, 1, 2)) == "2026-01-02")
    check("iso_refusals", lambda: _raises(m.DeclarationError, lambda: m.horizon_iso(_dt.datetime(2026, 1, 1, tzinfo=_dt.timezone.utc))) and _raises(m.DeclarationError, lambda: m.horizon_iso(None))
          and _raises(m.DeclarationError, lambda: m.horizon_iso(20260101)) and _raises(m.DeclarationError, lambda: m.horizon_iso("not a date")))
    check("fixed_width_order", lambda: m.horizon_iso(_dt.datetime(2026, 1, 2, 3, 0, 0)) < m.horizon_iso(_dt.datetime(2026, 1, 2, 3, 0, 0, 5)))
    check("iso_ok", lambda: m.horizon_iso_ok("2026-01-02") and m.horizon_iso_ok("2026-01-02T03:04:05.000001") and not m.horizon_iso_ok("2026-13-45") and not m.horizon_iso_ok("2026-01-02T03:04:05")
          and not m.horizon_iso_ok(None) and not m.horizon_iso_ok(20260102) and not m.horizon_iso_ok("2026-1-2")
          and not m.horizon_iso_ok("2026-13-45T03:04:05.000000") and not m.horizon_iso_ok("2026-01-02T25:04:05.000000"))
    d = m.Declarations(doc=copy.deepcopy(DOC), sha256="9" * 64) if hasattr(m, "Declarations") else None
    check("horizon_tables", lambda: d.horizon_tables()["bg_sky_calendar"] == {"table": "bg_sky_calendar", "date_column": "event_datetime_utc"} and list(d.horizon_tables()) == ["bg_muhurta_lattice", "bg_sky_calendar"])
    fake = types.SimpleNamespace(load_rows=lambda conn, decl_, chart, **kw: prod if decl_["table"] == "bg_sky_calendar" else [], fingerprint_rows=nsc.fingerprint_rows,
                                 validate_declaration=nsc.validate_declaration)
    orig = m._e55
    m._e55 = lambda: fake
    try:
        r = m.unit_fingerprint(None, d, "bg_sky_calendar", horizon_cutoff="2026-01-04T03:00:00.000000")
        o = m.unit_fingerprints(None, d, ["bg_sky_calendar", "bg_nakshatra"], horizon_cutoffs={"bg_sky_calendar": "2026-01-03T03:00:00.000000"})
        own = m.unit_fingerprint(None, d, "bg_sky_calendar")
    finally:
        m._e55 = orig
    check("unit_horizon_cutoff", lambda: r["horizons"]["bg_sky_calendar"]["overlap_rows"] == 4 and r["horizons"]["bg_sky_calendar"]["rows"] == 6)
    check("unit_horizon_same_rows", lambda: r["tables"]["bg_sky_calendar"]["rows"] == 6 and own["horizons"]["bg_sky_calendar"]["overlap_sha256"] == own["tables"]["bg_sky_calendar"]["sha256"])
    check("units_horizon_cutoffs_by_unit", lambda: o["horizons"]["bg_sky_calendar"]["bg_sky_calendar"]["overlap_rows"] == 3 and "bg_nakshatra" not in o["horizons"])
    return bad


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def test_the_horizon_computation_holds_every_invariant():
    assert _horizon_invariants(fd) == []


@pytest.mark.parametrize("old,new", [
    ('    cut = mx if cutoff is _OWN_MAX else cutoff', '    cut = mx'),
    ('    cut = mx if cutoff is _OWN_MAX else cutoff', '    cut = cutoff'),
    ('    over = [r for r, i in zip(rows, isos) if cut is not None and i <= cut]', '    over = [r for r, i in zip(rows, isos) if cut is not None and i < cut]'),
    ('    over = [r for r, i in zip(rows, isos) if cut is not None and i <= cut]', '    over = list(rows)'),
    ('    over = [r for r, i in zip(rows, isos) if cut is not None and i <= cut]', '    over = [r for r, i in zip(rows, isos) if i <= (cut or "9")]'),
    ('"overlap_sha256": _e55().fingerprint_rows(over, decl)}', '"overlap_sha256": _e55().fingerprint_rows(rows, decl)}'),
    ('    mn, mx = (min(isos), max(isos)) if isos else (None, None)', '    mn, mx = (max(isos), min(isos)) if isos else (None, None)'),
    ('    if cut is not None and not horizon_iso_ok(cut):', '    if False:'),
    ('        if v.tzinfo is not None:\n            raise DeclarationError', '        if False:\n            raise DeclarationError'),
    ('        return v.isoformat(timespec="microseconds")', '        return v.isoformat()'),
    ('    raise DeclarationError([("bad_horizon_value", where, f"the horizon column holds {v!r}', '    return str(v)\n    raise DeclarationError([("bad_horizon_value", where, f"the horizon column holds {v!r}'),
    ('        if isinstance(v, str) and _ISO_DATE.fullmatch(v):\n            return dt.date.fromisoformat(v).isoformat() == v', '        if isinstance(v, str) and _ISO_DATE.fullmatch(v):\n            return True'),
    ('            return dt.datetime.fromisoformat(v).isoformat(timespec="microseconds") == v', '            return True'),
    ('            out.setdefault("horizons", {})[table] = horizon_block(rows, decl, ht["date_column"], horizon_cutoff)', '            out.setdefault("horizons", {})[table] = horizon_block(rows, decl, ht["date_column"])'),
    ('        r = unit_fingerprint(conn, decls, u, horizon_cutoff=cuts[u] if u in cuts else _OWN_MAX, **kw)', '        r = unit_fingerprint(conn, decls, u, **kw)'),
    ('        if r.get("horizons"):\n            hzs[u] = r["horizons"]', '        if False:\n            hzs[u] = r["horizons"]'),
    ('            if "rolling_horizon" in v["reproducibility"]:\n                hit =', '            if False:\n                hit ='),
], ids=lambda x: None)
def test_horizon_source_mutants_are_caught(old, new):
    assert SRC_FD.count(old) == 1, f"the mutant target is absent or not unique: {old!r}"
    mod = load_module(SRC_FD.replace(old, new, 1), "fd_hz_mut_" + str(abs(hash(old + new)) % 10**8))
    assert _horizon_invariants(mod), f"SURVIVING MUTANT: {old!r} -> {new!r}"


# ----- round 11 (speed): `Declarations._unit` builds ONE unit, from the same helpers as `units()` -----

def _old_unit(d, unit):
    """What `_unit` did before: rebuild the dict of ALL units and look one up."""
    u = d.units().get(unit)
    if u is None:
        raise fd.DeclarationError([("unknown_asset", unit, "not a comparison unit (a declared asset with tables, or a group)")])
    return u


def _unit_outcome(fn):
    try:
        return ("ok", fn())
    except fd.DeclarationError as exc:
        return ("err", [tuple(x) for x in exc.problems])


def _unit_invariants(m, decls_list) -> list[str]:
    bad: list[str] = []

    def check(name, cond):
        try:
            ok = bool(cond())
        except Exception:                                                  # noqa: BLE001 - a crash is a failed invariant
            ok = False
        if not ok:
            bad.append(name)
    for tag, d in decls_list:
        probes = sorted(set(d.assets) | {d.group_unit(g) for g in d.groups} | set(d.units()) | {"nope", "", "grp_", "grp_nope", "grp_" + "x" * 5, "GRP_x", "bg_"})
        check(f"{tag}:every_unit_equals_the_units_entry", lambda d=d: all(d._unit(u) == d.units()[u] for u in d.units()) and len(d.units()) > 0)
        check(f"{tag}:same_outcome_for_every_probe", lambda d=d, probes=probes: all(_unit_outcome(lambda u=u: d._unit(u)) == _unit_outcome(lambda u=u: _old_unit(d, u)) for u in probes))
        check(f"{tag}:unknown_raises_the_same_error", lambda d=d: _unit_outcome(lambda: d._unit("nope")) == ("err", [("unknown_asset", "nope", "not a comparison unit (a declared asset with tables, or a group)")]))
        check(f"{tag}:undeclared_asset_raises", lambda d=d: all(_unit_outcome(lambda a=a: d._unit(a))[0] == "err" for a in d.undeclared_assets()))
        check(f"{tag}:asset_without_tables_raises", lambda d=d: all(_unit_outcome(lambda a=a: d._unit(a))[0] == "err" for a in d.declared_assets() if not d.assets[a]["tables"]))
        check(f"{tag}:bad_group_id_raises", lambda d=d: all(_unit_outcome(lambda g=g: d._unit(g))[0] == "err" for g in ("grp_nope", "grp_", "grp_" + "z" * 40)))
        check(f"{tag}:group_prefix_alone_is_not_a_unit", lambda d=d: _unit_outcome(lambda: d._unit(fd.GROUP_PREFIX))[0] == "err")
        check(f"{tag}:tables_and_reproducibility_follow", lambda d=d: all(d.tables(u) == d.units()[u]["tables"] and d.reproducibility(u) == d.units()[u]["reproducibility"] for u in d.units()))
        check(f"{tag}:unit_dicts_are_independent_copies", lambda d=d: d._unit(next(iter(d.units())))["members"] is not d._unit(next(iter(d.units())))["members"])
    check("helpers_are_shared", lambda: all(hasattr(m.Declarations, h) for h in ("_asset_unit", "_group_unit")))
    return bad


def _unit_cases():
    real = fd.load_declarations()
    syn = fd.Declarations(doc=copy.deepcopy(SYN_DOC), sha256="9" * 64)
    return [("real", real), ("syn", syn)]


def test_unit_builds_one_unit_and_matches_units_for_every_unit_and_raises_the_same_errors():
    assert _unit_invariants(fd, _unit_cases()) == []
    real = fd.load_declarations()
    assert len(real.units()) == 32 and any(not real.assets[a]["tables"] for a in real.declared_assets()) and real.undeclared_assets() and real.groups
    # `_unit` never rebuilds the dict of all units
    calls = []
    orig = fd.Declarations.units
    fd.Declarations.units = lambda self: calls.append(1) or orig(self)
    try:
        real._unit("bg_sky_calendar")
        real._unit("grp_brahma_ontology")
        real.tables("bg_sky_calendar")
        real.table_declaration("bg_sky_calendar", "bg_sky_calendar")
    finally:
        fd.Declarations.units = orig
    assert calls == []


@pytest.mark.parametrize("old,new", [
    ('        if isinstance(unit, str) and unit.startswith(GROUP_PREFIX) and unit[len(GROUP_PREFIX):] in self.groups:', '        if False:'),
    ('        if isinstance(unit, str) and unit.startswith(GROUP_PREFIX) and unit[len(GROUP_PREFIX):] in self.groups:', '        if isinstance(unit, str) and unit.startswith(GROUP_PREFIX):'),
    ('        elif unit in self.assets and self.assets[unit]["status"] == "declared":', '        elif unit in self.assets:'),
    ('        elif unit in self.assets and self.assets[unit]["status"] == "declared":', '        elif False:'),
    ('        if not d["tables"]:\n            return None', '        if False:\n            return None'),
    ('"reproducibility": list(g["reproducibility"]),\n                "seeded": bool(g["seeded"])}', '"reproducibility": list(g["reproducibility"]),\n                "seeded": False}'),
    ('"members": [a], "tables": [t["name"] for t in d["tables"]], "reproducibility": list(d["reproducibility"]), "seeded": False}', '"members": [a], "tables": [t["name"] for t in d["tables"]][:1], "reproducibility": list(d["reproducibility"]), "seeded": False}'),
    ('            u = self._asset_unit(a)\n            if u is not None:\n                out[a] = u', '            out[a] = self._asset_unit(a)'),
    ('            raise DeclarationError([("unknown_asset", unit, "not a comparison unit (a declared asset with tables, or a group)")])\n        return u', '            return {"kind": "asset", "members": [unit], "tables": [], "reproducibility": ["deterministic"], "seeded": False}\n        return u'),
], ids=["no_group_branch", "group_prefix_without_membership", "undeclared_accepted", "no_asset_branch", "no_tables_accepted", "group_seeded_false", "tables_truncated", "units_keeps_none", "unknown_returns_a_unit"])
def test_unit_source_mutants_are_caught(old, new):
    assert SRC_FD.count(old) == 1, f"the mutant target is absent or not unique: {old!r}"
    mod = load_module(SRC_FD.replace(old, new, 1), "fd_unit_mut_" + str(abs(hash(old + new)) % 10**8))
    cases = [("real", mod.load_declarations()), ("syn", mod.Declarations(doc=copy.deepcopy(SYN_DOC), sha256="9" * 64))]
    assert _unit_invariants(mod, cases), f"SURVIVING MUTANT: {old!r} -> {new!r}"


def test_one_fingerprint_definition_everywhere():
    assert fd.FINGERPRINT_DEFINITION == sr.FINGERPRINT_DEFINITION == "nikasha_stale_certs.table_fingerprint/1"
    assert DOC["fingerprint_definition"] == fd.FINGERPRINT_DEFINITION
    assert all(d["fingerprint_definition"] == fd.FINGERPRINT_DEFINITION for d in DOC["assets"].values() if d["status"] == "declared")
    src = (GOV / "fingerprint_declarations.py").read_text(encoding="utf-8")
    assert "def fingerprint_rows" not in src and "def table_fingerprint" not in src       # the module defines no fingerprint of its own


def test_reproducibility_flags_are_the_known_ones():
    d = fd.load_declarations()
    assert d.non_deterministic() == {"bg_cohort": ["platform_bound"], "bg_muhurta_lattice": ["rolling_horizon"],
                                                       "bg_sky_calendar": ["rolling_horizon", "platform_bound"]}


def test_the_declarations_file_is_stable_json_with_no_duplicate_keys():
    text = fd.DEFAULT_DECLARATIONS.read_text(encoding="utf-8")
    assert fd.strict_loads(text) == DOC and text.endswith("\n")


# ═════════════════════════ 2. the mirror dump ═════════════════════════

def _declared_tables():
    out = []
    for a, d in DOC["assets"].items():
        if d["status"] == "declared":
            out += [(a, t) for t in d["tables"]]
    for g, v in DOC["groups"].items():
        out += [(f"grp_{g}", t) for t in v["tables"]]
    return out


def test_every_declared_table_and_excluded_column_exists_in_the_committed_extract():
    for a, t in _declared_tables():
        tab = EXT["tables"].get(t["name"])
        assert tab is not None, (a, t["name"])
        for e in t["exclude"]:
            assert e["column"] in tab["columns"], (a, t["name"], e["column"])
        for c in t["key"]:
            assert c in tab["columns"]


@needs_dump
def test_every_declared_table_exists_in_the_mirror_dump_and_every_excluded_column_is_in_its_body():
    text = MIRROR_DUMP.read_text(encoding="utf-8")
    for a, t in _declared_tables():
        assert re.search(rf"^CREATE TABLE public\.{re.escape(t['name'])} \(", text, re.M), (a, t["name"])
        body = fd.dump_table_body(text, t["name"])
        assert body is not None
        for e in t["exclude"]:
            assert re.search(rf'^\s+"?{re.escape(e["column"])}"? ', body, re.M), (a, t["name"], e["column"])
        for c in t["key"] + t["naive_utc_columns"]:
            assert re.search(rf'^\s+"?{re.escape(c)}"? ', body, re.M), (a, t["name"], c)
    for a, d in DOC["assets"].items():
        for n in d.get("not_covered_tables", []) + d.get("not_written_tables", []):
            assert fd.dump_table_body(text, n["name"]) is not None
        for n in d.get("tables_written", []):
            assert fd.dump_table_body(text, n) is not None
    assert EXT["table_names"] == sorted(fd.dump_table_names(text))


@needs_dump
def test_the_committed_schema_extract_is_exactly_what_the_dump_yields():
    text = MIRROR_DUMP.read_text(encoding="utf-8")
    seed_only = {"nirmana_bg_texts_integrity_baselines"}                  # round 7: a config-seed table (data-only extract entry, columns taken from the dump)
    again = fd.extract_schema(text, sorted(set(fd.tables_named(DOC)) | seed_only), dump_name="prod_schema.sql")
    assert again == EXT and set(EXT["tables"]) == set(fd.tables_named(DOC)) | seed_only
    assert DOC["source"]["schema_dump_sha256"] == EXT["source"]["sha256"] == fd.sha256_bytes(text.encode("utf-8"))


@needs_dump
def test_the_mirror_dump_is_schema_only():
    """Schema only: no COPY data block and no column-0 INSERT (the INSERT text in it sits inside function bodies)."""
    lines = MIRROR_DUMP.read_text(encoding="utf-8").split("\n")
    assert not [i for i, ln in enumerate(lines, 1) if ln.startswith("COPY ") or ln.startswith("INSERT INTO ")]


def test_registry_snapshot_hash_in_the_declarations_is_the_snapshots():
    assert DOC["source"]["registry_snapshot_sha256"] == fd.sha256_file(fd.DEFAULT_REGISTRY)
    assert (REPO / DOC["source"]["registry_snapshot"]).is_file()


def test_extract_schema_parses_columns_keys_and_identity_on_a_synthetic_dump():
    dump = (
        "CREATE TABLE public.t_a (\n    id integer NOT NULL,\n    k text NOT NULL,\n    v numeric(9,6) NOT NULL,\n"
        "    ts timestamp without time zone,\n    created_at timestamp with time zone DEFAULT now() NOT NULL,\n"
        "    u uuid DEFAULT gen_random_uuid() NOT NULL,\n    g text GENERATED ALWAYS AS (COALESCE(k, ''::text)) STORED,\n"
        "    CONSTRAINT t_a_chk CHECK ((v > 0))\n);\n\n"
        "ALTER TABLE public.t_a ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (\n    SEQUENCE NAME public.t_a_id_seq\n);\n"
        "ALTER TABLE ONLY public.t_a\n    ADD CONSTRAINT t_a_pkey PRIMARY KEY (id);\n"
        "ALTER TABLE ONLY public.t_a\n    ADD CONSTRAINT t_a_k_key UNIQUE (k);\n"
        "CREATE UNIQUE INDEX t_a_part ON public.t_a USING btree (v) WHERE (v > 1);\n"
        "CREATE UNIQUE INDEX t_a_plain ON public.t_a USING btree (k, v);\n")
    e = fd.extract_schema(dump, ["t_a"])
    t = e["tables"]["t_a"]
    assert t["primary_key"] == ["id"] and t["primary_key_name"] == "t_a_pkey"
    assert t["columns"]["id"]["identity"] and t["columns"]["u"]["identity"] and not t["columns"]["k"]["identity"]
    assert t["columns"]["ts"] == {"type": "timestamp without time zone", "not_null": False, "default": None, "generated": False, "identity": False}
    assert t["columns"]["v"]["type"] == "numeric(9,6)" and t["columns"]["g"]["generated"] is True
    assert t["columns"]["created_at"]["default"] == "now()"
    assert [u["name"] for u in t["unique"]] == ["t_a_k_key", "t_a_plain"] and t["unique"][1]["columns"] == ["k", "v"]
    assert [u["name"] for u in t["unique_other"]] == ["t_a_part"]
    with pytest.raises(fd.DeclarationError):
        fd.extract_schema(dump, ["t_missing"])


# ═════════════════════════ 3. refusals (one mutation each, table-driven) ═════════════════════════

def _t(doc, asset, name=None):
    tabs = doc["assets"][asset]["tables"]
    return tabs[0] if name is None else next(t for t in tabs if t["name"] == name)


# The committed declarations carry no expected-difference record any more (#3015 is on main), but the MECHANISM stays: a record on a table says which
# columns a known, tracked difference is limited to. These tests exercise it on a synthetic record.
SYN_ED = {"columns": ["node_mode", "epoch_convention"], "reference": "synthetic tracked change (test fixture)",
          "detail": "a synthetic known difference limited to the two columns, used to exercise the expected-difference mechanism in tests",
          "until": "the synthetic tracked change is merged: remove this record"}


def _install_ed(doc):
    t = _t(doc, "bg_ephemeris", "ephemeris_daily")
    t["expected_difference"] = copy.deepcopy(SYN_ED)
    return t


def _decl_with_ed(tmp_path):
    doc = copy.deepcopy(DOC)
    _install_ed(doc)
    f = tmp_path / "decl_with_ed.json"
    f.write_text(json.dumps(doc), encoding="utf-8")
    return fd.load_declarations(f)


def _ex_append(code, col, asset="bg_medical_mappings"):
    return lambda x: _t(x, asset)["exclude"].append({"column": col, "reason_code": code, "reason": "r" * 30})


def _del_reason(x):
    del _t(x, "bg_medical_mappings")["exclude"][0]["reason"]


def _nullable_schema(sch):
    sch["tables"]["bg_medical_mappings"]["columns"]["graha"]["not_null"] = False


MP = "platform/python-sidecar/brahmagyan/l0_medical.py"
# (id, expected problem code, mutator of the DOC | None, mutator of the schema extract | None)
REFUSALS = [
    ("unknown_asset", "unknown_asset", lambda x: x["assets"].update({"bg_not_an_asset": copy.deepcopy(x["assets"]["bg_sign_medical"])}), None),
    ("missing_asset", "missing_asset", lambda x: x["assets"].pop("bg_sign_medical"), None),
    ("unknown_top_key", "unknown_key", lambda x: x.update({"extra": 1}), None),
    ("missing_top_key", "missing_key", lambda x: x.pop("source"), None),
    ("unknown_asset_key", "unknown_key", lambda x: x["assets"]["bg_sign_medical"].update({"x": 1}), None),
    ("unknown_table_key", "unknown_key", lambda x: _t(x, "bg_sign_medical").update({"x": 1}), None),
    ("unknown_exclude_key", "unknown_key", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"x": 1}), None),
    ("undeclared_with_tables_key", "unknown_key", lambda x: x["assets"]["bg_panchanga"].update({"tables": []}), None),
    ("unknown_table", "unknown_table", lambda x: _t(x, "bg_sign_medical").update({"name": "no_such_table"}), None),
    ("unknown_table_written", "unknown_table", lambda x: x["assets"]["bg_compendium_index"]["tables_written"].append("no_such_table"), None),
    ("unknown_table_not_covered", "unknown_table", lambda x: x["assets"]["bg_remedies"]["not_covered_tables"][0].update({"name": "no_such_table"}), None),
    ("unknown_key_column", "unknown_column", lambda x: _t(x, "bg_medical_mappings").update({"key": ["no_such_col"]}), None),
    ("unknown_exclude_column", "unknown_column", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"column": "no_such_col"}), None),
    ("unknown_naive_column", "unknown_column", lambda x: _t(x, "bg_medical_mappings").update({"naive_utc_columns": ["no_such_col"]}), None),
    ("duplicate_key_column", "key_duplicate_column", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key": ["scheme_name", "scheme_name"]}), None),
    ("key_not_a_constraint", "key_not_unique_in_schema", lambda x: _t(x, "bg_medical_mappings").update({"key": ["classical_citation"]}), None),
    ("key_proper_subset", "key_not_unique_in_schema", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key": ["scheme_name"]}), None),
    ("key_evidence_unknown_constraint", "key_not_unique_in_schema", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key_evidence": "unique:no_such_constraint"}), None),
    ("key_evidence_other_columns", "key_not_unique_in_schema", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key_evidence": "primary_key:bg_avastha_schemes_pkey"}), None),
    ("key_evidence_malformed", "bad_key_evidence", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key_evidence": "somewhere"}), None),
    ("nullable_key", "key_nullable", None, _nullable_schema),
    ("excluded_key_column", "exclude_key", _ex_append("surrogate_identity", "graha"), None),
    ("exclude_reason_deleted", "exclude_no_reason", _del_reason, None),
    ("exclude_reason_blank", "exclude_no_reason", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason": "   "}), None),
    ("exclude_reason_null", "exclude_no_reason", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason": None}), None),
    ("exclude_reason_short", "exclude_reason_short", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason": "volatile"}), None),
    ("exclude_unknown_code", "exclude_bad_reason_code", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason_code": "because"}), None),
    ("exclude_identity_unfit", "exclude_reason_unfit", _ex_append("surrogate_identity", "classical_citation"), None),
    ("exclude_timestamp_unfit", "exclude_reason_unfit", _ex_append("wall_clock_timestamp", "classical_citation"), None),
    ("exclude_build_unfit", "exclude_reason_unfit", _ex_append("build_identity", "classical_citation"), None),
    ("exclude_twice", "exclude_duplicate", lambda x: _t(x, "bg_medical_mappings")["exclude"].append(copy.deepcopy(_t(x, "bg_medical_mappings")["exclude"][0])), None),
    ("table_claimed_by_two_assets", "duplicate_table_claim", lambda x: x["assets"]["bg_nakshatra_medical"]["tables"].append(copy.deepcopy(_t(x, "bg_sign_medical"))), None),
    ("declared_table_also_written_elsewhere", "duplicate_table_claim", lambda x: x["assets"]["bg_compendium_index"]["tables_written"].append("bg_sign_medical"), None),
    ("declared_and_not_covered", "duplicate_table_claim", lambda x: x["assets"]["bg_remedies"]["not_covered_tables"][0].update({"name": "brahma_remedy_corpus"}), None),
    ("naive_not_declared", "naive_utc_missing", lambda x: _t(x, "bg_muhurta_lattice").update({"naive_utc_columns": ["start_utc"]}), None),
    ("naive_not_declared_sky", "naive_utc_missing", lambda x: _t(x, "bg_sky_calendar").update({"naive_utc_columns": []}), None),
    ("naive_on_a_non_naive_column", "bad_naive_utc", lambda x: _t(x, "bg_medical_mappings").update({"naive_utc_columns": ["graha"]}), None),
    ("write_evidence_empty", "evidence_missing", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": []}), None),
    ("write_evidence_no_file", "evidence_untracked", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["platform/python-sidecar/brahmagyan/no_such.py:3"]}), None),
    ("write_evidence_no_line", "evidence_missing", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"{MP}:99999999"]}), None),
    ("write_evidence_other_table", "evidence_missing", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py:5"]}), None),
    ("write_evidence_no_line_number", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["l0_medical.py"]}), None),
    ("write_evidence_absolute", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["/etc/passwd:1"]}), None),
    ("write_evidence_dotdot", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["../x.py:1"]}), None),
    ("write_evidence_line_zero", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"{MP}:0"]}), None),
    ("undeclared_reason_short", "undeclared_reason", lambda x: x["assets"]["bg_panchanga"].update({"reason": "service"}), None),
    ("undeclared_reason_code", "undeclared_reason", lambda x: x["assets"]["bg_panchanga"].update({"reason_code": "whatever"}), None),
    ("undeclared_reason_code_missing", "missing_key", lambda x: x["assets"]["bg_panchanga"].pop("reason_code"), None),
    ("undeclared_no_evidence", "evidence_missing", lambda x: x["assets"]["bg_compendium_index"].update({"evidence": []}), None),
    ("undeclared_reason_empty", "undeclared_reason", lambda x: x["assets"]["bg_compendium_index"].update({"reason": ""}), None),
    ("partial_without_not_covered", "partial_mismatch", lambda x: x["assets"]["bg_remedies"].update({"coverage": "full"}), None),
    ("full_with_not_covered", "partial_mismatch", lambda x: x["assets"]["bg_sign_medical"].update({"coverage": "partial"}), None),
    ("not_covered_reason_short", "undeclared_reason", lambda x: x["assets"]["bg_remedies"]["not_covered_tables"][0].update({"reason": "queue"}), None),
    ("top_definition", "bad_definition", lambda x: x.update({"fingerprint_definition": "other/1"}), None),
    ("asset_definition", "bad_definition", lambda x: x["assets"]["bg_sign_medical"].update({"fingerprint_definition": "other/1"}), None),
    ("schema_id", "bad_schema_id", lambda x: x.update({"schema": "other/v1"}), None),
    ("asset_scope", "bad_scope", lambda x: x["assets"]["bg_sign_medical"].update({"scope": "chart"}), None),
    ("table_scope", "bad_scope", lambda x: _t(x, "bg_sign_medical").update({"scope": "chart"}), None),
    ("status", "bad_status", lambda x: x["assets"]["bg_sign_medical"].update({"status": "maybe"}), None),
    ("reproducibility_value", "bad_reproducibility", lambda x: x["assets"]["bg_sign_medical"].update({"reproducibility": ["sometimes"]}), None),
    ("reproducibility_mixed", "bad_reproducibility", lambda x: x["assets"]["bg_sign_medical"].update({"reproducibility": ["deterministic", "rolling_horizon"]}), None),
    ("coverage_value", "bad_coverage", lambda x: x["assets"]["bg_sign_medical"].update({"coverage": "most"}), None),
    ("empty_tables", "empty_tables", lambda x: x["assets"]["bg_sign_medical"].update({"tables": []}), None),
    ("registry_table_unaccounted", "registry_table_unaccounted",
     lambda x: _t(x, "bg_sign_medical").update({"name": "bg_nakshatra_medical", "key": ["nakshatra_name"], "key_evidence": "unique:bg_nakshatra_medical_nakshatra_name_key",
                                                "write_evidence": [f"{MP}:454"]}), None),
    ("undeclared_registry_table_unaccounted", "registry_table_unaccounted", lambda x: x["assets"]["bg_compendium_index"].update({"tables_written": []}), None),
    # ── round 2: groups, embedding, expected difference, machine checks on exclusions, coverage, evidence statement ──
    ("group_table_also_an_asset_table", "duplicate_table_claim",
     lambda x: x["assets"]["bg_dasha_systems"]["tables"].append(copy.deepcopy(x["groups"]["brahma_ontology"]["tables"][0])), None),
    ("same_table_in_two_groups", "duplicate_table_claim", lambda x: x["groups"].update({"brahma_ontology_b": copy.deepcopy(x["groups"]["brahma_ontology"])}), None),
    ("group_with_one_member", "group_too_small", lambda x: x["groups"]["brahma_class_priors"]["members"].pop("bg_class_priors"), None),
    ("member_does_not_list_its_group", "group_member_mismatch", lambda x: x["assets"]["bg_ontology"].update({"groups": []}), None),
    ("asset_names_a_group_it_is_not_in", "group_member_mismatch", lambda x: x["assets"]["bg_sign_medical"].update({"groups": ["brahma_ontology"]}), None),
    ("asset_names_an_unknown_group", "group_member_mismatch", lambda x: x["assets"]["bg_sign_medical"].update({"groups": ["no_such_group"]}), None),
    ("group_member_is_undeclared", "group_member_mismatch",
     lambda x: x["groups"]["brahma_ontology"]["members"].update({"bg_compendium_index": copy.deepcopy(x["groups"]["brahma_ontology"]["members"]["bg_ontology"])}), None),
    ("group_id_is_an_asset_id", "bad_group", lambda x: x["groups"].update({"bg_sign_medical": copy.deepcopy(x["groups"]["brahma_ontology"])}), None),
    ("group_without_tables", "bad_group", lambda x: x["groups"]["brahma_ontology"].update({"tables": []}), None),
    ("group_member_without_evidence", "evidence_missing", lambda x: x["groups"]["brahma_ontology"]["members"].update({"bg_ontology": []}), None),
    ("group_member_evidence_names_no_group_table", "evidence_missing",
     lambda x: x["groups"]["brahma_ontology"]["members"].update({"bg_ontology": ["platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py:155"]}), None),
    ("group_bad_reproducibility", "bad_reproducibility", lambda x: x["groups"]["brahma_ontology"].update({"reproducibility": ["never"]}), None),
    ("partial_ownership_wrong_code", "bad_partial_ownership", lambda x: _t(x, "bg_formula_constants")["partial_ownership"].update({"reason_code": "other"}), None),
    ("partial_ownership_short_detail", "bad_partial_ownership", lambda x: _t(x, "bg_formula_constants")["partial_ownership"].update({"detail": "short"}), None),
    ("partial_ownership_no_evidence", "evidence_missing", lambda x: _t(x, "bg_formula_constants")["partial_ownership"].update({"evidence": []}), None),
    ("partial_ownership_evidence_names_another_table", "evidence_missing",
     lambda x: _t(x, "bg_formula_constants")["partial_ownership"].update({"evidence": ["platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py:155"]}), None),
    ("partial_ownership_unknown_key", "unknown_key", lambda x: _t(x, "bg_formula_constants")["partial_ownership"].update({"x": 1}), None),
    ("partial_ownership_missing_key", "missing_key", lambda x: _t(x, "bg_formula_constants")["partial_ownership"].pop("detail"), None),
    ("group_seeded_not_a_bool", "bad_seeded", lambda x: x["groups"]["classical_text_chunks"].update({"seeded": "yes"}), None),
    ("group_seeded_null", "bad_seeded", lambda x: x["groups"]["brahma_ontology"].update({"seeded": None}), None),
    ("group_seeded_missing", "missing_key", lambda x: x["groups"]["brahma_ontology"].pop("seeded"), None),
    ("group_unknown_key", "unknown_key", lambda x: x["groups"]["brahma_ontology"].update({"x": 1}), None),
    ("embedding_column_also_excluded", "bad_embedding",
     lambda x: x["groups"]["classical_text_chunks"]["tables"][0]["exclude"].append({"column": "embedding", "reason_code": "not_written_by_writer", "reason": "r" * 30}), None),
    ("embedding_source_column_excluded", "bad_embedding",
     lambda x: x["groups"]["classical_text_chunks"]["tables"][0]["exclude"].append({"column": "content_en", "reason_code": "not_written_by_writer", "reason": "r" * 30}), None),
    ("embedding_unknown_source_column", "unknown_column",
     lambda x: x["groups"]["classical_text_chunks"]["tables"][0]["embedding"][0].update({"source_columns": ["no_such_col"]}), None),
    ("embedding_empty_list", "bad_embedding", lambda x: x["groups"]["classical_text_chunks"]["tables"][0].update({"embedding": []}), None),
    ("embedding_without_model", "bad_embedding", lambda x: x["groups"]["classical_text_chunks"]["tables"][0]["embedding"][0].update({"model_id": ""}), None),
    ("expected_difference_on_an_excluded_column", "bad_expected_difference", lambda x: _install_ed(x)["expected_difference"].update({"columns": ["computed_at"]}), None),
    ("expected_difference_short_detail", "bad_expected_difference", lambda x: _install_ed(x)["expected_difference"].update({"detail": "short"}), None),
    ("expected_difference_without_until", "bad_expected_difference", lambda x: _install_ed(x)["expected_difference"].update({"until": ""}), None),
    ("horizon_column_is_timestamptz", "bad_horizon_column", lambda x: _t(x, "bg_sky_calendar").update({"horizon_date_column": "computed_at"}), None),
    ("horizon_column_is_not_a_date", "bad_horizon_column", lambda x: _t(x, "bg_sky_calendar").update({"horizon_date_column": "event_jd"}), None),
    ("horizon_column_does_not_exist", "bad_horizon_column", lambda x: _t(x, "bg_sky_calendar").update({"horizon_date_column": "no_such_col"}), None),
    ("horizon_column_is_not_an_identifier", "bad_horizon_column", lambda x: _t(x, "bg_sky_calendar").update({"horizon_date_column": "Bad Col"}), None),
    ("horizon_naive_timestamp_not_listed_naive", "bad_horizon_column", lambda x: _t(x, "bg_sky_calendar").update({"naive_utc_columns": []}), None),
    ("rolling_unit_without_a_horizon_column", "horizon_column_required", lambda x: _t(x, "bg_sky_calendar").pop("horizon_date_column"), None),
    ("rolling_unit_with_two_horizon_columns", "horizon_column_required",
     lambda x: x["assets"]["bg_muhurta_lattice"]["tables"].append({**copy.deepcopy(_t(x, "bg_muhurta_lattice")), "name": "bg_muhurta_lattice"}), None),
    ("horizon_column_on_a_deterministic_unit", "horizon_on_non_rolling", lambda x: _t(x, "bg_nakshatra").update({"horizon_date_column": "created_at"}), None),
    ("expected_difference_unknown_column", "unknown_column", lambda x: _install_ed(x)["expected_difference"].update({"columns": ["no_such_col"]}), None),
    ("not_written_but_the_writer_writes_it", "exclude_not_written_unproven",
     lambda x: _t(x, "bg_ghatana", "brahma_event_ontology")["exclude"].append({"column": "name_en", "reason_code": "not_written_by_writer", "reason": "r" * 30}), None),
    ("not_written_without_an_insert_list", "exclude_not_written_unproven",
     lambda x: _t(x, "bg_ghatana", "brahma_event_ontology").update({"write_evidence": ["platform/python-sidecar/brahmagyan/l0_ghatana.py:557"]}), None),
    ("wall_clock_on_an_unusual_name_without_a_clock", "exclude_wall_clock_unproven",
     lambda x: _t(x, "bg_ephemeris").setdefault("exclude", []).append({"column": "tropical_longitude", "reason_code": "wall_clock_timestamp", "reason": "r" * 30}), None),
    ("every_non_key_column_excluded", "fingerprint_key_only",
     lambda x: _t(x, "bg_medical_mappings").update({"exclude": [{"column": c, "reason_code": "not_written_by_writer", "reason": "r" * 30}
                                                                 for c in ("id", "dosha", "dhatu", "organ_systems", "body_part", "disease_tendency", "classical_citation")]}), None),
    ("writer_writes_a_table_that_is_not_listed", "coverage_unlisted_table", lambda x: x["assets"]["bg_reference"].pop("not_written_tables"), None),
    ("registry_count_table_not_listed", "coverage_unlisted_table", lambda x: x["assets"]["bg_nakshatra"]["tables"].pop(1), None),
    ("registry_count_table_of_a_group_member_not_listed", "coverage_unlisted_table", lambda x: x["assets"]["bg_dasha_systems"].update({"groups": []}), None),
    ("ownership_evidence_empty", "evidence_missing", lambda x: _t(x, "bg_rules").update({"ownership_evidence": []}), None),
    ("ownership_evidence_names_another_table", "evidence_missing",
     lambda x: _t(x, "bg_rules").update({"ownership_evidence": ["platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py:155"]}), None),
    ("write_evidence_is_not_a_write", "evidence_not_a_write", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"{MP}:1"]}), None),
    ("write_evidence_dotdot_in_the_middle", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"platform/../{MP}:1"]}), None),
    ("write_evidence_dot_segment", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"./{MP}:1"]}), None),
    ("write_evidence_empty_segment", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"platform//{MP[9:]}:1"]}), None),
    ("not_written_tables_without_reason", "undeclared_reason", lambda x: x["assets"]["bg_reference"]["not_written_tables"][0].update({"reason": "dead"}), None),
    ("evidence_line_beyond_the_end_of_a_file_without_a_table", "evidence_missing", lambda x: x["assets"]["bg_panchanga"].update({"evidence": [f"{MP}:99999999"]}), None),
    ("groups_key_missing", "missing_key", lambda x: x.pop("groups"), None),
    ("asset_groups_key_missing", "missing_key", lambda x: x["assets"]["bg_sign_medical"].pop("groups"), None),
    ("asset_id_with_group_prefix", "bad_asset_id", lambda x: x["assets"].update({"grp_x": copy.deepcopy(x["assets"]["bg_sign_medical"])}), None),
    ("source_commit", "bad_source", lambda x: x["source"].update({"code_commit": "abc"}), None),
    ("source_sha", "bad_source", lambda x: x["source"].update({"schema_dump_sha256": "zz"}), None),
    ("no_assets", "bad_shape", lambda x: x.update({"assets": {}}), None),
]


def refusal_results(validate_fn, first_only: bool = False) -> dict[str, bool]:
    """For every refusal: True when `validate_fn` (the validator under test) reports the expected problem code on the mutated document.
    `first_only` stops at the first refusal that fails (enough to kill a validator mutant). The document and the schema extract are copied
    only when the refusal edits them: the validator does not modify its inputs."""
    out = {}
    for rid, code, mdoc, msch in REFUSALS:
        doc = copy.deepcopy(DOC) if mdoc else DOC
        sch = copy.deepcopy(EXT) if msch else EXT
        if mdoc:
            mdoc(doc)
        if msch:
            msch(sch)
        try:
            out[rid] = code in {c for c, _p, _m in validate_fn(doc, registry=REG, schema=sch, repo_root=REPO)}
        except Exception:                                         # noqa: BLE001 - the validator never raises: a crash is a failed refusal
            out[rid] = False
        if first_only and not out[rid]:
            return out
    return out


def test_unmutated_baseline_has_no_problem():
    assert problems(copy.deepcopy(DOC)) == []


@pytest.mark.parametrize("rid,code,mdoc,msch", REFUSALS, ids=[r[0] for r in REFUSALS])
def test_refusal(rid, code, mdoc, msch):
    doc, sch = copy.deepcopy(DOC), copy.deepcopy(EXT)
    if mdoc:
        mdoc(doc)
    if msch:
        msch(sch)
    got = {c for c, _p, _m in problems(doc, schema=sch)}
    assert code in got, f"{rid}: expected {code}, got {sorted(got)}"


def test_every_refusal_code_the_validator_can_emit_is_covered_by_a_mutation():
    emitted = set(re.findall(r'probs\.append\(\("([a-z_]+)"', SRC_FD))
    covered = {r[1] for r in REFUSALS}
    # codes that guard the caller's own inputs rather than the document (registry/extract/file unreadable, bad fingerprint, bad table name)
    exempt = {"registry_unreadable", "schema_extract_unreadable", "declarations_unreadable", "bad_fingerprint", "bad_json", "duplicate_json_key",
              "bad_table_name", "bad_asset_id", "bad_key", "bad_exclude", "bad_naive_utc", "bad_shape", "unknown_key", "missing_key"}
    missing = sorted(emitted - covered - exempt)
    assert not missing, f"validator codes with no refusal test: {missing}"


def test_evidence_must_be_a_tracked_file(monkeypatch):
    """A path that exists on disk but is not tracked in git is refused (L5): only the repository's own files are evidence."""
    real = fd._tracked_paths
    monkeypatch.setattr(fd, "_tracked_paths", lambda root, paths: frozenset(p for p in real(root, paths) if p != "platform/python-sidecar/brahmagyan/l0_medical.py"))
    got = {c for c, _p, _m in fd.validate(DOC, registry=REG, schema=EXT, repo_root=REPO)}
    assert "evidence_untracked" in got
    assert (REPO / "platform/python-sidecar/brahmagyan/l0_medical.py").is_file()


def test_without_a_git_checkout_missing_evidence_is_still_refused(tmp_path):
    got = {c for c, _p, _m in fd.validate(DOC, registry=REG, schema=EXT, repo_root=tmp_path)}
    assert "evidence_missing" in got and "evidence_untracked" not in got


def test_the_registry_count_sql_tables_are_read_into_the_registry():
    assert REG["bg_dasha_systems"]["count_tables"] == ["brahma_dasha_systems", "brahma_ontology", "reference_dasha_systems"]
    assert REG["bg_reference"]["count_tables"] and len(REG["bg_reference"]["count_tables"]) == 11
    assert REG["bg_panchanga"]["count_tables"] == []


def test_the_schema_extract_is_loaded_strictly(tmp_path):
    good = fd.DEFAULT_SCHEMA_EXTRACT.read_text(encoding="utf-8")
    assert fd.load_schema_extract()["table_names"] == EXT["table_names"] and len(EXT["table_names"]) > 300
    for name, text in (("dup.json", good.replace('"schema": "suvarna-l0-schema-extract/v1",', '"schema": "suvarna-l0-schema-extract/v1", "schema": "x",', 1)),
                       ("nan.json", good.replace('"table_names"', '"nan": NaN, "table_names"', 1)),
                       ("inf.json", good.replace('"table_names"', '"inf": Infinity, "table_names"', 1)),
                       ("notype.json", good.replace('"table_names"', '"table_namez"', 1))):
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        with pytest.raises(fd.DeclarationError):
            fd.load_schema_extract(p)


def test_refuses_a_duplicate_json_key():
    text = json.dumps(DOC).replace('"bg_sign_medical": {', '"bg_sign_medical": {"status": "declared", "status": "declared", ', 1)
    with pytest.raises(fd.DeclarationError) as ei:
        fd.strict_loads(text)
    assert "duplicate_json_key" in ei.value.codes
    with pytest.raises(fd.DeclarationError) as e2:
        fd.strict_loads("{not json")
    assert "bad_json" in e2.value.codes
    with pytest.raises(fd.DeclarationError):
        fd.strict_loads('{"a": NaN}')


def test_load_declarations_raises_with_every_problem(tmp_path):
    bad = copy.deepcopy(DOC)
    _t(bad, "bg_medical_mappings")["exclude"][0]["reason"] = ""
    bad["assets"].pop("bg_sign_medical")
    p = tmp_path / "d.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(fd.DeclarationError) as ei:
        fd.load_declarations(p)
    assert {"exclude_no_reason", "missing_asset"} <= set(ei.value.codes)
    with pytest.raises(fd.DeclarationError):
        fd.load_declarations(tmp_path / "absent.json")
    assert fd.main(["validate", "--declarations", str(p)]) == 2


def test_cli_validate_and_summary_on_the_committed_file(capsys):
    assert fd.main(["validate"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert fd.main(["summary"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["assets_total"] == 40 and len(rep["declared"]) + len(rep["undeclared"]) == 40


# ═════════════════════════ 4. conversion to E5.5 and composition ═════════════════════════

def test_every_declared_table_is_a_valid_e55_declaration_in_volatile_mode():
    d = fd.load_declarations()
    n = 0
    for u in d.expected_assets():
        for t in d.tables(u):
            decl = d.table_declaration(u, t)
            norm = nsc.validate_declaration(decl, u)
            assert norm["scope"] == "global" and norm["semantic_columns"] is None and norm["volatile_columns"] == decl["volatile_columns"]
            assert nsc.build_select(decl) == f'SELECT * FROM "{t}"'
            n += 1
    own = sum(len(x["tables"]) for x in DOC["assets"].values() if x["status"] == "declared")
    assert n == own + sum(len(g["tables"]) for g in DOC["groups"].values()) == 64


def test_group_unit_embedding_value_never_enters_the_fingerprint_but_its_sources_do():
    d = fd.load_declarations()
    decl = d.table_declaration("grp_classical_text_chunks", "classical_text_chunks")
    base = {"id": "u1", "chunk_id": "c1", "text_id": "t", "verse_ref": "1", "chapter": 1, "verse_start": 1, "verse_end": 1, "content_sa": "sa", "content_en": "en",
            "content_summary": None, "topics": ["a"], "source_citation": "s", "ingested_at": "2020-01-01T00:00:00+00:00", "translator": None,
            "tradition_school": None, "embedding": "[0.1,0.2]", "content_sha256": "x", "topic_tag": None, "ocr_confidence_score": None,
            "cleaned_translation_text": None, "cleaned_devanagari_text": None, "low_confidence_flag": False, "ocr_review_note": None,
            "ocr_cleanup_pass_version": None, "translation_status": None, "translation_provenance": None}
    fp = nsc.fingerprint_rows([base], decl)
    assert nsc.fingerprint_rows([{**base, "embedding": "[0.9,0.8]", "id": "u2", "ingested_at": "2024-02-02T00:00:00+00:00"}], decl) == fp   # vector, id, ingested_at ignored
    assert nsc.fingerprint_rows([{**base, "content_en": "other"}], decl) != fp                       # a source column moves it
    assert nsc.fingerprint_rows([{**base, "topic_tag": "x"}], decl) != fp                            # so does a column bg_text_index writes


def test_table_declaration_refuses_an_undeclared_asset_and_an_unknown_table():
    d = fd.load_declarations()
    for bad in (("bg_panchanga", "x"), ("bg_class_priors", "brahma_class_priors"), ("bg_nope", "x"), ("bg_sign_medical", "no_such"),
                ("grp_nope", "x"), ("grp_brahma_ontology", "no_such")):
        with pytest.raises(fd.DeclarationError):
            d.table_declaration(*bad)
    for bad in ("bg_text_index", "bg_panchanga"):                     # a group-only member has no unit of its own
        with pytest.raises(fd.DeclarationError):
            d.tables(bad)


def test_a_declaration_that_e55_refuses_is_refused_at_conversion():
    d = fd.load_declarations()
    bad = copy.deepcopy(d.doc)
    _t(bad, "bg_medical_mappings")["key"] = ["Graha"]                       # not a lower-case identifier: E5.5's own refusal
    dd = fd.Declarations(doc=bad, sha256="0" * 64)
    with pytest.raises(nsc.BadDeclaration):
        dd.table_declaration("bg_medical_mappings", "bg_medical_mappings")


def test_composite_fingerprint_single_table_is_passthrough_and_multi_is_order_independent():
    a, b, c = "a" * 64, "b" * 64, "c" * 64
    assert fd.composite_fingerprint({"t1": a}) == a
    m1 = fd.composite_fingerprint({"t1": a, "t2": b})
    assert m1 == fd.composite_fingerprint({"t2": b, "t1": a}) and m1 not in (a, b)
    assert fd.composite_fingerprint({"t1": a, "t2": c}) != m1                  # a changed table moves the asset fingerprint
    assert fd.composite_fingerprint({"t1": a, "t3": b}) != m1                  # a renamed table moves it too
    for bad in ({}, {"t": "short"}, {"t": 5}, {1: a}):
        with pytest.raises(fd.DeclarationError):
            fd.composite_fingerprint(bad)


def test_reader_selects_are_exactly_the_build_select_of_each_unit_table():
    d = fd.load_declarations()
    sel = fd.reader_selects(d)
    assert len(sel) == 64 and all(re.fullmatch(r'SELECT \* FROM "[a-z0-9_]+"', s["sql"]) for s in sel)
    assert [s for s in sel if s["asset"] == "bg_sign_medical"] == [{"asset": "bg_sign_medical", "table": "bg_sign_medical", "sql": 'SELECT * FROM "bg_sign_medical"'}]
    assert not [s for s in sel if s["asset"] in d.undeclared_assets()]
    assert [s["table"] for s in sel if s["asset"] == "grp_brahma_ontology"] == ["brahma_ontology"]
    assert fd.reader_selects(d, ["bg_sign_medical"]) == [s for s in sel if s["asset"] == "bg_sign_medical"]
    for bad in (["bg_panchanga"], ["bg_text_index"]):
        with pytest.raises(fd.DeclarationError):
            fd.reader_selects(d, bad)


# ═════════════════════════ 5. real SQL on the disposable cluster ═════════════════════════

@pytest.fixture
def needs_psycopg():
    return pytest.importorskip("psycopg")


SYN_REG = {"a_one": {"target_table": "syn_one"}, "a_two": {"target_table": "syn_two_a"}}
SYN_DOC = {
    "schema": fd.SCHEMA_ID, "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "layer": "L0", "scope": "global",
    "source": {"registry_snapshot": "x", "registry_snapshot_sha256": "0" * 64, "schema_dump": "x", "schema_dump_sha256": "0" * 64, "code_commit": "1" * 40},
    "groups": {},
    "assets": {
        "a_one": {"status": "declared", "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "scope": "global", "coverage": "full",
                  "reproducibility": ["deterministic"], "groups": [], "not_covered_tables": [], "tables": [
                      {"name": "syn_one", "scope": "global", "key": ["k"], "key_evidence": "primary_key:syn_one_k", "naive_utc_columns": ["at_utc"],
                       "exclude": [{"column": "id", "reason_code": "surrogate_identity", "reason": "serial surrogate assigned at insert"},
                                   {"column": "created_at", "reason_code": "wall_clock_timestamp", "reason": "DEFAULT now() at insert time"}],
                       "write_evidence": ["x.py:1"]}]},
        "a_two": {"status": "declared", "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "scope": "global", "coverage": "full",
                  "reproducibility": ["deterministic"], "groups": [], "not_covered_tables": [], "tables": [
                      {"name": "syn_two_a", "scope": "global", "key": ["k"], "key_evidence": "primary_key:p", "naive_utc_columns": [],
                       "exclude": [], "write_evidence": ["x.py:1"]},
                      {"name": "syn_two_b", "scope": "global", "key": ["k", "n"], "key_evidence": "unique:u", "naive_utc_columns": [],
                       "exclude": [{"column": "id", "reason_code": "surrogate_identity", "reason": "identity column assigned at insert"}],
                       "write_evidence": ["x.py:1"]}]},
        "a_three": {"status": "undeclared", "reason_code": "no_table", "tables_written": [], "evidence": [],
                    "reason": "a service asset: it owns no stored rows so there is nothing to fingerprint at all"}}}


def _syn_decls():
    reg = {**SYN_REG, "a_three": {"target_table": None}}
    assert fd.validate(SYN_DOC, registry=reg, schema=None, repo_root=None) == []
    return fd.Declarations(doc=copy.deepcopy(SYN_DOC), sha256="9" * 64)


def _connect(cl):
    log = sr.ConnectionLog()
    return sr.connect_checked(cl.url, "disposable", log, expect={"data_directory": str(cl.data_dir), "port": cl.port})


def _make_synthetic(conn, build: int, bump: str | None = None):
    cur = conn.cursor()
    for t in ("syn_one", "syn_two_a", "syn_two_b"):
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    cur.execute("CREATE TABLE syn_one (id bigserial, k text PRIMARY KEY, v numeric(9,4) NOT NULL, at_utc timestamp NOT NULL, created_at timestamptz NOT NULL DEFAULT now())")
    cur.execute("CREATE TABLE syn_two_a (k text PRIMARY KEY, j jsonb NOT NULL)")
    cur.execute("CREATE TABLE syn_two_b (id bigserial, k text NOT NULL, n int NOT NULL, w text, UNIQUE (k, n))")
    for i in range(30):
        v = f"{i * 1.5:.4f}" if bump != f"k{i:02d}" else f"{i * 1.5 + 1:.4f}"
        cur.execute("INSERT INTO syn_one (k, v, at_utc) VALUES (%s, %s, %s)", (f"k{i:02d}", v, f"2020-01-{i % 28 + 1:02d} 00:00:00"))
        cur.execute("INSERT INTO syn_two_a (k, j) VALUES (%s, %s::jsonb)", (f"k{i:02d}", json.dumps({"i": i})))
        cur.execute("INSERT INTO syn_two_b (k, n, w) VALUES (%s, %s, %s)", (f"k{i:02d}", i, f"w{i}"))
    conn.commit()


def test_unit_fingerprint_equals_e55_table_fingerprint_and_ignores_exactly_the_declared_volatile_columns(needs_psycopg, disposable_pg):
    d = _syn_decls()
    conn = _connect(disposable_pg)
    try:
        _make_synthetic(conn, 1)
        one = fd.unit_fingerprint(conn, d, "a_one")
        decl = d.table_declaration("a_one", "syn_one")
        assert one["composite"] == one["tables"]["syn_one"]["sha256"] == nsc.table_fingerprint(conn, decl)
        assert one["tables"]["syn_one"]["rows"] == 30
        two = fd.unit_fingerprint(conn, d, "a_two")
        assert two["composite"] == fd.composite_fingerprint({t: v["sha256"] for t, v in two["tables"].items()}) != two["tables"]["syn_two_a"]["sha256"]
        # a delete-then-insert rebuild changes only id and created_at: the fingerprint must not move
        cur = conn.cursor()
        cur.execute("DELETE FROM syn_one")
        for i in range(30):
            cur.execute("INSERT INTO syn_one (k, v, at_utc) VALUES (%s, %s, %s)", (f"k{i:02d}", f"{i * 1.5:.4f}", f"2020-01-{i % 28 + 1:02d} 00:00:00"))
        conn.commit()
        assert fd.unit_fingerprint(conn, d, "a_one")["composite"] == one["composite"]
        # one semantic column changes in one table of a two-table asset: only that table and the composite move
        cur.execute("UPDATE syn_two_b SET w = 'changed' WHERE k = 'k07'")
        conn.commit()
        two2 = fd.unit_fingerprint(conn, d, "a_two")
        assert two2["tables"]["syn_two_a"] == two["tables"]["syn_two_a"] and two2["tables"]["syn_two_b"]["sha256"] != two["tables"]["syn_two_b"]["sha256"]
        assert two2["composite"] != two["composite"]
        # a semantic change in syn_one moves it
        cur.execute("UPDATE syn_one SET v = v + 1 WHERE k = 'k03'")
        conn.commit()
        assert fd.unit_fingerprint(conn, d, "a_one")["composite"] != one["composite"]
    finally:
        for t in ("syn_one", "syn_two_a", "syn_two_b"):
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
        conn.close()


def test_unit_fingerprints_cover_comparison_units_only_and_refuses_an_undeclared_one(needs_psycopg, disposable_pg):
    d = _syn_decls()
    conn = _connect(disposable_pg)
    try:
        _make_synthetic(conn, 1)
        out = fd.unit_fingerprints(conn, d, cursor_prefix="t")                 # server-side named cursors
        assert sorted(out["fingerprints"]) == ["a_one", "a_two"] and out["definition"] == fd.FINGERPRINT_DEFINITION
        assert out["declarations_sha256"] == "9" * 64 and out["tables"]["a_one"]["syn_one"]["rows"] == 30
        assert out["fingerprints"]["a_one"] == fd.unit_fingerprint(conn, d, "a_one")["composite"]
        with pytest.raises(fd.DeclarationError):
            fd.unit_fingerprints(conn, d, ["a_three"])
    finally:
        for t in ("syn_one", "syn_two_a", "syn_two_b"):
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
        conn.close()


def test_a_missing_declared_table_raises_it_never_reads_as_unchanged(needs_psycopg, disposable_pg):
    d = _syn_decls()
    conn = _connect(disposable_pg)
    try:
        conn.execute("DROP TABLE IF EXISTS syn_one")
        conn.commit()
        with pytest.raises(nsc.UnreadableInput):
            fd.unit_fingerprint(conn, d, "a_one")
        conn.rollback()
    finally:
        conn.close()


def test_a_naive_timestamp_not_declared_naive_utc_is_refused_by_e55_at_fingerprint_time(needs_psycopg, disposable_pg):
    d = _syn_decls()
    bad = copy.deepcopy(d.doc)
    bad["assets"]["a_one"]["tables"][0]["naive_utc_columns"] = []
    conn = _connect(disposable_pg)
    try:
        _make_synthetic(conn, 1)
        with pytest.raises(nsc.UnreadableInput):
            fd.unit_fingerprint(conn, fd.Declarations(doc=bad, sha256="9" * 64), "a_one")
        conn.rollback()
    finally:
        for t in ("syn_one", "syn_two_a", "syn_two_b"):
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
        conn.close()


# ═════════════════════════ 6. source mutants of the validator ═════════════════════════

SRC_FD = (GOV / "fingerprint_declarations.py").read_text(encoding="utf-8")


def load_module(src: str, name: str):
    mod = types.ModuleType(name)
    mod.__file__ = str(GOV / "fingerprint_declarations.py")
    sys.modules[name] = mod
    exec(compile(src, f"<{name}>", "exec"), mod.__dict__)         # noqa: S102 - the repo's own source, one mutation applied
    return mod


MUTANTS = [
    ('probs.append(("exclude_no_reason"', 'probs.append(("exclude_no_reason_x"'),
    ('                if hz not in cols:', '                if False:'),
    ('                elif cols[hz]["type"] not in HORIZON_TYPES:', '                elif False:'),
    ('                elif cols[hz]["type"] == TIMESTAMP_NAIVE and hz not in naive:', '                elif False:'),
    ('        if len(carriers) != 1:', '        if False:'),
    ('    elif carriers:\n        probs.append(("horizon_on_non_rolling"', '    elif False:\n        probs.append(("horizon_on_non_rolling"'),
    ('    if "rolling_horizon" in repro:\n        if len(carriers)', '    if False:\n        if len(carriers)'),
    ('        if col in key:\n            probs.append(("exclude_key"', '        if False:\n            probs.append(("exclude_key"'),
    ('        if code not in EXCLUDE_REASON_CODES:', '        if False:'),
    ('    if len(set(key)) != len(key):', '    if False:'),
    ('and not cols[c]["generated"]:', 'and False:'),
    ('        elif sorted(named[ke]) != sorted(key):', '        elif False:'),
    ('        if ke not in named:', '        if False:'),
    ('        for a in sorted(set(assets) - set(registry)):', '        for a in []:'),
    ('        for a in sorted(set(registry) - set(assets)):', '        for a in []:'),
    ('if code == "surrogate_identity" and not meta["identity"]:', 'if False:'),
    ('if code == "wall_clock_timestamp" and not meta["type"].startswith("timestamp"):', 'if False:'),
    ('if code == "build_identity" and col != "build_id":', 'if False:'),
    ('        if meta["type"] == TIMESTAMP_NAIVE and c not in ex_cols and c not in naive:', '        if False:'),
    ('        if c in cols and cols[c]["type"] != TIMESTAMP_NAIVE:', '        if False:'),
    ('        if (d["coverage"] == "partial") != bool(notcov):', '        if False:'),
    ('    if doc["fingerprint_definition"] != FINGERPRINT_DEFINITION:', '    if False:'),
    ('        if d["fingerprint_definition"] != FINGERPRINT_DEFINITION:', '        if False:'),
    ('    if int(line) > len(lines):', '    if False:'),
    ('    if tables and not any(_mentions(win, t, lines) for t in tables):', '    if False:'),
    ('                if n in claimed and claimed[n] != f"asset {asset}":', '                if False:'),
    ('        if others:', '        if False:'),
    ('            if d["reason_code"] not in UNDECLARED_CODES:', '            if False:'),
    ('        if d["coverage"] not in COVERAGE:', '        if False:'),
    ('    if doc["schema"] != SCHEMA_ID:', '    if False:'),
    ('    if t["scope"] != SCOPE:', '    if False:'),
    ('        if d["scope"] != SCOPE:', '        if False:'),
    ('        if status != "declared":', '        if False:'),
    ('    if tab is None:', '    if False:'),
    ('        if not tables and not gids:', '        if False:'),
    ('elif len(reason.strip()) < MIN_REASON_CHARS:', 'elif False:'),
    ('            if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *(tw if isinstance(tw, list) else [])):', '            if False:'),
    ('        if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *accounted):', '        if False:'),
    ('        for k in ("registry_snapshot_sha256", "schema_dump_sha256"):', '        for k in ():'),
    ('        if not (isinstance(src["code_commit"], str) and _HEX40.fullmatch(src["code_commit"])):', '        if False:'),
    ('    elif write and not _WRITE_VERB.search(win):', '    elif False:'),
    ('    if ctx.tracked is not None and rel not in ctx.tracked:', '    if False:'),
    ('    if rel.startswith("/") or ".." in parts or "." in parts or "" in parts:', '    if rel.startswith("/") or ".." in parts:'),
    ('    if rel.startswith("/") or ".." in parts or "." in parts or "" in parts:', '    if rel.startswith("/") or "." in parts or "" in parts:'),
    ('            elif any(col in c for c in lists):', '            elif False:'),
    ('            if not lists:', '            if False:'),
    ('        if ctx is not None and code == "wall_clock_timestamp" and col not in WALL_CLOCK_NAMES and not any(_CLOCK.search(w) for w in wins):', '        if False:'),
    ('    if non_key and non_key <= (set(ex_cols) | set(emb_cols)):', '    if False:'),
    ('            if n not in accounted:', '            if False:'),
    ('                        if n in universe and n not in accounted and n not in known and n not in seen:', '                        if False:'),
    ('        if not (isinstance(mem, Mapping) and len(mem) >= 2):', '        if False:'),
    ('        if not isinstance(g["seeded"], bool):', '        if False:'),
    ('        if po["reason_code"] != PARTIAL_OWNERSHIP_CODE:', '        if False:'),
    ('            elif asset not in group_members.get(gid, []):', '            elif False:'),
    ('            elif gid not in (a.get("groups") or []):', '            elif False:'),
    ('        others = side.get(n, set()) - {owner}', '        others = set()'),
    ('        if not (isinstance(gid, str) and _IDENT.fullmatch(gid)) or gid in assets or (GROUP_PREFIX + gid) in assets:', '        if False:'),
    ('                if e["column"] in key or e["column"] in ex_cols:', '                if False:'),
    ('                    if c in ex_cols or c in key:', '                    if False:'),
    ('                    if s in ex_cols:', '                    if False:'),
    ('        return json.loads(text, object_pairs_hook=_no_dup_pairs, parse_constant=_refuse_constant)', '        return json.loads(text, object_pairs_hook=_no_dup_pairs)'),
    ('    if len(table_shas) == 1:\n        return next(iter(table_shas.values()))', '    if len(table_shas) == 0:\n        return next(iter(table_shas.values()))'),
    ('"tables": dict(sorted(table_shas.items()))', '"tables": {k: "0" * 64 for k in table_shas}'),
    ('            raise DeclarationError([("duplicate_json_key"', '            pass\n            DeclarationError([("duplicate_json_key"'),
]


def _judge_validator_mutant(args):
    """One validator mutant -> (index, verdict). Module-level so a process pool can run it."""
    i, old, new = args
    if SRC_FD.count(old) < 1:
        return i, "TARGET_ABSENT"
    mutated = SRC_FD.replace(old, new, 1)
    if mutated == SRC_FD:
        return i, "NO_CHANGE"
    try:
        m = load_module(mutated, "fd_mut_" + str(abs(hash(old + new)) % 10**8))
    except Exception:                                             # noqa: BLE001 - a mutant that does not even load is trivially dead
        return i, "dead"
    base = {rid: ok for rid, ok in refusal_results(m.validate, first_only=True).items()}
    failed = [rid for rid, ok in base.items() if not ok]
    ok_clean = m.validate(copy.deepcopy(DOC), registry=REG, schema=EXT, repo_root=REPO) == []
    comp = False
    try:
        comp = (m.composite_fingerprint({"t1": "a" * 64}) == "a" * 64
                and m.composite_fingerprint({"t1": "a" * 64, "t2": "b" * 64}) == fd.composite_fingerprint({"t1": "a" * 64, "t2": "b" * 64}))
    except Exception:                                             # noqa: BLE001
        comp = False
    try:
        m.strict_loads('{"a": 1, "a": 2}')
        dup_refused = False
    except Exception:                                             # noqa: BLE001 - DeclarationError from the mutant's own class
        dup_refused = True
    try:
        m.strict_loads('{"a": NaN}')
        nan_refused = False
    except Exception:                                             # noqa: BLE001
        nan_refused = True
    dead = bool(failed or not ok_clean or not comp or not dup_refused or not nan_refused)
    return i, ("dead" if dead else "SURVIVED")


def _validator_mutant_verdicts(items):
    """Every mutant judged in parallel where `fork` exists (each judgement is independent and CPU-bound; serially these ~60 mutants took about
    five minutes on a CI runner and, with the other E5.7 suites, pushed one governance shard past its 10-minute ceiling), serially elsewhere."""
    import concurrent.futures
    import multiprocessing
    import os
    jobs = [(i, o, n) for i, (o, n) in enumerate(items)]
    workers = max(1, min(8, os.cpu_count() or 1))
    if workers > 1 and "fork" in multiprocessing.get_all_start_methods():
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("fork")) as pool:
            return sorted(pool.map(_judge_validator_mutant, jobs, chunksize=2))
    return sorted(_judge_validator_mutant(j) for j in jobs)


def test_validator_source_mutants_are_caught():
    """Each mutant removes one refusal from the validator; the refusal matrix (and the composition checks) must notice."""
    verdicts = _validator_mutant_verdicts(MUTANTS)
    assert len(verdicts) == len(MUTANTS) and len(MUTANTS) >= 50
    bad = [(i, v, MUTANTS[i][0][:90]) for i, v in verdicts if v != "dead"]
    assert not bad, f"{len(bad)} mutant(s) not caught (SURVIVING or target moved): {bad[:5]}"
