"""ga_vichara writer — row identity, whole-row dedupe, sorted provenance, honest count,
and pinned AS-OF (TI-l1-vichara-writer-001).

Real-writer tests (`build_ga_vichara_substep` against a fake in-memory conn) on a
SYNTHETIC dataset reproducing the canonical duplicate/identity structure:

  30 vargas x (12 lord_placed + 24 lord_aspects bhava_significance_link facts
  + 19 aspect_parashari_per_varga facts) = 1,650 valence_pass rows per ayanamsha.
  Mars/Mercury/Jupiter/Venus/Saturn each lord TWO signs, so each emits two
  byte-identical lord_placed rows per varga: 5 x 30 = 150 exact duplicates.
  Expected after whole-row dedupe: valence_pass 1,650 -> 1,500.

chart_vichara has NO natural key (migration 747). The identity used here is
"grain plus L1 source-fact provenance set, NOT a natural key".

Mutation notes (each turns >=1 test red; results recorded in the PR body):
  * remove `sorted(...)` in the valence builders      -> test_cf_sorted*, test_hashseed_*
  * remove `dedupe_rows(...)` in the substep          -> test_valence_dedupe_1650_to_1500
  * remove `assert_no_identity_collision(...)`        -> test_collision_*_real_writer
  * leverage reads wall clock / swallows missing run   -> test_same_run_date_*, test_orchestrator_adapter_*
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ga_writers import ga_vichara_writer as gw  # noqa: E402

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"
VARGAS = [f"D{i}" for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60,
                            81, 108, 144, 150, 15, 13, 14, 17, 18, 19)]
assert len(VARGAS) == 30

# sign order Aries..Pisces -> classical lord
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars",
              "Jupiter", "Saturn", "Saturn", "Jupiter"]
GRAHAS7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
SUBJ = gw.PLANET_TO_SUBJECT
AS_OF = "2026-09-08T00:00:00+00:00"


def _fid(*parts) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16]


def _fact(fid, cat, subj, key, text=None, num=None, jsonb=None):
    return {"fact_id": fid, "fact_category": cat, "fact_subject": subj, "fact_key": key,
            "fact_value_text": text, "fact_value_num": num, "fact_value_jsonb": jsonb}


def synthetic_facts() -> list[dict]:
    facts: list[dict] = []
    for v in VARGAS:
        place = {}  # lord -> placement house (one house per graha)
        for i, lord in enumerate(SIGN_LORDS):
            place.setdefault(lord, (i * 5) % 12 + 1)
        for i, lord in enumerate(SIGN_LORDS):
            src, tgt = i + 1, place[lord]
            facts.append(_fact(
                _fid("bsl", v, "lp", src), "bhava_significance_link", f"{v}_HOUSE_{src}_to_HOUSE_{tgt}",
                "lord_placed", text="neutral_link",
                jsonb={"varga": v, "source_house": src, "target_house": tgt, "lord": lord,
                       "link_kind": "lord_placed", "link_type": "neutral_link"}))
            for off in (7, 4):
                t2 = (tgt + off - 2) % 12 + 1
                facts.append(_fact(
                    _fid("bsl", v, "la", src, off), "bhava_significance_link",
                    f"{v}_HOUSE_{src}_to_HOUSE_{t2}", "lord_aspects", text="neutral_link",
                    jsonb={"varga": v, "source_house": src, "target_house": t2, "lord": lord,
                           "link_kind": "lord_aspects", "link_type": "neutral_link"}))
        combos = [(g, 7) for g in GRAHAS7] + [("Mars", 4), ("Mars", 8), ("Jupiter", 5), ("Jupiter", 9),
                                              ("Saturn", 3), ("Saturn", 10), ("Venus", 5), ("Mercury", 5),
                                              ("Sun", 5), ("Moon", 9), ("Mars", 9), ("Venus", 9)]
        for g, off in combos:
            t = (place.get(g, 1) + off - 2) % 12 + 1
            facts.append(_fact(
                _fid("asp", v, g, off), "aspect_parashari_per_varga", f"{v}_{SUBJ[g]}", f"house_{t}",
                num=1.0, jsonb={"varga": v, "source_house": place.get(g, 1), "target_house": t,
                                "offset": off, "source_sign": "x"}))
    # dignity + shadbala for ratification/consistency/leverage
    for v in ("D1", "D9", "D2", "D11"):
        for j, g in enumerate(GRAHAS7):
            facts.append(_fact(_fid("dig", v, g), "graha_dignity_per_varga", f"{v}_{SUBJ[g]}", "dignity_state",
                               text=["exalted", "own", "neutral", "debilitated"][(j + len(v)) % 4],
                               jsonb={"varga": v, "sign": f"S{(j * 3 + len(v)) % 12}", "house": j + 1}))
    for j, g in enumerate(GRAHAS7):
        facts.append(_fact(_fid("sb", g), "graha_shadbala_total", SUBJ[g], "rupa", num=4.0 + j * 0.7))
    return facts


def constants_rows() -> list[dict]:
    domains = {d: {"vargas": ["D1", "D2", "D9", "D11"], "houses": hs, "karaka": k, "provisional": False}
               for d, hs, k in [("wealth", [2, 11], "Jupiter"), ("career", [10, 6], "Saturn"),
                                ("marriage", [7], "Venus"), ("health", [1, 6], "Sun"),
                                ("general", [1, 5, 9], "Jupiter")]}
    vals = {
        "ratification_step": 0.2, "ratification_clamp": {"lo": 0.6, "hi": 1.4},
        "operative_vargas": domains, "valence_matrix": {},
        "dignity_score_map": {"exalted": 1.0, "own": 0.75, "neutral": 0.5, "debilitated": 0.25},
        "leverage_weights": {"lordship": 1.0, "karakatva": 0.75, "occupancy": 0.5, "yoga_participation": 0.75,
                             "capability_floor": 0.1, "runway_base": 1.0, "runway_scale": 0.5,
                             "runway_duration_norm_years": 20, "runway_start_horizon_years": 15,
                             "runway_lookforward_years": 30, "domain_yoga_keywords": {}},
        "consistency_weights": {"w_sign": 0.5, "w_dignity": 0.5},
    }
    return [{"constant_key": k, "value_jsonb": v} for k, v in vals.items()]


def dasha_rows() -> list[dict]:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    out = []
    for i, g in enumerate(GRAHAS7):
        start = base + timedelta(days=int(365.25 * 3 * i) + 17)
        dur = 365.25 * (6 + i)
        out.append({"lord_graha": g, "start_iso": start, "end_iso": start + timedelta(days=dur),
                    "duration_days": dur, "system_id": "vimshottari"})
        if i % 2 == 0:   # a second system with a NEARER period for some grahas (the mix)
            ms = base + timedelta(days=int(365.25 * 2 * i) + 3)
            out.append({"lord_graha": g, "start_iso": ms, "end_iso": ms + timedelta(days=365.25),
                        "duration_days": 365.25, "system_id": "mudda"})
    return out


class FakeCursor:
    def __init__(self, conn):
        self.c, self.rows, self.rowcount = conn, [], 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self.rows = []
        if s.startswith("SELECT fact_id"):
            self.rows = self.c.facts
        elif s.startswith("SELECT constant_key"):
            self.rows = self.c.consts
        elif s.startswith("SELECT lord_graha"):
            self.c.sqls.append(s)
            self.rows = self.c.dashas
        elif s.startswith("SELECT created_at FROM build_runs"):
            ts = self.c.runs.get(params[0])
            self.rows = [{"created_at": ts}] if ts is not None else []
        elif s.startswith("INSERT INTO chart_vichara"):
            self.c.inserted.append(params)
        elif s.startswith("DELETE FROM chart_vichara"):
            self.c.deleted += 1

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


RUN = "11111111-1111-4111-8111-111111111111"
RUN_CREATED = datetime(2026, 9, 8, 8, 10, 24, tzinfo=timezone.utc)


class FakeConn:
    def __init__(self, facts=None, dashas=None):
        self.facts = synthetic_facts() if facts is None else facts
        self.consts = constants_rows()
        self.dashas = dasha_rows() if dashas is None else dashas
        self.inserted: list[tuple] = []
        self.deleted = 0
        self.runs = {RUN: RUN_CREATED}
        self.sqls: list[str] = []

    def cursor(self):
        return FakeCursor(self)


# positional layout of _insert_rows' VALUES tuple
I_FAMILY, I_CF, I_CFA, I_JSONB, I_VNUM = 3, 14, 15, 12, 10


def run_writer(conn=None, as_of=None, build_id=RUN) -> tuple[FakeConn, int]:
    conn = conn or FakeConn()
    n = gw.build_ga_vichara_substep(CHART, build_id, AYA, conn, as_of=as_of)
    return conn, n


def by_family(conn: FakeConn) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in conn.inserted:
        out[p[I_FAMILY]] = out.get(p[I_FAMILY], 0) + 1
    return out


# ── (2) whole-row dedupe, (4) honest count ───────────────────────────────────

def test_valence_dedupe_1650_to_1500():
    # pre-dedupe: build rows exactly as the substep does, count valence_pass
    idx = gw.VicharaFactIndex(synthetic_facts())
    pre = []
    for v in sorted(idx.links_by_varga):
        pre += gw.build_valence_pass_rows(idx, v, {})
    for v in sorted(idx.aspects_by_varga):
        pre += gw.build_aspect_valence_rows(idx, v, {})
    assert len(pre) == 1650
    conn, n = run_writer()
    fam = by_family(conn)
    assert fam["valence_pass"] == 1500          # 150 exact duplicates removed (5 lords x 30 vargas)
    assert n == len(conn.inserted)              # reported count == rows actually inserted
    assert n == sum(fam.values())
    assert conn.deleted == 1
    # nothing else touched: other families unchanged by dedupe
    assert fam["leverage_index"] == 35


def test_dedupe_removed_only_lord_placed_of_dual_lords():
    idx = gw.VicharaFactIndex(synthetic_facts())
    pre = []
    for v in sorted(idx.links_by_varga):
        pre += gw.build_valence_pass_rows(idx, v, {})
    for v in sorted(idx.aspects_by_varga):
        pre += gw.build_aspect_valence_rows(idx, v, {})
    kept = gw.dedupe_rows(pre)
    kept_ids = {id(r) for r in kept}
    dropped = [r for r in pre if id(r) not in kept_ids]
    assert len(dropped) == 150
    assert {r["value_jsonb"]["link_kind"] for r in dropped} == {"lord_placed"}
    assert {r["subject"] for r in dropped} == {"MAR", "MER", "JUP", "VEN", "SAT"}
    from collections import Counter
    assert set(Counter(r["subject"] for r in dropped).values()) == {30}


def test_dedupe_loses_no_provenance():
    """The surviving row's constituent_fact_ids already lists every collapsed link."""
    idx = gw.VicharaFactIndex(synthetic_facts())
    pre = []
    for v in sorted(idx.links_by_varga):
        pre += gw.build_valence_pass_rows(idx, v, {})
    kept = gw.dedupe_rows(pre)
    kept_ids = {id(r) for r in kept}
    survivors = {}
    for r in kept:
        survivors.setdefault(gw._whole_row_key(r), r)
    for r in pre:
        if id(r) in kept_ids:
            continue
        surv = survivors[gw._whole_row_key(r)]
        assert set(r["constituent_fact_ids"]) <= set(surv["constituent_fact_ids"])
        assert len(surv["constituent_fact_ids"]) >= 2  # both collapsed links listed
    # and in the inserted data: every source link fact id is referenced by >=1 inserted valence row
    conn, _ = run_writer()
    referenced = {f for p in conn.inserted if p[I_FAMILY] == "valence_pass" for f in p[I_CF]}
    lp = {f["fact_id"] for f in synthetic_facts() if f["fact_key"] == "lord_placed"}
    assert lp <= referenced


def test_dedupe_keeps_non_duplicate_with_differing_provenance():
    base = {"vichara_family": "valence_pass", "subject": "MAR", "actor": "MAR", "target": "D1_HOUSE_3",
            "domain": None, "varga_id": "D1", "varga": "D1", "value_num": -0.5, "value_text": "malefic",
            "value_jsonb": {"a": 1, "b": 2}, "ratification_factor": None,
            "constituent_fact_ids": ["a", "b"], "formula_version": "v", "source_citation": "c"}
    same_but_reordered = {**base, "constituent_fact_ids": ["b", "a"], "value_jsonb": {"b": 2, "a": 1}}
    diff_prov = {**base, "constituent_fact_ids": ["a", "b", "c"]}
    diff_value = {**base, "value_num": -0.4}
    out = gw.dedupe_rows([base, same_but_reordered, diff_prov, diff_value])
    assert out == [base, diff_prov, diff_value]          # first occurrence kept, order preserved


# ── (3) collision assertion ──────────────────────────────────────────────────

def _row(**kw):
    r = {"vichara_family": "varga_consistency", "subject": "SUN", "actor": None, "target": None,
         "domain": None, "varga_id": None, "varga": None, "value_num": 0.5, "value_text": None,
         "value_jsonb": {}, "ratification_factor": None, "constituent_fact_ids": ["x", "y"],
         "formula_version": "varga_consistency_v1", "source_citation": "c"}
    r.update(kw)
    return r


def test_collision_assertion_unit_names_identity():
    a, b = _row(), _row(value_num=0.9, constituent_fact_ids=["y", "x"])  # same identity, different value
    with pytest.raises(gw.VicharaIdentityCollision) as e:
        gw.assert_no_identity_collision(CHART, AYA, [a, b])
    msg = str(e.value)
    assert "NOT a natural key" in msg and "SUN" in msg and "varga_consistency_v1" in msg and AYA in msg
    gw.assert_no_identity_collision(CHART, AYA, [a, _row(constituent_fact_ids=["x", "z"])])  # provenance differs -> ok


def test_collision_real_writer_raises_before_any_insert(monkeypatch):
    real = gw.build_varga_consistency_rows

    def colliding(idx, ws, wd):
        rows = real(idx, ws, wd)
        assert rows
        twin = dict(rows[0], value_num=rows[0]["value_num"] + 0.25)   # same identity, different value
        return rows + [twin]

    monkeypatch.setattr(gw, "build_varga_consistency_rows", colliding)
    conn = FakeConn()
    with pytest.raises(gw.VicharaIdentityCollision, match="grain"):
        gw.build_ga_vichara_substep(CHART, RUN, AYA, conn)
    assert conn.inserted == []                       # failed in the writer, nothing written


def test_no_collision_on_synthetic_canonical_like_data():
    conn, _ = run_writer()
    idents = {gw.row_identity(CHART, AYA, dict(
        vichara_family=p[I_FAMILY], subject=p[4], target=p[6], domain=p[7], varga_id=p[8],
        formula_version=p[16], constituent_fact_ids=p[I_CF])) for p in conn.inserted}
    assert len(idents) == len(conn.inserted)         # the identity is unique across the inserted set


# ── (1) sorted constituent_fact_ids ──────────────────────────────────────────

def test_cf_sorted_in_inserted_rows():
    conn, _ = run_writer()
    assert conn.inserted
    for p in conn.inserted:
        assert list(p[I_CF]) == sorted(p[I_CF]) and list(p[I_CFA]) == list(p[I_CF])
    # the valence rows really are multi-element (so an unsorted set could differ)
    assert any(len(p[I_CF]) >= 3 for p in conn.inserted if p[I_FAMILY] == "valence_pass")


def _dump(legacy: bool = False) -> dict:
    if legacy:   # PRE-FIX CONTROL: valence constituent_fact_ids in Python set iteration order (as before the fix)
        for name in ("build_valence_pass_rows", "build_aspect_valence_rows"):
            def _wrap(fn):
                def inner(*a, **k):
                    rows = fn(*a, **k)
                    for r in rows:
                        r["constituent_fact_ids"] = list(set(r["constituent_fact_ids"]))
                    return rows
                return inner
            setattr(gw, name, _wrap(getattr(gw, name)))
    conn, n = run_writer()
    rows = [list(map(lambda x: list(x) if isinstance(x, (list, tuple)) else x, p)) for p in conn.inserted]
    # CONTROL: the pre-fix expression, `list({...} - {None})`, for the same inputs
    idx = gw.VicharaFactIndex(synthetic_facts())
    legacy = []
    for v in sorted(idx.links_by_varga):
        for link in idx.links_by_varga[v]:
            if link["lord"]:
                legacy.append(list({link["fact_id"], *idx.lordship_fact_ids(v, link["lord"])} - {None}))
    return {"n": n, "rows": rows, "legacy_cf": legacy}


def _digest(rows) -> str:
    """Model of migration 920's valence_pass component: rows ordered by the key columns
    (which include constituent_fact_ids as an ordered array), each row's value columns
    hashed in order. Order of cf elements is part of the hashed bytes."""
    keyed = sorted(rows, key=lambda p: json.dumps([p[3], p[4], p[5], p[6], p[8], p[10], p[11], p[14]], default=str))
    h = hashlib.sha256()
    for p in keyed:
        h.update(json.dumps(p, sort_keys=True, default=str).encode())
    return h.hexdigest()


def _run_seed(seed: str, legacy: bool = False) -> dict:
    env = dict(os.environ, PYTHONHASHSEED=seed)
    args = ["--dump"] + (["--legacy"] if legacy else [])
    out = subprocess.run([sys.executable, str(Path(__file__).resolve()), *args], env=env,
                         capture_output=True, text=True, timeout=240, cwd=str(Path(__file__).resolve().parents[1]))
    assert out.returncode == 0, out.stderr[-2000:]
    return json.loads(out.stdout.splitlines()[-1])


def test_hashseed_independent_rows_and_digest_model():
    a, b = _run_seed("1"), _run_seed("2")
    assert a["n"] == b["n"] == len(a["rows"]) == len(b["rows"])
    assert a["rows"] == b["rows"]                                   # byte-identical inserted rows
    assert _digest(a["rows"]) == _digest(b["rows"])
    # CONTROL (pre-fix expression): set iteration order differs across seeds
    assert a["legacy_cf"] != b["legacy_cf"]


# ── migration-920 digest: the REAL compute_output_digest on a disposable Postgres ─────────
# Runs in CI in the job that hosts the Postgres service (dedicated step, own database
# `vichara_digest_test`). Under GITHUB_ACTIONS=true an unset/unreachable database FAILS (never
# a silent skip). Marked `integration` so the generic sidecar selection (`-m "not integration"`,
# no Postgres service) does not collect it. Locally it skips when no disposable DB is given.

DSN = os.environ.get("VICHARA_DIGEST_DSN")
MIG_920 = Path(__file__).resolve().parents[2] / "migrations/920_nirmana_l1_ga_vichara_output_digest_spec.sql"
_INSERT = """INSERT INTO chart_vichara (chart_id, ayanamsha_id, build_id, vichara_family, subject, actor, target,
    domain, varga_id, varga, value_num, value_text, value_jsonb, ratification_factor, constituent_fact_ids,
    constituent_facts_array, formula_version, source_citation, computed_at)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,NOW())"""
_DDL = """
DROP TABLE IF EXISTS chart_vichara; DROP TABLE IF EXISTS asset_output_digest_specs;
CREATE TABLE chart_vichara (id BIGSERIAL PRIMARY KEY, chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID,
  vichara_family TEXT NOT NULL, subject TEXT NOT NULL, actor TEXT, target TEXT, domain TEXT, varga_id TEXT, varga TEXT,
  value_num NUMERIC, value_text TEXT, value_jsonb JSONB, ratification_factor NUMERIC,
  constituent_fact_ids TEXT[] DEFAULT ARRAY[]::TEXT[], constituent_facts_array TEXT[] DEFAULT ARRAY[]::TEXT[],
  formula_version TEXT, source_citation TEXT, computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE asset_output_digest_specs (asset_id TEXT NOT NULL, spec_sha256 TEXT NOT NULL, spec JSONB NOT NULL,
  retired_at TIMESTAMPTZ, PRIMARY KEY (asset_id, spec_sha256));
"""


def _pg_digest(rows) -> str:
    import re
    import psycopg
    from psycopg.rows import dict_row
    from pipeline.orchestrator.output_digest import compute_output_digest
    m = re.search(r"VALUES\s*\(\s*'ga_vichara'\s*,\s*'([a-f0-9]{64})'\s*,\s*'(\{.*?\})'::jsonb\s*\)",
                  MIG_920.read_text(), flags=re.DOTALL)
    assert m, "migration 920 spec row not found"
    with psycopg.connect(DSN, row_factory=dict_row, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(_DDL)
            cur.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_vichara', %s, %s::jsonb)",
                        (m.group(1), m.group(2)))
            for p in rows:
                p = list(p)
                p[2] = None
                cur.execute(_INSERT, p)
            digest, _ = compute_output_digest(cur, asset_id="ga_vichara")
        conn.rollback()
    return digest


def _require_pg() -> None:
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    if not DSN:
        msg = "VICHARA_DIGEST_DSN (disposable Postgres) is not set"
        if in_ci:
            pytest.fail(f"{msg}: under GITHUB_ACTIONS=true this suite REQUIRES a database (never a silent skip)")
        pytest.skip(f"NOT_RUN: {msg}")
    try:
        import psycopg
        with psycopg.connect(DSN, connect_timeout=10):
            pass
    except Exception as exc:  # noqa: BLE001
        if in_ci:
            pytest.fail(f"VICHARA_DIGEST_DSN unreachable under GITHUB_ACTIONS=true: {exc}")
        pytest.skip(f"NOT_RUN: VICHARA_DIGEST_DSN unreachable ({exc})")


@pytest.mark.integration
def test_mig920_real_digest_hashseed_independent_after_fix_and_dependent_before():
    _require_pg()
    a, b = _run_seed("1"), _run_seed("2")
    assert a["rows"] == b["rows"]
    d_a, d_b = _pg_digest(a["rows"]), _pg_digest(b["rows"])
    assert d_a == d_b                                           # AFTER the fix: same digest across set orders
    la, lb = _run_seed("1", legacy=True), _run_seed("2", legacy=True)
    assert la["n"] == lb["n"]
    assert _pg_digest(la["rows"]) != _pg_digest(lb["rows"])     # BEFORE the fix: digest moves with set order


# ── dasha-system disclosure (SS ruling: disclosure only, NO number changes) ─────────────

def _legacy_runway(graha, dasha_rows, now, weights):
    """Verbatim copy of the pre-disclosure `_dasha_runway` (selection and arithmetic)."""
    lookforward_years = float(weights.get("runway_lookforward_years", 30))
    base = float(weights.get("runway_base", 1.0))
    scale = float(weights.get("runway_scale", 0.5))
    dur_norm = float(weights.get("runway_duration_norm_years", 20))
    start_horizon = float(weights.get("runway_start_horizon_years", 15))
    best = None
    for r in dasha_rows:
        if str(r.get("lord_graha")) != graha:
            continue
        start, end = r.get("start_iso"), r.get("end_iso")
        if start is None or end is None:
            continue
        if end < now:
            continue
        s_years = max(0.0, (start - now).days / 365.25)
        if s_years > lookforward_years:
            continue
        if best is None or s_years < best[0]:
            dd = r.get("duration_days")
            y_years = float(dd) / 365.25 if dd is not None else (end - start).days / 365.25
            best = (s_years, y_years)
    if best is None:
        return 1.0, {"dasha_runway_found": False}
    s_years, y_years = best
    weight = base + scale * (y_years / dur_norm) * max(0.0, 1 - s_years / start_horizon)
    return weight, {"dasha_runway_found": True, "years_to_start": round(s_years, 3), "md_duration_years": round(y_years, 3)}


_DISCLOSURE_KEYS = ("dasha_runway_systems", "dasha_runway_setting_system")


def test_runway_disclosure_changes_no_number_randomised():
    import random
    rng = random.Random(920)
    W = {"runway_lookforward_years": 30, "runway_base": 1.0, "runway_scale": 0.5,
         "runway_duration_norm_years": 20, "runway_start_horizon_years": 15}
    now = datetime(2026, 9, 8, tzinfo=timezone.utc)
    systems = ["vimshottari", "mudda", "yogini", "ashtottari", "naisargika", "narayana", "kalachakra", "chara_karaka"]
    for _ in range(300):
        rows = []
        for _k in range(rng.randint(0, 40)):
            st = now + timedelta(days=rng.randint(-4000, 14000))
            dur = rng.choice([None, rng.randint(200, 9000)])
            rows.append({"lord_graha": rng.choice(gw.CLASSICAL_GRAHAS), "start_iso": st,
                         "end_iso": st + timedelta(days=dur or 700), "duration_days": dur,
                         "system_id": rng.choice(systems)})
        rng.shuffle(rows)
        for g in gw.CLASSICAL_GRAHAS:
            w_old, m_old = _legacy_runway(g, rows, now, W)
            w_new, m_new = gw._dasha_runway(g, rows, now, W)
            assert w_new == w_old
            assert {k: v for k, v in m_new.items() if k not in _DISCLOSURE_KEYS} == m_old
            assert m_new["dasha_runway_systems"] == sorted(m_new["dasha_runway_systems"])
            assert (m_new["dasha_runway_setting_system"] is None) == (not m_old["dasha_runway_found"])
            if m_old["dasha_runway_found"]:
                assert m_new["dasha_runway_setting_system"] in m_new["dasha_runway_systems"]


def test_disclosure_names_the_setting_system_and_contributors():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    mk = lambda sys_, d0, dur: {"lord_graha": "Mars", "start_iso": now + timedelta(days=d0),
                                "end_iso": now + timedelta(days=d0 + dur), "duration_days": dur, "system_id": sys_}
    rows = [mk("vimshottari", 3000, 2555), mk("mudda", 400, 365), mk("yogini", 900, 700),
            mk("kalachakra", -5000, 100),          # elapsed: not a contributor
            mk("naisargika", 20000, 700)]           # beyond the 30-year look-forward: not a contributor
    w, m = gw._dasha_runway("Mars", rows, now, {})
    assert m["dasha_runway_systems"] == ["mudda", "vimshottari", "yogini"]
    assert m["dasha_runway_setting_system"] == "mudda"


def test_leverage_values_byte_identical_to_pre_disclosure_at_equal_as_of():
    conn, _ = run_writer(_conn_with_run(RUN_CREATED))
    now = datetime(2026, 9, 8, tzinfo=timezone.utc)
    consts = {r["constant_key"]: r["value_jsonb"] for r in conn.consts}
    seen_setting = set()
    for p in _leverage(conn):
        j = json.loads(p[I_JSONB])
        graha = gw.SUBJECT_TO_PLANET[p[4]]
        w_old, m_old = _legacy_runway(graha, conn.dashas, now, consts["leverage_weights"])
        assert j["dasha_runway_weight"] == round(w_old, 4)
        for k, v in m_old.items():
            assert j[k] == v
        seen_setting.add(j["dasha_runway_setting_system"])
        assert j["dasha_runway_systems"] == sorted(j["dasha_runway_systems"])
    assert "mudda" in seen_setting   # the mix is real in the fixture
    # the other four families carry no disclosure/as-of keys at all
    for p in conn.inserted:
        if p[I_FAMILY] != "leverage_index" and p[I_JSONB]:
            j = json.loads(p[I_JSONB])
            assert not ({"as_of", "as_of_source", *_DISCLOSURE_KEYS} & set(j))


def test_dasha_loader_reads_system_id_with_a_total_order():
    conn, _ = run_writer()
    assert conn.sqls and "system_id" in conn.sqls[0].split("FROM")[0]
    assert "ORDER BY start_iso, system_id, lord_graha" in conn.sqls[0]


# ── (7) AS-OF = the build run's creation DATE: the clock must not leak into rows ──

class _FrozenDT(datetime):
    _now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        return cls._now.astimezone(tz) if tz else cls._now


def _leverage(conn):
    return [p for p in conn.inserted if p[I_FAMILY] == "leverage_index"]


def _as_of_meta(conn):
    j = json.loads(_leverage(conn)[0][I_JSONB])
    return j["as_of"], j["as_of_source"]


def _conn_with_run(created):
    c = FakeConn()
    c.runs = {RUN: created}
    return c


def test_same_run_date_two_wall_clocks_byte_identical(monkeypatch):
    monkeypatch.setattr(gw, "datetime", _FrozenDT)
    _FrozenDT._now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
    c1, n1 = run_writer(_conn_with_run(RUN_CREATED))
    _FrozenDT._now = datetime(2027, 3, 1, 3, 0, tzinfo=timezone.utc)       # wall clock shifted ~6 months
    # same run DATE (different time of day within the date) => identical
    c2, n2 = run_writer(_conn_with_run(datetime(2026, 9, 8, 23, 59, tzinfo=timezone.utc)))
    assert n1 == n2
    assert c1.inserted == c2.inserted                    # byte-identical output, ALL families
    assert _as_of_meta(c1) == ("2026-09-08", "build_run_created_at")
    for p in _leverage(c1):                              # recorded on EVERY leverage row
        j = json.loads(p[I_JSONB])
        assert (j["as_of"], j["as_of_source"]) == ("2026-09-08", "build_run_created_at")


def test_different_run_dates_differ_in_values_and_recorded_as_of_but_not_count(monkeypatch):
    monkeypatch.setattr(gw, "datetime", _FrozenDT)
    c1, n1 = run_writer(_conn_with_run(datetime(2026, 9, 8, 8, 0, tzinfo=timezone.utc)))
    c2, n2 = run_writer(_conn_with_run(datetime(2027, 3, 1, 8, 0, tzinfo=timezone.utc)))
    assert n1 == n2 == len(c1.inserted) == len(c2.inserted)               # COUNT is clock-independent
    assert _as_of_meta(c1) == ("2026-09-08", "build_run_created_at")
    assert _as_of_meta(c2) == ("2027-03-01", "build_run_created_at")
    assert [p[I_VNUM] for p in _leverage(c1)] != [p[I_VNUM] for p in _leverage(c2)]
    assert [json.loads(p[I_JSONB])["dasha_runway_weight"] for p in _leverage(c1)] != \
           [json.loads(p[I_JSONB])["dasha_runway_weight"] for p in _leverage(c2)]
    # every other family is untouched by the as-of
    assert [p for p in c1.inserted if p[I_FAMILY] != "leverage_index"] == \
           [p for p in c2.inserted if p[I_FAMILY] != "leverage_index"]


def test_config_override_beats_run_date(monkeypatch):
    monkeypatch.setattr(gw, "datetime", _FrozenDT)
    c, _ = run_writer(_conn_with_run(RUN_CREATED), as_of="2026-01-01T15:00:00Z")
    assert _as_of_meta(c) == ("2026-01-01", "config_override")


def test_orchestrator_adapter_without_resolvable_run_date_raises(monkeypatch):
    """The wall clock must be IMPOSSIBLE on the orchestrator path."""
    from pipeline.orchestrator.writers.ga_vichara import GaVicharaWriter
    from pipeline.orchestrator.writers import ContextSpec, SubStep
    monkeypatch.setattr(gw, "datetime", _FrozenDT)
    step = SubStep(key=f"ayanamsha_{AYA}")
    # (a) run id present but build_runs row missing / created_at NULL
    for runs in ({}, {RUN: None}):
        conn = FakeConn()
        conn.runs = runs
        ctx = ContextSpec(asset_id="ga_vichara", build_id=RUN, db_conn=conn, config={"chart_id": CHART})
        with pytest.raises(gw.AsOfUnresolvable, match="wall clock"):
            GaVicharaWriter().run_substep(ctx, step)
        assert conn.inserted == [] and conn.deleted == 0
    # (b) no run id at all in the orchestrator context
    conn = FakeConn()
    ctx = ContextSpec(asset_id="ga_vichara", build_id="", db_conn=conn, config={"chart_id": CHART})
    with pytest.raises(gw.AsOfUnresolvable, match="wall clock"):
        GaVicharaWriter().run_substep(ctx, step)
    assert conn.inserted == []
    # (c) happy path through the adapter: as-of = run creation date
    conn = FakeConn()
    ctx = ContextSpec(asset_id="ga_vichara", build_id=RUN, db_conn=conn, config={"chart_id": CHART})
    res = GaVicharaWriter().run_substep(ctx, step)
    assert res.rows_inserted == len(conn.inserted) == 1556
    assert _as_of_meta(conn) == ("2026-09-08", "build_run_created_at")


def test_direct_call_without_run_is_flagged_unpinned_and_cannot_pass_as_pinned(monkeypatch):
    monkeypatch.setattr(gw, "datetime", _FrozenDT)
    _FrozenDT._now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
    c1, _ = run_writer(FakeConn(), build_id=None)
    _FrozenDT._now = datetime(2027, 3, 1, 3, 0, tzinfo=timezone.utc)
    c2, _ = run_writer(FakeConn(), build_id=None)
    assert _as_of_meta(c1) == ("2026-09-08", "wall_clock_unpinned")
    assert _as_of_meta(c2) == ("2027-03-01", "wall_clock_unpinned")
    assert _leverage(c1) != _leverage(c2)


def test_no_env_var_pin_exists(monkeypatch):
    assert not hasattr(gw, "AS_OF_ENV_VAR")
    monkeypatch.setenv("GA_VICHARA_AS_OF", "2020-01-01")
    c, _ = run_writer(_conn_with_run(RUN_CREATED))
    assert _as_of_meta(c) == ("2026-09-08", "build_run_created_at")       # env is ignored


def test_adapter_passes_override_and_requires_run_date(monkeypatch):
    from pipeline.orchestrator.writers.ga_vichara import GaVicharaWriter
    from pipeline.orchestrator.writers import ContextSpec, SubStep
    seen = {}

    def fake_build(**kw):
        seen.update(kw)
        return 7

    monkeypatch.setattr(gw, "build_ga_vichara_substep", fake_build)
    ctx = ContextSpec(asset_id="ga_vichara", build_id=RUN, db_conn=object(),
                      config={"chart_id": CHART, "as_of": AS_OF})
    res = GaVicharaWriter().run_substep(ctx, SubStep(key=f"ayanamsha_{AYA}"))
    assert seen["as_of"] == AS_OF and seen["require_run_date"] is True and res.rows_inserted == 7


if __name__ == "__main__":
    if "--dump" in sys.argv:
        print(json.dumps(_dump(legacy="--legacy" in sys.argv), default=str))
