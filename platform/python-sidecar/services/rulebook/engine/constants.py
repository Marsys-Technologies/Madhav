"""Rule Book engine (E3/E4) — conventions pinned in one place.

Every value here is a convention or a vocabulary; none is a chart value. The
manifest records this module's hash, so a change here changes the manifest.
"""

from __future__ import annotations

from types import MappingProxyType

ENGINE_VERSION = "rulebook-engine-v1.0"
STATES_SCHEMA = "rulebook-engine-states-v1"
MANIFEST_SCHEMA = "rulebook-unit-manifest-v1"
BUNDLE_SCHEMA = "rulebook-rule-bundle-v1"
FIXTURE_SCHEMA = "rulebook-engine-fixture-v1"

# ── day atom (ENGINE_PLAN v0.2 §2.5, Q2; YARDSTICK §0, §3.1) ───────────────
DAY_CONVENTION_ID = "sunrise-to-sunrise@birthplace-v1"
# The state of civil date D is the configuration at the sunrise that STARTS on D
# (the sunrise instant of D at the birthplace); the day runs to the next sunrise.
DAY_STATE_INSTANT = "sunrise_start_of_day"

# ── time zone: fail closed (DF-04) ──────────────────────────────────────────
# L1 writers fall back silently to IST (+5:30) when no offset is supplied
# (ga_dashas_writer.BIRTH_TZ_OFFSET). Until DF-04 is fixed, only an IST-zone
# birthplace is accepted; anything else (including a missing zone) raises.
IST_ZONES = frozenset({"Asia/Kolkata", "Asia/Calcutta"})
IST_OFFSET_MINUTES = 330

# ── ayanāṃśa / house system / node models ───────────────────────────────────
AYANAMSHA_L1 = "lahiri_chitrapaksha"
AYANAMSHA_L0 = "lahiri"  # bg_sky_calendar.ayanamsha_key; engine alias: lahiri_chitrapaksha == lahiri
HOUSE_SYSTEM = "whole_sign"
# Node models are not chosen here (DF-03 is undecided): no unit reads a Rāhu/Ketu
# position, natal or transit. See NODE_POLICY.
NODE_MODEL_NATAL_L1 = "mean"
NODE_MODEL_TRANSIT_L0 = "true"
NODES = frozenset({"rahu", "ketu"})

# Ashtakavarga counts are benefic points (BPHS "rekhā"); the compiler's bindu map
# (data/bindu_conventions.json) quarantines any card whose count term is not declared.
ASHTAKAVARGA_COUNT_CONVENTION = "benefic_points"

NODE_POLICY_ID = "nodes-out-v1"
NODE_POLICY = (
    "No unit reads a Rahu/Ketu position (DF-03 undecided, YARDSTICK D1). "
    "(1) A rule whose gate names a node in a position or state read (natal or transit placement, "
    "conjunction, aspect, retrograde/dignity flag, vedha obstructor set) is EXCLUDED_NODE. "
    "(2) A rule that is about dasha-lord identity only (is_dasha_lord / is_antardasha_lord, any graha "
    "including Rahu and Ketu) needs no node position and is evaluated. "
    "(3) A rule that reads the position or state of 'the' dasha or antardasha lord, or counts from the "
    "dasha lord's natal position, is evaluated; on days when that lord is Rahu or Ketu the predicate is "
    "NOT_ASSESSED (never FALSE), so no node convention is ever applied."
)

# Vimśottarī: the only daśā system the engine reads (v1).
DASHA_SYSTEM = "vimshottari"
DASHA_LEVEL_MD = 1
DASHA_LEVEL_AD = 2

SIGN_NAMES = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)
SIGN_NUMBER = MappingProxyType({name: i + 1 for i, name in enumerate(SIGN_NAMES)})

# Card graha -> chart_facts subject / L0 body / daśā lord_graha name (same tables as the compiler).
from ..constants import CF_SUBJECT, L0_BODY, GRAHAS  # noqa: E402

CARD_GRAHA_BY_L0_BODY = MappingProxyType({v: k for k, v in L0_BODY.items()})
CARD_GRAHA_BY_CF_SUBJECT = MappingProxyType({v: k for k, v in CF_SUBJECT.items()})

# L1 vocabularies the loader accepts. Anything else is a missing fact (NOT_ASSESSED).
RETROGRADE_FLAG_VALUES = MappingProxyType({"retrograde": True, "direct": False})
BOOL_TEXT = MappingProxyType({"true": True, "false": False})

# Sky coverage: Lahiri ingress/station rows, true node, 1900-01-02 .. rolling end.
SKY_EVENT_INGRESS = "ingress"

# JD <-> UTC
JD_UNIX_EPOCH = 2440587.5
SECONDS_PER_DAY = 86400.0

# Output run-length state codes
STATE_CODE = MappingProxyType({"TRUE": "T", "FALSE": "F", "NOT_ASSESSED": "N"})
