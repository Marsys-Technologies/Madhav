"""VC-2 lane rehearsal: the arm generator against real candidate tables on a guarded disposable database.

The candidate field / Taraṅga / jury tables come from the repository's own migrations (applied verbatim);
only chart_dashas and life_events are minimal stand-ins carrying the columns the reader selects. Every value
is synthetic (a non-canonical chart id, evaluation_eligible = false): this proves the machinery, never a chart
fact, an outcome, a baseline or a result. Evidence (identifiers, counts, digests) goes to
$VC2_REHEARSAL_EVIDENCE_DIR when set.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

import psycopg
import pytest
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[6]
SRC = Path(os.environ.get("VC2_SRC_DIR", ROOT / "platform/scripts/value_checkpoint"))
sys.path.insert(0, str(SRC))
core = importlib.import_module("vc2_core")
run = importlib.import_module("vc2_run")

MIG = ROOT / "platform/migrations"
CHART = "00000000-0000-0000-0000-00000000c0de"  # synthetic: NOT the canonical chart
BUILD = "00000000-0000-0000-0000-00000000b001"
GEN, OTHER = "candidate:vc2-rehearsal", "candidate:vc2-other"
BIRTH = datetime(1990, 1, 1, tzinfo=timezone.utc)
CLASSES = [f"vc2_class_{i}" for i in range(6)]
MD_YEARS = (7, 20, 6, 10, 7, 18, 16, 19, 17)
SENTINEL = "SENTINEL_OUTCOME_TEXT_DO_NOT_LEAK"


def _add_years(d: date, y: int) -> date:
    return d.replace(year=d.year + y)


@pytest.fixture(scope="module")
def lane(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn) as conn:
        conn.execute("CREATE TABLE build_runs(id uuid PRIMARY KEY, chart_id uuid NOT NULL)")
        conn.execute("CREATE TABLE kala_layer_candidate(chart_id uuid, generation text, build_id uuid, state text, "
                     "conventions jsonb, PRIMARY KEY(chart_id, generation))")
        conn.execute("CREATE TABLE kala_layer_head(chart_id uuid PRIMARY KEY, generation text)")
        conn.execute("CREATE TABLE build_substep_progress(chart_id uuid, asset_id text, substep_key text, "
                     "build_fingerprint text, rows_written int, completed_at timestamptz, "
                     "PRIMARY KEY(chart_id, asset_id, substep_key))")
        conn.execute("CREATE TABLE asset_registry(asset_id text PRIMARY KEY, count_sql text, integrity_check_sql text)")
        conn.execute("INSERT INTO asset_registry VALUES ('ka_taranga','SELECT 0','SELECT false')")
        conn.execute("CREATE TABLE kala_taranga(chart_id uuid, month date, scope_kind text, scope_id text, "
                     "activation numeric, components jsonb)")
        for n in [488, 489, 490, 492, 493, 494, 495, 496]:
            body = next((ROOT / "platform/supabase/migrations").glob(f"{n}_*.sql")).read_text()
            body = re.sub(r"--[^\n]*", "", body)
            for statement in re.findall(r"^CREATE (?:TABLE|(?:UNIQUE )?INDEX)[\s\S]*?;", body, re.M):
                conn.execute(statement)
        body = (ROOT / "platform/supabase/migrations/571_p3a_shape_only_tier.sql").read_text()
        conn.execute(re.search(r"ALTER TABLE kala_field_windows\s+ADD COLUMN[^;]*;", body)[0])
        for name in ("1385_k5_g1a_candidate_field.sql", "1393_k5_g1a_candidate_identity.sql",
                     "1350_kala_jury_candidate.sql", "1389_k6_taranga_candidate.sql"):
            conn.execute((MIG / name).read_text())
        # minimal stand-ins for the two L1 reads
        conn.execute("CREATE TABLE chart_dashas(dasha_row_id uuid PRIMARY KEY, chart_id uuid, system_id text, "
                     "level_n int, ayanamsha_id text, lord_graha text, start_date date, end_date date, "
                     "start_iso timestamptz)")
        conn.execute("CREATE TABLE life_events(event_id text PRIMARY KEY, chart_id uuid, event_date date, "
                     "description text)")
        conn.commit()
    return isolated_kala_db_dsn


def _seed(conn):
    conn.execute("INSERT INTO build_runs VALUES (%s,%s)", (BUILD, CHART))
    for gen in (GEN, OTHER):
        conn.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,'building',%s)", (CHART, gen, BUILD, Jsonb({})))
    cursor, chapters = BIRTH.date(), []
    for i, years in enumerate(MD_YEARS):
        end = _add_years(cursor, years)
        row_id = str(UUID(int=0xD0000 + i))
        conn.execute("INSERT INTO chart_dashas VALUES (%s,%s,'vimshottari',1,'lahiri_chitrapaksha',%s,%s,%s,%s)",
                     (row_id, CHART, f"MD{i}", cursor, end, datetime.combine(cursor, datetime.min.time(), timezone.utc)))
        conn.execute("INSERT INTO chart_dashas VALUES (%s,%s,'vimshottari',2,'lahiri_chitrapaksha','AD',%s,%s,%s)",
                     (str(UUID(int=0xE0000 + i)), CHART, cursor, end, datetime.combine(cursor, datetime.min.time(), timezone.utc)))
        chapters.append((cursor, end))
        cursor = end
    # synthetic event ids/dates; description is a leak sentinel that must never reach an output
    for k in range(40):
        conn.execute("INSERT INTO life_events VALUES (%s,%s,%s,%s)",
                     (f"vc2-ev-{k:02d}", CHART, BIRTH.date() + timedelta(days=173 * k * (1 + k // 12)), SENTINEL))
    pin = {"birth_utc": BIRTH.isoformat(), "axis": "days_since_birth_UT; ephemeris_daily_noon_UT"}
    for gen in (GEN, OTHER):
        conn.execute("INSERT INTO kala_field_snapshots_candidate (generation, chart_id, field_snapshot_id, weights_version, "
                     "x_schema_version, corpus_pin, config_pin, horizon_days) VALUES (%s,%s,'snap','w','x','c',%s,36525)",
                     (gen, CHART, Jsonb(pin)))
    total_months = sum(MD_YEARS) * 12
    for index, cls in enumerate(CLASSES):
        for gen, tag in ((GEN, "g"), (OTHER, "o")):
            if index == 5 and gen == GEN:
                continue  # class 5: no Sangam / field / Taranga rows at all => unavailable arm inputs
            for chapter_index, (start, end) in enumerate(chapters):
                ws = datetime.combine(start + timedelta(days=200), datetime.min.time(), timezone.utc)
                we = ws + timedelta(days=150 + 10 * index)
                conn.execute(
                    "INSERT INTO kala_jury_candidate (chart_id, generation, event_class, assertion_id, window_start, "
                    "window_end, subject, roots, provenance, coverage, evidence_graph, witness_groups, witness_signature, "
                    "conditional_effect, conditional_null, pipeline_null_reason) VALUES "
                    "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'not_run')",
                    (CHART, gen, cls, f"{tag}-{cls}-{chapter_index}", ws, we, Jsonb({"k": 1}), Jsonb({"r": 1}),
                     Jsonb({"p": 1}), Jsonb({}), Jsonb([]), Jsonb([]), Jsonb(["G-P", "G-T"] if chapter_index % 2 else ["G-P"]),
                     0.1 * (chapter_index + 1) + (0 if tag == "g" else 9.0),
                     Jsonb({"estimand": "jury_incremental_agreement", "denominator": 8, "verdict": "pass"})))
            for m in range(total_months):
                first = date(1990 + m // 12, m % 12 + 1, 1)
                conn.execute("INSERT INTO kala_taranga_candidate (chart_id, generation, month, scope_kind, scope_id, "
                             "integral, units, risk_set_null_reason, judge_count_null_reason, overlap_flag, source_refs, "
                             "formula_version) VALUES (%s,%s,%s,'event_class',%s,%s,'expected_events','n','n',false,%s,'v1')",
                             (CHART, gen, first, cls, round(0.01 * ((m * (index + 3)) % 17) + (0 if tag == "g" else 5), 6),
                              Jsonb({"field_snapshot_ids": ["snap"], "field_segment_ids": [1]})))
            per_chapter = 150 if index == 3 else 6  # class 3 is dense: B must overflow the word ceiling
            seg = 0
            for chapter_index, (start, end) in enumerate(chapters):
                t0 = float((start - BIRTH.date()).days)
                span = float((end - start).days)
                for j in range(per_chapter):
                    a, b = t0 + span * j / per_chapter, t0 + span * (j + 1) / per_chapter
                    conn.execute(
                        "INSERT INTO kala_field_candidate (generation, chart_id, event_class, segment_index, t_start, t_end, "
                        "alpha, gamma, lambda_start, lambda_end, integral_days, promise_term, clock_term_start, "
                        "modifier_term_start, suppression_term_start, signed_obstruction_start, weights_version, "
                        "x_schema_version, field_snapshot_id) VALUES (%s,%s,%s,%s,%s,%s,-3.5,0.0001,0.03,0.03,0.5,"
                        "0.6,0.2,0.1,0.9,-0.1,'w','x','snap')", (gen, CHART, cls, seg, a, b))
                    seg += 1
                conn.execute(
                    "INSERT INTO kala_field_windows_candidate (generation, chart_id, window_id, event_class, t_start, t_end, "
                    "window_start, window_end, peak_date, t_peak, lambda_peak, expected_count, duration_days, "
                    "promise_state, temporal_shape, weakest_link, baseline_is_synthetic, weights_version, "
                    "x_schema_version, field_snapshot_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0.1,0.2,10,'strong','interval',"
                    "'clock',%s,'w','x','snap')",
                    (gen, CHART, f"{tag}-{cls}-{chapter_index}", cls, t0 + 1, t0 + 40, start, start + timedelta(days=40),
                     start + timedelta(days=20), t0 + 20, index == 4))  # class 4: synthetic baseline prior
    return chapters


def eligibility():
    return {"chart_id": CHART, "synthetic": True, "evaluation_eligible": False, "real_outcome_records": False,
            "consent_ref": None, "lel_coverage": {"ref": "vc2-synthetic-coverage", "start": "1990-01-01", "end": "2200-01-01"},
            "classes": [{"event_class": c, "prior_provenance": "synthetic-rehearsal", "calibrated": True,
                         "synthetic_prior": False} for c in CLASSES]}


@pytest.fixture
def seeded(lane):
    with psycopg.connect(lane) as conn:
        chapters = _seed(conn)
        conn.commit()
    yield lane, chapters
    with psycopg.connect(lane) as conn:
        for table in ("kala_field_windows_candidate", "kala_field_candidate", "kala_taranga_candidate",
                      "kala_jury_candidate", "kala_field_snapshots_candidate", "life_events", "chart_dashas",
                      "kala_layer_candidate", "build_runs"):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()


def loader(dsn, generation=GEN):
    def load():
        with psycopg.connect(dsn) as conn:
            return run.load_snapshot(conn, CHART, generation, eligibility())
    return load


def units(files):
    return {u["event_class"] + f"@{u['pair_index']}": u for u in json.loads(files["manifest.json"])["units"]}


def test_lane_rehearsal_reads_the_candidate_generation_and_reproduces(seeded):
    """Item test 1: outputs byte-identical on a second run; the arms come from this generation only."""
    dsn, chapters = seeded
    files = run.produce(loader(dsn), eligibility(), "rehearsal")          # raises unless run 1 == run 2
    other = run.produce(loader(dsn, OTHER), eligibility(), "rehearsal")
    manifest = json.loads(files["manifest.json"])
    assert files["REPRO_DIGEST.json"] and manifest["mode"] == "rehearsal" and manifest["synthetic"] is True
    assert files != other and manifest["source_snapshot_sha256"] != json.loads(other["manifest.json"])["source_snapshot_sha256"]
    ok = [u for u in manifest["units"] if u["status"] == "ok"]
    assert ok, manifest["units"]
    sample = ok[0]
    text = files[f"arms/{sample['unit_id']}/B.txt"].decode()
    assert "g-" in text and "o-vc2" not in text                              # generation 'other' never leaks in
    assert not any(SENTINEL.encode() in data for data in files.values())     # LEL descriptions never read into outputs


def test_segments_are_placed_on_the_pinned_utc_birth_axis(seeded):
    """Axis (ALGO 3.20 d): t is days since the pinned UTC birth; render = birth + t days, independently computed."""
    dsn, chapters = seeded
    snapshot = loader(dsn)()
    seg = snapshot["sources"][CLASSES[0]]["segments"][0]
    first_start = chapters[0][0]
    assert seg["start"] == (BIRTH + timedelta(days=0)).strftime("%Y-%m-%dT%H:%M:%SZ")
    expected_end = BIRTH + timedelta(days=(chapters[0][1] - first_start).days / 6)
    assert seg["end"] == expected_end.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert seg["weakest_link"] in ("clock", "no_window")


def test_stored_synthetic_prior_overrides_a_declaration_of_calibration(seeded):
    """prereg §3: class priors must be non-synthetic; the stored baseline_is_synthetic flag decides."""
    dsn, _ = seeded
    files = run.produce(loader(dsn), eligibility(), "rehearsal")
    by_class = {}
    for u in json.loads(files["manifest.json"])["units"]:
        by_class.setdefault(u["event_class"], set()).add((u["status"], u["reason"]))
    assert by_class[CLASSES[4]] == {("not_evaluable", "class_prior_not_calibrated_or_unprovenanced")}
    assert by_class[CLASSES[5]] == {("not_evaluable", "arm_input_unavailable:sangam,taranga,segments")}
    assert any(s == "budget_overflow:B" or (s and s.startswith("budget_overflow")) for _, s in by_class[CLASSES[3]])
    assert ("ok", None) in by_class[CLASSES[0]]


def test_the_reader_is_read_only_and_chart_scoped(seeded):
    """Job header: lane DB reads only; nothing in the database changes, and no write is possible on the connection."""
    dsn, _ = seeded
    with psycopg.connect(dsn) as conn:
        before = conn.execute("SELECT (SELECT count(*) FROM kala_field_candidate), (SELECT count(*) FROM kala_jury_candidate), "
                              "(SELECT count(*) FROM life_events)").fetchone()
        run.load_snapshot(conn, CHART, GEN, eligibility())
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("DELETE FROM life_events")
        conn.rollback()
        after = conn.execute("SELECT (SELECT count(*) FROM kala_field_candidate), (SELECT count(*) FROM kala_jury_candidate), "
                             "(SELECT count(*) FROM life_events)").fetchone()
    assert before == after
    other = "00000000-0000-0000-0000-0000000000ff"
    with psycopg.connect(dsn) as conn:
        with pytest.raises(run.Refused):
            run.load_snapshot(conn, other, GEN, eligibility())  # no pinned birth axis for a chart with no field snapshot


def test_rehearsal_evidence_is_written_when_requested(seeded):
    """Evidence = identifiers, counts and digests only; never outputs or personal data."""
    dsn, _ = seeded
    files = run.produce(loader(dsn), eligibility(), "rehearsal")
    manifest = json.loads(files["manifest.json"])
    digest = json.loads(files["REPRO_DIGEST.json"])
    evidence = {
        "schema": "ky.vc2_rehearsal_evidence/1", "mode": "rehearsal", "synthetic": True,
        "chart_id_is_canonical": False, "generation": GEN,
        "protocol_sha256": manifest["pins"]["protocol_sha256"], "declaration_sha256": manifest["pins"]["declaration_sha256"],
        "seed": manifest["pins"]["seed"], "renderer_version": manifest["renderer_version"], "prng": manifest["prng"],
        "source_snapshot_sha256": manifest["source_snapshot_sha256"], "source_pins": manifest["source_pins"],
        "eligible_pairs": manifest["selection"]["eligible_count"],
        "selected_pairs": manifest["selection"]["selected_pair_indexes"], "ordinary_threshold": manifest["selection"]["ordinary_threshold"],
        "unit_status_counts": {s: sum(1 for u in manifest["units"] if u["status"] == s) for s in ("ok", "not_evaluable")},
        "unit_reasons": sorted({u["reason"] for u in manifest["units"] if u["reason"]}),
        "max_words_ok_units": {a: max(u["words"][a] for u in manifest["units"] if u["status"] == "ok") for a in core.ARMS},
        "max_words_overflow_units": {a: max(u["words"][a] for u in manifest["units"]
                                            if u["words"] and u["reason"] and u["reason"].startswith("budget")) for a in core.ARMS},
        "file_count": len(digest["files"]), "reproducibility_digest": digest["digest"],
        "order_map_sha256": manifest["order_map_sha256"], "second_run_byte_identical": True,
        "actual_scores": None, "actual_verdict": None,
    }
    target = os.environ.get("VC2_REHEARSAL_EVIDENCE_DIR")
    if target:
        Path(target).mkdir(parents=True, exist_ok=True)
        (Path(target) / "rehearsal_evidence.json").write_text(core.pretty_json(evidence))
    assert evidence["unit_status_counts"]["ok"] > 0 and evidence["unit_status_counts"]["not_evaluable"] > 0


def test_cli_rehearsal_reproduces_and_real_mode_is_refused_without_the_freeze(seeded, tmp_path, capsys, monkeypatch):
    """CLI path: lane-guarded DSN, byte-identical re-run to a second directory, real mode fail-closed (prereg §2).

    The production guard (run.assert_lane_dsn: single-host loopback URI, ky_*/kala_ci_* database) is pinned to
    127.0.0.1:55433 and is tested as such in governance/__tests__/test_vc2_core.py. CI's disposable server is not on
    that port, and a skip here would leave this CLI path with no oracle (§N.8; the Kāla DB job fails on skips), so the
    test points only the two lane constants at the disposable server it was given; every other guard check still runs.
    """
    dsn, _ = seeded
    info = psycopg.conninfo.conninfo_to_dict(dsn)
    monkeypatch.setattr(run, "LANE_HOST", info["host"])
    monkeypatch.setattr(run, "LANE_PORT", int(info["port"]))
    auth = quote(info["user"], safe="") + (":" + quote(info["password"], safe="") if info.get("password") else "")
    uri = f"postgresql://{auth}@{info['host']}:{info['port']}/{info['dbname']}"
    elig = tmp_path / "eligibility.json"
    elig.write_text(json.dumps(eligibility()))
    common = ["--dsn", uri, "--chart", CHART, "--generation", GEN, "--eligibility", str(elig)]
    assert run.main(["--mode", "rehearsal", *common, "--dest", str(tmp_path / "one")]) == 0
    assert run.main(["--mode", "rehearsal", *common, "--dest", str(tmp_path / "two")]) == 0
    one = (tmp_path / "one/REPRO_DIGEST.json").read_bytes()
    assert one == (tmp_path / "two/REPRO_DIGEST.json").read_bytes()
    for rel in json.loads(one)["files"]:
        assert (tmp_path / "one" / rel).read_bytes() == (tmp_path / "two" / rel).read_bytes()
    capsys.readouterr()
    code = run.main(["--mode", "real", *common, "--receipt", str(tmp_path / "no_receipt.json"),
                     "--binding", str(tmp_path / "no_binding.json"), "--dest", str(tmp_path / "three")])
    refusal = json.loads(capsys.readouterr().out)
    assert code == 2 and refusal["status"] == "refused" and not (tmp_path / "three").exists()
    assert {"g1_receipt_absent_or_unreadable", "binding_receipt_absent_or_unreadable",
            "synthetic_chart_refused", "evaluation_eligible_not_true"} <= set(refusal["reasons"])
    target = os.environ.get("VC2_REHEARSAL_EVIDENCE_DIR")
    if target:
        (Path(target) / "real_mode_refusal.json").write_text(core.pretty_json(refusal))
