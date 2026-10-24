#!/usr/bin/env python3
"""Load the 2026-10-03 live snapshot of the bg_transit_* tables + the two asset_registry
rows into a DISPOSABLE local PostgreSQL (unix socket), reproducing production column
types and constraints.  Usage: pg_replica_load.py <socket_dir> <port> <dbname>
Used only by run_pg_test_draft_transit_curation.py.  Never connects to production."""
import json, subprocess, sys, pathlib
SNAP = pathlib.Path(__file__).resolve().parent.parent / "snapshots"
PSQL = "/opt/homebrew/bin/psql"

DDL = """
DROP TABLE IF EXISTS bg_transit_moorti, bg_transit_rules, bg_transit_engine, asset_registry CASCADE;
CREATE TABLE asset_registry (
  asset_id text PRIMARY KEY, layer text, sort_order integer, english_description text,
  volume_explanation text, target_floor bigint, target_table text, count_sql text,
  catalog_status text, integrity_check_sql text, has_writer boolean, asset_kind text);
CREATE TABLE bg_transit_engine (
  id serial PRIMARY KEY, graha text NOT NULL UNIQUE,
  avg_daily_motion_deg double precision NOT NULL, zodiac_period_days double precision NOT NULL,
  sign_residence_days double precision NOT NULL, classical_citation text NOT NULL);
CREATE TABLE bg_transit_rules (
  id serial PRIMARY KEY, rule_type text NOT NULL CHECK (rule_type = ANY (ARRAY['favourable','unfavourable','vedha','double_transit'])),
  graha text NOT NULL, primary_house integer NOT NULL CHECK (primary_house BETWEEN 1 AND 12),
  vedha_house integer CHECK (vedha_house BETWEEN 1 AND 12), phala text NOT NULL,
  classical_citation text NOT NULL, rule_notes text,
  CONSTRAINT bg_transit_rules_graha_type_house_unique UNIQUE (graha, rule_type, primary_house));
CREATE TABLE bg_transit_moorti (
  nakshatra_offset integer PRIMARY KEY CHECK (nakshatra_offset BETWEEN 1 AND 27),
  moorti_name text NOT NULL CHECK (moorti_name = ANY (ARRAY['swarna','rajata','tamra','loha'])),
  quality_tier integer NOT NULL CHECK (quality_tier BETWEEN 1 AND 4), phala_brief text NOT NULL,
  classical_citation text NOT NULL, rule_notes text);
"""

def q(v):
    if v is None: return "NULL"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(v)
    return "'" + str(v).replace("'", "''") + "'"

def inserts(table, rows, cols):
    out = []
    for r in rows:
        out.append(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(q(r[c]) for c in cols)});")
    return "\n".join(out)

def main(sock, port, db):
    load = lambda n: json.load(open(SNAP / f"live_{n}.json"))
    sql = DDL
    sql += inserts("bg_transit_engine", load("engine"), ["id","graha","avg_daily_motion_deg","zodiac_period_days","sign_residence_days","classical_citation"])
    sql += "\n" + inserts("bg_transit_rules", load("rules"), ["id","rule_type","graha","primary_house","vedha_house","phala","classical_citation","rule_notes"])
    sql += "\n" + inserts("bg_transit_moorti", load("moorti"), ["nakshatra_offset","moorti_name","quality_tier","phala_brief","classical_citation","rule_notes"])
    sql += "\n" + inserts("asset_registry", load("registry"), ["asset_id","layer","sort_order","english_description","volume_explanation","target_floor","target_table","count_sql","catalog_status","integrity_check_sql","has_writer","asset_kind"])
    sql += "\nSELECT setval(pg_get_serial_sequence('bg_transit_rules','id'), (SELECT max(id) FROM bg_transit_rules));\n"
    p = subprocess.run([PSQL, "-X", "-q", "-h", sock, "-p", str(port), "-U", "cur", "-d", db, "-v", "ON_ERROR_STOP=1", "-f", "-"], input=sql, text=True, capture_output=True)
    if p.returncode: sys.exit(p.stderr)

if __name__ == "__main__":
    main(*sys.argv[1:4])
