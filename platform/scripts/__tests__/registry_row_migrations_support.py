"""Derive ka_gochara_v5's registry depends_on from main's OWN migrations (ruling SR-W3-REGISTRY-ROW), so a later registry migration fails a
test instead of the production dispatch/teardown.

The chain, each step read from the migration's SQL text (never typed in here):
  1304  UPDATE ... depends_on = ARRAY['ga_positions','ga_dashas']              -> the small-test pair
  1392  K8 registry truth: the `ka_gochara_v5` element of the corrections JSON -> {ga_positions, ga_dashas, bg_transit_rules}
  1403  SR-K8-EDGE-1403: v_edge {"asset_id":"ka_gochara_v5","from":..,"to":..} -> from must equal 1392's array; "to" is the final array
Any OTHER migration numbered above 1304 whose executable (non-comment) SQL names ka_gochara_v5 and depends_on is an unknown writer of the
column: `unknown_depends_on_writers` lists it, and the tests fail until this chain is extended."""
from __future__ import annotations

import json
import re
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"
ASSET = "ka_gochara_v5"
CHAIN = ("1304_ka_gochara_v5_registry_row_small_test.sql", "1392_k8_registry_truth.sql", "1403_ka_gochara_v5_depends_on_l0_dignity.sql")


def _code(sql: str) -> str:
    return "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))


def depends_on_1304(sql: str) -> list[str]:
    update = sql[sql.index("UPDATE asset_registry"):sql.index(f"WHERE asset_id = '{ASSET}'")]
    arr = re.search(r"depends_on = ARRAY\[([^\]]*)\]::text\[\]", update).group(1)
    return [x.strip().strip("'") for x in arr.split(",")]


def depends_on_1392(sql: str) -> list[str]:
    body = re.search(r"corrections constant jsonb := \$k8_rows\$(.*?)\$k8_rows\$", sql, re.S).group(1)
    rows = [r for r in json.loads(body) if r["asset_id"] == ASSET]
    assert len(rows) == 1, f"1392 must carry exactly one {ASSET} correction, found {len(rows)}"
    return list(rows[0]["depends_on"])


def edge_1403(sql: str) -> dict:
    edge = json.loads(re.search(r"\$k8_edge\$\s*(\{.*?\})\s*\$k8_edge\$", sql, re.S).group(1))
    assert edge["asset_id"] == ASSET
    return edge


def derive_depends_on(migrations: Path = MIGRATIONS) -> list[str]:
    """The array main's migrations leave in asset_registry.depends_on for ka_gochara_v5, in the stored order."""
    m1304, m1392, m1403 = ((migrations / name).read_text(encoding="utf-8") for name in CHAIN)
    after_1304, after_1392 = depends_on_1304(m1304), depends_on_1392(m1392)
    edge = edge_1403(m1403)
    assert edge["from"] == after_1392, f"1403 expects 1392's array {edge['from']}, but 1392 leaves {after_1392}"
    return list(edge["to"])


def unknown_depends_on_writers(migrations: Path = MIGRATIONS) -> list[str]:
    """Migrations numbered above 1304, outside the chain, whose non-comment SQL names the asset and depends_on."""
    found = []
    for path in sorted(migrations.glob("*.sql")):
        number = re.match(r"(\d+)_", path.name)
        if not number or int(number.group(1)) <= 1304 or path.name in CHAIN:
            continue
        code = _code(path.read_text(encoding="utf-8"))
        if ASSET in code and "depends_on" in code:
            found.append(path.name)
    return found
