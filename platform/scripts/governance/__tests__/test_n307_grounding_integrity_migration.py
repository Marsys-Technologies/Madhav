"""test_n307_grounding_integrity_migration.py: SS N-307 migration 1343 and the integrity detector it installs, on a DISPOSABLE PostgreSQL.

bo_grounding now stores a yoga row's `target_id` as the firing's natural key (`yoga_canonical_id`) instead of the renumbering serial `ga_yoga_firings.id`. The registry's integrity detector (migration 1032, a
set-based rewrite of 899) resolved a yoga row through `f.id::text`, so it would go RED after the first rebuild with the new writer, and the new writer would fail its own integrity probe. Migration 1343 moves the
detector onto the stable identity and keeps a TRANSITION tolerance for rows still carrying the old serial form. Proof, on real SQL:

  detector     legacy rows are green; new rows are green; both forms for one firing, a missing / duplicate / unresolvable row, a bad tier and a sruti row without its rule are red; 1032's detector is
               RED on new rows (the reason the migration is needed)
  migration    installs from 899's text and from 1032's text, is idempotent, refuses any other text, a missing row, and a detector that is red on current data (rolling back), updates exactly one row
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _disposable_pg import disposable_pg  # noqa: E402,F401

MIGRATIONS = HERE.parents[2] / "migrations"
M1343 = MIGRATIONS / "1343_bo_grounding_integrity_target_id_natural_key.sql"
M1032 = MIGRATIONS / "1032_nirmana_l2_bo_grounding_set_based_integrity.sql"
M899 = MIGRATIONS / "899_nirmana_l2_bo_grounding_registry_row.sql"

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART = "1c826d5a-0000-0000-0000-000000000000"
AYA = "lahiri_chitrapaksha"
SIG1 = "11111111-1111-1111-1111-111111111111"
SIG2 = "22222222-2222-2222-2222-222222222222"


def _body(path: pathlib.Path) -> str:
    return re.search(r"\$ICHECK\$(.*?)\$ICHECK\$", path.read_text(encoding="utf-8"), re.S).group(1)


NEW_SQL, SQL_1032, SQL_899 = _body(M1343), _body(M1032), _body(M899)
H = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()  # noqa: E731


def lit(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


SCHEMA = """
DROP TABLE IF EXISTS asset_registry, ga_yoga_firings, bodha_msr_signals, bodha_grounding_matches CASCADE;
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text);
CREATE TABLE ga_yoga_firings (id serial PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, yoga_canonical_id text NOT NULL, fired boolean NOT NULL DEFAULT true,
                              UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id));
CREATE TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL);
CREATE TABLE bodha_grounding_matches (chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, target_kind text NOT NULL, target_id text NOT NULL, grounding_tier text NOT NULL, matched_rule_id text);
"""


def reset(cl, registry_sql: str | None = None):
    cl.psql(SCHEMA)
    cl.psql(f"INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id, fired) VALUES "
            f"('{CHART}', '{AYA}', 'gajakesari', true), ('{CHART}', '{AYA}', 'chandra_mangala', true), ('{CHART}', '{AYA}', 'not_fired', false)")
    cl.psql(f"INSERT INTO bodha_msr_signals VALUES ('{SIG1}', '{CHART}', '{AYA}'), ('{SIG2}', '{CHART}', '{AYA}')")
    if registry_sql is not None:
        cl.psql(f"INSERT INTO asset_registry VALUES ('bo_grounding', {lit(registry_sql)})")


def ids(cl):
    return {r.split("|")[1]: r.split("|")[0] for r in cl.psql("SELECT id, yoga_canonical_id FROM ga_yoga_firings").splitlines()}


def ground(cl, rows):
    for kind, tid, tier, rule in rows:
        cl.psql(f"INSERT INTO bodha_grounding_matches VALUES ('{CHART}', '{AYA}', '{kind}', {lit(tid)}, '{tier}', {('NULL' if rule is None else lit(rule))})")


def detector(cl, sql: str) -> bool:
    return cl.psql(sql.strip().rstrip(";")) == "t"


def green_rows(cl, form: str):
    """The complete, valid grounding set for the seeded chart: both fired yogas and both MSR signals, once each. form = 'new' (yoga_canonical_id) | 'legacy' (the serial)."""
    sid = ids(cl)
    yoga = {"new": ("gajakesari", "chandra_mangala"), "legacy": (sid["gajakesari"], sid["chandra_mangala"])}[form]
    return [("yoga_dosha_firing", yoga[0], "sruti", "r-01"), ("yoga_dosha_firing", yoga[1], "yukti", "r-02"),
            ("msr_signal", SIG1, "pratyaksa", None), ("msr_signal", SIG2, "yukti", "r-03")]


# ───────────────────────── the detector ─────────────────────────

def test_legacy_rows_are_green_before_the_rebuild_and_new_rows_after_it(disposable_pg):
    for form in ("legacy", "new"):
        reset(disposable_pg)
        ground(disposable_pg, green_rows(disposable_pg, form))
        assert detector(disposable_pg, NEW_SQL) is True, form


def test_the_old_detector_would_go_red_on_new_rows_which_is_why_the_migration_exists(disposable_pg):
    reset(disposable_pg)
    ground(disposable_pg, green_rows(disposable_pg, "legacy"))
    assert detector(disposable_pg, SQL_1032) is True                                                   # 1032 is green on the old serial identity ...
    reset(disposable_pg)
    ground(disposable_pg, green_rows(disposable_pg, "new"))
    assert detector(disposable_pg, SQL_1032) is False                                                  # ... and RED on the new identity: the new writer would fail its own probe
    assert detector(disposable_pg, NEW_SQL) is True


@pytest.mark.parametrize("name, mutate", [
    ("a fired yoga with no grounding row", lambda r: [x for x in r if x[1] != "gajakesari"]),
    ("a fired yoga grounded twice", lambda r: r + [("yoga_dosha_firing", "gajakesari", "yukti", "r-09")]),
    ("an MSR signal with no grounding row", lambda r: [x for x in r if x[1] != SIG2]),
    ("an MSR signal grounded twice", lambda r: r + [("msr_signal", SIG1, "yukti", "r-09")]),
    ("a grounding row for a firing that does not exist", lambda r: r + [("yoga_dosha_firing", "no_such_yoga", "pratyaksa", None)]),
    ("a grounding row for a serial that is no firing", lambda r: r + [("yoga_dosha_firing", "999999", "pratyaksa", None)]),
    ("a grounding row for an MSR signal that does not exist", lambda r: r + [("msr_signal", "33333333-3333-3333-3333-333333333333", "pratyaksa", None)]),
    ("a tier outside the vocabulary", lambda r: [("yoga_dosha_firing", "gajakesari", "shruti", "r-01")] + [x for x in r if x[1] != "gajakesari"]),
    ("a sruti row without its rule", lambda r: [("yoga_dosha_firing", "gajakesari", "sruti", None)] + [x for x in r if x[1] != "gajakesari"]),
])
def test_forgery_each_broken_invariant_reads_red(disposable_pg, name, mutate):
    reset(disposable_pg)
    ground(disposable_pg, mutate(green_rows(disposable_pg, "new")))
    assert detector(disposable_pg, NEW_SQL) is False, name


def test_forgery_the_same_firing_in_both_identity_forms_is_a_duplicate_not_a_pass(disposable_pg):
    reset(disposable_pg)
    sid = ids(disposable_pg)
    ground(disposable_pg, green_rows(disposable_pg, "new") + [("yoga_dosha_firing", sid["gajakesari"], "yukti", "r-09")])
    assert detector(disposable_pg, NEW_SQL) is False                                                   # two rows for one firing: match_count 2


def test_a_firing_that_did_not_fire_needs_no_grounding_row(disposable_pg):
    reset(disposable_pg)
    ground(disposable_pg, green_rows(disposable_pg, "new"))
    assert detector(disposable_pg, NEW_SQL) is True                                                    # 'not_fired' (fired = false) has none


def test_another_chart_without_grounding_is_not_a_built_chart(disposable_pg):
    reset(disposable_pg)
    ground(disposable_pg, green_rows(disposable_pg, "new"))
    disposable_pg.psql(f"INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id) VALUES ('{OTHER_CHART}', '{AYA}', 'gajakesari')")
    disposable_pg.psql(f"INSERT INTO bodha_msr_signals VALUES ('44444444-4444-4444-4444-444444444444', '{OTHER_CHART}', '{AYA}')")
    assert detector(disposable_pg, NEW_SQL) is True                                                    # only charts that have grounding rows are required to be fully grounded


def test_the_serial_form_of_one_chart_does_not_resolve_another_charts_firing(disposable_pg):
    reset(disposable_pg)
    disposable_pg.psql(f"INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id) VALUES ('{OTHER_CHART}', '{AYA}', 'gajakesari')")
    other_serial = disposable_pg.psql(f"SELECT id FROM ga_yoga_firings WHERE chart_id = '{OTHER_CHART}'")
    rows = [x for x in green_rows(disposable_pg, "new") if x[1] != "gajakesari"] + [("yoga_dosha_firing", other_serial, "sruti", "r-01")]
    ground(disposable_pg, rows)
    assert detector(disposable_pg, NEW_SQL) is False                                                   # the serial belongs to ANOTHER chart's firing: it resolves nothing here


# ───────────────────────── the migration ─────────────────────────

def apply(cl, path=M1343):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL"))}
    env.update(cl.env())
    return subprocess.run([str(cl.bin_dir / "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(path)], capture_output=True, text=True, env=env, timeout=120)


def registry(cl):
    """The installed detector's fingerprint, computed IN THE DATABASE the way the migration computes it (psql output is trimmed, so hashing the printed text would lose the leading / trailing newlines)."""
    return cl.psql("SELECT encode(sha256(convert_to(integrity_check_sql, 'UTF8')), 'hex') FROM asset_registry WHERE asset_id = 'bo_grounding'")


def test_the_guard_fingerprints_in_the_file_match_the_texts_they_name():
    text = M1343.read_text(encoding="utf-8")
    assert "266ed3d30f63f601f1f5a8f515da147e272d0fcd7f9afe52f8861925d2b2800e" in text and H(SQL_899) == "266ed3d30f63f601f1f5a8f515da147e272d0fcd7f9afe52f8861925d2b2800e"
    assert H(SQL_1032) in text
    assert "ICHECK" not in NEW_SQL


@pytest.mark.parametrize("start, label", [(SQL_1032, "from 1032's detector"), (SQL_899, "from 899's detector")])
def test_the_migration_installs_the_new_detector_and_is_idempotent(disposable_pg, start, label):
    reset(disposable_pg, registry_sql=start)
    ground(disposable_pg, green_rows(disposable_pg, "legacy"))                                          # the state before the first rebuild with the new writer
    p = apply(disposable_pg)
    assert p.returncode == 0, p.stderr[-500:]
    assert registry(disposable_pg) == H(NEW_SQL), label
    assert apply(disposable_pg).returncode == 0                                                         # replay: the fingerprint is the new one, accepted
    assert registry(disposable_pg) == H(NEW_SQL)
    assert disposable_pg.psql("SELECT count(*) FROM asset_registry") == "1"


def test_the_migration_refuses_an_unexpected_detector_text_and_changes_nothing(disposable_pg):
    reset(disposable_pg, registry_sql="SELECT true -- someone's hand edit")
    p = apply(disposable_pg)
    assert p.returncode != 0 and "unexpected bo_grounding detector fingerprint" in p.stderr
    assert registry(disposable_pg) == H("SELECT true -- someone's hand edit")


def test_the_migration_refuses_a_missing_registry_row(disposable_pg):
    reset(disposable_pg)
    p = apply(disposable_pg)
    assert p.returncode != 0 and "registry row or integrity detector is missing" in p.stderr


def test_the_migration_rolls_back_when_the_new_detector_is_red_on_current_data(disposable_pg):
    reset(disposable_pg, registry_sql=SQL_1032)
    ground(disposable_pg, green_rows(disposable_pg, "legacy")[:-1])                                     # an MSR signal with no grounding row: a real integrity failure
    p = apply(disposable_pg)
    assert p.returncode != 0 and "red on current data" in p.stderr
    assert registry(disposable_pg) == H(SQL_1032)                                                    # the transaction rolled back: the old detector is still installed


def test_the_migration_updates_exactly_one_row_and_only_bo_grounding(disposable_pg):
    reset(disposable_pg, registry_sql=SQL_1032)
    disposable_pg.psql("INSERT INTO asset_registry VALUES ('bo_other', 'SELECT 1')")
    ground(disposable_pg, green_rows(disposable_pg, "legacy"))
    assert apply(disposable_pg).returncode == 0
    assert disposable_pg.psql("SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bo_other'") == "SELECT 1"


# ───────────────────────── review of #3368 (Kāla): the ayanamsha predicates on the identity joins must be pinned ─────────────────────────

AYA2 = "raman"


def _two_ayanamsha_setup(cl):
    """The same yoga fires under TWO ayanamshas of one chart (two firing rows, two serials); grounding must be per (chart, ayanamsha, firing)."""
    reset(cl)
    cl.psql(f"INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id, fired) VALUES ('{CHART}', '{AYA2}', 'gajakesari', true), ('{CHART}', '{AYA2}', 'chandra_mangala', true)")
    sid = {(r.split("|")[0], r.split("|")[1]): r.split("|")[2] for r in cl.psql("SELECT ayanamsha_id, yoga_canonical_id, id FROM ga_yoga_firings").splitlines()}
    return sid


def _ground_aya(cl, aya, rows):
    for kind, tid, tier, rule in rows:
        cl.psql(f"INSERT INTO bodha_grounding_matches VALUES ('{CHART}', '{aya}', '{kind}', {lit(tid)}, '{tier}', {('NULL' if rule is None else lit(rule))})")


def _both_ayanamshas_grounded_in_new_form(cl):
    for aya in (AYA, AYA2):
        _ground_aya(cl, aya, [("yoga_dosha_firing", "gajakesari", "sruti", "r-01"), ("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")])
    for aya in (AYA, AYA2):
        for sig in (SIG1, SIG2):
            cl.psql(f"INSERT INTO bodha_msr_signals VALUES ({lit(sig if aya == AYA else sig.replace('1', '3').replace('2', '4'))}, '{CHART}', '{aya}') ON CONFLICT DO NOTHING")
        _ground_aya(cl, aya, [("msr_signal", sig if aya == AYA else sig.replace("1", "3").replace("2", "4"), "pratyaksa", None) for sig in (SIG1, SIG2)])


def test_two_ayanamshas_each_fully_grounded_in_the_new_form_are_green(disposable_pg):
    _two_ayanamsha_setup(disposable_pg)
    _both_ayanamshas_grounded_in_new_form(disposable_pg)
    assert detector(disposable_pg, NEW_SQL) is True


def test_forgery_the_serial_of_a_firing_under_ANOTHER_ayanamsha_resolves_nothing(disposable_pg):
    sid = _two_ayanamsha_setup(disposable_pg)
    # ayanamsha 1 is grounded, but its gajakesari row carries the SERIAL of the RAMAN firing: without the ayanamsha predicate on the legacy join it would resolve to 'gajakesari' and the cell would read green
    for aya in (AYA, AYA2):
        for sig in (SIG1, SIG2) if aya == AYA else ("33333333-3333-3333-3333-333333333333", "44444444-4444-4444-4444-444444444444"):
            disposable_pg.psql(f"INSERT INTO bodha_msr_signals VALUES ('{sig}', '{CHART}', '{aya}') ON CONFLICT DO NOTHING")
            _ground_aya(disposable_pg, aya, [("msr_signal", sig, "pratyaksa", None)])
    _ground_aya(disposable_pg, AYA, [("yoga_dosha_firing", sid[(AYA2, "gajakesari")], "sruti", "r-01"), ("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")])
    _ground_aya(disposable_pg, AYA2, [("yoga_dosha_firing", "gajakesari", "sruti", "r-01"), ("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")])
    assert detector(disposable_pg, NEW_SQL) is False
    # the test has teeth: the SAME data reads GREEN under the detector with that predicate deleted
    assert "AND fl.ayanamsha_id = g.ayanamsha_id" in NEW_SQL
    assert detector(disposable_pg, NEW_SQL.replace("AND fl.ayanamsha_id = g.ayanamsha_id", "")) is True


def test_forgery_a_firing_grounded_under_one_ayanamsha_does_not_ground_the_same_yoga_under_another(disposable_pg):
    _two_ayanamsha_setup(disposable_pg)
    _both_ayanamshas_grounded_in_new_form(disposable_pg)
    disposable_pg.psql(f"DELETE FROM bodha_grounding_matches WHERE ayanamsha_id = '{AYA2}' AND target_id = 'gajakesari'")
    assert detector(disposable_pg, NEW_SQL) is False                                                    # (chart, raman, gajakesari) now has no row, though (chart, lahiri, gajakesari) does
    assert detector(disposable_pg, NEW_SQL.replace("AND fl.ayanamsha_id = g.ayanamsha_id", "").replace("AND fn.ayanamsha_id = g.ayanamsha_id", "")) is False


def test_forgery_the_new_form_join_needs_its_chart_and_ayanamsha_predicates_to_stay_in_the_text():
    for needle in ("fn.chart_id = g.chart_id", "fn.ayanamsha_id = g.ayanamsha_id", "fl.chart_id = g.chart_id", "fl.ayanamsha_id = g.ayanamsha_id"):
        assert needle in NEW_SQL, needle


# ───────────────────────── review of #3368 (Kāla): TWO BUILT CHARTS firing the same yoga give the chart predicates real coverage ─────────────────────────

CHART_B = "1c826d5a-0000-0000-0000-000000000000"
SIG_B1, SIG_B2 = "55555555-5555-5555-5555-555555555555", "66666666-6666-6666-6666-666666666666"


def _two_built_charts(cl):
    """Chart A (the seeded one) and chart B both fire gajakesari and chandra_mangala under the same ayanamsha, each with its own serials, and BOTH are built (they have grounding rows)."""
    reset(cl)
    cl.psql(f"INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id, fired) VALUES ('{CHART_B}', '{AYA}', 'gajakesari', true), ('{CHART_B}', '{AYA}', 'chandra_mangala', true)")
    cl.psql(f"INSERT INTO bodha_msr_signals VALUES ('{SIG_B1}', '{CHART_B}', '{AYA}'), ('{SIG_B2}', '{CHART_B}', '{AYA}')")
    return {(r.split("|")[0], r.split("|")[1]): r.split("|")[2] for r in cl.psql("SELECT chart_id, yoga_canonical_id, id FROM ga_yoga_firings").splitlines()}


def _ground_chart(cl, chart, rows):
    for kind, tid, tier, rule in rows:
        cl.psql(f"INSERT INTO bodha_grounding_matches VALUES ('{chart}', '{AYA}', '{kind}', {lit(tid)}, '{tier}', {('NULL' if rule is None else lit(rule))})")


def _msr(chart):
    return [("msr_signal", s, "pratyaksa", None) for s in ((SIG1, SIG2) if chart == CHART else (SIG_B1, SIG_B2))]


def test_two_built_charts_each_fully_grounded_are_green(disposable_pg):
    _two_built_charts(disposable_pg)
    for ch in (CHART, CHART_B):
        _ground_chart(disposable_pg, ch, [("yoga_dosha_firing", "gajakesari", "sruti", "r-01"), ("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")] + _msr(ch))
    assert detector(disposable_pg, NEW_SQL) is True


def test_forgery_the_serial_of_ANOTHER_charts_firing_resolves_nothing_even_when_both_charts_are_built(disposable_pg):
    sid = _two_built_charts(disposable_pg)
    # chart A's gajakesari row carries the SERIAL of chart B's gajakesari firing: without the chart predicate on the legacy join it resolves to 'gajakesari' under chart A and the cell reads green
    _ground_chart(disposable_pg, CHART, [("yoga_dosha_firing", sid[(CHART_B, "gajakesari")], "sruti", "r-01"), ("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")] + _msr(CHART))
    _ground_chart(disposable_pg, CHART_B, [("yoga_dosha_firing", "gajakesari", "sruti", "r-01"), ("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")] + _msr(CHART_B))
    assert detector(disposable_pg, NEW_SQL) is False
    assert "AND fl.chart_id = g.chart_id" in NEW_SQL
    assert detector(disposable_pg, NEW_SQL.replace("AND fl.chart_id = g.chart_id", "")) is True                         # the same data is green without the predicate: the test has teeth


def test_forgery_a_firing_grounded_for_one_chart_does_not_ground_the_same_yoga_of_another_chart(disposable_pg):
    _two_built_charts(disposable_pg)
    _ground_chart(disposable_pg, CHART, [("yoga_dosha_firing", "gajakesari", "sruti", "r-01"), ("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")] + _msr(CHART))
    _ground_chart(disposable_pg, CHART_B, [("yoga_dosha_firing", "chandra_mangala", "yukti", "r-02")] + _msr(CHART_B))        # chart B's gajakesari has no grounding row
    assert detector(disposable_pg, NEW_SQL) is False
    # and the new-form join: removing the chart predicate from it must not turn this green either (the source side is per chart)
    assert detector(disposable_pg, NEW_SQL.replace("AND fn.chart_id = g.chart_id", "").replace("AND fl.chart_id = g.chart_id", "")) is False
