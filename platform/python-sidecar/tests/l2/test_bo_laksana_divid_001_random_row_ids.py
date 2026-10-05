"""S-L2 TI-b1 (N-143 / DIVID-001): bo_laksana must not embed a random L1 row id.

Production shape (chart 482012f1, measured read-only): the L1 vargottama facts carry
`constituent_fact_id` = chart_divisionals.id (uuid4, regenerated per ga_vargas rebuild)
in fact_value_jsonb. bo_laksana copied it into configuration_jsonb and the summary
text, so signal_id (a hash of the config) churned on every L1 rebuild. Stripping it
alone makes 352 of the 1,340 signals identical (the graha lived only in fact_subject),
which the P-3 count check would turn into a hard build failure -- hence fact_subject.
"""
from __future__ import annotations

import itertools
import json
import re
import uuid

import pytest

from pipeline.orchestrator.writers import bo_laksana as bo

_NOW = "2026-10-05T00:00:00+00:00"
_UUID_ANY = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
_AYANAMSHAS = ("lahiri_chitrapaksha", "raman", "krishnamurti", "true_chitra",
               "surya_siddhanta_classical")
_GRAHAS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
_VARGAS = tuple(f"D{n}" for n in range(2, 32))


def _vargottama_fact(aya, varga, graha, vargottama, rowid):
    return {
        "fact_id": uuid.uuid4().hex[:16],
        "fact_category": "vargottama_per_varga",
        "fact_key": "is_vargottama",
        "fact_subject": f"{varga}_{graha}",
        "fact_value_text": "vargottama" if vargottama else "not_vargottama",
        "fact_value_num": 1.0 if vargottama else 0.0,
        "ayanamsha_id": aya,
        "source_calculation": "chart_divisionals.varga_vargottama_flag/pyjhora/1.0.0",
        "fact_value_jsonb": {"varga": varga, "varga_sign": "Pisces", "ayanamsha_id": aya,
                             "uncatalogued": False, "constituent_fact_id": rowid},
    }


def _amplification_fact(aya, graha, rowid):
    return {
        "fact_id": uuid.uuid4().hex[:16],
        "fact_category": "graha_vargottama_amplification_factor",
        "fact_key": "amplification_factor",
        "fact_subject": graha,
        "fact_value_text": "non-vargottama",
        "fact_value_num": 1.0,
        "ayanamsha_id": aya,
        "source_calculation": "chart_divisionals.varga_vargottama_flag/pyjhora/1.0.0",
        "fact_value_jsonb": {"source_table": "chart_divisionals",
                             "source_category": "varga_vargottama_flag",
                             "constituent_fact_id": rowid},
    }


def _population():
    """Production-shaped: identical values across grahas/vargas, only the random row
    id and fact_subject differ (the real data has 979 distinct configs of 1,305 once
    the id is gone, because value+varga_sign repeat)."""
    facts = []
    for aya in _AYANAMSHAS:
        for varga, graha in itertools.product(_VARGAS[:29], _GRAHAS):
            facts.append(_vargottama_fact(aya, varga, graha, False, str(uuid.uuid4())))
        for graha in _GRAHAS[:7]:
            facts.append(_amplification_fact(aya, graha, str(uuid.uuid4())))
    return facts


def _build(fact, valid=None):
    return bo._build_signal_row(fact, "chart-1", "b1", {}, {}, {}, _NOW,
                                valid_fact_ids=valid or {fact["fact_id"]})


def _db_conflict_key(row):
    # chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb (jsonb
    # equality is key-order independent -> canonical dump)
    return (row["chart_id"], row["ayanamsha_id"], row["signal_type_id"], row["build_id"],
            json.dumps(json.loads(row["configuration_jsonb"]), sort_keys=True))


def _simulate_insert(rows):
    """ON CONFLICT (...) DO NOTHING: count of rows actually written."""
    return len({_db_conflict_key(r) for r in rows})


def test_no_random_row_id_in_config_or_summary():
    for fact in _population()[:400]:
        row = _build(fact)
        assert not _UUID_ANY.search(row["configuration_jsonb"]), row["configuration_jsonb"]
        assert not _UUID_ANY.search(row["signal_summary_text"]), row["signal_summary_text"]
        assert "constituent_fact_id" not in json.loads(row["configuration_jsonb"])


def test_signal_identity_inputs_are_independent_of_random_row_id():
    f1 = _vargottama_fact("raman", "D9", "MAR", True, str(uuid.uuid4()))
    f2 = dict(f1, fact_value_jsonb=dict(f1["fact_value_jsonb"],
                                        constituent_fact_id=str(uuid.uuid4())))
    r1, r2 = _build(f1), _build(f2)
    assert r1["configuration_jsonb"] == r2["configuration_jsonb"]
    assert r1["signal_summary_text"] == r2["signal_summary_text"]


def test_natural_key_fact_subject_carried_in_config():
    row = _build(_vargottama_fact("raman", "D108", "JUP", False, str(uuid.uuid4())))
    assert json.loads(row["configuration_jsonb"])["fact_subject"] == "D108_JUP"
    assert "fact_subject=D108_JUP" in row["signal_summary_text"]
    row = _build(_amplification_fact("raman", "MER", str(uuid.uuid4())))
    assert json.loads(row["configuration_jsonb"])["fact_subject"] == "MER"


def test_missing_fact_subject_refuses_rather_than_emitting_collidable_row():
    f = _amplification_fact("raman", "MER", str(uuid.uuid4()))
    f["fact_subject"] = None
    with pytest.raises(ValueError, match="no fact_subject"):
        _build(f)


def test_population_is_unique_on_the_db_conflict_key_after_strip():
    """The 1,340-style proof: every row survives ON CONFLICT DO NOTHING."""
    rows = [_build(f) for f in _population()]
    assert len(rows) > 1300
    assert _simulate_insert(rows) == len(rows)
    # signal_id inputs (without build_id) are equally unique
    assert len({(r["ayanamsha_id"], r["signal_type_id"], r["varga_id"],
                 json.dumps(json.loads(r["configuration_jsonb"]), sort_keys=True))
                for r in rows}) == len(rows)


def test_strip_alone_would_have_collided_p3_failing_first():
    """Guards the reason fact_subject is in the config: strip WITHOUT it and the
    production-shaped population collapses (the pre-fix-naive change)."""
    rows = [_build(f) for f in _population()]
    naive = set()
    for r in rows:
        cfg = json.loads(r["configuration_jsonb"])
        cfg.pop("fact_subject", None)
        naive.add((r["ayanamsha_id"], r["signal_type_id"], json.dumps(cfg, sort_keys=True)))
    assert len(naive) < len(rows)


def test_count_check_raises_on_duplicate_key_scenario():
    """P-3: two rows colliding on the ON CONFLICT key -> DO NOTHING drops one -> the
    substep must refuse the partial root generation, not pass silently."""
    f = _vargottama_fact("raman", "D9", "MAR", True, str(uuid.uuid4()))
    r1 = _build(f)
    r2 = dict(r1)  # identical identity key
    inserted = _simulate_insert([r1, r2])
    assert inserted == 1
    with pytest.raises(RuntimeError, match="refusing a partial root generation"):
        bo._assert_full_root_generation("raman", inserted, 2)
    bo._assert_full_root_generation("raman", 2, 2)  # no raise when complete


def test_strip_keeps_fact_ids_and_deterministic_uuid5_and_nested_ids():
    fid = str(uuid.uuid4())      # a uuid-shaped chart_facts.fact_id must survive
    u5 = str(uuid.uuid5(uuid.NAMESPACE_DNS, "rule"))
    cfg = {"fact_id_ref": fid, "rule_id": u5, "n": 1,
           "nested": {"x": str(uuid.uuid4()), "keep": "a"}, "lst": [str(uuid.uuid4()), "b"]}
    out = bo._strip_random_row_ids(cfg, {fid})
    assert out == {"fact_id_ref": fid, "rule_id": u5, "n": 1,
                   "nested": {"keep": "a"}, "lst": ["b"]}


def test_other_signal_types_unchanged_by_strip():
    fact = {"fact_id": "f1", "fact_category": "panchadha_maitri", "fact_key": "compound_relation",
            "fact_subject": "MAR_SAT", "fact_value_text": "shatru", "fact_value_num": None,
            "ayanamsha_id": "raman", "source_calculation": "x",
            "fact_value_jsonb": {"source": "Mars", "target": "Saturn",
                                 "compound_rule_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "r"))}}
    cfg = json.loads(_build(fact)["configuration_jsonb"])
    assert "compound_rule_id" in cfg and cfg["fact_subject"] == "MAR_SAT"  # natural key now carried for every fact (LAKSANA-COLLISION)


# ── Determinism through the REAL identity function (disposable PostgreSQL) ──────
from pathlib import Path  # noqa: E402

from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, pg, psql  # noqa: E402,F401

_MIG_661 = Path(__file__).resolve().parents[3] / "migrations" / "661_l2_bodha_signal_identity.sql"


def _identity_function_sql() -> str:
    text = _MIG_661.read_text()
    start = text.index("CREATE OR REPLACE FUNCTION bodha_signal_identity_namespace()")
    end = text.index("COMMENT ON FUNCTION bodha_signal_identity(")
    return text[start:end]


def _build_population_with_new_random_ids():
    """Same logical L1 facts, a FRESH set of random row ids (= a ga_vargas rebuild)."""
    return [_build(f) for f in _population_same_facts()]


_FIXED_FACTS = None


def _population_same_facts():
    """Deterministic logical content; only the embedded random ids are re-minted per call."""
    global _FIXED_FACTS
    if _FIXED_FACTS is None:
        _FIXED_FACTS = _population()
    out = []
    for f in _FIXED_FACTS:
        jb = dict(f["fact_value_jsonb"], constituent_fact_id=str(uuid.uuid4()))
        out.append(dict(f, fact_value_jsonb=jb))
    return out


def test_signal_id_set_identical_across_two_runs_real_identity_function(pg):  # noqa: F811
    if not HAVE_PG:
        pytest.skip(PG_SKIP_REASON)
    import psycopg
    from psycopg.rows import dict_row

    db = new_db(pg)
    r = psql(pg, db, 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    if r.returncode != 0:
        pytest.skip("uuid-ossp extension is not available in this PostgreSQL install")
    assert psql(pg, db, _identity_function_sql()).returncode == 0

    chart = str(uuid.uuid4())
    runs = []
    for _ in range(2):  # two local runs of the row builder, same inputs, fresh random ids
        rows = [bo._build_signal_row(f, chart, "b1", {}, {}, {}, _NOW,
                                     valid_fact_ids={f["fact_id"]})
                for f in _population_same_facts()]
        with psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db,
                             row_factory=dict_row) as conn:
            collapsed = bo.assign_deterministic_signal_ids(conn, rows)
        assert collapsed == 0, f"{collapsed} rows collapsed onto an existing identity"
        runs.append([r["signal_id"] for r in rows])

    assert len(runs[0]) > 1300
    assert len(set(runs[0])) == len(runs[0])          # all distinct
    assert runs[0] == runs[1]                          # identical, in order
    assert set(runs[0]) == set(runs[1])
