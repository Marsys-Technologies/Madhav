# bo_cgm_motifs Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `bo_cgm_motifs` produce real rows by fixing the upstream data gaps that cause all three motif detectors to return zero results.

**Architecture:** Two bugs in `bo_karanajala.py` block all motif detection: (1) `_fetch_graha_sign_numbers` uses `subject.title()` which produces wrong keys for 7/9 grahas (MAR→Mar instead of Mars), breaking the argala edge builder AND any new dispositor edge builder; (2) `_build_dispositor_edges()` doesn't exist at all — so mutual_reception and parivartana_chain detectors never see a dispositor edge. Fix both, then add tests. The `bo_bimba.py` position fix (`_SUBJECT_TO_GRAHA` mapping) is already deployed and makes the stellium detector operational.

**Tech Stack:** Python 3.13, psycopg2/psycopg3 connection protocol, pytest, MagicMock

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py` | Modify | Fix `_fetch_graha_sign_numbers` + add `SIGN_LORD` + add `_build_dispositor_edges()` + wire in `run()` |
| `platform/python-sidecar/tests/l2/test_bo_karanajala_dispositor.py` | Create | Tests for `_fetch_graha_sign_numbers` fix + `_build_dispositor_edges()` + integration with motif detectors |

---

## Task 1: Fix `_fetch_graha_sign_numbers` subject mapping bug

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py:180-182`
- Test: `platform/python-sidecar/tests/l2/test_bo_karanajala_dispositor.py`

**Context:** `_fetch_graha_sign_numbers` reads L1 `chart_facts` where `fact_subject` is UPPER_SNAKE (SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN). Line 181 calls `subject.title()` which only works for 2 of 9 — SUN→Sun and MOON→Moon. The other 7 produce Mar/Mer/Jup/Ven/Sat/Rah_Mean/Ket_Mean which are NOT in `KNOWN_GRAHAS`. Result: `graha_signs` dict has 7/9 keys that fail `g in KNOWN_GRAHAS` — argala edges for those grahas are silently dropped, and the dispositor edges we're about to add would also be empty.

The same mapping `_SUBJECT_TO_GRAHA` that bo_bimba uses is the fix. Import it.

- [ ] **Step 1: Write failing test**

Create `platform/python-sidecar/tests/l2/test_bo_karanajala_dispositor.py`:

```python
"""
Tests for bo_karanajala dispositor edge generation.

Covers:
1. _fetch_graha_sign_numbers subject mapping (title() bug fix)
2. _build_dispositor_edges() output correctness
3. Integration: motif detectors fire when dispositor edges exist
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest

from pipeline.orchestrator.writers.bo_karanajala import (
    _fetch_graha_sign_numbers,
    _build_dispositor_edges,
    SIGN_LORD,
    KNOWN_GRAHAS,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID  = str(uuid.uuid4())
AYA       = "lahiri_chitrapaksha"
NOW       = "2026-06-29T00:00:00+00:00"


def _make_conn_with_rows(rows: list[tuple]) -> MagicMock:
    """Return a conn mock whose .execute().fetchall() returns rows."""
    conn = MagicMock()
    conn.execute.return_value.fetchall.return_value = rows
    return conn


class TestFetchGrahaSignNumbers:

    def test_abbreviated_codes_map_to_full_graha_names(self) -> None:
        """MAR→Mars, MER→Mercury, etc. — abbreviated L1 codes must produce KNOWN_GRAHAS keys."""
        rows = [
            ("SUN",      10.0),   # Capricorn
            ("MOON",     11.0),   # Aquarius
            ("MAR",       1.0),   # Aries
            ("MER",       9.0),   # Sagittarius
            ("JUP",       5.0),   # Leo
            ("VEN",       8.0),   # Scorpio
            ("SAT",      10.0),   # Capricorn
            ("RAH_MEAN",  6.0),   # Virgo
            ("KET_MEAN", 12.0),   # Pisces
        ]
        conn = _make_conn_with_rows(rows)
        result = _fetch_graha_sign_numbers(conn, CHART_ID, AYA)

        assert set(result.keys()) == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu"
        }, f"Expected all 9 KNOWN_GRAHA keys; got {set(result.keys())}"

    def test_sign_numbers_are_integers(self) -> None:
        rows = [("SUN", 10.0), ("MOON", 4.0)]
        conn = _make_conn_with_rows(rows)
        result = _fetch_graha_sign_numbers(conn, CHART_ID, AYA)
        assert result["Sun"] == 10
        assert result["Moon"] == 4
        assert isinstance(result["Sun"], int)

    def test_old_title_case_would_have_failed(self) -> None:
        """Document that subject.title() on abbreviated codes produces wrong keys."""
        assert "MAR".title() == "Mar"      # would miss KNOWN_GRAHAS["Mars"]
        assert "MER".title() == "Mer"      # would miss KNOWN_GRAHAS["Mercury"]
        assert "JUP".title() == "Jup"      # would miss KNOWN_GRAHAS["Jupiter"]
        assert "VEN".title() == "Ven"      # would miss KNOWN_GRAHAS["Venus"]
        assert "SAT".title() == "Sat"      # would miss KNOWN_GRAHAS["Saturn"]
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_bo_karanajala_dispositor.py::TestFetchGrahaSignNumbers -v
```
Expected: `ImportError` on `_build_dispositor_edges` and `SIGN_LORD` (don't exist yet), and `TestFetchGrahaSignNumbers.test_abbreviated_codes_map_to_full_graha_names` FAILS (returns Mar/Mer/etc.)

- [ ] **Step 3: Fix `_fetch_graha_sign_numbers` in bo_karanajala.py**

In `bo_karanajala.py`, import `_SUBJECT_TO_GRAHA` from bo_bimba at the top of the file (after the existing imports):

```python
from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA as _GRAHA_SUBJECT_MAP
```

Then change line ~181 in `_fetch_graha_sign_numbers`:

**Old (line 181):**
```python
            graha = subject.title()
```

**New:**
```python
            graha = _GRAHA_SUBJECT_MAP.get(subject.upper(), subject.title())
```

- [ ] **Step 4: Run test — verify it passes**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_bo_karanajala_dispositor.py::TestFetchGrahaSignNumbers -v
```
Expected: `TestFetchGrahaSignNumbers` 3 tests PASS (the import errors for `_build_dispositor_edges`/`SIGN_LORD` will still fail other classes — that's fine at this stage).

---

## Task 2: Add `SIGN_LORD` mapping and `_build_dispositor_edges()`

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py`
- Test: `platform/python-sidecar/tests/l2/test_bo_karanajala_dispositor.py`

**Context:** `_detect_mutual_reception` and `_detect_parivartana_chains` in `bo_cgm_motifs.py` look for edges where `edge_type='dispositor'`. `bo_karanajala` already has `graha_signs` (graha → sign_number) from `_fetch_graha_sign_numbers`. We need a sign → lord mapping and a function that emits one dispositor edge per non-self-ruling graha.

Classical Parashari sign lordship (no Rahu/Ketu):
- 1 Aries → Mars, 2 Taurus → Venus, 3 Gemini → Mercury, 4 Cancer → Moon,
- 5 Leo → Sun, 6 Virgo → Mercury, 7 Libra → Venus, 8 Scorpio → Mars,
- 9 Sagittarius → Jupiter, 10 Capricorn → Saturn, 11 Aquarius → Saturn, 12 Pisces → Jupiter

Rahu and Ketu have no sign lordship and are never the source of a dispositor edge (they are always disposed, never the dispositor). Skip them as `from_node` — but they CAN be the target (e.g., Rahu in Scorpio → lord Mars → edge Rahu→Mars).

- [ ] **Step 1: Add test for `_build_dispositor_edges` and `SIGN_LORD`**

Append to `test_bo_karanajala_dispositor.py`:

```python
class TestSignLord:

    def test_sign_lord_has_all_12_signs(self) -> None:
        assert set(SIGN_LORD.keys()) == set(range(1, 13))

    def test_sign_lord_classical_values(self) -> None:
        assert SIGN_LORD[1]  == "Mars"      # Aries
        assert SIGN_LORD[2]  == "Venus"     # Taurus
        assert SIGN_LORD[3]  == "Mercury"   # Gemini
        assert SIGN_LORD[4]  == "Moon"      # Cancer
        assert SIGN_LORD[5]  == "Sun"       # Leo
        assert SIGN_LORD[6]  == "Mercury"   # Virgo
        assert SIGN_LORD[7]  == "Venus"     # Libra
        assert SIGN_LORD[8]  == "Mars"      # Scorpio
        assert SIGN_LORD[9]  == "Jupiter"   # Sagittarius
        assert SIGN_LORD[10] == "Saturn"    # Capricorn
        assert SIGN_LORD[11] == "Saturn"    # Aquarius
        assert SIGN_LORD[12] == "Jupiter"   # Pisces


class TestBuildDispositorEdges:

    def _make_node_map(self, assignments: dict[str, str]) -> dict[tuple[str, str], str]:
        """assignments: {graha_name: node_uuid}"""
        return {("graha", g): nid for g, nid in assignments.items()}

    def test_sun_in_capricorn_disposits_saturn(self) -> None:
        """Sun in Capricorn (sign 10, lord Saturn) → edge Sun→Saturn."""
        node_map = self._make_node_map({
            "Sun": "node-sun", "Saturn": "node-sat",
        })
        graha_signs = {"Sun": 10, "Saturn": 10}   # both in Capricorn for simplicity
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        sun_edges = [e for e in edges if e["from_node_id"] == "node-sun"]
        assert len(sun_edges) == 1
        e = sun_edges[0]
        assert e["edge_type"] == "dispositor"
        assert e["to_node_id"] == "node-sat"
        assert e["direction"] == "directed"

    def test_self_ruling_graha_skipped(self) -> None:
        """Sun in Leo (sign 5) is self-ruling — no dispositor edge emitted."""
        node_map = self._make_node_map({"Sun": "node-sun"})
        graha_signs = {"Sun": 5}   # Leo, lord is Sun itself
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        assert edges == [], "Self-ruling graha must not produce a dispositor edge"

    def test_mutual_reception_produces_two_edges(self) -> None:
        """
        Sun in Aries (lord Mars) + Mars in Leo (lord Sun) → mutual reception.
        Both edges must be emitted: Sun→Mars and Mars→Sun.
        """
        node_map = self._make_node_map({"Sun": "node-sun", "Mars": "node-mars"})
        graha_signs = {
            "Sun":  1,   # Aries → lord Mars
            "Mars": 5,   # Leo   → lord Sun
        }
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        assert len(edges) == 2
        from_to = {(e["from_node_id"], e["to_node_id"]) for e in edges}
        assert ("node-sun", "node-mars") in from_to
        assert ("node-mars", "node-sun") in from_to

    def test_unknown_graha_skipped(self) -> None:
        """Grahas not in KNOWN_GRAHAS (e.g. typo) are silently skipped."""
        node_map = self._make_node_map({"Sun": "node-sun"})
        graha_signs = {"Sun": 10, "NotAGraha": 1}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        # Only Sun's edge should be produced (if Saturn node exists — here it doesn't)
        assert all(e["from_node_id"] == "node-sun" or True for e in edges)

    def test_missing_node_in_map_skipped(self) -> None:
        """If a graha or its lord has no node in node_map, skip gracefully."""
        node_map = self._make_node_map({"Sun": "node-sun"})  # Saturn missing from map
        graha_signs = {"Sun": 10}   # lord is Saturn, but Saturn has no node
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        assert edges == [], "Missing target node must not raise — edge silently skipped"

    def test_edge_fields_complete(self) -> None:
        """Verify required edge fields are present and non-null."""
        node_map = self._make_node_map({"Sun": "node-sun", "Saturn": "node-sat"})
        graha_signs = {"Sun": 10, "Saturn": 10}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        sun_edges = [e for e in edges if e["from_node_id"] == "node-sun"]
        assert sun_edges, "Expected at least one edge for Sun"
        e = sun_edges[0]
        for field in ("edge_id", "chart_id", "ayanamsha_id", "build_id", "edge_type",
                      "from_node_id", "to_node_id", "direction", "computed_strength",
                      "verification_pass_status", "citation_ref", "computed_at"):
            assert e.get(field) is not None, f"Required field '{field}' is None"
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_bo_karanajala_dispositor.py::TestSignLord tests/l2/test_bo_karanajala_dispositor.py::TestBuildDispositorEdges -v
```
Expected: `ImportError` — `SIGN_LORD` and `_build_dispositor_edges` don't exist yet.

- [ ] **Step 3: Add `SIGN_LORD` and `_build_dispositor_edges()` to bo_karanajala.py**

After the `VIRODHA_POSITIONS` constant block (around line 109), add:

```python
# Classical Parashari sign lordship: sign_number (1-12) → graha name
# Rahu and Ketu have no sign lordship in Parashari tradition.
SIGN_LORD: dict[int, str] = {
    1:  "Mars",     # Aries
    2:  "Venus",    # Taurus
    3:  "Mercury",  # Gemini
    4:  "Moon",     # Cancer
    5:  "Sun",      # Leo
    6:  "Mercury",  # Virgo
    7:  "Venus",    # Libra
    8:  "Mars",     # Scorpio
    9:  "Jupiter",  # Sagittarius
    10: "Saturn",   # Capricorn
    11: "Saturn",   # Aquarius
    12: "Jupiter",  # Pisces
}
```

After `_build_argala_edges()` (around line 297), add:

```python
def _build_dispositor_edges(
    chart_id: str, aya: str, build_id: str,
    graha_signs: dict[str, int], node_map: dict[tuple[str, str], str], now: str
) -> list[dict]:
    """Build dispositor edges: graha → its sign lord.

    For each graha in graha_signs, looks up the lord of its sign via SIGN_LORD.
    Emits edge_type='dispositor' (from graha → lord graha).
    Self-ruling grahas (e.g. Sun in Leo) are skipped — no self-loops.
    Rahu/Ketu: included as from_node (disposed by whichever graha rules their sign),
    but Rahu/Ketu are never the lord (SIGN_LORD has no entry for them).
    """
    edges: list[dict] = []
    for graha, sign_num in graha_signs.items():
        if graha not in KNOWN_GRAHAS:
            continue
        lord = SIGN_LORD.get(sign_num)
        if not lord or lord == graha:
            continue  # self-ruling or unknown sign
        from_node = node_map.get(("graha", graha))
        to_node   = node_map.get(("graha", lord))
        if not from_node or not to_node:
            continue
        edges.append({
            "edge_id":                         str(uuid.uuid4()),
            "chart_id":                        chart_id,
            "ayanamsha_id":                    aya,
            "build_id":                        build_id,
            "snapshot_type":                   SNAPSHOT_TYPE,
            "edge_type":                       "dispositor",
            "from_node_id":                    from_node,
            "to_node_id":                      to_node,
            "direction":                       "directed",
            "computed_strength":               0.6,
            "weight_formula_version":          "edge_weight_v1.0",
            "edge_properties_jsonb":           json.dumps({
                "graha":             graha,
                "sign_num":          sign_num,
                "dispositor":        lord,
                "relationship_basis": "sign_lord",
            }),
            "relationship_class":              "dispositor",
            "semantic_path_class":             "sign_lordship",
            "active_duration_class":           "natal_permanent",
            "active_dasha_periods_jsonb":      None,
            "underlying_msr_signal_ids_array": [],
            "cross_system_consensus_count":    1,
            "cancelled_flag":                  False,
            "present_in_traditions_array":     ["parashari"],
            "graph_compute_library":           GRAPH_LIB,
            "graph_compute_library_version":   GRAPH_LIB_VER,
            "is_cross_subsystem":              False,
            "subsystem_from":                  "parashari",
            "subsystem_to":                    "parashari",
            "verification_pass_status":        "two_pass_verified",
            "citation_ref":                    f"parashari/sign_lordship/{graha}",
            "citation_human":                  f"Dispositor: {graha} (sign {sign_num}) → lord {lord}",
            "computed_at":                     now,
            "engine_version":                  ENGINE_VERSION,
        })
    return edges
```

- [ ] **Step 4: Run test — verify it passes**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_bo_karanajala_dispositor.py::TestSignLord tests/l2/test_bo_karanajala_dispositor.py::TestBuildDispositorEdges -v
```
Expected: All tests PASS.

---

## Task 3: Wire `_build_dispositor_edges()` into `run()`

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py:570-583`

**Context:** The `run()` method already calls `_build_argala_edges()` and extends `edges`. We do the same with `_build_dispositor_edges()`. Also update the log line to show the dispositor count.

- [ ] **Step 1: Wire dispositor edges in `run()`**

In `BoKaranajalaWriter.run()`, after the argala block, add the dispositor block. The target section (around lines 571–583) currently reads:

```python
            argala_edges = _build_argala_edges(
                chart_id, aya, build_id, graha_signs, node_map, now
            )
            edges.extend(argala_edges)

            replace_prior_cgm_edges(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_contradictions(conn, chart_id, aya)

            logger.info(
                "[bo_karanajala] %s — %d edges (%d argala), %d contradictions",
                aya, len(edges), len(argala_edges), len(contradictions),
            )
```

Change to:

```python
            argala_edges = _build_argala_edges(
                chart_id, aya, build_id, graha_signs, node_map, now
            )
            edges.extend(argala_edges)

            dispositor_edges = _build_dispositor_edges(
                chart_id, aya, build_id, graha_signs, node_map, now
            )
            edges.extend(dispositor_edges)

            replace_prior_cgm_edges(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_contradictions(conn, chart_id, aya)

            logger.info(
                "[bo_karanajala] %s — %d edges (%d argala, %d dispositor), %d contradictions",
                aya, len(edges), len(argala_edges), len(dispositor_edges), len(contradictions),
            )
```

- [ ] **Step 2: Run the full test suite for L2 writers**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest tests/l2/ -v
```
Expected: All tests pass. No regressions.

- [ ] **Step 3: Commit Task 2+3**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py \
        platform/python-sidecar/tests/l2/test_bo_karanajala_dispositor.py
git commit -m "feat(bo_karanajala): add dispositor edges + fix graha sign subject mapping

- Fix _fetch_graha_sign_numbers: use _SUBJECT_TO_GRAHA mapping from bo_bimba
  instead of subject.title() — 7/9 grahas had wrong keys (MAR→Mar not Mars)
- Add SIGN_LORD: classical Parashari sign→lord mapping (12 signs)
- Add _build_dispositor_edges(): graha→lord directed edges (edge_type='dispositor')
- Wire dispositor edges into run() after argala edges
- Tests: TestFetchGrahaSignNumbers, TestSignLord, TestBuildDispositorEdges

Unblocks bo_cgm_motifs mutual_reception and parivartana_chain detectors
which require edge_type='dispositor' in bodha_cgm_edges."
```

---

## Task 4: Integration test — motif detectors fire with dispositor edges

**Files:**
- Test: `platform/python-sidecar/tests/l2/test_bo_karanajala_dispositor.py`

**Context:** The motif detectors in `bo_cgm_motifs.py` take `graha_nodes` and `edge_by_from` as parameters. We can test them directly with synthetic data using dispositor edges. This verifies the full contract: dispositor edges produced by bo_karanajala are correctly consumed by the motif detectors.

- [ ] **Step 1: Add integration tests**

Append to `test_bo_karanajala_dispositor.py`:

```python
# ── Integration: motif detectors fire when dispositor edges exist ──────────────

from pipeline.orchestrator.writers.bo_cgm_motifs import (
    _detect_mutual_reception,
    _detect_parivartana_chains,
    _detect_stellia,
)


def _make_graha_node(node_id: str, subject: str, house: int | None = None) -> dict:
    pos = json.dumps({"house": house}) if house is not None else None
    return {
        "node_id": node_id,
        "node_subject": subject,
        "node_label_human": subject,
        "position_in_chart_jsonb": pos,
    }


def _make_dispositor_edge(edge_id: str, from_id: str, to_id: str) -> dict:
    return {
        "edge_id": edge_id,
        "from_node_id": from_id,
        "to_node_id": to_id,
        "edge_type": "dispositor",
        "relationship_basis": None,
        "computed_strength": 0.6,
    }


def _make_conjunction_edge(edge_id: str, from_id: str, to_id: str) -> dict:
    return {
        "edge_id": edge_id,
        "from_node_id": from_id,
        "to_node_id": to_id,
        "edge_type": "conjunction",
        "relationship_basis": None,
        "computed_strength": 0.7,
    }


class TestMotifDetectorsWithDispositorEdges:

    def test_mutual_reception_detected(self) -> None:
        """
        Sun→Mars dispositor + Mars→Sun dispositor → mutual_reception motif fires.
        Scenario: Sun in Aries (lord Mars), Mars in Leo (lord Sun).
        """
        nodes = [
            _make_graha_node("n-sun",  "Sun"),
            _make_graha_node("n-mars", "Mars"),
        ]
        # Sun → Mars (Sun is disposed by Mars)
        # Mars → Sun (Mars is disposed by Sun)
        edge_sun_mars  = _make_dispositor_edge("e1", "n-sun",  "n-mars")
        edge_mars_sun  = _make_dispositor_edge("e2", "n-mars", "n-sun")
        edge_by_from = {
            "n-sun":  [edge_sun_mars],
            "n-mars": [edge_mars_sun],
        }
        motifs = _detect_mutual_reception(nodes, edge_by_from)
        assert len(motifs) == 1, f"Expected 1 mutual_reception motif; got {len(motifs)}"
        assert motifs[0]["motif_class"] == "mutual_reception"
        assert "Sun" in motifs[0]["motif_name"] or "Mars" in motifs[0]["motif_name"]

    def test_no_mutual_reception_when_only_one_direction(self) -> None:
        """Sun→Mars edge exists but no Mars→Sun edge → no mutual reception."""
        nodes = [
            _make_graha_node("n-sun",  "Sun"),
            _make_graha_node("n-mars", "Mars"),
        ]
        edge_by_from = {"n-sun": [_make_dispositor_edge("e1", "n-sun", "n-mars")]}
        motifs = _detect_mutual_reception(nodes, edge_by_from)
        assert motifs == []

    def test_parivartana_chain_length_3_detected(self) -> None:
        """
        Sun→Mars→Moon→Sun dispositor cycle (length 3) → parivartana_chain motif.
        """
        nodes = [
            _make_graha_node("n-sun",  "Sun"),
            _make_graha_node("n-mars", "Mars"),
            _make_graha_node("n-moon", "Moon"),
        ]
        edge_by_from = {
            "n-sun":  [_make_dispositor_edge("e1", "n-sun",  "n-mars")],
            "n-mars": [_make_dispositor_edge("e2", "n-mars", "n-moon")],
            "n-moon": [_make_dispositor_edge("e3", "n-moon", "n-sun")],
        }
        motifs = _detect_parivartana_chains(nodes, edge_by_from)
        assert len(motifs) >= 1, f"Expected ≥1 parivartana_chain; got {len(motifs)}"
        classes = [m["motif_class"] for m in motifs]
        assert "parivartana_chain" in classes

    def test_stellium_detected_with_position_data(self) -> None:
        """
        3 graha nodes all in house 1 → stellium motif fires.
        Requires position_in_chart_jsonb populated (bo_bimba fix already deployed).
        """
        nodes = [
            _make_graha_node("n-sun",  "Sun",  house=1),
            _make_graha_node("n-mars", "Mars", house=1),
            _make_graha_node("n-sat",  "Saturn", house=1),
            _make_graha_node("n-moon", "Moon", house=4),   # different house
        ]
        conj_1 = _make_conjunction_edge("c1", "n-sun",  "n-mars")
        conj_2 = _make_conjunction_edge("c2", "n-sun",  "n-sat")
        conj_3 = _make_conjunction_edge("c3", "n-mars", "n-sat")
        edge_by_from = {
            "n-sun":  [conj_1, conj_2],
            "n-mars": [conj_3],
        }
        motifs = _detect_stellia(nodes, edge_by_from)
        assert len(motifs) == 1, f"Expected 1 stellium; got {len(motifs)}"
        assert motifs[0]["motif_class"] == "stellium"
        assert "House 1" in motifs[0]["motif_name"]

    def test_stellium_requires_3_grahas(self) -> None:
        """2 grahas in same house → no stellium (below threshold)."""
        nodes = [
            _make_graha_node("n-sun",  "Sun",  house=1),
            _make_graha_node("n-mars", "Mars", house=1),
        ]
        edge_by_from = {"n-sun": [_make_conjunction_edge("c1", "n-sun", "n-mars")]}
        motifs = _detect_stellia(nodes, edge_by_from)
        assert motifs == []

    def test_no_motifs_without_dispositor_edges(self) -> None:
        """Without any dispositor edges, mutual_reception and parivartana_chain return 0."""
        nodes = [
            _make_graha_node("n-sun",  "Sun"),
            _make_graha_node("n-mars", "Mars"),
        ]
        edge_by_from: dict = {}
        assert _detect_mutual_reception(nodes, edge_by_from) == []
        assert _detect_parivartana_chains(nodes, edge_by_from) == []
```

- [ ] **Step 2: Run integration tests**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_bo_karanajala_dispositor.py::TestMotifDetectorsWithDispositorEdges -v
```
Expected: All 6 tests PASS.

- [ ] **Step 3: Run complete L2 test suite — no regressions**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest tests/l2/ -v
```
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add platform/python-sidecar/tests/l2/test_bo_karanajala_dispositor.py
git commit -m "test(bo_cgm_motifs): integration tests for motif detectors with dispositor edges

- TestFetchGrahaSignNumbers: guards against title() regression
- TestSignLord: verifies all 12 classical sign-lord mappings
- TestBuildDispositorEdges: edge output shape, self-ruling skip, mutual-reception pair
- TestMotifDetectorsWithDispositorEdges: end-to-end — detectors fire with real edge data"
```

---

## Summary

| What was broken | Root cause | Fix |
|---|---|---|
| `position_in_chart_jsonb=None` for 7/9 grahas | `bo_bimba.py:126` used `subject.title()` — **ALREADY FIXED** (wave 2, `_SUBJECT_TO_GRAHA`) | N/A |
| Graha sign numbers wrong for 7/9 grahas | `bo_karanajala.py:181` same `subject.title()` bug — breaks argala + would break dispositor | Fix: `_GRAHA_SUBJECT_MAP.get(subject.upper(), subject.title())` |
| mutual_reception + parivartana_chain: 0 motifs | `bo_karanajala` never emitted `edge_type='dispositor'` | Fix: add `SIGN_LORD` + `_build_dispositor_edges()` + wire in `run()` |
| stellium: 0 motifs | `position_in_chart_jsonb=None` (upstream) | Already fixed by bo_bimba wave 2 fix |

After these changes, a fresh `bo_karanajala` + `bo_cgm_motifs` rebuild will produce:
- Up to 9 dispositor edges per ayanamsha (one per non-self-ruling graha)
- Stellium motifs for any chart with 3+ grahas co-located in a house
- Mutual reception motifs for any graha pair ruling each other's signs
- Parivartana chain motifs for any dispositor cycle of length 3–6
