"""A5.3 — migration 1240: static contract + the FROZEN digest vector (R8-4; Stream B's constraints 1, 4, 9, 11).

Static (no database): no BEGIN/COMMIT (migrate.ts owns the transaction), exactly ONE new trigger on the seal table,
no SECURITY DEFINER, no column-level grants, the BUILDER is granted nothing, no function an applied migration defines
is replaced, and the gate's required-field list is the verifier's governed-field list.

Frozen vector: the IEEE-bits / NULL-distinct window-content preimage is a LITERAL string with a literal sha256, so a
serializer drift (key order, float encoding, null handling) fails CI; and the database's own digest equals the same
preimage built independently in Python from the stored values.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import window_verifier as wv

MIGRATIONS = Path(__file__).resolve().parents[4] / "migrations"
SQL = (MIGRATIONS / "1240_gochara_window_verification_gate.sql").read_text()
UTC = timezone.utc

FROZEN_PREIMAGE = (
    '[{"evidence_against":{"null":true},"evidence_for":{"f4":"3f800000"},"interval":["2025-01-10T00:00:00.000000Z",'
    '"2025-02-20T00:00:00.000000Z"],"members":["00000000-0000-8000-8000-00000000000a","00000000-0000-8000-8000-'
    '00000000000b"],"null_states":[],"objective":{"s":"evidence_for_per_root_sum"},"objective_value":{"f4":"3dcccccd"},'
    '"peak":{"t":"2025-01-10T00:00:00.000000Z"},"qualification":{"q":{"affected_channels":[],"members":2,'
    '"qualified_members":2,"unqualified_reason":null,"unresolved":{}}},"score":{"f4":"3f000000"},"severity":'
    '{"null":true},"valence":"favourable"},{"evidence_against":{"null":true},"evidence_for":{"null":true},"interval":'
    '["2025-03-01T00:00:00.000000Z","2025-03-09T12:30:15.250000Z"],"members":["00000000-0000-8000-8000-'
    '00000000000c"],"null_states":["unqualified"],"objective":{"s":"max_min_agent_activity"},"objective_value":'
    '{"null":true},"peak":{"null":true},"qualification":{"q":{"affected_channels":[],"members":1,"qualified_members":1,'
    '"unqualified_reason":"dynamic_objective_solver_guarantee_not_available","unresolved":'
    '{"dynamic_objective_solver_guarantee_not_available":1}}},"score":{"null":true},"severity":{"null":true},'
    '"valence":"unqualified"}]')
FROZEN_SHA256 = "890d9028f1819d830ad6191edc28bd994ce1f1be55ba8e518ab9260dc30c6ad9"


def _f4(x):
    return {"null": True} if x is None else {"f4": struct.pack(">f", x).hex()}


def _ts(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def window_content_preimage(windows) -> str:
    """The preimage `ka_gochara_eval_window_content_digest` hashes, built from stored VALUES — independent of SQL."""
    out = []
    for w in sorted(windows, key=lambda w: w["interval"][0]):
        out.append({
            "interval": [_ts(w["interval"][0]), _ts(w["interval"][1])],
            "peak": {"null": True} if w["peak"] is None else {"t": _ts(w["peak"])},
            "score": _f4(w["score"]), "evidence_for": _f4(w["evidence_for"]),
            "evidence_against": _f4(w["evidence_against"]), "severity": _f4(w["severity"]),
            "objective_value": _f4(w["objective_value"]), "valence": w["valence"],
            "objective": {"null": True} if w["objective"] is None else {"s": w["objective"]},
            "qualification": {"null": True} if w["qualification"] is None else {"q": w["qualification"]},
            "null_states": w["null_states"], "members": sorted(w["members"])})
    return json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


FROZEN_WINDOWS = [
    {"interval": (datetime(2025, 1, 10, tzinfo=UTC), datetime(2025, 2, 20, tzinfo=UTC)),
     "peak": datetime(2025, 1, 10, tzinfo=UTC), "score": 0.5, "evidence_for": 1.0, "evidence_against": None,
     "severity": None, "objective_value": 0.1, "valence": "favourable", "objective": "evidence_for_per_root_sum",
     "qualification": {"unqualified_reason": None, "unresolved": {}, "affected_channels": [], "members": 2,
                       "qualified_members": 2},
     "null_states": [], "members": ["00000000-0000-8000-8000-00000000000b", "00000000-0000-8000-8000-00000000000a"]},
    {"interval": (datetime(2025, 3, 1, tzinfo=UTC), datetime(2025, 3, 9, 12, 30, 15, 250000, tzinfo=UTC)),
     "peak": None, "score": None, "evidence_for": None, "evidence_against": None, "severity": None,
     "objective_value": None, "valence": "unqualified", "objective": "max_min_agent_activity",
     "qualification": {"unqualified_reason": "dynamic_objective_solver_guarantee_not_available",
                       "unresolved": {"dynamic_objective_solver_guarantee_not_available": 1},
                       "affected_channels": [], "members": 1, "qualified_members": 1},
     "null_states": ["unqualified"], "members": ["00000000-0000-8000-8000-00000000000c"]}]


def test_the_frozen_window_preimage_and_hash_are_literal_and_reproduced():
    literal = window_content_preimage(FROZEN_WINDOWS)
    assert literal == FROZEN_PREIMAGE
    assert hashlib.sha256(literal.encode("utf-8")).hexdigest() == FROZEN_SHA256
    # NULL is distinct from JSON null / from zero, and a REAL is its IEEE bit pattern, not a decimal rendering
    assert _f4(None) != _f4(0.0) and _f4(0.1) == {"f4": "3dcccccd"} and _f4(1.0) == {"f4": "3f800000"}
    assert window_content_preimage([{**FROZEN_WINDOWS[0], "qualification": None}]) != window_content_preimage(
        [{**FROZEN_WINDOWS[0], "qualification": {}}])


# ── static contract ────────────────────────────────────────────────────────────────────────────────────────

def _statements(text):
    body = re.sub(r"--[^\n]*", "", text)
    return body


def test_1240_has_no_transaction_control_and_no_security_definer():
    body = _statements(SQL)
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", body, re.M | re.I)
    assert "SECURITY DEFINER" not in body.upper()


def test_1240_adds_exactly_one_before_trigger_and_one_deferred_receipt_constraint_trigger_to_the_seal_table():
    body = _statements(SQL)
    triggers = re.findall(r"CREATE TRIGGER\s+(\w+)\s+BEFORE INSERT ON public\.ka_gochara_generation_seal", body)
    assert triggers == ["ka_gochara_generation_seal_zz_window_verified"]
    assert triggers[0] > "ka_gochara_generation_seal_z_search_complete"        # name order = firing order
    # R11-3 (steward M…145007): the approval receipt is ENFORCED — ONE additive DEFERRED constraint trigger on the first-seal INSERT
    # (AFTER INSERT: it never fires for a replay's ON CONFLICT DO NOTHING nor for a generation sealed before 1240)
    cons = re.findall(r"CREATE CONSTRAINT TRIGGER\s+(\w+)\s+AFTER INSERT ON public\.ka_gochara_generation_seal\s+"
                      r"DEFERRABLE INITIALLY DEFERRED\s+FOR EACH ROW EXECUTE FUNCTION public\.(\w+)\(\)", body)
    assert cons == [("ka_gochara_generation_seal_zz_receipt_required", "ka_gochara_seal_requires_approval_receipt")]
    assert "approval_receipt_missing" in body and "SECURITY DEFINER" not in body.upper()


def test_1240_never_replaces_a_function_an_applied_migration_defines():
    mine = set(re.findall(r"CREATE OR REPLACE FUNCTION\s+public\.(\w+)", _statements(SQL)))
    assert mine, "no functions found"
    for fname in sorted(MIGRATIONS.glob("115[3-7]_*.sql")) + [MIGRATIONS / "1206_gochara_search_inventory_completeness.sql"]:
        theirs = set(re.findall(r"FUNCTION\s+(?:IF NOT EXISTS\s+)?public\.(\w+)", fname.read_text()))
        assert not (mine & theirs), (fname.name, mine & theirs)


def test_1240_grants_are_table_level_explicit_and_the_builder_gets_exactly_one_helper_execute():
    body = _statements(SQL)
    grants = re.findall(r"^\s*(GRANT\s+.*?;)", body, re.S | re.I | re.M)       # statements, not words inside a NOTICE
    assert grants
    builder = [g for g in grants if "data_plane_builder" in g]
    # R9-4: the builder holds NOTHING on the verification table and exactly ONE function — the window CHECK helper
    assert len(builder) == 1, builder
    assert re.fullmatch(r"GRANT\s+EXECUTE\s+ON\s+FUNCTION\s+public\.ka_gochara_window_qualification_ok\(jsonb\)"
                        r"\s+TO\s+data_plane_builder;", " ".join(builder[0].split()), re.I), builder[0]
    for g in grants:
        assert not re.search(r"GRANT\s+\w+\s*\(", g), f"column-level grant: {g[:60]}"
        assert not re.search(r"\bTO\s+PUBLIC\b", g, re.I), g[:80]
        assert re.search(r"\bTO\s+(gochara_verifier|gochara_sealer|data_plane_builder)\b", g), g[:80]
        if "data_plane_builder" not in g:
            assert re.search(r"\bTO\s+(gochara_verifier|gochara_sealer)\b", g), g[:80]
    # every grant block is guarded by role existence (the production roles are not provisioned yet)
    assert body.count("IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder')") == 1
    assert body.count("IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier')") == 1
    assert body.count("IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer')") == 1
    assert "REVOKE" not in body.upper() and "GRANT ALL" not in body.upper()
    # the helper the grant names is the one the window CHECK calls
    assert "CHECK (public.ka_gochara_window_qualification_ok(qualification) IS TRUE)" in body


def test_1240_does_not_touch_applied_objects_beyond_the_three_window_columns():
    body = _statements(SQL)
    alters = re.findall(r"ALTER TABLE\s+(public\.\w+)", body)
    assert set(alters) == {"public.ka_gochara_eval_window"}
    cols = set(re.findall(r"ADD COLUMN\s+(\w+)", body))
    assert cols == {"objective", "objective_value", "qualification"}
    assert not re.search(r"DROP\s+(TABLE|COLUMN|CONSTRAINT)", body, re.I)
    assert not re.search(r"\b(UPDATE|DELETE FROM|INSERT INTO)\s+public\.", body)         # no data change


def test_the_gates_required_field_list_is_the_verifiers_governed_field_list():
    m = re.search(r"SELECT ARRAY\[(.*?)\]::text\[\] AS f", SQL, re.S)
    sql_fields = set(re.findall(r"'(\w+)'", m.group(1)))
    assert sql_fields == set(wv.GOVERNED_FIELDS)


def test_the_header_states_the_roles_blocker_plainly():
    assert "NO verification row can be written there and the candidate gate stays CLOSED" in SQL
    assert "gochara_verifier" in SQL and "gochara_sealer" in SQL
    assert "builder gets NOTHING" in SQL.replace("The builder gets NOTHING on the new table", "builder gets NOTHING")


# ── the database digest equals the independently built preimage ───────────────────────────────────────────

from .test_a53_window_verification_gate import _boot_p3, _consistent_sky, _windows, world  # noqa: E402,F401
from .test_a53_inventory import CHART_ID  # noqa: E402


def test_the_database_content_digest_equals_the_independently_built_preimage(world):
    w = world
    _boot_p3(w)
    _windows(w, ("P3",))
    conn = w.conn
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute(
            "UPDATE public.ka_gochara_eval_window SET peak_instant = lower(interval), score = 0.5, evidence_for = 1.0,"
            " evidence_against = NULL, severity = NULL, objective_value = 0.1, outcome_valence_for_native = 'favourable',"
            " qualification = '{\"policy\": \"window_qualification/1\", \"unqualified_reason\": null, \"unresolved\": {}, \"affected_channels\": [],"
            " \"members\": 1, \"qualified_members\": 1}'::jsonb, null_states_used = '{}' WHERE path_id = 'P3'")
    row = conn.execute(
        "SELECT lower(interval), upper(interval), peak_instant, score, evidence_for, evidence_against, severity,"
        " objective_value, outcome_valence_for_native, objective, qualification, null_states_used, window_id"
        " FROM public.ka_gochara_eval_window WHERE path_id = 'P3'").fetchone()
    members = [r[0] for r in conn.execute(
        "SELECT record_id::text FROM public.ka_gochara_eval_window_record WHERE window_id = %s", (row[12],)).fetchall()]
    pre = window_content_preimage([{
        "interval": (row[0], row[1]), "peak": row[2], "score": row[3], "evidence_for": row[4],
        "evidence_against": row[5], "severity": row[6], "objective_value": row[7], "valence": row[8],
        "objective": row[9], "qualification": row[10], "null_states": list(row[11]), "members": members}])
    sql_digest = conn.execute("SELECT public.ka_gochara_eval_window_content_digest(%s::uuid, %s, %s, %s, %s)",
                              (CHART_ID, "5.0", "marriage", "P3", "1.0.0")).fetchone()[0]
    assert sql_digest == hashlib.sha256(pre.encode("utf-8")).hexdigest()
    # the SQL canonical JSON of a REAL token is the frozen IEEE hex, NULL distinct
    toks = conn.execute("SELECT public.ka_gochara_f4_token(0.1::real)::text, public.ka_gochara_f4_token(NULL)::text,"
                        " public.ka_gochara_f4_token(1.0::real)::text").fetchone()
    assert json.loads(toks[0]) == {"f4": "3dcccccd"} and json.loads(toks[1]) == {"null": True} \
        and json.loads(toks[2]) == {"f4": "3f800000"}
