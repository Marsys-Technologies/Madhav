"""Declared schools and admission, never an assertion of independence."""
from dataclasses import dataclass, replace
from services.kala_core.measure import Interval
from .evidence import GROUPS, ROLES


@dataclass(frozen=True)
class Group:
    group_id: str
    inputs: tuple[str,...]
    roles: frozenset[str]
    coverage: tuple[Interval,...]
    status: str
    reason: str | None
    ancestry: frozenset[str]=frozenset()
    source_refs: tuple[str,...]=()
    review_refs: tuple[str,...]=()
    admission: str='declared_input'
    requested_horizon: Interval | None=None

    def __post_init__(self):
        if self.group_id not in GROUPS or not self.inputs or not self.roles or not self.roles<=ROLES:
            raise ValueError('group requires declared inputs and roles')
        if self.status not in ('available','information_unavailable'):
            raise ValueError('unknown admission status')
        if self.status=='available' and (not self.coverage or not self.source_refs or not self.review_refs or self.reason is not None):
            raise ValueError('available group requires coverage and provenance')
        if self.status=='information_unavailable' and not self.reason:
            raise ValueError('missing input needs a named reason')


def declarations(horizon: Interval) -> tuple[Group,...]:
    groups=(
        Group('G-P',('judge_assertions','negative_space','F1','F2'),frozenset({'selects','corroborates','conditions'}),(horizon,),'information_unavailable','judge_inputs_missing'),
        Group('G-J',('complete_jaimini_output','F2:chara','directed_rasi_drishti'),frozenset({'corroborates'}),(horizon,),'information_unavailable','jaimini_output_missing',frozenset({'jaimini_cara','rasi_drishti'}),admission='complete_method'),
        Group('G-T',('admitted_tajaka_corpus',),frozenset({'corroborates'}),(horizon,),'information_unavailable','corpus_not_admitted',admission='corpus'),
        Group('G-K',('ingested_kp_reader_v_vi',),frozenset({'corroborates'}),(horizon,),'information_unavailable','kp_not_ingested',frozenset({'moon_nakshatra'}),admission='ingestion'),
        Group('G-A',('F2:yogini','F2:kalachakra'),frozenset({'explains'}),(horizon,),'information_unavailable','testimony_inputs_missing',frozenset({'moon_nakshatra'})),
    )
    return tuple(replace(g,coverage=(),requested_horizon=horizon) for g in groups)


def admit(group: Group, source_refs: tuple[str,...], coverage: tuple[Interval,...],
          review_refs: tuple[str,...], *, corpus_admitted: bool=False,
          ingested: bool=False, complete_method: bool=False) -> Group:
    if group.admission=='complete_method' and not complete_method:
        return replace(group,status='information_unavailable',reason='complete_method_required')
    if group.admission=='corpus' and not corpus_admitted:
        return replace(group,status='information_unavailable',reason='corpus_not_admitted')
    if group.admission=='ingestion' and not ingested:
        return replace(group,status='information_unavailable',reason='kp_not_ingested')
    if not source_refs or not all(source_refs) or not review_refs or not all(review_refs) or not coverage:
        return replace(group,status='information_unavailable',reason='incomplete_input_provenance')
    return replace(group,status='available',reason=None,coverage=tuple(coverage),source_refs=tuple(source_refs),review_refs=tuple(review_refs))
