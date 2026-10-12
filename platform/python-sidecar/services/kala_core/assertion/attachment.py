"""Canonical event links (concept note §5.5), independent of evidence scoring.

This prepares candidate forecasts; it neither issues a prediction nor scores an
outcome. Event/predicate references are supplied by F1, never inferred from text.
"""
import hashlib
import json
from typing import Literal
from uuid import UUID

from pydantic import Field, computed_field, model_validator

from . import Ref, Typed


def _identity(prefix, *parts):
    material = json.dumps(parts, ensure_ascii=False, separators=(',', ':'))
    return prefix + hashlib.sha256(material.encode()).hexdigest()


class EventIdentity(Typed):
    event_class: Ref
    phase: Ref
    affected_person: Ref
    episode: Ref


class ReadingClaim(Typed):
    signal_id: Ref
    kind: Literal['observable_event', 'trait', 'condition', 'lifetime_tendency', 'subjective_rasa']
    event: EventIdentity | None = None
    observable_event_ref: Ref | None = None
    objects: tuple[Ref, ...] = ()


class CanonicalForecast(Typed):
    chart_id: UUID
    event: EventIdentity
    observable_event_ref: Ref
    objects: tuple[Ref, ...]
    assertion_ids: tuple[Ref, ...] = Field(min_length=1)

    @model_validator(mode='before')
    @classmethod
    def validate_stored_ids(cls, value):
        if isinstance(value, dict) and {'forecast_id', 'shared_episode_id'} & value.keys():
            if not {'event', 'chart_id'} <= value.keys():
                raise ValueError('stored identity requires chart and event')
            # Derived identifiers may travel over JSON, but cannot override the
            # event identity. All other unknown fields remain forbidden.
            value = dict(value)
            event = EventIdentity.model_validate(value['event'])
            chart = str(UUID(str(value['chart_id'])))
            expected = {
                'forecast_id': _identity('forecast:', chart, event.event_class,
                                        event.phase, event.affected_person, event.episode),
                'shared_episode_id': _identity('episode:', chart, event.affected_person, event.episode),
            }
            for name, identity in expected.items():
                if name in value and value.pop(name) != identity:
                    raise ValueError('stored canonical identity disagrees with event')
        return value

    @computed_field
    @property
    def forecast_id(self) -> str:
        event = self.event
        return _identity('forecast:', str(self.chart_id), event.event_class,
                         event.phase, event.affected_person, event.episode)

    @computed_field
    @property
    def shared_episode_id(self) -> str:
        return _identity('episode:', str(self.chart_id), self.event.affected_person, self.event.episode)


class AttachedForecast(Typed):
    forecast: CanonicalForecast
    reading_attachments: tuple[Ref, ...]


class UnattachedClaim(Typed):
    claim: ReadingClaim
    reason: Literal['nonobservable_reading', 'event_mapping_unavailable',
                    'observable_predicate_unavailable', 'canonical_forecast_unavailable',
                    'observable_predicate_mismatch', 'event_objects_mismatch']


class EvaluationCluster(Typed):
    shared_episode_id: Ref
    forecast_ids: tuple[Ref, ...]


class AttachmentReport(Typed):
    acceptance_scope: Literal['candidate_preparation'] = 'candidate_preparation'
    forecasts: tuple[AttachedForecast, ...]
    unattached: tuple[UnattachedClaim, ...]
    evaluation_clusters: tuple[EvaluationCluster, ...]
    null_reason: Literal['canonical_event_identity_unavailable'] | None


def _event_key(event):
    return event.event_class, event.phase, event.affected_person, event.episode


def attach_reading_claims(forecasts: tuple[CanonicalForecast, ...],
                        claims: tuple[ReadingClaim, ...]) -> AttachmentReport:
    """One canonical evaluation unit per event, with many non-scoring links.

Different definitions of one signal or event are refused before any write.
Unmatched/unsupported claims remain visible with their original mapping.
Shared episodes cluster events across classes/phases without merging them.
"""
    if len({f.chart_id for f in forecasts}) > 1:
        raise ValueError('attachment batch must belong to one chart')
    canonical = {}
    for forecast in forecasts:
        key = _event_key(forecast.event)
        previous = canonical.get(key)
        if previous and (previous.observable_event_ref != forecast.observable_event_ref
                         or set(previous.objects) != set(forecast.objects)):
            raise ValueError('conflicting canonical forecast definition')
        ids = set(forecast.assertion_ids) | (set(previous.assertion_ids) if previous else set())
        canonical[key] = forecast.model_copy(update={
            'assertion_ids': tuple(sorted(ids)), 'objects': tuple(sorted(set(forecast.objects)))})
    unique_claims = {}
    for claim in claims:
        claim = claim.model_copy(update={'objects': tuple(sorted(set(claim.objects)))})
        if claim.signal_id in unique_claims and unique_claims[claim.signal_id] != claim:
            raise ValueError('conflicting reading signal mapping')
        unique_claims[claim.signal_id] = claim
    attached = {key: set() for key in canonical}
    unattached = []
    for signal_id, claim in sorted(unique_claims.items()):
        target = canonical.get(_event_key(claim.event)) if claim.event else None
        if claim.kind != 'observable_event':
            reason = 'nonobservable_reading'
        elif claim.event is None:
            reason = 'event_mapping_unavailable'
        elif claim.observable_event_ref is None:
            reason = 'observable_predicate_unavailable'
        elif target is None:
            reason = 'canonical_forecast_unavailable'
        elif target.observable_event_ref != claim.observable_event_ref:
            reason = 'observable_predicate_mismatch'
        elif set(target.objects) != set(claim.objects):
            reason = 'event_objects_mismatch'
        else:
            attached[_event_key(claim.event)].add(signal_id)
            continue
        unattached.append(UnattachedClaim(claim=claim, reason=reason))
    clusters = {}
    result = []
    for key, forecast in sorted(canonical.items()):
        result.append(AttachedForecast(forecast=forecast, reading_attachments=tuple(sorted(attached[key]))))
        clusters.setdefault(forecast.shared_episode_id, set()).add(forecast.forecast_id)
    return AttachmentReport(forecasts=tuple(result), unattached=tuple(unattached),
        evaluation_clusters=tuple(EvaluationCluster(shared_episode_id=episode,
            forecast_ids=tuple(sorted(ids))) for episode, ids in sorted(clusters.items())),
        null_reason=None if canonical else 'canonical_event_identity_unavailable')
