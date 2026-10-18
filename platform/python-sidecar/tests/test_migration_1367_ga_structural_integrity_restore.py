"""Static test for migration 1367 (restores ga_structural's pre-1363 integrity_check_sql). Stdlib only, no database.

The embedded restore text must be byte-equal to the live text before 1363: the pre-1326 fixture plus migration 1326's single replacement
(md5 fcd217e25127653ee28ad41c629946aa, 208,378 chars). The guard must name migration 1363's text (md5 f49616e2...) as the only accepted start,
and the file must contain exactly one UPDATE, of one column of one row, with no transaction control.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_MIG_DIR = _HERE.parent.parent / "migrations"
MIG = (_MIG_DIR / "1367_ga_structural_integrity_restore_pre1363.sql").read_text()
M1363 = (_MIG_DIR / "1363_ga_structural_integrity_single_scan_speed.sql").read_text()
FIXTURE = (_HERE / "fixtures" / "ga_structural_1326" / "live_integrity_check_sql_pre1326_2026-10-07.sql").read_text()

TO_MD5, TO_LEN = "fcd217e25127653ee28ad41c629946aa", 208378
FROM_MD5, FROM_LEN = "f49616e257f9a85de4f0cebf09fe2603", 209602
_L1326_OLD_LINE = "          WHEN re.retrograde_flag = 'retrograde' THEN 'weak'\n"
_L1326_NEW_BLOCK = (
    "          -- Migration 1326 (node exclusion): the mean nodes Rahu/Ketu are always retrograde and ga_positions stores\n"
    "          -- retrograde_flag 'retrograde' for them (N-185/N-187), but the retrograde composite downgrade does NOT apply to the\n"
    "          -- nodes (their re_dignity is always 'neutral'); a node row therefore stays 'neutral'. Tara grahas are unchanged.\n"
    "          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'\n"
)


def _embedded() -> str:
    m = re.search(r"c_to_text\s+constant text := \$ot\$(.*?)\$ot\$;", MIG, re.S)
    assert m, "restore text literal not found"
    return m.group(1)


def test_embedded_text_is_the_pre_1363_live_text():
    t = _embedded()
    assert len(t) == TO_LEN and hashlib.md5(t.encode()).hexdigest() == TO_MD5
    assert t == FIXTURE.replace(_L1326_OLD_LINE, _L1326_NEW_BLOCK)
    assert MIG.count("$ot$") == 2


def test_guard_names_1363_text_and_this_text():
    assert f"c_from_md5 constant text := '{FROM_MD5}'" in MIG
    assert f"c_to_md5   constant text := '{TO_MD5}'" in MIG
    m = re.search(r"c_new_text constant text := \$nt\$(.*?)\$nt\$;", M1363, re.S)
    assert m and len(m.group(1)) == FROM_LEN and hashlib.md5(m.group(1).encode()).hexdigest() == FROM_MD5


def test_one_update_one_row_no_transaction_control():
    code = re.sub(r"\$ot\$.*?\$ot\$", "''", MIG, flags=re.S)
    code = "\n".join(l for l in code.splitlines() if not l.lstrip().startswith("--"))
    assert len(re.findall(r"^\s*UPDATE\b", code, re.M)) == 1 and code.count("FOR UPDATE") == 1
    assert re.search(r"UPDATE asset_registry\s+SET integrity_check_sql = c_to_text\s+WHERE asset_id = 'ga_structural'\s+AND md5\(integrity_check_sql\) = c_from_md5;", code)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code.replace("BEGIN\n", ""))
    assert not re.search(r"\b(DROP|DELETE|TRUNCATE|CREATE|ALTER|EXECUTE|DISABLE TRIGGER)\b", code, re.I)
    assert "SET LOCAL lock_timeout = '5s';" in code
