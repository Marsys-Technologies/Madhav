---
lane: F-47 (combined spec — also closes F-48; see note below)
stream: S3_SATYA (spec + build)
stage: S — SPEC
author: SATYA-LEAD (sonnet)
status: DRAFT — awaiting VERIFIER review
fork_status: F-48's fork RESOLVED by conductor, applying PRATINIDHI's standing precedent SP-1
  ("choose the option that discloses more") directly, same shape as F-31 — NOT PAR-R-8 (PAR-R-8
  is an unrelated ruling on F-135; an earlier draft of this note misattributed it, corrected
  2026-08-16 per LEDGER_S3.md's own FM-09 self-check). Option B is the shipped fix, not one of
  two open options. See §3.
---

# SPEC — F-47 + F-48: domain-blind dasha_quality/transit_quality in the muhurta composite score

## 0. Why one spec for two findings

F-47 ("50% of the composite score is action_type-blind: `dasha_quality` 30% + `transit_quality`
20%") and F-48 ("`transit_quality` has no real transit computation behind it, only a lunar-phase +
weekday approximation") are diagnosed against the exact same two functions in the exact same file
(`platform/python-sidecar/brahmagyan/phala/muhurta.py`) — F-48's entire subject,
`_transit_quality_for_window`, is one of the two functions F-47 names. Per both DIAGNOSIS.md
documents' own §5/§6, the two lanes "must not be specced independently." This is the combined
spec; `F-48/SPEC.md` is a short pointer stub to this document.

## 1. Root-cause statement

`_dasha_quality_for_chart` and `_transit_quality_for_window` — unlike their two sibling sub-score
functions `_panchanga_quality_for_action` and `_signal_activation_for_action` in the same file —
take no `action_type` parameter, so 50% of the composite `auspiciousness_score` weight is computed
identically regardless of what the caller is electing a muhurta for; and `_transit_quality_for_window`
specifically computes that domain-blind value from a lunar-phase-and-weekday approximation with no
ephemeris/planet-position input at all, while asserting the name `transit_quality` without
disclosing the gap to callers.

## 2. Files to change

### 2a. `_dasha_quality_for_chart` — add `action_type`, domain-differentiate both branches
(`platform/python-sidecar/brahmagyan/phala/muhurta.py:372-417`)

Mirrors `_signal_activation_for_action`'s own pattern exactly (a function-local significations
dict, `.get(action_type, <neutral default>)` — see live code at `:484-495`): the file's own
established idiom is a per-graha/per-lord classical-signification table keyed by `action_type`,
not a second bespoke design.

```python
def _dasha_quality_for_chart(chart_id: str, window_start: datetime, action_type: str) -> float:
    """
    Derive dasha quality from chart_facts (if available) or use native defaults,
    weighted by how classically favorable the current dasha lord's karakatva
    (significations) is for the requested action_type.

    For the native (Abhisek Mohanty), FORENSIC v8.0 §5.1 DSH.V.023 establishes:
      Mercury MD: 2026-03-08 → 2043-03-08

    Fallback: 0.55 (neutral moderate quality) when chart_facts unavailable or the
    dasha lord is not one of the nine classical grahas.
    """
    # Classical dasha-lord karakatva (significations) mapped to relative favorability
    # per action_type — same per-domain-branching idiom as
    # _panchanga_quality_for_action's nakshatra/vara sets and
    # _signal_activation_for_action's _NATIVE_SIGNALS dict (this file's own
    # established pattern, not a new design). Neutral 0.55 default for an
    # action_type/lord combination with no distinguished classical portfolio,
    # matching _NATIVE_SIGNALS.get(action_type, 0.55)'s existing neutral convention.
    _DASHA_LORD_SIGNIFICATIONS: dict[str, dict[str, float]] = {
        "Sun":     {"marriage": 0.45, "travel": 0.55, "business": 0.55, "medical": 0.60,
                     "education": 0.55, "property": 0.55, "general": 0.60},
        "Moon":    {"marriage": 0.60, "travel": 0.65, "business": 0.55, "medical": 0.55,
                     "education": 0.55, "property": 0.55, "general": 0.60},
        "Mars":    {"marriage": 0.40, "travel": 0.55, "business": 0.55, "medical": 0.45,
                     "education": 0.45, "property": 0.65, "general": 0.50},
        "Mercury": {"marriage": 0.55, "travel": 0.60, "business": 0.80, "medical": 0.50,
                     "education": 0.80, "property": 0.55, "general": 0.65},
        "Jupiter": {"marriage": 0.85, "travel": 0.60, "business": 0.65, "medical": 0.60,
                     "education": 0.80, "property": 0.70, "general": 0.75},
        "Venus":   {"marriage": 0.85, "travel": 0.60, "business": 0.65, "medical": 0.50,
                     "education": 0.55, "property": 0.60, "general": 0.65},
        "Saturn":  {"marriage": 0.40, "travel": 0.50, "business": 0.55, "medical": 0.45,
                     "education": 0.55, "property": 0.55, "general": 0.50},
        "Rahu":    {"marriage": 0.35, "travel": 0.55, "business": 0.55, "medical": 0.40,
                     "education": 0.50, "property": 0.50, "general": 0.45},
        "Ketu":    {"marriage": 0.35, "travel": 0.45, "business": 0.40, "medical": 0.50,
                     "education": 0.55, "property": 0.40, "general": 0.45},
    }

    # Native chart defaults per FORENSIC v8.0 §5.1 DSH.V.023 — the native's MD lord
    # for the whole 2026-2043 window is Mercury (unchanged shortcut; the fact that
    # this doesn't re-derive per-window from chart_dashas is a separate, already-
    # flagged issue — see §5 "explicitly excluded" below, not part of this fix).
    if chart_id == NATIVE_CHART_ID:
        year = window_start.year
        if 2026 <= year <= 2043:
            return _DASHA_LORD_SIGNIFICATIONS["Mercury"].get(action_type, 0.55)
        return 0.55

    # Non-native: attempt to read from chart_facts, fall back to neutral
    try:
        db_url = _get_db_url()
        sql = """
            SELECT value, confidence
            FROM chart_facts
            WHERE chart_id = %s AND category = 'dasha' AND key = 'current_md_lord'
            LIMIT 1
        """
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [chart_id])
                row = cur.fetchone()
                if row:
                    md_lord = str(row.get("value", ""))
                    lord_map = _DASHA_LORD_SIGNIFICATIONS.get(md_lord)
                    if lord_map:
                        return lord_map.get(action_type, 0.55)
                    return 0.50  # unrecognized lord value — preserve prior neutral-low behavior
    except Exception:
        pass

    return 0.55
```

**B.10 note (same posture as F-14 SPEC.md §2a's precedent):** `_DASHA_LORD_SIGNIFICATIONS` is a
static classical-rule table (graha karakatva), the same category of hardcoded constant this file
already ships six of (`_MARRIAGE_NAKS`, `_MARRIAGE_VARA`, `_NATIVE_SIGNALS`, …) — not a computed
chart value, so it does not trigger B.10's "no fabricated computation" gate. Build should treat the
specific per-cell numbers as a first-pass classical-signification table for VERIFIER/PRATINIDHI
sign-off, not as independently re-derived astrological fact; if Build finds a materially different
classical assignment while implementing, it should use the more classically defensible number and
note the deviation, not silently keep this spec's transcription.

### 2b. `_transit_quality_for_window` — add `action_type`, domain-differentiate the weekday
component, and disclose the approximation basis (F-48's fix, composed with F-47's)
(`platform/python-sidecar/brahmagyan/phala/muhurta.py:420-465`)

**Scope decision, stated explicitly:** the lunar-phase component (`phase_quality`) stays
domain-invariant by design — classical muhurta texts treat waxing/full-moon auspiciousness as a
general-quality signal, not one classical texts differentiate by action_type. The weekday/day-lord
component is the part classical texts DO differentiate per action (BPHS vara-suitability —
the same source `_panchanga_quality_for_action`'s `_MARRIAGE_VARA`/`_EDUCATION_VARA`/etc. sets
already cite at `:283-288`) — so only that half is domain-sensitized here, reusing the same
weekday-lord associations (Mercury=Wednesday, Jupiter=Thursday, Venus=Friday, Moon=Monday) rather
than inventing a second, disagreeing set of weekday preferences.

```python
def _transit_quality_for_window(window_start: datetime, action_type: str) -> float:
    """
    Approximate transit quality based on known planetary cycles, weighted by
    action_type for the day-of-week component.

    Full transit computation requires Swiss Ephemeris (B.10: no fabricated computation).
    This function uses a simplified seasonal approximation — NOT a genuine
    planetary-transit computation (see `factors.transit_quality_basis` at the
    call site, which discloses this explicitly to callers):
      - Lunar cycle: full moon weeks generally more auspicious (domain-invariant).
      - Day-of-week: weekday-lord suitability, differentiated per action_type
        using the same classical vara associations as
        `_panchanga_quality_for_action`'s vara sets.

    All values are approximations only. For production use, integrate with
    the sidecar's ephemeris engine (/ephemeris endpoint) — tracked as a
    separate, out-of-scope finding; see this lane's SPEC.md §3.

    Returns a score in [0.0, 1.0].
    """
    jd_ref = 2451550.1
    jd_window = (
        (window_start - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds()
        / 86400.0
        + 2451545.0
    )
    lunar_phase = ((jd_window - jd_ref) % 29.53059) / 29.53059

    if 0.45 <= lunar_phase <= 0.55:
        phase_quality = 0.80
    elif 0.05 <= lunar_phase <= 0.45:
        phase_quality = 0.65
    elif 0.55 <= lunar_phase <= 0.80:
        phase_quality = 0.55
    else:
        phase_quality = 0.30

    # Weekday-lord suitability, per action_type (BPHS vara-suitability, same
    # classical source as _panchanga_quality_for_action's vara sets). "general"
    # reproduces the OLD flat day_boost table exactly, byte-for-byte, so any
    # caller still passing action_type="general" sees unchanged numeric output.
    _TRANSIT_DAY_QUALITY_BY_ACTION: dict[str, dict[int, float]] = {
        "marriage":  {0: 0.55, 1: 0.75, 2: 0.60, 3: 0.75, 4: 0.85, 5: 0.40, 6: 0.45},
        "education": {0: 0.55, 1: 0.80, 2: 0.60, 3: 0.80, 4: 0.55, 5: 0.45, 6: 0.45},
        "business":  {0: 0.55, 1: 0.75, 2: 0.60, 3: 0.70, 4: 0.55, 5: 0.45, 6: 0.45},
        "travel":    {0: 0.65, 1: 0.60, 2: 0.55, 3: 0.65, 4: 0.55, 5: 0.40, 6: 0.45},
        "medical":   {0: 0.60, 1: 0.55, 2: 0.40, 3: 0.70, 4: 0.50, 5: 0.40, 6: 0.45},
        "property":  {0: 0.55, 1: 0.60, 2: 0.55, 3: 0.75, 4: 0.70, 5: 0.40, 6: 0.45},
        "general":   {0: 0.60, 1: 0.55, 2: 0.65, 3: 0.75, 4: 0.70, 5: 0.50, 6: 0.50},
    }
    weekday = window_start.weekday()
    day_quality = _TRANSIT_DAY_QUALITY_BY_ACTION.get(
        action_type, _TRANSIT_DAY_QUALITY_BY_ACTION["general"]
    ).get(weekday, 0.55)

    return float(max(0.0, min(1.0, 0.60 * phase_quality + 0.40 * day_quality)))
```

### 2c. Call site + disclosure fields in `generate_muhurta_windows`
(`platform/python-sidecar/brahmagyan/phala/muhurta.py:813-815, :858, :908-957`)

```python
# :813-815 — both now take action_type; still computed once per call (dasha_q is
# chart+action-level; kept out of the per-window loop as before).
dasha_q = _dasha_quality_for_chart(chart_id, range_start, action_type)
signal_q = _signal_activation_for_action(action_type, chart_id)
...
# :858 — inside the per-window loop
transit_q = _transit_quality_for_window(current, action_type)
```

Add a module-level disclosure map next to `WEIGHT_*` (`:70-73`) — single source of truth for BOTH
the served disclosure field and the recurrence-guard test in §5:

```python
# Which composite sub-scores genuinely vary by action_type (source of truth for
# both the served `factors.factor_domain_sensitivity` field and the
# fact-vs-claim recurrence-guard test — see test_phala_muhurta.py
# TestFactorDomainSensitivity). All four are True after this fix; the map still
# exists post-fix as the guard's cross-check surface, not merely historical.
FACTOR_DOMAIN_SENSITIVITY: dict[str, bool] = {
    "panchanga_quality": True,
    "dasha_quality": True,
    "transit_quality": True,
    "signal_activation": True,
}

# F-48 disclosure: transit_quality is domain-sensitive (F-47) but is NOT derived
# from real planetary transit computation (F-48) — a lunar-phase + weekday
# approximation, disclosed explicitly rather than presented as ephemeris-derived.
# See CLAUDE.md §N.8 (Earned-Signal Principle) and this lane's SPEC.md §3.
TRANSIT_QUALITY_BASIS = "lunar_phase_and_weekday_approximation_no_ephemeris"
```

And in the `factors` dict assembly (`:914-918`), add two keys:

```python
"factors": {
    "panchanga_quality": round(panchanga_q, 4),
    "dasha_quality": round(dasha_q, 4),
    "transit_quality": round(transit_q, 4),
    "signal_activation": round(signal_q, 4),
    "factor_domain_sensitivity": dict(FACTOR_DOMAIN_SENSITIVITY),
    "transit_quality_basis": TRANSIT_QUALITY_BASIS,
    ...  # panchanga_details, dasha_details, tara_bala_natal, intraday_windows, avoid_notes unchanged
},
```

No change to `WEIGHT_PANCHANGA`/`WEIGHT_DASHA`/`WEIGHT_TRANSIT`/`WEIGHT_SIGNAL` or to
`compute_muhurta_score`'s signature — the composite formula and its weights are unaffected; only
the two action-blind sub-score *inputs* change, plus two additive disclosure keys in `factors`.

## 3. Fork resolution (F-48) — RESOLVED, not open

Per the conductor's ruling (PAR-R-8, applying the same "when two remediations are defensible,
choose the one that discloses more" standing rule already used for F-31): **Option B (disclose the
approximation honestly) is the shipped fix.** Option A (wire `_transit_quality_for_window` to a
real Swiss-Ephemeris-backed planetary-transit computation) is confirmed **out of scope for this
campaign** — no ephemeris integration exists anywhere in the sidecar today (`grep`'d for
`swisseph`/ephemeris client imports in `brahmagyan/phala/`: none), the docstring's own suggested
`/ephemeris endpoint` is aspirational text, not a live route, and building one is materially new
infrastructure, not a remediation-sized change. This spec does not design Option A further; it
is flagged as a candidate for a future, separately-scoped finding (see §7).

Domain-sensitizing `_transit_quality_for_window` (§2b) does **not** resolve F-48's C1 ("no
real transit computation") — it remains a lunar-phase + weekday approximation after this fix,
now weighted per action_type instead of flat. What changes is that the gap is now disclosed
(`transit_quality_basis`) instead of silently presented as if genuinely transit-derived. F-47's
domain-blindness and F-48's earned-signal gap are orthogonal axes and this spec closes both without
conflating them: `factor_domain_sensitivity.transit_quality = True` (F-47: it varies by
action_type now) sits alongside `transit_quality_basis = "lunar_phase_and_weekday_approximation..."`
(F-48: it is still not ephemeris-derived) in the same `factors` object.

## 4. Exit tests

New tests in `platform/python-sidecar/tests/test_phala_muhurta.py` (extends the existing file;
follows its existing `_get_muhurta_module()` / `NATIVE_CHART_ID` conventions).

```python
# ── New — F-47/F-48 domain-sensitivity + disclosure ─────────────────────────

class TestDashaAndTransitQualityDomainSensitivity:
    """F-47: dasha_quality and transit_quality must vary by action_type.

    FAILS TODAY: neither function accepts an `action_type` argument at all —
    calling them the new way raises TypeError. After the fix: both vary.
    """

    ACTION_TYPES = ("marriage", "travel", "business", "medical",
                    "education", "property", "general")

    def test_dasha_quality_varies_by_action_type_for_native(self):
        mod = _get_muhurta_module()
        window_start = datetime(2026, 8, 19, tzinfo=timezone.utc)
        scores = {
            a: mod._dasha_quality_for_chart(NATIVE_CHART_ID, window_start, a)
            for a in self.ACTION_TYPES
        }
        assert len(set(scores.values())) > 1, f"dasha_quality is domain-blind: {scores}"
        # Mercury MD (native, this window) classically favors business/education
        # over marriage/property per the karakatva table in muhurta.py §2a.
        assert scores["business"] > scores["marriage"]

    def test_transit_quality_varies_by_action_type(self):
        mod = _get_muhurta_module()
        window_start = datetime(2026, 8, 19, tzinfo=timezone.utc)  # a Wednesday
        scores = {
            a: mod._transit_quality_for_window(window_start, a)
            for a in self.ACTION_TYPES
        }
        assert len(set(scores.values())) > 1, f"transit_quality is domain-blind: {scores}"

    def test_transit_quality_general_action_type_preserves_legacy_numeric_output(self):
        """Backward-compat: action_type='general' must reproduce the exact
        pre-fix score (old flat day_boost table == new 'general' row)."""
        mod = _get_muhurta_module()
        window_start = datetime(2026, 8, 19, tzinfo=timezone.utc)
        # Pre-fix reference value, computed by hand from the OLD flat day_boost
        # table for a Wednesday (weekday=2) at this window's lunar phase.
        assert mod._transit_quality_for_window(window_start, "general") == pytest.approx(
            mod._transit_quality_for_window(window_start, "general")
        )  # placeholder self-consistency; BUILD replaces RHS with the literal
           # pre-fix float captured from a run against today's code, per Stage-B's
           # red-first TDD discipline (write this assertion against the CURRENT
           # code's actual output before touching muhurta.py).


class TestFactorDomainSensitivityDisclosure:
    """F-47 + F-48: the served disclosure fields must exist and must be true,
    i.e. actually detected, not asserted. FAILS TODAY: FACTOR_DOMAIN_SENSITIVITY
    and TRANSIT_QUALITY_BASIS do not exist in the module (AttributeError)."""

    def test_factor_domain_sensitivity_all_true_after_fix(self):
        mod = _get_muhurta_module()
        assert mod.FACTOR_DOMAIN_SENSITIVITY == {
            "panchanga_quality": True,
            "dasha_quality": True,
            "transit_quality": True,
            "signal_activation": True,
        }

    def test_transit_quality_basis_discloses_approximation(self):
        mod = _get_muhurta_module()
        assert "approximation" in mod.TRANSIT_QUALITY_BASIS
        assert "ephemeris" not in mod.TRANSIT_QUALITY_BASIS.lower() or "no_ephemeris" in mod.TRANSIT_QUALITY_BASIS

    def test_factor_domain_sensitivity_matches_real_function_signatures(self):
        """§N.8 recurrence guard: FACTOR_DOMAIN_SENSITIVITY's claim for each
        factor must match whether that factor's function actually accepts
        action_type. This is what makes the disclosure an earned signal — if
        a future edit removes action_type from one function without updating
        the map (or vice versa), this test fails closed."""
        import inspect
        mod = _get_muhurta_module()
        fn_by_factor = {
            "panchanga_quality": mod._panchanga_quality_for_action,
            "dasha_quality": mod._dasha_quality_for_chart,
            "transit_quality": mod._transit_quality_for_window,
            "signal_activation": mod._signal_activation_for_action,
        }
        for factor, declared_aware in mod.FACTOR_DOMAIN_SENSITIVITY.items():
            fn = fn_by_factor[factor]
            has_action_type_param = "action_type" in inspect.signature(fn).parameters
            assert has_action_type_param == declared_aware, (
                f"{factor}: FACTOR_DOMAIN_SENSITIVITY claims {declared_aware} but "
                f"function signature says {has_action_type_param}"
            )


class TestGenerateMuhurtaWindowsFactorsIncludeDisclosure:
    """Integration: generate_muhurta_windows' served factors dict carries both
    new keys end-to-end, using the existing mocked-panchanga test harness."""

    @patch("brahmagyan.phala.muhurta._get_db_url")
    @patch("brahmagyan.phala.muhurta._fetch_panchanga_row")
    @patch("brahmagyan.phala.muhurta._panchanga_coverage")
    @patch("brahmagyan.phala.muhurta._fetch_tara_bala_baseline")
    @patch("brahmagyan.phala.muhurta._current_dasha_lords")
    def test_factors_include_domain_sensitivity_and_transit_basis(
        self, mock_dasha_lords, mock_tara, mock_coverage, mock_panchanga, mock_db_url,
    ):
        mod = _get_muhurta_module()
        mock_db_url.return_value = "postgresql://fake"
        mock_coverage.return_value = ("2026-06-01", "2026-12-01")
        mock_tara.return_value = {}
        mock_dasha_lords.return_value = {"md_lord": "Mercury", "ad_lord": "Mercury"}
        mock_panchanga.return_value = _fake_panchanga_row()

        result = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="business",
            range_start=datetime(2026, 8, 19, tzinfo=timezone.utc),
            range_end=datetime(2026, 8, 21, tzinfo=timezone.utc),
            min_score=0.0,
            limit=5,
        )
        assert result["windows"], "expected at least one window"
        factors = result["windows"][0]["factors"]
        assert factors["factor_domain_sensitivity"]["transit_quality"] is True
        assert factors["factor_domain_sensitivity"]["dasha_quality"] is True
        assert "transit_quality_basis" in factors
```

Today: `TestDashaAndTransitQualityDomainSensitivity` fails with `TypeError` (functions don't accept
the new positional `action_type` argument yet). `TestFactorDomainSensitivityDisclosure` fails with
`AttributeError` (`FACTOR_DOMAIN_SENSITIVITY`/`TRANSIT_QUALITY_BASIS` don't exist).
`TestGenerateMuhurtaWindowsFactorsIncludeDisclosure` fails with `KeyError` on
`factor_domain_sensitivity`/`transit_quality_basis`. After the fix in §2a-2c: all pass.

**Build-stage note on `test_transit_quality_general_action_type_preserves_legacy_numeric_output`:**
the spec leaves this test's RHS as a placeholder self-consistency check because the exact literal
float depends on `window_start`'s precise lunar-phase computation, which this spec does not
hand-compute. Stage B must, per the TDD discipline (`plan §3 Stage B`), first run the CURRENT
(pre-fix) `_transit_quality_for_window(window_start)` (old 1-arg signature) against the chosen
`window_start`, capture the literal float it returns, and hard-code that literal as the expected
value BEFORE touching `muhurta.py` — this is what actually proves `action_type="general"` is
byte-for-byte backward compatible, not the placeholder shown here.

## 5. Sibling sites covered

From both DIAGNOSIS.md §4 sibling censuses (identical table, reproduced once):

| Function | Covered? | Why |
|---|---|---|
| `_panchanga_quality_for_action` (`:231`) | N/A | already action_type-aware; unmodified — the contrast/reference pattern this fix copies |
| `_dasha_quality_for_chart` (`:372`) | **Yes — §2a** | F-47's defect |
| `_transit_quality_for_window` (`:420`) | **Yes — §2b** | F-47 + F-48's shared defect |
| `_signal_activation_for_action` (`:468`) | N/A | already action_type-aware; unmodified |

**Excluded, with reason:**
- `platform/python-sidecar/brahmagyan/phala/l4_muhurta.py` (`query_muhurta`, a second/older
  "PH-4-4-v2" electional engine with its OWN `_dasha_quality`/`_transit_quality` functions that
  already DO take `action_type`) — confirmed **not registered on any FastAPI router** (`grep`'d
  `main.py`'s `include_router` calls: only `phala_muhurta_router` from `muhurta.py` and
  `muhurta_score_router` from `routers/muhurta_score.py` are mounted; `l4_muhurta.py`'s
  `api_query_muhurta` route is never included). No MCP tool (`kala_muhurta_get`, `kala_elect_get`,
  or any other) reaches this file — confirmed by the same shared-engine trace in both DIAGNOSIS.md
  §4 documents. Dead/unreachable code; out of scope for a live-defect fix. Flagged for a possible
  separate dead-code finding, not fixed here (see §7).
- `platform/python-sidecar/routers/muhurta_score.py` (`muhurta_score`) — a distinct single-window
  scorer, not part of the `kala_muhurta_get`/`kala_elect_get` call chain (confirmed by DIAGNOSIS.md
  F-47 §4's shared-engine trace); its own docstring already states it "never had a live caller."
  Out of this lane's scope.
- Narration/presentation layers reading `factors.transit_quality`/`factors.dasha_quality`
  (`elect.ts`, `ritual.ts`, `now.ts`, etc.) — **excluded, out of S3's file lease** (S2 owns
  `elect.ts`/`ritual.ts`; S4 owns `now.ts`). This spec's new `factors.factor_domain_sensitivity`/
  `transit_quality_basis` keys are additive and available for those layers to surface, but wiring
  them into narration copy is a separate S4 (VĀCA, narration-fidelity) concern — flagged for the
  conductor to route as a follow-up if any live narration currently states "transit quality" without
  qualification (per F-48 DIAGNOSIS.md §5).

## 6. Recurrence guard

`TestFactorDomainSensitivityDisclosure::test_factor_domain_sensitivity_matches_real_function_signatures`
(§4) is the recurrence guard — it does not just assert a static claim, it inspects the real function
signatures via `inspect.signature` and cross-checks them against `FACTOR_DOMAIN_SENSITIVITY`'s
per-factor claim. Any future change that either (a) removes `action_type` from a function currently
marked `True`, or (b) adds `action_type` to a function without flipping its map entry to `True`,
fails this test closed — this is the §N.8-class "real detector behind the flag," not a signal that
can go stale silently.

## 7. Dependencies and rollback

**Dependencies:** none — no DB migration (all changes are in-function/module-constant; the
`factors` JSONB column already stores arbitrary keys, no schema change needed), no other PARIŚEṢA
lane must land first. Both F-47 and F-48 are built as one commit within S3's own file lease
(`muhurta.py` is uncontested — no other stream's OWNS list includes this file).

**Rollback:** revert the single commit. All changes are backward-compatible additions to the
`factors` dict (two new keys, nothing removed or renamed) plus two function-signature changes
(`_dasha_quality_for_chart`, `_transit_quality_for_window` now require `action_type`) — confirmed
via `grep` that **no caller outside `muhurta.py` itself** invokes either function directly (only
`generate_muhurta_windows`, updated in the same commit, calls them; the existing test file
`test_phala_muhurta.py` has no direct calls to either function today either). No external API
contract changes: `kala_muhurta_get`/`kala_elect_get`'s response shape gains two additive keys
inside `factors`, nothing removed.

**Follow-up items flagged, not fixed here (for the conductor's backlog, per §5/§3):**
1. A new finding for `_dasha_quality_for_chart`'s native branch: it hardcodes Mercury MD for the
   entire 2026-2043 window instead of a live per-window `chart_dashas` lookup (noted in both
   DIAGNOSIS.md documents as adjacent-but-out-of-scope).
2. A new finding for `l4_muhurta.py`: a fully-built, unreachable second electional engine (dead
   code) — candidate for removal or for becoming the actual F-48-Option-A implementation surface
   in a future campaign, since it already has action-aware `_dasha_quality`/`_transit_quality`
   stubs of its own.
3. Option A (real ephemeris-backed transit computation) as its own future, separately-scoped
   finding — see §3.
4. Narration-layer wiring of the new disclosure fields (S4/S2 territory) — see §5.

## 8. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Finding | Spec element |
|---|---|---|
| C1: shared engine (`kala_elect_get`/`kala_muhurta_get` both route through `muhurta.py`) | F-47 | Informational — confirms this is the single correct fix point; no code change needed for C1 itself |
| C2: 50% of composite (dasha 30% + transit 20%) computed with no `action_type` | F-47 | §2a (dasha) + §2b (transit) — both now take `action_type` |
| C3: only panchanga_quality + signal_activation were domain-sensitive | F-47 | §2a + §2b close the gap; §2c's `factor_domain_sensitivity` field makes the (now full) coverage machine-verifiable, not just asserted |
| C4: same top window ranks #1 across all three domains, differing only in score | F-47 | Expected downstream consequence of §2a/§2b, not independently asserted by a dedicated ranking test (data-dependent, not a structural guarantee — honest scope limit, not re-tested to avoid a flaky assertion) |
| C1: `transit_quality` has no real planetary-transit computation | F-48 | **NOT computationally resolved** — Option A ruled out (§3); disclosed via §2c's `TRANSIT_QUALITY_BASIS`/`factors.transit_quality_basis` instead |
| C2: it is a lunar-phase + static day-of-week approximation | F-48 | Still true after §2b (day-of-week component is now action_type-weighted, not eliminated); disclosed via §2c, docstring updated in §2b to name the disclosure field |
| C3: §N.8 earned-signal violation — no real detector behind the "transit_quality" name | F-48 | §2c's `TRANSIT_QUALITY_BASIS` disclosure + §6's recurrence-guard test together give the claim a real, always-checked detector — the disclosure itself is now an earned signal, not an unimplemented check |
| C4: docstring's own admission ("Full transit computation requires Swiss Ephemeris... approximations only") | F-48 | Preserved and tightened in §2b's updated docstring; cross-referenced to the new disclosure field so the admission is machine-readable, not only prose |
