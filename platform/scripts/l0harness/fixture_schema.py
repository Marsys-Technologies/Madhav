"""Generate fixture DDL from production-probe-derived column/constraint metadata.

Source data (all read-only production probes, 2026-09-26):
  - columns.json                     information_schema.columns, 15 tables
  - bodha_msr_signals_columns.json   information_schema.columns, bodha_msr_signals
  - columns_l0w7_tables.json         information_schema.columns, 11 more tables
                                     (charts, fact_category_ownership + the 9 empty
                                     L1 tables 1035's static triggers require)
  - constraints.json                 pg_constraint (pg_get_constraintdef), 16 tables
  - constraints_l0w7_tables.json     pg_constraint (pg_get_constraintdef), 11 tables

Emit CREATE EXTENSION / CREATE SEQUENCE / CREATE TABLE / ALTER TABLE ADD CONSTRAINT
DDL preserving nullability, defaults, CHECKs (incl. NOT VALID), UNIQUEs, PKs and FKs.
FK edges to tables outside the fixture set are skipped (see SKIPPED_FKS; each is
recorded in REHEARSAL_NOTES.md).
Local-rehearsal only; CI restores production --schema-only pg_dump instead.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE / "production_schema"

UDT_MAP = {
    "text": "text",
    "uuid": "uuid",
    "jsonb": "jsonb",
    "bool": "boolean",
    "int2": "smallint",
    "int4": "integer",
    "int8": "bigint",
    "float4": "real",
    "float8": "double precision",
    "date": "date",
    "time": "time without time zone",
    "timetz": "time with time zone",
    "interval": "interval",
    "timestamptz": "timestamp with time zone",
    "timestamp": "timestamp without time zone",
    "_text": "text[]",
    "_uuid": "uuid[]",
    "_int8": "bigint[]",
}

# information_schema.columns does not carry the vector dimension; probed via
# pg_attribute/format_type on 2026-09-26.
TYPE_OVERRIDES = {
    ("classical_text_chunks", "embedding"): "vector(768)",
}

# Sequences are derived from nextval() defaults in the probed columns at emit
# time; this list is only a fallback for probes that predate that derivation.
SEQUENCES = [
    "chart_vichara_id_seq",
    "ga_yoga_firings_id_seq",
    "yoga_families_id_seq",
]

NEXTVAL_RE = re.compile(r"nextval\('([a-z0-9_]+)'::regclass\)")

# FK constraints whose parent table is outside the 27-table fixture set.
# Probed 2026-09-26; omission disclosed in REHEARSAL_NOTES.md.
SKIPPED_FKS = {
    "charts_client_id_fkey",  # charts.client_id -> profiles(id); profiles not in fixture
}

# CREATE TABLE order: parents before FK children (FKs are added by ALTER afterwards,
# so order here is not load-bearing, but keep it readable).
TABLE_ORDER = [
    "classical_texts",
    "classical_text_chunks",
    "yoga_families",
    "yoga_family_members",
    "asset_registry",
    "brahma_yoga_catalog",
    "brahma_dosha_catalog",
    "brahma_class_priors",
    "brahma_ontology",
    "brahma_remedy_corpus",
    "brahma_dasha_systems",
    "charts",
    "fact_category_ownership",
    "chart_facts",
    "chart_vichara",
    "chart_dashas",
    "chart_divisionals",
    "ga_condition_composite",
    "ga_transit_anchors",
    "l1_tajik_varsha_year_lords",
    "ga_medical",
    "ga_vastu_planet_direction_map",
    "ga_prashna_lagna",
    "ga_prashna_judgment",
    "ga_yoga_firings",
    "sutravali_rules",
    "bodha_msr_signals",
]


def load_columns() -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    for r in json.loads((SCHEMA_DIR / "columns.json").read_text()):
        tables.setdefault(r["table_name"], []).append(r)
    for r in json.loads((SCHEMA_DIR / "bodha_msr_signals_columns.json").read_text()):
        r["table_name"] = "bodha_msr_signals"
        tables.setdefault("bodha_msr_signals", []).append(r)
    for r in json.loads((SCHEMA_DIR / "columns_l0w7_tables.json").read_text()):
        tables.setdefault(r["table_name"], []).append(r)
    for cols in tables.values():
        cols.sort(key=lambda r: r["ordinal_position"])
    return tables


def column_type(table: str, col: dict) -> str:
    override = TYPE_OVERRIDES.get((table, col["column_name"]))
    if override:
        return override
    udt = col["udt_name"]
    if udt == "numeric":
        if col["numeric_precision"] is not None and col["numeric_scale"] is not None:
            return f"numeric({col['numeric_precision']},{col['numeric_scale']})"
        return "numeric"
    if udt == "varchar":
        if col["character_maximum_length"] is not None:
            return f"varchar({col['character_maximum_length']})"
        return "varchar"
    if udt not in UDT_MAP:
        raise ValueError(f"unmapped udt_name {udt!r} on {table}.{col['column_name']}")
    return UDT_MAP[udt]


def load_constraints() -> list[dict]:
    constraints = json.loads((SCHEMA_DIR / "constraints.json").read_text())
    constraints += json.loads((SCHEMA_DIR / "constraints_l0w7_tables.json").read_text())
    return [c for c in constraints if c["conname"] not in SKIPPED_FKS]


def emit() -> str:
    tables = load_columns()
    constraints = load_constraints()

    missing = [t for t in TABLE_ORDER if t not in tables]
    if missing:
        raise ValueError(f"column metadata missing for tables: {missing}")

    out: list[str] = []
    out.append("-- Fixture DDL generated from production-probe metadata (2026-09-26).")
    out.append("-- Local rehearsal only; CI restores production --schema-only pg_dump.")
    out.append("CREATE EXTENSION IF NOT EXISTS vector;")
    out.append("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    out.append('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    out.append("")
    sequences = set(SEQUENCES)
    for cols in tables.values():
        for col in cols:
            if col["column_default"]:
                sequences.update(NEXTVAL_RE.findall(col["column_default"]))
    for seq in sorted(sequences):
        out.append(f"CREATE SEQUENCE IF NOT EXISTS {seq};")
    out.append("")

    for table in TABLE_ORDER:
        lines = []
        for col in tables[table]:
            line = f"  {col['column_name']} {column_type(table, col)}"
            if col["column_default"] is not None:
                line += f" DEFAULT {col['column_default']}"
            if col["is_nullable"] == "NO":
                line += " NOT NULL"
            lines.append(line)
        out.append(f"CREATE TABLE {table} (")
        out.append(",\n".join(lines))
        out.append(");")
        out.append("")

    # Non-FK constraints first (p, u, c), then FKs.
    def add(c: dict) -> None:
        out.append(
            f"ALTER TABLE {c['table_name']} ADD CONSTRAINT {c['conname']} {c['def']};"
        )

    for c in constraints:
        if c["contype"] != "f":
            add(c)
    out.append("")
    for c in constraints:
        if c["contype"] == "f":
            add(c)
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    sql = emit()
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(sql)
        print(f"wrote {sys.argv[1]} ({len(sql)} chars)", file=sys.stderr)
    else:
        sys.stdout.write(sql)
