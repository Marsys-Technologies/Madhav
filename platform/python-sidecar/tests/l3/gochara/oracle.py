"""WP2 hand-specified factorized scorer oracle (pure Python, zero dependencies).

This module is the INDEPENDENT oracle against which WP3b's span-aware legacy
algebra reproduction and WP4's duplication/equivalence tests compare the system
under test. It is definitionally independent: it reads no database, calls no
ephemeris, and imports nothing from services/. Every input is an explicit
argument; every constant below is pinned in WP2_FIXTURES.md with hand-worked
arithmetic.

Pinned formula (WP1_CONTRACTS.md §7 orb table + plan §4.5 legacy reproduction):

    lambda_raw   = clamp(PROMISE * PERMISSION * activity * tara_modifier
                         * w30_modifier * quality_gates, 0.0, 1.0)
    lambda_signed = +lambda_raw  if channel == 'benefic'
                  = -lambda_raw  if channel == 'malefic'   (sign applied separately)

Activity — span-aware legacy +/-5-day box, reproduced factor-by-factor before
any M-1 change (WP1_CONTRACTS.md §7 `orb_legacy_box`; plan §4.5 E8):

  Per episode i (linear motion assumed through t_exact, per the fixture
  specification; separation from exact grows at speed_deg_per_day):
      window_i = [max(t_in, t_exact - B), min(t_out, t_exact + B)] (+ query_span clip)
      if window_i is empty:            c_i = 0
      else: c_i = max over window_i of max(0, 1 - sep(t)/orb_max_deg)
              where sep(t) = speed_deg_per_day * |t - t_exact|
  COMBINATION RULE (pinned, noisy-OR):
      activity = 1 - prod_i (1 - c_i), clamped to [0, 1]
  Rationale for noisy-OR over summation: legacy semantics saturate at 1.0
  (legacy applies a hard max/saturate over contributing events, engine.py:821
  class behavior); summing k near-1 contributions would exceed 1 and require an
  un-pinned renormalization, while noisy-OR is order-independent, idempotent
  (duplicate episodes count once), and monotone -- all required by H-6.

Honesty rules (pinned):
  * quality_gates is None  -> state 'unavailable', lambda None (never 1.0 by
    default; WP2 case 10 / F06).
  * A factor that is None elsewhere -> ValueError (an unknown input is never
    silently treated as empty; execution prompt §6).
  * No clamping hides an exception: this oracle never catches one.

Hand-worked examples (see WP2_FIXTURES.md §13 for full arithmetic):
  E1: promise=0.8, permission=1.0, tara=1.0, w30=1.0, qg=1.0, benefic,
      one episode (speed 0.05 deg/d, orb 1.0, t_exact at window centre):
      c_1 = 1 (sep 0 at t_exact inside window) -> activity = 1
      lambda_raw = 0.8, lambda_signed = +0.8.
  E2: same but the query window is [t_exact + 8 d, t_exact + 10 d], B = 5 d:
      window_i empty (8 d > 5 d box) -> c_1 = 0 -> activity 0 -> lambda 0.
  E3: two episodes each c = 0.5 -> activity = 1 - (1-.5)(1-.5) = 0.75
      (NOT 1.0: noisy-OR; NOT 0.5: independence, H-6 counts a duplicate once).
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

__all__ = ["score_lambda", "ORACLE_VERSION", "BOX_HALF_DAYS_DEFAULT"]

ORACLE_VERSION = "wp2-oracle-1.0"
BOX_HALF_DAYS_DEFAULT = 5.0  # pinned ±5-day legacy box (WP1_CONTRACTS.md §7)


def _to_utc(value):
    """Accept ISO-8601 'Z' strings or datetime; return aware UTC datetime."""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    raise TypeError(f"unsupported time value: {value!r}")


def _episode_contribution(episode, box_half_days, query_start, query_end):
    """Peak orb-decayed weight of one episode inside its pinned window."""
    t_in = _to_utc(episode["t_in"])
    t_exact = _to_utc(episode["t_exact"])
    t_out = _to_utc(episode["t_out"])
    speed = float(episode["speed_deg_per_day"])
    orb = float(episode["orb_max_deg"])
    if orb <= 0:
        raise ValueError("orb_max_deg must be positive")

    win_start = max(t_in, t_exact - timedelta(days=box_half_days))
    win_end = min(t_out, t_exact + timedelta(days=box_half_days))
    if query_start is not None:
        win_start = max(win_start, query_start)
    if query_end is not None:
        win_end = min(win_end, query_end)
    if win_end < win_start:
        return 0.0

    # decay(t) = max(0, 1 - speed*|t - t_exact| / orb) is piecewise linear in t;
    # its max over a closed window is attained at an endpoint or at t_exact.
    candidates = [win_start, win_end]
    if win_start <= t_exact <= win_end:
        candidates.append(t_exact)
    best = 0.0
    for t in candidates:
        sep = abs(speed * (t - t_exact).total_seconds() / 86400.0)
        decay = max(0.0, 1.0 - sep / orb)
        best = max(best, decay)
    return min(best, 1.0)


def score_lambda(factors):
    """Score one (body, target, relation, interval) row from explicit factors.

    factors: dict with keys
      promise          float in [0,1]
      permission       float in [0,1]
      tara_modifier    float in [0,1]
      w30_modifier     float in [0,1]
      quality_gates    float in [0,1], or None -> honest 'unavailable'
      channel          'benefic' | 'malefic' (sign applied separately)
      episodes         list of dicts, each:
                         t_in, t_exact, t_out  ISO-8601 UTC (or datetime)
                         speed_deg_per_day     absolute angular speed through exact
                         orb_max_deg           declared orb (WP1 §7 orb row)
                       (episodes may be [] -> activity 0)
      box_half_days    optional, default 5.0 (pinned legacy ±5-day box)
      query_span       optional [start, end] ISO-8601 UTC clipping window

    Returns dict:
      state          'ok' | 'unavailable' (quality_gates None)
      lambda_raw     float in [0,1], or None when unavailable
      lambda_signed  +lambda_raw / -lambda_raw, or None
      activity       noisy-OR combination of episode contributions, [0,1]
      contributions  per-episode c_i list (deterministic order = input order)
      oracle_version pinned string
    """
    qg = factors.get("quality_gates", "MISSING")
    if qg == "MISSING":
        raise ValueError("quality_gates is required (pass None for honest unavailable)")
    if qg is None:
        return {
            "state": "unavailable",
            "reason": "quality_gates unavailable (overlay absent); never defaulted to 1.0",
            "lambda_raw": None,
            "lambda_signed": None,
            "activity": None,
            "contributions": [],
            "oracle_version": ORACLE_VERSION,
        }

    required = ["promise", "permission", "tara_modifier", "w30_modifier", "channel"]
    for key in required:
        if key not in factors or factors[key] is None:
            raise ValueError(f"factor '{key}' is required and must not be None")

    for key in ("promise", "permission", "tara_modifier", "w30_modifier", "quality_gates"):
        value = float(factors[key])
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"factor '{key}' out of [0,1]: {value}")

    channel = factors["channel"]
    if channel not in ("benefic", "malefic"):
        raise ValueError(f"channel must be 'benefic' or 'malefic', got {channel!r}")

    box_half_days = float(factors.get("box_half_days", BOX_HALF_DAYS_DEFAULT))
    query_span = factors.get("query_span")
    query_start = query_end = None
    if query_span is not None:
        query_start, query_end = _to_utc(query_span[0]), _to_utc(query_span[1])
        if query_end < query_start:
            raise ValueError("query_span end before start")

    contributions = [
        _episode_contribution(ep, box_half_days, query_start, query_end)
        for ep in factors.get("episodes", [])
    ]
    # Pinned combination: noisy-OR, 1 - prod(1 - c_i); empty product -> 0.
    activity = 1.0 - math.prod(1.0 - c for c in contributions)
    activity = min(max(activity, 0.0), 1.0)

    lambda_raw = (
        float(factors["promise"])
        * float(factors["permission"])
        * activity
        * float(factors["tara_modifier"])
        * float(factors["w30_modifier"])
        * float(qg)
    )
    lambda_raw = min(max(lambda_raw, 0.0), 1.0)
    lambda_signed = lambda_raw if channel == "benefic" else -lambda_raw

    return {
        "state": "ok",
        "lambda_raw": lambda_raw,
        "lambda_signed": lambda_signed,
        "activity": activity,
        "contributions": contributions,
        "oracle_version": ORACLE_VERSION,
    }
