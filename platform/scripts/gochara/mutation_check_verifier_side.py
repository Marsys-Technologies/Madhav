"""Mutation harness for the verifier-side modules (measuring_report, nd_h_tables, near_miss_verifier).

Each mutant is one literal replacement in one module; the module's whole pure suite must then FAIL BY ASSERTION. The baseline must
pass first (a harness that cannot pass cleanly measures nothing). Classification is from the structured junit report: only a test
failure whose element is an assertion failure counts as CAUGHT; a collection error, an import error, a non-assertion exception or a
missing report is NOT caught (it would pass for the wrong reason). Equivalent mutants are listed with the reason they are skipped.

Run from platform/python-sidecar:  python ../scripts/gochara/mutation_check_verifier_side.py [--only NAME]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SIDECAR = Path(__file__).resolve().parents[2] / "python-sidecar"
K = SIDECAR / "services" / "gochara_kernel"

# name -> (module file, suite, old, new)
MUTANTS = {'ndh.band': ('nd_h_tables.py', 'test_nd_h_tables.py', 'BAND_DEG = 1.0', 'BAND_DEG = 1.5'),
 'ndh.node-aspect': ('nd_h_tables.py',
                     'test_nd_h_tables.py',
                     '"rahu": frozenset({"conjunction"})',
                     '"rahu": frozenset({"conjunction", "aspect"})'),
 'ndh.guard-ge': ('nd_h_tables.py',
                  'test_nd_h_tables.py',
                  'p4_alone_with_dvi_share > GAIN_BAND',
                  'p4_alone_with_dvi_share >= GAIN_BAND'),
 'ndh.dvi-in-p3': ('nd_h_tables.py',
                   'test_nd_h_tables.py',
                   '    if path in ("P1", "P3"):\n        return t.core',
                   '    if path in ("P1",):\n'
                   '        return t.core\n'
                   '    if path == "P3":\n'
                   '        return t.core | t.dvi'),
 'ndh.saturn-karaka': ('nd_h_tables.py',
                       'test_nd_h_tables.py',
                       '"financial_deception": frozenset({"rahu"}),       #',
                       '"financial_deception": frozenset({"rahu", "saturn"}),       #'),
 'ndh.frame': ('nd_h_tables.py',
               'test_nd_h_tables.py',
               '(anchor + offset - 2) % 12 + 1',
               '(anchor + offset - 1) % 12 + 1'),
 'ndh.p4-nodes': ('nd_h_tables.py',
                  'test_nd_h_tables.py',
                  'P4_KB_AGENTS = frozenset({"jupiter", "saturn"})',
                  'P4_KB_AGENTS = frozenset({"jupiter", "saturn", "rahu", "ketu"})'),
 'ndh.bereavement-moon': ('nd_h_tables.py',
                          'test_nd_h_tables.py',
                          '    "bereavement": "sun",                             # ND-P2',
                          '    "bereavement": "moon",                             # ND-P2'),
 'ndh.mother-resolves': ('nd_h_tables.py', 'test_nd_h_tables.py', 'if person == "mother":', 'if person == "motherX":'),
 'ndh.karakatva-native': ('nd_h_tables.py',
                          'test_nd_h_tables.py',
                          'AFFECTED_PERSON.get(cls, DEFAULT_PERSON)): KARAKA_A',
                          'AFFECTED_PERSON.get(cls)): KARAKA_A'),
 'ndh.unknown-agent': ('nd_h_tables.py',
                       'test_nd_h_tables.py',
                       '    if agent not in NINE:\n'
                       '        raise ValueError(f"unknown_agent: {agent!r} (the nine, lower-case)")\n',
                       ''),
 'nm.min-approach': ('near_miss_verifier.py',
                     'test_near_miss_verifier.py',
                     'GRAZE_MIN_APPROACH_DEG = 5e-3',
                     'GRAZE_MIN_APPROACH_DEG = 5e-2'),
 'nm.band-exclusive': ('near_miss_verifier.py',
                       'test_near_miss_verifier.py',
                       '    return abs(d) <= orb                # INCLUSIVE',
                       '    return abs(d) < orb                # INCLUSIVE'),
 'nm.band-narrowed': ('near_miss_verifier.py',
                      'test_near_miss_verifier.py',
                      'cr.band_intervals(checked, body, centres, orb_deg, lo, hi)',
                      'cr.band_intervals(checked, body, centres, orb_deg * 0.5, lo, hi)'),
 'nm.bb-prunes-all': ('near_miss_verifier.py',
                      'test_near_miss_verifier.py',
                      '            if lower >= best - tol:',
                      '            if True:'),
 'nm.bb-no-sign-check': ('near_miss_verifier.py',
                         'test_near_miss_verifier.py',
                         '        if dm == 0 or (dm > 0) != (d0 > 0):',
                         '        if False:'),
 'nm.window-empty': ('near_miss_verifier.py', 'test_near_miss_verifier.py', '    if not hi > lo:', '    if False:'),
 'nm.proximity-tol': ('near_miss_verifier.py',
                      'test_near_miss_verifier.py',
                      'PROXIMITY_TOL = 1.5e-4',
                      'PROXIMITY_TOL = 1.5e-2'),
 'nm.clearance-tol': ('near_miss_verifier.py',
                      'test_near_miss_verifier.py',
                      'CLEARANCE_TOL_DEG = 1e-3',
                      'CLEARANCE_TOL_DEG = 1e-1'),
 'nm.closest-slack': ('near_miss_verifier.py',
                      'test_near_miss_verifier.py',
                      'CLOSEST_SLACK_SECONDS = 5.0',
                      'CLOSEST_SLACK_SECONDS = 6e6'),
 'nm.cert-tol': ('near_miss_verifier.py',
                 'test_near_miss_verifier.py',
                 'CERT_TOL_DEG = GRAZE_MIN_APPROACH_DEG / 10',
                 'CERT_TOL_DEG = 50.0'),
 'nm.junction-tout': ('near_miss_verifier.py',
                      'test_near_miss_verifier.py',
                      'kinds = sorted({k for k, t in events if t_in <= t < t_out})',
                      'kinds = sorted({k for k, t in events if t_in <= t <= t_out})'),
 'nm.junction-tin': ('near_miss_verifier.py',
                     'test_near_miss_verifier.py',
                     'kinds = sorted({k for k, t in events if t_in <= t < t_out})',
                     'kinds = sorted({k for k, t in events if t_in < t < t_out})'),
 'nm.no-speed-floor': ('near_miss_verifier.py',
                       'test_near_miss_verifier.py',
                       '    if vmax_dps is not None and vmax_dps < table:',
                       '    if False:'),
 'nm.compare-skips-clearance': ('near_miss_verifier.py',
                                'test_near_miss_verifier.py',
                                '        if abs(float(s["clearance_deg"]) - w["clearance_deg"]) > CLEARANCE_TOL_DEG:',
                                '        if False:'),
 'nm.compare-skips-junction': ('near_miss_verifier.py',
                               'test_near_miss_verifier.py',
                               '        if (expect["kinds"], expect["complete"]) != (stored_kinds, '
                               's.get("junction_complete")):',
                               '        if False:'),
 'nm.edge-unplaced-free': ('near_miss_verifier.py',
                           'test_near_miss_verifier.py',
                           '        elif not (row["t_in"] <= domain[0] or row["t_out"] >= domain[1]):',
                           '        elif False:'),
 'nm.tie-input-order': ('near_miss_verifier.py',
                        'test_near_miss_verifier.py',
                        'key_placed = lambda r: (r["t_closest"], r["t_in"], r["t_out"])',
                        'key_placed = lambda r: (r["t_closest"], 0, 0)'),
 'nm.ni-skip': ('near_miss_verifier.py',
                'test_near_miss_verifier.py',
                '        elif layer_on[k] != layer_off[k]:',
                '        elif False:'),
 'nm.scored-allowed': ('near_miss_verifier.py',
                       'test_near_miss_verifier.py',
                       '    if row.get("score") is not None:',
                       '    if False:'),
 'ndh.saturn-testimony': ('nd_h_tables.py',
                          'test_nd_h_tables.py',
                          'SATURN_TESTIMONY = {"spiritual_turn": frozenset({12})}',
                          'SATURN_TESTIMONY = {"spiritual_turn": frozenset({12, 9})}'),
 'ndh.affected-person': ('nd_h_tables.py',
                         'test_nd_h_tables.py',
                         'AFFECTED_PERSON = {"parental_event": "father"}',
                         'AFFECTED_PERSON = {"parental_event": "mother"}'),
 'ndh.gain-band': ('nd_h_tables.py', 'test_nd_h_tables.py', 'GAIN_BAND = 0.40', 'GAIN_BAND = 0.45'),
 'ndh.stamp-dvi-role': ('nd_h_tables.py',
                        'test_nd_h_tables.py',
                        '"dvi":     {"provenance": "uncited_extension", "operator_role": "scored"',
                        '"dvi":     {"provenance": "uncited_extension", "operator_role": "testimony"'),
 'ndh.stamp-class-ruling': ('nd_h_tables.py',
                            'test_nd_h_tables.py',
                            '        elif row.get("ruling_ref") != KB_SOURCE[event_class]:',
                            '        elif False:'),
 'nm.cand-skip': ('near_miss_verifier.py',
                  'test_near_miss_verifier.py',
                  'if tc is None or not any(lo - slack <= tc <= hi + slack for lo, hi in cands):',
                  'if tc is None:'),
 'nm.ordinal-skip': ('near_miss_verifier.py',
                     'test_near_miss_verifier.py',
                     'if s.get("ordinal") != ordinal_of.get(id(w)):',
                     'if False:'),
 'nm.orb-skip': ('near_miss_verifier.py',
                 'test_near_miss_verifier.py',
                 'if abs(float(s["orb_deg"]) - float(expected_orb_deg)) > 1e-9:',
                 'if False:'),
 'nm.object-skip': ('near_miss_verifier.py',
                    'test_near_miss_verifier.py',
                    'if s.get("object_id") != expected_object_id:',
                    'if False:'),
 'nm.finite-position': ('near_miss_verifier.py',
                        'test_near_miss_verifier.py',
                        'if v is None or not math.isfinite(float(v)):',
                        'if v is None:'),
 'nm.limit-unstated': ('near_miss_verifier.py',
                       'test_near_miss_verifier.py',
                       'if search.get("resolution_limit_seconds") != 60.0:',
                       'if False:'),
 'nm.junction-iterator': ('near_miss_verifier.py',
                          'test_near_miss_verifier.py',
                          '    events = list(events)                                              # materialised ONCE: '
                          'an iterator would be exhausted by the first row',
                          '    events = events'),
 'nm.finite-row': ('near_miss_verifier.py', 'test_near_miss_verifier.py', '    if nonfinite:', '    if False:'),
 'ndh.stamp-rule-version': ('nd_h_tables.py',
                            'test_nd_h_tables.py',
                            'if row.get("rule_version") != RULE_VERSION:',
                            'if False:'),
 'mr.p4-union': ('measuring_report.py',
                 'test_measuring_report.py',
                 'return _intersection(\n'
                 '        _supports(records, lambda r: r.path == "P4" and r.agent == "jupiter" and r.via in vias),\n'
                 '        _supports(records, lambda r: r.path == "P4" and r.agent == "saturn" and r.via in vias))',
                 'return _merge([\n'
                 '        *_supports(records, lambda r: r.path == "P4" and r.agent == "jupiter" and r.via in vias),\n'
                 '        *_supports(records, lambda r: r.path == "P4" and r.agent == "saturn" and r.via in vias)])'),
 'mr.role': ('measuring_report.py',
             'test_measuring_report.py',
             '(r.role != "scored", "testimony_record_in_scored_share")',
             '(False, "testimony_record_in_scored_share")'),
 'mr.birth-vocab': ('measuring_report.py',
                    'test_measuring_report.py',
                    '    return row.get("domain") == "other/birth"\n',
                    '    return row.get("domain") == "other/birth" or row.get("event_type") == "birth" or '
                    'row.get("subcategory") == "birth"\n'),
 'mr.ist': ('measuring_report.py',
            'test_measuring_report.py',
            'IST = timezone(timedelta(hours=5, minutes=30))',
            'IST = timezone.utc'),
 'mr.marker-incomplete': ('measuring_report.py',
                          'test_measuring_report.py',
                          'if view.marker_horizon is None or view.marker_schema != MARKER_SCHEMA or not '
                          'view.marker_digest:',
                          'if False:'),
 'mr.excluded-path': ('measuring_report.py',
                      'test_measuring_report.py',
                      'c in EXCLUDED_EIGHT and p in ("P1", "P3", "P4")',
                      'c in EXCLUDED_EIGHT'),
 'nm.refine-floor': ('near_miss_verifier.py', 'test_near_miss_verifier.py', 'for k in (1, 2, 3):', 'for k in ():'),
 'nm.closest-evidence': ('near_miss_verifier.py',
                         'test_near_miss_verifier.py',
                         'if w.get("closest_certified") is not True or not cands or not callable(dist):',
                         'if False:'),
 'nm.null-fields': ('near_miss_verifier.py', 'test_near_miss_verifier.py', '        if absent:', '        if False:'),
 'nm.band-budget': ('near_miss_verifier.py',
                    'test_near_miss_verifier.py',
                    'if calls[0] > max_position_calls:',
                    'if False:'),
 'mr.scorer-numerator': ('measuring_report.py',
                         'test_measuring_report.py',
                         'int(grid.date_inclusive or local_hi.time() != time())',
                         'int(local_hi.time() != time())'),
 'mr.underivable-log': ('measuring_report.py',
                        'test_measuring_report.py',
                        'if rows and not info["dates"]:',
                        'if False:'),
 'mr.digest-shape': ('measuring_report.py',
                     'test_measuring_report.py',
                     'elif not isinstance(view.marker_digest, str) or re.fullmatch(r"[0-9a-f]{64}", '
                     'view.marker_digest) is None:',
                     'elif False:'),
 'nm.separation': ('near_miss_verifier.py',
                   'test_near_miss_verifier.py',
                   'elif abs(dist(tc)) > w["clearance_deg"] + CERT_TOL_DEG:',
                   'elif False:'),
 'nm.junction-no-geometry': ('near_miss_verifier.py',
                             'test_near_miss_verifier.py',
                             'near_edge = abs(t - t_in) <= zone or abs(t - t_out) <= zone',
                             'near_edge = False'),
 'nm.junction-unresolved': ('near_miss_verifier.py',
                            'test_near_miss_verifier.py',
                            'if abs(margin) < GEOMETRY_RESOLUTION_DEG:',
                            'if False:'),
 'nm.junction-margin-sign': ('near_miss_verifier.py',
                             'test_near_miss_verifier.py',
                             'elif margin > 0 and (t_in - zone) <= t <= (t_out + zone):',
                             'elif (t_in - zone) <= t <= (t_out + zone):'),
 'mr.lel-id-fallback': ('measuring_report.py',
                        'test_measuring_report.py',
                        'lel_id = provenance.get("lel_id") if isinstance(provenance, dict) else None',
                        'lel_id = (provenance.get("lel_id") if isinstance(provenance, dict) else None) or '
                        'row.get("event_id")'),
 'mr.report-only-exact': ('measuring_report.py',
                          'test_measuring_report.py',
                          '        if not lel_id:\n            result["rows_without_lel_id"].append(report)',
                          '        if confidence == "exact" and not lel_id:\n'
                          '            result["rows_without_lel_id"].append(report)'),
 'mr.no-lel-id-reported': ('measuring_report.py',
                           'test_measuring_report.py',
                           '        if not lel_id:\n            result["rows_without_lel_id"].append(report)',
                           '        if False:\n            result["rows_without_lel_id"].append(report)'),
 'mr.digest-fullmatch': ('measuring_report.py',
                         'test_measuring_report.py',
                         're.fullmatch(r"[0-9a-f]{64}", view.marker_digest) is None',
                         're.match(r"[0-9a-f]{64}", view.marker_digest) is None'),
 'mr.vs-class-removal': ('measuring_report.py',
                         'test_measuring_report.py',
                         'others = _days(_supports(rs, lambda r: r.agent != agent and r.path != "P4"), grid)',
                         'others = _days(_supports(rs, lambda r: r.path != "P4"), grid)'),
 'nm.connected-skip': ('near_miss_verifier.py',
                       'test_near_miss_verifier.py',
                       'if rec.get("vmax_dps") is not None and _connected(dist, float(orb), t, inner, '
                       'float(rec["vmax_dps"])):',
                       'if True:'),
 'nm.connected-no-margin-check': ('near_miss_verifier.py',
                                  'test_near_miss_verifier.py',
                                  '        if m0 < 0 or m1 < 0:',
                                  '        if False:'),
 'nm.connected-always-proved': ('near_miss_verifier.py',
                                'test_near_miss_verifier.py',
                                '        if (m0 + m1 - v * gap) / 2.0 >= 0:',
                                '        if True:'),
 'nm.connected-floor': ('near_miss_verifier.py',
                        'test_near_miss_verifier.py',
                        '        if gap <= floor_seconds:\n            return False',
                        '        if gap <= floor_seconds:\n            return True'),
 'mr.no-start-bound': ('measuring_report.py',
                       'test_measuring_report.py',
                       '    if start < SUBSTRATE_DOMAIN_START:\n        return',
                       '    if False:\n        return'),
 'mr.midnight': ('measuring_report.py', 'test_measuring_report.py', 'if value.time() != time():', 'if False:'),
 'mr.unknown-agent': ('measuring_report.py',
                      'test_measuring_report.py',
                      '(r.agent not in ALL_AGENTS, "unknown_agent")',
                      '(False, "unknown_agent")'),
 'mr.blacklist': ('measuring_report.py',
                  'test_measuring_report.py',
                  '(bool(view.rule_versions - ALLOWED_RULE_VERSIONS),',
                  '(bool(view.rule_versions & {"1.2.0"}),'),
 'mr.census': ('measuring_report.py',
               'test_measuring_report.py',
               '(set(view.marker_classes) != SCORED_CLASSES,',
               '(False,'),
 'mr.year-trunc': ('measuring_report.py',
                   'test_measuring_report.py',
                   'start = date(min(info["dates"]).year, 1, 1) if rows else today',
                   'start = min(info["dates"]) if rows else today'),
 'mr.fast-split': ('measuring_report.py',
                   'test_measuring_report.py',
                   'FAST_AGENTS = frozenset({"sun", "moon", "mars", "mercury", "venus"})',
                   'FAST_AGENTS = frozenset({"sun", "moon", "mercury", "venus"})'),
 'mr.no-birth-bound': ('measuring_report.py',
                       'test_measuring_report.py',
                       '    if birth_date is not None and start < birth_date:',
                       '    if False:'),
 'mr.no-future-refusal': ('measuring_report.py', 'test_measuring_report.py', 'if start > today:', 'if False:'),
 'mr.empty-generation': ('measuring_report.py',
                         'test_measuring_report.py',
                         '(not view.class_paths_with_rows, "measuring_build_holds_no_rows")',
                         '(False, "measuring_build_holds_no_rows")'),
 'mr.via-path': ('measuring_report.py',
                 'test_measuring_report.py',
                 '        if r.path not in VIA_PATHS[r.via]:',
                 '        if False:'),
 'mr.status': ('measuring_report.py',
               'test_measuring_report.py',
               '(view.status not in (None, "candidate", "published"),',
               '(False,'),
 'mr.birth-row': ('measuring_report.py',
                  'test_measuring_report.py',
                  'if rows and (len(births) != 1 or _event_date(births[0].get("event_date")) != birth_date):',
                  'if False:'),
 'mr.shape-sensitivity': ('measuring_report.py',
                          'test_measuring_report.py',
                          '    if len(set(readings.values())) > 1:',
                          '    if False:'),
 'mr.unbounded': ('measuring_report.py',
                  'test_measuring_report.py',
                  '        if lo_inf or hi_inf or lo is None or hi is None:',
                  '        if False:')}
# EQUIVALENT mutants: run, and REPORTED as such when they survive (a survivor with a stated reason is not a gap; a caught one is fine too).
EQUIVALENT = {
    "ndh.finite-share": ("nd_h_tables.py", "test_nd_h_tables.py", "or not math.isfinite(p4_alone_with_dvi_share)", "or False",
                         "the range check `0 <= share <= 1` already refuses NaN and infinity; isfinite is a belt over braces"),
    "mr.merge-touching": ("measuring_report.py", "test_measuring_report.py", "        if merged and a <= merged[-1][1]:", "        if merged and a < merged[-1][1]:",
                          "merging day ranges that only touch does not change any count"),
}


# J4C-B mutations additionally bind integration and preparation isolation.
MUTANTS.update({
    'builder.class-selection': ('rule_registry.py', 'test_nd_h_builder_tiers.py::test_1_2_0_is_bound_and_selected_for_the_eight_classes_only', 'if cls == event_class and (_FINAL_RULES.get() or version != rules_registry.ND_H_VERSION):', 'if False:'),
    'builder.p1-pd': ('../gochara_rules/permission.py', 'test_nd_h_builder_tiers.py', '(level is None or level in kind["levels"])', 'True'),
    'builder.absorption': ('evaluator.py', 'test_nd_h_builder_tiers.py', 'replace(e, dvi_absorbed_by_core=True)', 'replace(e, dvi_absorbed_by_core=False)'),
    'builder.legacy-profile': ('rule_registry.py', 'test_nd_h_builder_tiers.py', 'ND_H_PATH_REFS if _FINAL_RULES.get() else ()', 'ND_H_PATH_REFS'),
    'builder.guard-boundary': ('../gochara_eval/density.py', 'test_nd_h_builder_tiers.py', 'len(sets["P4"]) * GAIN_BAND_DEN > GAIN_BAND_NUM * total', 'len(sets["P4"]) * GAIN_BAND_DEN >= GAIN_BAND_NUM * total'),
    'verifier.tier-derivation': ('inventory_verifier.py', 'test_p06_final_rule_verification.py', '_ndh_path_houses(event_class, path.upper())', '_ndh_TIERS[event_class].core'),
    'verifier.rank-category': ('record_derivation.py', 'test_p06_final_rule_verification.py', "if 'karaka_agent' not in metadata or metadata.get('karaka_agent') != want_category:", 'if False:'),
    'verifier.kb-missing': ('record_derivation.py', 'test_p06_final_rule_verification.py', '(expected_kb - stored_kb).items()', '{}.items()'),
    'verifier.kb-extra': ('record_derivation.py', 'test_p06_final_rule_verification.py', '(stored_kb - expected_kb).items()', '{}.items()'),
    'verifier.context': ('record_derivation.py', 'test_p06_final_rule_verification.py', 'if context is not None and (not contexts or any(c != context for c in contexts)):', 'if False:'),
})


MUTANTS.update({'builder.house.achievement_recognition': ('../gochara_rules/registry.py',
                                           'test_nd_h_builder_tiers.py',
                                           '_nd_h_row(\n'
                                           '        core=(10,), dvi=(11,), support=(5, 1, 9),\n'
                                           '        karakas=(_nd_karaka("Sun", "PG47:C1", "glory, service '
                                           'under the sovereign", KARAKA_RANK,\n'
                                           '                            text="phaladeepika"),\n'
                                           '                 _nd_karaka("Jupiter", "PG127:C1", "honour from '
                                           'the king", KARAKA_RANK)),\n'
                                           '        sources=("Phaladīpikā I.15", "BPHS 11.11", "Uttara '
                                           'Kālāmṛta PG127:C1 (meanings)"))',
                                           '_nd_h_row(\n'
                                           '        core=(3,), dvi=(11,), support=(5, 1, 9),\n'
                                           '        karakas=(_nd_karaka("Sun", "PG47:C1", "glory, service '
                                           'under the sovereign", KARAKA_RANK,\n'
                                           '                            text="phaladeepika"),\n'
                                           '                 _nd_karaka("Jupiter", "PG127:C1", "honour from '
                                           'the king", KARAKA_RANK)),\n'
                                           '        sources=("Phaladīpikā I.15", "BPHS 11.11", "Uttara '
                                           'Kālāmṛta PG127:C1 (meanings)"))'),
 'builder.house.business_launch': ('../gochara_rules/registry.py',
                                   'test_nd_h_builder_tiers.py',
                                   '_nd_h_row(\n'
                                   '        core=(7, 10), support=(6,),\n'
                                   '        karakas=(_nd_karaka("Mercury", "PG125:C2", "commerce", '
                                   'KARAKA_RANK),),\n'
                                   '        sources=("Phaladīpikā I.15", "BPHS 11.8", "Uttara Kālāmṛta '
                                   'PG125:C2 (Commerce)"))',
                                   '_nd_h_row(\n'
                                   '        core=(8, 10), support=(6,),\n'
                                   '        karakas=(_nd_karaka("Mercury", "PG125:C2", "commerce", '
                                   'KARAKA_RANK),),\n'
                                   '        sources=("Phaladīpikā I.15", "BPHS 11.8", "Uttara Kālāmṛta '
                                   'PG125:C2 (Commerce)"))'),
 'builder.house.financial_deception': ('../gochara_rules/registry.py',
                                       'test_nd_h_builder_tiers.py',
                                       '_nd_h_row(\n'
                                       '        core=(2, 12), dvi=(6,), support=(8,),\n'
                                       '        karakas=(_nd_karaka("Rahu", "PG131:C1", "falsehood, '
                                       'perplexity", KARAKA_RANK),),\n'
                                       '        sources=("Phaladīpikā I.13", "Phaladīpikā I.16", "BPHS '
                                       '24.18",\n'
                                       '                 "Uttara Kālāmṛta PG121:C1", "Uttara Kālāmṛta '
                                       'PG131:C1 (Rāhu)"),\n'
                                       '        notes="Saturn excluded as a kāraka; Mercury not added; no '
                                       '\'Rāhu must be involved\' gate")',
                                       '_nd_h_row(\n'
                                       '        core=(1, 12), dvi=(6,), support=(8,),\n'
                                       '        karakas=(_nd_karaka("Rahu", "PG131:C1", "falsehood, '
                                       'perplexity", KARAKA_RANK),),\n'
                                       '        sources=("Phaladīpikā I.13", "Phaladīpikā I.16", "BPHS '
                                       '24.18",\n'
                                       '                 "Uttara Kālāmṛta PG121:C1", "Uttara Kālāmṛta '
                                       'PG131:C1 (Rāhu)"),\n'
                                       '        notes="Saturn excluded as a kāraka; Mercury not added; no '
                                       '\'Rāhu must be involved\' gate")'),
 'builder.house.foreign_settlement': ('../gochara_rules/registry.py',
                                      'test_nd_h_builder_tiers.py',
                                      '_nd_h_row(\n'
                                      '        core=(12,), dvi=(4,), support=(9, 7),\n'
                                      '        karakas=(_nd_karaka("Rahu", "PG131:C1", "going to a different '
                                      'country", KARAKA_RANK),),\n'
                                      '        sources=("Uttara Kālāmṛta PG121:C1 (migrating to a different '
                                      'place)", "Jātaka Pārijāta VIII.97",\n'
                                      '                 "Uttara Kālāmṛta PG131:C1 (Rāhu)"),\n'
                                      '        notes="Saturn excluded as a kāraka; the 10th is noted beside '
                                      'SUPPORT 9/7, not a tier member")',
                                      '_nd_h_row(\n'
                                      '        core=(2,), dvi=(4,), support=(9, 7),\n'
                                      '        karakas=(_nd_karaka("Rahu", "PG131:C1", "going to a different '
                                      'country", KARAKA_RANK),),\n'
                                      '        sources=("Uttara Kālāmṛta PG121:C1 (migrating to a different '
                                      'place)", "Jātaka Pārijāta VIII.97",\n'
                                      '                 "Uttara Kālāmṛta PG131:C1 (Rāhu)"),\n'
                                      '        notes="Saturn excluded as a kāraka; the 10th is noted beside '
                                      'SUPPORT 9/7, not a tier member")'),
 'builder.house.parental_event': ('../gochara_rules/registry.py',
                                  'test_nd_h_builder_tiers.py',
                                  '_nd_h_row(\n'
                                  '        anchor_house=9, affected_person="father",\n'
                                  '        core=(1, 6), support=(8, 12),\n'
                                  '        karakas=(_nd_karaka("Sun", "PG47:C1", "father", KARAKA_RANK, '
                                  'KARAKA_ADMISSION,\n'
                                  '                            text="phaladeepika"),),\n'
                                  '        sources=("BPHS 7.39-43", "BPHS 23.7", "Phaladīpikā II.1 (Sun: '
                                  'father — meaning only)"),\n'
                                  '        notes="offsets derived; P2 emits no parental_event row (the '
                                  'native\'s Moon never evidences the parent)")',
                                  '_nd_h_row(\n'
                                  '        anchor_house=9, affected_person="father",\n'
                                  '        core=(2, 6), support=(8, 12),\n'
                                  '        karakas=(_nd_karaka("Sun", "PG47:C1", "father", KARAKA_RANK, '
                                  'KARAKA_ADMISSION,\n'
                                  '                            text="phaladeepika"),),\n'
                                  '        sources=("BPHS 7.39-43", "BPHS 23.7", "Phaladīpikā II.1 (Sun: '
                                  'father — meaning only)"),\n'
                                  '        notes="offsets derived; P2 emits no parental_event row (the '
                                  'native\'s Moon never evidences the parent)")'),
 'builder.house.property_acquisition': ('../gochara_rules/registry.py',
                                        'test_nd_h_builder_tiers.py',
                                        '_nd_h_row(\n'
                                        '        core=(4,), dvi=(11,), support=(2,),\n'
                                        '        karakas=(_nd_karaka("Mars", "PG125:C1", "land, house", '
                                        'KARAKA_RANK),),\n'
                                        '        sources=("BPHS 11.5", "Phaladīpikā I.12", "Uttara Kālāmṛta '
                                        'PG125:C1 (Mars: House)"))',
                                        '_nd_h_row(\n'
                                        '        core=(3,), dvi=(11,), support=(2,),\n'
                                        '        karakas=(_nd_karaka("Mars", "PG125:C1", "land, house", '
                                        'KARAKA_RANK),),\n'
                                        '        sources=("BPHS 11.5", "Phaladīpikā I.12", "Uttara Kālāmṛta '
                                        'PG125:C1 (Mars: House)"))'),
 'builder.house.psychological_arc': ('../gochara_rules/registry.py',
                                     'test_nd_h_builder_tiers.py',
                                     '_nd_h_row(\n'
                                     '        core=(4,), support=(5, 8),\n'
                                     '        karakas=(_nd_karaka("Moon", "PG47:C1", "Phaladīpikā II.2 (the '
                                     'Moon\'s significations)", KARAKA_ADMISSION,\n'
                                     '                            text="phaladeepika"),),\n'
                                     '        sources=("BPHS 11.5", "Phaladīpikā I.12", "Phaladīpikā II.2"))',
                                     '_nd_h_row(\n'
                                     '        core=(3,), support=(5, 8),\n'
                                     '        karakas=(_nd_karaka("Moon", "PG47:C1", "Phaladīpikā II.2 (the '
                                     'Moon\'s significations)", KARAKA_ADMISSION,\n'
                                     '                            text="phaladeepika"),),\n'
                                     '        sources=("BPHS 11.5", "Phaladīpikā I.12", "Phaladīpikā '
                                     'II.2"))'),
 'builder.house.spiritual_turn': ('../gochara_rules/registry.py',
                                  'test_nd_h_builder_tiers.py',
                                  '_nd_h_row(\n'
                                  '        core=(9, 5), support=(12,),\n'
                                  '        karakas=(_nd_karaka("Jupiter", "PG127:C1", "penance, dharma, '
                                  'mantra", KARAKA_RANK),\n'
                                  '                 _nd_karaka("Ketu", "PG132:C1", "final salvation, great '
                                  'penance, renunciation",\n'
                                  '                            KARAKA_RANK)),\n'
                                  '        sources=("Phaladīpikā I.14", "Phaladīpikā I.12", "BPHS 11.6", '
                                  '"BPHS 11.10",\n'
                                  '                 "Uttara Kālāmṛta PG127:C1", "Uttara Kālāmṛta '
                                  'PG132:C1"),\n'
                                  '        notes="12 is SUPPORT by ratification only (practice; no śloka '
                                  'located); Saturn is testimony on "\n'
                                  '              "contacts to the 12th SUPPORT member only — never a scored '
                                  'kāraka")',
                                  '_nd_h_row(\n'
                                  '        core=(10, 5), support=(12,),\n'
                                  '        karakas=(_nd_karaka("Jupiter", "PG127:C1", "penance, dharma, '
                                  'mantra", KARAKA_RANK),\n'
                                  '                 _nd_karaka("Ketu", "PG132:C1", "final salvation, great '
                                  'penance, renunciation",\n'
                                  '                            KARAKA_RANK)),\n'
                                  '        sources=("Phaladīpikā I.14", "Phaladīpikā I.12", "BPHS 11.6", '
                                  '"BPHS 11.10",\n'
                                  '                 "Uttara Kālāmṛta PG127:C1", "Uttara Kālāmṛta '
                                  'PG132:C1"),\n'
                                  '        notes="12 is SUPPORT by ratification only (practice; no śloka '
                                  'located); Saturn is testimony on "\n'
                                  '              "contacts to the 12th SUPPORT member only — never a scored '
                                  'kāraka")')})

MUTANTS.update({
    'writer.default-isolation': ('../../pipeline/orchestrator/writers/ka_gochara_v5.py', 'test_a53_gochara_v5_writer.py', 'final = ctx.config.get("gochara_v5_final_rules", False)', 'final = ctx.config.get("gochara_v5_final_rules", True)'),
    'writer.candidate-opt-in': ('../../pipeline/orchestrator/writers/ka_gochara_v5.py', 'test_a53_gochara_v5_writer.py', 'final = ctx.config.get("gochara_v5_final_rules", False)', 'final = False'),
    'writer.slice-isolation': ('../../pipeline/orchestrator/writers/ka_gochara_v5.py', 'test_a53_gochara_v5_writer.py', 'if ctx.config.get("gochara_v5_final_rules") is True:', 'if False:'),
    'verifier.job-stage': ('verification_job.py', 'test_p06_final_rule_verification.py', 'if version == "1.2.0":', 'if False:'),
})

MUTANTS.update({
    'builder.pd-withholding': ('record_store.py', 'test_nd_h_builder_registry_pg.py::test_pd_dispositor_testimony_is_withheld_even_when_the_same_lord_is_an_ad_karaka', 'if _unwritable(_anchor(edge), edge.period_anchor_level):', 'if _unwritable(_anchor(edge)):'),
})

MUTANTS.update({
    'verifier.cli-profile': ('../../pipeline/orchestrator/verification_job.py', 'test_p06_final_rule_verification.py::test_verification_cli_uses_the_same_explicit_candidate_profile', 'with rule_registry.rule_profile(final_rules=args.final_rules, **({"p1_form_b": True} if args.p1_form_b else {})):', 'with rule_registry.rule_profile(final_rules=False, **({"p1_form_b": True} if args.p1_form_b else {})):'),
})

MUTANTS.update({'fixture.setup-cleanup': ('../../tests/l3/gochara/test_a55_replace_chain.py',
                           'test_p06_final_rule_verification.py::test_golden_fixture_drops_its_owned_database_when_substrate_setup_is_interrupted',
                           '    except BaseException:\n'
                           '        conn.close()\n'
                           '        drop_am5_database(admin, name)\n'
                           '        raise\n',
                           '    except BaseException:\n'
                           '        conn.close()\n'
                           '        raise\n')})


# P02 merge adapter: same 29 mr.* claims, rebased onto the real current API.
MUTANTS.update({
    'mr.excluded-path': ("measuring_report.py", "test_measuring_report.py", 'any(c in EXCLUDED_EIGHT and p in ("P1", "P3", "P4") for c, p in view.class_paths_with_rows)', 'any(c in EXCLUDED_EIGHT for c, p in view.class_paths_with_rows)'),
    'mr.scorer-numerator': ("measuring_report.py", "test_measuring_report.py", 'int(grid.date_inclusive or local_hi.time() != time())', 'int(local_hi.time() != time())'),
    'mr.underivable-log': ("measuring_report.py", "test_measuring_report.py", 'if rows and not info["dates"]:', 'if False:'),
    'mr.digest-shape': ("measuring_report.py", "test_measuring_report.py", 'elif not isinstance(view.marker_digest, str) or re.fullmatch(r"[0-9a-f]{64}", view.marker_digest) is None:', 'elif False:'),
    'mr.lel-id-fallback': ("measuring_report.py", "test_measuring_report.py", 'lel_id = provenance.get("lel_id") if isinstance(provenance, dict) else None', 'lel_id = provenance.get("lel_id") if isinstance(provenance, dict) else None\n        lel_id = lel_id or row.get("event_id")'),
    'mr.report-only-exact': ("measuring_report.py", "test_measuring_report.py", 'if not lel_id:\n            result["rows_without_lel_id"].append(report)', 'if confidence == "exact" and not lel_id:\n            result["rows_without_lel_id"].append(report)'),
    'mr.no-lel-id-reported': ("measuring_report.py", "test_measuring_report.py", 'if not lel_id:\n            result["rows_without_lel_id"].append(report)', 'if False:\n            result["rows_without_lel_id"].append(report)'),
    'mr.digest-fullmatch': ("measuring_report.py", "test_measuring_report.py", 're.fullmatch(r"[0-9a-f]{64}", view.marker_digest)', 're.match(r"[0-9a-f]{64}", view.marker_digest)'),
    'mr.vs-class-removal': ("measuring_report.py", "test_measuring_report.py", '_class_supports([r for r in rs if r.agent != agent])', '_class_supports(rs)'),
    'mr.midnight': ("measuring_report.py", "test_measuring_report.py", 'if value.time() != time():', 'if False:'),
    'mr.unknown-agent': ("measuring_report.py", "test_measuring_report.py", '(r.agent not in ALL_AGENTS, "unknown_agent")', '(False, "unknown_agent")'),
    'mr.blacklist': ("measuring_report.py", "test_measuring_report.py", 'bool(view.rule_versions - ALLOWED_RULE_VERSIONS)', 'bool(view.rule_versions & {"1.2.0"})'),
    'mr.census': ("measuring_report.py", "test_measuring_report.py", 'set(view.marker_classes) != SCORED_CLASSES', 'False'),
    'mr.year-trunc': ("measuring_report.py", "test_measuring_report.py", 'start = date(min(info["dates"]).year, 1, 1) if rows else today', 'start = min(info["dates"]) if rows else today'),
    'mr.no-future-refusal': ("measuring_report.py", "test_measuring_report.py", 'if start > today:', 'if False:'),
    'mr.empty-generation': ("measuring_report.py", "test_measuring_report.py", 'not view.class_paths_with_rows, "measuring_build_holds_no_rows"', 'False, "measuring_build_holds_no_rows"'),
    'mr.status': ("measuring_report.py", "test_measuring_report.py", 'view.status not in (None, "candidate", "published")', 'False'),
    'mr.birth-row': ("measuring_report.py", "test_measuring_report.py", 'if rows and (len(births) != 1 or _event_date(births[0].get("event_date")) != birth_date):', 'if False:'),
})
EQUIVALENT["mr.merge-touching"] = ("measuring_report.py", "test_measuring_report.py", "        if merged and lo <= merged[-1][1]:", "        if merged and lo < merged[-1][1]:", "merging touching intervals does not change any admitted-day count")

MUTANTS["mr.p4-union"] = ("measuring_report.py", "test_measuring_report.py", 'return _intersection(\n        _supports(records, lambda r: r.path == "P4" and r.agent == "jupiter" and r.via in vias),\n        _supports(records, lambda r: r.path == "P4" and r.agent == "saturn" and r.via in vias))', 'return _merge([\n        *_supports(records, lambda r: r.path == "P4" and r.agent == "jupiter" and r.via in vias),\n        *_supports(records, lambda r: r.path == "P4" and r.agent == "saturn" and r.via in vias)])')
MUTANTS["mr.role"] = ("measuring_report.py", "test_measuring_report.py", '(r.role != "scored", "testimony_record_in_scored_share")', '(False, "testimony_record_in_scored_share")')


def classify(returncode, xml_path):
    try:
        root = ET.parse(xml_path).getroot()
    except (ET.ParseError, FileNotFoundError):
        return 'INFRASTRUCTURE'
    cases = list(root.iter('testcase'))
    failures = [c.find('failure') for c in cases if c.find('failure') is not None]
    if not cases or any(c.find('error') is not None for c in cases):
        return 'INFRASTRUCTURE'
    if returncode == 0:
        return 'SURVIVED'
    if returncode != 1 or not failures:
        return 'INFRASTRUCTURE'
    def assertion(f):
        msg = f.get('message', '')
        return msg.startswith(('assert ', 'AssertionError', 'Failed: ')) or msg == 'assert'
    return 'CAUGHT' if all(assertion(f) for f in failures) else 'UNEXPECTED_EXCEPTION'


def main(argv=None):
    import argparse
    import json
    import os
    import shutil

    ap = argparse.ArgumentParser(description='Run inherited verifier and J4C-B mutations in retained tree copies.')
    ap.add_argument('--only', help='One mutation name (exact match).')
    ap.add_argument('--scratch', type=Path, default=os.environ.get('JOB_SCRATCH'),
                    help='Required scratch parent; defaults to JOB_SCRATCH. Never uses /tmp.')
    args = ap.parse_args(argv)
    if args.scratch is None:
        ap.error('--scratch or JOB_SCRATCH is required')
    selected = {k: v for k, v in MUTANTS.items() if args.only is None or k == args.only}
    if not selected:
        ap.error('unknown --only mutation')
    root = args.scratch.resolve() / 'verifier-mutations'
    root.mkdir(parents=True, exist_ok=True)
    base = root / 'fixed'
    repo = SIDECAR.parent.parent
    if base.exists():
        ap.error(f'{base} exists; use a fresh scratch parent to preserve previous proof trees')
    paths = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=repo,
        env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}).decode().split('\0')
    for rel in paths:
        if not rel or not (rel.startswith(('platform/python-sidecar/', 'platform/migrations/', 'platform/scripts/seed/'))
                           or rel in ('.github/workflows/ci.yml', 'platform/scripts/governance/no_real_cloud_guard.py',
                                      'platform/scripts/governance/no_real_cloud_pytest.py',
                                      'platform/scripts/governance/git_env_scrub.py')):
            continue
        src = repo / rel
        if src.is_symlink():
            raise RuntimeError(f'refusing a symlink in the source copy: {rel}')
        if not src.is_file():
            continue
        dst = base / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)

    def run(tree, suite, label):
        report = root / (label + '.xml')
        temp = root / (label + '-tmp')
        cmd = [sys.executable, '-m', 'pytest', 'tests/l3/gochara/' + suite,
               '-q', '-p', 'no:cacheprovider', '--tb=short', '--basetemp=' + str(temp),
               '--junitxml=' + str(report)]
        proc = subprocess.run(cmd, cwd=tree / 'platform/python-sidecar', capture_output=True, text=True,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_ADDOPTS': ''})
        (root / (label + '.log')).write_text(proc.stdout + proc.stderr)
        return proc.returncode, report, cmd

    baselines = {}
    for i, suite in enumerate(sorted({v[1] for v in selected.values()})):
        rc, report, cmd = run(base, suite, 'baseline-' + str(i))
        baselines[suite] = {'exit': rc, 'report': str(report), 'cmd': cmd}
        print(f'BASELINE {suite}: {rc}', flush=True)
        if rc:
            return 2
    rows = []
    for name, (module, suite, old, new) in selected.items():
        copy = root / name
        shutil.copytree(base, copy, copy_function=os.link)
        target = copy / 'platform/python-sidecar/services/gochara_kernel' / module
        original = target.read_text()
        if old not in original or old == new:
            row = {'name': name, 'verdict': 'SETUP_ERROR', 'copy_path': str(copy)}
        else:
            # Break the hard link before mutating; the fixed tree stays immutable.
            target.unlink()
            target.write_text(original.replace(old, new, 1))
            rc, report, cmd = run(copy, suite, name)
            row = {'name': name, 'verdict': classify(rc, report), 'test': cmd,
                   'revert_exit': rc, 'fixed_exit': baselines[suite]['exit'],
                   'copy_path': str(copy), 'report': str(report)}
        rows.append(row)
        print(name + ': ' + row['verdict'], flush=True)
        (root / 'proofs.json').write_text(json.dumps({'baselines': baselines, 'mutations': rows}, indent=2) + '\n')
    bad = [r for r in rows if r['verdict'] != 'CAUGHT']
    print(f'{len(rows) - len(bad)}/{len(rows)} caught; equivalent historical mutants are not counted', flush=True)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
