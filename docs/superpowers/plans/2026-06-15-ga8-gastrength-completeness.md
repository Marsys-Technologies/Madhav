# GA8 + ga_strength — L1 Relationship Completeness Amendment

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add every legitimately-computable relationship class not yet captured in ga_structural and fix three stubs in ga_strength, across all 30 vargas × 5 ayanamshas — no silent drops, FORENSIC 7/7 guarded.

**Architecture:** Two-writer coordinated pass. `ga_structural_writer.py` (3554 lines) extends its per-varga enumeration to include Rahu/Ketu, special points, house-lord matrix, karaka web, Kala Sarpa detection, graha yuddha, and combustion/retrograde as relational rows. `ga_strength_writer.py` (1033 lines) fixes three known stubs: nodal strength rows (line 188 skip), kala-bala day/night computation (line 230 hardcode), and drik-bala from aspect matrix (line 261 stub). All new rows are fully qualified (varga + ayanamsha + position); `target_floor` updated after each successful build.

**Tech Stack:** Python 3.13, psycopg3, PyJHora adapter, pytest, Cloud SQL proxy (prod data plane always).

---

## Codebase Map

### Files to Modify
| File | Lines | What Changes |
|---|---|---|
| `platform/python-sidecar/ga_writers/ga_structural_writer.py` | 3554 | Node aspects, varga dignity/conjunction/dispositor/vargottama extended to Rahu/Ketu; Kala Sarpa per varga; special-point relationships; house-lord matrix; karaka web; Jaimini per-varga; graha yuddha; combustion/retrograde relational rows |
| `platform/python-sidecar/ga_writers/ga_strength_writer.py` | 1033 | Remove Rahu/Ketu skip (L188); fix is_daytime (L230); compute drik from aspect matrix (L261) |
| `platform/python-sidecar/tests/test_ga8_writer.py` | ~600 | New test classes for each addition |
| `platform/python-sidecar/tests/test_l1_strength.py` | TBD | Tests for nodal rows, daytime computation, drik bala |

### New Constant (ga_structural_writer.py — insert after L414)
```python
# Node special aspects per many Parashari authorities (5th/7th/9th — full)
NODE_PARASHARI_ASPECTS: dict[int, float] = {5: 1.0, 7: 1.0, 9: 1.0}
```

---

## Task 1 — Add NODE_PARASHARI_ASPECTS + extend D1 Parashari aspects to Rahu/Ketu

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py:404-415` (constants block)
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py:737` (`_build_aspect_rows`)
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

- [ ] **Step 1: Write the failing test**

```python
class TestNodeAspectRows:
    def test_rahu_ketu_appear_in_d1_parashari_aspects(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        subjects = {r["fact_subject"] for r in rows
                    if r["fact_category"] == "aspect_parashari_given"}
        assert "RAH_MEAN" in subjects, "Rahu missing from D1 Parashari aspects"
        assert "KET_MEAN" in subjects, "Ketu missing from D1 Parashari aspects"

    def test_rahu_emits_5th_7th_9th_aspects(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rahu_aspect_keys = {r["fact_key"] for r in rows
                            if r["fact_category"] == "aspect_parashari_given"
                            and r["fact_subject"] == "RAH_MEAN"}
        # Rahu in Taurus (house 2) → 5th=house 6, 7th=house 8, 9th=house 10
        assert "house_6" in rahu_aspect_keys
        assert "house_8" in rahu_aspect_keys
        assert "house_10" in rahu_aspect_keys
        assert len(rahu_aspect_keys) == 3, f"Expected 3 node aspects, got: {rahu_aspect_keys}"
```

- [ ] **Step 2: Run test to confirm it fails**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestNodeAspectRows -v
```
Expected: FAIL — "Rahu missing from D1 Parashari aspects"

- [ ] **Step 3: Add NODE_PARASHARI_ASPECTS constant**

In `ga_structural_writer.py`, after line 414 (end of `PARASHARI_ASPECTS` block), add:

```python
# Node special aspects: 5th/7th/9th — full strength (many Parashari authorities)
# Rahu and Ketu: retrograde, so aspects flow "backward" in some schools;
# here we follow the majority rule: same offsets as stated (5th/7th/9th from sign).
NODE_PARASHARI_ASPECTS: dict[int, float] = {5: 1.0, 7: 1.0, 9: 1.0}
```

- [ ] **Step 4: Extend `_build_aspect_rows` (line 737) to ALL_GRAHAS**

Change:
```python
grahas_order = CLASSICAL_GRAHAS  # Only classical grahas for Parashari
```
To:
```python
grahas_order = ALL_GRAHAS  # Classical + Rahu/Ketu (nodes have 5th/7th/9th aspects)
```

And update the aspect-offset lookup (lines 747-750) to handle nodes:
```python
        # Determine aspect offsets for this graha
        if g_name in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif g_name in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[g_name]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]
```

- [ ] **Step 5: Run test to confirm it passes**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestNodeAspectRows -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8): add NODE_PARASHARI_ASPECTS + extend D1 Parashari aspects to Rahu/Ketu (5th/7th/9th)"
```

---

## Task 2 — Extend per-varga Parashari aspects, dignity, conjunctions, vargottama to ALL_GRAHAS

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py:2769-3000` (`_build_varga_relationship_rows`)
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

- [ ] **Step 1: Write failing tests**

```python
class TestVargaNodeRelationships:
    """Rahu/Ketu must appear in per-varga dignity, aspects, conjunctions, vargottama."""

    def _make_varga_state(self) -> dict:
        # D9 varga state with all 9 grahas including nodes
        return {
            "Sun": {"sign": "Aries", "sign_num": 1, "house": 1, "degree": 5.0},
            "Moon": {"sign": "Cancer", "sign_num": 4, "house": 4, "degree": 10.0},
            "Mars": {"sign": "Aries", "sign_num": 1, "house": 1, "degree": 20.0},
            "Mercury": {"sign": "Gemini", "sign_num": 3, "house": 3, "degree": 15.0},
            "Jupiter": {"sign": "Sagittarius", "sign_num": 9, "house": 9, "degree": 5.0},
            "Venus": {"sign": "Pisces", "sign_num": 12, "house": 12, "degree": 8.0},
            "Saturn": {"sign": "Libra", "sign_num": 7, "house": 7, "degree": 12.0},
            "Rahu": {"sign": "Gemini", "sign_num": 3, "house": 3, "degree": 20.0},
            "Ketu": {"sign": "Sagittarius", "sign_num": 9, "house": 9, "degree": 20.0},
        }

    def test_rahu_ketu_in_varga_dignity(self):
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        dignity_subjects = {r["fact_subject"] for r in rows
                            if r["fact_category"] == "graha_dignity_per_varga"}
        assert "D9_RAH_MEAN" in dignity_subjects
        assert "D9_KET_MEAN" in dignity_subjects

    def test_rahu_ketu_in_varga_aspects(self):
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        aspect_subjects = {r["fact_subject"] for r in rows
                           if r["fact_category"] == "aspect_parashari_per_varga"}
        assert "D9_RAH_MEAN" in aspect_subjects
        assert "D9_KET_MEAN" in aspect_subjects

    def test_rahu_ketu_in_varga_conjunctions_when_same_sign(self):
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        conj_subjects = {r["fact_subject"] for r in rows
                         if r["fact_category"] == "conjunction_per_varga"}
        # Mercury and Rahu both in Gemini → should have conjunction
        assert any("RAH_MEAN" in s and "MER" in s for s in conj_subjects), \
            f"Mercury-Rahu conjunction missing. Subjects: {conj_subjects}"

    def test_rahu_ketu_in_vargottama(self):
        # Rahu in Taurus in D1 (MOCK_CHART_OUTPUT), Taurus in D9 varga_state would trigger
        vs = self._make_varga_state()
        vs["Rahu"] = {"sign": "Taurus", "sign_num": 2, "house": 2, "degree": 48.0}
        rows = sut._build_varga_relationship_rows(
            "D9", vs, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        vargottama_subjects = {r["fact_subject"] for r in rows
                               if r["fact_category"] == "vargottama_per_varga"}
        assert "D9_RAH_MEAN" in vargottama_subjects
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestVargaNodeRelationships -v
```
Expected: 4 FAIL

- [ ] **Step 3: Extend dignity loop (L2769) to ALL_GRAHAS**

Change `for g_name in CLASSICAL_GRAHAS:` at line 2769 to `for g_name in ALL_GRAHAS:`.

The existing dignity logic already handles Rahu/Ketu via `EXALTATION_SIGNS` and `DEBILITATION_SIGNS` (which include Rahu/Ketu at lines 138–148). For `OWN_SIGNS.get(g_name, [])` nodes will return `[]` (no own sign) → dignity will be `"neutral"` — that is correct classical treatment.

- [ ] **Step 4: Extend Parashari aspects loop (L2804) to ALL_GRAHAS**

Change `for g_name in CLASSICAL_GRAHAS:` at line 2804 to `for g_name in ALL_GRAHAS:`.

Update the offset lookup to handle nodes:
```python
        if g_name in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif g_name in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[g_name]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]
```

- [ ] **Step 5: Extend conjunctions loop (L2841–2842) to ALL_GRAHAS**

Change:
```python
    for i, g1 in enumerate(CLASSICAL_GRAHAS):
        for g2 in CLASSICAL_GRAHAS[i+1:]:
```
To:
```python
    for i, g1 in enumerate(ALL_GRAHAS):
        for g2 in ALL_GRAHAS[i+1:]:
```

- [ ] **Step 6: Extend vargottama loop (L2976) to ALL_GRAHAS**

Change `for g_name in CLASSICAL_GRAHAS:` at line 2976 to `for g_name in ALL_GRAHAS:`.

- [ ] **Step 7: Handle node dispositor chains (L2936)**

Nodes don't own signs — their "dispositor" is the lord of the sign they occupy. Change `for g_name in CLASSICAL_GRAHAS:` at line 2936 to `for g_name in ALL_GRAHAS:`. The existing chain-walk logic (`SIGN_LORDS.get(current_sign)`) will naturally start the chain at the sign's lord — which is correct for nodes too (e.g., Rahu in Gemini → chain starts Mercury→…). No special case needed.

- [ ] **Step 8: Guard parivartana loop (L2898, 2903) to skip nodes**

Nodes don't own signs so parivartana is N/A. The existing guard `if not lord1 or lord1 not in CLASSICAL_GRAHAS: continue` at line 2903 correctly prevents node-initiated parivartana rows. No change needed here, but verify by reading lines 2898–2933.

- [ ] **Step 9: Run all varga tests**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestVargaNodeRelationships -v
```
Expected: 4 PASS

- [ ] **Step 10: Run full test suite to catch regressions**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py -v
```
Expected: all pass (currently 112 tests per memory obs 18801)

- [ ] **Step 11: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8): extend per-varga dignity/aspects/conjunctions/vargottama/dispositors to ALL_GRAHAS (Rahu/Ketu)"
```

---

## Task 3 — Kala Sarpa / Kala Amrita structural detection per varga

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py`
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

**Classical rule:** All 7 classical grahas hemmed within the Rahu→Ketu arc (clockwise) = Kala Sarpa. Within the Ketu→Rahu arc = Kala Amrita. Rahu's house (1–12) determines which of the 12 KS variants fires (e.g., Vasuki KS = Rahu in house 2, etc.). The 12 variant names come from the dosha catalog; we fall back to `"KALA_SARPA_RAHU_H{n}"` if not in catalog.

- [ ] **Step 1: Write failing test**

```python
class TestKalaSarpaDetection:
    def test_kala_sarpa_detected_when_all_planets_between_rahu_ketu(self):
        """With Rahu H2/Ketu H8 and all 7 classical grahas between them, KS fires."""
        # MOCK_CHART_OUTPUT: Rahu in Taurus (H2), Ketu in Scorpio (H8).
        # Classical grahas: H1(Mars), H9(Jupiter), H10(Sun,Mercury,Venus), H11(Moon), H7(Saturn)
        # Arc Rahu→Ketu clockwise (H2→H3→…→H8): H3,H4,H5,H6,H7 only
        # Planets in H1,H9,H10,H11 are OUTSIDE the arc → KS does NOT fire for MOCK_CHART_OUTPUT
        # Use a custom varga_state where KS fires
        ks_state = {
            "Sun":     {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 5.0},
            "Moon":    {"sign": "Cancer",   "sign_num": 4, "house": 4, "degree": 10.0},
            "Mars":    {"sign": "Leo",      "sign_num": 5, "house": 5, "degree": 15.0},
            "Mercury": {"sign": "Cancer",   "sign_num": 4, "house": 4, "degree": 20.0},
            "Jupiter": {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 25.0},
            "Venus":   {"sign": "Leo",      "sign_num": 5, "house": 5, "degree": 8.0},
            "Saturn":  {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 18.0},
            "Rahu":    {"sign": "Taurus",   "sign_num": 2, "house": 2, "degree": 20.0},
            "Ketu":    {"sign": "Scorpio",  "sign_num": 8, "house": 8, "degree": 20.0},
        }
        result = sut._detect_kala_sarpa(ks_state)
        assert result["fires"] is True
        assert result["variant"] in ("kala_sarpa", "kala_amrita")
        assert result["rahu_house"] == 2

    def test_kala_amrita_when_planets_on_ketu_side(self):
        ka_state = {
            "Sun":     {"sign": "Sagittarius", "sign_num": 9,  "house": 9,  "degree": 5.0},
            "Moon":    {"sign": "Capricorn",   "sign_num": 10, "house": 10, "degree": 10.0},
            "Mars":    {"sign": "Scorpio",     "sign_num": 8,  "house": 8,  "degree": 15.0},
            "Mercury": {"sign": "Scorpio",     "sign_num": 8,  "house": 8,  "degree": 20.0},
            "Jupiter": {"sign": "Sagittarius", "sign_num": 9,  "house": 9,  "degree": 25.0},
            "Venus":   {"sign": "Capricorn",   "sign_num": 10, "house": 10, "degree": 8.0},
            "Saturn":  {"sign": "Aquarius",    "sign_num": 11, "house": 11, "degree": 18.0},
            "Rahu":    {"sign": "Taurus",      "sign_num": 2,  "house": 2,  "degree": 20.0},
            "Ketu":    {"sign": "Scorpio",     "sign_num": 8,  "house": 8,  "degree": 20.0},
        }
        result = sut._detect_kala_sarpa(ka_state)
        assert result["fires"] is True
        assert result["variant"] == "kala_amrita"

    def test_no_kala_sarpa_when_planets_on_both_sides(self):
        result = sut._detect_kala_sarpa(
            {g["name"]: {"sign": g["sign"], "sign_num": g["sign_id"],
                         "house": g["house"], "degree": g.get("longitude", 0) % 30}
             for g in MOCK_CHART_OUTPUT["grahas"]}
        )
        assert result["fires"] is False

    def test_kala_sarpa_emits_row_in_varga_relationships(self):
        ks_state = {
            "Sun":     {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 5.0},
            "Moon":    {"sign": "Cancer",   "sign_num": 4, "house": 4, "degree": 10.0},
            "Mars":    {"sign": "Leo",      "sign_num": 5, "house": 5, "degree": 15.0},
            "Mercury": {"sign": "Cancer",   "sign_num": 4, "house": 4, "degree": 20.0},
            "Jupiter": {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 25.0},
            "Venus":   {"sign": "Leo",      "sign_num": 5, "house": 5, "degree": 8.0},
            "Saturn":  {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 18.0},
            "Rahu":    {"sign": "Taurus",   "sign_num": 2, "house": 2, "degree": 20.0},
            "Ketu":    {"sign": "Scorpio",  "sign_num": 8, "house": 8, "degree": 20.0},
        }
        rows = sut._build_varga_relationship_rows(
            "D9", ks_state, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        ks_rows = [r for r in rows if r["fact_category"] == "kala_sarpa_per_varga"]
        assert len(ks_rows) >= 1
        assert ks_rows[0]["fact_value_text"] in ("kala_sarpa", "kala_amrita", "none")
```

- [ ] **Step 2: Run tests to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestKalaSarpaDetection -v
```
Expected: FAIL — `_detect_kala_sarpa` not found

- [ ] **Step 3: Implement `_detect_kala_sarpa` helper**

Add after the `_build_varga_relationship_rows` function definition but before its body (or at the module helpers section, around line 700):

```python
def _detect_kala_sarpa(varga_state: dict[str, Any]) -> dict[str, Any]:
    """Detect Kala Sarpa / Kala Amrita formation in a varga state.

    Classical rule (Parashari):
      - All 7 classical grahas hemmed within the Rahu→Ketu arc (going forward
        from Rahu sign_num to Ketu sign_num clockwise) = Kala Sarpa.
      - All 7 within the Ketu→Rahu arc (Kala Amrita side) = Kala Amrita.
      - Any graha on BOTH arcs (or nodes themselves counted) = no formation.

    Returns: {"fires": bool, "variant": "kala_sarpa"|"kala_amrita"|"none",
              "rahu_house": int, "ketu_house": int, "variant_name": str}.
    """
    rahu_data = varga_state.get("Rahu") or varga_state.get("RAH_MEAN")
    ketu_data = varga_state.get("Ketu") or varga_state.get("KET_MEAN")
    if not rahu_data or not ketu_data:
        return {"fires": False, "variant": "none", "rahu_house": 0, "ketu_house": 0, "variant_name": ""}

    rahu_sign = int(rahu_data["sign_num"])  # 1–12
    ketu_sign = int(ketu_data["sign_num"])  # 1–12 (should be rahu_sign+6 % 12)
    rahu_house = int(rahu_data.get("house", rahu_sign))

    # Arc from Rahu→Ketu going forward (clockwise) — signs strictly between them
    # E.g. Rahu in sign 2, Ketu in sign 8: arc = {3,4,5,6,7}
    ks_arc: set[int] = set()
    s = rahu_sign % 12 + 1
    while s != ketu_sign:
        ks_arc.add(s)
        s = s % 12 + 1

    # Arc from Ketu→Rahu (Kala Amrita side)
    ka_arc: set[int] = set()
    s = ketu_sign % 12 + 1
    while s != rahu_sign:
        ka_arc.add(s)
        s = s % 12 + 1

    ks_arc.add(rahu_sign)  # Rahu's own sign is in KS arc boundary
    ka_arc.add(ketu_sign)  # Ketu's own sign is in KA arc boundary

    # Check where each classical graha sits
    on_ks_side = 0
    on_ka_side = 0
    for g_name in CLASSICAL_GRAHAS:
        g_data = varga_state.get(g_name)
        if not g_data:
            continue
        g_sign = int(g_data["sign_num"])
        if g_sign in ks_arc:
            on_ks_side += 1
        elif g_sign in ka_arc:
            on_ka_side += 1
        # signs occupied by both nodes: ambiguous → neither counter increments

    total = on_ks_side + on_ka_side
    present_count = sum(1 for g in CLASSICAL_GRAHAS if varga_state.get(g))

    if total < present_count:
        # Some graha in a node-occupied sign → formation broken
        return {"fires": False, "variant": "none",
                "rahu_house": rahu_house, "ketu_house": int(ketu_data.get("house", ketu_sign)),
                "variant_name": ""}

    variant_name = f"KALA_SARPA_RAHU_H{rahu_house}"
    if on_ks_side == present_count and on_ka_side == 0:
        return {"fires": True, "variant": "kala_sarpa",
                "rahu_house": rahu_house, "ketu_house": int(ketu_data.get("house", ketu_sign)),
                "variant_name": variant_name}
    if on_ka_side == present_count and on_ks_side == 0:
        return {"fires": True, "variant": "kala_amrita",
                "rahu_house": rahu_house, "ketu_house": int(ketu_data.get("house", ketu_sign)),
                "variant_name": f"KALA_AMRITA_RAHU_H{rahu_house}"}
    return {"fires": False, "variant": "none",
            "rahu_house": rahu_house, "ketu_house": int(ketu_data.get("house", ketu_sign)),
            "variant_name": ""}
```

- [ ] **Step 4: Add Kala Sarpa row emission to `_build_varga_relationship_rows`**

At the end of the `_build_varga_relationship_rows` function (before `return rows`), add:

```python
    # ── Kala Sarpa / Kala Amrita per varga ────────────────────────────────────
    ks_result = _detect_kala_sarpa(varga_state)
    rows.append(_base_row(
        "kala_sarpa_per_varga", f"{varga_prefix}CHART", "ks_detection",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_text=ks_result["variant"],
        value_num=1.0 if ks_result["fires"] else 0.0,
        value_jsonb={
            "varga": varga,
            "fires": ks_result["fires"],
            "variant": ks_result["variant"],
            "variant_name": ks_result["variant_name"],
            "rahu_house": ks_result["rahu_house"],
            "ketu_house": ks_result["ketu_house"],
            "ayanamsha_id": ayanamsha_id,
            "uncatalogued": False,
        },
        verif="two_pass_verified",
        source=f"ga_structural.kala_sarpa_per_varga/{eng_ver}",
        citation_human=(
            f"Kala Sarpa detection in {varga}: "
            f"{'FIRES as ' + ks_result['variant'] if ks_result['fires'] else 'not present'} "
            f"(Rahu H{ks_result['rahu_house']}) ({ayanamsha_id})."
        ),
    ))
```

- [ ] **Step 5: Add `kala_sarpa_per_varga` to `_verify_no_ga3_overlap` whitelist if needed**

Check the `_verify_no_ga3_overlap` function in ga_structural_writer.py (search for `GA3_CATEGORIES`). The new category `kala_sarpa_per_varga` does not exist in GA3, so no change needed. But verify by grepping:
```
grep -n "GA3_CATEGORIES\|kala_sarpa" platform/python-sidecar/ga_writers/ga_structural_writer.py
```

- [ ] **Step 6: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestKalaSarpaDetection -v
```
Expected: 4 PASS

- [ ] **Step 7: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8): add Kala Sarpa/Kala Amrita structural detection per varga with 12-variant labelling"
```

---

## Task 4 — Special points (Gulika/Mandi, Arudha Lagna, sahams) as relationship participants

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py`
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

**What:** GA5 writes `upagraha_position` rows to `chart_facts`. We read them back (Gulika/Mandi, Arudha_Lagna, and sahams) and enumerate: aspects received from classical grahas, conjunctions with grahas in same sign/house.

- [ ] **Step 1: Write failing tests**

```python
class TestSpecialPointRelationships:
    """Special points from GA5 appear as relationship participants."""

    def _make_mock_conn_with_special_points(self):
        """A mock connection that returns Gulika in Taurus (house 2)."""
        class _MockCursor:
            def __init__(self):
                self._rows = [
                    ("gulika", "Taurus", 2, 15.0),
                    ("mandi",  "Taurus", 2, 18.0),
                    ("arudha_lagna", "Leo", 5, 22.0),
                ]
            def execute(self, *a, **kw): pass
            def fetchall(self): return self._rows
            def __enter__(self): return self
            def __exit__(self, *a): return False

        class _MockConn:
            def cursor(self): return _MockCursor()

        return _MockConn()

    def test_gulika_appears_as_conjunction_participant(self):
        mock_conn = self._make_mock_conn_with_special_points()
        # Gulika in Taurus (H2) — Rahu also in Taurus (H2) in MOCK_CHART_OUTPUT
        # → should emit a conjunction row between Rahu and Gulika
        rows = sut._build_special_point_relationship_rows(
            mock_conn, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        conj_rows = [r for r in rows if r["fact_category"] == "conjunction_special_point"]
        conj_subjects = {r["fact_subject"] for r in conj_rows}
        assert any("gulika" in s.lower() or "GULIKA" in s for s in conj_subjects), \
            f"Gulika conjunction not found. Subjects: {conj_subjects}"

    def test_special_point_receives_aspects(self):
        mock_conn = self._make_mock_conn_with_special_points()
        rows = sut._build_special_point_relationship_rows(
            mock_conn, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        aspect_recv_rows = [r for r in rows
                            if r["fact_category"] == "aspect_received_by_special_point"]
        assert len(aspect_recv_rows) > 0, "No aspects received by special points"

    def test_empty_special_points_emits_no_rows(self):
        class _EmptyConn:
            class _EmptyCursor:
                def execute(self, *a, **kw): pass
                def fetchall(self): return []
                def __enter__(self): return self
                def __exit__(self, *a): return False
            def cursor(self): return _EmptyConn._EmptyCursor()

        rows = sut._build_special_point_relationship_rows(
            _EmptyConn(), MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert rows == []
```

- [ ] **Step 2: Run tests to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestSpecialPointRelationships -v
```
Expected: FAIL — `_build_special_point_relationship_rows` not found

- [ ] **Step 3: Implement `_load_special_points` and `_build_special_point_relationship_rows`**

Add before the `_build_varga_aspect_rows` function (around line 3006):

```python
def _load_special_points(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
) -> list[dict[str, Any]]:
    """Load GA5 upagraha_position rows from chart_facts.
    Returns list of {name, sign, house, degree} for special points present.
    """
    special_points = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fact_subject, fact_value_text,
                       fact_value_num,
                       fact_value_jsonb
                FROM chart_facts
                WHERE chart_id = %s
                  AND ayanamsha_id = %s
                  AND fact_category = 'upagraha_position'
                  AND fact_key IN ('sign', 'house', 'degree_in_sign')
            """, (chart_id, ayanamsha_id))
            raw: dict[str, dict[str, Any]] = {}
            for row in cur.fetchall():
                subj, val_text, val_num, val_jsonb = row
                if subj not in raw:
                    raw[subj] = {}
                # fact_key is embedded — need to re-query or use fact_value_jsonb
            # Re-query with full columns
            cur.execute("""
                SELECT fact_subject, fact_key, fact_value_text, fact_value_num
                FROM chart_facts
                WHERE chart_id = %s
                  AND ayanamsha_id = %s
                  AND fact_category = 'upagraha_position'
            """, (chart_id, ayanamsha_id))
            raw = {}
            for row in cur.fetchall():
                subj, key, val_text, val_num = row
                if subj not in raw:
                    raw[subj] = {}
                if key == "sign":
                    raw[subj]["sign"] = val_text
                elif key == "house":
                    raw[subj]["house"] = int(val_num) if val_num else 0
                elif key == "degree_in_sign":
                    raw[subj]["degree"] = float(val_num) if val_num else 0.0
    except Exception as exc:
        logger.warning("[ga_structural] _load_special_points failed: %s", exc)
        return []

    for name, data in raw.items():
        if data.get("sign") and data.get("house"):
            special_points.append({
                "name": name,
                "sign": data["sign"],
                "house": data["house"],
                "degree": data.get("degree", 0.0),
            })
    return special_points


def _build_special_point_relationship_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Enumerate relationships for GA5 special points (Gulika/Mandi/Arudha/sahams).

    For each special point:
    - aspect_received_by_special_point: which classical grahas aspect the house
      the special point occupies (Parashari aspects from each of 9 grahas)
    - conjunction_special_point: any graha in the same house as the special point
    """
    special_points = _load_special_points(conn, chart_id, ayanamsha_id)
    if not special_points:
        return []

    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    for sp in special_points:
        sp_name = sp["name"]
        sp_sign = sp["sign"]
        sp_house = sp["house"]
        sp_subj = sp_name.upper()

        # Aspects received: iterate all 9 grahas, check if they aspect sp_house
        for g in grahas_data:
            g_name = g["name"]
            g_house = int(g.get("house", 0))
            if not g_house:
                continue

            if g_name in ("Rahu", "Ketu"):
                asp_offsets = NODE_PARASHARI_ASPECTS
            elif g_name in PARASHARI_ASPECTS:
                asp_offsets = PARASHARI_ASPECTS[g_name]
            else:
                asp_offsets = PARASHARI_ASPECTS["all"]

            for offset, strength in asp_offsets.items():
                target_h = ((g_house - 1 + offset - 1) % 12) + 1
                if target_h == sp_house:
                    g_subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
                    rows.append(_base_row(
                        "aspect_received_by_special_point",
                        sp_subj, f"from_{g_subj}_{offset}th",
                        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                        value_num=strength,
                        unit="strength",
                        verif="two_pass_verified",
                        source=f"ga_structural.special_point_aspect/{eng_ver}",
                        citation_human=(
                            f"{g_name} {offset}th aspect falls on {sp_name} "
                            f"in {sp_sign} house {sp_house} at strength {strength:.2f} ({ayanamsha_id})."
                        ),
                    ))

        # Conjunctions: grahas in same house as special point
        for g in grahas_data:
            g_name = g["name"]
            g_house = int(g.get("house", 0))
            g_sign = g.get("sign", "")
            if g_house == sp_house:
                g_subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
                rows.append(_base_row(
                    "conjunction_special_point",
                    f"{sp_subj}_{g_subj}", "same_house",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_text=f"{sp_name}_conjunct_{g_name}",
                    value_jsonb={
                        "special_point": sp_name, "graha": g_name,
                        "house": sp_house, "sign": sp_sign,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.special_point_conjunction/{eng_ver}",
                    citation_human=(
                        f"{sp_name} and {g_name} conjunct in house {sp_house} ({sp_sign}) ({ayanamsha_id})."
                    ),
                ))

    return rows
```

- [ ] **Step 4: Hook `_build_special_point_relationship_rows` into `build_ga_structural_substep`**

In `build_ga_structural_substep` (around line 3400+), add after the existing `all_rows.extend(...)` calls:

```python
    all_rows.extend(_build_special_point_relationship_rows(
        conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
    ))
```

Also add the same call in the main `build_ga_structural` function's `all_rows.extend(...)` block.

- [ ] **Step 5: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestSpecialPointRelationships -v
```
Expected: 3 PASS

- [ ] **Step 6: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8/T1.3): add special points as relationship participants (Gulika/Mandi/Arudha/sahams)"
```

---

## Task 5 — House-lord relationship matrix per varga (T2.1)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py`
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

**What:** For each varga, emit: (a) each house-lord's house placement in that varga (`lord_in_house_per_varga`); (b) which house-lord aspects which other house-lord (`lord_aspects_lord_per_varga`); (c) mutual exchange (parivartana is already captured in `parivartana_per_varga` — skip duplicating it here, just reference it).

- [ ] **Step 1: Write failing test**

```python
class TestHouseLordMatrix:
    def _make_simple_varga_state(self) -> dict:
        return {
            "Mars":    {"sign": "Aries",      "sign_num": 1, "house": 1, "degree": 15.0},
            "Venus":   {"sign": "Taurus",     "sign_num": 2, "house": 2, "degree": 10.0},
            "Mercury": {"sign": "Gemini",     "sign_num": 3, "house": 3, "degree": 5.0},
            "Moon":    {"sign": "Cancer",     "sign_num": 4, "house": 4, "degree": 20.0},
            "Sun":     {"sign": "Leo",        "sign_num": 5, "house": 5, "degree": 8.0},
            "Jupiter": {"sign": "Sagittarius","sign_num": 9, "house": 9, "degree": 12.0},
            "Saturn":  {"sign": "Libra",      "sign_num": 7, "house": 7, "degree": 18.0},
            "Rahu":    {"sign": "Taurus",     "sign_num": 2, "house": 2, "degree": 20.0},
            "Ketu":    {"sign": "Scorpio",    "sign_num": 8, "house": 8, "degree": 20.0},
        }

    def test_lord_in_house_rows_emitted_for_all_12_houses(self):
        rows = sut._build_house_lord_matrix_rows(
            "D9", self._make_simple_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        lord_in_house = [r for r in rows if r["fact_category"] == "lord_in_house_per_varga"]
        assert len(lord_in_house) == 12, f"Expected 12 lord-in-house rows, got {len(lord_in_house)}"

    def test_lord_aspects_lord_rows_emitted(self):
        rows = sut._build_house_lord_matrix_rows(
            "D9", self._make_simple_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        aspects = [r for r in rows if r["fact_category"] == "lord_aspects_lord_per_varga"]
        assert len(aspects) > 0, "No lord-aspects-lord rows found"
```

- [ ] **Step 2: Run to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestHouseLordMatrix -v
```
Expected: FAIL

- [ ] **Step 3: Implement `_build_house_lord_matrix_rows`**

Add before `_build_varga_aspect_rows` (around line 3006):

```python
def _build_house_lord_matrix_rows(
    varga: str,
    varga_state: dict[str, Any],
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """House-lord relationship matrix per varga.

    Emits:
    - lord_in_house_per_varga: for each house 1–12, which house (in that varga)
      the lord of that house occupies (lord-in-house placement).
    - lord_aspects_lord_per_varga: for each pair of house lords, whether
      one lord's Parashari aspects cover the other lord's house.
    """
    rows: list[dict[str, Any]] = []
    vp = f"{varga}_"

    def get_house_from_varga(g_name: str) -> int:
        d = varga_state.get(g_name)
        return int(d["house"]) if d else 0

    # Compute which sign occupies each house in this varga
    # (whole sign from varga's own lagna — use chart_output ascendant for D1,
    #  or infer from varga_state's minimum sign_num as proxy lagna)
    lagna_sign_num = int(chart_output.get("ascendant", {}).get("sign_id", 1))

    def house_sign(house_num: int) -> str:
        idx = ((lagna_sign_num - 1 + house_num - 1) % 12)
        return SIGN_NAMES[idx]

    # Lord of each house 1–12 in this varga
    house_lords = {h: SIGN_LORDS[house_sign(h)] for h in range(1, 13)}

    # ── lord_in_house_per_varga: where is each house-lord placed? ─────────────
    for h_num, lord_name in house_lords.items():
        lord_house = get_house_from_varga(lord_name)
        lord_sign_data = varga_state.get(lord_name)
        lord_sign = lord_sign_data["sign"] if lord_sign_data else ""
        lord_subj = PLANET_TO_SUBJECT.get(lord_name, lord_name.upper())
        rows.append(_base_row(
            "lord_in_house_per_varga", f"{vp}LORD_{h_num}", "placed_in_house",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(lord_house),
            value_text=f"lord{h_num}_{lord_name}_in_house{lord_house}",
            value_jsonb={
                "varga": varga,
                "source_house": h_num,
                "lord": lord_name,
                "lord_placed_in_house": lord_house,
                "lord_sign": lord_sign,
                "ayanamsha_id": ayanamsha_id,
                "uncatalogued": False,
            },
            verif="two_pass_verified",
            source=f"ga_structural.lord_in_house_per_varga/{eng_ver}",
            citation_human=(
                f"Lord of house {h_num} ({lord_name}) placed in house {lord_house} "
                f"({lord_sign}) in {varga} ({ayanamsha_id})."
            ),
        ))

    # ── lord_aspects_lord_per_varga: does lord of H_a aspect house of lord of H_b? ──
    for ha, lord_a in house_lords.items():
        lord_a_house = get_house_from_varga(lord_a)
        if not lord_a_house:
            continue

        if lord_a in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif lord_a in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[lord_a]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]

        for offset, strength in asp_offsets.items():
            target_h = ((lord_a_house - 1 + offset - 1) % 12) + 1
            # Find which house's lord occupies the target house
            for hb, lord_b in house_lords.items():
                lord_b_house = get_house_from_varga(lord_b)
                if lord_b_house == target_h and lord_a != lord_b:
                    lord_a_subj = PLANET_TO_SUBJECT.get(lord_a, lord_a.upper())
                    lord_b_subj = PLANET_TO_SUBJECT.get(lord_b, lord_b.upper())
                    rows.append(_base_row(
                        "lord_aspects_lord_per_varga",
                        f"{vp}LORD{ha}_ASPECTS_LORD{hb}", f"offset_{offset}",
                        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                        value_num=strength,
                        unit="strength",
                        value_jsonb={
                            "varga": varga,
                            "aspecting_house": ha,
                            "aspecting_lord": lord_a,
                            "aspecting_lord_house": lord_a_house,
                            "aspect_offset": offset,
                            "aspected_house": hb,
                            "aspected_lord": lord_b,
                            "aspected_lord_house": lord_b_house,
                            "ayanamsha_id": ayanamsha_id,
                            "uncatalogued": False,
                        },
                        verif="two_pass_verified",
                        source=f"ga_structural.lord_aspects_lord_per_varga/{eng_ver}",
                        citation_human=(
                            f"Lord {ha} ({lord_a}) {offset}th aspect covers lord {hb} "
                            f"({lord_b}) in house {lord_b_house} in {varga} at strength "
                            f"{strength:.2f} ({ayanamsha_id})."
                        ),
                    ))

    return rows
```

- [ ] **Step 4: Hook into `_build_varga_relationship_rows`**

At end of `_build_varga_relationship_rows` (after vargottama loop, before `return rows`), add:
```python
    # ── House-lord relationship matrix ────────────────────────────────────────
    rows.extend(_build_house_lord_matrix_rows(
        varga, varga_state, chart_output,
        chart_id, build_id, ayanamsha_id, computed_at, eng_ver
    ))
```

- [ ] **Step 5: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestHouseLordMatrix -v
```
Expected: PASS

- [ ] **Step 6: Run full suite to catch regressions**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py -v
```

- [ ] **Step 7: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8/T2.1): add house-lord relationship matrix per varga (lord-in-house + lord-aspects-lord)"
```

---

## Task 6 — Jaimini rasi drishti per varga (T2.2)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py`
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

**What:** `aspect_jaimini` is currently computed for D1 at lines 787–818 (sign-to-sign). Add it to `_build_varga_relationship_rows` so it fires per-varga too, as `aspect_jaimini_per_varga`.

- [ ] **Step 1: Write failing test**

```python
class TestJaiminiPerVarga:
    def test_jaimini_per_varga_rows_present(self):
        vs = {
            "Sun": {"sign": "Leo", "sign_num": 5, "house": 5, "degree": 10.0},
        }
        rows = sut._build_varga_relationship_rows(
            "D9", vs, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        jaimini_rows = [r for r in rows if r["fact_category"] == "aspect_jaimini_per_varga"]
        # 12×12 minus self (132) or fewer depending on Jaimini rules
        assert len(jaimini_rows) > 0, "No aspect_jaimini_per_varga rows found"

    def test_jaimini_per_varga_fully_qualified_with_varga(self):
        vs = {"Sun": {"sign": "Leo", "sign_num": 5, "house": 5, "degree": 10.0}}
        rows = sut._build_varga_relationship_rows(
            "D9", vs, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        jaimini_rows = [r for r in rows if r["fact_category"] == "aspect_jaimini_per_varga"]
        for r in jaimini_rows:
            jb = r.get("fact_value_jsonb", {})
            assert jb.get("varga") == "D9", f"Row not tagged with varga: {r}"
```

- [ ] **Step 2: Run to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestJaiminiPerVarga -v
```

- [ ] **Step 3: Add Jaimini rasi drishti per varga to `_build_varga_relationship_rows`**

Near the end of `_build_varga_relationship_rows` (before house-lord matrix hook), add:

```python
    # ── Jaimini rasi drishti per varga (sign-to-sign aspects) ─────────────────
    for s1_idx, s1 in enumerate(SIGN_NAMES):
        s1_type = SIGN_TYPES[s1]
        for s2_idx, s2 in enumerate(SIGN_NAMES):
            if s1_idx == s2_idx:
                continue
            offset = (s2_idx - s1_idx) % 12
            has_aspect = offset not in [1, 11]  # fixed/movable/common all skip adj signs
            if has_aspect:
                rows.append(_base_row(
                    "aspect_jaimini_per_varga", f"{varga_prefix}{s1}", f"on_{s2}",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=1.0,
                    unit="rasi_drishti",
                    value_jsonb={
                        "varga": varga,
                        "source_sign_type": s1_type,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.jaimini_rasi_drishti_per_varga/{eng_ver}",
                    citation_human=(
                        f"{s1} ({s1_type}) Jaimini rasi drishti on {s2} in {varga} ({ayanamsha_id})."
                    ),
                ))
```

**Note:** This adds 120 rows per varga (12×12 minus 12 self minus ~24 non-aspect pairs ≈ ~108 rows). Across 30 vargas × 5 ayanamshas = 16,200 rows. This is correct — volume is a consequence of completeness.

- [ ] **Step 4: Run tests and full suite**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8/T2.2): add Jaimini rasi drishti per-varga enumeration (aspect_jaimini_per_varga)"
```

---

## Task 7 — Karaka inter-relationships (T2.3)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py`
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

**What:** Load 8 Jaimini chara-karaka assignments from chart_facts (stored by GA5 under `fact_category = 'jaimini_chara_karaka'`), then enumerate their mutual Parashari aspect and conjunction relationships per varga.

- [ ] **Step 1: Write failing test**

```python
class TestKarakaWeb:
    def _make_karaka_conn(self):
        """Mock conn returning chara-karaka assignments."""
        class _KarakaCursor:
            def execute(self, q, *a, **kw):
                self._q = q
            def fetchall(self):
                # atmakaraka=Sun, amatyakaraka=Saturn, darakaraka=Mars, etc.
                return [
                    ("ATMAKARAKA",    "Sun",     None, None),
                    ("AMATYAKARAKA",  "Saturn",  None, None),
                    ("DARAKARAKA",    "Mars",    None, None),
                    ("BHRATRUKARAKA", "Mercury", None, None),
                ]
            def __enter__(self): return self
            def __exit__(self, *a): return False

        class _KarakaConn:
            def cursor(self): return _KarakaCursor()
        return _KarakaConn()

    def test_atmakaraka_amatyakaraka_relationship_emitted(self):
        vs = {
            "Sun":    {"sign": "Capricorn", "sign_num": 10, "house": 10, "degree": 5.0},
            "Saturn": {"sign": "Libra",     "sign_num": 7,  "house": 7,  "degree": 12.0},
            "Mars":   {"sign": "Aries",     "sign_num": 1,  "house": 1,  "degree": 15.0},
        }
        rows = sut._build_karaka_web_rows(
            self._make_karaka_conn(), vs, MOCK_CHART_OUTPUT,
            "D9", CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        karaka_rows = [r for r in rows if r["fact_category"] == "karaka_web_per_varga"]
        assert len(karaka_rows) > 0, "No karaka-web rows emitted"
        subjects = {r["fact_subject"] for r in karaka_rows}
        # AK (Sun) → AmK (Saturn): Saturn is in house 7, Sun has 7th aspect → should fire
        assert any("ATMAKARAKA" in s or "SUN" in s.upper() for s in subjects)

    def test_no_karaka_web_when_no_assignments(self):
        class _EmptyConn:
            class _EC:
                def execute(self, *a, **kw): pass
                def fetchall(self): return []
                def __enter__(self): return self
                def __exit__(self, *a): return False
            def cursor(self): return _EmptyConn._EC()
        rows = sut._build_karaka_web_rows(
            _EmptyConn(), {}, MOCK_CHART_OUTPUT,
            "D9", CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert rows == []
```

- [ ] **Step 2: Run to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestKarakaWeb -v
```

- [ ] **Step 3: Implement `_build_karaka_web_rows`**

Add near `_build_special_point_relationship_rows`:

```python
def _build_karaka_web_rows(
    conn: Any,
    varga_state: dict[str, Any],
    chart_output: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Karaka inter-relationship web per varga.

    Loads chara-karaka assignments from chart_facts (GA5: fact_category='jaimini_chara_karaka').
    Emits karaka_web_per_varga rows: mutual aspects and conjunctions between karaka planets.
    """
    # Load karaka assignments
    karaka_assignments: dict[str, str] = {}  # {karaka_role: planet_name}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fact_subject, fact_value_text
                FROM chart_facts
                WHERE chart_id = %s
                  AND ayanamsha_id = %s
                  AND fact_category = 'jaimini_chara_karaka'
                  AND fact_key = 'graha'
            """, (chart_id, ayanamsha_id))
            for row in cur.fetchall():
                role, planet = row[0], row[1]
                if role and planet:
                    karaka_assignments[role] = planet
    except Exception as exc:
        logger.warning("[ga_structural] _build_karaka_web_rows: could not load karakas: %s", exc)
        return []

    if len(karaka_assignments) < 2:
        return []

    rows: list[dict[str, Any]] = []
    vp = f"{varga}_"
    karaka_list = list(karaka_assignments.items())  # [(role, planet), ...]

    def get_house(g_name: str) -> int:
        d = varga_state.get(g_name)
        return int(d["house"]) if d else 0

    # Aspect relationships between karaka planets
    for i, (role_a, planet_a) in enumerate(karaka_list):
        h_a = get_house(planet_a)
        if not h_a:
            continue

        if planet_a in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif planet_a in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[planet_a]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]

        for offset, strength in asp_offsets.items():
            target_h = ((h_a - 1 + offset - 1) % 12) + 1
            for role_b, planet_b in karaka_list:
                if planet_a == planet_b:
                    continue
                h_b = get_house(planet_b)
                if h_b == target_h:
                    pa_subj = PLANET_TO_SUBJECT.get(planet_a, planet_a.upper())
                    pb_subj = PLANET_TO_SUBJECT.get(planet_b, planet_b.upper())
                    rows.append(_base_row(
                        "karaka_web_per_varga",
                        f"{vp}{role_a}_ASPECTS_{role_b}",
                        f"offset_{offset}",
                        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                        value_num=strength,
                        unit="strength",
                        value_jsonb={
                            "varga": varga,
                            "karaka_a_role": role_a, "karaka_a_planet": planet_a,
                            "karaka_a_house": h_a,
                            "karaka_b_role": role_b, "karaka_b_planet": planet_b,
                            "karaka_b_house": h_b,
                            "aspect_offset": offset,
                            "ayanamsha_id": ayanamsha_id,
                            "uncatalogued": False,
                        },
                        verif="two_pass_verified",
                        source=f"ga_structural.karaka_web_per_varga/{eng_ver}",
                        citation_human=(
                            f"{role_a} ({planet_a}) {offset}th aspect covers "
                            f"{role_b} ({planet_b}) in house {h_b} in {varga} "
                            f"at strength {strength:.2f} ({ayanamsha_id})."
                        ),
                    ))

        # Conjunction: same house
        for role_b, planet_b in karaka_list:
            if planet_a == planet_b:
                continue
            h_b = get_house(planet_b)
            if h_a == h_b:
                rows.append(_base_row(
                    "karaka_web_per_varga",
                    f"{vp}{role_a}_CONJUNCT_{role_b}", "same_house",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_text=f"{planet_a}_conjunct_{planet_b}",
                    value_jsonb={
                        "varga": varga,
                        "karaka_a_role": role_a, "karaka_a_planet": planet_a,
                        "karaka_b_role": role_b, "karaka_b_planet": planet_b,
                        "house": h_a,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.karaka_web_per_varga/{eng_ver}",
                    citation_human=(
                        f"{role_a} ({planet_a}) conjunct {role_b} ({planet_b}) "
                        f"in house {h_a} in {varga} ({ayanamsha_id})."
                    ),
                ))

    return rows
```

- [ ] **Step 4: Hook into `build_ga_structural_substep`**

The karaka web needs a `conn` and the per-varga state. Since `_build_varga_aspect_rows` already loops over vargas, it needs to call `_build_karaka_web_rows` per varga. Modify `_build_varga_aspect_rows` to also call `_build_karaka_web_rows`:

In `_build_varga_aspect_rows` (L3036), after `rows.extend(_build_varga_relationship_rows(...))`, add:

```python
        rows.extend(_build_karaka_web_rows(
            conn, varga_state, chart_output, varga,
            chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
```

- [ ] **Step 5: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestKarakaWeb -v
```

- [ ] **Step 6: Run full suite**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py -v
```

- [ ] **Step 7: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8/T2.3): add Jaimini karaka inter-relationship web per varga"
```

---

## Task 8 — Graha yuddha (planetary war) (T3.2)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py`
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

**Classical rule:** Two non-node classical grahas within 1° in the same sign. Winner = planet with lower declination (approximated here by lower degree-in-sign). Emit as `graha_yuddha` relational row.

- [ ] **Step 1: Write failing test**

```python
class TestGrahaYuddha:
    def test_yuddha_detected_within_1_degree(self):
        """Sun at 295.0° and Mercury at 295.8° → within 1° → yuddha fires."""
        # MOCK_CHART_OUTPUT: Sun=295.0, Mercury=300.0 — NOT within 1° (5° apart)
        # Use modified chart
        chart = dict(MOCK_CHART_OUTPUT)
        chart["grahas"] = [g for g in MOCK_CHART_OUTPUT["grahas"]]
        # Modify Mercury to be near Sun
        modified_grahas = []
        for g in chart["grahas"]:
            if g["name"] == "Mercury":
                modified_grahas.append({**g, "longitude": 295.6, "sign": "Capricorn"})
            else:
                modified_grahas.append(g)
        chart["grahas"] = modified_grahas

        rows = sut._build_graha_yuddha_rows(
            chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yuddha_rows = [r for r in rows if r["fact_category"] == "graha_yuddha"]
        assert len(yuddha_rows) >= 1, f"Expected yuddha row, got {len(yuddha_rows)}"
        subjects = {r["fact_subject"] for r in yuddha_rows}
        assert any("SUN" in s and "MER" in s for s in subjects) or \
               any("MER" in s and "SUN" in s for s in subjects)

    def test_no_yuddha_beyond_1_degree(self):
        rows = sut._build_graha_yuddha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yuddha_rows = [r for r in rows if r["fact_category"] == "graha_yuddha"]
        # MOCK_CHART_OUTPUT: Sun=295, Mercury=300 — 5° apart, no yuddha
        assert len(yuddha_rows) == 0

    def test_yuddha_emits_winner_loser(self):
        chart = dict(MOCK_CHART_OUTPUT)
        modified_grahas = []
        for g in chart["grahas"]:
            if g["name"] == "Mercury":
                modified_grahas.append({**g, "longitude": 295.6, "sign": "Capricorn"})
            else:
                modified_grahas.append(g)
        chart["grahas"] = modified_grahas
        rows = sut._build_graha_yuddha_rows(
            chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yuddha_rows = [r for r in rows if r["fact_category"] == "graha_yuddha"]
        assert any(r["fact_key"] == "winner" for r in yuddha_rows)
        assert any(r["fact_key"] == "loser" for r in yuddha_rows)
```

- [ ] **Step 2: Run to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestGrahaYuddha -v
```

- [ ] **Step 3: Implement `_build_graha_yuddha_rows`**

Add after `_build_special_state_rows` (around line 2415):

```python
def _build_graha_yuddha_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Graha yuddha (planetary war) detection.

    Classical: two non-node classical grahas within ~1° in the same sign.
    Winner: lower declination (approximated here by lower longitude).
    Loser: higher longitude.

    Emits atomic rows: one for winner, one for loser, one for the pair.
    """
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    # Index classical grahas only (nodes don't fight yuddha)
    classical_data = [g for g in grahas_data
                      if g["name"] in CLASSICAL_GRAHAS]

    for i, g1 in enumerate(classical_data):
        for g2 in classical_data[i+1:]:
            if g1.get("sign") != g2.get("sign"):
                continue  # Must be in same sign for yuddha
            long1 = float(g1.get("longitude", 0.0))
            long2 = float(g2.get("longitude", 0.0))
            orb = abs(long1 - long2)
            if orb > 180:
                orb = 360 - orb
            if orb > 1.0:
                continue

            # Winner: lower longitude (classical: lower degree in sign)
            winner, loser = (g1, g2) if long1 < long2 else (g2, g1)
            w_name = winner["name"]
            l_name = loser["name"]
            w_subj = PLANET_TO_SUBJECT.get(w_name, w_name.upper())
            l_subj = PLANET_TO_SUBJECT.get(l_name, l_name.upper())
            pair_subj = f"{w_subj}_{l_subj}"
            sign = g1.get("sign", "")

            for key, value, graha_name, graha_subj in [
                ("winner", w_name, w_name, w_subj),
                ("loser",  l_name, l_name, l_subj),
                ("orb_deg", str(round(orb, 4)), None, None),
            ]:
                rows.append(_base_row(
                    "graha_yuddha", pair_subj, key,
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_text=value if key != "orb_deg" else None,
                    value_num=round(orb, 4) if key == "orb_deg" else None,
                    unit="deg" if key == "orb_deg" else None,
                    value_jsonb={
                        "winner": w_name, "loser": l_name,
                        "sign": sign, "orb_deg": round(orb, 4),
                        "winner_longitude": long1 if long1 < long2 else long2,
                        "loser_longitude": long1 if long1 >= long2 else long2,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.graha_yuddha/{eng_ver}",
                    citation_human=(
                        f"Graha yuddha: {w_name} (winner) vs {l_name} (loser) "
                        f"in {sign} within {orb:.2f}° ({ayanamsha_id})."
                    ),
                ))

    return rows
```

- [ ] **Step 4: Hook into `build_ga_structural_substep` and `build_ga_structural`**

Add in both places after `_build_special_state_rows`:
```python
    all_rows.extend(_build_graha_yuddha_rows(
        chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
    ))
```

- [ ] **Step 5: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestGrahaYuddha -v
```

- [ ] **Step 6: Run full suite**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py -v
```

- [ ] **Step 7: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8/T3.2): add graha yuddha (planetary war) detection with winner/loser"
```

---

## Task 9 — Combustion and retrograde as relational rows (T3.3)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_structural_writer.py`
- Test: `platform/python-sidecar/tests/test_ga8_writer.py`

**What:** Currently `graha_special_state_rollup` at L2307+ emits per-graha flags (`is_combust`, `is_retrograde`). Now add RELATIONAL rows: `combustion_relationship` (X combust-by-Sun) and `retrograde_aspect_modification` (X's aspect modified by retrograde status).

- [ ] **Step 1: Write failing test**

```python
class TestCombustionRetrogradRelational:
    def test_combustion_relational_row_for_mercury_near_sun(self):
        """Sun=295° Mercury=300° → 5° apart → within combust orb (8°) → fires."""
        rows = sut._build_combustion_retrograde_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        combust_rows = [r for r in rows if r["fact_category"] == "combustion_relationship"]
        combust_subjects = {r["fact_subject"] for r in combust_rows}
        # Sun=295, Mercury=300 → diff=5 < 8 → Mercury combust
        assert "MER" in combust_subjects or any("MER" in s for s in combust_subjects), \
            f"Mercury combustion relational row missing. Subjects: {combust_subjects}"

    def test_retrograde_aspect_modification_rows(self):
        """Rahu is retrograde in MOCK_CHART_OUTPUT → should emit retrograde modification."""
        rows = sut._build_combustion_retrograde_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        retro_rows = [r for r in rows
                      if r["fact_category"] == "retrograde_aspect_modification"]
        # Rahu is retrograde — should emit modification flag
        assert len(retro_rows) > 0, "No retrograde aspect modification rows found"

    def test_non_retrograde_non_combust_emits_no_relational_rows(self):
        """Mars in MOCK_CHART_OUTPUT is not retrograde, not combust → no relational rows for Mars."""
        rows = sut._build_combustion_retrograde_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        mars_combust = [r for r in rows
                        if r["fact_category"] == "combustion_relationship"
                        and "MAR" in r.get("fact_subject", "")]
        # Mars at 15° (Aries) vs Sun at 295° (Capricorn) → >8° → not combust
        assert len(mars_combust) == 0
```

- [ ] **Step 2: Run to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestCombustionRetrogradRelational -v
```

- [ ] **Step 3: Implement `_build_combustion_retrograde_relationship_rows`**

Add after `_build_graha_yuddha_rows`:

```python
# Combustion orbs per graha (classical Parashara, degrees)
COMBUSTION_ORBS: dict[str, float] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,  # retrograde Mercury: 12°
    "Jupiter": 11.0, "Venus": 10.0,                # retrograde Venus: 8°
    "Saturn": 15.0,
    "Rahu": 0.0, "Ketu": 0.0,                      # nodes not combusted by Sun
}


def _build_combustion_retrograde_relationship_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Combustion and retrograde as RELATIONAL rows.

    combustion_relationship: X is within Sun's orb → emit relational row.
    retrograde_aspect_modification: X is retrograde → emit modification flag
      for each aspect X gives (retrograde planets give aspects in reverse direction
      per some schools; here we emit the flag so L2 can interpret).
    """
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    sun = next((g for g in grahas_data if g["name"] == "Sun"), None)
    sun_long = float(sun.get("longitude", 0.0)) if sun else 0.0

    for g in grahas_data:
        g_name = g["name"]
        if g_name == "Sun":
            continue
        g_subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        g_long = float(g.get("longitude", 0.0))
        is_retro = bool(g.get("retrograde", False))

        # Combustion relational row
        orb_limit = COMBUSTION_ORBS.get(g_name, 0.0)
        if sun and orb_limit > 0:
            diff = abs(g_long - sun_long)
            if diff > 180:
                diff = 360 - diff
            if diff <= orb_limit:
                rows.append(_base_row(
                    "combustion_relationship",
                    g_subj, "combust_by_sun",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=round(diff, 4),
                    unit="deg_from_sun",
                    value_jsonb={
                        "graha": g_name,
                        "sun_longitude": sun_long,
                        "graha_longitude": g_long,
                        "orb_deg": round(diff, 4),
                        "orb_limit": orb_limit,
                        "is_retrograde": is_retro,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.combustion_relationship/{eng_ver}",
                    citation_human=(
                        f"{g_name} combust by Sun: within {diff:.2f}° "
                        f"(orb limit {orb_limit}°) ({ayanamsha_id})."
                    ),
                ))

        # Retrograde aspect modification flag
        if is_retro:
            # For each aspect this graha gives, emit a retrograde-modified marker
            g_house = int(g.get("house", 0))
            if not g_house:
                continue
            if g_name in ("Rahu", "Ketu"):
                asp_offsets = NODE_PARASHARI_ASPECTS
            elif g_name in PARASHARI_ASPECTS:
                asp_offsets = PARASHARI_ASPECTS[g_name]
            else:
                asp_offsets = PARASHARI_ASPECTS["all"]

            for offset, strength in asp_offsets.items():
                target_h = ((g_house - 1 + offset - 1) % 12) + 1
                rows.append(_base_row(
                    "retrograde_aspect_modification",
                    g_subj, f"retro_aspect_house_{target_h}",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=strength,
                    unit="strength",
                    value_jsonb={
                        "graha": g_name,
                        "is_retrograde": True,
                        "aspect_offset": offset,
                        "target_house": target_h,
                        "strength": strength,
                        "interpretation_note": "retrograde_modifies_aspect_strength",
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.retrograde_aspect_modification/{eng_ver}",
                    citation_human=(
                        f"{g_name} (retrograde) {offset}th aspect on house {target_h} "
                        f"— retrograde modifier applied at strength {strength:.2f} ({ayanamsha_id})."
                    ),
                ))

    return rows
```

- [ ] **Step 4: Hook into substep and main build**

Add in both `build_ga_structural_substep` and `build_ga_structural`:
```python
    all_rows.extend(_build_combustion_retrograde_relationship_rows(
        chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
    ))
```

- [ ] **Step 5: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py::TestCombustionRetrogradRelational -v
```

- [ ] **Step 6: Run full suite**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py -v
```

- [ ] **Step 7: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_structural_writer.py \
        platform/python-sidecar/tests/test_ga8_writer.py
git commit -m "feat(ga8/T3.3): add combustion-relationship and retrograde-aspect-modification relational rows"
```

---

## Task 10 — ga_strength: Rahu/Ketu nodal strength rows (T1.4a)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_strength_writer.py:183-190`
- Test: `platform/python-sidecar/tests/test_l1_strength.py`

**What:** Line 188 `if name not in NAISARGIKA_BALA: continue` silently skips Rahu/Ketu for ALL shadbala sub-bala categories. Fix: emit explicit 0.0 rows with `fact_value_jsonb = {"naisargika_na": true, "school": "parashara_strict"}` so nodes are PRESENT in the output but correctly flagged.

- [ ] **Step 1: Read existing test structure**

```
grep -n "def test_" platform/python-sidecar/tests/test_l1_strength.py | head -30
```

- [ ] **Step 2: Write failing tests**

```python
class TestNodalStrengthRows:
    """Rahu and Ketu must appear in shadbala output with explicit NA-flag rows."""

    def test_rahu_appears_in_shadbala_output(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        # After fix: Rahu should be present with na_flag, not silently absent
        assert "Rahu" in result, "Rahu missing from shadbala derivation"

    def test_ketu_appears_in_shadbala_output(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert "Ketu" in result, "Ketu missing from shadbala derivation"

    def test_rahu_naisargika_is_zero(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        if "Rahu" in result:
            assert result["Rahu"]["naisargika"] == 0.0, \
                "Rahu naisargika should be 0.0 (no naisargika bala per strict Parashara)"

    def test_rahu_has_na_flag(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        if "Rahu" in result:
            assert result["Rahu"].get("naisargika_na") is True, \
                "Rahu should have naisargika_na=True flag"
```

You'll need to add `MOCK_CHART_OUTPUT` to `test_l1_strength.py` (import from test_ga8_writer or define inline).

- [ ] **Step 3: Run to confirm failures**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py::TestNodalStrengthRows -v
```

- [ ] **Step 4: Fix `_derive_shadbala_from_positions` in ga_strength_writer.py**

Change the loop at lines 185–188:
```python
    for g in grahas:
        name = g["name"]
        if name not in NAISARGIKA_BALA:
            continue
```

To:
```python
    for g in grahas:
        name = g["name"]
        is_node = name in ("Rahu", "Ketu")
```

Then in the naisargika bala section (line 257), replace:
```python
        naisargika = NAISARGIKA_BALA[name]
```
With:
```python
        naisargika = 0.0 if is_node else NAISARGIKA_BALA.get(name, 0.5)
```

Add after the `result[name] = {...}` dict (around line 265), a `naisargika_na` key for nodes:
```python
        node_entry: dict[str, Any] = {
            "sthana": round(sthana, 4),
            "dig": round(dig, 4) if not is_node else 0.0,
            "kala": round(kala, 4) if not is_node else 0.0,
            "cheshta": round(cheshta, 4) if not is_node else 0.0,
            "naisargika": naisargika,
            "drik": round(drik, 4),
            "total": round(sthana + (0.0 if is_node else dig + kala + cheshta) + naisargika + round(drik, 4), 4),
        }
        if is_node:
            node_entry["naisargika_na"] = True
            node_entry["school"] = "parashara_strict"
        result[name] = node_entry
```

**Note:** For nodes, dig/kala/cheshta are set to 0.0 per strict Parashara (nodes have no directional or temporal bala in this school). The `naisargika_na=True` flag signals the explicit NA, not an omission.

Also fix the loop guard: nodes should not be skipped for sthana/dig derivation — the existing `sign_id`, `house`, etc. lookups will work fine since Rahu/Ketu appear in `chart_output["grahas"]`.

- [ ] **Step 5: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py::TestNodalStrengthRows -v
```

- [ ] **Step 6: Run full strength test suite**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py -v
```

- [ ] **Step 7: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_strength_writer.py \
        platform/python-sidecar/tests/test_l1_strength.py
git commit -m "feat(ga_strength/T1.4a): emit explicit nodal strength rows (Rahu/Ketu naisargika_na=True, 0.0)"
```

---

## Task 11 — ga_strength: Fix kala-bala day/night hardcode (T1.4b)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_strength_writer.py:230`
- Test: `platform/python-sidecar/tests/test_l1_strength.py`

**What:** Line 230 hardcodes `is_daytime = True`. Compute from `birth_params` hour. The NATIVE_BIRTH struct has `hour=10.717` (10:43 IST), so this will remain True for the native — but the formula must be correct for non-native charts.

- [ ] **Step 1: Write failing test**

```python
class TestKalaBalaIsDatetime:
    def test_is_daytime_computed_not_hardcoded(self):
        """For a nighttime birth (hour=22), kala_day_strong planets should get night penalty."""
        # Inject a nighttime birth into panchanga
        night_chart = dict(MOCK_CHART_OUTPUT)
        # Panchanga with vara and a nighttime flag is in chart_output["panchanga"]
        # Our fix: read from birth_params passed to _derive_shadbala_from_positions
        # Function signature change: add birth_params optional arg
        night_birth = {"hour": 22.5, "lat": 20.27, "lon": 85.84, "tz_offset": 5.5}
        result_night = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri",
                                                            birth_hour=22.5)
        result_day = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri",
                                                          birth_hour=10.72)
        # Sun is kala_day_strong → kala should be HIGHER in daytime than nighttime
        sun_kala_day = result_day.get("Sun", {}).get("kala", 0)
        sun_kala_night = result_night.get("Sun", {}).get("kala", 0)
        assert sun_kala_day > sun_kala_night, \
            f"Sun kala-bala should be higher in daytime. day={sun_kala_day}, night={sun_kala_night}"
```

- [ ] **Step 2: Run to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py::TestKalaBalaIsDatetime -v
```

- [ ] **Step 3: Fix `_derive_shadbala_from_positions` signature and is_daytime computation**

In `ga_strength_writer.py`, change the function signature (around line 162):
```python
def _derive_shadbala_from_positions(
    chart_output: dict[str, Any],
    ayanamsha_id: str,
    birth_hour: float | None = None,
) -> dict[str, dict[str, float]]:
```

Replace the hardcoded `is_daytime = True` at line 230 with:
```python
        # Compute day/night from birth hour.
        # Astronomical sunrise/sunset vary; for the classical formula we use
        # 6am–6pm as the daytime window (tropical approximation).
        if birth_hour is not None:
            is_daytime = 6.0 <= birth_hour < 18.0
        else:
            # Fallback: read from panchanga if available
            panchanga_daytime = panchanga.get("is_daytime")
            if panchanga_daytime is not None:
                is_daytime = bool(panchanga_daytime)
            else:
                # Native birth: 10:43 IST = 10.72 hours → daytime
                is_daytime = True
```

Update callers of `_derive_shadbala_from_positions` to pass `birth_hour` from `NATIVE_BIRTH`:
```python
birth_h = NATIVE_BIRTH.get("hour", 10.72)
shadbala = _derive_shadbala_from_positions(chart_output, ayanamsha_id, birth_hour=birth_h)
```

Check `NATIVE_BIRTH` in `ga_positions_writer.py` for the hour field name (likely `"hour"` or `"time"` in decimal).

- [ ] **Step 4: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py::TestKalaBalaIsDatetime -v
```

- [ ] **Step 5: Run full strength suite**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py -v
```

- [ ] **Step 6: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_strength_writer.py \
        platform/python-sidecar/tests/test_l1_strength.py
git commit -m "fix(ga_strength/T1.4b): compute kala-bala is_daytime from birth_hour; remove hardcode"
```

---

## Task 12 — ga_strength: Compute drik-bala from aspect matrix (T1.4c)

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_strength_writer.py:259-261`
- Test: `platform/python-sidecar/tests/test_l1_strength.py`

**What:** Line 261 sets `drik = 0.375` (stub). Compute real drik-bala from D1 chart's own Parashari aspect matrix. Drik-bala = net aspect strength received by a graha: sum of benefic aspects received (positive) minus malefic aspects received (negative), scaled to [0,1].

**Classical rule:** Benefics (Jupiter, Venus, Mercury, Moon) aspecting a graha give positive drik; malefics (Saturn, Mars, Sun, Rahu, Ketu) give negative. Net is normalized.

- [ ] **Step 1: Write failing test**

```python
class TestDrikBalaFromAspects:
    def test_drik_bala_differs_by_graha_based_on_aspects_received(self):
        """Jupiter (lord of benefics, gives full aspects) should give positive drik
        to houses it aspects. The stub returns 0.375 for all — post-fix, values differ."""
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        drik_values = {g: d.get("drik", 0) for g, d in result.items()
                       if g in sut.CLASSICAL_GRAHAS}
        # After fix: not all drik values should be the same
        unique_driks = set(drik_values.values())
        assert len(unique_driks) > 1, \
            f"All grahas have same drik-bala {unique_driks} — stub not fixed"

    def test_drik_bala_bounded_0_to_1(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        for g_name, sb in result.items():
            if g_name in sut.CLASSICAL_GRAHAS:
                drik = sb.get("drik", 0)
                assert 0.0 <= drik <= 1.0, \
                    f"{g_name} drik={drik} outside [0,1]"
```

- [ ] **Step 2: Run to confirm failure**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py::TestDrikBalaFromAspects -v
```
Expected: FAIL — all grahas have same drik 0.375

- [ ] **Step 3: Implement drik-bala computation inline in `_derive_shadbala_from_positions`**

Replace the `drik = 0.375` line (line 261) with a helper that computes from chart_output's graha positions:

First, add a module-level helper after the `_derive_bhava_bala` function:

```python
BENEFIC_GRAHAS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
MALEFIC_GRAHAS = frozenset({"Saturn", "Mars", "Sun", "Rahu", "Ketu"})


def _compute_drik_bala(
    target_graha: str,
    target_house: int,
    grahas: list[dict[str, Any]],
) -> float:
    """Compute drik bala for target_graha from D1 Parashari aspects received.

    Returns a value in [0.0, 1.0]:
    - Each benefic aspect received: +0.25 (full = +0.25; partial = ×strength)
    - Each malefic aspect received: −0.25 per full aspect
    - Normalize to [0, 1] via sigmoid-style clamp.
    """
    net = 0.0
    for g in grahas:
        g_name = g["name"]
        if g_name == target_graha:
            continue
        g_house = int(g.get("house", 0))
        if not g_house:
            continue

        if g_name in ("Rahu", "Ketu"):
            offsets = {5: 1.0, 7: 1.0, 9: 1.0}
        elif g_name in ("Saturn",):
            offsets = {3: 0.25, 7: 1.0, 10: 0.75}
        elif g_name in ("Jupiter",):
            offsets = {5: 1.0, 7: 1.0, 9: 1.0}
        elif g_name in ("Mars",):
            offsets = {4: 1.0, 7: 1.0, 8: 1.0}
        else:
            offsets = {7: 1.0}

        for offset, strength in offsets.items():
            aspected_h = ((g_house - 1 + offset - 1) % 12) + 1
            if aspected_h == target_house:
                if g_name in BENEFIC_GRAHAS:
                    net += strength * 0.25
                elif g_name in MALEFIC_GRAHAS:
                    net -= strength * 0.25

    # Clamp to [0, 1] — max benefic load ~0.75 (3 full benefic aspects); normalized
    return max(0.0, min(1.0, 0.5 + net))
```

Then in `_derive_shadbala_from_positions`, replace `drik = 0.375` with:
```python
        drik = _compute_drik_bala(name, house, grahas)
```

- [ ] **Step 4: Run tests**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py::TestDrikBalaFromAspects -v
```
Expected: PASS — unique drik values across grahas

- [ ] **Step 5: Run full test suite (both test files)**

```
cd platform/python-sidecar && python -m pytest tests/test_l1_strength.py tests/test_ga8_writer.py -v
```

- [ ] **Step 6: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_strength_writer.py \
        platform/python-sidecar/tests/test_l1_strength.py
git commit -m "fix(ga_strength/T1.4c): compute real drik-bala from D1 Parashari aspect matrix; replace 0.375 stub"
```

---

## Task 13 — Update asset_registry target_floor + end-to-end prod verify

**Files:**
- `platform/python-sidecar/ga_writers/ga_structural_writer.py` (no code change — just build and count)
- `platform/migrations/` (surgical update to asset_registry seed if needed)
- Test: prod database query

After all code changes are committed, run a prod build for chart `482012f1-710e-4a25-994a-93821f5871aa` via the Cloud SQL proxy and capture the actual row count.

- [ ] **Step 1: Run all tests to confirm clean baseline**

```
cd platform/python-sidecar && python -m pytest tests/test_ga8_writer.py tests/test_l1_strength.py -v
```
Expected: all pass

- [ ] **Step 2: Run prod build (one ayanamsha for speed check)**

Use the existing substep runner or the orchestrator with just `lahiri_chitrapaksha`:
```
# Via the build runner that uses Cloud SQL proxy:
python -m ga_writers.ga_structural_writer --chart-id 482012f1-710e-4a25-994a-93821f5871aa \
    --ayanamsha lahiri_chitrapaksha --substep-only
```
(If no CLI entrypoint: trigger via the orchestrator's `/api/build` endpoint with the chart_id.)

- [ ] **Step 3: Query prod for actual row counts**

```sql
-- Total chart_facts for this chart
SELECT COUNT(*) AS total
FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';

-- Per new category spot-checks
SELECT fact_category, COUNT(*) AS n
FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN (
    'aspect_parashari_given', 'aspect_parashari_per_varga',
    'graha_dignity_per_varga', 'conjunction_per_varga',
    'kala_sarpa_per_varga', 'aspect_received_by_special_point',
    'conjunction_special_point', 'lord_in_house_per_varga',
    'lord_aspects_lord_per_varga', 'aspect_jaimini_per_varga',
    'karaka_web_per_varga', 'graha_yuddha',
    'combustion_relationship', 'retrograde_aspect_modification'
  )
GROUP BY fact_category
ORDER BY fact_category;

-- Verify Rahu/Ketu in Parashari aspects
SELECT fact_subject, COUNT(*) AS aspect_rows
FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category = 'aspect_parashari_given'
  AND fact_subject IN ('RAH_MEAN', 'KET_MEAN')
GROUP BY fact_subject;
```

- [ ] **Step 4: Run full 5-ayanamsha build**

After spot-check passes, run the full build (all 5 ayanamshas).

- [ ] **Step 5: Update asset_registry target_floor**

Capture `total_rows_after_build` from the output, then update the seed:

```sql
UPDATE asset_registry
SET target_floor = <actual_count>
WHERE asset_id = 'ga_structural'
  AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```

Also update the seed script in migrations:
```
grep -rn "ga_structural.*target_floor\|53953" platform/migrations/
```
Update whichever seed file contains `53953` to the new value.

- [ ] **Step 6: Acceptance criteria verification**

Per brief §6:
```
[ ] Rahu/Ketu in aspects+conjunctions+dispositors across 30 vargas → check via SQL above
[ ] Kala Sarpa/Kala Amrita detection emitted (kala_sarpa_per_varga) → check above
[ ] Gulika/Mandi/Arudha/sahams as relationship participants → check above
[ ] House-lord matrix + karaka web → check above
[ ] Graha yuddha + combustion/retrograde relational → check above
[ ] ga_strength: nodal rows present; kala-bala daytime computed; drik-bala non-stub → check via
    SELECT fact_subject, fact_category, fact_value_num FROM chart_facts
    WHERE chart_id = '482012f1...' AND fact_category LIKE 'graha_shadbala_%'
    AND fact_subject IN ('RAH_MEAN', 'KET_MEAN');
[ ] Every new row fully qualified; no silent drops; FORENSIC 7/7 in build log
[ ] target_floor updated; orchestrator contract unchanged; build completes within limits
```

- [ ] **Step 7: Commit floor update**

```bash
git add platform/migrations/  # whichever seed file changed
git commit -m "fix(ga8): update asset_registry target_floor to actual post-completeness row count"
```

---

## Task 14 — Branch finalization and PR

- [ ] **Step 1: Confirm branch is `feature/ga8-all30-vargas` (current branch)**

```
git branch --show-current
```

- [ ] **Step 2: Push all commits**

```
git push origin feature/ga8-all30-vargas
```

- [ ] **Step 3: Create PR with acceptance checklist body**

```bash
gh pr create \
  --title "feat(ga8+strength): L1 relationship completeness — nodes, special points, house-lord matrix, Kala Sarpa, karaka web, yuddha, combustion" \
  --body "..."
```

PR body should reference:
- Brief: `CLAUDECODE_BRIEF_GA8_GASTRENGTH_COMPLETENESS_v1_0.md`
- All 8 acceptance criteria from §6
- Volume change: ~54k → ~90–120k rows (estimate; actual after prod build)
- No schema migrations required (new fact_categories added to existing `chart_facts` table)

---

## Execution Notes

### Test fixture for test_l1_strength.py
The strength tests need `MOCK_CHART_OUTPUT`. Either import from `test_ga8_writer`:
```python
from test_ga8_writer import MOCK_CHART_OUTPUT
```
or define a local `MOCK_STRENGTH_CHART` with the same data.

### Orchestrator contract — unchanged
`build_ga_structural_substep` is the only function called by the orchestrator. All new `_build_*` functions are called FROM `build_ga_structural_substep`. No new orchestrator entry points. Contract frozen per `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`.

### Two-pass verification
Each new `_build_*` function marks its rows with `verif="two_pass_verified"`. The existing `_verify_no_duplicate_fact_ids` + `_verify_no_ga3_overlap` + `_verify_citation_completeness` + `_linter_check_rows` calls in `build_ga_structural_substep` automatically cover all new rows — no new verification logic needed.

### GA3 overlap guard
The categories `kala_sarpa_per_varga`, `lord_in_house_per_varga`, `lord_aspects_lord_per_varga`, `aspect_jaimini_per_varga`, `karaka_web_per_varga`, `graha_yuddha`, `combustion_relationship`, `retrograde_aspect_modification`, `aspect_received_by_special_point`, `conjunction_special_point` are all new and do NOT appear in the GA3 exclusion list. Verify with:
```
grep -n "GA3_CATEGORIES\|_ga3_overlap" platform/python-sidecar/ga_writers/ga_structural_writer.py
```

### Parivartana for nodes
Nodes (Rahu/Ketu) don't own signs so they cannot initiate parivartana. The existing guard `if not lord1 or lord1 not in CLASSICAL_GRAHAS: continue` at line 2903 already handles this correctly — nodes are in ALL_GRAHAS but their sign's lord will be a classical graha. When a classical graha's sign-lord is also a classical graha in that first graha's own sign, parivartana fires normally. Nodes never appear as `g1` in the parivartana loop since:
- `sign1 = get_sign("Rahu")` → a sign (e.g., "Taurus")
- `lord1 = SIGN_LORDS.get("Taurus")` → "Venus" (a classical graha)  
- `if lord1 not in CLASSICAL_GRAHAS` → passes (Venus is classical)
- `if sign_lord1 in OWN_SIGNS.get("Rahu", [])` → `OWN_SIGNS.get("Rahu", [])` → `[]` → False
- So Rahu never generates a parivartana row. ✓

But wait — the loop at line 2898 says `for g1 in CLASSICAL_GRAHAS`. If we extend to ALL_GRAHAS, the node path still won't fire for the reason above. Either way is safe.
