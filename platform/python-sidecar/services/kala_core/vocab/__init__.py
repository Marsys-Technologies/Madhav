"""Closed Kāla identities and boundary adapters.

Graha aliases resolve through the versioned L0 semantic release. The graph's
two-letter node spelling is an explicit wire format, never a second identity.
Unknown or ambiguous input fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from brahmagyan.l0_semantic_release import graha_subject_code
from pyjhora_adapter._names import SIGN_NAMES
from services.gochara_rules.registry import CLASS_BY_NAME


class GrahaId(StrEnum):
    SUN = "SUN"
    MOON = "MOON"
    MARS = "MAR"
    MERCURY = "MER"
    JUPITER = "JUP"
    VENUS = "VEN"
    SATURN = "SAT"
    RAHU_MEAN = "RAH_MEAN"
    KETU_MEAN = "KET_MEAN"
    RAHU_TRUE = "RAH_TRUE"
    KETU_TRUE = "KET_TRUE"
    LAGNA = "LAGNA"


_PROMISE_GRAPH_GRAHAS = (
    GrahaId.SUN, GrahaId.MOON, GrahaId.MARS, GrahaId.MERCURY,
    GrahaId.JUPITER, GrahaId.VENUS, GrahaId.SATURN,
    GrahaId.RAHU_MEAN, GrahaId.KETU_MEAN,
)
# stage2_promise's wire format is the first two letters of L0's released
# canonical subject code, Title-cased. Derive it, do not keep a second map.
_GRAPH_CODE: dict[GrahaId, str] = {
    graha: graha.value[:2].capitalize() for graha in _PROMISE_GRAPH_GRAHAS
}
_GRAPH_TO_GRAHA = {code: graha for graha, code in _GRAPH_CODE.items()}


def graha_id(value: str | GrahaId) -> GrahaId:
    """Resolve a released L0 alias, preserving mean/true node identity."""
    if isinstance(value, GrahaId):
        return value
    return GrahaId(graha_subject_code(value))


def graha_node_id(value: str | GrahaId) -> str:
    """Return the established promise-graph spelling for a graha.

    The current graph supports the seven classical planets and mean nodes.
    A true-node variant or Lagna must not silently collapse into that graph.
    """
    graha = graha_id(value)
    try:
        return f"graha:{_GRAPH_CODE[graha]}"
    except KeyError as exc:
        raise ValueError(f"graha {graha.value} has no promise-graph node") from exc


def parse_graha_node(node_id: str) -> GrahaId:
    if not node_id.startswith("graha:"):
        raise ValueError(f"not a graha node: {node_id!r}")
    try:
        return _GRAPH_TO_GRAHA[node_id[6:]]
    except KeyError as exc:
        raise ValueError(f"unknown graha node: {node_id!r}") from exc


class DashaSystemId(StrEnum):
    VIMSHOTTARI = "vimshottari"
    ASHTOTTARI = "ashtottari"
    YOGINI = "yogini"
    KALACHAKRA = "kalachakra"
    CHARA = "chara"
    NARAYANA = "narayana"
    NAISARGIKA = "naisargika"
    MUDDA = "mudda"
    VIMSHOTTARI_KP = "vimshottari_kp"
    KARAKA_KENDRADI = "karaka_kendradi"
    MULA = "mula"


# The L1 producer stores Jaimini Cara under this historical id. It is not the
# separate kāraka-kendrādi method; preserve that distinction at this boundary.
_L1_SYSTEM_ID = {system: system.value for system in DashaSystemId}
_L1_SYSTEM_ID[DashaSystemId.CHARA] = "chara_karaka"
_NO_L1_PRODUCER = frozenset({DashaSystemId.KARAKA_KENDRADI, DashaSystemId.MULA})
_L1_TO_SYSTEM = {stored: system for system, stored in _L1_SYSTEM_ID.items()
                 if system not in _NO_L1_PRODUCER}


def system_id(value: str | DashaSystemId) -> DashaSystemId:
    if isinstance(value, DashaSystemId):
        return value
    if value in _L1_TO_SYSTEM:
        return _L1_TO_SYSTEM[value]
    return DashaSystemId(value)


def l1_system_id(value: str | DashaSystemId) -> str:
    system = system_id(value)
    if system in _NO_L1_PRODUCER:
        raise ValueError(f"{system.value} has no L1 period producer")
    return _L1_SYSTEM_ID[system]


class SignId(StrEnum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


assert tuple(sign.value for sign in SignId) == tuple(SIGN_NAMES)


class YoginiId(StrEnum):
    MANGALA = "Mangala"
    PINGALA = "Pingala"
    DHANYA = "Dhanya"
    BHRAMARI = "Bhramari"
    BHADRIKA = "Bhadrika"
    ULKA = "Ulka"
    SIDDHA = "Siddha"
    SANKATA = "Sankata"


# L1 ga_dashas_writer.YOGINI_SEQUENCE, BPHS2 46.195–199. A Yoginī deity
# inherits a graha's condition but remains a distinct period-lord identity.
YOGINI_GRAHA: dict[YoginiId, GrahaId] = dict(zip(YoginiId, (
    GrahaId.MOON, GrahaId.SUN, GrahaId.JUPITER, GrahaId.MARS,
    GrahaId.MERCURY, GrahaId.SATURN, GrahaId.VENUS, GrahaId.RAHU_MEAN,
), strict=True))


class LordKind(StrEnum):
    GRAHA = "graha"
    SIGN = "sign"
    YOGINI = "yogini"


@dataclass(frozen=True)
class LordId:
    kind: LordKind
    value: GrahaId | SignId | YoginiId

    def __post_init__(self) -> None:
        if not isinstance(self.kind, LordKind):
            raise TypeError("lord kind requires LordKind")
        expected = {LordKind.GRAHA: GrahaId, LordKind.SIGN: SignId,
                    LordKind.YOGINI: YoginiId}[self.kind]
        if not isinstance(self.value, expected):
            raise TypeError(f"{self.kind.value} lord requires {expected.__name__}")


def period_lord(system: str | DashaSystemId, value: str) -> LordId:
    """Interpret an L1 period lord in its method, without cross-kind coercion."""
    method = system_id(system)
    l1_system_id(method)  # A declared but unbuilt method has no L1 lord to read.
    if method in (DashaSystemId.CHARA, DashaSystemId.KALACHAKRA,
                  DashaSystemId.NARAYANA):
        return LordId(LordKind.SIGN, SignId(value))
    if method is DashaSystemId.YOGINI:
        return LordId(LordKind.YOGINI, YoginiId(value))
    return LordId(LordKind.GRAHA, graha_id(value))


def lord_node_id(lord: LordId) -> str:
    """Graph key: sign periods stay signs; deity periods use their graha."""
    if lord.kind is LordKind.SIGN:
        return f"rashi:{lord.value.value}"
    if lord.kind is LordKind.YOGINI:
        return graha_node_id(YOGINI_GRAHA[lord.value])
    return graha_node_id(lord.value)


def route_contains_lord(lord: LordId, path_node_ids: Iterable[str]) -> bool:
    return lord_node_id(lord) in path_node_ids


class FrameKind(StrEnum):
    LAGNA = "lagna"
    MOON = "moon"
    ARUDHA = "arudha"
    GRAHA = "graha"


@dataclass(frozen=True)
class FrameId:
    kind: FrameKind
    graha: GrahaId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, FrameKind):
            raise TypeError("frame kind requires FrameKind")
        if self.graha is not None and not isinstance(self.graha, GrahaId):
            raise TypeError("frame graha requires GrahaId")
        if (self.kind is FrameKind.GRAHA) != (self.graha is not None):
            raise ValueError("only a graha frame carries a graha id")

    @property
    def wire_id(self) -> str:
        return f"graha:{self.graha.value}" if self.graha else self.kind.value


def frame_id(value: str) -> FrameId:
    if value.startswith("graha:"):
        return FrameId(FrameKind.GRAHA, graha_id(value[6:]))
    return FrameId(FrameKind(value))


EVENT_CLASS_IDS = frozenset(CLASS_BY_NAME)


def event_class_id(value: str) -> str:
    if value not in EVENT_CLASS_IDS:
        raise ValueError(f"unknown event class: {value!r}")
    return value


class GrainId(StrEnum):
    INSTANT = "instant"
    INTERVAL = "interval"
    EPISODE = "episode"
    CLASS = "class"
    CLASS_MONTH = "class_month"
    ISSUE = "issue"


class EvidenceRole(StrEnum):
    SELECTS = "selects"
    CONDITIONS = "conditions"
    QUALIFIES = "qualifies"
    CORROBORATES = "corroborates"
    EXPLAINS = "explains"


class AssertionState(StrEnum):
    CANDIDATE = "candidate"
    EFFECTIVE = "effective"
    DEFEATED = "defeated"
    UNKNOWN = "unknown"


class OperatorRole(StrEnum):
    SCORED = "scored"
    TESTIMONY = "testimony"


class NullReason(StrEnum):
    OUTSIDE_RISK_SET = "outside_risk_set"
    METHOD_INAPPLICABLE = "method_inapplicable"
    INFORMATION_UNAVAILABLE = "information_unavailable"
    EVALUATED_SILENT = "evaluated_silent"
    OBSTRUCTION_ACTIVE = "obstruction_active"
    MEASURED_LOWER_RATE = "measured_lower_rate"
    CLASS_POLARITY_NOT_DECLARED_UPSTREAM = "class_polarity_not_declared_upstream"
    MISSING_FACT = "missing_fact"
    EVALUATED_EMPTY = "evaluated_empty"


class MethodQualification(StrEnum):
    QUALIFIED = "qualified"
    METHOD_CONTESTED = "method_contested"
    UNCITED_EXTENSION = "uncited_extension"


__all__ = [
    "GrahaId", "graha_id", "graha_node_id", "parse_graha_node",
    "DashaSystemId", "system_id", "l1_system_id", "SignId", "YoginiId",
    "YOGINI_GRAHA", "LordKind", "LordId", "period_lord", "lord_node_id",
    "route_contains_lord", "FrameKind", "FrameId", "frame_id",
    "EVENT_CLASS_IDS", "event_class_id", "GrainId", "EvidenceRole",
    "AssertionState", "OperatorRole", "NullReason", "MethodQualification",
]
