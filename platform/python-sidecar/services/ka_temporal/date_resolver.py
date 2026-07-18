"""ka_temporal.date_resolver — deterministic predicate→date resolution (WP-2.1 / R-45).

ROOT CAUSE this module fixes (LANE0, R-45 + R-39 + R-40 + F-L10-018):
    The L3 activation writer (ka_kalasutra) and the obstruction writer
    (ka_vighnakara) previously derived every temporal column from a SINGLE
    anchor: `kala_convergence.peak_date`. When a predicate signal had no
    matching convergence window (the common case — convergence covers only a
    small fraction of signals), the activation row was emitted with NULL
    `activation_start/end/peak`, an EMPTY `activation_predicted_dates_jsonb`
    fallback, and a `dasha_activation_proximity_score` of 0.5. On the native
    chart that produced 0/13,364 dated rows → the (correct) serving query
    excluded 100% of activations. A naive rebuild could not fix it because the
    convergence table simply does not carry a peak for most signals.

THE FIX (deterministic, B.10-clean — no fabricated dates):
    Resolve each activation predicate against the chart's L1 Vimśottarī daśā
    timeline (`chart_dashas`, authored by ga_dashas). The predicate's
    `dasha_eligibility_rule.constituent_lords` name the grahā(s) whose daśā
    activates the signal; intersecting those lords with the real MD/AD periods
    in `chart_dashas` yields concrete, L1-sourced start/end windows. The
    convergence peak, when present, still refines the bounded window; when
    absent, the daśā period IS the bounded window. Every emitted date traces to
    an L1 `chart_dashas` row (§N.5 — L3 references L1, never invents).

REUSE CONTRACT (for WP-2.3-temporal — CGM edge `active_dasha_periods_jsonb`):
    The CGM-edge lane shares exactly this resolution. It should:
      1. `timeline = load_dasha_timeline(conn, chart_id)`  (once per chart)
      2. per edge, build a `dasha_rule`-shaped dict whose `constituent_lords`
         are the edge's two graha endpoints (+ any dispositors), then call
         `windows = resolve_activation_windows(dasha_rule, timeline)`
      3. write `windows.active_dasha_periods` into the edge's
         `active_dasha_periods_jsonb` column.
    The helper is pure (no DB, no I/O) apart from `load_dasha_timeline`, so it
    is trivially unit-testable and identical across both consumers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional, Sequence

import logging

logger = logging.getLogger(__name__)


# ── Graha-name normalization ──────────────────────────────────────────────────
# chart_dashas.lord_graha stores English full names ("Sun", "Saturn", "Ketu").
# Predicate constituent_lords come from L2 configuration_jsonb and may arrive as
# full names, 2-letter codes, or lowercase. Normalize both sides to a canonical
# English full name so the intersection is robust.
_GRAHA_CANON: dict[str, str] = {}
_GRAHA_ALIASES: dict[str, list[str]] = {
    "Sun":     ["su", "sun", "surya", "ravi"],
    "Moon":    ["mo", "moo", "chandra", "soma"],
    "Mars":    ["ma", "mar", "mangala", "kuja", "angaraka"],
    "Mercury": ["me", "mer", "budha"],
    "Jupiter": ["ju", "jup", "guru", "brihaspati", "brhaspati"],
    "Venus":   ["ve", "ven", "shukra", "sukra"],
    "Saturn":  ["sa", "sat", "shani", "sani"],
    "Rahu":    ["ra", "rah", "north_node", "true_node"],
    "Ketu":    ["ke", "ket", "south_node"],
}

# Rāśi lordship (fixed classical doctrine — deterministic, not fabricated).
# A sign-based signal (e.g. a jaimini rāśi aspect) activates in the daśā of the
# sign's lord. Used by extract_lords_from_config for sign-valued keys.
_SIGN_LORD: dict[str, str] = {
    "aries": "Mars", "taurus": "Venus", "gemini": "Mercury", "cancer": "Moon",
    "leo": "Sun", "virgo": "Mercury", "libra": "Venus", "scorpio": "Mars",
    "sagittarius": "Jupiter", "capricorn": "Saturn", "aquarius": "Saturn",
    "pisces": "Jupiter",
}

# Config keys whose VALUE is a graha name / code.
_GRAHA_VALUE_KEYS = (
    "graha", "planet", "lord", "primary_graha", "planet_a", "planet_b",
    "bhava_lord", "sign_lord", "dasha_lord", "significator", "lord_graha",
    "prana_lord", "sub_lord", "star_lord", "fact_value_text",
)
# Config keys whose VALUE is a sign name (→ resolve to that sign's rāśi lord).
_SIGN_VALUE_KEYS = (
    "sign", "source_sign", "target_sign", "sign_a", "sign_b", "bhava_sign",
    "rasi", "rashi", "d1_sign", "varga_sign",
)
for _canon, _aliases in _GRAHA_ALIASES.items():
    _GRAHA_CANON[_canon.lower()] = _canon
    for _a in _aliases:
        _GRAHA_CANON[_a.lower()] = _canon


def normalize_graha(name) -> Optional[str]:
    """Return the canonical English graha name for any known spelling/alias.

    Returns None for empty / unrecognized input (so callers can skip cleanly
    rather than match a bogus lord).
    """
    if not name:
        return None
    return _GRAHA_CANON.get(str(name).strip().lower())


_TEXT_TOKEN_RE = None  # lazily compiled


def extract_lords_from_text(text) -> list[str]:
    """WP-S4-R45-iter2: best-effort DETERMINISTIC lord extraction from a
    free-form identifier string — specifically `chart_facts.fact_subject`
    (e.g. "D20_SUN_MER" for a sambandha_grade cell, "Mars_in_H7" for a
    lord_placement row). Tokenizes on non-alpha boundaries and normalizes
    each token via `normalize_graha`; house/varga tokens ("D20", "H7") never
    match because `normalize_graha` only recognizes graha names/codes/aliases
    via an exact (not substring) lookup. Returns de-duped canonical names in
    order of first appearance; [] when nothing recognizable is present.

    This is the LAST-RESORT fallback in the ka_yojaka lord-resolution chain
    (config keys -> house/varga bhava-lord lookup -> this), used only when a
    signal's `configuration_jsonb` carries no graha/sign-valued key at all but
    its `constituent_facts_array[0]` resolves to an L1 `chart_facts` row whose
    `fact_subject` names the graha(s) involved (§N.5 — still an L1 reference,
    never a fabrication).
    """
    global _TEXT_TOKEN_RE
    if not text:
        return []
    if _TEXT_TOKEN_RE is None:
        import re
        _TEXT_TOKEN_RE = re.compile(r"[A-Za-z]+")
    out: list[str] = []
    for tok in _TEXT_TOKEN_RE.findall(str(text)):
        g = normalize_graha(tok)
        if g and g not in out:
            out.append(g)
    return out


def lord_from_house_varga(
    house_lord_map: dict,
    ayanamsha_id: Optional[str],
    varga: Optional[str],
    house,
) -> Optional[str]:
    """WP-S4-R45-iter2: resolve a (varga, house) pair to its bhava lord using a
    prebuilt map from `chart_facts` (fact_category='lord_in_house_per_varga').
    Pure — the map itself is fetched once per chart by the caller (I/O stays
    in the writer, per this module's existing contract). `house` may be an int
    or a numeric string; returns None if the map has no entry (e.g. an
    unrecognized varga id) — no fabrication.

    `house_lord_map` keys are `(ayanamsha_id, "{varga}_H{house}")` ->
    canonical lord name, built by the caller from rows shaped like
    fact_subject="D9_H1", fact_value_text="Mars_in_H12" (lord of D9-H1 is
    Mars; parsed by the caller, not here).
    """
    if not varga or house is None or ayanamsha_id is None:
        return None
    try:
        house_int = int(house)
    except (TypeError, ValueError):
        return None
    key = (ayanamsha_id, f"{varga}_H{house_int}")
    return house_lord_map.get(key)


def sign_lord(sign) -> Optional[str]:
    """Return the canonical rāśi lord for a sign name, or None if unrecognized."""
    if not sign:
        return None
    return _SIGN_LORD.get(str(sign).strip().lower())


_ON_SIGN_RE = None  # lazily compiled


def extract_lords_from_config(
    config,
    signal_type_id: Optional[str] = None,
    signal_type_class: Optional[str] = None,
) -> list[str]:
    """Best-effort, DETERMINISTIC extraction of the grahā(s) whose daśā activates
    a signal, from its L2 `configuration_jsonb` (+ signal_type_id / class).

    This is the WP-2.1 fix for the real root cause: ka_yojaka's ratified binder
    only set concrete `constituent_lords` for the YOGA class, leaving ~99% of
    predicates with no lord to resolve a daśā against. Sources, in order:

      1. graha-valued keys (planet, lord, bhava_lord code, planet_a/b, …)
      2. sign-valued keys (source_sign / target_sign / sign_a/b / …) → rāśi lord
      3. `on_<Sign>` embedded in signal_type_id → rāśi lord
      4. class shortcut: sade_sati / dhaiyā signals are Saturn (by definition)

    Every mapping is fixed classical doctrine (graha names, rāśi lordship) — no
    fabrication, no LLM. Returns a de-duped canonical-name list (possibly empty).
    """
    global _ON_SIGN_RE
    if isinstance(config, str):
        import json as _json
        try:
            config = _json.loads(config)
        except Exception:
            config = {}
    config = config or {}
    out: list[str] = []

    def _add(g: Optional[str]):
        if g and g not in out:
            out.append(g)

    # 1. graha-valued keys
    for key in _GRAHA_VALUE_KEYS:
        val = config.get(key)
        if isinstance(val, list):
            for v in val:
                _add(normalize_graha(v))
        elif val is not None:
            _add(normalize_graha(val))

    # 2. sign-valued keys → rāśi lord
    for key in _SIGN_VALUE_KEYS:
        _add(sign_lord(config.get(key)))

    # 3. on_<Sign> in signal_type_id
    if signal_type_id:
        if _ON_SIGN_RE is None:
            import re
            _ON_SIGN_RE = re.compile(
                r"on_(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|"
                r"Sagittarius|Capricorn|Aquarius|Pisces)", re.IGNORECASE
            )
        for m in _ON_SIGN_RE.findall(signal_type_id):
            _add(sign_lord(m))

    # 4. class shortcut: Śani sāḍe-sātī / dhaiyā are Saturn by definition
    cls = (signal_type_class or "").lower()
    if "sade_sati" in cls or "sadesati" in cls or "dhaiya" in cls or "dhaiyā" in cls:
        _add("Saturn")

    return out


# ── Data contracts ────────────────────────────────────────────────────────────
@dataclass
class DashaPeriod:
    """One L1 dasha period (from chart_dashas). Dates are real `date` objects."""
    lord: str            # canonical graha name (already normalized on load)
    level_n: int         # 1 = mahadasha (MD), 2 = antardasha (AD), ...
    start: date
    end: date


@dataclass
class ActivationWindows:
    """Resolved temporal columns for one activation predicate.

    active_dasha_periods : list of dicts for active_dasha_periods_jsonb
    predicted_dates      : list of dicts for activation_predicted_dates_jsonb
    activation_start/end : bounded DATE window (None only when NOTHING resolves).
        Kept for backward compatibility — this is the single PRIMARY window
        (current > soonest-future > most-recent-past) — same selection as before
        CR-109. Existing single-window consumers (ka_vighnakara's anchor scan,
        the CGM-edge lane) are unaffected by the CR-109 addition below.
    activation_peak      : representative peak DATE (primary window's peak)
    proximity_score      : [0,1] dasha_activation_proximity_score (primary window)
    resolution_source    : 'convergence' | 'dasha_timeline' | 'none' (primary window)
    period_windows       : CR-109 fix (D-4a Lane A-0). One entry per matched
        in-life dasha period (birth-forward, capped at max_windows) — NOT
        collapsed to the single primary. Each entry:
        {start, end, peak, graha, level, proximity_score, resolution_source}.
        Same peak/proximity FORMULAS as the primary window above (zero
        kernel/weight change) — applied per period instead of once, so a
        writer can serve every period the dasha table holds instead of
        silently collapsing coverage to one bounded band. Always non-empty
        whenever activation_start is non-None (falls back to a single entry
        mirroring the primary window when `matched` is empty but a bare
        convergence peak still resolved).
    """
    active_dasha_periods: list = field(default_factory=list)
    predicted_dates: list = field(default_factory=list)
    activation_start: Optional[date] = None
    activation_end: Optional[date] = None
    activation_peak: Optional[date] = None
    proximity_score: float = 0.5
    resolution_source: str = "none"
    period_windows: list = field(default_factory=list)


# ── DB load (the only I/O in this module) ─────────────────────────────────────
# Canonical default ayanamsha. chart_dashas pools all 5 ayanamshas (~9,200 MD/AD
# rows each) spanning ~1949→2100. Loading without an ayanamsha filter mixes
# systems; loading without a birth-forward bound admits pre-birth cycles (the
# native's earliest AD of every graha is 1949–1955, 30+ years before birth).
_DEFAULT_AYANAMSHA = "lahiri_chitrapaksha"


def resolve_birth_date(conn, chart_id, birth_params=None) -> Optional[date]:
    """Deterministic native birth date. Prefers ctx.config['birth_params']
    ['datetime_iso']; falls back to charts.birth_date. No fabrication — returns
    None if neither source yields a date (caller then skips the birth clip).
    """
    if isinstance(birth_params, dict):
        iso = birth_params.get("datetime_iso") or birth_params.get("date_of_birth")
        if iso:
            try:
                from datetime import datetime as _dt
                return _dt.fromisoformat(str(iso)).date()
            except ValueError:
                pass
    if conn is not None:
        try:
            import psycopg
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT birth_date FROM charts WHERE chart_id = %s",
                    (str(chart_id),),
                )
                row = cur.fetchone()
            if row and row.get("birth_date"):
                bd = row["birth_date"]
                return date.fromisoformat(bd) if isinstance(bd, str) else bd
        except Exception as exc:
            logger.debug("resolve_birth_date: charts fallback failed: %s", exc)
    return None


def load_dasha_timeline(
    conn,
    chart_id,
    *,
    system_id: str = "vimshottari",
    ayanamsha_id: str = _DEFAULT_AYANAMSHA,
    max_level: int = 2,
    birth_date: Optional[date] = None,
) -> list[DashaPeriod]:
    """Load the chart's dasha timeline (MD + AD by default) from chart_dashas,
    scoped to ONE ayanamsha and (when birth_date is given) BIRTH-FORWARD.

    - `ayanamsha_id` — REQUIRED scoping. chart_dashas pools 5 ayanamshas; a
      predicate must resolve against periods computed under its OWN ayanamsha.
    - `birth_date` — when provided, periods that END before birth are excluded
      (they are theoretical pre-birth cycles, not life-indexable). A period that
      straddles birth is kept; the caller clips its start to birth.

    Read-only, explicit dict_row cursor. Rows with null lord/dates are skipped.
    Returns [] if nothing matches (caller degrades to convergence-only).
    """
    import psycopg

    sql = """
        SELECT lord_graha, level_n, start_date, end_date
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s
          AND level_n <= %s
          AND start_date IS NOT NULL AND end_date IS NOT NULL
    """
    params: list = [str(chart_id), system_id, ayanamsha_id, max_level]
    if birth_date is not None:
        sql += " AND end_date >= %s"
        params.append(birth_date)
    sql += " ORDER BY level_n, start_date"

    periods: list[DashaPeriod] = []
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(sql, tuple(params))
        for row in cur.fetchall():
            lord = normalize_graha(row["lord_graha"])
            if lord is None:
                continue
            ds, de = row["start_date"], row["end_date"]
            if isinstance(ds, str):
                ds = date.fromisoformat(ds)
            if isinstance(de, str):
                de = date.fromisoformat(de)
            if ds is None or de is None or de < ds:
                continue
            periods.append(DashaPeriod(lord=lord, level_n=int(row["level_n"]), start=ds, end=de))
    return periods


# ── Core resolution (pure) ────────────────────────────────────────────────────
_SIG_CLASS_HALFWIDTH_DAYS: dict[str, int] = {
    "YOGA": 7,
    "DOSHA": 14,
    "DIGNITY": 5,
    "SENSITIVE_POINT": 5,
}
_DEFAULT_HALFWIDTH_DAYS = 5


def _extract_constituent_lords(dasha_rule: Optional[dict]) -> list[str]:
    """Normalized, de-duped list of constituent lords from a dasha rule dict."""
    if not dasha_rule:
        return []
    raw = dasha_rule.get("constituent_lords") or []
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for r in raw:
        canon = normalize_graha(r)
        if canon and canon not in out:
            out.append(canon)
    return out


def _midpoint(start: date, end: date) -> date:
    return start + timedelta(days=(end - start).days // 2)


def resolve_activation_windows(
    dasha_rule: Optional[dict],
    dasha_timeline: Sequence[DashaPeriod],
    *,
    transit_rule: Optional[dict] = None,
    strength_hook: Optional[dict] = None,
    convergence_peak: Optional[date] = None,
    signature_class: Optional[str] = None,
    birth_date: Optional[date] = None,
    max_windows: int = 8,
    as_of_date: Optional[date] = None,
) -> ActivationWindows:
    """Resolve one predicate into concrete, LIFE-INDEXED activation date windows.

    Parameters
    ----------
    dasha_rule : the predicate's `dasha_eligibility_rule_jsonb` (dict). Its
        `constituent_lords` drive the dasha-period match. May also carry an
        explicit `periods` list (preserved verbatim) and a `dignity_score`.
    dasha_timeline : output of `load_dasha_timeline` — the chart's real MD/AD
        periods for the predicate's ayanamsha, ideally already birth-forward.
        This is the deterministic date source (L1 authority, §N.5).
    transit_rule : optional `transit_trigger_jsonb`; only its `type` is recorded
        as the `trigger` label on emitted predicted dates (no fabrication).
    strength_hook : optional `strength_affliction_hook_jsonb`; supplies
        `non_affliction` for the proximity score.
    convergence_peak : optional peak DATE from kala_convergence. When present it
        REFINES the bounded window (peak ± signature-class half-width).
    signature_class : YOGA / DOSHA / DIGNITY / … — sets the window half-width.
    birth_date : the native's birth date. Belt-and-suspenders life-indexing —
        periods ending before birth are dropped and every emitted start/peak/end
        is clipped to >= birth_date, so no window falls in a pre-birth cycle even
        if the timeline was loaded without a birth bound.
    max_windows : cap on emitted dasha periods / date clusters (row-size guard).
    as_of_date : WP-S4-fix2 (Gate Ś #8/#9 root cause). Defaults to `date.today()` when
        not supplied. Drives WHICH in-life matched period becomes the PRIMARY bounded
        window when no convergence peak exists: a period straddling `as_of_date` wins,
        else the soonest period starting after it, else (only when every matched period
        has already elapsed — no current or future occurrence for any constituent lord)
        the most recently-ended past period. Before this fix the primary was always
        `matched[0]` — the chronologically EARLIEST in-life period, which for a chart
        with 40+ years already elapsed is almost always a long-past period, so
        forward-looking callers (get_temporal_windows' default 1yr-forward window,
        yoga_activation_by_dasha's 2026-2029 window) saw zero coverage even though the
        lord-resolution mechanism (R-45) and the underlying chart_dashas rows were both
        correct. This does not change the FULL matched-period listing (still every
        in-life period, birth-forward) — only which one is elevated to the single
        bounded activation_start/end/peak window.

    Returns
    -------
    ActivationWindows — populated when a convergence peak exists OR a constituent
    lord resolves to an IN-LIFE dasha period. All-None dates only when nothing
    resolves in-life.
    """
    lords = set(_extract_constituent_lords(dasha_rule))

    # Matched real dasha periods, birth-forward (drop periods that end before birth).
    matched_all = [p for p in dasha_timeline if p.lord in lords]
    if birth_date is not None:
        matched_all = [p for p in matched_all if p.end >= birth_date]

    # WP-S4-fix2: select the temporally-relevant PRIMARY period before truncating the
    # listing, so a period selected for the bounded activation_start/end/peak window is
    # never accidentally cut by the max_windows row-size guard below.
    today = as_of_date if as_of_date is not None else date.today()
    primary_selected: Optional[DashaPeriod] = None
    if matched_all:
        current_tier = [p for p in matched_all if p.start <= today <= p.end]
        future_tier = [p for p in matched_all if p.start > today]
        if current_tier:
            # Finest level (AD tighter than MD), then earliest start (tightest window).
            current_tier.sort(key=lambda p: (-p.level_n, p.start))
            primary_selected = current_tier[0]
        elif future_tier:
            # Finest level, then SOONEST upcoming start — the next occurrence in time,
            # not the earliest-ever (which is what the old matched[0] bug picked).
            future_tier.sort(key=lambda p: (-p.level_n, p.start))
            primary_selected = future_tier[0]
        else:
            # Nothing current or future for any constituent lord — every matched period
            # has already elapsed. Fall back to the most recently-ended past period
            # (closest to "now" is still more relevant than the earliest-ever).
            past_tier = sorted(matched_all, key=lambda p: (p.end, -p.level_n), reverse=True)
            primary_selected = past_tier[0]

    # Listing order for active_dasha_periods_jsonb / _dasha_period_dates: finest level
    # first, then chronological — same ordering as before this fix — but with the
    # selected primary period always guaranteed a slot ahead of the max_windows cut.
    matched = sorted(matched_all, key=lambda p: (-p.level_n, p.start))
    if primary_selected is not None and primary_selected not in matched[:max_windows]:
        matched = [primary_selected] + [p for p in matched if p is not primary_selected]
    matched = matched[:max_windows]

    def _clip(d: Optional[date]) -> Optional[date]:
        if d is None:
            return None
        return max(d, birth_date) if birth_date is not None else d

    result = ActivationWindows()

    # active_dasha_periods_jsonb — real, dated, in-life periods (start clipped to
    # birth for a straddling period — the EXPERIENCED portion, per ka_jivana_parva
    # doctrine), plus explicit rule periods, plus lord-only entries with no
    # timeline coverage (backward-compatible provenance).
    level_name = {1: "mahadasha", 2: "antardasha", 3: "pratyantardasha"}
    for p in matched:
        clipped_start = _clip(p.start)
        entry = {
            "graha": p.lord,
            "level": level_name.get(p.level_n, f"level_{p.level_n}"),
            "start": clipped_start.isoformat(),
            "end": p.end.isoformat(),
            "match_kind": "exact_lord",
            "source": "chart_dashas",
        }
        if birth_date is not None and p.start < birth_date:
            entry["clipped_to_birth"] = True
        result.active_dasha_periods.append(entry)
    if dasha_rule:
        explicit = dasha_rule.get("periods") or []
        if isinstance(explicit, list):
            result.active_dasha_periods.extend(explicit)
    matched_lords = {p.lord for p in matched}
    for lord in lords - matched_lords:
        result.active_dasha_periods.append({
            "graha": lord,
            "level": "mahadasha",
            "source": "dasha_eligibility_rule",
            "match_kind": "lord_only_no_timeline",
        })

    # Bounded window + peak.
    half = _SIG_CLASS_HALFWIDTH_DAYS.get(signature_class or "", _DEFAULT_HALFWIDTH_DAYS)
    if convergence_peak is not None and (birth_date is None or convergence_peak >= birth_date):
        peak = convergence_peak
        result.activation_peak = peak
        result.activation_start = _clip(peak - timedelta(days=half))
        result.activation_end = peak + timedelta(days=half)
        result.resolution_source = "convergence"
        result.predicted_dates = _peak_cluster_dates(peak, transit_rule, birth_date)
    elif matched:
        # WP-S4-fix2: primary_selected (current > soonest-future > most-recent-past,
        # computed above) — NOT matched[0]/earliest-ever. Falls back to matched[0] only
        # if selection somehow didn't run (defensive; primary_selected is always set
        # when matched_all is non-empty, and matched is a superset-preserving reorder).
        primary = primary_selected if primary_selected is not None else matched[0]
        start = _clip(primary.start)
        end = primary.end
        result.activation_start = start
        result.activation_end = end
        result.activation_peak = _midpoint(start, end)
        result.resolution_source = "dasha_timeline"
        result.predicted_dates = _dasha_period_dates(matched, transit_rule, max_windows, birth_date)
    else:
        # Nothing resolves in-life — leave dates None (no temporal anchor).
        result.resolution_source = "none"

    result.proximity_score = _proximity_score(dasha_rule, strength_hook, result.activation_peak)

    # CR-109 fix (D-4a Lane A-0): one bounded window PER matched in-life period,
    # not just the single primary. Same peak-refinement and proximity FORMULAS as
    # the primary window above (no kernel/weight/threshold change) — a convergence
    # peak still refines whichever period it actually falls inside; every other
    # matched period gets its own natural [start, end] bound with a midpoint peak.
    # This is what lets a writer serve >1 period per lord (full birth-forward
    # coverage) instead of collapsing to one build-time-relative band.
    for p in matched:
        p_start = _clip(p.start)
        p_end = p.end
        if (
            convergence_peak is not None
            and (birth_date is None or convergence_peak >= birth_date)
            and p_start is not None and p_start <= convergence_peak <= p_end
        ):
            p_peak = convergence_peak
            p_win_start = _clip(max(p_start, p_peak - timedelta(days=half)))
            p_win_end = min(p_end, p_peak + timedelta(days=half))
            p_source = "convergence"
        else:
            p_peak = _midpoint(p_start, p_end) if p_start is not None else None
            p_win_start = p_start
            p_win_end = p_end
            p_source = "dasha_timeline"
        result.period_windows.append({
            "start": p_win_start,
            "end": p_win_end,
            "peak": p_peak,
            "graha": p.lord,
            "level": level_name.get(p.level_n, f"level_{p.level_n}"),
            "proximity_score": _proximity_score(dasha_rule, strength_hook, p_peak),
            "resolution_source": p_source,
        })

    if not result.period_windows and result.activation_start is not None:
        # No real matched period (pure convergence-only resolution, e.g. a signal
        # with no constituent_lords timeline coverage at all) — mirror the primary
        # window as the sole entry so a caller can always iterate period_windows
        # rather than special-casing an empty list.
        result.period_windows.append({
            "start": result.activation_start,
            "end": result.activation_end,
            "peak": result.activation_peak,
            "graha": None,
            "level": None,
            "proximity_score": result.proximity_score,
            "resolution_source": result.resolution_source,
        })

    return result


def _peak_cluster_dates(peak: date, transit_rule: Optional[dict],
                        birth_date: Optional[date] = None) -> list:
    """Convergence path: peak ± 3 days, strength decaying outward. Any point that
    would fall before birth is dropped (life-indexed)."""
    trigger = (transit_rule or {}).get("type", "unknown")
    out = []
    for delta in range(-3, 4):
        d = peak + timedelta(days=delta)
        if birth_date is not None and d < birth_date:
            continue
        out.append({
            "date": d.isoformat(),
            "strength": round(max(0.0, 1.0 - abs(delta) * 0.2), 3),
            "trigger": trigger,
            "source": "convergence_peak",
        })
    return out


def _dasha_period_dates(
    matched: Sequence[DashaPeriod],
    transit_rule: Optional[dict],
    max_windows: int,
    birth_date: Optional[date] = None,
) -> list:
    """Fallback path: representative dates (start / midpoint / end) per matched
    dasha period. This is what makes `activation_predicted_dates_jsonb` non-empty
    for the ~99% of signals that have no convergence peak. Every date is a real
    chart_dashas boundary (deterministic, L1-sourced), clipped in-life: a period
    straddling birth contributes its EXPERIENCED portion (start := birth)."""
    trigger = (transit_rule or {}).get("type", "dasha_period")
    out = []
    for p in matched[:max_windows]:
        start = max(p.start, birth_date) if birth_date is not None else p.start
        if start > p.end:
            continue
        mid = _midpoint(start, p.end)
        for d, strength, kind in (
            (start, 0.6, "period_start"),
            (mid, 1.0, "period_peak"),
            (p.end, 0.4, "period_end"),
        ):
            out.append({
                "date": d.isoformat(),
                "strength": strength,
                "trigger": trigger,
                "graha": p.lord,
                "level": p.level_n,
                "point_kind": kind,
                "source": "dasha_timeline",
            })
    return out


def _proximity_score(
    dasha_rule: Optional[dict],
    strength_hook: Optional[dict],
    peak: Optional[date],
) -> float:
    """dasha_activation_proximity_score in [0,1]. 0.5 only when no peak resolves
    at all; otherwise dignity × non-affliction (matches the legacy proxy)."""
    if peak is None:
        return 0.5
    dignity = (dasha_rule or {}).get(
        "dignity_score", (strength_hook or {}).get("dignity_score", 0.5)
    )
    non_affliction = (strength_hook or {}).get("non_affliction", 1.0)
    try:
        return min(1.0, max(0.0, float(dignity) * float(non_affliction)))
    except (TypeError, ValueError):
        return 0.5
