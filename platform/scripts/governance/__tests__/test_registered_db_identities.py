"""test_registered_db_identities.py: the committed registry of cluster identities is well-formed (E1.7(b), SS N-119)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FILE = ROOT / "00_ARCHITECTURE" / "control" / "REGISTERED_DB_IDENTITIES.json"


def _doc():
    return json.loads(FILE.read_text(encoding="utf-8"))


def test_schema_and_entries_are_closed_and_well_formed():
    d = _doc()
    assert set(d) == {"schema", "_doc", "entries"} and d["schema"] == "nikasha_registered_db_identities/1"
    assert d["entries"], "no registered identity"
    seen = set()
    for e in d["entries"]:
        assert set(e) == {"role", "database", "system_id_sha256", "hash_definition", "decision", "evidence"}, e
        assert e["role"] in {"production"} and re.fullmatch(r"[A-Za-z0-9_.$-]{1,63}", e["database"])
        assert re.fullmatch(r"[0-9a-f]{64}", e["system_id_sha256"])
        assert re.fullmatch(r"SS N-\d+.*", e["decision"])
        assert isinstance(e["evidence"], list) and len(e["evidence"]) >= 2 and all(isinstance(x, str) and x.strip() for x in e["evidence"]), "two independent reads required"
        key = (e["role"], e["database"], e["system_id_sha256"])
        assert key not in seen
        seen.add(key)


def test_no_secret_shaped_content():
    raw = FILE.read_text(encoding="utf-8").lower()
    for bad in ("password", "postgres://", "postgresql://", "host=", "pgpassword", "@127.0.0.1", ".sql.goog", "user=", "sslmode", "port="):
        assert bad not in raw
    assert not re.search(r"\b\d{12,}\b", raw), "a long digit run (a raw system identifier?) must never be committed"
    assert not re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", raw), "an IP address must never be committed"


def test_one_production_entry_per_database_and_the_evidence_abbreviation_matches_the_hash():
    d = _doc()
    prod = [e for e in d["entries"] if e["role"] == "production"]
    assert len({e["database"] for e in prod}) == len(prod), "two production entries for one database"
    for e in prod:
        h = e["system_id_sha256"]
        abbr = f"{h[:8]}...{h[-4:]}"
        assert sum(abbr in line for line in e["evidence"]) >= 2, "each independent read must quote the registered hash (abbreviated)"
        assert len(set(e["evidence"])) == len(e["evidence"]), "identical evidence lines are not two independent reads"
        assert e["hash_definition"] == "sha256('nikasha-db-identity/1:' + system_identifier) as lowercase hex"
