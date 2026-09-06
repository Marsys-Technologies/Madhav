"""
services.kala_trigger.trigger — L3 Kāla TRIGGER lock (Doctrine-Waves D-3, lane T-5).

Headline deliverable: SIGNED SUPPRESSIVE currents that can SUBTRACT from a
window's net activation — genuine destructive interference, which
`services.ka_sangam.engine` (T-3/prior waves' "12 currents") cannot express:
every current in `ka_sangam.engine.SUPPORTING_WEIGHTS` is additive/saturating,
and `services.ka_sangam.engine._c11_vedha_factor` is a NECESSARY-side
multiplicative veto (0..1), never negative. This module is the first place
in the L3 stack a current can push a score DOWN below what the additive
terms alone would produce (CR-89).

Composition contract for the caller (T-6, serving-layer wiring):

    trig = compute_trigger_currents(chart_id=..., ...)
    net  = compose_with_ka_sangam(ka_sangam_convergence_score, trig)
    # net = clamp01(ka_sangam_convergence_score + trig['suppressive'])

`trig['suppressive']` is always <= 0.0. `trig['additive']` carries this
module's OWN new additive currents (guru_shani_double_transit, saham
activation) — currents that do not exist in `ka_sangam.SUPPORTING_WEIGHTS`
and are therefore NOT already counted in `ka_sangam_convergence_score`. They
are kept separate from `suppressive` so a caller can choose whether to fold
them into ka_sangam's saturating-sum machinery (T-6's call) or use them
standalone; `compute_trigger_currents` also reports `net` for this module's
own scope (`additive + suppressive`, unclamped) for direct testing.

READ-ONLY reuse (imports only, zero writes, zero modification):
  - services.ka_sangam.engine — orb_strength_score, HIGH_CONFIDENCE_ORB_THRESHOLD.
  - chart_facts saham_position rows written by ga_writers/ga_sensitive_writer.py
    (read via fetch_saham_facts — a plain SELECT with SAVEPOINT guard, no
    writes, mirroring the read pattern in
    pipeline/orchestrator/writers/ka_sangam.py::_build_enrichment_context).

`vedha_rules`/`vedha_planet` parameters on `compute_trigger_currents` are
accepted but currently unused (F-SANGAM-5, L3-W3, removed this module's own
vedha-filter-gap diagnostic — see that function's docstring) — kept on the
signature rather than removed, to avoid rippling a signature change out to
`apply_trigger_suppression`'s own caller in ka_sangam.py.

NEVER calls conn.commit()/rollback() — the one DB-reading helper here
(`fetch_saham_facts`) only ever issues a SAVEPOINT-guarded SELECT; the caller
(a future writer, if T-6 wraps this in one) owns the transaction exactly per
the FROZEN orchestrator contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2).
This module registers no `@register` writer itself — it is a pure service
layer, imported by a writer, not a writer.

CR-87: every entry point that could resolve to a specific chart REQUIRES
chart_id explicitly. No module-level chart_id/nakshatra/location constants.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from services.ka_sangam.engine import (
    HIGH_CONFIDENCE_ORB_THRESHOLD,
    orb_strength_score,
)

logger = logging.getLogger(__name__)

# ── Malefic aspect weighting (suppressive side) ───────────────────────────────
# Classical: conjunction and square are the most afflictive angular relations
# for a malefic; opposition next; trine/sextile weakest (still counted, since
# even a "soft" angle from Saturn/Mars/Rahu/Ketu carries some drag — this is
# NOT the benefic-dristi table in ka_sangam.engine, which is intentionally
# different because malefic affliction does not favor trine the way benefic
# grace does).
_MALEFIC_ASPECT_WEIGHT: dict[int, float] = {0: 1.0, 90: 0.8, 180: 0.6, 60: 0.3, 120: 0.3}
_MALEFICS: tuple[str, ...] = ("Saturn", "Mars", "Rahu", "Ketu")


# ── T-5.1: malefic transit over the (D-2) Mechanism — suppressive ────────────

def _malefic_transit_over_mechanism(
    mechanism_lon: Optional[float],
    gochara_service: Any,
    w_jd_start: Optional[float],
    w_jd_end: Optional[float],
    orb_deg: float = 5.0,
) -> float:
    """
    Max orb-strength × aspect-weight across Saturn/Mars/Rahu/Ketu aspecting
    the Mechanism's activation longitude within the window. 0.0 if no data.
    Uses the same gochara_service.find_aspects(...) duck-type contract
    ka_sangam.engine._c_benefic_dristi already relies on (read-only reuse
    of the interface shape, not of the file itself).
    """
    if gochara_service is None or mechanism_lon is None or w_jd_start is None:
        return 0.0
    max_score = 0.0
    for mal in _MALEFICS:
        try:
            events = gochara_service.find_aspects(
                transit_planet=mal,
                target_lon=mechanism_lon,
                aspect_degrees=[0, 60, 90, 120, 180],
                orb=orb_deg,
                start_jd=w_jd_start,
                end_jd=w_jd_end,
            )
            for ev in events:
                orb_at = getattr(ev, "orb_at_event_deg", orb_deg)
                base = orb_strength_score(
                    orb_at, orb_deg, getattr(ev, "applying_separating", "applying")
                )
                extra = getattr(ev, "extra", None) or {}
                asp = int(round(abs(float(extra.get("aspect_deg", 0)))))
                weight = _MALEFIC_ASPECT_WEIGHT.get(asp, 0.3)
                max_score = max(max_score, base * weight)
        except Exception as exc:
            logger.debug("_malefic_transit_over_mechanism(%s) failed: %s", mal, exc)
    return min(1.0, max_score)


# ── T-5.1: papa-kartari sandwich (affliction sandwiching) — suppressive ──────

def _papa_kartari_sandwich(
    target_lon: Optional[float],
    gochara_service: Any,
    w_jd_start: Optional[float],
    w_jd_end: Optional[float],
    orb_deg: float = 8.0,
) -> float:
    """
    Classical papa-kartari yoga: a point is 'sandwiched' when malefics occupy
    BOTH the sign immediately before (12th) and immediately after (2nd) the
    target point's sign, concurrently. Neither malefic need touch the point
    itself — the affliction is structural (bracketing), which is exactly the
    destructive-interference case an additive-only model cannot represent:
    each malefic alone might even read as neutral/irrelevant to the point,
    yet the PAIR together classically damages it.

    Approximated via conjunction checks (aspect_degrees=[0]) to the sign
    centers 30° before / after target_lon — a real sign-occupancy check
    without needing a separate ephemeris position primitive.
    Returns 0.0 unless BOTH sides are hit within the window.
    """
    if gochara_service is None or target_lon is None or w_jd_start is None:
        return 0.0
    before_lon = (target_lon - 30.0) % 360.0
    after_lon = (target_lon + 30.0) % 360.0
    before_hit = 0.0
    after_hit = 0.0
    for mal in _MALEFICS:
        for lon, label in ((before_lon, "before"), (after_lon, "after")):
            try:
                events = gochara_service.find_aspects(
                    transit_planet=mal,
                    target_lon=lon,
                    aspect_degrees=[0],
                    orb=orb_deg,
                    start_jd=w_jd_start,
                    end_jd=w_jd_end,
                )
                for ev in events:
                    orb_at = getattr(ev, "orb_at_event_deg", orb_deg)
                    s = orb_strength_score(
                        orb_at, orb_deg, getattr(ev, "applying_separating", "applying")
                    )
                    if label == "before":
                        before_hit = max(before_hit, s)
                    else:
                        after_hit = max(after_hit, s)
            except Exception as exc:
                logger.debug("_papa_kartari_sandwich(%s/%s) failed: %s", mal, label, exc)
    if before_hit > 0.0 and after_hit > 0.0:
        return min(1.0, (before_hit + after_hit) / 2.0)
    return 0.0


# ── T-5.2: Guru-Śani (Jupiter+Saturn) double-transit — additive ──────────────

def guru_shani_double_transit(
    target_lon: Optional[float],
    gochara_service: Any,
    w_jd_start: Optional[float],
    w_jd_end: Optional[float],
    orb_deg: float = 5.0,
) -> dict[str, Any]:
    """
    GENERAL current (not Sade-Sati-specific, unlike
    ga_sade_sati_writer.py's `jupiter_aspect_to_saturn` which is
    Jupiter-aspects-Saturn only): fires when Jupiter AND Saturn are BOTH
    simultaneously aspecting/transiting a shared target longitude (a bhāva
    cusp or a lord's natal degree) within the window. Structurally borrows
    the aspect-detection call shape from ka_sangam.engine's benefic-dristi /
    Sade-Sati writer's aspect check (read-only pattern reuse, not code reuse).

    Returns {'score', 'jupiter_hit', 'saturn_hit', 'jupiter_orb_strength',
    'saturn_orb_strength'}. score is 0.0 unless BOTH planets hit.
    """
    hits: dict[str, float] = {"Jupiter": 0.0, "Saturn": 0.0}
    if gochara_service is not None and target_lon is not None and w_jd_start is not None:
        for planet in ("Jupiter", "Saturn"):
            try:
                events = gochara_service.find_aspects(
                    transit_planet=planet,
                    target_lon=target_lon,
                    aspect_degrees=[0, 60, 90, 120, 180],
                    orb=orb_deg,
                    start_jd=w_jd_start,
                    end_jd=w_jd_end,
                )
                best = 0.0
                for ev in events:
                    orb_at = getattr(ev, "orb_at_event_deg", orb_deg)
                    s = orb_strength_score(
                        orb_at, orb_deg, getattr(ev, "applying_separating", "applying")
                    )
                    if s >= HIGH_CONFIDENCE_ORB_THRESHOLD:
                        best = max(best, s)
                hits[planet] = best
            except Exception as exc:
                logger.debug("guru_shani_double_transit(%s) failed: %s", planet, exc)

    jupiter_hit = hits["Jupiter"] > 0.0
    saturn_hit = hits["Saturn"] > 0.0
    score = min(1.0, (hits["Jupiter"] + hits["Saturn"]) / 2.0) if (jupiter_hit and saturn_hit) else 0.0
    return {
        "score": round(score, 4),
        "jupiter_hit": jupiter_hit,
        "saturn_hit": saturn_hit,
        "jupiter_orb_strength": round(hits["Jupiter"], 4),
        "saturn_orb_strength": round(hits["Saturn"], 4),
    }


# ── T-5.3: Saham currents (read-only reuse of ga_sensitive_writer's facts) ───

def fetch_saham_facts(conn: Any, chart_id: str, ayanamsha_id: str = "lahiri_chitrapaksha") -> dict[str, dict]:
    """
    READ-ONLY SELECT of `saham_position` rows from `chart_facts` (written by
    ga_writers/ga_sensitive_writer.py — never touched by this module).
    Returns {saham_name: {'longitude_sidereal': float|None, 'house_d1': float|None}}.

    SAVEPOINT-guarded soft dependency (mirrors
    pipeline/orchestrator/writers/ka_sangam.py::_build_enrichment_context's
    fetch pattern) — never commits/rolls back the outer transaction, only
    ever releases/rolls back its own savepoint.

    CR-87: chart_id is REQUIRED — no default, no fallback to another chart.
    """
    if not chart_id:
        raise ValueError("fetch_saham_facts: chart_id is REQUIRED (CR-87) — no default")
    out: dict[str, dict] = {}
    try:
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_trigger_saham")
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fact_subject, fact_key, fact_value_num
                FROM chart_facts
                WHERE chart_id = %s
                  AND ayanamsha_id = %s
                  AND fact_category = 'saham_position'
                  AND fact_key IN ('longitude_sidereal', 'house_d1')
                """,
                (chart_id, ayanamsha_id),
            )
            for row in cur.fetchall():
                subj = row["fact_subject"]
                out.setdefault(subj, {})[row["fact_key"]] = row["fact_value_num"]
        with conn.cursor() as sp:
            sp.execute("RELEASE SAVEPOINT sp_trigger_saham")
    except Exception as exc:
        logger.debug("fetch_saham_facts: fetch skipped: %s", exc)
        try:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_trigger_saham")
        except Exception:
            pass
    return out


def saham_current(
    saham_facts: dict[str, dict],
    saham_name: str,
    transiting_planet_lon: Optional[float] = None,
    dasha_lord: Optional[str] = None,
    saham_lord: Optional[str] = None,
    orb_deg: float = 3.0,
) -> float:
    """
    Fires when either:
      (a) a transiting planet conjoins the saham's longitude within orb_deg
          (classical: a graha's transit over a Saham activates its result), or
      (b) the current daśā lord IS the saham's own significator lord
          (classical: a saham's period is 'awake' under its own lord's daśā).
    Generalizes over any key in ga_sensitive_writer._SAHAM_FORMULAS
    (SAHAM_DHANA at minimum — caller passes saham_name='SAHAM_DHANA' and,
    for the dasha-lord path, the Dhana Saham's day/night formula lord as
    saham_lord, resolved by the caller from is_day_birth same as the writer).

    Returns 0.0 (not fired) .. 1.0 (exact conjunction or lord match, whichever
    is stronger).
    """
    entry = saham_facts.get(saham_name)
    if not entry:
        return 0.0
    saham_lon = entry.get("longitude_sidereal")
    score = 0.0
    if saham_lon is not None and transiting_planet_lon is not None:
        delta = abs(((transiting_planet_lon - saham_lon) + 180.0) % 360.0 - 180.0)
        score = max(score, orb_strength_score(delta, orb_deg, "applying"))
    if dasha_lord is not None and saham_lord is not None and dasha_lord == saham_lord:
        score = max(score, 0.6)  # classical dasha-lord activation; no orb concept
    return min(1.0, score)


# T-5.4 (Gochara vedha filter extension, CR-102) formerly lived here:
# house_from_moon() + vedha_factor_corrected(), a standalone re-derivation of
# services.ka_sangam.engine._c11_vedha_factor using the correct house-from-
# Moon reference frame, for a call site that fed it the wrong (raw sign-
# number) argument. F-SANGAM-5 (L3-W3) found and fixed a DEEPER defect in
# the same current: the vedha_rules data source itself
# (bg_transit_rules WHERE rule_type='vedha') never matched any row at all —
# 0 of 0, regardless of which reference frame the house number used — and
# replaced the whole house-number approach with date-range matching against
# kala_vedha_gochara (the real, populated, per-chart source). That fix
# supersedes T-5.4's premise entirely (there is no longer a house number for
# CR-102's "sign vs house-from-Moon" distinction to apply to), so both
# functions and the diagnostic block that compared them were removed rather
# than updated to a comparison that would now always show identical values.


# ── T-5.5: school_consensus repair-or-honest-flag ─────────────────────────────
#
# services.ka_sangam.engine._c13_school_consensus_score ALWAYS returns 0.0
# today, because EnrichmentContext.school_consensus_by_domain is never
# populated (ka_sangam.py writer, line ~768: "pre-U4 default — not yet
# built, stays empty"). That 0.0 is indistinguishable, downstream, from a
# GENUINELY computed "0 of 7 schools agree" — a B.10 honesty violation
# ("computed, no consensus" vs "never computed" collapse to the same number).
# This module cannot repair the wiring (populating EnrichmentContext requires
# touching ka_sangam.py, out of scope for this lane — flagged below as a T-6
# follow-up) but it DOES fix the dishonesty: the function below never
# silently emits 0.0 for "no data" — it reports `computed=False` with an
# explicit reason instead, and only ever returns a numeric score when real
# schools_agreeing data was actually supplied.

_DOMAIN_PREFIXES: tuple[tuple[str, str], ...] = (
    ("CAREER", "CAREER"),
    ("HEALTH", "HEALTH"),
    ("RELATIONSHIP", "RELATIONSHIP"),
    ("SPIRITUAL", "SPIRITUAL"),
    ("PSYCHOLOGICAL", "PSYCHOLOGICAL"),
)


def _infer_domain(signature_class: str) -> Optional[str]:
    sig = (signature_class or "").upper()
    for prefix, mapped in _DOMAIN_PREFIXES:
        if sig.startswith(prefix):
            return mapped
    return None


def school_consensus_score(
    signature_class: str,
    school_consensus_by_domain: Optional[dict[str, int]],
) -> dict[str, Any]:
    """
    Honest replacement for `_c13_school_consensus_score`'s silent 0.0.
    Returns {'score', 'computed', 'schools_agreeing', 'reason'}:
      - computed=False, score=0.0, reason set: no real data was available —
        the caller MUST NOT treat this as "0 schools agree".
      - computed=True, score=n/7.0, schools_agreeing=n: a REAL value, which
        may legitimately be 0 (genuinely zero schools agree).
    """
    if not school_consensus_by_domain:
        return {
            "score": 0.0,
            "computed": False,
            "schools_agreeing": None,
            "reason": "not_computed: school_consensus_by_domain never populated upstream (pre-U4/EnrichmentContext gap)",
        }
    domain = _infer_domain(signature_class)
    if domain is None or domain not in school_consensus_by_domain:
        return {
            "score": 0.0,
            "computed": False,
            "schools_agreeing": None,
            "reason": f"not_computed: no domain match for signature_class={signature_class!r}",
        }
    n = school_consensus_by_domain[domain]
    return {
        "score": min(1.0, max(0.0, n / 7.0)),
        "computed": True,
        "schools_agreeing": n,
        "reason": None,
    }


# ── T-5.6: ka_yojaka/binder.py stub-predicate audit ───────────────────────────

def audit_binder_stub_predicates() -> dict[str, Any]:
    """
    Programmatic audit of services.ka_yojaka.binder._BUILDERS: for each
    signature_class builder, call it with two structurally different signal
    dicts (different constituent lords / graha_name / dispositor_lord /
    signal_type_class / constituent_facts_array) and compare outputs. A
    builder whose output is IDENTICAL for both inputs ignores `signal`
    entirely and is a genuine template stub — not a doctrine-doc guess, a
    directly observed fact about the code.

    Does not modify binder.py. Read-only import + call.
    """
    from services.ka_yojaka import binder

    sig_a = {
        "signal_id": "audit-a",
        "configuration_jsonb": {"grahas": ["Jupiter"]},
        "constituent_facts_array": ["fact-a1"],
        "graha_name": "Jupiter",
        "dispositor_lord": "Jupiter",
        "signal_type_class": "type_a",
    }
    sig_b = {
        "signal_id": "audit-b",
        "configuration_jsonb": {"grahas": ["Saturn", "Mars"]},
        "constituent_facts_array": ["fact-b1", "fact-b2"],
        "graha_name": "Saturn",
        "dispositor_lord": "Mars",
        "signal_type_class": "type_b",
    }

    detail: dict[str, dict[str, Any]] = {}
    for sig_class, builder in binder._BUILDERS.items():
        out_a = builder(sig_a)
        out_b = builder(sig_b)
        detail[sig_class] = {"signal_sensitive": out_a != out_b}

    total = len(detail)
    stub_count = sum(1 for v in detail.values() if not v["signal_sensitive"])
    return {
        "total_builders": total,
        "stub_count": stub_count,
        "stub_fraction": round(stub_count / total, 4) if total else 0.0,
        "detail": detail,
        "note": (
            "Directly-observed count via output-equality probe, not the "
            "doctrine doc's unverified '~90%' figure — that figure is NOT "
            "confirmed by this audit and should not be repeated as fact."
        ),
    }


# ── T-5.1 composition: compute_trigger_currents / compose_with_ka_sangam ─────

# Saturating combine weights for this module's OWN additive currents (guru_shani,
# saham) — a small, separate weight table from ka_sangam.SUPPORTING_WEIGHTS
# (intentionally: these currents do not exist there, so there is no double-
# counting risk when a caller adds ka_sangam's convergence_score to this
# module's suppressive term per the composition contract above).
TRIGGER_ADDITIVE_WEIGHTS: dict[str, float] = {
    "guru_shani_double_transit": 0.5,
    "saham_activation": 0.5,
}

# Saturating combine weights for the suppressive side.
TRIGGER_SUPPRESSIVE_WEIGHTS: dict[str, float] = {
    "malefic_transit_over_mechanism": 0.6,
    "papa_kartari_sandwich": 0.6,
}


def _saturating_combine(scores: dict[str, float], weights: dict[str, float]) -> float:
    """1 - Π(1 - w_i * s_i) — same saturating-sum shape as ka_sangam.engine's
    convergence_score supporting term (read-only structural reuse of the
    invariant, not the code)."""
    product = 1.0
    for key, weight in weights.items():
        s = max(0.0, min(1.0, scores.get(key, 0.0)))
        product *= (1.0 - weight * s)
    return 1.0 - product


def compute_trigger_currents(
    *,
    chart_id: str,
    mechanism_lon: Optional[float] = None,
    target_lon: Optional[float] = None,
    transit_sign_idx_1based: Optional[int] = None,
    moon_sign_idx_0based: Optional[int] = None,
    w_jd_start: Optional[float] = None,
    w_jd_end: Optional[float] = None,
    gochara_service: Any = None,
    vedha_rules: Optional[list[dict]] = None,
    vedha_planet: Optional[str] = None,
    saham_facts: Optional[dict[str, dict]] = None,
    saham_name: str = "SAHAM_DHANA",
    transiting_planet_lon: Optional[float] = None,
    dasha_lord: Optional[str] = None,
    saham_lord: Optional[str] = None,
    signature_class: str = "UNKNOWN",
    school_consensus_by_domain: Optional[dict[str, int]] = None,
    orb_deg: float = 5.0,
    additive_weights: Optional[dict[str, float]] = None,
    suppressive_weights: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """
    TRIGGER lock entry point. Computes:
      - additive: this module's OWN new currents (guru_shani + saham),
        saturating-combined, in [0, 1].
      - suppressive: malefic-over-mechanism + papa-kartari, saturating-
        combined then NEGATED, in [-1, 0]. THE headline deliverable — this
        is the signed term a caller subtracts from ka_sangam's score.
      - net: additive + suppressive, this module's own scope, UNCLAMPED
        (a caller composing with ka_sangam should use compose_with_ka_sangam
        instead; `net` here is for standalone testing of this module).
      - components: full per-current breakdown, including the honest
        school_consensus flag. (F-SANGAM-5, L3-W3: the vedha-filter-gap
        comparison this used to report was removed — see the comment at
        this function's former vedha_filter block.)

    CR-87: chart_id is REQUIRED (keyword-only, no default) — every entry
    point in this module that could resolve to a specific chart enforces
    this; a missing/falsy chart_id raises, never silently defaults.

    additive_weights / suppressive_weights (D-3 ADMIT lane, T-6 wiring):
    override the module-level TRIGGER_ADDITIVE_WEIGHTS / TRIGGER_
    SUPPRESSIVE_WEIGHTS constants (this module's own transparent, UNRATIFIED
    defaults — 0.5/0.5 additive, 0.6/0.6 suppressive). The kernel-admission
    loop (wave/D-3/ADMIT, receipted ACCEPT) found 0.2/0.2 for BOTH weight
    keys on each side scores best on the train split (train_score=0.312,
    +0.024 vs the v1 baseline) — genuinely tuned, not the module's own
    defaults. A caller wiring the ADMITTED score MUST pass
    `additive_weights={'guru_shani_double_transit': 0.2, 'saham_activation': 0.2}`
    and `suppressive_weights={'malefic_transit_over_mechanism': 0.2,
    'papa_kartari_sandwich': 0.2}` explicitly — omitting these falls back to
    the module's own unratified 0.5/0.6 defaults, which is correct for
    standalone/exploratory use but WRONG for the admitted composite score.
    """
    if not chart_id:
        raise ValueError("compute_trigger_currents: chart_id is REQUIRED (CR-87) — no default")

    additive_w = additive_weights if additive_weights is not None else TRIGGER_ADDITIVE_WEIGHTS
    suppressive_w = suppressive_weights if suppressive_weights is not None else TRIGGER_SUPPRESSIVE_WEIGHTS

    components: dict[str, Any] = {}

    # ── Suppressive side ──
    malefic_score = _malefic_transit_over_mechanism(
        mechanism_lon, gochara_service, w_jd_start, w_jd_end, orb_deg
    )
    papa_score = _papa_kartari_sandwich(
        target_lon, gochara_service, w_jd_start, w_jd_end, orb_deg + 3.0
    )
    components["malefic_transit_over_mechanism"] = round(malefic_score, 4)
    components["papa_kartari_sandwich"] = round(papa_score, 4)

    suppressive_raw = _saturating_combine(
        {
            "malefic_transit_over_mechanism": malefic_score,
            "papa_kartari_sandwich": papa_score,
        },
        suppressive_w,
    )
    suppressive = -suppressive_raw

    # ── Additive side (this module's own new currents) ──
    gs = guru_shani_double_transit(target_lon, gochara_service, w_jd_start, w_jd_end, orb_deg)
    components["guru_shani_double_transit"] = gs

    saham_score = 0.0
    if saham_facts is not None:
        saham_score = saham_current(
            saham_facts, saham_name, transiting_planet_lon, dasha_lord, saham_lord
        )
    components["saham_activation"] = {"saham_name": saham_name, "score": round(saham_score, 4)}

    additive = _saturating_combine(
        {
            "guru_shani_double_transit": gs["score"],
            "saham_activation": saham_score,
        },
        additive_w,
    )

    # F-SANGAM-5 (L3-W3) removed the vedha-filter-gap diagnostic this section
    # used to report (old_factor_sign_number_bug vs corrected_factor_house_
    # from_moon): _c11_vedha_factor no longer takes a house/sign-number
    # argument at all — it matches peak_date against real kala_vedha_gochara
    # date windows — so the CR-102 "sign-number vs house-from-Moon" contrast
    # this block existed to demonstrate no longer applies to either function
    # being compared, and computing it would either crash (wrong argument
    # type passed to the new _c11_vedha_factor signature) or compare two
    # calls that are now identical. `vedha_rules`/`vedha_planet` parameters
    # are kept (not removed from this function's signature) to avoid
    # rippling a signature change out to apply_trigger_suppression's own
    # caller in ka_sangam.py — currently unused here, flagged as a
    # follow-up cleanup rather than silently left unexplained.

    # ── school_consensus honest flag (informational — NOT folded into
    #    additive/suppressive; it duplicates ka_sangam's own C13 current and
    #    is reported here purely so a caller can see the honest computed/
    #    not_computed distinction alongside the other currents) ──
    components["school_consensus"] = school_consensus_score(
        signature_class, school_consensus_by_domain
    )

    return {
        "additive": round(additive, 4),
        "suppressive": round(suppressive, 4),
        "net": round(additive + suppressive, 4),
        "components": components,
        "weights_used": {
            "additive": dict(additive_w),
            "suppressive": dict(suppressive_w),
        },
    }


def compose_with_ka_sangam(ka_sangam_convergence_score: float, trigger_result: dict[str, Any]) -> float:
    """
    THE composition contract: net = additive_from_ka_sangam + suppressive_signed_term.
    Clamped to [0, 1] (same convention as ka_sangam.engine.convergence_score).
    """
    net = float(ka_sangam_convergence_score) + float(trigger_result["suppressive"])
    return max(0.0, min(1.0, net))
