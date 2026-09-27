"""RR-05 / R-6 / M-7. Proposition (post-fix behaviour): the separated kernel carries
adverse activity as DATA — a dignity-0 intensely active configuration has activity > 0
and valence < 0 on the new kernel while the legacy I-16 composite stays 0.0 (S11 defect
preserved only as the labelled legacy_i16 reading); eligibility failure is recorded as
availability['dasha'] = 'unavailable', never manufactured support (RRV-08); the RRV-03
ordering key (activity DESC, contact instant ASC) never pools valence — equal-activity
opposite-valence windows both survive a page cut. Calls the real engine."""
from _common import *
from datetime import date
from services.ka_sangam import engine as E

head("S15 — R-6 kernel: adverse activity visible, availability honest, ordering valence-free")

kern = E.separate_kernel
if NEG:
    # negative control: a "separated" kernel that secretly keeps dignity inside the
    # product and reports zero valence — i.e. the R-6 defect reborn.
    def kern(dignity, nec, sup, **kw):
        return {'activity': E.convergence_score([dignity] + list(nec), sup),
                'valence': 0.0, 'applicability': {}, 'availability': {}}

full_support = {'constituent_lord_transit': 1.0, 'benefic_dristi': 1.0}
k0 = kern(0.0, [1.0, 1.0], full_support)
legacy = E.convergence_score([0.0, 1.0, 1.0], full_support)
prop("dignity 0, full intensity → new-kernel activity > 0", k0['activity'] > 0, f"activity={k0['activity']}")
prop("dignity 0, full intensity → new-kernel valence < 0", k0['valence'] < 0, f"valence={k0['valence']}")
prop("legacy I-16 composite still 0.0 (labelled legacy reading)", legacy == 0.0, f"legacy={legacy}")

k1 = kern(1.0, [1.0, 1.0], full_support)
prop("dignity 1 → valence > 0", k1['valence'] > 0, f"valence={k1['valence']}")

# RRV-08: eligibility failure is an availability state, not support.
k_unavail = kern(0.5, [1.0], {}, availability={'dasha': 'unavailable'},
                 applicability={'constituent_lord_transit': False})
prop("eligibility failure → availability['dasha'] == 'unavailable'",
     k_unavail['availability'].get('dasha') == 'unavailable')
prop("eligibility failure → dasha applicability False (no manufactured support)",
     k_unavail['applicability'].get('constituent_lord_transit') is False)
prop("zero manufactured support: activity without dasha term < with neutral 0.5 term",
     k_unavail['activity'] < E.convergence_score([1.0], {'constituent_lord_transit': 0.5}),
     f"activity={k_unavail['activity']}")

# RRV-03: ordering key — valence carried as data, never pooled.
def win(activity, valence, peak):
    return {'activity': activity, 'valence': valence, 'peak_date': peak,
            'comparability_class': 'ka_sangam/DIGNITY', 'kernel_version': 'separated_v2'}
pos = win(0.8, 1.0, date(2024, 1, 1))
neg = win(0.8, -1.0, date(2024, 2, 1))
filler = win(0.1, 1.0, date(2024, 3, 1))
page = sorted([filler, neg, pos], key=E.ordering_key)[:2]
prop("equal-activity opposite-valence both survive a LIMIT-2 page cut",
     {w['valence'] for w in page} == {1.0, -1.0}, f"page valences={[w['valence'] for w in page]}")
ordered = sorted([pos, neg], key=E.ordering_key)
prop("tiebreak is contact instant ASC (valence not consulted)",
     ordered[0]['peak_date'] == date(2024, 1, 1) and ordered[1]['peak_date'] == date(2024, 2, 1))

done("POST-FIX BEHAVIOUR")
