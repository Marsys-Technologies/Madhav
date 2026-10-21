"""F-CHANNEL (SR-W34-PREP-RULINGS 1, option a): the century run's rule profile, verify-deferral switch and horizon reach the writer — and an unmarked run that
arrives without an explicit profile or horizon REFUSES by name instead of silently running the measuring profile over the code-default horizon.

The production orchestrator builds `ctx.config` from chart_id and birth_params only (the FROZEN asset_runner), so the values travel in
`build_runs.plan_manifest[gochara_v5_century_config]`, covered by `plan_manifest_digest`; the writer overlays them on `ctx.config`. Claims, each with its
own fail-on-revert oracle (the planted reversion is named in the docstring):

  1. a staged config is accepted and reaches the writer (config overlay + the rule profile actually in force)        — revert: drop the overlay
  2. an unmarked run without a rule profile refuses `run_rule_profile_required`                                      — revert: default the profile to False
  3. an unmarked run without a horizon (absent or explicit null) refuses `run_horizon_required`                      — revert: default the horizon to DEFAULT_HORIZON
  4. a test slice is unaffected: no profile / horizon needed, and a century config beside a marker is refused        — revert: apply the guard to slices
  5. a malformed component is refused by name (shape, types, naive/inverted/out-of-domain horizon, deferral w/o final rules)
  6. a staged value that contradicts an explicit ctx.config value is refused, never merged
  7. the staged config is bound by the manifest digest: a config edited after dispatch is refused
  8. (OD-1, SR-OD1-NUMERICAL) the numeric-result policy is an EXPLICIT staged value: a final-rules run with no `result_policy` refuses `run_result_policy_required`,
     a staged policy reaches the writer config (so the manifest step binds it), an unknown one is refused, and a contradiction with ctx.config is refused  — revert: default the policy

SYNTHETIC bounds only: the real horizon is life-event derived and appears in no code, test or commit text.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pipeline.orchestrator.writers.ka_gochara_v5 as writer_mod  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec, SubStep  # noqa: E402
from services.gochara_kernel import rule_registry as rr  # noqa: E402

from .test_c46_v5_test_slice import _ManifestConn, _marker  # noqa: E402

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
START, END = "2001-01-01T00:00:00+00:00", "2051-01-01T00:00:00+00:00"
HORIZON = (datetime(2001, 1, 1, tzinfo=timezone.utc), datetime(2051, 1, 1, tzinfo=timezone.utc))


def _component(**over):
    base = {"schema": writer_mod.CENTURY_CONFIG_SCHEMA, "final_rules": True, "defer_in_build_verify": False, "horizon": [START, END],
            "result_policy": "window_qualification/1"}
    base.update(over)
    return base


def _ctx(manifest=None, dry_run=False, **config) -> ContextSpec:
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_ManifestConn(manifest),
                       config={"chart_id": CHART_ID, **config}, dry_run=dry_run)


def _century(**over):
    return {writer_mod.CENTURY_CONFIG_KEY: _component(**over)}


# ── 1. accepted and passed through ────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("final_rules,defer", [(True, False), (True, True), (False, False)])
def test_a_staged_century_config_reaches_the_writer_config_and_the_rule_profile(monkeypatch, final_rules, defer):
    """The overlay hands the writer exactly what was staged, and `run_substep` runs the substep proper under that profile (the contextvar the rule registry reads)."""
    manifest = _century(final_rules=final_rules, defer_in_build_verify=defer)
    resolved = writer_mod._resolve_run_config(_ctx(manifest))
    assert resolved.config["gochara_v5_final_rules"] is final_rules
    assert resolved.config["gochara_v5_defer_in_build_verify"] is defer
    assert resolved.config["horizon"] == HORIZON and writer_mod._effective_horizon(resolved, None) == HORIZON
    assert resolved.config["result_policy"] == "window_qualification/1"                  # OD-1: the staged policy reaches the manifest step's `ctx.config.get("result_policy")`
    assert len(writer_mod.GocharaV5Writer().plan_substeps(_ctx(manifest))) == 298            # the full, unsliced plan

    seen = {}
    monkeypatch.setattr(writer_mod, "_ephe_path", lambda ctx: "ephe")
    monkeypatch.setattr(writer_mod.GocharaV5Writer, "_run_resolved_substep",
                        lambda self, ctx, step, chart_id: seen.update(profile=rr._FINAL_RULES.get(), config=dict(ctx.config)) or "ran")
    assert writer_mod.GocharaV5Writer().run_substep(_ctx(manifest), SubStep(key=writer_mod.RULES_SUBSTEP, label="rules")) == "ran"
    assert seen["profile"] is final_rules and seen["config"]["gochara_v5_defer_in_build_verify"] is defer and seen["config"]["horizon"] == HORIZON


# ── 2-3. an unmarked run without an explicit profile / horizon refuses ──────────────────────────────────────────────────────────────────────

def test_an_unmarked_run_without_a_rule_profile_refuses_by_name(monkeypatch):
    """Claim 2: an absent `gochara_v5_final_rules` on a run that is not a test slice — it would have run the measuring profile. (An explicit null is not a name: the
    rule registry already refuses it as 'must be a boolean'.)"""
    with pytest.raises(writer_mod.RunProfileRefusal, match="run_rule_profile_required"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({}, horizon=HORIZON))
    monkeypatch.setattr(writer_mod, "_ephe_path", lambda ctx: "ephe")
    with pytest.raises(writer_mod.RunProfileRefusal, match="run_rule_profile_required"):
        writer_mod.GocharaV5Writer().run_substep(_ctx({}, horizon=HORIZON), SubStep(key=writer_mod.RULES_SUBSTEP, label="rules"))


@pytest.mark.parametrize("config", [{"gochara_v5_final_rules": False}, {"gochara_v5_final_rules": True, "horizon": None}])
def test_an_unmarked_run_without_a_horizon_refuses_by_name(monkeypatch, config):
    """Claim 3: an absent horizon — and an explicit null, which main would have left to fail downstream — on a run that is not a test slice."""
    with pytest.raises(writer_mod.RunHorizonRefusal, match="run_horizon_required"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({}, **config))
    monkeypatch.setattr(writer_mod, "_ephe_path", lambda ctx: "ephe")
    with pytest.raises(writer_mod.RunHorizonRefusal, match="run_horizon_required"):
        writer_mod.GocharaV5Writer().run_substep(_ctx({}, **config), SubStep(key=writer_mod.RULES_SUBSTEP, label="rules"))


def test_an_unmarked_run_naming_both_is_not_refused_and_a_dry_run_executes_nothing_so_is_not_guarded():
    named = _ctx({}, gochara_v5_final_rules=False, horizon=HORIZON)
    assert writer_mod._resolve_run_config(named) is named                           # nothing staged, nothing to overlay
    assert len(writer_mod.GocharaV5Writer().plan_substeps(named)) == 298
    bare_dry_run = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None, config={"chart_id": CHART_ID}, dry_run=True)
    assert len(writer_mod.GocharaV5Writer().plan_substeps(bare_dry_run)) == 298


def test_the_refusal_comes_after_the_configuration_checks_so_a_misprovisioned_job_still_fails_before_any_database_use():
    """The ephemeris check stays the first thing a substep does (c47's contract): the guard reads build_runs, so it must not run before it."""
    class Untouched:
        row_factory = None

        def __getattr__(self, name):
            raise AssertionError(f"connection used: {name}")
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="x", db_conn=Untouched(), dry_run=False,
                      config={"chart_id": CHART_ID, "ephe_path": "/nonexistent-ephe-dir"})
    with pytest.raises(writer_mod.EphemerisConfigRefusal):
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.RULES_SUBSTEP, label="rules"))


# ── 4. a test slice is unaffected ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_test_slice_needs_neither_profile_nor_horizon_and_takes_no_century_config(monkeypatch):
    """Claim 4: the measuring build (a test slice) sets its scope in its marker and always runs the measuring rules, exactly as before."""
    marked = {writer_mod.TEST_SLICE_KEY: _marker()}
    plan = writer_mod.GocharaV5Writer().plan_substeps(_ctx(marked))
    assert 0 < len(plan) < 298
    monkeypatch.setattr(writer_mod, "_ephe_path", lambda ctx: "ephe")
    seen = {}
    monkeypatch.setattr(writer_mod.GocharaV5Writer, "_run_resolved_substep",
                        lambda self, ctx, step, chart_id: seen.update(profile=rr._FINAL_RULES.get()) or "ran")
    writer_mod.GocharaV5Writer().run_substep(_ctx(marked), SubStep(key=writer_mod.RULES_SUBSTEP, label="rules"))
    assert seen["profile"] is False
    with pytest.raises(writer_mod.CenturyConfigRefusal, match="takes no century config"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({**marked, **_century()}))


# ── 5. a malformed component is refused by name ───────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,component", [
    ("not an object", ["x"]),
    ("an extra field", {**_component(), "extra": 1}),
    ("a missing field", {k: v for k, v in _component().items() if k != "horizon"}),
    ("the wrong schema", _component(schema="gochara_v5_century_config/1")),
    ("a missing result policy", {k: v for k, v in _component().items() if k != "result_policy"}),
    ("an unknown result policy", _component(result_policy="all_null")),
    ("a null result policy", _component(result_policy=None)),
    ("a non-boolean profile", _component(final_rules="true")),
    ("a non-boolean deferral", _component(defer_in_build_verify=1)),
    ("deferral without the final rules", _component(final_rules=False, defer_in_build_verify=True)),
    ("a horizon that is not a pair", _component(horizon=[START])),
    ("a naive horizon", _component(horizon=["2001-01-01T00:00:00", END])),
    ("an inverted horizon", _component(horizon=[END, START])),
    ("an unparseable horizon", _component(horizon=["not-a-date", END])),
    ("a horizon outside the substrate domain", _component(horizon=["1900-01-01T00:00:00+00:00", END])),
])
def test_a_malformed_century_config_is_refused_by_name(name, component):
    """Claim 5: refused with a NAMED error — the writer's CenturyConfigRefusal, or the horizon module's own domain refusal — never a TypeError/KeyError from a guess."""
    from services.gochara_kernel import horizon as gk_horizon
    named = (writer_mod.CenturyConfigRefusal, gk_horizon.HorizonOutsideSubstrateDomain, gk_horizon.HorizonStartBeforeSubstrateDomain)
    with pytest.raises(named):
        writer_mod.validate_century_config(component)
    with pytest.raises(named):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({writer_mod.CENTURY_CONFIG_KEY: component}))


def test_the_canonical_form_is_utc_and_a_fixed_point():
    shifted = writer_mod.validate_century_config(_component(horizon=["2001-01-01T05:30:00+05:30", END]))
    assert shifted["horizon"] == [START, END]
    assert writer_mod.validate_century_config(shifted) == shifted


# ── 6. a contradiction with an explicit ctx.config value is refused ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("config", [{"gochara_v5_final_rules": False}, {"gochara_v5_defer_in_build_verify": True},
                                    {"horizon": (datetime(2002, 1, 1, tzinfo=timezone.utc), HORIZON[1])},
                                    {"result_policy": "all_null_candidate/1"}])
def test_a_staged_value_that_contradicts_the_explicit_config_is_refused_never_merged(config):
    with pytest.raises(writer_mod.CenturyConfigRefusal, match="contradicts the staged value"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx(_century(), **config))
    agreeing = _ctx(_century(), gochara_v5_final_rules=True, gochara_v5_defer_in_build_verify=False, horizon=list(HORIZON), result_policy="window_qualification/1")
    assert writer_mod._resolve_run_config(agreeing).config["horizon"] == HORIZON


# ── 7. the staged config is bound by the manifest digest ──────────────────────────────────────────────────────────────────────────────────

def test_a_century_config_edited_after_dispatch_is_refused_not_read():
    manifest = _century()
    stored_digest = writer_mod._manifest_digest(manifest)
    edited = _century(final_rules=False)
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_ManifestConn(edited, digest=stored_digest),
                      config={"chart_id": CHART_ID}, dry_run=False)
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest_digest"):
        writer_mod.GocharaV5Writer().plan_substeps(ctx)
    ok = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_ManifestConn(manifest, digest=stored_digest),
                     config={"chart_id": CHART_ID}, dry_run=False)
    assert len(writer_mod.GocharaV5Writer().plan_substeps(ok)) == 298


# ── 8. OD-1: the numeric-result policy is explicit on a final-rules run ───────────────────────────────────────────────────────────────────────

def test_a_final_rules_run_without_an_explicit_result_policy_refuses_by_name(monkeypatch):
    """Claim 8a: a run that is not a test slice, names the final rules and a horizon but NO result_policy (no century config) would have bound the all-null DEFAULT — refused at
    plan time and at the first substep. (revert: default the policy in `_resolve_run_config` — both raises vanish)"""
    config = {"gochara_v5_final_rules": True, "horizon": HORIZON}
    with pytest.raises(writer_mod.RunResultPolicyRefusal, match="run_result_policy_required"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({}, **config))
    monkeypatch.setattr(writer_mod, "_ephe_path", lambda ctx: "ephe")
    with pytest.raises(writer_mod.RunResultPolicyRefusal, match="run_result_policy_required"):
        writer_mod.GocharaV5Writer().run_substep(_ctx({}, **config), SubStep(key=writer_mod.RULES_SUBSTEP, label="rules"))
    with pytest.raises(writer_mod.RunResultPolicyRefusal, match="run_result_policy_required"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({}, **config, result_policy=None))      # an explicit null is not a name either


@pytest.mark.parametrize("policy", ["all_null_candidate/1", "window_qualification/1"])
def test_a_final_rules_run_naming_either_policy_is_accepted_and_the_measuring_default_is_untouched(policy):
    """Claim 8b: both NAMED policies are valid explicit choices (all-null stays valid); a measuring-profile unmarked run (final_rules False) keeps the default and needs none."""
    named = _ctx({}, gochara_v5_final_rules=True, horizon=HORIZON, result_policy=policy)
    assert writer_mod._resolve_run_config(named) is named
    measuring = _ctx({}, gochara_v5_final_rules=False, horizon=HORIZON)
    assert writer_mod._resolve_run_config(measuring) is measuring
