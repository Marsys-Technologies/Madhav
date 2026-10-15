"""Migration 1366: bg_rules' integrity_check_sql re-sealed after the writer change of commit 829d8db1d (#3435) moved the sutravali_rules content digest.

PURE FILE-READING TEST (no database, no server): it reads migration 1366, migration 618 (the OLD check) and the sibling re-seal conventions (1361, 1365).
It asserts: the migration number is free and unique; the OLD text embedded in 1366 equals migration 618's rules_check byte for byte; the NEW text is the OLD with
EXACTLY ONE replacement (the sha256 content digest literal); the migration is runner-owned (no BEGIN/COMMIT), guarded on exactly two starting states, touches ONE
asset_registry row, does not execute the stored check (the table still holds the old rows until the governed bg_rules rebuild), and refuses to run while the NEW digest
is not filled in. `test_new_digest_and_md5_are_filled_in` FAILS LOUDLY until /Users/Dev/suvarna-evidence/N431/fill_bg_rules_reseal_digest.sh <64-hex> has been run with
the measured digest; it is the only test that depends on the fill.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parents[4]
_NAME = "1366_bg_rules_integrity_digest_reseal.sql"
_MIG = _REPO / "platform" / "migrations" / _NAME
_M618 = _REPO / "platform" / "supabase" / "migrations" / "618_nirmana_l0_rules_integrity_contract.sql"

OLD_DIGEST = "87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd"
OLD_MD5, OLD_LEN = "7c155f20d9a983b3c86586007c01550d", 1463
# Filled by fill_bg_rules_reseal_digest.sh (the md5 is computed by the script from the NEW check text, never typed).
NEW_DIGEST = "1a0c275d9c175cef7df07825985f52dfb06e50c87fca84707530df3f959915c5"
NEW_MD5 = "b70718d7b77040c435f0aee2c436b287"

_PLACEHOLDER_FRAGMENT = "PLACEHOLDER" + "_REPLACE_ME"     # built by concatenation so the fill script never rewrites this line
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()

MIG = _MIG.read_text()
CODE = "\n".join(l for l in MIG.splitlines() if not l.lstrip().startswith("--"))   # SQL without comment lines
OLD_618 = re.search(r"rules_check constant text := \$check\$(.*?)\$check\$;", _M618.read_text(), re.S).group(1)
OLD_TEXT = re.search(r"old_check constant text := \$oldcheck\$(.*?)\$oldcheck\$;", MIG, re.S).group(1)
NEW_TEXT = re.search(r"new_check constant text := \$newcheck\$(.*?)\$newcheck\$;", MIG, re.S).group(1)


def _const(name: str) -> str:
    return re.search(rf"\b{name}\s+constant\s+text\s*:=\s*'([^']*)'", MIG).group(1)


def test_number_is_free_and_unique():
    assert _MIG.name == _NAME and _MIG.exists()
    for d in ("migrations", "supabase/migrations"):
        taken = sorted(p.name for p in (_REPO / "platform" / d).glob("1366_*"))
        assert taken == ([_NAME] if d == "migrations" else []), f"migration number 1366 not unique in platform/{d}: {taken}"
    assert not list((_REPO / "platform" / "migrations").glob("1366[!_]*"))


def test_old_text_is_migration_618_rules_check_byte_for_byte():
    assert OLD_TEXT == OLD_618
    assert md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == OLD_LEN
    assert OLD_TEXT.count(OLD_DIGEST) == 1
    assert _const("old_md5") == OLD_MD5 and _const("old_digest") == OLD_DIGEST


def test_new_text_is_old_with_exactly_one_replacement():
    assert NEW_TEXT.count(NEW_DIGEST) == 1 and OLD_DIGEST not in NEW_TEXT and NEW_DIGEST not in OLD_TEXT
    assert OLD_TEXT.replace(OLD_DIGEST, NEW_DIGEST) == NEW_TEXT
    old_lines, new_lines = OLD_TEXT.split("\n"), NEW_TEXT.split("\n")
    assert len(old_lines) == len(new_lines)
    diff = [(a, b) for a, b in zip(old_lines, new_lines) if a != b]
    assert diff == [(f"    '{OLD_DIGEST}'", f"    '{NEW_DIGEST}'")]          # one line, only the quoted digest literal
    # the nine other clauses are still there, untouched
    for clause in ("count(*) = 3002", "count(DISTINCT rule_id) = 3002", "extracted_by = 'python_regex_v2') = 3002",
                   "confidence < 0.600 OR quality_score < 0.600) = 0", "confidence IS DISTINCT FROM quality_score) = 0",
                   "yoga_canonical_id IS NOT NULL) = 17", "dasha_system_id IS NOT NULL) = 0", "transit_marker IS TRUE) = 25",
                   "NOT EXISTS (", "FROM sutravali_rules\n"):
        assert clause in NEW_TEXT and clause in OLD_TEXT


def test_migration_is_runner_owned_and_guarded_on_exactly_two_states():
    assert not re.search(r"^\s*(BEGIN(\s+TRANSACTION|\s+WORK)?|COMMIT|ROLLBACK|END|START\s+TRANSACTION)\s*;", CODE, re.M | re.I)    # transaction ownership belongs to migrate.ts (the plpgsql BEGIN of the DO block is not a transaction statement)
    assert not re.search(r"\b(SAVEPOINT|PREPARE\s+TRANSACTION)\b", CODE, re.I)
    # starting-state guards: OLD text, floor, explanation, partition; the converged NEW state is a NOTICE no-op; anything else RAISES
    assert "registry_row.integrity_check_sql IS DISTINCT FROM old_check" in CODE
    assert "registry_row.target_floor IS DISTINCT FROM 3002" in CODE
    assert "registry_row.volume_explanation IS DISTINCT FROM canonical_explanation" in CODE
    assert "registry_row.natural_key_partition IS DISTINCT FROM canonical_partition" in CODE
    assert "canonical_partition constant text := 'sutravali_rules.rule_id'" in CODE
    assert "registry_row.integrity_check_sql IS NOT DISTINCT FROM new_check" in CODE and "RAISE NOTICE" in CODE
    assert "migration 1366 refuses unknown bg_rules registry state" in CODE and "migration 1366 refuses: no bg_rules registry row" in CODE
    # the md5 guards are part of the UPDATE itself
    upd = re.search(r"^\s*UPDATE\s+asset_registry\b.*?;", CODE, re.S | re.M).group(0)
    for g in ("md5(integrity_check_sql) = old_md5", "target_floor = 3002", "volume_explanation = canonical_explanation", "natural_key_partition = canonical_partition"):
        assert g in upd
    assert "changed_rows <> 1" in CODE and "update did not take" in CODE
    # canonical explanation is migration 618's, character for character
    expl618 = re.search(r"canonical_explanation constant text :=\s*((?:'[^']*'\s*)+);", _M618.read_text()).group(1)
    expl1366 = re.search(r"canonical_explanation constant text :=\s*((?:'[^']*'\s*)+);", MIG).group(1)
    assert expl618 == expl1366


def test_exactly_one_registry_row_and_no_other_writes():
    updates = re.findall(r"^\s*UPDATE\s+(\w+)", CODE, re.M)       # statements only (the RAISE messages mention the word update)
    assert updates == ["asset_registry"]                                  # one UPDATE statement, one table
    upd = re.search(r"^\s*UPDATE\s+asset_registry\b.*?;", CODE, re.S | re.M).group(0)
    assert re.search(r"^\s*WHERE\s+asset_id\s*=\s*'bg_rules'\s*$", upd, re.M)
    assert re.findall(r"SET\s+(\w+)\s*=", upd) == ["integrity_check_sql"]    # sets that one column and no other
    assert len(re.findall(r"asset_id\s*=\s*'([a-z_]+)'", CODE)) == 3 and set(re.findall(r"asset_id\s*=\s*'([a-z_]+)'", CODE)) == {"bg_rules"}
    for forbidden in (r"\bINSERT\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"DISABLE\s+TRIGGER", r"\bEXECUTE\b"):
        assert not re.search(forbidden, CODE, re.I), forbidden             # EXECUTE: the postflight does NOT run the stored check (rows are old until the governed rebuild)
    assert "SET LOCAL lock_timeout" in CODE


def test_migration_refuses_to_run_while_digest_or_md5_is_not_real_hex():
    assert "new_digest !~ '^[0-9a-f]{64}$' OR new_md5 !~ '^[0-9a-f]{32}$'" in CODE
    assert "RAISE EXCEPTION 'migration 1366 refuses: the NEW digest / NEW check md5 constants are not filled in" in CODE
    # the self-consistency assertions that bind the NEW text to the OLD text and to the stated md5 at run time
    assert "replace(old_check, old_digest, new_digest) IS DISTINCT FROM new_check" in CODE and "md5(new_check) <> new_md5" in CODE and "md5(old_check) <> old_md5" in CODE
    # the placeholder guard sits before any registry access
    assert CODE.index("constants are not filled in") < CODE.index("FROM asset_registry WHERE asset_id = 'bg_rules'")


def test_new_digest_and_md5_are_filled_in():
    """FAILS until fill_bg_rules_reseal_digest.sh <64-hex> has been run: the NEW digest is measured, not guessed."""
    assert _PLACEHOLDER_FRAGMENT not in MIG, "migration 1366 still carries the NEW-digest/NEW-md5 placeholder: run /Users/Dev/suvarna-evidence/N431/fill_bg_rules_reseal_digest.sh <64-hex>"
    assert _PLACEHOLDER_FRAGMENT not in NEW_DIGEST + NEW_MD5, "this test file still carries the placeholder constants: run the fill script"
    assert re.fullmatch(r"[0-9a-f]{64}", NEW_DIGEST), NEW_DIGEST
    assert re.fullmatch(r"[0-9a-f]{32}", NEW_MD5), NEW_MD5
    assert NEW_DIGEST != OLD_DIGEST
    assert _const("new_digest") == NEW_DIGEST and _const("new_md5") == NEW_MD5
    assert md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == OLD_LEN               # a 64-hex digest replaces a 64-hex digest: same length
    assert NEW_TEXT.count(NEW_DIGEST) == 1
