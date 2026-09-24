"""K-1/V-1 (migration 1084): the held ka_kshetra -> ka_gochara edge must stay out.

`depends_on` is a hard build gate (asset_runner requires a dependency to be `lit`; the
dependencies also feed the upstream hash), and the edge's target is doubtful — see the
header of 1084. It is the Kṣetra stream's own declaration to apply or decline. This
file makes re-adding it here a deliberate act, not a drive-by.
"""
from __future__ import annotations

import re
from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[4] / "migrations" / "1084_wp7_k1_v1_registry_edges.sql"


def _executable_sql() -> str:
    return "\n".join(l for l in MIGRATION.read_text().splitlines() if not l.lstrip().startswith("--"))


def test_the_held_ka_gochara_edge_is_not_added_to_kshetra():
    sql = _executable_sql()
    assert not re.search(r"array_append\(depends_on,\s*'ka_gochara'\)", sql), (
        "1084 must not add ka_gochara to any depends_on: it would gate every Kṣetra build "
        "on the W2G writer (held pending the Kṣetra stream's decision)"
    )


def test_the_service_seam_edges_are_still_declared():
    sql = _executable_sql()
    for asset in ("ka_kshetra", "ka_sangam"):
        assert re.search(
            r"array_append\(depends_on,\s*'ka_vedha_gochara'\)\s*WHERE asset_id = '%s'" % asset,
            re.sub(r"\s+", " ", sql),
        ), f"{asset} -> ka_vedha_gochara (authority seam) is missing"


def test_migration_stays_idempotent():
    sql = _executable_sql()
    assert sql.count("array_append") == sql.count("NOT (depends_on @>"), (
        "every append must be guarded by a NOT (depends_on @> …) predicate"
    )
