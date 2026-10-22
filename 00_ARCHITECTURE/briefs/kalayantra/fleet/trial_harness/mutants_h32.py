"""Planted reversions for the HARNESS-3.2 claims (D-8, D-9, D-10) — one per distinct claim (D-OWNER-TESTS-20261016).  (id, claim, file, old, new); `old` must occur exactly once."""

M32 = [
    ("H-a", "the cross-check binds the per-grain vedha source, not the module constant VEDHA_SOURCE (D-8)", "trial_slice.py",
     'drishti=self.w.DRISHTI_SOURCE, vedha=vedha)', 'drishti=self.w.DRISHTI_SOURCE, vedha=self.w.VEDHA_SOURCE)'),
    ("H-a2p", "the cross-check reads a P1 grain with the writer's P1 operand sources (D-8)", "trial_slice.py",
     'position_at=self.position_at, p1=self._p1_operands(key[1], rows))}', 'position_at=self.position_at)}'),
    ("H-a2f", "the cross-check runs under rule_profile(final_rules=True) (D-8)", "trial_slice.py",
     '        with rule_registry.rule_profile(final_rules=True):               # the profile the trial', '        if True:               # the profile the trial'),
    ("H-b", "G-4's generation verdict is scoped to the trial classes (D-9)", "trial_slice.py",
     'nwg.generation_verdict(conn, CHART, GENERATION, classes=state["classes"])', 'nwg.generation_verdict(conn, CHART, GENERATION)'),
    ("H-cs", "G-5's projection is not evaluated for a slice smaller than the trial (D-10)", "gates.py",
     '    if n_trial < n_required:\n', '    if False:\n'),
    ("H-cl", "G-5's projection is not evaluated when the machine was loaded (D-10)", "gates.py",
     '    elif valid is not True:\n', '    elif False:\n'),
    ("H-cm", "the clock keeps the busiest load per core of a stage (D-10)", "trial_eval.py",
     'else max(s["max_load_per_core"], max_load)', 'else min(s["max_load_per_core"], max_load)'),
]
