"""SR-TR26-HARNESS-1410 (ruling OPTION A) — the trial database carries migration 1410 (public.ka_gochara_build_ledger, the committed-substep ledger of the century build).

Measured defect (ky-tr-vm, run 20261025T1236Z26 at d1febbc0a): the trial DB had MIGRATIONS + overlay 250/1401/1402/1403 but never 1410; completion-probe died with
ResumeRefused("build_ledger_absent: public.ka_gochara_build_ledger does not exist — apply migration 1410 before a century build") from build_ledger.load.

One oracle per distinct claim; the single planted reversion that fails it is named in each docstring.  Doctrine: ruling condition (1) 1410 is MANDATORY, the real file applied as production applies it,
and the harness REFUSES FIRST without it.  (Condition 2, the writer / IMPLEMENTATION_MODULES untouched, is checked by century_contract.py --check, not by a test that would rot on later branches.)  §N.8: each read-back below is a detector that can read false."""
import re
from pathlib import Path

import pytest

import trial_slice as ts
from test_baseline_overlay_skip import _NoDatabase, checkout, no_database      # noqa: F401  (fixtures: the checkout's disposable-DB guard is replaced by a stop)

M1410 = "1410_ka_gochara_build_ledger.sql"
LEDGER_CODE = {"build_ledger.py": 'TABLE = "ka_gochara_build_ledger"\nSQL = "SELECT 1 FROM public.ka_gochara_build_ledger"\n'}      # what the writer's ledger module says
MAIN_LIKE = {"window_sweep.py": "def qualification():\n    return {'policy': 'x'}\n"}                                                    # a checkout with no ledger code
REAL_CHECKOUT_MIGRATIONS = Path(__file__).resolve().parents[6] / "platform" / "migrations"       # the repository this harness lives in


def _century_checkout(tmp_path, *, with_1410, services):
    """Every file setup_lane checks before it touches a database: MIGRATIONS, 250/1401/1402, and 1410 only when asked."""
    co = checkout(tmp_path, with_1402=True, with_1410=with_1410, services=services)
    for f in ts.MIGRATIONS:
        (co / "platform" / "migrations" / f).write_text("-- stub\n")
    return co


# ── claim 0 (REQUIRED, ruling condition 1): a century-shape trial setup WITHOUT 1410 refuses FIRST — before any database exists, so before any substep ───────────────────────────────

def test_a_trial_setup_without_1410_refuses_first_by_name(tmp_path, no_database, capsys):
    """Reversion: make 1410 non-mandatory (or drop it from OVERLAY_MIGRATIONS) → setup_lane gets past planning and reaches the database step (_NoDatabase), not Refused."""
    co = _century_checkout(tmp_path, with_1410=False, services=LEDGER_CODE)
    with pytest.raises(ts.Refused):                                  # not _NoDatabase: no database was created, so no substep can have run
        ts.setup_lane({"baseline_mode": False}, co, tmp_path / "out")
    assert f"overlay migration file missing in the checkout: {M1410}" in capsys.readouterr().err


def test_1410_is_mandatory_and_the_last_overlay_file():
    """Reversion: flip the mandatory flag of 1410 to False, or put it ahead of 250 (it is applied in numeric order, after the files it follows in production)."""
    plan = {f: m for f, m, _t in ts.OVERLAY_MIGRATIONS}
    assert plan[M1410] is True
    assert [f for f, _m, _t in ts.OVERLAY_MIGRATIONS][-1] == M1410


# ── claim c: baseline mode may skip 1410 BY NAME only when the checkout lacks the ledger code; one WITH it refuses (SR-BASELINE-OVERLAY-SKIP) ─────────────────────────────────────────────

def test_baseline_mode_skips_1410_by_name_when_the_checkout_has_no_ledger_code(tmp_path):
    """Reversion: drop the skip branch for a mandatory file in plan_overlay → Refused here."""
    co = checkout(tmp_path, with_1410=False, services=MAIN_LIKE)
    todo, skipped = ts.plan_overlay(co / "platform" / "migrations", lambda t: True, baseline_checkout=co)
    assert M1410 not in todo and "baseline mode" in skipped[M1410] and "no code that requires it" in skipped[M1410]


def test_baseline_mode_refuses_1410_when_the_checkout_has_the_ledger_code(tmp_path, capsys):
    """Reversion: make the 1410 probe pattern never match (e.g. a wrong table name in OVERLAY_REQUIRING_CODE) → the missing file is skipped and no Refused is raised."""
    co = checkout(tmp_path, with_1410=False, services=LEDGER_CODE)
    with pytest.raises(ts.Refused):
        ts.plan_overlay(co / "platform" / "migrations", lambda t: True, baseline_checkout=co)
    assert f"{M1410} (baseline mode does not skip it" in capsys.readouterr().err


def test_the_1410_probe_reads_production_python_not_a_test_that_names_the_table(tmp_path):
    """Reversion: drop the tests/test_* exclusion in requiring_code (every test mentions the table; main's baseline would then refuse for a name in a test)."""
    co = checkout(tmp_path, with_1410=False, services={"test_ledger.py": "ka_gochara_build_ledger\n"})
    tdir = co / "platform" / "python-sidecar" / "services" / "tests"
    tdir.mkdir()
    (tdir / "helper.py").write_text("ka_gochara_build_ledger\n")
    assert ts.requiring_code(co, M1410) == []
    assert ts.requiring_code(_century_checkout(tmp_path / "w", with_1410=False, services=LEDGER_CODE), M1410) == ["platform/python-sidecar/services/gochara_kernel/build_ledger.py"]


# ── claim a: the REAL 1410 text applies on the AM5 stub as it is (no edit), its effect read-back reads TRUE only afterwards, and the writer's ledger load stops raising ─────────────────────

@pytest.fixture
def stub_db():
    inv = pytest.importorskip("tests.l3.gochara.test_a53_inventory")           # the checkout's own AM5 stub + guard (KY_TEST_CHECKOUT puts its sidecar on sys.path)
    admin, name, dsn = inv.create_am5_database("h1410", apply_1305=True)
    try:
        yield dsn
    finally:
        inv.drop_am5_database(admin, name)


def test_the_real_1410_applies_on_the_stub_and_the_effect_reads_false_before_and_true_after(stub_db):
    """Reversion: make OVERLAY_EFFECTS['1410'] constant TRUE (reads true before the apply), or drop the table check from it (an unapplied 1410 would not read false); and with 1410's prerequisite
    tables absent from the stub the real file RAISES (printed below) — the stub carries both today, which is what lets the harness apply 1410 unedited."""
    import psycopg
    mig = REAL_CHECKOUT_MIGRATIONS / M1410
    assert mig.is_file(), mig
    with psycopg.connect(stub_db, autocommit=True) as conn:
        assert conn.execute("SELECT to_regclass('public.charts') IS NOT NULL AND to_regclass('public.kala_gochara_publication') IS NOT NULL").fetchone()[0] is True
        assert conn.execute(ts.OVERLAY_EFFECTS["1410"]).fetchone()[0] is False          # before: a detector that CAN read false (not NULL)
        with conn.transaction():
            conn.execute(mig.read_text(encoding="utf-8"))                                  # the real file text, exactly as the harness applies an overlay
        assert conn.execute(ts.OVERLAY_EFFECTS["1410"]).fetchone()[0] is True


def test_1410_fails_closed_on_a_stub_without_its_prerequisite_tables(stub_db):
    """The premise of 'apply cleanly WITHOUT editing 1410': the file refuses when public.kala_gochara_publication is missing, so the harness must not run it on a DB lacking it (reversion: none; this pins
    that the fail-closed guard is real, so the clean apply above is a measurement and not an absent check)."""
    import psycopg
    with psycopg.connect(stub_db, autocommit=True) as conn:
        conn.execute("DROP TABLE public.kala_gochara_publication CASCADE")
        with pytest.raises(psycopg.errors.RaiseException, match="prerequisite table"):
            with conn.transaction():
                conn.execute((REAL_CHECKOUT_MIGRATIONS / M1410).read_text(encoding="utf-8"))


def test_the_writers_ledger_load_raises_build_ledger_absent_without_1410_and_not_with_it(stub_db):
    """Completion-probe's century path (ka_gochara_v5.plan_substeps -> _resume_plan -> build_ledger.load).  Reversion: leave 1410 out of the harness's applied list → the second half raises
    ResumeRefused('build_ledger_absent') exactly as in the ky-tr-vm run; the first half is the control that the detector can read false."""
    import psycopg
    bl = pytest.importorskip("services.gochara_kernel.build_ledger")
    with psycopg.connect(stub_db, autocommit=True) as conn:
        with pytest.raises(bl.ResumeRefused) as e:
            bl.load(conn, ts.CHART, ts.GENERATION)
        assert e.value.code == "build_ledger_absent"
        conn.execute((REAL_CHECKOUT_MIGRATIONS / M1410).read_text(encoding="utf-8"))
        assert bl.load(conn, ts.CHART, ts.GENERATION) == []


# ── claim a (end to end, local only: needs the approved canonical-L1 export): setup_lane itself builds the trial DB with 1410, in the overlay order, and the writer's load is satisfied ──────────

def test_setup_lane_builds_a_trial_database_that_carries_1410(tmp_path):
    """Reversion: drop 1410 from OVERLAY_MIGRATIONS → 'overlay_applied' lacks it, the effect key is absent and the ledger table does not exist (build_ledger.load raises build_ledger_absent)."""
    import os
    import psycopg
    if not (ts.EXPORT / "manifest.json").is_file():
        pytest.skip(f"the approved canonical-L1 export is not on this machine ({ts.EXPORT})")
    pytest.importorskip("tests.l3.gochara.test_a53_inventory")
    bl = pytest.importorskip("services.gochara_kernel.build_ledger")
    co = REAL_CHECKOUT_MIGRATIONS.parents[1]
    if not (co / "platform" / "python-sidecar" / "services" / "gochara_kernel" / "build_ledger.py").is_file():
        pytest.skip("the checkout under test has no build_ledger.py")
    cwd, env = os.getcwd(), dict(os.environ)
    state = {"job": ts.job_name(tmp_path), "db": None, "baseline_mode": False, "code": {"checkout": str(co)}}
    try:
        ts.bind_checkout(co)
        ts.setup_lane(state, co, tmp_path)
        lane = state["lane"]
        assert M1410 in lane["overlay_applied"] and lane["overlay_applied"][-1] == M1410
        assert lane["overlay_effects_present"]["1410"] is True
        assert lane["overlay_sha256"][M1410] == ts.sha_file(co / "platform" / "migrations" / M1410)             # the REAL file, byte for byte — never a copy
        with psycopg.connect(ts.dsn_for(state["db"]), autocommit=True) as conn:
            assert conn.execute("SELECT to_regclass('public.ka_gochara_build_ledger') IS NOT NULL").fetchone()[0] is True
            assert bl.load(conn, ts.CHART, ts.GENERATION) == []
    finally:
        if state.get("db"):
            ts.drop_db(state, tmp_path)
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(env)


# ── TR-HARNESS-MIGRATION-PARITY: the harness's migration set covers what the writer's ledger code requires, DERIVED from the code and the migration files (not a list typed here) ────────────

def _writer_required_migrations(co: Path) -> dict:
    """{migration file: why}: the file(s) that CREATE the table build_ledger.py's TABLE names, and every 'apply migration NNNN' its refusal text names."""
    svc = co / "platform" / "python-sidecar" / "services" / "gochara_kernel" / "build_ledger.py"
    text = svc.read_text(encoding="utf-8")
    table = re.search(r'^TABLE = "([a-z_0-9]+)"', text, re.M).group(1)
    need: dict = {}
    for p in sorted((co / "platform" / "migrations").glob("*.sql")):
        if re.search(r"CREATE TABLE (?:IF NOT EXISTS )?public\.%s\b" % re.escape(table), p.read_text(encoding="utf-8")):
            need[p.name] = f"creates public.{table}"
    for num in re.findall(r"apply migration (\d{3,4})\b", text):
        match = sorted((co / "platform" / "migrations").glob(f"{num}_*.sql"))
        assert len(match) == 1, (num, match)
        need[match[0].name] = f"named by the writer's refusal text ('apply migration {num}')"
    return need


def test_the_harness_database_setup_covers_every_migration_the_writers_ledger_requires():
    """Reversion: drop 1410 from OVERLAY_MIGRATIONS (and from MIGRATIONS) → the file the writer's own TABLE / refusal text names is not in the harness set."""
    co = REAL_CHECKOUT_MIGRATIONS.parents[1]
    if not (co / "platform" / "python-sidecar" / "services" / "gochara_kernel" / "build_ledger.py").is_file():
        pytest.skip("the checkout under test has no build_ledger.py")
    need = _writer_required_migrations(co)
    assert M1410 in need, need                                          # the derivation itself finds 1410 (a derivation that finds nothing would pass vacuously)
    applied = set(ts.MIGRATIONS) | {f for f, _m, _t in ts.OVERLAY_MIGRATIONS} | {"1305_gochara_snapshot_owns_l1_copy.sql"}
    assert not (set(need) - applied), {f: why for f, why in need.items() if f not in applied}
