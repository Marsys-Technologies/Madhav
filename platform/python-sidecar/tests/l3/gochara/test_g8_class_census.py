"""G8 (steward GAPS-G8-G9) — the EXPECTED CLASS CENSUS at verify and at seal.

Before 1306 nothing compared the classes a generation CLAIMS (its event_class coverage partitions / search inventories) with the scored
classes it was built for, so a candidate with 25 of 26 classes could be verified class by class and sealed. These tests pin, on the real
migration chain and the real code:

  * the registry fact: 27 classes registered, 26 scored, `birth_anchor` excluded (an unscored annotation the evaluator refuses to enumerate),
    and the verifier's OWN universe equal to both the protocol's table and the builder's scored classes (no silent drift);
  * the vector: the key is additive (absent unless supplied), strictly validated, and re-derived by the verifier from its own universe;
  * the verification job: refuses a claimed-vs-pinned mismatch BY NAME before writing anything (25 of 26 refused, extra refused, unpinned refused);
  * the database: the completeness function (and so the seal) refuses 25 of 26, an extra class, an absent or malformed pin; 26 of 26 passes the census;
    migration 1306 changes ONLY what it says (static equality with the 1232 function) and the pre-1306 function demonstrably let 25 of 26 through.
Mutation checks are in the tests themselves (the pre-1306 function is the mutant)."""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_eval import registry as eval_registry
from services.gochara_kernel import evaluator as gk_evaluator
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import input_vector_verifier as ivv
from services.gochara_kernel import verification_job as vj

from .test_a53_input_vector import _ivv, _vector, db, ephe  # noqa: F401  (fixtures + helpers of the vector suite)
from .test_a53_inventory import CHART_ID, create_am5_database, drop_am5_database
from .test_a53_record_store import MIGRATIONS

M1306 = MIGRATIONS / "1306_gochara_expected_class_census.sql"
M1232 = MIGRATIONS / "1232_gochara_search_moon_scope_domain.sql"
#: sha256 of pg_get_functiondef of the completeness function as production holds it (read-only catalog read, 2026-10-05) — what 1232 produces
PROD_1232_DEF_SHA256 = "63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb"
CENSUS_VIOLATIONS = ("expected_class_list_missing", "expected_class_list_malformed", "class_missing", "class_not_pinned")


# ── the registry fact ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_27_registered_26_scored_and_birth_anchor_is_the_one_excluded():
    registered = set(gk_evaluator.ROW_MEMBERSHIP)
    scored = {c for c, k in gk_evaluator.ROW_MEMBERSHIP.items() if k is not None}
    assert len(registered) == 27 and len(scored) == 26
    assert registered - scored == {"birth_anchor"}
    assert set(writer_mod.SCORED_CLASSES) == scored
    with pytest.raises(ValueError, match="excluded from enumeration entirely"):
        gk_evaluator.enumerate_p3_edges("birth_anchor", {"lagna_deg": 0.0, "natal": {}})        # the evaluator refuses the annotation class by design (O-CF-N6)


def test_the_verifiers_own_universe_equals_the_protocol_table_minus_the_annotation_and_the_builders_scored_classes():
    universe = set(ivv.SCORED_CLASS_UNIVERSE)
    assert len(ivv.SCORED_CLASS_UNIVERSE) == 26 and len(universe) == 26                       # distinct
    assert universe == set(eval_registry.CLASSES_27) - set(ivv.ANNOTATION_ONLY_CLASSES)       # EVALUATION_PROTOCOL_v2_3 §2
    assert universe == set(writer_mod.SCORED_CLASSES)                                         # the builder
    assert ivv.ANNOTATION_ONLY_CLASSES == ("birth_anchor",)


# ── the vector ──────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [[], "marriage", None.__class__, ["marriage", "marriage"], ["marriage", 3], ["marriage", ""], ["marriage", " x"], ["marriage ", "x"]])
def test_a_malformed_scored_class_list_is_refused_never_normalised(bad):
    if bad is None.__class__:
        bad = 5
    with pytest.raises(iv.InputDrift, match="scored_classes"):
        iv._scored_classes_component(bad)


def test_the_key_is_additive_via_the_real_builder(db, ephe):
    plain = _vector(db, str(ephe))
    pinned = _vector(db, str(ephe), scored_classes=list(writer_mod.SCORED_CLASSES))
    assert "scored_classes" not in plain
    assert pinned["scored_classes"] == sorted(writer_mod.SCORED_CLASSES)
    assert {k: v for k, v in pinned.items() if k != "scored_classes"} == plain                  # nothing else moved
    # verify_live / verify_replay read the pin back from the stored vector, so a stored candidate replays to itself
    assert iv.canonical_json(plain) != iv.canonical_json(pinned)                                # the identity DOES move for a full build


def test_the_verifier_rederives_the_pin_from_its_own_universe(db, ephe):
    good = _vector(db, str(ephe), scored_classes=list(writer_mod.SCORED_CLASSES))
    assert "scored_classes" in _ivv(db, good, str(ephe), require_scored_classes=True)["derived"]
    short = _vector(db, str(ephe), scored_classes=list(writer_mod.SCORED_CLASSES)[:-1])        # a builder that pinned 25 classes
    with pytest.raises(RuntimeError, match="scored_classes: independently derived"):
        _ivv(db, short, str(ephe), require_scored_classes=True)
    extra = _vector(db, str(ephe), scored_classes=list(writer_mod.SCORED_CLASSES) + ["birth_anchor"])
    with pytest.raises(RuntimeError, match="scored_classes: independently derived"):
        _ivv(db, extra, str(ephe), require_scored_classes=True)
    with pytest.raises(RuntimeError, match="pins no expected class census"):                   # REQUIRED for a real candidate
        _ivv(db, _vector(db, str(ephe)), str(ephe), require_scored_classes=True)
    _ivv(db, _vector(db, str(ephe)), str(ephe))                                                # a vector that predates the key is judged only when it carries one


# ── the verification job ────────────────────────────────────────────────────────────────────────────────────────────────

class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _Range:
    """A tstzrange stand-in with the two bounds the job reads."""
    from datetime import datetime as _dt, timezone as _tz
    lower, upper = _dt(2025, 1, 1, tzinfo=_tz.utc), _dt(2025, 3, 1, tzinfo=_tz.utc)


class _JobConn:
    """A connection that answers exactly the queries check_preconditions makes up to and including the per-class gap check, so the census can be
    judged in isolation: it refuses by name, writes nothing, and never reaches the heavier input check when the census is wrong."""

    def __init__(self, vector, inventories, partitions, status="candidate"):
        self.vector, self.inventories, self.partitions, self.status = vector, set(inventories), set(partitions), status
        self.writes = 0

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith(("INSERT", "UPDATE", "DELETE")):
            self.writes += 1
        if "FROM public.kala_gochara_publication" in s:
            return _Rows([(self.status, self.vector, _Range())])
        if "ka_gochara_generation_is_sealed" in s:
            return _Rows([(False,)])
        if s.startswith("SELECT event_class FROM public.ka_gochara_search_inventory"):
            return _Rows([(c,) for c in sorted(self.inventories)])
        if s.startswith("SELECT partition_key FROM public.kala_gochara_coverage"):
            claimed = self.partitions | (self.inventories if "UNION SELECT event_class FROM public.ka_gochara_search_inventory" in s else set())
            return _Rows([(c,) for c in sorted(claimed)])
        if s.startswith("SELECT i.inventory_digest IS NOT NULL"):
            return _Rows([(True, _Range(), _Range())]) if params[2] in self.inventories else _Rows([])
        raise AssertionError(f"the job made an unexpected query: {s[:140]}")


def _refusal(vector, inventories, partitions):
    conn = _JobConn(vector, inventories, partitions)
    with pytest.raises(vj.VerificationRefused) as exc:
        vj.check_preconditions(conn, chart_id=CHART_ID, generation="5.0", ephe_path="/x", modules={"geometry": ()})
    assert conn.writes == 0
    return exc.value


ALL26 = sorted(writer_mod.SCORED_CLASSES)


def test_the_job_refuses_25_of_26_by_name_before_writing_anything():
    err = _refusal({"scored_classes": ALL26}, ALL26[:-1], ALL26[:-1])
    assert err.code == "class_census_mismatch" and ALL26[-1] in err.detail and "missing" in err.detail


def test_the_job_refuses_an_extra_class_whether_claimed_by_inventory_or_by_partition_alone():
    both = _refusal({"scored_classes": ALL26}, ALL26 + ["birth_anchor"], ALL26 + ["birth_anchor"])
    assert both.code == "class_census_mismatch" and "birth_anchor" in both.detail
    partition_only = _refusal({"scored_classes": ALL26}, ALL26, ALL26 + ["birth_anchor"])
    assert partition_only.code == "class_census_mismatch" and "birth_anchor" in partition_only.detail


def test_the_job_refuses_an_unpinned_or_empty_pin():
    assert _refusal({"stored_scope": "stored_non_moon"}, ALL26, ALL26).code == "class_census_unpinned"
    assert _refusal({"scored_classes": None}, ALL26, ALL26).code == "class_census_unpinned"
    assert _refusal({"scored_classes": "marriage"}, ALL26, ALL26).code == "class_census_unpinned"          # not an array: the same name the SQL gives


@pytest.mark.parametrize("pin", [[], [{}], [1], [None], [["x"]], ["marriage", ""], ["marriage", " x"], ["marriage", "marriage"]])
def test_the_job_names_a_malformed_pin_before_any_set_operation_touches_it(pin):
    """Codex G8 amendment 3: a pin holding an unhashable or non-string element used to raise TypeError inside the set arithmetic; it is now a NAMED refusal
    (the SQL's expected_class_list_malformed), for every shape the seal-time function calls malformed."""
    assert _refusal({"scored_classes": pin}, ALL26, ALL26).code == "class_census_malformed"


def test_26_of_26_passes_the_census_and_reaches_the_input_check(monkeypatch):
    seen = {}

    def sentinel(conn, vec, **kw):
        seen["require"] = kw.get("require_scored_classes")
        raise RuntimeError("sentinel: past the census")
    monkeypatch.setattr(ivv, "verify_inputs", sentinel)
    conn = _JobConn({"scored_classes": ALL26}, ALL26, ALL26)
    with pytest.raises(vj.VerificationRefused) as exc:
        vj.check_preconditions(conn, chart_id=CHART_ID, generation="5.0", ephe_path="/x", modules={"geometry": ()})
    assert exc.value.code == "stale_inputs" and "sentinel" in exc.value.detail             # the census passed; the NEXT check ran
    assert seen["require"] is True                                                        # and it was told the pin is REQUIRED


# ── the database: the real chain, the real seal path ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def chain():
    import psycopg
    admin, name, dsn = create_am5_database("g8", faithful=True)
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        yield conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


def _def_sha(conn) -> str:
    return conn.execute("SELECT encode(sha256(convert_to(pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure),"
                        " 'UTF8')), 'hex')").fetchone()[0]


BEFORE_1306: dict = {}


def _function_identity(conn):
    return conn.execute("SELECT pg_get_userbyid(p.proowner), p.proacl::text, p.prosecdef, p.provolatile, p.proconfig::text, p.proleakproof, p.proparallel,"
                        " p.prorettype::regtype::text FROM pg_proc p WHERE p.oid = 'public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure").fetchone()


def _function_text(sql: str) -> str:
    a = sql.index("CREATE OR REPLACE FUNCTION public.ka_gochara_search_completeness_violations")
    return sql[a:sql.index("$$;", a) + 3]


def test_the_function_1306_replaces_is_exactly_what_1232_produces_and_what_production_holds(chain):
    assert _def_sha(chain) == PROD_1232_DEF_SHA256        # a fresh 1206 + 1232 chain reproduces production's function text byte for byte
    BEFORE_1306["identity"] = _function_identity(chain)    # owner, ACL, security mode, volatility, config: compared after 1306 is applied


def test_1306_equals_the_1232_function_with_exactly_the_declared_edits():
    old, new = _function_text(M1232.read_text()), _function_text(M1306.read_text())
    assert new != old
    # (a) one added declaration line, (b) one appended block after the 1232 Moon-scope call; nothing else differs
    old_lines, new_lines = old.split("\n"), new.split("\n")
    added = [ln for ln in new_lines if ln not in old_lines]
    removed = [ln for ln in old_lines if ln not in new_lines]
    assert removed == [], removed
    assert any("census_vec jsonb" in ln for ln in added)
    block_start = next(i for i, ln in enumerate(new_lines) if "G8 (1306): the EXPECTED CLASS CENSUS" in ln)
    assert "ka_gochara_search_moon_scope_violations(p_chart, p_generation);" in new_lines[block_start - 2] + new_lines[block_start - 3] + new_lines[block_start - 1]
    prefix_new = "\n".join(new_lines[:block_start - 1]).replace("\n  census_vec jsonb; pinned_classes text[]; claimed_classes text[];", "")
    assert old.startswith(prefix_new.rstrip()), "the 1232 body changed before the appended block"
    assert not re.search(r"\b(BEGIN|COMMIT)\b;", M1306.read_text()), "transaction ownership belongs to migrate.ts"


PUB_SQL = ("INSERT INTO public.kala_gochara_publication (manifest_id, chart_id, generation, writer_asset_id, convention_id, input_generation_vector,"
           " ephemeris_backend, horizon, row_counts, content_digest, status) VALUES (%s, %s, '5.0', 'ka_gochara', %s, %s::jsonb, '{}'::jsonb,"
           " tstzrange('2025-01-01+00', '2025-03-01+00'), '{}'::jsonb, 'x', %s)")
COV_SQL = ("INSERT INTO public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key, convention_id, requested_horizon, completed_horizon,"
           " resolution, relations_searched, targets_requested, targets_resolved, targets_unresolved, target_resolution_state_counts, build_id)"
           " VALUES (%s, '5.0', 'event_class', %s, %s, tstzrange('2025-01-01+00', '2025-03-01+00'), tstzrange('2025-01-01+00', '2025-03-01+00'),"
           " 1, ARRAY['conjunction'], 1, 1, 0, '{}'::jsonb, 'b')")
CONV = "sha256:" + "g8" * 32


def _candidate(conn, vector: dict | None, classes, status="published"):
    """A synthetic candidate for chart CHART_ID generation 5.0: one publication row and one event_class partition per class, written as the
    superuser under replica role (the guards under test are not what is being observed)."""
    if conn.execute("SELECT count(*) FROM public.kala_gochara_convention WHERE convention_id = %s", (CONV,)).fetchone()[0] == 0:
        conn.execute("INSERT INTO public.kala_gochara_convention (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source, epoch_convention,"
                     " time_scale, house_system, ephemeris_mode, method_version) VALUES (%s, 'sidereal', 'lahiri', 'm', 'mean', 's', 'e', 'ut', 'whole_sign', 'swiss', '1')", (CONV,))
    with conn.transaction():
        conn.execute("SET LOCAL session_replication_role = replica")
        conn.execute("DELETE FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = '5.0'", (CHART_ID,))
        conn.execute("DELETE FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", (CHART_ID,))
        conn.execute(PUB_SQL, (str(uuid.uuid4()), CHART_ID, CONV, json.dumps(vector if vector is not None else {"stored_scope": "stored_non_moon"}), status))
        for c in classes:
            conn.execute(COV_SQL, (CHART_ID, c, CONV))


def _census(conn) -> list[tuple[str, str]]:
    return [(r[0], r[1]) for r in conn.execute(
        "SELECT event_class, violation FROM public.ka_gochara_search_completeness_violations(%s::uuid, '5.0') WHERE violation = ANY(%s) ORDER BY 2, 1",
        (CHART_ID, list(CENSUS_VIOLATIONS))).fetchall()]


def _seal_message(conn) -> str:
    import psycopg
    try:
        with conn.transaction():
            conn.execute("INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)"
                         " SELECT chart_id, generation, manifest_id FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", (CHART_ID,))
        return "SEALED"
    except psycopg.Error as exc:
        return str(exc)


def test_before_1306_a_candidate_with_25_of_26_classes_is_not_refused_by_any_census_the_defect(chain):
    """THE G8 DEFECT, reproduced on the real 1206 + 1232 chain: the pre-1306 function reports no census violation for 25 of 26 classes, for 26 of 26, or for
    an absent pin — the census does not exist. (This is the mutant of every test below: they fail on this function.)"""
    assert _def_sha(chain) == PROD_1232_DEF_SHA256
    _candidate(chain, {"stored_scope": "stored_non_moon", "scored_classes": ALL26}, ALL26[:-1])
    assert _census(chain) == []
    assert "class_missing" not in _seal_message(chain)


def test_after_1306_the_census_refuses_25_of_26_an_extra_class_and_passes_26_of_26_of_the_CENSUS_only(chain):
    chain.execute(M1306.read_text())                                       # the real migration, applied as the owner (the test connection is the superuser)
    assert _def_sha(chain) != PROD_1232_DEF_SHA256
    vec = {"stored_scope": "stored_non_moon", "scored_classes": ALL26}
    # 26 of 26: no census violation
    _candidate(chain, vec, ALL26)
    assert _census(chain) == []
    assert "class_missing" not in _seal_message(chain) and "class_not_pinned" not in _seal_message(chain)       # the seal may refuse for OTHER reasons (synthetic rows), never the census
    # 25 of 26: exactly the absent class, by name, at the function AND at the seal
    _candidate(chain, vec, ALL26[:-1])
    assert _census(chain) == [(ALL26[-1], "class_missing")]
    msg = _seal_message(chain)
    assert msg != "SEALED" and "class_missing" in msg and ALL26[-1] in msg
    # 24 of 26: both absent classes
    _candidate(chain, vec, ALL26[1:-1])
    assert _census(chain) == [(ALL26[0], "class_missing"), (ALL26[-1], "class_missing")]
    # 26 + one extra
    _candidate(chain, vec, ALL26 + ["birth_anchor"])
    assert _census(chain) == [("birth_anchor", "class_not_pinned")]
    msg = _seal_message(chain)
    assert msg != "SEALED" and "class_not_pinned" in msg and "birth_anchor" in msg
    # a candidate that claims nothing at all: every pinned class is missing
    _candidate(chain, vec, [])
    assert len(_census(chain)) == 26 and {v for _, v in _census(chain)} == {"class_missing"}


@pytest.mark.parametrize("vector,violation", [
    ({"stored_scope": "stored_non_moon"}, "expected_class_list_missing"),
    ({"stored_scope": "stored_non_moon", "scored_classes": None}, "expected_class_list_missing"),
    ({"stored_scope": "stored_non_moon", "scored_classes": "marriage"}, "expected_class_list_missing"),
    ({"stored_scope": "stored_non_moon", "scored_classes": {"a": 1}}, "expected_class_list_missing"),
    ({"stored_scope": "stored_non_moon", "scored_classes": []}, "expected_class_list_malformed"),
    ({"stored_scope": "stored_non_moon", "scored_classes": ["marriage", "marriage"]}, "expected_class_list_malformed"),
    ({"stored_scope": "stored_non_moon", "scored_classes": ["marriage", 3]}, "expected_class_list_malformed"),
    ({"stored_scope": "stored_non_moon", "scored_classes": ["marriage", ""]}, "expected_class_list_malformed"),
    ({"stored_scope": "stored_non_moon", "scored_classes": ["marriage", " bereavement"]}, "expected_class_list_malformed"),
])
def test_an_absent_or_malformed_pin_refuses_the_seal_by_name(chain, vector, violation):
    _candidate(chain, vector, ALL26)
    assert _census(chain) == [("*", violation)]
    assert violation in _seal_message(chain)


def test_the_census_is_judged_only_against_the_published_manifest_the_seal_paths_own_precondition(chain):
    _candidate(chain, {"stored_scope": "stored_non_moon", "scored_classes": ALL26}, ALL26[:-1], status="candidate")
    assert _census(chain) == []


def test_a_slice_stamped_vector_is_refused_for_its_own_reason_and_the_census_is_a_second_one(chain):
    vec = {"stored_scope": "test_slice", "test_slice": {"schema": "gochara_v5_test_slice/1"}, "scored_classes": ALL26}
    _candidate(chain, vec, ALL26[:3])
    got = [r[1] for r in chain.execute("SELECT event_class, violation FROM public.ka_gochara_search_completeness_violations(%s::uuid, '5.0')", (CHART_ID,)).fetchall()]
    assert "stored_scope_missing" in got and "class_missing" in got


def test_1306_leaves_the_functions_owner_acl_security_mode_volatility_config_and_return_type_exactly_as_1232_made_them(chain):
    """What this proves: every catalog attribute that carries the 1241 verifier/sealer closure is IDENTICAL before and after 1306 (owner, proacl, security
    mode, volatility, proconfig incl. the pinned search_path, leakproof, parallel safety, return type) — recorded before 1306 was applied, compared after."""
    after = _function_identity(chain)
    assert BEFORE_1306["identity"] == after, (BEFORE_1306["identity"], after)
    assert after[2] is False and after[3] == "s" and after[4] == "{\"search_path=pg_catalog, public\"}"      # and still INVOKER, STABLE, the pinned search_path


# ── the census can only be switched off by a suite that says so, and the list of those suites is closed ───────────────────

from .conftest import G8_OPT_OUT_ALLOWLIST as G8_OPT_OUT_SUITES      # the ONE list; the fixture enforces membership, this guard enforces that the tree matches it


def _suite_sources():
    """Every test module under this directory, RECURSIVELY, keyed by its path relative to it."""
    root = Path(__file__).parent
    return {p.relative_to(root).as_posix(): p.read_text() for p in sorted(root.rglob("test_*.py")) if p.name != Path(__file__).name}


def test_exactly_the_listed_suites_opt_out_of_the_census_each_with_a_stated_reason():
    sources = _suite_sources()
    opted = {n for n, s in sources.items() if "g8_census_opt_out" in s}
    assert opted == G8_OPT_OUT_SUITES, (
        f"suites that opt out of the G8 class census must be exactly the reviewed list; unexpected {sorted(opted - G8_OPT_OUT_SUITES)}, "
        f"missing {sorted(G8_OPT_OUT_SUITES - opted)}")
    for name in sorted(opted):
        src = sources[name]
        m = re.search(r'^G8_CENSUS_OPT_OUT_REASON = "([^"]+)"$', src, re.M)
        assert m and len(m.group(1).strip()) >= 20, f"{name} opts out without a stated reason"
        assert re.search(r'^(pytestmark = |@)pytest\.mark\.usefixtures\("g8_census_opt_out"\)$', src, re.M), \
            f"{name} does not apply the opt-out as a module mark or a test decorator"


def test_nothing_else_replaces_or_patches_the_census_step():
    for name, src in _suite_sources().items():
        if name in G8_OPT_OUT_SUITES:
            continue
        assert "_enforce_class_census" not in src and "class_census_violations" not in src, \
            f"{name} touches the census step directly; opt out by name instead (conftest.g8_census_opt_out)"
    code = "\n".join(ln for ln in (Path(__file__).parent / "conftest.py").read_text().splitlines() if not ln.lstrip().startswith("#"))
    assert "_enforce_class_census" not in code.split("def g8_census_opt_out")[0] and "class_census_violations" not in code.split("def g8_census_opt_out")[0], \
        "the conftest must not patch the census anywhere but inside the named opt-out fixture"


def _unwrapped_fixture():
    from . import conftest as cf
    fn = cf.g8_census_opt_out
    return getattr(fn, "__wrapped__", None) or fn._get_wrapped_function()


class _Req:
    def __init__(self, path, reason="x" * 30, has_reason=True):
        import types
        mod = types.SimpleNamespace(__file__=str(path), __name__="m")
        if has_reason:
            mod.G8_CENSUS_OPT_OUT_REASON = reason
        self.module = mod


def test_the_opt_out_fixture_itself_refuses_an_unlisted_suite_and_a_missing_or_short_reason(monkeypatch):
    """Codex G8 amendment 2, behaviourally: the FIXTURE (not just a guard test) refuses a file that is not on the allowlist, and one with no usable reason,
    and only for a listed file with a reason does it set the census step aside."""
    fixture = _unwrapped_fixture()
    here = Path(__file__).resolve().parent
    with pytest.raises(pytest.UsageError, match="not on the G8 census opt-out allowlist"):
        fixture(_Req(here / "test_a53_inventory.py"), monkeypatch)                      # a real suite, but not a listed one
    with pytest.raises(pytest.UsageError, match="not on the G8 census opt-out allowlist"):
        fixture(_Req(here / "sub" / "test_a53_verification_job.py"), monkeypatch)      # a listed NAME in another directory is a different relative path
    with pytest.raises(pytest.UsageError, match="without a stated reason"):
        fixture(_Req(here / "test_a53_verification_job.py", has_reason=False), monkeypatch)
    with pytest.raises(pytest.UsageError, match="without a stated reason"):
        fixture(_Req(here / "test_a53_verification_job.py", reason="too short"), monkeypatch)
    real, real_v = vj._enforce_class_census, vj.class_census_violations
    fixture(_Req(here / "test_a53_verification_job.py"), monkeypatch)
    assert vj._enforce_class_census is not real and vj.class_census_violations(None, []) == []    # listed + reason: only then is the census set aside (job AND adapter)
    monkeypatch.undo()
    assert vj._enforce_class_census is real and vj.class_census_violations is real_v


# ── Codex G8 amendment 1: the brief (the candidate adapter) judges the census too ────────────────────────────────────────

SCENARIOS = [                                                           # (vector, claimed classes): every shape the census distinguishes
    ({"scored_classes": ALL26}, ALL26),
    ({"scored_classes": ALL26}, ALL26[:-1]),
    ({"scored_classes": ALL26}, ALL26[1:-1]),
    ({"scored_classes": ALL26}, ALL26 + ["birth_anchor"]),
    ({"scored_classes": ALL26}, []),
    ({"stored_scope": "stored_non_moon"}, ALL26),
    ({"scored_classes": None}, ALL26),
    ({"scored_classes": []}, ALL26),
    ({"scored_classes": ["marriage", ""]}, ALL26),
    ({"scored_classes": ["marriage", "marriage"]}, ALL26),
    ({"scored_classes": ["marriage", 3]}, ALL26),
]


@pytest.mark.parametrize("vector,claimed", SCENARIOS)
def test_the_python_census_equals_the_seal_time_function_for_every_scenario(chain, vector, claimed):
    """The job refusal and the candidate adapter use ONE python function; here it is held equal to the 1306 SQL function (names AND detail text), so the three
    surfaces (job, brief, seal) cannot disagree."""
    _candidate(chain, {"stored_scope": "stored_non_moon", **vector}, claimed, status="published")
    sql = sorted((r[0], r[1], r[2]) for r in chain.execute(
        "SELECT event_class, violation, detail FROM public.ka_gochara_search_completeness_violations(%s::uuid, '5.0') WHERE violation = ANY(%s)",
        (CHART_ID, list(CENSUS_VIOLATIONS))).fetchall())
    assert sorted(vj.class_census_violations({"stored_scope": "stored_non_moon", **vector}, claimed)) == sql


def test_the_candidate_adapter_and_so_the_brief_refuse_25_of_26_by_name(chain):
    """THE amendment-1 regression: on a CANDIDATE manifest (the only kind a brief is made for) the 1306 arms read nothing, so before this change the adapter
    returned no census violation and a 25-class candidate could be briefed and approved. Now the adapter names the missing class and the brief's own
    approvability check turns it into a problem."""
    from services.gochara_kernel import seal_brief
    vec = {"stored_scope": "stored_non_moon", "scored_classes": ALL26}
    _candidate(chain, vec, ALL26, status="candidate")
    full = vj.candidate_gate_on_candidate_manifest(chain, CHART_ID, "5.0")
    assert not [v for v in full if v["violation"] in CENSUS_VIOLATIONS]
    _candidate(chain, vec, ALL26[:-1], status="candidate")
    got = vj.candidate_gate_on_candidate_manifest(chain, CHART_ID, "5.0")
    assert [(v["event_class"], v["violation"]) for v in got if v["violation"] in CENSUS_VIOLATIONS] == [(ALL26[-1], "class_missing")]
    problems = seal_brief._current_and_complete({"candidate_gate": {"violations": got}, "classes": [], "legacy_projection": {},
                                                 "attestations": {"ka_gochara_search_inventory_verification": [1]},
                                                 "manifest": {"status": "candidate"}, "code": {}})
    assert any("class_missing" in str(p) and ALL26[-1] in str(p) for p in problems)         # the brief would be refused (BriefRefused: candidate_not_approvable)
    _candidate(chain, {"stored_scope": "stored_non_moon"}, ALL26, status="candidate")       # unpinned
    assert ("*", "expected_class_list_missing") in [(v["event_class"], v["violation"]) for v in vj.candidate_gate_on_candidate_manifest(chain, CHART_ID, "5.0")]
