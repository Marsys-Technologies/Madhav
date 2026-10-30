"""Birth inputs for the calibration timelines.

Source: the people table of the confirmatory sample, read through a column projection. ONLY these columns
are ever extracted: ``confirmatory``, ``stratum``, ``india``, ``born_year``, ``born_time``, ``tz_raw``. No
name, title, place string or event count is read; the row's position in the file is its chart code.

The table carries a birth YEAR but not the day, nor coordinates. The calibration therefore builds SURROGATE
births (``surrogate_births``): the real birth year, time of day and stated UT offset of each confirmatory row,
with a day of the year and a latitude drawn from a seeded generator, and longitude from the UT offset. Every
timeline built from them is labelled ``surrogate`` in its metadata. A file of real birth data (code, date,
time, offset, lat, lon) replaces them through ``births_from_file`` with no other change.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from ..engine.birthrecord import ChartRefused, record_fields_from_adb_tz_raw

ALLOWED_COLUMNS = ("confirmatory", "stratum", "india", "born_year", "born_time", "tz_raw")


@dataclass(frozen=True)
class BirthRow:
    code: str  # "r<row index>": a row index, never a name
    local_date: date
    local_time: str  # HH:MM
    lat: float
    lon: float
    utc_offset_minutes: int
    india: bool
    surrogate: bool


def read_permitted_columns(path: str) -> List[Dict[str, str]]:
    """Rows as dicts of ONLY the allowed columns; every other field is dropped as the row is read."""
    out: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        header = next(rd)
        idx = {c: header.index(c) for c in ALLOWED_COLUMNS}
        for i, row in enumerate(rd):
            rec = {c: row[j] for c, j in idx.items()}
            rec["_row"] = str(i)
            out.append(rec)
    return out


_H_OFFSET = re.compile(r"\bh(\d{1,2})([ew])(\d{1,2})?\b")


def _offset_fields(tz_raw: str) -> Optional[Dict[str, Any]]:
    """The engine's parser first; for a numeric zone code (``-05 h5w``) the same ``h<H>(e|w)[<MM>]`` rule."""
    try:
        return record_fields_from_adb_tz_raw(tz_raw)
    except ChartRefused:
        m = _H_OFFSET.search(tz_raw or "")
        if not m:
            return None
        mins = (int(m.group(1)) * 60 + int(m.group(3) or 0)) * (1 if m.group(2) == "e" else -1)
        return {"utc_offset_minutes": mins}


def _clock(text: str) -> Optional[str]:
    t = (text or "").strip()
    parts = t.split(":")
    if len(parts) < 2 or not all(p.isdigit() for p in parts[:2]):
        return None
    return "%02d:%02d" % (int(parts[0]), int(parts[1]))


def surrogate_births(rows: Sequence[Dict[str, str]], seed: int = 20261030) -> List[BirthRow]:
    """Confirmatory rows -> surrogate births (see module text). Deterministic in (rows, seed)."""
    out: List[BirthRow] = []
    for rec in rows:
        if rec["confirmatory"] != "Y":
            continue
        t = _clock(rec["born_time"])
        if t is None:
            continue
        fields = _offset_fields(rec["tz_raw"])
        if fields is None:
            continue
        rng = np.random.default_rng([seed, int(rec["_row"])])
        year = int(rec["born_year"])
        d0 = date(year, 1, 1)
        local_date = d0 + timedelta(days=int(rng.integers(0, 365)))
        india = rec["india"] == "True"
        lat = float(rng.uniform(12.0, 30.0)) if india else float(rng.uniform(20.0, 58.0))
        off = int(fields["utc_offset_minutes"])
        lon = max(-179.0, min(179.0, off / 4.0 + float(rng.uniform(-7.0, 7.0))))
        out.append(BirthRow("r%03d" % int(rec["_row"]), local_date, t, lat, lon, off, india, True))
    return out


def births_from_file(path: str) -> List[BirthRow]:
    """Real births: a JSON list of {code, local_date, local_time, lat, lon, utc_offset_minutes, india}."""
    rows = json.loads(open(path, "r", encoding="utf-8").read())
    return [
        BirthRow(r["code"], date.fromisoformat(r["local_date"]), r["local_time"], float(r["lat"]), float(r["lon"]), int(r["utc_offset_minutes"]), bool(r.get("india", False)), False)
        for r in rows
    ]


def births_sha256(births: Sequence[BirthRow]) -> str:
    """Hash of the birth list (kept local; only the hash and counts leave this machine)."""
    h = hashlib.sha256()
    for b in births:
        h.update(json.dumps([b.code, b.local_date.isoformat(), b.local_time, round(b.lat, 4), round(b.lon, 4), b.utc_offset_minutes, b.india, b.surrogate]).encode() + b"\n")
    return h.hexdigest()
