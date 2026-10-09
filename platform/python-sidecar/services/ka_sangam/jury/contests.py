"""Half-open opposing testimony, joint turning points and connected sequences."""
from dataclasses import dataclass, replace
from itertools import combinations
from typing import Literal, get_args
from services.kala_core.measure import Interval, union_intervals

Conclusion=Literal['supportive','adverse','obstructed','conditionally_deferred','denied','defeated','none']
CONCLUSIONS=frozenset(get_args(Conclusion))


@dataclass(frozen=True)
class Opinion:
    event_class: str
    interval: Interval
    conclusion: Conclusion
    groups: frozenset[str]
    roots: frozenset[str]

    def __post_init__(self):
        if not self.event_class or self.conclusion not in CONCLUSIONS or not self.groups or not self.roots:
            raise ValueError('typed conclusion with separate group and root support required')


@dataclass(frozen=True)
class Contest:
    event_class: str
    interval: Interval
    sides: tuple[Opinion,...]


@dataclass(frozen=True)
class TurningPoint:
    interval: Interval
    event_classes: frozenset[str]
    support: tuple[Opinion,...]


def _key(o):
    return (o.event_class,o.interval,o.conclusion,sorted(o.groups),sorted(o.roots))


def _canonical(opinions):
    # Interval presentation is not a new witness or predicate. Union coverage
    # of the same conclusion and evidence before deriving any boundaries.
    buckets={}
    for o in opinions:
        buckets.setdefault((o.event_class,o.conclusion,o.groups,o.roots),[]).append(o)
    result=[]
    for aliases in buckets.values():
        horizon=Interval(min(o.interval.start for o in aliases),max(o.interval.end for o in aliases))
        for interval in union_intervals((o.interval for o in aliases),horizon):
            original=next((o for o in aliases if o.interval==interval),None)
            result.append(original if original is not None else replace(aliases[0],interval=interval))
    return tuple(sorted(result,key=_key))


def _active(opinions):
    # Retain defeated testimony in the method output, but it supplies neither
    # joint support nor boundaries for operational contests and sequences.
    return tuple(o for o in opinions if o.conclusion not in ('defeated','none'))


def _segments(opinions):
    opinions=_canonical(_active(opinions))
    boundaries=sorted({t for o in opinions for t in (o.interval.start,o.interval.end)})
    for start,end in zip(boundaries,boundaries[1:]):
        active=tuple(o for o in opinions if o.interval.start<=start and o.interval.end>=end)
        if active:
            yield Interval(start,end),active


def contests(opinions) -> tuple[Contest,...]:
    result=[]
    for interval,active in _segments(opinions):
        for event_class in sorted({o.event_class for o in active}):
            sides=tuple(o for o in active if o.event_class==event_class and o.conclusion!='none')
            if any(o.conclusion=='supportive' for o in sides) and any(o.conclusion in {'adverse','obstructed','conditionally_deferred','denied'} for o in sides):
                result.append(Contest(event_class,interval,sides))
    return tuple(result)


def turning_points(opinions, *, min_classes: int) -> tuple[TurningPoint,...]:
    if type(min_classes) is not int or min_classes<2:
        raise ValueError('declare at least two jointly supported event classes')
    return tuple(TurningPoint(i,frozenset(o.event_class for o in a),a)
        for i,a in _segments(opinions) if len({o.event_class for o in a})>=min_classes)


@dataclass(frozen=True)
class Sequence:
    joint_interval: Interval
    earlier: Opinion
    later: Opinion


def sequences(opinions) -> tuple[Sequence,...]:
    # No order is inferred across a gap. Pairs retain their own conclusions;
    # boundary contact alone supplies no jointly supported sequence.
    return tuple(Sequence(Interval(b.interval.start,min(a.interval.end,b.interval.end)),a,b)
        for a,b in combinations(sorted(_canonical(_active(opinions)),key=lambda o:(o.interval.start,_key(o))),2)
        if a.interval.start<b.interval.start<min(a.interval.end,b.interval.end))
