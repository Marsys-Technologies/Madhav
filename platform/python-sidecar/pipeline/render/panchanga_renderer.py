"""
panchanga_renderer.py — Full birth-day Panchanga renderer for FORENSIC.md (F-08).

Covers:
  1. Five Limbs (Pancha Anga) — Tithi, Vara, Nakshatra, Yoga, Karana
  2. Astronomical Windows — Sunrise, Sunset, Brahma Muhurta, Abhijit Muhurta,
     Rahu Kalam, Gulika Kalam, Yamaganda
  3. Choghadiya — 8 day segments + 8 night segments
  4. Hora Sequence — 24 planetary hora entries
  5. Birth-Moment Strengths — Tara Bala, Chandra Bala
  6. Special Yogas — Siddha, Amrit, Marana, Kshana
  7. Era Conversions — Vikram Samvat, Shaka Samvat, Kali Yuga

No narration verbs — pure factual data only.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PANCHA_ANGA_LIMBS: list[str] = ["Tithi", "Vara", "Nakshatra", "Yoga", "Karana"]

SPECIAL_YOGA_NAMES: list[str] = ["Siddha", "Amrit", "Marana", "Kshana"]

ERA_NAMES: list[str] = ["Vikram Samvat", "Shaka Samvat", "Kali Yuga"]

ASTRONOMICAL_WINDOWS: list[str] = [
    "Sunrise",
    "Sunset",
    "Brahma Muhurta",
    "Abhijit Muhurta",
    "Rahu Kalam",
    "Gulika Kalam",
    "Yamaganda",
]

_NA = "N/A"


# ---------------------------------------------------------------------------
# Private formatting helpers
# ---------------------------------------------------------------------------

def _fmt_str(value: Any) -> str:
    if value is None:
        return _NA
    s = str(value).strip()
    return s if s else _NA


def _fmt_int(value: Any) -> str:
    if value is None:
        return _NA
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return _NA


def _fmt_float(value: Any, precision: int = 1) -> str:
    if value is None:
        return _NA
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return _NA


def _fmt_bool_yn(value: Any) -> str:
    if value is None:
        return _NA
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if str(value).lower() in ("true", "yes", "1"):
        return "Yes"
    if str(value).lower() in ("false", "no", "0"):
        return "No"
    return _NA


def _fmt_sandhi(value: Any) -> str:
    """Return 'Yes' / 'No' for sandhi flag."""
    return _fmt_bool_yn(value)


def _title(value: Any) -> str:
    """Title-case a string; return _NA if absent."""
    s = _fmt_str(value)
    return s if s == _NA else s.title()


def _window_start_end(data: Any) -> tuple[str, str]:
    """Extract start/end from a dict or return (_NA, _NA)."""
    if not isinstance(data, dict):
        return _NA, _NA
    start = _fmt_str(data.get("start"))
    end = _fmt_str(data.get("end"))
    return start, end


# ---------------------------------------------------------------------------
# Sub-renderers — Five Limbs
# ---------------------------------------------------------------------------

def _render_five_limbs(panchanga: dict) -> str:
    """Render the Pancha Anga (five limbs) as a markdown table."""
    lines: list[str] = [
        "### Five Limbs (Pancha Anga)\n",
        "| Limb | Value | Details |",
        "|------|-------|---------|",
    ]

    # --- Tithi ---
    tithi = panchanga.get("tithi") or {}
    if isinstance(tithi, dict):
        t_name   = _fmt_str(tithi.get("name"))
        t_pada   = _fmt_int(tithi.get("pada"))
        t_lord   = _fmt_str(tithi.get("lord"))
        t_paksha = _fmt_str(tithi.get("paksha"))
        t_pct    = _fmt_float(tithi.get("completion_pct"), precision=1)
        t_pada_s   = f"Pada {t_pada}" if t_pada != _NA else f"Pada {_NA}"
        t_details  = (
            f"{t_pada_s}, Lord: {t_lord}, Paksha: {t_paksha}, "
            f"Completion: {t_pct}%"
        )
    else:
        t_name, t_details = _NA, _NA
    lines.append(f"| Tithi | {t_name} | {t_details} |")

    # --- Vara ---
    vara = panchanga.get("vara") or {}
    if isinstance(vara, dict):
        v_name = _fmt_str(vara.get("name"))
        v_lord = _fmt_str(vara.get("lord"))
        v_details = f"Lord: {v_lord}"
    else:
        v_name, v_details = _NA, _NA
    lines.append(f"| Vara | {v_name} | {v_details} |")

    # --- Nakshatra ---
    nak = panchanga.get("nakshatra") or {}
    if isinstance(nak, dict):
        n_name   = _fmt_str(nak.get("name"))
        n_pada   = _fmt_int(nak.get("pada"))
        n_lord   = _fmt_str(nak.get("lord"))
        n_sandhi = _fmt_sandhi(nak.get("sandhi"))
        n_pada_s   = f"Pada {n_pada}" if n_pada != _NA else f"Pada {_NA}"
        n_details  = f"{n_pada_s}, Lord: {n_lord}, Sandhi: {n_sandhi}"
    else:
        n_name, n_details = _NA, _NA
    lines.append(f"| Nakshatra | {n_name} | {n_details} |")

    # --- Yoga ---
    yoga = panchanga.get("yoga") or {}
    if isinstance(yoga, dict):
        y_name   = _fmt_str(yoga.get("name"))
        y_nature = _title(yoga.get("nature"))
        y_details = f"Nature: {y_nature}"
    else:
        y_name, y_details = _NA, _NA
    lines.append(f"| Yoga | {y_name} | {y_details} |")

    # --- Karana ---
    karana = panchanga.get("karana") or {}
    if isinstance(karana, dict):
        k_name   = _fmt_str(karana.get("name"))
        k_lord   = _fmt_str(karana.get("lord"))
        k_nature = _title(karana.get("nature"))
        k_details = f"Lord: {k_lord}, Nature: {k_nature}"
    else:
        k_name, k_details = _NA, _NA
    lines.append(f"| Karana | {k_name} | {k_details} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sub-renderers — Astronomical Windows
# ---------------------------------------------------------------------------

def _render_astronomical_windows(panchanga: dict) -> str:
    """Render sunrise/sunset + muhurta + kalam windows as a markdown table."""
    lines: list[str] = [
        "### Astronomical Windows\n",
        "| Window | Start (UTC) | End (UTC) |",
        "|--------|-------------|-----------|",
    ]

    # Sunrise — single time, no end
    sunrise = _fmt_str(panchanga.get("sunrise"))
    lines.append(f"| Sunrise | {sunrise} | — |")

    # Sunset — single time, no end
    sunset = _fmt_str(panchanga.get("sunset"))
    lines.append(f"| Sunset | {sunset} | — |")

    # Brahma Muhurta
    brahma = panchanga.get("brahma_muhurta") or {}
    b_start, b_end = _window_start_end(brahma)
    lines.append(f"| Brahma Muhurta | {b_start} | {b_end} |")

    # Abhijit Muhurta
    abhijit = panchanga.get("abhijit_muhurta") or {}
    a_start, a_end = _window_start_end(abhijit)
    lines.append(f"| Abhijit Muhurta | {a_start} | {a_end} |")

    # Rahu Kalam
    rahu = panchanga.get("rahu_kalam") or {}
    r_start, r_end = _window_start_end(rahu)
    lines.append(f"| Rahu Kalam | {r_start} | {r_end} |")

    # Gulika Kalam
    gulika = panchanga.get("gulika_kalam") or {}
    g_start, g_end = _window_start_end(gulika)
    lines.append(f"| Gulika Kalam | {g_start} | {g_end} |")

    # Yamaganda
    yama = panchanga.get("yamaganda") or {}
    ym_start, ym_end = _window_start_end(yama)
    lines.append(f"| Yamaganda | {ym_start} | {ym_end} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sub-renderers — Choghadiya
# ---------------------------------------------------------------------------

def _render_choghadiya_table(segments: list, title: str) -> str:
    """Render one choghadiya table (day or night)."""
    lines: list[str] = [
        f"### {title}\n",
        "| Segment | Name | Nature | Start | End |",
        "|---------|------|--------|-------|-----|",
    ]

    if not segments:
        lines.append("| — | — | — | — | — |")
    else:
        for idx, seg in enumerate(segments, start=1):
            if not isinstance(seg, dict):
                lines.append(f"| {idx} | {_NA} | {_NA} | {_NA} | {_NA} |")
                continue
            name   = _fmt_str(seg.get("name"))
            nature = _title(seg.get("nature"))
            start  = _fmt_str(seg.get("start"))
            end    = _fmt_str(seg.get("end"))
            lines.append(f"| {idx} | {name} | {nature} | {start} | {end} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sub-renderers — Hora Sequence
# ---------------------------------------------------------------------------

def _render_hora_sequence(panchanga: dict) -> str:
    """Render 24-hour planetary hora table."""
    lines: list[str] = [
        "### Hora Sequence (24 Hours)\n",
        "| Hour | Planetary Hora |",
        "|------|---------------|",
    ]

    hora_seq = panchanga.get("hora_sequence") or []

    if not hora_seq:
        lines.append("| — | — |")
    else:
        for entry in hora_seq:
            if not isinstance(entry, dict):
                continue
            hour   = _fmt_int(entry.get("hour"))
            planet = _fmt_str(entry.get("planet"))
            lines.append(f"| {hour} | {planet} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sub-renderers — Birth-Moment Strengths
# ---------------------------------------------------------------------------

def _render_birth_strengths(panchanga: dict) -> str:
    """Render Tara Bala and Chandra Bala as a markdown table."""
    lines: list[str] = [
        "### Birth-Moment Strengths\n",
        "| Measure | Value |",
        "|---------|-------|",
    ]

    # Tara Bala
    tara = panchanga.get("tara_bala") or {}
    if isinstance(tara, dict):
        t_class = _fmt_str(tara.get("class"))
        t_fav   = _fmt_bool_yn(tara.get("favorable"))
        t_value = f"{t_class} ({t_fav})" if t_class != _NA else _NA
    else:
        t_value = _NA
    lines.append(f"| Tara Bala | {t_value} |")

    # Chandra Bala
    chandra = panchanga.get("chandra_bala") or {}
    if isinstance(chandra, dict):
        c_class = _fmt_str(chandra.get("class"))
        c_score = _fmt_int(chandra.get("score"))
        if c_class != _NA and c_score != _NA:
            c_value = f"{c_class} (Score: {c_score})"
        elif c_class != _NA:
            c_value = c_class
        else:
            c_value = _NA
    else:
        c_value = _NA
    lines.append(f"| Chandra Bala | {c_value} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sub-renderers — Special Yogas
# ---------------------------------------------------------------------------

def _render_special_yogas(panchanga: dict) -> str:
    """Render special yoga presence flags as a markdown table."""
    lines: list[str] = [
        "### Special Yogas\n",
        "| Yoga | Present |",
        "|------|---------|",
    ]

    special = panchanga.get("special_yogas") or {}
    if isinstance(special, dict):
        lines.append(f"| Siddha Yoga | {_fmt_bool_yn(special.get('siddha'))} |")
        lines.append(f"| Amrit Yoga  | {_fmt_bool_yn(special.get('amrit'))} |")
        lines.append(f"| Marana Yoga | {_fmt_bool_yn(special.get('marana'))} |")
        lines.append(f"| Kshana Yoga | {_fmt_bool_yn(special.get('kshana'))} |")
    else:
        for name in ["Siddha Yoga", "Amrit Yoga", "Marana Yoga", "Kshana Yoga"]:
            lines.append(f"| {name} | {_NA} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sub-renderers — Era Conversions
# ---------------------------------------------------------------------------

def _render_era_conversions(panchanga: dict) -> str:
    """Render Vikram Samvat, Shaka Samvat, Kali Yuga as a markdown table."""
    lines: list[str] = [
        "### Era Conversions\n",
        "| Era | Year |",
        "|-----|------|",
    ]

    vs = _fmt_int(panchanga.get("vikram_samvat"))
    ss = _fmt_int(panchanga.get("shaka_samvat"))
    ky = _fmt_int(panchanga.get("kali_yuga"))

    lines.append(f"| Vikram Samvat | {vs} |")
    lines.append(f"| Shaka Samvat  | {ss} |")
    lines.append(f"| Kali Yuga     | {ky} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Section renderer (public API)
# ---------------------------------------------------------------------------

def render_panchanga_section(chart_output: dict) -> str:
    """
    Render the full birth-day Panchanga section for FORENSIC.md.

    Covers:
    - Five Limbs (Pancha Anga): Tithi, Vara, Nakshatra, Yoga, Karana
    - Astronomical Windows: Sunrise, Sunset, Brahma/Abhijit Muhurtas,
      Rahu Kalam, Gulika Kalam, Yamaganda
    - Choghadiya Day (8 segments) and Night (8 segments)
    - Hora Sequence: 24 planetary hora entries
    - Birth-Moment Strengths: Tara Bala, Chandra Bala
    - Special Yogas: Siddha, Amrit, Marana, Kshana
    - Era Conversions: Vikram Samvat, Shaka Samvat, Kali Yuga

    Expected chart_output key:
      "panchanga" — dict with all panchanga sub-keys as described above

    Returns a markdown string with no narration verbs.
    Gracefully degrades to N/A / placeholder rows when data is absent.
    """
    panchanga: dict = chart_output.get("panchanga") or {}

    parts: list[str] = []

    # 1. Five Limbs
    parts.append(_render_five_limbs(panchanga))
    parts.append("\n")

    # 2. Astronomical Windows
    parts.append(_render_astronomical_windows(panchanga))
    parts.append("\n")

    # 3. Choghadiya Day
    choghadiya_day = panchanga.get("choghadiya_day") or []
    parts.append(_render_choghadiya_table(choghadiya_day, "Choghadiya (Day)"))
    parts.append("\n")

    # 4. Choghadiya Night
    choghadiya_night = panchanga.get("choghadiya_night") or []
    parts.append(_render_choghadiya_table(choghadiya_night, "Choghadiya (Night)"))
    parts.append("\n")

    # 5. Hora Sequence
    parts.append(_render_hora_sequence(panchanga))
    parts.append("\n")

    # 6. Birth-Moment Strengths
    parts.append(_render_birth_strengths(panchanga))
    parts.append("\n")

    # 7. Special Yogas
    parts.append(_render_special_yogas(panchanga))
    parts.append("\n")

    # 8. Era Conversions
    parts.append(_render_era_conversions(panchanga))

    return "\n".join(parts)
