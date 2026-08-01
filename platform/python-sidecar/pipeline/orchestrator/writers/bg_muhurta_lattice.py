"""
pipeline/orchestrator/writers/bg_muhurta_lattice.py
L0 Brahmagyan global muhūrta boundary/factor lattice writer — seeds bg_muhurta_lattice.

ṢAḌ-DARŚANA campaign, registry item 36-substrate ("Contender lattice + adjudication
engine ... Stage 1: The temporal lattice"). SHAD_DARSHANA_BRIEF_v2_0.md §2 names this
writer `bg_muhurta_lattice.py` — "global boundary/factor lattice tables, rolling
horizon (~5y), incl. Agnivāsa states, combination-yoga spans, kālams, ghaṭīs
(chart-independent parts only; per-chart contact joins live in `ka_kshetra` stage 1)".

W4 EXTENSION (ṢAḌ-DARŚANA Lane R, DESIGN RULING R-1 — five NEW families)
──────────────────────────────────────────────────────────────────
`KALA_W4_UPAYA_DESIGN_v1_0.md` §3.1 found that three of the canned W4 Mode-2
fixture's six constraints (`hora_lord = Guru`, `vara = Guru-vāra`, and the
`bg_muhurta_activity_rules` join) had **no lattice atoms to search over** — the
census rows for `day_part/hora_lord`, `panchangika/vara` and
`panchangika/nakshatra` pointed at *functions*, not at this table. Elevation §9
Stage 1 makes coverage a property of the CONSTRUCTION (the horizon is partitioned
by every boundary event of every factor, so "no sampling interval exists inside
which a 90-minute window could hide"); a Mode-2 search that sampled panchāṅga
per candidate would reintroduce exactly the sampling interval that guarantee
exists to abolish. Ruling R-1 therefore extends this writer with:

  5. HORA          — the 24 planetary hours per sunrise→next-sunrise cycle, via
     `panchang_engine.timings.compute_hora` (Chaldean HORA_CYCLE seeded from
     VARA_HORA_START). `detail.lord` is the hora lord's canonical graha name,
     read from panchang_engine's own table — never hand-mapped.
  6. VARA          — the sunrise-to-sunrise weekday, `factor_id` = the CANONICAL
     `VARA_NAMES` key (1..7) read straight from `compute_vara(...).id`.
  7. NAKSHATRA     — the sunrise nakṣatra, `factor_id` = `compute_nakshatra(...).id`
     (1..27), the canonical `NAKSHATRA_NAMES` index.
  8. TITHI         — the sunrise tithi, `factor_id` = `compute_tithi(...).id`
     (1..30), the canonical `TITHI_NAMES` key.
  9. LAGNA         — registry item 7 (muhūrta-lagna + strength check): the 12
     rising-sign spans per day at the reference location, found by real bisection
     over `panchang_engine.lagna.compute_lagna`'s `ascendant_sign_id`, each row
     carrying the lagna lord (`SIGN_LORDS`) and all nine grahas' sidereal
     sign_ids at the span start — the FACTS from which a query-time strength
     check (dignity via `bg_dignity_reference`, dṛṣṭi via BPHS Ch.26) is
     computed. This writer emits no dignity/aspect JUDGMENT: §N.5 — the
     reference table is the authority, and a judgment restated here would be a
     second copy of it.

  THE ID PROVENANCE RAIL (ADJUDICATION-10 / design §3.3, binding). Families 6–8
  carry `detail.factor_id` **read from panchang_engine's own numbered tables**
  (`compute_vara(...).id`, `compute_nakshatra(...).id`, `compute_tithi(...).id`)
  — the SAME source `bg_muhurta_activity_rules.factor_id` was populated from
  (`shastra_tables.EVENT_TABLES`, materialized verbatim by
  `bg_parihara_rules.build_activity_rule_rows`). The item-6 join therefore rests
  on ONE deterministic source, never on a hand-written name→id correspondence.
  A hand-mapped correspondence would be a B.10 fabrication and a gate failure;
  if a future edit ever makes these ids anything other than a direct read from
  panchang_engine, the item-6 join MUST be disabled again, not patched.

  SPAN CONVENTION for families 6–8 (disclosed, not assumed). Each row spans the
  Hindu day `[sunrise_utc, next_sunrise_utc)` and names the aṅga PREVAILING AT
  SUNRISE — the same convention family 1 (agnivāsa) already uses, and the same
  convention `bg_muhurta_activity_rules` grades a day by. The aṅga's TRUE
  sub-day boundary is not discarded: `detail.anga_true_end_utc` carries
  panchang_engine's own computed `end_utc` for the aṅga, and
  `detail.span_convention` names the convention on every row. A consumer needing
  exact aṅga boundaries reads `anga_true_end_utc`; a consumer grading a day
  reads the span. Neither is silently substituted for the other.

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

WHAT THIS WRITER DOES NOT BUILD (post-R-1 — this list SHRANK, deliberately):
  - `nityayoga` and `karana` as their own lattice families. R-1's ruling text
    calls these "optional-but-recommended … If Lane R defers them, the census
    must say so by name and the Mode-2 coverage block must list them as
    `not_computed (lattice family not materialized)`." They ARE deferred here,
    and the census says so by name (`bg_parihara_rules.CENSUS_ROWS` →
    `panchangika/nityayoga_lattice_family`, `panchangika/karana_lattice_family`).
    Deferring them does not block the W4 fixture (no fixture constraint names
    either as a lattice atom; the fixture's `karana NOT IN (viṣṭi)` clause
    resolves against the ALREADY-materialized `combination_yoga/bhadra` span).
    Pretending they are covered would.
  - Any per-querent-location computation. The lagna family (item 7) is computed
    at the SAME single reference location as every other sunrise-anchored family
    here — a querent whose location diverges gets that divergence served as data
    (`reference_location_key` is on every row), never silently reconciled.
  - Any dignity/aspect JUDGMENT on the lagna family. The row carries facts
    (sign ids, lord name, graha sign ids); the strength verdict is a query-time
    join against `bg_dignity_reference` (exaltation/debilitation/moolatrikona/
    own-signs, BPHS-cited) and BPHS Ch.26 dṛṣṭi. §N.5: this writer references
    the authority, it does not restate it.
  - Per-chart CONTACT joins (e.g. "is this window good for THIS native") — those
    are `ka_kshetra`'s job (brief §2, explicit), and chart-relative constraints
    (tārā-bala, chandrāṣṭama) are evaluated at QUERY time against the chart's own
    `chart_facts` rows. `nakshatra_tara_bala` correctly stays `not_computed` in
    the global census (design §3.1's ruling: "that disposition is correct and
    must not be 'fixed'"); a global table cannot hold a chart-personal value.

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
# v2 (ṢAḌ-DARŚANA W4 Lane R, ruling R-1): five families added — hora, vara,
# nakshatra, tithi, lagna. Version bumped rather than mutated so a row written
# by v1 is distinguishable from a v2 row at read time.
SAMPLING_METHOD_VERSION = "muhurta_lattice_agnivasa_yoga_kalam_ghati_hora_vara_nakshatra_tithi_lagna_v2"

# The nine families this writer emits. Kept as a module constant because the
# migration's CHECK constraint and this list must never disagree — the writer
# test asserts every emitted family is in this set, and the migration lists the
# same nine.
FACTOR_FAMILIES: tuple[str, ...] = (
    "agnivasa", "combination_yoga", "kalam", "ghati_muhurta",
    "hora", "vara", "nakshatra", "tithi", "lagna",
)

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


# ── W4 (ruling R-1) citations for the five new families ─────────────────────
# Each string below was read out of panchang_engine's OWN source before being
# written here (the same discipline the four original families used); where the
# source table carries no inline "Source:" comment the row is
# `computed_uncited_convention`, never silently upgraded.

# `timings.compute_hora`'s own docstring: "Source: VS; Hora Sara (Prithuyashas)."
# `shastra_tables.py` §11's HORA_CYCLE/VARA_HORA_START header carries the same.
HORA_CITATION = (
    "panchang_engine.timings.compute_hora — 24 planetary hours over the "
    "sunrise→next-sunrise cycle, Chaldean sequence (shastra_tables.HORA_CYCLE: "
    "Saturn→Jupiter→Mars→Sun→Venus→Mercury→Moon), first hora lord = the vāra "
    "lord (shastra_tables.VARA_HORA_START). Source (inline, both in "
    "timings.compute_hora's docstring and shastra_tables §11's own header "
    "comment): Viṣṇu Smṛti; Horā Sāra (Pṛthuyaśas).",
    "computed_cited",
)

# `shastra_tables.py` §7's VARA_NAMES header: "Source: VS; MC §1."
VARA_CITATION = (
    "panchang_engine.angas.compute_vara + shastra_tables.VARA_NAMES (1=Ravivāra "
    "… 7=Śanivāra, sunrise-to-sunrise Hindu-day convention). Source (inline, "
    "shastra_tables §7 header): Viṣṇu Smṛti; Muhūrta Chintāmaṇi §1.",
    "computed_cited",
)

# `shastra_tables.py` §2's NAKSHATRA_NAMES header: "Source: BS §2; MC §3."
NAKSHATRA_CITATION = (
    "panchang_engine.angas.compute_nakshatra (real boundary search over the "
    "Moon's sidereal longitude) + shastra_tables.NAKSHATRA_NAMES (1=Aśvinī … "
    "27=Revatī). Source (inline, shastra_tables §2 header): Bṛhat Saṃhitā §2; "
    "Muhūrta Chintāmaṇi §3.",
    "computed_cited",
)

# `shastra_tables.py` §1's TITHI_NAMES header: "Source: MC §1; BS §2."
TITHI_CITATION = (
    "panchang_engine.angas.compute_tithi (real bisection over Moon−Sun sidereal "
    "separation) + shastra_tables.TITHI_NAMES (1..15 Śukla, 16..30 Kṛṣṇa). "
    "Source (inline, shastra_tables §1 header): Muhūrta Chintāmaṇi §1; Bṛhat "
    "Saṃhitā §2.",
    "computed_cited",
)

# `lagna.py` carries NO inline classical "Source:" comment — it is a swisseph
# Placidus-cusp computation. The RISING-SIGN identity it yields is astronomical,
# not doctrinal, and the sign→lord map it is joined with (shastra_tables §8
# SIGN_LORDS) IS cited ("Source: BS §1; Parasara Hora Shastra"). Disclosed as a
# convention rather than claiming a muhūrta-lagna verse this codebase does not
# hold: the classical muhūrta-lagna DOCTRINE (which lagnas suit which rite) is a
# separate corpus gap, registered in the factor census, not asserted here.
LAGNA_CITATION = (
    "panchang_engine.lagna.compute_lagna (swisseph Placidus cusps, sidereal "
    "Lahiri) — the rising-sign span is an astronomical quantity, computed by "
    "bisection on ascendant_sign_id, and carries no inline classical citation in "
    "source. The sign→lord map applied to it (shastra_tables §8 SIGN_LORDS) IS "
    "cited: Bṛhat Saṃhitā §1; Bṛhat Parāśara Horā Śāstra. The classical "
    "muhūrta-lagna DOCTRINE (which lagna suits which rite, lagna-śuddhi rules) "
    "is NOT held in this codebase at verse grain — registered as a corpus gap in "
    "bg_muhurta_factor_census (muhurta_lagna/lagna_shuddhi_rules), never "
    "invented here.",
    "computed_uncited_convention",
)

# Bisection tolerance for the lagna sign-boundary search: 1 second. The
# ascendant advances ~15'/minute, so a 1-second bracket is far finer than any
# consumer's resolution and terminates in ~17 halvings of a 2-hour bracket.
_LAGNA_BISECTION_TOLERANCE_SECONDS = 1.0
# Coarse scan step for detecting a rising-sign change. The fastest-rising sign
# at 20°N takes well over an hour; a 5-minute probe cannot skip a whole sign.
_LAGNA_COARSE_STEP_MINUTES = 5


def _slug(name: str) -> str:
    """Lowercase, underscore-joined factor_key form of a Sanskrit display name.
    Pure string transform of panchang_engine's OWN name — never a rename."""
    return "_".join(name.strip().lower().split())


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
    from panchang_engine.shastra_tables import VARA_HORA_START, VARA_NAMES
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

    # ══════════════════════════════════════════════════════════════════════════
    # W4 ruling R-1 families 5–9. See module docstring for the ID PROVENANCE
    # RAIL and the SPAN CONVENTION disclosure — both are load-bearing.
    # ══════════════════════════════════════════════════════════════════════════

    # ── Family 5: horā (24 planetary hours) ──────────────────────────────────
    # The ONE fixture constraint (`planet_state {body: Guru, in: {hora_lord}}`)
    # that had no atom before this. `detail.lord` is panchang_engine's own graha
    # name, taken from the Timing label it emits — not re-derived here.
    from panchang_engine.timings import compute_hora  # local import: mirrors this fn's style

    citation, corpus_status = HORA_CITATION
    horas = compute_hora(sunrise_utc, next_sunrise_utc, vara.id)
    for idx, t in enumerate(horas, start=1):
        # t.label is exactly "hora_<planet_lower>" (timings.compute_hora builds
        # it from HORA_CYCLE). Splitting it back out is a read of that table's
        # own value, not a name→id map.
        lord = t.label.split("_", 1)[1]
        rows.append(_Row(
            factor_family="hora",
            factor_key=t.label,
            start_utc=t.start_utc,
            end_utc=t.end_utc,
            detail={
                "lord": lord.capitalize(),
                "hora_index": idx,
                "vara_id": vara.id,
                "vara_lord": VARA_HORA_START[vara.id],
            },
            source_citation=citation, corpus_status=corpus_status,
        ))

    # ── Family 6: vāra (sunrise-to-sunrise weekday) ──────────────────────────
    citation, corpus_status = VARA_CITATION
    vara_info = VARA_NAMES[vara.id]
    rows.append(_Row(
        factor_family="vara",
        factor_key=_slug(vara.name),
        start_utc=sunrise_utc,
        end_utc=next_sunrise_utc,
        detail={
            # factor_id: the canonical VARA_NAMES key, read from
            # compute_vara(...).id — the SAME id space
            # bg_muhurta_activity_rules.factor_id (factor_type='vara') uses.
            "factor_id": vara.id,
            "name_sanskrit": vara_info["name_sanskrit"],
            "name_english": vara_info["name_english"],
            "lord": vara_info["lord"],
            "span_convention": "hindu_day_sunrise_to_next_sunrise",
        },
        source_citation=citation, corpus_status=corpus_status,
    ))

    # ── Family 7: nakṣatra (sunrise nakṣatra, Hindu-day span) ────────────────
    citation, corpus_status = NAKSHATRA_CITATION
    rows.append(_Row(
        factor_family="nakshatra",
        factor_key=_slug(nakshatra.name),
        start_utc=sunrise_utc,
        end_utc=next_sunrise_utc,
        detail={
            "factor_id": nakshatra.id,
            "name": nakshatra.name,
            # panchang_engine's OWN computed transition moment. Carried so the
            # sub-day boundary is disclosed rather than discarded by the
            # Hindu-day span convention above.
            "anga_true_end_utc": nakshatra.end_utc.isoformat(),
            "span_convention": "hindu_day_sunrise_to_next_sunrise_anga_at_sunrise",
        },
        source_citation=citation, corpus_status=corpus_status,
    ))

    # ── Family 8: tithi (sunrise tithi, Hindu-day span) ──────────────────────
    citation, corpus_status = TITHI_CITATION
    rows.append(_Row(
        factor_family="tithi",
        factor_key=_slug(tithi.name),
        start_utc=sunrise_utc,
        end_utc=next_sunrise_utc,
        detail={
            "factor_id": tithi.id,
            "name": tithi.name,
            # Pakṣa is a pure partition of the SAME id (1..15 Śukla, 16..30
            # Kṛṣṇa) documented in shastra_tables §1's own header — a restatement
            # of the id's meaning, not a new astrological constant.
            "paksha": "shukla" if tithi.id <= 15 else "krishna",
            "anga_true_end_utc": tithi.end_utc.isoformat(),
            "span_convention": "hindu_day_sunrise_to_next_sunrise_anga_at_sunrise",
        },
        source_citation=citation, corpus_status=corpus_status,
    ))

    # ── Family 9: lagna (registry item 7 — muhūrta-lagna substrate) ──────────
    citation, corpus_status = LAGNA_CITATION
    for span in compute_lagna_spans(sunrise_utc, next_sunrise_utc, planets):
        rows.append(_Row(
            factor_family="lagna",
            factor_key=_slug(span["sign_name"]),
            start_utc=span["start_utc"],
            end_utc=span["end_utc"],
            detail=span["detail"],
            source_citation=citation, corpus_status=corpus_status,
        ))

    return rows


# ── Family 9 helper: the rising-sign boundary search (item 7) ────────────────


def _ascendant_sign_id_at(instant_utc: datetime) -> int:
    """The sidereal rising sign (1..12) at `instant_utc`, via
    `panchang_engine.lagna.compute_lagna` at the fixed reference location.
    Pure; no DB. `compute_lagna` takes NAIVE LOCAL time, so the UTC instant is
    shifted by the reference tz offset and stripped of tzinfo here."""
    from panchang_engine.lagna import compute_lagna

    local_naive = (instant_utc + timedelta(minutes=REFERENCE_TZ_OFFSET_MINUTES)).replace(tzinfo=None)
    return compute_lagna(
        local_naive, REFERENCE_LAT, REFERENCE_LON, REFERENCE_TZ_OFFSET_MINUTES
    ).ascendant_sign_id


def _bisect_sign_change(lo: datetime, hi: datetime, sign_lo: int) -> datetime:
    """First instant in (lo, hi] at which the rising sign differs from `sign_lo`,
    to `_LAGNA_BISECTION_TOLERANCE_SECONDS`. Precondition: the sign at `hi`
    already differs from `sign_lo`. Real bisection — no interpolation, no
    assumed 2-hour sign length (which would be false away from the equator)."""
    while (hi - lo).total_seconds() > _LAGNA_BISECTION_TOLERANCE_SECONDS:
        mid = lo + (hi - lo) / 2
        if _ascendant_sign_id_at(mid) == sign_lo:
            lo = mid
        else:
            hi = mid
    # Truncate to whole seconds. The natural key is (family, key, start_utc), and
    # the SAME rounded instant is reused as the previous span's end AND the next
    # span's start, so spans stay exactly contiguous with no gap or overlap.
    return hi.replace(microsecond=0)


def compute_lagna_spans(
    sunrise_utc: datetime, next_sunrise_utc: datetime, planets: list[Any],
) -> list[dict[str, Any]]:
    """
    Registry item 7 substrate: the rising-sign spans covering
    `[sunrise_utc, next_sunrise_utc)` at the fixed reference location, each with
    the FACTS a query-time muhūrta-lagna strength check needs.

    Method: coarse probe at `_LAGNA_COARSE_STEP_MINUTES`, then real bisection on
    every detected change. Because the ascendant is strictly monotonic in time
    and the coarse step is far shorter than the shortest rising sign at this
    latitude, no sign can be skipped — the same completeness-by-construction
    property Elevation §9 Stage 1 requires of every family in this table.

    Each span's `detail` carries:
      sign_id / sign_name  — the rising sign (LagnaState.ascendant_sign_id/name)
      lord                 — shastra_tables.SIGN_LORDS[sign_id-1] (BS §1; BPHS)
      lord_sign_id         — the lagna lord's OWN sidereal sign at span start
      lord_retrograde      — the lagna lord's retrograde flag at span start
      graha_sign_ids       — {graha: sidereal sign_id} for all nine at span start
      graha_positions_at   — the instant those positions were read (span start)

    NO dignity verdict and NO aspect verdict is stored (§N.5): the exaltation/
    debilitation/moolatrikona/own-sign authority is `bg_dignity_reference` and
    the dṛṣṭi authority is BPHS Ch.26 (`brahma_constants special_aspect_*`).
    A verdict restated here would be a second copy that can drift from both.
    `planets` is the already-computed sunrise graha set, reused for the first
    span so the common case costs no extra ephemeris work.
    """
    from panchang_engine.planets import compute_all_grahas
    from panchang_engine.shastra_tables import SIGN_LORDS, SIGN_NAMES
    import swisseph as swe

    def _graha_sign_ids(
        instant_utc: datetime, precomputed: list[Any] | None = None,
    ) -> tuple[dict[str, int], list[Any]]:
        if precomputed is not None:
            ps = precomputed
        else:
            jd = swe.julday(
                instant_utc.year, instant_utc.month, instant_utc.day,
                instant_utc.hour + instant_utc.minute / 60.0 + instant_utc.second / 3600.0,
            )
            ps = compute_all_grahas(jd)
        # p.sign_id is PlanetState's OWN computed field — read, never re-derived
        # from the longitude here (§N.5: the upstream value is the authority).
        return {p.name: p.sign_id for p in ps}, ps

    spans: list[dict[str, Any]] = []
    cursor = sunrise_utc
    current_sign = _ascendant_sign_id_at(cursor)
    first = True

    while cursor < next_sunrise_utc:
        probe = min(cursor + timedelta(minutes=_LAGNA_COARSE_STEP_MINUTES), next_sunrise_utc)
        while probe < next_sunrise_utc and _ascendant_sign_id_at(probe) == current_sign:
            probe = min(probe + timedelta(minutes=_LAGNA_COARSE_STEP_MINUTES), next_sunrise_utc)

        if probe >= next_sunrise_utc and _ascendant_sign_id_at(next_sunrise_utc) == current_sign:
            span_end = next_sunrise_utc
            next_sign = None
        else:
            span_end = _bisect_sign_change(probe - timedelta(minutes=_LAGNA_COARSE_STEP_MINUTES), probe, current_sign)
            if span_end >= next_sunrise_utc:
                span_end = next_sunrise_utc
                next_sign = None
            else:
                next_sign = _ascendant_sign_id_at(span_end)

        sign_ids, planet_states = _graha_sign_ids(cursor, planets if first else None)
        lord = SIGN_LORDS[current_sign - 1]
        lord_state = next((p for p in planet_states if p.name == lord), None)
        spans.append({
            "sign_name": SIGN_NAMES[current_sign - 1],
            "start_utc": cursor,
            "end_utc": span_end,
            "detail": {
                "sign_id": current_sign,
                "sign_name": SIGN_NAMES[current_sign - 1],
                "lord": lord,
                "lord_sign_id": sign_ids.get(lord),
                "lord_retrograde": bool(getattr(lord_state, "retrograde", False)) if lord_state else None,
                "graha_sign_ids": sign_ids,
                "graha_positions_at": cursor.isoformat(),
                "strength_verdict": None,
                "strength_verdict_note": (
                    "Deliberately null (§N.5). Dignity is resolved at query time against "
                    "bg_dignity_reference (exaltation/debilitation/moolatrikona/own_signs, "
                    "BPHS-cited) and dṛṣṭi against BPHS Ch.26; a verdict stored here would "
                    "be a second copy of those authorities and could drift from them."
                ),
            },
        })

        if span_end >= next_sunrise_utc or next_sign is None:
            break
        cursor = span_end
        current_sign = next_sign
        first = False

    return spans


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
