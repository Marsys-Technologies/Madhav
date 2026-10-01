"""Pravāha B6.0 PART 0 — pure tests for resonance_restore_from_file.py
(native decision 2026-10-01: certified FILE backup, steward
M20261001T125637-9b2b).

No DB here: the file-side refuse-unless-verified controls (sha256, count,
joined-md5, chart uniformity, JSON shape, id uniqueness, recorded-pair
sanity) and the runbook drift guard (the file-mode variant quotes the
script's usage verbatim and records the steward's certified pair). The
live disposable run is resonance_restore_from_file_rehearsal.py (exit 1 on
any failure) — success + the five refusals on the migration-derived schema.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "kala_gochara_cutover"
sys.path.insert(0, str(HERE))

import resonance_restore_from_file as RESTORE  # noqa: E402

CH = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "00000000-0000-4000-8000-0000000000aa"


def _lines(n: int, chart: str = CH) -> list[str]:
    out = []
    for i in range(1, n + 1):
        out.append(json.dumps({
            "id": i, "chart_id": chart, "event_class": "marriage", "target_type": "bhava",
            "target_ref": str(i), "weight": 1, "classical_citation": f"citation {i}",
            "uncited_extension": False, "source_rule_id": None,
            "computed_at": "2026-09-07T21:08:11.192812+00:00",
            "target_resolution_state": "resolved", "target_qualifier": None}))
    return out


def _write(tmp_path: Path, lines: list[str], name: str = "backup.jsonl",
           sha: str | None = None) -> Path:
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    p = tmp_path / name
    p.write_bytes(payload)
    token = sha if sha is not None else hashlib.sha256(payload).hexdigest()
    (tmp_path / (name + ".sha256")).write_text(f"{token}  {name}\n", encoding="utf-8")
    return p


def _pair(lines: list[str]) -> tuple[int, str]:
    return len(lines), hashlib.md5("\n".join(lines).encode("utf-8")).hexdigest()


def test_honest_backup_verifies(tmp_path):
    lines = _lines(7)
    p = _write(tmp_path, lines)
    n, d = _pair(lines)
    assert RESTORE.load_and_verify_file(str(p), CH, n, d) == lines


def test_sha_mismatch_refused(tmp_path):
    lines = _lines(7)
    p = _write(tmp_path, lines, sha="0" * 64)
    n, d = _pair(lines)
    with pytest.raises(RESTORE.Refusal, match="sha256"):
        RESTORE.load_and_verify_file(str(p), CH, n, d)


def test_tampered_file_refused(tmp_path):
    lines = _lines(7)
    p = _write(tmp_path, lines)
    raw = bytearray(p.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    p.write_bytes(bytes(raw))
    n, d = _pair(lines)
    with pytest.raises(RESTORE.Refusal, match="sha256"):
        RESTORE.load_and_verify_file(str(p), CH, n, d)


def test_truncated_file_refused(tmp_path):
    lines = _lines(7)
    p = _write(tmp_path, lines[:-2])
    n, d = _pair(lines)
    with pytest.raises(RESTORE.Refusal, match="rows"):
        RESTORE.load_and_verify_file(str(p), CH, n, d)


def test_joined_md5_mismatch_refused(tmp_path):
    lines = _lines(7)
    p = _write(tmp_path, lines)
    with pytest.raises(RESTORE.Refusal, match="joined-md5"):
        RESTORE.load_and_verify_file(str(p), CH, len(lines), "0" * 32)


def test_foreign_row_refused_even_with_recomputed_pair(tmp_path):
    lines = _lines(7)
    row = json.loads(lines[3])
    row["chart_id"] = OTHER
    lines[3] = json.dumps(row)
    p = _write(tmp_path, lines)
    n, d = _pair(lines)
    with pytest.raises(RESTORE.Refusal, match="foreign row"):
        RESTORE.load_and_verify_file(str(p), CH, n, d)


def test_non_json_line_refused(tmp_path):
    lines = _lines(7)
    lines[2] = "{not json"
    p = _write(tmp_path, lines)
    n, d = _pair(lines)
    with pytest.raises(RESTORE.Refusal, match="not JSON"):
        RESTORE.load_and_verify_file(str(p), CH, n, d)


def test_duplicate_id_refused(tmp_path):
    lines = _lines(7)
    row = json.loads(lines[6])
    row["id"] = 1
    lines[6] = json.dumps(row)
    p = _write(tmp_path, lines)
    n, d = _pair(lines)
    with pytest.raises(RESTORE.Refusal, match="twice"):
        RESTORE.load_and_verify_file(str(p), CH, n, d)


def test_blank_line_refused(tmp_path):
    lines = _lines(7)
    payload = ("\n".join(lines[:3]) + "\n\n" + "\n".join(lines[3:]) + "\n").encode("utf-8")
    p = tmp_path / "blank.jsonl"
    p.write_bytes(payload)
    (tmp_path / "blank.jsonl.sha256").write_text(
        hashlib.sha256(payload).hexdigest() + "  blank.jsonl\n", encoding="utf-8")
    n, d = len(lines), hashlib.md5("\n".join(lines).encode("utf-8")).hexdigest()
    with pytest.raises(RESTORE.Refusal, match="blank line"):
        RESTORE.load_and_verify_file(str(p), CH, n, d)


def test_recorded_pair_sanity():
    with pytest.raises(RESTORE.Refusal, match="positive"):
        RESTORE._check_recorded_pair(0, "a" * 32)
    with pytest.raises(RESTORE.Refusal, match="md5 hex"):
        RESTORE._check_recorded_pair(10, "not-md5")
    with pytest.raises(RESTORE.Refusal, match="md5 hex"):
        RESTORE._check_recorded_pair(10, "empty")
    assert RESTORE._check_recorded_pair(10, "b" * 32) == (10, "b" * 32)


def test_chart_uuid_validated():
    with pytest.raises(RESTORE.Refusal, match="not a chart uuid"):
        RESTORE._check_chart("482012F1-not-a-uuid")
    assert RESTORE._check_chart(CH.upper()) == CH


def test_sidecar_format_and_errors(tmp_path):
    lines = _lines(3)
    p = _write(tmp_path, lines)
    assert RESTORE.read_sha256_sidecar(str(p)) == hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(RESTORE.Refusal, match="cannot read"):
        RESTORE.read_sha256_sidecar(str(tmp_path / "absent.jsonl"))
    bad = tmp_path / "bad.jsonl"
    bad.write_text("x\n")
    (tmp_path / "bad.jsonl.sha256").write_text("not-a-sha\n", encoding="utf-8")
    with pytest.raises(RESTORE.Refusal, match="sha256 hex"):
        RESTORE.read_sha256_sidecar(str(bad))


def test_restore_certificate_sql_is_the_runbooks():
    """The live-side certificate IS the runbook §1 statement (same
    serialisation, same order) — file and database stay comparable."""
    import resonance_rebuild_backup_sql as B
    expected = B.full_row_digest_sql("gochara_resonance_map", CH)
    for fragment in ("row_to_json(t)::text", "ORDER BY t.id", "gochara_resonance_map"):
        assert fragment in RESTORE.FULL_ROW_CERTIFICATE_SQL
        assert fragment in expected


def test_runbook_carries_the_file_mode_variant_verbatim():
    """Drift guard: the production runbook's file-mode §1/§4 variant quotes
    this script's usage verbatim and records the steward's certified pair."""
    text = (HERE / "resonance_rebuild_R1_R6_runbook.md").read_text()
    assert RESTORE.RUNBOOK_USAGE in text
    assert "resonance_restore_from_file.py" in text
    assert "RESONANCE_RESTORE_DATABASE_URL" in text
    assert "765" in text and "3d270ef0a2db00b240a2acb4d45171c0" in text


def test_steward_certified_backup_verifies():
    """The steward's real certified backup (read-only) verifies against the
    recorded production pair."""
    steward = Path("/Users/Dev/pravaha/run/backups/gochara_resonance_map_482012f1_20261001071822.jsonl")
    if not steward.exists():
        pytest.skip("steward backup not present on this host")
    lines = RESTORE.load_and_verify_file(str(steward), CH, 765, "3d270ef0a2db00b240a2acb4d45171c0")
    assert len(lines) == 765
