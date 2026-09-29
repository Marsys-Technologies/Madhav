"""§12.4 — KALA_SYNERGY_BINDING v2.3 conformance detectors (B1–B7).

Adopted by reference in GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §1; the proof
matrix is wp7_packets/BINDING_PROOF_MATRIX_v1_0.md. Each detector here pairs a
positive assertion on the real tree with a NEGATIVE fixture that makes the
detector fire (Layer contract §9; binding §B7).

Covered in this file (the rest are covered by existing tests named in the
matrix):

  * B1 / Layer test 7 (boundary/timezone): naive instants rejected at write;
    a tz-aware non-UTC instant round-trips as the same UTC instant.
  * B6 (single producer, DECISION B8-6 adopted as written by §12.4): a static
    detector fails if any writer other than gochara_kernel/ledger.py emits
    INSERT INTO kala_gochara_contacts.
  * B1 resolver row (no private date↔instant conversion): a static detector
    fails on date.today() / naive now() / utcnow() in the Gochara services.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SIDECAR_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SIDECAR_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ledger.py loaded by file path, same discipline as test_wp6_ledger.py.
_LEDGER_PATH = SIDECAR_ROOT / "services/gochara_kernel/ledger.py"
_spec = importlib.util.spec_from_file_location("b_binding_ledger_under_test",
                                               _LEDGER_PATH)
ledger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ledger)

from test_wp6_ledger import (  # noqa: E402
    CONVENTION_VECTOR,
    EPHEM_BACKEND_JSON,
    PROBE,
    SE1_CHECKSUMS,
    make_episode,
    setup_candidate,
    synth,
)

UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))  # synthetic tz edge fixture


# ── B1 / Layer test 7: naive instant rejected at write ───────────────────────


def test_naive_instant_rejected_at_write():
    """B1 failure mode: 'a row with a naive instant is rejected at write'.

    Negative fixture: t_exact as a naive datetime must raise before any row
    reaches the database.
    """
    ep = make_episode(t_exact=datetime(2021, 6, 15, 12, 0, 0))  # naive
    with pytest.raises(ValueError, match="naive"):
        ledger._normalize_episode(ep, synth(80), "4.0", "conv-x", "1.0.0",
                                  manifest_id=None, build_id="b-naive")


def test_naive_t_in_t_out_rejected_at_write():
    for key in ("t_in", "t_out"):
        ep = make_episode()
        ep[key] = datetime(2021, 6, 15, 10, 0, 0)  # naive
        with pytest.raises(ValueError, match="naive"):
            ledger._normalize_episode(ep, synth(81), "4.0", "conv-x", "1.0.0",
                                      manifest_id=None, build_id="b-naive")


def test_tz_aware_non_utc_round_trips_as_same_utc_instant(conn):
    """Boundary/timezone control: an episode whose t_* are tz-aware at +05:30
    (a chart tz differing from the run tz, per B1's proof note) writes and
    reads back as the SAME UTC instant — never reinterpreted, never shifted.
    """
    chart = synth(82)
    cid, _, _ = setup_candidate(conn, chart)
    t_exact_ist = datetime(2021, 6, 15, 17, 30, 0, tzinfo=IST)
    ep = make_episode(t_exact=t_exact_ist)
    ep["t_in"] = t_exact_ist - timedelta(hours=2)
    ep["t_out"] = t_exact_ist + timedelta(hours=2)
    ledger.write_contacts(conn, chart, "4.0", cid, [ep], build_id="b-tz")
    row = conn.execute(
        "SELECT t_in, t_exact, t_out FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = '4.0'",
        (chart,),
    ).fetchone()
    expected = t_exact_ist.astimezone(UTC)
    assert row[1] == expected
    assert row[0] == expected - timedelta(hours=2)
    assert row[2] == expected + timedelta(hours=2)


# ── B6: single producer of contact episodes ──────────────────────────────────

_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+(?:\w+\.)?kala_gochara_contacts", re.IGNORECASE
)
# The sole writers the binding (B6, adopted as written by §12.4) permits.
_ALLOWED_CONTACT_WRITERS = {
    "services/gochara_kernel/ledger.py",
}


def find_contact_writers(root: Path) -> list[str]:
    """Return repo-relative .py paths that INSERT into kala_gochara_contacts
    outside the allowed sole-producer set. Empty list = conformant."""
    offenders = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if "/tests/" in f"/{rel}" or rel.startswith("tests/"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _INSERT_RE.search(text) and rel not in _ALLOWED_CONTACT_WRITERS:
            offenders.append(rel)
    return offenders


def test_b6_sole_producer_real_tree():
    offenders = find_contact_writers(SIDECAR_ROOT)
    assert offenders == [], (
        "B6 violated: contact-episode writers outside the sole producer: "
        f"{offenders}"
    )


def test_b6_detector_fires_on_second_writer(tmp_path):
    """Negative fixture: a fabricated second writer must make the detector fire."""
    (tmp_path / "services/gochara_kernel").mkdir(parents=True)
    (tmp_path / "services/gochara_kernel/ledger.py").write_text(
        'sql = "INSERT INTO kala_gochara_contacts (x) VALUES (1)"\n'
    )
    (tmp_path / "services/other_writer").mkdir(parents=True)
    (tmp_path / "services/other_writer/writer.py").write_text(
        'sql = "insert into kala_gochara_contacts (x) values (1)"\n'
    )
    offenders = find_contact_writers(tmp_path)
    assert offenders == ["services/other_writer/writer.py"]


# ── B1 resolver row: no private date↔instant conversion ─────────────────────
# Gochara's kernel works in JD/UTC end-to-end (revjul/fromtimestamp(tz=utc)
# only); there is no civil date↔instant conversion to route through
# ka_temporal/date_resolver (which in its current form resolves dasha
# activation dates, not instants). The binding's failure mode for this row is
# a PRIVATE conversion creeping in; these detectors make that fail loudly.

_FORBIDDEN_TEMPORAL_PATTERNS = {
    "date.today()": re.compile(r"\bdate\.today\("),
    "datetime.utcnow()": re.compile(r"\bdatetime\.utcnow\("),
    "naive datetime.now()": re.compile(r"\bdatetime\.now\(\s*\)"),
}
_GOCHARA_SERVICE_DIRS = [
    "services/gochara_kernel",
    "services/ka_gochara",
    "services/gochara_v3",
]


def find_private_temporal_conversions(root: Path) -> list[str]:
    offenders = []
    for rel_dir in _GOCHARA_SERVICE_DIRS:
        base = root / rel_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = path.relative_to(root).as_posix()
            if "/tests/" in f"/{rel}":
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for name, pat in _FORBIDDEN_TEMPORAL_PATTERNS.items():
                if pat.search(text):
                    offenders.append(f"{rel}: {name}")
    return offenders


def test_b1_no_private_temporal_conversion_real_tree():
    offenders = find_private_temporal_conversions(SIDECAR_ROOT)
    assert offenders == [], (
        "B1 tz-source/resolver rule violated — private temporal conversion: "
        f"{offenders}"
    )


def test_b1_private_conversion_detector_fires(tmp_path):
    """Negative fixture: a fabricated date.today() caller must fire."""
    d = tmp_path / "services/ka_gochara"
    d.mkdir(parents=True)
    (d / "bad.py").write_text(
        "from datetime import date\n_today = date.today()\n"
    )
    offenders = find_private_temporal_conversions(tmp_path)
    assert offenders == ["services/ka_gochara/bad.py: date.today()"]
