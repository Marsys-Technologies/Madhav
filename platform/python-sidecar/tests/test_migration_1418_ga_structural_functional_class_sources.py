"""Verify the functional-class registry migration against the exact predecessor."""
import hashlib
import re
from pathlib import Path


PLATFORM = Path(__file__).resolve().parents[2]
MIGRATIONS = PLATFORM / "migrations"
BEFORE = "b746387fd48e2a7df4383d48433afc79"
AFTER = "cacc07d6ce4f610ee031f6d56f89394e"


def _literal(sql, tag):
    marker = f"${tag}$"
    assert sql.count(marker) == 2
    return sql.split(marker)[1]


def _md5(sql):
    return hashlib.md5(sql.encode()).hexdigest()


def test_functional_class_splice_matches_the_deployed_predecessor():
    restore = (MIGRATIONS / "1367_ga_structural_integrity_restore_pre1363.sql").read_text()
    first_build = (MIGRATIONS / "1414_ga_structural_integrity_first_build_fixes.sql").read_text()
    sql = _literal(restore, "ot")
    for number in range(1, 6):
        old = _literal(first_build, f"o{number}")
        assert sql.count(old) == 1
        sql = sql.replace(old, _literal(first_build, f"n{number}"))
    assert _md5(sql) == BEFORE

    migration = (PLATFORM / "supabase/migrations/1418_ga_structural_functional_class_sources.sql").read_text()
    for clause in ("school", "lordship"):
        old = _literal(migration, f"old_{clause}")
        assert sql.count(old) == 1
        sql = sql.replace(old, _literal(migration, f"new_{clause}"))
    assert _md5(sql) == AFTER
    assert f"expected_before constant text := '{BEFORE}'" in migration
    assert f"expected_after constant text := '{AFTER}'" in migration
    assert len(re.findall(r"^\s*UPDATE public\.asset_registry\b", migration, re.M)) == 1
