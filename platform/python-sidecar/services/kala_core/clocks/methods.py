"""Named F2 constructions and sourced entry conditions (ALGO 3.1, NR-R13a)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from services.kala_core.vocab import DashaSystemId, SignId, l1_system_id, system_id

ApplicabilityState = Literal["applicable", "method_inapplicable", "unknown"]


@dataclass(frozen=True)
class DashaMethod:
    method_id: DashaSystemId
    l1_producer: str | None
    tags: tuple[str, ...]
    ancestry_groups: tuple[str, ...]
    sources: tuple[str, ...]


# Producer names identify L1, never implementations or alternate ladders in F2.
_METHODS = {
    "vimshottari": ("compute_vimshottari", ("fruition_ladder",), ("moon_nakshatra",), ("BPHS 46.12-16",)),
    "ashtottari": ("compute_ashtottari_system", ("fruition_ladder", "conditional_entry"), ("moon_nakshatra",), ("BPHS 46.17-20,23",)),
    "yogini": ("compute_yogini_system", ("fruition_ladder",), ("moon_nakshatra",), ("BPHS 46.195-199",)),
    "kalachakra": ("compute_kalachakra_system", ("rasi_period",), ("moon_nakshatra",), ("BPHS PG594", "Patel PG1872")),
    "chara": ("compute_chara_system", ("rasi_period",), (), ("Jaimini PG46,PG48", "BPHS2 7078-7168")),
    "karaka_kendradi": (None, ("rasi_period",), (), ("BPHS2 7717-7877",)),
    "mula": (None, ("fruition_ladder",), (), ("Saravali PG155",)),
    "naisargika": ("compute_naisargika_system", ("life_stage",), (), ("ALGO 3.1 life-stage band",)),
    "mudda": ("compute_mudda_system", ("annual",), (), ("ALGO 3.1 annual admission [U]",)),
    "vimshottari_kp": ("compute_kp_subperiods", ("sub_lord_refinement",), ("moon_nakshatra",), ("KP Reader V",)),
}


def dasha_method(system: str | DashaSystemId) -> DashaMethod:
    method = system_id(system)
    if method.value not in _METHODS:
        raise ValueError(f"no admitted F2 method: {method.value}")
    producer, tags, ancestry, sources = _METHODS[method.value]
    return DashaMethod(method, f"ga_dashas_writer.{producer}" if producer else None, tags, ancestry, sources)


def stored_system(system: str | DashaSystemId) -> str:
    return l1_system_id(system)


@dataclass(frozen=True)
class ClockFact:
    """A value from an admitted L1 artifact, with its actual fact references."""
    value: Any
    fact_ids: tuple[str, ...]

    @property
    def known(self) -> bool:
        return self.value is not None and bool(self.fact_ids) and all(self.fact_ids)


@dataclass(frozen=True)
class AshtottariFacts:
    # Houses already measured in the named frames by L1, never a hard-coded chart.
    rahu_house_from_lagna: ClockFact
    rahu_house_from_lagna_lord: ClockFact
    daytime: ClockFact
    paksha: ClockFact


@dataclass(frozen=True)
class EntryCondition:
    name: str
    state: Literal["satisfied", "failed", "unknown"]
    fact_ids: tuple[str, ...]
    source: str
    required: bool = True


@dataclass(frozen=True)
class Applicability:
    state: ApplicabilityState
    conditions: tuple[EntryCondition, ...] = ()

    @property
    def failed_conditions(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.conditions if c.required and c.state == "failed")


def assess_ashtottari(facts: AshtottariFacts | None) -> Applicability:
    """46.17-20 entry rule; 46.23's recommendation is disclosed separately.

    A true producer annotation supplies none of these facts. Missing fact ids,
    missing values and invalid frame values remain unknown, even on the native.
    """
    if facts is None:
        facts = AshtottariFacts(*(ClockFact(None, ()) for _ in range(4)))
    conditions = []
    for name, fact, allowed in (
        ("rahu_not_in_lagna", facts.rahu_house_from_lagna, set(range(2, 13))),
        ("rahu_kendra_trikona_from_lagna_lord", facts.rahu_house_from_lagna_lord, {1, 4, 5, 7, 9, 10}),
    ):
        valid = fact.known and type(fact.value) is int and 1 <= fact.value <= 12
        state = ("satisfied" if fact.value in allowed else "failed") if valid else "unknown"
        conditions.append(EntryCondition(name, state, fact.fact_ids, "BPHS 46.17-20"))
    day, paksha = facts.daytime, facts.paksha
    valid = day.known and paksha.known and type(day.value) is bool and paksha.value in ("shukla", "krishna")
    time_ok = (day.value and paksha.value == "krishna") or (day.value is False and paksha.value == "shukla")
    conditions.append(EntryCondition(
        "day_krishna_or_night_shukla", ("satisfied" if time_ok else "failed") if valid else "unknown",
        day.fact_ids + paksha.fact_ids, "BPHS 46.23", required=False,
    ))
    required = [c.state for c in conditions if c.required]
    state = "method_inapplicable" if "failed" in required else "unknown" if "unknown" in required else "applicable"
    return Applicability(state, tuple(conditions))


@dataclass(frozen=True)
class KalachakraFacts:
    """L1 method details, not a Kālacakra schedule construction in F2."""
    direction: Literal["savya", "apasavya"]
    nakshatra_pada: int
    deha: str
    jiva: str
    gati: tuple[str, ...]
    fact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.direction not in ("savya", "apasavya") or self.nakshatra_pada not in range(1, 5):
            raise ValueError("invalid Kālacakra direction/pada")
        SignId(self.deha)
        SignId(self.jiva)
        if not self.fact_ids or not all(self.fact_ids):
            raise ValueError("Kālacakra details require L1 fact ids")


def validate_f2_row(row: Any) -> None:
    """Reject scores/votes anywhere in an F2 payload, including nested rows."""
    if isinstance(row, dict):
        for key, value in row.items():
            if "score" in str(key).lower() or "agreement" in str(key).lower():
                raise ValueError(f"F2 cannot carry scored field {key!r}")
            validate_f2_row(value)
    elif isinstance(row, (tuple, list)):
        for value in row:
            validate_f2_row(value)
