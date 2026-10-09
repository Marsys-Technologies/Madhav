"""Root algebra, independent of stage placement and display assertion identity."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from services.kala_core.measure import Interval

ROLES=frozenset({'selects','conditions','qualifies','corroborates','explains'})
GROUPS=frozenset({'G-P','G-J','G-T','G-K','G-A'})


@dataclass(frozen=True)
class Node:
    node_id: str
    roots: frozenset[str]
    parents: tuple[str,...]=()
    selection_roots: frozenset[str]=frozenset()

    def __post_init__(self):
        if not self.node_id or any(not x for x in (*self.roots,*self.parents,*self.selection_roots)):
            raise ValueError('source identities must be nonempty')


@dataclass(frozen=True)
class Use:
    node_id: str
    group_id: str
    interval: Interval
    role: str
    ancestry: frozenset[str]=frozenset()
    testimony: bool=False

    def __post_init__(self):
        if self.role not in ROLES or self.group_id not in GROUPS or not self.node_id:
            raise ValueError('unknown role, group or source identity')


@dataclass(frozen=True)
class Support:
    group_id: str
    interval: Interval
    roots: frozenset[str]
    ancestry: frozenset[str]


@dataclass(frozen=True)
class RootUse:
    root_id: str
    group_id: str
    interval: Interval
    role: str
    ancestry: frozenset[str]
    testimony: bool
    selected: bool
    required_roots: frozenset[str]


def evidence_graph(nodes: Iterable[Node], uses: Iterable[Use]) -> tuple[RootUse,...]:
    nodes,uses=tuple(nodes),tuple(uses)
    index={n.node_id:n for n in nodes}
    if len(index)!=len(nodes):
        raise ValueError('duplicate node identity; aliases need distinct node ids')
    cache={}
    def resolve(key,visiting=frozenset()):
        if key in visiting or key not in index:
            raise ValueError('cyclic or missing evidence parent')
        if key not in cache:
            n=index[key]; roots=set(n.roots); selected=set(n.selection_roots)
            for parent in n.parents:
                r,s=resolve(parent,visiting|{key}); roots.update(r); selected.update(s)
            if not roots:
                raise ValueError('evidence must resolve to a source root')
            cache[key]=(frozenset(roots),frozenset(selected))
        return cache[key]
    for key in index:
        resolve(key)
    records=set()
    for u in uses:
        roots,selected=resolve(u.node_id)
        records.update(RootUse(r,u.group_id,u.interval,u.role,u.ancestry,u.testimony,r in selected,roots) for r in roots)
    return tuple(sorted(records,key=lambda r:(r.root_id,r.group_id,r.interval,r.role,sorted(r.ancestry),r.testimony,r.selected,sorted(r.required_roots))))


def corroboration(nodes: Iterable[Node], uses: Iterable[Use]) -> tuple[Support,...]:
    graph=evidence_graph(nodes,uses)
    blocked={r.root_id for r in graph if r.selected or r.role in ('selects','conditions')}
    selection_ancestry=frozenset(a for r in graph if r.role in ('selects','conditions') for a in r.ancestry)
    buckets={}
    for r in graph:
        if r.role=='corroborates' and not r.testimony and not r.required_roots & blocked and not r.ancestry & selection_ancestry:
            buckets.setdefault((r.group_id,r.interval,r.ancestry,r.required_roots),set()).add(r.root_id)
    supports={Support(g,i,frozenset(roots),a) for (g,i,a,bundle),roots in buckets.items()}
    owner={}; admitted=[]
    for s in sorted(supports,key=lambda s:(s.group_id!='G-P',s.group_id,sorted(s.roots))):
        if any(root in owner and owner[root]!=s.group_id for root in s.roots):
            continue
        admitted.append(s)
        for root in s.roots:
            owner.setdefault(root,s.group_id)
    unique=(Support(s.group_id,s.interval,frozenset(r for r in s.roots if owner[r]==s.group_id),s.ancestry) for s in admitted)
    return tuple(sorted((s for s in unique if s.roots),key=lambda s:(s.group_id,s.interval,sorted(s.roots),sorted(s.ancestry))))
