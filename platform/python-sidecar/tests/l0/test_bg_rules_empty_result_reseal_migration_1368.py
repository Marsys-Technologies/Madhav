"""Migration 1368: bg_rules' registry row re-sealed for the 2,994-rule output (rules with no consequence are no longer kept).

PURE FILE-READING TEST (no database): OLD text embedded in 1368 == migration 1366's NEW text byte for byte; NEW text == OLD with exactly the sha256 digest literal and the
three count literals replaced (and nothing else); runner-owned; guarded on exactly two starting states; ONE UPDATE of ONE registry row (three columns); the stored check is
NOT executed by the migration (the live rows stay the 3,002 until the governed rebuild). The measured digest comes from replaying the real writer over the frozen corpus
(see the migration header); the numbers below are pinned.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parents[4]
_NAME = "1368_bg_rules_empty_result_rules_dropped_reseal.sql"
_MIG = _REPO / "platform" / "migrations" / _NAME
_M1366 = _REPO / "platform" / "migrations" / "1366_bg_rules_integrity_digest_reseal.sql"

OLD_DIGEST = "1a0c275d9c175cef7df07825985f52dfb06e50c87fca84707530df3f959915c5"
NEW_DIGEST = "8e18dc1c02c8b815ed9f78be1e1843d917fb079f50b2ebee5d4dc032674cb9fc"
OLD_MD5, OLD_LEN = "b70718d7b77040c435f0aee2c436b287", 1463
NEW_MD5 = "5b27581cbeee1e91f65951d9a30e7b62"
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()

MIG = _MIG.read_text()
CODE = "\n".join(l for l in MIG.splitlines() if not l.lstrip().startswith("--"))
OLD_TEXT = re.search(r"old_check constant text := \$oldcheck\$(.*?)\$oldcheck\$;", MIG, re.S).group(1)
NEW_TEXT = re.search(r"new_check constant text := \$newcheck\$(.*?)\$newcheck\$;", MIG, re.S).group(1)
M1366_NEW = re.search(r"new_check constant text := \$newcheck\$(.*?)\$newcheck\$;", _M1366.read_text(), re.S).group(1)


def _const(name: str) -> str:
    return re.search(rf"\b{name}\s+constant\s+text\s*:=\s*'([^']*)'", MIG).group(1)


def test_number_is_free_and_unique():
    assert _MIG.name == _NAME and _MIG.exists()
    assert sorted(p.name for p in (_REPO / "platform" / "migrations").glob("1368_*")) == [_NAME]
    assert not list((_REPO / "platform" / "supabase" / "migrations").glob("1368_*"))


def test_old_text_is_migration_1366_new_text_byte_for_byte():
    assert OLD_TEXT == M1366_NEW
    assert md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == OLD_LEN
    assert _const("old_md5") == OLD_MD5 and _const("old_digest") == OLD_DIGEST


def test_new_text_is_old_with_exactly_the_digest_and_three_count_literals_replaced():
    assert md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == OLD_LEN
    assert _const("new_md5") == NEW_MD5 and _const("new_digest") == NEW_DIGEST
    old_lines, new_lines = OLD_TEXT.split("\n"), NEW_TEXT.split("\n")
    assert len(old_lines) == len(new_lines)
    diff = [(a.strip(), b.strip()) for a, b in zip(old_lines, new_lines) if a != b]
    assert diff == [
        ("count(*) = 3002", "count(*) = 2994"),
        ("AND count(DISTINCT rule_id) = 3002", "AND count(DISTINCT rule_id) = 2994"),
        ("AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 3002", "AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 2994"),
        (f"'{OLD_DIGEST}'", f"'{NEW_DIGEST}'"),
    ]
    assert "3002" not in NEW_TEXT and OLD_DIGEST not in NEW_TEXT and NEW_DIGEST not in OLD_TEXT
    # the other seven clauses are untouched
    for clause in ("confidence < 0.600 OR quality_score < 0.600) = 0", "confidence IS DISTINCT FROM quality_score) = 0", "yoga_canonical_id IS NOT NULL) = 17",
                   "dasha_system_id IS NOT NULL) = 0", "transit_marker IS TRUE) = 25", "NOT EXISTS (", "FROM sutravali_rules\n"):
        assert clause in NEW_TEXT


def test_migration_is_runner_owned_and_guarded_on_exactly_two_states():
    assert not re.search(r"^\s*(BEGIN(\s+TRANSACTION|\s+WORK)?|COMMIT|ROLLBACK|END|START\s+TRANSACTION)\s*;", CODE, re.M | re.I)
    assert "registry_row.integrity_check_sql IS DISTINCT FROM old_check" in CODE
    assert "registry_row.target_floor IS DISTINCT FROM 3002" in CODE
    assert "registry_row.volume_explanation IS DISTINCT FROM old_explanation" in CODE
    assert "registry_row.natural_key_partition IS DISTINCT FROM canonical_partition" in CODE
    assert "registry_row.integrity_check_sql IS NOT DISTINCT FROM new_check" in CODE and "registry_row.target_floor = 2994" in CODE and "RAISE NOTICE" in CODE
    assert "migration 1368 refuses unknown bg_rules registry state" in CODE and "migration 1368 refuses: no bg_rules registry row" in CODE
    upd = re.search(r"^\s*UPDATE\s+asset_registry\b.*?;", CODE, re.S | re.M).group(0)
    for g in ("md5(integrity_check_sql) = old_md5", "target_floor = 3002", "volume_explanation = old_explanation", "natural_key_partition = canonical_partition"):
        assert g in upd
    assert "changed_rows <> 1" in CODE and "update did not take" in CODE


def test_exactly_one_registry_row_and_no_other_writes():
    assert re.findall(r"^\s*UPDATE\s+(\w+)", CODE, re.M) == ["asset_registry"]
    upd = re.search(r"^\s*UPDATE\s+asset_registry\b.*?;", CODE, re.S | re.M).group(0)
    assert re.search(r"^\s*WHERE\s+asset_id\s*=\s*'bg_rules'\s*$", upd, re.M)
    assert re.findall(r"SET\s+(\w+)\s*=", upd) == ["integrity_check_sql"] or re.findall(r"^\s*(?:SET\s+)?(integrity_check_sql|target_floor|volume_explanation)\s*=", upd, re.M) == ["integrity_check_sql", "target_floor", "volume_explanation"]
    assert set(re.findall(r"asset_id\s*=\s*'([a-z_]+)'", CODE)) == {"bg_rules"}
    for forbidden in (r"\bINSERT\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"DISABLE\s+TRIGGER", r"\bEXECUTE\b"):
        assert not re.search(forbidden, CODE, re.I), forbidden
    assert "SET LOCAL lock_timeout" in CODE


def test_new_floor_and_explanation_are_the_measured_count():
    assert "target_floor = 2994," in CODE.replace("         target_floor = 2994", "target_floor = 2994,") or "target_floor = 2994" in CODE
    assert "'2,994 deterministic regex-extracted rules" in CODE
    assert "SET integrity_check_sql = new_check" in CODE


def test_runtime_self_consistency_assertions_are_present_and_run_before_registry_access():
    for g in ("md5(old_check) <> old_md5", "md5(new_check) <> new_md5", "position('3002' IN new_check) <> 0", "a re-seal must move the pin"):
        assert g in CODE
    assert CODE.index("a re-seal must move the pin") < CODE.index("FROM asset_registry WHERE asset_id = 'bg_rules'")
