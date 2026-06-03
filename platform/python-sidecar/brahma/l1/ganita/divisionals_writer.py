"""
divisionals_writer.py — Brahma GA-1-3: ganita.divisionals writer

Reads typed JSONL from the ganita.engine (GA-1-1) output and writes all
varga (divisional chart) positions to the chart_divisionals table.

Supported vargas: D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27,
                  D30, D40, D45, D60   (the canonical 16-varga set).

Tool exposed: query_divisional(chart_id, varga, ayanamsha)
Table:        chart_divisionals (chart_id, graha, ayanamsha_id, varga, sign,
                                  sign_number, degree_in_sign, house, vargottama,
                                  source_citation, build_id)

FORENSIC benchmark (Lahiri, native 1984-02-05 10:43 IST Bhubaneswar):
  Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §2.1, §3.5, §3.6 (authoritative)
  D1: Lagna=Aries (12°23′), Sun=Capricorn (21°57′), Moon=Aquarius (27°02′),
      Mars=Libra, Mercury=Capricorn, Jupiter=Sagittarius, Venus=Sagittarius,
      Saturn=Libra (exalted), Rahu=Taurus, Ketu=Scorpio
  D9: Lagna=Cancer, Sun=Cancer, Moon=Gemini, Mercury=Capricorn (vargottama=YES),
      Mars=Pisces, Jupiter=Gemini, Venus=Virgo, Saturn=Aries, Rahu=Gemini,
      Ketu=Sagittarius
  D10: Lagna=Leo, Sun=Aries
  Vimshottari MD at birth: Venus (Shukra) mahadasha (1982–2002)

Commit tag: BRAHMA-GA-1-3
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator

# ─── Canonical constants ───────────────────────────────────────────────────────

ASSET_ID = "ganita.divisionals"
ASSET_TAG = "BRAHMA-GA-1-3"
SOURCE_CITATION = "PyJHora DE441 / MARSYS-engine v1"
ENGINE_VERSION = "v1"

# Canonical varga catalog: divisional factor → label
VARGA_CATALOG: dict[int, str] = {
    1:  "D1",
    2:  "D2",
    3:  "D3",
    4:  "D4",
    7:  "D7",
    9:  "D9",
    10: "D10",
    12: "D12",
    16: "D16",
    20: "D20",
    24: "D24",
    27: "D27",
    30: "D30",
    40: "D40",
    45: "D45",
    60: "D60",
}
VARGA_FACTORS: list[int] = sorted(VARGA_CATALOG.keys())
VARGA_LABELS: set[str] = set(VARGA_CATALOG.values())

# Sign names (0-based index → name, jhora convention)
SIGNS: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Graha index → canonical name (jhora convention: 0=Sun…8=Ketu, 'L'=Lagna)
GRAHA_MAP: dict[Any, str] = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
    4: "Jupiter", 5: "Venus", 6: "Saturn",
    7: "Rahu", 8: "Ketu", "L": "Lagna",
}

# Ayanamsha ID → jhora mode string
AYANAMSHA_MAP: dict[str, str] = {
    "lahiri":      "LAHIRI",
    "kp":          "KP",
    "raman":       "RAMAN",
    "true_pushya": "TRUE_PUSHYA",
    "tropical":    "FAGAN",   # tropical uses Fagan–Bradley (offset ~0)
}

# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DivisionalRow:
    """One graha's position in one varga under one ayanamsha."""
    chart_id: str
    graha: str
    ayanamsha_id: str
    varga: str
    sign: str
    sign_number: int          # 1-based
    degree_in_sign: float
    house: int | None         # 1-based from divisional lagna; None until lagna known
    vargottama: bool | None   # D9 only
    source_citation: str
    build_id: str

# ─── Engine JSONL helpers ──────────────────────────────────────────────────────

def iter_engine_jsonl(path: str) -> Iterator[dict]:
    """Yield each JSON object from the engine JSONL file."""
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_vargas_from_engine(record: dict) -> list[dict]:
    """
    Extract the 'vargas' block from a ganita.engine JSONL record.

    The engine record shape (per GA-1-1 contract):
      {
        "vargas": [
          {"varga": "D1", "positions": [["L", [sign_idx_0based, deg]], [0, [...]], ...]},
          {"varga": "D9", "positions": [...]}
          ...
        ],
        "ayanamsha": {"id": "lahiri", ...},
        "chart_id": "...",
        ...
      }

    Falls back to computing from raw positions if 'vargas' block absent (e.g.
    when called from a partial engine record that only has graha positions).
    """
    return record.get("vargas", [])


# ─── Core computation ─────────────────────────────────────────────────────────

def _import_jhora():
    """Lazy import of jhora (avoids Qt initialization at module load time)."""
    import os as _os
    _os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from jhora import utils as _utils
    from jhora.panchanga import drik as _drik
    from jhora.horoscope.chart import charts as _charts
    return _utils, _drik, _charts


def compute_vargas_for_native(
    *,
    birth_datetime_iso: str,
    tz_offset_hours: float,
    latitude_deg: float,
    longitude_deg: float,
    ayanamsha_id: str,
) -> dict[str, list[tuple[str, int, float]]]:
    """
    Compute all 16 vargas using PyJHora for a given birth instant and ayanamsha.

    Returns:
        {
          "D1": [("Lagna", sign_number_1based, deg_in_sign), ("Sun", ...), ...],
          "D9": [...],
          ...
        }
    """
    utils, drik, charts = _import_jhora()

    # Parse datetime
    from datetime import datetime as _dt
    dt = _dt.fromisoformat(birth_datetime_iso)

    # Julian day from local wall-clock
    jd = utils.julian_day_number(
        (dt.year, dt.month, dt.day),
        (dt.hour, dt.minute, dt.second),
    )

    # Set ayanamsha
    jhora_mode = AYANAMSHA_MAP.get(ayanamsha_id, "LAHIRI")
    drik.set_ayanamsa_mode(jhora_mode)

    place = drik.Place("birth_place", latitude_deg, longitude_deg, tz_offset_hours)

    result: dict[str, list[tuple[str, int, float]]] = {}
    for factor, varga_label in VARGA_CATALOG.items():
        raw = charts.divisional_chart(jd, place, divisional_chart_factor=factor)
        # raw: [['L', (sign_0based, deg)] | [int, (sign_0based, deg)], ...]
        positions: list[tuple[str, int, float]] = []
        for entry in raw:
            body_key, pos = entry
            sign_0based = int(pos[0])
            deg = float(pos[1])
            graha_name = GRAHA_MAP.get(body_key, str(body_key))
            sign_name = SIGNS[sign_0based]
            sign_number = sign_0based + 1  # 1-based
            positions.append((graha_name, sign_number, deg))
        result[varga_label] = positions

    return result


def compute_house_from_lagna(graha_sign_number: int, lagna_sign_number: int) -> int:
    """House number (1-based) of a graha relative to divisional lagna."""
    return ((graha_sign_number - lagna_sign_number) % 12) + 1


def compute_vargottama(
    d1_positions: list[tuple[str, int, float]],
    d9_positions: list[tuple[str, int, float]],
) -> dict[str, bool]:
    """
    Compute vargottama flag for each graha (same sign in D1 and D9).
    Returns dict: {graha_name: is_vargottama}
    """
    d1_signs = {g: sn for g, sn, _ in d1_positions}
    d9_signs = {g: sn for g, sn, _ in d9_positions}
    result = {}
    for graha in d1_signs:
        if graha == "Lagna":
            continue  # Lagna vargottama is a separate concept; skip
        result[graha] = d1_signs.get(graha) == d9_signs.get(graha)
    return result


# ─── Writer ───────────────────────────────────────────────────────────────────

def build_divisional_rows(
    *,
    chart_id: str,
    birth_datetime_iso: str,
    tz_offset_hours: float,
    latitude_deg: float,
    longitude_deg: float,
    ayanamsha_id: str,
    build_id: str,
) -> list[DivisionalRow]:
    """
    Compute all divisional positions and return as DivisionalRow objects.
    Called by the bootstrap writer or the on-demand build trigger.
    """
    vargas = compute_vargas_for_native(
        birth_datetime_iso=birth_datetime_iso,
        tz_offset_hours=tz_offset_hours,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        ayanamsha_id=ayanamsha_id,
    )

    # Pre-compute vargottama from D1 vs D9
    d1_pos = vargas.get("D1", [])
    d9_pos = vargas.get("D9", [])
    vargottama_map = compute_vargottama(d1_pos, d9_pos)

    rows: list[DivisionalRow] = []
    for varga_label, positions in vargas.items():
        # Find Lagna sign for house calculation
        lagna_sign: int | None = next(
            (sn for g, sn, _ in positions if g == "Lagna"), None
        )

        for graha, sign_number, degree_in_sign in positions:
            # House from divisional lagna
            house: int | None = None
            if lagna_sign is not None and graha != "Lagna":
                house = compute_house_from_lagna(sign_number, lagna_sign)

            # Vargottama: only meaningful for D9
            vargottama: bool | None = None
            if varga_label == "D9" and graha != "Lagna":
                vargottama = vargottama_map.get(graha)

            rows.append(DivisionalRow(
                chart_id=chart_id,
                graha=graha,
                ayanamsha_id=ayanamsha_id,
                varga=varga_label,
                sign=SIGNS[sign_number - 1],
                sign_number=sign_number,
                degree_in_sign=round(degree_in_sign, 4),
                house=house,
                vargottama=vargottama,
                source_citation=SOURCE_CITATION,
                build_id=build_id,
            ))

    return rows


def build_divisional_rows_from_engine_jsonl(
    jsonl_path: str,
    build_id: str,
    ayanamsha_ids: list[str] | None = None,
) -> list[DivisionalRow]:
    """
    Read ganita.engine JSONL file and produce DivisionalRow objects for all
    charts × ayanamshas present in the file.

    The engine JSONL may contain pre-computed vargas (preferred) or only raw
    inputs (fallback: recompute from birth data).
    """
    if ayanamsha_ids is None:
        ayanamsha_ids = list(AYANAMSHA_MAP.keys())

    all_rows: list[DivisionalRow] = []
    for record in iter_engine_jsonl(jsonl_path):
        chart_id = record.get("chart_id", "unknown")
        inputs = record.get("inputs", {})
        birth_dt = inputs.get("datetime_iso", record.get("datetime_iso", ""))
        tz = inputs.get("tz_offset_hours", record.get("tz_offset_hours", 5.5))
        lat = inputs.get("latitude_deg", record.get("latitude_deg", 0.0))
        lon = inputs.get("longitude_deg", record.get("longitude_deg", 0.0))

        # If the engine already computed vargas, use them; else recompute.
        pre_computed_vargas = extract_vargas_from_engine(record)
        record_ayanamsha = record.get("ayanamsha", {}).get("id", "lahiri")

        if pre_computed_vargas:
            # Use engine-provided data (already under the engine's ayanamsha)
            rows = _rows_from_precomputed(
                chart_id=chart_id,
                pre_computed=pre_computed_vargas,
                ayanamsha_id=record_ayanamsha,
                d1_source=record,
                build_id=build_id,
            )
            all_rows.extend(rows)
        else:
            # Recompute for each requested ayanamsha
            for ayan in ayanamsha_ids:
                rows = build_divisional_rows(
                    chart_id=chart_id,
                    birth_datetime_iso=birth_dt,
                    tz_offset_hours=tz,
                    latitude_deg=lat,
                    longitude_deg=lon,
                    ayanamsha_id=ayan,
                    build_id=build_id,
                )
                all_rows.extend(rows)

    return all_rows


def _rows_from_precomputed(
    *,
    chart_id: str,
    pre_computed: list[dict],
    ayanamsha_id: str,
    d1_source: dict,
    build_id: str,
) -> list[DivisionalRow]:
    """Convert engine-provided varga data to DivisionalRow objects."""
    # Parse D1 positions for vargottama computation
    d1_pos: list[tuple[str, int, float]] = []
    d9_pos: list[tuple[str, int, float]] = []
    for block in pre_computed:
        label = block.get("varga", "")
        positions = block.get("positions", [])
        parsed = []
        for entry in positions:
            body_key = entry[0]
            pos = entry[1]
            graha = GRAHA_MAP.get(body_key, str(body_key))
            sign_0based = int(pos[0])
            deg = float(pos[1])
            parsed.append((graha, sign_0based + 1, deg))
        if label == "D1":
            d1_pos = parsed
        elif label == "D9":
            d9_pos = parsed

    vargottama_map = compute_vargottama(d1_pos, d9_pos)

    rows: list[DivisionalRow] = []
    for block in pre_computed:
        label = block.get("varga", "")
        if label not in VARGA_LABELS:
            continue
        positions = block.get("positions", [])
        parsed = []
        for entry in positions:
            body_key = entry[0]
            pos = entry[1]
            graha = GRAHA_MAP.get(body_key, str(body_key))
            sign_0based = int(pos[0])
            deg = float(pos[1])
            parsed.append((graha, sign_0based + 1, deg))

        lagna_sign = next((sn for g, sn, _ in parsed if g == "Lagna"), None)
        for graha, sign_number, degree_in_sign in parsed:
            house = None
            if lagna_sign is not None and graha != "Lagna":
                house = compute_house_from_lagna(sign_number, lagna_sign)
            vargottama = None
            if label == "D9" and graha != "Lagna":
                vargottama = vargottama_map.get(graha)
            rows.append(DivisionalRow(
                chart_id=chart_id,
                graha=graha,
                ayanamsha_id=ayanamsha_id,
                varga=label,
                sign=SIGNS[sign_number - 1],
                sign_number=sign_number,
                degree_in_sign=round(degree_in_sign, 4),
                house=house,
                vargottama=vargottama,
                source_citation=SOURCE_CITATION,
                build_id=build_id,
            ))

    return rows


# ─── DB writer ────────────────────────────────────────────────────────────────

INSERT_SQL = """
INSERT INTO public.chart_divisionals
  (chart_id, graha, ayanamsha_id, varga, sign, sign_number,
   degree_in_sign, house, vargottama, source_citation, build_id)
VALUES
  (%(chart_id)s, %(graha)s, %(ayanamsha_id)s, %(varga)s, %(sign)s, %(sign_number)s,
   %(degree_in_sign)s, %(house)s, %(vargottama)s, %(source_citation)s, %(build_id)s)
ON CONFLICT (chart_id, graha, ayanamsha_id, varga) DO UPDATE SET
  sign           = EXCLUDED.sign,
  sign_number    = EXCLUDED.sign_number,
  degree_in_sign = EXCLUDED.degree_in_sign,
  house          = EXCLUDED.house,
  vargottama     = EXCLUDED.vargottama,
  source_citation= EXCLUDED.source_citation,
  build_id       = EXCLUDED.build_id,
  created_at     = NOW()
"""


def write_rows_to_db(rows: list[DivisionalRow], db_conn) -> int:
    """
    Upsert DivisionalRow objects into chart_divisionals.
    Returns number of rows written.
    """
    if not rows:
        return 0
    with db_conn.cursor() as cur:
        for row in rows:
            cur.execute(INSERT_SQL, {
                "chart_id": row.chart_id,
                "graha": row.graha,
                "ayanamsha_id": row.ayanamsha_id,
                "varga": row.varga,
                "sign": row.sign,
                "sign_number": row.sign_number,
                "degree_in_sign": row.degree_in_sign,
                "house": row.house,
                "vargottama": row.vargottama,
                "source_citation": row.source_citation,
                "build_id": row.build_id,
            })
    db_conn.commit()
    return len(rows)


# ─── Query tool ───────────────────────────────────────────────────────────────

def query_divisional(
    *,
    db_conn,
    chart_id: str,
    varga: str,
    ayanamsha_id: str = "lahiri",
    graha: str | None = None,
) -> dict:
    """
    query_divisional — retrieve divisional chart positions.

    Args:
        db_conn:      psycopg connection
        chart_id:     chart UUID
        varga:        'D1' | 'D2' | ... | 'D60'
        ayanamsha_id: 'lahiri' | 'kp' | 'raman' | 'true_pushya' | 'tropical'
        graha:        optional filter (e.g. 'Sun') — returns all if None

    Returns:
        dict with keys:
          provenance_envelope: {source, engine_version, computed_at}
          rows: list of dicts with keys:
            graha, sign, sign_number, degree_in_sign, house, vargottama,
            ayanamsha_id, varga, source_citation, build_id
    """
    if varga not in VARGA_LABELS:
        raise ValueError(
            f"Unknown varga '{varga}'. Supported: {sorted(VARGA_LABELS)}"
        )
    sql = """
        SELECT
          graha, sign, sign_number, degree_in_sign, house, vargottama,
          ayanamsha_id, varga, source_citation, build_id
        FROM public.chart_divisionals
        WHERE chart_id = %(chart_id)s
          AND ayanamsha_id = %(ayanamsha_id)s
          AND varga = %(varga)s
    """
    params: dict = {
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "varga": varga,
    }
    if graha is not None:
        sql += " AND graha = %(graha)s"
        params["graha"] = graha
    sql += " ORDER BY sign_number, degree_in_sign"

    with db_conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {
        "provenance_envelope": {
            "source": SOURCE_CITATION,
            "engine_version": ENGINE_VERSION,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
        "rows": rows,
    }


# ─── Bootstrap entrypoint ─────────────────────────────────────────────────────

def bootstrap_native_chart(
    *,
    chart_id: str,
    build_id: str | None = None,
    ayanamsha_ids: list[str] | None = None,
    db_conn=None,
) -> list[DivisionalRow]:
    """
    Bootstrap the native chart (Abhisek Mohanty, 1984-02-05 10:43 IST Bhubaneswar)
    for all requested ayanamshas. If db_conn provided, writes to DB immediately.

    This is the FORENSIC-grounded bootstrap for acceptance gate verification.
    """
    if build_id is None:
        build_id = f"ganita-divisionals-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    if ayanamsha_ids is None:
        ayanamsha_ids = ["lahiri"]

    all_rows: list[DivisionalRow] = []
    for ayan in ayanamsha_ids:
        rows = build_divisional_rows(
            chart_id=chart_id,
            birth_datetime_iso="1984-02-05T10:43:00",
            tz_offset_hours=5.5,
            latitude_deg=20.2961,
            longitude_deg=85.8245,
            ayanamsha_id=ayan,
            build_id=build_id,
        )
        all_rows.extend(rows)

    if db_conn is not None:
        write_rows_to_db(all_rows, db_conn)

    return all_rows
