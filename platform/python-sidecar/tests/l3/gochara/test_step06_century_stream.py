"""Pravāha A2.5 — the century streaming chain (CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §2/§3).

Pure-python, no Swiss calls, no DB. What this file proves:

  * NDJSON write/read round-trip is IDENTICAL to the monolithic --episodes-out
    JSON path: the same small episode set written by
    step06_enumerate_episodes.write_episodes_ndjson and read back by
    step06_candidate_build.read_episodes_ndjson yields the same dicts, the
    same canonical (t_in, body, relation) ordering, and the same
    order-independent content digest as the monolithic write/read;
  * --episodes-out and --episodes-ndjson-out are mutually exclusive in the
    enumeration driver (exit 3, before any ephemeris or DB touch); exactly
    one is required;
  * --episodes-json and --episodes-ndjson are mutually exclusive in the
    candidate build (exit 3);
  * per-body NDJSON appends concatenate exactly: two append-mode writes to
    one file read back as the canonical concatenation, and the reader's
    re-sort reproduces the monolithic dedupe order byte-for-byte;
  * century_run.py REFUSES without PRAVAHA_CENTURY_RUN_AUTHORIZED=1 (exit 3),
    and refuses a non-pinned horizon even with the marker (ADK-0028), in both
    cases before any subprocess starts;
  * the GCS upload path is a disclosed no-op without --gcs-prefix.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

CUT_OVER_DIR = (
    Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover"
)
ENUM_PATH = CUT_OVER_DIR / "step06_enumerate_episodes.py"
BUILD_PATH = CUT_OVER_DIR / "step06_candidate_build.py"
CENTURY_PATH = CUT_OVER_DIR / "century_run.py"

UTC = timezone.utc


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


enum_mod = _load(ENUM_PATH, "step06_enumerate_episodes")
build_mod = _load(BUILD_PATH, "step06_candidate_build")
century_mod = _load(CENTURY_PATH, "century_run")


def _episode(body: str, relation: str, t_in: datetime, target_ref: str) -> dict:
    """A minimal ledger `_normalize_episode`-shaped dict (datetimes live, as
    the driver holds them before default=str serialization)."""
    return {
        "independence_group": f"ig-{body}-{relation}-{target_ref}",
        "body": body, "relation": relation,
        "aspect_deg": 0,
        "target_type": "karaka", "target_ref": target_ref,
        "target_fact_id": None, "target_resolution_state": "resolved",
        "target_longitude_deg": 90.0,
        "t_in": t_in, "t_exact": t_in + timedelta(hours=1),
        "t_out": t_in + timedelta(hours=2),
        "bracket_seconds": 300, "tolerance_arcsec": 2.0,
        "truncated_at_horizon": None, "branch": "direct",
        "station_flag": None, "exact_crossing": True,
        "orb_max_deg": 5.0, "orb_source": "orb_conj_slow",
        "dwell_days": None,
        "epistemic_class": "observed_event", "completeness_state": "applied",
        "operator_role": "kernel", "precision_regime": "instant_grain",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": {"backend": "swieph", "retflag": 258},
        "evidence_fact_ids": [],
        "classical_citation": None, "uncited_extension": True,
        "corpus_verifiable": None,
    }


BASE = datetime(2020, 3, 1, 0, 0, 0, tzinfo=UTC)
SUN_EPS = [
    _episode("Sun", "conjunction", BASE + timedelta(days=10), "SUN"),
    _episode("Sun", "conjunction", BASE + timedelta(days=2), "MOON"),
]
SAT_EPS = [
    _episode("Saturn", "conjunction", BASE + timedelta(days=5), "SUN"),
    _episode("Saturn", "return", BASE + timedelta(days=1), "SATURN"),
]
ALL_EPS = SUN_EPS + SAT_EPS


def _monolithic_round_trip(path: Path, episodes: list[dict]) -> list[dict]:
    """What the decade-scale path does: json.dumps(indent=2, default=str) out,
    json.loads + _coerce_episode_times back in."""
    path.write_text(json.dumps(episodes, indent=2, default=str) + "\n")
    return build_mod._coerce_episode_times(json.loads(path.read_text()))


def _content_digest(episodes: list[dict]) -> str:
    """Order-independent content digest of a read-back episode set: sha256
    over the sorted canonical serialization of each row (the same discipline
    as ledger.reference_digest/_canonical_row_set — the manifest digest is
    computed over the canonically sorted DB row set, so set equality is what
    must hold)."""
    canon = sorted(
        json.dumps(e, sort_keys=True, separators=(",", ":"), default=str)
        for e in episodes)
    return hashlib.sha256(
        json.dumps(canon, separators=(",", ":")).encode("utf-8")).hexdigest()


# ── round-trip identity ────────────────────────────────────────────────────────


def _canonical_order(episodes: list[dict]) -> list[dict]:
    return sorted(episodes, key=lambda d: (d["t_in"], d["body"], d["relation"]))


def test_ndjson_round_trip_identical_to_monolithic(tmp_path):
    mono = _monolithic_round_trip(tmp_path / "eps.json", ALL_EPS)
    nd = tmp_path / "eps.ndjson"
    assert enum_mod.write_episodes_ndjson(str(nd), ALL_EPS) == len(ALL_EPS)
    streamed = build_mod.read_episodes_ndjson(str(nd))
    # same SET, and the reader's canonical order equals the canonically
    # sorted monolithic payload (the order dedupe_episodes leaves on disk)
    assert streamed == _canonical_order(mono)
    assert _content_digest(streamed) == _content_digest(mono)


def test_ndjson_reader_reproduces_canonical_order(tmp_path):
    """The concatenated per-body stream is per-body ordered (Sun block, then
    Saturn); the reader re-sorts by the dedupe key (t_in, body, relation), so
    the resulting list equals the monolithic payload of the same episodes
    sorted by that key — byte-identical row order, not just row set."""
    eps_dir = tmp_path / "episodes"
    enum_mod.write_episodes_ndjson(str(eps_dir / "Sun.ndjson"), SUN_EPS)
    enum_mod.write_episodes_ndjson(str(eps_dir / "Saturn.ndjson"), SAT_EPS)
    streamed = build_mod.read_episodes_ndjson(str(eps_dir / "*.ndjson"))
    expected = sorted(
        _monolithic_round_trip(tmp_path / "eps.json", ALL_EPS),
        key=lambda d: (d["t_in"], d["body"], d["relation"]),
    )
    assert streamed == expected
    # The glob's file order (Saturn before Sun alphabetically) must not leak:
    # canonical order here is Saturn(BASE+1d), Sun(BASE+2d), Saturn(BASE+5d),
    # Sun(BASE+10d).
    assert [e["body"] for e in streamed] == ["Saturn", "Sun", "Saturn", "Sun"]
    assert [(e["t_in"], e["body"]) for e in streamed] == [
        (e["t_in"], e["body"]) for e in expected]


def test_per_body_appends_concatenate_exactly(tmp_path):
    """Two append-mode writes to ONE file (the per-body chunked shape) read
    back as exactly the concatenation, line per episode, nothing lost or
    reordered within a block."""
    nd = tmp_path / "sun.ndjson"
    enum_mod.write_episodes_ndjson(str(nd), SUN_EPS[:1])
    enum_mod.write_episodes_ndjson(str(nd), SUN_EPS[1:], append=True)
    lines = nd.read_text().strip().split("\n")
    assert len(lines) == len(SUN_EPS)
    read_back = [json.loads(line) for line in lines]
    assert read_back == json.loads(json.dumps(SUN_EPS, default=str))
    # and the full reader sees the same rows in canonical order
    assert build_mod.read_episodes_ndjson(str(nd)) == _canonical_order(
        _monolithic_round_trip(tmp_path / "m.json", SUN_EPS))


def test_ndjson_reader_missing_file_refuses(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_mod.read_episodes_ndjson(str(tmp_path / "nope" / "*.ndjson"))


# ── flag validation ────────────────────────────────────────────────────────────


def _argv(*extra: str) -> list[str]:
    return ["--dsn", "postgresql://wp6:local@localhost:55433/wp6",
            "--chart-id", "482012f1-0000-0000-0000-000000000000", *extra]


def test_step06_output_flags_mutually_exclusive(tmp_path, capsys):
    rc = enum_mod.main(_argv(
        "--episodes-out", str(tmp_path / "a.json"),
        "--episodes-ndjson-out", str(tmp_path / "a.ndjson"),
        "--coverage-out", str(tmp_path / "c.json")))
    assert rc == 3
    assert "exactly one" in capsys.readouterr().err


def test_step06_requires_exactly_one_output_flag(tmp_path, capsys):
    rc = enum_mod.main(_argv("--coverage-out", str(tmp_path / "c.json")))
    assert rc == 3
    assert "exactly one" in capsys.readouterr().err


def test_candidate_build_input_flags_mutually_exclusive(tmp_path, capsys):
    rc = build_mod.main(_argv(
        "--episodes-json", str(tmp_path / "a.json"),
        "--episodes-ndjson", str(tmp_path / "*.ndjson"),
        "--coverage-json", str(tmp_path / "c.json")))
    assert rc == 3
    assert "mutually exclusive" in capsys.readouterr().err


def test_candidate_build_ndjson_requires_coverage(tmp_path, capsys):
    rc = build_mod.main(_argv("--episodes-ndjson", str(tmp_path / "*.ndjson")))
    assert rc == 3


# ── century_run guard (ADK-0028) ───────────────────────────────────────────────


def test_century_run_refuses_without_env_marker(monkeypatch, capsys):
    monkeypatch.delenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", raising=False)
    rc = century_mod.main(["--dsn", "postgresql://x", "--chart-id", "482012f1"])
    assert rc == 3
    assert "ADK-0028" in capsys.readouterr().err


def test_century_run_refuses_non_pinned_horizon(monkeypatch, capsys):
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    rc = century_mod.main([
        "--dsn", "postgresql://x", "--chart-id", "482012f1",
        "--horizon-start", "1984-02-05T00:00:00+00:00",
        "--horizon-end", "2080-01-01T00:00:00+00:00"])
    assert rc == 3
    assert "pinned" in capsys.readouterr().err


def test_century_run_imports_persisted_bodies():
    """The driver loops the pinned eight non-Moon grahas, imported from the
    enumerator (never restated here)."""
    assert century_mod.PERSISTED_BODIES == enum_mod.PERSISTED_BODIES
    assert tuple(century_mod.PERSISTED_BODIES) == (
        "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")


def test_gcs_upload_noop_without_prefix(tmp_path, capsys):
    nd = tmp_path / "Sun.ndjson"
    enum_mod.write_episodes_ndjson(str(nd), SUN_EPS)
    msg = century_mod.upload_ndjson_to_gcs(None, nd, "Sun.ndjson")
    assert "SKIPPED" in msg
    assert not (tmp_path / "uploaded").exists()
