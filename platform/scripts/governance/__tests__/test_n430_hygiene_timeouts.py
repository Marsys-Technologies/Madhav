"""test_n430_hygiene_timeouts.py: SS N-430 T3, A READ TIMEOUT IS NO_DETECTOR EVERYWHERE, NEVER ERRORED.

A read the server cancelled (statement timeout, lock timeout) or the census killed (client-side limit) measured NOTHING: the cell reads NO_DETECTOR with a FIXED cause that names the
timeout (no psql text, no SQL, no host) and is never a PASS. A real error (a missing relation, a bad value) stays ERRORED. Every site that used to turn a failed read into
`check errored: ...` goes through `_read_failure_cell`; an AST audit pins the complete list of the sites that deliberately do not (they read no database).

Offline: fakes only (no database, no cluster).
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_n99_build_completion_integrity as n99  # noqa: E402

PASS, FAIL, PARTIAL, NO_DET, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.ERRORED

STMT = "ERROR:  canceling statement due to statement timeout"
LOCK = "ERROR:  canceling statement due to lock timeout"
REAL = 'ERROR:  relation "ga_t" does not exist'
TIMEOUTS = [("statement", lambda: ac.Unknown(STMT)), ("lock", lambda: ac.Unknown(LOCK))]           # the SERVER cancelled the read: NO_DETECTOR
CLIENT = lambda: ac.CheckTimeout("client-side timeout after 180s (psql killed): SELECT secret_column FROM t")         # noqa: E731  the census's own kill: stays ERRORED, as before
FIXED = {"statement": "the server's statement timeout", "lock": "the server's lock timeout"}


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("SUVARNA_CENSUS_STATEMENT_CAP_SECS", raising=False)


def _is_timeout_cell(cell, kind=None):
    assert cell["v"] == NO_DET, cell
    assert cell["measured"].startswith("NO_DETECTOR — a read this check needs was cancelled by"), cell
    assert "neither a PASS nor a FAIL" in cell["measured"]
    if kind:
        assert FIXED[kind] in cell["measured"]
    for leak in ("SELECT", "secret_column", "ERROR:", "psql"):
        assert leak not in cell["measured"], cell
    return True


# ───────────────────────── the classifier and the cell helper ─────────────────────────

@pytest.mark.parametrize("exc,kind", [(ac.Unknown(STMT), "statement"), (ac.Unknown("ERROR:  57014: canceling statement due to statement timeout"), "statement"),
                                      (ac.Unknown("canceling statement due to STATEMENT TIMEOUT"), "statement"),
                                      (ac.Unknown(LOCK), "lock"), (ac.Unknown("ERROR:  55P03: canceling statement due to lock timeout"), "lock"),
                                      (ac.Unknown("lock_not_available"), "lock"),
                                      (ac.CheckTimeout("client-side timeout after 180s"), "client"),
                                      (STMT, "statement"), (LOCK, "lock"),
                                      (ac.Unknown(REAL), None), (ac.Unknown('ERROR:  permission denied for table charts'), None),
                                      (ac.Unknown("server closed the connection unexpectedly"), None), (ac.ReadError("psql row 1 has 2 field(s)"), None),
                                      (ValueError("bad value"), None), (None, None), ("", None)])
def test_the_timeout_classifier(exc, kind):
    assert ac._read_timeout_kind(exc) == kind
    assert ac._is_statement_timeout(exc) is (kind is not None)


def test_the_lock_timeout_reaches_the_existing_statement_timeout_paths():
    """`_is_statement_timeout` is what the already-NO_DETECTOR sites ask: a lock timeout now takes the same road as a statement timeout."""
    assert ac._is_statement_timeout(ac.Unknown(LOCK))
    assert ac._fl_unread(ac.Unknown(LOCK))["kind"] == "timeout"
    assert "statement timeout" in ac._formgap_unread_reason(ac.Unknown(LOCK))


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_the_helper_turns_a_timeout_into_a_fixed_no_detector_and_keeps_the_other_keys(kind, make):
    errored = dict(v=ERRORED, declared=True, citation_state="verified", measured="check errored: whatever the psql text was")
    got = ac._read_failure_cell(make(), errored)
    assert _is_timeout_cell(got, kind)
    assert list(got) == list(errored) and got["declared"] is True and got["citation_state"] == "verified"        # same keys, same order
    assert errored["v"] == ERRORED, "the input cell is not mutated"


@pytest.mark.parametrize("exc", [ac.Unknown(REAL), ac.Unknown("permission denied for table x"), ValueError("v"), ac.ReadError("ragged")])
def test_a_real_error_stays_the_very_same_errored_cell(exc):
    errored = dict(v=ERRORED, measured=f"check errored: {exc}")
    assert ac._read_failure_cell(exc, errored) is errored


def test_a_client_side_kill_stays_errored_exactly_as_before():
    """Decision recorded in `_read_failure_cell`: the census's own wall-clock kill is not a server timeout; Carr.D3 and the null convention document it as an error and pin it."""
    errored = dict(v=ERRORED, measured="check errored: client-side timeout after 180s (psql killed)")
    assert ac._read_failure_cell(CLIENT(), errored) is errored
    assert ac._is_statement_timeout(CLIENT()) is True                 # the pre-existing unread-with-cause paths still treat it as a timeout


def test_the_text_does_not_depend_on_what_the_failed_statement_said():
    a = ac._read_failure_cell(ac.Unknown(STMT + " in relation alpha"), dict(v=ERRORED, measured="x"))
    b = ac._read_failure_cell(ac.Unknown(STMT + " in relation beta"), dict(v=ERRORED, measured="y"))
    assert a == b


# ───────────────────────── measure(): the sites inside the per-asset loop ─────────────────────────

def _measure(monkeypatch, tmp_path, *, cols=("id", "v"), keys=((("v",),)), live=5, counts=None, patches=None):
    monkeypatch.setitem(n99._TABLE, "ga_t", (list(cols), [tuple(k) for k in keys]))
    reg = {"ph_x": n99._reg_row("ph_x", None, has_integrity=False)}
    n99._stub_layer(monkeypatch, tmp_path, reg, live=live)
    if counts is not None:
        monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: counts)
    for name, fn in (patches or {}).items():
        monkeypatch.setattr(ac, name, fn)
    return None, n99._cell


def _depth_with_rows(t, c):
    return dict(columns=len(c), rows=5, full=list(c), never=[], note="")


def _raise(exc_factory):
    def f(*a, **k):
        raise exc_factory()
    return f


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_bo_laksana_style_Vocab_identity_probe_timeout_is_no_detector(monkeypatch, tmp_path, kind, make):
    """The bo_laksana Vocab.identity cell errored on 'canceling statement due to statement timeout' (identity_duplicates). Driven through measure()."""
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(identity_duplicates=_raise(make)))
    census = ac.measure("L4")
    assert _is_timeout_cell(cell(census, "ph_x", "Vocab.identity"), kind)


def test_Vocab_identity_a_real_error_stays_errored_and_a_clean_probe_still_passes(monkeypatch, tmp_path):
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(identity_duplicates=_raise(lambda: ac.Unknown(REAL))))
    got = cell(ac.measure("L4"), "ph_x", "Vocab.identity")
    assert got["v"] == ERRORED and REAL.split("ERROR:")[1].strip() in got["measured"]
    monkeypatch.setattr(ac, "identity_duplicates", lambda t, k: (False, "0 duplicate(s)"))
    monkeypatch.setattr(ac, "identity_has_rows", lambda t: True)
    monkeypatch.setattr(ac, "depth_census", _depth_with_rows)
    assert cell(ac.measure("L4"), "ph_x", "Vocab.identity")["v"] == PASS


def test_Vocab_identity_timeout_on_the_has_rows_probe_is_no_detector_too(monkeypatch, tmp_path):
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(identity_duplicates=lambda t, k: (False, "0 duplicate(s)"), identity_has_rows=_raise(lambda: ac.Unknown(STMT)),
                                                                  depth_census=lambda t, c: dict(columns=len(c), note="rows unknown")))     # no `rows`: the EXISTS probe runs
    assert _is_timeout_cell(cell(ac.measure("L4"), "ph_x", "Vocab.identity"), "statement")


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_Complete_depth_timeout_is_no_detector(monkeypatch, tmp_path, kind, make):
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(depth_census=_raise(make)))
    assert _is_timeout_cell(cell(ac.measure("L4"), "ph_x", "Complete.depth"), kind)


def test_Complete_depth_a_real_error_stays_errored(monkeypatch, tmp_path):
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(depth_census=_raise(lambda: ac.Unknown(REAL))))
    assert cell(ac.measure("L4"), "ph_x", "Complete.depth")["v"] == ERRORED


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_legacy_Vocab_alias_timeout_is_no_detector(monkeypatch, tmp_path, kind, make):
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(alias_census=_raise(make)))
    assert _is_timeout_cell(cell(ac.measure("L4"), "ph_x", "Vocab.alias"), kind)


def test_legacy_Vocab_alias_a_real_error_stays_errored(monkeypatch, tmp_path):
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(alias_census=_raise(lambda: ac.Unknown(REAL))))
    assert cell(ac.measure("L4"), "ph_x", "Vocab.alias")["v"] == ERRORED


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_legacy_Ldgr_source_presence_timeout_is_no_detector(monkeypatch, tmp_path, kind, make):
    """bo_laksana_rerank's Ldgr.source_presence cell: a timed-out presence read is NO_DETECTOR (a DROPPED connection is a different matter: see test_n430_hygiene_retry)."""
    _, cell = _measure(monkeypatch, tmp_path, cols=("id", "v", "classical_citation"),
                       patches=dict(depth_census=_depth_with_rows, ldgr_legacy_presence=_raise(make)))
    assert _is_timeout_cell(cell(ac.measure("L4"), "ph_x", "Ldgr.source_presence"), kind)


def test_legacy_Ldgr_source_presence_a_real_error_and_a_dropped_connection_stay_errored(monkeypatch, tmp_path):
    for msg in (REAL, "server closed the connection unexpectedly"):
        _, cell = _measure(monkeypatch, tmp_path, cols=("id", "v", "classical_citation"),
                           patches=dict(depth_census=_depth_with_rows, ldgr_legacy_presence=_raise(lambda m=msg: ac.Unknown(m))))
        assert cell(ac.measure("L4"), "ph_x", "Ldgr.source_presence")["v"] == ERRORED


@pytest.mark.parametrize("err", [STMT, LOCK])
def test_a_timed_out_count_sql_is_no_detector_for_Build_completion_and_Count_floor(monkeypatch, tmp_path, err):
    _, cell = _measure(monkeypatch, tmp_path, counts=({"ph_x": None}, {"ph_x": err}))
    census = ac.measure("L4")
    for crit in ("Build.completion", "Count.floor"):
        assert _is_timeout_cell(cell(census, "ph_x", crit)), crit


def test_a_count_sql_real_error_stays_errored_for_both(monkeypatch, tmp_path):
    _, cell = _measure(monkeypatch, tmp_path, counts=({"ph_x": None}, {"ph_x": REAL}))
    census = ac.measure("L4")
    assert cell(census, "ph_x", "Build.completion")["v"] == ERRORED and cell(census, "ph_x", "Count.floor")["v"] == ERRORED


def test_a_timeout_never_becomes_a_pass_anywhere(monkeypatch, tmp_path):
    _, cell = _measure(monkeypatch, tmp_path, counts=({"ph_x": None}, {"ph_x": STMT}), patches=dict(identity_duplicates=_raise(lambda: ac.Unknown(STMT)),
                                                                                                        depth_census=_raise(lambda: ac.Unknown(LOCK))))
    census = ac.measure("L4")
    for crit in ("Build.completion", "Count.floor", "Vocab.identity", "Complete.depth"):
        assert cell(census, "ph_x", crit)["v"] == NO_DET, crit


# ───────────────────────── the called functions: one test per remaining read site ─────────────────────────

def _decl():
    return json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["assets"]["bg_phaladeepika_latta"]


LATTA_COLS = ["table_version", "graha", "count_from_graha", "direction", "effect_description", "affliction_condition", "source_citation", "verse_ref", "created_at"]


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_declared_Vocab_alias_read_timeout_is_no_detector_and_a_real_error_errored(monkeypatch, kind, make):
    va = _decl()["vocab_alias"]
    monkeypatch.setattr(ac, "alias_fetch_forms", _raise(make))
    got = ac.vocab_alias_declared_check("bg_phaladeepika_latta", va, "bg_phaladeepika_latta", LATTA_COLS)["Vocab.alias"]
    assert _is_timeout_cell(got, kind) and got["declared"] is True
    monkeypatch.setattr(ac, "alias_fetch_forms", _raise(lambda: ac.Unknown(REAL)))
    assert ac.vocab_alias_declared_check("bg_phaladeepika_latta", va, "bg_phaladeepika_latta", LATTA_COLS)["Vocab.alias"]["v"] == ERRORED


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_declared_Ldgr_source_read_timeout_is_no_detector_and_keeps_the_citation_state(monkeypatch, kind, make):
    ls = _decl()["ldgr_source"]
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", _raise(make))
    got = ac.ldgr_source_declared_check("bg_phaladeepika_latta", ls, "bg_phaladeepika_latta", LATTA_COLS, [["table_version", "graha"]])["Ldgr.source_presence"]
    assert _is_timeout_cell(got, kind) and got["citation_state"] == ls["citation_state"] and got["declared"] is True
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", _raise(lambda: ac.Unknown(REAL)))
    assert ac.ldgr_source_declared_check("bg_phaladeepika_latta", ls, "bg_phaladeepika_latta", LATTA_COLS, [["table_version", "graha"]])["Ldgr.source_presence"]["v"] == ERRORED


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_declared_D1_carriage_read_timeout_is_no_detector_and_a_real_error_errored(monkeypatch, kind, make):
    car = _decl()["carriage"]
    monkeypatch.setattr(ac, "d1_fetch_chunks", _raise(make))
    got = ac.carriage_declared_checks("bg_phaladeepika_latta", car, "bg_phaladeepika_latta", False, column_types={}, prose_columns=[])
    d1 = got[f"Carr.{car['applies']}"]
    assert _is_timeout_cell(d1, kind) and d1["citation_state"] == car.get("citation_state")
    monkeypatch.setattr(ac, "d1_fetch_chunks", _raise(lambda: ac.Unknown(REAL)))
    assert ac.carriage_declared_checks("bg_phaladeepika_latta", car, "bg_phaladeepika_latta", False, column_types={}, prose_columns=[])[f"Carr.{car['applies']}"]["v"] == ERRORED


import test_c1_3_census_d3_wiring as d3w  # noqa: E402
from test_c1_3_census_d3_wiring import reads  # noqa: E402,F401  (the fixture: fake D3 reads)


@pytest.mark.parametrize("kind,make", TIMEOUTS)
def test_D3_server_side_timeout_is_no_detector_and_a_real_error_errored(reads, monkeypatch, kind, make):
    monkeypatch.setattr(ac, "d3_fetch_rows", _raise(make))
    got = ac.carriage_declared_checks(d3w.AID, d3w.car_pass(), "chart_facts", True, asset_rows=1205, **d3w.KW)["Carr.D3"]
    assert _is_timeout_cell(got, kind)
    monkeypatch.setattr(ac, "d3_fetch_rows", _raise(lambda: ac.Unknown(REAL)))
    assert ac.carriage_declared_checks(d3w.AID, d3w.car_pass(), "chart_facts", True, asset_rows=1205, **d3w.KW)["Carr.D3"]["v"] == ERRORED


def test_D3_keeps_its_documented_contract_a_client_side_kill_is_an_error(reads, monkeypatch):
    """N-156 / test_c1_3_census_d3_wiring: D3 reads in ONE pass under a stated client timeout and 'a timeout is an error'. The client-side kill stays ERRORED there (the one exception to T3)."""
    monkeypatch.setattr(ac, "d3_fetch_rows", _raise(CLIENT))
    got = ac.carriage_declared_checks(d3w.AID, d3w.car_pass(), "chart_facts", True, asset_rows=1205, **d3w.KW)["Carr.D3"]
    assert got["v"] == ERRORED and "a timeout is an error" in got["measured"]


def test_Vocab_identity_client_side_kill_stays_errored(monkeypatch, tmp_path):
    _, cell = _measure(monkeypatch, tmp_path, patches=dict(identity_duplicates=_raise(CLIENT)))
    assert cell(ac.measure("L4"), "ph_x", "Vocab.identity")["v"] == ERRORED


def test_Build_target_owner_read_timeout_is_no_detector_and_a_real_error_errored():
    r = n99._reg_row("ph_x", None)
    r.update(target_table=None, asset_kind="data", has_writer=True)
    assert _is_timeout_cell(ac._measure_target(r, _raise(lambda: ac.Unknown(STMT)), None), "statement")
    assert ac._measure_target(r, _raise(lambda: ac.Unknown(REAL)), None)["v"] == ERRORED


def test_Count_floor_helper_directly():
    r = n99._reg_row("ph_x", None)
    assert _is_timeout_cell(ac._grade_count_floor(r, None, STMT, ["ga_t"]))
    assert ac._grade_count_floor(r, None, REAL, ["ga_t"])["v"] == ERRORED


def test_Build_dag_reads_match_ownership_read_timeout_is_no_detector(monkeypatch):
    r = n99._reg_row("ph_x", None)
    monkeypatch.setattr(ac, "reads_scan", lambda aid, files: dict(reads=["some_table"]))
    v, text, _ = ac._reads_clause("ph_x", r, ["w.py"], _raise(lambda: ac.Unknown(STMT)), None)
    assert v == NO_DET and "cancelled by the server's statement timeout" in text
    v, text, _ = ac._reads_clause("ph_x", r, ["w.py"], _raise(lambda: ac.Unknown(REAL)), None)
    assert v == ERRORED and "table ownership unreadable" in text


def test_null_convention_read_timeout_is_no_detector_and_a_real_error_errored(monkeypatch):
    import test_e6_decl_latta_null as dln
    own = {dln.AID: (dln.COLS, dln.TYPES, {"created_at": "now()"})}
    monkeypatch.setattr(ac, "null_convention_fetch", _raise(lambda: ac.Unknown(STMT)))
    got = ac.null_convention_check(dln.NC, own, {dln.AID}, ac._table_scope(dln.AID, dln.R, own, set()))
    assert _is_timeout_cell(got, "statement") and got["declared"] is True
    monkeypatch.setattr(ac, "null_convention_fetch", _raise(lambda: ac.Unknown(REAL)))
    assert ac.null_convention_check(dln.NC, own, {dln.AID}, ac._table_scope(dln.AID, dln.R, own, set()))["v"] == ERRORED


# ───────────────────────── the audit: every remaining ERRORED site is a deliberate non-read ─────────────────────────

# (enclosing function, start of the `measured` text) for every `dict(v=ERRORED, ...)` / `return ERRORED, ...` that does NOT go through `_read_failure_cell`: none of them reads a database
# (a file scan, a git window, a tie in recorded rows, an unreadable declarations file, a count_sql that produced no value), or (source_declared_check) it already sits behind an
# explicit `_is_statement_timeout` branch that returns NO_DETECTOR first, or (_reads_clause) behind the `_read_timeout_kind` branch tested above.
NON_READ_ERRORED_SITES = {
    ("_grade_dep_liveness", "f'check errored: {head}; undetermined (R44 tie)"),
    ("narr_lint_scan", "f'check errored: narration lint could not run"),
    ("_measure_contract", "f'check errored: {exc}'"),
    ("_measure_idem", "f'check errored: {exc}'"),
    ("source_declared_check", "f'check errored: {exc}'"),
    ("cell", 'f"check errored: the Build.history window raised'),
    ("measure", "f'check errored: the declarations file is unreadable"),
    ("measure", "'check errored: count_sql produced no value'"),
    ("measure", 'f"check errored: {t.get(\'n_rows\')} asset_throughput rows'),
    ("_reads_clause", "f'check errored: reads-match scan failed"),
    ("_reads_clause", "f'check errored: {exc}'"),
    ("_reads_clause", "f'check errored: table ownership unreadable"),
}


def _errored_sites_not_wrapped():
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}

    def enclosing(n):
        while n in parent:
            n = parent[n]
            if isinstance(n, ast.FunctionDef):
                return n.name
        return None
    found, wrapped = set(), 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "dict" and any(
                k.arg == "v" and isinstance(k.value, ast.Name) and k.value.id == "ERRORED" for k in n.keywords):
            measured = next((ast.unparse(k.value) for k in n.keywords if k.arg == "measured"), "")
            p = parent[n]
            if isinstance(p, ast.Call) and isinstance(p.func, ast.Name) and p.func.id == "_read_failure_cell":
                wrapped += 1
            else:
                found.add((enclosing(n), measured))
        elif isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple) and n.value.elts and isinstance(n.value.elts[0], ast.Name) and n.value.elts[0].id == "ERRORED":
            found.add((enclosing(n), ast.unparse(n.value.elts[1])))
    return found, wrapped


def test_every_errored_site_is_either_routed_through_the_timeout_helper_or_a_pinned_non_read():
    found, wrapped = _errored_sites_not_wrapped()
    unpinned = sorted(s for s in found if not any(s[0] == f and s[1].startswith(t) for f, t in NON_READ_ERRORED_SITES))
    assert not unpinned, f"an ERRORED cell is built without _read_failure_cell: route it (if it reads the database) or pin it here (if it does not): {unpinned}"
    stale = sorted(t for t in NON_READ_ERRORED_SITES if not any(s[0] == t[0] and s[1].startswith(t[1]) for s in found))
    assert not stale, f"pinned non-read sites that no longer exist: {stale}"
    assert wrapped >= 17, f"expected at least 17 sites routed through _read_failure_cell, found {wrapped}"
