"""
pipeline/orchestrator/writers/bg_muhurta_lattice.py
L0 Brahmagyan global muhūrta boundary/factor lattice writer — seeds bg_muhurta_lattice.

ṢAḌ-DARŚANA campaign, registry item 36-substrate ("Contender lattice + adjudication
engine ... Stage 1: The temporal lattice"). SHAD_DARSHANA_BRIEF_v2_0.md §2 names this
writer `bg_muhurta_lattice.py` — "global boundary/factor lattice tables, rolling
horizon (~5y), incl. Agnivāsa states, combination-yoga spans, kālams, ghaṭīs
(chart-independent parts only; per-chart contact joins live in `ka_kshetra` stage 1)".

WHAT THIS WRITER BUILDS (four chart-independent factor families)
──────────────────────────────────────────────────────────────────
A single chart-INDEPENDENT lattice of muhūrta-relevant classical factors, all
computed via `panchang_engine` (REUSED wholesale — no astronomical/classical-rule
math is reimplemented here, exactly the `bg_sky_calendar` precedent):

  1. AGNIVĀSA  — Agni's tithi-keyed elemental residence (Pṛthvī/Jala/Vāyu/Ākāśa),
     one row per calendar day, via `panchang_engine.rich_topics.compute_vasa_family`
     (`AGNI_VASA_TABLE`). The sibling Vāsa attributes (Chandra/Rāhu/Diśā/Nakṣatra/
     Bhadra vāsa) ride along in the same row's `detail` — they are the same
     tithi/vāra/nakṣatra-keyed family, not a separate factor_family.

  2. COMBINATION-YOGA SPANS — the 9 special-yoga detectors `panchang_engine`
     already implements and cites: Sarvārtha-siddhi, Amṛta-siddhi, Ravi-Puṣya,
     Guru-Puṣya, Tripuṣkara, Dvipuṣkara, Siddha-yoga, Bhadra (Viṣṭi karaṇa),
     Pañchaka doṣa (`panchang_engine.special_yogas.detect_all_special_yogas`).

  3. KĀLAM PERIODS — day-part windows via `panchang_engine.timings`:
     `compute_extended_inauspicious` (rāhu-kālam, yamagaṇḍa, gulika-kālam,
     durmuhūrta, yamakaṇṭaka, krakaca, varjyam, viṣa-ghaṭī, ṣaṣṭi-ghaṭī) +
     `compute_extended_auspicious` (brāhma-muhūrta, prātaḥ-sandhyā, abhijit,
     mādhyāhna-sandhyā, vijaya, godhūli, sāyaṃ-sandhyā, niśīta) + amṛta-kālam
     (from the base `compute_auspicious_timings`, which the extended function
     does not re-include; entries with no table value for a given nakṣatra —
     `AMRIT_KALAM_TABLE`'s documented "S1 stub" `None`s — are honestly skipped,
     never fabricated).

  4. GHAṬĪ-MUHŪRTA BOUNDARIES — the 30 named ghaṭī-grained day+night muhūrtas
     via `panchang_engine.timings.compute_day_muhurtas`. CORRECTION (Opus
     corpus-citation review, 2026-07-30): this writer's earlier text implied
     the day/night boundary is the true computed sunset. It is NOT —
     `compute_day_muhurtas(sunrise_utc, next_sunrise_utc)` takes only
     sunrise and the FOLLOWING day's sunrise (never the true `sunset_utc`
     this writer already computes) and internally APPROXIMATES the day/night
     midpoint as the exact arithmetic half of the sunrise-to-next-sunrise
     interval (`sunset_approx = sunrise_utc + (next_sunrise_utc -
     sunrise_utc) / 2`), not the real, asymmetric sunrise/sunset split. The
     15 day-muhūrtas and 15 night-muhūrtas are real ghaṭī (24-min) grained
     boundaries computed relative to this approximated midpoint, not the
     chart's true sunset — disclosed here rather than silently assumed.

WHAT THIS WRITER DOES NOT BUILD:
  - The base pañcāṅga aṅgas (tithi/vāra/nakṣatra/yoga/karaṇa) as their own factor
    family — those are read here only as INPUTS to the four families above (e.g.
    a combination-yoga span's start/end IS the underlying aṅga's window), not
    re-served as a fifth family. A global pañcāṅga almanac, if ever needed, is a
    separate future asset.
  - Any per-chart/per-querent-location computation. Item 6 (activity-specific
    muhūrta rule tables) and item 7 (muhūrta-lagna) are W3-owned, not this
    writer's job. Per-chart CONTACT joins (e.g. "is this window good for THIS
    native") are `ka_kshetra`'s job (brief §2, explicit).

REFERENCE LOCATION (explicit scope decision — mirrors bg_sky_calendar's own
documented boundary-drawing style): Agnivāsa/combination-yoga membership is a pure
function of tithi/vāra/nakṣatra (location-independent), but kālam windows are
sunrise/sunset-anchored and ghaṭī-muhūrtas are sunrise/next-sunrise-anchored
(see the family-4 correction note below for the exact, non-true-sunset
midpoint `compute_day_muhurtas` actually uses) — both genuinely
LOCATION-dependent —
"chart-independent" does not mean "location-independent." This writer computes at
ONE FIXED reference location: Bhubaneswar/IST, (lat=20.27, lon=85.84,
tz_offset_minutes=+330) — the exact (lat, lon, tz_offset) triple
`platform/python-sidecar/routers/panchang.py`'s `_PANCHANGA_KNOWN_LOCATIONS
['bhubaneswar']` already uses as its FORENSIC-matching fallback (chosen for
consistency with the rest of the project's "global panchāṅga reference" usage,
not because it is the native's own birth location — this table is still
chart-independent; it merely needs SOME location to anchor a sunrise). Adjusting
to a specific querent's actual location is explicitly deferred to a future
per-location join (parallel to bg_sky_calendar's returns/per-chart-join
deferral) — NOT built here.

CITATION DISCIPLINE (B.10 / CLAUDE.md §N.7 — every row honestly disclosed):
Each factor_key below carries the actual inline citation panchang_engine's own
source documents (Muhūrta Chintāmaṇi / Bṛhat Saṃhitā / Drik Panchang, abbreviated
MC/BS/DP per that module's own convention) where one exists. Where the underlying
shastra_tables.py table carries NO inline "Source:" comment (found for real during
this writer's construction — the Vāsa-family tables, Yamakaṇṭaka/Krakaca/Viṣa-
ghaṭī/Ṣaṣṭi-ghaṭī, and several of the extended-auspicious Sandhyā-type windows),
the row is stored with `corpus_status='computed_uncited_convention'` rather than
inventing a citation — disclosed honestly, never silently upgraded to
`computed_cited`. See `bg_parihara_rules`'s `bg_muhurta_factor_census` for the
full census/gap register this feeds.

HORIZON (rolling ~5y forward, brief's own figure for this asset — deliberately
NOT bg_sky_calendar's 10y; that asset serves retrodiction too, this one is a
forward election substrate only):
  FORWARD_HORIZON_YEARS = 5, computed as `today + 5y` AT RUN TIME (rolling,
  re-runnable to extend — brief §2.5.6). No fixed historical start (unlike
  bg_sky_calendar's HISTORY_START=1900) — muhūrta election has no retrodiction use
  case named in this writer's brief; the horizon starts at `today`.

Conforms to FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2):
- uses ctx.db_conn exclusively (never opens, commits, or closes it)
- returns WriterResult with actual rows_inserted
- honours ctx.dry_run
- HEAVY writer (`plan_substeps` + `run_substep`, one sub-step per calendar year
  touched by the horizon — up to 6 sub-steps for a 5y forward span straddling a
  partial first/last year): per-day `compute_panchang`-style computation (9
  planets + 4 bisection anga searches + timing/yoga derivation per day) is a
  meaningfully heavier per-unit cost than bg_sky_calendar's cached ingress scan,
  so this writer takes the heavy-writer shape from the start rather than
  discovering the >~10 min threshold in production.

L0 idempotency (CLAUDE.md §N.3): global reference table, `ON CONFLICT
(factor_family, factor_key, start_utc) DO NOTHING` — deterministic recomputation
of an already-covered window reproduces identical rows; a re-run only WIDENS
coverage as the rolling forward horizon advances.

ZERO LLM use. Pure deterministic panchang_engine (pyswisseph-backed) computation,
reused wholesale.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)

logger = logging.getLogger(__name__)

# ── Horizon (rolling forward only; see module docstring) ────────────────────

FORWARD_HORIZON_YEARS = 5
SAMPLING_METHOD_VERSION = "muhurta_lattice_agnivasa_yoga_kalam_ghati_v1"

# ── Reference location (see module docstring "REFERENCE LOCATION") ──────────
REFERENCE_LOCATION_KEY = "bhubaneswar"
REFERENCE_LAT = 20.27
REFERENCE_LON = 85.84
REFERENCE_TZ_OFFSET_MINUTES = 330
AYANAMSHA_KEY = "lahiri"


def compute_horizon(today: date | None = None) -> tuple[date, date]:
    """
    Pure function: (start, forward_end) for a given `today`. Rolling forward
    horizon — no fixed historical start (see module docstring HORIZON section).
    """
    if today is None:
        today = date.today()
    try:
        forward_end = today.replace(year=today.year + FORWARD_HORIZON_YEARS)
    except ValueError:
        # Feb 29 on a non-leap target year -- fall back to Feb 28.
        forward_end = today.replace(year=today.year + FORWARD_HORIZON_YEARS, day=28)
    return today, forward_end


def plan_year_substeps(start: date, end: date) -> list[SubStep]:
    """
    Pure function: partition [start, end) into one SubStep per calendar year
    touched (a partial first/last year is its own sub-step, scoped to the
    actual sub-range it covers).
    """
    steps: list[SubStep] = []
    year = start.year
    while year <= end.year:
        steps.append(SubStep(key=f"year:{year}", label=f"bg_muhurta_lattice:{year}"))
        year += 1
    return steps


def _year_range(year: int, start: date, end: date) -> tuple[date, date]:
    """The [range_start, range_end) sub-range of `year` inside [start, end)."""
    year_start = date(year, 1, 1)
    year_end = date(year + 1, 1, 1)
    return max(start, year_start), min(end, year_end)


# ── Citation map (honest per-factor-key disclosure; see module docstring) ────
# (source_citation, corpus_status) — corpus_status is 'computed_cited' when
# panchang_engine's own source documents an inline MC/BS/DP citation for this
# exact table/function, 'computed_uncited_convention' when the underlying
# shastra_tables.py entry carries no inline citation (found honestly during
# construction of this writer, not assumed).
_MC = "Muhūrta Chintāmaṇi"
_BS = "Bṛhat Saṃhitā"
_DP = "Drik Panchang (drikpanchang.com) published convention"

COMBINATION_YOGA_CITATIONS: dict[str, tuple[str, str]] = {
    # NOTE (Opus corpus-citation review, 2026-07-30): earlier text over-cited
    # specific verse numbers "(5.16)"/"(5.17)" here. shastra_tables.py's own
    # per-table comments do assign those numbers to these two tables, but
    # special_yogas.py's own docstring for Amrit Siddhi separately states
    # "may be blocked by death-yoga overrides (MC 5.17)" as an UNIMPLEMENTED
    # exclusion rule -- i.e. 5.17 is cited for two different things in this
    # codebase's own source (the formation table AND a distinct, unbuilt
    # blocking rule), which is an ambiguity in the source, not something this
    # writer can honestly resolve. Narrowed to the un-ambiguous "MC §10"
    # (both tables' shared parent section) rather than assert a specific
    # sub-verse split that isn't cleanly attributable.
    "sarvartha_siddhi": (f"{_MC} §10; {_DP}", "computed_cited"),
    "amrit_siddhi": (f"{_MC} §10; {_DP} (note: MC 5.17 also names a separate, unimplemented death-yoga/Visha-Yoga blocking rule on this table -- see bg_muhurta_factor_census)", "computed_cited"),
    "ravi_pushya": (f"{_MC} §10; {_DP} 'Ravi Pushya Yoga' dedicated page", "computed_cited"),
    "guru_pushya": (f"{_MC} §10; {_DP} 'Guru Pushya Nakshatra Yoga' dedicated page", "computed_cited"),
    "tripushkar": (f"{_MC} §11; {_DP}", "computed_cited"),
    "dwipushkar": (f"{_MC} §11; {_DP}", "computed_cited"),
    "siddha_yoga": (f"{_MC} §10; {_BS} §3; {_DP} published table", "computed_cited"),
    "bhadra": (f"{_MC} §2; {_BS} §2; {_DP} (start/end display convention)", "computed_cited"),
    "panchaka": (f"{_BS} §3; {_DP} 'Panchaka' dedicated page", "computed_cited"),
}

KALAM_CITATIONS: dict[str, tuple[str, str]] = {
    "rahu_kalam": (f"{_DP} published index tables (RAHU_KALAM_INDEX)", "computed_cited"),
    "yamaganda": (f"{_DP} published index tables (YAMAGANDAM_INDEX)", "computed_cited"),
    "gulika_kalam": (f"{_DP} published index tables (GULIKA_INDEX)", "computed_cited"),
    # NOTE (Opus corpus-citation review, 2026-07-30): earlier text cited
    # "BS §2" for durmuhurta -- that citation does not appear anywhere in
    # source for this table. The two REAL citations that DO appear (in two
    # different source files, for the same DUR_MUHURTA_TABLE) are combined
    # here: timings.py's own compute_inauspicious_timings docstring says
    # "Source: MC §9"; shastra_tables.py's own §15 table comment says
    # "Source: DP published Dur Muhurta times."
    "durmuhurta": (f"{_MC} §9 (per panchang_engine.timings docstring); {_DP} published Dur Muhurta times (per shastra_tables.py table comment)", "computed_cited"),
    "varjyam": (f"{_MC} §8; {_DP} convention", "computed_cited"),
    "amrit_kalam": (f"{_MC} §7; {_DP} convention", "computed_cited"),
    "brahma_muhurta": (f"{_DP} convention (96-48 min before sunrise)", "computed_cited"),
    "abhijit": (f"{_MC} §5 (excluded on Wednesday)", "computed_cited"),
    # No inline "Source:" comment found in panchang_engine/shastra_tables.py or
    # timings.py for the following — honestly disclosed, not invented:
    "yamakantaka": (f"{_DP}-style day-part convention (no inline classical citation found in source; corpus gap — see bg_muhurta_factor_census)", "computed_uncited_convention"),
    "krakaca": (f"{_DP}-style night-part convention (no inline classical citation found in source; corpus gap — see bg_muhurta_factor_census)", "computed_uncited_convention"),
    "visha_ghati": (f"{_DP}-style ghaṭī convention (no inline classical citation found in source; corpus gap — see bg_muhurta_factor_census)", "computed_uncited_convention"),
    "sashtighati": (f"{_DP}-style ghaṭī convention (no inline classical citation found in source; corpus gap — see bg_muhurta_factor_census)", "computed_uncited_convention"),
    "pratah_sandhya": ("Sandhyā convention (no inline classical citation found in source; corpus gap)", "computed_uncited_convention"),
    "madhyahna_sandhya": ("Sandhyā convention (no inline classical citation found in source; corpus gap)", "computed_uncited_convention"),
    "vijaya": ("Vijaya-muhūrta convention (no inline classical citation found in source; corpus gap)", "computed_uncited_convention"),
    "godhuli": ("Godhūli convention (no inline classical citation found in source; corpus gap)", "computed_uncited_convention"),
    "sayam_sandhya": ("Sandhyā convention (no inline classical citation found in source; corpus gap)", "computed_uncited_convention"),
    "nishita": ("Niśīta convention (no inline classical citation found in source; corpus gap)", "computed_uncited_convention"),
}

AGNIVASA_CITATION = (
    "panchang_engine.shastra_tables.AGNI_VASA_TABLE (tithi-keyed elemental "
    "residence: Prithvi tithi 1-7, Jala 8-15, Vayu 16-22, Akasha 23-30); "
    "convention already live in production via ga_panchanga_writer.py's "
    "AGNI_VASA_BIRTH fact + get_panchanga.ts's panchanga_agni_vasa. No inline "
    "per-row classical-verse citation in source; Muhurta Chintamani ch.8-9 "
    "(classical_text_chunks text_id='muhurta_chintamani') contains an Agni/"
    "Vahni-nivasa section but is untranslated Devanagari OCR (content_en null) "
    "-- not independently re-verified against this exact 4-fold grouping. See "
    "bg_muhurta_factor_census for the full gap disclosure.",
    "computed_uncited_convention",
)

GHATI_MUHURTA_CITATION = (
    "panchang_engine.timings.compute_day_muhurtas — 30-fold day+night ghati-"
    "muhurta naming (Rudra..Bhaga day; Girisha..Samudram night), a well-known "
    "classical convention (cf. the cited Dur Muhurta subset, MC §9), but no "
    "inline per-row classical citation was found in source for this exact list "
    "-- disclosed honestly rather than assumed. See bg_muhurta_factor_census.",
    "computed_uncited_convention",
)


@dataclass
class _Row:
    factor_family: str
    factor_key: str
    start_utc: datetime
    end_utc: datetime
    detail: dict[str, Any]
    source_citation: str
    corpus_status: str


def compute_day_factors(day: date) -> list[_Row]:
    """
    Compute all four lattice factor families for one calendar day at the fixed
    reference location. Pure function of `day` (deterministic; no DB access).

    Reuses panchang_engine's existing, tested computation functions directly
    (thinner than calling `compute_panchang()` wholesale, which also computes
    several rich-topic fields this writer does not need — upagrahas, outer
    planets, calendrical, festivals, day_events, shoonya, choghadiya, hora).
    """
    from panchang_engine.timings import (
        compute_sunrise_sunset,
        compute_extended_inauspicious,
        compute_extended_auspicious,
        compute_auspicious_timings,
        compute_day_muhurtas,
    )
    from panchang_engine.planets import compute_all_grahas
    from panchang_engine.angas import (
        compute_tithi, compute_nakshatra, compute_yoga,
        compute_karana_pair, compute_vara,
    )
    from panchang_engine.rich_topics import compute_vasa_family
    from panchang_engine.special_yogas import detect_all_special_yogas
    from panchang_engine.ayanamsha import set_ayanamsha
    import swisseph as swe

    set_ayanamsha(AYANAMSHA_KEY)

    sunrise_utc, sunset_utc = compute_sunrise_sunset(
        day, REFERENCE_LAT, REFERENCE_LON, REFERENCE_TZ_OFFSET_MINUTES
    )
    next_sunrise_utc, _ = compute_sunrise_sunset(
        day + timedelta(days=1), REFERENCE_LAT, REFERENCE_LON, REFERENCE_TZ_OFFSET_MINUTES
    )

    jd_sunrise = swe.julday(
        sunrise_utc.year, sunrise_utc.month, sunrise_utc.day,
        sunrise_utc.hour + sunrise_utc.minute / 60.0 + sunrise_utc.second / 3600.0,
    )
    planets = compute_all_grahas(jd_sunrise)
    sun_lon = next(p.longitude_sidereal for p in planets if p.name == "Sun")
    moon_lon = next(p.longitude_sidereal for p in planets if p.name == "Moon")

    tithi = compute_tithi(sun_lon, moon_lon, sunrise_utc)
    nakshatra = compute_nakshatra(moon_lon, sunrise_utc)
    yoga = compute_yoga(sun_lon, moon_lon, sunrise_utc)
    karana_first, karana_second = compute_karana_pair(sun_lon, moon_lon, sunrise_utc, sunrise_utc)
    vara = compute_vara(day)

    rows: list[_Row] = []

    # ── Family 1: Agnivāsa (+ sibling vāsa attributes in detail) ─────────────
    vasa = compute_vasa_family(tithi.id, vara.id, nakshatra.id)
    citation, corpus_status = AGNIVASA_CITATION
    rows.append(_Row(
        factor_family="agnivasa",
        factor_key="agni_vasa",
        start_utc=sunrise_utc,
        end_utc=next_sunrise_utc,
        detail={
            "tithi_id": tithi.id, "tithi_name": tithi.name,
            "vara_id": vara.id, "vara_name": vara.name,
            "element": vasa.agni_vasa,
            "chandra_vasa": vasa.chandra_vasa,
            "rahu_vasa": vasa.rahu_vasa,
            "disha_vasa": vasa.disha_vasa,
            "nakshatra_vasa": vasa.nakshatra_vasa,
            "bhadra_vasa": vasa.bhadra_vasa,
        },
        source_citation=citation,
        corpus_status=corpus_status,
    ))

    # ── Family 2: combination-yoga spans ─────────────────────────────────────
    special_yogas = detect_all_special_yogas(
        sunrise_utc, sunset_utc, next_sunrise_utc,
        tithi, nakshatra, yoga, karana_first, karana_second, vara,
    )
    for yd in special_yogas:
        citation, corpus_status = COMBINATION_YOGA_CITATIONS.get(
            yd["yoga"], (f"{_DP} (uncatalogued yoga key; corpus gap)", "computed_uncited_convention")
        )
        rows.append(_Row(
            factor_family="combination_yoga",
            factor_key=yd["yoga"],
            start_utc=yd["start_utc"],
            end_utc=yd["end_utc"],
            detail={"strength": yd["strength"], "stars": yd["stars"]},
            source_citation=citation,
            corpus_status=corpus_status,
        ))

    # ── Family 3: kālam periods ───────────────────────────────────────────────
    inauspicious = compute_extended_inauspicious(
        sunrise_utc, sunset_utc, vara.id, nakshatra.id, nakshatra.end_utc,
    )
    auspicious = compute_extended_auspicious(
        sunrise_utc, sunset_utc, vara.id, tithi.id, nakshatra.id,
    )
    for t in inauspicious:
        citation, corpus_status = KALAM_CITATIONS.get(
            t.label, (f"{_DP} (uncatalogued kalam key; corpus gap)", "computed_uncited_convention")
        )
        rows.append(_Row(
            factor_family="kalam", factor_key=t.label,
            start_utc=t.start_utc, end_utc=t.end_utc,
            detail={"category": "inauspicious"},
            source_citation=citation, corpus_status=corpus_status,
        ))
    for t in auspicious:
        # BUG FOUND AND FIXED (Opus corpus-citation review, 2026-07-30):
        # `compute_extended_auspicious` (panchang_engine/timings.py:463-489)
        # ignores vara_id entirely and always emits "abhijit" -- but the
        # KALAM_CITATIONS entry for "abhijit" cites "Muhurta Chintamani §5
        # (excluded on Wednesday)", the SAME rule the base (non-extended)
        # `compute_auspicious_timings` correctly implements (it returns None
        # for abhijit when vara_id==4). Empirically confirmed on a real
        # Wednesday (2026-08-05, vara.id=4): extended path returned "abhijit"
        # present while the base path correctly returned None. Serving
        # "abhijit present" on a Wednesday while citing "excluded on
        # Wednesday" is a self-contradicting row -- filtered here rather than
        # patching the shared, reused `compute_extended_auspicious` (out of
        # this writer's scope; the same "don't touch shared reused utilities"
        # discipline bg_sky_calendar's own docstring already establishes for
        # `find_ingress_events`'s sign-cusp artifact).
        if t.label == "abhijit" and vara.id == 4:
            continue
        citation, corpus_status = KALAM_CITATIONS.get(
            t.label, (f"{_DP} (uncatalogued kalam key; corpus gap)", "computed_uncited_convention")
        )
        rows.append(_Row(
            factor_family="kalam", factor_key=t.label,
            start_utc=t.start_utc, end_utc=t.end_utc,
            detail={"category": "auspicious"},
            source_citation=citation, corpus_status=corpus_status,
        ))
    # amrit_kalam: only in the BASE compute_auspicious_timings (not re-included
    # by compute_extended_auspicious) -- honestly skip nakshatras with no table
    # entry (AMRIT_KALAM_TABLE's documented "S1 stub" Nones), never fabricate.
    base_auspicious = compute_auspicious_timings(
        sunrise_utc, sunset_utc, vara.id, tithi.id, nakshatra.id,
    )
    amrit = base_auspicious.get("amrit_kalam")
    if amrit is not None:
        citation, corpus_status = KALAM_CITATIONS["amrit_kalam"]
        rows.append(_Row(
            factor_family="kalam", factor_key="amrit_kalam",
            start_utc=amrit.start_utc, end_utc=amrit.end_utc,
            detail={"category": "auspicious"},
            source_citation=citation, corpus_status=corpus_status,
        ))

    # ── Family 4: ghaṭī-muhūrta boundaries ────────────────────────────────────
    day_muhurtas = compute_day_muhurtas(sunrise_utc, next_sunrise_utc)
    citation, corpus_status = GHATI_MUHURTA_CITATION
    for m in day_muhurtas:
        rows.append(_Row(
            factor_family="ghati_muhurta",
            factor_key=f"{m['number']}:{m['name']}",
            start_utc=m["start_utc"], end_utc=m["end_utc"],
            detail={"number": m["number"], "period": m["period"], "quality": m["quality"]},
            source_citation=citation, corpus_status=corpus_status,
        ))

    return rows


@register("bg_muhurta_lattice")
class BgMuhurtaLatticeWriter(WriterBase):
    """
    Seeds bg_muhurta_lattice — a chart-independent global muhūrta boundary/factor
    lattice (Agnivāsa, combination-yoga spans, kālam periods, ghaṭī-muhūrtas), at a
    fixed Bhubaneswar/IST reference location, over a rolling ~5y forward horizon.
    See module docstring for full methodology and scope boundaries.

    HEAVY writer: one sub-step per calendar year in the horizon.
    """

    asset_id = "bg_muhurta_lattice"
    has_substeps = True
    _BATCH_SIZE = 500

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        start, end = compute_horizon()
        return plan_year_substeps(start, end)

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        t0 = time.time()

        if ctx.dry_run:
            logger.info("[bg_muhurta_lattice] dry_run=True — skipping %s", step.key)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0, notes="dry_run",
                duration_seconds=round(time.time() - t0, 2),
            )

        try:
            import swisseph  # noqa: F401  -- availability probe
        except ImportError:
            logger.warning("[bg_muhurta_lattice] swisseph not available — skipping %s", step.key)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="skipped: swisseph unavailable",
                duration_seconds=round(time.time() - t0, 2),
            )

        start, end = compute_horizon()
        year = int(step.key.split(":", 1)[1])
        range_start, range_end = _year_range(year, start, end)

        all_rows: list[_Row] = []
        try:
            d = range_start
            while d < range_end:
                all_rows.extend(compute_day_factors(d))
                d += timedelta(days=1)
        except Exception as exc:
            logger.error("[bg_muhurta_lattice] computation failed for %s: %s", step.key, exc)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"failed: {exc}",
                duration_seconds=round(time.time() - t0, 2),
            )

        conn = ctx.db_conn
        rows_written = 0
        try:
            with conn.cursor() as cur:
                batch: list[dict[str, Any]] = []
                for row in all_rows:
                    batch.append(self._to_insert_dict(row, ctx.build_id))
                    if len(batch) >= self._BATCH_SIZE:
                        rows_written += self._flush_batch(cur, batch)
                        batch = []
                if batch:
                    rows_written += self._flush_batch(cur, batch)
        except Exception as exc:
            logger.error(
                "[bg_muhurta_lattice] insert failed after %d rows for %s: %s",
                rows_written, step.key, exc,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=rows_written,
                notes=f"partial: {exc}",
                duration_seconds=round(time.time() - t0, 2),
            )

        elapsed = round(time.time() - t0, 2)
        logger.info(
            "[bg_muhurta_lattice] %s complete — %d/%d rows written in %.1fs",
            step.key, rows_written, len(all_rows), elapsed,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_written,
            duration_seconds=elapsed,
            notes=(
                f"{step.key}: range={range_start.isoformat()}..{range_end.isoformat()}; "
                f"scanned={len(all_rows)}"
            ),
        )

    @staticmethod
    def _to_insert_dict(row: _Row, build_id: str) -> dict[str, Any]:
        import json
        return {
            "factor_family": row.factor_family,
            "factor_key": row.factor_key,
            "start_utc": row.start_utc,
            "end_utc": row.end_utc,
            "detail": json.dumps(row.detail),
            "reference_lat": REFERENCE_LAT,
            "reference_lon": REFERENCE_LON,
            "reference_tz_offset_minutes": REFERENCE_TZ_OFFSET_MINUTES,
            "reference_location_key": REFERENCE_LOCATION_KEY,
            "ayanamsha_key": AYANAMSHA_KEY,
            "sampling_method": SAMPLING_METHOD_VERSION,
            "source_citation": row.source_citation,
            "corpus_status": row.corpus_status,
            "build_id": build_id,
        }

    @staticmethod
    def _flush_batch(cur: Any, batch: list[dict[str, Any]]) -> int:
        cur.executemany(
            """
            INSERT INTO bg_muhurta_lattice
              (factor_family, factor_key, start_utc, end_utc, detail,
               reference_lat, reference_lon, reference_tz_offset_minutes,
               reference_location_key, ayanamsha_key, sampling_method,
               source_citation, corpus_status, build_id, computed_at)
            VALUES
              (%(factor_family)s, %(factor_key)s, %(start_utc)s, %(end_utc)s,
               %(detail)s::jsonb, %(reference_lat)s, %(reference_lon)s,
               %(reference_tz_offset_minutes)s, %(reference_location_key)s,
               %(ayanamsha_key)s, %(sampling_method)s, %(source_citation)s,
               %(corpus_status)s, %(build_id)s, NOW())
            ON CONFLICT (factor_family, factor_key, start_utc)
            DO NOTHING
            """,
            batch,
        )
        return cur.rowcount
