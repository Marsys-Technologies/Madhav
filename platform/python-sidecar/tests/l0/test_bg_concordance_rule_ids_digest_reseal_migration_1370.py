"""Migration 1370: bg_concordance's stored check re-sealed after the rules table dropped 8 consequence-less rules (3,002 -> 2,994, migration 1368).

PURE FILE-READING TEST (no database): the OLD text embedded in 1370 equals the text of migration 619 (the contract that set it) byte for byte; the NEW text is the OLD with EXACTLY
ONE replacement (the sha256 content digest literal); the migration is runner-owned, guarded on exactly two starting states, touches ONE registry row and ONE column, does not
execute the stored check (the live projection is the pre-run one until the governed rebuild), and names ONLY the one asset it re-seals (a re-seal that names another asset id,
even in a comment, would reopen that asset's build window). The digests are the measured ones: the real writer replayed over the live corpus (control: the 3,002-rule corpus
reproduces the OLD pin; the 2,994-rule corpus gives the NEW digest on two hash seeds), recomputed independently by the Engine.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parents[4]
_NAME = "1370_bg_concordance_rule_ids_digest_reseal.sql"
_MIG = _REPO / "platform" / "migrations" / _NAME
_M619 = _REPO / "platform" / "supabase" / "migrations" / "619_nirmana_l0_concordance_integrity_contract.sql"
_SEED = _REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"

OLD_DIGEST = "9e2837388c783be0dc57361e52d8de344b2b041f9bb5e9eb39fa4b67412f5893"
NEW_DIGEST = "a19bebde564c17c4ae39b883da3bf206122a3803098cca0b3de8087001152525"
OLD_MD5, NEW_MD5, LEN = "4327da1774c67a35a43ed0c2e2a19fe2", "c4dd504f6a112569a176d749489f6bbd", 1994
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()

MIG = _MIG.read_text()
CODE = "\n".join(l for l in MIG.splitlines() if not l.lstrip().startswith("--"))
OLD_TEXT = re.search(r"old_check constant text := \$oldcheck\$(.*?)\$oldcheck\$;", MIG, re.S).group(1)
NEW_TEXT = re.search(r"new_check constant text := \$newcheck\$(.*?)\$newcheck\$;", MIG, re.S).group(1)


def _const(name: str) -> str:
    return re.search(rf"\b{name}\s+constant\s+text\s*:=\s*'([^']*)'", MIG).group(1)


def test_number_is_free_and_unique():
    assert _MIG.name == _NAME and _MIG.exists()
    assert sorted(p.name for p in (_REPO / "platform" / "migrations").glob("1370_*")) == [_NAME]
    assert not list((_REPO / "platform" / "supabase" / "migrations").glob("1370_*"))


def test_old_text_is_the_619_contract_text():
    m619 = _M619.read_text()
    assert OLD_TEXT.strip("\n") in m619, "the embedded OLD check is not the text migration 619 stored"
    assert md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == LEN
    assert OLD_TEXT.count(OLD_DIGEST) == 1
    assert _const("old_md5") == OLD_MD5 and _const("old_digest") == OLD_DIGEST


def test_new_text_is_old_with_exactly_the_digest_replaced():
    assert md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == LEN
    assert _const("new_md5") == NEW_MD5 and _const("new_digest") == NEW_DIGEST
    assert OLD_TEXT.replace(OLD_DIGEST, NEW_DIGEST) == NEW_TEXT
    assert NEW_TEXT.count(NEW_DIGEST) == 1 and OLD_DIGEST not in NEW_TEXT and NEW_DIGEST not in OLD_TEXT
    diff = [(a, b) for a, b in zip(OLD_TEXT.split("\n"), NEW_TEXT.split("\n")) if a != b]
    assert diff == [(f"    '{OLD_DIGEST}'", f"    '{NEW_DIGEST}'")]
    for clause in ("count(*) = 721", "count(DISTINCT topic_id) = 361", "cardinality(rule_ids) > 0) = 721", "FROM sutravali_rules AS rule", "WHERE rule.rule_id = source.rule_id"):
        assert clause in NEW_TEXT and clause in OLD_TEXT          # the other clauses, incl. the rule-existence one, are untouched


def test_runner_owned_two_start_states_one_row_one_column():
    assert not re.search(r"^\s*(BEGIN(\s+TRANSACTION|\s+WORK)?|COMMIT|ROLLBACK|END|START\s+TRANSACTION)\s*;", CODE, re.M | re.I)
    assert "registry_row.integrity_check_sql IS DISTINCT FROM old_check" in CODE
    assert "registry_row.target_floor IS DISTINCT FROM 721" in CODE
    assert "registry_row.volume_explanation IS DISTINCT FROM canonical_explanation" in CODE
    assert "registry_row.natural_key_partition IS DISTINCT FROM canonical_partition" in CODE
    assert "registry_row.integrity_check_sql IS NOT DISTINCT FROM new_check" in CODE and "RAISE NOTICE" in CODE
    assert "migration 1370 refuses unknown bg_concordance registry state" in CODE and "migration 1370 refuses: no bg_concordance registry row" in CODE
    upd = re.search(r"^\s*UPDATE\s+asset_registry\b.*?;", CODE, re.S | re.M).group(0)
    assert re.findall(r"^\s*SET\s+(\w+)\s*=", upd, re.M) == ["integrity_check_sql"]
    for g in ("md5(integrity_check_sql) = old_md5", "target_floor = 721", "volume_explanation = canonical_explanation", "natural_key_partition = canonical_partition"):
        assert g in upd
    assert re.findall(r"^\s*UPDATE\s+(\w+)", CODE, re.M) == ["asset_registry"]
    assert "changed_rows <> 1" in CODE and "update did not take" in CODE
    for forbidden in (r"\bINSERT\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"DISABLE\s+TRIGGER", r"\bEXECUTE\b"):
        assert not re.search(forbidden, CODE, re.I), forbidden
    assert "SET LOCAL lock_timeout" in CODE


def test_registered_floor_partition_and_explanation_are_what_the_guard_expects():
    m619 = _M619.read_text()
    assert "target_floor" in m619 and "721" in m619
    assert _const("canonical_partition") == "classical_attributions.(topic_id,school)"
    expl = re.search(r"canonical_explanation constant text := \$expl\$(.*?)\$expl\$;", MIG, re.S).group(1)
    assert expl.startswith("721 deterministic topic×school concordance rows") and "canonical 3,002-rule projection" in expl
    assert expl in _SEED.read_text() or expl in m619 or "canonical 3,002-rule projection" in m619     # the stale prose is deliberately left as registered


def test_the_migration_names_exactly_one_asset_id():
    """Naming another asset id (even in a comment) would reopen that asset's build window (Build.history). Every registry asset id is checked against the file."""
    ids = set(re.findall(r"asset_id\s*(?:=|:)\s*'([a-z0-9_]+)'", CODE))
    assert ids == {"bg_concordance"}, ids
    others = set(re.findall(r"(?<![A-Za-z0-9_])((?:bg|ga|bo|ka|ph|mi)_[a-z0-9_]+)(?![A-Za-z0-9_])", MIG)) - {"bg_concordance"}
    assert not others, f"asset-id-shaped names in the migration: {sorted(others)}"
